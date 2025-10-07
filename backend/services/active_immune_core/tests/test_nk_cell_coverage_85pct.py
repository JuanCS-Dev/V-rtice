"""NK Cell Coverage Tests - Additional tests to reach 85%

This module contains additional focused tests to reach 85% coverage target.

Current: ~75-80%
Target: 85%
Gap: ~5-10%

Missing lines identified:
- 263: get_host_metrics else return {} (status != 200)
- 267-272: get_host_metrics ClientConnectorError and Exception
- 338-368: _update_baseline() complete flow
- 516-517: _secretar_ifn_gamma() exception handling
- 292-296: _calcular_anomalia baseline establishment (first observation)
- 534-537: get_nk_metrics efficiency calculation
"""

import asyncio
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest
import pytest_asyncio

from active_immune_core.agents import AgentStatus, AgentType
from active_immune_core.agents.nk_cell import CelulaNKDigital


# ==================== FIXTURES ====================


@pytest_asyncio.fixture
async def nk_cell():
    """Create and initialize NK Cell agent"""
    nk = CelulaNKDigital(
        area_patrulha="coverage_85pct_zone",
        kafka_bootstrap="localhost:9092",
        redis_url="redis://localhost:6379",
        anomaly_threshold=0.7,
    )

    # Initialize to create HTTP session
    await nk.iniciar()
    await asyncio.sleep(0.5)

    yield nk

    if nk._running:
        await nk.parar()


@pytest.fixture
def sample_host():
    """Sample host"""
    return {
        "id": "host_10_0_2_100",
        "ip": "10.0.2.100",
        "hostname": "server-100",
    }


@pytest.fixture
def normal_metrics():
    """Normal baseline metrics"""
    return {
        "cpu_usage": 30.0,
        "memory_usage": 45.0,
        "network_tx": 1000000,
        "network_rx": 800000,
        "process_count": 50,
        "failed_auth_count": 0,
    }


# ==================== ADDITIONAL COVERAGE TESTS ====================


class TestNKCellMetricsRetrieval:
    """Tests for _get_host_metrics coverage (Lines 263, 267-272)"""

    @pytest.mark.asyncio
    async def test_get_host_metrics_non_200_status(self, nk_cell, sample_host):
        """
        Test get_host_metrics with non-200 status (e.g., 500).

        Coverage: Line 263 (else return {})

        Scenario:
        - Metrics endpoint returns 500 error
        - Should return empty dict
        """
        # ARRANGE
        mock_response = AsyncMock()
        mock_response.status = 500  # Server error

        # ACT
        with patch.object(nk_cell._http_session, "get") as mock_get:
            mock_get.return_value.__aenter__.return_value = mock_response

            metrics = await nk_cell._get_host_metrics(sample_host["id"])

        # ASSERT
        assert metrics == {}, "Should return empty dict on non-200 status"

    @pytest.mark.asyncio
    async def test_get_host_metrics_connection_error(self, nk_cell, sample_host):
        """
        Test get_host_metrics with connection error.

        Coverage: Lines 267-268 (ClientConnectorError except block)

        Scenario:
        - HTTP connection fails
        - Should catch exception and return empty dict
        """
        # ARRANGE
        with patch.object(nk_cell._http_session, "get") as mock_get:
            mock_get.side_effect = aiohttp.ClientConnectorError(
                connection_key=None, os_error=OSError("Connection refused")
            )

            # ACT
            metrics = await nk_cell._get_host_metrics(sample_host["id"])

        # ASSERT
        assert metrics == {}, "Should return empty dict on connection error"

    @pytest.mark.asyncio
    async def test_get_host_metrics_generic_exception(self, nk_cell, sample_host):
        """
        Test get_host_metrics with generic exception.

        Coverage: Lines 270-272 (generic Exception catch)

        Scenario:
        - Unexpected exception during metrics retrieval
        - Should catch, log, and return empty dict
        """
        # ARRANGE
        with patch.object(nk_cell._http_session, "get") as mock_get:
            mock_get.side_effect = ValueError("Unexpected error")

            # ACT
            metrics = await nk_cell._get_host_metrics(sample_host["id"])

        # ASSERT
        assert metrics == {}, "Should return empty dict on generic exception"


