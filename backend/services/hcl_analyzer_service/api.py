"""Maximus HCL Analyzer Service - API Entry Point.

This module serves as the API entry point for the HCL Analyzer Service.
It imports the FastAPI application from the main module.

The actual implementation is in main.py.
"""

from services.hcl_analyzer_service.main import app

__all__ = ["app"]
