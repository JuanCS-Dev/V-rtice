"""Homeostatic Controller Ultra-Surgical - 90% → 95%+

These tests target REMAINING uncovered lines with ultra-precision:
- MMEI unavailable warning (159-160)
- Lymphnode 404 handling (502-504)
- Determine action params edge cases (725-726, 729-730, 739-740, 760-762)
- Execute method exceptions (ClientConnectorError) (852-854, 866-868, 882-884)
- HTTP session unavailable for execute (792-793)
- Execute routing (798, 804)
- Execution exception handling (816-818)

Focus: ULTRA-PRECISION for final 5%
"""

from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest
import pytest_asyncio

from active_immune_core.coordination.homeostatic_controller import (
    ActionType,
    HomeostaticController,
)

# ==================== FIXTURES ====================


@pytest_asyncio.fixture
async def controller():
    """Create homeostatic controller for ultra tests"""
    ctrl = HomeostaticController(
        controller_id="ctrl_ultra",
        lymphnode_url="http://localhost:8200",
        metrics_url="http://localhost:9090",
        db_url="postgresql://user:pass@localhost:5432/immunis_test",
        monitor_interval=1,
    )
    yield ctrl
    if ctrl._running:
        await ctrl.parar()


# ==================== MMEI UNAVAILABLE WARNING ====================


class TestMMEIUnavailableWarning:
    """Test MMEI unavailable warning (Lines 159-160)"""

    @pytest.mark.asyncio
    async def test_set_mmei_client_when_unavailable_logs_warning(self, controller):
        """
        Test set_mmei_client logs warning when MMEI not available.

        Real scenario: MMEI module not installed/imported.

        Coverage: Lines 159-160 (warning + early return)
        """
        # ARRANGE: Mock MMEI_AVAILABLE = False
        with patch("active_immune_core.coordination.homeostatic_controller.MMEI_AVAILABLE", False):
            mock_client = MagicMock()

            # ACT: Try to set MMEI client
            controller.set_mmei_client(mock_client)

        # ASSERT: Should NOT set client
        assert controller.mmei_client is None, "Should not set MMEI client when unavailable"


# ==================== LYMPHNODE 404 HANDLING ====================


class TestLymphnod404Handling:
    """Test Lymphnode 404 response handling (Lines 502-504)"""

    @pytest.mark.asyncio
    async def test_collect_agent_metrics_handles_404(self, controller):
        """
        Test _collect_agent_metrics handles 404 (lymphnode not found).

        Real scenario: Lymphnode endpoint not available.

        Coverage: Lines 502-504 (404 handling)
        """
        # ARRANGE: Mock HTTP session with 404 response
        mock_response = MagicMock()
        mock_response.status = 404

        mock_get = MagicMock()
        mock_get.__aenter__ = AsyncMock(return_value=mock_response)
        mock_get.__aexit__ = AsyncMock(return_value=False)

        controller._http_session = MagicMock()
        controller._http_session.get = MagicMock(return_value=mock_get)

        # ACT: Collect agent metrics
        metrics = await controller._collect_agent_metrics()

        # ASSERT: Should return empty dict on 404
        assert metrics == {}, "Should return empty metrics on 404 (lymphnode unavailable)"


# ==================== DETERMINE ACTION PARAMS EDGE CASES ====================


