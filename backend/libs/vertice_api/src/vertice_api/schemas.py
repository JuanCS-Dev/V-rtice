"""Standard API response schemas."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(default="healthy")
    service: str
    version: str
    dependencies: dict[str, str] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Error response format."""

    error: str
    message: str
    status_code: int
    details: dict[str, Any] = Field(default_factory=dict)


class SuccessResponse(BaseModel, Generic[T]):
    """Generic success response wrapper."""

    success: bool = Field(default=True)
    data: T


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""

    items: list[T]
    total: int
    page: int
    per_page: int
    pages: int

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int = 1,
        per_page: int = 50,
    ) -> "PaginatedResponse[T]":
        """Create paginated response from items."""
        pages = (total + per_page - 1) // per_page
        return cls(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
        )
