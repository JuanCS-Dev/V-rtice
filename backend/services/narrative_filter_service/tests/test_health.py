"""Tests for health endpoint."""

import pytest


@pytest.mark.asyncio
async def test_health_check() -> None:
    """Test health check endpoint."""
    import health_api

    response = await health_api.health_check()

    assert response.status == "ok"
    assert response.service == "narrative-filter-service"
    assert response.version == "1.0.0"
    assert response.timestamp is not None


@pytest.mark.asyncio
async def test_health_check_model_validation() -> None:
    """Test health check response model validation."""
    import health_api
    from models import HealthResponse

    response = await health_api.health_check()

    # Verify it's the correct model
    assert isinstance(response, HealthResponse)

    # Verify required fields
    assert hasattr(response, "status")
    assert hasattr(response, "service")
    assert hasattr(response, "version")
    assert hasattr(response, "timestamp")
