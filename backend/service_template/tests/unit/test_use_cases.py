"""
Tests for Application Layer - Use Cases

100% coverage required.
"""
import pytest
from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

from service_template.application.use_cases import (
    CreateEntityUseCase,
    DeleteEntityUseCase,
    GetEntityUseCase,
    ListEntitiesUseCase,
    UpdateEntityUseCase,
)
from service_template.domain.entities import ExampleEntity
from service_template.domain.exceptions import (
    EntityAlreadyExistsError,
    EntityNotFoundError,
)


class TestCreateEntityUseCase:
    """Tests for CreateEntityUseCase."""

    @pytest.mark.asyncio
    async def test_create_success(self) -> None:
        """Test successful entity creation."""
        repo = AsyncMock()
        repo.get_by_name.return_value = None
        created_entity = ExampleEntity(name="test", description="desc")
        repo.create.return_value = created_entity
        
        use_case = CreateEntityUseCase(repo)
        result = await use_case.execute("test", "desc")
        
        assert result == created_entity
        repo.get_by_name.assert_awaited_once_with("test")
        repo.create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_already_exists(self) -> None:
        """Test creation when entity already exists."""
        repo = AsyncMock()
        repo.get_by_name.return_value = ExampleEntity(name="test")
        
        use_case = CreateEntityUseCase(repo)
        
        with pytest.raises(EntityAlreadyExistsError):
            await use_case.execute("test")


class TestGetEntityUseCase:
    """Tests for GetEntityUseCase."""

    @pytest.mark.asyncio
    async def test_get_success(self) -> None:
        """Test successful entity retrieval."""
        entity_id = uuid4()
        entity = ExampleEntity(name="test")
        entity.id = entity_id
        
        repo = AsyncMock()
        repo.get_by_id.return_value = entity
        
        use_case = GetEntityUseCase(repo)
        result = await use_case.execute(entity_id)
        
        assert result == entity
        repo.get_by_id.assert_awaited_once_with(entity_id)

    @pytest.mark.asyncio
    async def test_get_not_found(self) -> None:
        """Test get when entity not found."""
        entity_id = uuid4()
        repo = AsyncMock()
        repo.get_by_id.return_value = None
        
        use_case = GetEntityUseCase(repo)
        
        with pytest.raises(EntityNotFoundError):
            await use_case.execute(entity_id)


class TestUpdateEntityUseCase:
    """Tests for UpdateEntityUseCase."""

    @pytest.mark.asyncio
    async def test_update_name_success(self) -> None:
        """Test successful name update."""
        entity_id = uuid4()
        entity = ExampleEntity(name="old", description="desc")
        entity.id = entity_id
        
        repo = AsyncMock()
        repo.get_by_id.return_value = entity
        repo.get_by_name.return_value = None
        repo.update.return_value = entity
        
        use_case = UpdateEntityUseCase(repo)
        result = await use_case.execute(entity_id, name="new")
        
        assert result.name == "new"
        repo.update.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_description_success(self) -> None:
        """Test successful description update."""
        entity_id = uuid4()
        entity = ExampleEntity(name="test", description="old")
        entity.id = entity_id
        
        repo = AsyncMock()
        repo.get_by_id.return_value = entity
        repo.update.return_value = entity
        
        use_case = UpdateEntityUseCase(repo)
        result = await use_case.execute(entity_id, description="new")
        
        assert result.description == "new"

    @pytest.mark.asyncio
    async def test_update_not_found(self) -> None:
        """Test update when entity not found."""
        entity_id = uuid4()
        repo = AsyncMock()
        repo.get_by_id.return_value = None
        
        use_case = UpdateEntityUseCase(repo)
        
        with pytest.raises(EntityNotFoundError):
            await use_case.execute(entity_id, name="new")

    @pytest.mark.asyncio
    async def test_update_name_conflict(self) -> None:
        """Test update when new name conflicts."""
        entity_id = uuid4()
        entity = ExampleEntity(name="old")
        entity.id = entity_id
        
        other_entity = ExampleEntity(name="new")
        other_entity.id = uuid4()
        
        repo = AsyncMock()
        repo.get_by_id.return_value = entity
        repo.get_by_name.return_value = other_entity
        
        use_case = UpdateEntityUseCase(repo)
        
        with pytest.raises(EntityAlreadyExistsError):
            await use_case.execute(entity_id, name="new")

    @pytest.mark.asyncio
    async def test_update_same_name_allowed(self) -> None:
        """Test update with same name is allowed."""
        entity_id = uuid4()
        entity = ExampleEntity(name="test")
        entity.id = entity_id
        
        repo = AsyncMock()
        repo.get_by_id.return_value = entity
        repo.get_by_name.return_value = entity
        repo.update.return_value = entity
        
        use_case = UpdateEntityUseCase(repo)
        result = await use_case.execute(entity_id, name="test")
        
        repo.update.assert_awaited_once()


