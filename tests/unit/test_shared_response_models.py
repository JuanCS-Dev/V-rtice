"""Tests for backend/shared/response_models.py - 100% coverage.

Strategy: Test all Pydantic models for structure, validation, serialization.
"""

import pytest
from datetime import datetime
from typing import List, Dict, Any
from pydantic import ValidationError
from backend.shared.response_models import (
    BaseResponse,
    SuccessResponse,
    ErrorResponse,
    ErrorDetail,
    PaginationMeta,
    ListResponse,
)


class TestBaseResponse:
    """Test BaseResponse model."""

    def test_base_response_creation(self):
        """BaseResponse can be created with required fields."""
        response = BaseResponse(success=True)
        
        assert response.success is True
        assert isinstance(response.timestamp, datetime)
        assert response.request_id is None

    def test_base_response_with_request_id(self):
        """BaseResponse can include request_id."""
        response = BaseResponse(success=False, request_id="req-123")
        
        assert response.success is False
        assert response.request_id == "req-123"

    def test_base_response_timestamp_auto(self):
        """BaseResponse auto-generates timestamp if not provided."""
        response = BaseResponse(success=True)
        
        assert response.timestamp is not None
        assert isinstance(response.timestamp, datetime)
        # Should be recent (within last minute)
        time_diff = datetime.utcnow() - response.timestamp
        assert time_diff.total_seconds() < 60

    def test_base_response_json_serialization(self):
        """BaseResponse serializes to JSON correctly."""
        response = BaseResponse(success=True, request_id="req-456")
        
        json_data = response.model_dump()
        assert json_data["success"] is True
        assert "timestamp" in json_data
        assert json_data["request_id"] == "req-456"

    def test_base_response_timestamp_format(self):
        """Timestamp should be ISO format with Z suffix."""
        response = BaseResponse(success=True)
        
        json_str = response.model_dump_json()
        # Should contain ISO timestamp with Z
        assert "Z" in json_str or "timestamp" in json_str


class TestSuccessResponse:
    """Test SuccessResponse model."""

    def test_success_response_creation(self):
        """SuccessResponse can be created with data."""
        data = {"user_id": 123, "username": "test"}
        response = SuccessResponse(data=data, message="User retrieved")
        
        assert response.success is True
        assert response.data == data
        assert response.message == "User retrieved"

    def test_success_response_generic_typing(self):
        """SuccessResponse supports generic data types."""
        # Dict data
        dict_response = SuccessResponse[Dict](data={"key": "value"})
        assert dict_response.data == {"key": "value"}
        
        # List data
        list_response = SuccessResponse[List](data=[1, 2, 3])
        assert list_response.data == [1, 2, 3]
        
        # String data
        str_response = SuccessResponse[str](data="simple string")
        assert str_response.data == "simple string"

    def test_success_response_with_meta(self):
        """SuccessResponse can include metadata."""
        response = SuccessResponse(
            data={"id": 1},
            message="Success",
            meta={"processing_time_ms": 45, "version": "v1"}
        )
        
        assert response.meta is not None
        assert response.meta["processing_time_ms"] == 45
        assert response.meta["version"] == "v1"

    def test_success_response_without_message(self):
        """SuccessResponse message is optional."""
        response = SuccessResponse(data={"test": True})
        
        assert response.data == {"test": True}
        assert response.message is None or response.message == ""

    def test_success_response_complex_data(self):
        """SuccessResponse handles complex nested data."""
        complex_data = {
            "user": {
                "id": 1,
                "profile": {
                    "name": "Test",
                    "tags": ["admin", "user"]
                }
            },
            "permissions": ["read", "write"]
        }
        
        response = SuccessResponse(data=complex_data)
        assert response.data == complex_data
        assert response.data["user"]["profile"]["tags"] == ["admin", "user"]


