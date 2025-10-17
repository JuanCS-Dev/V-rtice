"""Base repository pattern."""

from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .base import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """Base repository for CRUD operations."""

    def __init__(self, model: type[T], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def get(self, id: int) -> T | None:
        """Get by ID."""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id),  # type: ignore[attr-defined]
        )
        return result.scalar_one_or_none()

    async def list(self, limit: int = 100, offset: int = 0) -> list[T]:
        """List with pagination."""
        result = await self.session.execute(
            select(self.model).limit(limit).offset(offset),
        )
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> T:
        """Create new record."""
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(self, id: int, **kwargs: Any) -> T | None:
        """Update record."""
        instance = await self.get(id)
        if not instance:
            return None
        for key, value in kwargs.items():
            setattr(instance, key, value)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def delete(self, id: int) -> bool:
        """Delete record."""
        instance = await self.get(id)
        if not instance:
            return False
        await self.session.delete(instance)
        await self.session.flush()
        return True
