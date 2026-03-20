import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin


class ReadingSession(Base, UUIDMixin):
    """
    Reading session for tracking reading activity.

    Links to a user's book entry with session details.
    """

    __tablename__ = "reading_sessions"

    user_book_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user_books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    pages_read: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    user_book: Mapped["UserBook"] = relationship(
        "UserBook",
        back_populates="sessions",
    )

    def __repr__(self) -> str:
        return f"<ReadingSession(id={self.id}, user_book_id={self.user_book_id}, pages={self.pages_read})>"
