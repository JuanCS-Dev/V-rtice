"""
Domain Layer - Entities

Business entities with domain logic.
Pure Python, no framework dependencies.
"""
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass
class Entity:
    """Base entity with ID and timestamps."""

    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __eq__(self, other: object) -> bool:
        """Entities are equal if they have the same ID."""
        if not isinstance(other, Entity):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on ID."""
        return hash(self.id)


@dataclass
class ExampleEntity:
    """Example domain entity with business logic."""

    name: str
    description: str | None = None
    status: str = "active"
    extra_data: dict[str, str] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __eq__(self, other: object) -> bool:
        """Entities are equal if they have the same ID."""
        if not isinstance(other, ExampleEntity):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on ID."""
        return hash(self.id)

    def update(self, name: str | None = None, description: str | None = None) -> None:
        """Update entity fields."""
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        self.updated_at = datetime.now(UTC)

    def activate(self) -> None:
        """Activate the entity.

        Raises:
            ValueError: If entity is already active.
        """
        if self.status == "active":
            raise ValueError("Entity is already active")
        self.status = "active"
        self.updated_at = datetime.now(UTC)

    def deactivate(self) -> None:
        """Deactivate the entity.

        Raises:
            ValueError: If entity is already inactive.
        """
        if self.status == "inactive":
            raise ValueError("Entity is already inactive")
        self.status = "inactive"
        self.updated_at = datetime.now(UTC)

    def update_extra_data(self, key: str, value: str) -> None:
        """Update extra_data dictionary.

        Args:
            key: Data key.
            value: Data value.
        """
        self.extra_data[key] = value
        self.updated_at = datetime.now(UTC)
