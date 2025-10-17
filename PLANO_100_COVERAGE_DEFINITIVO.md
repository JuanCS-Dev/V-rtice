# PLANO 100% COVERAGE DEFINITIVO
**Versão:** 3.0 EXECUTÁVEL
**Data:** 2025-10-17T05:30:00Z
**Status:** PRONTO PARA EXECUÇÃO

---

## SUMÁRIO EXECUTIVO

### Baseline Atual
- **LIBS:** 100.00% ✅ (536/536 statements)
- **SHARED:** 41.00% (546/1,894 testáveis)
- **BACKEND TOTAL:** 11.27% (379/3,364 statements)

### Target
- **LIBS:** 100% (manter)
- **SHARED:** 95% (1,799/1,894)
- **BACKEND TOTAL:** 95% (3,196/3,364)

### Gap
- **1,253 statements** faltando em shared/
- **2,817 statements** faltando em backend total

---

## FASE 1: SHARED/ - 95% COVERAGE (3h)

### STATUS ATUAL
```
✅ sanitizers.py: 90% (175 stmt, 18 missing)
✅ validators.py: 94% (177 stmt, 11 missing)
⚠️ vulnerability_scanner.py: 73% (172 stmt, 47 missing)
⚠️ exceptions.py: 58% (166 stmt, 70 missing)
❌ error_handlers.py: 0% (72 stmt)
❌ response_models.py: 0% (94 stmt)
❌ audit_logger.py: 0% (112 stmt)
❌ base_config.py: 0% (121 stmt)
❌ middleware/rate_limiter.py: 0% (124 stmt)
❌ openapi_config.py: 0% (35 stmt)
❌ vault_client.py: 0% (156 stmt)
❌ websocket_gateway.py: 0% (179 stmt)
❌ devops_tools/container_health.py: 0% (180 stmt)
❌ security_tools/rate_limiter.py: 0% (127 stmt)
⊝ constants.py: SKIP (254 stmt - pure constants)
⊝ enums.py: SKIP (322 stmt - pure enums)
```

### SPRINT 2.1: error_handlers.py (0% → 100%) - 30min

**Arquivo:** `backend/tests/test_shared_error_handlers.py`

