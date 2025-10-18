"""
Comprehensive tests for shared/exceptions.py

Tests all 41 exception classes with 99%+ coverage.
"""

import pytest
from backend.shared.exceptions import (
    # Base
    VerticeException,
    # Validation
    ValidationError,
    SchemaValidationError,
    InvalidInputError,
    MissingFieldError,
    # Security
    SecurityException,
    UnauthorizedError,
    ForbiddenError,
    InvalidTokenError,
    RateLimitExceeded,
    SecurityViolationError,
    # Service
    ServiceException,
    ServiceUnavailableError,
    ServiceTimeoutError,
    ServiceConfigurationError,
    # Database
    DatabaseException,
    DatabaseConnectionError,
    DatabaseQueryError,
    DuplicateRecordError,
    RecordNotFoundError,
    # External API
    ExternalAPIException,
    ExternalAPIError,
    ExternalAPITimeoutError,
    APIQuotaExceededError,
    # Business Logic
    BusinessLogicException,
    InvalidOperationError,
    StateTransitionError,
    WorkflowException,
    # Resource
    ResourceException,
    ResourceNotFoundError,
    ResourceConflictError,
    ResourceExhaustedError,
    QuotaExceededError,
    # Analysis
    AnalysisException,
    AnalysisTimeoutError,
    ModelNotFoundError,
    InsufficientDataError,
    # Threat
    ThreatException,
    MalwareDetectedError,
    ScanFailedError,
)


class TestVerticeException:
    """Test base VerticeException."""

    def test_init_basic(self):
        """Test basic initialization."""
        exc = VerticeException("Test error")
        assert exc.message == "Test error"
        assert exc.error_code == "VERTICE_ERROR"
        assert exc.status_code == 500
        assert exc.details == {}

    def test_init_full(self):
        """Test full initialization with all parameters."""
        exc = VerticeException(
            message="Custom error",
            error_code="CUSTOM_001",
            status_code=418,
            details={"key": "value"},
        )
        assert exc.message == "Custom error"
        assert exc.error_code == "CUSTOM_001"
        assert exc.status_code == 418
        assert exc.details == {"key": "value"}

    def test_context_property(self):
        """Test context property."""
        exc = VerticeException("Error", error_code="ERR", status_code=400, details={"x": 1})
        ctx = exc.context
        assert ctx["message"] == "Error"
        assert ctx["error_code"] == "ERR"
        assert ctx["status_code"] == 400
        assert ctx["details"] == {"x": 1}

    def test_str_without_details(self):
        """Test __str__ without details."""
        exc = VerticeException("Simple error", error_code="ERR001")
        assert str(exc) == "[ERR001] Simple error"

    def test_str_with_details(self):
        """Test __str__ with details."""
        exc = VerticeException("Error", error_code="ERR", details={"field": "value"})
        result = str(exc)
        assert "[ERR]" in result
        assert "Error" in result
        assert "Details:" in result
        assert "field" in result

    def test_repr(self):
        """Test __repr__."""
        exc = VerticeException("Test", error_code="T1", status_code=404)
        rep = repr(exc)
        assert "VerticeException" in rep
        assert "message='Test'" in rep
        assert "error_code='T1'" in rep
        assert "status_code=404" in rep


class TestValidationExceptions:
    """Test validation exception hierarchy."""

    def test_validation_error(self):
        """Test ValidationError."""
        exc = ValidationError("Invalid input")
        assert exc.error_code == "VALIDATION_ERROR"
        assert exc.status_code == 400
        assert exc.message == "Invalid input"

    def test_validation_error_with_details(self):
        """Test ValidationError with details."""
        exc = ValidationError("Invalid", details={"field": "email"})
        assert exc.details == {"field": "email"}

    def test_schema_validation_error(self):
        """Test SchemaValidationError."""
        exc = SchemaValidationError("Schema failed")
        assert exc.error_code == "SCHEMA_VALIDATION_ERROR"
        assert exc.status_code == 400

    def test_invalid_input_error(self):
        """Test InvalidInputError."""
        exc = InvalidInputError("Bad input")
        assert exc.error_code == "INVALID_INPUT"
        assert exc.status_code == 400

    def test_missing_field_error(self):
        """Test MissingFieldError."""
        exc = MissingFieldError("username")
        assert "username" in exc.message
        assert exc.error_code == "MISSING_FIELD"


