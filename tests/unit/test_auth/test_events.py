from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


class TestAuthEvents:
    """Tests for AuthEvents."""

    def test_user_registered_event(self):
        """Should create user_registered event."""
        from app.features.auth.events import AuthEvents

        event = AuthEvents.user_registered("user-123", "test@example.com")

        assert event.name == "auth.user_registered"
        assert event.data["user_id"] == "user-123"
        assert event.data["email"] == "test@example.com"
        assert event.metadata["source"] == "auth"

    def test_user_logged_in_event(self):
        """Should create user_logged_in event."""
        from app.features.auth.events import AuthEvents

        event = AuthEvents.user_logged_in("user-456")

        assert event.name == "auth.user_logged_in"
        assert event.data["user_id"] == "user-456"
        assert event.metadata["source"] == "auth"

    def test_user_logged_out_event(self):
        """Should create user_logged_out event."""
        from app.features.auth.events import AuthEvents

        event = AuthEvents.user_logged_out("user-789")

        assert event.name == "auth.user_logged_out"
        assert event.data["user_id"] == "user-789"
        assert event.metadata["source"] == "auth"


class TestAuthServiceEvents:
    """Tests for AuthService event emissions."""

    async def test_register_emits_user_registered_event(self):
        """register() should emit user_registered event."""
        from app.features.auth.service import AuthService

        mock_session = AsyncMock()

        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_user.email = "new@example.com"
        mock_user.created_at.isoformat.return_value = "2024-01-01T00:00:00"

        mock_repo = AsyncMock()
        mock_repo.email_exists.return_value = False
        mock_repo.create.return_value = mock_user

        with (
            patch("app.features.auth.service.UserRepository", return_value=mock_repo),
            patch("app.features.auth.service.RefreshTokenRepository"),
            patch("app.features.auth.service.event_bus") as mock_bus,
        ):
            mock_bus.publish = AsyncMock()

            service = AuthService(mock_session)
            service._user_repo = mock_repo

            await service.register("new@example.com", "password123")

            mock_bus.publish.assert_called_once()
            call_args = mock_bus.publish.call_args[0][0]
            assert call_args.name == "auth.user_registered"

    async def test_login_emits_user_logged_in_event(self):
        """login() should emit user_logged_in event."""
        from app.core.security import hash_password
        from app.features.auth.service import AuthService

        mock_session = AsyncMock()

        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_user.email = "login@example.com"
        mock_user.password_hash = hash_password("password123")

        mock_repo = AsyncMock()
        mock_repo.get_by_email.return_value = mock_user

        with (
            patch("app.features.auth.service.UserRepository", return_value=mock_repo),
            patch(
                "app.features.auth.service.RefreshTokenRepository"
            ) as mock_token_repo_cls,
            patch("app.features.auth.service.event_bus") as mock_bus,
        ):
            mock_token_repo = AsyncMock()
            mock_token_repo_cls.return_value = mock_token_repo
            mock_bus.publish = AsyncMock()

            service = AuthService(mock_session)
            service._user_repo = mock_repo
            service._token_repo = mock_token_repo

            await service.login("login@example.com", "password123")

            mock_bus.publish.assert_called()
            call_args = mock_bus.publish.call_args[0][0]
            assert call_args.name == "auth.user_logged_in"

    async def test_logout_emits_user_logged_out_event(self):
        """logout() should emit user_logged_out event."""
        from app.core.security import create_access_token
        from app.features.auth.service import AuthService

        mock_session = AsyncMock()

        mock_token_repo = AsyncMock()
        mock_token_repo.revoke_all_for_user = AsyncMock()

        with (
            patch(
                "app.features.auth.service.RefreshTokenRepository",
                return_value=mock_token_repo,
            ),
            patch("app.features.auth.service.get_redis") as mock_get_redis,
        ):
            mock_redis = AsyncMock()
            mock_get_redis.return_value = mock_redis

            with patch(
                "app.features.auth.service.TokenBlacklist"
            ) as mock_blacklist_cls:
                mock_blacklist = AsyncMock()
                mock_blacklist_cls.return_value = mock_blacklist

                with patch("app.features.auth.service.event_bus") as mock_bus:
                    mock_bus.publish = AsyncMock()

                    service = AuthService(mock_session)
                    service._token_repo = mock_token_repo

                    token, _ = create_access_token(str(uuid4()))
                    await service.logout(uuid4(), token)

                    mock_bus.publish.assert_called()
                    call_args = mock_bus.publish.call_args[0][0]
                    assert call_args.name == "auth.user_logged_out"
