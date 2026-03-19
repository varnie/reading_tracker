from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import not_

from app.models.book import Book


class CatalogRepository:
    """Repository for Book (catalog) data access."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        title: str,
        author: str,
        pages_total: int,
        created_by_user_id: UUID,
        isbn: str | None = None,
        description: str | None = None,
    ) -> Book:
        """Create a new catalog book."""
        book = Book(
            title=title,
            author=author,
            pages_total=pages_total,
            created_by_user_id=created_by_user_id,
            isbn=isbn,
            description=description,
        )
        self._session.add(book)
        await self._session.flush()
        await self._session.refresh(book)
        return book

    async def get_by_id(self, book_id: UUID) -> Book | None:
        """Get catalog book by ID."""
        result = await self._session.execute(
            select(Book).where(Book.id == book_id, not_(Book.is_deleted))
        )
        return result.scalar_one_or_none()

    async def search(
        self,
        query: str | None = None,
        author: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Book], int]:
        """Search catalog books."""
        base_query = select(Book).where(not_(Book.is_deleted))
        count_query = select(func.count(Book.id)).where(not_(Book.is_deleted))

        if query:
            search_filter = Book.title.ilike(f"%{query}%")
            base_query = base_query.where(search_filter)
            count_query = count_query.where(search_filter)

        if author:
            author_filter = Book.author.ilike(f"%{author}%")
            base_query = base_query.where(author_filter)
            count_query = count_query.where(author_filter)

        base_query = base_query.offset((page - 1) * per_page).limit(per_page)

        result = await self._session.execute(base_query)
        count_result = await self._session.execute(count_query)

        items = list(result.scalars().all())
        total = count_result.scalar()

        return items, total

    async def get_popular(
        self,
        limit: int = 10,
    ) -> list[Book]:
        """Get popular books (most added by users)."""
        from sqlalchemy import desc

        from app.models.user_book import UserBook

        result = await self._session.execute(
            select(Book)
            .join(UserBook, Book.id == UserBook.book_id)
            .where(not_(Book.is_deleted))
            .group_by(Book.id)
            .order_by(desc(func.count(UserBook.id)))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def isbn_exists(self, isbn: str) -> bool:
        """Check if ISBN already exists."""
        result = await self._session.execute(
            select(Book.id).where(Book.isbn == isbn, not_(Book.is_deleted))
        )
        return result.scalar_one_or_none() is not None
