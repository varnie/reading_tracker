# Reading Tracker API

REST API for tracking reading progress with books, sessions, and statistics.

## Features

- **Books Management**: Add books from catalog, track personal progress
- **Reading Sessions**: Log reading sessions with pages and notes
- **Statistics**: Personal stats, reading streaks, top users leaderboard
- **Catalog**: Shared book catalog for all users
- **Celery Tasks**: Weekly reports, abandoned books detection, leaderboard updates
- **Event-Driven Architecture**: Features communicate via Event Bus
- **Repository Pattern**: Clean data access layer
- **Event-Driven Analytics**: User registration/login tracking
- **Email Notifications**: Weekly reports, reading reminders (optional)

## Tech Stack

| Component | Tool |
|-----------|------|
| API | FastAPI |
| Database | PostgreSQL + asyncpg |
| ORM | SQLAlchemy 2.0 (async) |
| Cache/Broker | Redis |
| Background Tasks | Celery |
| Auth | JWT (access + refresh rotation) + Argon2 |
| Email | aiosmtplib (SMTP) |
| Python Tools | uv + ruff |
| Testing | pytest + pytest-cov |

## Quick Start

### Option 1: Hybrid (Recommended)

API runs locally via uv, infrastructure in Docker.

```bash
# 1. Clone and enter directory
cd reading_tracker

# 2. Copy environment config (optional - defaults work for local dev)
# cp .env.example .env

# 3. Start infrastructure
docker compose up -d postgres redis

# 4. Install all dependencies (including dev)
uv sync --extra dev

# 5. Run API (in one terminal)
uv run uvicorn app.main:app --reload

# 6. Run Celery worker (in another terminal)
uv run celery -A app.tasks.celery_app worker --loglevel=info

# 7. Run Celery beat scheduler (optional, for scheduled tasks)
uv run celery -A app.tasks.celery_app beat --loglevel=info

# 8. Run tests
uv run pytest

# 9. Linting
uv run ruff check
uv run ruff format
```

> **Note:** `--extra dev` installs `dev` optional dependencies (pytest, ruff, etc.). Without it, only production dependencies are installed.

### Option 2: Full Docker

Everything runs in Docker Compose.

```bash
# 1. Start API only (uses .env.docker for Docker service names)
docker compose up -d api

# 2. Start API + Celery (worker + beat)
docker compose --profile celery up -d

# 3. View logs
docker compose logs -f api
docker compose logs -f worker
docker compose logs -f beat

# 4. Run tests
docker compose exec api python -m pytest

# 5. Linting
docker compose exec api ruff check .
```

### Option 3: Production Docker

Runs production containers with separate project name and ports to avoid conflicts with dev.

```bash
# Start production stack
docker compose -f docker-compose.prod.yml -p reading_tracker_prod --env-file .env.prod up -d

# View logs
docker compose -p reading_tracker_prod logs -f api
docker compose -p reading_tracker_prod logs -f worker

# Stop production stack
docker compose -p reading_tracker_prod down -v
```

> **Note:** The `--env-file .env.prod` flag is required to provide secrets (JWT_SECRET_KEY, passwords).
>
> **Ports:** API (8001), PostgreSQL (5433), Redis (6380) - different from dev to allow running both simultaneously.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_ENV` | `development` or `production` | `development` |
| `DATABASE_URL` | PostgreSQL connection string | postgresql+asyncpg://... |
| `REDIS_URL` | Redis connection string | redis://localhost:6379/0 |
| `JWT_SECRET_KEY` | Secret for JWT tokens | (change in production!) |
| `LOG_LEVEL` | Logging level | `INFO` |
| `RATE_LIMIT_PER_MINUTE` | API rate limit | `60` |
| `CORS_ORIGINS` | Allowed origins (comma-separated) | localhost:3000,localhost:8080 |
| `EMAIL_ENABLED` | Enable email sending | `false` |
| `SMTP_HOST` | SMTP server host | `localhost` |
| `SMTP_PORT` | SMTP server port | `587` |
| `SMTP_USER` | SMTP username | (empty) |
| `SMTP_PASSWORD` | SMTP password | (empty) |
| `SMTP_FROM_EMAIL` | From email address | noreply@readingtracker.app |

**Environment files:**
- `.env` - Local development (uses `localhost` for services)
- `.env.docker` - Docker Compose (uses `postgres`, `redis` service names)

## API Endpoints

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login and get tokens |
| POST | `/auth/refresh` | Refresh access token |
| POST | `/auth/logout` | Invalidate tokens |

### Books (Personal)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/books` | List user's books |
| POST | `/books` | Add book from catalog |
| GET | `/books/{id}` | Get book details |
| PATCH | `/books/{id}` | Update book |
| DELETE | `/books/{id}` | Remove book |
| POST | `/books/{id}/sessions` | Start reading session |
| GET | `/books/{id}/sessions` | List sessions |

### Catalog
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/catalog` | Search catalog |
| POST | `/catalog` | Add book to catalog |

### Stats
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/stats` | User statistics |
| GET | `/stats/top-users` | Top readers leaderboard |

## Project Structure

```
reading_tracker/
├── app/
│   ├── core/                    # Config, security, redis, logging
│   ├── shared/                  # Base models, events, dependencies
│   ├── features/                # Feature modules (auth, books, etc.)
│   │   ├── auth/
│   │   ├── books/
│   │   ├── catalog/
│   │   ├── sessions/
│   │   └── stats/
│   ├── tasks/                   # Celery tasks
│   ├── db/                      # Database session
│   └── main.py                  # Application factory
├── tests/
│   ├── unit/
│   └── integration/
├── docs/
│   ├── README.prod.md           # Production deployment
│   └── ARCHITECTURE.md           # Architecture documentation
└── docker-compose.yml
```

## Testing

> **Prerequisite:** Run `uv sync --extra dev` first to install test dependencies.

```bash
# Run all tests with coverage
uv run pytest --cov=app --cov-report=term-missing --cov-fail-under=70

# Run specific test file
uv run pytest tests/unit/test_auth/

# Run with verbose output
uv run pytest -v

# Run tests without coverage (faster)
uv run pytest -q
```

## Stopping

```bash
# Stop infrastructure only (hybrid)
docker compose stop postgres redis

# Stop dev Docker setup
docker compose down -v

# Stop production Docker setup
docker compose -p reading_tracker_prod down -v
```

## API Documentation

Once running, access the interactive API docs at:
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Documentation Files

See also:
- [docs/README.prod.md](docs/README.prod.md) - Production Deployment
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - Architecture
