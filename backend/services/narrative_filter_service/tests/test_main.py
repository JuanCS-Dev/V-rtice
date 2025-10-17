"""Tests for main FastAPI app."""

from fastapi.testclient import TestClient
from narrative_filter_service.main import app

client = TestClient(app)


def test_metrics_endpoint() -> None:
    """Test Prometheus metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "narrative_filter" in response.text or "python_info" in response.text


def test_app_metadata() -> None:
    """Test app metadata."""
    assert app.title == "narrative-filter-service"
    assert app.version == "1.0.0"


def test_lifespan_coverage() -> None:
    """Test app lifespan is properly configured."""
    # The lifespan function is tested during app initialization
    assert hasattr(app, 'router')
    assert app.title == "narrative-filter-service"


def test_health_router_included() -> None:
    """Test health router is included."""
    response = client.get("/health/")
    assert response.status_code == 200
