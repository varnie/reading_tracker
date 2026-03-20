from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedError
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency to get current authenticated user from JWT token.

    Raises:
        UnauthorizedError: If token is invalid or missing
    """
    if not credentials:
        raise UnauthorizedError("Authorization header missing")

    token = credentials.credentials

    try:
        payload = decode_token(token)
        user_id = payload.get("sub")

        if not user_id:
            raise UnauthorizedError("Invalid token payload")

        user = await db.get(User, UUID(user_id))

        if not user:
            raise UnauthorizedError("User not found")

        return user

    except Exception as e:
        raise UnauthorizedError("Could not validate credentials") from e
