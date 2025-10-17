"""
Comprehensive tests for error_handlers.py
Targeting: 100% coverage (72 stmts, 8 branches)
"""
import uuid
from unittest.mock import Mock, patch

import pytest
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError
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
    DatabaseQueryError,
    RecordNotFoundError,
    VerticeException,
)

# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def mock_request():
    """Create mock FastAPI Request."""
    request = Mock(spec=Request)
    request.headers = {}
    request.url = Mock()
    request.url.path = "/api/v1/test"
    request.method = "GET"
    request.state = Mock()
    return request

@pytest.fixture
def app():
    """Create FastAPI app."""
    return FastAPI()

# ==============================================================================
# TEST: build_error_response
# ==============================================================================

def test_build_error_response_minimal():
    """Test build_error_response with minimal args."""
    response = build_error_response(
        error_code="TEST_ERROR",
        message="Test message",
        status_code=400
    )

    assert response["error"]["code"] == "TEST_ERROR"
    assert response["error"]["message"] == "Test message"
    assert response["error"]["status_code"] == 400
    assert response["error"]["details"] == {}
    assert "request_id" in response["error"]
    assert "timestamp" in response["error"]

def test_build_error_response_full():
    """Test build_error_response with all args."""
    request_id = str(uuid.uuid4())
    details = {"key": "value"}

    response = build_error_response(
        error_code="TEST_ERROR",
        message="Test message",
        status_code=500,
        details=details,
        request_id=request_id
    )

    assert response["error"]["code"] == "TEST_ERROR"
    assert response["error"]["message"] == "Test message"
    assert response["error"]["status_code"] == 500
    assert response["error"]["details"] == details
    assert response["error"]["request_id"] == request_id
    assert response["error"]["timestamp"].endswith("Z")

# ==============================================================================
# TEST: extract_request_id
# ==============================================================================

def test_extract_request_id_from_x_request_id(mock_request):
    """Test extracting request ID from X-Request-ID header."""
    request_id = str(uuid.uuid4())
    mock_request.headers = {"X-Request-ID": request_id}

    result = extract_request_id(mock_request)
    assert result == request_id

def test_extract_request_id_from_x_correlation_id(mock_request):
    """Test extracting request ID from X-Correlation-ID header."""
    request_id = str(uuid.uuid4())
    mock_request.headers = {"X-Correlation-ID": request_id}

    result = extract_request_id(mock_request)
    assert result == request_id

def test_extract_request_id_from_x_trace_id(mock_request):
    """Test extracting request ID from X-Trace-ID header."""
    request_id = str(uuid.uuid4())
    mock_request.headers = {"X-Trace-ID": request_id}

    result = extract_request_id(mock_request)
    assert result == request_id

def test_extract_request_id_generates_new(mock_request):
    """Test generating new request ID when none in headers."""
    result = extract_request_id(mock_request)

    assert result is not None
    # Should be valid UUID
    uuid.UUID(result)
    # Should store in request.state
    assert mock_request.state.request_id == result

def test_extract_request_id_priority(mock_request):
    """Test header priority: X-Request-ID > X-Correlation-ID > X-Trace-ID."""
    mock_request.headers = {
        "X-Request-ID": "id1",
        "X-Correlation-ID": "id2",
        "X-Trace-ID": "id3"
    }

    result = extract_request_id(mock_request)
    assert result == "id1"

# ==============================================================================
# TEST: vertice_exception_handler
# ==============================================================================

@pytest.mark.asyncio
async def test_vertice_exception_handler_client_error(mock_request):
    """Test handling VerticeException with 4xx status."""
    exc = RecordNotFoundError(resource_type="User", resource_id="123")

    with patch("backend.shared.error_handlers.logger") as mock_logger:
        response = await vertice_exception_handler(mock_request, exc)

        assert response.status_code == 404
        assert "error" in response.body.decode()
        mock_logger.warning.assert_called_once()
        mock_logger.error.assert_not_called()

@pytest.mark.asyncio
async def test_vertice_exception_handler_server_error(mock_request):
    """Test handling VerticeException with 5xx status."""
    exc = DatabaseQueryError(message="Query failed", details={"query": "SELECT * FROM users"})

    with patch("backend.shared.error_handlers.logger") as mock_logger:
        response = await vertice_exception_handler(mock_request, exc)

        assert response.status_code == 500
        mock_logger.error.assert_called_once()
        mock_logger.warning.assert_not_called()

# ==============================================================================
# TEST: http_exception_handler
# ==============================================================================

@pytest.mark.asyncio
async def test_http_exception_handler_404(mock_request):
    """Test handling 404 HTTP exception."""
    exc = StarletteHTTPException(status_code=404, detail="Resource not found")

    with patch("backend.shared.error_handlers.logger") as mock_logger:
        response = await http_exception_handler(mock_request, exc)

        assert response.status_code == 404
        body = response.body.decode()
        assert "NOT_FOUND" in body
        assert "Resource not found" in body
        mock_logger.warning.assert_called_once()

@pytest.mark.asyncio
async def test_http_exception_handler_500(mock_request):
    """Test handling 500 HTTP exception."""
    exc = StarletteHTTPException(status_code=500, detail="Internal error")

    response = await http_exception_handler(mock_request, exc)
    assert response.status_code == 500
    body = response.body.decode()
    assert "INTERNAL_SERVER_ERROR" in body

