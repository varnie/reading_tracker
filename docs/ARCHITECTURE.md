# Architecture

## Overview

Reading Tracker API uses a feature-based architecture with Event Bus for loose coupling between features.

```
app/
├── core/                    # Infrastructure
├── shared/                  # Common utilities
├── features/                # Feature modules
│   ├── auth/
│   ├── books/
│   ├── catalog/
│   ├── sessions/
│   └── stats/
├── tasks/                   # Celery tasks
├── middleware/              # Custom middleware
└── main.py                  # Application factory
```

## Feature Module Structure

Each feature follows the same pattern:

```
feature/
├── router.py      # FastAPI routes
├── schemas.py     # Pydantic models
├── service.py     # Business logic
├── repository.py  # Data access layer
└── events.py     # Event definitions
```

## Repository Pattern

Data access is abstracted through repositories:

```python
# repository.py
class BookRepository:
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def create(self, ...) -> UserBook:
        ...
    
    async def get_by_id(self, ...) -> UserBook | None:
        ...
```

```python
# service.py
class BookService:
    def __init__(self, session: AsyncSession):
        self._repo = BookRepository(session)
```

Benefits:
- **Testability**: Easy to mock repository
- **Isolation**: Changes to DB don't affect business logic
- **Reusability**: Same repository can be used in different services

## Event Bus

Features communicate through events without direct dependencies:

```python
# books/events.py
class BookEvents:
    @staticmethod
    def book_finished(user_id: str, user_book_id: str) -> Event:
        return Event(
            name="books.book_finished",
            data={"user_id": user_id, "user_book_id": user_book_id},
        )

# books/service.py
await event_bus.publish(BookEvents.book_finished(user_id, book_id))

# stats/events.py
async def on_book_finished(event: Event):
    await cache.delete(f"user_stats:{event.data['user_id']}")

event_bus.subscribe("books.book_finished", on_book_finished)
```

## Event Flow

```
User finishes book
       │
       ▼
books/service.py
       │
       ▼
event_bus.publish("books.book_finished")
       │
       ├──────────────────┐
       ▼                  ▼
stats/events.py     future features
(invalidate cache)  (achievements, etc.)
```

## Adding New Features

1. Create feature folder:
```bash
mkdir app/features/communities/
```

2. Create files:
```python
# schemas.py
class CommunityCreate(BaseModel): ...

# repository.py
class CommunityRepository: ...

# service.py
class CommunityService: ...

# events.py
class CommunityEvents: ...

# router.py
router = APIRouter()
@router.get("/communities", ...)
```

3. Register routes in `app/api/router.py`:
```python
from app.features.communities.router import router as communities_router
api_router.include_router(communities_router)
```

4. Subscribe to events in `app/main.py`:
```python
from app.features.communities.events import register_handlers
register_handlers()
```

## Celery Tasks

Tasks are defined in `app/tasks/` and run by Celery worker.

### Scheduled Tasks

| Task | Schedule | Description |
|------|----------|-------------|
| `check_abandoned_books` | Daily | Mark books without activity > 30 days |
| `calculate_user_streaks` | Daily | Recalculate reading streaks |
| `update_leaderboard` | Hourly | Update Redis cache |
| `cleanup_old_sessions` | Weekly | Delete old reading sessions |

### Triggering Tasks

```python
from app.tasks.book_tasks import generate_weekly_report

# Async (fire and forget)
generate_weekly_report.delay(str(user_id))

# Sync (wait for result)
result = generate_weekly_report.delay(str(user_id)).get()
```

## Redis Usage

| Key Pattern | Purpose | TTL |
|-------------|---------|-----|
| `rate_limit:*` | Rate limiting | 60s |
| `blacklist:*` | JWT token blacklist | Until token expiry |
| `cache:user_stats:*` | User statistics cache | 5 min |
| `cache:leaderboard:*` | Leaderboard cache | 1 hour |

## Database Models

```
users
  │
  ├── refresh_tokens
  │
  └── user_books ──────────────► books (catalog)
         │
         └── reading_sessions
```

- **users**: Authentication
- **books**: Shared catalog (title, author, pages)
- **user_books**: User's personal book (status, progress, rating)
- **reading_sessions**: Reading activity log
- **refresh_tokens**: JWT refresh token storage
