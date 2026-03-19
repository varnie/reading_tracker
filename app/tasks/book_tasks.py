from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select

from app.core.enums import BookStatus
from app.core.logging import get_logger
from app.models.reading_session import ReadingSession
from app.models.user import User
from app.models.user_book import UserBook
from app.tasks.celery_app import celery_app
from app.tasks.celery_db import get_sync_session

logger = get_logger(__name__)


@celery_app.task
def cleanup_old_sessions(days_old: int = 365) -> dict:
    """
    Clean up old reading sessions.

    Args:
        days_old: Delete sessions older than this many days

    Returns:
        Number of deleted sessions.
    """
    logger.info(f"Running cleanup_old_sessions task (days_old={days_old})")

    with get_sync_session() as session:
        cutoff_date = datetime.now(UTC) - timedelta(days=days_old)

        result = session.execute(
            delete(ReadingSession).where(ReadingSession.started_at < cutoff_date)
        )
        deleted_count = result.rowcount

        logger.info(f"Deleted {deleted_count} old reading sessions")
        return {"deleted": deleted_count}


@celery_app.task
def check_abandoned_books(days_inactive: int = 30) -> dict:
    """
    Check for abandoned books (no activity for specified days).

    Args:
        days_inactive: Days without activity before marking as abandoned

    Returns:
        Number of books marked as abandoned.
    """
    logger.info(f"Running check_abandoned_books task (days_inactive={days_inactive})")

    with get_sync_session() as session:
        cutoff_date = datetime.now(UTC) - timedelta(days=days_inactive)

        result = session.execute(
            select(UserBook).where(UserBook.status == BookStatus.READING)
        )
        reading_books = result.scalars().all()

        abandoned_count = 0
        for book in reading_books:
            last_session = session.execute(
                select(ReadingSession)
                .where(ReadingSession.user_book_id == book.id)
                .order_by(ReadingSession.started_at.desc())
                .limit(1)
            ).scalar_one_or_none()

            if last_session and last_session.started_at < cutoff_date:
                book.status = BookStatus.ABANDONED
                abandoned_count += 1
                logger.info(
                    f"Marked book {book.id} as abandoned (last read: {last_session.started_at})"
                )
            elif not last_session and book.started_at and book.started_at < cutoff_date:
                book.status = BookStatus.ABANDONED
                abandoned_count += 1
                logger.info(
                    f"Marked book {book.id} as abandoned (started: {book.started_at})"
                )

        session.flush()
        logger.info(f"Marked {abandoned_count} books as abandoned")
        return {"abandoned": abandoned_count}


@celery_app.task
def generate_weekly_report(user_id: str) -> dict:
    """
    Generate weekly reading report for a user.

    Args:
        user_id: User ID to generate report for

    Returns:
        Report data with reading statistics.
    """
    logger.info(f"Generating weekly report for user {user_id}")

    with get_sync_session() as session:
        week_ago = datetime.now(UTC) - timedelta(days=7)

        user_books = (
            session.execute(select(UserBook).where(UserBook.user_id == user_id))
            .scalars()
            .all()
        )

        book_ids = [ub.id for ub in user_books]

        sessions_result = session.execute(
            select(ReadingSession).where(
                ReadingSession.user_book_id.in_(book_ids),
                ReadingSession.started_at >= week_ago,
            )
        )
        sessions = sessions_result.scalars().all()

        pages_read = sum(s.pages_read for s in sessions)
        sessions_count = len(sessions)

        books_started = sum(
            1 for ub in user_books if ub.started_at and ub.started_at >= week_ago
        )
        books_finished = sum(
            1 for ub in user_books if ub.finished_at and ub.finished_at >= week_ago
        )

        user = session.get(User, user_id)
        email = user.email if user else "unknown"

        report = {
            "user_id": user_id,
            "email": email,
            "books_started": books_started,
            "books_finished": books_finished,
            "pages_read": pages_read,
            "sessions": sessions_count,
            "period_start": week_ago.isoformat(),
            "period_end": datetime.now(UTC).isoformat(),
        }

        logger.info(f"Generated report for user {user_id}: {report}")
        return report


# TODO: Implement send_reminder task when email service is added
# @celery_app.task
# def send_reminder(user_id: str, book_id: str) -> dict:
#     """Send a reminder about a book (requires email integration)."""
#     ...
