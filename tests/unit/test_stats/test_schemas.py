import pytest
from unittest.mock import AsyncMock, MagicMock

from app.features.stats.schemas import UserStatsResponse, TopUsersResponse, TopUserEntry
from app.features.stats.repository import StatsRepository


class TestUserStatsResponse:
    """Tests for UserStatsResponse schema."""

    def test_valid_stats(self):
        """Valid stats should pass."""
        data = UserStatsResponse(
            total_books=10,
            books_want_to_read=3,
            books_reading=2,
            books_finished=5,
            books_abandoned=0,
            total_pages_read=1500,
            current_streak=5,
            longest_streak=10,
        )
        assert data.total_books == 10
        assert data.books_finished == 5

    def test_zero_stats(self):
        """Zero stats should pass."""
        data = UserStatsResponse(
            total_books=0,
            books_want_to_read=0,
            books_reading=0,
            books_finished=0,
            books_abandoned=0,
            total_pages_read=0,
            current_streak=0,
            longest_streak=0,
        )
        assert data.total_books == 0


class TestTopUsersResponse:
    """Tests for TopUsersResponse schema."""

    def test_valid_leaderboard(self):
        """Valid leaderboard should pass."""
        data = TopUsersResponse(
            period="month",
            users=[
                TopUserEntry(
                    rank=1,
                    user_id="u1",
                    books_finished=10,
                    pages_read=3000,
                    streak_days=15,
                ),
                TopUserEntry(
                    rank=2,
                    user_id="u2",
                    books_finished=8,
                    pages_read=2400,
                    streak_days=10,
                ),
            ],
        )
        assert data.period == "month"
        assert len(data.users) == 2
        assert data.users[0].rank == 1


class TestTopUserEntry:
    """Tests for TopUserEntry schema."""

    def test_valid_entry(self):
        """Valid entry should pass."""
        data = TopUserEntry(
            rank=1,
            user_id="user-123",
            books_finished=5,
            pages_read=1500,
            streak_days=7,
        )
        assert data.rank == 1
        assert data.user_id == "user-123"


class TestStatsRepository:
    """Tests for StatsRepository."""

    @pytest.mark.asyncio
    async def test_get_top_users_aggregates_correctly(self):
        """Repository should correctly aggregate books_finished and pages_read per user."""
        mock_session = AsyncMock()

        row1 = MagicMock()
        row1.user_id = "user-1"
        row1.books_finished = 5
        row1.pages_read = 1500

        row2 = MagicMock()
        row2.user_id = "user-2"
        row2.books_finished = 3
        row2.pages_read = 900

        mock_result = MagicMock()
        mock_result.all.return_value = [row1, row2]
        mock_session.execute.return_value = mock_result

        repo = StatsRepository(mock_session)
        result = await repo.get_top_users(period="month", limit=10)

        assert len(result) == 2
        assert result[0]["rank"] == 1
        assert result[0]["user_id"] == "user-1"
        assert result[0]["books_finished"] == 5
        assert result[0]["pages_read"] == 1500
        assert result[1]["rank"] == 2
        assert result[1]["books_finished"] == 3
        assert result[1]["pages_read"] == 900

    @pytest.mark.asyncio
    async def test_get_top_users_handles_null_pages(self):
        """Repository should handle NULL pages_read gracefully."""
        mock_session = AsyncMock()

        row = MagicMock()
        row.user_id = "user-1"
        row.books_finished = 1
        row.pages_read = None

        mock_result = MagicMock()
        mock_result.all.return_value = [row]
        mock_session.execute.return_value = mock_result

        repo = StatsRepository(mock_session)
        result = await repo.get_top_users()

        assert result[0]["pages_read"] == 0

    @pytest.mark.asyncio
    async def test_get_top_users_empty_result(self):
        """Repository should return empty list when no users."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.execute.return_value = mock_result

        repo = StatsRepository(mock_session)
        result = await repo.get_top_users()

        assert result == []
