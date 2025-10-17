"""Integration tests for repository with real database."""

from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
from service_template.domain.entities import ExampleEntity
from service_template.domain.exceptions import EntityNotFoundError
from service_template.infrastructure.config import Settings
from service_template.infrastructure.database import Database, SQLAlchemyExampleRepository
from sqlalchemy.ext.asyncio import AsyncSession


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


@pytest.fixture
async def session(db: Database) -> AsyncIterator[AsyncSession]:
    """Create database session."""
    async with db.session() as s:
        yield s


@pytest.fixture
def repository(session: AsyncSession) -> SQLAlchemyExampleRepository:
    """Create repository with test database."""
    return SQLAlchemyExampleRepository(session)


@pytest.mark.integration
class TestSQLAlchemyExampleRepositoryIntegration:
    """Integration tests for SQLAlchemy repository."""

    async def test_create_and_retrieve(self, repository: SQLAlchemyExampleRepository) -> None:
        """Test creating and retrieving entity."""
        entity = ExampleEntity(name="Test Entity", description="Test Description")

        created = await repository.create(entity)
        assert created.id == entity.id
        assert created.name == "Test Entity"

        retrieved = await repository.get_by_id(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == "Test Entity"

    async def test_get_by_name(self, repository: SQLAlchemyExampleRepository) -> None:
        """Test retrieving by name."""
        entity = ExampleEntity(name="Unique Name", description="Desc")
        await repository.create(entity)

        found = await repository.get_by_name("Unique Name")
        assert found is not None
        assert found.name == "Unique Name"

    async def test_get_by_name_not_found(self, repository: SQLAlchemyExampleRepository) -> None:
        """Test get by name returns None if not found."""
        result = await repository.get_by_name("NonExistent")
        assert result is None

    async def test_list_all(self, repository: SQLAlchemyExampleRepository) -> None:
        """Test listing all entities."""
        entity1 = ExampleEntity(name="Entity 1", description="Desc 1")
        entity2 = ExampleEntity(name="Entity 2", description="Desc 2")

        await repository.create(entity1)
        await repository.create(entity2)

        entities = await repository.list_all(limit=10, offset=0)
        assert len(entities) == 2
        names = {e.name for e in entities}
        assert "Entity 1" in names
        assert "Entity 2" in names

    async def test_list_with_pagination(self, repository: SQLAlchemyExampleRepository) -> None:
        """Test pagination."""
        for i in range(5):
            entity = ExampleEntity(name=f"Entity {i}", description=f"Desc {i}")
            await repository.create(entity)

        page1 = await repository.list_all(limit=2, offset=0)
        assert len(page1) == 2

        page2 = await repository.list_all(limit=2, offset=2)
        assert len(page2) == 2

        page1_ids = {e.id for e in page1}
        page2_ids = {e.id for e in page2}
        assert page1_ids.isdisjoint(page2_ids)

    async def test_update(self, repository: SQLAlchemyExampleRepository) -> None:
        """Test updating entity."""
        entity = ExampleEntity(name="Original", description="Original desc")
        created = await repository.create(entity)

        created.name = "Updated"
        created.description = "Updated desc"
        updated = await repository.update(created)

        assert updated.name == "Updated"
        assert updated.description == "Updated desc"

        retrieved = await repository.get_by_id(created.id)
        assert retrieved is not None
        assert retrieved.name == "Updated"

    async def test_delete(self, repository: SQLAlchemyExampleRepository) -> None:
        """Test deleting entity."""
        entity = ExampleEntity(name="To Delete", description="Desc")
        created = await repository.create(entity)

        await repository.delete(created.id)

        with pytest.raises(EntityNotFoundError):
            await repository.get_by_id(created.id)

    async def test_count(self, repository: SQLAlchemyExampleRepository) -> None:
        """Test counting entities."""
        initial_count = await repository.count()

        entity1 = ExampleEntity(name="Entity 1", description="Desc")
        entity2 = ExampleEntity(name="Entity 2", description="Desc")

        await repository.create(entity1)
        await repository.create(entity2)

        final_count = await repository.count()
        assert final_count == initial_count + 2

    async def test_get_by_id_not_found_raises(self, repository: SQLAlchemyExampleRepository) -> None:
        """Test get_by_id raises when entity not found."""
        fake_id = uuid4()
        with pytest.raises(EntityNotFoundError) as exc_info:
            await repository.get_by_id(fake_id)

        assert str(fake_id) in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_save_nonexistent_raises(self, repo: SQLAlchemyExampleRepository) -> None:
        """Test save non-existent entity raises error."""
        entity = ExampleEntity(name="test")
        entity.id = uuid4()  # Non-existent ID

        with pytest.raises(EntityNotFoundError):
            await repo.save(entity)

    @pytest.mark.asyncio
    async def test_delete_nonexistent_raises(self, repo: SQLAlchemyExampleRepository) -> None:
        """Test delete non-existent entity raises error."""
        entity_id = uuid4()

        with pytest.raises(EntityNotFoundError):
            await repo.delete(entity_id)
