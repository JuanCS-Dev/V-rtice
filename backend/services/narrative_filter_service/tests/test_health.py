"""Tests for health endpoint."""

from fastapi.testclient import TestClient

from narrative_filter_service.main import app

client = TestClient(app)


def test_health_check() -> None:
    """Test health check endpoint."""
    response = client.get("/health/")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "narrative-filter-service"
    assert data["version"] == "1.0.0"
    assert "timestamp" in data


def test_health_check_fields() -> None:
    """Test health check response fields."""
    response = client.get("/health/")
    data = response.json()

    required_fields = ["status", "service", "version", "timestamp"]
    for field in required_fields:
        assert field in data, f"Missing field: {field}"
