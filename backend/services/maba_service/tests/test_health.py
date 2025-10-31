"""Health check endpoint tests.

Author: Vértice Platform Team
License: Proprietary
"""

from fastapi import status


class TestHealthEndpoints:
    """Test suite for health check endpoints."""

    def test_health_check_success(self, client, mock_maba_service):
        """Test health check returns 200 when service is healthy."""
        response = client.get("/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "components" in data

    def test_health_check_service_not_initialized(self, client):
        """Test health check fails when service not initialized."""
        from services.maba_service.api.routes import set_maba_service

        set_maba_service(None)

        response = client.get("/health")

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_root_endpoint(self, client, mock_maba_service):
        """Test root endpoint returns service information."""
        response = client.get("/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["service"] == "MABA - MAXIMUS Browser Agent"
        assert "version" in data
        assert "status" in data
        assert "endpoints" in data

    def test_metrics_endpoint(self, client):
        """Test metrics endpoint returns metrics information."""
        response = client.get("/metrics")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "metrics_port" in data
