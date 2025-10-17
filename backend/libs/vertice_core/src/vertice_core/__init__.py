"""Vertice Core - Shared utilities for all services."""

__version__ = "1.0.0"

from .config import BaseServiceSettings
from .exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ServiceUnavailableError,
    UnauthorizedError,
    ValidationError,
    VerticeError,
)
from .logging import get_logger
from .metrics import create_service_metrics
from .tracing import instrument_fastapi, setup_tracing

# Backward compatibility alias
VerticeException = VerticeError

__all__ = [
    "BaseServiceSettings",
    "ConflictError",
    "ForbiddenError",
    "NotFoundError",
    "ServiceUnavailableError",
    "UnauthorizedError",
    "ValidationError",
    "VerticeError",
    "VerticeException",  # Keep for backward compatibility
    "create_service_metrics",
    "get_logger",
    "instrument_fastapi",
    "setup_tracing",
]