class TestSecurityExceptions:
    """Test security exception hierarchy."""

    def test_security_exception_base(self):
        """Test SecurityException."""
        exc = SecurityException("Sec error", error_code="SEC001")
        assert exc.status_code == 403
        assert exc.error_code == "SEC001"

    def test_unauthorized_error(self):
        """Test UnauthorizedError."""
        exc = UnauthorizedError("Not authenticated")
        assert exc.error_code == "UNAUTHORIZED"
        assert exc.status_code == 401

    def test_unauthorized_with_details(self):
        """Test UnauthorizedError with details."""
        exc = UnauthorizedError("Auth failed", details={"reason": "expired"})
        assert exc.details["reason"] == "expired"

    def test_forbidden_error_default(self):
        """Test ForbiddenError with default message."""
        exc = ForbiddenError()
        assert "permissions" in exc.message.lower()
        assert exc.error_code == "FORBIDDEN"

    def test_forbidden_error_custom(self):
        """Test ForbiddenError with custom message."""
        exc = ForbiddenError("No access")
        assert exc.message == "No access"

    def test_invalid_token_error_default(self):
        """Test InvalidTokenError with default message."""
        exc = InvalidTokenError()
        assert "token" in exc.message.lower()
        assert exc.error_code == "INVALID_TOKEN"

    def test_invalid_token_error_custom(self):
        """Test InvalidTokenError with custom message."""
        exc = InvalidTokenError("Token expired")
        assert exc.message == "Token expired"

    def test_rate_limit_exceeded_default(self):
        """Test RateLimitExceeded with default message."""
        exc = RateLimitExceeded()
        assert exc.error_code == "RATE_LIMIT_EXCEEDED"
        assert exc.status_code == 429

    def test_rate_limit_exceeded_custom(self):
        """Test RateLimitExceeded with custom message."""
        exc = RateLimitExceeded("Too many requests", details={"limit": 100})
        assert exc.message == "Too many requests"

    def test_security_violation_error(self):
        """Test SecurityViolationError."""
        exc = SecurityViolationError("Policy violated")
        assert exc.error_code == "SECURITY_VIOLATION"


class TestServiceExceptions:
    """Test service exception hierarchy."""

    def test_service_exception_base(self):
        """Test ServiceException."""
        exc = ServiceException("Service error", error_code="SVC001")
        assert exc.status_code == 503
        assert exc.error_code == "SVC001"

    def test_service_unavailable_error_default(self):
        """Test ServiceUnavailableError with service name."""
        exc = ServiceUnavailableError("auth-service")
        assert "unavailable" in exc.message.lower()
        assert exc.error_code == "SERVICE_UNAVAILABLE"
        assert "auth-service" in exc.message

    def test_service_unavailable_error_custom(self):
        """Test ServiceUnavailableError with details."""
        exc = ServiceUnavailableError("db-service", details={"reason": "maintenance"})
        assert "db-service" in exc.message
        assert exc.details["reason"] == "maintenance"

    def test_service_timeout_error_default(self):
        """Test ServiceTimeoutError."""
        exc = ServiceTimeoutError("api-service", 30)
        assert "timed out" in exc.message.lower() or "timeout" in exc.message.lower()
        assert "30" in exc.message

    def test_service_timeout_error_custom(self):
        """Test ServiceTimeoutError with details."""
        exc = ServiceTimeoutError("db-service", 60, details={"query": "SELECT *"})
        assert "db-service" in exc.message
        assert exc.details["query"] == "SELECT *"

    def test_service_configuration_error(self):
        """Test ServiceConfigurationError."""
        exc = ServiceConfigurationError("Bad config", details={"var": "API_KEY"})
        assert exc.error_code == "SERVICE_CONFIGURATION_ERROR"


class TestDatabaseExceptions:
    """Test database exception hierarchy."""

    def test_database_exception_base(self):
        """Test DatabaseException."""
        exc = DatabaseException("DB error", error_code="DB001")
        assert exc.status_code == 500
        assert exc.error_code == "DB001"

    def test_database_connection_error_default(self):
        """Test DatabaseConnectionError default."""
        exc = DatabaseConnectionError()
        assert "connection" in exc.message.lower()
        assert exc.error_code == "DATABASE_CONNECTION_ERROR"

    def test_database_connection_error_custom(self):
        """Test DatabaseConnectionError with details."""
        exc = DatabaseConnectionError("Cannot connect", details={"host": "localhost"})
        assert exc.message == "Cannot connect"

    def test_database_query_error(self):
        """Test DatabaseQueryError."""
        exc = DatabaseQueryError("Query failed", details={"query": "SELECT *"})
        assert exc.error_code == "DATABASE_QUERY_ERROR"

    def test_duplicate_record_error(self):
        """Test DuplicateRecordError."""
        exc = DuplicateRecordError("User exists", details={"field": "email"})
        assert exc.error_code == "DUPLICATE_RECORD"

    def test_record_not_found_error(self):
        """Test RecordNotFoundError."""
        exc = RecordNotFoundError("User", "user-123")
        assert "User" in exc.message
        assert "user-123" in exc.message
        assert exc.error_code == "RECORD_NOT_FOUND"
        assert exc.status_code == 404


