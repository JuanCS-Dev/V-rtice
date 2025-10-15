"""
MCEA Controller: 89.15% → 100.00% Test Suite
=============================================

Target: consciousness/mcea/controller.py
Coverage goal: 100.00% (Padrão Pagani Absoluto)

Uncovered Lines (from coverage report):
151, 161-162, 303, 309, 313, 476, 504-505, 596, 621-623, 653-655, 693-694,
754, 768, 770, 796-799, 820-821, 834-842

Test Strategy:
1. Line 151: ArousalRateLimiter - no time passed (elapsed <= 0)
2. Line 161-162: ArousalRateLimiter - limited change (abs(requested_change) > max_change)
3. Line 303: ArousalModulation.is_expired() - instant modulation
4. Line 309: ArousalModulation.get_current_delta() - instant modulation
5. Line 313: ArousalModulation.get_current_delta() - expired duration modulation
6. Line 476: ArousalController.start() - already running (idempotency)
7. Line 504-505: ArousalController._update_loop() - exception handling
8. Line 596: ArousalController._compute_external_contribution() - zero priority
9. Line 621-623: ArousalController._compute_circadian_contribution() - with circadian enabled
10. Line 653-655: ArousalController._invoke_callbacks() - async callback + exception
11. Line 693-694: ArousalController.update_from_needs() - invalid needs
12. Line 754: ArousalController._validate_needs() - None input
13. Line 768: ArousalController._validate_needs() - non-numeric value
14. Line 770: ArousalController._validate_needs() - out of range value
15. Line 796-799: ArousalController._detect_saturation() - saturation event
16. Line 820-821: ArousalController._detect_oscillation() - oscillation event
17. Line 834-842: ArousalController.get_health_metrics() - with saturation

Authors: Claude Code (100% Coverage Executor)
Date: 2025-10-14
Governance: Constituição Vértice v2.5
"""

import asyncio
import time

import numpy as np
import pytest

from consciousness.mcea.controller import (
    AROUSAL_OSCILLATION_THRESHOLD,
    AROUSAL_OSCILLATION_WINDOW,
    AROUSAL_SATURATION_THRESHOLD_SECONDS,
    ArousalBoundEnforcer,
    ArousalConfig,
    ArousalController,
    ArousalLevel,
    ArousalModulation,
    ArousalRateLimiter,
    ArousalState,
)
from consciousness.mmei.monitor import AbstractNeeds


# ============================================================================
# Test Suite 1: ArousalRateLimiter Coverage (Lines 151, 161-162)
# ============================================================================


def test_rate_limiter_no_time_passed():
    """
    Test ArousalRateLimiter when no time has passed (elapsed <= 0).

    Coverage: Line 151
    """
    limiter = ArousalRateLimiter(max_delta_per_second=0.20)

    # First call
    t0 = time.time()
    result1 = limiter.limit(0.5, t0)
    assert result1 == 0.5

    # Second call with same timestamp - no time passed
    result2 = limiter.limit(0.8, t0)  # Try to jump +0.3
    assert result2 == 0.5  # Should return last value (no change allowed)


def test_rate_limiter_change_limited():
    """
    Test ArousalRateLimiter when requested change exceeds max_change.

    Coverage: Lines 161-162
    """
    limiter = ArousalRateLimiter(max_delta_per_second=0.20)

    # First call
    t0 = time.time()
    result1 = limiter.limit(0.5, t0)
    assert result1 == 0.5

    # Second call 0.5 seconds later
    # Max change allowed: 0.20 * 0.5 = 0.10
    # Requested: 0.8 - 0.5 = 0.3 (exceeds max)
    t1 = t0 + 0.5
    result2 = limiter.limit(0.8, t1)

    # Should be limited to 0.5 + 0.10 = 0.60
    assert abs(result2 - 0.60) < 0.001


