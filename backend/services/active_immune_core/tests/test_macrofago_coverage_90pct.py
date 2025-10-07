"""Macrophage Coverage Tests - Additional tests to reach 90%

This module contains additional focused tests to reach 90% coverage target.

Current: 87%
Target: 90%
Gap: 3%

Missing lines identified:
- 93-126: Patrol flow (connections → investigation → neutralization)
- 136-137: _scan_network_connections without HTTP session
- 224: High ephemeral port scoring (_calcular_suspeita)
- 229: Unusual protocol scoring
- 259-260: executar_investigacao without HTTP session
- 415-416: executar_neutralizacao without HTTP session
"""

import asyncio
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from active_immune_core.agents import AgentStatus, AgentType
from active_immune_core.agents.macrofago import MacrofagoDigital


# ==================== FIXTURES ====================


@pytest_asyncio.fixture
async def macrofago():
    """Create and initialize Macrophage agent"""
    mac = MacrofagoDigital(
        area_patrulha="coverage_90pct_zone",
        kafka_bootstrap="localhost:9092",
        redis_url="redis://localhost:6379",
    )

    # Initialize to create HTTP session
    await mac.iniciar()
    await asyncio.sleep(0.5)

    yield mac

    if mac._running:
        await mac.parar()


@pytest.fixture
def suspicious_connection():
    """Suspicious network connection"""
    return {
        "id": "conn_suspicious_001",
        "src_ip": "10.0.1.50",
        "src_port": 45123,
        "dst_ip": "198.51.100.42",
        "dst_port": 4444,  # Metasploit default
        "protocol": "TCP",
        "bytes_sent": 15000000,  # 15MB
        "state": "established",
    }


@pytest.fixture
def normal_connection():
    """Normal network connection"""
    return {
        "id": "conn_normal_001",
        "src_ip": "10.0.1.60",
        "src_port": 55000,
        "dst_ip": "93.184.216.34",  # example.com
        "dst_port": 443,  # HTTPS
        "protocol": "TCP",
        "bytes_sent": 5000,
        "state": "established",
    }


# ==================== PATROL FLOW TESTS ====================


class TestMacrofagoPatrolFlow:
    """Tests for complete patrol flow (Lines 93-126)"""

    @pytest.mark.asyncio
    async def test_patrol_detects_and_neutralizes_threat(
        self, macrofago, suspicious_connection
    ):
        """
        Test complete patrol flow: scan → detect → investigate → neutralize.

        Coverage: Lines 93-126 (patrol complete flow)

        Scenario:
        - Patrol finds suspicious connection
        - Calculates high suspicion score
        - Investigates and confirms threat
        - Neutralizes with phagocytosis
        """
        # ARRANGE: Mock RTE connections response
        mock_connections_response = AsyncMock()
        mock_connections_response.status = 200
        mock_connections_response.json = AsyncMock(
            return_value={"connections": [suspicious_connection]}
        )

        # Mock IP Intel response (high threat)
        mock_intel_response = AsyncMock()
        mock_intel_response.status = 200
        mock_intel_response.json = AsyncMock(
            return_value={
                "reputation": {"score": 9},
                "malicious": True,
                "blocklists": ["spamhaus", "malwaredomains"],
            }
        )

        # Mock RTE block response
        mock_block_response = AsyncMock()
        mock_block_response.status = 200
        mock_block_response.text = AsyncMock(return_value="OK")

        # ACT: Execute patrol with ethical AI bypass
        with patch.object(
            macrofago, "_validate_ethical", new_callable=AsyncMock, return_value=True
        ):
            with patch.object(macrofago._http_session, "get") as mock_get:
                with patch.object(macrofago._http_session, "post") as mock_post:

                    def post_side_effect(url, **kwargs):
                        """Return different mocks based on URL"""
                        mock = AsyncMock()
                        if "/analyze" in str(url):
                            mock.__aenter__.return_value = mock_intel_response
                        elif "/block" in str(url):
                            mock.__aenter__.return_value = mock_block_response
                        return mock

                    mock_get.return_value.__aenter__.return_value = (
                        mock_connections_response
                    )
                    mock_post.side_effect = post_side_effect

                    await macrofago.patrulhar()

        # ASSERT: Threat should be phagocytosed
        assert len(macrofago.fagocitados) > 0, "Should phagocytose threat"
        assert (
            suspicious_connection["dst_ip"] in macrofago.fagocitados
        ), "Should phagocytose suspicious IP"
        assert macrofago.conexoes_escaneadas == 1, "Should scan 1 connection"


    @pytest.mark.asyncio
    async def test_patrol_skips_normal_connections(
        self, macrofago, normal_connection
    ):
        """
        Test patrol flow with normal connection (low suspicion score).

        Coverage: Lines 93-108 (patrol with low suspicion)

        Scenario:
        - Patrol finds normal connection
        - Calculates low suspicion score
        - Skips investigation (below threshold)
        """
        # ARRANGE: Mock RTE response with normal connection
        mock_connections_response = AsyncMock()
        mock_connections_response.status = 200
        mock_connections_response.json = AsyncMock(
            return_value={"connections": [normal_connection]}
        )

        fagocitados_before = len(macrofago.fagocitados)

        # ACT
        with patch.object(macrofago._http_session, "get") as mock_get:
            mock_get.return_value.__aenter__.return_value = mock_connections_response

            await macrofago.patrulhar()

        # ASSERT: Normal connection should not be phagocytosed
        assert (
            len(macrofago.fagocitados) == fagocitados_before
        ), "Should not phagocytose normal connection"
        assert macrofago.conexoes_escaneadas == 1, "Should still scan connection"


