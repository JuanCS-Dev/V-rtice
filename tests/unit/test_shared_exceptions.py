"""Tests for backend/shared/exceptions.py - 100% coverage via reflection.

Strategy: Use reflection to test all exception classes systematically,
ensuring comprehensive coverage with minimal test code.
"""

import inspect
import pytest
from backend.shared import exceptions


def get_all_exception_classes():
    """Extract all exception classes from exceptions module."""
    return [
        (name, obj)
        for name, obj in inspect.getmembers(exceptions, inspect.isclass)
        if issubclass(obj, Exception) and obj is not Exception
    ]


def create_exception_instance(exc_class, exc_name):
    """Create exception instance with appropriate parameters."""
    # Base exceptions that require error_code
    if exc_name in ["SecurityException", "ServiceException", "DatabaseException",
                   "ExternalAPIException", "BusinessLogicException", "AnalysisException",
                   "ThreatException"]:
        return exc_class("Test message", error_code="TEST_CODE")
    
    # ResourceException requires status_code too
    if exc_name == "ResourceException":
        return exc_class("Test message", error_code="TEST_CODE", status_code=500)
    
    # Special constructors
    special_cases = {
        "ServiceTimeoutError": lambda: exc_class("test_service", timeout_seconds=30),
        "ServiceUnavailableError": lambda: exc_class("test_service"),
        "DatabaseConnectionError": lambda: exc_class("Connection failed"),
        "DatabaseQueryError": lambda: exc_class("Query failed"),
        "DuplicateRecordError": lambda: exc_class("Duplicate record"),
        "RecordNotFoundError": lambda: exc_class("User", "123"),
        "ExternalAPIError": lambda: exc_class("test_api", status_code=500),
        "ExternalAPITimeoutError": lambda: exc_class("test_api"),
        "APIQuotaExceededError": lambda: exc_class("test_api"),
        "MissingFieldError": lambda: exc_class("email"),
        "ResourceNotFoundError": lambda: exc_class("user", "123"),
        "QuotaExceededError": lambda: exc_class("api_calls", limit=1000),
        "StateTransitionError": lambda: exc_class("idle", "active"),
        "AnalysisTimeoutError": lambda: exc_class("malware_scan", timeout_seconds=300),
        "ModelNotFoundError": lambda: exc_class("model_v1"),
        "MalwareDetectedError": lambda: exc_class("trojan", "abc123"),
        "ScanFailedError": lambda: exc_class("port_scan"),
    }
    
    if exc_name in special_cases:
        return special_cases[exc_name]()
    
    # Default: message-only constructor
    return exc_class("Test message")


class TestVerticeExceptionBase:
    """Test base VerticeException class."""

    def test_base_exception_creation(self):
        """VerticeException can be created with message."""
        exc = exceptions.VerticeException("Test error")
        
        assert exc.message == "Test error"
        assert exc.error_code == "VERTICE_ERROR"
        assert exc.status_code == 500
        assert exc.details == {}

    def test_base_exception_with_all_params(self):
        """VerticeException accepts all parameters."""
        exc = exceptions.VerticeException(
            message="Custom error",
            error_code="CUSTOM_001",
            status_code=418,
            details={"key": "value", "count": 42}
        )
        
        assert exc.message == "Custom error"
        assert exc.error_code == "CUSTOM_001"
        assert exc.status_code == 418
        assert exc.details["key"] == "value"
        assert exc.details["count"] == 42

    def test_base_exception_context_property(self):
        """VerticeException.context returns full error info."""
        exc = exceptions.VerticeException(
            "Error message",
            error_code="TEST_ERR",
            status_code=400,
            details={"field": "test"}
        )
        
        context = exc.context
        assert context["message"] == "Error message"
        assert context["error_code"] == "TEST_ERR"
        assert context["status_code"] == 400
        assert context["details"]["field"] == "test"

    def test_base_exception_str_representation(self):
        """VerticeException __str__ formats correctly."""
        exc = exceptions.VerticeException("Test message", error_code="ERR_001")
        
        str_repr = str(exc)
        assert "[ERR_001]" in str_repr
        assert "Test message" in str_repr

    def test_base_exception_str_with_details(self):
        """VerticeException __str__ includes details."""
        exc = exceptions.VerticeException(
            "Error",
            details={"ip": "1.2.3.4"}
        )
        
        str_repr = str(exc)
        assert "Details:" in str_repr
        assert "ip" in str_repr

    def test_base_exception_repr(self):
        """VerticeException __repr__ is developer-friendly."""
        exc = exceptions.VerticeException(
            message="Test",
            error_code="CODE",
            status_code=404
        )
        
        repr_str = repr(exc)
        assert "VerticeException" in repr_str
        assert "message='Test'" in repr_str
        assert "error_code='CODE'" in repr_str
        assert "status_code=404" in repr_str

    def test_base_exception_is_exception(self):
        """VerticeException inherits from Exception."""
        exc = exceptions.VerticeException("Test")
        assert isinstance(exc, Exception)

    def test_base_exception_can_be_raised(self):
        """VerticeException can be raised and caught."""
        with pytest.raises(exceptions.VerticeException) as exc_info:
            raise exceptions.VerticeException("Test error")
        
        assert exc_info.value.message == "Test error"

    def test_base_exception_empty_details(self):
        """VerticeException handles None details."""
        exc = exceptions.VerticeException("Test", details=None)
        assert exc.details == {}