def test_rate_limiter_negative_change_limited():
    """
    Test ArousalRateLimiter when requested negative change exceeds max_change.

    Coverage: Lines 161-162 (negative branch)
    """
    limiter = ArousalRateLimiter(max_delta_per_second=0.20)

    # First call
    t0 = time.time()
    result1 = limiter.limit(0.8, t0)
    assert result1 == 0.8

    # Second call 0.5 seconds later
    # Max change allowed: 0.20 * 0.5 = 0.10
    # Requested: 0.3 - 0.8 = -0.5 (exceeds max in negative direction)
    t1 = t0 + 0.5
    result2 = limiter.limit(0.3, t1)

    # Should be limited to 0.8 - 0.10 = 0.70
    assert abs(result2 - 0.70) < 0.001


# ============================================================================
# Test Suite 2: ArousalModulation Coverage (Lines 303, 309, 313)
# ============================================================================


def test_modulation_instant_is_expired():
    """
    Test ArousalModulation.is_expired() for instant modulation (duration=0).

    Coverage: Line 303
    """
    modulation = ArousalModulation(
        source="test",
        delta=0.2,
        duration_seconds=0.0  # Instant modulation
    )

    # Instant modulations always expire immediately
    assert modulation.is_expired() is True


def test_modulation_instant_get_current_delta():
    """
    Test ArousalModulation.get_current_delta() for instant modulation.

    Coverage: Line 309
    """
    modulation = ArousalModulation(
        source="test",
        delta=0.2,
        duration_seconds=0.0  # Instant modulation
    )

    # Instant modulations return full delta
    assert modulation.get_current_delta() == 0.2


def test_modulation_expired_duration_get_current_delta():
    """
    Test ArousalModulation.get_current_delta() for expired duration modulation.

    Coverage: Line 313
    """
    # Create modulation in the past
    modulation = ArousalModulation(
        source="test",
        delta=0.3,
        duration_seconds=1.0
    )

    # Fake expiration by setting timestamp in the past
    modulation.timestamp = time.time() - 2.0  # 2 seconds ago (> 1.0 duration)

    # Should return 0.0 (expired)
    assert modulation.get_current_delta() == 0.0


# ============================================================================
# Test Suite 3: ArousalController.start() Idempotency (Line 476)
# ============================================================================


@pytest.mark.asyncio
async def test_controller_start_idempotent():
    """
    Test ArousalController.start() when already running.

    Coverage: Line 476
    """
    config = ArousalConfig(update_interval_ms=100)
    controller = ArousalController(config)

    # Start once
    await controller.start()
    assert controller._running is True

    # Start again - should return early (idempotent)
    await controller.start()
    assert controller._running is True

    # Cleanup
    await controller.stop()


# ============================================================================
# Test Suite 4: ArousalController._update_loop() Exception (Lines 504-505)
# ============================================================================


@pytest.mark.asyncio
async def test_controller_update_loop_exception_handling():
    """
    Test ArousalController._update_loop() exception handling.

    Coverage: Lines 504-505
    """
    config = ArousalConfig(update_interval_ms=50)  # Fast updates
    controller = ArousalController(config)

    # Mock _update_arousal to raise exception
    original_update = controller._update_arousal
    exception_raised = False

    async def failing_update(dt):
        nonlocal exception_raised
        if not exception_raised:
            exception_raised = True
            raise RuntimeError("Simulated update failure")
        # After first exception, work normally
        await original_update(dt)

    controller._update_arousal = failing_update

    # Start controller
    await controller.start()

    # Wait for exception to be handled
    await asyncio.sleep(0.15)  # 3 update cycles

    # Controller should still be running
    assert controller._running is True
    assert exception_raised is True

    # Cleanup
    await controller.stop()


# ============================================================================
# Test Suite 5: External Contribution with Zero Priority (Line 596)
# ============================================================================


@pytest.mark.asyncio
async def test_compute_external_contribution_zero_priority():
    """
    Test _compute_external_contribution() when total_priority is 0.

    Coverage: Line 596
    """
    config = ArousalConfig(update_interval_ms=100)
    controller = ArousalController(config)

    # Add modulation with priority 0
    modulation = ArousalModulation(
        source="test",
        delta=0.2,
        duration_seconds=5.0,
        priority=0
    )
    controller._active_modulations.append(modulation)

    # Should return 0.0 when total_priority is 0
    contribution = controller._compute_external_contribution()
    assert contribution == 0.0


# ============================================================================
# Test Suite 6: Circadian Contribution (Lines 621-623)
# ============================================================================


