from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.redis import Cache, TokenBlacklist


class TestTokenBlacklist:
    """Tests for TokenBlacklist."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        return AsyncMock()

    @pytest.fixture
    def blacklist(self, mock_redis):
        """Create TokenBlacklist with mock Redis."""
        return TokenBlacklist(mock_redis)

    @pytest.mark.asyncio
    async def test_blacklist_token(self, blacklist, mock_redis):
        """Should set token in blacklist with TTL."""
        await blacklist.blacklist_token("test-jti", 1800)
        mock_redis.setex.assert_called_once_with("blacklist:test-jti", 1800, "1")

    @pytest.mark.asyncio
    async def test_is_blacklisted_true(self, blacklist, mock_redis):
        """Should return True if token is blacklisted."""
        mock_redis.exists.return_value = 1
        result = await blacklist.is_blacklisted("test-jti")
        assert result is True
        mock_redis.exists.assert_called_once_with("blacklist:test-jti")

    @pytest.mark.asyncio
    async def test_is_blacklisted_false(self, blacklist, mock_redis):
        """Should return False if token is not blacklisted."""
        mock_redis.exists.return_value = 0
        result = await blacklist.is_blacklisted("test-jti")
        assert result is False


class TestCache:
    """Tests for Cache."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        mock = AsyncMock()
        mock.get.return_value = '{"key": "value"}'
        return mock

    @pytest.fixture
    def cache(self, mock_redis):
        """Create Cache with mock Redis."""
        return Cache(mock_redis)

    @pytest.mark.asyncio
    async def test_get_found(self, cache, mock_redis):
        """Should return cached value."""
        result = await cache.get("test-key")
        assert result == {"key": "value"}
        mock_redis.get.assert_called_once_with("cache:test-key")

    @pytest.mark.asyncio
    async def test_get_not_found(self, cache, mock_redis):
        """Should return None if key not found."""
        mock_redis.get.return_value = None
        result = await cache.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_set(self, cache, mock_redis):
        """Should set value with TTL."""
        await cache.set("test-key", {"data": "value"}, ttl=300)
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == "cache:test-key"
        assert call_args[0][1] == 300

    @pytest.mark.asyncio
    async def test_delete(self, cache, mock_redis):
        """Should delete key."""
        await cache.delete("test-key")
        mock_redis.delete.assert_called_once_with("cache:test-key")

    @pytest.mark.asyncio
    async def test_invalidate_pattern(self, cache, mock_redis):
        """Should invalidate all keys matching pattern."""
        mock_redis.scan_iter = MagicMock(
            return_value=AsyncMock(__aiter__=lambda self: self)
        )
        mock_redis.scan_iter.return_value.__anext__ = AsyncMock(
            side_effect=[
                "cache:leaderboard:month",
                "cache:leaderboard:week",
                StopAsyncIteration(),
            ]
        )
        mock_redis.delete.return_value = 2

        result = await cache.invalidate_pattern("leaderboard:*")

        assert result == 2
        mock_redis.delete.assert_called_once()
