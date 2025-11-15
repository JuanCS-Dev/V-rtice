"""Standardized Error Response Models.

This module defines type-safe error response models for the Vértice API Gateway.
All error responses include request IDs for distributed tracing and debugging.

Error codes follow a hierarchical structure:
- AUTH_xxx: Authentication/authorization errors
- VAL_xxx: Validation errors
- RATE_xxx: Rate limiting errors
- SYS_xxx: System/internal errors
- EXT_xxx: External service errors

Following Boris Cherny's principle: "Errors should be as informative as the data"

Author: Vértice Development Team
DOUTRINA VÉRTICE - ARTIGO II: PAGANI Standard
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standardized error response with distributed tracing.

    This model provides a consistent error format across all API endpoints,
    enabling better client error handling and server-side debugging.

    Attributes:
        detail: Human-readable error message for developers
        error_code: Machine-readable error code for programmatic handling
        timestamp: ISO 8601 timestamp when error occurred
        request_id: UUID for distributed tracing and log correlation
        path: Request path that triggered the error

    Example:
        >>> error = ErrorResponse(
        ...     detail="Invalid JWT token signature",
        ...     error_code="AUTH_002",
        ...     request_id="550e8400-e29b-41d4-a716-446655440000",
        ...     path="/api/v1/scan/start"
        ... )

        >>> # JSON output:
        >>> {
        ...     "detail": "Invalid JWT token signature",
        ...     "error_code": "AUTH_002",
        ...     "timestamp": "2025-11-15T10:30:00.123456Z",
        ...     "request_id": "550e8400-e29b-41d4-a716-446655440000",
        ...     "path": "/api/v1/scan/start"
        ... }
    """

    detail: str = Field(
        ...,
        description="Human-readable error message",
        min_length=1,
        examples=["Invalid authentication token"],
    )

    error_code: str = Field(
        ...,
        description="Machine-readable error code",
        pattern="^[A-Z]+_[0-9]{3}$",
        examples=["AUTH_001", "VAL_002", "SYS_500"],
    )

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="ISO 8601 timestamp when error occurred",
        examples=["2025-11-15T10:30:00.123456Z"],
    )

    request_id: str = Field(
        ...,
        description="Request correlation ID for distributed tracing",
        pattern="^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )

    path: str = Field(
        ...,
        description="Request path that caused the error",
        min_length=1,
        examples=["/api/v1/scan/start"],
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "detail": "Invalid authentication token",
                "error_code": "AUTH_001",
                "timestamp": "2025-11-15T10:30:00.123456Z",
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "path": "/api/v1/scan/start",
            }
        }


class ValidationErrorDetail(BaseModel):
    """Individual validation error detail.

    Attributes:
        loc: Location of the error (e.g., ["body", "email"])
        msg: Human-readable error message
        type: Error type (e.g., "value_error.email")

    Example:
        >>> detail = ValidationErrorDetail(
        ...     loc=["body", "email"],
        ...     msg="Invalid email format",
        ...     type="value_error.email"
        ... )
    """

    loc: List[str] = Field(
        ...,
        description="Error location path",
        examples=[["body", "email"], ["query", "limit"]],
    )

    msg: str = Field(
        ...,
        description="Human-readable error message",
        min_length=1,
        examples=["Invalid email format", "Field required"],
    )

    type: str = Field(
        ...,
        description="Error type identifier",
        min_length=1,
        examples=["value_error.email", "type_error.integer"],
    )


class ValidationErrorResponse(BaseModel):
    """Response for validation errors (422 Unprocessable Entity).

    This model extends ErrorResponse with validation-specific details,
    providing field-level error information for client-side form handling.

    Attributes:
        detail: High-level error message
        error_code: Always "VAL_422"
        timestamp: When validation failed
        request_id: Correlation ID
        path: Request path
        validation_errors: List of field-level validation errors

    Example:
        >>> error = ValidationErrorResponse(
        ...     detail="Request validation failed",
        ...     error_code="VAL_422",
        ...     request_id="550e8400-...",
        ...     path="/api/v1/users",
        ...     validation_errors=[
        ...         ValidationErrorDetail(
        ...             loc=["body", "email"],
        ...             msg="Invalid email format",
        ...             type="value_error.email"
        ...         )
        ...     ]
        ... )
    """

    detail: str = Field(
        default="Request validation failed",
        description="High-level error message",
    )

    error_code: str = Field(
        default="VAL_422",
        description="Validation error code",
        pattern="^VAL_[0-9]{3}$",
    )

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When validation failed",
    )

    request_id: str = Field(
        ...,
        description="Request correlation ID",
        pattern="^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$",
    )

    path: str = Field(
        ...,
        description="Request path",
        min_length=1,
    )

    validation_errors: List[ValidationErrorDetail] = Field(
        ...,
        description="Field-level validation errors",
        min_items=1,
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "detail": "Request validation failed",
                "error_code": "VAL_422",
                "timestamp": "2025-11-15T10:30:00.123456Z",
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "path": "/api/v1/users",
                "validation_errors": [
                    {
                        "loc": ["body", "email"],
                        "msg": "Invalid email format",
                        "type": "value_error.email",
                    },
                    {
                        "loc": ["body", "age"],
                        "msg": "Must be greater than 0",
                        "type": "value_error.number.not_gt",
                    },
                ],
            }
        }


# ============================================================================
# Error Code Registry
# ============================================================================

class ErrorCodes:
    """Registry of all error codes used in the API.

    This provides a single source of truth for error codes,
    preventing duplicates and documenting all possible errors.

    Following Boris Cherny's principle: "Magic strings are bugs waiting to happen"
    """

    # Authentication Errors (AUTH_xxx)
    AUTH_MISSING_TOKEN = "AUTH_001"
    AUTH_INVALID_TOKEN = "AUTH_002"
    AUTH_EXPIRED_TOKEN = "AUTH_003"
    AUTH_INSUFFICIENT_PERMISSIONS = "AUTH_004"

    # Validation Errors (VAL_xxx)
    VAL_UNPROCESSABLE_ENTITY = "VAL_422"
    VAL_INVALID_INPUT = "VAL_001"
    VAL_MISSING_FIELD = "VAL_002"
    VAL_INVALID_FORMAT = "VAL_003"

    # Rate Limiting Errors (RATE_xxx)
    RATE_LIMIT_EXCEEDED = "RATE_429"
    RATE_QUOTA_EXCEEDED = "RATE_001"

    # System Errors (SYS_xxx)
    SYS_INTERNAL_ERROR = "SYS_500"
    SYS_SERVICE_UNAVAILABLE = "SYS_503"
    SYS_TIMEOUT = "SYS_504"

    # External Service Errors (EXT_xxx)
    EXT_SERVICE_UNAVAILABLE = "EXT_001"
    EXT_TIMEOUT = "EXT_002"
    EXT_INVALID_RESPONSE = "EXT_003"


# ============================================================================
# Utility Functions
# ============================================================================


def create_error_response(
    detail: str,
    error_code: str,
    request_id: str,
    path: str,
) -> ErrorResponse:
    """Create a standardized error response.

    Args:
        detail: Human-readable error message
        error_code: Machine-readable error code
        request_id: Request correlation ID
        path: Request path

    Returns:
        ErrorResponse instance

    Example:
        >>> error = create_error_response(
        ...     detail="Invalid token",
        ...     error_code=ErrorCodes.AUTH_INVALID_TOKEN,
        ...     request_id="550e8400-...",
        ...     path="/api/v1/scan/start"
        ... )
    """
    return ErrorResponse(
        detail=detail,
        error_code=error_code,
        request_id=request_id,
        path=path,
    )