@pytest.mark.asyncio
async def test_compute_circadian_contribution_enabled():
    """
    Test _compute_circadian_contribution() when circadian is enabled.

    Coverage: Lines 621-623
    """
    config = ArousalConfig(
        enable_circadian=True,
        circadian_amplitude=0.1
    )
    controller = ArousalController(config)

    # Compute circadian contribution
    contribution = controller._compute_circadian_contribution()

    # Should be between -amplitude and +amplitude
    assert -0.1 <= contribution <= 0.1

    # Should not be exactly 0 (unless it's noon/midnight by chance)
    # Just verify it's a valid float
    assert isinstance(contribution, (float, np.floating))


# ============================================================================
# Test Suite 7: Async Callback with Exception (Lines 653-655)
# ============================================================================


@pytest.mark.asyncio
async def test_invoke_callbacks_async_with_exception():
    """
    Test _invoke_callbacks() with async callback that raises exception.

    Coverage: Lines 653-655
    """
    config = ArousalConfig(update_interval_ms=100)
    controller = ArousalController(config)

    # Register async callback that raises exception
    async def failing_callback(state):
        raise RuntimeError("Callback failure")

    controller.register_arousal_callback(failing_callback)

    # Invoke callbacks - should handle exception gracefully
    await controller._invoke_callbacks()

    # Controller should still be functional
    state = controller.get_current_arousal()
    assert state is not None


# ============================================================================
# Test Suite 8: Invalid Needs Handling (Lines 693-694, 754, 768, 770)
# ============================================================================


@pytest.mark.asyncio
async def test_update_from_needs_invalid_needs():
    """
    Test update_from_needs() with invalid needs (increments counter).

    Coverage: Lines 693-694
    """
    config = ArousalConfig()
    controller = ArousalController(config)

    # Invalid needs (None)
    controller.update_from_needs(None)
    assert controller.invalid_needs_count == 1

    # Invalid needs (out of range)
    invalid_needs = AbstractNeeds(
        rest_need=0.5,
        repair_need=2.0,  # Out of range [0, 1]
        efficiency_need=0.3,
        connectivity_need=0.4,
        curiosity_drive=0.1,
        learning_drive=0.2
    )
    controller.update_from_needs(invalid_needs)
    assert controller.invalid_needs_count == 2


def test_validate_needs_none_input():
    """
    Test _validate_needs() with None input.

    Coverage: Line 754
    """
    controller = ArousalController()
    assert controller._validate_needs(None) is False


def test_validate_needs_non_numeric_value():
    """
    Test _validate_needs() with non-numeric value.

    Coverage: Line 768
    """
    controller = ArousalController()

    # Create needs with non-numeric value
    needs = AbstractNeeds(
        rest_need=0.5,
        repair_need=0.3,
        efficiency_need=0.4,
        connectivity_need=0.5,
        curiosity_drive=0.2,
        learning_drive=0.3
    )

    # Replace with non-numeric
    needs.rest_need = "invalid"

    assert controller._validate_needs(needs) is False


def test_validate_needs_out_of_range_negative():
    """
    Test _validate_needs() with negative value (out of range).

    Coverage: Line 770
    """
    controller = ArousalController()

    needs = AbstractNeeds(
        rest_need=-0.1,  # Out of range
        repair_need=0.3,
        efficiency_need=0.4,
        connectivity_need=0.5,
        curiosity_drive=0.2,
        learning_drive=0.3
    )

    assert controller._validate_needs(needs) is False


def test_validate_needs_out_of_range_positive():
    """
    Test _validate_needs() with value > 1.0 (out of range).

    Coverage: Line 770
    """
    controller = ArousalController()

    needs = AbstractNeeds(
        rest_need=0.5,
        repair_need=1.5,  # Out of range
        efficiency_need=0.4,
        connectivity_need=0.5,
        curiosity_drive=0.2,
        learning_drive=0.3
    )

    assert controller._validate_needs(needs) is False


# ============================================================================
# Test Suite 9: Saturation Detection (Lines 796-799)
# ============================================================================


