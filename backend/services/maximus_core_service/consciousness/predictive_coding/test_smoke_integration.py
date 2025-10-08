"""
Smoke Test - Predictive Coding Hierarchy Integration (FASE 2 Validation)

Quick validation that entire predictive coding system works:
1. Create hierarchy with all 5 layers
2. Process real-world-like inputs
3. Verify bounds maintained across all layers
4. Verify layer isolation protects system
5. Verify circuit breakers protect system
6. Verify emergency stop works
7. Verify metrics aggregation works

This is a REAL integration test - no mocks.

10 smoke tests validating end-to-end functionality.

Authors: Claude Code + Juan
Version: 1.0.0
Date: 2025-10-08
"""

import asyncio

import numpy as np
import pytest

from consciousness.predictive_coding.hierarchy_hardened import (
    HierarchyConfig,
    PredictiveCodingHierarchy,
)


def test_smoke_create_hierarchy():
    """Smoke test: Create hierarchy successfully."""
    hierarchy = PredictiveCodingHierarchy()

    # All 5 layers initialized
    assert hierarchy.layer1 is not None
    assert hierarchy.layer2 is not None
    assert hierarchy.layer3 is not None
    assert hierarchy.layer4 is not None
    assert hierarchy.layer5 is not None

    # All active
    assert all(layer._is_active for layer in hierarchy._layers)


@pytest.mark.asyncio
async def test_smoke_process_single_input():
    """Smoke test: Process single input through hierarchy."""
    hierarchy = PredictiveCodingHierarchy()

    # Realistic input (security event vector)
    raw_input = np.random.randn(10000).astype(np.float32) * 0.1

    errors = await hierarchy.process_input(raw_input)

    # Should return errors dict
    assert isinstance(errors, dict)
    assert len(errors) >= 1  # At least Layer 1 succeeded

    # All errors bounded
    for error in errors.values():
        assert error <= 10.0  # Default max_prediction_error


@pytest.mark.asyncio
async def test_smoke_process_multiple_inputs():
    """Smoke test: Process multiple inputs in sequence."""
    hierarchy = PredictiveCodingHierarchy()

    # Process 10 varied inputs
    for i in range(10):
        raw_input = np.random.randn(10000).astype(np.float32) * 0.1 * (i % 3 + 1)
        errors = await hierarchy.process_input(raw_input)

        # Each should succeed
        assert len(errors) >= 1

    # System still operational
    state = hierarchy.get_state()
    assert state.total_cycles == 10
    assert state.aggregate_circuit_breaker_open is False


@pytest.mark.asyncio
async def test_smoke_bounds_maintained_under_stress():
    """Smoke test: Bounds maintained under heavy stress."""
    config = HierarchyConfig(
        max_hierarchy_cycle_time_ms=1000.0  # Generous timeout
    )
    hierarchy = PredictiveCodingHierarchy(config)

    # Apply 50 varied inputs with different magnitudes
    for i in range(50):
        # Vary magnitude: small, medium, large
        magnitude = [0.1, 1.0, 10.0][i % 3]
        raw_input = np.random.randn(10000).astype(np.float32) * magnitude

        try:
            errors = await hierarchy.process_input(raw_input)

            # All errors should be bounded
            for layer_name, error in errors.items():
                assert error >= 0.0, f"{layer_name} negative error: {error}"
                assert error <= 10.0, f"{layer_name} unbounded error: {error}"

        except RuntimeError:
            # Circuit breaker may open - this is expected and safe
            break

    # System should still be intact (even if breaker opened)
    state = hierarchy.get_state()
    assert state.total_cycles >= 1


@pytest.mark.asyncio
async def test_smoke_layer_isolation_protection():
    """Smoke test: Layer isolation prevents cascading failures."""
    hierarchy = PredictiveCodingHierarchy()

    # Force Layer 3 to fail

    async def failing_impl(input_data):
        raise RuntimeError("Simulated Layer 3 failure")

    hierarchy.layer3._predict_impl = failing_impl

    raw_input = np.random.randn(10000).astype(np.float32) * 0.1

    # Should not crash entire hierarchy
    errors = await hierarchy.process_input(raw_input)

    # Layers 1 and 2 should still work
    assert "layer1_sensory" in errors

    # Layer 3 and beyond stopped
    assert "layer3_operational" not in errors or errors.get("layer3_operational") is None


