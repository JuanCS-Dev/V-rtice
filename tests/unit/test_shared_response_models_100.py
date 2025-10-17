"""
Test Suite: response_models.py - 100% ABSOLUTE Coverage
========================================================

Target: backend/shared/response_models.py
Estratégia: Testes exhaustivos de todos os modelos, funções helper e edge cases
Meta: 100% statements + 100% branches
"""

from datetime import datetime
from typing import Any

import pytest
from pydantic import ValidationError

from backend.shared.response_models import (
    ERROR_EXAMPLE,
    LIST_EXAMPLE,
    # Examples
    SUCCESS_EXAMPLE,
    VALIDATION_ERROR_EXAMPLE,
    # Base Models
    BaseResponse,
    CreatedResponse,
    DeletedResponse,
    # Error Models
    ErrorDetail,
    ErrorResponse,
    HealthResponse,
    # Health Models
    HealthStatus,
    # Constants
    HTTPStatusCode,
    ListResponse,
    PaginationMeta,
    # Success Models
    SuccessResponse,
    UpdatedResponse,
    ValidationErrorResponse,
    error_response,
    list_response,
    # Helper Functions
    success_response,
)

# ============================================================================
# BASE RESPONSE TESTS
# ============================================================================


class TestBaseResponse:
    """Test BaseResponse model."""

    def test_base_response_creation(self):
        """Test basic creation with required fields."""
        resp = BaseResponse(success=True)
        assert resp.success is True
        assert isinstance(resp.timestamp, datetime)
        assert resp.request_id is None

    def test_base_response_with_request_id(self):
        """Test with request_id."""
        resp = BaseResponse(success=False, request_id="req_123")
        assert resp.request_id == "req_123"

    def test_base_response_timestamp_serialization(self):
        """Test datetime serialization to ISO format."""
        resp = BaseResponse(success=True)
        data = resp.model_dump()
        assert "timestamp" in data
        # Pydantic handles serialization in model_dump_json()
        json_str = resp.model_dump_json()
        assert "Z" in json_str  # ISO format with Z


# ============================================================================
# SUCCESS RESPONSE TESTS
# ============================================================================


class TestSuccessResponse:
    """Test SuccessResponse model."""

    def test_success_response_basic(self):
        """Test basic success response."""
        resp = SuccessResponse(data={"id": 1, "name": "test"})
        assert resp.success is True
        assert resp.data == {"id": 1, "name": "test"}
        assert resp.message is None
        assert resp.meta is None

    def test_success_response_with_message(self):
        """Test with message."""
        resp = SuccessResponse(data=[1, 2, 3], message="Items retrieved")
        assert resp.message == "Items retrieved"

    def test_success_response_with_meta(self):
        """Test with metadata."""
        resp = SuccessResponse(
            data="test",
            meta={"processing_time_ms": 42, "version": "1.0"}
        )
        assert resp.meta["processing_time_ms"] == 42
        assert resp.meta["version"] == "1.0"

    def test_success_response_generic_types(self):
        """Test different data types."""
        # String
        resp1 = SuccessResponse[str](data="hello")
        assert resp1.data == "hello"

        # List
        resp2 = SuccessResponse[list[int]](data=[1, 2, 3])
        assert resp2.data == [1, 2, 3]

        # Dict
        resp3 = SuccessResponse[dict[str, Any]](data={"key": "value"})
        assert resp3.data == {"key": "value"}


class TestListResponse:
    """Test ListResponse model."""

    def test_list_response_basic(self):
        """Test basic list response."""
        resp = ListResponse(data=[1, 2, 3])
        assert resp.success is True
        assert resp.data == [1, 2, 3]
        assert resp.pagination is None

    def test_list_response_with_pagination(self):
        """Test with pagination metadata."""
        pagination = PaginationMeta.from_params(
            page=1, page_size=10, total_items=42
        )
        resp = ListResponse(data=[1, 2, 3], pagination=pagination)
        assert resp.pagination.page == 1
        assert resp.pagination.total_items == 42

    def test_list_response_empty(self):
        """Test empty list."""
        resp = ListResponse(data=[])
        assert resp.data == []


