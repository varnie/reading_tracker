import json
from typing import Annotated, Any

import redis.asyncio as redis
from fastapi import Depends

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RedisManager:
    """Redis connection manager using connection pool."""

    def __init__(self) -> None:
        self._pool = redis.ConnectionPool.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=settings.redis_max_connections,
        )
        self._client = redis.Redis(connection_pool=self._pool)

    async def close(self) -> None:
        """Close Redis connections."""
        await self._client.close()
        await self._pool.disconnect()

    @property
    def client(self) -> redis.Redis:
        """Get Redis client."""
        return self._client


redis_manager = RedisManager()


def get_redis_client() -> redis.Redis:
    """Get Redis client (for dependency injection and events)."""
    return redis_manager.client


async def close_redis() -> None:
    """Close Redis connection."""
    await redis_manager.close()


async def get_blacklist(
    redis_client: Annotated[redis.Redis, Depends(get_redis_client)],
) -> "TokenBlacklist":
    """Get TokenBlacklist instance (for dependency injection in endpoints)."""
    return TokenBlacklist(redis_client)


async def get_cache(
    redis_client: Annotated[redis.Redis, Depends(get_redis_client)],
) -> "Cache":
    """Get Cache instance (for dependency injection in endpoints)."""
    return Cache(redis_client)


class TokenBlacklist:
    """Manage blacklisted JWT tokens in Redis."""

    def __init__(self, redis_client: redis.Redis | None = None) -> None:
        self._redis = redis_client or get_redis_client()
        self._prefix = "blacklist:"

    async def blacklist_token(self, jti: str, ttl: int) -> None:
        """Add a token JTI to the blacklist."""
        if ttl <= 0:
            return
        key = f"{self._prefix}{jti}"
        await self._redis.setex(key, ttl, "1")
        logger.debug(f"Blacklisted token: {jti}")

    async def is_blacklisted(self, jti: str) -> bool:
        """Check if a token JTI is blacklisted."""
        try:
            return await self._redis.exists(f"{self._prefix}{jti}") > 0
        except redis.RedisError as e:
            logger.error(f"Redis error during blacklist check: {e}")
            return True  # Fail closed - deny access on Redis errors


class Cache:
    """Simple cache manager using Redis."""

    def __init__(self, redis_client: redis.Redis | None = None) -> None:
        self._redis = redis_client or get_redis_client()
        self._prefix = "cache:"

    def _get_full_key(self, key: str) -> str:
        return f"{self._prefix}{key}"

    async def get(self, key: str) -> Any | None:
        """Get a value from cache."""
        raw_value = await self._redis.get(self._get_full_key(key))
        if raw_value is None:
            return None
        try:
            return json.loads(raw_value)
        except (json.JSONDecodeError, TypeError):
            return raw_value

    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Set a value in cache with TTL in seconds."""
        data = json.dumps(value) if not isinstance(value, (str, int, float)) else value
        await self._redis.setex(self._get_full_key(key), ttl, data)

    async def delete(self, key: str) -> None:
        """Delete a key from cache."""
        await self._redis.delete(self._get_full_key(key))

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern."""
        full_pattern = self._get_full_key(pattern)
        keys = [k async for k in self._redis.scan_iter(match=full_pattern, count=1000)]
        if keys:
            return await self._redis.delete(*keys)
        return 0
