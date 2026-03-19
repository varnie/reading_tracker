from uuid import UUID

from sqlalchemy import select, func
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
    ) -> list[ReadingSession]:
        """List all sessions for a user's book."""
        result = await self._session.execute(
            select(ReadingSession)
            .where(ReadingSession.user_book_id == user_book_id)
            .order_by(ReadingSession.started_at.desc())
        )
        return list(result.scalars().all())

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
