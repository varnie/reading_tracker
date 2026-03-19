import pytest
from pydantic import ValidationError

from app.features.auth.schemas import (
    UserCreate,
    UserLogin,
    TokenResponse,
)


class TestUserSchemas:
    """Tests for auth schemas."""

    def test_user_create_valid(self):
        """Valid user create should pass."""
        data = UserCreate(
            email="test@example.com",
            password="TestPassword123!",
        )
        assert data.email == "test@example.com"
        assert data.password == "TestPassword123!"

    def test_user_create_invalid_email(self):
        """Invalid email should raise ValidationError."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="not-an-email",
                password="TestPassword123!",
            )

    def test_user_create_short_password(self):
        """Password shorter than 8 chars should raise ValidationError."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                password="short",
            )

    def test_user_create_empty_email(self):
        """Empty email should raise ValidationError."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="",
                password="TestPassword123!",
            )


class TestLoginSchemas:
    """Tests for login schemas."""

    def test_login_valid(self):
        """Valid login should pass."""
        data = UserLogin(
            email="test@example.com",
            password="TestPassword123!",
        )
        assert data.email == "test@example.com"

    def test_login_empty_email(self):
        """Empty email should raise ValidationError."""
        with pytest.raises(ValidationError):
            UserLogin(
                email="",
                password="TestPassword123!",
            )


class TestTokenSchemas:
    """Tests for token schemas."""

    def test_token_response_valid(self):
        """Token response should have all required fields."""
        data = TokenResponse(
            access_token="test-access-token",
            refresh_token="test-refresh-token",
            expires_in=1800,
            token_jti="test-jti",
        )
        assert data.access_token == "test-access-token"
        assert data.token_type == "bearer"
