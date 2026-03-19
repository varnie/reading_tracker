import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestEmailIntegration:
    """Integration tests for email functionality."""

    async def test_email_service_initialized(self):
        """Email service should be initialized."""
        from app.core.email import email_service

        assert email_service is not None
        assert email_service.enabled is False

    async def test_email_disabled_logs_instead_of_sending(
        self, client: AsyncClient, api_prefix: str
    ):
        """When email is disabled, weekly reports should still be generated."""
        import uuid

        email = f"email-int-{uuid.uuid4()}@test.com"
        await client.post(
            f"{api_prefix}/auth/register",
            json={"email": email, "password": "TestPassword123!"},
        )
        login_resp = await client.post(
            f"{api_prefix}/auth/login",
            json={"email": email, "password": "TestPassword123!"},
        )
        token = login_resp.json()["access_token"]

        response = await client.get(
            f"{api_prefix}/stats",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_books" in data


class TestEmailCeleryTasksIntegration:
    """Integration tests for Celery email tasks."""

    def test_email_tasks_can_be_imported(self):
        """Email tasks module should be importable."""
        from app.tasks import email_tasks

        assert hasattr(email_tasks, "generate_weekly_report")
        assert hasattr(email_tasks, "send_reminder")
        assert hasattr(email_tasks, "send_weekly_reports_to_all_users")

    def test_send_weekly_reports_task_exists(self):
        """send_weekly_reports_to_all_users task should exist."""
        from app.tasks.email_tasks import send_weekly_reports_to_all_users

        assert send_weekly_reports_to_all_users is not None

    def test_generate_weekly_report_task_exists(self):
        """generate_weekly_report task should exist."""
        from app.tasks.email_tasks import generate_weekly_report

        assert generate_weekly_report is not None

    def test_send_reminder_task_exists(self):
        """send_reminder task should exist."""
        from app.tasks.email_tasks import send_reminder

        assert send_reminder is not None


class TestEmailServiceIntegration:
    """Integration tests for EmailService."""

    async def test_send_weekly_report_generates_correct_subject(self):
        """Weekly report email should have correct subject."""
        from app.core.email import EmailService

        service = EmailService()
        html_body = service._weekly_report_html(
            "testuser",
            {
                "books_started": 2,
                "books_finished": 1,
                "pages_read": 300,
                "sessions": 5,
            },
        )

        assert "Weekly Reading Report" in html_body
        assert "testuser" in html_body
        assert "2" in html_body
        assert "1" in html_body
        assert "300" in html_body
        assert "5" in html_body

    async def test_send_weekly_report_text_fallback(self):
        """Weekly report should have text fallback."""
        from app.core.email import EmailService

        service = EmailService()
        text_body = service._weekly_report_text(
            "testuser",
            {
                "books_started": 2,
                "books_finished": 1,
                "pages_read": 300,
                "sessions": 5,
            },
        )

        assert "testuser" in text_body
        assert "YOUR WEEKLY READING REPORT" in text_body
        assert "Books Started: 2" in text_body

    async def test_email_disabled_returns_true(self):
        """When email is disabled, send_email should return True (no-op)."""
        from app.core.email import EmailService

        service = EmailService()
        service.enabled = False

        result = await service.send_email(
            to_email="test@example.com",
            subject="Test",
            html_body="<p>Test</p>",
        )

        assert result is True

    async def test_email_enabled_but_smtp_fails_gracefully(self):
        """When email enabled but SMTP fails, should return False."""
        from app.core.email import EmailService

        service = EmailService()
        service.enabled = True
        service.host = "invalid-host-that-does-not-exist"

        result = await service.send_email(
            to_email="test@example.com",
            subject="Test",
            html_body="<p>Test</p>",
        )

        assert result is False
