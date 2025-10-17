"""Main entry point - imports app from api module."""
from services.immunis_treg_service.api import app

__all__ = ["app"]
