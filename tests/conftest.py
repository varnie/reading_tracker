import uuid
from collections.abc import AsyncGenerator
from unittest.mock import patch
from uuid import UUID

import fakeredis.aioredis
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

FIXED_UUID = UUID("12345678-1234-5678-1234-567812345678")


@pytest_asyncio.fixture(scope="function")
async def fake_redis():
    """Create fake Redis for tests."""
    return fakeredis.aioredis.FakeRedis(decode_responses=True)


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create test database engine with SQLite."""
    from app.models.base import Base

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
    from app.core.redis import Cache, TokenBlacklist, get_blacklist, get_cache

    uuid_patch = patch("uuid.uuid4", return_value=FIXED_UUID)
    models_uuid_patch = patch("app.models.base.uuid.uuid4", return_value=FIXED_UUID)
    redis_patch = patch("app.core.redis.get_redis_client", return_value=fake_redis)

    uuid_patch.start()
    models_uuid_patch.start()
    redis_patch.start()

    from app.main import app

    app.state.testing = True

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
    app.dependency_overrides[get_cache] = lambda: Cache(fake_redis)
    app.dependency_overrides[get_blacklist] = lambda: TokenBlacklist(fake_redis)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    app.state.testing = False
    redis_patch.stop()
    uuid_patch.stop()
    models_uuid_patch.stop()


@pytest_asyncio.fixture(scope="function")
async def auth_client(client, api_prefix) -> tuple[AsyncClient, str]:
    """Client with valid auth token. Returns (client, token)."""
    email = f"auth-{uuid.uuid4().hex[:8]}@test.com"
    await client.post(
        f"{api_prefix}/auth/register",
        json={"email": email, "password": "TestPassword123!"},
    )
    resp = await client.post(
        f"{api_prefix}/auth/login",
        json={"email": email, "password": "TestPassword123!"},
    )
    token = resp.json()["access_token"]
    return client, token


@pytest.fixture
def api_prefix() -> str:
    """Get API prefix from settings."""
    from app.core.config import settings

    return f"/api/{settings.app_version}"
