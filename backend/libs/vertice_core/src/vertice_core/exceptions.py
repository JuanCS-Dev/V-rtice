"""Standard exceptions for all Vértice services."""

from typing import Any


class VerticeException(Exception):
    """Base exception for all Vértice services."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to API response format."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "status_code": self.status_code,
            "details": self.details,
        }


class NotFoundError(VerticeException):
    """Resource not found (HTTP 404)."""

    def __init__(self, resource: str, identifier: Any) -> None:
        super().__init__(
            message=f"{resource} not found: {identifier}",
            status_code=404,
            details={"resource": resource, "identifier": str(identifier)},
        )


class ValidationError(VerticeException):
    """Request validation failed (HTTP 422)."""

    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(
            message=message,
            status_code=422,
            details={"field": field} if field else {},
        )


class UnauthorizedError(VerticeException):
    """Authentication failed (HTTP 401)."""

    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__(message=message, status_code=401)


class ForbiddenError(VerticeException):
    """Authorization failed (HTTP 403)."""

    def __init__(self, message: str = "Permission denied") -> None:
        super().__init__(message=message, status_code=403)


class ConflictError(VerticeException):
    """Resource conflict (HTTP 409)."""

    def __init__(self, message: str, resource: str) -> None:
        super().__init__(
            message=message,
            status_code=409,
            details={"resource": resource},
        )


class ServiceUnavailableError(VerticeException):
    """Service temporarily unavailable (HTTP 503)."""

    def __init__(self, service_name: str, reason: str = "") -> None:
        msg = f"Service {service_name} unavailable"
        if reason:
            msg += f": {reason}"
        super().__init__(
            message=msg,
            status_code=503,
            details={"service": service_name, "reason": reason},
        )
