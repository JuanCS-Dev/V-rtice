"""Constitutional Compliance Tests for active_immune_core.

Tests compliance with Constituição Vértice v3.0.

Author: Vértice Platform Team
"""

import pytest
from fastapi.testclient import TestClient


def test_metrics_endpoint_exists(client: TestClient):
    """Test that /metrics endpoint exists and returns Prometheus format."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers.get("content-type", "")

    content = response.text
    assert "vertice_service_uptime_seconds" in content


def test_health_live_endpoint(client: TestClient):
    """Test liveness probe endpoint."""
    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["alive"] is True


def test_health_ready_endpoint(client: TestClient):
    """Test readiness probe endpoint."""
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


def test_constitutional_metrics_exported(client: TestClient):
    """Test that constitutional metrics are being exported."""
    response = client.get("/metrics")
    content = response.text

    # DETER-AGENT metrics
    assert "vertice_constitutional_rule_satisfaction" in content
    assert "vertice_lazy_execution_index" in content


def test_no_p1_violations(client: TestClient):
    """Test that no P1 violations are being reported."""
    response = client.get("/metrics")
    content = response.text

    if "vertice_aletheia_hallucinations_total" in content:
        for line in content.split('\n'):
            if "vertice_aletheia_hallucinations_total" in line and not line.startswith("#"):
                assert " 0" in line or " 0.0" in line, "P1 Violation: Hallucinations detected!"
