import json
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select

from app.core.enums import BookStatus, Period
from app.core.logging import get_logger
from app.models.reading_session import ReadingSession
from app.models.user import User
from app.models.user_book import UserBook
from app.tasks.celery_app import celery_app
from app.tasks.celery_db import get_sync_redis, get_sync_session

logger = get_logger(__name__)


@celery_app.task
def calculate_user_streaks() -> dict:
    """
    Calculate and update reading streaks for all active users.

    Returns:
        Number of users with active streaks.
    """
    logger.info("Running calculate_user_streaks task")

    redis_client = get_sync_redis()

    with get_sync_session() as session:
        users = session.execute(select(User)).scalars().all()
        users_updated = 0

        for user in users:
            user_books = (
                session.execute(select(UserBook).where(UserBook.user_id == user.id))
                .scalars()
                .all()
            )

            book_ids = [ub.id for ub in user_books]
            if not book_ids:
                continue

            sessions = (
                session.execute(
                    select(ReadingSession)
                    .where(ReadingSession.user_book_id.in_(book_ids))
                    .order_by(ReadingSession.started_at)
                )
                .scalars()
                .all()
            )

            session_dates = set()
            for s in sessions:
                if s.started_at:
                    session_dates.add(s.started_at.date())

            if not session_dates:
                continue

            current_streak = 0
            longest_streak = 0
            today = datetime.now(UTC).date()
            check_date = today

            while check_date in session_dates:
                current_streak += 1
                check_date -= timedelta(days=1)

            sorted_dates = sorted(session_dates)
            temp_streak = 1
            for i in range(1, len(sorted_dates)):
                if (sorted_dates[i] - sorted_dates[i - 1]).days == 1:
                    temp_streak += 1
                else:
                    longest_streak = max(longest_streak, temp_streak)
                    temp_streak = 1
            longest_streak = max(longest_streak, temp_streak)

            streak_data = {
                "user_id": str(user.id),
                "current_streak": current_streak,
                "longest_streak": longest_streak,
                "last_read_date": max(session_dates).isoformat()
                if session_dates
                else None,
            }

            redis_client.setex(f"streak:{user.id}", 3600, json.dumps(streak_data))
            users_updated += 1

        logger.info(f"Updated streaks for {users_updated} users")
        return {"users_updated": users_updated}


@celery_app.task
def update_leaderboard(period: Period = Period.MONTH, limit: int = 10) -> dict:
    """
    Update the top users leaderboard cache in Redis.

    Args:
        period: Time period for leaderboard (week, month, all)
        limit: Number of top users to return

    Returns:
        Leaderboard data.
    """
    logger.info(f"Running update_leaderboard task (period={period}, limit={limit})")

    redis_client = get_sync_redis()

    with get_sync_session() as session:
        if period == Period.WEEK:
            cutoff = datetime.now(UTC) - timedelta(days=7)
        elif period == Period.MONTH:
            cutoff = datetime.now(UTC) - timedelta(days=30)
        else:
            cutoff = None

        query = (
            select(UserBook.user_id, func.count(UserBook.id).label("finished_count"))
            .where(UserBook.status == BookStatus.FINISHED)
            .group_by(UserBook.user_id)
            .order_by(func.count(UserBook.id).desc())
            .limit(limit)
        )

        if cutoff:
            query = query.where(UserBook.finished_at >= cutoff)

        result = session.execute(query).all()

        leaderboard = []
        for rank, row in enumerate(result, 1):
            user = session.get(User, row.user_id)
            user_email = user.email if user else "unknown"

            total_pages = (
                session.execute(
                    select(func.sum(UserBook.pages_read)).where(
                        UserBook.user_id == row.user_id
                    )
                ).scalar()
                or 0
            )

            streak_data = redis_client.get(f"streak:{row.user_id}")
            streak_days = 0
            if streak_data:
                streak_json = json.loads(streak_data)
                streak_days = streak_json.get("current_streak", 0)

            leaderboard.append(
                {
                    "rank": rank,
                    "user_id": str(row.user_id),
                    "user_email": user_email,
                    "books_finished": row.finished_count,
                    "pages_read": total_pages,
                    "streak_days": streak_days,
                }
            )

        cache_key = f"leaderboard:{period}:{limit}"
        redis_client.setex(cache_key, 3600, json.dumps(leaderboard))

        logger.info(
            f"Updated leaderboard for period={period}: {len(leaderboard)} users"
        )
        return {
            "period": period,
            "users": leaderboard,
        }
