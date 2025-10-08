"""
Vértice Platform - FastAPI Service Template with OpenAPI Documentation
=======================================================================

This template demonstrates best practices for creating a new FastAPI service
with comprehensive OpenAPI/Swagger documentation in the Vértice platform.

Features demonstrated:
    - OpenAPI configuration using shared module
    - Request/response models with Pydantic
    - Endpoint tagging and descriptions
    - Error handling integration
    - Security scheme integration
    - Health check endpoint
    - Request validation
    - Response examples

Usage:
    1. Copy this template to your new service directory
    2. Update service name, description, and port
    3. Implement your business logic
    4. Test with: http://localhost:{PORT}/docs
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

# Import shared modules
from backend.shared.constants import ServicePorts
from backend.shared.enums import ResponseStatus, ServiceStatus, ThreatLevel
from backend.shared.error_handlers import register_error_handlers
from backend.shared.exceptions import ValidationError
from backend.shared.openapi_config import create_openapi_config
from backend.shared.validators import validate_ip_address

# ============================================================================
# SERVICE CONFIGURATION
# ============================================================================

SERVICE_NAME = "Example Threat Analysis Service"
SERVICE_DESCRIPTION = """
**Example Threat Analysis Service** - Template for Vértice platform services.

This service demonstrates how to create a well-documented FastAPI service with:
- Comprehensive OpenAPI/Swagger documentation
- Standardized error handling
- Request validation
- Response models
- Security integration

## Endpoints

### Analysis
- `POST /analyze` - Analyze a threat indicator

