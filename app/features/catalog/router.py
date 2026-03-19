
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.dependencies import get_db, get_current_user
from app.models.user import User
from app.features.catalog.schemas import (
    CatalogBookCreate,
    CatalogBookResponse,
    CatalogBookListResponse,
)
from app.features.catalog.service import CatalogService
from app.features.catalog.events import CatalogEvents
from app.shared.events import event_bus


router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get(
    "",
    response_model=CatalogBookListResponse,
    summary="Search catalog",
)
async def search_catalog(
    query: str | None = Query(default=None, description="Search by title"),
    author: str | None = Query(default=None, description="Filter by author"),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
) -> CatalogBookListResponse:
    """Search books in catalog."""
    service = CatalogService(session)
    books, total = await service.search_books(
        query=query,
        author=author,
        page=page,
        per_page=per_page,
    )

    pages = (total + per_page - 1) // per_page if total > 0 else 1

    return CatalogBookListResponse(
        items=books,
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


@router.get(
    "/popular",
    response_model=list[CatalogBookResponse],
    summary="Get popular books",
)
async def get_popular_books(
    limit: int = Query(default=10, ge=1, le=50),
    session: AsyncSession = Depends(get_db),
) -> list[CatalogBookResponse]:
    """Get most popular books in catalog."""
    service = CatalogService(session)
    return await service.get_popular(limit=limit)


@router.post(
    "",
    response_model=CatalogBookResponse,
    status_code=201,
    summary="Add book to catalog",
)
async def create_catalog_book(
    data: CatalogBookCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> CatalogBookResponse:
    """Add a new book to catalog."""
    service = CatalogService(session)
    book = await service.create_book(user.id, data)

    await event_bus.publish(
        CatalogEvents.book_added_to_catalog(str(book.id), str(user.id))
    )

    return book
