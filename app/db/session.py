from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings


class DatabaseSessionManager:
    """Database session manager - the FastAPI way."""

    def __init__(self) -> None:
        self._engine = create_async_engine(
            settings.database_url,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            echo=settings.is_development,
        )
        self._session_maker = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )

    async def close(self) -> None:
        """Close database connections."""
        await self._engine.dispose()

    async def get_session(self) -> AsyncGenerator[AsyncSession]:
        """Get database session as async context manager."""
        async with self._session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def init_db(self) -> None:
        """Initialize database tables."""
        import app.models  # noqa: F401 - imports all models to register them
        from app.models.base import Base

        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)


db_manager = DatabaseSessionManager()


async def init_db() -> None:
    """Initialize database tables."""
    await db_manager.init_db()


async def close_db() -> None:
    """Close database connections."""
    await db_manager.close()


async def get_db() -> AsyncGenerator[AsyncSession]:
    """Dependency to get database session."""
    async with db_manager._session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
