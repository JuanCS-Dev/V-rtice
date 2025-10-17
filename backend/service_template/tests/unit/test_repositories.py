"""
Tests for Infrastructure Layer - SQLAlchemy Repositories

100% coverage required.
"""
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from service_template.domain.entities import ExampleEntity
from service_template.infrastructure.database import ExampleModel, SQLAlchemyExampleRepository


class TestSQLAlchemyExampleRepository:
    """Tests for SQLAlchemyExampleRepository."""

    def setup_method(self) -> None:
        """Setup test fixtures."""
        self.session = AsyncMock()
        self.repo = SQLAlchemyExampleRepository(self.session)

    def test_to_entity(self) -> None:
        """Test model to entity conversion."""
        model = ExampleModel(
            id=uuid4(),
            name="test",
            description="desc",
            status="active",
            extra_data={"key": "value"}
        )

        entity = self.repo._to_entity(model)

        assert entity.id == model.id
        assert entity.name == "test"
        assert entity.description == "desc"
        assert entity.status == "active"
        assert entity.extra_data == {"key": "value"}

    def test_to_model(self) -> None:
        """Test entity to model conversion."""
        entity = ExampleEntity(
            name="test",
            description="desc",
            status="inactive",
            extra_data={"test": "data"}
        )

        model = self.repo._to_model(entity)

        assert model.name == "test"
        assert model.description == "desc"
        assert model.status == "inactive"
        assert model.extra_data == {"test": "data"}

    @pytest.mark.asyncio
    async def test_create(self) -> None:
        """Test creating entity."""
        entity = ExampleEntity(
            name="test",
            description="test desc"
        )

        self.session.add = AsyncMock()
        self.session.commit = AsyncMock()
        self.session.refresh = AsyncMock()

        result = await self.repo.create(entity)

        self.session.add.assert_called_once()
        self.session.commit.assert_awaited_once()
        self.session.refresh.assert_awaited_once()
        assert result.name == "test"

    @pytest.mark.asyncio
    async def test_get_by_id_found(self) -> None:
        """Test getting entity by ID - found."""
        entity_id = uuid4()
        model = ExampleModel(
            id=entity_id,
            name="test",
            status="active"
        )

        # Mock must return actual value, not coroutine
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = lambda: model
        self.session.execute = AsyncMock(return_value=mock_result)

        result = await self.repo.get_by_id(entity_id)

        assert result is not None
        assert result.id == entity_id

    @pytest.mark.asyncio
    async def test_get_by_name_found(self) -> None:
        """Test getting entity by name - found."""
        model = ExampleModel(
            name="test",
            status="active"
        )

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = lambda: model
        self.session.execute = AsyncMock(return_value=mock_result)

        result = await self.repo.get_by_name("test")

        assert result is not None
        assert result.name == "test"

    @pytest.mark.asyncio
    async def test_list_all(self) -> None:
        """Test listing all entities."""
        models = [
            ExampleModel(name=f"test{i}")
            for i in range(3)
        ]

        # Mock chain: execute() -> result -> scalars() -> scalars_result -> all()
        mock_scalars_result = AsyncMock()
        mock_scalars_result.all = lambda: models

        mock_result = AsyncMock()
        mock_result.scalars = lambda: mock_scalars_result

        self.session.execute = AsyncMock(return_value=mock_result)

        entities = await self.repo.list_all(limit=10, offset=0)

        assert len(entities) == 3

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self) -> None:
        """Test getting entity by ID - not found."""
        from service_template.domain.exceptions import EntityNotFoundError

        entity_id = uuid4()

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = lambda: None
        self.session.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(EntityNotFoundError):
            await self.repo.get_by_id(entity_id)

    @pytest.mark.asyncio
    async def test_update_success(self) -> None:
        """Test updating entity - success."""
        entity = ExampleEntity(
            name="updated",
            description="new desc",
            status="inactive"
        )
        entity._id = uuid4()  # Set ID for update

        model = ExampleModel(
            id=entity.id,
            name="old",
            status="active"
        )

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = lambda: model
        self.session.execute = AsyncMock(return_value=mock_result)
        self.session.commit = AsyncMock()
        self.session.refresh = AsyncMock()

        await self.repo.update(entity)

        assert model.name == "updated"
        assert model.description == "new desc"
        assert model.status == "inactive"
        self.session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_not_found(self) -> None:
        """Test updating entity - not found."""
        from service_template.domain.exceptions import EntityNotFoundError

        entity = ExampleEntity(name="test", description="test")
        entity._id = uuid4()

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = lambda: None
        self.session.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(EntityNotFoundError):
            await self.repo.update(entity)

    @pytest.mark.asyncio
    async def test_delete_success(self) -> None:
        """Test deleting entity - success."""
        entity_id = uuid4()
        model = ExampleModel(id=entity_id, name="test", status="active")

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = lambda: model
        self.session.execute = AsyncMock(return_value=mock_result)
        self.session.delete = AsyncMock()
        self.session.commit = AsyncMock()

        await self.repo.delete(entity_id)

        self.session.delete.assert_awaited_once()
        self.session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_not_found(self) -> None:
        """Test deleting entity - not found."""
        from service_template.domain.exceptions import EntityNotFoundError

        entity_id = uuid4()

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = lambda: None
        self.session.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(EntityNotFoundError):
            await self.repo.delete(entity_id)

    @pytest.mark.asyncio
    async def test_count(self) -> None:
        """Test counting entities."""
        mock_result = AsyncMock()
        mock_result.scalar = lambda: 42
        self.session.execute = AsyncMock(return_value=mock_result)

        result = await self.repo.count()

        assert result == 42

    @pytest.mark.asyncio
    async def test_count_zero(self) -> None:
        """Test counting entities when None returned."""
        mock_result = AsyncMock()
        mock_result.scalar = lambda: None
        self.session.execute = AsyncMock(return_value=mock_result)

        result = await self.repo.count()

        assert result == 0
