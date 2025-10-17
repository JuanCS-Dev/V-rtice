"""Tests for vertice_core.exceptions - 100% coverage."""

import pytest
from vertice_core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ServiceUnavailableError,
    UnauthorizedError,
    ValidationError,
    VerticeException,
)


class TestVerticeException:
    """Test base VerticeException."""
    
    def test_basic_exception(self):
        """Test basic exception creation."""
        exc = VerticeException(message="Test error")
        assert exc.message == "Test error"
        assert exc.status_code == 500
        assert exc.details == {}
        assert str(exc) == "Test error"
    
    def test_exception_with_details(self):
        """Test exception with details."""
        details = {"field": "value", "error": "specific"}
        exc = VerticeException(message="Error", details=details)
        assert exc.details == details
    
    def test_exception_custom_status_code(self):
        """Test exception with custom status code."""
        exc = VerticeException(message="Error", status_code=418)
        assert exc.status_code == 418
    
    def test_to_dict(self):
        """Test to_dict method."""
        exc = VerticeException(message="Test", status_code=500, details={"key": "value"})
        result = exc.to_dict()
        assert result["error"] == "VerticeException"
        assert result["message"] == "Test"
        assert result["status_code"] == 500
        assert result["details"] == {"key": "value"}


class TestValidationError:
    """Test ValidationError."""
    
    def test_default_status_code(self):
        """Test ValidationError has 422 status code."""
        exc = ValidationError(message="Invalid input")
        assert exc.status_code == 422
        assert exc.message == "Invalid input"
    
    def test_with_field(self):
        """Test ValidationError with field details."""
        exc = ValidationError(message="Invalid email", field="email")
        assert exc.details == {"field": "email"}
        assert exc.status_code == 422
    
    def test_without_field(self):
        """Test ValidationError without field."""
        exc = ValidationError(message="Invalid input")
        assert exc.details == {}
        assert exc.status_code == 422


class TestUnauthorizedError:
    """Test UnauthorizedError."""
    
    def test_default_status_code(self):
        """Test UnauthorizedError has 401 status code."""
        exc = UnauthorizedError(message="Invalid token")
        assert exc.status_code == 401
        assert exc.message == "Invalid token"
    
    def test_default_message(self):
        """Test UnauthorizedError with default message."""
        exc = UnauthorizedError()
        assert exc.status_code == 401
        assert exc.message == "Authentication required"


class TestForbiddenError:
    """Test ForbiddenError."""
    
    def test_default_status_code(self):
        """Test ForbiddenError has 403 status code."""
        exc = ForbiddenError(message="Access denied")
        assert exc.status_code == 403
        assert exc.message == "Access denied"
    
    def test_default_message(self):
        """Test ForbiddenError with default message."""
        exc = ForbiddenError()
        assert exc.status_code == 403
        assert exc.message == "Permission denied"


class TestNotFoundError:
    """Test NotFoundError."""
    
    def test_default_status_code(self):
        """Test NotFoundError has 404 status code."""
        exc = NotFoundError(resource="User", identifier=123)
        assert exc.status_code == 404
        assert "User" in exc.message
        assert "123" in exc.message
    
    def test_resource_details(self):
        """Test NotFoundError with resource details."""
        exc = NotFoundError(resource="user", identifier=456)
        assert exc.details == {"resource": "user", "identifier": "456"}
        assert exc.status_code == 404


class TestConflictError:
    """Test ConflictError."""
    
    def test_default_status_code(self):
        """Test ConflictError has 409 status code."""
        exc = ConflictError(message="Email already exists", resource="User")
        assert exc.status_code == 409
        assert "Email already exists" in exc.message
    
    def test_conflict_details(self):
        """Test ConflictError with conflict details."""
        exc = ConflictError(message="Duplicate entry", resource="email")
        assert exc.details == {"resource": "email"}
        assert exc.status_code == 409


class TestServiceUnavailableError:
    """Test ServiceUnavailableError."""
    
    def test_default_status_code(self):
        """Test ServiceUnavailableError has 503 status code."""
        exc = ServiceUnavailableError(service_name="database")
        assert exc.status_code == 503
        assert "database" in exc.message
    
    def test_service_details(self):
        """Test ServiceUnavailableError with reason."""
        exc = ServiceUnavailableError(service_name="postgresql", reason="Connection timeout")
        assert exc.details == {"service": "postgresql", "reason": "Connection timeout"}
        assert exc.status_code == 503
        assert "Connection timeout" in exc.message


class TestExceptionHierarchy:
    """Test exception hierarchy and inheritance."""
    
    def test_all_inherit_from_vertice_exception(self):
        """Test that all custom exceptions inherit from VerticeException."""
        exceptions = [
            ValidationError,
            UnauthorizedError,
            ForbiddenError,
            NotFoundError,
            ConflictError,
            ServiceUnavailableError,
        ]
        
        for exc_class in exceptions:
            assert issubclass(exc_class, VerticeException)
    
    def test_all_inherit_from_exception(self):
        """Test that all exceptions inherit from Exception."""
        exceptions = [
            VerticeException,
            ValidationError,
            UnauthorizedError,
            ForbiddenError,
            NotFoundError,
            ConflictError,
            ServiceUnavailableError,
        ]
        
        for exc_class in exceptions:
            assert issubclass(exc_class, Exception)
    
    def test_exception_raising(self):
        """Test that exceptions can be raised and caught."""
        with pytest.raises(VerticeException):
            raise VerticeException(message="Test")
        
        with pytest.raises(ValidationError):
            raise ValidationError(message="Test")
        
        with pytest.raises(NotFoundError):
            raise NotFoundError(resource="Test", identifier=1)
    
    def test_catch_base_exception(self):
        """Test catching specific exceptions as VerticeException."""
        try:
            raise ValidationError(message="Test", field="test_field")
        except VerticeException as e:
            assert isinstance(e, ValidationError)
            assert isinstance(e, VerticeException)