@pytest.mark.asyncio
async def test_http_exception_handler_unknown_status(mock_request):
    """Test handling HTTP exception with unmapped status code."""
    exc = StarletteHTTPException(status_code=418, detail="I'm a teapot")

    response = await http_exception_handler(mock_request, exc)
    assert response.status_code == 418
    body = response.body.decode()
    assert "HTTP_ERROR" in body

# ==============================================================================
# TEST: validation_exception_handler
# ==============================================================================

@pytest.mark.asyncio
async def test_validation_exception_handler(mock_request):
    """Test handling RequestValidationError."""
    from pydantic import BaseModel, Field

    class TestModel(BaseModel):
        name: str = Field(..., min_length=3)
        age: int = Field(..., gt=0)

    try:
        TestModel(name="ab", age=-1)
    except PydanticValidationError as e:
        # Convert to RequestValidationError
        exc = RequestValidationError(errors=e.errors())

        with patch("backend.shared.error_handlers.logger") as mock_logger:
            response = await validation_exception_handler(mock_request, exc)

            assert response.status_code == 422
            body = response.body.decode()
            assert "VALIDATION_ERROR" in body
            assert "validation_errors" in body
            mock_logger.warning.assert_called_once()

# ==============================================================================
# TEST: pydantic_validation_exception_handler
# ==============================================================================

@pytest.mark.asyncio
async def test_pydantic_validation_exception_handler(mock_request):
    """Test handling raw PydanticValidationError."""
    from pydantic import BaseModel, Field

    class TestModel(BaseModel):
        email: str = Field(..., pattern=r".+@.+\..+")
        count: int = Field(..., ge=1, le=100)

    try:
        TestModel(email="invalid", count=200)
    except PydanticValidationError as exc:
        with patch("backend.shared.error_handlers.logger") as mock_logger:
            response = await pydantic_validation_exception_handler(mock_request, exc)

            assert response.status_code == 422
            body = response.body.decode()
            assert "VALIDATION_ERROR" in body
            assert "validation_errors" in body
            mock_logger.warning.assert_called_once()

# ==============================================================================
# TEST: generic_exception_handler
# ==============================================================================

@pytest.mark.asyncio
async def test_generic_exception_handler(mock_request):
    """Test handling unexpected exception."""
    exc = ValueError("Something went wrong")

    with patch("backend.shared.error_handlers.logger") as mock_logger:
        with patch("backend.shared.error_handlers.traceback.print_exc"):
            response = await generic_exception_handler(mock_request, exc)

            assert response.status_code == 500
            body = response.body.decode()
            assert "INTERNAL_SERVER_ERROR" in body
            assert "unexpected error occurred" in body
            mock_logger.error.assert_called_once()

@pytest.mark.asyncio
async def test_generic_exception_handler_debug_mode(mock_request):
    """Test generic handler in debug mode (includes exception type)."""
    exc = RuntimeError("Debug test")

    with patch("backend.shared.error_handlers.logger") as mock_logger:
        mock_logger.isEnabledFor.return_value = True
        with patch("backend.shared.error_handlers.traceback.print_exc"):
            response = await generic_exception_handler(mock_request, exc)

            body = response.body.decode()
            assert "RuntimeError" in body

# ==============================================================================
# TEST: register_error_handlers
# ==============================================================================

def test_register_error_handlers(app):
    """Test registering all error handlers."""
    with patch.object(app, "add_exception_handler") as mock_add:
        with patch("backend.shared.error_handlers.logger") as mock_logger:
            register_error_handlers(app)

            # Should register 5 handlers
            assert mock_add.call_count == 5
            mock_logger.info.assert_called_once_with("Error handlers registered successfully")

def test_register_error_handlers_handlers_called(app):
    """Test that register_error_handlers actually adds handlers."""
    register_error_handlers(app)

    # Verify handlers are in app's exception_handlers
    assert VerticeException in app.exception_handlers
    assert StarletteHTTPException in app.exception_handlers
    assert RequestValidationError in app.exception_handlers
    assert PydanticValidationError in app.exception_handlers
    assert Exception in app.exception_handlers

# ==============================================================================
# TEST: request_id_middleware
# ==============================================================================

@pytest.mark.asyncio
async def test_request_id_middleware_existing_id(mock_request):
    """Test middleware with existing request ID."""
    request_id = str(uuid.uuid4())
    mock_request.headers = {"X-Request-ID": request_id}

    mock_response = Mock()
    mock_response.headers = {}

    async def mock_call_next(req):
        return mock_response

    response = await request_id_middleware(mock_request, mock_call_next)

    assert response.headers["X-Request-ID"] == request_id

@pytest.mark.asyncio
async def test_request_id_middleware_generates_id(mock_request):
    """Test middleware generates new request ID."""
    mock_response = Mock()
    mock_response.headers = {}

    async def mock_call_next(req):
        return mock_response

    response = await request_id_middleware(mock_request, mock_call_next)

    assert "X-Request-ID" in response.headers
    # Should be valid UUID
    uuid.UUID(response.headers["X-Request-ID"])

# ==============================================================================
# TEST: __all__
# ==============================================================================

def test_module_exports():
    """Test module __all__ exports."""
    from backend.shared import error_handlers

    assert "register_error_handlers" in error_handlers.__all__
    assert "request_id_middleware" in error_handlers.__all__
    assert "build_error_response" in error_handlers.__all__
    assert "vertice_exception_handler" in error_handlers.__all__
    assert "http_exception_handler" in error_handlers.__all__
    assert "validation_exception_handler" in error_handlers.__all__
    assert "generic_exception_handler" in error_handlers.__all__
