"""
100% Coverage Tests for response_models.py
=========================================

Tests ALL classes, functions, edge cases and branches.
Production-grade only.
"""

from datetime import datetime
from typing import Any

import pytest
from pydantic import ValidationError
from shared.response_models import (
    ERROR_EXAMPLE,
    LIST_EXAMPLE,
    SUCCESS_EXAMPLE,
    VALIDATION_ERROR_EXAMPLE,
    BaseResponse,
    CreatedResponse,
    DeletedResponse,
    ErrorDetail,
    ErrorResponse,
    HealthResponse,
    HealthStatus,
    HTTPStatusCode,
    ListResponse,
    PaginationMeta,
    SuccessResponse,
    UpdatedResponse,
    ValidationErrorResponse,
    error_response,
    list_response,
    success_response,
)


class TestBaseResponse:
    """Test BaseResponse model."""

    def test_base_response_success_true(self):
        """Test base response with success=True."""
        response = BaseResponse(success=True)
        assert response.success is True
        assert isinstance(response.timestamp, datetime)
        assert response.request_id is None

    def test_base_response_success_false(self):
        """Test base response with success=False."""
        response = BaseResponse(success=False)
        assert response.success is False

    def test_base_response_with_request_id(self):
        """Test base response with request_id."""
        response = BaseResponse(success=True, request_id="req_123")
        assert response.request_id == "req_123"

    def test_base_response_timestamp_serialization(self):
        """Test timestamp JSON serialization."""
        response = BaseResponse(success=True)
        data = response.model_dump()
        assert "timestamp" in data

    def test_base_response_json_encoder(self):
        """Test datetime JSON encoder."""
        response = BaseResponse(success=True)
        json_data = response.model_dump_json()
        assert "timestamp" in json_data
        assert "Z" in json_data  # UTC timezone marker


class TestSuccessResponse:
    """Test SuccessResponse model."""

    def test_success_response_basic(self):
        """Test basic success response."""
        response = SuccessResponse(data={"key": "value"})
        assert response.success is True
        assert response.data == {"key": "value"}
        assert response.message is None
        assert response.meta is None

    def test_success_response_with_message(self):
        """Test success response with message."""
        response = SuccessResponse(data={}, message="Operation successful")
        assert response.message == "Operation successful"

    def test_success_response_with_meta(self):
        """Test success response with metadata."""
        meta = {"version": "1.0", "processing_time": 0.5}
        response = SuccessResponse(data={}, meta=meta)
        assert response.meta == meta

    def test_success_response_typed_data(self):
        """Test success response with typed data."""
        data = {"id": 1, "name": "Test"}
        response = SuccessResponse[dict[str, Any]](data=data)
        assert response.data == data

    def test_success_response_list_data(self):
        """Test success response with list data."""
        data = [1, 2, 3]
        response = SuccessResponse(data=data)
        assert response.data == data

    def test_success_response_none_data(self):
        """Test success response with None data."""
        response = SuccessResponse(data=None)
        assert response.data is None

    def test_success_response_complex_data(self):
        """Test success response with complex nested data."""
        data = {
            "users": [{"id": 1}, {"id": 2}],
            "meta": {"count": 2},
        }
        response = SuccessResponse(data=data)
        assert response.data == data


class TestListResponse:
    """Test ListResponse model."""

    def test_list_response_basic(self):
        """Test basic list response."""
        data = [{"id": 1}, {"id": 2}]
        response = ListResponse(data=data)
        assert response.success is True
        assert response.data == data
        assert response.pagination is None

    def test_list_response_with_pagination(self):
        """Test list response with pagination."""
        data = [{"id": 1}]
        pagination = PaginationMeta(
            page=1,
            page_size=10,
            total_items=1,
            total_pages=1,
            has_next=False,
            has_previous=False,
        )
        response = ListResponse(data=data, pagination=pagination)
        assert response.pagination == pagination

    def test_list_response_empty_list(self):
        """Test list response with empty list."""
        response = ListResponse(data=[])
        assert response.data == []

    def test_list_response_with_message_and_meta(self):
        """Test list response with message and meta."""
        response = ListResponse(
            data=[1, 2],
            message="Items retrieved",
            meta={"total": 2},
        )
        assert response.message == "Items retrieved"
        assert response.meta == {"total": 2}


