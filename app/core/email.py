import asyncio
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import aiosmtplib

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Async email service using SMTP."""

    def __init__(self) -> None:
        self.host = settings.smtp_host
        self.port = settings.smtp_port
        self.user = settings.smtp_user
        self.password = settings.smtp_password
        self.from_email = settings.smtp_from_email
        self.from_name = settings.smtp_from_name
        self.tls = settings.smtp_tls
        self.enabled = settings.email_enabled

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str | None = None,
    ) -> bool:
        """
        Send an email via SMTP.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML content of the email
            text_body: Plain text fallback (optional)

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.info(f"Email disabled - would send to {to_email}: {subject}")
            return True

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{self.from_name} <{self.from_email}>"
        message["To"] = to_email

        if text_body:
            message.attach(MIMEText(text_body, "plain"))
        message.attach(MIMEText(html_body, "html"))

        try:
            await aiosmtplib.send(
                message,
                hostname=self.host,
                port=self.port,
                username=self.user if self.user else None,
                password=self.password if self.password else None,
                start_tls=self.tls,
            )
            logger.info(f"Email sent to {to_email}: {subject}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    async def send_weekly_report(
        self,
        to_email: str,
        user_name: str,
        stats: dict[str, Any],
    ) -> bool:
        """
        Send weekly reading report email.

        Args:
            to_email: Recipient email
            user_name: User's name or email prefix
            stats: Report statistics

        Returns:
            True if sent successfully
        """
        subject = f"Your Weekly Reading Report"
        html_body = self._weekly_report_html(user_name, stats)
        text_body = self._weekly_report_text(user_name, stats)

        return await self.send_email(to_email, subject, html_body, text_body)

    def _weekly_report_html(self, user_name: str, stats: dict[str, Any]) -> str:
        """Generate HTML for weekly report."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #4A90D9; color: white; padding: 20px; text-align: center; }}
                .stats {{ display: flex; flex-wrap: wrap; gap: 10px; margin: 20px 0; }}
                .stat {{ background: #f5f5f5; padding: 15px; border-radius: 8px; flex: 1; min-width: 120px; text-align: center; }}
                .stat-value {{ font-size: 2em; font-weight: bold; color: #4A90D9; }}
                .stat-label {{ color: #666; font-size: 0.9em; }}
                .footer {{ text-align: center; color: #666; font-size: 0.8em; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📚 Your Weekly Reading Report</h1>
                    <p>Hello {user_name}!</p>
                </div>

                <h2>This Week's Stats</h2>
                <div class="stats">
                    <div class="stat">
                        <div class="stat-value">{stats.get("books_started", 0)}</div>
                        <div class="stat-label">Books Started</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">{stats.get("books_finished", 0)}</div>
                        <div class="stat-label">Books Finished</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">{stats.get("pages_read", 0)}</div>
                        <div class="stat-label">Pages Read</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">{stats.get("sessions", 0)}</div>
                        <div class="stat-label">Reading Sessions</div>
                    </div>
                </div>

                <p>Keep up the great work! Every page counts towards your reading goals.</p>

                <div class="footer">
                    <p>Reading Tracker API</p>
                </div>
            </div>
        </body>
        </html>
        """

    def _weekly_report_text(self, user_name: str, stats: dict[str, Any]) -> str:
        """Generate plain text for weekly report."""
        return f"""
Hi {user_name}!

YOUR WEEKLY READING REPORT

This Week's Stats:
- Books Started: {stats.get("books_started", 0)}
- Books Finished: {stats.get("books_finished", 0)}
- Pages Read: {stats.get("pages_read", 0)}
- Reading Sessions: {stats.get("sessions", 0)}

Keep up the great work!

---
Reading Tracker API
"""


email_service = EmailService()
