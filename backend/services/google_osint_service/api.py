"""Maximus Google OSINT Service - API Entry Point.

This module serves as the API entry point for the Google OSINT Service.
It imports the FastAPI application from the main module.

The actual implementation is in main.py, which handles:
- Google Search API integration
- Open-source intelligence gathering
- Public data source queries for threat intelligence
- Situational awareness data collection
"""

from backend.services.google_osint_service.main import app

__all__ = ["app"]