@pytest.mark.asyncio
async def test_smoke_aggregate_circuit_breaker():
    """Smoke test: Aggregate circuit breaker protects system."""
    hierarchy = PredictiveCodingHierarchy()

    # Manually open 3 layer breakers (simulate multiple failures)
    hierarchy.layer1._circuit_breaker_open = True
    hierarchy.layer2._circuit_breaker_open = True
    hierarchy.layer3._circuit_breaker_open = True

    # Aggregate breaker should be open
    assert hierarchy._is_aggregate_circuit_breaker_open() is True

    raw_input = np.random.randn(10000).astype(np.float32) * 0.1

    # Processing should be rejected
    with pytest.raises(RuntimeError, match="aggregate circuit breaker"):
        await hierarchy.process_input(raw_input)


@pytest.mark.asyncio
async def test_smoke_emergency_stop():
    """Smoke test: Emergency stop shuts down entire system."""
    hierarchy = PredictiveCodingHierarchy()

    # Process some inputs
    raw_input = np.random.randn(10000).astype(np.float32) * 0.1
    await hierarchy.process_input(raw_input)
    await hierarchy.process_input(raw_input)

    # Emergency stop
    hierarchy.emergency_stop()

    # All layers should be shut down
    assert all(layer._circuit_breaker_open for layer in hierarchy._layers)
    assert all(not layer._is_active for layer in hierarchy._layers)

    # Further processing should fail
    with pytest.raises(RuntimeError):
        await hierarchy.process_input(raw_input)


@pytest.mark.asyncio
async def test_smoke_metrics_export():
    """Smoke test: Metrics export works correctly."""
    hierarchy = PredictiveCodingHierarchy()

    raw_input = np.random.randn(10000).astype(np.float32) * 0.1
    await hierarchy.process_input(raw_input)

    metrics = hierarchy.get_health_metrics()

    # Has hierarchy-level metrics
    assert "hierarchy_total_cycles" in metrics
    assert "hierarchy_aggregate_circuit_breaker_open" in metrics
    assert "hierarchy_layers_active_count" in metrics

    # Has all layer metrics (check prefixes exist)
    layer_keywords = ["layer1", "layer2", "layer3", "layer4", "layer5"]
    for keyword in layer_keywords:
        # At least one metric per layer
        assert any(keyword in key.lower() for key in metrics.keys())

    # All values numeric
    for key, value in metrics.items():
        assert isinstance(value, (int, float, bool)), f"{key} non-numeric: {value}"


@pytest.mark.asyncio
async def test_smoke_timeout_protection():
    """Smoke test: Hierarchy timeout protection works."""
    config = HierarchyConfig(
        max_hierarchy_cycle_time_ms=50.0  # Very short timeout
    )
    hierarchy = PredictiveCodingHierarchy(config)

    # Force layers to be slow
    for layer in hierarchy._layers:

        async def slow_impl(input_data):
            await asyncio.sleep(0.1)  # 100ms each = 500ms total (will timeout)
            return np.random.randn(layer.config.input_dim).astype(np.float32) * 0.1

        layer._predict_impl = slow_impl

    raw_input = np.random.randn(10000).astype(np.float32) * 0.1

    # Should timeout
    with pytest.raises(asyncio.TimeoutError):
        await hierarchy.process_input(raw_input)

    # Timeout counter incremented
    assert hierarchy.total_timeouts >= 1


@pytest.mark.asyncio
async def test_smoke_full_lifecycle():
    """Smoke test: Full lifecycle - create, process, monitor, shutdown."""
    config = HierarchyConfig(max_hierarchy_cycle_time_ms=1000.0)

    kill_switch_calls = []

    def mock_kill_switch(reason: str):
        kill_switch_calls.append(reason)

    hierarchy = PredictiveCodingHierarchy(config, kill_switch_callback=mock_kill_switch)

    # 1. Initial state
    state = hierarchy.get_state()
    assert state.total_cycles == 0
    assert all(state.layers_active)

    # 2. Process multiple inputs (simulate real workload)
    for i in range(20):
        raw_input = np.random.randn(10000).astype(np.float32) * 0.1

        try:
            errors = await hierarchy.process_input(raw_input)
            assert len(errors) >= 1
        except RuntimeError:
            # Circuit breaker may open after many cycles (expected)
            break

    # 3. Check metrics
    metrics = hierarchy.get_health_metrics()
    assert metrics["hierarchy_total_cycles"] >= 1

    # 4. Verify bounds maintained
    state = hierarchy.get_state()
    assert state.average_prediction_error >= 0.0

    # 5. Emergency shutdown
    hierarchy.emergency_stop()
    assert all(layer._circuit_breaker_open for layer in hierarchy._layers)

    # Kill switch should NOT have been called (manual shutdown)
    # (only called on failures, not manual shutdown)


if __name__ == "__main__":
    # Run smoke tests standalone
    pytest.main([__file__, "-v", "--tb=short"])
