from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.features.catalog.repository import _escape_like_query


class TestEscapeLikeQuery:
    """Tests for LIKE query escaping."""

    def test_escape_percent_sign(self):
        """Should escape percent signs."""
        result = _escape_like_query("test%value")
        assert result == "test\\%value"

    def test_escape_underscore(self):
        """Should escape underscores."""
        result = _escape_like_query("test_value")
        assert result == "test\\_value"

    def test_escape_backslash(self):
        """Should escape backslashes."""
        result = _escape_like_query("test\\value")
        assert result == "test\\\\value"

    def test_escape_multiple_special_chars(self):
        """Should escape multiple special characters."""
        result = _escape_like_query("50%_off\\today")
        assert result == "50\\%\\_off\\\\today"

    def test_escape_no_special_chars(self):
        """Should return unchanged if no special chars."""
        result = _escape_like_query("normal search query")
        assert result == "normal search query"

    def test_escape_empty_string(self):
        """Should handle empty string."""
        result = _escape_like_query("")
        assert result == ""


class TestCatalogService:
    """Tests for CatalogService."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return AsyncMock()

    @pytest.fixture
    def mock_repo(self):
        """Create a mock catalog repository."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_session, mock_repo):
        """Create a CatalogService with mocked dependencies."""
        from app.features.catalog.service import CatalogService

        with patch(
            "app.features.catalog.service.CatalogRepository", return_value=mock_repo
        ):
            return CatalogService(mock_session)

    @pytest.mark.asyncio
    async def test_create_book_success(self, service, mock_repo):
        """Should create a book successfully."""
        user_id = uuid4()
        book_id = uuid4()

        book = MagicMock()
        book.id = book_id
        book.title = "Test Book"
        book.author = "Test Author"
        book.isbn = "1234567890"
        book.description = "A test book"
        book.pages_total = 200
        book.created_at = datetime.now(UTC)
        book.created_by_user_id = user_id
        mock_repo.isbn_exists.return_value = False
        mock_repo.create.return_value = book

        from app.features.catalog.schemas import CatalogBookCreate

        data = CatalogBookCreate(
            title="Test Book",
            author="Test Author",
            pages_total=200,
            isbn="1234567890",
            description="A test book",
        )

        result = await service.create_book(user_id, data)

        assert result.title == "Test Book"
        mock_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_book_duplicate_isbn(self, service, mock_repo):
        """Should raise error if ISBN already exists."""
        from app.core.exceptions import AlreadyExistsError
        from app.features.catalog.schemas import CatalogBookCreate

        user_id = uuid4()
        mock_repo.isbn_exists.return_value = True

        data = CatalogBookCreate(
            title="Test Book",
            author="Test Author",
            pages_total=200,
            isbn="1234567890",
        )

        with pytest.raises(AlreadyExistsError):
            await service.create_book(user_id, data)

    @pytest.mark.asyncio
    async def test_search_books(self, service, mock_repo):
        """Should search books."""
        book1 = MagicMock()
        book1.id = uuid4()
        book1.title = "Book One"
        book1.author = "Author A"
        book1.isbn = "111"
        book1.description = "Desc 1"
        book1.pages_total = 100
        book1.created_at = datetime.now(UTC)
        book1.created_by_user_id = uuid4()

        mock_repo.search.return_value = ([book1], 1)

        results, total = await service.search_books(query="book")

        assert total == 1
        assert results[0].title == "Book One"

    @pytest.mark.asyncio
    async def test_get_popular(self, service, mock_repo):
        """Should get popular books."""
        book = MagicMock()
        book.id = uuid4()
        book.title = "Popular Book"
        book.author = "Popular Author"
        book.isbn = "999"
        book.description = "A popular book"
        book.pages_total = 300
        book.created_at = datetime.now(UTC)
        book.created_by_user_id = uuid4()

        mock_repo.get_popular.return_value = [book]

        results = await service.get_popular(limit=10)

        assert len(results) == 1
        assert results[0].title == "Popular Book"
