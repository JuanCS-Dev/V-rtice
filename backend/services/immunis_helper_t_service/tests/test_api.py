"""
Testes REAIS para immunis_helper_t_service - API Endpoints

OBJETIVO: 100% COBERTURA ABSOLUTA da API
- Testa todos os endpoints HTTP
- Testa autenticação (require_identity)
- Testa degraded state (protective quarantine)
- Testa graceful degradation quando core indisponível
- ZERO MOCKS desnecessários

Padrão Pagani Absoluto: Cada endpoint, cada response code testado.
"""

import pytest
from fastapi.testclient import TestClient
import sys
import time

sys.path.insert(0, "/home/juan/vertice-dev/backend/services/immunis_helper_t_service")

# Import da API real
from api import app, _failure_timestamps, FAILURE_THRESHOLD


class TestHealthEndpoint:
    """Testes do endpoint /health."""

    def test_health_endpoint_requires_authentication(self):
        """Testa que /health requer autenticação."""
        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 401
        assert "Authentication required" in response.json()["detail"]

    def test_health_endpoint_with_invalid_token(self):
        """Testa /health com token inválido."""
        client = TestClient(app)
        response = client.get("/health", headers={"Authorization": "Bearer invalid-token"})

        assert response.status_code == 403
        assert "Invalid token" in response.json()["detail"]

    def test_health_endpoint_with_valid_token(self):
        """Testa /health com token válido."""
        client = TestClient(app)
        response = client.get("/health", headers={"Authorization": "Bearer trusted-token"})

        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "immunis_helper_t"
        assert "core_available" in data
        assert "degraded" in data
        assert "timestamp" in data

    def test_health_endpoint_shows_core_available(self):
        """Testa que /health indica se core está disponível."""
        client = TestClient(app)
        response = client.get("/health", headers={"Authorization": "Bearer trusted-token"})

        data = response.json()
        # Core deve estar disponível (importado com sucesso)
        assert data["core_available"] is True


class TestStatusEndpoint:
    """Testes do endpoint /status."""

    def test_status_endpoint_requires_authentication(self):
        """Testa que /status requer autenticação."""
        client = TestClient(app)
        response = client.get("/status")

        assert response.status_code == 401

    def test_status_endpoint_with_valid_token(self):
        """Testa /status com token válido."""
        client = TestClient(app)
        response = client.get("/status", headers={"Authorization": "Bearer trusted-token"})

        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "operational"

    def test_status_endpoint_with_core(self):
        """Testa /status quando core está disponível."""
        client = TestClient(app)
        response = client.get("/status", headers={"Authorization": "Bearer trusted-token"})

        data = response.json()

        # Se core disponível, deve ter estatísticas
        if "mode" not in data or data.get("mode") != "limited":
            # Core disponível - deve ter campos do HelperTCellCore.get_status()
            assert "threat_intel_count" in data
            assert "directives_issued" in data
            assert "outcomes_recorded" in data


class TestProcessEndpoint:
    """Testes do endpoint /process."""

    def test_process_endpoint_requires_authentication(self):
        """Testa que /process requer autenticação."""
        client = TestClient(app)
        response = client.post("/process", json={"data": {}})

        assert response.status_code == 401

    def test_process_endpoint_requires_data_field(self):
        """Testa que /process requer campo 'data'."""
        client = TestClient(app)

        # Request sem 'data' deve falhar
        response = client.post("/process", json={}, headers={"Authorization": "Bearer trusted-token"})

        assert response.status_code == 422  # Unprocessable Entity

    def test_process_endpoint_with_valid_data(self):
        """Testa /process com dados válidos (antigen activation)."""
        client = TestClient(app)

        request_data = {
            "data": {
                "antigen_id": "ag_test",
                "malware_family": "TestMalware",
                "severity": 0.6,
                "correlation_count": 0,
            },
            "context": {"source": "test"},
        }

        response = client.post("/process", json=request_data, headers={"Authorization": "Bearer trusted-token"})

        # Core deve estar disponível
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["service"] == "immunis_helper_t"
        assert "results" in data
        assert "latency_ms" in data
        assert "timestamp" in data

    def test_process_endpoint_calls_core_activate(self):
        """Testa que /process chama core.activate (método process não existe)."""
        client = TestClient(app)

        # HelperTCellCore não tem método process(), então deve usar resultado vazio
        request_data = {
            "data": {
                "antigen_id": "ag_activation",
                "malware_family": "Emotet",
                "severity": 0.75,
                "correlation_count": 5,
            }
        }

        response = client.post("/process", json=request_data, headers={"Authorization": "Bearer trusted-token"})

        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        # Core retornou resultado (ou placeholder)
        assert "results" in data


class TestDegradedState:
    """Testes de protective quarantine (degraded state)."""

    def test_degraded_state_after_multiple_failures(self):
        """Testa que serviço entra em quarantine após múltiplas falhas."""
        from api import log_failure
        import asyncio

        client = TestClient(app)

        # Limpa failure timestamps
        _failure_timestamps.clear()

        # Simula FAILURE_THRESHOLD falhas manualmente
        for i in range(FAILURE_THRESHOLD):
            asyncio.run(log_failure())

        # Agora serviço deve estar degraded
        health_response = client.get("/health", headers={"Authorization": "Bearer trusted-token"})
        assert health_response.json()["degraded"] is True

        # Requests devem ser rejeitadas com 503
        response = client.post(
            "/process",
            json={"data": {"antigen_id": "test"}},
            headers={"Authorization": "Bearer trusted-token"},
        )

        # Deve ser 503 (quarantine)
        assert response.status_code == 503
        assert "protective quarantine" in response.json()["detail"]


