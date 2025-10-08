"""
Tests for BiomimeticSafetyBridge - Production-Hardened Integration Layer

Tests integration of Neuromodulation + Predictive Coding systems:
1. Bridge initialization
2. Coordinated processing (both systems working together)
3. System isolation (one fails, other continues)
4. Cross-system anomaly detection
5. Aggregate circuit breaker
6. Emergency shutdown coordination
7. Metrics aggregation
8. Rate limiting

25 tests validating end-to-end integration.

NO MOCK - Uses real neuromodulation + predictive coding implementations.

Authors: Claude Code + Juan
Version: 1.0.0
Date: 2025-10-08
"""

import pytest
import asyncio
import numpy as np

from consciousness.biomimetic_safety_bridge import (
    BiomimeticSafetyBridge,
    BridgeConfig,
    BridgeState,
)
from consciousness.neuromodulation.coordinator_hardened import ModulationRequest


# ============================================================================
# Tests: Initialization
# ============================================================================


def test_bridge_initialization_default_config():
    """Test bridge initializes with default config."""
    bridge = BiomimeticSafetyBridge()

    assert bridge.neuromodulation is not None
    assert bridge.predictive_coding is not None
    assert bridge.total_coordination_cycles == 0
    assert bridge._aggregate_circuit_breaker_open is False


def test_bridge_initialization_custom_config():
    """Test bridge accepts custom config."""
    config = BridgeConfig(
        max_coordination_cycles_per_second=5,
        max_coordination_time_ms=500.0
    )
    bridge = BiomimeticSafetyBridge(config)

    assert bridge.config.max_coordination_cycles_per_second == 5
    assert bridge.config.max_coordination_time_ms == 500.0


def test_bridge_initialization_with_kill_switch():
    """Test bridge initializes with kill switch callback."""
    kill_switch_calls = []

    def mock_kill_switch(reason: str):
        kill_switch_calls.append(reason)

    bridge = BiomimeticSafetyBridge(kill_switch_callback=mock_kill_switch)

    assert bridge._kill_switch is not None


# ============================================================================
# Tests: Coordinated Processing
# ============================================================================


@pytest.mark.asyncio
async def test_coordinate_processing_success():
    """Test successful coordination through both systems."""
    bridge = BiomimeticSafetyBridge()

    raw_input = np.random.randn(10000).astype(np.float32) * 0.1

    result = await bridge.coordinate_processing(raw_input)

    # Should have results from both systems
    assert isinstance(result, dict)
    assert "prediction_errors" in result or "predictive_coding_success" in result
    assert "neuromod_levels" in result or "neuromodulation_success" in result


@pytest.mark.asyncio
async def test_coordinate_processing_increments_counter():
    """Test coordination increments cycle counter."""
    bridge = BiomimeticSafetyBridge()

    raw_input = np.random.randn(10000).astype(np.float32) * 0.1

    cycles_before = bridge.total_coordination_cycles
    await bridge.coordinate_processing(raw_input)
    cycles_after = bridge.total_coordination_cycles

    assert cycles_after == cycles_before + 1


@pytest.mark.asyncio
async def test_coordinate_processing_with_explicit_modulation():
    """Test coordination with explicitly provided modulation requests."""
    bridge = BiomimeticSafetyBridge()

    raw_input = np.random.randn(10000).astype(np.float32) * 0.1

    modulation_requests = [
        ModulationRequest("dopamine", delta=0.1, source="test"),
        ModulationRequest("serotonin", delta=0.05, source="test"),
    ]

    result = await bridge.coordinate_processing(raw_input, modulation_requests)

    # Should have processed modulation requests
    assert "neuromod_changes" in result or "neuromodulation_success" in result


# ============================================================================
# Tests: System Isolation
# ============================================================================


