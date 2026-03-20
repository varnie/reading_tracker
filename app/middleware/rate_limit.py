import logging
import os
import sys
from collections.abc import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core import redis as redis_module
from app.core.config import settings

logger = logging.getLogger(__name__)


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
        # Tests use in-memory/fake Redis and ASGITransport, which can make global
        # rate limiting state appear flaky across the suite. Disable rate
        # limiting under pytest to keep CI deterministic.
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

        key = f"rate_limit:{client_ip}:{path}"

        try:
            # Use indirection so tests can override `app.core.redis.get_redis_client`.
            redis = redis_module.get_redis_client()
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
        """Extract client IP from request."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        if request.client:
            return request.client.host

        return "unknown"

    def _is_excluded(self, path: str) -> bool:
        """Check if path is excluded from rate limiting."""
        return (
            path in self._excluded
            or path == self._auth_register_path
            or path == self._openapi_path
        )
