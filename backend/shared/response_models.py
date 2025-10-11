"""
Vértice Platform - Standardized API Response Models
===================================================

Provides consistent response format across all 67+ microservices for
success, error, and paginated responses. Ensures API consumers can
reliably parse responses regardless of which service they're calling.

Features:
    - Standardized success/error response structure
    - Pagination support with metadata
    - Type-safe response models with Pydantic
    - Consistent field naming across services
    - HTTP status code conventions
    - Easy JSON serialization

Response Format Standards:
    Success: {"success": true, "data": {...}, "meta": {...}}
    Error: {"success": false, "error": {...}}
    List: {"success": true, "data": [...], "meta": {...}, "pagination": {...}}

Usage:
    >>> from backend.shared.response_models import SuccessResponse, ErrorResponse
    >>> 
    >>> @app.get("/users/{id}")
    >>> async def get_user(id: int) -> SuccessResponse:
    >>>     user = await fetch_user(id)
    >>>     return SuccessResponse(data=user, message="User retrieved")

Author: Vértice Platform Team
License: Proprietary
"""

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

# Generic type for data payload
T = TypeVar("T")


# ============================================================================
# BASE RESPONSE MODELS
# ============================================================================


class BaseResponse(BaseModel):
    """Base response model with common fields."""

    success: bool = Field(
        ..., description="Indicates if the request was successful"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Response timestamp in UTC",
    )
    request_id: Optional[str] = Field(
        default=None, description="Unique request identifier for tracing"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() + "Z"}


# ============================================================================
# SUCCESS RESPONSES
# ============================================================================


class SuccessResponse(BaseResponse, Generic[T]):
    """Standard success response with generic data payload.

    Use this for single object responses (GET /resource/{id}, POST, PUT, PATCH).

    Attributes:
        success: Always True for success responses
        data: The actual response payload (flexible type)
        message: Optional human-readable success message
        meta: Optional metadata (processing time, version, etc.)
    """

    success: bool = Field(default=True, const=True)
    data: T = Field(..., description="Response payload")
    message: Optional[str] = Field(
        default=None, description="Human-readable success message"
    )
    meta: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional metadata"
    )


class ListResponse(BaseResponse, Generic[T]):
    """Standard response for list/collection endpoints.

    Use this for GET /resources (list endpoints).

    Attributes:
        success: Always True for success responses
        data: List of items
        message: Optional success message
        meta: Metadata about the collection
        pagination: Pagination information (if applicable)
    """

    success: bool = Field(default=True, const=True)
    data: List[T] = Field(..., description="List of items")
    message: Optional[str] = Field(default=None)
    meta: Optional[Dict[str, Any]] = Field(default=None)
    pagination: Optional["PaginationMeta"] = Field(
        default=None, description="Pagination metadata"
    )


class PaginationMeta(BaseModel):
    """Pagination metadata for list responses.

    Provides information about the current page, total items, and navigation.
    """

    page: int = Field(..., ge=1, description="Current page number (1-indexed)")
    page_size: int = Field(..., ge=1, description="Number of items per page")
    total_items: int = Field(..., ge=0, description="Total number of items")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_previous: bool = Field(..., description="Whether there is a previous page")
    next_page: Optional[int] = Field(
        default=None, description="Next page number (if available)"
    )
    previous_page: Optional[int] = Field(
        default=None, description="Previous page number (if available)"
    )

    @classmethod
    def from_params(
        cls, page: int, page_size: int, total_items: int
    ) -> "PaginationMeta":
        """Create pagination metadata from query parameters.

        Args:
            page: Current page number (1-indexed)
            page_size: Items per page
            total_items: Total number of items available

        Returns:
            PaginationMeta instance with calculated fields
        """
        total_pages = (total_items + page_size - 1) // page_size or 1
        has_next = page < total_pages
        has_previous = page > 1

        return cls(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
            has_next=has_next,
            has_previous=has_previous,
            next_page=page + 1 if has_next else None,
            previous_page=page - 1 if has_previous else None,
        )