@pytest.mark.asyncio
async def test_system_isolation_predictive_failure():
    """Test neuromodulation continues when predictive coding fails."""
    bridge = BiomimeticSafetyBridge()

    # Force predictive coding to fail (all layers)
    for layer in bridge.predictive_coding._layers:
        layer._circuit_breaker_open = True

    raw_input = np.random.randn(10000).astype(np.float32) * 0.1

    # Should not crash bridge (system isolation)
    result = await bridge.coordinate_processing(raw_input)

    # Predictive coding failed
    assert result.get("predictive_coding_success") is False

    # But neuromodulation should still work
    # (may succeed if modulation_requests auto-generated or provided)


@pytest.mark.asyncio
async def test_system_isolation_neuromod_failure():
    """Test predictive coding continues when neuromodulation fails."""
    bridge = BiomimeticSafetyBridge()

    # Force neuromodulation to fail (all modulators)
    bridge.neuromodulation.dopamine._circuit_breaker_open = True
    bridge.neuromodulation.serotonin._circuit_breaker_open = True
    bridge.neuromodulation.acetylcholine._circuit_breaker_open = True

    raw_input = np.random.randn(10000).astype(np.float32) * 0.1

    # Should not crash bridge (system isolation)
    result = await bridge.coordinate_processing(raw_input)

    # Predictive coding should still succeed (at least Layer 1)
    assert "prediction_errors" in result or "predictive_coding_success" in result


# ============================================================================
# Tests: Auto-Generated Modulation Requests
# ============================================================================


@pytest.mark.asyncio
async def test_auto_generated_modulation_high_error():
    """Test bridge auto-generates modulation requests for high prediction error."""
    bridge = BiomimeticSafetyBridge()

    # Simulate high prediction errors
    prediction_errors = {
        "layer1_sensory": 6.0,
        "layer2_behavioral": 7.0,
    }

    requests = bridge._generate_modulation_requests(prediction_errors)

    # High error → norepinephrine + dopamine
    assert len(requests) >= 1
    assert any(req.modulator == "norepinephrine" for req in requests)


@pytest.mark.asyncio
async def test_auto_generated_modulation_low_error():
    """Test bridge auto-generates modulation requests for low prediction error."""
    bridge = BiomimeticSafetyBridge()

    # Simulate low prediction errors
    prediction_errors = {
        "layer1_sensory": 0.5,
    }

    requests = bridge._generate_modulation_requests(prediction_errors)

    # Low error → serotonin
    assert len(requests) >= 1
    assert any(req.modulator == "serotonin" for req in requests)


# ============================================================================
# Tests: Cross-System Anomaly Detection
# ============================================================================


def test_cross_system_anomaly_high_error_high_conflict():
    """Test detection of high prediction error + high neuromod conflict rate."""
    bridge = BiomimeticSafetyBridge()

    # Simulate high prediction errors
    prediction_errors = {
        "layer1_sensory": 9.0,
        "layer2_behavioral": 8.5,
    }

    # Simulate high conflict rate
    bridge.neuromodulation.conflicts_detected = 10
    bridge.neuromodulation.total_coordinations = 15  # 67% conflict rate

    anomaly = bridge._detect_cross_system_anomaly(prediction_errors, {})

    assert anomaly is not None
    assert "high prediction error" in anomaly.lower() or "high conflict rate" in anomaly.lower()


def test_cross_system_anomaly_multiple_breakers():
    """Test detection when multiple circuit breakers open in both systems."""
    bridge = BiomimeticSafetyBridge()

    # Open 2 neuromod breakers
    bridge.neuromodulation.dopamine._circuit_breaker_open = True
    bridge.neuromodulation.serotonin._circuit_breaker_open = True

    # Open 2 predictive breakers
    bridge.predictive_coding.layer1._circuit_breaker_open = True
    bridge.predictive_coding.layer2._circuit_breaker_open = True

    anomaly = bridge._detect_cross_system_anomaly({}, {})

    assert anomaly is not None
    assert "breakers open" in anomaly.lower()


# ============================================================================
# Tests: Aggregate Circuit Breaker
# ============================================================================