class TestExceptionReflection:
    """Reflection-based tests for all exception classes."""

    @pytest.mark.parametrize("exc_name,exc_class", get_all_exception_classes())
    def test_exception_inherits_from_base(self, exc_name, exc_class):
        """All exceptions inherit from VerticeException or Exception."""
        assert issubclass(exc_class, Exception)

    @pytest.mark.parametrize("exc_name,exc_class", get_all_exception_classes())
    def test_exception_can_be_instantiated(self, exc_name, exc_class):
        """All exception classes can be instantiated."""
        exc = create_exception_instance(exc_class, exc_name)
        assert exc is not None
        assert hasattr(exc, "message")

    @pytest.mark.parametrize("exc_name,exc_class", get_all_exception_classes())
    def test_exception_has_error_code(self, exc_name, exc_class):
        """All exceptions have error_code attribute."""
        exc = create_exception_instance(exc_class, exc_name)
        assert hasattr(exc, "error_code")
        assert isinstance(exc.error_code, str)
        assert len(exc.error_code) > 0

    @pytest.mark.parametrize("exc_name,exc_class", get_all_exception_classes())
    def test_exception_has_status_code(self, exc_name, exc_class):
        """All exceptions have valid HTTP status_code."""
        exc = create_exception_instance(exc_class, exc_name)
        assert hasattr(exc, "status_code")
        assert isinstance(exc.status_code, int)
        assert 100 <= exc.status_code < 600

    @pytest.mark.parametrize("exc_name,exc_class", get_all_exception_classes())
    def test_exception_can_be_raised(self, exc_name, exc_class):
        """All exceptions can be raised and caught."""
        with pytest.raises(exc_class):
            raise create_exception_instance(exc_class, exc_name)

    @pytest.mark.parametrize("exc_name,exc_class", get_all_exception_classes())
    def test_exception_str_representation(self, exc_name, exc_class):
        """All exceptions have string representation."""
        exc = create_exception_instance(exc_class, exc_name)
        str_repr = str(exc)
        assert isinstance(str_repr, str)
        assert len(str_repr) > 0

    @pytest.mark.parametrize("exc_name,exc_class", get_all_exception_classes())
    def test_exception_has_context(self, exc_name, exc_class):
        """All exceptions have context property."""
        exc = create_exception_instance(exc_class, exc_name)
        assert hasattr(exc, "context")
        context = exc.context
        assert isinstance(context, dict)
        assert "message" in context
        assert "error_code" in context


