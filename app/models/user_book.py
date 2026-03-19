import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models import Base, TimestampMixin, UUIDMixin


class UserBook(Base, UUIDMixin, TimestampMixin):
    """
    User's personal book entry.

    Links a user to a book from the catalog with personal tracking data.
    """

    __tablename__ = "user_books"
    __table_args__ = (UniqueConstraint("user_id", "book_id", name="uq_user_book"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    book_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="want_to_read",
        nullable=False,
    )
    pages_read: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    rating: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="books",
    )
    book: Mapped["Book"] = relationship(
        "Book",
        back_populates="user_books",
    )
    sessions: Mapped[list["ReadingSession"]] = relationship(
        "ReadingSession",
        back_populates="user_book",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<UserBook(id={self.id}, user_id={self.user_id}, book_id={self.book_id}, status={self.status})>"
