from uuid import UUID

from pydantic import BaseModel, Field

from app.core.enums import BookStatus


class BookCreate(BaseModel):
    """Schema for adding a book to user's list."""

    catalog_book_id: UUID
    status: BookStatus = Field(default=BookStatus.WANT_TO_READ)


class BookUpdate(BaseModel):
    """Schema for updating a user's book."""

    status: BookStatus | None = None
    pages_read: int | None = Field(default=None, ge=0)
    rating: int | None = Field(default=None, ge=1, le=5)


class BookResponse(BaseModel):
    """Schema for book response."""

    model_config = {"from_attributes": True}

    id: UUID
    catalog_book_id: UUID
    status: str
    pages_read: int
    rating: int | None
    started_at: str | None
    finished_at: str | None
    added_at: str
    book_title: str
    book_author: str
    book_pages_total: int


class BookListResponse(BaseModel):
    """Schema for paginated book list response."""

    items: list[BookResponse]
    total: int
    page: int
    per_page: int
    pages: int
