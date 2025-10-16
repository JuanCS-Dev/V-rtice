"""
Presentation Layer - Dependencies

FastAPI dependency injection.
"""
from typing import Annotated

from fastapi import Depends

from ..infrastructure.config import Settings, get_settings
from ..infrastructure.database import Database

_database_instance: Database | None = None


def get_database(settings: Annotated[Settings, Depends(get_settings)]) -> Database:
    """Get database instance."""
    global _database_instance
    if _database_instance is None:
        _database_instance = Database(settings.database_url)
    return _database_instance
