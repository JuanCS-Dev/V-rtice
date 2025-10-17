"""Tests for health API."""

import pytest
from health_api import router
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def test_app():
    """Create test FastAPI app."""
    app = FastAPI()
    app.include_router(router, prefix="/health")
    return app


@pytest.fixture
def client(test_app):
    """Create test client."""
    return TestClient(test_app)


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "command-bus-service"
    assert data["version"] == "1.0.0"
    assert "timestamp" in data
