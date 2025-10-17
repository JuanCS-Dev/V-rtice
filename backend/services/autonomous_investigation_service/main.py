"""Main entry point - imports app from api module."""
from services.autonomous_investigation_service.api import app

__all__ = ["app"]
