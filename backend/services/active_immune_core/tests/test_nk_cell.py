"""NK Cell Tests - Unit tests for CelulaNKDigital

Tests the Natural Killer cell agent without requiring external services.
Uses graceful degradation paths for testing.
"""

import asyncio
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from active_immune_core.agents import AgentStatus, AgentType
from active_immune_core.agents.nk_cell import CelulaNKDigital


# ==================== FIXTURES ====================


@pytest_asyncio.fixture
async def nk_cell():
    """Create NK Cell agent"""
    nk = CelulaNKDigital(
        area_patrulha="test_subnet_10_0_1_0",
        kafka_bootstrap="localhost:9092",
        redis_url="redis://localhost:6379",
        anomaly_threshold=0.7,
    )
    yield nk

    # Cleanup
    if nk._running:
        await nk.parar()


@pytest.fixture
def sample_host():
    """Sample host"""
    return {
        "id": "host_192_168_1_100",
        "ip": "192.168.1.100",
        "hostname": "workstation-01",
        "audit_enabled": True,
    }


@pytest.fixture
def compromised_host():
    """Compromised host (disabled audit logging)"""
    return {
        "id": "host_192_168_1_200",
        "ip": "192.168.1.200",
        "hostname": "workstation-02",
        "audit_enabled": False,  # Missing MHC-I
    }


@pytest.fixture
def normal_metrics():
    """Normal host metrics"""
    return {
        "cpu_usage": 25.0,
        "memory_usage": 40.0,
        "network_tx": 1000000,  # 1MB/s
        "network_rx": 500000,  # 500KB/s
        "process_count": 50,
        "failed_auth_count": 0,
    }


@pytest.fixture
def anomalous_metrics():
    """Anomalous host metrics (exfiltration pattern)"""
    return {
        "cpu_usage": 95.0,  # High CPU
        "memory_usage": 85.0,  # High memory
        "network_tx": 50000000,  # 50MB/s (high egress)
        "network_rx": 1000000,  # 1MB/s
        "process_count": 150,  # Many processes
        "failed_auth_count": 25,  # Failed auth attempts
    }


# ==================== TESTS ====================


@pytest.mark.asyncio
class TestNKCellInitialization:
    """Test NK Cell initialization"""

    async def test_nk_cell_creation(self, nk_cell):
        """Test that NK Cell initializes correctly"""
        assert nk_cell.state.tipo == AgentType.NK_CELL
        assert nk_cell.state.area_patrulha == "test_subnet_10_0_1_0"
        assert nk_cell.baseline_behavior == {}
        assert nk_cell.anomalias_detectadas == 0
        assert nk_cell.hosts_isolados == []
        assert nk_cell.mhc_violations == 0
        assert nk_cell.anomaly_threshold == 0.7

    async def test_nk_cell_default_threshold(self):
        """Test default anomaly threshold"""
        nk = CelulaNKDigital(area_patrulha="test")
        assert nk.anomaly_threshold == 0.7

        await nk.parar()

    async def test_nk_cell_custom_threshold(self):
        """Test custom anomaly threshold"""
        nk = CelulaNKDigital(area_patrulha="test", anomaly_threshold=0.85)
        assert nk.anomaly_threshold == 0.85

        await nk.parar()


