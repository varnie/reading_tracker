from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for user registration."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response."""

    model_config = {"from_attributes": True}

    id: UUID
    email: str
    created_at: str


class TokenResponse(BaseModel):
    """Schema for token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    token_jti: str


class RefreshTokenResponse(BaseModel):
    """Schema for refresh token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    token_jti: str


class LogoutResponse(BaseModel):
    """Schema for logout response."""

    success: bool = True
    message: str = "Logged out successfully"


class MessageResponse(BaseModel):
    """Schema for generic message response."""

    message: str