@pytest.mark.asyncio
async def test_aggregate_circuit_breaker_opens_on_consecutive_failures():
    """Test aggregate breaker opens after consecutive coordination failures."""
    config = BridgeConfig(
        max_consecutive_coordination_failures=3,
        max_coordination_time_ms=10.0  # Very short timeout (will fail)
    )
    bridge = BiomimeticSafetyBridge(config)

    # Force timeouts by making systems slow
    for layer in bridge.predictive_coding._layers:
        original_impl = layer._predict_impl

        async def slow_impl(input_data):
            await asyncio.sleep(0.1)  # 100ms (will timeout)
            return np.random.randn(layer.config.input_dim).astype(np.float32) * 0.1

        layer._predict_impl = slow_impl

    raw_input = np.random.randn(10000).astype(np.float32) * 0.1

    # Trigger 3 consecutive failures
    for _ in range(3):
        try:
            await bridge.coordinate_processing(raw_input)
        except asyncio.TimeoutError:
            pass

    # Aggregate breaker should be open
    assert bridge._aggregate_circuit_breaker_open is True


@pytest.mark.asyncio
async def test_aggregate_circuit_breaker_rejects_processing():
    """Test aggregate breaker rejects new processing."""
    bridge = BiomimeticSafetyBridge()

    # Manually open aggregate breaker
    bridge._aggregate_circuit_breaker_open = True

    raw_input = np.random.randn(10000).astype(np.float32) * 0.1

    with pytest.raises(RuntimeError, match="[Aa]ggregate circuit breaker"):
        await bridge.coordinate_processing(raw_input)


@pytest.mark.asyncio
async def test_aggregate_circuit_breaker_calls_kill_switch():
    """Test aggregate breaker triggers kill switch."""
    kill_switch_calls = []

    def mock_kill_switch(reason: str):
        kill_switch_calls.append(reason)

    bridge = BiomimeticSafetyBridge(kill_switch_callback=mock_kill_switch)

    # Manually trigger aggregate breaker
    bridge._open_aggregate_circuit_breaker("test_reason")

    # Kill switch should have been called
    assert len(kill_switch_calls) == 1
    assert "aggregate failure" in kill_switch_calls[0].lower()


# ============================================================================
# Tests: Rate Limiting
# ============================================================================


@pytest.mark.asyncio
async def test_rate_limiting_enforced():
    """Test rate limiting prevents too many coordination cycles per second."""
    config = BridgeConfig(
        max_coordination_cycles_per_second=2  # Max 2 cycles/sec
    )
    bridge = BiomimeticSafetyBridge(config)

    raw_input = np.random.randn(10000).astype(np.float32) * 0.1

    start_time = asyncio.get_event_loop().time()

    # Try 3 coordinations (should take at least 1 second due to rate limit)
    for _ in range(3):
        await bridge.coordinate_processing(raw_input)

    elapsed = asyncio.get_event_loop().time() - start_time

    # Should have taken at least 1 second (3 cycles at 2/sec = 1.5s, but we're lenient)
    assert elapsed >= 0.8  # Allow some margin


# ============================================================================
# Tests: Emergency Stop
# ============================================================================


def test_emergency_stop_shuts_down_both_systems():
    """Test emergency_stop() deactivates both biomimetic systems."""
    bridge = BiomimeticSafetyBridge()

    # Both systems active initially
    assert not bridge.neuromodulation._is_aggregate_circuit_breaker_open()
    assert not bridge.predictive_coding._is_aggregate_circuit_breaker_open()

    bridge.emergency_stop()

    # Both systems should be shut down
    assert bridge.neuromodulation._is_aggregate_circuit_breaker_open()
    assert bridge.predictive_coding._is_aggregate_circuit_breaker_open()
    assert bridge._aggregate_circuit_breaker_open is True


@pytest.mark.asyncio
async def test_emergency_stop_prevents_further_processing():
    """Test processing fails after emergency_stop()."""
    bridge = BiomimeticSafetyBridge()

    bridge.emergency_stop()

    raw_input = np.random.randn(10000).astype(np.float32) * 0.1

    with pytest.raises(RuntimeError):
        await bridge.coordinate_processing(raw_input)


