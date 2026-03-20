import asyncio
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core.email import email_service
from app.models.reading_session import ReadingSession
from app.models.user import User
from app.models.user_book import UserBook
from app.tasks.celery_app import celery_app
from app.tasks.celery_db import get_sync_session

logger = logging.getLogger(__name__)


@celery_app.task
def generate_weekly_report(user_id: str) -> dict:
    """
    Generate and send weekly reading report email to a user.

    Args:
        user_id: User ID to generate report for

    Returns:
        Report data with sending status.
    """
    logger.info(f"Generating weekly report for user {user_id}")

    with get_sync_session() as session:
        week_ago = datetime.now(UTC) - timedelta(days=7)

        user = session.get(User, user_id)
        if not user:
            logger.warning(f"User {user_id} not found")
            return {"sent": False, "reason": "User not found"}

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

        stats = {
            "books_started": books_started,
            "books_finished": books_finished,
            "pages_read": pages_read,
            "sessions": sessions_count,
        }

        user_name = user.email.split("@")[0]

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            sent = loop.run_until_complete(
                email_service.send_weekly_report(user.email, user_name, stats)
            )
        finally:
            loop.close()

        report = {
            "user_id": user_id,
            "email": user.email,
            "sent": sent,
            **stats,
        }

        logger.info(f"Report for {user_id}: sent={sent}")
        return report


@celery_app.task
def send_reminder(user_id: str, book_id: str) -> dict:
    """
    Send a reminder email about a book.

    Args:
        user_id: User ID
        book_id: Book ID to remind about

    Returns:
        Reminder status.
    """
    logger.info(f"Sending reminder for user {user_id}, book {book_id}")

    with get_sync_session() as session:
        user = session.get(User, user_id)
        if not user:
            logger.warning(f"User {user_id} not found")
            return {"sent": False, "reason": "User not found"}

        user_book = session.execute(
            select(UserBook).where(UserBook.user_id == user_id, UserBook.id == book_id)
        ).scalar_one_or_none()

        if not user_book:
            logger.warning(f"UserBook {book_id} not found for user {user_id}")
            return {"sent": False, "reason": "Book not found"}

        last_session = session.execute(
            select(ReadingSession)
            .where(ReadingSession.user_book_id == book_id)
            .order_by(ReadingSession.started_at.desc())
            .limit(1)
        ).scalar_one_or_none()

        if last_session:
            days_since = (datetime.now(UTC) - last_session.started_at).days
            message = f"You haven't read in {days_since} days"
        else:
            days_since = (
                (datetime.now(UTC) - user_book.started_at).days
                if user_book.started_at
                else 0
            )
            message = f"You haven't started reading in {days_since} days"

        subject = "Reading Reminder"
        html_body = f"""
        <h2>Time to Read!</h2>
        <p>{message}</p>
        <p>Open the app to continue your reading journey.</p>
        """

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            sent = loop.run_until_complete(
                email_service.send_email(user.email, subject, html_body)
            )
        finally:
            loop.close()

        return {"sent": sent, "user_email": user.email}


@celery_app.task
def send_weekly_reports_to_all_users() -> dict:
    """
    Send weekly reports to all active users.

    Returns:
        Summary of sent reports.
    """
    logger.info("Sending weekly reports to all users")

    with get_sync_session() as session:
        users = session.execute(select(User)).scalars().all()

        sent_count = 0
        failed_count = 0

        for user in users:
            report = generate_weekly_report(str(user.id))
            if report.get("sent"):
                sent_count += 1
            else:
                failed_count += 1

        logger.info(f"Sent {sent_count} reports, {failed_count} failed")
        return {"sent": sent_count, "failed": failed_count}
