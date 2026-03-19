from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import BookStatus
from app.core.exceptions import ConflictError, NotFoundError
from app.features.books.events import BookEvents
from app.features.books.repository import BookRepository
from app.features.books.schemas import BookCreate, BookResponse, BookUpdate
from app.features.catalog.repository import CatalogRepository
from app.shared.events import event_bus


class BookService:
    """Service for user book operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = BookRepository(session)
        self._catalog_repo = CatalogRepository(session)

    async def add_book(
        self,
        user_id: UUID,
        data: BookCreate,
    ) -> BookResponse:
        """
        Add a book from catalog to user's list.

        Raises:
            NotFoundError: If catalog book doesn't exist
            ConflictError: If user already has this book
        """
        catalog_book = await self._catalog_repo.get_by_id(data.catalog_book_id)
        if not catalog_book:
            raise NotFoundError("Book")

        if await self._repo.exists(user_id, data.catalog_book_id):
            raise ConflictError("You already have this book")

        user_book = await self._repo.create(
            user_id=user_id,
            book_id=data.catalog_book_id,
            status=data.status,
        )

        await event_bus.publish(BookEvents.book_added(str(user_id), str(user_book.id)))

        return await self._to_response(user_book)

    async def get_book(self, user_id: UUID, book_id: UUID) -> BookResponse:
        """Get a user's book by ID."""
        user_book = await self._repo.get_by_id(book_id, user_id)
        if not user_book:
            raise NotFoundError("Book")
        return await self._to_response(user_book)

    async def list_books(
        self,
        user_id: UUID,
        status: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[BookResponse], int]:
        """List user's books."""
        books, total = await self._repo.list_by_user(
            user_id, status=status, page=page, per_page=per_page
        )
        responses = [await self._to_response(book) for book in books]
        return responses, total

    async def update_book(
        self,
        user_id: UUID,
        book_id: UUID,
        data: BookUpdate,
    ) -> BookResponse:
        """Update a user's book."""
        user_book = await self._repo.get_by_id(book_id, user_id)
        if not user_book:
            raise NotFoundError("Book")

        update_data = data.model_dump(exclude_unset=True)

        if data.status == BookStatus.READING and not user_book.started_at:
            update_data["started_at"] = datetime.now(UTC)

        if data.status == BookStatus.FINISHED:
            update_data["finished_at"] = datetime.now(UTC)
            update_data["rating"] = data.rating
            await event_bus.publish(
                BookEvents.book_finished(str(user_id), str(user_book.id))
            )

        updated = await self._repo.update(book_id, user_id, **update_data)
        return await self._to_response(updated)

    async def delete_book(self, user_id: UUID, book_id: UUID) -> None:
        """Delete a user's book."""
        deleted = await self._repo.delete(book_id, user_id)
        if not deleted:
            raise NotFoundError("Book")
        await event_bus.publish(BookEvents.book_deleted(str(user_id), str(book_id)))

    async def _to_response(self, user_book) -> BookResponse:
        """Convert UserBook model to response."""
        from sqlalchemy import select

        from app.models.book import Book

        result = await self._session.execute(
            select(Book).where(Book.id == user_book.book_id)
        )
        catalog_book = result.scalar_one()

        return BookResponse(
            id=user_book.id,
            catalog_book_id=user_book.book_id,
            status=user_book.status,
            pages_read=user_book.pages_read,
            rating=user_book.rating,
            started_at=user_book.started_at.isoformat()
            if user_book.started_at
            else None,
            finished_at=user_book.finished_at.isoformat()
            if user_book.finished_at
            else None,
            added_at=user_book.added_at.isoformat(),
            book_title=catalog_book.title,
            book_author=catalog_book.author,
            book_pages_total=catalog_book.pages_total,
        )
