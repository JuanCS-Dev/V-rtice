"""
Tests for Domain Layer - Repository Interfaces

100% coverage required.
"""
from uuid import uuid4

import pytest
from service_template.domain.entities import ExampleEntity
from service_template.domain.repositories import ExampleRepository


class ConcreteRepository(ExampleRepository):
    """Concrete implementation for testing abstract methods."""

    async def create(self, entity: ExampleEntity) -> ExampleEntity:
        """Test implementation."""
        await super().create(entity)  # Trigger abstract pass
        return entity

    async def get_by_id(self, entity_id) -> ExampleEntity:
        """Test implementation."""
        await super().get_by_id(entity_id)  # Trigger abstract pass
        return ExampleEntity(name="test", description="test")

    async def get_by_name(self, name: str) -> ExampleEntity | None:
        """Test implementation."""
        await super().get_by_name(name)  # Trigger abstract pass
        return None

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[ExampleEntity]:
        """Test implementation."""
        await super().list_all(limit, offset)  # Trigger abstract pass
        return []

    async def update(self, entity: ExampleEntity) -> ExampleEntity:
        """Test implementation."""
        await super().update(entity)  # Trigger abstract pass
        return entity

    async def delete(self, entity_id) -> None:
        """Test implementation."""
        await super().delete(entity_id)  # Trigger abstract pass

    async def count(self) -> int:
        """Test implementation."""
        await super().count()  # Trigger abstract pass
        return 0


class TestExampleRepository:
    """Tests for ExampleRepository ABC."""

    @pytest.mark.asyncio
    async def test_create_contract(self) -> None:
        """Test create method exists and is callable."""
        repo = ConcreteRepository()
        entity = ExampleEntity(name="test", description="test")

        result = await repo.create(entity)

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_by_id_contract(self) -> None:
        """Test get_by_id method exists and is callable."""
        repo = ConcreteRepository()
        entity_id = uuid4()

        result = await repo.get_by_id(entity_id)

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_by_name_contract(self) -> None:
        """Test get_by_name method exists and is callable."""
        repo = ConcreteRepository()

        result = await repo.get_by_name("test")

        assert result is None

    @pytest.mark.asyncio
    async def test_list_all_contract(self) -> None:
        """Test list_all method exists and is callable."""
        repo = ConcreteRepository()

        result = await repo.list_all(limit=10, offset=0)

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_update_contract(self) -> None:
        """Test update method exists and is callable."""
        repo = ConcreteRepository()
        entity = ExampleEntity(name="test", description="test")

        result = await repo.update(entity)

        assert result is not None

    @pytest.mark.asyncio
    async def test_delete_contract(self) -> None:
        """Test delete method exists and is callable."""
        repo = ConcreteRepository()
        entity_id = uuid4()

        await repo.delete(entity_id)

    @pytest.mark.asyncio
    async def test_count_contract(self) -> None:
        """Test count method exists and is callable."""
        repo = ConcreteRepository()

        result = await repo.count()

        assert result == 0

    def test_cannot_instantiate_abc(self) -> None:
        """Test ABC cannot be instantiated directly."""
        with pytest.raises(TypeError):
            ExampleRepository()  # type: ignore
