"""Tests for vertice_core.exceptions module."""


from vertice_core import VerticeException  # Use alias from __init__
from vertice_core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ServiceUnavailableError,
    UnauthorizedError,
    ValidationError,
)


class TestVerticeException:
    """Tests for VerticeException base class."""

    def test_creates_with_defaults(self) -> None:
        """Test creating exception with default values."""
        exc = VerticeException("Test error")

        assert exc.message == "Test error"
        assert exc.status_code == 500
        assert exc.details == {}

    def test_creates_with_custom_values(self) -> None:
        """Test creating exception with custom values."""
        exc = VerticeException(
            "Custom error",
            status_code=400,
            details={"field": "value"},
        )

        assert exc.message == "Custom error"
        assert exc.status_code == 400
        assert exc.details == {"field": "value"}

    def test_to_dict_format(self) -> None:
        """Test to_dict() returns correct format."""
        exc = VerticeException("Test", status_code=400, details={"x": 1})

        result = exc.to_dict()

        # VerticeException is an alias for VerticeError
        assert result["error"] in ("VerticeException", "VerticeError")
        assert result["message"] == "Test"
        assert result["status_code"] == 400
        assert result["details"] == {"x": 1}


class TestNotFoundError:
    """Tests for NotFoundError."""

    def test_creates_with_resource_and_id(self) -> None:
        """Test creating NotFoundError."""
        exc = NotFoundError("User", 123)

        assert "User not found: 123" in exc.message
        assert exc.status_code == 404
        assert exc.details["resource"] == "User"
        assert exc.details["identifier"] == "123"

    def test_to_dict_includes_details(self) -> None:
        """Test that to_dict includes resource details."""
        exc = NotFoundError("Task", "abc-123")

        result = exc.to_dict()

        assert result["error"] == "NotFoundError"
        assert result["status_code"] == 404
        assert result["details"]["resource"] == "Task"


class TestValidationError:
    """Tests for ValidationError."""

    def test_creates_without_field(self) -> None:
        """Test creating ValidationError without field."""
        exc = ValidationError("Invalid data")

        assert exc.message == "Invalid data"
        assert exc.status_code == 422
        assert exc.details == {}

    def test_creates_with_field(self) -> None:
        """Test creating ValidationError with field."""
        exc = ValidationError("Invalid email", field="email")

        assert exc.message == "Invalid email"
        assert exc.status_code == 422
        assert exc.details["field"] == "email"


class TestUnauthorizedError:
    """Tests for UnauthorizedError."""

    def test_creates_with_default_message(self) -> None:
        """Test creating UnauthorizedError with default message."""
        exc = UnauthorizedError()

        assert exc.message == "Authentication required"
        assert exc.status_code == 401

    def test_creates_with_custom_message(self) -> None:
        """Test creating UnauthorizedError with custom message."""
        exc = UnauthorizedError("Invalid token")

        assert exc.message == "Invalid token"
        assert exc.status_code == 401


class TestForbiddenError:
    """Tests for ForbiddenError."""

    def test_creates_with_default_message(self) -> None:
        """Test creating ForbiddenError with default message."""
        exc = ForbiddenError()

        assert exc.message == "Permission denied"
        assert exc.status_code == 403

    def test_creates_with_custom_message(self) -> None:
        """Test creating ForbiddenError with custom message."""
        exc = ForbiddenError("Admin access required")

        assert exc.message == "Admin access required"
        assert exc.status_code == 403


class TestConflictError:
    """Tests for ConflictError."""

    def test_creates_with_resource(self) -> None:
        """Test creating ConflictError."""
        exc = ConflictError("User already exists", "User")

        assert exc.message == "User already exists"
        assert exc.status_code == 409
        assert exc.details["resource"] == "User"


class TestServiceUnavailableError:
    """Tests for ServiceUnavailableError."""

    def test_creates_without_reason(self) -> None:
        """Test creating ServiceUnavailableError without reason."""
        exc = ServiceUnavailableError("database")

        assert "Service database unavailable" in exc.message
        assert exc.status_code == 503
        assert exc.details["service"] == "database"

    def test_creates_with_reason(self) -> None:
        """Test creating ServiceUnavailableError with reason."""
        exc = ServiceUnavailableError("redis", "connection timeout")

        assert "Service redis unavailable: connection timeout" in exc.message
        assert exc.status_code == 503
        assert exc.details["reason"] == "connection timeout"