class TestPaginationMeta:
    """Test PaginationMeta model."""

    def test_pagination_meta_basic(self):
        """Test basic pagination metadata."""
        pagination = PaginationMeta(
            page=1,
            page_size=10,
            total_items=100,
            total_pages=10,
            has_next=True,
            has_previous=False,
        )
        assert pagination.page == 1
        assert pagination.page_size == 10
        assert pagination.total_items == 100
        assert pagination.total_pages == 10
        assert pagination.has_next is True
        assert pagination.has_previous is False

    def test_pagination_meta_with_next_page(self):
        """Test pagination with next_page."""
        pagination = PaginationMeta(
            page=1,
            page_size=10,
            total_items=20,
            total_pages=2,
            has_next=True,
            has_previous=False,
            next_page=2,
        )
        assert pagination.next_page == 2

    def test_pagination_meta_with_previous_page(self):
        """Test pagination with previous_page."""
        pagination = PaginationMeta(
            page=2,
            page_size=10,
            total_items=20,
            total_pages=2,
            has_next=False,
            has_previous=True,
            previous_page=1,
        )
        assert pagination.previous_page == 1

    def test_pagination_meta_from_params_first_page(self):
        """Test from_params for first page."""
        pagination = PaginationMeta.from_params(
            page=1, page_size=10, total_items=25
        )
        assert pagination.page == 1
        assert pagination.page_size == 10
        assert pagination.total_items == 25
        assert pagination.total_pages == 3
        assert pagination.has_next is True
        assert pagination.has_previous is False
        assert pagination.next_page == 2
        assert pagination.previous_page is None

    def test_pagination_meta_from_params_middle_page(self):
        """Test from_params for middle page."""
        pagination = PaginationMeta.from_params(
            page=2, page_size=10, total_items=30
        )
        assert pagination.page == 2
        assert pagination.has_next is True
        assert pagination.has_previous is True
        assert pagination.next_page == 3
        assert pagination.previous_page == 1

    def test_pagination_meta_from_params_last_page(self):
        """Test from_params for last page."""
        pagination = PaginationMeta.from_params(
            page=3, page_size=10, total_items=25
        )
        assert pagination.page == 3
        assert pagination.total_pages == 3
        assert pagination.has_next is False
        assert pagination.has_previous is True
        assert pagination.next_page is None
        assert pagination.previous_page == 2

    def test_pagination_meta_from_params_zero_items(self):
        """Test from_params with zero items."""
        pagination = PaginationMeta.from_params(
            page=1, page_size=10, total_items=0
        )
        assert pagination.total_pages == 1
        assert pagination.has_next is False
        assert pagination.has_previous is False

    def test_pagination_meta_from_params_exact_page_size(self):
        """Test from_params when total matches page_size exactly."""
        pagination = PaginationMeta.from_params(
            page=1, page_size=10, total_items=10
        )
        assert pagination.total_pages == 1
        assert pagination.has_next is False

    def test_pagination_meta_from_params_large_dataset(self):
        """Test from_params with large dataset."""
        pagination = PaginationMeta.from_params(
            page=50, page_size=100, total_items=10000
        )
        assert pagination.total_pages == 100
        assert pagination.has_next is True
        assert pagination.has_previous is True

    def test_pagination_meta_validation_page_min(self):
        """Test page validation (minimum 1)."""
        with pytest.raises(ValidationError):
            PaginationMeta(
                page=0,
                page_size=10,
                total_items=10,
                total_pages=1,
                has_next=False,
                has_previous=False,
            )

    def test_pagination_meta_validation_page_size_min(self):
        """Test page_size validation (minimum 1)."""
        with pytest.raises(ValidationError):
            PaginationMeta(
                page=1,
                page_size=0,
                total_items=10,
                total_pages=1,
                has_next=False,
                has_previous=False,
            )

    def test_pagination_meta_validation_total_items_min(self):
        """Test total_items validation (minimum 0)."""
        with pytest.raises(ValidationError):
            PaginationMeta(
                page=1,
                page_size=10,
                total_items=-1,
                total_pages=1,
                has_next=False,
                has_previous=False,
            )


