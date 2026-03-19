import pytest
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime, timedelta, timezone
from contextlib import contextmanager

from app.tasks.book_tasks import (
    check_abandoned_books,
    cleanup_old_sessions,
    generate_weekly_report,
)


@contextmanager
def mock_session_cm(mock_session, raise_error=False):
    """Create a mock context manager for session."""
    try:
        yield mock_session
        mock_session.commit()
    except Exception:
        mock_session.rollback()
        raise
    finally:
        mock_session.close()


class TestCleanupOldSessions:
    """Tests for cleanup_old_sessions task."""

    def test_cleanup_old_sessions_default(self):
        """Task should cleanup sessions older than default 365 days."""
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.rowcount = 5
        mock_session.execute.return_value = mock_result

        with patch(
            "app.tasks.book_tasks.get_sync_session",
            return_value=mock_session_cm(mock_session),
        ):
            result = cleanup_old_sessions()

            assert isinstance(result, dict)
            assert "deleted" in result
            assert result["deleted"] == 5

    def test_cleanup_old_sessions_custom_days(self):
        """Task should cleanup sessions older than custom days."""
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.rowcount = 10
        mock_session.execute.return_value = mock_result

        with patch(
            "app.tasks.book_tasks.get_sync_session",
            return_value=mock_session_cm(mock_session),
        ):
            result = cleanup_old_sessions(days_old=30)

            assert result["deleted"] == 10

    def test_cleanup_old_sessions_error(self):
        """Task should rollback on error."""
        mock_session = MagicMock()
        mock_session.execute.side_effect = Exception("DB error")

        with patch(
            "app.tasks.book_tasks.get_sync_session",
            return_value=mock_session_cm(mock_session),
        ):
            with pytest.raises(Exception):
                cleanup_old_sessions()

            mock_session.rollback.assert_called_once()


class TestCheckAbandonedBooks:
    """Tests for check_abandoned_books task."""

    def test_check_abandoned_books(self):
        """Task should mark inactive reading books as abandoned."""
        mock_session = MagicMock()

        book = MagicMock()
        book.id = "book-1"
        book.status = "reading"
        book.started_at = datetime.now(timezone.utc) - timedelta(days=60)

        reading_books_result = MagicMock()
        reading_books_result.scalars.return_value.all.return_value = [book]

        last_session = MagicMock()
        last_session.started_at = datetime.now(timezone.utc) - timedelta(days=35)

        last_session_result = MagicMock()
        last_session_result.scalar_one_or_none.return_value = last_session

        mock_session.execute.side_effect = [reading_books_result, last_session_result]

        with patch(
            "app.tasks.book_tasks.get_sync_session",
            return_value=mock_session_cm(mock_session),
        ):
            result = check_abandoned_books()

            assert isinstance(result, dict)
            assert "abandoned" in result

    def test_check_abandoned_books_no_abandoned(self):
        """Task should return 0 when no books are abandoned."""
        mock_session = MagicMock()

        book = MagicMock()
        book.status = "reading"
        book.started_at = datetime.now(timezone.utc) - timedelta(days=1)

        reading_books_result = MagicMock()
        reading_books_result.scalars.return_value.all.return_value = [book]

        last_session = MagicMock()
        last_session.started_at = datetime.now(timezone.utc) - timedelta(days=1)

        last_session_result = MagicMock()
        last_session_result.scalar_one_or_none.return_value = last_session

        mock_session.execute.side_effect = [reading_books_result, last_session_result]

        with patch(
            "app.tasks.book_tasks.get_sync_session",
            return_value=mock_session_cm(mock_session),
        ):
            result = check_abandoned_books()

            assert result["abandoned"] == 0


class TestGenerateWeeklyReport:
    """Tests for generate_weekly_report task."""

    def test_generate_weekly_report(self):
        """Task should generate report for user."""
        mock_session = MagicMock()

        user_book = MagicMock()
        user_book.id = "ub-1"
        user_book.started_at = datetime.now(timezone.utc) - timedelta(days=3)
        user_book.finished_at = None

        user_books_result = MagicMock()
        user_books_result.scalars.return_value.all.return_value = [user_book]

        sessions_result = MagicMock()
        sessions_result.scalars.return_value.all.return_value = []

        user = MagicMock()
        user.email = "test@example.com"

        mock_session.execute.side_effect = [user_books_result, sessions_result]
        mock_session.get.return_value = user

        with patch(
            "app.tasks.book_tasks.get_sync_session",
            return_value=mock_session_cm(mock_session),
        ):
            result = generate_weekly_report("user-id")

            assert isinstance(result, dict)
            assert result["user_id"] == "user-id"
            assert result["email"] == "test@example.com"
            assert "books_started" in result
            assert "books_finished" in result
            assert "pages_read" in result

    def test_generate_weekly_report_user_not_found(self):
        """Task should handle user not found."""
        mock_session = MagicMock()
        mock_session.get.return_value = None

        with patch(
            "app.tasks.book_tasks.get_sync_session",
            return_value=mock_session_cm(mock_session),
        ):
            result = generate_weekly_report("nonexistent-user")

            assert result["books_started"] == 0
            assert result["books_finished"] == 0
            assert result["pages_read"] == 0
