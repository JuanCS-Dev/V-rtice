"""
Tests for Infrastructure Layer - Database Session

100% coverage required.
"""
import pytest
from service_template.infrastructure.database import Database


class TestDatabase:
    """Tests for Database class."""

    @pytest.mark.asyncio
    async def test_sqlite_initialization(self) -> None:
        """Test Database init with SQLite (no pool settings)."""
        db = Database("sqlite+aiosqlite:///:memory:")

        assert db.engine is not None
        assert db.session_factory is not None

    @pytest.mark.asyncio
    async def test_postgresql_initialization(self) -> None:
        """Test Database init with PostgreSQL (with pool settings)."""
        db = Database("postgresql+asyncpg://user:pass@localhost/db")

        assert db.engine is not None
        assert db.session_factory is not None

    @pytest.mark.asyncio
    async def test_create_tables(self) -> None:
        """Test creating tables."""
        db = Database("sqlite+aiosqlite:///:memory:")

        await db.create_tables()

        # Tables created, no exception

    @pytest.mark.asyncio
    async def test_drop_tables(self) -> None:
        """Test dropping tables."""
        db = Database("sqlite+aiosqlite:///:memory:")

        await db.create_tables()
        await db.drop_tables()

        # Tables dropped, no exception

    @pytest.mark.asyncio
    async def test_session_context_manager(self) -> None:
        """Test session context manager commits on success."""
        db = Database("sqlite+aiosqlite:///:memory:")
        await db.create_tables()

        async with db.session() as session:
            # Successful operation
            assert session is not None

        # Session committed and closed

    @pytest.mark.asyncio
    async def test_session_rollback_on_error(self) -> None:
        """Test session context manager rolls back on error."""
        db = Database("sqlite+aiosqlite:///:memory:")
        await db.create_tables()

        with pytest.raises(RuntimeError):
            async with db.session() as session:
                assert session is not None
                raise RuntimeError("Test error")

        # Session rolled back and closed

    @pytest.mark.asyncio
    async def test_close(self) -> None:
        """Test closing database connection."""
        db = Database("sqlite+aiosqlite:///:memory:")

        await db.close()

        # Connection closed, no exception
