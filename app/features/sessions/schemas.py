from uuid import UUID

from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    """Schema for creating a reading session."""

    pages_read: int = Field(gt=0)
    notes: str | None = None


class SessionUpdate(BaseModel):
    """Schema for updating a reading session."""

    ended_at: str | None = None
    pages_read: int | None = Field(default=None, gt=0)
    notes: str | None = None


class SessionResponse(BaseModel):
    """Schema for reading session response."""

    model_config = {"from_attributes": True}

    id: UUID
    user_book_id: UUID
    pages_read: int
    started_at: str
    ended_at: str | None
    notes: str | None


class SessionListResponse(BaseModel):
    """Schema for session list response."""

    items: list[SessionResponse]
    total: int
