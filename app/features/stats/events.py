import logging

from app.core.redis import Cache, get_redis_client
from app.shared.events import Event, event_bus

ONE_YEAR = 86400 * 365
ONE_MONTH = 86400 * 30


class StatsHandlers:
    def __init__(self, cache: Cache):
        self.cache = cache

    async def _invalidate_user_stats(self, event: Event) -> None:
        user_id = event.data.get("user_id")
        if user_id:
            await self.cache.delete(f"user_stats:{user_id}")
            await self.cache.invalidate_pattern("leaderboard:*")

    async def on_book_finished(self, event: Event) -> None:
        await self._invalidate_user_stats(event)

    async def on_book_added(self, event: Event) -> None:
        await self._invalidate_user_stats(event)

    async def on_session_created(self, event: Event) -> None:
        await self._invalidate_user_stats(event)

    async def on_book_deleted(self, event: Event) -> None:
        await self._invalidate_user_stats(event)

    async def on_catalog_book_added(self, event: Event) -> None:
        await self.cache.delete("catalog:stats")

    async def on_user_registered(self, event: Event) -> None:
        logger = logging.getLogger(__name__)
        user_id = event.data.get("user_id")
        email = event.data.get("email")

        if user_id:
            await self.cache.set(
                f"user:{user_id}:registered", {"email": email}, ttl=ONE_YEAR
            )
            logger.info(f"Tracked new user registration: {email}")
            await self.cache.invalidate_pattern("stats:active_users:*")

    async def on_user_logged_in(self, event: Event) -> None:
        logger = logging.getLogger(__name__)
        user_id = event.data.get("user_id")

        if user_id:
            await self.cache.set(
                f"user:{user_id}:last_login", event.data, ttl=ONE_MONTH
            )
            logger.debug(f"Tracked user login: {user_id}")


def register_stats_handlers() -> None:
    handlers = StatsHandlers(Cache(get_redis_client()))

    event_bus.subscribe("books.book_finished", handlers.on_book_finished)
    event_bus.subscribe("books.book_added", handlers.on_book_added)
    event_bus.subscribe("books.session_created", handlers.on_session_created)
    event_bus.subscribe("books.book_deleted", handlers.on_book_deleted)
    event_bus.subscribe("catalog.book_added", handlers.on_catalog_book_added)
    event_bus.subscribe("auth.user_registered", handlers.on_user_registered)
    event_bus.subscribe("auth.user_logged_in", handlers.on_user_logged_in)
