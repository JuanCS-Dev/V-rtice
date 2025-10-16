"""
Domain Layer - Entities

Business entities with domain logic.
Pure Python, no framework dependencies.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4


@dataclass
class Entity:
    """Base entity with ID and timestamps."""

    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __eq__(self, other: object) -> bool:
        """Entities are equal if they have the same ID."""
        if not isinstance(other, Entity):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on ID."""
        return hash(self.id)


@dataclass
class ExampleEntity(Entity):
    """Example domain entity - replace with actual domain model."""

    name: str
    description: Optional[str] = None
    status: str = "active"
    metadata: dict[str, str] = field(default_factory=dict)

    def activate(self) -> None:
        """Business logic: activate entity."""
        if self.status == "active":
            raise ValueError(f"Entity {self.id} is already active")
        self.status = "active"
        self.updated_at = datetime.utcnow()

    def deactivate(self) -> None:
        """Business logic: deactivate entity."""
        if self.status == "inactive":
            raise ValueError(f"Entity {self.id} is already inactive")
        self.status = "inactive"
        self.updated_at = datetime.utcnow()

    def update_metadata(self, key: str, value: str) -> None:
        """Business logic: update metadata."""
        self.metadata[key] = value
        self.updated_at = datetime.utcnow()
