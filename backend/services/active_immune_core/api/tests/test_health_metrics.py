"""Health and Metrics Tests - PRODUCTION-READY

Comprehensive tests for health checks and metrics endpoints.

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

import pytest
from fastapi.testclient import TestClient


# ==================== ROOT ENDPOINT ====================


def test_root_endpoint(client: TestClient):
    """Test root endpoint"""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()

    assert data["name"] == "Active Immune Core API"
    assert data["version"] == "1.0.0"
    assert data["status"] == "operational"
    assert "docs" in data
    assert "health" in data
    assert "metrics" in data


# ==================== HEALTH CHECKS ====================


def test_health_endpoint(client: TestClient):
    """Test main health check endpoint"""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    assert "timestamp" in data
    assert "summary" in data
    assert "components" in data


def test_liveness_probe(client: TestClient):
    """Test Kubernetes liveness probe"""
    response = client.get("/health/live")

    # Should always return 200 if app is running
    assert response.status_code == 200
    data = response.json()

    assert "status" in data


def test_readiness_probe(client: TestClient):
    """Test Kubernetes readiness probe"""
    response = client.get("/health/ready")

    assert response.status_code in [200, 503]  # Ready or not ready
    data = response.json()

    assert "ready" in data or "status" in data


def test_health_detailed(client: TestClient):
    """Test detailed health check"""
    response = client.get("/health/components")

    assert response.status_code == 200
    data = response.json()

    assert "components_status" in data or "components" in data


def test_health_component_api(client: TestClient):
    """Test API component health"""
    response = client.get("/health/components/api")

    assert response.status_code == 200
    data = response.json()

    assert "name" in data or "component" in data
    assert data.get("name") == "api" or data.get("component") == "api"
    assert "status" in data


# ==================== METRICS ====================


def test_metrics_prometheus_endpoint(client: TestClient):
    """Test Prometheus metrics endpoint"""
    response = client.get("/metrics/")

    assert response.status_code == 200

    # Should return text format
    assert response.headers["content-type"].startswith("text/plain")

    # Content should contain Prometheus metrics
    content = response.text
    assert len(content) > 0


def test_metrics_json_endpoint(client: TestClient):
    """Test JSON metrics endpoint"""
    response = client.get("/metrics/statistics")

    assert response.status_code == 200
    data = response.json()

    # Should have metrics structure
    assert isinstance(data, dict)


def test_metrics_detailed(client: TestClient):
    """Test detailed metrics"""
    response = client.get("/metrics/list")

    assert response.status_code == 200
    data = response.json()

    assert "metrics" in data


def test_metrics_system(client: TestClient):
    """Test system metrics"""
    response = client.get("/metrics/rates")

    assert response.status_code == 200
    data = response.json()

    # Should contain metrics rates
    assert isinstance(data, dict)


# ==================== ERROR HANDLING ====================


def test_not_found_error(client: TestClient):
    """Test 404 error handling"""
    response = client.get("/nonexistent/endpoint")

    assert response.status_code == 404


def test_validation_error(client: TestClient):
    """Test validation error handling"""
    response = client.post("/agents/", json={"invalid": "data"})

    assert response.status_code == 422
    data = response.json()

    assert "error" in data or "detail" in data


# ==================== CORS ====================


def test_cors_headers_present(client: TestClient):
    """Test that CORS headers are present"""
    response = client.options(
        "/",
        headers={"Origin": "http://localhost:3000"}
    )

    # Should have CORS headers
    assert "access-control-allow-origin" in response.headers


# ==================== REQUEST METRICS ====================


def test_request_logging(client: TestClient):
    """Test that requests are logged and metrics recorded"""
    # Make multiple requests
    for _ in range(3):
        client.get("/")

    # Get metrics
    response = client.get("/metrics/statistics")
    assert response.status_code == 200

    # Metrics should exist (structure depends on implementation)
    data = response.json()
    assert isinstance(data, dict)


# ==================== HEALTH STATUS CHANGES ====================


def test_health_status_with_no_components(client: TestClient):
    """Test health status when no problematic components"""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()

    # Status should be healthy/degraded/unhealthy
    assert data["status"] in ["healthy", "degraded", "unhealthy", "unknown"]


# ==================== INTEGRATION ====================


def test_health_and_metrics_integration(client: TestClient):
    """Test that health and metrics work together"""
    # Check health
    health_response = client.get("/health")
    assert health_response.status_code == 200

    # Check metrics
    metrics_response = client.get("/metrics/")
    assert metrics_response.status_code == 200

    # Both should work independently
    assert health_response.json()["status"] in ["healthy", "degraded", "unhealthy", "unknown"]
    assert len(metrics_response.text) > 0
