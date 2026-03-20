import json
from typing import Any

import redis.asyncio as redis

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_redis_client: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    """Get or create Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def close_redis() -> None:
    """Close Redis connection."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None


class TokenBlacklist:
    """Manage blacklisted JWT tokens in Redis."""

    def __init__(self, redis_client: redis.Redis) -> None:
        self._redis = redis_client
        self._prefix = "blacklist:"

    async def blacklist_token(self, jti: str, ttl: int) -> None:
        """Add a token JTI to the blacklist."""
        key = f"{self._prefix}{jti}"
        await self._redis.setex(key, ttl, "1")
        logger.debug(f"Blacklisted token: {jti}")

    async def is_blacklisted(self, jti: str) -> bool:
        """Check if a token JTI is blacklisted."""
        key = f"{self._prefix}{jti}"
        return await self._redis.exists(key) > 0


class Cache:
    """Simple cache manager using Redis."""

    def __init__(self, redis_client: redis.Redis) -> None:
        self._redis = redis_client
        self._prefix = "cache:"

    async def get(self, key: str) -> Any | None:
        """Get a value from cache."""
        full_key = f"{self._prefix}{key}"
        value = await self._redis.get(full_key)
        if value:
            return json.loads(value)
        return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Set a value in cache with TTL in seconds."""
        full_key = f"{self._prefix}{key}"
        await self._redis.setex(full_key, ttl, json.dumps(value))

    async def delete(self, key: str) -> None:
        """Delete a key from cache."""
        full_key = f"{self._prefix}{key}"
        await self._redis.delete(full_key)

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern."""
        full_pattern = f"{self._prefix}{pattern}"
        keys = [key async for key in self._redis.scan_iter(match=full_pattern)]
        if keys:
            return await self._redis.delete(*keys)
        return 0
