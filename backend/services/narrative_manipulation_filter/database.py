"""
Database Connection Manager for Cognitive Defense System.

Provides async PostgreSQL connection pooling, session management,
and dependency injection for FastAPI.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy import event, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import QueuePool

from config import get_settings
from db_models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages PostgreSQL async connections and sessions."""

    def __init__(self):
        """Initialize database manager."""
        self.engine: Optional[AsyncEngine] = None
        self.async_session_maker: Optional[async_sessionmaker] = None
        self.settings = get_settings()

    async def initialize(self) -> None:
        """
        Initialize database engine and session factory.

        Sets up connection pooling with optimized parameters for high throughput.
        """
        if self.engine is not None:
            logger.warning("Database already initialized, skipping")
            return

        try:
            # Create async engine with connection pooling
            self.engine = create_async_engine(
                self.settings.DATABASE_URL,
                echo=self.settings.DB_ECHO,
                future=True,
                pool_size=self.settings.DB_POOL_SIZE,
                max_overflow=self.settings.DB_MAX_OVERFLOW,
                pool_timeout=self.settings.DB_POOL_TIMEOUT,
                pool_recycle=3600,  # Recycle connections after 1 hour
                pool_pre_ping=True,  # Verify connections before using
                poolclass=QueuePool,
            )

            # Configure statement timeout for safety
            @event.listens_for(self.engine.sync_engine, "connect")
            def set_timeout(dbapi_conn, connection_record):
                cursor = dbapi_conn.cursor()
                cursor.execute("SET statement_timeout = 30000")  # 30 seconds
                cursor.close()

            # Create session factory
            self.async_session_maker = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
                autocommit=False,
            )

            # Test connection
            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))

            logger.info(
                f"✅ Database initialized successfully: "
                f"{self.settings.POSTGRES_HOST}:{self.settings.POSTGRES_PORT}/{self.settings.POSTGRES_DB}"
            )

        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            raise

    async def create_tables(self) -> None:
        """
        Create all database tables.

        Note: In production, use Alembic migrations instead.
        """
        if self.engine is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("✅ Database tables created successfully")
        except Exception as e:
            logger.error(f"❌ Failed to create tables: {e}")
            raise

    async def drop_tables(self) -> None:
        """
        Drop all database tables.

        ⚠️  WARNING: This will delete all data!
        """
        if self.engine is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            logger.warning("⚠️  All database tables dropped")
        except Exception as e:
            logger.error(f"❌ Failed to drop tables: {e}")
            raise

    async def close(self) -> None:
        """Close database connections and cleanup."""
        if self.engine is not None:
            await self.engine.dispose()
            self.engine = None
            self.async_session_maker = None
            logger.info("✅ Database connections closed")

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Provide a transactional scope around a series of operations.

        Usage:
            async with db_manager.session() as session:
                result = await session.execute(query)
                await session.commit()
        """
        if self.async_session_maker is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        session = self.async_session_maker()
        try:
            yield session
            await session.commit()
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Database error: {e}")
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Unexpected error: {e}")
            raise
        finally:
            await session.close()

    async def health_check(self) -> bool:
        """
        Check database connectivity.

        Returns:
            bool: True if database is healthy, False otherwise.
        """
        if self.engine is None:
            return False

        try:
            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# ============================================================================
# GLOBAL INSTANCE & DEPENDENCY INJECTION
# ============================================================================

# Global database manager instance
db_manager = DatabaseManager()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database sessions.

    Usage in API endpoints:
        @app.get("/example")
        async def example(db: AsyncSession = Depends(get_db_session)):
            result = await db.execute(select(Model))
            return result.scalars().all()
    """
    if db_manager.async_session_maker is None:
        raise RuntimeError("Database not initialized")

    async with db_manager.session() as session:
        yield session


# ============================================================================
# LIFESPAN MANAGEMENT FOR FASTAPI
# ============================================================================


@asynccontextmanager
async def lifespan_db(app):
    """
    FastAPI lifespan context for database initialization/cleanup.

    Usage:
        app = FastAPI(lifespan=lifespan_db)
    """
    # Startup
    logger.info("🚀 Initializing database...")
    await db_manager.initialize()

    # Optionally create tables (comment out if using migrations)
    if get_settings().POSTGRES_AUTO_CREATE_TABLES:
        await db_manager.create_tables()

    yield

    # Shutdown
    logger.info("🛑 Closing database connections...")
    await db_manager.close()


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


async def execute_raw_query(query: str, params: Optional[dict] = None) -> list:
    """
    Execute raw SQL query with parameters.

    Args:
        query: SQL query string
        params: Query parameters (optional)

    Returns:
        List of result rows
    """
    async with db_manager.session() as session:
        result = await session.execute(text(query), params or {})
        return result.fetchall()


async def get_table_count(table_name: str) -> int:
    """
    Get row count for a table.

    Args:
        table_name: Name of the table

    Returns:
        Number of rows
    """
    query = f"SELECT COUNT(*) FROM {table_name}"
    result = await execute_raw_query(query)
    return result[0][0] if result else 0


async def vacuum_analyze() -> None:
    """
    Run VACUUM ANALYZE on database for optimization.

    Should be run periodically in production.
    """
    async with db_manager.engine.begin() as conn:
        # VACUUM cannot run inside a transaction, so use autocommit
        await conn.execute(text("COMMIT"))
        await conn.execute(text("VACUUM ANALYZE"))
    logger.info("✅ Database vacuumed and analyzed")


# ============================================================================
# REPOSITORY PATTERN BASE CLASS (Optional)
# ============================================================================


class BaseRepository:
    """Base repository for data access patterns."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with session."""
        self.session = session

    async def add(self, instance):
        """Add instance to session."""
        self.session.add(instance)
        await self.session.flush()

    async def delete(self, instance):
        """Delete instance from session."""
        await self.session.delete(instance)
        await self.session.flush()

    async def commit(self):
        """Commit current transaction."""
        await self.session.commit()

    async def rollback(self):
        """Rollback current transaction."""
        await self.session.rollback()

    async def refresh(self, instance):
        """Refresh instance from database."""
        await self.session.refresh(instance)