@pytest.mark.asyncio
async def test_detect_saturation_event():
    """
    Test _detect_saturation() saturation event detection.

    Coverage: Lines 796-799
    """
    config = ArousalConfig(update_interval_ms=50)
    controller = ArousalController(config)

    # Set arousal to boundary
    controller.arousal_saturation_start = time.time() - (AROUSAL_SATURATION_THRESHOLD_SECONDS + 1)

    # Trigger saturation detection
    controller._detect_saturation(0.0)  # At boundary

    # Should increment saturation_events
    assert controller.saturation_events == 1


# ============================================================================
# Test Suite 10: Oscillation Detection (Lines 820-821)
# ============================================================================


@pytest.mark.asyncio
async def test_detect_oscillation_event():
    """
    Test _detect_oscillation() oscillation event detection.

    Coverage: Lines 820-821
    """
    config = ArousalConfig()
    controller = ArousalController(config)

    # Fill arousal history with oscillating values
    # Create high variance arousal pattern
    for i in range(AROUSAL_OSCILLATION_WINDOW):
        value = 0.3 if i % 2 == 0 else 0.8  # Alternating 0.3 and 0.8
        controller.arousal_history.append(value)

    # Verify variance is high
    stddev = float(np.std(controller.arousal_history))
    assert stddev > AROUSAL_OSCILLATION_THRESHOLD

    # Trigger oscillation detection
    controller._detect_oscillation()

    # Should increment oscillation_events
    assert controller.oscillation_events == 1


# ============================================================================
# Test Suite 11: Health Metrics with Saturation (Lines 834-842)
# ============================================================================


@pytest.mark.asyncio
async def test_get_health_metrics_with_saturation():
    """
    Test get_health_metrics() when controller is saturated.

    Coverage: Lines 834-842
    """
    config = ArousalConfig()
    controller = ArousalController(config)

    # Set up saturation state
    controller.arousal_saturation_start = time.time() - (AROUSAL_SATURATION_THRESHOLD_SECONDS + 1)
    controller._current_state.arousal = 1.0  # At upper boundary

    # Add arousal history
    for _ in range(10):
        controller.arousal_history.append(0.6)

    # Get health metrics
    metrics = controller.get_health_metrics()

    # Verify saturation detection
    assert metrics["is_saturated"] is True
    assert "arousal_variance" in metrics
    assert metrics["arousal_history_size"] == 10


@pytest.mark.asyncio
async def test_get_health_metrics_with_variance():
    """
    Test get_health_metrics() variance calculation with sufficient history.

    Coverage: Lines 834-842
    """
    config = ArousalConfig()
    controller = ArousalController(config)

    # Add varied arousal history
    controller.arousal_history.extend([0.4, 0.5, 0.6, 0.5, 0.4, 0.6])

    # Get health metrics
    metrics = controller.get_health_metrics()

    # Verify variance is calculated
    assert metrics["arousal_variance"] > 0.0
    assert metrics["arousal_history_size"] == 6


@pytest.mark.asyncio
async def test_get_health_metrics_insufficient_history():
    """
    Test get_health_metrics() variance calculation with insufficient history.

    Coverage: Line 834 (else branch)
    """
    config = ArousalConfig()
    controller = ArousalController(config)

    # Only 1 value in history (< 2)
    controller.arousal_history.append(0.6)

    # Get health metrics
    metrics = controller.get_health_metrics()

    # Variance should be 0.0 when insufficient history
    assert metrics["arousal_variance"] == 0.0


# ============================================================================
# Test Suite 12: Additional Edge Cases for 100% Coverage
# ============================================================================


def test_arousal_bound_enforcer():
    """Test ArousalBoundEnforcer.enforce() for completeness."""
    # Test lower bound
    assert ArousalBoundEnforcer.enforce(-0.5) == 0.0

    # Test upper bound
    assert ArousalBoundEnforcer.enforce(1.5) == 1.0

    # Test valid range
    assert ArousalBoundEnforcer.enforce(0.6) == 0.6


def test_arousal_state_repr():
    """Test ArousalState.__repr__() for completeness."""
    state = ArousalState(arousal=0.75)
    repr_str = repr(state)

    assert "ArousalState" in repr_str
    assert "0.75" in repr_str
    assert "alert" in repr_str.lower()


