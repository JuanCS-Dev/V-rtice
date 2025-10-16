"""
Domain Layer - Domain Events

Events that represent significant domain occurrences.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4


@dataclass
class DomainEvent:
    """Base domain event."""

    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    aggregate_id: UUID = field(default_factory=uuid4)
    event_type: str = ""


@dataclass
class EntityCreated(DomainEvent):
    """Event: Entity was created."""

    entity_id: UUID = field(default_factory=uuid4)
    entity_data: dict[str, Any] = field(default_factory=dict)
    event_type: str = "entity_created"


@dataclass
class EntityUpdated(DomainEvent):
    """Event: Entity was updated."""

    entity_id: UUID = field(default_factory=uuid4)
    changes: dict[str, Any] = field(default_factory=dict)
    event_type: str = "entity_updated"


@dataclass
class EntityDeleted(DomainEvent):
    """Event: Entity was deleted."""

    entity_id: UUID = field(default_factory=uuid4)
    event_type: str = "entity_deleted"
