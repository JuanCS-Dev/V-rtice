"""Custom API Exceptions with Error Codes.

DOUTRINA VÉRTICE - GAP #6 (P1)
Standardized exceptions for consistent error handling

Following Boris Cherny's principle: "Errors should be as informative as the data"
"""

from typing import Optional
from fastapi import HTTPException, status
from .errors import ErrorCodes


class APIException(HTTPException):
    """Base API exception with error code.

    All custom exceptions should inherit from this class.
    Automatically includes error_code in detail.
    """

    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str,
        headers: Optional[dict] = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code


# ============================================================================
# Authentication Exceptions
# ============================================================================


class AuthenticationError(APIException):
    """Authentication failed - missing or invalid credentials."""

    def __init__(self, detail: str = "Authentication required"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code=ErrorCodes.AUTH_MISSING_TOKEN,
            headers={"WWW-Authenticate": "Bearer"},
        )


class InvalidTokenError(APIException):
    """Invalid or malformed token."""

    def __init__(self, detail: str = "Invalid authentication token"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code=ErrorCodes.AUTH_INVALID_TOKEN,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ExpiredTokenError(APIException):
    """Token has expired."""

    def __init__(self, detail: str = "Authentication token has expired"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code=ErrorCodes.AUTH_EXPIRED_TOKEN,
            headers={"WWW-Authenticate": "Bearer"},
        )


class InsufficientPermissionsError(APIException):
    """User lacks required permissions."""

    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code=ErrorCodes.AUTH_INSUFFICIENT_PERMISSIONS,
        )


# ============================================================================
# Validation Exceptions
# ============================================================================


class ValidationError(APIException):
    """Input validation failed."""

    def __init__(self, detail: str, field: Optional[str] = None):
        if field:
            detail = f"{field}: {detail}"
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code=ErrorCodes.VAL_INVALID_INPUT,
        )


# ============================================================================
# Resource Exceptions
# ============================================================================


class ResourceNotFoundError(APIException):
    """Requested resource not found."""

    def __init__(self, resource: str, identifier: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} '{identifier}' not found",
            error_code="RES_001",
        )


class ResourceAlreadyExistsError(APIException):
    """Resource already exists (conflict)."""

    def __init__(self, resource: str, identifier: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{resource} '{identifier}' already exists",
            error_code="RES_002",
        )


# ============================================================================
# Rate Limiting Exceptions
# ============================================================================


class RateLimitExceededError(APIException):
    """Rate limit exceeded."""

    def __init__(self, detail: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        headers = {}
        if retry_after:
            headers["Retry-After"] = str(retry_after)

        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            error_code=ErrorCodes.RATE_LIMIT_EXCEEDED,
            headers=headers or None,
        )


# ============================================================================
# System Exceptions
# ============================================================================


class ServiceUnavailableError(APIException):
    """External service unavailable."""

    def __init__(self, service: str, detail: Optional[str] = None):
        message = f"{service} is currently unavailable"
        if detail:
            message += f": {detail}"

        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=message,
            error_code=ErrorCodes.SYS_SERVICE_UNAVAILABLE,
        )


class TimeoutError(APIException):
    """Request timeout."""

    def __init__(self, detail: str = "Request timeout"):
        super().__init__(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=detail,
            error_code=ErrorCodes.SYS_TIMEOUT,
        )


# ============================================================================
# External Service Exceptions
# ============================================================================


class ExternalServiceError(APIException):
    """External service error."""

    def __init__(self, service: str, detail: str):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"{service}: {detail}",
            error_code=ErrorCodes.EXT_SERVICE_UNAVAILABLE,
        )
