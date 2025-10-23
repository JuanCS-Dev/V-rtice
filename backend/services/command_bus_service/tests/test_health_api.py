"""Tests for health API."""

import pytest
from health_api import router
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def test_app():
    """Create test FastAPI app."""
    app = FastAPI()
    app.include_router(router, prefix="/health")
    return app


@pytest.mark.asyncio
async def test_health_check(test_app):
    """Test health check endpoint."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "command-bus-service"
        assert data["version"] == "1.0.0"
        assert "timestamp" in data
