import logging

from app.core.redis import Cache, get_redis_client
from app.shared.events import Event, event_bus

_cache: Cache | None = None


def _get_cache() -> Cache:
    """Get cached Cache instance (for event handlers)."""
    global _cache
    if _cache is None:
        redis_client = get_redis_client()
        _cache = Cache(redis_client)
    return _cache


class StatsEvents:
    """Events emitted by stats feature (internal handlers)."""

    @staticmethod
    async def on_book_finished(event: Event) -> None:
        """Handler: invalidate user stats cache when book is finished."""
        cache = _get_cache()
        user_id = event.data.get("user_id")
        if user_id:
            await cache.delete(f"user_stats:{user_id}")
            await cache.invalidate_pattern("leaderboard:*")

    @staticmethod
    async def on_book_added(event: Event) -> None:
        """Handler: invalidate user stats cache when book is added."""
        cache = _get_cache()
        user_id = event.data.get("user_id")
        if user_id:
            await cache.delete(f"user_stats:{user_id}")
            await cache.invalidate_pattern("leaderboard:*")

    @staticmethod
    async def on_session_created(event: Event) -> None:
        """Handler: invalidate user stats cache when session is created."""
        cache = _get_cache()
        user_id = event.data.get("user_id")
        if user_id:
            await cache.delete(f"user_stats:{user_id}")
            await cache.invalidate_pattern("leaderboard:*")

    @staticmethod
    async def on_book_deleted(event: Event) -> None:
        """Handler: invalidate user stats cache when book is deleted."""
        cache = _get_cache()
        user_id = event.data.get("user_id")
        if user_id:
            await cache.delete(f"user_stats:{user_id}")
            await cache.invalidate_pattern("leaderboard:*")

    @staticmethod
    async def on_catalog_book_added(event: Event) -> None:
        """Handler: invalidate catalog stats cache when book is added."""
        cache = _get_cache()
        await cache.delete("catalog:stats")

    @staticmethod
    async def on_user_registered(event: Event) -> None:
        """Handler: track new user registration for weekly reports."""
        logger = logging.getLogger(__name__)
        cache = _get_cache()
        user_id = event.data.get("user_id")
        email = event.data.get("email")

        if user_id:
            await cache.set(
                f"user:{user_id}:registered", {"email": email}, ttl=86400 * 365
            )
            logger.info(f"Tracked new user registration: {email}")
            await cache.invalidate_pattern("stats:active_users:*")

    @staticmethod
    async def on_user_logged_in(event: Event) -> None:
        """Handler: track user login for activity reports."""

        logger = logging.getLogger(__name__)
        cache = _get_cache()
        user_id = event.data.get("user_id")

        if user_id:
            await cache.set(f"user:{user_id}:last_login", event.data, ttl=86400 * 30)
            logger.debug(f"Tracked user login: {user_id}")


def register_stats_handlers() -> None:
    """Register handlers for stats events."""
    event_bus.subscribe("books.book_finished", StatsEvents.on_book_finished)
    event_bus.subscribe("books.book_added", StatsEvents.on_book_added)
    event_bus.subscribe("books.session_created", StatsEvents.on_session_created)
    event_bus.subscribe("books.book_deleted", StatsEvents.on_book_deleted)
    event_bus.subscribe(
        "catalog.book_added", StatsEvents.on_catalog_book_added
    )
    event_bus.subscribe("auth.user_registered", StatsEvents.on_user_registered)
    event_bus.subscribe("auth.user_logged_in", StatsEvents.on_user_logged_in)
