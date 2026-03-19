from pydantic import BaseModel


class UserStatsResponse(BaseModel):
    """Schema for user statistics response."""

    total_books: int
    books_want_to_read: int
    books_reading: int
    books_finished: int
    books_abandoned: int
    total_pages_read: int
    current_streak: int
    longest_streak: int


class TopUserEntry(BaseModel):
    """Schema for a single top user entry."""

    rank: int
    user_id: str
    books_finished: int
    pages_read: int
    streak_days: int


class TopUsersResponse(BaseModel):
    """Schema for top users response."""

    period: str
    users: list[TopUserEntry]