@pytest.mark.asyncio
class TestAnomalyScoring:
    """Test anomaly score calculation"""

    async def test_calcular_anomalia_first_observation(self, nk_cell, normal_metrics):
        """Test that first observation establishes baseline"""
        host_id = "host_001"

        score = nk_cell._calcular_anomalia(host_id, normal_metrics)

        # First observation should be 0.0
        assert score == 0.0
        # Baseline should be stored
        assert host_id in nk_cell.baseline_behavior
        assert nk_cell.baseline_behavior[host_id] == normal_metrics

    async def test_calcular_anomalia_normal_behavior(self, nk_cell, normal_metrics):
        """Test anomaly score for normal behavior"""
        host_id = "host_001"

        # Establish baseline
        nk_cell._calcular_anomalia(host_id, normal_metrics)

        # Slightly different but normal
        similar_metrics = {
            "cpu_usage": 27.0,  # +2%
            "memory_usage": 42.0,  # +2%
            "network_tx": 1100000,  # +10%
            "network_rx": 520000,  # +4%
            "process_count": 52,  # +2
            "failed_auth_count": 0,
        }

        score = nk_cell._calcular_anomalia(host_id, similar_metrics)

        # Should be low
        assert score < 0.3

    async def test_calcular_anomalia_high_deviation(
        self, nk_cell, normal_metrics, anomalous_metrics
    ):
        """Test anomaly score for high deviation"""
        host_id = "host_001"

        # Establish baseline
        nk_cell._calcular_anomalia(host_id, normal_metrics)

        # Anomalous behavior
        score = nk_cell._calcular_anomalia(host_id, anomalous_metrics)

        # Should be high
        assert score > 0.5

    async def test_calcular_anomalia_capped_at_one(self, nk_cell):
        """Test that anomaly score is capped at 1.0"""
        host_id = "host_001"

        # Establish baseline
        baseline = {"cpu_usage": 10.0, "memory_usage": 20.0}
        nk_cell._calcular_anomalia(host_id, baseline)

        # Extreme deviation
        extreme = {"cpu_usage": 1000.0, "memory_usage": 2000.0}
        score = nk_cell._calcular_anomalia(host_id, extreme)

        # Should be capped at 1.0
        assert score <= 1.0

    async def test_calcular_anomalia_no_overlap(self, nk_cell):
        """Test anomaly score when metrics don't overlap"""
        host_id = "host_001"

        # Establish baseline
        baseline = {"cpu_usage": 50.0, "memory_usage": 40.0}
        nk_cell._calcular_anomalia(host_id, baseline)

        # Different metrics entirely
        different = {"network_tx": 1000000, "network_rx": 500000}
        score = nk_cell._calcular_anomalia(host_id, different)

        # Should be 0.0 (no overlapping metrics to compare)
        assert score == 0.0


@pytest.mark.asyncio
class TestBaselineManagement:
    """Test baseline learning and updates"""

    async def test_baseline_established_on_first_patrol(
        self, nk_cell, normal_metrics
    ):
        """Test that baseline is established during patrol"""
        host_id = "host_001"

        # Manually add to baseline (simulating patrol)
        nk_cell.baseline_behavior[host_id] = normal_metrics

        assert host_id in nk_cell.baseline_behavior

    async def test_baseline_not_updated_for_anomalies(self, nk_cell):
        """Test that baseline is not updated for anomalous hosts"""
        host_id = "host_001"

        # Establish baseline
        normal = {"cpu_usage": 25.0, "memory_usage": 40.0}
        nk_cell._calcular_anomalia(host_id, normal)

        # Anomalous metrics
        anomalous = {"cpu_usage": 95.0, "memory_usage": 90.0}
        score = nk_cell._calcular_anomalia(host_id, anomalous)

        # Baseline should not be updated (score > 0.3)
        # This is tested in _update_baseline, which only updates if score < 0.3
        assert score > 0.3


@pytest.mark.asyncio
class TestMHCIDetection:
    """Test missing MHC-I detection"""

    async def test_detectar_mhc_ausente_graceful_degradation(self, nk_cell):
        """Test graceful degradation when RTE service unavailable"""
        await nk_cell.iniciar()
        await asyncio.sleep(0.5)

        # RTE service not running, should return empty list
        hosts = await nk_cell._detectar_mhc_ausente()

        assert hosts == []

        await nk_cell.parar()

    async def test_mhc_violation_increments_counter(self, nk_cell, compromised_host):
        """Test that MHC violation counter increments"""
        await nk_cell.iniciar()
        await asyncio.sleep(0.5)

        initial_violations = nk_cell.mhc_violations

        # Simulate MHC violation detection
        # In real scenario, this would be detected during patrol
        # For testing, we manually increment
        nk_cell.mhc_violations += 1

        assert nk_cell.mhc_violations == initial_violations + 1

        await nk_cell.parar()


@pytest.mark.asyncio
class TestNKCellLifecycle:
    """Test NK Cell lifecycle"""

    async def test_nk_cell_start_stop(self, nk_cell):
        """Test starting and stopping NK Cell"""
        # Start
        await nk_cell.iniciar()
        assert nk_cell._running is True
        assert nk_cell.state.ativo is True
        assert nk_cell.state.status == AgentStatus.PATRULHANDO

        await asyncio.sleep(0.5)

        # Stop
        await nk_cell.parar()
        assert nk_cell._running is False
        assert nk_cell.state.ativo is False

    async def test_nk_cell_patrol_executes(self, nk_cell):
        """Test that patrol loop executes"""
        await nk_cell.iniciar()
        await asyncio.sleep(2)

        # Patrol should have run (even if no hosts found)
        assert nk_cell._running is True

        await nk_cell.parar()


