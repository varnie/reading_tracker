from celery import Celery

from app.core.config import settings


celery_app = Celery(
    "reading_tracker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.book_tasks",
        "app.tasks.stats_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

celery_app.conf.beat_schedule = {
    "check-abandoned-books": {
        "task": "app.tasks.book_tasks.check_abandoned_books",
        "schedule": 86400.0,  # Daily
    },
    "calculate-user-streaks": {
        "task": "app.tasks.stats_tasks.calculate_user_streaks",
        "schedule": 86400.0,  # Daily
    },
    "update-leaderboard": {
        "task": "app.tasks.stats_tasks.update_leaderboard",
        "schedule": 3600.0,  # Hourly
    },
    "cleanup-old-sessions": {
        "task": "app.tasks.book_tasks.cleanup_old_sessions",
        "schedule": 604800.0,  # Weekly (Monday)
    },
}
