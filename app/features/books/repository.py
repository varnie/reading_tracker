from uuid import UUID

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_book import UserBook


class BookRepository:
    """Repository for UserBook data access."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        user_id: UUID,
        book_id: UUID,
        status: str = "want_to_read",
    ) -> UserBook:
        """Create a new user book entry."""
        user_book = UserBook(
            user_id=user_id,
            book_id=book_id,
            status=status,
        )
        self._session.add(user_book)
        await self._session.flush()
        await self._session.refresh(user_book)
        return user_book

    async def get_by_id(self, book_id: UUID, user_id: UUID) -> UserBook | None:
        """Get user book by ID."""
        result = await self._session.execute(
            select(UserBook).where(
                UserBook.id == book_id,
                UserBook.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: UUID,
        status: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[UserBook], int]:
        """List user's books with optional status filter."""
        query = select(UserBook).where(UserBook.user_id == user_id)
        count_query = select(UserBook.id).where(UserBook.user_id == user_id)

        if status:
            query = query.where(UserBook.status == status)
            count_query = count_query.where(UserBook.status == status)

        query = query.offset((page - 1) * per_page).limit(per_page)

        result = await self._session.execute(query)
        count_result = await self._session.execute(count_query)

        items = list(result.scalars().all())
        total = len(list(count_result.scalars().all()))

        return items, total

    async def update(
        self,
        book_id: UUID,
        user_id: UUID,
        **kwargs,
    ) -> UserBook | None:
        """Update user book."""
        await self._session.execute(
            update(UserBook)
            .where(UserBook.id == book_id, UserBook.user_id == user_id)
            .values(**kwargs)
        )
        await self._session.flush()
        return await self.get_by_id(book_id, user_id)

    async def delete(self, book_id: UUID, user_id: UUID) -> bool:
        """Delete user book."""
        result = await self._session.execute(
            delete(UserBook).where(
                UserBook.id == book_id,
                UserBook.user_id == user_id,
            )
        )
        return result.rowcount > 0

    async def exists(self, user_id: UUID, book_id: UUID) -> bool:
        """Check if user already has this book."""
        result = await self._session.execute(
            select(UserBook.id).where(
                UserBook.user_id == user_id,
                UserBook.book_id == book_id,
            )
        )
        return result.scalar_one_or_none() is not None
