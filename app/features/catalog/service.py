from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AlreadyExistsError
from app.features.catalog.repository import CatalogRepository
from app.features.catalog.schemas import CatalogBookCreate, CatalogBookResponse


class CatalogService:
    """Service for catalog operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = CatalogRepository(session)

    async def create_book(
        self,
        user_id: UUID,
        data: CatalogBookCreate,
    ) -> CatalogBookResponse:
        """Create a new book in catalog."""
        if data.isbn and await self._repo.isbn_exists(data.isbn):
            raise AlreadyExistsError("Book with this ISBN")

        book = await self._repo.create(
            title=data.title,
            author=data.author,
            pages_total=data.pages_total,
            created_by_user_id=user_id,
            isbn=data.isbn,
            description=data.description,
        )

        return CatalogBookResponse(
            id=book.id,
            title=book.title,
            author=book.author,
            isbn=book.isbn,
            description=book.description,
            pages_total=book.pages_total,
            created_at=book.created_at.isoformat(),
            created_by_user_id=str(book.created_by_user_id),
        )

    async def search_books(
        self,
        query: str | None = None,
        author: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[CatalogBookResponse], int]:
        """Search catalog books."""
        books, total = await self._repo.search(
            query=query,
            author=author,
            page=page,
            per_page=per_page,
        )

        responses = [
            CatalogBookResponse(
                id=book.id,
                title=book.title,
                author=book.author,
                isbn=book.isbn,
                description=book.description,
                pages_total=book.pages_total,
                created_at=book.created_at.isoformat(),
                created_by_user_id=str(book.created_by_user_id),
            )
            for book in books
        ]

        return responses, total

    async def get_popular(
        self,
        limit: int = 10,
    ) -> list[CatalogBookResponse]:
        """Get popular catalog books."""
        books = await self._repo.get_popular(limit=limit)

        return [
            CatalogBookResponse(
                id=book.id,
                title=book.title,
                author=book.author,
                isbn=book.isbn,
                description=book.description,
                pages_total=book.pages_total,
                created_at=book.created_at.isoformat(),
                created_by_user_id=str(book.created_by_user_id),
            )
            for book in books
        ]
