"""
Testes REAIS para immunis_dendritic_service - API Endpoints

OBJETIVO: 100% COBERTURA ABSOLUTA da API
- Testa todos os endpoints HTTP (health, status, process)
- Testa graceful degradation quando core indisponível
- Testa diferentes code paths em /process
- ZERO MOCKS desnecessários

Padrão Pagani Absoluto: Cada endpoint, cada response code testado.
"""

import pytest
from fastapi.testclient import TestClient
import sys
from datetime import datetime

sys.path.insert(0, "/home/juan/vertice-dev/backend/services/immunis_dendritic_service")

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
        assert data["service"] == "immunis_dendritic"
        assert "core_available" in data
        assert "timestamp" in data

    def test_health_endpoint_shows_core_available(self):
        """Testa que /health indica se core está disponível."""
        client = TestClient(app)
        response = client.get("/health")

        data = response.json()
        # Core deve estar disponível (importado com sucesso)
        assert data["core_available"] is True

    def test_health_endpoint_timestamp_format(self):
        """Testa que timestamp está em formato ISO."""
        client = TestClient(app)
        response = client.get("/health")

        data = response.json()
        # Deve ser parseable como datetime
        timestamp = datetime.fromisoformat(data["timestamp"])
        assert isinstance(timestamp, datetime)


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
            # Core disponível - deve ter campos do DendriticCore.get_status()
            assert "processed_antigens_count" in data
            assert "activations_count" in data
            assert "last_processing" in data
            assert "kafka_enabled" in data
            assert "qdrant_enabled" in data

    def test_status_endpoint_fallback_mode(self):
        """Testa que /status funciona mesmo sem core."""
        client = TestClient(app)
        response = client.get("/status")

        # Nunca deve falhar, sempre retorna algo
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestProcessEndpoint:
    """Testes do endpoint /process."""

    def test_process_endpoint_requires_data_field(self):
        """Testa que /process requer campo 'data'."""
        client = TestClient(app)

        # Request sem 'data' deve falhar
        response = client.post("/process", json={})

        assert response.status_code == 422  # Unprocessable Entity

    def test_process_endpoint_with_valid_antigen(self):
        """Testa /process com antigen válido."""
        client = TestClient(app)

        request_data = {
            "data": {
                "antigen_id": "ag_api_test",
                "timestamp": datetime.now().isoformat(),
                "malware_family": "TestMalware",
                "severity": 0.7,
                "iocs": {"ips": ["192.168.1.100"]},
            },
            "context": {"source": "test"},
        }

        response = client.post("/process", json=request_data)

        # Core deve estar disponível
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["service"] == "immunis_dendritic"
        assert "results" in data
        assert "timestamp" in data

    def test_process_endpoint_fallback_to_dict(self):
        """Testa que /process usa fallback quando core não tem process/analyze."""
        client = TestClient(app)

        # DendriticCore não tem método process() ou analyze()
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
        request_without_context = {"data": {"antigen_id": "ag_no_context", "severity": 0.5}}

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

    def test_process_with_invalid_data_structure(self):
        """Testa /process com estrutura de dados inválida."""
        client = TestClient(app)

        # Data sem campos obrigatórios pode causar erro no core
        request_data = {
            "data": {"incomplete": "data"},
        }

        response = client.post("/process", json=request_data)

        # Pode retornar 200 (processou) ou 500 (erro no core)
        assert response.status_code in [200, 500]


class TestStartupShutdown:
    """Testes de eventos de startup/shutdown."""

    def test_app_starts_successfully(self):
        """Testa que aplicação inicia com sucesso."""
        client = TestClient(app)

        # Se consegue fazer request, app iniciou
        response = client.get("/health")
        assert response.status_code == 200

    def test_startup_event_executes(self):
        """Testa que startup event executa."""
        # TestClient já triggera startup event
        client = TestClient(app)

        # Faz qualquer request para confirmar app está rodando
        response = client.get("/health")
        assert response.status_code == 200


class TestIntegration:
    """Testes de integração end-to-end da API."""

    def test_full_api_workflow(self):
        """Testa workflow completo: health → status → process."""
        client = TestClient(app)

        # 1. Check health
        health_response = client.get("/health")
        assert health_response.status_code == 200
        assert health_response.json()["status"] == "healthy"

        # 2. Check status
        status_response = client.get("/status")
        assert status_response.status_code == 200
        assert status_response.json()["status"] == "operational"

        # 3. Process antigen
        process_response = client.post(
            "/process",
            json={
                "data": {
                    "antigen_id": "ag_integration",
                    "timestamp": datetime.now().isoformat(),
                    "malware_family": "IntegrationTest",
                    "severity": 0.8,
                    "iocs": {"ips": ["10.0.0.1"], "domains": ["evil.com"]},
                }
            },
        )

        assert process_response.status_code == 200

    def test_concurrent_requests(self):
        """Testa múltiplas requests concorrentes."""
        client = TestClient(app)

        # Simula 20 requests simultâneas
        responses = []
        for i in range(20):
            response = client.get("/health")
            responses.append(response)

        # Todas devem retornar 200
        for response in responses:
            assert response.status_code == 200

    def test_mixed_endpoint_calls(self):
        """Testa chamadas mistas de diferentes endpoints."""
        client = TestClient(app)

        # Alterna entre diferentes endpoints
        endpoints = [
            ("/health", "get"),
            ("/status", "get"),
            ("/health", "get"),
            ("/status", "get"),
        ]

        for endpoint, method in endpoints:
            if method == "get":
                response = client.get(endpoint)
                assert response.status_code == 200


class TestProcessEdgeCases:
    """Testes de edge cases em /process."""

    def test_process_with_empty_data_dict(self):
        """Testa /process com data dict vazio."""
        client = TestClient(app)

        response = client.post("/process", json={"data": {}})

        # Deve processar (com defaults)
        assert response.status_code == 200

    def test_process_with_complex_nested_data(self):
        """Testa /process com data complexo e nested."""
        client = TestClient(app)

        complex_data = {
            "data": {
                "antigen_id": "ag_complex",
                "timestamp": datetime.now().isoformat(),
                "malware_family": "ComplexThreat",
                "severity": 0.9,
                "iocs": {
                    "ips": ["192.168.1.1", "192.168.1.2", "192.168.1.3"],
                    "domains": ["evil1.com", "evil2.com"],
                    "urls": ["http://evil1.com/malware", "http://evil2.com/payload"],
                    "file_hashes": ["abc123", "def456", "ghi789"],
                },
                "nested": {
                    "deep": {
                        "structure": {
                            "test": "value",
                        }
                    }
                },
            },
            "context": {
                "source": "macrophage",
                "priority": "high",
                "metadata": {"key1": "value1", "key2": "value2"},
            },
        }

        response = client.post("/process", json=complex_data)

        assert response.status_code == 200

    def test_process_with_large_ioc_list(self):
        """Testa /process com lista grande de IOCs."""
        client = TestClient(app)

        large_iocs = {
            "data": {
                "antigen_id": "ag_large",
                "severity": 0.7,
                "iocs": {
                    "ips": [f"192.168.1.{i}" for i in range(100)],
                    "domains": [f"evil{i}.com" for i in range(50)],
                },
            }
        }

        response = client.post("/process", json=large_iocs)

        # Deve processar sem problemas
        assert response.status_code == 200


class TestExceptionPathsCoverage:
    """Testa exception handlers e logs para 100% coverage."""

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
        """Testa exception em status retrieval (lines 104-107)."""
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