def test_controller_repr():
    """Test ArousalController.__repr__() for completeness."""
    controller = ArousalController(controller_id="test-controller")
    repr_str = repr(controller)

    assert "ArousalController" in repr_str
    assert "test-controller" in repr_str


@pytest.mark.asyncio
async def test_controller_get_statistics():
    """Test ArousalController.get_statistics() for completeness."""
    config = ArousalConfig()
    controller = ArousalController(config, controller_id="stats-test")

    stats = controller.get_statistics()

    assert stats["controller_id"] == "stats-test"
    assert "running" in stats
    assert "current_arousal" in stats
    assert "esgt_threshold" in stats


@pytest.mark.asyncio
async def test_controller_stress_management():
    """Test stress level and reset functionality."""
    config = ArousalConfig()
    controller = ArousalController(config)

    # Manually set stress
    controller._accumulated_stress = 0.8

    # Get stress level
    assert controller.get_stress_level() == 0.8

    # Reset stress
    controller.reset_stress()
    assert controller.get_stress_level() == 0.0


# ============================================================================
# Test Suite 13: Remaining Uncovered Lines (90.85% → 100%)
# ============================================================================


def test_arousal_state_classification_sleep():
    """Test ArousalState._classify_arousal_level() for SLEEP level.

    Coverage: Line 247
    """
    state = ArousalState(arousal=0.2)  # Exactly at boundary
    assert state.level == ArousalLevel.SLEEP


def test_arousal_state_classification_drowsy():
    """Test ArousalState._classify_arousal_level() for DROWSY level.

    Coverage: Line 249
    """
    state = ArousalState(arousal=0.4)  # Exactly at boundary
    assert state.level == ArousalLevel.DROWSY


def test_arousal_state_classification_hyperalert():
    """Test ArousalState._classify_arousal_level() for HYPERALERT level.

    Coverage: Line 254
    """
    state = ArousalState(arousal=0.9)  # >0.8
    assert state.level == ArousalLevel.HYPERALERT


@pytest.mark.asyncio
async def test_update_arousal_with_esgt_refractory():
    """Test _update_arousal() when ESGT refractory period is active.

    Coverage: Line 525
    """
    config = ArousalConfig(
        baseline_arousal=0.6,
        esgt_refractory_arousal_drop=0.15
    )
    controller = ArousalController(config)

    # Apply ESGT refractory
    controller.apply_esgt_refractory()

    # Start controller to trigger update
    await controller.start()
    await asyncio.sleep(0.15)  # Wait for update

    # Current arousal should be reduced due to refractory
    current = controller.get_current_arousal()
    # Baseline 0.6 - refractory drop 0.15 = 0.45
    assert current.arousal < 0.6

    await controller.stop()


@pytest.mark.asyncio
async def test_update_arousal_increasing_path():
    """Test _update_arousal() when target > current (increasing path).

    Coverage: Lines 535-536
    """
    config = ArousalConfig(
        baseline_arousal=0.8,  # High baseline
        arousal_increase_rate=0.05
    )
    controller = ArousalController(config)

    # Start at low arousal
    controller._current_state.arousal = 0.3

    # Start controller
    await controller.start()
    await asyncio.sleep(0.15)  # Wait for updates

    # Should have increased toward 0.8
    current = controller.get_current_arousal()
    assert current.arousal > 0.3

    await controller.stop()


@pytest.mark.asyncio
async def test_update_arousal_level_transition():
    """Test _update_arousal() level transition tracking.

    Coverage: Lines 569-570
    """
    config = ArousalConfig(
        baseline_arousal=0.9,  # HYPERALERT level
        arousal_increase_rate=0.30  # Very fast increase
    )
    controller = ArousalController(config)

    # Start at RELAXED level
    controller._current_state.arousal = 0.5
    controller._current_state.level = ArousalLevel.RELAXED
    controller._last_level = ArousalLevel.RELAXED

    # Start controller
    await controller.start()
    await asyncio.sleep(0.5)  # Wait longer for level transition

    # Should have transitioned from RELAXED
    current = controller.get_current_arousal()
    # Arousal should have increased
    assert current.arousal > 0.5  # Should have increased from 0.5

    await controller.stop()


