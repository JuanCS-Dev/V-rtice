"""
Reactive Fabric - Database Session Management.

Async database session management for FastAPI dependency injection.
Implements proper connection pooling and transaction handling.
"""

from typing import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
import structlog
import os


logger = structlog.get_logger(__name__)


# Database configuration from environment
DATABASE_URL = os.getenv(
    "REACTIVE_FABRIC_DATABASE_URL",
    "postgresql+asyncpg://vertice:vertice@localhost:5432/reactive_fabric"
)

# Create async engine with proper pooling
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    poolclass=NullPool if os.getenv("TESTING", "false").lower() == "true" else None
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database session injection.
    
    Provides async database session with automatic cleanup.
    Implements proper transaction handling and rollback on errors.
    
    Yields:
        AsyncSession: Database session for request scope
    
    Example:
        >>> @router.get("/items")
        >>> async def list_items(session: AsyncSession = Depends(get_db_session)):
        >>>     return await item_repository.list(session)
    
    Note:
        Session is automatically closed after request completion.
        Uncommitted transactions are rolled back on errors.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error("database_session_error", error=str(e), exc_info=True)
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_session_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database session (non-FastAPI usage).
    
    Use this for background tasks, scripts, or non-HTTP contexts.
    
    Yields:
        AsyncSession: Database session
    
    Example:
        >>> async with get_db_session_context() as session:
        >>>     await repository.create(session, item)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error("database_context_error", error=str(e), exc_info=True)
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database schema.
    
    Creates all tables defined in SQLAlchemy models.
    Should be called on application startup.
    
    Note:
        In production, use Alembic migrations instead.
    """
    from .schemas import Base
    
    async with engine.begin() as conn:
        logger.info("initializing_database_schema")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("database_schema_initialized")


async def drop_db() -> None:
    """
    Drop all database tables.
    
    WARNING: This destroys all data. Only use in testing/development.
    """
    from .schemas import Base
    
    async with engine.begin() as conn:
        logger.warning("dropping_database_schema")
        await conn.run_sync(Base.metadata.drop_all)
        logger.warning("database_schema_dropped")


async def close_db() -> None:
    """
    Close database engine and all connections.
    
    Should be called on application shutdown.
    """
    logger.info("closing_database_connections")
    await engine.dispose()
    logger.info("database_connections_closed")


async def health_check() -> bool:
    """
    Check database connectivity.
    
    Returns:
        True if database is accessible, False otherwise
    """
    try:
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error("database_health_check_failed", error=str(e))
        return False