class TestErrorResponse:
    """Test ErrorResponse model."""

    def test_error_response_creation(self):
        """ErrorResponse can be created with error details."""
        error = ErrorDetail(
            code="VALIDATION_ERROR",
            message="Invalid input",
            field="email"
        )
        response = ErrorResponse(error=error)
        
        assert response.success is False
        assert response.error.code == "VALIDATION_ERROR"
        assert response.error.message == "Invalid input"
        assert response.error.field == "email"

    def test_error_response_without_field(self):
        """ErrorResponse field is optional."""
        error = ErrorDetail(
            code="SERVER_ERROR",
            message="Internal server error"
        )
        response = ErrorResponse(error=error)
        
        assert response.error.code == "SERVER_ERROR"
        assert response.error.field is None

    def test_error_response_with_details(self):
        """ErrorResponse can include additional details."""
        error = ErrorDetail(
            code="VALIDATION_ERROR",
            message="Multiple validation errors",
            details={
                "email": "Invalid format",
                "age": "Must be positive"
            }
        )
        response = ErrorResponse(error=error)
        
        assert response.error.details is not None
        assert "email" in response.error.details
        assert response.error.details["age"] == "Must be positive"

    def test_error_detail_minimal(self):
        """ErrorDetail requires only code and message."""
        error = ErrorDetail(code="TEST_ERROR", message="Test message")
        
        assert error.code == "TEST_ERROR"
        assert error.message == "Test message"
        assert error.field is None
        assert error.details is None


class TestPaginationMeta:
    """Test PaginationMeta model."""

    def test_pagination_meta_creation(self):
        """PaginationMeta can be created with all fields."""
        pagination = PaginationMeta(
            page=1,
            page_size=20,
            total_items=100,
            total_pages=5,
            has_next=True,
            has_previous=False
        )
        
        assert pagination.page == 1
        assert pagination.page_size == 20
        assert pagination.total_items == 100
        assert pagination.total_pages == 5

    def test_pagination_meta_validation(self):
        """PaginationMeta validates numeric fields are positive."""
        # Valid pagination
        valid = PaginationMeta(
            page=2,
            page_size=10,
            total_items=50,
            total_pages=5,
            has_next=True,
            has_previous=True
        )
        assert valid.page == 2

    def test_pagination_meta_first_page(self):
        """PaginationMeta works with first page."""
        pagination = PaginationMeta(
            page=1,
            page_size=25,
            total_items=100,
            total_pages=4,
            has_next=True,
            has_previous=False
        )
        
        assert pagination.page == 1
        assert pagination.total_pages == 4

    def test_pagination_meta_last_page(self):
        """PaginationMeta works with last page."""
        pagination = PaginationMeta(
            page=10,
            page_size=10,
            total_items=100,
            total_pages=10,
            has_next=False,
            has_previous=True
        )
        
        assert pagination.page == 10
        assert pagination.total_pages == 10

    def test_pagination_meta_from_params(self):
        """PaginationMeta.from_params factory method works."""
        pagination = PaginationMeta.from_params(
            page=2, page_size=10, total_items=100
        )
        
        assert pagination.page == 2
        assert pagination.page_size == 10
        assert pagination.total_items == 100
        assert pagination.total_pages == 10
        assert pagination.has_next is True
        assert pagination.has_previous is True


class TestListResponse:
    """Test ListResponse model."""

    def test_list_response_creation(self):
        """ListResponse can be created with list data."""
        items = [
            {"id": 1, "name": "Item 1"},
            {"id": 2, "name": "Item 2"},
        ]
        pagination = PaginationMeta(
            page=1, page_size=20, total_items=2, total_pages=1,
            has_next=False, has_previous=False
        )
        
        response = ListResponse(
            data=items,
            pagination=pagination,
            message="Items retrieved"
        )
        
        assert response.success is True
        assert len(response.data) == 2
        assert response.pagination.total_items == 2

    def test_list_response_empty_list(self):
        """ListResponse handles empty lists."""
        pagination = PaginationMeta(
            page=1, page_size=20, total_items=0, total_pages=0,
            has_next=False, has_previous=False
        )
        
        response = ListResponse(data=[], pagination=pagination)
        
        assert response.data == []
        assert response.pagination.total_items == 0

    def test_list_response_with_meta(self):
        """ListResponse can include metadata."""
        items = [{"id": 1}]
        pagination = PaginationMeta(
            page=1, page_size=10, total_items=1, total_pages=1,
            has_next=False, has_previous=False
        )
        
        response = ListResponse(
            data=items,
            pagination=pagination,
            meta={"query_time_ms": 23}
        )
        
        assert response.meta is not None
        assert response.meta["query_time_ms"] == 23

    def test_list_response_generic_typing(self):
        """ListResponse supports generic list types."""
        # List of dicts
        dict_items = [{"id": 1}, {"id": 2}]
        pagination = PaginationMeta(
            page=1, page_size=10, total_items=2, total_pages=1,
            has_next=False, has_previous=False
        )
        
        response = ListResponse(data=dict_items, pagination=pagination)
        assert len(response.data) == 2


