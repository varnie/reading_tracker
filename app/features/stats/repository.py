from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import BookStatus, Period
from app.models.user_book import UserBook


class StatsRepository:
    """Repository for statistics data access."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_user_stats(self, user_id: UUID) -> dict:
        """Get statistics for a user."""
        result = await self._session.execute(
            select(UserBook).where(UserBook.user_id == user_id)
        )
        books = list(result.scalars().all())

        total_books = len(books)
        books_want_to_read = sum(
            1 for b in books if b.status == BookStatus.WANT_TO_READ
        )
        books_reading = sum(1 for b in books if b.status == BookStatus.READING)
        books_finished = sum(1 for b in books if b.status == BookStatus.FINISHED)
        books_abandoned = sum(1 for b in books if b.status == BookStatus.ABANDONED)
        total_pages_read = sum(b.pages_read for b in books)

        return {
            "total_books": total_books,
            "books_want_to_read": books_want_to_read,
            "books_reading": books_reading,
            "books_finished": books_finished,
            "books_abandoned": books_abandoned,
            "total_pages_read": total_pages_read,
            "current_streak": 0,
            "longest_streak": 0,
        }

    async def get_top_users(
        self,
        period: Period = Period.MONTH,
        limit: int = 10,
    ) -> list[dict]:
        """Get top users by reading activity."""
        from sqlalchemy import desc

        now = datetime.now(UTC)
        if period == Period.WEEK:
            start_date = now - timedelta(days=7)
        elif period == Period.MONTH:
            start_date = now - timedelta(days=30)
        else:
            start_date = None

        query = select(
            UserBook.user_id,
            func.count(UserBook.id).label("books_finished"),
            func.sum(UserBook.pages_read).label("pages_read"),
        ).where(UserBook.status == BookStatus.FINISHED)

        if start_date:
            query = query.where(UserBook.finished_at >= start_date)

        result = await self._session.execute(
            query.group_by(UserBook.user_id)
            .order_by(desc(func.count(UserBook.id)))
            .limit(limit)
        )

        users = []
        for i, row in enumerate(result.all(), 1):
            users.append(
                {
                    "rank": i,
                    "user_id": str(row.user_id),
                    "books_finished": row.books_finished,
                    "pages_read": row.pages_read or 0,
                    "streak_days": 0,
                }
            )

        return users
