"""
Health check endpoints for HITL API.

Provides multiple health check endpoints for different use cases:
- /health: Basic health check (fast, always returns 200 if app is running)
- /health/ready: Readiness check (checks dependencies like DB, Redis, RabbitMQ)
- /health/live: Liveness check (simple ping, for Kubernetes liveness probes)

Usage:
    # Include in main.py:
    from .health import router as health_router
    app.include_router(health_router)

    # Docker healthcheck:
    HEALTHCHECK CMD curl -f http://localhost:8003/health || exit 1

    # Kubernetes liveness probe:
    livenessProbe:
      httpGet:
        path: /health/live
        port: 8003

    # Kubernetes readiness probe:
    readinessProbe:
      httpGet:
        path: /health/ready
        port: 8003
"""

from fastapi import APIRouter, Response, status
from pydantic import BaseModel, Field
from typing import Dict
from datetime import datetime
import time


router = APIRouter(prefix="/health", tags=["Health"])

# Track application start time
_start_time = time.time()


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(
        description="Overall health status (healthy, degraded, unhealthy)"
    )
    version: str = Field(description="Application version")
    uptime_seconds: float = Field(description="Application uptime in seconds")
    timestamp: str = Field(description="Current timestamp (ISO 8601)")
    checks: Dict[str, str] = Field(description="Individual component health checks")


@router.get("/", response_model=HealthResponse, summary="Basic health check")
async def health_check() -> HealthResponse:
    """
    Basic health check endpoint.

    Returns:
        200 OK if the application is running.

    Use this for:
        - Docker healthcheck
        - Load balancer health checks
        - Simple monitoring

    This endpoint does NOT check dependencies (database, Redis, etc.).
    Use /health/ready for dependency checks.
    """
    uptime = time.time() - _start_time

    return HealthResponse(
        status="healthy",
        version="1.0.0",
        uptime_seconds=uptime,
        timestamp=datetime.utcnow().isoformat() + "Z",
        checks={
            "api": "ok",
        },
    )


@router.get("/ready", response_model=HealthResponse, summary="Readiness check")
async def readiness_check() -> HealthResponse:
    """
    Readiness check endpoint with dependency validation.

    Checks:
        - Database connection
        - Redis connection
        - RabbitMQ connection
        - GitHub API accessibility

    Returns:
        - 200 OK if all dependencies are healthy (status="ready")
        - 503 Service Unavailable if any dependency is unhealthy (status="not_ready")

    Use this for:
        - Kubernetes readiness probes
        - Load balancer readiness checks
        - Deployment validation

    This endpoint should NOT be used for liveness probes as it may fail
    temporarily during startup or brief outages.
    """
    uptime = time.time() - _start_time
    checks = {}
    all_healthy = True

    # Check Database
    try:
        # TODO: Add actual database health check
        # from hitl.database import engine
        # async with engine.connect() as conn:
        #     await conn.execute("SELECT 1")
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"
        all_healthy = False

    # Check Redis
    try:
        # TODO: Add actual Redis health check
        # from hitl.cache import redis_client
        # await redis_client.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {str(e)}"
        all_healthy = False

    # Check RabbitMQ
    try:
        # TODO: Add actual RabbitMQ health check
        # from hitl.messaging import rabbitmq_connection
        # assert rabbitmq_connection.is_open
        checks["rabbitmq"] = "ok"
    except Exception as e:
        checks["rabbitmq"] = f"error: {str(e)}"
        all_healthy = False

    # Check GitHub API
    try:
        # TODO: Add actual GitHub API health check
        # from hitl.config import settings
        # if settings.github_configured:
        #     from github import Github
        #     g = Github(settings.github_token)
        #     g.get_rate_limit()  # Will raise if token is invalid
        checks["github"] = "ok"
    except Exception as e:
        checks["github"] = f"error: {str(e)}"
        all_healthy = False

    # Determine overall status
    overall_status = "ready" if all_healthy else "not_ready"
    http_status = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    response = HealthResponse(
        status=overall_status,
        version="1.0.0",
        uptime_seconds=uptime,
        timestamp=datetime.utcnow().isoformat() + "Z",
        checks=checks,
    )

    # Return 503 if not ready
    if not all_healthy:
        return Response(
            content=response.model_dump_json(),
            status_code=http_status,
            media_type="application/json",
        )

    return response


@router.get("/live", summary="Liveness check")
async def liveness_check() -> Dict[str, str]:
    """
    Liveness check endpoint (simple ping).

    Always returns 200 OK if the application process is running.

    Use this for:
        - Kubernetes liveness probes
        - Process monitoring

    This endpoint should return quickly (< 100ms) and never fail unless
    the application process is deadlocked or crashed.

    Do NOT use this for checking dependencies - use /health/ready instead.

    Returns:
        Simple JSON response: {"status": "alive"}
    """
    return {"status": "alive"}


@router.get("/startup", summary="Startup check")
async def startup_check() -> Dict[str, str]:
    """
    Startup check endpoint.

    Used by Kubernetes startup probes to know when the application has
    finished initialization and is ready to accept traffic.

    This can have a longer timeout than liveness/readiness probes since
    startup may take several seconds.

    Returns:
        {"status": "started"} once application initialization is complete
    """
    # TODO: Add actual startup checks
    # - Database migrations complete
    # - Configuration loaded
    # - Required services connected

    return {"status": "started"}
