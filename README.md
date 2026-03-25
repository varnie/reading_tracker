# Reading Tracker API

REST API for tracking reading progress with books, sessions, and statistics.

---

## 1. Development Setup (with Docker)

```bash
# Build and start all services (API + postgres + redis)
docker compose up -d

# Start with Celery worker + beat scheduler
docker compose --profile celery up -d

# View logs
docker compose logs -f api
docker compose logs -f worker

# Stop
docker compose down -v
```

**API:** http://localhost:8000

---

## 2. Development Setup (without Docker)

```bash
# Install dependencies
uv sync --extra dev

# Start infrastructure in Docker only
docker compose up -d postgres redis

# Run API
uv run uvicorn app.main:app --reload

# Run Celery worker (in another terminal)
uv run celery -A app.tasks.celery_app worker --loglevel=info

# Run Celery beat scheduler (in another terminal)
uv run celery -A app.tasks.celery_app beat --loglevel=info

# Stop infrastructure
docker compose stop postgres redis
```

**API:** http://localhost:8000

---

## 3. Production Setup (with Docker)

```bash
# Build and start all services (uses .env.prod for secrets)
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d

# View logs
docker compose -f docker-compose.prod.yml logs -f api
docker compose -f docker-compose.prod.yml logs -f worker

# Stop
docker compose -f docker-compose.prod.yml down -v
```

**API:** http://localhost:8001
**PostgreSQL:** localhost:5433
**Redis:** localhost:6380

> **Required:** `--env-file .env.prod` provides secrets (JWT_SECRET_KEY, passwords).

### Environment Variables

| Variable | Default | Description |
|---------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://...` | PostgreSQL connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection string |
| `JWT_SECRET_KEY` | `change-me...` | JWT signing key (change in prod!) |
| `TRUSTED_PROXIES` | empty | Comma-separated trusted proxy IPs |
| `RATE_LIMIT_MAX_FAILED_ATTEMPTS` | 5 | Failed attempts before lockout |
| `RATE_LIMIT_LOCKOUT_DURATION_MINUTES` | 15 | Lockout duration in minutes |

---

## 4. Development Tools

### Running Tests

**Without Docker:**
```bash
uv run pytest
```

**With Docker:**
```bash
docker compose exec api python -m pytest
```

**Options:**
```bash
# Run with coverage
uv run pytest --cov=app --cov-report=term-missing

# Run specific test file
uv run pytest tests/unit/test_auth/

# Run with verbose output
uv run pytest -v

# Run without coverage (faster)
uv run pytest -q
```

### Linting

**Without Docker:**
```bash
uv run ruff check .
uv run ruff format .
```

**With Docker:**
```bash
docker compose exec api ruff check .
docker compose exec api ruff format .
```

### Type Checking

**Without Docker:**
```bash
uv run mypy app/
```

---

## Tech Stack

| Component | Tool |
|-----------|------|
| API | FastAPI |
| Database | PostgreSQL + asyncpg |
| ORM | SQLAlchemy 2.0 (async) |
| Cache/Broker | Redis |
| Background Tasks | Celery |
| Auth | JWT (access + refresh rotation) + Argon2 |
| Search | PostgreSQL full-text search |
| Rate Limiting | Redis + FastAPI dependency (Lua atomic) |
| Python Tools | uv + ruff |

---

## Security Features

- **Rate limiting** - Per-IP with Lua atomic operations, granular per-endpoint limits
- **Account lockout** - Auto-lock after 5 failed login attempts (15 min)
- **Proxy-aware** - Respects `X-Forwarded-For` with trusted proxy config
- **JWT rotation** - Access + refresh token with automatic rotation
- **Token blacklist** - Instant logout revocation

---

## API Documentation

Once running, access:
- Swagger UI: http://localhost:8000/docs (dev) or http://localhost:8001/docs (prod)
- ReDoc: http://localhost:8000/redoc (dev) or http://localhost:8001/redoc (prod)

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login and get tokens |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| POST | `/api/v1/auth/logout` | Logout and revoke tokens |
| GET | `/api/v1/books` | List user's books |
| POST | `/api/v1/books` | Add book from catalog |
| PATCH | `/api/v1/books/{id}` | Update book status/progress |
| DELETE | `/api/v1/books/{id}` | Remove book from library |
| POST | `/api/v1/books/{id}/sessions` | Start reading session |
| PATCH | `/api/v1/books/{id}/sessions/{sid}` | Update session |
| DELETE | `/api/v1/books/{id}/sessions/{sid}` | Delete session |
| GET | `/api/v1/catalog` | Search catalog |
| GET | `/api/v1/catalog/{id}` | Get catalog book |
| GET | `/api/v1/catalog/popular` | Popular books |
| GET | `/api/v1/stats` | User statistics |
| GET | `/api/v1/stats/top-users` | Top readers leaderboard |

---

## Project Structure

```
reading_tracker/
├── app/
│   ├── core/                    # Config, security, redis, logging
│   ├── shared/                  # Base models, events, dependencies
│   ├── features/                # Feature modules (auth, books, etc.)
│   ├── tasks/                   # Celery tasks
│   └── main.py                  # Application factory
├── tests/
│   ├── unit/
│   └── integration/
├── docs/                          # Architecture + production notes
├── Dockerfile                   # Multi-stage build
├── docker-compose.yml           # Development
├── docker-compose.prod.yml      # Production (uses .env.prod)
└── README.md
```

---

## Documentation Files

- [docs/README.prod.md](docs/README.prod.md) - Production Deployment
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - Architecture
