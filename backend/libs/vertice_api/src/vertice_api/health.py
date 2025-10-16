"""Health check endpoint."""

from collections.abc import Callable

from fastapi import APIRouter, Response

from .schemas import HealthResponse


def create_health_router(
    service_name: str,
    service_version: str,
    dependency_checks: dict[str, Callable[[], bool]] | None = None,
) -> APIRouter:
    """Create health check router with optional dependency checks."""
    router = APIRouter(tags=["health"])
    checks = dependency_checks or {}

    @router.get("/health", response_model=HealthResponse)
    async def health_check(response: Response) -> HealthResponse:
        """Health check endpoint."""
        dependencies = {}
        all_healthy = True

        for name, check_fn in checks.items():
            try:
                is_healthy = check_fn()
                dependencies[name] = "healthy" if is_healthy else "unhealthy"
                if not is_healthy:
                    all_healthy = False
            except Exception:
                dependencies[name] = "error"
                all_healthy = False

        if not all_healthy:
            response.status_code = 503

        return HealthResponse(
            status="healthy" if all_healthy else "unhealthy",
            service=service_name,
            version=service_version,
            dependencies=dependencies,
        )

    @router.get("/health/ready")
    async def readiness_check(response: Response) -> dict[str, str]:
        """Readiness check for k8s."""
        all_ready = all(check_fn() for check_fn in checks.values())

        if not all_ready:
            response.status_code = 503
            return {"status": "not_ready"}

        return {"status": "ready"}

    @router.get("/health/live")
    async def liveness_check() -> dict[str, str]:
        """Liveness check for k8s."""
        return {"status": "alive"}

    return router
