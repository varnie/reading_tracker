import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHash

from app.core.config import settings


argon2_hasher = PasswordHasher(
    memory_cost=settings.argon2_memory_cost,
    time_cost=settings.argon2_time_cost,
    parallelism=settings.argon2_parallelism,
)


def hash_password(password: str) -> str:
    """Hash a password using Argon2."""
    return argon2_hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a password against its hash.

    Returns True if password matches, False otherwise.
    """
    try:
        argon2_hasher.verify(hashed, password)
        return True
    except (VerifyMismatchError, InvalidHash):
        return False


def create_access_token(
    subject: str | UUID,
    expires_delta: timedelta | None = None,
) -> tuple[str, str]:
    """
    Create a JWT access token.

    Returns tuple of (token, jti).
    """
    if isinstance(subject, UUID):
        subject = str(subject)

    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.access_token_lifetime_minutes
        )

    jti = secrets.token_hex(16)

    payload = {
        "sub": subject,
        "jti": jti,
        "exp": expire,
        "type": "access",
    }

    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    return token, jti


def decode_token(token: str) -> dict[str, Any]:
    """Decode and verify a JWT token."""
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )


def create_refresh_token() -> str:
    """Create a refresh token string."""
    return secrets.token_urlsafe(64)


def hash_token(token: str) -> str:
    """Hash a token for storage."""
    import hashlib

    return hashlib.sha256(token.encode()).hexdigest()
