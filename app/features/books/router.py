from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.dependencies import get_db, get_current_user
from app.models.user import User

from app.features.books.schemas import (
    BookCreate,
    BookUpdate,
    BookResponse,
    BookListResponse,
)
from app.features.books.service import BookService


router = APIRouter(prefix="/books", tags=["books"])


@router.get(
    "",
    response_model=BookListResponse,
    summary="List user's books",
)
async def list_books(
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> BookListResponse:
    """List user's books with optional status filter."""
    service = BookService(session)
    books, total = await service.list_books(
        user_id=user.id,
        status=status,
        page=page,
        per_page=per_page,
    )

    pages = (total + per_page - 1) // per_page if total > 0 else 1

    return BookListResponse(
        items=books,
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


@router.post(
    "",
    response_model=BookResponse,
    status_code=201,
    summary="Add book to user's list",
)
async def add_book(
    data: BookCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> BookResponse:
    """Add a book from catalog to user's reading list."""
    service = BookService(session)
    return await service.add_book(user.id, data)


@router.get(
    "/{book_id}",
    response_model=BookResponse,
    summary="Get book details",
)
async def get_book(
    book_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> BookResponse:
    """Get details of a specific user's book."""
    service = BookService(session)
    return await service.get_book(user.id, book_id)


@router.patch(
    "/{book_id}",
    response_model=BookResponse,
    summary="Update book",
)
async def update_book(
    book_id: UUID,
    data: BookUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> BookResponse:
    """Update a user's book (status, pages read, rating)."""
    service = BookService(session)
    return await service.update_book(user.id, book_id, data)


@router.delete(
    "/{book_id}",
    status_code=204,
    summary="Delete book",
)
async def delete_book(
    book_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    """Remove a book from user's list."""
    service = BookService(session)
    await service.delete_book(user.id, book_id)
