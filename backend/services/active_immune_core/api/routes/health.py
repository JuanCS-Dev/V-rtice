"""Health Routes - PRODUCTION-READY

Health check endpoints for liveness and readiness probes.

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

from typing import Any, Dict

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/", response_model=Dict[str, Any])
async def health_check() -> Dict[str, Any]:
    """
    Overall health check (liveness + readiness).

    Returns comprehensive health status including all components.

    Returns:
        Health status report
    """
    from api.main import health_checker

    if not health_checker:
        return {
            "status": "unknown",
            "message": "Health checker not initialized",
        }

    # Get full health report
    health_report = await health_checker.check_health()

    return health_report


@router.get("/live", response_model=Dict[str, str])
async def liveness_probe() -> JSONResponse:
    """
    Liveness probe endpoint.

    Kubernetes liveness probe - checks if the application is alive.
    Returns 200 if alive, 503 if dead.

    Returns:
        Liveness status
    """
    from api.main import health_checker

    if not health_checker:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "alive", "message": "Health checker not initialized yet"},
        )

    # Check overall health
    health_report = await health_checker.check_health()

    # If system is unhealthy, return 503
    if health_report["status"] == "unhealthy":
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "dead",
                "message": "System is unhealthy",
            },
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "alive"},
    )


@router.get("/ready", response_model=Dict[str, Any])
async def readiness_probe() -> JSONResponse:
    """
    Readiness probe endpoint.

    Kubernetes readiness probe - checks if the application is ready to serve traffic.
    Returns 200 if ready, 503 if not ready.

    Returns:
        Readiness status
    """
    from api.main import health_checker

    if not health_checker:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "ready": False,
                "message": "Health checker not initialized",
            },
        )

    # Check readiness
    readiness_report = await health_checker.check_readiness()

    if not readiness_report["ready"]:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=readiness_report,
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=readiness_report,
    )


@router.get("/components", response_model=Dict[str, Any])
async def components_health() -> Dict[str, Any]:
    """
    Get health status of all components.

    Returns detailed health information for each registered component.

    Returns:
        Component health statuses
    """
    from api.main import health_checker

    if not health_checker:
        return {
            "error": "Health checker not initialized",
            "components": {},
        }

    # Get health summary (doesn't perform checks, just returns last known state)
    summary = health_checker.get_health_summary()

    return summary


@router.get("/components/{component_name}", response_model=Dict[str, Any])
async def component_health(component_name: str) -> JSONResponse:
    """
    Check health of specific component.

    Args:
        component_name: Name of the component to check

    Returns:
        Component health status
    """
    from api.main import health_checker

    if not health_checker:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"error": "Health checker not initialized"},
        )

    # Get component
    component = health_checker.get_component(component_name)

    if not component:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": f"Component '{component_name}' not found"},
        )

    # Check component health
    await health_checker.check_component(component_name)

    # Return component details
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=component.to_dict(),
    )
