import logging
from collections.abc import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.redis import get_redis_client

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis."""

    _excluded = frozenset({"/health", "/docs", "/openapi.json", "/redoc"})
    _auth_register_path = f"/api/{settings.app_version}/auth/register"

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        client_ip = self._get_client_ip(request)
        path = request.url.path

        if self._is_excluded(path):
            return await call_next(request)

        if path.startswith("/auth/"):
            limit = settings.rate_limit_auth_per_minute
        else:
            limit = settings.rate_limit_per_minute

        key = f"rate_limit:{client_ip}:{path}"

        try:
            redis = get_redis_client()
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
        return path in self._excluded or path == self._auth_register_path
