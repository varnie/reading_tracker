import json
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import Period
from app.core.redis import Cache, get_redis_client
from app.features.stats.repository import StatsRepository
from app.features.stats.schemas import (
    TopUserEntry,
    TopUsersResponse,
    UserStatsResponse,
)


class StatsService:
    """Service for statistics operations."""

    def __init__(self, session: AsyncSession, cache: Cache) -> None:
        self._session = session
        self._repo = StatsRepository(session)
        self._cache = cache

    async def get_user_stats(self, user_id: UUID) -> UserStatsResponse:
        """Get statistics for a user."""
        cache_key = f"user_stats:{user_id}"
        cached = await self._cache.get(cache_key)

        if cached:
            return UserStatsResponse(**cached)

        stats = await self._repo.get_user_stats(user_id)

        # Streaks are computed asynchronously by Celery and stored under `streak:{user_id}`.
        # We keep the DB stats aggregation simple and enrich with Redis-derived streak values here.
        try:
            redis = get_redis_client()
            streak_raw = await redis.get(f"streak:{user_id}")
            if streak_raw:
                streak = json.loads(streak_raw)
                stats["current_streak"] = streak.get(
                    "current_streak", stats.get("current_streak", 0)
                )
                stats["longest_streak"] = streak.get(
                    "longest_streak", stats.get("longest_streak", 0)
                )
        except Exception:
            # Stats should still be returned even if Redis is temporarily unavailable.
            pass

        response = UserStatsResponse(**stats)
        await self._cache.set(cache_key, response.model_dump(), ttl=300)

        return response

    async def get_top_users(
        self,
        period: Period = Period.MONTH,
        limit: int = 10,
    ) -> TopUsersResponse:
        """Get top users leaderboard."""
        cache_key = f"leaderboard:{period.value}:{limit}"
        cached = await self._cache.get(cache_key)

        if cached:
            return TopUsersResponse(**cached)

        users = await self._repo.get_top_users(period=period, limit=limit)

        response = TopUsersResponse(
            period=period.value,
            users=[TopUserEntry(**u) for u in users],
        )

        await self._cache.set(cache_key, response.model_dump(), ttl=3600)

        return response
