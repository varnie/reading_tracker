import time
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.redis import get_redis


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        client_ip = self._get_client_ip(request)
        path = request.url.path

        if self._is_excluded(path):
            return await call_next(request)

        if path.startswith("/api/"):
            limit = settings.rate_limit_per_minute
        elif path.startswith("/auth/"):
            limit = settings.rate_limit_auth_per_minute
        else:
            limit = settings.rate_limit_per_minute

        key = f"rate_limit:{client_ip}:{path}"

        redis = await get_redis()

        current = await redis.get(key)

        if current is None:
            await redis.setex(key, 60, "1")
        else:
            current_int = int(current)
            if current_int >= limit:
                ttl = await redis.ttl(key)
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded"},
                    headers={"Retry-After": str(ttl) if ttl > 0 else "60"},
                )
            await redis.incr(key)

        response = await call_next(request)

        remaining = limit - int(await redis.get(key) or "0") - 1
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
        excluded = ["/health", "/docs", "/openapi.json", "/redoc"]
        return path in excluded or path.startswith("/api/v1/auth/register")
