from app.shared.events import Event


class CatalogEvents:
    """Events emitted by catalog feature."""

    @staticmethod
    def book_added_to_catalog(book_id: str, user_id: str) -> Event:
        """Emitted when a new book is added to catalog."""
        return Event(
            name="catalog.book_added",
            data={
                "book_id": book_id,
                "user_id": user_id,
            },
            metadata={"source": "catalog"},
        )
