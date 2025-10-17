"""Tests for backend/shared/error_handlers.py - 100% coverage.

Strategy: Test FastAPI error handler functions and registration.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.shared.error_handlers import (
    build_error_response,
    extract_request_id,
    vertice_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    pydantic_validation_exception_handler,
    generic_exception_handler,
    register_error_handlers,
    request_id_middleware,
)
from backend.shared.exceptions import (
    VerticeException,
    ValidationError as VerticeValidationError,
    UnauthorizedError,
)


class TestBuildErrorResponse:
    """Test build_error_response function."""

    def test_build_error_response_basic(self):
        """build_error_response creates standardized dict."""
        response = build_error_response(
            error_code="TEST_ERROR",
            message="Test error message",
            status_code=400
        )
        
        assert "error" in response
        assert response["error"]["code"] == "TEST_ERROR"
        assert response["error"]["message"] == "Test error message"
        assert response["error"]["status_code"] == 400
        assert "request_id" in response["error"]
        assert "timestamp" in response["error"]

    def test_build_error_response_with_details(self):
        """build_error_response includes details."""
        details = {"field": "email", "value": "invalid"}
        response = build_error_response(
            error_code="VALIDATION",
            message="Invalid input",
            status_code=400,
            details=details
        )
        
        assert response["error"]["details"] == details

    def test_build_error_response_with_request_id(self):
        """build_error_response uses provided request_id."""
        response = build_error_response(
            error_code="ERROR",
            message="Error",
            status_code=500,
            request_id="custom-req-id"
        )
        
        assert response["error"]["request_id"] == "custom-req-id"

    def test_build_error_response_generates_request_id(self):
        """build_error_response generates UUID if no request_id."""
        response = build_error_response(
            error_code="ERROR",
            message="Error",
            status_code=500
        )
        
        request_id = response["error"]["request_id"]
        assert isinstance(request_id, str)
        assert len(request_id) > 0
        # Should be UUID format
        assert "-" in request_id

    def test_build_error_response_timestamp_format(self):
        """build_error_response includes ISO timestamp with Z."""
        response = build_error_response(
            error_code="ERROR",
            message="Error",
            status_code=500
        )
        
        timestamp = response["error"]["timestamp"]
        assert timestamp.endswith("Z")
        assert "T" in timestamp


class TestExtractRequestId:
    """Test extract_request_id function."""

    def test_extract_request_id_from_header(self):
        """extract_request_id gets ID from X-Request-ID header."""
        mock_request = Mock(spec=Request)
        mock_request.headers = {"X-Request-ID": "req-123"}
        mock_request.state = Mock()
        
        request_id = extract_request_id(mock_request)
        assert request_id == "req-123"

    def test_extract_request_id_from_correlation_id(self):
        """extract_request_id tries X-Correlation-ID header."""
        mock_request = Mock(spec=Request)
        mock_request.headers = {"X-Correlation-ID": "corr-456"}
        mock_request.state = Mock()
        
        request_id = extract_request_id(mock_request)
        assert request_id == "corr-456"

    def test_extract_request_id_from_trace_id(self):
        """extract_request_id tries X-Trace-ID header."""
        mock_request = Mock(spec=Request)
        mock_request.headers = {"X-Trace-ID": "trace-789"}
        mock_request.state = Mock()
        
        request_id = extract_request_id(mock_request)
        assert request_id == "trace-789"

    def test_extract_request_id_generates_new(self):
        """extract_request_id generates UUID if no header."""
        mock_request = Mock(spec=Request)
        mock_request.headers = {}
        mock_request.state = Mock()
        
        request_id = extract_request_id(mock_request)
        assert isinstance(request_id, str)
        assert len(request_id) > 0
        assert mock_request.state.request_id == request_id


@pytest.mark.asyncio
class TestVerticeExceptionHandler:
    """Test vertice_exception_handler function."""

    async def test_vertice_exception_handler_client_error(self):
        """vertice_exception_handler handles 4xx errors."""
        mock_request = Mock(spec=Request)
        mock_request.headers = {"X-Request-ID": "test-req"}
        mock_request.url = Mock(path="/test")
        mock_request.method = "GET"
        mock_request.state = Mock()
        
        exc = VerticeValidationError("Invalid input", details={"field": "email"})
        
        response = await vertice_exception_handler(mock_request, exc)
        
        assert response.status_code == 400
        assert "error" in response.body.decode()

    async def test_vertice_exception_handler_server_error(self):
        """vertice_exception_handler handles 5xx errors with logging."""
        mock_request = Mock(spec=Request)
        mock_request.headers = {}
        mock_request.url = Mock(path="/api/test")
        mock_request.method = "POST"
        mock_request.state = Mock()
        
        exc = VerticeException("Server error", status_code=500)
        
        with patch("backend.shared.error_handlers.logger") as mock_logger:
            response = await vertice_exception_handler(mock_request, exc)
            
            assert response.status_code == 500
            # Should log as error for 5xx
            mock_logger.error.assert_called_once()


@pytest.mark.asyncio
class TestHttpExceptionHandler:
    """Test http_exception_handler function."""

    async def test_http_exception_handler_404(self):
        """http_exception_handler handles 404 errors."""
        mock_request = Mock(spec=Request)
        mock_request.headers = {}
        mock_request.url = Mock(path="/not/found")
        mock_request.method = "GET"
        mock_request.state = Mock()
        
        exc = StarletteHTTPException(status_code=404, detail="Not found")
        
        response = await http_exception_handler(mock_request, exc)
        
        assert response.status_code == 404
        body = response.body.decode()
        assert "error" in body
        assert "Not found" in body


@pytest.mark.asyncio
class TestValidationExceptionHandlers:
    """Test validation exception handlers."""

    async def test_validation_exception_handler(self):
        """validation_exception_handler handles RequestValidationError."""
        mock_request = Mock(spec=Request)
        mock_request.headers = {}
        mock_request.url = Mock(path="/api/test")
        mock_request.method = "POST"
        mock_request.state = Mock()
        
        # Mock validation error
        exc = Mock(spec=RequestValidationError)
        exc.errors = Mock(return_value=[
            {"loc": ("body", "email"), "msg": "Invalid email", "type": "value_error"}
        ])
        
        response = await validation_exception_handler(mock_request, exc)
        
        assert response.status_code == 422

    async def test_pydantic_validation_exception_handler(self):
        """pydantic_validation_exception_handler handles Pydantic errors."""
        mock_request = Mock(spec=Request)
        mock_request.headers = {}
        mock_request.url = Mock(path="/api/test")
        mock_request.method = "POST"
        mock_request.state = Mock()
        
        # Mock Pydantic validation error
        exc = Mock(spec=PydanticValidationError)
        exc.errors = Mock(return_value=[
            {"loc": ("field1",), "msg": "Field required", "type": "value_error.missing"}
        ])
        
        response = await pydantic_validation_exception_handler(mock_request, exc)
        
        assert response.status_code == 422
        body = response.body.decode()
        assert "VALIDATION_ERROR" in body


@pytest.mark.asyncio
class TestGenericExceptionHandler:
    """Test generic_exception_handler function."""

    async def test_generic_exception_handler(self):
        """generic_exception_handler handles unexpected exceptions."""
        mock_request = Mock(spec=Request)
        mock_request.headers = {}
        mock_request.url = Mock(path="/api/crash")
        mock_request.method = "GET"
        mock_request.state = Mock()
        
        exc = Exception("Unexpected error")
        
        with patch("backend.shared.error_handlers.logger") as mock_logger:
            response = await generic_exception_handler(mock_request, exc)
            
            assert response.status_code == 500
            # Should log error (not critical)
            mock_logger.error.assert_called_once()
            
            body = response.body.decode()
            assert "INTERNAL_SERVER_ERROR" in body


class TestRegisterErrorHandlers:
    """Test register_error_handlers function."""

    def test_register_error_handlers(self):
        """register_error_handlers adds all exception handlers to app."""
        app = FastAPI()
        
        register_error_handlers(app)
        
        # Verify handlers were registered
        assert len(app.exception_handlers) > 0
        
        # Check for specific exception types
        assert VerticeException in app.exception_handlers
        assert Exception in app.exception_handlers

    def test_register_error_handlers_middleware(self):
        """register_error_handlers registers exception handlers."""
        app = FastAPI()
        initial_handler_count = len(app.exception_handlers)
        
        register_error_handlers(app)
        
        # Should have added multiple exception handlers
        assert len(app.exception_handlers) > initial_handler_count
        assert len(app.exception_handlers) >= 5  # VerticeException, HTTP, Validation, etc.


@pytest.mark.asyncio
class TestRequestIdMiddleware:
    """Test request_id_middleware function."""

    async def test_request_id_middleware_adds_header(self):
        """request_id_middleware adds X-Request-ID to response."""
        mock_request = Mock(spec=Request)
        mock_request.headers = {}
        mock_request.state = Mock()
        
        mock_response = Mock()
        mock_response.headers = {}
        
        async def mock_call_next(request):
            return mock_response
        
        response = await request_id_middleware(mock_request, mock_call_next)
        
        assert "X-Request-ID" in response.headers

    async def test_request_id_middleware_preserves_existing_id(self):
        """request_id_middleware preserves existing request ID."""
        mock_request = Mock(spec=Request)
        mock_request.headers = {"X-Request-ID": "existing-id"}
        mock_request.state = Mock()
        
        mock_response = Mock()
        mock_response.headers = {}
        
        async def mock_call_next(request):
            return mock_response
        
        response = await request_id_middleware(mock_request, mock_call_next)
        
        assert response.headers["X-Request-ID"] == "existing-id"


class TestErrorHandlerIntegration:
    """Integration tests for error handlers."""

    def test_error_response_format_consistency(self):
        """All error responses follow same format."""
        response1 = build_error_response("ERR1", "Message 1", 400)
        response2 = build_error_response("ERR2", "Message 2", 500)
        
        # Both should have same structure
        assert set(response1.keys()) == set(response2.keys())
        assert set(response1["error"].keys()) == set(response2["error"].keys())

    @pytest.mark.asyncio
    async def test_different_exception_types_handled(self):
        """Different exception types produce appropriate responses."""
        mock_request = Mock(spec=Request)
        mock_request.headers = {}
        mock_request.url = Mock(path="/test")
        mock_request.method = "GET"
        mock_request.state = Mock()
        
        # Test VerticeException
        exc1 = UnauthorizedError("Not authenticated")
        resp1 = await vertice_exception_handler(mock_request, exc1)
        assert resp1.status_code == 401
        
        # Test HTTPException
        exc2 = StarletteHTTPException(status_code=403, detail="Forbidden")
        resp2 = await http_exception_handler(mock_request, exc2)
        assert resp2.status_code == 403
