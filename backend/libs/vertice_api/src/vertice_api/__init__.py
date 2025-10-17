"""Vertice API - FastAPI utilities for services."""

__version__ = "1.0.0"

from .client import ServiceClient
from .dependencies import (
    get_current_user,
    get_db,
    get_logger,
    get_service_client,
    require_permissions,
)
from .factory import create_app
from .health import create_health_router
from .middleware import ErrorHandlingMiddleware, RequestLoggingMiddleware
from .schemas import ErrorResponse, HealthResponse, PaginatedResponse, SuccessResponse
from .versioning import (
    APIVersionMiddleware,
    get_request_version,
    version,
    version_range,
)

__all__ = [
    # Middleware
    "APIVersionMiddleware",
    "ErrorHandlingMiddleware",
    "RequestLoggingMiddleware",
    # Schemas
    "ErrorResponse",
    "HealthResponse",
    "PaginatedResponse",
    "SuccessResponse",
    # Factory
    "ServiceClient",
    "create_app",
    "create_health_router",
    # Dependencies
    "get_current_user",
    "get_db",
    "get_logger",
    "get_service_client",
    "require_permissions",
    # Versioning
    "get_request_version",
    "version",
    "version_range",
]
