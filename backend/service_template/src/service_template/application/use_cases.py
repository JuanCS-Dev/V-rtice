"""
Application Layer - Use Cases

Business use cases orchestrating domain logic.
Framework-independent application logic.
"""
from uuid import UUID

from ..domain.entities import ExampleEntity
from ..domain.events import EntityCreated, EntityDeleted, EntityUpdated
from ..domain.exceptions import EntityAlreadyExistsError
from ..domain.repositories import ExampleRepository


class CreateEntityUseCase:
    """Use case: Create new entity."""

    def __init__(self, repository: ExampleRepository) -> None:
        self.repository = repository

    async def execute(self, name: str, description: str | None = None) -> ExampleEntity:
        """Execute use case."""
        # Check if entity already exists
        existing = await self.repository.get_by_name(name)
        if existing:
            raise EntityAlreadyExistsError(name, "ExampleEntity")

        # Create new entity
        entity = ExampleEntity(name=name, description=description)

        # Persist
        created_entity = await self.repository.create(entity)

        # Emit domain event (in real system, use event bus)
        EntityCreated(entity_id=created_entity.id, entity_data={"name": name})

        return created_entity


class GetEntityUseCase:
    """Use case: Get entity by ID."""

    def __init__(self, repository: ExampleRepository) -> None:
        self.repository = repository

    async def execute(self, entity_id: UUID) -> ExampleEntity:
        """Execute use case.

        Raises:
            EntityNotFoundError: If entity not found.
        """
        return await self.repository.get_by_id(entity_id)


class UpdateEntityUseCase:
    """Use case: Update entity."""

    def __init__(self, repository: ExampleRepository) -> None:
        self.repository = repository

    async def execute(
        self,
        entity_id: UUID,
        name: str | None = None,
        description: str | None = None,
    ) -> ExampleEntity:
        """Execute use case.

        Raises:
            EntityNotFoundError: If entity not found.
            EntityAlreadyExistsError: If new name already exists.
        """
        # Get existing entity
        entity = await self.repository.get_by_id(entity_id)

        # Track changes
        changes: dict[str, str] = {}

        # Update fields
        if name and name != entity.name:
            # Check name uniqueness
            existing = await self.repository.get_by_name(name)
            if existing and existing.id != entity_id:
                raise EntityAlreadyExistsError(name, "ExampleEntity")
            entity.name = name
            changes["name"] = name

        if description is not None and description != entity.description:
            entity.description = description
            changes["description"] = description

        # Persist
        updated_entity = await self.repository.update(entity)

        # Emit event if there were changes
        if changes:
            EntityUpdated(entity_id=entity_id, changes=changes)

        return updated_entity


class DeleteEntityUseCase:
    """Use case: Delete entity."""

    def __init__(self, repository: ExampleRepository) -> None:
        self.repository = repository

    async def execute(self, entity_id: UUID) -> None:
        """Execute use case.

        Raises:
            EntityNotFoundError: If entity not found.
        """
        # This will raise EntityNotFoundError if not found
        await self.repository.get_by_id(entity_id)

        # Delete
        await self.repository.delete(entity_id)

        # Emit event
        EntityDeleted(entity_id=entity_id)


class ListEntitiesUseCase:
    """Use case: List entities with pagination."""

    def __init__(self, repository: ExampleRepository) -> None:
        self.repository = repository

    async def execute(self, limit: int = 100, offset: int = 0) -> list[ExampleEntity]:
        """Execute use case."""
        if limit < 1 or limit > 1000:
            limit = 100
        if offset < 0:
            offset = 0

        return await self.repository.list_all(limit=limit, offset=offset)
