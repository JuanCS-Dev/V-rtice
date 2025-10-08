"""
Tests for PredictiveCodingLayerBase - Production-Hardened Base Class

Tests ALL safety features inherited by all 5 layers:
1. Bounded prediction errors [0, max_prediction_error]
2. Timeout protection (max computation time)
3. Attention gating (max predictions per cycle)
4. Circuit breaker (consecutive errors/timeouts)
5. Layer isolation (exceptions don't propagate)
6. Kill switch integration
7. Full observability (metrics export)

NO MOCK - Uses concrete test implementation of base class.

Authors: Claude Code + Juan
Version: 1.0.0
Date: 2025-10-08
"""

import pytest
import asyncio
import numpy as np

from consciousness.predictive_coding.layer_base_hardened import (
    PredictiveCodingLayerBase,
    LayerConfig,
    LayerState,
)


# ============================================================================
# Test Implementation of Base Class
# ============================================================================


class TestLayer(PredictiveCodingLayerBase):
    """Concrete test implementation of base class."""

    def __init__(self, config: LayerConfig, kill_switch_callback=None, **kwargs):
        super().__init__(config, kill_switch_callback)
        self._should_fail = kwargs.get("should_fail", False)
        self._delay_ms = kwargs.get("delay_ms", 0)

    def get_layer_name(self) -> str:
        return "TestLayer"

    async def _predict_impl(self, input_data):
        """Simple echo prediction with optional delay/failure."""
        if self._delay_ms > 0:
            await asyncio.sleep(self._delay_ms / 1000.0)

        if self._should_fail:
            raise RuntimeError("Simulated prediction failure")

        # Echo input
        return input_data

    def _compute_error_impl(self, predicted, actual) -> float:
        """Simple MSE."""
        pred = np.array(predicted, dtype=np.float32)
        act = np.array(actual, dtype=np.float32)
        return float(np.mean((pred - act) ** 2))


# ============================================================================
# Tests: Initialization & Configuration
# ============================================================================


def test_layer_initialization():
    """Test layer initialization with valid config."""
    config = LayerConfig(layer_id=1, input_dim=100, hidden_dim=50)
    layer = TestLayer(config)

    assert layer.config.layer_id == 1
    assert layer.config.input_dim == 100
    assert layer.config.hidden_dim == 50
    assert layer._is_active is True
    assert layer._circuit_breaker_open is False


def test_layer_initialization_with_kill_switch():
    """Test layer initialization with kill switch callback."""
    kill_switch_called = []

    def mock_kill_switch(reason: str):
        kill_switch_called.append(reason)

    config = LayerConfig(layer_id=2, input_dim=50, hidden_dim=25)
    layer = TestLayer(config, kill_switch_callback=mock_kill_switch)

    assert layer._kill_switch is not None


def test_layer_config_validation():
    """Test config validation rejects invalid parameters."""
    with pytest.raises(AssertionError):
        LayerConfig(layer_id=0, input_dim=100, hidden_dim=50)  # layer_id must be 1-5

    with pytest.raises(AssertionError):
        LayerConfig(layer_id=6, input_dim=100, hidden_dim=50)  # layer_id must be 1-5

    with pytest.raises(AssertionError):
        LayerConfig(layer_id=1, input_dim=0, hidden_dim=50)  # input_dim must be > 0

    with pytest.raises(AssertionError):
        LayerConfig(layer_id=1, input_dim=100, hidden_dim=0)  # hidden_dim must be > 0


# ============================================================================
# Tests: Bounded Prediction Errors
# ============================================================================


@pytest.mark.asyncio
async def test_bounded_prediction_errors_clipping():
    """Test prediction errors are clipped to max_prediction_error."""
    config = LayerConfig(
        layer_id=1,
        input_dim=10,
        hidden_dim=5,
        max_prediction_error=1.0  # HARD CLIP at 1.0
    )
    layer = TestLayer(config)

    # Predict
    input_data = np.ones(10) * 5.0
    prediction = await layer.predict(input_data)

    # Compute error with very different actual (would produce error > 1.0)
    actual = np.ones(10) * 10.0  # Large difference
    error = layer.compute_error(prediction, actual)

    # Error should be clipped to max_prediction_error
    assert error <= config.max_prediction_error


@pytest.mark.asyncio
async def test_bounded_errors_tracking():
    """Test bounded_errors counter tracks how many times we clipped."""
    config = LayerConfig(
        layer_id=1,
        input_dim=10,
        hidden_dim=5,
        max_prediction_error=0.1  # Very low clip threshold
    )
    layer = TestLayer(config)

    # Predict
    input_data = np.ones(10)
    prediction = await layer.predict(input_data)

    # Compute error with large difference (will clip)
    actual = np.ones(10) * 100.0
    layer.compute_error(prediction, actual)

    state = layer.get_state()
    assert state.bounded_errors >= 1  # Should have clipped at least once


