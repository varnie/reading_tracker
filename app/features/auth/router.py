import logging
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, Header, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import UnauthorizedError
from app.core.redis import TokenBlacklist, get_blacklist
from app.features.auth.schemas import (
    LogoutResponse,
    RefreshTokenResponse,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.features.auth.service import AuthService
from app.middleware.rate_limit import auth_limiter
from app.shared.dependencies import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=201,
    summary="Register a new user",
    dependencies=[Depends(auth_limiter)],
)
async def register(
    data: UserCreate,
    session: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Register a new user account."""
    service = AuthService(session)
    return await service.register(data.email, data.password)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login user",
    dependencies=[Depends(auth_limiter)],
)
async def login(
    data: UserLogin,
    response: Response,
    session: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Login and receive access and refresh tokens."""
    service = AuthService(session)
    tokens = await service.login(data.email, data.password)

    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings.refresh_token_lifetime_days * 24 * 60 * 60,
    )

    return tokens


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    summary="Refresh access token",
)
async def refresh_token(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    session: AsyncSession = Depends(get_db),
) -> RefreshTokenResponse:
    """Refresh access token using refresh token from cookie."""
    if not refresh_token:
        raise UnauthorizedError("No refresh token")

    service = AuthService(session)
    tokens = await service.refresh(refresh_token)

    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings.refresh_token_lifetime_days * 24 * 60 * 60,
    )

    return tokens


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Logout user",
)
async def logout(
    response: Response,
    authorization: str | None = Header(default=None),
    refresh_token: str | None = Cookie(default=None),
    session: AsyncSession = Depends(get_db),
    blacklist: TokenBlacklist = Depends(get_blacklist),
) -> LogoutResponse:
    """Logout user and invalidate tokens."""
    from app.core.security import decode_token

    if authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer ") :].strip()
        try:
            payload = decode_token(token)
            user_id = UUID(payload["sub"])
            service = AuthService(session, blacklist)
            await service.logout(user_id, token)
        except Exception:
            logger.warning("Failed to blacklist token during logout")

    response.delete_cookie("refresh_token")

    return LogoutResponse()
