from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.dependencies import get_db, get_current_user
from app.models.user import User
from app.features.sessions.schemas import (
    SessionCreate,
    SessionResponse,
    SessionListResponse,
)
from app.features.sessions.service import SessionService
from uuid import UUID


router = APIRouter(tags=["sessions"])


@router.get(
    "/books/{book_id}/sessions",
    response_model=SessionListResponse,
    summary="List book sessions",
)
async def list_sessions(
    book_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> SessionListResponse:
    """List all reading sessions for a book."""
    service = SessionService(session)
    sessions = await service.list_sessions(user.id, book_id)

    return SessionListResponse(
        items=sessions,
        total=len(sessions),
    )


@router.post(
    "/books/{book_id}/sessions",
    response_model=SessionResponse,
    status_code=201,
    summary="Create reading session",
)
async def create_session(
    book_id: UUID,
    data: SessionCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> SessionResponse:
    """Create a new reading session for a book."""
    service = SessionService(session)
    return await service.create_session(user.id, book_id, data)
