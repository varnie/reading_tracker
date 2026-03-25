from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.features.books.events import BookEvents
from app.features.books.repository import BookRepository
from app.features.sessions.repository import SessionRepository
from app.features.sessions.schemas import SessionCreate, SessionResponse, SessionUpdate
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
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[SessionResponse], int]:
        """List all sessions for a user's book with pagination."""
        user_book = await self._book_repo.get_by_id(book_id, user_id)
        if not user_book:
            raise NotFoundError("Book")

        sessions, total = await self._repo.list_by_user_book(
            book_id, page=page, per_page=per_page
        )

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
        ], total

    async def update_session(
        self,
        user_id: UUID,
        book_id: UUID,
        session_id: UUID,
        data: SessionUpdate,
    ) -> SessionResponse:
        """Update a reading session."""
        user_book = await self._book_repo.get_by_id(book_id, user_id)
        if not user_book:
            raise NotFoundError("Book")

        existing_session = await self._repo.get_by_id(session_id)
        if not existing_session or existing_session.user_book_id != book_id:
            raise NotFoundError("Session")

        old_pages = existing_session.pages_read

        update_data = data.model_dump(exclude_unset=True)
        if update_data.get("ended_at"):
            update_data["ended_at"] = datetime.fromisoformat(
                update_data["ended_at"].replace("Z", "+00:00")
            )

        updated = await self._repo.update(session_id, **update_data)

        if "pages_read" in update_data and update_data["pages_read"] != old_pages:
            pages_diff = update_data["pages_read"] - old_pages
            user_book.pages_read += pages_diff
            await self._session.flush()

        return SessionResponse(
            id=updated.id,
            user_book_id=updated.user_book_id,
            pages_read=updated.pages_read,
            started_at=updated.started_at.isoformat(),
            ended_at=updated.ended_at.isoformat() if updated.ended_at else None,
            notes=updated.notes,
        )

    async def delete_session(
        self,
        user_id: UUID,
        book_id: UUID,
        session_id: UUID,
    ) -> None:
        """Delete a reading session."""
        user_book = await self._book_repo.get_by_id(book_id, user_id)
        if not user_book:
            raise NotFoundError("Book")

        existing_session = await self._repo.get_by_id(session_id)
        if not existing_session or existing_session.user_book_id != book_id:
            raise NotFoundError("Session")

        pages_to_subtract = existing_session.pages_read
        deleted = await self._repo.delete(session_id)

        if deleted:
            user_book.pages_read = max(0, user_book.pages_read - pages_to_subtract)
            await self._session.flush()
