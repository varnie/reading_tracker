from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4


async def mock_send_weekly_report(*args, **kwargs):
    return True


async def mock_send_email(*args, **kwargs):
    return True


class TestGenerateWeeklyReport:
    """Tests for generate_weekly_report task."""

    def test_generate_weekly_report_success(self):
        """Should generate and send weekly report successfully."""
        from app.tasks.email_tasks import generate_weekly_report

        mock_session = MagicMock()

        user = MagicMock()
        user.id = uuid4()
        user.email = "test@example.com"

        user_book1 = MagicMock()
        user_book1.id = uuid4()
        user_book1.started_at = datetime.now(UTC)
        user_book1.finished_at = None

        user_book2 = MagicMock()
        user_book2.id = uuid4()
        user_book2.started_at = datetime.now(UTC)
        user_book2.finished_at = datetime.now(UTC)

        session1 = MagicMock()
        session1.pages_read = 25
        session1.started_at = datetime.now(UTC)

        session2 = MagicMock()
        session2.pages_read = 30
        session2.started_at = datetime.now(UTC)

        mock_session.get.return_value = user
        mock_session.execute.side_effect = [
            MagicMock(
                scalars=MagicMock(
                    return_value=MagicMock(
                        all=MagicMock(return_value=[user_book1, user_book2])
                    )
                )
            ),
            MagicMock(
                scalars=MagicMock(
                    return_value=MagicMock(
                        all=MagicMock(return_value=[session1, session2])
                    )
                )
            ),
        ]

        from tests.unit.test_tasks import mock_session_cm

        with (
            patch(
                "app.tasks.email_tasks.get_sync_session",
                return_value=mock_session_cm(mock_session),
            ),
            patch("app.tasks.email_tasks.email_service") as mock_email,
        ):
            mock_email.send_weekly_report = mock_send_weekly_report
            result = generate_weekly_report(str(user.id))

        assert result["sent"] is True
        assert result["email"] == "test@example.com"
        assert result["pages_read"] == 55

    def test_generate_weekly_report_user_not_found(self):
        """Should handle user not found."""
        from app.tasks.email_tasks import generate_weekly_report

        mock_session = MagicMock()
        mock_session.get.return_value = None

        from tests.unit.test_tasks import mock_session_cm

        with (
            patch(
                "app.tasks.email_tasks.get_sync_session",
                return_value=mock_session_cm(mock_session),
            ),
            patch("app.tasks.email_tasks.email_service") as mock_email,
        ):
            mock_email.send_weekly_report = mock_send_weekly_report
            result = generate_weekly_report("nonexistent-user")

        assert result["sent"] is False
        assert result["reason"] == "User not found"


class TestSendReminder:
    """Tests for send_reminder task."""

    def test_send_reminder_success_with_session(self):
        """Should send reminder for book with recent session."""
        from app.tasks.email_tasks import send_reminder

        mock_session = MagicMock()

        user = MagicMock()
        user.email = "test@example.com"

        user_book = MagicMock()
        user_book.id = uuid4()
        user_book.started_at = datetime.now(UTC) - timedelta(days=10)

        last_session = MagicMock()
        last_session.started_at = datetime.now(UTC) - timedelta(days=3)

        mock_session.get.return_value = user
        mock_session.execute.side_effect = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=user_book)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=last_session)),
        ]

        from tests.unit.test_tasks import mock_session_cm

        with (
            patch(
                "app.tasks.email_tasks.get_sync_session",
                return_value=mock_session_cm(mock_session),
            ),
            patch("app.tasks.email_tasks.email_service") as mock_email,
        ):
            mock_email.send_email = mock_send_email
            result = send_reminder(str(user.id), str(user_book.id))

        assert result["sent"] is True
        assert result["user_email"] == "test@example.com"

    def test_send_reminder_success_no_session(self):
        """Should send reminder for book without sessions."""
        from app.tasks.email_tasks import send_reminder

        mock_session = MagicMock()

        user = MagicMock()
        user.email = "test@example.com"

        user_book = MagicMock()
        user_book.id = uuid4()
        user_book.started_at = datetime.now(UTC) - timedelta(days=15)

        mock_session.get.return_value = user
        mock_session.execute.side_effect = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=user_book)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),
        ]

        from tests.unit.test_tasks import mock_session_cm

        with (
            patch(
                "app.tasks.email_tasks.get_sync_session",
                return_value=mock_session_cm(mock_session),
            ),
            patch("app.tasks.email_tasks.email_service") as mock_email,
        ):
            mock_email.send_email = mock_send_email
            result = send_reminder(str(user.id), str(user_book.id))

        assert result["sent"] is True
        assert result["user_email"] == "test@example.com"

    def test_send_reminder_user_not_found(self):
        """Should handle user not found."""
        from app.tasks.email_tasks import send_reminder

        mock_session = MagicMock()
        mock_session.get.return_value = None

        from tests.unit.test_tasks import mock_session_cm

        with (
            patch(
                "app.tasks.email_tasks.get_sync_session",
                return_value=mock_session_cm(mock_session),
            ),
            patch("app.tasks.email_tasks.email_service") as mock_email,
        ):
            mock_email.send_email = mock_send_email
            result = send_reminder("nonexistent", "book-id")

        assert result["sent"] is False
        assert result["reason"] == "User not found"

    def test_send_reminder_book_not_found(self):
        """Should handle book not found."""
        from app.tasks.email_tasks import send_reminder

        mock_session = MagicMock()

        user = MagicMock()
        user.email = "test@example.com"
        mock_session.get.return_value = user
        mock_session.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=None)
        )

        from tests.unit.test_tasks import mock_session_cm

        with (
            patch(
                "app.tasks.email_tasks.get_sync_session",
                return_value=mock_session_cm(mock_session),
            ),
            patch("app.tasks.email_tasks.email_service") as mock_email,
        ):
            mock_email.send_email = mock_send_email
            result = send_reminder("user-id", "nonexistent-book")

        assert result["sent"] is False
        assert result["reason"] == "Book not found"
