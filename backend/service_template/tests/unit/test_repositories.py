"""
Tests for Infrastructure Layer - SQLAlchemy Repositories

100% coverage required.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from service_template.domain.entities import ExampleEntity
from service_template.infrastructure.repositories import SQLAlchemyExampleRepository
from service_template.infrastructure.models import ExampleModel


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
            extra_data={"key": "value"}
        )
        
        model = self.repo._to_model(entity)
        
        assert model.id == entity.id
        assert model.name == "test"
        assert model.description == "desc"
        assert model.status == "inactive"
        assert model.extra_data == {"key": "value"}

    @pytest.mark.asyncio
    async def test_create(self) -> None:
        """Test create entity."""
        entity = ExampleEntity(name="test")
        
        self.session.flush = AsyncMock()
        self.session.refresh = AsyncMock()
        
        result = await self.repo.create(entity)
        
        self.session.add.assert_called_once()
        self.session.flush.assert_awaited_once()
        self.session.refresh.assert_awaited_once()
        assert result.name == "test"

    @pytest.mark.asyncio
    async def test_get_by_id_found(self) -> None:
        """Test get by ID when entity exists."""
        entity_id = uuid4()
        model = ExampleModel(id=entity_id, name="test")
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = model
        self.session.execute = AsyncMock(return_value=mock_result)
        
        result = await self.repo.get_by_id(entity_id)
        
        assert result is not None
        assert result.id == entity_id

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self) -> None:
        """Test get by ID when entity doesn't exist."""
        entity_id = uuid4()
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        self.session.execute = AsyncMock(return_value=mock_result)
        
        result = await self.repo.get_by_id(entity_id)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_name_found(self) -> None:
        """Test get by name when entity exists."""
        model = ExampleModel(name="test")
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = model
        self.session.execute = AsyncMock(return_value=mock_result)
        
        result = await self.repo.get_by_name("test")
        
        assert result is not None
        assert result.name == "test"

    @pytest.mark.asyncio
    async def test_get_by_name_not_found(self) -> None:
        """Test get by name when entity doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        self.session.execute = AsyncMock(return_value=mock_result)
        
        result = await self.repo.get_by_name("nonexistent")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_list_all(self) -> None:
        """Test list all entities."""
        models = [
            ExampleModel(name="test1"),
            ExampleModel(name="test2"),
        ]
        
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = models
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        self.session.execute = AsyncMock(return_value=mock_result)
        
        result = await self.repo.list_all(limit=10, offset=0)
        
        assert len(result) == 2
        assert result[0].name == "test1"
        assert result[1].name == "test2"

    @pytest.mark.asyncio
    async def test_update_success(self) -> None:
        """Test update entity."""
        entity = ExampleEntity(name="updated", description="new")
        model = ExampleModel(id=entity.id, name="old")
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = model
        self.session.execute = AsyncMock(return_value=mock_result)
        self.session.flush = AsyncMock()
        self.session.refresh = AsyncMock()
        
        result = await self.repo.update(entity)
        
        assert model.name == "updated"
        assert model.description == "new"
        self.session.flush.assert_awaited_once()
        self.session.refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_not_found(self) -> None:
        """Test update when entity not found."""
        entity = ExampleEntity(name="test")
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        self.session.execute = AsyncMock(return_value=mock_result)
        
        with pytest.raises(ValueError, match="not found"):
            await self.repo.update(entity)

    @pytest.mark.asyncio
    async def test_delete_success(self) -> None:
        """Test delete entity."""
        entity_id = uuid4()
        model = ExampleModel(id=entity_id, name="test")
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = model
        self.session.execute = AsyncMock(return_value=mock_result)
        self.session.delete = AsyncMock()
        self.session.flush = AsyncMock()
        
        result = await self.repo.delete(entity_id)
        
        assert result is True
        self.session.delete.assert_awaited_once_with(model)
        self.session.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_not_found(self) -> None:
        """Test delete when entity not found."""
        entity_id = uuid4()
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        self.session.execute = AsyncMock(return_value=mock_result)
        
        result = await self.repo.delete(entity_id)
        
        assert result is False

    @pytest.mark.asyncio
    async def test_count(self) -> None:
        """Test count entities."""
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 42
        self.session.execute = AsyncMock(return_value=mock_result)
        
        result = await self.repo.count()
        
        assert result == 42
