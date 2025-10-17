"""
Infrastructure Layer - Repository Implementation

SQLAlchemy implementation of domain repositories.
"""
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.entities import ExampleEntity
from ...domain.exceptions import EntityNotFoundError
from ...domain.repositories import ExampleRepository
from .models import ExampleModel


class SQLAlchemyExampleRepository(ExampleRepository):
    """SQLAlchemy implementation of ExampleRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _to_entity(self, model: ExampleModel) -> ExampleEntity:
        """Convert model to entity."""
        return ExampleEntity(
            id=model.id,
            name=model.name,
            description=model.description,
            status=model.status,
            extra_data=model.extra_data or {},
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, entity: ExampleEntity) -> ExampleModel:
        """Convert entity to model."""
        return ExampleModel(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            status=entity.status,
            extra_data=entity.extra_data,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    async def create(self, entity: ExampleEntity) -> ExampleEntity:
        """Create new entity."""
        model = self._to_model(entity)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def get_by_id(self, entity_id: UUID) -> ExampleEntity:
        """Get entity by ID.

        Raises:
            EntityNotFoundError: If entity not found.
        """
        result = await self.session.execute(
            select(ExampleModel).where(ExampleModel.id == entity_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            raise EntityNotFoundError(str(entity_id), "ExampleEntity")
        return self._to_entity(model)

    async def get_by_name(self, name: str) -> ExampleEntity | None:
        """Get entity by name."""
        result = await self.session.execute(
            select(ExampleModel).where(ExampleModel.name == name)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def update(self, entity: ExampleEntity) -> ExampleEntity:
        """Update existing entity.

        Raises:
            EntityNotFoundError: If entity not found.
        """
        result = await self.session.execute(
            select(ExampleModel).where(ExampleModel.id == entity.id)
        )
        model = result.scalar_one_or_none()

        if not model:
            raise EntityNotFoundError(str(entity.id), "ExampleEntity")

        model.name = entity.name
        model.description = entity.description
        model.status = entity.status
        model.extra_data = entity.extra_data
        model.updated_at = entity.updated_at

        await self.session.commit()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def delete(self, entity_id: UUID) -> None:
        """Delete entity by ID.

        Raises:
            EntityNotFoundError: If entity not found.
        """
        result = await self.session.execute(
            select(ExampleModel).where(ExampleModel.id == entity_id)
        )
        model = result.scalar_one_or_none()

        if not model:
            raise EntityNotFoundError(str(entity_id), "ExampleEntity")

        await self.session.delete(model)
        await self.session.commit()

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[ExampleEntity]:
        """List all entities with pagination."""
        result = await self.session.execute(
            select(ExampleModel).limit(limit).offset(offset)
        )
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    async def count(self) -> int:
        """Count total entities."""
        result = await self.session.execute(
            select(func.count()).select_from(ExampleModel)
        )
        return result.scalar() or 0