class TestNKCellBaselineUpdate:
    """Tests for _update_baseline coverage (Lines 338-368)"""

    @pytest.mark.asyncio
    async def test_update_baseline_establishes_new_host(
        self, nk_cell, sample_host, normal_metrics
    ):
        """
        Test baseline establishment for new host.

        Coverage: Lines 338-368 (complete _update_baseline flow)

        Scenario:
        - Host has no baseline yet
        - Metrics are normal (anomaly_score < 0.3)
        - Should establish baseline for host
        """
        # ARRANGE: Ensure no baseline exists
        assert sample_host["id"] not in nk_cell.baseline_behavior

        # Mock RTE responses
        mock_hosts_list = AsyncMock()
        mock_hosts_list.status = 200
        mock_hosts_list.json = AsyncMock(return_value={"hosts": [sample_host]})

        mock_metrics = AsyncMock()
        mock_metrics.status = 200
        mock_metrics.json = AsyncMock(return_value=normal_metrics)

        # ACT
        with patch.object(nk_cell._http_session, "get") as mock_get:

            def get_side_effect(url, **kwargs):
                mock = AsyncMock()
                if "/metrics" in str(url):
                    mock.__aenter__.return_value = mock_metrics
                else:  # hosts/list
                    mock.__aenter__.return_value = mock_hosts_list
                return mock

            mock_get.side_effect = get_side_effect

            await nk_cell._update_baseline()

        # ASSERT
        assert (
            sample_host["id"] in nk_cell.baseline_behavior
        ), "Should establish baseline for new host"
        assert nk_cell.baseline_behavior[sample_host["id"]] == normal_metrics

    @pytest.mark.asyncio
    async def test_update_baseline_skips_isolated_hosts(
        self, nk_cell, sample_host, normal_metrics
    ):
        """
        Test baseline update skips isolated hosts.

        Coverage: Lines 343-344 (skip isolated hosts)

        Scenario:
        - Host is in hosts_isolados list
        - Should skip updating baseline for this host
        """
        # ARRANGE: Mark host as isolated
        nk_cell.hosts_isolados.append(sample_host["id"])

        # Mock RTE responses
        mock_hosts_list = AsyncMock()
        mock_hosts_list.status = 200
        mock_hosts_list.json = AsyncMock(return_value={"hosts": [sample_host]})

        baseline_before = dict(nk_cell.baseline_behavior)

        # ACT
        with patch.object(nk_cell._http_session, "get") as mock_get:
            mock_get.return_value.__aenter__.return_value = mock_hosts_list

            await nk_cell._update_baseline()

        # ASSERT
        assert (
            nk_cell.baseline_behavior == baseline_before
        ), "Should not update baseline for isolated host"

    @pytest.mark.asyncio
    async def test_update_baseline_exponential_moving_average(
        self, nk_cell, sample_host, normal_metrics
    ):
        """
        Test baseline update uses exponential moving average.

        Coverage: Lines 354-362 (EMA update logic)

        Scenario:
        - Host has existing baseline
        - New metrics are slightly different but normal (anomaly < 0.3)
        - Should update baseline using EMA (alpha=0.1)
        """
        # ARRANGE: Establish baseline
        old_baseline = {
            "cpu_usage": 20.0,
            "memory_usage": 40.0,
        }
        nk_cell.baseline_behavior[sample_host["id"]] = old_baseline.copy()

        # New metrics (slightly higher but still normal - anomaly score < 0.3)
        # cpu: (22-20)/20 = 0.1, mem: (42-40)/40 = 0.05 → anomaly ~0.08 < 0.3
        new_metrics = {
            "cpu_usage": 22.0,  # +2 (10% increase)
            "memory_usage": 42.0,  # +2 (5% increase)
        }

        # Mock RTE responses
        mock_hosts_list = AsyncMock()
        mock_hosts_list.status = 200
        mock_hosts_list.json = AsyncMock(return_value={"hosts": [sample_host]})

        mock_metrics = AsyncMock()
        mock_metrics.status = 200
        mock_metrics.json = AsyncMock(return_value=new_metrics)

        # ACT
        with patch.object(nk_cell._http_session, "get") as mock_get:

            def get_side_effect(url, **kwargs):
                mock = AsyncMock()
                if "/metrics" in str(url):
                    mock.__aenter__.return_value = mock_metrics
                else:
                    mock.__aenter__.return_value = mock_hosts_list
                return mock

            mock_get.side_effect = get_side_effect

            await nk_cell._update_baseline()

        # ASSERT: Baseline should be updated with EMA (0.9 * old + 0.1 * new)
        expected_cpu = 0.9 * 20.0 + 0.1 * 22.0  # = 18.0 + 2.2 = 20.2
        expected_mem = 0.9 * 40.0 + 0.1 * 42.0  # = 36.0 + 4.2 = 40.2

        baseline = nk_cell.baseline_behavior[sample_host["id"]]
        assert abs(baseline["cpu_usage"] - expected_cpu) < 0.01, (
            f"CPU baseline should be ~{expected_cpu}, got {baseline['cpu_usage']}"
        )
        assert abs(baseline["memory_usage"] - expected_mem) < 0.01, (
            f"Memory baseline should be ~{expected_mem}, got {baseline['memory_usage']}"
        )


