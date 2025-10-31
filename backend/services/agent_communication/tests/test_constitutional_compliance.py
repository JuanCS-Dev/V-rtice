"""Constitutional Compliance Tests.

Tests compliance with Constituição Vértice v3.0.

Author: Vértice Platform Team
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client."""
    from fastapi import FastAPI
    from shared.metrics_exporter import MetricsExporter
    from shared.health_checks import ConstitutionalHealthCheck

    app = FastAPI()
    metrics_exporter = MetricsExporter(service_name="agent_communication", version="1.0.0")
    app.include_router(metrics_exporter.create_router())

    health_checker = ConstitutionalHealthCheck(service_name="agent_communication")
    health_checker.mark_startup_complete()

    @app.get("/health/live")
    async def health_live():
        return await health_checker.liveness_check()

    @app.get("/health/ready")
    async def health_ready():
        return await health_checker.readiness_check()

    return TestClient(app)


def test_metrics_endpoint_exists(client: TestClient):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers.get("content-type", "")
    assert "vertice_service_uptime_seconds" in response.text


def test_health_live_endpoint(client: TestClient):
    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["alive"] is True


def test_health_ready_endpoint(client: TestClient):
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


def test_constitutional_metrics_exported(client: TestClient):
    response = client.get("/metrics")
    content = response.text
    assert "vertice_constitutional_rule_satisfaction" in content
    assert "vertice_lazy_execution_index" in content


def test_no_p1_violations(client: TestClient):
    response = client.get("/metrics")
    content = response.text
    if "vertice_aletheia_hallucinations_total" in content:
        for line in content.split('\n'):
            if "vertice_aletheia_hallucinations_total" in line and not line.startswith("#"):
                assert " 0" in line or " 0.0" in line, "P1 Violation: Hallucinations detected!"