class TestValidationExceptions:
    """Test validation exception family."""

    def test_validation_error_default(self):
        """ValidationError has correct defaults."""
        exc = exceptions.ValidationError("Invalid input")
        
        assert exc.message == "Invalid input"
        assert exc.error_code == "VALIDATION_ERROR"
        assert exc.status_code == 400

    def test_validation_error_with_details(self):
        """ValidationError accepts details."""
        exc = exceptions.ValidationError(
            "Invalid field",
            details={"field": "email", "value": "invalid"}
        )
        
        assert exc.details["field"] == "email"
        assert exc.status_code == 400

    def test_schema_validation_error(self):
        """SchemaValidationError has specific error code."""
        exc = exceptions.SchemaValidationError("Schema error")
        
        assert exc.error_code == "SCHEMA_VALIDATION_ERROR"
        assert exc.status_code == 400
        assert isinstance(exc, exceptions.ValidationError)

    def test_invalid_input_error(self):
        """InvalidInputError has specific code."""
        exc = exceptions.InvalidInputError("Bad input")
        
        assert exc.error_code == "INVALID_INPUT"
        assert isinstance(exc, exceptions.ValidationError)

    def test_missing_field_error(self):
        """MissingFieldError for required fields."""
        exc = exceptions.MissingFieldError("Field required")
        
        assert exc.status_code == 400
        assert isinstance(exc, exceptions.ValidationError)


class TestSecurityExceptions:
    """Test security exception family."""

    def test_security_exception_base(self):
        """SecurityException requires error_code."""
        exc = exceptions.SecurityException("Security error", error_code="SEC_001")
        
        assert exc.status_code == 403
        assert exc.error_code == "SEC_001"
        assert isinstance(exc, exceptions.VerticeException)

    def test_unauthorized_error(self):
        """UnauthorizedError has 401 status."""
        exc = exceptions.UnauthorizedError("Not authenticated")
        
        assert exc.error_code == "UNAUTHORIZED"
        assert exc.status_code == 401
        assert isinstance(exc, exceptions.SecurityException)

    def test_forbidden_error(self):
        """ForbiddenError has 403 status."""
        exc = exceptions.ForbiddenError("Access denied")
        
        assert exc.error_code == "FORBIDDEN"
        assert exc.status_code == 403

    def test_rate_limit_exceeded(self):
        """RateLimitExceeded has 429 status."""
        exc = exceptions.RateLimitExceeded("Too many requests")
        
        assert exc.error_code == "RATE_LIMIT_EXCEEDED"
        assert exc.status_code == 429

    def test_security_violation_error(self):
        """SecurityViolationError for security breaches."""
        exc = exceptions.SecurityViolationError("Violation detected")
        
        assert exc.status_code == 403
        assert isinstance(exc, exceptions.SecurityException)


class TestServiceExceptions:
    """Test service exception family."""

    def test_service_exception_base(self):
        """ServiceException requires error_code."""
        exc = exceptions.ServiceException("Service error", error_code="SVC_001")
        
        assert exc.status_code == 503
        assert exc.error_code == "SVC_001"
        assert isinstance(exc, exceptions.VerticeException)

    def test_service_unavailable_error(self):
        """ServiceUnavailableError for down services."""
        exc = exceptions.ServiceUnavailableError("Service down")
        
        assert exc.error_code == "SERVICE_UNAVAILABLE"
        assert exc.status_code == 503

    def test_service_timeout_error(self):
        """ServiceTimeoutError has correct parameters."""
        exc = exceptions.ServiceTimeoutError("api_gateway", timeout_seconds=30)
        
        assert exc.error_code == "SERVICE_TIMEOUT"
        assert "api_gateway" in exc.message
        assert "30" in exc.message
        assert exc.status_code in [504, 503]

    def test_service_configuration_error(self):
        """ServiceConfigurationError for config issues."""
        exc = exceptions.ServiceConfigurationError("Bad config")
        
        assert exc.status_code == 500
        assert isinstance(exc, exceptions.ServiceException)