class TestCreatedResponse:
    """Test CreatedResponse model."""

    def test_created_response_default_message(self):
        """Test created response with default message."""
        response = CreatedResponse(data={"id": 1})
        assert response.message == "Resource created successfully"
        assert response.success is True

    def test_created_response_custom_message(self):
        """Test created response with custom message."""
        response = CreatedResponse(data={"id": 1}, message="User created")
        assert response.message == "User created"


class TestUpdatedResponse:
    """Test UpdatedResponse model."""

    def test_updated_response_default_message(self):
        """Test updated response with default message."""
        response = UpdatedResponse(data={"id": 1})
        assert response.message == "Resource updated successfully"
        assert response.success is True

    def test_updated_response_custom_message(self):
        """Test updated response with custom message."""
        response = UpdatedResponse(data={"id": 1}, message="User updated")
        assert response.message == "User updated"


class TestDeletedResponse:
    """Test DeletedResponse model."""

    def test_deleted_response_default_message(self):
        """Test deleted response with default message."""
        response = DeletedResponse()
        assert response.message == "Resource deleted successfully"
        assert response.success is True
        assert response.meta is None

    def test_deleted_response_custom_message(self):
        """Test deleted response with custom message."""
        response = DeletedResponse(message="User deleted")
        assert response.message == "User deleted"

    def test_deleted_response_with_meta(self):
        """Test deleted response with metadata."""
        response = DeletedResponse(meta={"deleted_id": 123})
        assert response.meta == {"deleted_id": 123}


class TestErrorDetail:
    """Test ErrorDetail model."""

    def test_error_detail_basic(self):
        """Test basic error detail."""
        error = ErrorDetail(code="NOT_FOUND", message="Resource not found")
        assert error.code == "NOT_FOUND"
        assert error.message == "Resource not found"
        assert error.field is None
        assert error.details is None

    def test_error_detail_with_field(self):
        """Test error detail with field."""
        error = ErrorDetail(
            code="VALIDATION_ERROR",
            message="Invalid email",
            field="email",
        )
        assert error.field == "email"

    def test_error_detail_with_details(self):
        """Test error detail with additional details."""
        error = ErrorDetail(
            code="SERVER_ERROR",
            message="Internal error",
            details={"trace_id": "xyz", "severity": "high"},
        )
        assert error.details == {"trace_id": "xyz", "severity": "high"}


class TestErrorResponse:
    """Test ErrorResponse model."""

    def test_error_response_basic(self):
        """Test basic error response."""
        error_detail = ErrorDetail(code="ERROR", message="Something failed")
        response = ErrorResponse(error=error_detail)
        assert response.success is False
        assert response.error == error_detail
        assert response.errors is None

    def test_error_response_with_multiple_errors(self):
        """Test error response with multiple errors."""
        error1 = ErrorDetail(code="ERR1", message="Error 1")
        error2 = ErrorDetail(code="ERR2", message="Error 2")
        response = ErrorResponse(error=error1, errors=[error2])
        assert len(response.errors) == 1
        assert response.errors[0] == error2