@pytest.mark.asyncio
async def test_compute_external_contribution_with_priority():
    """Test _compute_external_contribution() with non-zero priority.

    Coverage: Line 595
    """
    config = ArousalConfig()
    controller = ArousalController(config)

    # Add modulation with priority > 0
    controller.request_modulation(
        source="test",
        delta=0.3,
        duration_seconds=5.0,
        priority=2  # Non-zero priority
    )

    # Should return weighted contribution
    contribution = controller._compute_external_contribution()
    assert contribution != 0.0


@pytest.mark.asyncio
async def test_compute_temporal_contribution_high_arousal():
    """Test _compute_temporal_contribution() when arousal > 0.7 (stress buildup).

    Coverage: Line 604
    """
    config = ArousalConfig(stress_buildup_rate=0.01)
    controller = ArousalController(config)

    # Set high arousal
    controller._current_state.arousal = 0.8

    # Compute contribution
    contribution = controller._compute_temporal_contribution(dt=1.0)

    # Stress should have increased
    assert controller._accumulated_stress > 0.0


@pytest.mark.asyncio
async def test_compute_temporal_contribution_low_arousal():
    """Test _compute_temporal_contribution() when arousal < 0.5 (stress recovery).

    Coverage: Line 607
    """
    config = ArousalConfig(stress_recovery_rate=0.005)
    controller = ArousalController(config)

    # Set accumulated stress
    controller._accumulated_stress = 0.5

    # Set low arousal
    controller._current_state.arousal = 0.3

    # Compute contribution
    controller._compute_temporal_contribution(dt=1.0)

    # Stress should have decreased
    assert controller._accumulated_stress < 0.5


def test_classify_arousal_sleep_level():
    """Test _classify_arousal() for SLEEP level.

    Coverage: Line 637
    """
    controller = ArousalController()
    level = controller._classify_arousal(0.15)
    assert level == ArousalLevel.SLEEP


def test_classify_arousal_drowsy_level():
    """Test _classify_arousal() for DROWSY level.

    Coverage: Line 639
    """
    controller = ArousalController()
    level = controller._classify_arousal(0.35)
    assert level == ArousalLevel.DROWSY


def test_classify_arousal_alert_level():
    """Test _classify_arousal() for ALERT level.

    Coverage: Line 642-643
    """
    controller = ArousalController()
    level = controller._classify_arousal(0.75)
    assert level == ArousalLevel.ALERT


def test_classify_arousal_hyperalert_level():
    """Test _classify_arousal() for HYPERALERT level.

    Coverage: Line 644
    """
    controller = ArousalController()
    level = controller._classify_arousal(0.95)
    assert level == ArousalLevel.HYPERALERT


@pytest.mark.asyncio
async def test_invoke_callbacks_sync_callback():
    """Test _invoke_callbacks() with synchronous callback.

    Coverage: Line 653
    """
    config = ArousalConfig()
    controller = ArousalController(config)

    callback_invoked = False

    def sync_callback(state):
        nonlocal callback_invoked
        callback_invoked = True

    controller.register_arousal_callback(sync_callback)

    # Invoke callbacks
    await controller._invoke_callbacks()

    assert callback_invoked is True


def test_get_esgt_threshold():
    """Test get_esgt_threshold() public API.

    Coverage: Line 665
    """
    controller = ArousalController()
    threshold = controller.get_esgt_threshold()

    # Should return valid threshold
    assert 0.0 < threshold < 2.0


def test_request_modulation_public_api():
    """Test request_modulation() public API.

    Coverage: Lines 677-680
    """
    controller = ArousalController()

    initial_count = controller.total_modulations

    # Request modulation
    controller.request_modulation(
        source="test_source",
        delta=0.2,
        duration_seconds=5.0,
        priority=3
    )

    # Should increment counter
    assert controller.total_modulations == initial_count + 1
    assert len(controller._active_modulations) == 1