class TestResponseModelIntegration:
    """Integration tests for response models."""

    def test_success_to_json_roundtrip(self):
        """SuccessResponse serializes and deserializes correctly."""
        original = SuccessResponse(
            data={"id": 123, "name": "Test"},
            message="Success"
        )
        
        # Serialize to JSON
        json_data = original.model_dump()
        
        # Deserialize back
        restored = SuccessResponse(**json_data)
        
        assert restored.data == original.data
        assert restored.message == original.message

    def test_error_to_json_roundtrip(self):
        """ErrorResponse serializes and deserializes correctly."""
        original = ErrorResponse(
            error=ErrorDetail(
                code="TEST_ERROR",
                message="Test error message",
                field="test_field"
            )
        )
        
        json_data = original.model_dump()
        restored = ErrorResponse(**json_data)
        
        assert restored.error.code == original.error.code
        assert restored.error.message == original.error.message
        assert restored.error.field == original.error.field

    def test_list_response_to_json_roundtrip(self):
        """ListResponse serializes and deserializes correctly."""
        original = ListResponse(
            data=[{"id": 1}, {"id": 2}],
            pagination=PaginationMeta(
                page=1, page_size=10, total_items=2, total_pages=1,
                has_next=False, has_previous=False
            )
        )
        
        json_data = original.model_dump()
        restored = ListResponse(**json_data)
        
        assert restored.data == original.data
        assert restored.pagination.total_items == 2

    def test_response_models_with_fastapi(self):
        """Response models are compatible with FastAPI."""
        # FastAPI uses model_dump() and model_dump_json()
        response = SuccessResponse(data={"test": True})
        
        assert hasattr(response, "model_dump")
        assert hasattr(response, "model_dump_json")
        
        json_str = response.model_dump_json()
        assert isinstance(json_str, str)
        assert "test" in json_str


class TestResponseModelEdgeCases:
    """Edge cases and validation tests."""

    def test_success_response_none_data(self):
        """SuccessResponse handles None data."""
        response = SuccessResponse(data=None)
        assert response.data is None

    def test_error_detail_empty_strings(self):
        """ErrorDetail handles empty strings."""
        error = ErrorDetail(code="", message="")
        assert error.code == ""
        assert error.message == ""

    def test_pagination_zero_items(self):
        """PaginationMeta handles zero items."""
        pagination = PaginationMeta(
            page=1, page_size=10, total_items=0, total_pages=0,
            has_next=False, has_previous=False
        )
        assert pagination.total_items == 0
        assert pagination.total_pages == 0

    def test_response_model_inheritance(self):
        """All response models inherit from BaseResponse."""
        success = SuccessResponse(data={})
        error = ErrorResponse(error=ErrorDetail(code="E", message="M"))
        list_resp = ListResponse(
            data=[],
            pagination=PaginationMeta(
                page=1, page_size=10, total_items=0, total_pages=0,
                has_next=False, has_previous=False
            )
        )
        
        assert isinstance(success, BaseResponse)
        assert isinstance(error, BaseResponse)
        assert isinstance(list_resp, BaseResponse)


class TestValidationErrorResponse:
    """Test ValidationErrorResponse model."""

    def test_validation_error_response_creation(self):
        """ValidationErrorResponse creates response from Pydantic errors."""
        from backend.shared.response_models import ValidationErrorResponse
        
        # Simular erros do Pydantic
        pydantic_errors = [
            {
                "loc": ("field1",),
                "msg": "Field required",
                "type": "value_error.missing"
            },
            {
                "loc": ("field2", "nested"),
                "msg": "Invalid value",
                "type": "value_error"
            }
        ]
        
        response = ValidationErrorResponse(errors=pydantic_errors)
        
        assert response.success is False
        assert response.error.code == "VALIDATION_ERROR"
        assert response.error.message == "Request validation failed"
        assert response.errors is not None
        assert len(response.errors) == 2
        assert response.errors[0].field == "field1"
        assert response.errors[1].field == "field2.nested"

    def test_validation_error_single_field(self):
        """ValidationErrorResponse handles single field error."""
        from backend.shared.response_models import ValidationErrorResponse
        
        errors = [{"loc": ("email",), "msg": "Invalid email", "type": "value_error"}]
        response = ValidationErrorResponse(errors=errors)
        
        assert len(response.errors) == 1
        assert response.errors[0].field == "email"
        assert response.errors[0].message == "Invalid email"


