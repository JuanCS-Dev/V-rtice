"""IP Intelligence Service - Database Setup.

This module configures the asynchronous database connection using SQLAlchemy.
It sets up the async engine and a session factory for dependency injection
in the FastAPI application.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings

# Create an asynchronous engine for the database.
engine = create_async_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}  # Required for SQLite
)

# Create a factory for asynchronous database sessions.
AsyncSessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine, 
    class_=AsyncSession
)

# Base class for declarative SQLAlchemy models.
Base = declarative_base()

async def get_db() -> AsyncSession:
    """Provides a database session dependency for FastAPI endpoints.

    This dependency will create a new session for each request and ensure it is
    closed properly, with transactions rolled back on error.

    Yields:
        AsyncSession: The database session object.
    """
    async with AsyncSessionLocal() as session:
        yield session