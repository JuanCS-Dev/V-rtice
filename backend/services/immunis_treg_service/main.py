"""Main entry point - imports app from api module."""
from backend.services.immunis_treg_service.api import app

__all__ = ["app"]
