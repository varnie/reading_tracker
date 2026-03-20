from uuid import UUID

from pydantic import BaseModel, Field

from app.shared.schemas import PaginatedResponse


class CatalogBookCreate(BaseModel):
    """Schema for creating a book in catalog."""

    title: str = Field(min_length=1, max_length=255)
    author: str = Field(min_length=1, max_length=255)
    isbn: str | None = Field(default=None, max_length=20)
    description: str | None = None
    pages_total: int = Field(gt=0)


class CatalogBookResponse(BaseModel):
    """Schema for catalog book response."""

    model_config = {"from_attributes": True}

    id: UUID
    title: str
    author: str
    isbn: str | None
    description: str | None
    pages_total: int
    created_at: str
    created_by_user_id: str


CatalogBookListResponse = PaginatedResponse[CatalogBookResponse]
