import pytest

from app.features.catalog.schemas import CatalogBookCreate


class TestCatalogBookCreateSchemas:
    """Tests for CatalogBookCreate schema."""

    def test_valid_book(self):
        """Valid book creation should pass."""
        data = CatalogBookCreate(
            title="1984",
            author="George Orwell",
            pages_total=328,
        )
        assert data.title == "1984"
        assert data.author == "George Orwell"
        assert data.pages_total == 328

    def test_with_isbn(self):
        """Book with ISBN should pass."""
        data = CatalogBookCreate(
            title="1984",
            author="George Orwell",
            pages_total=328,
            isbn="978-0451524935",
        )
        assert data.isbn == "978-0451524935"

    def test_with_description(self):
        """Book with description should pass."""
        data = CatalogBookCreate(
            title="1984",
            author="George Orwell",
            pages_total=328,
            description="A dystopian novel",
        )
        assert data.description == "A dystopian novel"

    def test_empty_title_fails(self):
        """Empty title should fail."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CatalogBookCreate(
                title="",
                author="George Orwell",
                pages_total=328,
            )

    def test_zero_pages_fails(self):
        """Zero pages should fail."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CatalogBookCreate(
                title="1984",
                author="George Orwell",
                pages_total=0,
            )