class CreatedResponse(SuccessResponse[T]):
    """Response for resource creation (POST).

    Extends SuccessResponse with 201 status code semantics.
    """

    message: str = Field(default="Resource created successfully")


class UpdatedResponse(SuccessResponse[T]):
    """Response for resource update (PUT/PATCH).

    Extends SuccessResponse for update operations.
    """

    message: str = Field(default="Resource updated successfully")


class DeletedResponse(BaseResponse):
    """Response for resource deletion (DELETE).

    Typically returns no data, just success confirmation.
    """

    success: bool = Field(default=True, const=True)
    message: str = Field(default="Resource deleted successfully")
    meta: Optional[Dict[str, Any]] = Field(default=None)


# ============================================================================
# ERROR RESPONSES
# ============================================================================


class ErrorDetail(BaseModel):
    """Detailed error information.

    Provides structured error data for API consumers.
    """

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    field: Optional[str] = Field(
        default=None, description="Field name for validation errors"
    )
    details: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional error context"
    )


class ErrorResponse(BaseResponse):
    """Standard error response.

    Use this for all error cases (400, 401, 403, 404, 500, etc.).

    Attributes:
        success: Always False for error responses
        error: Structured error information
        errors: Optional list of multiple errors (e.g., validation)
    """

    success: bool = Field(default=False, const=False)
    error: ErrorDetail = Field(..., description="Primary error information")
    errors: Optional[List[ErrorDetail]] = Field(
        default=None, description="Additional errors (validation, etc.)"
    )


class ValidationErrorResponse(ErrorResponse):
    """Response for validation errors (422).

    Includes detailed field-level validation errors.
    """

    def __init__(self, errors: List[Dict[str, Any]], **kwargs):
        """Create validation error response from error list.

        Args:
            errors: List of validation errors from Pydantic
            **kwargs: Additional fields
        """
        error_details = [
            ErrorDetail(
                code="VALIDATION_ERROR",
                message=err.get("msg", "Validation failed"),
                field=".".join(str(loc) for loc in err.get("loc", [])),
                details={"type": err.get("type")},
            )
            for err in errors
        ]

        super().__init__(
            error=ErrorDetail(
                code="VALIDATION_ERROR",
                message="Request validation failed",
                details={"error_count": len(error_details)},
            ),
            errors=error_details,
            **kwargs,
        )


# ============================================================================
# HEALTH CHECK RESPONSE
# ============================================================================


class HealthStatus(BaseModel):
    """Service health status."""

    status: str = Field(..., description="Health status (healthy/degraded/unhealthy)")
    checks: Dict[str, bool] = Field(
        default_factory=dict, description="Individual health checks"
    )
    version: Optional[str] = Field(default=None, description="Service version")
    uptime_seconds: Optional[float] = Field(default=None, description="Service uptime")


