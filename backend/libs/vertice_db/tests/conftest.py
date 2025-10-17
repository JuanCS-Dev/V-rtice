"""Pytest fixtures for vertice_db tests."""

from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from vertice_db import Base


@pytest.fixture()
async def db_engine():
    """Create test database engine."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture()
async def db_session(db_engine):
    """Create test database session."""
    async_session = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        async with session.begin():
            yield session
            await session.rollback()


@pytest.fixture()
def mock_async_engine():
    """Mock async SQLAlchemy engine."""
    engine = AsyncMock(spec=AsyncEngine)
    engine.dispose = AsyncMock()
    engine.url = "postgresql+asyncpg://localhost/test"
    engine.echo = False
    return engine