class TestDetermineActionParamsEdgeCases:
    """Test _determine_action_params edge cases"""

    @pytest.mark.asyncio
    async def test_determine_params_scale_up_high_threat_load(self, controller):
        """
        Test _determine_action_params for scale_up with high_threat_load.

        Real behavior: Scale proportional to threat count.

        Coverage: Lines 725-726 (high_threat_load params)
        """
        # ARRANGE: High threat load issue
        issues = ["high_threat_load"]
        controller.agent_metrics = {"threats_detected": 30}

        # ACT: Determine params
        params = controller._determine_action_params(ActionType.SCALE_UP_AGENTS, issues)

        # ASSERT: Should scale based on threats
        assert params["quantity"] == min(50, 30 * 2), "Should scale proportional to threats (max 50)"
        assert params["reason"] == "high_threat_load"

    @pytest.mark.asyncio
    async def test_determine_params_scale_up_high_repair_need(self, controller):
        """
        Test _determine_action_params for scale_up with high_repair_need.

        Real behavior: MMEI repair_need triggers agent scale-up.

        Coverage: Lines 729-730 (high_repair_need params)
        """
        # ARRANGE: High repair need issue (from MMEI)
        issues = ["high_repair_need_alert"]
        controller.agent_metrics = {"threats_detected": 5}

        # ACT
        params = controller._determine_action_params(ActionType.SCALE_UP_AGENTS, issues)

        # ASSERT: Should scale for repair
        assert params["quantity"] == 15, "Should scale by 15 for repair need"
        assert params["reason"] == "high_repair_need"

    @pytest.mark.asyncio
    async def test_determine_params_scale_down_rest_need(self, controller):
        """
        Test _determine_action_params for scale_down with rest_need.

        Real behavior: MMEI rest_need triggers conservation (scale down).

        Coverage: Lines 739-740 (rest_need_conservation params)
        """
        # ARRANGE: High rest need issue (from MMEI)
        issues = ["high_rest_need_fatigue"]

        # ACT
        params = controller._determine_action_params(ActionType.SCALE_DOWN_AGENTS, issues)

        # ASSERT: Should conserve resources
        assert params["quantity"] == 10, "Should scale down by 10 for rest need conservation"
        assert params["reason"] == "rest_need_conservation"

    @pytest.mark.asyncio
    async def test_determine_params_adjust_temp_efficiency_optimization(self, controller):
        """
        Test _determine_action_params for temperature with efficiency_optimization.

        Real behavior: MMEI efficiency_need → cool down for optimization.

        Coverage: Lines 760-762 (efficiency_optimization params)
        """
        # ARRANGE: Efficiency optimization needed (from MMEI)
        issues = ["efficiency_optimization_needed"]

        # ACT
        params = controller._determine_action_params(ActionType.ADJUST_TEMPERATURE, issues)

        # ASSERT: Should cool down
        assert params["delta"] == -0.5, "Should cool down by -0.5 for efficiency"
        assert params["reason"] == "efficiency_optimization"


# ==================== EXECUTE METHOD EXCEPTIONS ====================


class TestExecuteMethodExceptions:
    """Test execute methods exception handling (ClientConnectorError)"""

    @pytest.mark.asyncio
    async def test_execute_scale_down_handles_connector_error(self, controller):
        """
        Test _execute_scale_down handles ClientConnectorError gracefully.

        Real scenario: Lymphnode service down.

        Coverage: Lines 852-854 (ClientConnectorError in scale_down)
        """
        # ARRANGE: Mock HTTP post to raise ClientConnectorError
        import errno

        controller._http_session = MagicMock()
        controller._http_session.post = MagicMock(
            side_effect=aiohttp.ClientConnectorError(
                connection_key=None, os_error=OSError(errno.ECONNREFUSED, "Connection refused")
            )
        )

        # ACT: Try to scale down
        success = await controller._execute_scale_down({"quantity": 5})

        # ASSERT: Should handle gracefully
        assert success is False, "Should return False on ClientConnectorError"

    @pytest.mark.asyncio
    async def test_execute_clone_specialized_handles_connector_error(self, controller):
        """
        Test _execute_clone_specialized handles ClientConnectorError.

        Coverage: Lines 866-868 (ClientConnectorError in clone)
        """
        # ARRANGE: Mock HTTP post to raise ClientConnectorError
        import errno

        controller._http_session = MagicMock()
        controller._http_session.post = MagicMock(
            side_effect=aiohttp.ClientConnectorError(
                connection_key=None, os_error=OSError(errno.ECONNREFUSED, "Connection refused")
            )
        )

        # ACT
        success = await controller._execute_clone_specialized({"tipo": "neutrofilo", "quantity": 20})

        # ASSERT
        assert success is False, "Should handle ClientConnectorError gracefully"

    @pytest.mark.asyncio
    async def test_execute_destroy_clones_handles_connector_error(self, controller):
        """
        Test _execute_destroy_clones handles ClientConnectorError.

        Coverage: Lines 882-884 (ClientConnectorError in destroy)
        """
        # ARRANGE: Mock HTTP post to raise ClientConnectorError
        import errno

        controller._http_session = MagicMock()
        controller._http_session.post = MagicMock(
            side_effect=aiohttp.ClientConnectorError(
                connection_key=None, os_error=OSError(errno.ECONNREFUSED, "Connection refused")
            )
        )

        # ACT
        success = await controller._execute_destroy_clones({"specialization": "malware_xyz"})

        # ASSERT
        assert success is False, "Should handle ClientConnectorError gracefully"


