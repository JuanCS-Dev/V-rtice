"""
Reactive Fabric - Repository Pattern Implementation.

Base repository providing common database operations with type safety.
Implements Unit of Work pattern for transaction management.
"""

from typing import Generic, TypeVar, Type, Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from ..database.schemas import Base


ModelType = TypeVar("ModelType", bound=Base)


class RepositoryError(Exception):
    """Base exception for repository operations."""
    pass


class NotFoundError(RepositoryError):
    """Entity not found in database."""
    pass


class DuplicateError(RepositoryError):
    """Duplicate entity violation."""
    pass


class DatabaseError(RepositoryError):
    """General database operation error."""
    pass


class BaseRepository(Generic[ModelType]):
    """
    Generic repository base class.
    
    Provides CRUD operations with consistent error handling and logging.
    All methods are async for FastAPI integration.
    
    Design Philosophy:
    - Type-safe operations via generics
    - Explicit error types for caller handling
    - Transaction boundaries at service layer
    - No business logic (pure data access)
    
    Usage:
        class ThreatRepository(BaseRepository[ThreatEventDB]):
            def __init__(self, session: AsyncSession):
                super().__init__(ThreatEventDB, session)
    """
    
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        """
        Initialize repository.
        
        Args:
            model: SQLAlchemy model class
            session: Async database session (managed by service layer)
        """
        self.model = model
        self.session = session
    
    async def create(self, **kwargs: Any) -> ModelType:
        """
        Create new entity.
        
        Args:
            **kwargs: Entity attributes
        
        Returns:
            Created entity with generated ID
        
        Raises:
            DuplicateError: If unique constraint violated
            DatabaseError: On other database errors
        """
        try:
            entity = self.model(**kwargs)
            self.session.add(entity)
            await self.session.flush()  # Get ID without committing
            await self.session.refresh(entity)  # Load relationships
            return entity
        except IntegrityError as e:
            await self.session.rollback()
            raise DuplicateError(f"Duplicate entity: {str(e)}") from e
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DatabaseError(f"Database error: {str(e)}") from e
    
    async def get_by_id(self, entity_id: UUID) -> Optional[ModelType]:
        """
        Retrieve entity by ID.
        
        Args:
            entity_id: Entity UUID
        
        Returns:
            Entity if found, None otherwise
        
        Raises:
            DatabaseError: On database errors
        """
        try:
            result = await self.session.execute(
                select(self.model).where(self.model.id == entity_id)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error: {str(e)}") from e
    
    async def get_by_id_or_raise(self, entity_id: UUID) -> ModelType:
        """
        Retrieve entity by ID or raise exception.
        
        Args:
            entity_id: Entity UUID
        
        Returns:
            Entity
        
        Raises:
            NotFoundError: If entity not found
            DatabaseError: On database errors
        """
        entity = await self.get_by_id(entity_id)
        if entity is None:
            raise NotFoundError(f"{self.model.__name__} with ID {entity_id} not found")
        return entity
    
    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        order_by: Optional[Any] = None
    ) -> List[ModelType]:
        """
        Retrieve all entities with pagination.
        
        Args:
            limit: Maximum results to return
            offset: Number of results to skip
            order_by: Column to order by (defaults to created_at DESC)
        
        Returns:
            List of entities
        
        Raises:
            DatabaseError: On database errors
        """
        try:
            query = select(self.model)
            
            if order_by is not None:
                query = query.order_by(order_by)
            elif hasattr(self.model, 'created_at'):
                query = query.order_by(self.model.created_at.desc())
            
            query = query.limit(limit).offset(offset)
            
            result = await self.session.execute(query)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error: {str(e)}") from e
    
    async def count(self, **filters: Any) -> int:
        """
        Count entities matching filters.
        
        Args:
            **filters: Column = value filters
        
        Returns:
            Count of matching entities
        
        Raises:
            DatabaseError: On database errors
        """
        try:
            query = select(func.count()).select_from(self.model)
            
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)
            
            result = await self.session.execute(query)
            return result.scalar_one()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error: {str(e)}") from e
    
    async def update(self, entity_id: UUID, **kwargs: Any) -> ModelType:
        """
        Update entity by ID.
        
        Args:
            entity_id: Entity UUID
            **kwargs: Attributes to update
        
        Returns:
            Updated entity
        
        Raises:
            NotFoundError: If entity not found
            DatabaseError: On database errors
        """
        try:
            entity = await self.get_by_id_or_raise(entity_id)
            
            for key, value in kwargs.items():
                if hasattr(entity, key) and value is not None:
                    setattr(entity, key, value)
            
            # Update timestamp if available
            if hasattr(entity, 'updated_at'):
                entity.updated_at = datetime.utcnow()
            
            await self.session.flush()
            await self.session.refresh(entity)
            return entity
        except NotFoundError:
            raise
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DatabaseError(f"Database error: {str(e)}") from e
    
    async def delete(self, entity_id: UUID) -> bool:
        """
        Delete entity by ID.
        
        Args:
            entity_id: Entity UUID
        
        Returns:
            True if deleted, False if not found
        
        Raises:
            DatabaseError: On database errors
        """
        try:
            result = await self.session.execute(
                delete(self.model).where(self.model.id == entity_id)
            )
            await self.session.flush()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DatabaseError(f"Database error: {str(e)}") from e
    
    async def exists(self, **filters: Any) -> bool:
        """
        Check if entity exists matching filters.
        
        Args:
            **filters: Column = value filters
        
        Returns:
            True if exists, False otherwise
        
        Raises:
            DatabaseError: On database errors
        """
        try:
            query = select(func.count()).select_from(self.model)
            
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)
            
            result = await self.session.execute(query)
            return result.scalar_one() > 0
        except SQLAlchemyError as e:
            raise DatabaseError(f"Database error: {str(e)}") from e
