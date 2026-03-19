from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import Cache, get_redis
from app.features.stats.repository import StatsRepository
from app.features.stats.schemas import (
    UserStatsResponse,
    TopUsersResponse,
    TopUserEntry,
)


class StatsService:
    """Service for statistics operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = StatsRepository(session)

    async def get_user_stats(self, user_id: UUID) -> UserStatsResponse:
        """Get statistics for a user."""
        redis = await get_redis()
        cache = Cache(redis)

        cache_key = f"user_stats:{user_id}"
        cached = await cache.get(cache_key)

        if cached:
            return UserStatsResponse(**cached)

        stats = await self._repo.get_user_stats(user_id)

        response = UserStatsResponse(**stats)
        await cache.set(cache_key, response.model_dump(), ttl=300)

        return response

    async def get_top_users(
        self,
        period: str = "month",
        limit: int = 10,
    ) -> TopUsersResponse:
        """Get top users leaderboard."""
        redis = await get_redis()
        cache = Cache(redis)

        cache_key = f"leaderboard:{period}:{limit}"
        cached = await cache.get(cache_key)

        if cached:
            return TopUsersResponse(**cached)

        users = await self._repo.get_top_users(period=period, limit=limit)

        response = TopUsersResponse(
            period=period,
            users=[TopUserEntry(**u) for u in users],
        )

        await cache.set(cache_key, response.model_dump(), ttl=3600)

        return response