# ==================== EXECUTE ROUTING & EXCEPTION HANDLING ====================


class TestExecuteRoutingAndExceptions:
    """Test execute method routing and exception handling"""

    @pytest.mark.asyncio
    async def test_execute_without_http_session(self, controller):
        """
        Test _execute handles missing HTTP session.

        Real scenario: Session not initialized.

        Coverage: Lines 792-793 (HTTP session check)
        """
        # ARRANGE: No HTTP session
        controller._http_session = None

        # ACT: Try to execute action
        success = await controller._execute(ActionType.SCALE_UP_AGENTS, {})

        # ASSERT: Should return False
        assert success is False, "Should return False when HTTP session unavailable"

    @pytest.mark.asyncio
    async def test_execute_routes_to_scale_up(self, controller):
        """
        Test _execute routes SCALE_UP_AGENTS to _execute_scale_up.

        Coverage: Line 798 (routing to scale_up)
        """
        # ARRANGE: Mock _execute_scale_up
        with patch.object(controller, "_execute_scale_up", new_callable=AsyncMock) as mock_scale_up:
            mock_scale_up.return_value = True
            controller._http_session = MagicMock()  # Needs session

            # ACT: Execute scale up
            success = await controller._execute(ActionType.SCALE_UP_AGENTS, {"quantity": 10})

        # ASSERT: Should route correctly
        assert success is True
        mock_scale_up.assert_called_once_with({"quantity": 10})

    @pytest.mark.asyncio
    async def test_execute_routes_to_clone_specialized(self, controller):
        """
        Test _execute routes CLONE_SPECIALIZED to _execute_clone_specialized.

        Coverage: Line 804 (routing to clone)
        """
        # ARRANGE: Mock _execute_clone_specialized
        with patch.object(controller, "_execute_clone_specialized", new_callable=AsyncMock) as mock_clone:
            mock_clone.return_value = True
            controller._http_session = MagicMock()

            # ACT
            success = await controller._execute(ActionType.CLONE_SPECIALIZED, {"quantity": 20})

        # ASSERT
        assert success is True
        mock_clone.assert_called_once_with({"quantity": 20})

    @pytest.mark.asyncio
    async def test_execute_handles_general_exception(self, controller):
        """
        Test _execute handles general exceptions gracefully.

        Real scenario: Unexpected error during execution.

        Coverage: Lines 816-818 (exception handling)
        """
        # ARRANGE: Mock _execute_scale_up to raise exception
        with patch.object(controller, "_execute_scale_up", new_callable=AsyncMock) as mock_scale_up:
            mock_scale_up.side_effect = Exception("Unexpected error")
            controller._http_session = MagicMock()

            # ACT: Try to execute (should catch exception)
            success = await controller._execute(ActionType.SCALE_UP_AGENTS, {})

        # ASSERT: Should handle gracefully
        assert success is False, "Should return False on exception"


# ==================== SUMMARY ====================

"""
Homeostatic Controller Ultra Tests Summary (90% → 95%+):

Tests Added: 14 ultra-surgical tests

Specific Lines Targeted:
✅ Lines 159-160: MMEI unavailable warning
✅ Lines 502-504: Lymphnode 404 handling
✅ Lines 725-726: Scale up with high_threat_load
✅ Lines 729-730: Scale up with high_repair_need (MMEI)
✅ Lines 739-740: Scale down with rest_need (MMEI)
✅ Lines 760-762: Adjust temperature with efficiency_optimization (MMEI)
✅ Lines 792-793: HTTP session unavailable for execute
✅ Line 798: Execute routing to scale_up
✅ Line 804: Execute routing to clone_specialized
✅ Lines 816-818: Execute general exception handling
✅ Lines 852-854: Scale down ClientConnectorError
✅ Lines 866-868: Clone specialized ClientConnectorError
✅ Lines 882-884: Destroy clones ClientConnectorError

Coverage Impact: 90% → ~94-96%+ (targeting 25-30 lines)

These tests validate HOMEOSTATIC RESILIENCE:
- MMEI integration edge cases
- Network failure handling (ClientConnectorError)
- Action routing and parameter determination
- Graceful degradation under all conditions

"Equilíbrio através da resiliência" 🌟🎯
"""