class TestPaginationMeta:
    """Test PaginationMeta model."""

    def test_pagination_first_page(self):
        """Test first page pagination."""
        meta = PaginationMeta.from_params(page=1, page_size=10, total_items=42)
        assert meta.page == 1
        assert meta.page_size == 10
        assert meta.total_items == 42
        assert meta.total_pages == 5
        assert meta.has_next is True
        assert meta.has_previous is False
        assert meta.next_page == 2
        assert meta.previous_page is None

    def test_pagination_middle_page(self):
        """Test middle page pagination."""
        meta = PaginationMeta.from_params(page=3, page_size=10, total_items=100)
        assert meta.page == 3
        assert meta.has_next is True
        assert meta.has_previous is True
        assert meta.next_page == 4
        assert meta.previous_page == 2

    def test_pagination_last_page(self):
        """Test last page pagination."""
        meta = PaginationMeta.from_params(page=5, page_size=10, total_items=42)
        assert meta.page == 5
        assert meta.has_next is False
        assert meta.has_previous is True
        assert meta.next_page is None
        assert meta.previous_page == 4

    def test_pagination_single_page(self):
        """Test single page (all items fit)."""
        meta = PaginationMeta.from_params(page=1, page_size=50, total_items=10)
        assert meta.total_pages == 1
        assert meta.has_next is False
        assert meta.has_previous is False

    def test_pagination_exact_multiple(self):
        """Test when total_items is exact multiple of page_size."""
        meta = PaginationMeta.from_params(page=2, page_size=10, total_items=20)
        assert meta.total_pages == 2
        assert meta.page == 2
        assert meta.has_next is False

    def test_pagination_zero_items(self):
        """Test with zero items."""
        meta = PaginationMeta.from_params(page=1, page_size=10, total_items=0)
        assert meta.total_pages == 1  # At least 1 page
        assert meta.total_items == 0
        assert meta.has_next is False

    def test_pagination_validation_constraints(self):
        """Test field validation."""
        with pytest.raises(ValidationError):
            PaginationMeta(
                page=0,  # Must be >= 1
                page_size=10,
                total_items=100,
                total_pages=10,
                has_next=True,
                has_previous=False,
            )


class TestCreatedResponse:
    """Test CreatedResponse model."""

    def test_created_response_default_message(self):
        """Test default success message."""
        resp = CreatedResponse(data={"id": 123})
        assert resp.message == "Resource created successfully"
        assert resp.data == {"id": 123}

    def test_created_response_custom_message(self):
        """Test custom message override."""
        resp = CreatedResponse(data={"id": 456}, message="User created")
        assert resp.message == "User created"


class TestUpdatedResponse:
    """Test UpdatedResponse model."""

    def test_updated_response_default_message(self):
        """Test default update message."""
        resp = UpdatedResponse(data={"id": 789})
        assert resp.message == "Resource updated successfully"

    def test_updated_response_with_meta(self):
        """Test with metadata."""
        resp = UpdatedResponse(
            data={"id": 789},
            meta={"fields_updated": ["name", "email"]}
        )
        assert resp.meta["fields_updated"] == ["name", "email"]


class TestDeletedResponse:
    """Test DeletedResponse model."""

    def test_deleted_response_default(self):
        """Test default deleted response."""
        resp = DeletedResponse()
        assert resp.success is True
        assert resp.message == "Resource deleted successfully"
        assert resp.meta is None

    def test_deleted_response_with_meta(self):
        """Test with metadata."""
        resp = DeletedResponse(meta={"deleted_count": 5})
        assert resp.meta["deleted_count"] == 5


# ============================================================================
# ERROR RESPONSE TESTS
# ============================================================================


class TestErrorDetail:
    """Test ErrorDetail model."""

    def test_error_detail_basic(self):
        """Test basic error detail."""
        err = ErrorDetail(code="NOT_FOUND", message="Resource not found")
        assert err.code == "NOT_FOUND"
        assert err.message == "Resource not found"
        assert err.field is None
        assert err.details is None

    def test_error_detail_with_field(self):
        """Test validation error with field."""
        err = ErrorDetail(
            code="VALIDATION_ERROR",
            message="Invalid email",
            field="email"
        )
        assert err.field == "email"

    def test_error_detail_with_details(self):
        """Test with additional details."""
        err = ErrorDetail(
            code="INTERNAL_ERROR",
            message="Database connection failed",
            details={"host": "db.example.com", "port": 5432}
        )
        assert err.details["host"] == "db.example.com"


class TestErrorResponse:
    """Test ErrorResponse model."""

    def test_error_response_basic(self):
        """Test basic error response."""
        resp = ErrorResponse(
            error=ErrorDetail(code="SERVER_ERROR", message="Internal error")
        )
        assert resp.success is False
        assert resp.error.code == "SERVER_ERROR"
        assert resp.errors is None

    def test_error_response_multiple_errors(self):
        """Test with multiple errors."""
        resp = ErrorResponse(
            error=ErrorDetail(code="VALIDATION_ERROR", message="Validation failed"),
            errors=[
                ErrorDetail(code="REQUIRED", message="Field required", field="name"),
                ErrorDetail(code="INVALID", message="Invalid format", field="email"),
            ]
        )
        assert len(resp.errors) == 2
        assert resp.errors[0].field == "name"
        assert resp.errors[1].field == "email"


