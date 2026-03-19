from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, RefreshToken


class UserRepository:
    """Repository for User data access."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, email: str, password_hash: str) -> User:
        """Create a new user."""
        user = User(email=email, password_hash=password_hash)
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def get_by_id(self, user_id: UUID) -> User | None:
        """Get user by ID."""
        result = await self._session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email."""
        result = await self._session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        """Check if email already exists."""
        result = await self._session.execute(select(User.id).where(User.email == email))
        return result.scalar_one_or_none() is not None


class RefreshTokenRepository:
    """Repository for RefreshToken data access."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        user_id: UUID,
        token_hash: str,
        expires_at,
    ) -> RefreshToken:
        """Create a new refresh token."""
        token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self._session.add(token)
        await self._session.flush()
        await self._session.refresh(token)
        return token

    async def get_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        """Get refresh token by its hash."""
        result = await self._session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def revoke(self, token_id: UUID) -> None:
        """Revoke a refresh token."""
        await self._session.execute(
            update(RefreshToken).where(RefreshToken.id == token_id).values(revoked=True)
        )

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        """Revoke all refresh tokens for a user."""
        await self._session.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .values(revoked=True)
        )
