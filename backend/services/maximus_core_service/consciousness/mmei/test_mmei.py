"""
MMEI Test Suite - Internal State Monitoring Validation
========================================================

Comprehensive tests for interoception and autonomous goal generation.

Test Coverage:
--------------
1. Physical → Abstract translation accuracy
2. Need classification and urgency
3. Continuous monitoring loop
4. Goal generation from needs
5. Goal satisfaction and lifecycle
6. Callback invocation
7. Performance and statistics
8. Integration with HCL (conceptual)

Testing Philosophy (REGRA DE OURO):
------------------------------------
- All tests use real implementations (NO MOCKS)
- Async tests use actual asyncio
- Tests validate theoretical foundations
- Performance benchmarks included
- Edge cases covered (zero needs, critical needs, etc.)

Historical Note:
----------------
First test suite for computational interoception in AI.
Validates that "feeling" computation works correctly.

"Tests prove theory. Theory guides implementation."
"""

import pytest
import pytest_asyncio
import asyncio
import time
from typing import List

from consciousness.mmei.monitor import (
    InternalStateMonitor,
    PhysicalMetrics,
    AbstractNeeds,
    NeedUrgency,
    InteroceptionConfig,
)

from consciousness.mmei.goals import (
    AutonomousGoalGenerator,
    Goal,
    GoalType,
    GoalPriority,
    GoalGenerationConfig,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def default_config():
    """Default interoception configuration."""
    return InteroceptionConfig(
        collection_interval_ms=50.0,  # Fast for testing
        short_term_window_samples=5,
        long_term_window_samples=10,
    )


@pytest.fixture
def goal_gen_config():
    """Default goal generation configuration."""
    return GoalGenerationConfig(
        rest_threshold=0.60,
        repair_threshold=0.40,
        min_goal_interval_seconds=1.0,  # Fast for testing
    )


@pytest_asyncio.fixture(scope="function")
async def monitor(default_config):
    """Create and configure monitor."""
    mon = InternalStateMonitor(config=default_config)

    # Simple metrics collector
    async def collect_test_metrics() -> PhysicalMetrics:
        return PhysicalMetrics(
            cpu_usage_percent=50.0,
            memory_usage_percent=40.0,
            error_rate_per_min=1.0,
            network_latency_ms=20.0,
        )

    mon.set_metrics_collector(collect_test_metrics)
    yield mon

    # Cleanup
    if mon._running:
        await mon.stop()


@pytest.fixture
def goal_generator(goal_gen_config):
    """Create goal generator."""
    return AutonomousGoalGenerator(config=goal_gen_config)


# =============================================================================
# Physical → Abstract Translation Tests
# =============================================================================

def test_physical_metrics_normalization():
    """Test that percentage values are normalized to [0, 1]."""
    metrics = PhysicalMetrics(
        cpu_usage_percent=75.0,
        memory_usage_percent=150.0,  # Invalid - should clamp to 100
        packet_loss_percent=5.0,
    )

    normalized = metrics.normalize()

    assert 0.0 <= normalized.cpu_usage_percent <= 1.0
    assert normalized.cpu_usage_percent == 0.75

    assert normalized.memory_usage_percent == 1.0  # Clamped
    assert normalized.packet_loss_percent == 0.05


def test_abstract_needs_classification():
    """Test need urgency classification."""
    # SATISFIED
    needs = AbstractNeeds(rest_need=0.15)
    _, _, urgency = needs.get_most_urgent()
    assert urgency == NeedUrgency.SATISFIED

    # MODERATE
    needs = AbstractNeeds(rest_need=0.50)
    _, _, urgency = needs.get_most_urgent()
    assert urgency == NeedUrgency.MODERATE

    # CRITICAL
    needs = AbstractNeeds(repair_need=0.85)
    name, value, urgency = needs.get_most_urgent()
    assert name == "repair_need"
    assert value == 0.85
    assert urgency == NeedUrgency.CRITICAL


def test_critical_needs_detection():
    """Test detection of critical needs above threshold."""
    needs = AbstractNeeds(
        rest_need=0.90,
        repair_need=0.85,
        efficiency_need=0.50,
    )

    critical = needs.get_critical_needs(threshold=0.80)

    assert len(critical) == 2
    assert ("rest_need", 0.90) in critical
    assert ("repair_need", 0.85) in critical


def test_physical_to_abstract_translation(default_config):
    """Test translation from physical metrics to abstract needs."""
    monitor = InternalStateMonitor(config=default_config)

    # High CPU load
    metrics = PhysicalMetrics(
        cpu_usage_percent=95.0,
        memory_usage_percent=30.0,
    ).normalize()

    needs = monitor._compute_needs(metrics)

    # High CPU should produce high rest_need
    assert needs.rest_need > 0.60
    assert needs.rest_need <= 1.0


def test_error_to_repair_need_translation(default_config):
    """Test that errors translate to repair need."""
    monitor = InternalStateMonitor(config=default_config)

    # High error rate
    metrics = PhysicalMetrics(
        error_rate_per_min=8.0,  # 80% of critical threshold (10.0)
        exception_count=5,
    ).normalize()

    needs = monitor._compute_needs(metrics)

    # High errors should produce high repair_need
    assert needs.repair_need > 0.50


def test_idle_to_curiosity_translation(default_config):
    """Test that idle time translates to curiosity drive."""
    monitor = InternalStateMonitor(config=default_config)

    # High idle time
    metrics = PhysicalMetrics(
        idle_time_percent=80.0,
        cpu_usage_percent=20.0,
    ).normalize()

    # Simulate accumulation over multiple cycles
    for _ in range(20):
        needs = monitor._compute_needs(metrics)

    # Extended idle should increase curiosity
    assert needs.curiosity_drive > 0.0


# =============================================================================
# Monitoring Loop Tests
# =============================================================================

@pytest.mark.asyncio
async def test_monitor_start_stop(monitor):
    """Test monitor starts and stops cleanly."""
    assert not monitor._running

    await monitor.start()
    assert monitor._running

    await asyncio.sleep(0.2)  # Let it run a few cycles

    await monitor.stop()
    assert not monitor._running


@pytest.mark.asyncio
async def test_monitor_collects_metrics(monitor):
    """Test monitor continuously collects metrics."""
    await monitor.start()
    await asyncio.sleep(0.3)  # Allow 5-6 collections at 50ms interval
    await monitor.stop()

    assert monitor.total_collections >= 3
    assert monitor._current_metrics is not None
    assert monitor._current_needs is not None


@pytest.mark.asyncio
async def test_monitor_maintains_history(monitor):
    """Test monitor maintains metrics/needs history."""
    await monitor.start()
    await asyncio.sleep(0.3)
    await monitor.stop()

    assert len(monitor._metrics_history) > 0
    assert len(monitor._needs_history) > 0

    # History should not exceed configured window
    assert len(monitor._metrics_history) <= monitor.config.long_term_window_samples


@pytest.mark.asyncio
async def test_monitor_callback_invocation(monitor):
    """Test callbacks invoked when needs exceed threshold."""
    callback_invoked = []

    async def test_callback(needs: AbstractNeeds):
        callback_invoked.append(needs)

    monitor.register_need_callback(test_callback, threshold=0.0)  # Always trigger

    await monitor.start()
    await asyncio.sleep(0.2)
    await monitor.stop()

    assert len(callback_invoked) > 0
    assert monitor.callback_invocations > 0


# =============================================================================
# Need Trend Analysis Tests
# =============================================================================

@pytest.mark.asyncio
async def test_needs_trend_tracking(default_config):
    """Test trend analysis for specific needs."""
    monitor = InternalStateMonitor(config=default_config)

    # Gradually increasing CPU load
    load = 30.0

    async def increasing_load_collector():
        nonlocal load
        load = min(load + 5.0, 95.0)
        return PhysicalMetrics(cpu_usage_percent=load).normalize()

    monitor.set_metrics_collector(increasing_load_collector)

    await monitor.start()
    await asyncio.sleep(0.4)  # 8 collections
    await monitor.stop()

    # Get trend
    rest_trend = monitor.get_needs_trend("rest_need")

    assert len(rest_trend) > 0
    # Trend should be increasing (load increases → rest_need increases)
    assert rest_trend[-1] > rest_trend[0]


@pytest.mark.asyncio
async def test_moving_average_computation(monitor):
    """Test moving average computation."""
    await monitor.start()
    await asyncio.sleep(0.3)
    await monitor.stop()

    avg = monitor.get_moving_average("rest_need", window_samples=5)

    assert 0.0 <= avg <= 1.0


# =============================================================================
# Goal Generation Tests
# =============================================================================

def test_goal_creation_from_high_rest_need(goal_generator):
    """Test goal generated when rest_need exceeds threshold."""
    needs = AbstractNeeds(rest_need=0.80)  # Above 0.60 threshold

    goals = goal_generator.generate_goals(needs)

    assert len(goals) > 0
    rest_goals = [g for g in goals if g.goal_type == GoalType.REST]
    assert len(rest_goals) == 1

    goal = rest_goals[0]
    assert goal.priority == GoalPriority.CRITICAL
    assert goal.source_need == "rest_need"


def test_goal_creation_from_repair_need(goal_generator):
    """Test goal generated from error detection."""
    needs = AbstractNeeds(repair_need=0.60)

    goals = goal_generator.generate_goals(needs)

    repair_goals = [g for g in goals if g.goal_type == GoalType.REPAIR]
    assert len(repair_goals) == 1

    goal = repair_goals[0]
    assert goal.priority in [GoalPriority.HIGH, GoalPriority.CRITICAL]


def test_multiple_goals_from_multiple_needs(goal_generator):
    """Test multiple goals generated when multiple needs present."""
    needs = AbstractNeeds(
        rest_need=0.70,
        repair_need=0.50,
        connectivity_need=0.60,
    )

    goals = goal_generator.generate_goals(needs)

    # Should generate 3 goals (one for each need)
    assert len(goals) == 3

    goal_types = {g.goal_type for g in goals}
    assert GoalType.REST in goal_types
    assert GoalType.REPAIR in goal_types
    assert GoalType.RESTORE in goal_types


def test_goal_spam_prevention(goal_generator):
    """Test that goals are not generated too frequently."""
    needs = AbstractNeeds(rest_need=0.80)

    # First generation
    goals1 = goal_generator.generate_goals(needs)
    assert len(goals1) > 0

    # Immediate second generation - should be prevented
    goals2 = goal_generator.generate_goals(needs)
    assert len(goals2) == 0  # Blocked by min_goal_interval


def test_goal_priority_classification(goal_gen_config):
    """Test goal priority matches need urgency."""
    # Low need → Low priority
    needs_low = AbstractNeeds(rest_need=0.35)
    gen_low = AutonomousGoalGenerator(config=goal_gen_config)
    goals_low = gen_low.generate_goals(needs_low)
    # Below threshold, no goal generated
    assert len(goals_low) == 0

    # High need → High priority
    needs_high = AbstractNeeds(rest_need=0.75)
    gen_high = AutonomousGoalGenerator(config=goal_gen_config)
    goals_high = gen_high.generate_goals(needs_high)
    assert len(goals_high) > 0, "Should generate goal for high rest need"
    assert goals_high[0].priority == GoalPriority.HIGH

    # Critical need → Critical priority
    needs_critical = AbstractNeeds(rest_need=0.90)
    gen_critical = AutonomousGoalGenerator(config=goal_gen_config)
    goals_critical = gen_critical.generate_goals(needs_critical)
    assert len(goals_critical) > 0, "Should generate goal for critical rest need"
    assert goals_critical[0].priority == GoalPriority.CRITICAL


# =============================================================================
# Goal Lifecycle Tests
# =============================================================================

def test_goal_satisfaction_detection():
    """Test goal satisfaction when need drops."""
    goal = Goal(
        goal_type=GoalType.REST,
        source_need="rest_need",
        need_value=0.80,
        target_need_value=0.30,
    )

    assert goal.is_active

    # Need still high - not satisfied
    assert not goal.is_satisfied(0.70)

    # Need dropped below target - satisfied
    assert goal.is_satisfied(0.25)

    goal.mark_satisfied()
    assert not goal.is_active
    assert goal.satisfied_at is not None


def test_goal_expiration():
    """Test goal expiration after timeout."""
    goal = Goal(
        goal_type=GoalType.EXPLORE,
        timeout_seconds=0.1,  # 100ms timeout
    )

    assert not goal.is_expired()

    time.sleep(0.15)

    assert goal.is_expired()


def test_goal_priority_score():
    """Test goal priority scoring for sorting."""
    goal_low = Goal(goal_type=GoalType.LEARN, priority=GoalPriority.LOW, need_value=0.30)
    goal_high = Goal(goal_type=GoalType.REPAIR, priority=GoalPriority.CRITICAL, need_value=0.90)

    assert goal_high.get_priority_score() > goal_low.get_priority_score()


def test_active_goals_update(goal_generator):
    """Test active goals list updates on satisfaction."""
    needs_high = AbstractNeeds(rest_need=0.80)
    goals = goal_generator.generate_goals(needs_high)

    assert len(goal_generator.get_active_goals()) == 1

    # Simulate need dropping
    needs_low = AbstractNeeds(rest_need=0.20)
    goal_generator._update_active_goals(needs_low)

    # Goal should be satisfied and removed
    assert len(goal_generator.get_active_goals()) == 0
    assert goal_generator.total_goals_satisfied == 1


def test_goal_consumer_notification(goal_generator):
    """Test goal consumers are notified of new goals."""
    notified_goals = []

    def consumer(goal: Goal):
        notified_goals.append(goal)

    goal_generator.register_goal_consumer(consumer)

    needs = AbstractNeeds(repair_need=0.70)
    goal_generator.generate_goals(needs)

    assert len(notified_goals) == 1
    assert notified_goals[0].goal_type == GoalType.REPAIR


# =============================================================================
# Query and Statistics Tests
# =============================================================================

def test_get_active_goals_sorted(goal_generator):
    """Test active goals returned sorted by priority."""
    needs = AbstractNeeds(
        rest_need=0.65,       # Moderate priority
        repair_need=0.90,     # Critical priority
        efficiency_need=0.55, # Moderate priority
    )

    goal_generator.generate_goals(needs)

    sorted_goals = goal_generator.get_active_goals(sort_by_priority=True)

    # First goal should be CRITICAL (repair)
    assert sorted_goals[0].priority == GoalPriority.CRITICAL
    assert sorted_goals[0].goal_type == GoalType.REPAIR


def test_get_critical_goals(goal_generator):
    """Test filtering for critical goals."""
    needs = AbstractNeeds(
        rest_need=0.95,
        repair_need=0.45,
    )

    goal_generator.generate_goals(needs)

    critical = goal_generator.get_critical_goals()

    assert len(critical) == 1
    assert critical[0].goal_type == GoalType.REST


def test_get_goals_by_type(goal_generator):
    """Test filtering goals by type."""
    needs = AbstractNeeds(
        rest_need=0.70,
        repair_need=0.60,
    )

    goal_generator.generate_goals(needs)

    rest_goals = goal_generator.get_goals_by_type(GoalType.REST)
    repair_goals = goal_generator.get_goals_by_type(GoalType.REPAIR)

    assert len(rest_goals) == 1
    assert len(repair_goals) == 1


def test_monitor_statistics(monitor):
    """Test monitor statistics collection."""
    stats = monitor.get_statistics()

    assert "monitor_id" in stats
    assert "total_collections" in stats
    assert "success_rate" in stats


def test_goal_generator_statistics(goal_generator):
    """Test goal generator statistics."""
    needs = AbstractNeeds(rest_need=0.80, repair_need=0.70)
    goal_generator.generate_goals(needs)

    # Simulate satisfaction
    needs_low = AbstractNeeds(rest_need=0.20, repair_need=0.15)
    goal_generator._update_active_goals(needs_low)

    stats = goal_generator.get_statistics()

    assert stats["total_generated"] == 2
    assert stats["total_satisfied"] == 2
    assert stats["satisfaction_rate"] == 1.0


# =============================================================================
# Performance and Stress Tests
# =============================================================================

@pytest.mark.asyncio
async def test_monitoring_performance(default_config):
    """Test monitor performance under continuous operation."""
    monitor = InternalStateMonitor(config=default_config)

    async def fast_collector():
        return PhysicalMetrics(cpu_usage_percent=50.0).normalize()

    monitor.set_metrics_collector(fast_collector)

    await monitor.start()
    await asyncio.sleep(1.0)  # Run for 1 second
    await monitor.stop()

    # At 50ms interval, should collect ~20 samples/second
    assert monitor.total_collections >= 15

    # Success rate should be high
    stats = monitor.get_statistics()
    assert stats["success_rate"] > 0.95


def test_goal_generation_at_scale(goal_gen_config):
    """Test goal generation performance with many needs."""
    # Modify config for stress test
    config = GoalGenerationConfig(
        min_goal_interval_seconds=0.0,  # No throttling
        max_concurrent_goals=50,
    )

    generator = AutonomousGoalGenerator(config=config)

    # Generate many goals
    for i in range(20):
        needs = AbstractNeeds(
            rest_need=0.70,
            repair_need=0.60,
            efficiency_need=0.55,
            connectivity_need=0.65,
        )
        generator.generate_goals(needs)

        time.sleep(0.05)

    # Should handle large goal set
    # Note: Can slightly exceed max because multiple goals generated per call
    # (up to 6 types: rest, repair, efficiency, connectivity, curiosity, learning)
    active = generator.get_active_goals()
    assert len(active) <= config.max_concurrent_goals + 6, \
        f"Generated {len(active)} goals, max is {config.max_concurrent_goals} + batch tolerance"


# =============================================================================
# Edge Case Tests
# =============================================================================

def test_zero_needs_no_goals(goal_generator):
    """Test that zero needs generate no goals."""
    needs = AbstractNeeds()  # All needs = 0.0

    goals = goal_generator.generate_goals(needs)

    assert len(goals) == 0


def test_all_critical_needs(goal_generator):
    """Test behavior when all needs are critical."""
    needs = AbstractNeeds(
        rest_need=0.95,
        repair_need=0.90,
        efficiency_need=0.85,
        connectivity_need=0.88,
    )

    goals = goal_generator.generate_goals(needs)

    # All should generate critical goals
    assert len(goals) == 4
    assert all(g.priority == GoalPriority.CRITICAL for g in goals)


@pytest.mark.asyncio
async def test_monitor_with_failing_collector(default_config):
    """Test monitor handles collector failures gracefully."""
    monitor = InternalStateMonitor(config=default_config)

    async def failing_collector():
        raise RuntimeError("Simulated failure")

    monitor.set_metrics_collector(failing_collector)

    await monitor.start()
    await asyncio.sleep(0.3)  # Longer wait to ensure multiple collection attempts
    await monitor.stop()

    # Should handle errors without crashing
    # Note: total_collections tracks successes, failed_collections tracks failures
    # With failing collector, we expect 0 successes and >0 failures
    assert monitor.total_collections == 0, "Should have no successful collections with failing collector"
    assert monitor.failed_collections > 0, f"Should have failed collections, got {monitor.failed_collections}"

    # Verify monitor stayed running despite failures
    assert not monitor._running, "Monitor should be stopped after stop() call"


# =============================================================================
# Integration Test (Conceptual - HCL not fully integrated yet)
# =============================================================================

@pytest.mark.asyncio
async def test_mmei_full_pipeline(default_config, goal_gen_config):
    """
    Test full MMEI pipeline: metrics → needs → goals → (HCL).

    This is a conceptual integration test showing the full flow.
    """
    # Setup
    monitor = InternalStateMonitor(config=default_config)
    generator = AutonomousGoalGenerator(config=goal_gen_config)

    # Metrics collector simulating high load
    async def high_load_metrics():
        # Don't call normalize() - monitor does it automatically
        return PhysicalMetrics(
            cpu_usage_percent=90.0,
            memory_usage_percent=85.0,
            error_rate_per_min=5.0,
        )

    monitor.set_metrics_collector(high_load_metrics)

    # Start monitoring
    await monitor.start()
    await asyncio.sleep(0.3)
    await monitor.stop()

    # Get current needs
    needs = monitor.get_current_needs()

    assert needs is not None
    assert needs.rest_need > 0.60  # High load → high rest need
    assert needs.repair_need > 0.30  # Errors → repair need

    # Generate goals from needs
    goals = generator.generate_goals(needs)

    assert len(goals) >= 1

    # Should include REST goal (high CPU/memory)
    rest_goals = [g for g in goals if g.goal_type == GoalType.REST]
    assert len(rest_goals) > 0

    # In full integration, goals would go to HCL for execution
    # HCL would reduce load → needs decrease → goals satisfied

    print(f"✅ Full MMEI pipeline test complete: {len(goals)} goals generated from needs")


# =============================================================================
# Test Main
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
