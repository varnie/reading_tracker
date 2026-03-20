# Architecture

Reading Tracker is a FastAPI + async SQLAlchemy backend with Redis-backed caching and Celery for background jobs.

## High-level components

- `app/main.py`: application factory (lifespan), middleware, router mounting, and event handler registration.
- `app/api/router.py`: mounts feature routers under `/api/{app_version}`.
- `app/features/*`: feature modules (auth, books, catalog, sessions, stats). Each feature uses a router -> service -> repository layout.
- `app/core/redis.py`: Redis connection manager and small async helpers (cache + JWT blacklist).
- `app/tasks/*`: Celery tasks for streaks, leaderboard updates, and email reporting.
- `app/shared/events.py`: internal async publish/subscribe bus used to invalidate caches or trigger side effects.

## Data flow (typical request)

1. Request hits FastAPI route in a feature `router.py`.
2. Route calls `service.py` business logic.
3. Service uses `repository.py` for persistence via async SQLAlchemy.
4. For derived data (stats/leaderboards), services read/write Redis cache and/or rely on Celery jobs.
5. Events emitted on state changes can invalidate related caches via `app/shared/events.py`.