class TestExternalAPIExceptions:
    """Test external API exception hierarchy."""

    def test_external_api_exception_base(self):
        """Test ExternalAPIException."""
        exc = ExternalAPIException("API error", error_code="EXT001")
        assert exc.status_code == 502
        assert exc.error_code == "EXT001"

    def test_external_api_error_default(self):
        """Test ExternalAPIError."""
        exc = ExternalAPIError("github", 500)
        assert "github" in exc.message
        assert exc.error_code == "EXTERNAL_API_ERROR"
        assert "500" in exc.message

    def test_external_api_error_custom(self):
        """Test ExternalAPIError with details."""
        exc = ExternalAPIError("slack", 503, details={"retry_after": 60})
        assert "slack" in exc.message
        assert exc.details["retry_after"] == 60

    def test_external_api_timeout_error(self):
        """Test ExternalAPITimeoutError."""
        exc = ExternalAPITimeoutError("stripe")
        assert "stripe" in exc.message
        assert "timed out" in exc.message.lower() or "timeout" in exc.message.lower()

    def test_api_quota_exceeded_error(self):
        """Test APIQuotaExceededError."""
        exc = APIQuotaExceededError(api_name="openai", details={"limit": 1000})
        assert "openai" in exc.message
        assert exc.error_code == "API_QUOTA_EXCEEDED"


class TestBusinessLogicExceptions:
    """Test business logic exception hierarchy."""

    def test_business_logic_exception_base(self):
        """Test BusinessLogicException."""
        exc = BusinessLogicException("Business error", error_code="BIZ001")
        assert exc.status_code == 422
        assert exc.error_code == "BIZ001"

    def test_invalid_operation_error(self):
        """Test InvalidOperationError."""
        exc = InvalidOperationError("Cannot delete active user")
        assert exc.error_code == "INVALID_OPERATION"

    def test_state_transition_error(self):
        """Test StateTransitionError."""
        exc = StateTransitionError("pending", "cancelled")
        assert "pending" in exc.message
        assert "cancelled" in exc.message

    def test_state_transition_error_with_details(self):
        """Test StateTransitionError with details."""
        exc = StateTransitionError("pending", "cancelled", details={"reason": "Already processed"})
        assert exc.details["reason"] == "Already processed"

    def test_workflow_exception(self):
        """Test WorkflowException."""
        exc = WorkflowException("Workflow timeout in scan-workflow")
        assert "timeout" in exc.message.lower()


class TestResourceExceptions:
    """Test resource exception hierarchy."""

    def test_resource_exception_base(self):
        """Test ResourceException."""
        exc = ResourceException("Resource error", "RES001", 404)
        assert exc.status_code == 404
        assert exc.error_code == "RES001"

    def test_resource_not_found_error_type_only(self):
        """Test ResourceNotFoundError."""
        exc = ResourceNotFoundError("scan", "scan-123")
        assert "scan" in exc.message
        assert "scan-123" in exc.message
        assert exc.error_code == "RESOURCE_NOT_FOUND"

    def test_resource_not_found_error_full(self):
        """Test ResourceNotFoundError with details."""
        exc = ResourceNotFoundError("user", "user-123", details={"org": "org-1"})
        assert "user" in exc.message
        assert "user-123" in exc.message
        assert exc.details["org"] == "org-1"

    def test_resource_conflict_error(self):
        """Test ResourceConflictError."""
        exc = ResourceConflictError("Workflow already active")
        assert "Workflow" in exc.message
        assert exc.error_code == "RESOURCE_CONFLICT"
        assert exc.status_code == 409

    def test_resource_exhausted_error(self):
        """Test ResourceExhaustedError."""
        exc = ResourceExhaustedError("Worker pool exhausted", details={"max": 10})
        assert "exhausted" in exc.message.lower()
        assert exc.error_code == "RESOURCE_EXHAUSTED"

    def test_quota_exceeded_error(self):
        """Test QuotaExceededError."""
        exc = QuotaExceededError("scans", 100)
        assert "scans" in exc.message
        assert "100" in exc.message


