"""Database utilities for Vértice services."""

from .connection import DatabaseConnection, create_db_connection
from .models import Base, TimestampMixin
from .redis_client import RedisClient, create_redis_client
from .repository import BaseRepository

__all__ = [
    "Base",
    "BaseRepository",
    "DatabaseConnection",
    "RedisClient",
    "TimestampMixin",
    "create_db_connection",
    "create_redis_client",
]

__version__ = "1.0.0"