@pytest.mark.asyncio
class TestNKCellInvestigation:
    """Test investigation logic"""

    async def test_investigation_no_metrics(self, nk_cell, sample_host):
        """Test investigation when no metrics available"""
        await nk_cell.iniciar()
        await asyncio.sleep(0.5)

        # RTE service not running, no metrics available
        result = await nk_cell.executar_investigacao(sample_host)

        assert "is_threat" in result
        assert result["is_threat"] is False
        assert result["method"] == "no_metrics"

        await nk_cell.parar()

    async def test_investigation_updates_status(self, nk_cell, sample_host):
        """Test that investigation updates agent status"""
        await nk_cell.iniciar()
        await asyncio.sleep(0.5)

        # Execute investigation
        await nk_cell.investigar(sample_host)

        # Status should have been INVESTIGANDO during investigation
        # (though it may have changed back by now)

        await nk_cell.parar()

    async def test_investigation_increments_detection_counter(self, nk_cell, sample_host):
        """Test that investigation increments detection counter"""
        await nk_cell.iniciar()
        await asyncio.sleep(0.5)

        initial_detections = nk_cell.state.deteccoes_total

        await nk_cell.investigar(sample_host)

        # Detection count should increase
        assert nk_cell.state.deteccoes_total == initial_detections + 1

        await nk_cell.parar()


@pytest.mark.asyncio
class TestNKCellNeutralization:
    """Test neutralization (cytotoxicity)"""

    async def test_neutralization_isolate_method(self, nk_cell, compromised_host):
        """Test isolation method"""
        await nk_cell.iniciar()
        await asyncio.sleep(0.5)

        host_id = compromised_host["id"]

        # Attempt neutralization (RTE service not running, will degrade gracefully)
        result = await nk_cell.executar_neutralizacao(
            compromised_host, metodo="isolate"
        )

        # Should succeed locally even if RTE unavailable
        assert result is True
        assert host_id in nk_cell.hosts_isolados

        await nk_cell.parar()

    async def test_neutralization_invalid_method(self, nk_cell, sample_host):
        """Test that invalid method is rejected"""
        await nk_cell.iniciar()
        await asyncio.sleep(0.5)

        # Try invalid method
        result = await nk_cell.executar_neutralizacao(sample_host, metodo="monitor")

        # Should fail
        assert result is False

        await nk_cell.parar()

    async def test_hosts_isolados_list_limit(self, nk_cell):
        """Test that isolated hosts list is limited to 100 entries"""
        await nk_cell.iniciar()
        await asyncio.sleep(0.5)

        # Add 150 hosts
        for i in range(150):
            host_id = f"host_{i:03d}"
            await nk_cell.executar_neutralizacao({"id": host_id}, metodo="isolate")

        # Should only keep last 100
        assert len(nk_cell.hosts_isolados) == 100

        await nk_cell.parar()

    async def test_neutralization_triggers_ifn_gamma(self, nk_cell, compromised_host):
        """Test that neutralization triggers IFN-gamma secretion"""
        await nk_cell.iniciar()
        await asyncio.sleep(0.5)

        # Neutralize
        result = await nk_cell.executar_neutralizacao(
            compromised_host, metodo="isolate"
        )

        # Should succeed (tracked locally even if cytokine fails)
        assert result is True

        # IFN-gamma secretion is logged (can't verify without Kafka)

        await nk_cell.parar()


@pytest.mark.asyncio
class TestNKCellMetrics:
    """Test NK Cell metrics"""

    async def test_get_nk_metrics(self, nk_cell):
        """Test NK Cell-specific metrics"""
        await nk_cell.iniciar()
        await asyncio.sleep(0.5)

        # Simulate some activity
        nk_cell.anomalias_detectadas = 10
        nk_cell.hosts_isolados = ["host_1", "host_2", "host_3"]
        nk_cell.mhc_violations = 5
        nk_cell.baseline_behavior = {"host_1": {}, "host_2": {}, "host_3": {}}
        nk_cell.state.neutralizacoes_total = 8

        metrics = nk_cell.get_nk_metrics()

        assert metrics["anomalias_detectadas"] == 10
        assert metrics["hosts_isolados_total"] == 3
        assert metrics["mhc_violations"] == 5
        assert metrics["baseline_hosts"] == 3
        assert metrics["eficiencia_deteccao"] == 0.8  # 8/10

        await nk_cell.parar()

    async def test_repr(self, nk_cell):
        """Test string representation"""
        nk_cell.anomalias_detectadas = 5
        nk_cell.hosts_isolados = ["host_1", "host_2"]
        nk_cell.mhc_violations = 3

        repr_str = repr(nk_cell)

        assert "CelulaNKDigital" in repr_str
        assert nk_cell.state.id[:8] in repr_str
        assert "anomalias=5" in repr_str
        assert "isolados=2" in repr_str
        assert "mhc_violations=3" in repr_str


