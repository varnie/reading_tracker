from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Common pagination parameters."""

    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""

    model_config = ConfigDict(from_attributes=True)

    items: list[T]
    total: int
    page: int
    per_page: int
    pages: int


class TimestampSchema(BaseModel):
    """Schema with timestamp fields."""

    model_config = ConfigDict(from_attributes=True)

    created_at: datetime
    updated_at: datetime | None = None


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str
    error_code: str | None = None


class SuccessResponse(BaseModel):
    """Standard success response."""

    success: bool = True
    message: str | None = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str = "0.1.0"
    timestamp: datetime