class TestValidationErrorResponse:
    """Test ValidationErrorResponse model."""

    def test_validation_error_response_single_error(self):
        """Test with single validation error."""
        errors = [
            {
                "msg": "field required",
                "loc": ("body", "email"),
                "type": "value_error.missing"
            }
        ]
        resp = ValidationErrorResponse(errors=errors)
        assert resp.success is False
        assert resp.error.code == "VALIDATION_ERROR"
        assert resp.error.message == "Request validation failed"
        assert len(resp.errors) == 1
        assert resp.errors[0].field == "body.email"

    def test_validation_error_response_multiple_errors(self):
        """Test with multiple validation errors."""
        errors = [
            {"msg": "field required", "loc": ("name",), "type": "value_error.missing"},
            {"msg": "invalid email", "loc": ("email",), "type": "value_error.email"},
        ]
        resp = ValidationErrorResponse(errors=errors)
        assert len(resp.errors) == 2
        assert resp.error.details["error_count"] == 2

    def test_validation_error_response_nested_field(self):
        """Test nested field path."""
        errors = [
            {
                "msg": "invalid",
                "loc": ("body", "user", "address", "zip"),
                "type": "value_error"
            }
        ]
        resp = ValidationErrorResponse(errors=errors)
        assert resp.errors[0].field == "body.user.address.zip"

    def test_validation_error_response_empty_loc(self):
        """Test error without loc field."""
        errors = [
            {"msg": "validation failed", "type": "value_error"}
        ]
        resp = ValidationErrorResponse(errors=errors)
        assert resp.errors[0].field == ""  # Empty string from empty loc


# ============================================================================
# HEALTH RESPONSE TESTS
# ============================================================================


class TestHealthStatus:
    """Test HealthStatus model."""

    def test_health_status_basic(self):
        """Test basic health status."""
        status = HealthStatus(status="healthy")
        assert status.status == "healthy"
        assert status.checks == {}
        assert status.version is None

    def test_health_status_with_checks(self):
        """Test with health checks."""
        status = HealthStatus(
            status="healthy",
            checks={"database": True, "redis": True, "api": True}
        )
        assert status.checks["database"] is True

    def test_health_status_degraded(self):
        """Test degraded status."""
        status = HealthStatus(
            status="degraded",
            checks={"database": True, "redis": False},
            version="1.2.3",
            uptime_seconds=3600.5
        )
        assert status.status == "degraded"
        assert status.checks["redis"] is False
        assert status.uptime_seconds == 3600.5


class TestHealthResponse:
    """Test HealthResponse model."""

    def test_health_response(self):
        """Test health response."""
        health_status = HealthStatus(
            status="healthy",
            checks={"db": True},
            version="1.0.0"
        )
        resp = HealthResponse(data=health_status)
        assert resp.success is True
        assert resp.data.status == "healthy"


# ============================================================================
# HELPER FUNCTION TESTS
# ============================================================================


class TestHelperFunctions:
    """Test utility helper functions."""

    def test_success_response_helper_basic(self):
        """Test success_response() helper."""
        result = success_response(data={"id": 1})
        assert result["success"] is True
        assert result["data"] == {"id": 1}
        assert result["message"] is None

    def test_success_response_helper_with_message(self):
        """Test with message."""
        result = success_response(data="test", message="Success!")
        assert result["message"] == "Success!"

    def test_success_response_helper_with_meta(self):
        """Test with metadata."""
        result = success_response(
            data=[1, 2],
            meta={"count": 2}
        )
        assert result["meta"]["count"] == 2

    def test_list_response_helper_without_pagination(self):
        """Test list_response() without pagination."""
        result = list_response(data=[1, 2, 3])
        assert result["success"] is True
        assert result["data"] == [1, 2, 3]
        assert result["pagination"] is None

    def test_list_response_helper_with_pagination(self):
        """Test with pagination parameters."""
        result = list_response(
            data=[1, 2, 3],
            page=2,
            page_size=10,
            total_items=42
        )
        assert result["pagination"]["page"] == 2
        assert result["pagination"]["total_pages"] == 5

    def test_list_response_helper_partial_pagination(self):
        """Test with partial pagination params (should skip pagination)."""
        result = list_response(data=[1, 2], page=1, page_size=10)
        assert result["pagination"] is None  # total_items missing

    def test_list_response_helper_with_message(self):
        """Test with message."""
        result = list_response(data=[], message="No items found")
        assert result["message"] == "No items found"

    def test_error_response_helper_basic(self):
        """Test error_response() helper."""
        result = error_response(code="NOT_FOUND", message="Resource not found")
        assert result["success"] is False
        assert result["error"]["code"] == "NOT_FOUND"
        assert result["error"]["message"] == "Resource not found"

    def test_error_response_helper_with_field(self):
        """Test with field parameter."""
        result = error_response(
            code="INVALID",
            message="Invalid value",
            field="email"
        )
        assert result["error"]["field"] == "email"

    def test_error_response_helper_with_details(self):
        """Test with details."""
        result = error_response(
            code="DB_ERROR",
            message="Connection failed",
            details={"host": "localhost", "port": 5432}
        )
        assert result["error"]["details"]["host"] == "localhost"

    def test_error_response_helper_default_status_code(self):
        """Test default status_code parameter (not in response, just for docs)."""
        result = error_response(
            code="ERROR",
            message="Error",
            status_code=500  # This param exists but not in response dict
        )
        assert "status_code" not in result  # Not part of response model


