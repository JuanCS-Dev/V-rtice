"""
Vértice Platform - FastAPI Error Handlers
==========================================

This module provides centralized error handling for FastAPI applications across
the Vértice platform. It registers exception handlers for custom exceptions and
standard HTTP exceptions, ensuring consistent error responses across all services.

Features:
    - Automatic exception handler registration
    - Standardized JSON error response format
    - Logging integration for all exceptions
    - HTTP status code mapping from custom exceptions
    - Validation error formatting (Pydantic)
    - Request ID tracking for debugging

Error Response Format:
    {
        "error": {
            "code": "ERROR_CODE",
            "message": "Human-readable error message",
            "details": {...},  // Optional additional context
            "request_id": "uuid",
            "timestamp": "ISO8601"
        }
    }

Usage:
    >>> from fastapi import FastAPI
    >>> from backend.shared.error_handlers import register_error_handlers
    >>>
    >>> app = FastAPI()
    >>> register_error_handlers(app)

Author: Vértice Platform Team
License: Proprietary
"""

from datetime import datetime
import logging
import traceback
from typing import Any, Dict, Union
import uuid

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.shared.exceptions import VerticeException

logger = logging.getLogger(__name__)


# ============================================================================
# RESPONSE BUILDERS
# ============================================================================


def build_error_response(
    error_code: str,
    message: str,
    status_code: int,
    details: Dict[str, Any] = None,
    request_id: str = None,
) -> Dict[str, Any]:
    """Build standardized error response dictionary.

    Args:
        error_code: Machine-readable error code
        message: Human-readable error message
        status_code: HTTP status code
        details: Additional context and metadata
        request_id: Request tracking ID

    Returns:
        Standardized error response dictionary
    """
    return {
        "error": {
            "code": error_code,
            "message": message,
            "status_code": status_code,
            "details": details or {},
            "request_id": request_id or str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    }


def extract_request_id(request: Request) -> str:
    """Extract request ID from request headers or generate new one.

    Args:
        request: FastAPI request object

    Returns:
        Request ID string
    """
    # Try common request ID header names
    request_id = (
        request.headers.get("X-Request-ID")
        or request.headers.get("X-Correlation-ID")
        or request.headers.get("X-Trace-ID")
    )

    if not request_id:
        request_id = str(uuid.uuid4())
        # Store in request state for later access
        request.state.request_id = request_id

    return request_id


# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================


async def vertice_exception_handler(
    request: Request, exc: VerticeException
) -> JSONResponse:
    """Handle all Vértice custom exceptions.

    Args:
        request: FastAPI request object
        exc: VerticeException instance

    Returns:
        JSONResponse with standardized error format
    """
    request_id = extract_request_id(request)

    # Log the exception with context
    log_context = {
        "request_id": request_id,
        "path": request.url.path,
        "method": request.method,
        "error_code": exc.error_code,
        "status_code": exc.status_code,
    }

    if exc.status_code >= 500:
        logger.error(
            f"Server error: {exc.message}",
            extra=log_context,
            exc_info=True,
        )
    else:
        logger.warning(
            f"Client error: {exc.message}",
            extra=log_context,
        )

    response_data = build_error_response(
        error_code=exc.error_code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
        request_id=request_id,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=response_data,
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle standard HTTP exceptions from Starlette/FastAPI.

    Args:
        request: FastAPI request object
        exc: StarletteHTTPException instance

    Returns:
        JSONResponse with standardized error format
    """
    request_id = extract_request_id(request)

    # Map HTTP status codes to error codes
    error_code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "UNPROCESSABLE_ENTITY",
        429: "TOO_MANY_REQUESTS",
        500: "INTERNAL_SERVER_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
        504: "GATEWAY_TIMEOUT",
    }

    error_code = error_code_map.get(exc.status_code, "HTTP_ERROR")

    logger.warning(
        f"HTTP {exc.status_code}: {exc.detail}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code,
        },
    )

    response_data = build_error_response(
        error_code=error_code,
        message=str(exc.detail),
        status_code=exc.status_code,
        request_id=request_id,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=response_data,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors from FastAPI.

    Formats validation errors into readable format with field-level details.

    Args:
        request: FastAPI request object
        exc: RequestValidationError from FastAPI/Pydantic

    Returns:
        JSONResponse with formatted validation errors
    """
    request_id = extract_request_id(request)

    # Format validation errors
    formatted_errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        formatted_errors.append(
            {
                "field": field_path,
                "message": error["msg"],
                "type": error["type"],
                "input": error.get("input"),
            }
        )

    logger.warning(
        f"Validation error: {len(formatted_errors)} field(s)",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "errors": formatted_errors,
        },
    )

    response_data = build_error_response(
        error_code="VALIDATION_ERROR",
        message=f"Request validation failed: {len(formatted_errors)} error(s)",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details={"validation_errors": formatted_errors},
        request_id=request_id,
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response_data,
    )


async def pydantic_validation_exception_handler(
    request: Request, exc: PydanticValidationError
) -> JSONResponse:
    """Handle raw Pydantic validation errors.

    Args:
        request: FastAPI request object
        exc: PydanticValidationError

    Returns:
        JSONResponse with formatted validation errors
    """
    request_id = extract_request_id(request)

    formatted_errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        formatted_errors.append(
            {
                "field": field_path,
                "message": error["msg"],
                "type": error["type"],
            }
        )

    logger.warning(
        f"Pydantic validation error: {len(formatted_errors)} field(s)",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "errors": formatted_errors,
        },
    )

    response_data = build_error_response(
        error_code="VALIDATION_ERROR",
        message=f"Data validation failed: {len(formatted_errors)} error(s)",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details={"validation_errors": formatted_errors},
        request_id=request_id,
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response_data,
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all uncaught exceptions.

    This is the catch-all handler for unexpected errors. Logs full traceback
    and returns generic 500 error to client.

    Args:
        request: FastAPI request object
        exc: Any unhandled exception

    Returns:
        JSONResponse with generic error message
    """
    request_id = extract_request_id(request)

    # Log full exception with traceback
    logger.error(
        f"Unhandled exception: {exc.__class__.__name__}: {str(exc)}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "exception_type": exc.__class__.__name__,
        },
        exc_info=True,
    )

    # Print traceback for debugging (will appear in logs)
    traceback.print_exc()

    # Generic response (don't leak internal details)
    response_data = build_error_response(
        error_code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred. Please contact support.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details=(
            {"exception_type": exc.__class__.__name__}
            if logger.isEnabledFor(logging.DEBUG)
            else {}
        ),
        request_id=request_id,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_data,
    )


# ============================================================================
# REGISTRATION FUNCTION
# ============================================================================


def register_error_handlers(app: FastAPI) -> None:
    """Register all exception handlers with FastAPI application.

    This function should be called during application startup to register
    custom exception handlers for all services.

    Args:
        app: FastAPI application instance

    Example:
        >>> app = FastAPI()
        >>> register_error_handlers(app)
    """
    # Custom Vértice exceptions
    app.add_exception_handler(VerticeException, vertice_exception_handler)

    # Standard HTTP exceptions
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)

    # Validation errors
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(
        PydanticValidationError, pydantic_validation_exception_handler
    )

    # Catch-all for unexpected errors
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.info("Error handlers registered successfully")


# ============================================================================
# MIDDLEWARE (Optional - for request ID injection)
# ============================================================================


async def request_id_middleware(request: Request, call_next):
    """Middleware to inject request ID into all requests.

    This middleware ensures every request has a unique tracking ID,
    either from headers or newly generated.

    Args:
        request: FastAPI request object
        call_next: Next middleware/handler in chain

    Returns:
        Response with X-Request-ID header
    """
    request_id = extract_request_id(request)

    # Process request
    response = await call_next(request)

    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id

    return response


# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    "register_error_handlers",
    "request_id_middleware",
    "build_error_response",
    "vertice_exception_handler",
    "http_exception_handler",
    "validation_exception_handler",
    "generic_exception_handler",
]
