"""
Tests for Domain Layer - Events

100% coverage required.
"""
from datetime import datetime
from uuid import UUID

from service_template.domain.events import (
    DomainEvent,
    EntityCreated,
    EntityDeleted,
    EntityUpdated,
)


class TestDomainEvent:
    """Tests for base DomainEvent."""

    def test_creation(self) -> None:
        """Test domain event creation."""
        event = DomainEvent()

        assert isinstance(event.event_id, UUID)
        assert isinstance(event.occurred_at, datetime)
        assert isinstance(event.aggregate_id, UUID)
        assert event.event_type == ""

    def test_custom_values(self) -> None:
        """Test domain event with custom values."""
        custom_id = UUID("12345678-1234-5678-1234-567812345678")
        event = DomainEvent(aggregate_id=custom_id, event_type="custom")

        assert event.aggregate_id == custom_id
        assert event.event_type == "custom"


class TestEntityCreated:
    """Tests for EntityCreated event."""

    def test_creation(self) -> None:
        """Test entity created event."""
        event = EntityCreated()

        assert isinstance(event.entity_id, UUID)
        assert event.entity_data == {}
        assert event.event_type == "entity_created"

    def test_with_data(self) -> None:
        """Test entity created event with data."""
        entity_id = UUID("12345678-1234-5678-1234-567812345678")
        data = {"name": "test", "status": "active"}

        event = EntityCreated(entity_id=entity_id, entity_data=data)

        assert event.entity_id == entity_id
        assert event.entity_data == data


class TestEntityUpdated:
    """Tests for EntityUpdated event."""

    def test_creation(self) -> None:
        """Test entity updated event."""
        event = EntityUpdated()

        assert isinstance(event.entity_id, UUID)
        assert event.changes == {}
        assert event.event_type == "entity_updated"

    def test_with_changes(self) -> None:
        """Test entity updated event with changes."""
        entity_id = UUID("12345678-1234-5678-1234-567812345678")
        changes = {"name": "new_name", "status": "inactive"}

        event = EntityUpdated(entity_id=entity_id, changes=changes)

        assert event.entity_id == entity_id
        assert event.changes == changes


class TestEntityDeleted:
    """Tests for EntityDeleted event."""

    def test_creation(self) -> None:
        """Test entity deleted event."""
        event = EntityDeleted()

        assert isinstance(event.entity_id, UUID)
        assert event.event_type == "entity_deleted"

    def test_with_entity_id(self) -> None:
        """Test entity deleted event with specific ID."""
        entity_id = UUID("12345678-1234-5678-1234-567812345678")

        event = EntityDeleted(entity_id=entity_id)

        assert event.entity_id == entity_id