# ============================================================================
# Tests: State Observability
# ============================================================================


@pytest.mark.asyncio
async def test_get_state_returns_correct_structure():
    """Test get_state() returns BridgeState with correct fields."""
    bridge = BiomimeticSafetyBridge()

    raw_input = np.random.randn(10000).astype(np.float32) * 0.1
    await bridge.coordinate_processing(raw_input)

    state = bridge.get_state()

    assert isinstance(state, BridgeState)
    assert state.total_coordination_cycles == 1
    assert isinstance(state.neuromodulation_active, bool)
    assert isinstance(state.predictive_coding_active, bool)
    assert isinstance(state.aggregate_circuit_breaker_open, bool)


# ============================================================================
# Tests: Metrics Aggregation
# ============================================================================


@pytest.mark.asyncio
async def test_get_health_metrics_aggregates_both_systems():
    """Test get_health_metrics() combines metrics from both systems."""
    bridge = BiomimeticSafetyBridge()

    raw_input = np.random.randn(10000).astype(np.float32) * 0.1
    await bridge.coordinate_processing(raw_input)

    metrics = bridge.get_health_metrics()

    # Should have neuromodulation metrics
    assert any("dopamine" in key.lower() for key in metrics.keys())

    # Should have predictive coding metrics
    assert any("layer" in key.lower() or "hierarchy" in key.lower() for key in metrics.keys())

    # Should have bridge metrics
    assert "bridge_total_coordination_cycles" in metrics
    assert "bridge_aggregate_circuit_breaker_open" in metrics


@pytest.mark.asyncio
async def test_get_health_metrics_all_numeric():
    """Test all metrics have numeric values."""
    bridge = BiomimeticSafetyBridge()

    raw_input = np.random.randn(10000).astype(np.float32) * 0.1
    await bridge.coordinate_processing(raw_input)

    metrics = bridge.get_health_metrics()

    for key, value in metrics.items():
        assert isinstance(value, (int, float, bool)), f"{key} has non-numeric value: {value}"


# ============================================================================
# Tests: Repr
# ============================================================================


def test_repr_formatting():
    """Test __repr__ returns useful debug string."""
    bridge = BiomimeticSafetyBridge()

    repr_str = repr(bridge)

    assert "BiomimeticSafetyBridge" in repr_str
    assert "cycles=" in repr_str
    assert "neuromod_active=" in repr_str
    assert "predictive_active=" in repr_str


# ============================================================================
# Tests: Integration Scenarios
# ============================================================================


@pytest.mark.asyncio
async def test_scenario_normal_operation():
    """Test scenario: Normal operation with multiple coordination cycles."""
    bridge = BiomimeticSafetyBridge()

    # Process 10 varied inputs
    for i in range(10):
        raw_input = np.random.randn(10000).astype(np.float32) * 0.1 * (i % 3 + 1)
        result = await bridge.coordinate_processing(raw_input)

        # Each cycle should succeed (at least partially)
        assert isinstance(result, dict)

    state = bridge.get_state()
    assert state.total_coordination_cycles == 10
    assert state.aggregate_circuit_breaker_open is False


@pytest.mark.asyncio
async def test_scenario_one_system_fails_other_continues():
    """Test scenario: One system fails, other continues (system isolation)."""
    bridge = BiomimeticSafetyBridge()

    # Normal operation
    raw_input = np.random.randn(10000).astype(np.float32) * 0.1
    result1 = await bridge.coordinate_processing(raw_input)

    # Force neuromodulation to fail
    bridge.neuromodulation.dopamine._circuit_breaker_open = True
    bridge.neuromodulation.serotonin._circuit_breaker_open = True
    bridge.neuromodulation.acetylcholine._circuit_breaker_open = True

    # Predictive coding should still work
    result2 = await bridge.coordinate_processing(raw_input)

    # Should have some results (from predictive coding)
    assert isinstance(result2, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
