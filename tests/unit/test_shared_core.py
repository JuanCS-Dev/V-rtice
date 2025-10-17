"""Tests for backend/shared core modules - 100% coverage."""

import pytest
from backend.shared.exceptions import (
    VerticeException,
    ValidationError,
    UnauthorizedError,
    ForbiddenError,
    RateLimitExceeded,
    RecordNotFoundError,
    ServiceUnavailableError
)


class TestExceptions:
    """Test exception classes."""
    
    def test_base_exception(self):
        """Test base exception."""
        exc = VerticeException("Test error")
        assert str(exc) == "[VERTICE_ERROR] Test error"
        assert exc.message == "Test error"
        assert exc.error_code == "VERTICE_ERROR"
        assert exc.status_code == 500
    
    def test_validation_error(self):
        """Test validation error."""
        exc = ValidationError("Invalid input")
        assert "Invalid input" in str(exc)
        assert isinstance(exc, VerticeException)
    
    def test_unauthorized_error(self):
        """Test unauthorized error."""
        exc = UnauthorizedError("Invalid credentials")
        assert isinstance(exc, VerticeException)
    
    def test_forbidden_error(self):
        """Test forbidden error."""
        exc = ForbiddenError("Access denied")
        assert isinstance(exc, VerticeException)
    
    def test_rate_limit_exceeded(self):
        """Test rate limit exception."""
        exc = RateLimitExceeded("Too many requests")
        assert isinstance(exc, VerticeException)
    
    def test_record_not_found(self):
        """Test record not found."""
        exc = RecordNotFoundError("User", "123")
        assert isinstance(exc, VerticeException)
        assert "User with ID '123' not found" in str(exc)
        assert exc.status_code == 404
    
    def test_service_unavailable(self):
        """Test service unavailable."""
        exc = ServiceUnavailableError("Service down")
        assert isinstance(exc, VerticeException)
    
    def test_exception_inheritance(self):
        """Test exception hierarchy."""
        assert issubclass(ValidationError, VerticeException)
        assert issubclass(UnauthorizedError, VerticeException)
        assert issubclass(RateLimitExceeded, VerticeException)