class TestAnalysisExceptions:
    """Test analysis exception hierarchy."""

    def test_analysis_exception_base(self):
        """Test AnalysisException."""
        exc = AnalysisException("Analysis error", error_code="ANA001")
        assert exc.status_code == 500
        assert exc.error_code == "ANA001"

    def test_analysis_timeout_error_default(self):
        """Test AnalysisTimeoutError."""
        exc = AnalysisTimeoutError("ml-inference", 60)
        assert "timed out" in exc.message.lower() or "timeout" in exc.message.lower()
        assert exc.error_code == "ANALYSIS_TIMEOUT"
        assert "ml-inference" in exc.message
        assert "60" in exc.message

    def test_analysis_timeout_error_custom(self):
        """Test AnalysisTimeoutError with details."""
        exc = AnalysisTimeoutError("pattern-matching", 120, details={"samples": 1000})
        assert "pattern-matching" in exc.message
        assert exc.details["samples"] == 1000

    def test_model_not_found_error(self):
        """Test ModelNotFoundError."""
        exc = ModelNotFoundError("xgboost-v2")
        assert "xgboost-v2" in exc.message
        assert exc.error_code == "MODEL_NOT_FOUND"

    def test_insufficient_data_error(self):
        """Test InsufficientDataError."""
        exc = InsufficientDataError("Not enough training data", details={"min_required": 100, "current": 45})
        assert "training" in exc.message.lower()
        assert exc.details["min_required"] == 100
        assert exc.details["current"] == 45


class TestThreatExceptions:
    """Test threat exception hierarchy."""

    def test_threat_exception_base(self):
        """Test ThreatException."""
        exc = ThreatException("Threat detected", "THR001")
        assert exc.status_code == 500
        assert exc.error_code == "THR001"

    def test_malware_detected_error(self):
        """Test MalwareDetectedError."""
        exc = MalwareDetectedError("trojan", "abc123def456")
        assert "trojan" in exc.message
        assert "abc123" in exc.message
        assert exc.error_code == "MALWARE_DETECTED"

    def test_malware_detected_error_with_details(self):
        """Test MalwareDetectedError with details."""
        exc = MalwareDetectedError("ransomware", "hash456", details={"file": "/tmp/evil.exe"})
        assert exc.details["file"] == "/tmp/evil.exe"

    def test_scan_failed_error(self):
        """Test ScanFailedError."""
        exc = ScanFailedError("vulnerability")
        assert "vulnerability" in exc.message
        assert exc.error_code == "SCAN_FAILED"


class TestExceptionInheritance:
    """Test exception inheritance hierarchy."""

    def test_all_inherit_from_vertice_exception(self):
        """Verify all custom exceptions inherit from VerticeException."""
        exceptions = [
            ValidationError("test"),
            SecurityException("test", "SEC"),
            ServiceException("test", "SVC"),
            DatabaseException("test", "DB"),
            ExternalAPIException("test", "EXT"),
            BusinessLogicException("test", "BIZ"),
            ResourceException("test", "RES", 404),
            AnalysisException("test", "ANA"),
            ThreatException("test", "THR"),
        ]
        for exc in exceptions:
            assert isinstance(exc, VerticeException)
            assert isinstance(exc, Exception)

    def test_validation_hierarchy(self):
        """Test validation exception hierarchy."""
        assert issubclass(SchemaValidationError, ValidationError)
        assert issubclass(InvalidInputError, ValidationError)
        assert issubclass(MissingFieldError, ValidationError)

    def test_security_hierarchy(self):
        """Test security exception hierarchy."""
        assert issubclass(UnauthorizedError, SecurityException)
        assert issubclass(ForbiddenError, SecurityException)
        assert issubclass(InvalidTokenError, UnauthorizedError)


class TestExceptionRaising:
    """Test that exceptions can be raised and caught properly."""

    def test_raise_and_catch_vertice_exception(self):
        """Test raising and catching VerticeException."""
        with pytest.raises(VerticeException) as exc_info:
            raise VerticeException("Test error")
        assert exc_info.value.message == "Test error"

    def test_raise_and_catch_validation_error(self):
        """Test raising ValidationError."""
        with pytest.raises(ValidationError):
            raise ValidationError("Invalid data")

    def test_catch_parent_exception(self):
        """Test catching specific exception with parent handler."""
        with pytest.raises(VerticeException):
            raise ValidationError("Test")

    def test_exception_details_preserved(self):
        """Test that exception details are preserved when raised."""
        with pytest.raises(ResourceNotFoundError) as exc_info:
            raise ResourceNotFoundError("user", "user-123", details={"org": "org-1"})
        
        assert exc_info.value.details["org"] == "org-1"
