import pytest
from datetime import timedelta
from uuid import uuid4

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
    create_refresh_token,
    hash_token,
)


class TestPasswordHashing:
    """Tests for Argon2 password hashing."""

    def test_hash_password_returns_string(self):
        """Hash password should return a string."""
        password = "TestPassword123!"
        hashed = hash_password(password)
        assert isinstance(hashed, str)
        assert hashed != password

    def test_hash_password_different_each_time(self):
        """Hashes should be different due to salt."""
        password = "TestPassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Verify should return True for correct password."""
        password = "TestPassword123!"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Verify should return False for incorrect password."""
        password = "TestPassword123!"
        wrong_password = "WrongPassword456!"
        hashed = hash_password(password)
        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_empty_password(self):
        """Verify should return False for empty password."""
        hashed = hash_password("TestPassword123!")
        assert verify_password("", hashed) is False


class TestJWTTokens:
    """Tests for JWT token creation and verification."""

    def test_create_access_token_returns_tuple(self):
        """Access token should return tuple of (token, jti)."""
        user_id = str(uuid4())
        token, jti = create_access_token(user_id)
        assert isinstance(token, str)
        assert isinstance(jti, str)
        assert len(token) > 0
        assert len(jti) == 32

    def test_create_access_token_with_expiry(self):
        """Access token with custom expiry."""
        user_id = str(uuid4())
        expires = timedelta(minutes=60)
        token, jti = create_access_token(user_id, expires_delta=expires)
        assert isinstance(token, str)

    def test_decode_token_returns_dict(self):
        """Decode token should return payload dict."""
        user_id = str(uuid4())
        token, _ = create_access_token(user_id)
        payload = decode_token(token)
        assert isinstance(payload, dict)
        assert payload["sub"] == user_id
        assert payload["type"] == "access"
        assert "jti" in payload
        assert "exp" in payload

    def test_decode_token_invalid(self):
        """Decode should raise for invalid token."""
        with pytest.raises(Exception):
            decode_token("invalid.token.here")


class TestRefreshToken:
    """Tests for refresh token."""

    def test_create_refresh_token_returns_string(self):
        """Refresh token should be a string."""
        token = create_refresh_token()
        assert isinstance(token, str)
        assert len(token) > 32

    def test_refresh_token_deterministic(self):
        """Different calls should create different tokens."""
        token1 = create_refresh_token()
        token2 = create_refresh_token()
        assert token1 != token2


class TestTokenHashing:
    """Tests for token hashing."""

    def test_hash_token_returns_string(self):
        """Hash token should return hex string."""
        token = create_refresh_token()
        hashed = hash_token(token)
        assert isinstance(hashed, str)
        assert len(hashed) == 64  # SHA256 hex

    def test_hash_token_deterministic(self):
        """Same token should always hash to same value."""
        token = "test-token"
        hash1 = hash_token(token)
        hash2 = hash_token(token)
        assert hash1 == hash2

    def test_hash_token_different_inputs(self):
        """Different tokens should hash differently."""
        hash1 = hash_token("token1")
        hash2 = hash_token("token2")
        assert hash1 != hash2
