from unittest.mock import patch, MagicMock
from contextlib import contextmanager

from app.tasks.stats_tasks import (
    calculate_user_streaks,
    update_leaderboard,
)


@contextmanager
def mock_session_cm(mock_session):
    """Create a mock context manager that yields the session."""
    yield mock_session


class TestCalculateUserStreaks:
    """Tests for calculate_user_streaks task."""

    def test_calculate_user_streaks(self):
        """Task should calculate and cache user streaks."""
        from datetime import datetime, timedelta, timezone

        with (
            patch("app.tasks.stats_tasks.get_sync_session") as mock_get_session,
            patch("app.tasks.stats_tasks.get_sync_redis") as mock_get_redis,
        ):
            mock_session = MagicMock()
            mock_redis = MagicMock()
            mock_get_session.return_value = mock_session_cm(mock_session)
            mock_get_redis.return_value = mock_redis

            user = MagicMock()
            user.id = "user-1"

            users_result = MagicMock()
            users_result.scalars.return_value.all.return_value = [user]

            user_book = MagicMock()
            user_book.id = "ub-1"

            user_books_result = MagicMock()
            user_books_result.scalars.return_value.all.return_value = [user_book]

            session1 = MagicMock()
            session1.started_at = datetime.now(timezone.utc) - timedelta(days=1)
            session2 = MagicMock()
            session2.started_at = datetime.now(timezone.utc) - timedelta(days=2)

            sessions_result = MagicMock()
            sessions_result.scalars.return_value.all.return_value = [session1, session2]

            mock_session.execute.side_effect = [
                users_result,
                user_books_result,
                sessions_result,
            ]

            result = calculate_user_streaks()

            assert isinstance(result, dict)
            assert "users_updated" in result
            mock_redis.setex.assert_called()

    def test_calculate_user_streaks_no_users(self):
        """Task should handle no users gracefully."""
        with (
            patch("app.tasks.stats_tasks.get_sync_session") as mock_get_session,
            patch("app.tasks.stats_tasks.get_sync_redis") as mock_get_redis,
        ):
            mock_session = MagicMock()
            mock_redis = MagicMock()
            mock_get_session.return_value = mock_session_cm(mock_session)
            mock_get_redis.return_value = mock_redis

            users_result = MagicMock()
            users_result.scalars.return_value.all.return_value = []
            mock_session.execute.return_value = users_result

            result = calculate_user_streaks()

            assert result["users_updated"] == 0


class TestUpdateLeaderboard:
    """Tests for update_leaderboard task."""

    def test_update_leaderboard_default(self):
        """Task should update leaderboard cache."""
        with (
            patch("app.tasks.stats_tasks.get_sync_session") as mock_get_session,
            patch("app.tasks.stats_tasks.get_sync_redis") as mock_get_redis,
        ):
            mock_session = MagicMock()
            mock_redis = MagicMock()
            mock_get_session.return_value = mock_session_cm(mock_session)
            mock_get_redis.return_value = mock_redis

            leaderboard_entry = MagicMock()
            leaderboard_entry.user_id = "user-1"
            leaderboard_entry.finished_count = 5

            leaderboard_result = MagicMock()
            leaderboard_result.__iter__ = lambda self: iter([leaderboard_entry])

            sum_result = MagicMock()
            sum_result.scalar.return_value = 500

            mock_session.execute.side_effect = [leaderboard_result, sum_result]

            user = MagicMock()
            user.email = "top@example.com"
            mock_session.get.return_value = user

            result_data = update_leaderboard()

            assert isinstance(result_data, dict)
            assert "period" in result_data
            assert result_data["period"] == "month"
            assert "users" in result_data
            mock_redis.setex.assert_called()

    def test_update_leaderboard_week(self):
        """Task should update leaderboard for week period."""
        with (
            patch("app.tasks.stats_tasks.get_sync_session") as mock_get_session,
            patch("app.tasks.stats_tasks.get_sync_redis") as mock_get_redis,
        ):
            mock_session = MagicMock()
            mock_redis = MagicMock()
            mock_get_session.return_value = mock_session_cm(mock_session)
            mock_get_redis.return_value = mock_redis

            leaderboard_result = MagicMock()
            leaderboard_result.__iter__ = lambda self: iter([])

            mock_session.execute.return_value = leaderboard_result

            result_data = update_leaderboard(period="week")

            assert result_data["period"] == "week"
            assert result_data["users"] == []

    def test_update_leaderboard_all(self):
        """Task should update leaderboard for all time."""
        with (
            patch("app.tasks.stats_tasks.get_sync_session") as mock_get_session,
            patch("app.tasks.stats_tasks.get_sync_redis") as mock_get_redis,
        ):
            mock_session = MagicMock()
            mock_redis = MagicMock()
            mock_get_session.return_value = mock_session_cm(mock_session)
            mock_get_redis.return_value = mock_redis

            leaderboard_result = MagicMock()
            leaderboard_result.__iter__ = lambda self: iter([])

            mock_session.execute.return_value = leaderboard_result

            result_data = update_leaderboard(period="all")

            assert result_data["period"] == "all"