# ============================================================================
# Tests: Timeout Protection
# ============================================================================


@pytest.mark.asyncio
async def test_timeout_protection_triggers():
    """Test timeout protection activates when prediction takes too long."""
    config = LayerConfig(
        layer_id=1,
        input_dim=10,
        hidden_dim=5,
        max_computation_time_ms=50.0  # 50ms timeout
    )
    # Layer with 200ms delay (will timeout)
    layer = TestLayer(config, delay_ms=200)

    input_data = np.ones(10)
    result = await layer.predict(input_data)

    # Should return None after timeout
    assert result is None

    state = layer.get_state()
    assert state.total_timeouts == 1


@pytest.mark.asyncio
async def test_timeout_protection_increments_consecutive_counter():
    """Test consecutive timeouts increment counter."""
    config = LayerConfig(
        layer_id=1,
        input_dim=10,
        hidden_dim=5,
        max_computation_time_ms=20.0,
        max_consecutive_timeouts=3
    )
    layer = TestLayer(config, delay_ms=50)  # Will timeout

    input_data = np.ones(10)

    # Timeout 2 times
    await layer.predict(input_data)
    await layer.predict(input_data)

    state = layer.get_state()
    assert state.consecutive_timeouts == 2


@pytest.mark.asyncio
async def test_timeout_opens_circuit_breaker():
    """Test consecutive timeouts open circuit breaker."""
    config = LayerConfig(
        layer_id=1,
        input_dim=10,
        hidden_dim=5,
        max_computation_time_ms=20.0,
        max_consecutive_timeouts=3
    )
    layer = TestLayer(config, delay_ms=50)  # Will timeout

    input_data = np.ones(10)

    # Timeout 3 times → circuit breaker opens
    for _ in range(3):
        await layer.predict(input_data)

    state = layer.get_state()
    assert state.circuit_breaker_open is True


# ============================================================================
# Tests: Attention Gating
# ============================================================================


@pytest.mark.asyncio
async def test_attention_gating_blocks_excess_predictions():
    """Test attention gate blocks predictions beyond max_predictions_per_cycle."""
    config = LayerConfig(
        layer_id=1,
        input_dim=10,
        hidden_dim=5,
        max_predictions_per_cycle=3  # Max 3 per cycle
    )
    layer = TestLayer(config)

    input_data = np.ones(10)

    # Make 5 predictions (should block after 3)
    results = []
    for _ in range(5):
        result = await layer.predict(input_data)
        results.append(result)

    # First 3 should succeed, last 2 should be None (blocked)
    assert results[0] is not None
    assert results[1] is not None
    assert results[2] is not None
    assert results[3] is None
    assert results[4] is None


@pytest.mark.asyncio
async def test_attention_gate_resets_on_reset_cycle():
    """Test reset_cycle() resets attention gate counter."""
    config = LayerConfig(
        layer_id=1,
        input_dim=10,
        hidden_dim=5,
        max_predictions_per_cycle=2
    )
    layer = TestLayer(config)

    input_data = np.ones(10)

    # Make 2 predictions (exhaust cycle)
    await layer.predict(input_data)
    await layer.predict(input_data)

    # Next should be blocked
    result = await layer.predict(input_data)
    assert result is None

    # Reset cycle
    layer.reset_cycle()

    # Now should work again
    result = await layer.predict(input_data)
    assert result is not None


# ============================================================================
# Tests: Circuit Breaker
# ============================================================================


@pytest.mark.asyncio
async def test_circuit_breaker_opens_on_consecutive_errors():
    """Test circuit breaker opens after consecutive errors."""
    config = LayerConfig(
        layer_id=1,
        input_dim=10,
        hidden_dim=5,
        max_consecutive_errors=3
    )
    layer = TestLayer(config, should_fail=True)  # Will always fail

    input_data = np.ones(10)

    # Trigger 3 consecutive errors
    for _ in range(3):
        await layer.predict(input_data)

    state = layer.get_state()
    assert state.circuit_breaker_open is True


@pytest.mark.asyncio
async def test_circuit_breaker_rejects_predictions():
    """Test circuit breaker rejects predictions when open."""
    config = LayerConfig(
        layer_id=1,
        input_dim=10,
        hidden_dim=5,
        max_consecutive_errors=2
    )
    layer = TestLayer(config, should_fail=True)

    input_data = np.ones(10)

    # Open circuit breaker
    await layer.predict(input_data)
    await layer.predict(input_data)

    # Next prediction should raise RuntimeError
    with pytest.raises(RuntimeError, match="circuit breaker is open"):
        await layer.predict(input_data)


