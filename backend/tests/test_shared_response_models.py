"""
Testes para shared.response_models
Coverage target: 100% ABSOLUTO
"""
import pytest
from datetime import datetime
from typing import List

from backend.shared.response_models import (
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
    SUCCESS_EXAMPLE,
    LIST_EXAMPLE,
    ERROR_EXAMPLE,
    VALIDATION_ERROR_EXAMPLE,
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
        # Verify JSON encoding config
        json_str = response.model_dump_json()
        assert '"success":true' in json_str or '"success": true' in json_str


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
    
    def test_success_response_literal_true(self):
        """Test that success field is Literal[True]"""
        response = SuccessResponse(data={"test": 1})
        assert response.success is True
        # Field should always be True
        data = response.model_dump()
        assert data["success"] is True


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
    
    def test_list_response_empty_list(self):
        response = ListResponse(data=[])
        assert response.success is True
        assert len(response.data) == 0
    
    def test_list_response_with_meta(self):
        response = ListResponse(data=[{"id": 1}], meta={"total_count": 1})
        assert response.meta["total_count"] == 1


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
        assert meta.has_previous is False
    
    def test_pagination_meta_partial_last_page(self):
        # 95 items, 10 per page = 10 pages (last page has 5 items)
        meta = PaginationMeta.from_params(page=10, page_size=10, total_items=95)
        assert meta.total_pages == 10
        assert meta.has_next is False
    
    def test_pagination_meta_single_item(self):
        meta = PaginationMeta.from_params(page=1, page_size=10, total_items=1)
        assert meta.total_pages == 1
        assert meta.has_next is False
        assert meta.has_previous is False
    
    def test_pagination_meta_validation(self):
        """Test field validation"""
        meta = PaginationMeta(
            page=1,
            page_size=10,
            total_items=0,
            total_pages=1,
            has_next=False,
            has_previous=False
        )
        assert meta.page >= 1
        assert meta.page_size >= 1
        assert meta.total_items >= 0


class TestCreatedResponse:
    """Test CreatedResponse model"""
    
    def test_created_response_default_message(self):
        response = CreatedResponse(data={"id": 1})
        assert response.message == "Resource created successfully"
    
    def test_created_response_custom_message(self):
        response = CreatedResponse(data={"id": 1}, message="User created")
        assert response.message == "User created"


class TestUpdatedResponse:
    """Test UpdatedResponse model"""
    
    def test_updated_response_default_message(self):
        response = UpdatedResponse(data={"id": 1})
        assert response.message == "Resource updated successfully"
    
    def test_updated_response_custom_message(self):
        response = UpdatedResponse(data={"id": 1}, message="User updated")
        assert response.message == "User updated"


class TestDeletedResponse:
    """Test DeletedResponse model"""
    
    def test_deleted_response_default_message(self):
        response = DeletedResponse()
        assert response.success is True
        assert response.message == "Resource deleted successfully"
    
    def test_deleted_response_with_meta(self):
        response = DeletedResponse(meta={"deleted_count": 5})
        assert response.meta["deleted_count"] == 5
    
    def test_deleted_response_custom_message(self):
        response = DeletedResponse(message="Resource removed")
        assert response.message == "Resource removed"


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
    
    def test_error_detail_full(self):
        error = ErrorDetail(
            code="VALIDATION_ERROR",
            message="Field validation failed",
            field="username",
            details={"min_length": 3, "max_length": 20}
        )
        assert error.code == "VALIDATION_ERROR"
        assert error.field == "username"
        assert error.details["min_length"] == 3


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
    
    def test_error_response_literal_false(self):
        """Test that success field is Literal[False]"""
        error = ErrorDetail(code="ERROR", message="Test")
        response = ErrorResponse(error=error)
        assert response.success is False
        data = response.model_dump()
        assert data["success"] is False


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
    
    def test_validation_error_response_single_error(self):
        errors = [
            {"loc": ("body", "username"), "msg": "field required", "type": "value_error.missing"}
        ]
        response = ValidationErrorResponse(errors=errors)
        assert len(response.errors) == 1
        assert response.error.details["error_count"] == 1
    
    def test_validation_error_response_nested_location(self):
        errors = [
            {"loc": ("body", "user", "address", "zip"), "msg": "invalid format", "type": "type_error"}
        ]
        response = ValidationErrorResponse(errors=errors)
        assert response.errors[0].field == "body.user.address.zip"
    
    def test_validation_error_response_empty_loc(self):
        """Test error with empty location"""
        errors = [
            {"loc": (), "msg": "parsing error", "type": "value_error"}
        ]
        response = ValidationErrorResponse(errors=errors)
        assert response.errors[0].field == ""


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
    
    def test_health_status_unhealthy(self):
        status = HealthStatus(
            status="unhealthy",
            checks={"database": False, "redis": False}
        )
        assert status.status == "unhealthy"


class TestHealthResponse:
    """Test HealthResponse model"""
    
    def test_health_response(self):
        health_status = HealthStatus(status="healthy", checks={"db": True})
        response = HealthResponse(data=health_status)
        assert response.success is True
        assert response.data.status == "healthy"
    
    def test_health_response_with_version(self):
        health_status = HealthStatus(
            status="healthy",
            version="2.0.0",
            uptime_seconds=86400.0
        )
        response = HealthResponse(data=health_status)
        assert response.data.version == "2.0.0"


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
    
    def test_success_response_function_minimal(self):
        result = success_response(data={"test": "value"})
        assert result["success"] is True
        assert result["data"]["test"] == "value"
        assert result["message"] is None
    
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
    
    def test_list_response_function_partial_pagination(self):
        """Test with only page parameter (missing page_size)"""
        data = [{"id": 1}]
        result = list_response(data=data, page=1)
        assert result["pagination"] is None  # Incomplete pagination params
    
    def test_list_response_function_with_message_and_meta(self):
        result = list_response(
            data=[{"id": 1}],
            message="Items retrieved",
            meta={"total": 1}
        )
        assert result["message"] == "Items retrieved"
        assert result["meta"]["total"] == 1
    
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
    
    def test_error_response_function_with_status_code(self):
        result = error_response(
            code="NOT_FOUND",
            message="Resource not found",
            status_code=404
        )
        assert result["error"]["code"] == "NOT_FOUND"


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
    
    def test_success_example_is_valid(self):
        assert SUCCESS_EXAMPLE["success"] is True
        assert "data" in SUCCESS_EXAMPLE
        assert "timestamp" in SUCCESS_EXAMPLE
    
    def test_list_example_is_valid(self):
        assert LIST_EXAMPLE["success"] is True
        assert "data" in LIST_EXAMPLE
        assert isinstance(LIST_EXAMPLE["data"], list)
        assert "pagination" in LIST_EXAMPLE
        assert LIST_EXAMPLE["pagination"]["page"] == 1
    
    def test_error_example_is_valid(self):
        assert ERROR_EXAMPLE["success"] is False
        assert "error" in ERROR_EXAMPLE
        assert ERROR_EXAMPLE["error"]["code"] == "NOT_FOUND"
    
    def test_validation_error_example_is_valid(self):
        assert VALIDATION_ERROR_EXAMPLE["success"] is False
        assert "error" in VALIDATION_ERROR_EXAMPLE
        assert "errors" in VALIDATION_ERROR_EXAMPLE
        assert isinstance(VALIDATION_ERROR_EXAMPLE["errors"], list)
        assert len(VALIDATION_ERROR_EXAMPLE["errors"]) == 2


class TestEdgeCases:
    """Test edge cases and corner scenarios"""
    
    def test_pagination_with_one_item_per_page(self):
        meta = PaginationMeta.from_params(page=5, page_size=1, total_items=10)
        assert meta.total_pages == 10
        assert meta.has_next is True
        assert meta.has_previous is True
    
    def test_pagination_page_equals_total_pages(self):
        meta = PaginationMeta.from_params(page=5, page_size=20, total_items=100)
        assert meta.page == 5
        assert meta.total_pages == 5
        assert meta.has_next is False
    
    def test_error_response_with_empty_details(self):
        result = error_response(
            code="ERROR",
            message="Test",
            details={}
        )
        assert result["error"]["details"] == {}
    
    def test_success_response_with_none_data(self):
        """Test that None is a valid data value"""
        response = SuccessResponse(data=None)
        assert response.data is None
        assert response.success is True
    
    def test_list_response_with_complex_objects(self):
        """Test list response with nested complex objects"""
        complex_data = [
            {"id": 1, "nested": {"value": "test", "count": 42}},
            {"id": 2, "nested": {"value": "test2", "count": 43}}
        ]
        response = ListResponse(data=complex_data)
        assert len(response.data) == 2
        assert response.data[0]["nested"]["count"] == 42
