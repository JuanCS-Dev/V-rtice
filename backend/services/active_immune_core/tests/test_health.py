"""Health check tests - Fase 1 validation"""

import pytest
from fastapi import status


class TestHealthEndpoints:
    """Test health and readiness endpoints"""

    def test_health_endpoint_returns_200(self, client):
        """Test that /health returns 200 OK"""
        response = client.get("/health")

        assert response.status_code == status.HTTP_200_OK

    def test_health_response_schema(self, client):
        """Test that /health response has correct schema"""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        assert "agents_active" in data
        assert "lymphnodes_active" in data

        assert isinstance(data["agents_active"], int)
        assert isinstance(data["lymphnodes_active"], int)

    def test_readiness_endpoint_returns_200(self, client):
        """Test that /ready returns 200 OK"""
        response = client.get("/ready")

        assert response.status_code == status.HTTP_200_OK

    def test_readiness_response_schema(self, client):
        """Test that /ready response has correct schema"""
        response = client.get("/ready")
        data = response.json()

        assert "status" in data
        assert data["status"] == "ready"

    def test_metrics_endpoint_accessible(self, client):
        """Test that /metrics endpoint is accessible"""
        response = client.get("/metrics")

        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "text/plain; version=0.0.4; charset=utf-8"

    def test_metrics_contains_prometheus_format(self, client):
        """Test that /metrics returns Prometheus format"""
        response = client.get("/metrics")
        content = response.text

        # Check for Prometheus metric format
        assert "# HELP" in content or "# TYPE" in content


class TestRootEndpoint:
    """Test root endpoint"""

    def test_root_returns_service_info(self, client):
        """Test that / returns service information"""
        response = client.get("/")

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "operational"

    def test_root_contains_links(self, client):
        """Test that / contains documentation links"""
        response = client.get("/")
        data = response.json()

        assert "docs" in data
        assert "health" in data
        assert "metrics" in data


class TestDocumentationEndpoints:
    """Test API documentation endpoints"""

    def test_openapi_endpoint_accessible(self, client):
        """Test that /openapi.json is accessible"""
        response = client.get("/openapi.json")

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert data["info"]["title"] == "Active Immune Core Service"
        assert data["info"]["version"] == "1.0.0"

    def test_docs_endpoint_accessible(self, client):
        """Test that /docs (Swagger UI) is accessible"""
        response = client.get("/docs")

        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]

    def test_redoc_endpoint_accessible(self, client):
        """Test that /redoc (ReDoc) is accessible"""
        response = client.get("/redoc")

        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]


class TestAgentEndpoints:
    """Test agent management endpoints (Fase 1 - empty state)"""

    def test_list_agents_returns_empty(self, client):
        """Test that /agents returns empty list (no agents yet)"""
        response = client.get("/agents")

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "total" in data
        assert "agents" in data
        assert data["total"] == 0
        assert data["agents"] == []

    def test_get_agent_returns_404(self, client):
        """Test that /agents/{id} returns 404 (no agents yet)"""
        response = client.get("/agents/nonexistent-id")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_clone_agents_returns_501(self, client):
        """Test that /agents/clone returns 501 (not implemented yet)"""
        response = client.post(
            "/agents/clone",
            json={
                "tipo": "macrofago",
                "especializacao": "test",
                "quantidade": 5,
            },
        )

        assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED


class TestCoordinationEndpoints:
    """Test coordination endpoints (Fase 3 - not implemented)"""

    def test_list_lymphnodes_returns_501(self, client):
        """Test that /lymphnodes returns 501 (not implemented yet)"""
        response = client.get("/lymphnodes")

        assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED

    def test_get_homeostasis_returns_501(self, client):
        """Test that /homeostasis returns 501 (not implemented yet)"""
        response = client.get("/homeostasis")

        assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED
