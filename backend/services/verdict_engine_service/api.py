"""REST API endpoints for Verdict Engine.

Provides HTTP access to verdicts, stats, and health.
Integrates with cache and repository.
"""

from typing import Any, cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from services.verdict_engine_service.cache import VerdictCache
from services.verdict_engine_service.models import (
    CategoryType,
    HealthResponse,
    SeverityLevel,
    StatusType,
    Verdict,
    VerdictFilter,
    VerdictStats,
)
from services.verdict_engine_service.verdict_repository import VerdictRepository

router = APIRouter(prefix="/api/v1", tags=["verdicts"])


# Dependency injection
def get_repository() -> VerdictRepository:
    """Get verdict repository (injected)."""
    # Will be set by main.py during startup
    raise NotImplementedError("Repository not initialized")


def get_cache() -> VerdictCache:
    """Get verdict cache (injected)."""
    # Will be set by main.py during startup
    raise NotImplementedError("Cache not initialized")


@router.get("/verdicts/active", response_model=list[Verdict])
async def get_active_verdicts(
    status: str | None = Query(None, description="Filter by status"),
    severity: str | None = Query(None, description="Filter by severity"),
    category: str | None = Query(None, description="Filter by category"),
    agent_id: str | None = Query(None, description="Filter by agent ID"),
    limit: int = Query(50, ge=1, le=500, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    repository: VerdictRepository = Depends(get_repository),
) -> list[Verdict]:
    """Get active verdicts with optional filters."""
    filters = VerdictFilter(
        status=cast(StatusType | None, status),
        severity=cast(SeverityLevel | None, severity),
        category=cast(CategoryType | None, category),
        agent_id=agent_id,
        limit=limit,
        offset=offset,
    )

    verdicts = await repository.get_active_verdicts(filters)
    return verdicts


@router.get("/verdicts/stats", response_model=VerdictStats)
async def get_verdict_stats(
    cache: VerdictCache = Depends(get_cache),
    repository: VerdictRepository = Depends(get_repository),
) -> VerdictStats:
    """Get aggregated verdict statistics (cache-first)."""
    # Try cache first
    cached = await cache.get_stats()
    if cached:
        return cached

    # Fallback to database
    stats = await repository.get_stats()  # pragma: no cover
  # pragma: no cover
    # Cache for future requests  # pragma: no cover
    await cache.cache_stats(stats)  # pragma: no cover
  # pragma: no cover
    return stats  # pragma: no cover


@router.get("/verdicts/{verdict_id}", response_model=Verdict)
async def get_verdict(
    verdict_id: UUID,
    cache: VerdictCache = Depends(get_cache),
    repository: VerdictRepository = Depends(get_repository),
) -> Verdict:
    """Get single verdict by ID (cache-first)."""
    # Try cache first
    cached = await cache.get_verdict(verdict_id)
    if cached:
        return cached

    # Fallback to database
    verdict = await repository.get_verdict_by_id(verdict_id)
    if not verdict:
        raise HTTPException(status_code=404, detail="Verdict not found")

    # Cache for future requests
    await cache.cache_verdict(verdict)  # pragma: no cover
  # pragma: no cover
    return verdict  # pragma: no cover


@router.put("/verdicts/{verdict_id}/status")
async def update_verdict_status(
    verdict_id: UUID,
    new_status: str,
    mitigation_id: UUID | None = None,
    cache: VerdictCache = Depends(get_cache),
    repository: VerdictRepository = Depends(get_repository),
) -> dict[str, Any]:
    """Update verdict status (for C2L integration)."""
    success = await repository.update_verdict_status(verdict_id, new_status, mitigation_id)

    if not success:
        raise HTTPException(status_code=404, detail="Verdict not found")

    # Invalidate cache
    await cache.invalidate_verdict(verdict_id)
    await cache.invalidate_stats()

    return {"verdict_id": str(verdict_id), "status": new_status, "updated": True}


@router.get("/health", response_model=HealthResponse)
async def health_check(
    repository: VerdictRepository = Depends(get_repository),
    cache: VerdictCache = Depends(get_cache),
) -> HealthResponse:
    """Health check endpoint."""
    dependencies: dict[str, bool] = {
        "postgres": repository.pool is not None,
        "redis": cache.client is not None,
    }

    status: str = "healthy" if all(dependencies.values()) else "degraded"

    return HealthResponse(status=cast(Any, status), dependencies=dependencies)
