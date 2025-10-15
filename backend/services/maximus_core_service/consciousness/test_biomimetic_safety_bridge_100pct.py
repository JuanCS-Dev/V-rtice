"""
Biomimetic Safety Bridge - Final Push to 100%
==============================================

Target missing lines (91.46% → 100.00%):
- 204: Kill switch call when aggregate breaker is open
- 225: Pop oldest coordination time (>100 samples)
- 252-261: General exception handling + aggregate breaker
- 313-315: Cross-system anomaly detection + counter
- 336: Empty prediction errors early return
- 349: Medium error (2.0-5.0) modulation request

PADRÃO PAGANI ABSOLUTO - 100% MEANS 100%
"""

import asyncio
import pytest
import pytest_asyncio
import numpy as np

from consciousness.biomimetic_safety_bridge import (
    BiomimeticSafetyBridge,
    BridgeConfig,
)
from consciousness.neuromodulation.coordinator_hardened import ModulationRequest


@pytest_asyncio.fixture
async def bridge():
    """Create bridge for testing."""
    bridge = BiomimeticSafetyBridge()
    yield bridge
    bridge.emergency_stop()


class TestBiomimeticBridgeFinal14Lines:
    """Final tests to achieve 100% coverage."""

    @pytest.mark.asyncio
    async def test_aggregate_breaker_triggers_kill_switch_line_204(self):
        """Test kill switch is called when aggregate breaker opens (line 204)."""
        kill_switch_called = []

        def mock_kill_switch(reason: str):
            kill_switch_called.append(reason)

        bridge = BiomimeticSafetyBridge(kill_switch_callback=mock_kill_switch)

        # Open aggregate breaker
        bridge._aggregate_circuit_breaker_open = True

        # Try to coordinate - should trigger kill switch
        with pytest.raises(RuntimeError, match="Aggregate circuit breaker OPEN"):
            await bridge.coordinate_processing(np.random.rand(10))

        # Kill switch should have been called (line 204)
        assert len(kill_switch_called) == 1
        assert "aggregate circuit breaker open" in kill_switch_called[0]

    @pytest.mark.asyncio
    async def test_coordination_time_tracking_pops_oldest_line_225(self):
        """Test coordination times list pops oldest entry when >100 (line 225)."""
        bridge = BiomimeticSafetyBridge()

        # Pre-fill with 101 entries
        bridge._coordination_times = list(range(101))

        # Do a successful coordination
        result = await bridge.coordinate_processing(np.random.rand(10))

        # Should have popped oldest (line 225)
        assert len(bridge._coordination_times) <= 101
        assert 0 not in bridge._coordination_times  # Oldest removed

    @pytest.mark.asyncio
    async def test_coordination_general_exception_lines_252_261(self):
        """Test general exception handling in coordinate_processing (lines 252-261)."""
        bridge = BiomimeticSafetyBridge()

        # Mock _coordinate_impl to raise exception
        original_impl = bridge._coordinate_impl

        async def failing_impl(*args, **kwargs):
            raise ValueError("Intentional coordination error")

        bridge._coordinate_impl = failing_impl

        # Should catch exception and increment failures (lines 253-254)
        with pytest.raises(ValueError):
            await bridge.coordinate_processing(np.random.rand(10))

        assert bridge.total_coordination_failures == 1
        assert bridge.consecutive_coordination_failures == 1

        # Restore and trigger multiple failures to open breaker (lines 258-259)
        bridge._coordinate_impl = failing_impl
        bridge.config.max_consecutive_coordination_failures = 3

        for _ in range(2):  # 2 more failures = 3 total
            with pytest.raises(ValueError):
                await bridge.coordinate_processing(np.random.rand(10))

        # Aggregate breaker should be open now (line 259)
        assert bridge._aggregate_circuit_breaker_open

    @pytest.mark.asyncio
    async def test_cross_system_anomaly_detection_lines_313_315(self):
        """Test cross-system anomaly detection (lines 313-315)."""
        config = BridgeConfig(
            anomaly_threshold_prediction_error=5.0,  # Low threshold
            anomaly_threshold_neuromod_conflict_rate=0.1  # Low threshold
        )
        bridge = BiomimeticSafetyBridge(config=config)

        # Induce high prediction errors and high conflict rate
        # Need to manually craft the scenario

        # Mock detect to return anomaly
        original_detect = bridge._detect_cross_system_anomaly

        def mock_detect(*args, **kwargs):
            return "Mock anomaly for testing"

        bridge._detect_cross_system_anomaly = mock_detect

        # Process - should detect anomaly (lines 313-315)
        result = await bridge.coordinate_processing(np.random.rand(10))

        # Anomaly should be detected and counted
        assert bridge.cross_system_anomalies_detected >= 1
        assert result.get("cross_system_anomaly") is True

        bridge._detect_cross_system_anomaly = original_detect

    def test_generate_modulation_empty_prediction_errors_line_336(self):
        """Test _generate_modulation_requests with empty dict (line 336)."""
        bridge = BiomimeticSafetyBridge()

        # Empty prediction errors → early return (line 336)
        requests = bridge._generate_modulation_requests({})

        assert requests == []

    def test_generate_modulation_medium_error_line_349(self):
        """Test _generate_modulation_requests with medium error (line 349)."""
        bridge = BiomimeticSafetyBridge()

        # Medium error (2.0-5.0) → acetylcholine request (line 349)
        prediction_errors = {"layer1": 3.5, "layer2": 3.0}  # avg = 3.25
        requests = bridge._generate_modulation_requests(prediction_errors)

        assert len(requests) == 1
        assert requests[0].modulator == "acetylcholine"
        assert requests[0].delta == 0.1
        assert "medium_prediction_error" in requests[0].source


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--asyncio-mode=auto"])
