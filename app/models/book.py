import uuid

from sqlalchemy import Integer, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models import Base, SoftDeleteMixin, TimestampMixin, UUIDMixin


class Book(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """
    Book catalog entry.

    Shared across all users - represents a book in the system catalog.
    """

    __tablename__ = "books"

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    author: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    isbn: Mapped[str | None] = mapped_column(
        String(20),
        unique=True,
        nullable=True,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    pages_total: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    user_books: Mapped[list["UserBook"]] = relationship(
        "UserBook",
        back_populates="book",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Book(id={self.id}, title={self.title})>"