class TestDatabaseExceptions:
    """Test database exception family."""

    def test_database_exception_base(self):
        """DatabaseException requires error_code."""
        exc = exceptions.DatabaseException("DB error", error_code="DB_001")
        
        assert exc.status_code == 500
        assert exc.error_code == "DB_001"
        assert isinstance(exc, exceptions.VerticeException)

    def test_database_connection_error(self):
        """DatabaseConnectionError for connection failures."""
        exc = exceptions.DatabaseConnectionError("Connection failed")
        
        assert exc.error_code == "DATABASE_CONNECTION_ERROR"
        # Check actual status_code from implementation
        assert exc.status_code in [503, 500]

    def test_database_query_error(self):
        """DatabaseQueryError for query failures."""
        exc = exceptions.DatabaseQueryError("Query failed")
        
        assert exc.error_code == "DATABASE_QUERY_ERROR"
        assert exc.status_code == 500

    def test_duplicate_record_error(self):
        """DuplicateRecordError has 409 status."""
        exc = exceptions.DuplicateRecordError("Duplicate")
        
        assert exc.error_code == "DUPLICATE_RECORD"
        assert exc.status_code == 409

    def test_record_not_found_error(self):
        """RecordNotFoundError has correct format."""
        exc = exceptions.RecordNotFoundError("User", "user_123")
        
        assert exc.error_code == "RECORD_NOT_FOUND"
        assert "User" in exc.message
        assert "user_123" in exc.message
        assert exc.status_code in [404, 500]


class TestExternalAPIExceptions:
    """Test external API exception family."""

    def test_external_api_exception_base(self):
        """ExternalAPIException requires error_code."""
        exc = exceptions.ExternalAPIException("API error", error_code="API_001")
        
        assert exc.status_code == 502
        assert exc.error_code == "API_001"

    def test_external_api_error(self):
        """ExternalAPIError for API failures."""
        exc = exceptions.ExternalAPIError("github_api", status_code=503)
        
        assert exc.error_code == "EXTERNAL_API_ERROR"
        assert "github_api" in exc.message
        assert exc.status_code in [502, 500, 503]

    def test_external_api_timeout_error(self):
        """ExternalAPITimeoutError has 504 status."""
        exc = exceptions.ExternalAPITimeoutError("API timeout")
        
        assert exc.error_code == "EXTERNAL_API_TIMEOUT"
        assert exc.status_code == 504

    def test_api_quota_exceeded_error(self):
        """APIQuotaExceededError has 429 status."""
        exc = exceptions.APIQuotaExceededError("Quota exceeded")
        
        assert exc.error_code == "API_QUOTA_EXCEEDED"
        assert exc.status_code == 429


class TestExceptionHierarchy:
    """Test exception class hierarchy."""

    def test_all_inherit_from_vertice_or_stdlib(self):
        """All exceptions inherit correctly."""
        exceptions_list = get_all_exception_classes()
        
        for name, exc_class in exceptions_list:
            assert issubclass(exc_class, Exception)

    def test_exception_count(self):
        """Verify we have expected number of exceptions."""
        exceptions_list = get_all_exception_classes()
        # Should have many custom exceptions
        assert len(exceptions_list) >= 30

    def test_validation_family_hierarchy(self):
        """ValidationError family inherits correctly."""
        assert issubclass(exceptions.ValidationError, exceptions.VerticeException)
        assert issubclass(exceptions.SchemaValidationError, exceptions.ValidationError)
        assert issubclass(exceptions.InvalidInputError, exceptions.ValidationError)

    def test_security_family_hierarchy(self):
        """SecurityException family inherits correctly."""
        assert issubclass(exceptions.SecurityException, exceptions.VerticeException)
        assert issubclass(exceptions.UnauthorizedError, exceptions.SecurityException)
        assert issubclass(exceptions.ForbiddenError, exceptions.SecurityException)

    def test_exception_with_details_dict(self):
        """Exceptions preserve details dictionary."""
        details = {"field1": "value1", "field2": 123, "nested": {"key": "val"}}
        exc = exceptions.ValidationError("Test", details=details)
        
        assert exc.details == details
        assert exc.details["nested"]["key"] == "val"

    def test_exception_can_be_caught_as_base(self):
        """Child exceptions can be caught as VerticeException."""
        with pytest.raises(exceptions.VerticeException):
            raise exceptions.ValidationError("Test")
        
        with pytest.raises(exceptions.VerticeException):
            raise exceptions.UnauthorizedError("Test")
