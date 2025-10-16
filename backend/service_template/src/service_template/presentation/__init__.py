"""Presentation Layer - FastAPI application and routes."""

from .app import create_app
from .dependencies import get_database
from .routes import router

__all__ = [
    "create_app",
    "router",
    "get_database",
]
