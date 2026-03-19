from app.shared.events import Event


class BookEvents:
    """Events emitted by books feature."""

    @staticmethod
    def book_added(user_id: str, user_book_id: str) -> Event:
        """Emitted when a user adds a book to their list."""
        return Event(
            name="books.book_added",
            data={
                "user_id": user_id,
                "user_book_id": user_book_id,
            },
            metadata={"source": "books"},
        )

    @staticmethod
    def book_finished(user_id: str, user_book_id: str) -> Event:
        """Emitted when a user finishes reading a book."""
        return Event(
            name="books.book_finished",
            data={
                "user_id": user_id,
                "user_book_id": user_book_id,
            },
            metadata={"source": "books"},
        )

    @staticmethod
    def book_deleted(user_id: str, user_book_id: str) -> Event:
        """Emitted when a user removes a book from their list."""
        return Event(
            name="books.book_deleted",
            data={
                "user_id": user_id,
                "user_book_id": user_book_id,
            },
            metadata={"source": "books"},
        )

    @staticmethod
    def session_created(user_id: str, user_book_id: str, session_id: str) -> Event:
        """Emitted when a reading session is created."""
        return Event(
            name="books.session_created",
            data={
                "user_id": user_id,
                "user_book_id": user_book_id,
                "session_id": session_id,
            },
            metadata={"source": "books"},
        )
