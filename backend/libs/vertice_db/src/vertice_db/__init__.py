"""Database utilities for Vértice services."""

from .base import Base
from .connection import DatabaseConnection, create_db_connection
from .models import SoftDeleteMixin, TimestampMixin
from .redis_client import RedisClient, create_redis_client
from .repository import BaseRepository
from .session import (
    AsyncSessionFactory,
    TransactionManager,
    create_session_factory,
    create_test_session_factory,
    get_db_session,
)

__all__ = [
    # Base
    "Base",
    # Models & Mixins
    "SoftDeleteMixin",
    "TimestampMixin",
    # Session Management
    "AsyncSessionFactory",
    "TransactionManager",
    "create_session_factory",
    "create_test_session_factory",
    "get_db_session",
    # Repository
    "BaseRepository",
    # Connection (legacy, prefer session)
    "DatabaseConnection",
    "create_db_connection",
    # Redis
    "RedisClient",
    "create_redis_client",
]

__version__ = "1.0.0"
