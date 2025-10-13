"""
HITL API - FastAPI application for Human-in-the-Loop interface.

Components:
- main: FastAPI app with REST API and WebSocket support
- endpoints: API endpoints (reviews, decisions)
"""

from .main import app, broadcast_event

__all__ = [
    "app",
    "broadcast_event",
]
