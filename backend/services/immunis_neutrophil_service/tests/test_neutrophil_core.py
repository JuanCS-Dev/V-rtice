"""
Testes REAIS para immunis_neutrophil_service Core

OBJETIVO: 95%+ cobertura com testes de produção
ESTRATÉGIA: Testes REAIS sem RTE (mock httpx apenas)
- Testar TTL/lifecycle (ephemeral, 24h)
- Testar rapid response actions
- Testar self-destruct
- Mock APENAS httpx.AsyncClient para RTE

Padrão Pagani Absoluto: Testes REAIS, mocks CIRÚRGICOS apenas para infra externa.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
import sys

sys.path.insert(0, "/home/juan/vertice-dev/backend/services/immunis_neutrophil_service")

from neutrophil_core import NeutrophilCore


class TestNeutrophilLifecycle:
    """Testa lifecycle ephemeral (TTL 24h)."""

    def test_neutrophil_init(self):
        """Testa inicialização do Neutrophil."""
        neutrophil = NeutrophilCore(
            neutrophil_id="test-neutrophil-123",
            ttl_hours=24,
            rte_endpoint="http://test-rte:8003",
        )

        assert neutrophil.neutrophil_id == "test-neutrophil-123"
        assert neutrophil.rte_endpoint == "http://test-rte:8003"
        assert neutrophil.status == "active"
        assert isinstance(neutrophil.birth_time, datetime)
        assert isinstance(neutrophil.death_time, datetime)
        assert neutrophil.threats_engaged == []
        assert neutrophil.actions_taken == []

    def test_neutrophil_custom_ttl(self):
        """Testa TTL customizado."""
        neutrophil = NeutrophilCore(
            neutrophil_id="test-short-lived",
            ttl_hours=1,  # 1 hora apenas
        )

        expected_death = neutrophil.birth_time + timedelta(hours=1)

        # Tolera diferença de 1 segundo
        assert abs((neutrophil.death_time - expected_death).total_seconds()) < 1

    def test_is_alive_within_ttl(self):
        """Testa que neutrophil está alive dentro do TTL."""
        neutrophil = NeutrophilCore(
            neutrophil_id="test-alive",
            ttl_hours=24,
        )

        assert neutrophil.is_alive() is True

    def test_is_alive_expired(self):
        """Testa que neutrophil expira após TTL."""
        neutrophil = NeutrophilCore(
            neutrophil_id="test-expired",
            ttl_hours=1,
        )

        # Força death_time no passado
        neutrophil.death_time = datetime.now() - timedelta(hours=1)

        assert neutrophil.is_alive() is False

    def test_remaining_lifetime_seconds(self):
        """Testa cálculo de tempo restante."""
        neutrophil = NeutrophilCore(
            neutrophil_id="test-lifetime",
            ttl_hours=24,
        )

        remaining = neutrophil.remaining_lifetime_seconds()

        # Deve ser aproximadamente 24h (86400s), com margem de erro
        assert 86300 < remaining < 86500  # ~24h

    def test_remaining_lifetime_zero_when_expired(self):
        """Testa que lifetime retorna 0.0 quando expired."""
        neutrophil = NeutrophilCore(
            neutrophil_id="test-expired-zero",
            ttl_hours=1,
        )

        # Força death_time no passado
        neutrophil.death_time = datetime.now() - timedelta(hours=1)

        remaining = neutrophil.remaining_lifetime_seconds()

        assert remaining == 0.0


class TestRapidResponse:
    """Testa rapid response actions."""

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_initiate_rapid_response_critical_malware(self, mock_client_class):
        """Testa rapid response para malware crítico."""
        # Mock httpx AsyncClient
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        # Mock RTE response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "action_executed",
            "action_id": "rte-action-123",
        }
        mock_client.post.return_value = mock_response

        neutrophil = NeutrophilCore(neutrophil_id="test-neutrophil")

        threat_details = {
            "host_id": "host-abc-123",
            "file_hash": "abc123def456",
        }

        result = await neutrophil.initiate_rapid_response(
            threat_id="threat-malware-001",
            threat_type="malware",
            severity="critical",
            details=threat_details,
        )

        # Deve ter respondido com sucesso
        assert result["threat_id"] == "threat-malware-001"
        assert result["threat_type"] == "malware"
        assert result["severity"] == "critical"
        assert result["action_taken"]["type"] == "isolate_and_quarantine"
        assert result["action_taken"]["target"] == "host-abc-123"
        assert "response_time_ms" in result

        # Deve ter registrado no histórico
        assert len(neutrophil.threats_engaged) == 1
        assert "isolate_and_quarantine" in neutrophil.actions_taken

        # RTE deve ter sido chamado
        mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_initiate_rapid_response_high_intrusion(self, mock_client_class):
        """Testa rapid response para intrusion high."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "action_executed"}
        mock_client.post.return_value = mock_response

        neutrophil = NeutrophilCore(neutrophil_id="test-neutrophil")

        threat_details = {
            "ip_address": "192.168.1.100",
            "port": 22,
        }

        result = await neutrophil.initiate_rapid_response(
            threat_id="threat-intrusion-001",
            threat_type="intrusion",
            severity="high",
            details=threat_details,
        )

        # Deve ter escolhido block_network
        assert result["action_taken"]["type"] == "block_network"
        assert result["action_taken"]["target"] == "192.168.1.100"
        assert result["action_taken"]["duration"] == "1h"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_initiate_rapid_response_process_anomaly(self, mock_client_class):
        """Testa rapid response para process anomaly."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "action_executed"}
        mock_client.post.return_value = mock_response

        neutrophil = NeutrophilCore(neutrophil_id="test-neutrophil")

        threat_details = {
            "process_id": 12345,
            "process_name": "evil.exe",
        }

        result = await neutrophil.initiate_rapid_response(
            threat_id="threat-process-001",
            threat_type="process_anomaly",
            severity="medium",
            details=threat_details,
        )

        # Deve ter escolhido kill_process
        assert result["action_taken"]["type"] == "kill_process"
        assert result["action_taken"]["target"] == 12345

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_initiate_rapid_response_low_severity(self, mock_client_class):
        """Testa rapid response para severity baixa."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "action_executed"}
        mock_client.post.return_value = mock_response

        neutrophil = NeutrophilCore(neutrophil_id="test-neutrophil")

        threat_details = {
            "target": "suspicious-host-456",
        }

        result = await neutrophil.initiate_rapid_response(
            threat_id="threat-low-001",
            threat_type="unknown",
            severity="low",
            details=threat_details,
        )

        # Deve ter escolhido monitor_intensively (default)
        assert result["action_taken"]["type"] == "monitor_intensively"
        assert result["action_taken"]["target"] == "suspicious-host-456"

    @pytest.mark.asyncio
    async def test_initiate_rapid_response_expired_neutrophil(self):
        """Testa que neutrophil expired NÃO responde."""
        neutrophil = NeutrophilCore(neutrophil_id="test-expired", ttl_hours=1)

        # Força expired
        neutrophil.death_time = datetime.now() - timedelta(hours=1)

        result = await neutrophil.initiate_rapid_response(
            threat_id="threat-after-death",
            threat_type="malware",
            severity="critical",
            details={},
        )

        # Deve retornar expired
        assert result["status"] == "expired"
        assert result["neutrophil_id"] == "test-expired"

        # NÃO deve ter registrado
        assert len(neutrophil.threats_engaged) == 0

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_execute_via_rte_http_error(self, mock_client_class):
        """Testa fallback quando RTE retorna erro HTTP."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        # RTE retorna 500
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_client.post.return_value = mock_response

        neutrophil = NeutrophilCore(neutrophil_id="test-neutrophil")

        result = await neutrophil.initiate_rapid_response(
            threat_id="threat-rte-fail",
            threat_type="malware",
            severity="critical",
            details={"host_id": "host-123"},
        )

        # Deve ter registrado a tentativa (mesmo com erro)
        assert result["threat_id"] == "threat-rte-fail"
        assert result["result"]["success"] is False
        assert "error" in result["result"]

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_execute_via_rte_exception(self, mock_client_class):
        """Testa fallback quando RTE lança exception."""
        mock_client_class.side_effect = Exception("Connection refused")

        neutrophil = NeutrophilCore(neutrophil_id="test-neutrophil")

        result = await neutrophil.initiate_rapid_response(
            threat_id="threat-rte-exception",
            threat_type="malware",
            severity="critical",
            details={"host_id": "host-123"},
        )

        # Deve ter registrado fallback
        assert result["result"]["success"] is False
        assert "Connection refused" in result["result"]["error"]


class TestSelfDestruct:
    """Testa self-destruction."""

    @pytest.mark.asyncio
    async def test_self_destruct_active_neutrophil(self):
        """Testa self-destruct de neutrophil ativo."""
        neutrophil = NeutrophilCore(neutrophil_id="test-destruct")

        # Adiciona alguns engagements
        neutrophil.threats_engaged.append({"threat_id": "t1"})
        neutrophil.threats_engaged.append({"threat_id": "t2"})
        neutrophil.actions_taken.append("isolate")
        neutrophil.actions_taken.append("block")

        result = await neutrophil.self_destruct()

        # Deve ter retornado summary
        assert result["neutrophil_id"] == "test-destruct"
        assert result["threats_engaged"] == 2
        assert result["actions_taken"] == 2
        assert "lifetime_hours" in result
        assert "action_breakdown" in result

        # Status deve ser destroyed
        assert neutrophil.status == "destroyed"

        # Deve ter limpado memoria
        assert len(neutrophil.threats_engaged) == 0
        assert len(neutrophil.actions_taken) == 0

    @pytest.mark.asyncio
    async def test_self_destruct_multiple_times(self):
        """Testa self-destruct múltiplas vezes (sem check de already_destroyed)."""
        neutrophil = NeutrophilCore(neutrophil_id="test-already-destroyed")

        # Primeira destruição
        result1 = await neutrophil.self_destruct()
        assert neutrophil.status == "destroyed"

        # Segunda destruição (não há check, então executa novamente)
        result2 = await neutrophil.self_destruct()

        # Ambas retornam summary válido
        assert result2["neutrophil_id"] == "test-already-destroyed"


class TestResponseStatus:
    """Testa get_response_status."""

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_get_response_status_found(self, mock_client_class):
        """Testa get_response_status quando threat_id existe."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "action_executed"}
        mock_client.post.return_value = mock_response

        neutrophil = NeutrophilCore(neutrophil_id="test-neutrophil")

        # Cria um engagement
        await neutrophil.initiate_rapid_response(
            threat_id="threat-123",
            threat_type="malware",
            severity="high",
            details={"host_id": "host-1"},
        )

        # Busca status
        status = await neutrophil.get_response_status("threat-123")

        assert status is not None
        assert status["threat_id"] == "threat-123"

    @pytest.mark.asyncio
    async def test_get_response_status_not_found(self):
        """Testa get_response_status quando threat_id NÃO existe."""
        neutrophil = NeutrophilCore(neutrophil_id="test-neutrophil")

        status = await neutrophil.get_response_status("nonexistent-threat")

        assert status is None


class TestGetStatus:
    """Testa get_status."""

    @pytest.mark.asyncio
    async def test_get_status_active(self):
        """Testa get_status de neutrophil ativo."""
        neutrophil = NeutrophilCore(neutrophil_id="test-status")

        status = await neutrophil.get_status()

        assert status["neutrophil_id"] == "test-status"
        assert status["status"] == "active"
        assert status["is_alive"] is True
        assert "remaining_lifetime_seconds" in status
        assert status["threats_engaged"] == 0
        assert status["actions_taken"] == 0

    @pytest.mark.asyncio
    async def test_get_status_expired(self):
        """Testa get_status de neutrophil expired."""
        neutrophil = NeutrophilCore(neutrophil_id="test-expired")

        # Força expired
        neutrophil.death_time = datetime.now() - timedelta(hours=1)

        status = await neutrophil.get_status()

        assert status["is_alive"] is False
        assert status["remaining_lifetime_seconds"] == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