class HealthResponse(BaseResponse):
    """Response for /health endpoints."""

    success: bool = Field(default=True)
    data: HealthStatus = Field(..., description="Health status information")


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def success_response(
    data: Any, message: Optional[str] = None, meta: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Helper function to create success response dict.

    Args:
        data: Response data
        message: Optional success message
        meta: Optional metadata

    Returns:
        Dictionary in standard success format
    """
    return SuccessResponse(data=data, message=message, meta=meta).model_dump()


def list_response(
    data: List[Any],
    page: Optional[int] = None,
    page_size: Optional[int] = None,
    total_items: Optional[int] = None,
    message: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Helper function to create paginated list response.

    Args:
        data: List of items
        page: Current page number (1-indexed)
        page_size: Items per page
        total_items: Total number of items
        message: Optional message
        meta: Optional metadata

    Returns:
        Dictionary in standard list format
    """
    pagination = None
    if page is not None and page_size is not None and total_items is not None:
        pagination = PaginationMeta.from_params(page, page_size, total_items)

    return ListResponse(
        data=data, message=message, meta=meta, pagination=pagination
    ).model_dump()


def error_response(
    code: str,
    message: str,
    status_code: int = 500,
    field: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Helper function to create error response dict.

    Args:
        code: Error code
        message: Error message
        status_code: HTTP status code
        field: Field name for validation errors
        details: Additional error context

    Returns:
        Dictionary in standard error format
    """
    return ErrorResponse(
        error=ErrorDetail(code=code, message=message, field=field, details=details)
    ).model_dump()


# ============================================================================
# HTTP STATUS CODE CONSTANTS
# ============================================================================


class HTTPStatusCode:
    """Standard HTTP status codes for consistent usage."""

    # Success
    OK = 200  # General success
    CREATED = 201  # Resource created
    ACCEPTED = 202  # Request accepted, processing
    NO_CONTENT = 204  # Success with no response body

    # Client Errors
    BAD_REQUEST = 400  # Invalid request
    UNAUTHORIZED = 401  # Authentication required
    FORBIDDEN = 403  # Insufficient permissions
    NOT_FOUND = 404  # Resource not found
    CONFLICT = 409  # Resource conflict (duplicate)
    UNPROCESSABLE_ENTITY = 422  # Validation error
    TOO_MANY_REQUESTS = 429  # Rate limit exceeded

    # Server Errors
    INTERNAL_SERVER_ERROR = 500  # Unhandled error
    SERVICE_UNAVAILABLE = 503  # Service down/overloaded
    GATEWAY_TIMEOUT = 504  # Upstream timeout


# ============================================================================
# RESPONSE EXAMPLES (for OpenAPI docs)
# ============================================================================

SUCCESS_EXAMPLE = {
    "success": True,
    "data": {"id": 123, "name": "Example Resource"},
    "message": "Resource retrieved successfully",
    "timestamp": "2025-10-11T12:00:00Z",
    "request_id": "req_abc123",
}

LIST_EXAMPLE = {
    "success": True,
    "data": [
        {"id": 1, "name": "Item 1"},
        {"id": 2, "name": "Item 2"},
    ],
    "pagination": {
        "page": 1,
        "page_size": 10,
        "total_items": 42,
        "total_pages": 5,
        "has_next": True,
        "has_previous": False,
        "next_page": 2,
    },
    "timestamp": "2025-10-11T12:00:00Z",
}

ERROR_EXAMPLE = {
    "success": False,
    "error": {
        "code": "NOT_FOUND",
        "message": "Resource with ID 999 not found",
        "details": {"resource_type": "user", "id": 999},
    },
    "timestamp": "2025-10-11T12:00:00Z",
    "request_id": "req_xyz789",
}

VALIDATION_ERROR_EXAMPLE = {
    "success": False,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Request validation failed",
        "details": {"error_count": 2},
    },
    "errors": [
        {
            "code": "VALIDATION_ERROR",
            "message": "field required",
            "field": "email",
            "details": {"type": "value_error.missing"},
        },
        {
            "code": "VALIDATION_ERROR",
            "message": "value is not a valid integer",
            "field": "age",
            "details": {"type": "type_error.integer"},
        },
    ],
    "timestamp": "2025-10-11T12:00:00Z",
}


__all__ = [
    "BaseResponse",
    "SuccessResponse",
    "ListResponse",
    "PaginationMeta",
    "CreatedResponse",
    "UpdatedResponse",
    "DeletedResponse",
    "ErrorDetail",
    "ErrorResponse",
    "ValidationErrorResponse",
    "HealthStatus",
    "HealthResponse",
    "success_response",
    "list_response",
    "error_response",
    "HTTPStatusCode",
    "SUCCESS_EXAMPLE",
    "LIST_EXAMPLE",
    "ERROR_EXAMPLE",
    "VALIDATION_ERROR_EXAMPLE",
]