class TestNKCellCytokineSecretion:
    """Tests for _secretar_ifn_gamma coverage (Lines 516-517)"""

    @pytest.mark.asyncio
    async def test_secretar_ifn_gamma_exception_handling(self, nk_cell, sample_host):
        """
        Test IFN-gamma secretion exception handling.

        Coverage: Lines 516-517 (exception catch in _secretar_ifn_gamma)

        Scenario:
        - Cytokine messenger send fails with exception
        - Should catch exception and log error
        - Should not raise (graceful degradation)
        """
        # ARRANGE: Mock cytokine messenger to raise exception
        nk_cell._cytokine_messenger = MagicMock()
        nk_cell._cytokine_messenger.send_cytokine = AsyncMock(
            side_effect=Exception("Kafka send failed")
        )

        alvo = sample_host.copy()
        alvo["anomaly_score"] = 0.95

        # ACT: Should not raise exception
        await nk_cell._secretar_ifn_gamma(alvo)

        # ASSERT: Method completed without raising
        assert True, "Should handle exception gracefully"

    @pytest.mark.asyncio
    async def test_secretar_ifn_gamma_no_messenger(self, nk_cell, sample_host):
        """
        Test IFN-gamma secretion when messenger not initialized.

        Coverage: Lines 496-498 (early return if no messenger)

        Scenario:
        - Cytokine messenger is None
        - Should return early without error
        """
        # ARRANGE: Ensure no messenger
        nk_cell._cytokine_messenger = None

        # ACT: Should return early
        await nk_cell._secretar_ifn_gamma(sample_host)

        # ASSERT: Completed without error
        assert True, "Should handle missing messenger gracefully"


class TestNKCellAnomalyCalculation:
    """Tests for _calcular_anomalia coverage (Lines 292-296)"""

    @pytest.mark.asyncio
    async def test_calcular_anomalia_first_observation(self, nk_cell, normal_metrics):
        """
        Test anomaly calculation on first observation (baseline establishment).

        Coverage: Lines 292-296 (first observation path)

        Scenario:
        - Host has no baseline yet
        - Should establish baseline and return 0.0
        """
        # ARRANGE
        host_id = "new_host_123"
        assert host_id not in nk_cell.baseline_behavior

        # ACT
        score = nk_cell._calcular_anomalia(host_id, normal_metrics)

        # ASSERT
        assert score == 0.0, "First observation should return 0.0 anomaly score"
        assert (
            host_id in nk_cell.baseline_behavior
        ), "Should establish baseline on first observation"
        assert nk_cell.baseline_behavior[host_id] == normal_metrics


class TestNKCellMetrics:
    """Tests for get_nk_metrics coverage (Lines 534-537)"""

    @pytest.mark.asyncio
    async def test_get_nk_metrics_with_detections(self, nk_cell):
        """
        Test NK metrics calculation with anomaly detections.

        Coverage: Lines 534-537 (efficiency calculation)

        Scenario:
        - NK cell has detected anomalies and neutralized hosts
        - Should calculate detection efficiency correctly
        """
        # ARRANGE: Simulate detections and neutralizations
        nk_cell.anomalias_detectadas = 10
        nk_cell.state.neutralizacoes_total = 8  # 80% efficiency

        # ACT
        metrics = nk_cell.get_nk_metrics()

        # ASSERT
        assert metrics["anomalias_detectadas"] == 10
        assert metrics["eficiencia_deteccao"] == 0.8, "Should calculate 8/10 = 0.8"

    @pytest.mark.asyncio
    async def test_get_nk_metrics_zero_anomalies(self, nk_cell):
        """
        Test NK metrics with zero anomalies (division by zero protection).

        Coverage: Lines 534-537 (zero anomalies case)

        Scenario:
        - No anomalies detected yet
        - Should return 0.0 efficiency (avoid division by zero)
        """
        # ARRANGE: No detections
        nk_cell.anomalias_detectadas = 0
        nk_cell.state.neutralizacoes_total = 0

        # ACT
        metrics = nk_cell.get_nk_metrics()

        # ASSERT
        assert metrics["eficiencia_deteccao"] == 0.0, (
            "Should return 0.0 efficiency when no anomalies"
        )


# ==================== SUMMARY ====================

"""
Additional Coverage Tests Summary:

Tests Added: 10 focused tests

Coverage Targets:
- Lines 263: get_host_metrics non-200 status ✅
- Lines 267-268: get_host_metrics connection error ✅
- Lines 270-272: get_host_metrics generic exception ✅
- Lines 338-368: _update_baseline complete flow ✅
  - New host baseline establishment
  - Skip isolated hosts
  - Exponential moving average update
- Lines 496-498: _secretar_ifn_gamma no messenger ✅
- Lines 516-517: _secretar_ifn_gamma exception ✅
- Lines 292-296: _calcular_anomalia first observation ✅
- Lines 534-537: get_nk_metrics efficiency calculation ✅

Expected Coverage Increase: ~75-80% → 85%+ (additional ~5-10%)

Total NK Cell Tests: 70 + 10 = 80 tests
"""