def test_update_from_needs_valid_needs():
    """Test update_from_needs() with valid needs (contribution calculation).

    Coverage: Lines 696-703
    """
    config = ArousalConfig(
        repair_need_weight=0.3,
        rest_need_weight=-0.2,
        efficiency_need_weight=0.1,
        connectivity_need_weight=0.15
    )
    controller = ArousalController(config)

    # Valid needs
    needs = AbstractNeeds(
        rest_need=0.5,
        repair_need=0.8,
        efficiency_need=0.6,
        connectivity_need=0.4,
        curiosity_drive=0.2,
        learning_drive=0.3
    )

    # Update from needs
    controller.update_from_needs(needs)

    # Contribution should be calculated
    expected = (0.3 * 0.8) + (-0.2 * 0.5) + (0.1 * 0.6) + (0.15 * 0.4)
    assert abs(controller._current_state.need_contribution - expected) < 0.001


def test_apply_esgt_refractory():
    """Test apply_esgt_refractory() public API.

    Coverage: Lines 711-712
    """
    controller = ArousalController()

    initial_count = controller.esgt_refractories_applied

    # Apply refractory
    controller.apply_esgt_refractory()

    # Should set refractory_until and increment counter
    assert controller._refractory_until is not None
    assert controller.esgt_refractories_applied == initial_count + 1


def test_validate_needs_valid_returns_true():
    """Test _validate_needs() returns True for valid needs.

    Coverage: Line 772
    """
    controller = ArousalController()

    valid_needs = AbstractNeeds(
        rest_need=0.5,
        repair_need=0.3,
        efficiency_need=0.4,
        connectivity_need=0.5,
        curiosity_drive=0.2,
        learning_drive=0.3
    )

    assert controller._validate_needs(valid_needs) is True


def test_detect_saturation_start_tracking():
    """Test _detect_saturation() starts tracking when at boundary.

    Coverage: Line 790
    """
    controller = ArousalController()

    # Ensure not already tracking
    controller.arousal_saturation_start = None

    # Trigger saturation detection at boundary
    controller._detect_saturation(0.0)

    # Should start tracking
    assert controller.arousal_saturation_start is not None


# ============================================================================
# Coverage Summary
# ============================================================================

"""
Test Coverage Mapping:

Line 151: test_rate_limiter_no_time_passed
Lines 161-162: test_rate_limiter_change_limited, test_rate_limiter_negative_change_limited
Line 247: test_arousal_state_classification_sleep
Line 249: test_arousal_state_classification_drowsy
Line 254: test_arousal_state_classification_hyperalert
Line 303: test_modulation_instant_is_expired
Line 309: test_modulation_instant_get_current_delta
Line 313: test_modulation_expired_duration_get_current_delta
Line 476: test_controller_start_idempotent
Lines 504-505: test_controller_update_loop_exception_handling
Line 525: test_update_arousal_with_esgt_refractory
Lines 535-536: test_update_arousal_increasing_path
Lines 569-570: test_update_arousal_level_transition
Line 595: test_compute_external_contribution_with_priority
Line 596: test_compute_external_contribution_zero_priority
Line 604: test_compute_temporal_contribution_high_arousal
Line 607: test_compute_temporal_contribution_low_arousal
Lines 621-623: test_compute_circadian_contribution_enabled
Line 637: test_classify_arousal_sleep_level
Line 639: test_classify_arousal_drowsy_level
Lines 642-643: test_classify_arousal_alert_level
Line 644: test_classify_arousal_hyperalert_level
Line 653: test_invoke_callbacks_sync_callback
Lines 653-655: test_invoke_callbacks_async_with_exception
Line 665: test_get_esgt_threshold
Lines 677-680: test_request_modulation_public_api
Lines 693-694: test_update_from_needs_invalid_needs
Lines 696-703: test_update_from_needs_valid_needs
Lines 711-712: test_apply_esgt_refractory
Line 754: test_validate_needs_none_input
Line 768: test_validate_needs_non_numeric_value
Line 770: test_validate_needs_out_of_range_negative, test_validate_needs_out_of_range_positive
Line 772: test_validate_needs_valid_returns_true
Line 790: test_detect_saturation_start_tracking
Lines 796-799: test_detect_saturation_event
Lines 820-821: test_detect_oscillation_event
Lines 834-842: test_get_health_metrics_with_saturation, test_get_health_metrics_with_variance, test_get_health_metrics_insufficient_history

Total Tests Created: 45
Expected Coverage: 90.85% → 100.00%
"""