# ==================== HTTP SESSION NOT INITIALIZED TESTS ====================


class TestMacrofagoSessionErrors:
    """Tests for HTTP session not initialized paths"""

    @pytest.mark.asyncio
    async def test_scan_network_without_session(self):
        """
        Test _scan_network_connections without HTTP session.

        Coverage: Lines 136-137

        Scenario:
        - Macrophage not initialized (no HTTP session)
        - Should log warning and return empty list
        """
        # ARRANGE: Create macrophage without initialization
        mac = MacrofagoDigital(area_patrulha="test_zone")

        # ACT: Scan without HTTP session
        connections = await mac._scan_network_connections()

        # ASSERT: Should return empty list gracefully
        assert connections == [], "Should return empty list without HTTP session"

    @pytest.mark.asyncio
    async def test_investigacao_without_session(self):
        """
        Test executar_investigacao without HTTP session.

        Coverage: Lines 259-260

        Scenario:
        - Investigation called without HTTP session
        - Should return error gracefully
        """
        # ARRANGE: Create macrophage without initialization
        mac = MacrofagoDigital(area_patrulha="test_zone")

        alvo = {
            "dst_ip": "192.0.2.1",
            "dst_port": 8080,
        }

        # ACT
        result = await mac.executar_investigacao(alvo)

        # ASSERT: Should return error without crashing
        assert result["is_threat"] is False, "Should not flag as threat without intel"
        assert "error" in result, "Should include error key"
        assert result["error"] == "http_session_unavailable"

    @pytest.mark.asyncio
    async def test_neutralizacao_without_session(self):
        """
        Test executar_neutralizacao without HTTP session.

        Coverage: Lines 415-416

        Scenario:
        - Neutralization called without HTTP session
        - Should return False gracefully
        """
        # ARRANGE: Create macrophage without initialization
        mac = MacrofagoDigital(area_patrulha="test_zone")

        alvo = {
            "dst_ip": "192.0.2.1",
            "dst_port": 4444,
        }

        # ACT
        result = await mac.executar_neutralizacao(alvo, metodo="isolate")

        # ASSERT: Should fail gracefully
        assert result is False, "Should return False without HTTP session"


# ==================== SUSPICION SCORING TESTS ====================


class TestMacrofagoSuspicionScoring:
    """Tests for _calcular_suspeita edge cases"""

    def test_calcular_suspeita_high_ephemeral_port(self, macrofago):
        """
        Test suspicion scoring for high ephemeral port.

        Coverage: Line 224

        Scenario:
        - Connection to high ephemeral port (>49152)
        - Should add 0.1 to suspicion score
        """
        # ARRANGE
        conexao = {
            "dst_ip": "198.51.100.1",
            "dst_port": 54321,  # Ephemeral port
            "protocol": "TCP",
            "bytes_sent": 1000,
        }

        # ACT
        score = macrofago._calcular_suspeita(conexao)

        # ASSERT: Should detect ephemeral port
        assert score > 0.0, "Should have non-zero suspicion for ephemeral port"
        # Score includes: 0.3 (unusual port) + 0.1 (ephemeral) = 0.4
        assert score >= 0.4, f"Score should be at least 0.4, got {score}"

    def test_calcular_suspeita_unusual_protocol(self, macrofago):
        """
        Test suspicion scoring for unusual protocol.

        Coverage: Line 229

        Scenario:
        - Connection using unusual protocol (not TCP/UDP/ICMP)
        - Should add 0.2 to suspicion score
        """
        # ARRANGE
        conexao = {
            "dst_ip": "198.51.100.2",
            "dst_port": 80,
            "protocol": "SCTP",  # Unusual protocol
            "bytes_sent": 1000,
        }

        # ACT
        score = macrofago._calcular_suspeita(conexao)

        # ASSERT: Should detect unusual protocol
        assert score >= 0.2, f"Should add 0.2 for unusual protocol, got {score}"


# ==================== SUMMARY ====================

"""
Additional Coverage Tests Summary:

Tests Added: 7 focused tests

Coverage Targets:
- Lines 93-126: Patrol complete flow (detect + investigate + neutralize) ✅
- Lines 93-108: Patrol with normal connection (skip investigation) ✅
- Lines 136-137: _scan_network_connections without HTTP session ✅
- Line 224: Ephemeral port scoring ✅
- Line 229: Unusual protocol scoring ✅
- Lines 259-260: executar_investigacao without HTTP session ✅
- Lines 415-416: executar_neutralizacao without HTTP session ✅

Expected Coverage Increase: 87% → 90%+ (additional ~3%+)

Total Macrophage Tests: 44 + 7 = 51 tests
"""
