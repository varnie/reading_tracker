import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.features.auth.service import AuthService


class TestAuthService:
    """Tests for AuthService."""

    @pytest.fixture
    def mock_session(self):
        """Create mock session."""
        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.execute = AsyncMock()

        async def mock_refresh(obj, **kwargs):
            obj.id = uuid4()
            obj.created_at = datetime.utcnow()
            obj.updated_at = datetime.utcnow()

        session.refresh = mock_refresh
        return session

    @pytest.mark.asyncio
    async def test_register_success(self, mock_session):
        """Should register user successfully."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        service = AuthService(mock_session)

        user = await service.register("test@example.com", "Password123!")

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, mock_session):
        """Should raise error for duplicate email."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = True
        mock_session.execute.return_value = mock_result

        service = AuthService(mock_session)

        from app.core.exceptions import AlreadyExistsError

        with pytest.raises(AlreadyExistsError):
            await service.register("test@example.com", "Password123!")