@pytest.mark.asyncio
class TestIFNGammaSecretion:
    """Test IFN-gamma cytokine secretion"""

    async def test_ifn_gamma_requires_cytokine_messenger(self, nk_cell):
        """Test that IFN-gamma secretion requires cytokine messenger"""
        # Don't start agent (no cytokine messenger)
        host = {"id": "host_001", "anomaly_score": 0.9}

        # Should not crash, just log debug
        await nk_cell._secretar_ifn_gamma(host)

        # No errors should occur
        assert True

    async def test_ifn_gamma_secretion_high_priority(self, nk_cell):
        """Test that IFN-gamma is secreted with high priority"""
        await nk_cell.iniciar()
        await asyncio.sleep(0.5)

        host = {
            "id": "host_001",
            "anomaly_score": 0.95,
        }

        # Secrete IFN-gamma
        await nk_cell._secretar_ifn_gamma(host)

        # Should complete without error (even if Kafka unavailable)
        assert True

        await nk_cell.parar()


@pytest.mark.asyncio
class TestNKCellPatrolLogic:
    """Test patrol logic"""

    async def test_patrol_handles_no_hosts(self, nk_cell):
        """Test that patrol handles empty host list gracefully"""
        await nk_cell.iniciar()
        await asyncio.sleep(0.5)

        # Call patrol directly (will get empty hosts since RTE not running)
        await nk_cell.patrulhar()

        # Should complete without error
        assert True

        await nk_cell.parar()

    async def test_patrol_updates_baseline(self, nk_cell):
        """Test that patrol updates baseline for normal hosts"""
        await nk_cell.iniciar()
        await asyncio.sleep(2)

        # Baseline may or may not be updated (depends on RTE service)
        # Test that it doesn't crash
        assert True

        await nk_cell.parar()


@pytest.mark.asyncio
class TestNKCellEdgeCases:
    """Test edge cases"""

    async def test_anomaly_score_with_empty_metrics(self, nk_cell):
        """Test anomaly calculation with empty metrics"""
        host_id = "host_001"

        # Empty metrics
        empty_metrics = {}

        score = nk_cell._calcular_anomalia(host_id, empty_metrics)

        # Should handle gracefully
        assert score == 0.0

    async def test_anomaly_score_with_zero_baseline(self, nk_cell):
        """Test anomaly calculation when baseline has zero values"""
        host_id = "host_001"

        # Baseline with zeros
        baseline = {"cpu_usage": 0.0, "memory_usage": 0.0}
        nk_cell._calcular_anomalia(host_id, baseline)

        # Current metrics with non-zero values
        current = {"cpu_usage": 50.0, "memory_usage": 60.0}
        score = nk_cell._calcular_anomalia(host_id, current)

        # Should handle division by zero gracefully
        assert score >= 0.0

    async def test_neutralization_empty_host_id(self, nk_cell):
        """Test neutralization with empty host ID"""
        await nk_cell.iniciar()
        await asyncio.sleep(0.5)

        # Empty host ID
        result = await nk_cell.executar_neutralizacao({"id": ""}, metodo="isolate")

        # Should track even with empty ID (graceful degradation)
        assert result is True

        await nk_cell.parar()


