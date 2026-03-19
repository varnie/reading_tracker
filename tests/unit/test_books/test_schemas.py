from uuid import uuid4

import pytest

from app.features.books.schemas import BookCreate, BookUpdate


class TestBookCreateSchemas:
    """Tests for BookCreate schema."""

    def test_book_create_valid(self):
        """Valid book create should pass."""
        data = BookCreate(
            catalog_book_id=uuid4(),
        )
        assert data.catalog_book_id is not None

    def test_book_create_with_status(self):
        """Book create with status should pass."""
        data = BookCreate(
            catalog_book_id=uuid4(),
            status="reading",
        )
        assert data.status == "reading"


class TestBookUpdateSchemas:
    """Tests for BookUpdate schema."""

    def test_book_update_status(self):
        """Update status should pass."""
        data = BookUpdate(status="finished")
        assert data.status == "finished"

    def test_book_update_pages_read(self):
        """Update pages read should pass."""
        data = BookUpdate(pages_read=100)
        assert data.pages_read == 100

    def test_book_update_rating(self):
        """Update rating should pass."""
        data = BookUpdate(rating=5)
        assert data.rating == 5

    def test_book_update_invalid_rating(self):
        """Invalid rating should fail."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            BookUpdate(rating=10)

    def test_book_update_partial(self):
        """Partial update should pass."""
        data = BookUpdate(status="reading")
        assert data.pages_read is None
        assert data.rating is None