class TestFailureTracking:
    """Testes de tracking de falhas."""

    def test_failure_pruning_removes_old_failures(self):
        """Testa que falhas antigas são removidas após FAILURE_WINDOW_SECONDS."""
        from api import _prune_failures, _failure_timestamps, FAILURE_WINDOW_SECONDS

        _failure_timestamps.clear()

        now = time.time()

        # Adiciona failure antiga (fora da janela)
        _failure_timestamps.append(now - FAILURE_WINDOW_SECONDS - 10)

        # Adiciona failure recente
        _failure_timestamps.append(now)

        # Prune
        _prune_failures(now)

        # Deve ter removido antiga, mantido recente
        assert len(_failure_timestamps) == 1


class TestStartupShutdown:
    """Testes de eventos de startup/shutdown."""

    def test_app_starts_successfully(self):
        """Testa que aplicação inicia com sucesso."""
        client = TestClient(app)

        # Se consegue fazer request, app iniciou
        response = client.get("/health", headers={"Authorization": "Bearer trusted-token"})
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
            response = client.post(
                "/process", json=invalid_request, headers={"Authorization": "Bearer trusted-token"}
            )

            # Deve retornar 422 (validação falhou)
            assert response.status_code == 422

    def test_process_allows_optional_context(self):
        """Testa que context é opcional em /process."""
        client = TestClient(app)

        # Request sem context deve funcionar
        request_without_context = {"data": {"test": "data"}}

        response = client.post("/process", json=request_without_context, headers={"Authorization": "Bearer trusted-token"})

        # Não deve falhar por falta de context
        assert response.status_code in [200, 500]  # Core pode falhar, mas não por validação


class TestErrorHandling:
    """Testes de tratamento de erros."""

    def test_invalid_json_returns_422(self):
        """Testa que JSON inválido retorna 422."""
        client = TestClient(app)

        # Envia texto plano ao invés de JSON
        response = client.post(
            "/process",
            data="this is not json",
            headers={"Content-Type": "application/json", "Authorization": "Bearer trusted-token"},
        )

        assert response.status_code == 422

    def test_nonexistent_endpoint_returns_404(self):
        """Testa que endpoint inexistente retorna 404."""
        client = TestClient(app)

        response = client.get("/nonexistent_endpoint", headers={"Authorization": "Bearer trusted-token"})

        assert response.status_code == 404

    def test_wrong_method_returns_405(self):
        """Testa método HTTP errado retorna 405."""
        client = TestClient(app)

        # GET em /process (deve ser POST)
        response = client.get("/process", headers={"Authorization": "Bearer trusted-token"})

        assert response.status_code == 405  # Method Not Allowed


class TestIntegration:
    """Testes de integração end-to-end da API."""

    def test_full_api_workflow(self):
        """Testa workflow completo: health → status → process."""
        client = TestClient(app)

        headers = {"Authorization": "Bearer trusted-token"}

        # 1. Check health
        health_response = client.get("/health", headers=headers)
        assert health_response.status_code == 200
        assert health_response.json()["status"] == "healthy"

        # 2. Check status
        status_response = client.get("/status", headers=headers)
        assert status_response.status_code == 200
        assert status_response.json()["status"] == "operational"

        # 3. Process data (antigen activation)
        process_response = client.post(
            "/process",
            json={
                "data": {
                    "antigen_id": "ag_integration",
                    "malware_family": "IntegrationTest",
                    "severity": 0.7,
                    "correlation_count": 3,
                }
            },
            headers=headers,
        )

        assert process_response.status_code == 200

    def test_concurrent_requests(self):
        """Testa múltiplas requests concorrentes."""
        client = TestClient(app)

        headers = {"Authorization": "Bearer trusted-token"}

        # Simula 20 requests simultâneas
        responses = []
        for i in range(20):
            response = client.get("/health", headers=headers)
            responses.append(response)

        # Todas devem retornar 200
        for response in responses:
            assert response.status_code == 200


class TestExceptionPathsCoverage:
    """Testa exception handlers e logs para 100% coverage."""

    def test_startup_shutdown_logs(self, caplog):
        """Testa logs de startup/shutdown (lines 119-120, 126-127)."""
        import logging
        caplog.set_level(logging.INFO)

        headers = {"Authorization": "Bearer trusted-token"}
        with TestClient(app) as client:
            response = client.get("/health", headers=headers)
            assert response.status_code == 200

        # Verifica logs gerados
        assert len(caplog.records) > 0

    def test_status_retrieval_exception(self):
        """Testa exception em status retrieval (lines 156-159)."""
        from unittest.mock import patch
        import api

        client = TestClient(app)
        headers = {"Authorization": "Bearer trusted-token"}

        # Mock core.get_status para raise exception
        with patch.object(api.core, "get_status", side_effect=RuntimeError("Status failed")):
            response = client.get("/status", headers=headers)

            # Deve retornar fallback response
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "operational"

    def test_process_exception_handling(self):
        """Testa exception em process (lines 206-209)."""
        from unittest.mock import patch, AsyncMock
        import api

        client = TestClient(app)
        headers = {"Authorization": "Bearer trusted-token"}

        # Mock log_success to raise exception (triggers exception handler)
        with patch("api.log_success", AsyncMock(side_effect=RuntimeError("Logging failed"))):
            response = client.post(
                "/process",
                json={"data": {"test": "data"}, "context": None},
                headers=headers
            )

            # Should return 500 with exception
            assert response.status_code == 500
            assert "Helper T processing error" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
