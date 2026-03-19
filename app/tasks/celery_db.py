from contextlib import contextmanager

import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_engine = None
_session_factory = None
_redis_client = None


def get_sync_engine():
    """Get or create synchronous database engine for Celery tasks."""
    global _engine
    if _engine is None:
        sync_url = settings.database_url.replace(
            "postgresql+asyncpg://", "postgresql+psycopg2://"
        )
        _engine = create_engine(
            sync_url,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            echo=settings.is_development,
        )
    return _engine


def get_session_factory():
    """Get or create session factory."""
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(
            bind=get_sync_engine(),
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
    return _session_factory


def get_scoped_session():
    """Get thread-safe scoped session factory."""
    return scoped_session(get_session_factory())


@contextmanager
def get_sync_session():
    """Get a sync database session with automatic commit/rollback."""
    factory = get_scoped_session()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        factory.remove()


def get_sync_redis() -> redis.Redis:
    """Get synchronous Redis client for Celery tasks."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.redis_url,
            decode_responses=True,
        )
    return _redis_client
