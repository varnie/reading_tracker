# ===========================================
# Stage 1: Builder - Install dependencies
# ===========================================
FROM python:3.13-slim as builder

WORKDIR /app

# Install build dependencies in single layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first for layer caching
# Layer is invalidated only when dependencies change
COPY pyproject.toml uv.lock ruff.toml ./

# Install production dependencies
RUN uv sync --frozen --no-install-project --no-dev

# ===========================================
# Stage 2: Production API
# ===========================================
FROM python:3.13-slim as production

WORKDIR /app

# Runtime dependencies only - no build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get autoremove -y \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_INPUT=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_PREFER_BINARY=1

# Copy application code with ownership
COPY --chown=1000:1000 app/ ./app/

# Create non-root user with configurable UID/GID
ARG APP_UID=1000
ARG APP_GID=1000

RUN groupadd --gid ${APP_GID} appgroup \
    && useradd --uid ${APP_UID} --gid ${APP_GID} --shell /bin/bash --create-home appuser \
    && chown -R ${APP_UID}:${APP_GID} /app

USER ${APP_UID}:${APP_GID}

ENV APP_DATA_DIR=/home/appuser/data

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Production command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# ===========================================
# Stage 3: Production Worker
# ===========================================
FROM python:3.13-slim as production-worker

WORKDIR /app

# Runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY --chown=1000:1000 app/ ./app/

RUN groupadd --gid 1000 appgroup \
    && useradd --uid 1000 --gid 1000 --shell /bin/bash --create-home appuser \
    && chown -R 1000:1000 /app

USER 1000:1000

CMD ["celery", "-A", "app.tasks.celery_app", "worker", "--loglevel=info", "--concurrency=4"]
