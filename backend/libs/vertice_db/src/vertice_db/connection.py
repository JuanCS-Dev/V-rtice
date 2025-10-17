"""Database connection management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from vertice_core import get_logger

logger = get_logger(__name__)


class DatabaseConnection:
    """Async PostgreSQL connection manager."""

    def __init__(self, url: str, pool_size: int = 10, max_overflow: int = 20) -> None:
        self.url = url

        engine_kwargs: dict[str, Any] = {"echo": False}
        if not url.startswith("sqlite"):
            engine_kwargs.update({
                "pool_size": pool_size,
                "max_overflow": max_overflow,
                "pool_pre_ping": True,
            })

        self.engine: AsyncEngine = create_async_engine(url, **engine_kwargs)
        self._session_factory: sessionmaker[AsyncSession] = sessionmaker(  # type: ignore[type-var,call-overload]
            self.engine, class_=AsyncSession, expire_on_commit=False,
        )

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get async session."""
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def close(self) -> None:  # pragma: no cover
        """Close engine."""
        await self.engine.dispose()


def create_db_connection(database_url: str) -> DatabaseConnection:
    """Create database connection."""
    return DatabaseConnection(database_url)