class TestValidationErrorResponse:
    """Test ValidationErrorResponse model."""

    def test_validation_error_response_single_error(self):
        """Test validation error with single error."""
        errors = [
            {"msg": "field required", "loc": ["email"], "type": "value_error.missing"}
        ]
        response = ValidationErrorResponse(errors=errors)
        assert response.success is False
        assert response.error.code == "VALIDATION_ERROR"
        assert response.error.message == "Request validation failed"
        assert len(response.errors) == 1
        assert response.errors[0].field == "email"

    def test_validation_error_response_multiple_errors(self):
        """Test validation error with multiple errors."""
        errors = [
            {"msg": "field required", "loc": ["email"], "type": "value_error.missing"},
            {"msg": "invalid integer", "loc": ["age"], "type": "type_error.integer"},
        ]
        response = ValidationErrorResponse(errors=errors)
        assert len(response.errors) == 2
        assert response.error.details["error_count"] == 2

    def test_validation_error_response_nested_field(self):
        """Test validation error with nested field path."""
        errors = [
            {
                "msg": "invalid",
                "loc": ["user", "profile", "email"],
                "type": "value_error",
            }
        ]
        response = ValidationErrorResponse(errors=errors)
        assert response.errors[0].field == "user.profile.email"

    def test_validation_error_response_empty_loc(self):
        """Test validation error with empty location."""
        errors = [{"msg": "validation failed", "loc": [], "type": "value_error"}]
        response = ValidationErrorResponse(errors=errors)
        assert response.errors[0].field == ""

    def test_validation_error_response_missing_msg(self):
        """Test validation error with missing msg field."""
        errors = [{"loc": ["field"], "type": "error"}]
        response = ValidationErrorResponse(errors=errors)
        assert response.errors[0].message == "Validation failed"

    def test_validation_error_response_with_kwargs(self):
        """Test validation error with additional kwargs."""
        errors = [{"msg": "error", "loc": ["field"], "type": "error"}]
        response = ValidationErrorResponse(errors=errors, request_id="req_123")
        assert response.request_id == "req_123"


class TestHealthStatus:
    """Test HealthStatus model."""

    def test_health_status_basic(self):
        """Test basic health status."""
        status = HealthStatus(status="healthy")
        assert status.status == "healthy"
        assert status.checks == {}
        assert status.version is None
        assert status.uptime_seconds is None

    def test_health_status_with_checks(self):
        """Test health status with checks."""
        checks = {"database": True, "redis": True, "api": False}
        status = HealthStatus(status="degraded", checks=checks)
        assert status.checks == checks

    def test_health_status_with_version(self):
        """Test health status with version."""
        status = HealthStatus(status="healthy", version="1.2.3")
        assert status.version == "1.2.3"

    def test_health_status_with_uptime(self):
        """Test health status with uptime."""
        status = HealthStatus(status="healthy", uptime_seconds=3600.5)
        assert status.uptime_seconds == 3600.5


class TestHealthResponse:
    """Test HealthResponse model."""

    def test_health_response_basic(self):
        """Test basic health response."""
        health_status = HealthStatus(status="healthy")
        response = HealthResponse(data=health_status)
        assert response.success is True
        assert response.data == health_status

    def test_health_response_unhealthy(self):
        """Test health response for unhealthy service."""
        health_status = HealthStatus(
            status="unhealthy",
            checks={"database": False},
        )
        response = HealthResponse(success=False, data=health_status)
        assert response.success is False


