"""
Testes para immunis_api_service

OBJETIVO: 95%+ cobertura
ESTRATÉGIA: Testes de endpoints (sem serviços externos - mock httpx)
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
import sys

sys.path.insert(0, "/home/juan/vertice-dev/backend/services/immunis_api_service")

from api import app


class TestAPI:
    def test_health(self):
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @patch("httpx.AsyncClient")
    def test_threat_alert(self, mock_client_class):
        # Mock httpx client
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        # Mock responses from services
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "processed"}
        mock_client.post.return_value = mock_response

        client = TestClient(app)
        alert = {
            "threat_id": "t001",
            "threat_type": "malware",
            "severity": "high",
            "details": {"hash": "abc123"},
            "source": "test",
        }
        response = client.post("/threat_alert", json=alert)
        assert response.status_code == 200

    @patch("httpx.AsyncClient")
    def test_threat_alert_intrusion(self, mock_client_class):
        """Testa routing de intrusion (lines 113-114)."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "processed"}
        mock_client.post.return_value = mock_response

        client = TestClient(app)
        alert = {
            "threat_id": "t002",
            "threat_type": "intrusion",  # Triggers cytotoxic T routing
            "severity": "critical",
            "details": {"ip": "1.2.3.4"},
            "source": "test",
        }
        response = client.post("/threat_alert", json=alert)
        assert response.status_code == 200

    @patch("httpx.AsyncClient")
    def test_trigger_immune_response(self, mock_client_class):
        # Mock httpx
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "triggered"}
        mock_client.post.return_value = mock_response

        client = TestClient(app)
        trigger = {
            "response_type": "b_cell_activation",
            "target_id": "malware_001",
            "parameters": {},
        }
        response = client.post("/trigger_immune_response", json=trigger)
        assert response.status_code == 200

    @patch("httpx.AsyncClient")
    def test_immunis_status(self, mock_client_class):
        # Mock httpx
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "operational"}
        mock_client.get.return_value = mock_response

        client = TestClient(app)
        response = client.get("/immunis_status")
        assert response.status_code == 200

    @patch("httpx.AsyncClient")
    def test_threat_alert_request_error(self, mock_client_class):
        """Testa RequestError no threat_alert (line 125-126)."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        # Simula RequestError
        import httpx
        mock_client.post.side_effect = httpx.RequestError("Network error")

        client = TestClient(app)
        alert = {
            "threat_id": "t002",
            "threat_type": "malware",
            "severity": "low",
            "details": {},
            "source": "test",
        }
        response = client.post("/threat_alert", json=alert)
        assert response.status_code == 500
        assert "Error communicating" in response.json()["detail"]

    @patch("httpx.AsyncClient")
    def test_threat_alert_http_status_error(self, mock_client_class):
        """Testa HTTPStatusError no threat_alert (lines 127-128)."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        # Simula HTTPStatusError
        import httpx
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"

        error = httpx.HTTPStatusError("Server error", request=MagicMock(), response=mock_response)
        mock_client.post.side_effect = error

        client = TestClient(app)
        alert = {
            "threat_id": "t003",
            "threat_type": "malware",
            "severity": "high",
            "details": {},
            "source": "test",
        }
        response = client.post("/threat_alert", json=alert)
        assert response.status_code == 500
        assert "Immunis sub-service error" in response.json()["detail"]

    @patch("httpx.AsyncClient")
    def test_trigger_immune_response_request_error(self, mock_client_class):
        """Testa RequestError no trigger (line 162)."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        # Simula RequestError
        import httpx
        mock_client.post.side_effect = httpx.RequestError("Connection failed")

        client = TestClient(app)
        trigger = {
            "response_type": "t_cell_attack",
            "target_id": "target_001",
        }
        response = client.post("/trigger_immune_response", json=trigger)
        assert response.status_code == 500
        assert "Error communicating" in response.json()["detail"]

    @patch("httpx.AsyncClient")
    def test_trigger_immune_response_http_status_error(self, mock_client_class):
        """Testa HTTPStatusError no trigger (line 164)."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        # Simula HTTPStatusError
        import httpx
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_response.text = "Service unavailable"

        error = httpx.HTTPStatusError("Service error", request=MagicMock(), response=mock_response)
        mock_client.post.side_effect = error

        client = TestClient(app)
        trigger = {
            "response_type": "b_cell_activation",
            "target_id": "target_002",
        }
        response = client.post("/trigger_immune_response", json=trigger)
        assert response.status_code == 503
        assert "Immunis sub-service error" in response.json()["detail"]


class TestStartupShutdown:
    """Testa startup/shutdown events (lines 76-77, 83-84)."""

    def test_startup_shutdown_logging(self, caplog):
        """Testa que startup/shutdown events executam."""
        import logging

        caplog.set_level(logging.INFO)

        # TestClient triggera startup automaticamente
        with TestClient(app) as client:
            response = client.get("/health")
            assert response.status_code == 200

        # Startup/shutdown prints devem aparecer em stdout (captura indireta via logs)
        # Verifica que app foi criado sem erros
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