# ============================================================================
# HTTP STATUS CODE TESTS
# ============================================================================


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


# ============================================================================
# EXAMPLE CONSTANTS TESTS
# ============================================================================


class TestExampleConstants:
    """Test example response constants."""

    def test_success_example_structure(self):
        """Test SUCCESS_EXAMPLE structure."""
        assert SUCCESS_EXAMPLE["success"] is True
        assert "data" in SUCCESS_EXAMPLE
        assert "timestamp" in SUCCESS_EXAMPLE
        assert SUCCESS_EXAMPLE["data"]["id"] == 123

    def test_list_example_structure(self):
        """Test LIST_EXAMPLE structure."""
        assert LIST_EXAMPLE["success"] is True
        assert isinstance(LIST_EXAMPLE["data"], list)
        assert "pagination" in LIST_EXAMPLE
        assert LIST_EXAMPLE["pagination"]["page"] == 1

    def test_error_example_structure(self):
        """Test ERROR_EXAMPLE structure."""
        assert ERROR_EXAMPLE["success"] is False
        assert "error" in ERROR_EXAMPLE
        assert ERROR_EXAMPLE["error"]["code"] == "NOT_FOUND"

    def test_validation_error_example_structure(self):
        """Test VALIDATION_ERROR_EXAMPLE structure."""
        assert VALIDATION_ERROR_EXAMPLE["success"] is False
        assert "errors" in VALIDATION_ERROR_EXAMPLE
        assert len(VALIDATION_ERROR_EXAMPLE["errors"]) == 2


# ============================================================================
# EDGE CASES & INTEGRATION TESTS
# ============================================================================


class TestEdgeCasesAndIntegration:
    """Test edge cases and model integration."""

    def test_response_serialization_consistency(self):
        """Test all models serialize consistently."""
        resp1 = SuccessResponse(data={"test": 1})
        resp2 = ErrorResponse(error=ErrorDetail(code="ERR", message="Error"))
        resp3 = ListResponse(data=[1, 2, 3])

        # All should have success and timestamp
        for resp in [resp1, resp2, resp3]:
            data = resp.model_dump()
            assert "success" in data
            assert "timestamp" in data

    def test_nested_generic_types(self):
        """Test complex nested generic types."""
        resp = SuccessResponse[dict[str, list[int]]](
            data={"numbers": [1, 2, 3], "more": [4, 5, 6]}
        )
        assert resp.data["numbers"] == [1, 2, 3]

    def test_pagination_edge_case_one_item(self):
        """Test pagination with just 1 item."""
        meta = PaginationMeta.from_params(page=1, page_size=10, total_items=1)
        assert meta.total_pages == 1
        assert meta.has_next is False

    def test_all_models_have_timestamps(self):
        """Test all response models include timestamps."""
        models = [
            SuccessResponse(data=1),
            ListResponse(data=[]),
            ErrorResponse(error=ErrorDetail(code="E", message="M")),
            DeletedResponse(),
        ]
        for model in models:
            assert hasattr(model, "timestamp")
            assert isinstance(model.timestamp, datetime)

    def test_model_dump_json_all_types(self):
        """Test JSON serialization for all response types."""
        models = [
            SuccessResponse(data={"key": "value"}),
            ListResponse(data=[1, 2, 3]),
            ErrorResponse(error=ErrorDetail(code="E", message="M")),
        ]
        for model in models:
            json_str = model.model_dump_json()
            assert isinstance(json_str, str)
            assert len(json_str) > 0
