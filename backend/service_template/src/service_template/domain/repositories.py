"""
Domain Layer - Repository Interfaces

Abstract interfaces for data access.
Implementations in infrastructure layer.
"""
from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from .entities import ExampleEntity


class ExampleRepository(ABC):
    """Repository interface for ExampleEntity."""

    @abstractmethod
    async def create(self, entity: ExampleEntity) -> ExampleEntity:
        """Create new entity."""
        pass

    @abstractmethod
    async def get_by_id(self, entity_id: UUID) -> Optional[ExampleEntity]:
        """Get entity by ID."""
        pass

    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[ExampleEntity]:
        """Get entity by name."""
        pass

    @abstractmethod
    async def list_all(
        self, limit: int = 100, offset: int = 0
    ) -> list[ExampleEntity]:
        """List all entities with pagination."""
        pass

    @abstractmethod
    async def update(self, entity: ExampleEntity) -> ExampleEntity:
        """Update existing entity."""
        pass

    @abstractmethod
    async def delete(self, entity_id: UUID) -> bool:
        """Delete entity by ID. Returns True if deleted."""
        pass

    @abstractmethod
    async def count(self) -> int:
        """Count total entities."""
        pass
