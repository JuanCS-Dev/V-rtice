"""Tests for vertice_api.schemas module."""

from vertice_api.schemas import (
    ErrorResponse,
    HealthResponse,
    PaginatedResponse,
    SuccessResponse,
)


class TestHealthResponse:
    """Tests for HealthResponse schema."""

    def test_creates_with_defaults(self) -> None:
        """Test creating health response with defaults."""
        response = HealthResponse(service="test", version="1.0.0")

        assert response.status == "healthy"
        assert response.service == "test"
        assert response.version == "1.0.0"
        assert response.dependencies == {}

    def test_accepts_custom_dependencies(self) -> None:
        """Test health response with dependencies."""
        response = HealthResponse(
            service="test",
            version="1.0.0",
            dependencies={"db": "healthy", "redis": "unhealthy"},
        )

        assert response.dependencies["db"] == "healthy"
        assert response.dependencies["redis"] == "unhealthy"


class TestErrorResponse:
    """Tests for ErrorResponse schema."""

    def test_creates_error_response(self) -> None:
        """Test creating error response."""
        response = ErrorResponse(
            error="NotFound",
            message="Resource not found",
            status_code=404,
            details={"resource": "User", "id": 123},
        )

        assert response.error == "NotFound"
        assert response.message == "Resource not found"
        assert response.status_code == 404
        assert response.details["resource"] == "User"


class TestSuccessResponse:
    """Tests for SuccessResponse schema."""

    def test_wraps_data(self) -> None:
        """Test success response wraps data."""
        response = SuccessResponse(data={"user_id": 123, "name": "Test"})

        assert response.success is True
        assert response.data["user_id"] == 123
        assert response.data["name"] == "Test"


class TestPaginatedResponse:
    """Tests for PaginatedResponse schema."""

    def test_creates_paginated_response(self) -> None:
        """Test creating paginated response."""
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        response = PaginatedResponse.create(
            items=items,
            total=100,
            page=2,
            per_page=10,
        )

        assert len(response.items) == 3
        assert response.total == 100
        assert response.page == 2
        assert response.per_page == 10
        assert response.pages == 10

    def test_calculates_pages_correctly(self) -> None:
        """Test page calculation."""
        response = PaginatedResponse.create(
            items=[],
            total=25,
            page=1,
            per_page=10,
        )

        assert response.pages == 3

    def test_handles_exact_page_count(self) -> None:
        """Test when total is exact multiple of per_page."""
        response = PaginatedResponse.create(
            items=[],
            total=30,
            page=1,
            per_page=10,
        )

        assert response.pages == 3
