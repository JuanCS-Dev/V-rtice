"""Maximus HCL Executor Service - API Entry Point.

This module serves as the API entry point for the HCL Executor Service.
It imports the FastAPI application from the main module.

The actual implementation is in main.py.
"""

from services.hcl_executor_service.main import app

__all__ = ["app"]
