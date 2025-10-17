"""Async database session management for Vértice services.

This module provides session factories, connection pooling configuration,
and context managers for safe database access in async FastAPI applications.

Example:
-------
    Basic setup::

        from vertice_db.session import AsyncSessionFactory, create_session_factory

        # Create factory during app startup
        session_factory = create_session_factory(
            database_url="postgresql+asyncpg://user:pass@localhost/db",
            pool_size=20,
            max_overflow=10,
        )

        # Use in endpoint
        async with session_factory() as session:
            result = await session.execute(select(User))
            users = result.scalars().all()

    With FastAPI::

        from fastapi import FastAPI, Depends
        from vertice_db.session import get_db_session

        app = FastAPI()

        @app.on_event("startup")
        async def startup():
            app.state.session_factory = create_session_factory(DATABASE_URL)

        @app.get("/users")
        async def list_users(db=Depends(get_db_session)):
            result = await db.execute(select(User))
            return result.scalars().all()

Note:
----
    - Always use async context managers or get_db_session dependency
    - Sessions auto-commit on success, rollback on exception
    - Connection pooling is configured automatically

"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from types import TracebackType
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    AsyncSessionTransaction,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool, QueuePool


class AsyncSessionFactory:
    """Factory for creating async database sessions.

    Manages the engine and session maker, providing a clean interface
    for session creation with automatic cleanup.

    Args:
    ----
        engine: SQLAlchemy async engine.
        expire_on_commit: Whether to expire objects after commit (default: False).

    Attributes:
    ----------
        engine: The database engine.
        session_maker: Configured async_sessionmaker.

    Example:
    -------
        >>> factory = AsyncSessionFactory(engine)
        >>> async with factory() as session:
        >>>     result = await session.execute(select(User))
        >>>     users = result.scalars().all()
    """

    def __init__(
        self,
        engine: AsyncEngine,
        expire_on_commit: bool = False,
    ) -> None:
        self.engine = engine
        self.session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=expire_on_commit,
            autoflush=False,
            autocommit=False,
        )

    @asynccontextmanager
    async def __call__(self) -> AsyncGenerator[AsyncSession, None]:
        """Create a new session with automatic cleanup.

        Yields:
        ------
            AsyncSession instance.

        Example:
        -------
            >>> async with factory() as session:
            >>>     await session.execute(insert(User).values(name="Alice"))
            >>>     await session.commit()
        """
        async with self.session_maker() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def close(self) -> None:
        """Close the engine and all connections.

        Should be called during application shutdown.

        Example:
        -------
            >>> @app.on_event("shutdown")
            >>> async def shutdown():
            >>>     await app.state.session_factory.close()
        """
        await self.engine.dispose()


def create_session_factory(
    database_url: str,
    pool_size: int = 20,
    max_overflow: int = 10,
    pool_timeout: float = 30.0,
    pool_recycle: int = 3600,
    echo: bool = False,
    connect_args: dict[str, Any] | None = None,
) -> AsyncSessionFactory:
    """Create a configured async session factory.

    Args:
    ----
        database_url: Database connection URL (must be async driver, e.g., postgresql+asyncpg).
        pool_size: Number of permanent connections to maintain (default: 20).
        max_overflow: Max connections beyond pool_size (default: 10).
        pool_timeout: Seconds to wait for connection from pool (default: 30.0).
        pool_recycle: Seconds before recycling connection (default: 3600 = 1 hour).
        echo: Whether to log all SQL statements (default: False).
        connect_args: Additional connection arguments (default: None).

    Returns:
    -------
        Configured AsyncSessionFactory.

    Example:
    -------
        >>> # Production config
        >>> factory = create_session_factory(
        >>>     "postgresql+asyncpg://user:pass@localhost/db",
        >>>     pool_size=50,
        >>>     max_overflow=20,
        >>>     echo=False,
        >>> )

        >>> # Development config
        >>> factory = create_session_factory(
        >>>     "postgresql+asyncpg://localhost/dev_db",
        >>>     pool_size=5,
        >>>     echo=True,
        >>> )

    Note:
    ----
        - Use asyncpg driver for PostgreSQL (postgresql+asyncpg://)
        - Pool settings affect memory usage and performance
        - echo=True is useful for debugging but verbose in production
    """
    # Validate URL is async
    if "+asyncpg" not in database_url and "+asyncio" not in database_url:
        if "postgresql://" in database_url:
            # Auto-fix for common mistake
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
        else:
            raise ValueError(
                f"Database URL must use async driver (asyncpg, asyncio). Got: {database_url}",
            )

    # Create engine with pooling
    engine = create_async_engine(
        database_url,
        poolclass=QueuePool,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=pool_timeout,
        pool_recycle=pool_recycle,
        pool_pre_ping=True,  # Test connections before using
        echo=echo,
        connect_args=connect_args or {},
    )

    return AsyncSessionFactory(engine)


def create_test_session_factory(database_url: str) -> AsyncSessionFactory:
    """Create a session factory optimized for testing.

    Uses NullPool (no connection pooling) for isolation between tests.

    Args:
    ----
        database_url: Test database connection URL.

    Returns:
    -------
        AsyncSessionFactory configured for testing.

    Example:
    -------
        >>> @pytest.fixture
        >>> async def db_session():
        >>>     factory = create_test_session_factory("postgresql+asyncpg://localhost/test_db")
        >>>     async with factory() as session:
        >>>         yield session
        >>>     await factory.close()
    """
    engine = create_async_engine(
        database_url,
        poolclass=NullPool,  # No pooling for tests
        echo=False,
    )

    return AsyncSessionFactory(engine, expire_on_commit=True)


async def get_db_session(
    session_factory: AsyncSessionFactory,
) -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection helper for FastAPI.

    Args:
    ----
        session_factory: The session factory to use.

    Yields:
    ------
        AsyncSession instance with auto-commit and rollback.

    Example:
    -------
        >>> from fastapi import Depends, FastAPI
        >>> from vertice_db.session import get_db_session
        >>>
        >>> app = FastAPI()
        >>>
        >>> @app.on_event("startup")
        >>> async def startup():
        >>>     app.state.session_factory = create_session_factory(DATABASE_URL)
        >>>
        >>> def get_db():
        >>>     return get_db_session(app.state.session_factory)
        >>>
        >>> @app.get("/users")
        >>> async def list_users(db: AsyncSession = Depends(get_db)):
        >>>     result = await db.execute(select(User))
        >>>     return result.scalars().all()

    Note:
    ----
        - Auto-commits on success
        - Auto-rollbacks on exception
        - Ensures session is properly closed
    """
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


class TransactionManager:
    """Context manager for explicit transaction control.

    Useful for complex operations requiring manual transaction boundaries.

    Example:
    -------
        >>> async with session_factory() as session:
        >>>     async with TransactionManager(session):
        >>>         # Multiple operations in single transaction
        >>>         await session.execute(insert(User).values(name="Alice"))
        >>>         await session.execute(insert(User).values(name="Bob"))
        >>>         # Auto-commits here
        >>>     # Or manual control:
        >>>     async with TransactionManager(session, auto_commit=False) as tx:
        >>>         await session.execute(insert(User).values(name="Charlie"))
        >>>         if some_condition:
        >>>             await tx.commit()
        >>>         else:
        >>>             await tx.rollback()
    """

    def __init__(self, session: AsyncSession, auto_commit: bool = True) -> None:
        """Initialize transaction manager.

        Args:
        ----
            session: Database session to manage.
            auto_commit: Whether to auto-commit on exit (default: True).
        """
        self.session = session
        self.auto_commit = auto_commit
        self._transaction: AsyncSessionTransaction | None = None

    async def __aenter__(self) -> "TransactionManager":
        """Start transaction."""
        self._transaction = await self.session.begin()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Commit or rollback based on exception."""
        if exc_type is not None:
            # Exception occurred, rollback
            await self.rollback()
        elif self.auto_commit:
            # No exception, auto-commit
            await self.commit()
        # If auto_commit=False and no exception, transaction stays open
        # (caller must commit manually)

    async def commit(self) -> None:
        """Commit the transaction."""
        if self._transaction:
            await self._transaction.commit()
            self._transaction = None

    async def rollback(self) -> None:
        """Rollback the transaction."""
        if self._transaction:
            await self._transaction.rollback()
            self._transaction = None
