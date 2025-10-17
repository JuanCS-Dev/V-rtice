"""
Tests for backend/shared/error_handlers.py - 100% Coverage Target
==================================================================

Tests all exception handlers, response builders, and middleware.
"""

import logging
import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ValidationError as PydanticValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.shared.error_handlers import (
    build_error_response,
    extract_request_id,
    generic_exception_handler,
    http_exception_handler,
    pydantic_validation_exception_handler,
    register_error_handlers,
    request_id_middleware,
    validation_exception_handler,
    vertice_exception_handler,
)
from backend.shared.exceptions import (
    DatabaseConnectionError,
    RecordNotFoundError,
    UnauthorizedError,
    ValidationError,
    VerticeException,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_request():
    """Create mock FastAPI request."""
    request = MagicMock(spec=Request)
    request.url.path = "/api/test"
    request.method = "GET"
    request.headers = {}
    request.state = MagicMock()
    return request


@pytest.fixture
def mock_request_with_id():
    """Create mock request with existing request ID."""
    request = MagicMock(spec=Request)
    request.url.path = "/api/test"
    request.method = "POST"
    request.headers = {"X-Request-ID": "test-request-123"}
    request.state = MagicMock()
    return request


@pytest.fixture
def fastapi_app():
    """Create FastAPI app instance."""
    return FastAPI()


# ============================================================================
# TEST: build_error_response
# ============================================================================


class TestBuildErrorResponse:
    """Test error response builder function."""

    def test_minimal_error_response(self):
        """Test building error response with minimal params."""
        result = build_error_response(
            error_code="TEST_ERROR",
            message="Test message",
            status_code=400,
        )

        assert result["error"]["code"] == "TEST_ERROR"
        assert result["error"]["message"] == "Test message"
        assert result["error"]["status_code"] == 400
        assert result["error"]["details"] == {}
        assert "request_id" in result["error"]
        assert "timestamp" in result["error"]

    def test_full_error_response(self):
        """Test building error response with all params."""
        result = build_error_response(
            error_code="VALIDATION_ERROR",
            message="Invalid input",
            status_code=422,
            details={"field": "email", "reason": "invalid format"},
            request_id="custom-id-123",
        )

        assert result["error"]["code"] == "VALIDATION_ERROR"
        assert result["error"]["message"] == "Invalid input"
        assert result["error"]["status_code"] == 422
        assert result["error"]["details"]["field"] == "email"
        assert result["error"]["request_id"] == "custom-id-123"

    def test_timestamp_format(self):
        """Test timestamp is ISO8601 with Z suffix."""
        result = build_error_response("ERROR", "message", 500)
        timestamp = result["error"]["timestamp"]

        assert timestamp.endswith("Z")
        # Validate ISO8601 format
        datetime.fromisoformat(timestamp.rstrip("Z"))

    def test_auto_generate_request_id_if_none(self):
        """Test request ID is auto-generated when not provided."""
        result = build_error_response("ERROR", "message", 500, request_id=None)

        request_id = result["error"]["request_id"]
        assert request_id is not None
        # Validate UUID format
        uuid.UUID(request_id)


# ============================================================================
# TEST: extract_request_id
# ============================================================================


class TestExtractRequestId:
    """Test request ID extraction from headers."""

    def test_extract_from_x_request_id(self, mock_request):
        """Test extraction from X-Request-ID header."""
        mock_request.headers = {"X-Request-ID": "req-123"}
        result = extract_request_id(mock_request)
        assert result == "req-123"

    def test_extract_from_x_correlation_id(self, mock_request):
        """Test extraction from X-Correlation-ID header."""
        mock_request.headers = {"X-Correlation-ID": "corr-456"}
        result = extract_request_id(mock_request)
        assert result == "corr-456"

    def test_extract_from_x_trace_id(self, mock_request):
        """Test extraction from X-Trace-ID header."""
        mock_request.headers = {"X-Trace-ID": "trace-789"}
        result = extract_request_id(mock_request)
        assert result == "trace-789"

    def test_priority_order_of_headers(self, mock_request):
        """Test X-Request-ID takes priority over others."""
        mock_request.headers = {
            "X-Request-ID": "req-1",
            "X-Correlation-ID": "corr-2",
            "X-Trace-ID": "trace-3",
        }
        result = extract_request_id(mock_request)
        assert result == "req-1"

    def test_generate_new_id_if_no_headers(self, mock_request):
        """Test generating new UUID when no headers present."""
        mock_request.headers = {}
        result = extract_request_id(mock_request)

        # Should be valid UUID
        uuid.UUID(result)
        # Should store in request state
        assert mock_request.state.request_id == result

    def test_stores_generated_id_in_state(self, mock_request):
        """Test generated ID is stored in request.state."""
        mock_request.headers = {}
        result = extract_request_id(mock_request)
        assert hasattr(mock_request.state, "request_id")
        assert mock_request.state.request_id == result


# ============================================================================
# TEST: vertice_exception_handler
# ============================================================================


class TestVerticeExceptionHandler:
    """Test handler for VerticeException."""

    @pytest.mark.asyncio
    async def test_handles_authentication_error(self, mock_request):
        """Test handling UnauthorizedError (401)."""
        exc = UnauthorizedError("Invalid token")
        response = await vertice_exception_handler(mock_request, exc)

        assert response.status_code == 401
        assert response.body is not None
        content = eval(response.body.decode())
        assert content["error"]["code"] == "UNAUTHORIZED"
        assert "Invalid token" in content["error"]["message"]

    @pytest.mark.asyncio
    async def test_handles_not_found_error(self, mock_request):
        """Test handling RecordNotFoundError (404)."""
        exc = RecordNotFoundError("User", "123")
        response = await vertice_exception_handler(mock_request, exc)

        assert response.status_code == 404
        content = eval(response.body.decode())
        assert content["error"]["code"] == "RECORD_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_handles_validation_error(self, mock_request):
        """Test handling ValidationError (400)."""
        exc = ValidationError("Invalid input data", details={"field": "email"})
        response = await vertice_exception_handler(mock_request, exc)

        assert response.status_code == 400
        content = eval(response.body.decode())
        assert content["error"]["code"] == "VALIDATION_ERROR"
        assert content["error"]["details"]["field"] == "email"

    @pytest.mark.asyncio
    async def test_handles_database_error(self, mock_request):
        """Test handling DatabaseConnectionError (500)."""
        exc = DatabaseConnectionError("Connection failed")
        response = await vertice_exception_handler(mock_request, exc)

        assert response.status_code == 500
        content = eval(response.body.decode())
        assert content["error"]["code"] == "DATABASE_CONNECTION_ERROR"

    @pytest.mark.asyncio
    async def test_uses_existing_request_id(self, mock_request_with_id):
        """Test uses request ID from headers."""
        exc = RecordNotFoundError("User", "456")
        response = await vertice_exception_handler(mock_request_with_id, exc)

        content = eval(response.body.decode())
        assert content["error"]["request_id"] == "test-request-123"

    @pytest.mark.asyncio
    async def test_logs_server_errors(self, mock_request, caplog):
        """Test 500+ errors are logged as ERROR level."""
        with caplog.at_level(logging.ERROR):
            exc = DatabaseConnectionError("DB connection failed")
            await vertice_exception_handler(mock_request, exc)

        assert "Server error" in caplog.text
        assert "DB connection failed" in caplog.text

    @pytest.mark.asyncio
    async def test_logs_client_errors_as_warning(self, mock_request, caplog):
        """Test 4xx errors are logged as WARNING level."""
        with caplog.at_level(logging.WARNING):
            exc = RecordNotFoundError("Resource", "789")
            await vertice_exception_handler(mock_request, exc)

        assert "Client error" in caplog.text


# ============================================================================
# TEST: http_exception_handler
# ============================================================================


class TestHttpExceptionHandler:
    """Test handler for standard HTTP exceptions."""

    @pytest.mark.asyncio
    async def test_handles_404_not_found(self, mock_request):
        """Test 404 HTTP exception."""
        exc = StarletteHTTPException(status_code=404, detail="Page not found")
        response = await http_exception_handler(mock_request, exc)

        assert response.status_code == 404
        content = eval(response.body.decode())
        assert content["error"]["code"] == "NOT_FOUND"
        assert "Page not found" in content["error"]["message"]

    @pytest.mark.asyncio
    async def test_handles_401_unauthorized(self, mock_request):
        """Test 401 HTTP exception."""
        exc = StarletteHTTPException(status_code=401, detail="Unauthorized")
        response = await http_exception_handler(mock_request, exc)

        assert response.status_code == 401
        content = eval(response.body.decode())
        assert content["error"]["code"] == "UNAUTHORIZED"

    @pytest.mark.asyncio
    async def test_handles_429_rate_limit(self, mock_request):
        """Test 429 rate limiting exception."""
        exc = StarletteHTTPException(status_code=429, detail="Too many requests")
        response = await http_exception_handler(mock_request, exc)

        assert response.status_code == 429
        content = eval(response.body.decode())
        assert content["error"]["code"] == "TOO_MANY_REQUESTS"

    @pytest.mark.asyncio
    async def test_handles_500_server_error(self, mock_request):
        """Test 500 internal server error."""
        exc = StarletteHTTPException(status_code=500, detail="Internal error")
        response = await http_exception_handler(mock_request, exc)

        assert response.status_code == 500
        content = eval(response.body.decode())
        assert content["error"]["code"] == "INTERNAL_SERVER_ERROR"

    @pytest.mark.asyncio
    async def test_unknown_status_code_fallback(self, mock_request):
        """Test unknown status code uses HTTP_ERROR."""
        exc = StarletteHTTPException(status_code=418, detail="I'm a teapot")
        response = await http_exception_handler(mock_request, exc)

        content = eval(response.body.decode())
        assert content["error"]["code"] == "HTTP_ERROR"

    @pytest.mark.asyncio
    async def test_logs_http_exceptions(self, mock_request, caplog):
        """Test HTTP exceptions are logged."""
        with caplog.at_level(logging.WARNING):
            exc = StarletteHTTPException(status_code=404)
            await http_exception_handler(mock_request, exc)

        assert "HTTP 404" in caplog.text


# ============================================================================
# TEST: validation_exception_handler
# ============================================================================


class TestValidationExceptionHandler:
    """Test handler for FastAPI validation errors."""

    @pytest.mark.asyncio
    async def test_formats_validation_errors(self, mock_request):
        """Test validation errors are formatted correctly."""
        # Create mock validation error
        errors = [
            {
                "loc": ("body", "email"),
                "msg": "Invalid email format",
                "type": "value_error.email",
                "input": "not-an-email",
            }
        ]

        exc = MagicMock(spec=RequestValidationError)
        exc.errors.return_value = errors

        response = await validation_exception_handler(mock_request, exc)

        assert response.status_code == 422
        content = eval(response.body.decode())
        assert content["error"]["code"] == "VALIDATION_ERROR"

        validation_errors = content["error"]["details"]["validation_errors"]
        assert len(validation_errors) == 1
        assert validation_errors[0]["field"] == "body -> email"
        assert "Invalid email format" in validation_errors[0]["message"]

    @pytest.mark.asyncio
    async def test_handles_multiple_validation_errors(self, mock_request):
        """Test multiple validation errors in one request."""
        errors = [
            {
                "loc": ("body", "email"),
                "msg": "Invalid email",
                "type": "value_error.email",
                "input": "bad-email",
            },
            {
                "loc": ("body", "password"),
                "msg": "Too short",
                "type": "value_error.str.min_length",
                "input": "123",
            },
        ]

        exc = MagicMock(spec=RequestValidationError)
        exc.errors.return_value = errors

        response = await validation_exception_handler(mock_request, exc)

        content = eval(response.body.decode())
        validation_errors = content["error"]["details"]["validation_errors"]
        assert len(validation_errors) == 2

    @pytest.mark.asyncio
    async def test_nested_field_path_formatting(self, mock_request):
        """Test nested field paths are formatted correctly."""
        errors = [
            {
                "loc": ("body", "user", "profile", "age"),
                "msg": "Must be positive",
                "type": "value_error",
                "input": -5,
            }
        ]

        exc = MagicMock(spec=RequestValidationError)
        exc.errors.return_value = errors

        response = await validation_exception_handler(mock_request, exc)

        content = eval(response.body.decode())
        field_path = content["error"]["details"]["validation_errors"][0]["field"]
        assert field_path == "body -> user -> profile -> age"


# ============================================================================
# TEST: pydantic_validation_exception_handler
# ============================================================================


class TestPydanticValidationExceptionHandler:
    """Test handler for raw Pydantic validation errors."""

    @pytest.mark.asyncio
    async def test_handles_pydantic_errors(self, mock_request):
        """Test Pydantic ValidationError handling."""

        class TestModel(BaseModel):
            email: str
            age: int

        # Create validation error
        try:
            TestModel(email="invalid", age="not-a-number")
        except PydanticValidationError as exc:
            response = await pydantic_validation_exception_handler(mock_request, exc)

            assert response.status_code == 422
            content = eval(response.body.decode())
            assert content["error"]["code"] == "VALIDATION_ERROR"
            assert "validation_errors" in content["error"]["details"]

    @pytest.mark.asyncio
    async def test_formats_pydantic_errors(self, mock_request):
        """Test Pydantic errors are formatted correctly."""
        errors = [
            {"loc": ("email",), "msg": "Invalid email", "type": "value_error.email"}
        ]

        exc = MagicMock(spec=PydanticValidationError)
        exc.errors.return_value = errors

        response = await pydantic_validation_exception_handler(mock_request, exc)

        content = eval(response.body.decode())
        validation_errors = content["error"]["details"]["validation_errors"]
        assert validation_errors[0]["field"] == "email"


# ============================================================================
# TEST: generic_exception_handler
# ============================================================================


class TestGenericExceptionHandler:
    """Test catch-all exception handler."""

    @pytest.mark.asyncio
    async def test_handles_generic_exception(self, mock_request):
        """Test handling of unexpected exceptions."""
        exc = RuntimeError("Something went wrong")
        response = await generic_exception_handler(mock_request, exc)

        assert response.status_code == 500
        content = eval(response.body.decode())
        assert content["error"]["code"] == "INTERNAL_SERVER_ERROR"
        assert "unexpected error" in content["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_logs_full_traceback(self, mock_request, caplog):
        """Test full traceback is logged."""
        with caplog.at_level(logging.ERROR):
            exc = ValueError("Test error")
            await generic_exception_handler(mock_request, exc)

        assert "Unhandled exception" in caplog.text
        assert "ValueError" in caplog.text

    @pytest.mark.asyncio
    async def test_includes_exception_type_in_debug(self, mock_request):
        """Test exception type is included when DEBUG logging enabled."""
        with patch("backend.shared.error_handlers.logger") as mock_logger:
            mock_logger.isEnabledFor.return_value = True

            exc = TypeError("Type mismatch")
            response = await generic_exception_handler(mock_request, exc)

            content = eval(response.body.decode())
            assert content["error"]["details"]["exception_type"] == "TypeError"

    @pytest.mark.asyncio
    async def test_hides_exception_type_in_production(self, mock_request):
        """Test exception type is hidden in production."""
        with patch("backend.shared.error_handlers.logger") as mock_logger:
            mock_logger.isEnabledFor.return_value = False

            exc = TypeError("Type mismatch")
            response = await generic_exception_handler(mock_request, exc)

            content = eval(response.body.decode())
            assert content["error"]["details"] == {}


# ============================================================================
# TEST: register_error_handlers
# ============================================================================


class TestRegisterErrorHandlers:
    """Test error handler registration function."""

    def test_registers_all_handlers(self, fastapi_app):
        """Test all exception handlers are registered."""
        register_error_handlers(fastapi_app)

        # Verify handlers were added (FastAPI stores them in exception_handlers dict)
        assert len(fastapi_app.exception_handlers) >= 5

    def test_registers_vertice_exception_handler(self, fastapi_app):
        """Test VerticeException handler is registered."""
        register_error_handlers(fastapi_app)
        assert VerticeException in fastapi_app.exception_handlers

    def test_registers_http_exception_handler(self, fastapi_app):
        """Test HTTP exception handler is registered."""
        register_error_handlers(fastapi_app)
        assert StarletteHTTPException in fastapi_app.exception_handlers

    def test_registers_validation_handlers(self, fastapi_app):
        """Test validation exception handlers are registered."""
        register_error_handlers(fastapi_app)
        assert RequestValidationError in fastapi_app.exception_handlers
        assert PydanticValidationError in fastapi_app.exception_handlers

    def test_registers_generic_handler(self, fastapi_app):
        """Test generic Exception handler is registered."""
        register_error_handlers(fastapi_app)
        assert Exception in fastapi_app.exception_handlers

    def test_logs_successful_registration(self, fastapi_app, caplog):
        """Test successful registration is logged."""
        with caplog.at_level(logging.INFO):
            register_error_handlers(fastapi_app)

        assert "Error handlers registered successfully" in caplog.text


# ============================================================================
# TEST: request_id_middleware
# ============================================================================


class TestRequestIdMiddleware:
    """Test request ID injection middleware."""

    @pytest.mark.asyncio
    async def test_extracts_existing_request_id(self, mock_request_with_id):
        """Test middleware extracts existing request ID."""

        async def call_next(request):
            mock_response = MagicMock()
            mock_response.headers = {}
            return mock_response

        response = await request_id_middleware(mock_request_with_id, call_next)
        assert response.headers["X-Request-ID"] == "test-request-123"

    @pytest.mark.asyncio
    async def test_generates_new_request_id(self, mock_request):
        """Test middleware generates new ID if none exists."""

        async def call_next(request):
            mock_response = MagicMock()
            mock_response.headers = {}
            return mock_response

        response = await request_id_middleware(mock_request, call_next)
        request_id = response.headers["X-Request-ID"]

        # Validate UUID format
        uuid.UUID(request_id)

    @pytest.mark.asyncio
    async def test_adds_request_id_to_response_headers(self, mock_request):
        """Test request ID is added to response headers."""

        async def call_next(request):
            mock_response = MagicMock()
            mock_response.headers = {}
            return mock_response

        response = await request_id_middleware(mock_request, call_next)
        assert "X-Request-ID" in response.headers

    @pytest.mark.asyncio
    async def test_calls_next_middleware(self, mock_request):
        """Test middleware calls next in chain."""
        call_next_called = False

        async def call_next(request):
            nonlocal call_next_called
            call_next_called = True
            mock_response = MagicMock()
            mock_response.headers = {}
            return mock_response

        await request_id_middleware(mock_request, call_next)
        assert call_next_called


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestErrorHandlingIntegration:
    """Integration tests for full error handling flow."""

    def test_full_stack_vertice_exception(self, fastapi_app):
        """Test full stack with VerticeException."""
        from fastapi.testclient import TestClient

        register_error_handlers(fastapi_app)

        @fastapi_app.get("/test")
        async def test_endpoint():
            raise RecordNotFoundError("Test", "123")

        client = TestClient(fastapi_app)
        response = client.get("/test")

        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "RECORD_NOT_FOUND"
        assert "request_id" in data["error"]

    def test_full_stack_http_exception(self, fastapi_app):
        """Test full stack with HTTP exception."""
        from fastapi.testclient import TestClient

        register_error_handlers(fastapi_app)

        @fastapi_app.get("/test")
        async def test_endpoint():
            raise StarletteHTTPException(status_code=403, detail="Forbidden")

        client = TestClient(fastapi_app)
        response = client.get("/test")

        assert response.status_code == 403
        data = response.json()
        assert data["error"]["code"] == "FORBIDDEN"