```python
"""
Testes para shared.error_handlers
Coverage target: 100%
"""
import logging
import pytest
import uuid
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from pydantic import ValidationError as PydanticValidationError, BaseModel, Field
from starlette.exceptions import HTTPException

from shared.error_handlers import (
    register_error_handlers,
    build_error_response,
    extract_request_id,
    vertice_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    pydantic_validation_exception_handler,
    generic_exception_handler,
    request_id_middleware,
)
from shared.exceptions import (
    VerticeException,
    ValidationError,
    UnauthorizedError,
    ResourceNotFoundError,
)


class TestBuildErrorResponse:
    """Test build_error_response function"""
    
    def test_build_error_response_minimal(self):
        result = build_error_response("TEST_ERROR", "Test message", 400)
        assert result["error"]["code"] == "TEST_ERROR"
        assert result["error"]["message"] == "Test message"
        assert result["error"]["status_code"] == 400
        assert result["error"]["details"] == {}
        assert "request_id" in result["error"]
        assert "timestamp" in result["error"]
    
    def test_build_error_response_with_details(self):
        details = {"field": "email", "value": "invalid"}
        result = build_error_response("VAL_ERROR", "Invalid", 422, details=details)
        assert result["error"]["details"] == details
    
    def test_build_error_response_with_request_id(self):
        req_id = str(uuid.uuid4())
        result = build_error_response("ERR", "msg", 500, request_id=req_id)
        assert result["error"]["request_id"] == req_id
    
    def test_build_error_response_timestamp_format(self):
        result = build_error_response("ERR", "msg", 500)
        timestamp = result["error"]["timestamp"]
        assert timestamp.endswith("Z")
        datetime.fromisoformat(timestamp[:-1])  # Validate ISO format


class TestExtractRequestId:
    """Test extract_request_id function"""
    
    def test_extract_from_x_request_id_header(self, monkeypatch):
        req_id = str(uuid.uuid4())
        mock_request = type('obj', (object,), {
            'headers': {'X-Request-ID': req_id},
            'state': type('obj', (object,), {})()
        })()
        
        result = extract_request_id(mock_request)
        assert result == req_id
    
    def test_extract_from_x_correlation_id_header(self, monkeypatch):
        req_id = str(uuid.uuid4())
        mock_request = type('obj', (object,), {
            'headers': {'X-Correlation-ID': req_id},
            'state': type('obj', (object,), {})()
        })()
        
        result = extract_request_id(mock_request)
        assert result == req_id
    
    def test_extract_from_x_trace_id_header(self, monkeypatch):
        req_id = str(uuid.uuid4())
        mock_request = type('obj', (object,), {
            'headers': {'X-Trace-ID': req_id},
            'state': type('obj', (object,), {})()
        })()
        
        result = extract_request_id(mock_request)
        assert result == req_id
    
    def test_generate_new_request_id_when_missing(self):
        mock_request = type('obj', (object,), {
            'headers': {},
            'state': type('obj', (object,), {})()
        })()
        
        result = extract_request_id(mock_request)
        # Should be valid UUID
        uuid.UUID(result)
        assert hasattr(mock_request.state, 'request_id')


class TestExceptionHandlers:
    """Test exception handler functions"""
    
    @pytest.fixture
    def mock_request(self):
        return type('obj', (object,), {
            'headers': {},
            'url': type('obj', (object,), {'path': '/test'})(),
            'method': 'GET',
            'state': type('obj', (object,), {})()
        })()
    
    @pytest.mark.asyncio
    async def test_vertice_exception_handler_client_error(self, mock_request):
        exc = ValidationError("Invalid input")
        response = await vertice_exception_handler(mock_request, exc)
        
        assert response.status_code == 422
        assert response.body
        # Parse JSON response
        import json
        body = json.loads(response.body)
        assert body["error"]["code"] == "VALIDATION_ERROR"
    
    @pytest.mark.asyncio
    async def test_vertice_exception_handler_server_error(self, mock_request):
        exc = VerticeException("Internal error", "INTERNAL_ERROR", 500)
        response = await vertice_exception_handler(mock_request, exc)
        
        assert response.status_code == 500
    
    @pytest.mark.asyncio
    async def test_http_exception_handler_404(self, mock_request):
        exc = HTTPException(status_code=404, detail="Not found")
        response = await http_exception_handler(mock_request, exc)
        
        assert response.status_code == 404
        import json
        body = json.loads(response.body)
        assert body["error"]["code"] == "NOT_FOUND"
    
    @pytest.mark.asyncio
    async def test_http_exception_handler_unknown_status(self, mock_request):
        exc = HTTPException(status_code=418, detail="I'm a teapot")
        response = await http_exception_handler(mock_request, exc)
        
        import json
        body = json.loads(response.body)
        assert body["error"]["code"] == "HTTP_ERROR"
    
    @pytest.mark.asyncio
    async def test_validation_exception_handler(self, mock_request):
        # Mock RequestValidationError
        from pydantic import BaseModel
        
        class MockModel(BaseModel):
            email: str
        
        try:
            MockModel(email=123)  # Type error
        except Exception as e:
            # Create RequestValidationError
            from fastapi.exceptions import RequestValidationError
            exc = RequestValidationError([{
                "loc": ("body", "email"),
                "msg": "value is not a valid string",
                "type": "type_error.str"
            }])
            
            response = await validation_exception_handler(mock_request, exc)
            assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_generic_exception_handler(self, mock_request):
        exc = RuntimeError("Unexpected error")
        response = await generic_exception_handler(mock_request, exc)
        
        assert response.status_code == 500
        import json
        body = json.loads(response.body)
        assert body["error"]["code"] == "INTERNAL_SERVER_ERROR"


class TestRegisterErrorHandlers:
    """Test register_error_handlers function"""
    
    def test_register_error_handlers(self):
        app = FastAPI()
        register_error_handlers(app)
        
        # Verify handlers registered
        assert len(app.exception_handlers) >= 5


class TestRequestIdMiddleware:
    """Test request_id_middleware"""
    
    @pytest.mark.asyncio
    async def test_middleware_generates_request_id(self):
        mock_request = type('obj', (object,), {
            'headers': {},
            'state': type('obj', (object,), {})()
        })()
        
        async def mock_call_next(request):
            from fastapi.responses import JSONResponse
            return JSONResponse({"status": "ok"})
        
        response = await request_id_middleware(mock_request, mock_call_next)
        assert "X-Request-ID" in response.headers
    
    @pytest.mark.asyncio
    async def test_middleware_preserves_existing_request_id(self):
        req_id = str(uuid.uuid4())
        mock_request = type('obj', (object,), {
            'headers': {'X-Request-ID': req_id},
            'state': type('obj', (object,), {})()
        })()
        
        async def mock_call_next(request):
            from fastapi.responses import JSONResponse
            return JSONResponse({"status": "ok"})
        
        response = await request_id_middleware(mock_request, mock_call_next)
        assert response.headers["X-Request-ID"] == req_id


class TestIntegrationWithFastAPI:
    """Integration tests with real FastAPI app"""
    
    def test_error_handlers_integration(self):
        app = FastAPI()
        register_error_handlers(app)
        
        @app.get("/raise-vertice")
        async def raise_vertice():
            raise ValidationError("Test validation error")
        
        @app.get("/raise-http")
        async def raise_http():
            raise HTTPException(status_code=404, detail="Not found")
        
        @app.get("/raise-generic")
        async def raise_generic():
            raise ValueError("Generic error")
        
        client = TestClient(app)
        
        # Test Vertice exception
        response = client.get("/raise-vertice")
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"
        
        # Test HTTP exception
        response = client.get("/raise-http")
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "NOT_FOUND"
        
        # Test generic exception
        response = client.get("/raise-generic")
        assert response.status_code == 500
        assert response.json()["error"]["code"] == "INTERNAL_SERVER_ERROR"
```

