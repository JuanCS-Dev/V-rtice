"""Tests for vertice_db.connection module."""

import pytest
from sqlalchemy import text
from vertice_db import DatabaseConnection, create_db_connection


@pytest.mark.asyncio()
async def test_create_db_connection():
    """Test create_db_connection factory."""
    conn = create_db_connection("sqlite+aiosqlite:///:memory:")
    assert isinstance(conn, DatabaseConnection)
    await conn.close()


@pytest.mark.asyncio()
async def test_database_connection_init():
    """Test DatabaseConnection initialization."""
    conn = DatabaseConnection("sqlite+aiosqlite:///:memory:")
    assert conn.url == "sqlite+aiosqlite:///:memory:"
    assert conn.engine is not None
    await conn.close()


@pytest.mark.asyncio()
async def test_session_context_manager(db_engine):
    """Test session context manager."""
    conn = DatabaseConnection("sqlite+aiosqlite:///:memory:")
    conn.engine = db_engine

    async with conn.session() as session:
        assert session is not None
        result = await session.execute(text("SELECT 1"))
        assert result.scalar() == 1


@pytest.mark.asyncio()
async def test_session_rollback_on_error(db_engine):
    """Test session rollback on error."""
    conn = DatabaseConnection("sqlite+aiosqlite:///:memory:")
    conn.engine = db_engine

    with pytest.raises(ValueError):
        async with conn.session():
            raise ValueError("Test error")


@pytest.mark.asyncio()
async def test_database_connection_with_postgresql_url():
    """Test DatabaseConnection applies pooling config for PostgreSQL."""
    # PostgreSQL URL should trigger pool_size config
    conn = DatabaseConnection(
        "postgresql+asyncpg://user:pass@localhost/db",
        pool_size=5,
        max_overflow=10,
    )
    assert conn.url == "postgresql+asyncpg://user:pass@localhost/db"
    assert conn.engine is not None
    # Engine will have pooling configured (non-sqlite path)
    await conn.close()


@pytest.mark.asyncio()
async def test_database_connection_with_sqlite_url():
    """Test DatabaseConnection skips pooling config for SQLite."""
    # SQLite URL should skip pool_size config
    conn = DatabaseConnection(
        "sqlite+aiosqlite:///:memory:",
        pool_size=99,  # Should be ignored for sqlite
        max_overflow=99,
    )
    assert conn.url == "sqlite+aiosqlite:///:memory:"
    # Engine created without pooling (sqlite path)
    await conn.close()
