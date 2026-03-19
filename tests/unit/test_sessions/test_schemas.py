import pytest

from app.features.sessions.schemas import SessionCreate, SessionUpdate


class TestSessionCreateSchemas:
    """Tests for SessionCreate schema."""

    def test_valid_session(self):
        """Valid session should pass."""
        data = SessionCreate(pages_read=50)
        assert data.pages_read == 50

    def test_with_notes(self):
        """Session with notes should pass."""
        data = SessionCreate(pages_read=50, notes="Great chapter!")
        assert data.notes == "Great chapter!"

    def test_zero_pages_fails(self):
        """Zero pages should fail."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            SessionCreate(pages_read=0)

    def test_negative_pages_fails(self):
        """Negative pages should fail."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            SessionCreate(pages_read=-10)


class TestSessionUpdateSchemas:
    """Tests for SessionUpdate schema."""

    def test_update_pages(self):
        """Update pages should pass."""
        data = SessionUpdate(pages_read=100)
        assert data.pages_read == 100

    def test_update_notes(self):
        """Update notes should pass."""
        data = SessionUpdate(notes="Updated notes")
        assert data.notes == "Updated notes"

    def test_partial_update(self):
        """Partial update should pass."""
        data = SessionUpdate(notes="New notes")
        assert data.pages_read is None
