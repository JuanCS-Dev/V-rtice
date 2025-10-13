"""
Database client for Adaptive Immune System.

Provides connection management, session handling, and health checks.
"""

import logging
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

logger = logging.getLogger(__name__)


class DatabaseClient:
    """
    Database client with connection pooling and session management.

    Supports both sync and async operations.
    """

    def __init__(
        self,
        database_url: str,
        pool_size: int = 20,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        echo: bool = False,
    ):
        """
        Initialize database client.

        Args:
            database_url: PostgreSQL connection URL
            pool_size: Connection pool size
            max_overflow: Max overflow connections
            pool_timeout: Pool connection timeout in seconds
            echo: Echo SQL queries for debugging
        """
        self.database_url = database_url
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.echo = echo

        # Sync engine
        self.engine = create_engine(
            database_url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            echo=echo,
            pool_pre_ping=True,  # Verify connections before using
        )

        # Async engine (replace postgresql:// with postgresql+asyncpg://)
        async_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
        self.async_engine = create_async_engine(
            async_url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            echo=echo,
            pool_pre_ping=True,
        )

        # Session makers
        self.SessionLocal = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )

        self.AsyncSessionLocal = async_sessionmaker(
            bind=self.async_engine,
            class_=AsyncSession,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )

        logger.info(f"DatabaseClient initialized: pool_size={pool_size}")

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Get a synchronous database session.

        Usage:
            with db_client.get_session() as session:
                result = session.query(Threat).all()

        Yields:
            SQLAlchemy Session
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get an asynchronous database session.

        Usage:
            async with db_client.get_async_session() as session:
                result = await session.execute(select(Threat))

        Yields:
            SQLAlchemy AsyncSession
        """
        session = self.AsyncSessionLocal()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Async database session error: {e}")
            raise
        finally:
            await session.close()

    def health_check(self) -> bool:
        """
        Check database connectivity.

        Returns:
            True if database is reachable, False otherwise
        """
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    async def async_health_check(self) -> bool:
        """
        Check database connectivity (async).

        Returns:
            True if database is reachable, False otherwise
        """
        try:
            async with self.async_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Async database health check failed: {e}")
            return False

    def dispose(self):
        """Dispose all connections in the pool."""
        self.engine.dispose()

    async def async_dispose(self):
        """Dispose all async connections in the pool."""
        await self.async_engine.dispose()

    def get_pool_status(self) -> dict:
        """
        Get connection pool status.

        Returns:
            Dictionary with pool metrics
        """
        pool = self.engine.pool
        return {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "total": pool.size() + pool.overflow(),
        }


# Global database client instance (initialized by application)
_db_client: Optional[DatabaseClient] = None


def initialize_db_client(database_url: str, **kwargs) -> DatabaseClient:
    """
    Initialize global database client.

    Args:
        database_url: PostgreSQL connection URL
        **kwargs: Additional arguments for DatabaseClient

    Returns:
        Initialized DatabaseClient instance
    """
    global _db_client
    _db_client = DatabaseClient(database_url, **kwargs)
    logger.info("Global database client initialized")
    return _db_client


def get_db_client() -> DatabaseClient:
    """
    Get global database client instance.

    Returns:
        DatabaseClient instance

    Raises:
        RuntimeError: If database client not initialized
    """
    if _db_client is None:
        raise RuntimeError(
            "Database client not initialized. "
            "Call initialize_db_client() first."
        )
    return _db_client


# Dependency injection helpers for FastAPI
def get_db_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database sessions.

    Usage:
        @app.get("/apvs")
        def get_apvs(db: Session = Depends(get_db_session)):
            return db.query(APV).all()
    """
    client = get_db_client()
    with client.get_session() as session:
        yield session


async def get_async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for async database sessions.

    Usage:
        @app.get("/apvs")
        async def get_apvs(db: AsyncSession = Depends(get_async_db_session)):
            result = await db.execute(select(APV))
            return result.scalars().all()
    """
    client = get_db_client()
    async with client.get_async_session() as session:
        yield session
