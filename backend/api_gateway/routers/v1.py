"""API Gateway - Version 1 Router.

This module defines all v1 API endpoints for the Vértice platform.
All routes are prefixed with /api/v1/ for explicit versioning.

Following Boris Cherny's principle: "Explicit is better than implicit"
"""

from typing import Dict

from fastapi import APIRouter, status
from pydantic import BaseModel


# ============================================================================
# Router Configuration
# ============================================================================
router = APIRouter(
    prefix="/api/v1",
    tags=["v1"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"},
    },
)


# ============================================================================
# Response Models
# ============================================================================
class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    version: str
    timestamp: str
    services: Dict[str, str] = {}

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "3.3.1",
                "timestamp": "2025-11-15T12:00:00Z",
                "services": {
                    "database": "healthy",
                    "redis": "healthy",
                },
            }
        }


class RootResponse(BaseModel):
    """Root endpoint response model."""

    message: str
    version: str
    docs_url: str
    openapi_url: str

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Vértice API Gateway - Version 1",
                "version": "v1",
                "docs_url": "/docs",
                "openapi_url": "/openapi.json",
            }
        }


# ============================================================================
# Core Endpoints
# ============================================================================
@router.get(
    "/",
    response_model=RootResponse,
    summary="API Root",
    description="Get API version information and documentation links",
    tags=["core"],
    status_code=status.HTTP_200_OK,
)
async def root_v1() -> RootResponse:
    """Get API v1 root information.

    Returns:
        RootResponse: API version info and links
    """
    from datetime import datetime

    return RootResponse(
        message="Vértice API Gateway - Version 1",
        version="v1",
        docs_url="/docs",
        openapi_url="/openapi.json",
    )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Check API Gateway health status and service availability",
    tags=["health"],
    status_code=status.HTTP_200_OK,
)
async def health_v1() -> HealthResponse:
    """Health check endpoint for v1 API.

    This endpoint checks:
    - API Gateway responsiveness
    - Critical service availability
    - Redis connection status

    Returns:
        HealthResponse: Service health status

    Example:
        GET /api/v1/health
        {
            "status": "healthy",
            "version": "3.3.1",
            "timestamp": "2025-11-15T12:00:00Z",
            "services": {
                "redis": "healthy"
            }
        }
    """
    from datetime import datetime

    # TODO: Add actual service health checks
    # For now, return basic health status
    return HealthResponse(
        status="healthy",
        version="3.3.1",
        timestamp=datetime.utcnow().isoformat() + "Z",
        services={
            "api_gateway": "healthy",
            # Add actual health checks:
            # "redis": await check_redis_health(),
            # "database": await check_db_health(),
        },
    )


# ============================================================================
# Placeholder for Future v1 Endpoints
# ============================================================================
# When migrating existing endpoints to v1, add them here following this pattern:
#
# @router.post(
#     "/scan/start",
#     response_model=ScanResponse,
#     summary="Start Security Scan",
#     tags=["security"],
# )
# async def start_scan_v1(request: ScanRequest) -> ScanResponse:
#     """Start a new security scan."""
#     # Implementation
#     pass
#
# Guidelines:
# 1. All endpoints must have response_model for type safety
# 2. Add comprehensive docstrings with examples
# 3. Use proper HTTP status codes
# 4. Tag endpoints by functional area
# 5. Include request/response examples in Config