@pytest.mark.asyncio
async def test_circuit_breaker_calls_kill_switch():
    """Test circuit breaker triggers kill switch when opening."""
    kill_switch_calls = []

    def mock_kill_switch(reason: str):
        kill_switch_calls.append(reason)

    config = LayerConfig(
        layer_id=1,
        input_dim=10,
        hidden_dim=5,
        max_consecutive_errors=2
    )
    layer = TestLayer(config, kill_switch_callback=mock_kill_switch, should_fail=True)

    input_data = np.ones(10)

    # Trigger circuit breaker
    await layer.predict(input_data)
    await layer.predict(input_data)

    # Kill switch should have been called
    assert len(kill_switch_calls) == 1
    assert "circuit breaker" in kill_switch_calls[0].lower()


@pytest.mark.asyncio
async def test_consecutive_errors_reset_on_success():
    """Test consecutive error counter resets after successful prediction."""
    config = LayerConfig(
        layer_id=1,
        input_dim=10,
        hidden_dim=5,
        max_consecutive_errors=3
    )
    layer_fail = TestLayer(config, should_fail=True)
    layer_success = TestLayer(config, should_fail=False)

    input_data = np.ones(10)

    # Fail twice
    await layer_fail.predict(input_data)
    await layer_fail.predict(input_data)

    state = layer_fail.get_state()
    assert state.consecutive_errors == 2

    # Now reconfigure to succeed
    layer_fail._should_fail = False

    # Success should reset counter
    await layer_fail.predict(input_data)

    state = layer_fail.get_state()
    assert state.consecutive_errors == 0


# ============================================================================
# Tests: Emergency Stop
# ============================================================================


def test_emergency_stop_opens_circuit_breaker():
    """Test emergency_stop() opens circuit breaker."""
    config = LayerConfig(layer_id=1, input_dim=10, hidden_dim=5)
    layer = TestLayer(config)

    assert layer._circuit_breaker_open is False

    layer.emergency_stop()

    assert layer._circuit_breaker_open is True
    assert layer._is_active is False


@pytest.mark.asyncio
async def test_emergency_stop_rejects_predictions():
    """Test predictions fail after emergency stop."""
    config = LayerConfig(layer_id=1, input_dim=10, hidden_dim=5)
    layer = TestLayer(config)

    layer.emergency_stop()

    input_data = np.ones(10)

    with pytest.raises(RuntimeError, match="circuit breaker is open"):
        await layer.predict(input_data)


# ============================================================================
# Tests: Observability (Metrics Export)
# ============================================================================


@pytest.mark.asyncio
async def test_get_state_returns_correct_metrics():
    """Test get_state() returns accurate layer state."""
    config = LayerConfig(layer_id=1, input_dim=10, hidden_dim=5)
    layer = TestLayer(config)

    input_data = np.ones(10)

    # Make some predictions
    await layer.predict(input_data)
    await layer.predict(input_data)

    state = layer.get_state()

    assert state.layer_id == 1
    assert state.is_active is True
    assert state.total_predictions == 2
    assert state.circuit_breaker_open is False


@pytest.mark.asyncio
async def test_get_health_metrics_exports_all_metrics():
    """Test get_health_metrics() exports all required metrics."""
    config = LayerConfig(layer_id=1, input_dim=10, hidden_dim=5)
    layer = TestLayer(config)

    input_data = np.ones(10)
    await layer.predict(input_data)

    metrics = layer.get_health_metrics()

    # Check all expected keys present
    assert "testlayer_is_active" in metrics
    assert "testlayer_circuit_breaker_open" in metrics
    assert "testlayer_total_predictions" in metrics
    assert "testlayer_total_errors" in metrics
    assert "testlayer_total_timeouts" in metrics
    assert "testlayer_bounded_errors" in metrics
    assert "testlayer_error_rate" in metrics
    assert "testlayer_timeout_rate" in metrics
    assert "testlayer_avg_prediction_error" in metrics
    assert "testlayer_avg_computation_time_ms" in metrics


def test_repr_formatting():
    """Test __repr__ returns useful debug string."""
    config = LayerConfig(layer_id=1, input_dim=10, hidden_dim=5)
    layer = TestLayer(config)

    repr_str = repr(layer)

    assert "TestLayer" in repr_str
    assert "active=" in repr_str
    assert "predictions=" in repr_str


# ============================================================================
# Run Tests
# ============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
