"""
Tests for Domain Layer - Exceptions

100% coverage required.
"""
import pytest

from service_template.domain.exceptions import (
    DomainException,
    EntityAlreadyExistsError,
    EntityNotFoundError,
    InvalidEntityStateError,
    ValidationError,
)


class TestDomainException:
    """Tests for base DomainException."""

    def test_creation(self) -> None:
        """Test domain exception creation."""
        exc = DomainException("Test error")
        assert str(exc) == "Test error"

    def test_is_exception(self) -> None:
        """Test domain exception is an Exception."""
        exc = DomainException("Test")
        assert isinstance(exc, Exception)


class TestEntityNotFoundError:
    """Tests for EntityNotFoundError."""

    def test_creation_minimal(self) -> None:
        """Test error with minimal parameters."""
        exc = EntityNotFoundError("123")
        
        assert exc.entity_id == "123"
        assert exc.entity_type == "Entity"
        assert "Entity not found: 123" in str(exc)

    def test_creation_with_type(self) -> None:
        """Test error with custom entity type."""
        exc = EntityNotFoundError("456", "User")
        
        assert exc.entity_id == "456"
        assert exc.entity_type == "User"
        assert "User not found: 456" in str(exc)

    def test_is_domain_exception(self) -> None:
        """Test is subclass of DomainException."""
        exc = EntityNotFoundError("123")
        assert isinstance(exc, DomainException)


class TestEntityAlreadyExistsError:
    """Tests for EntityAlreadyExistsError."""

    def test_creation_minimal(self) -> None:
        """Test error with minimal parameters."""
        exc = EntityAlreadyExistsError("test@example.com")
        
        assert exc.identifier == "test@example.com"
        assert exc.entity_type == "Entity"
        assert "Entity already exists: test@example.com" in str(exc)

    def test_creation_with_type(self) -> None:
        """Test error with custom entity type."""
        exc = EntityAlreadyExistsError("admin", "User")
        
        assert exc.identifier == "admin"
        assert exc.entity_type == "User"
        assert "User already exists: admin" in str(exc)

    def test_is_domain_exception(self) -> None:
        """Test is subclass of DomainException."""
        exc = EntityAlreadyExistsError("test")
        assert isinstance(exc, DomainException)


class TestInvalidEntityStateError:
    """Tests for InvalidEntityStateError."""

    def test_creation(self) -> None:
        """Test error creation."""
        exc = InvalidEntityStateError("123", "delete", "archived")
        
        assert exc.entity_id == "123"
        assert exc.operation == "delete"
        assert exc.current_state == "archived"
        assert "Cannot delete entity 123" in str(exc)
        assert "current state is archived" in str(exc)

    def test_different_operation(self) -> None:
        """Test with different operation."""
        exc = InvalidEntityStateError("456", "activate", "deleted")
        
        assert "Cannot activate entity 456" in str(exc)
        assert "current state is deleted" in str(exc)

    def test_is_domain_exception(self) -> None:
        """Test is subclass of DomainException."""
        exc = InvalidEntityStateError("123", "op", "state")
        assert isinstance(exc, DomainException)


class TestValidationError:
    """Tests for ValidationError."""

    def test_creation(self) -> None:
        """Test error creation."""
        exc = ValidationError("email", "Invalid format")
        
        assert exc.field == "email"
        assert exc.message == "Invalid format"
        assert "Validation error on email" in str(exc)
        assert "Invalid format" in str(exc)

    def test_different_field(self) -> None:
        """Test with different field."""
        exc = ValidationError("username", "Too short")
        
        assert exc.field == "username"
        assert exc.message == "Too short"
        assert "username" in str(exc)

    def test_is_domain_exception(self) -> None:
        """Test is subclass of DomainException."""
        exc = ValidationError("field", "message")
        assert isinstance(exc, DomainException)
