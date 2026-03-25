import ipaddress
import logging
import os
import re
import sys
from collections.abc import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core import redis as redis_module
from app.core.config import settings

logger = logging.getLogger(__name__)


IPV4_PATTERN = re.compile(r"^(\d{1,3}\.){3}\d{1,3}$")


def _is_valid_ip(ip: str) -> bool:
    """Validate IP address format."""
    if not ip or len(ip) > 45:
        return False
    if IPV4_PATTERN.match(ip):
        parts = ip.split(".")
        return all(0 <= int(p) <= 255 for p in parts)
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis."""

    _excluded = frozenset({"/health", "/docs", "/redoc"})
    _auth_register_path = f"/api/{settings.app_version}/auth/register"
    _auth_prefix = f"/api/{settings.app_version}/auth/"
    _openapi_path = f"/api/{settings.app_version}/openapi.json"

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        if (
            "PYTEST_CURRENT_TEST" in os.environ
            or "PYTEST_VERSION" in os.environ
            or any(mod.startswith("pytest") for mod in sys.modules)
        ):
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        path = request.url.path

        if self._is_excluded(path):
            return await call_next(request)

        if path.startswith(self._auth_prefix):
            limit = settings.rate_limit_auth_per_minute
        else:
            limit = settings.rate_limit_per_minute

        try:
            redis = redis_module.get_redis_client()

            lockout_key = f"lockout:{client_ip}"
            if await redis.exists(lockout_key):
                ttl = await redis.ttl(lockout_key)
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Account temporarily locked due to too many failed attempts"
                    },
                    headers={
                        "Retry-After": str(max(ttl, 1)),
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": "0",
                    },
                )

            key = f"rate_limit:{client_ip}:{path}"
            current_count = await redis.incr(key)
            current_ttl = await redis.ttl(key)
            if current_count == 1 or current_ttl == -1:
                await redis.expire(key, 60)

            if current_count > limit:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded"},
                    headers={
                        "Retry-After": str(current_ttl) if current_ttl > 0 else "60",
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": "0",
                    },
                )

        except Exception:
            logger.warning("Redis error during rate limiting, allowing request")
            return await call_next(request)

        response = await call_next(request)

        remaining = limit - current_count
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request with proxy validation."""
        direct_client = request.client.host if request.client else None

        trusted_proxies = settings.trusted_proxies_list
        forwarded = request.headers.get("X-Forwarded-For")
        real_ip = request.headers.get("X-Real-IP")

        if trusted_proxies and direct_client in trusted_proxies:
            if forwarded:
                ips = [ip.strip() for ip in forwarded.split(",")]
                for ip in ips:
                    if _is_valid_ip(ip) and ip not in trusted_proxies:
                        return ip
                return ips[-1] if ips else direct_client

            if real_ip and _is_valid_ip(real_ip) and real_ip not in trusted_proxies:
                return real_ip

        if direct_client and _is_valid_ip(direct_client):
            return direct_client

        if real_ip and _is_valid_ip(real_ip):
            return real_ip

        return direct_client or "unknown"

    def _is_excluded(self, path: str) -> bool:
        """Check if path is excluded from rate limiting."""
        return (
            path in self._excluded
            or path == self._auth_register_path
            or path == self._openapi_path
        )


async def check_failed_login(client_ip: str, redis_client) -> tuple[bool, int]:
    """
    Check if client is locked out and track failed attempts.

    Returns:
        Tuple of (is_locked, attempts)
    """
    lockout_key = f"lockout:{client_ip}"
    if await redis_client.exists(lockout_key):
        return True, settings.rate_limit_max_failed_attempts

    attempts_key = f"failed_login:{client_ip}"
    attempts = await redis_client.get(attempts_key)
    return False, int(attempts) if attempts else 0


async def record_failed_login(client_ip: str, redis_client) -> bool:
    """
    Record a failed login attempt and lock out if threshold reached.

    Returns:
        True if account is now locked
    """
    attempts_key = f"failed_login:{client_ip}"
    lockout_key = f"lockout:{client_ip}"

    attempts = await redis_client.get(attempts_key)
    current_attempts = int(attempts) if attempts else 0
    new_attempts = current_attempts + 1

    if new_attempts >= settings.rate_limit_max_failed_attempts:
        lockout_seconds = settings.rate_limit_lockout_duration_minutes * 60
        await redis_client.setex(lockout_key, lockout_seconds, "1")
        await redis_client.delete(attempts_key)
        logger.warning(
            f"Account locked out for {client_ip} after {new_attempts} failed attempts"
        )
        return True

    await redis_client.setex(attempts_key, 3600, str(new_attempts))
    return False


async def clear_failed_logins(client_ip: str, redis_client) -> None:
    """Clear failed login attempts after successful login."""
    attempts_key = f"failed_login:{client_ip}"
    await redis_client.delete(attempts_key)