class TestUtilityFunctions:
    """Test utility functions."""

    def test_success_response_function_basic(self):
        """Test success_response helper function."""
        result = success_response(data={"key": "value"})
        assert result["success"] is True
        assert result["data"] == {"key": "value"}

    def test_success_response_function_with_message(self):
        """Test success_response with message."""
        result = success_response(data={}, message="Success")
        assert result["message"] == "Success"

    def test_success_response_function_with_meta(self):
        """Test success_response with meta."""
        result = success_response(data={}, meta={"version": "1.0"})
        assert result["meta"] == {"version": "1.0"}

    def test_list_response_function_basic(self):
        """Test list_response helper function."""
        result = list_response(data=[1, 2, 3])
        assert result["success"] is True
        assert result["data"] == [1, 2, 3]
        assert result["pagination"] is None

    def test_list_response_function_with_pagination(self):
        """Test list_response with pagination."""
        result = list_response(
            data=[1, 2],
            page=1,
            page_size=10,
            total_items=20,
        )
        assert result["pagination"]["page"] == 1
        assert result["pagination"]["total_pages"] == 2

    def test_list_response_function_partial_pagination(self):
        """Test list_response with incomplete pagination (should be None)."""
        result = list_response(data=[1, 2], page=1)
        assert result["pagination"] is None

    def test_list_response_function_with_message_meta(self):
        """Test list_response with message and meta."""
        result = list_response(
            data=[],
            message="No items",
            meta={"cached": True},
        )
        assert result["message"] == "No items"
        assert result["meta"] == {"cached": True}

    def test_error_response_function_basic(self):
        """Test error_response helper function."""
        result = error_response(code="ERROR", message="Failed")
        assert result["success"] is False
        assert result["error"]["code"] == "ERROR"
        assert result["error"]["message"] == "Failed"

    def test_error_response_function_with_status_code(self):
        """Test error_response with status_code."""
        result = error_response(code="NOT_FOUND", message="Not found", status_code=404)
        assert result["error"]["code"] == "NOT_FOUND"

    def test_error_response_function_with_field(self):
        """Test error_response with field."""
        result = error_response(
            code="VALIDATION",
            message="Invalid",
            field="email",
        )
        assert result["error"]["field"] == "email"

    def test_error_response_function_with_details(self):
        """Test error_response with details."""
        result = error_response(
            code="ERROR",
            message="Failed",
            details={"reason": "timeout"},
        )
        assert result["error"]["details"] == {"reason": "timeout"}


class TestHTTPStatusCode:
    """Test HTTPStatusCode constants."""

    def test_success_codes(self):
        """Test success status codes."""
        assert HTTPStatusCode.OK == 200
        assert HTTPStatusCode.CREATED == 201
        assert HTTPStatusCode.ACCEPTED == 202
        assert HTTPStatusCode.NO_CONTENT == 204

    def test_client_error_codes(self):
        """Test client error status codes."""
        assert HTTPStatusCode.BAD_REQUEST == 400
        assert HTTPStatusCode.UNAUTHORIZED == 401
        assert HTTPStatusCode.FORBIDDEN == 403
        assert HTTPStatusCode.NOT_FOUND == 404
        assert HTTPStatusCode.CONFLICT == 409
        assert HTTPStatusCode.UNPROCESSABLE_ENTITY == 422
        assert HTTPStatusCode.TOO_MANY_REQUESTS == 429

    def test_server_error_codes(self):
        """Test server error status codes."""
        assert HTTPStatusCode.INTERNAL_SERVER_ERROR == 500
        assert HTTPStatusCode.SERVICE_UNAVAILABLE == 503
        assert HTTPStatusCode.GATEWAY_TIMEOUT == 504


class TestExampleConstants:
    """Test example constants for OpenAPI docs."""

    def test_success_example_structure(self):
        """Test SUCCESS_EXAMPLE structure."""
        assert SUCCESS_EXAMPLE["success"] is True
        assert "data" in SUCCESS_EXAMPLE
        assert "timestamp" in SUCCESS_EXAMPLE

    def test_list_example_structure(self):
        """Test LIST_EXAMPLE structure."""
        assert LIST_EXAMPLE["success"] is True
        assert isinstance(LIST_EXAMPLE["data"], list)
        assert "pagination" in LIST_EXAMPLE

    def test_error_example_structure(self):
        """Test ERROR_EXAMPLE structure."""
        assert ERROR_EXAMPLE["success"] is False
        assert "error" in ERROR_EXAMPLE
        assert ERROR_EXAMPLE["error"]["code"] == "NOT_FOUND"

    def test_validation_error_example_structure(self) -> None:
        """Test VALIDATION_ERROR_EXAMPLE structure."""
        assert VALIDATION_ERROR_EXAMPLE["success"] is False
        assert "error" in VALIDATION_ERROR_EXAMPLE
        assert "errors" in VALIDATION_ERROR_EXAMPLE
        errors = VALIDATION_ERROR_EXAMPLE.get("errors", [])
        assert isinstance(errors, list)
        assert len(errors) == 2