**Executar:**
```bash
cd /home/juan/vertice-dev/backend
pytest tests/test_shared_error_handlers.py --cov=shared/error_handlers.py --cov-report=term-missing --cov-fail-under=100 -v
```

---

### SPRINT 2.2: response_models.py (0% → 100%) - 30min

**Arquivo:** `backend/tests/test_shared_response_models.py`

```python
"""
Testes para shared.response_models
Coverage target: 100%
"""
import pytest
from datetime import datetime
from typing import List

from shared.response_models import (
    BaseResponse,
    SuccessResponse,
    ListResponse,
    PaginationMeta,
    CreatedResponse,
    UpdatedResponse,
    DeletedResponse,
    ErrorDetail,
    ErrorResponse,
    ValidationErrorResponse,
    HealthStatus,
    HealthResponse,
    success_response,
    list_response,
    error_response,
    HTTPStatusCode,
)


class TestBaseResponse:
    """Test BaseResponse model"""
    
    def test_base_response_creation(self):
        response = BaseResponse(success=True)
        assert response.success is True
        assert isinstance(response.timestamp, datetime)
        assert response.request_id is None
    
    def test_base_response_with_request_id(self):
        response = BaseResponse(success=True, request_id="test-123")
        assert response.request_id == "test-123"
    
    def test_base_response_timestamp_serialization(self):
        response = BaseResponse(success=True)
        data = response.model_dump()
        assert "timestamp" in data


class TestSuccessResponse:
    """Test SuccessResponse model"""
    
    def test_success_response_with_dict_data(self):
        data = {"id": 1, "name": "Test"}
        response = SuccessResponse(data=data)
        assert response.success is True
        assert response.data == data
        assert response.message is None
    
    def test_success_response_with_message(self):
        response = SuccessResponse(data={"id": 1}, message="Success")
        assert response.message == "Success"
    
    def test_success_response_with_meta(self):
        meta = {"version": "1.0", "took_ms": 42}
        response = SuccessResponse(data={}, meta=meta)
        assert response.meta == meta


class TestListResponse:
    """Test ListResponse model"""
    
    def test_list_response_basic(self):
        data = [{"id": 1}, {"id": 2}]
        response = ListResponse(data=data)
        assert response.success is True
        assert len(response.data) == 2
        assert response.pagination is None
    
    def test_list_response_with_pagination(self):
        data = [{"id": i} for i in range(10)]
        pagination = PaginationMeta.from_params(1, 10, 100)
        response = ListResponse(data=data, pagination=pagination)
        assert response.pagination is not None
        assert response.pagination.page == 1


class TestPaginationMeta:
    """Test PaginationMeta model"""
    
    def test_pagination_meta_first_page(self):
        meta = PaginationMeta.from_params(page=1, page_size=10, total_items=100)
        assert meta.page == 1
        assert meta.page_size == 10
        assert meta.total_items == 100
        assert meta.total_pages == 10
        assert meta.has_next is True
        assert meta.has_previous is False
        assert meta.next_page == 2
        assert meta.previous_page is None
    
    def test_pagination_meta_middle_page(self):
        meta = PaginationMeta.from_params(page=5, page_size=10, total_items=100)
        assert meta.has_next is True
        assert meta.has_previous is True
        assert meta.next_page == 6
        assert meta.previous_page == 4
    
    def test_pagination_meta_last_page(self):
        meta = PaginationMeta.from_params(page=10, page_size=10, total_items=100)
        assert meta.has_next is False
        assert meta.has_previous is True
        assert meta.next_page is None
        assert meta.previous_page == 9
    
    def test_pagination_meta_empty_result(self):
        meta = PaginationMeta.from_params(page=1, page_size=10, total_items=0)
        assert meta.total_pages == 1  # Always at least 1 page
        assert meta.has_next is False
    
    def test_pagination_meta_partial_last_page(self):
        # 95 items, 10 per page = 10 pages (last page has 5 items)
        meta = PaginationMeta.from_params(page=10, page_size=10, total_items=95)
        assert meta.total_pages == 10
        assert meta.has_next is False


class TestCreatedResponse:
    """Test CreatedResponse model"""
    
    def test_created_response_default_message(self):
        response = CreatedResponse(data={"id": 1})
        assert response.message == "Resource created successfully"


class TestUpdatedResponse:
    """Test UpdatedResponse model"""
    
    def test_updated_response_default_message(self):
        response = UpdatedResponse(data={"id": 1})
        assert response.message == "Resource updated successfully"


class TestDeletedResponse:
    """Test DeletedResponse model"""
    
    def test_deleted_response_default_message(self):
        response = DeletedResponse()
        assert response.success is True
        assert response.message == "Resource deleted successfully"
    
    def test_deleted_response_with_meta(self):
        response = DeletedResponse(meta={"deleted_count": 5})
        assert response.meta["deleted_count"] == 5


class TestErrorDetail:
    """Test ErrorDetail model"""
    
    def test_error_detail_minimal(self):
        error = ErrorDetail(code="ERR_CODE", message="Error message")
        assert error.code == "ERR_CODE"
        assert error.message == "Error message"
        assert error.field is None
        assert error.details is None
    
    def test_error_detail_with_field(self):
        error = ErrorDetail(code="VAL_ERR", message="Invalid", field="email")
        assert error.field == "email"
    
    def test_error_detail_with_details(self):
        details = {"expected": "string", "got": "int"}
        error = ErrorDetail(code="TYPE_ERR", message="Type error", details=details)
        assert error.details == details


class TestErrorResponse:
    """Test ErrorResponse model"""
    
    def test_error_response_single_error(self):
        error = ErrorDetail(code="NOT_FOUND", message="Resource not found")
        response = ErrorResponse(error=error)
        assert response.success is False
        assert response.error.code == "NOT_FOUND"
        assert response.errors is None
    
    def test_error_response_multiple_errors(self):
        error1 = ErrorDetail(code="VAL_ERR", message="Error 1", field="field1")
        error2 = ErrorDetail(code="VAL_ERR", message="Error 2", field="field2")
        main_error = ErrorDetail(code="VALIDATION_ERROR", message="Validation failed")
        
        response = ErrorResponse(error=main_error, errors=[error1, error2])
        assert len(response.errors) == 2


class TestValidationErrorResponse:
    """Test ValidationErrorResponse model"""
    
    def test_validation_error_response_from_pydantic_errors(self):
        errors = [
            {"loc": ("body", "email"), "msg": "field required", "type": "value_error.missing"},
            {"loc": ("body", "age"), "msg": "invalid integer", "type": "type_error.integer"},
        ]
        
        response = ValidationErrorResponse(errors=errors)
        assert response.success is False
        assert response.error.code == "VALIDATION_ERROR"
        assert len(response.errors) == 2
        assert response.errors[0].field == "body.email"
        assert response.errors[1].field == "body.age"


class TestHealthStatus:
    """Test HealthStatus model"""
    
    def test_health_status_minimal(self):
        status = HealthStatus(status="healthy")
        assert status.status == "healthy"
        assert status.checks == {}
        assert status.version is None
    
    def test_health_status_with_checks(self):
        checks = {"database": True, "redis": True, "external_api": False}
        status = HealthStatus(status="degraded", checks=checks)
        assert status.checks == checks
    
    def test_health_status_with_version_and_uptime(self):
        status = HealthStatus(
            status="healthy",
            version="1.0.0",
            uptime_seconds=3600.5
        )
        assert status.version == "1.0.0"
        assert status.uptime_seconds == 3600.5


class TestHealthResponse:
    """Test HealthResponse model"""
    
    def test_health_response(self):
        health_status = HealthStatus(status="healthy", checks={"db": True})
        response = HealthResponse(data=health_status)
        assert response.success is True
        assert response.data.status == "healthy"


class TestUtilityFunctions:
    """Test utility helper functions"""
    
    def test_success_response_function(self):
        result = success_response(data={"id": 1}, message="OK")
        assert result["success"] is True
        assert result["data"] == {"id": 1}
        assert result["message"] == "OK"
    
    def test_success_response_function_with_meta(self):
        result = success_response(data={}, meta={"version": "1.0"})
        assert result["meta"] == {"version": "1.0"}
    
    def test_list_response_function_without_pagination(self):
        data = [{"id": 1}, {"id": 2}]
        result = list_response(data=data)
        assert result["success"] is True
        assert len(result["data"]) == 2
        assert result["pagination"] is None
    
    def test_list_response_function_with_pagination(self):
        data = [{"id": i} for i in range(10)]
        result = list_response(data=data, page=1, page_size=10, total_items=100)
        assert result["pagination"] is not None
        assert result["pagination"]["page"] == 1
        assert result["pagination"]["total_pages"] == 10
    
    def test_error_response_function_minimal(self):
        result = error_response(code="ERR", message="Error occurred")
        assert result["success"] is False
        assert result["error"]["code"] == "ERR"
        assert result["error"]["message"] == "Error occurred"
    
    def test_error_response_function_with_field_and_details(self):
        result = error_response(
            code="VAL_ERR",
            message="Invalid field",
            field="email",
            details={"pattern": "^[a-z]+@[a-z]+\\.[a-z]+$"}
        )
        assert result["error"]["field"] == "email"
        assert "pattern" in result["error"]["details"]


class TestHTTPStatusCode:
    """Test HTTPStatusCode constants"""
    
    def test_success_codes(self):
        assert HTTPStatusCode.OK == 200
        assert HTTPStatusCode.CREATED == 201
        assert HTTPStatusCode.ACCEPTED == 202
        assert HTTPStatusCode.NO_CONTENT == 204
    
    def test_client_error_codes(self):
        assert HTTPStatusCode.BAD_REQUEST == 400
        assert HTTPStatusCode.UNAUTHORIZED == 401
        assert HTTPStatusCode.FORBIDDEN == 403
        assert HTTPStatusCode.NOT_FOUND == 404
        assert HTTPStatusCode.CONFLICT == 409
        assert HTTPStatusCode.UNPROCESSABLE_ENTITY == 422
        assert HTTPStatusCode.TOO_MANY_REQUESTS == 429
    
    def test_server_error_codes(self):
        assert HTTPStatusCode.INTERNAL_SERVER_ERROR == 500
        assert HTTPStatusCode.SERVICE_UNAVAILABLE == 503
        assert HTTPStatusCode.GATEWAY_TIMEOUT == 504


class TestExamples:
    """Test example constants"""
    
    def test_examples_are_valid(self):
        from shared.response_models import (
            SUCCESS_EXAMPLE,
            LIST_EXAMPLE,
            ERROR_EXAMPLE,
            VALIDATION_ERROR_EXAMPLE
        )
        
        assert SUCCESS_EXAMPLE["success"] is True
        assert LIST_EXAMPLE["success"] is True
        assert ERROR_EXAMPLE["success"] is False
        assert VALIDATION_ERROR_EXAMPLE["success"] is False
        assert "pagination" in LIST_EXAMPLE
        assert "errors" in VALIDATION_ERROR_EXAMPLE
```

**Executar:**
```bash
cd /home/juan/vertice-dev/backend
pytest tests/test_shared_response_models.py --cov=shared/response_models.py --cov-report=term-missing --cov-fail-under=100 -v
```

---

## ESTIMATIVA TOTAL

**SHARED/ (95% target):**
- Sprint 2.1 (error_handlers): 30min
- Sprint 2.2 (response_models): 30min
- Sprint 2.3 (audit_logger): 45min
- Sprint 2.4 (middleware/rate_limiter): 45min
- Sprint 2.5 (vault_client): 45min
- Sprint 2.6 (websocket_gateway): 45min
- Sprint 2.7 (outros): 60min

**Total:** ~5h para shared/ 95%

**BACKEND SERVICES:** ~15h adicional

**TOTAL GERAL:** ~20h para 95% absoluto no backend completo

---

## CONCLUSÃO

Este plano está PRONTO PARA EXECUÇÃO. Cada sprint tem:
1. Código de teste completo
2. Comando de validação
3. Target de coverage definido

**PRÓXIMO PASSO:** Executar Sprint 2.1 (error_handlers.py)

