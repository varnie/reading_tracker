import asyncio
from collections.abc import AsyncGenerator, Generator
from typing import Any
from unittest.mock import patch
from uuid import UUID

import fakeredis.aioredis
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

FIXED_UUID = UUID("12345678-1234-5678-1234-567812345678")


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop]:
    """Create event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def fake_redis():
    """Create fake Redis for tests."""
    return fakeredis.aioredis.FakeRedis(decode_responses=True)


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create test database engine with SQLite."""
    from app.shared.models import Base

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_session_maker(test_engine):
    """Create test session maker."""
    return async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest_asyncio.fixture(scope="function")
async def client(fake_redis, test_session_maker) -> AsyncGenerator[AsyncClient]:
    """Create a test client with fake Redis and SQLite."""
    import app.features.stats.service as stats_service_module

    redis_patch = patch("app.core.redis.get_redis", return_value=fake_redis)
    stats_patch = patch.object(
        stats_service_module, "get_redis", return_value=fake_redis
    )
    uuid_patch = patch("uuid.uuid4", return_value=FIXED_UUID)
    models_uuid_patch = patch("app.shared.models.uuid.uuid4", return_value=FIXED_UUID)

    redis_patch.start()
    stats_patch.start()
    uuid_patch.start()
    models_uuid_patch.start()

    from app.main import app

    async def mock_get_db():
        async with test_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides.clear()

    from app.shared.dependencies import get_db

    app.dependency_overrides[get_db] = mock_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    uuid_patch.stop()
    models_uuid_patch.stop()
    stats_patch.stop()
    redis_patch.stop()


@pytest.fixture
def api_prefix() -> str:
    """Get API prefix from settings."""
    from app.core.config import settings

    return f"/api/{settings.app_version}"


@pytest.fixture
def mock_user() -> dict[str, Any]:
    """Create a mock user."""
    return {
        "id": "12345678-1234-5678-1234-567812345678",
        "email": "test@example.com",
        "password": "TestPassword123!",
    }


@pytest.fixture
def mock_book() -> dict[str, Any]:
    """Create a mock book."""
    return {
        "title": "1984",
        "author": "George Orwell",
        "isbn": "978-0451524935",
        "pages_total": 328,
        "description": "Dystopian novel",
    }
