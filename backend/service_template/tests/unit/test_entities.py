"""
Tests for Domain Layer - Entities

100% coverage required per Padrão Pagani.
"""
import pytest
from datetime import datetime
from uuid import UUID

from service_template.domain.entities import Entity, ExampleEntity


class TestEntity:
    """Tests for base Entity class."""

    def test_entity_creation(self) -> None:
        """Test entity is created with ID and timestamps."""
        entity = Entity()
        
        assert isinstance(entity.id, UUID)
        assert isinstance(entity.created_at, datetime)
        assert isinstance(entity.updated_at, datetime)

    def test_entity_equality_same_id(self) -> None:
        """Test entities with same ID are equal."""
        entity1 = Entity()
        entity2 = Entity()
        entity2.id = entity1.id
        
        assert entity1 == entity2

    def test_entity_equality_different_id(self) -> None:
        """Test entities with different IDs are not equal."""
        entity1 = Entity()
        entity2 = Entity()
        
        assert entity1 != entity2

    def test_entity_equality_different_type(self) -> None:
        """Test entity not equal to non-entity."""
        entity = Entity()
        
        assert entity != "not an entity"
        assert entity != 123
        assert entity != None

    def test_entity_hash(self) -> None:
        """Test entity can be hashed."""
        entity = Entity()
        
        hash_value = hash(entity)
        assert isinstance(hash_value, int)
        
        # Same entity should have same hash
        assert hash(entity) == hash_value


class TestExampleEntity:
    """Tests for ExampleEntity."""

    def test_creation_minimal(self) -> None:
        """Test entity creation with minimal fields."""
        entity = ExampleEntity(name="test")
        
        assert entity.name == "test"
        assert entity.description is None
        assert entity.status == "active"
        assert entity.extra_data == {}
        assert isinstance(entity.id, UUID)

    def test_creation_full(self) -> None:
        """Test entity creation with all fields."""
        entity = ExampleEntity(
            name="test",
            description="Test description",
            status="inactive",
            extra_data={"key": "value"}
        )
        
        assert entity.name == "test"
        assert entity.description == "Test description"
        assert entity.status == "inactive"
        assert entity.extra_data == {"key": "value"}

    def test_activate_from_inactive(self) -> None:
        """Test activating inactive entity."""
        entity = ExampleEntity(name="test", status="inactive")
        initial_updated = entity.updated_at
        
        entity.activate()
        
        assert entity.status == "active"
        assert entity.updated_at > initial_updated

    def test_activate_already_active_raises(self) -> None:
        """Test activating already active entity raises error."""
        entity = ExampleEntity(name="test", status="active")
        
        with pytest.raises(ValueError, match="already active"):
            entity.activate()

    def test_deactivate_from_active(self) -> None:
        """Test deactivating active entity."""
        entity = ExampleEntity(name="test", status="active")
        initial_updated = entity.updated_at
        
        entity.deactivate()
        
        assert entity.status == "inactive"
        assert entity.updated_at > initial_updated

    def test_deactivate_already_inactive_raises(self) -> None:
        """Test deactivating already inactive entity raises error."""
        entity = ExampleEntity(name="test", status="inactive")
        
        with pytest.raises(ValueError, match="already inactive"):
            entity.deactivate()

    def test_update_extra_data(self) -> None:
        """Test updating extra_data."""
        entity = ExampleEntity(name="test")
        initial_updated = entity.updated_at
        
        entity.update_extra_data("key1", "value1")
        
        assert entity.extra_data == {"key1": "value1"}
        assert entity.updated_at > initial_updated

    def test_update_extra_data_multiple_keys(self) -> None:
        """Test updating extra_data with multiple keys."""
        entity = ExampleEntity(name="test")
        
        entity.update_extra_data("key1", "value1")
        entity.update_extra_data("key2", "value2")
        
        assert entity.extra_data == {"key1": "value1", "key2": "value2"}

    def test_update_extra_data_overwrites_existing(self) -> None:
        """Test updating extra_data overwrites existing value."""
        entity = ExampleEntity(name="test", extra_data={"key": "old"})
        
        entity.update_extra_data("key", "new")
        
        assert entity.extra_data == {"key": "new"}
