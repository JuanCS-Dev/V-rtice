"""Constitutional Compliance Tests."""
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    from fastapi import FastAPI
    from shared.metrics_exporter import MetricsExporter
    from shared.health_checks import ConstitutionalHealthCheck
    app = FastAPI()
    metrics_exporter = MetricsExporter(service_name="auditory_cortex_service", version="1.0.0")
    app.include_router(metrics_exporter.create_router())
    health_checker = ConstitutionalHealthCheck(service_name="auditory_cortex_service")
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
    assert "vertice_service_uptime_seconds" in response.text

def test_health_live_endpoint(client: TestClient):
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_constitutional_metrics_exported(client: TestClient):
    response = client.get("/metrics")
    assert "vertice_constitutional_rule_satisfaction" in response.text
