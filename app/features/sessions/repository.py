from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reading_session import ReadingSession


class SessionRepository:
    """Repository for ReadingSession data access."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        user_book_id: UUID,
        pages_read: int,
        notes: str | None = None,
    ) -> ReadingSession:
        """Create a new reading session."""
        session = ReadingSession(
            user_book_id=user_book_id,
            pages_read=pages_read,
            notes=notes,
        )
        self._session.add(session)
        await self._session.flush()
        await self._session.refresh(session)
        return session

    async def get_by_id(self, session_id: UUID) -> ReadingSession | None:
        """Get session by ID."""
        result = await self._session.execute(
            select(ReadingSession).where(ReadingSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def list_by_user_book(
        self,
        user_book_id: UUID,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[ReadingSession], int]:
        """List all sessions for a user's book with pagination."""
        query = (
            select(ReadingSession)
            .where(ReadingSession.user_book_id == user_book_id)
            .order_by(ReadingSession.started_at.desc())
        )

        count_query = select(ReadingSession.id).where(
            ReadingSession.user_book_id == user_book_id
        )

        query = query.offset((page - 1) * per_page).limit(per_page)

        result = await self._session.execute(query)
        count_result = await self._session.execute(count_query)

        items = list(result.scalars().all())
        total = len(list(count_result.scalars().all()))

        return items, total

    async def update(
        self,
        session_id: UUID,
        **kwargs,
    ) -> ReadingSession | None:
        """Update a session."""
        from sqlalchemy import update as sql_update

        await self._session.execute(
            sql_update(ReadingSession)
            .where(ReadingSession.id == session_id)
            .values(**kwargs)
        )
        await self._session.flush()
        return await self.get_by_id(session_id)
