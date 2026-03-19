import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.features.auth.repository import UserRepository, RefreshTokenRepository


class TestUserRepository:
    """Tests for UserRepository."""

    @pytest.fixture
    def mock_session(self):
        """Create mock session."""
        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_create(self, mock_session):
        """Should create user."""
        repo = UserRepository(mock_session)

        await repo.create("test@example.com", "hashed_password")

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_email(self, mock_session):
        """Should get user by email."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = UserRepository(mock_session)
        result = await repo.get_by_email("test@example.com")

        assert result is None

    @pytest.mark.asyncio
    async def test_email_exists_true(self, mock_session):
        """Should return True if email exists."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = uuid4()
        mock_session.execute.return_value = mock_result

        repo = UserRepository(mock_session)
        result = await repo.email_exists("test@example.com")

        assert result is True


class TestRefreshTokenRepository:
    """Tests for RefreshTokenRepository."""

    @pytest.fixture
    def mock_session(self):
        """Create mock session."""
        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_create(self, mock_session):
        """Should create refresh token."""
        repo = RefreshTokenRepository(mock_session)
        user_id = uuid4()

        await repo.create(user_id, "token_hash", None)

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_token_hash(self, mock_session):
        """Should get token by hash."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = RefreshTokenRepository(mock_session)
        result = await repo.get_by_token_hash("some_hash")

        assert result is None