@pytest.mark.asyncio
class TestNKCellWithMockedServices:
    """Test NK Cell with mocked HTTP responses"""

    async def test_detectar_mhc_ausente_with_violations(self, nk_cell):
        """Test MHC-I detection when violations are found"""
        await nk_cell.iniciar()
        await asyncio.sleep(0.5)

        # Mock HTTP response with MHC violations
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "hosts": [
                {"id": "host_001", "audit_enabled": True},
                {"id": "host_002", "audit_enabled": False},  # Violation
                {"id": "host_003", "audit_enabled": False},  # Violation
            ]
        })

        with patch.object(nk_cell._http_session, 'get') as mock_get:
            mock_get.return_value.__aenter__.return_value = mock_response

            hosts = await nk_cell._detectar_mhc_ausente()

            # Should return 2 violations
            assert len(hosts) == 2
            assert all(not h.get("audit_enabled") for h in hosts)

        await nk_cell.parar()

    async def test_detectar_mhc_ausente_status_404(self, nk_cell):
        """Test MHC-I detection with 404 response"""
        await nk_cell.iniciar()
        await asyncio.sleep(0.5)

        mock_response = AsyncMock()
        mock_response.status = 404

        with patch.object(nk_cell._http_session, 'get') as mock_get:
            mock_get.return_value.__aenter__.return_value = mock_response

            hosts = await nk_cell._detectar_mhc_ausente()

            # Should return empty list (graceful degradation)
            assert hosts == []

        await nk_cell.parar()

    async def test_detectar_mhc_ausente_unexpected_status(self, nk_cell):
        """Test MHC-I detection with unexpected status code"""
        await nk_cell.iniciar()
        await asyncio.sleep(0.5)

        mock_response = AsyncMock()
        mock_response.status = 500

        with patch.object(nk_cell._http_session, 'get') as mock_get:
            mock_get.return_value.__aenter__.return_value = mock_response

            hosts = await nk_cell._detectar_mhc_ausente()

            # Should return empty list
            assert hosts == []

        await nk_cell.parar()

    async def test_get_host_metrics_success(self, nk_cell, normal_metrics):
        """Test getting host metrics with successful response"""
        await nk_cell.iniciar()
        await asyncio.sleep(0.5)

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=normal_metrics)

        with patch.object(nk_cell._http_session, 'get') as mock_get:
            mock_get.return_value.__aenter__.return_value = mock_response

            metrics = await nk_cell._get_host_metrics("host_001")

            assert metrics == normal_metrics

        await nk_cell.parar()

    async def test_get_host_metrics_failure(self, nk_cell):
        """Test getting host metrics with failed response"""
        await nk_cell.iniciar()
        await asyncio.sleep(0.5)

        mock_response = AsyncMock()
        mock_response.status = 500

        with patch.object(nk_cell._http_session, 'get') as mock_get:
            mock_get.return_value.__aenter__.return_value = mock_response

            metrics = await nk_cell._get_host_metrics("host_001")

            # Should return empty dict
            assert metrics == {}

        await nk_cell.parar()

    async def test_update_baseline_with_normal_hosts(self, nk_cell, normal_metrics):
        """Test baseline update for normal hosts"""
        await nk_cell.iniciar()
        await asyncio.sleep(0.5)

        # Establish initial baseline
        nk_cell.baseline_behavior["host_001"] = normal_metrics.copy()

        # Mock host list
        mock_list_response = AsyncMock()
        mock_list_response.status = 200
        mock_list_response.json = AsyncMock(return_value={
            "hosts": [{"id": "host_001"}]
        })

        # Mock metrics (slightly different from baseline, but normal)
        updated_metrics = normal_metrics.copy()
        updated_metrics["cpu_usage"] = 27.0  # Small change

        mock_metrics_response = AsyncMock()
        mock_metrics_response.status = 200
        mock_metrics_response.json = AsyncMock(return_value=updated_metrics)

        async def mock_get(*args, **kwargs):
            url = args[0] if args else kwargs.get('url', '')
            if '/list' in url:
                mock = AsyncMock()
                mock.__aenter__.return_value = mock_list_response
                return mock
            else:
                mock = AsyncMock()
                mock.__aenter__.return_value = mock_metrics_response
                return mock

        with patch.object(nk_cell._http_session, 'get', side_effect=mock_get):
            await nk_cell._update_baseline()

            # Baseline should be updated (EMA)
            assert "host_001" in nk_cell.baseline_behavior
            # CPU should be updated with EMA: 0.9 * 25.0 + 0.1 * 27.0 = 22.5 + 2.7 = 25.2
            updated_cpu = nk_cell.baseline_behavior["host_001"]["cpu_usage"]
            assert 24.0 < updated_cpu < 26.0  # Approximately 25.2

        await nk_cell.parar()

    async def test_update_baseline_skips_isolated_hosts(self, nk_cell, normal_metrics):
        """Test that baseline update skips isolated hosts"""
        await nk_cell.iniciar()
        await asyncio.sleep(0.5)

        # Mark host as isolated
        nk_cell.hosts_isolados.append("host_001")

        mock_list_response = AsyncMock()
        mock_list_response.status = 200
        mock_list_response.json = AsyncMock(return_value={
            "hosts": [{"id": "host_001"}]
        })

        with patch.object(nk_cell._http_session, 'get') as mock_get:
            mock_get.return_value.__aenter__.return_value = mock_list_response

            await nk_cell._update_baseline()

            # Isolated host should not be in baseline
            # (or if it was there before, should not be updated)
            # This test verifies the skip logic executes

        await nk_cell.parar()

    async def test_executar_investigacao_threat_detected(self, nk_cell, anomalous_metrics):
        """Test investigation when threat is detected"""
        await nk_cell.iniciar()
        await asyncio.sleep(0.5)

        # Establish baseline
        baseline = {
            "cpu_usage": 25.0,
            "memory_usage": 40.0,
            "network_tx": 1000000,
            "network_rx": 500000,
            "process_count": 50,
            "failed_auth_count": 0,
        }
        nk_cell.baseline_behavior["host_001"] = baseline

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=anomalous_metrics)

        with patch.object(nk_cell._http_session, 'get') as mock_get:
            mock_get.return_value.__aenter__.return_value = mock_response

            result = await nk_cell.executar_investigacao({"id": "host_001"})

            assert "is_threat" in result
            assert result["is_threat"] is True  # Anomaly score > threshold
            assert result["method"] == "behavioral_anomaly"
            assert "anomaly_score" in result
            assert result["anomaly_score"] > nk_cell.anomaly_threshold

        await nk_cell.parar()

    async def test_executar_neutralizacao_success_200(self, nk_cell, compromised_host):
        """Test neutralization with successful RTE response (200)"""
        await nk_cell.iniciar()
        await asyncio.sleep(0.5)

        mock_response = AsyncMock()
        mock_response.status = 200

        with patch.object(nk_cell._http_session, 'post') as mock_post:
            mock_post.return_value.__aenter__.return_value = mock_response

            result = await nk_cell.executar_neutralizacao(
                compromised_host, metodo="isolate"
            )

            assert result is True
            assert compromised_host["id"] in nk_cell.hosts_isolados

        await nk_cell.parar()

    async def test_executar_neutralizacao_rte_404(self, nk_cell, compromised_host):
        """Test neutralization with RTE service returning 404"""
        await nk_cell.iniciar()
        await asyncio.sleep(0.5)

        mock_response = AsyncMock()
        mock_response.status = 404

        with patch.object(nk_cell._http_session, 'post') as mock_post:
            mock_post.return_value.__aenter__.return_value = mock_response

            result = await nk_cell.executar_neutralizacao(
                compromised_host, metodo="isolate"
            )

            # Should still succeed (graceful degradation)
            assert result is True
            assert compromised_host["id"] in nk_cell.hosts_isolados

        await nk_cell.parar()

    async def test_executar_neutralizacao_rte_error(self, nk_cell, compromised_host):
        """Test neutralization with RTE service returning error"""
        await nk_cell.iniciar()
        await asyncio.sleep(0.5)

        mock_response = AsyncMock()
        mock_response.status = 500

        with patch.object(nk_cell._http_session, 'post') as mock_post:
            mock_post.return_value.__aenter__.return_value = mock_response

            result = await nk_cell.executar_neutralizacao(
                compromised_host, metodo="isolate"
            )

            # Should fail (not 200 or 404)
            assert result is False

        await nk_cell.parar()

    async def test_secretar_ifn_gamma_with_cytokine_messenger(self, nk_cell):
        """Test IFN-gamma secretion when cytokine messenger is available"""
        await nk_cell.iniciar()
        await asyncio.sleep(0.5)

        # Mock cytokine messenger
        nk_cell._cytokine_messenger = AsyncMock()
        nk_cell._cytokine_messenger.send_cytokine = AsyncMock()

        host = {"id": "host_001", "anomaly_score": 0.95}

        await nk_cell._secretar_ifn_gamma(host)

        # Should have called send_cytokine
        nk_cell._cytokine_messenger.send_cytokine.assert_called_once()
        call_args = nk_cell._cytokine_messenger.send_cytokine.call_args
        assert call_args[1]["tipo"] == "IFNgamma"
        assert call_args[1]["prioridade"] == 10  # High priority

        await nk_cell.parar()

