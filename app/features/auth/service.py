from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    hash_token,
    decode_token,
)
from app.core.exceptions import (
    AlreadyExistsError,
    InvalidCredentialsError,
    TokenExpiredError,
    UnauthorizedError,
)
from app.core.redis import TokenBlacklist, get_redis
from app.features.auth.repository import UserRepository, RefreshTokenRepository
from app.features.auth.schemas import (
    TokenResponse,
    RefreshTokenResponse,
    UserResponse,
)
from app.features.auth.events import AuthEvents
from app.shared.events import event_bus


class AuthService:
    """Service for authentication operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._user_repo = UserRepository(session)
        self._token_repo = RefreshTokenRepository(session)

    async def register(self, email: str, password: str) -> UserResponse:
        """
        Register a new user.

        Args:
            email: User email
            password: Plain text password

        Returns:
            Created user response

        Raises:
            AlreadyExistsError: If email already registered
        """
        if await self._user_repo.email_exists(email):
            raise AlreadyExistsError("Email already registered")

        password_hash = hash_password(password)
        user = await self._user_repo.create(email, password_hash)

        await event_bus.publish(AuthEvents.user_registered(str(user.id), user.email))

        return UserResponse(
            id=user.id,
            email=user.email,
            created_at=user.created_at.isoformat(),
        )

    async def login(self, email: str, password: str) -> TokenResponse:
        """
        Authenticate user and return tokens.

        Args:
            email: User email
            password: Plain text password

        Returns:
            Token response with access and refresh tokens

        Raises:
            InvalidCredentialsError: If credentials are invalid
        """
        user = await self._user_repo.get_by_email(email)

        if not user or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError()

        await event_bus.publish(AuthEvents.user_logged_in(str(user.id)))

        return await self._create_tokens(user.id)

    async def refresh(self, refresh_token: str) -> RefreshTokenResponse:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: The refresh token from cookie

        Returns:
            New access token response

        Raises:
            UnauthorizedError: If refresh token is invalid or revoked
        """
        token_hash = hash_token(refresh_token)
        stored_token = await self._token_repo.get_by_token_hash(token_hash)

        if not stored_token:
            raise UnauthorizedError("Invalid refresh token")

        if stored_token.revoked:
            raise UnauthorizedError("Refresh token has been revoked")

        if stored_token.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
            raise TokenExpiredError()

        await self._token_repo.revoke(stored_token.id)

        access_token, jti = create_access_token(str(stored_token.user_id))

        return RefreshTokenResponse(
            access_token=access_token,
            expires_in=settings.access_token_lifetime_minutes * 60,
            token_jti=jti,
        )

    async def logout(self, user_id: UUID, access_token: str) -> None:
        """
        Logout user by invalidating tokens.

        Args:
            user_id: User ID from token
            access_token: The access token to blacklist
        """
        try:
            payload = decode_token(access_token)
            jti = payload.get("jti")
            exp = payload.get("exp")

            if jti and exp:
                ttl = int(exp - datetime.now(UTC).timestamp())
                if ttl > 0:
                    redis_client = await get_redis()
                    blacklist = TokenBlacklist(redis_client)
                    await blacklist.blacklist_token(jti, ttl)

        except Exception:
            pass

        await self._token_repo.revoke_all_for_user(user_id)
        await event_bus.publish(AuthEvents.user_logged_out(str(user_id)))

    async def _create_tokens(self, user_id: UUID) -> TokenResponse:
        """Create access and refresh tokens for a user."""
        access_token, jti = create_access_token(str(user_id))

        refresh_token = create_refresh_token()
        token_hash = hash_token(refresh_token)
        expires_at = datetime.now(UTC) + timedelta(
            days=settings.refresh_token_lifetime_days
        )

        await self._token_repo.create(user_id, token_hash, expires_at)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_lifetime_minutes * 60,
            token_jti=jti,
        )
