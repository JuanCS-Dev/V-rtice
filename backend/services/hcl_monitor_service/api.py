"""Maximus HCL Monitor Service - API Entry Point.

This module serves as the API entry point for the HCL Monitor Service.
It imports the FastAPI application from the main module.

The actual implementation is in main.py.
"""

from backend.services.hcl_monitor_service.main import app

__all__ = ["app"]
