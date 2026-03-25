import logging
import os
import sys
from collections.abc import Callable
from ipaddress import ip_address

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core import redis as redis_module
from app.core.config import settings

logger = logging.getLogger(__name__)


def _parse_ip(ip: str) -> str | None:
    """Parse and validate IP address, return None if invalid."""
    try:
        str(ip_address(ip))
        return ip
    except ValueError:
        return None


def _get_client_ip(request: Request) -> str:
    """
    Extract client IP from request.

    Priority:
    1. X-Forwarded-For header (if request comes from trusted proxy)
    2. X-Real-IP header (if request comes from trusted proxy)
    3. Direct client IP (request.client)
    """
    direct_ip = request.client.host if request.client else None
    forwarded = request.headers.get("X-Forwarded-For")
    real_ip = request.headers.get("X-Real-IP")
    trusted = settings.trusted_proxies_list

    if trusted and direct_ip in trusted:
        if forwarded:
            for ip in reversed(forwarded.split(",")):
                ip = ip.strip()
                if _parse_ip(ip) and ip not in trusted:
                    return ip
            return direct_ip

        if real_ip and _parse_ip(real_ip) and real_ip not in trusted:
            return real_ip

    if direct_ip and _parse_ip(direct_ip):
        return direct_ip

    if real_ip and _parse_ip(real_ip):
        return real_ip

    return direct_ip or "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis."""

    EXCLUDED_PATHS = frozenset({"/health", "/docs", "/redoc"})
    AUTH_PREFIX = f"/api/{settings.app_version}/auth/"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if self._is_testing():
            return await call_next(request)

        client_ip = _get_client_ip(request)
        path = request.url.path

        if path in self.EXCLUDED_PATHS:
            return await call_next(request)

        if path.startswith(self.AUTH_PREFIX) and path != f"{self.AUTH_PREFIX}register":
            limit = settings.rate_limit_auth_per_minute
        else:
            limit = settings.rate_limit_per_minute

        try:
            redis = redis_module.get_redis_client()

            if await redis.exists(f"lockout:{client_ip}"):
                return self._lockout_response(limit)

            key = f"rate_limit:{client_ip}:{path}"
            count = await redis.incr(key)
            ttl = await redis.ttl(key)

            if count == 1:
                await redis.expire(key, 60)

            if count > limit:
                return self._rate_limit_response(limit, max(ttl, 1))

        except Exception:
            logger.warning("Rate limit check failed, allowing request")
            return await call_next(request)

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, limit - count))
        return response

    def _is_testing(self) -> bool:
        return (
            "PYTEST_CURRENT_TEST" in os.environ
            or "PYTEST_VERSION" in os.environ
            or any(m.startswith("pytest") for m in sys.modules)
        )

    def _rate_limit_response(self, limit: int, ttl: int) -> Response:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
            headers={
                "Retry-After": str(ttl),
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
            },
        )

    def _lockout_response(self, limit: int) -> Response:
        return JSONResponse(
            status_code=429,
            content={"detail": "Account temporarily locked"},
            headers={
                "Retry-After": "900",
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
            },
        )


async def check_failed_login(client_ip: str, redis) -> tuple[bool, int]:
    """Check if client IP is locked out."""
    if await redis.exists(f"lockout:{client_ip}"):
        return True, settings.rate_limit_max_failed_attempts
    attempts = await redis.get(f"failed_login:{client_ip}")
    return False, int(attempts) if attempts else 0


async def record_failed_login(client_ip: str, redis) -> bool:
    """Record failed login and lock out if threshold reached."""
    attempts_key = f"failed_login:{client_ip}"
    lockout_key = f"lockout:{client_ip}"

    attempts = int(await redis.get(attempts_key) or 0) + 1

    if attempts >= settings.rate_limit_max_failed_attempts:
        await redis.setex(
            lockout_key, settings.rate_limit_lockout_duration_minutes * 60, "1"
        )
        await redis.delete(attempts_key)
        logger.warning(f"Locked out {client_ip} after {attempts} failed attempts")
        return True

    await redis.setex(attempts_key, 3600, str(attempts))
    return False


async def clear_failed_logins(client_ip: str, redis) -> None:
    """Clear failed login tracking after successful login."""
    await redis.delete(f"failed_login:{client_ip}")
