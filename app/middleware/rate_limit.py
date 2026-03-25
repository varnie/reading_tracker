"""
Rate limiting using Redis with Lua scripting for atomic operations.

Use as a FastAPI dependency:
    from app.middleware.rate_limit import RateLimiter

    @router.post("/login", dependencies=[Depends(RateLimiter(times=5, seconds=60))])
    async def login(): ...
"""

import logging
from ipaddress import ip_address

from fastapi import HTTPException, Request, status

from app.core import redis as redis_module
from app.core.config import settings

logger = logging.getLogger(__name__)

RATE_LIMIT_LUA = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return current
"""


def _get_client_ip(request: Request) -> str:
    """Extract client IP, respecting trusted proxies."""
    direct_ip = request.client.host if request.client else None

    if settings.trusted_proxies_list and direct_ip in settings.trusted_proxies_list:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            for ip in reversed(forwarded.split(",")):
                ip = ip.strip()
                try:
                    ip_address(ip)
                    if ip not in settings.trusted_proxies_list:
                        return ip
                except ValueError:
                    continue
            return direct_ip or "unknown"

    if direct_ip:
        try:
            ip_address(direct_ip)
            return direct_ip
        except ValueError:
            pass

    return direct_ip or "unknown"


class RateLimiter:
    """
    FastAPI dependency for rate limiting.

    Usage:
        @router.post("/login", dependencies=[Depends(RateLimiter(times=5, seconds=60))])
        async def login(): ...
    """

    def __init__(self, times: int, seconds: int):
        self.times = times
        self.seconds = seconds

    async def __call__(self, request: Request) -> None:
        if getattr(request.app.state, "testing", False):
            return

        client_ip = _get_client_ip(request)
        key = f"rate:{client_ip}:{request.url.path}"

        redis = redis_module.get_redis_client()
        count = await redis.eval(RATE_LIMIT_LUA, 1, key, self.seconds)

        if count > self.times:
            ttl = await redis.ttl(key)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests",
                headers={
                    "Retry-After": str(max(ttl, 1)),
                    "X-RateLimit-Limit": str(self.times),
                    "X-RateLimit-Remaining": "0",
                },
            )


def get_rate_limiter(times: int, seconds: int) -> RateLimiter:
    """Factory for creating RateLimiter instances."""
    return RateLimiter(times=times, seconds=seconds)


def default_limiter() -> RateLimiter:
    """Default rate limiter (60 requests per minute)."""
    return RateLimiter(times=settings.rate_limit_per_minute, seconds=60)


def auth_limiter() -> RateLimiter:
    """Auth rate limiter (10 requests per minute)."""
    return RateLimiter(times=settings.rate_limit_auth_per_minute, seconds=60)


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
