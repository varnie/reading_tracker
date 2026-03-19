import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4

from app.tasks.email_tasks import (
    generate_weekly_report,
    send_reminder,
)


class TestGenerateWeeklyReport:
    """Tests for generate_weekly_report task."""

    def test_generate_weekly_report_user_not_found(self):
        """Should handle user not found."""
        mock_session = MagicMock()
        mock_session.get.return_value = None

        from tests.unit.test_tasks import mock_session_cm

        with patch(
            "app.tasks.email_tasks.get_sync_session",
            return_value=mock_session_cm(mock_session),
        ):
            with patch("app.tasks.email_tasks.email_service") as mock_email:
                mock_email.send_weekly_report = MagicMock()
                result = generate_weekly_report("nonexistent-user")

        assert result["sent"] is False
        assert result["reason"] == "User not found"


class TestSendReminder:
    """Tests for send_reminder task."""

    def test_send_reminder_user_not_found(self):
        """Should handle user not found."""
        mock_session = MagicMock()
        mock_session.get.return_value = None

        from tests.unit.test_tasks import mock_session_cm

        with patch(
            "app.tasks.email_tasks.get_sync_session",
            return_value=mock_session_cm(mock_session),
        ):
            with patch("app.tasks.email_tasks.email_service") as mock_email:
                mock_email.send_email = MagicMock()
                result = send_reminder("nonexistent", "book-id")

        assert result["sent"] is False
        assert result["reason"] == "User not found"

    def test_send_reminder_book_not_found(self):
        """Should handle book not found."""
        mock_session = MagicMock()

        user = MagicMock()
        user.email = "test@example.com"
        mock_session.get.return_value = user

        mock_session.execute.return_value = MagicMock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None

        from tests.unit.test_tasks import mock_session_cm

        with patch(
            "app.tasks.email_tasks.get_sync_session",
            return_value=mock_session_cm(mock_session),
        ):
            with patch("app.tasks.email_tasks.email_service") as mock_email:
                mock_email.send_email = MagicMock()
                result = send_reminder("user-id", "nonexistent-book")

        assert result["sent"] is False
        assert result["reason"] == "Book not found"