class TestDeleteEntityUseCase:
    """Tests for DeleteEntityUseCase."""

    @pytest.mark.asyncio
    async def test_delete_success(self) -> None:
        """Test successful entity deletion."""
        entity_id = uuid4()
        entity = ExampleEntity(name="test")
        
        repo = AsyncMock()
        repo.get_by_id.return_value = entity
        repo.delete.return_value = True
        
        use_case = DeleteEntityUseCase(repo)
        result = await use_case.execute(entity_id)
        
        assert result is True
        repo.delete.assert_awaited_once_with(entity_id)

    @pytest.mark.asyncio
    async def test_delete_not_found(self) -> None:
        """Test delete when entity not found."""
        entity_id = uuid4()
        repo = AsyncMock()
        repo.get_by_id.return_value = None
        
        use_case = DeleteEntityUseCase(repo)
        
        with pytest.raises(EntityNotFoundError):
            await use_case.execute(entity_id)


class TestListEntitiesUseCase:
    """Tests for ListEntitiesUseCase."""

    @pytest.mark.asyncio
    async def test_list_default_params(self) -> None:
        """Test list with default parameters."""
        entities = [ExampleEntity(name=f"test{i}") for i in range(3)]
        
        repo = AsyncMock()
        repo.list_all.return_value = entities
        
        use_case = ListEntitiesUseCase(repo)
        result = await use_case.execute()
        
        assert result == entities
        repo.list_all.assert_awaited_once_with(limit=100, offset=0)

    @pytest.mark.asyncio
    async def test_list_custom_params(self) -> None:
        """Test list with custom parameters."""
        entities = [ExampleEntity(name=f"test{i}") for i in range(10)]
        
        repo = AsyncMock()
        repo.list_all.return_value = entities
        
        use_case = ListEntitiesUseCase(repo)
        result = await use_case.execute(limit=10, offset=5)
        
        repo.list_all.assert_awaited_once_with(limit=10, offset=5)

    @pytest.mark.asyncio
    async def test_list_limit_too_large(self) -> None:
        """Test list with limit > 1000 defaults to 100."""
        repo = AsyncMock()
        repo.list_all.return_value = []
        
        use_case = ListEntitiesUseCase(repo)
        await use_case.execute(limit=2000)
        
        repo.list_all.assert_awaited_once_with(limit=100, offset=0)

    @pytest.mark.asyncio
    async def test_list_limit_zero(self) -> None:
        """Test list with limit 0 defaults to 100."""
        repo = AsyncMock()
        repo.list_all.return_value = []
        
        use_case = ListEntitiesUseCase(repo)
        await use_case.execute(limit=0)
        
        repo.list_all.assert_awaited_once_with(limit=100, offset=0)

    @pytest.mark.asyncio
    async def test_list_negative_offset(self) -> None:
        """Test list with negative offset defaults to 0."""
        repo = AsyncMock()
        repo.list_all.return_value = []
        
        use_case = ListEntitiesUseCase(repo)
        await use_case.execute(offset=-5)
        
        repo.list_all.assert_awaited_once_with(limit=100, offset=0)
