"""Integration tests for database layer."""

import pytest
from service_template.infrastructure.config import Settings
from service_template.infrastructure.database import Database, ExampleModel
from sqlalchemy import text


@pytest.fixture
async def db() -> Database:
    """Create test database."""
    settings = Settings(
        database_url="sqlite+aiosqlite:///:memory:",

    )
    database = Database(settings.database_url)
    await database.create_tables()
    yield database
    await database.close()


@pytest.mark.integration
class TestDatabase:
    """Integration tests for Database class."""

    async def test_database_connection(self, db: Database) -> None:
        """Test database connectivity."""
        async with db.session() as session:
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1

    async def test_create_tables(self, db: Database) -> None:
        """Test table creation."""
        async with db.session() as session:
            result = await session.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='examples'")
            )
            assert result.scalar() == "examples"

    async def test_session_context_manager(self, db: Database) -> None:
        """Test session context manager."""
        async with db.session() as session:
            model = ExampleModel(name="Test", description="Desc", status="active")
            session.add(model)
            await session.commit()
            await session.refresh(model)
            assert model.id is not None

    async def test_transaction_rollback(self, db: Database) -> None:
        """Test transaction rollback."""
        try:
            async with db.session() as session:
                model = ExampleModel(name="Test", description="Desc", status="active")
                session.add(model)
                await session.commit()
                raise ValueError("Force rollback")
        except ValueError:
            pass

        async with db.session() as session:
            result = await session.execute(text("SELECT COUNT(*) FROM examples"))
            count = result.scalar()
            assert count == 1