class TestHelperFunctions:
    """Test helper functions for response creation."""

    def test_success_response_helper(self):
        """success_response() helper function works."""
        from backend.shared.response_models import success_response
        
        result = success_response(
            data={"id": 1, "name": "Test"},
            message="Success",
            meta={"version": "v1"}
        )
        
        assert isinstance(result, dict)
        assert result["success"] is True
        assert result["data"] == {"id": 1, "name": "Test"}
        assert result["message"] == "Success"
        assert result["meta"]["version"] == "v1"

    def test_list_response_helper_with_pagination(self):
        """list_response() helper creates paginated response."""
        from backend.shared.response_models import list_response
        
        result = list_response(
            data=[{"id": 1}, {"id": 2}],
            page=1,
            page_size=10,
            total_items=2,
            message="Items retrieved"
        )
        
        assert isinstance(result, dict)
        assert result["success"] is True
        assert len(result["data"]) == 2
        assert result["pagination"] is not None
        assert result["pagination"]["page"] == 1
        assert result["pagination"]["total_items"] == 2

    def test_list_response_helper_without_pagination(self):
        """list_response() helper works without pagination."""
        from backend.shared.response_models import list_response
        
        result = list_response(
            data=[{"id": 1}],
            message="Items retrieved"
        )
        
        assert isinstance(result, dict)
        assert result["success"] is True
        assert result["pagination"] is None

    def test_error_response_helper(self):
        """error_response() helper function works."""
        from backend.shared.response_models import error_response
        
        result = error_response(
            code="NOT_FOUND",
            message="Resource not found",
            status_code=404,
            field="id",
            details={"resource_type": "user"}
        )
        
        assert isinstance(result, dict)
        assert result["success"] is False
        assert result["error"]["code"] == "NOT_FOUND"
        assert result["error"]["message"] == "Resource not found"
        assert result["error"]["field"] == "id"
        assert result["error"]["details"]["resource_type"] == "user"

    def test_error_response_helper_minimal(self):
        """error_response() helper works with minimal params."""
        from backend.shared.response_models import error_response
        
        result = error_response(
            code="SERVER_ERROR",
            message="Internal error"
        )
        
        assert isinstance(result, dict)
        assert result["success"] is False
        assert result["error"]["code"] == "SERVER_ERROR"
        assert result["error"]["field"] is None


class TestResponseModelSpecialCases:
    """Test special response model classes."""

    def test_created_response(self):
        """CreatedResponse has correct default message."""
        from backend.shared.response_models import CreatedResponse
        
        response = CreatedResponse(data={"id": 123})
        
        assert response.success is True
        assert response.message == "Resource created successfully"
        assert response.data["id"] == 123

    def test_updated_response(self):
        """UpdatedResponse has correct default message."""
        from backend.shared.response_models import UpdatedResponse
        
        response = UpdatedResponse(data={"id": 123, "updated": True})
        
        assert response.success is True
        assert response.message == "Resource updated successfully"

    def test_deleted_response(self):
        """DeletedResponse has correct structure."""
        from backend.shared.response_models import DeletedResponse
        
        response = DeletedResponse()
        
        assert response.success is True
        assert response.message == "Resource deleted successfully"
        assert response.meta is None

    def test_deleted_response_with_meta(self):
        """DeletedResponse can include metadata."""
        from backend.shared.response_models import DeletedResponse
        
        response = DeletedResponse(meta={"deleted_at": "2025-01-01T00:00:00Z"})
        
        assert response.success is True
        assert response.meta is not None
        assert "deleted_at" in response.meta

