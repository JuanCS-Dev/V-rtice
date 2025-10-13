"""
Database module for Adaptive Immune System.

Provides SQLAlchemy models, database connection management,
and Alembic migration support.
"""

from .client import DatabaseClient, get_db_session
from .models import (
    Threat,
    Dependency,
    APV,
    Remedy,
    WargameRun,
    HITLDecision,
    FeedSyncStatus,
)

__all__ = [
    "DatabaseClient",
    "get_db_session",
    "Threat",
    "Dependency",
    "APV",
    "Remedy",
    "WargameRun",
    "HITLDecision",
    "FeedSyncStatus",
]
