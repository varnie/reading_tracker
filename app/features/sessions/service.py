from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.features.books.events import BookEvents
from app.features.books.repository import BookRepository
from app.features.sessions.repository import SessionRepository
from app.features.sessions.schemas import SessionCreate, SessionResponse
from app.shared.events import event_bus


class SessionService:
    """Service for reading session operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = SessionRepository(session)
        self._book_repo = BookRepository(session)

    async def create_session(
        self,
        user_id: UUID,
        book_id: UUID,
        data: SessionCreate,
    ) -> SessionResponse:
        """Create a new reading session for a book."""
        user_book = await self._book_repo.get_by_id(book_id, user_id)
        if not user_book:
            raise NotFoundError("Book")

        reading_session = await self._repo.create(
            user_book_id=book_id,
            pages_read=data.pages_read,
            notes=data.notes,
        )

        user_book.pages_read += data.pages_read
        await self._session.flush()

        await event_bus.publish(
            BookEvents.session_created(
                str(user_id),
                str(book_id),
                str(reading_session.id),
            )
        )

        return SessionResponse(
            id=reading_session.id,
            user_book_id=reading_session.user_book_id,
            pages_read=reading_session.pages_read,
            started_at=reading_session.started_at.isoformat(),
            ended_at=reading_session.ended_at.isoformat()
            if reading_session.ended_at
            else None,
            notes=reading_session.notes,
        )

    async def list_sessions(
        self,
        user_id: UUID,
        book_id: UUID,
    ) -> list[SessionResponse]:
        """List all sessions for a user's book."""
        user_book = await self._book_repo.get_by_id(book_id, user_id)
        if not user_book:
            raise NotFoundError("Book")

        sessions = await self._repo.list_by_user_book(book_id)

        return [
            SessionResponse(
                id=s.id,
                user_book_id=s.user_book_id,
                pages_read=s.pages_read,
                started_at=s.started_at.isoformat(),
                ended_at=s.ended_at.isoformat() if s.ended_at else None,
                notes=s.notes,
            )
            for s in sessions
        ]