### Health
- `GET /health` - Service health check
"""

SERVICE_VERSION = "1.0.0"
SERVICE_PORT = 8999  # Replace with actual port from ServicePorts

# Create FastAPI app with OpenAPI config
app = FastAPI(
    **create_openapi_config(
        service_name=SERVICE_NAME,
        service_description=SERVICE_DESCRIPTION,
        version=SERVICE_VERSION,
        service_port=SERVICE_PORT,
        tags=[
            {
                "name": "Analysis",
                "description": "Threat analysis operations",
            },
            {
                "name": "Health",
                "description": "Service health and status monitoring",
            },
        ],
    )
)

# Register error handlers
register_error_handlers(app)


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class AnalysisRequest(BaseModel):
    """Request model for threat analysis.

    Attributes:
        indicator: Threat indicator (IP, domain, hash, etc.)
        indicator_type: Type of indicator ('ip', 'domain', 'hash')
        analysis_depth: Analysis depth level (1-5, default: 3)
    """

    indicator: str = Field(
        ...,
        description="Threat indicator to analyze",
        examples=["192.168.1.1", "malicious.com", "abc123def456"],
        min_length=1,
        max_length=256,
    )

    indicator_type: str = Field(
        ...,
        description="Type of indicator",
        examples=["ip", "domain", "hash"],
        pattern="^(ip|domain|hash|email|url)$",
    )

    analysis_depth: int = Field(
        default=3,
        description="Analysis depth level (1=quick, 5=comprehensive)",
        ge=1,
        le=5,
        examples=[1, 3, 5],
    )

    @field_validator("indicator")
    @classmethod
    def validate_indicator(cls, v: str, info) -> str:
        """Validate indicator based on type."""
        indicator_type = info.data.get("indicator_type")

        # Example: validate IP addresses
        if indicator_type == "ip":
            try:
                validate_ip_address(v)
            except ValidationError as e:
                raise ValueError(f"Invalid IP address: {e.message}")

        return v

    class Config:
        """Pydantic config for better OpenAPI docs."""

        json_schema_extra = {
            "examples": [
                {
                    "indicator": "192.168.1.100",
                    "indicator_type": "ip",
                    "analysis_depth": 3,
                },
                {
                    "indicator": "evil-malware.com",
                    "indicator_type": "domain",
                    "analysis_depth": 5,
                },
            ]
        }


class AnalysisResult(BaseModel):
    """Response model for analysis results.

    Attributes:
        indicator: Analyzed indicator
        threat_level: Assessed threat level
        confidence: Confidence score (0.0-1.0)
        findings: List of analysis findings
        timestamp: Analysis timestamp
    """

    indicator: str = Field(..., description="Analyzed indicator")
    threat_level: ThreatLevel = Field(..., description="Assessed threat level")
    confidence: float = Field(
        ..., description="Confidence score", ge=0.0, le=1.0, examples=[0.85]
    )
    findings: List[str] = Field(
        default_factory=list, description="Analysis findings and observations"
    )
    timestamp: str = Field(..., description="Analysis timestamp (ISO 8601)")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "examples": [
                {
                    "indicator": "192.168.1.100",
                    "threat_level": "high",
                    "confidence": 0.92,
                    "findings": [
                        "IP found in 3 blacklists",
                        "Associated with malware distribution",
                        "Recent port scanning activity detected",
                    ],
                    "timestamp": "2025-10-05T14:30:00Z",
                }
            ]
        }


class AnalysisResponse(BaseModel):
    """Standardized analysis response wrapper.

    Attributes:
        status: Response status
        data: Analysis result data
        request_id: Request tracking ID
        processing_time_ms: Processing time in milliseconds
    """

    status: ResponseStatus = Field(
        default=ResponseStatus.SUCCESS, description="Response status"
    )
    data: AnalysisResult = Field(..., description="Analysis result")
    request_id: str = Field(..., description="Request tracking ID (UUID)")
    processing_time_ms: float = Field(..., description="Processing time (ms)")


class HealthResponse(BaseModel):
    """Health check response model.

    Attributes:
        status: Service health status
        version: Service version
        uptime_seconds: Service uptime in seconds
        timestamp: Health check timestamp
    """

    status: ServiceStatus = Field(..., description="Service health status")
    version: str = Field(..., description="Service version")
    uptime_seconds: float = Field(..., description="Service uptime (seconds)")
    timestamp: str = Field(..., description="Timestamp (ISO 8601)")


# ============================================================================
# ENDPOINTS
# ============================================================================


@app.post(
    "/analyze",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
    tags=["Analysis"],
    summary="Analyze threat indicator",
    description="""
    Analyze a threat indicator and assess its risk level.

    This endpoint performs comprehensive threat analysis including:
    - Reputation checks across multiple threat intelligence sources
    - Historical behavior analysis
    - Pattern matching against known threats
    - Risk scoring and confidence assessment

    **Supported Indicator Types:**
    - `ip`: IPv4/IPv6 addresses
    - `domain`: Domain names
    - `hash`: File hashes (MD5, SHA1, SHA256)
    - `email`: Email addresses
    - `url`: URLs

    **Analysis Depth Levels:**
    - **1** (Quick): Basic reputation check (~1s)
    - **3** (Standard): Multi-source analysis (~3s)
    - **5** (Deep): Comprehensive investigation (~10s)
    """,
    responses={
        200: {
            "description": "Analysis completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "data": {
                            "indicator": "192.168.1.100",
                            "threat_level": "high",
                            "confidence": 0.92,
                            "findings": [
                                "IP found in 3 blacklists",
                                "Associated with malware distribution",
                            ],
                            "timestamp": "2025-10-05T14:30:00Z",
                        },
                        "request_id": "550e8400-e29b-41d4-a716-446655440000",
                        "processing_time_ms": 2847.3,
                    }
                }
            },
        },
        400: {
            "description": "Invalid request parameters",
        },
        422: {
            "description": "Validation error",
        },
        500: {
            "description": "Internal server error",
        },
    },
)
async def analyze_threat(request: AnalysisRequest) -> AnalysisResponse:
    """Analyze a threat indicator and return assessment.

    Args:
        request: Analysis request with indicator details

    Returns:
        Analysis result with threat level and confidence

    Raises:
        HTTPException: If analysis fails
    """
    import time
    import uuid

    start_time = time.time()

    # TODO: Implement actual analysis logic here
    # This is a mock implementation for demonstration

    # Simulate analysis processing
    import asyncio

    await asyncio.sleep(0.1 * request.analysis_depth)

    # Mock result
    result = AnalysisResult(
        indicator=request.indicator,
        threat_level=ThreatLevel.MEDIUM,  # Mock: would be calculated
        confidence=0.75,  # Mock: would be calculated
        findings=[
            f"Analysis depth: {request.analysis_depth}",
            f"Indicator type: {request.indicator_type}",
            "Example finding: No significant threats detected",
        ],
        timestamp=datetime.utcnow().isoformat() + "Z",
    )

    processing_time = (time.time() - start_time) * 1000  # Convert to ms

    return AnalysisResponse(
        status=ResponseStatus.SUCCESS,
        data=result,
        request_id=str(uuid.uuid4()),
        processing_time_ms=round(processing_time, 2),
    )


@app.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    tags=["Health"],
    summary="Service health check",
    description="""
    Check the health status of the service.

    Returns service metadata including:
    - Current health status (healthy, degraded, unhealthy)
    - Service version
    - Uptime in seconds
    - Timestamp of the health check

    This endpoint is used by:
    - Load balancers for health checks
    - Monitoring systems (Prometheus, Grafana)
    - Service orchestration (Docker, Kubernetes)
    """,
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "version": "1.0.0",
                        "uptime_seconds": 3600.5,
                        "timestamp": "2025-10-05T14:30:00Z",
                    }
                }
            },
        },
    },
)
async def health_check() -> HealthResponse:
    """Get service health status.

    Returns:
        Health status response

    Note:
        This is a basic health check. In production, you should check:
        - Database connectivity
        - External API availability
        - Memory usage
        - Disk space
        - Queue lengths
    """
    import time

    # TODO: Add actual health checks (database, dependencies, etc.)
    # Mock uptime (in production, track from service start time)
    uptime = 3600.5

    return HealthResponse(
        status=ServiceStatus.HEALTHY,
        version=SERVICE_VERSION,
        uptime_seconds=uptime,
        timestamp=datetime.utcnow().isoformat() + "Z",
    )


@app.get(
    "/",
    tags=["Health"],
    summary="Root endpoint",
    description="Service information and API documentation link",
)
async def root():
    """Root endpoint - redirect to docs."""
    return {
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "status": "running",
        "docs": f"http://localhost:{SERVICE_PORT}/docs",
        "redoc": f"http://localhost:{SERVICE_PORT}/redoc",
        "openapi": f"http://localhost:{SERVICE_PORT}/openapi.json",
    }


# ============================================================================
# STARTUP/SHUTDOWN EVENTS
# ============================================================================


@app.on_event("startup")
async def startup_event():
    """Initialize service on startup."""
    print(f"Starting {SERVICE_NAME} v{SERVICE_VERSION}")
    print(f"OpenAPI docs: http://localhost:{SERVICE_PORT}/docs")
    # TODO: Initialize database connections, load models, etc.


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    print(f"Shutting down {SERVICE_NAME}")
    # TODO: Close database connections, cleanup resources, etc.


# ============================================================================
# RUN SERVER (for development)
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=SERVICE_PORT,
        log_level="info",
        reload=True,  # Auto-reload on code changes (dev only)
    )
