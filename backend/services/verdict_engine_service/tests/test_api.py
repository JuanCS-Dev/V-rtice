"""Tests for REST API endpoints."""

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from api import get_cache, get_repository
from main import app


@pytest.mark.asyncio
async def test_get_active_verdicts_endpoint(mock_repository, mock_cache, sample_verdict):
    """Test GET /api/v1/verdicts/active."""
    mock_repository.get_active_verdicts.return_value = [sample_verdict]

    # Override dependencies
    app.dependency_overrides[get_repository] = lambda: mock_repository
    app.dependency_overrides[get_cache] = lambda: mock_cache

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/verdicts/active")

    app.dependency_overrides.clear()


    app.dependency_overrides.clear()
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["category"] == "DECEPTION"


@pytest.mark.asyncio
async def test_get_verdict_by_id_cached(mock_repository, mock_cache, sample_verdict):
    """Test GET /api/v1/verdicts/{id} with cache hit."""
    verdict_id = sample_verdict.id
    mock_cache.get_verdict.return_value = sample_verdict

    app.dependency_overrides[get_repository] = lambda: mock_repository
    app.dependency_overrides[get_cache] = lambda: mock_cache

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/v1/verdicts/{verdict_id}")

    assert response.status_code == 200
    data = response.json()

    app.dependency_overrides.clear()
    assert data["id"] == str(verdict_id)
    mock_cache.get_verdict.assert_called_once_with(verdict_id)


@pytest.mark.asyncio
async def test_get_verdict_by_id_not_found(mock_repository, mock_cache):
    """Test GET /api/v1/verdicts/{id} not found."""
    verdict_id = uuid4()
    mock_cache.get_verdict.return_value = None
    mock_repository.get_verdict_by_id.return_value = None

    app.dependency_overrides[get_repository] = lambda: mock_repository
    app.dependency_overrides[get_cache] = lambda: mock_cache

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/v1/verdicts/{verdict_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Verdict not found"


@pytest.mark.asyncio
async def test_get_verdict_stats_cached(mock_repository, mock_cache, sample_stats):
    """Test GET /api/v1/verdicts/stats with cache hit."""
    mock_cache.get_stats.return_value = sample_stats

    app.dependency_overrides[get_repository] = lambda: mock_repository
    app.dependency_overrides[get_cache] = lambda: mock_cache

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/verdicts/stats")

    assert response.status_code == 200
    data = response.json()

    app.dependency_overrides.clear()
    assert data["total_count"] == 100
    mock_cache.get_stats.assert_called_once()


@pytest.mark.asyncio
async def test_update_verdict_status(mock_repository, mock_cache):
    """Test PUT /api/v1/verdicts/{id}/status."""
    verdict_id = uuid4()
    mock_repository.update_verdict_status.return_value = True

    app.dependency_overrides[get_repository] = lambda: mock_repository
    app.dependency_overrides[get_cache] = lambda: mock_cache

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/verdicts/{verdict_id}/status",
            params={"new_status": "MITIGATED"},
        )


    app.dependency_overrides.clear()
    assert response.status_code == 200
    data = response.json()
    assert data["updated"] is True
    assert data["status"] == "MITIGATED"


@pytest.mark.asyncio
async def test_update_verdict_status_not_found(mock_repository, mock_cache):
    """Test PUT /api/v1/verdicts/{id}/status for non-existent verdict."""
    verdict_id = uuid4()
    mock_repository.update_verdict_status.return_value = False

    app.dependency_overrides[get_repository] = lambda: mock_repository
    app.dependency_overrides[get_cache] = lambda: mock_cache

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/verdicts/{verdict_id}/status",
            params={"new_status": "DISMISSED"},
        )


    app.dependency_overrides.clear()
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_health_check_healthy(mock_repository, mock_cache):
    """Test GET /api/v1/health when all dependencies healthy."""
    mock_repository.pool = True
    mock_cache.client = True

    app.dependency_overrides[get_repository] = lambda: mock_repository
    app.dependency_overrides[get_cache] = lambda: mock_cache

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()

    app.dependency_overrides.clear()
    assert data["status"] == "healthy"
    assert data["dependencies"]["postgres"] is True
    assert data["dependencies"]["redis"] is True


@pytest.mark.asyncio
async def test_health_check_degraded(mock_repository, mock_cache):
    """Test GET /api/v1/health when some dependencies down."""
    mock_repository.pool = True
    mock_cache.client = None  # Redis down

    app.dependency_overrides[get_repository] = lambda: mock_repository
    app.dependency_overrides[get_cache] = lambda: mock_cache

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()

    app.dependency_overrides.clear()
    assert data["status"] == "degraded"
    assert data["dependencies"]["redis"] is False
