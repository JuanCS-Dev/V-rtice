"""Vertice API - FastAPI utilities for services."""

__version__ = "1.0.0"

from .client import ServiceClient
from .factory import create_app
from .health import create_health_router
from .middleware import ErrorHandlingMiddleware, RequestLoggingMiddleware
from .schemas import ErrorResponse, HealthResponse, PaginatedResponse, SuccessResponse

__all__ = [
    "ErrorHandlingMiddleware",
    "ErrorResponse",
    "HealthResponse",
    "PaginatedResponse",
    "RequestLoggingMiddleware",
    "ServiceClient",
    "SuccessResponse",
    "create_app",
    "create_health_router",
]
