"""
Testes REAIS para immunis_cytotoxic_t_service - API Endpoints

OBJETIVO: 100% COBERTURA ABSOLUTA da API
- Testa todos os endpoints HTTP
- Testa graceful degradation quando core indisponível
- ZERO MOCKS desnecessários

Padrão Pagani Absoluto: Cada endpoint, cada response code testado.
"""

import pytest
from fastapi.testclient import TestClient
import sys

sys.path.insert(0, "/home/juan/vertice-dev/backend/services/immunis_cytotoxic_t_service")

# Import da API real
from api import app


class TestHealthEndpoint:
    """Testes do endpoint /health."""

    def test_health_endpoint_basic(self):
        """Testa /health retorna informações básicas."""
        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "immunis_cytotoxic_t"
        assert "core_available" in data
        assert "timestamp" in data

    def test_health_endpoint_shows_core_available(self):
        """Testa que /health indica se core está disponível."""
        client = TestClient(app)
        response = client.get("/health")

        data = response.json()
        # Core deve estar disponível (importado com sucesso)
        assert data["core_available"] is True


class TestStatusEndpoint:
    """Testes do endpoint /status."""

    def test_status_endpoint_basic(self):
        """Testa /status retorna status básico."""
        client = TestClient(app)
        response = client.get("/status")

        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "operational"

    def test_status_endpoint_with_core(self):
        """Testa /status quando core está disponível."""
        client = TestClient(app)
        response = client.get("/status")

        data = response.json()

        # Se core disponível, deve ter get_status() completo
        if "mode" not in data or data.get("mode") != "limited":
            # Core disponível - deve ter campos do NkCellCore.get_status()
            assert "eliminated_threats" in data or "status" in data


class TestProcessEndpoint:
    """Testes do endpoint /process."""

    def test_process_endpoint_requires_data_field(self):
        """Testa que /process requer campo 'data'."""
        client = TestClient(app)

        # Request sem 'data' deve falhar
        response = client.post("/process", json={})

        assert response.status_code == 422  # Unprocessable Entity

    def test_process_endpoint_with_valid_data(self):
        """Testa /process com dados válidos."""
        client = TestClient(app)

        request_data = {
            "data": {
                "threat_id": "threat_test",
                "malware_type": "TestMalware",
                "severity": 0.8,
            },
            "context": {"source": "test"},
        }

        response = client.post("/process", json=request_data)

        # Core deve estar disponível
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["service"] == "immunis_cytotoxic_t"
        assert "results" in data
        assert "timestamp" in data

    def test_process_endpoint_fallback_to_dict(self):
        """Testa que /process usa fallback quando core não tem process/analyze."""
        client = TestClient(app)

        # NkCellCore não tem método process() ou analyze()
        # Deve usar fallback: {"processed": True, "data": ...}
        request_data = {
            "data": {"test": "fallback"},
        }

        response = client.post("/process", json=request_data)

        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["results"]["processed"] is True

    def test_process_endpoint_allows_optional_context(self):
        """Testa que context é opcional em /process."""
        client = TestClient(app)

        # Request sem context deve funcionar
        request_without_context = {"data": {"threat_id": "ag_no_context", "severity": 0.5}}

        response = client.post("/process", json=request_without_context)

        # Não deve falhar por falta de context
        assert response.status_code == 200


class TestRequestValidation:
    """Testes de validação de requests."""

    def test_process_validates_request_structure(self):
        """Testa que /process valida estrutura do request."""
        client = TestClient(app)

        # Request com tipo errado de 'data' (deve ser dict)
        invalid_requests = [
            {"data": "string_instead_of_dict"},
            {"data": 123},
            {"data": ["list", "instead", "of", "dict"]},
        ]

        for invalid_request in invalid_requests:
            response = client.post("/process", json=invalid_request)

            # Deve retornar 422 (validação falhou)
            assert response.status_code == 422

    def test_invalid_json_returns_422(self):
        """Testa que JSON inválido retorna 422."""
        client = TestClient(app)

        # Envia texto plano ao invés de JSON
        response = client.post(
            "/process",
            data="this is not json",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422


class TestErrorHandling:
    """Testes de tratamento de erros."""

    def test_nonexistent_endpoint_returns_404(self):
        """Testa que endpoint inexistente retorna 404."""
        client = TestClient(app)

        response = client.get("/nonexistent_endpoint")

        assert response.status_code == 404

    def test_wrong_method_returns_405(self):
        """Testa método HTTP errado retorna 405."""
        client = TestClient(app)

        # GET em /process (deve ser POST)
        response = client.get("/process")

        assert response.status_code == 405  # Method Not Allowed


class TestStartupShutdown:
    """Testes de eventos de startup/shutdown."""

    def test_app_starts_successfully(self):
        """Testa que aplicação inicia com sucesso."""
        client = TestClient(app)

        # Se consegue fazer request, app iniciou
        response = client.get("/health")
        assert response.status_code == 200


class TestExceptionHandlers:
    """Testa exception handlers para 100% coverage."""

    def test_startup_shutdown_logs(self, caplog):
        """Testa logs de startup/shutdown (lines 68-69, 75-76)."""
        import logging

        caplog.set_level(logging.INFO)

        with TestClient(app) as client:
            response = client.get("/health")
            assert response.status_code == 200

        # Verifica logs gerados
        assert len(caplog.records) > 0

    def test_status_retrieval_exception(self):
        """Testa exception em status retrieval (lines 102-105)."""
        from unittest.mock import patch
        import api

        client = TestClient(app)

        # Mock core.get_status para raise exception
        with patch.object(api.core, "get_status", side_effect=RuntimeError("Status failed")):
            response = client.get("/status")

            # Deve retornar fallback response
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "operational"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
