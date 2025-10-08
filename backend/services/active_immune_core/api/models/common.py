"""Common API Models - PRODUCTION-READY

Common Pydantic models used across the API.

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response model"""

    status: str = Field(..., description="Health status (healthy/degraded/unhealthy/unknown)")
    timestamp: str = Field(..., description="ISO timestamp of check")
    summary: Dict[str, int] = Field(..., description="Summary statistics")
    components: Dict[str, Dict[str, Any]] = Field(..., description="Per-component health")


class MetricsResponse(BaseModel):
    """Metrics response model"""

    timestamp: str = Field(..., description="ISO timestamp")
    window_seconds: int = Field(..., description="Time window for aggregations")
    counters: Dict[str, int] = Field(..., description="Counter metrics")
    gauges: Dict[str, float] = Field(..., description="Gauge metrics")


class ErrorResponse(BaseModel):
    """Error response model"""

    error: str = Field(..., description="Error message")
    status_code: int = Field(..., description="HTTP status code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class SuccessResponse(BaseModel):
    """Success response model"""

    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional response data")


class PaginationParams(BaseModel):
    """Pagination parameters"""

    skip: int = Field(0, ge=0, description="Number of items to skip")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of items to return")


class PaginatedResponse(BaseModel):
    """Paginated response wrapper"""

    total: int = Field(..., description="Total number of items")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Maximum items in this response")
    items: List[Any] = Field(..., description="List of items")
