from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.stats.schemas import TopUsersResponse, UserStatsResponse
from app.features.stats.service import StatsService
from app.models.user import User
from app.shared.dependencies import get_current_user, get_db

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get(
    "",
    response_model=UserStatsResponse,
    summary="Get user statistics",
)
async def get_user_stats(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> UserStatsResponse:
    """Get statistics for the current user."""
    service = StatsService(session)
    return await service.get_user_stats(user.id)


@router.get(
    "/top-users",
    response_model=TopUsersResponse,
    summary="Get top users",
)
async def get_top_users(
    period: str = Query(
        default="month",
        description="Time period: week, month, or all",
    ),
    limit: int = Query(default=10, ge=1, le=50),
    session: AsyncSession = Depends(get_db),
) -> TopUsersResponse:
    """Get top readers leaderboard."""
    service = StatsService(session)
    return await service.get_top_users(period=period, limit=limit)
