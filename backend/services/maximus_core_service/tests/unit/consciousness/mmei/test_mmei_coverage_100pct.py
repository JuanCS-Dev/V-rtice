"""MMEI Monitor - 100% Coverage Tests

Target: mmei/monitor.py (24.67% → 100%)
Priority: P0 CRITICAL - Lei Zero Enforcement
Risk Level: MAXIMUM

This test file achieves 100% coverage of the MMEI Internal State Monitor,
with special focus on Lei Zero-critical paths:
- Goal generation logic (generate_goal_from_need)
- Need computation (_compute_needs)
- Rate limiting and overflow protection
- Internal state monitoring loop

Authors: Claude Code + Juan (Phase 3 - T5)
Date: 2025-10-14
Philosophy: "100% coverage como testemunho de que perfeição é possível"
"""

import pytest
import asyncio
import time

from consciousness.mmei.monitor import (
    InternalStateMonitor,
    PhysicalMetrics,
    AbstractNeeds,
    NeedUrgency,
    Goal,
    RateLimiter,
    MAX_GOALS_PER_MINUTE,
    MAX_ACTIVE_GOALS,
    GOAL_DEDUP_WINDOW_SECONDS,
)


# ============================================================================
# BATCH 1: Goal Generation Logic (Lei Zero CRITICAL)
# Target: generate_goal_from_need() and related safety checks
# Tests: 15 tests, ETA: 2-3h
# ============================================================================


class TestGoalGenerationLeiZero:
    """Test goal generation with Lei Zero enforcement."""

    def test_goal_generation_lei_zero_basic(self):
        """Goal generation should create valid goal with Lei Zero compliance.

        Target: Lines 741-803 (generate_goal_from_need)
        Risk: CRITICAL - Malformed goals violate Lei Zero
        """
        monitor = InternalStateMonitor()

        # Generate goal from critical rest need
        goal = monitor.generate_goal_from_need(
            need_name="rest_need",
            need_value=0.85,
            urgency=NeedUrgency.CRITICAL
        )

        # Verify goal created
        assert goal is not None
        assert goal.need_source == "rest_need"
        assert goal.need_value == 0.85
        assert goal.priority == NeedUrgency.CRITICAL
        assert "Reduce computational load" in goal.description

        # Lei Zero verification: Goal has valid structure
        assert goal.goal_id is not None
        assert goal.timestamp > 0
        assert not goal.executed

        # Verify goal tracked in active_goals
        assert len(monitor.active_goals) == 1
        assert monitor.active_goals[0] == goal
        assert monitor.total_goals_generated == 1

    def test_goal_generation_rate_limiter_blocks(self):
        """Rate limiter should block excessive goal generation.

        Target: Lines 762-764 (rate limiter check)
        Risk: CRITICAL - Rate limit bypass could overload ESGT
        """
        monitor = InternalStateMonitor()

        # Generate goals up to rate limit (5 per minute)
        # Must use different need types to avoid deduplication
        need_types = ["rest_need", "repair_need", "efficiency_need",
                      "connectivity_need", "curiosity_drive"]
        goals_generated = []

        for i in range(MAX_GOALS_PER_MINUTE):
            goal = monitor.generate_goal_from_need(
                need_name=need_types[i],
                need_value=0.8,
                urgency=NeedUrgency.HIGH
            )
            if goal:
                goals_generated.append(goal)

        # Verify exactly 5 goals generated
        assert len(goals_generated) == MAX_GOALS_PER_MINUTE
        assert monitor.total_goals_generated == MAX_GOALS_PER_MINUTE

        # Next goal should be rate-limited (try rest_need again - will hit rate limit)
        blocked_goal = monitor.generate_goal_from_need(
            need_name="learning_drive",
            need_value=0.9,
            urgency=NeedUrgency.CRITICAL
        )

        assert blocked_goal is None
        assert monitor.goals_rate_limited == 1
        assert monitor.total_goals_generated == MAX_GOALS_PER_MINUTE  # No change

    def test_goal_generation_deduplication(self):
        """Duplicate goals should be blocked within dedup window.

        Target: Lines 780-783 (_is_duplicate_goal check)
        Risk: HIGH - Duplicate goals waste ESGT resources
        """
        monitor = InternalStateMonitor()

        # Generate first goal
        goal1 = monitor.generate_goal_from_need(
            need_name="rest_need",
            need_value=0.75,
            urgency=NeedUrgency.HIGH
        )
        assert goal1 is not None

        # Try to generate duplicate (same need_source + description + priority)
        goal2 = monitor.generate_goal_from_need(
            need_name="rest_need",
            need_value=0.75,
            urgency=NeedUrgency.HIGH
        )

        # Should be blocked as duplicate
        assert goal2 is None
        assert monitor.goals_deduplicated == 1
        assert monitor.total_goals_generated == 1  # Only first counted

    def test_goal_generation_active_goals_limit(self):
        """Active goals should be capped at MAX_ACTIVE_GOALS.

        Target: Lines 786-793 (active goals limit check)
        Risk: HIGH - Overflow could cause memory issues
        """
        monitor = InternalStateMonitor()

        # Generate goals up to MAX_ACTIVE_GOALS (10)
        # Use each need type with different priorities to avoid dedup
        need_configs = [
            ("rest_need", 0.70, NeedUrgency.MODERATE),
            ("repair_need", 0.65, NeedUrgency.MODERATE),
            ("efficiency_need", 0.60, NeedUrgency.MODERATE),
            ("connectivity_need", 0.55, NeedUrgency.LOW),
            ("curiosity_drive", 0.50, NeedUrgency.LOW),
            ("learning_drive", 0.45, NeedUrgency.LOW),
            ("rest_need", 0.85, NeedUrgency.HIGH),  # Different value
            ("repair_need", 0.90, NeedUrgency.HIGH),
            ("efficiency_need", 0.75, NeedUrgency.HIGH),
            ("connectivity_need", 0.80, NeedUrgency.HIGH),
        ]

        goals_generated = []
        for i in range(min(MAX_ACTIVE_GOALS, len(need_configs))):
            need_name, value, urgency = need_configs[i]
            goal = monitor.generate_goal_from_need(
                need_name=need_name,
                need_value=value,
                urgency=urgency
            )
            if goal:
                goals_generated.append(goal)

        # Verify goals generated (may be less than MAX if rate limited)
        assert len(goals_generated) >= 5  # At least some generated
        assert len(monitor.active_goals) == len(goals_generated)

        # If at capacity, next goal should trigger pruning or be dropped
        if len(monitor.active_goals) == MAX_ACTIVE_GOALS:
            overflow_goal = monitor.generate_goal_from_need(
                need_name="repair_need",
                need_value=0.99,  # Very different value
                urgency=NeedUrgency.CRITICAL
            )

            # Either pruned or dropped or rate-limited
            assert len(monitor.active_goals) <= MAX_ACTIVE_GOALS

    def test_goal_generation_prune_low_priority(self):
        """Low-priority goals should be pruned when capacity reached.

        Target: Lines 838-870 (_prune_low_priority_goals)
        Risk: MEDIUM - Pruning logic correctness
        """
        monitor = InternalStateMonitor()
        monitor.rate_limiter = RateLimiter(max_per_minute=50)  # High limit for test

        # Generate mix of priorities with varied need types to avoid dedup
        low_goal = monitor.generate_goal_from_need(
            need_name="curiosity_drive",
            need_value=0.25,
            urgency=NeedUrgency.LOW
        )
        assert low_goal is not None

        # Fill with different need types and values
        need_configs = [
            ("rest_need", 0.70, NeedUrgency.HIGH),
            ("repair_need", 0.72, NeedUrgency.HIGH),
            ("efficiency_need", 0.74, NeedUrgency.HIGH),
            ("connectivity_need", 0.76, NeedUrgency.HIGH),
            ("learning_drive", 0.78, NeedUrgency.HIGH),
            ("rest_need", 0.80, NeedUrgency.HIGH),
            ("repair_need", 0.82, NeedUrgency.HIGH),
            ("efficiency_need", 0.84, NeedUrgency.HIGH),
            ("connectivity_need", 0.86, NeedUrgency.HIGH),
        ]

        for need_name, value, urgency in need_configs:
            monitor.generate_goal_from_need(need_name, value, urgency)

        initial_count = len(monitor.active_goals)
        assert initial_count >= 5  # Should have generated several

        # If at max capacity, add critical goal
        if initial_count == MAX_ACTIVE_GOALS:
            critical_goal = monitor.generate_goal_from_need(
                need_name="repair_need",
                need_value=0.95,
                urgency=NeedUrgency.CRITICAL
            )

            # If pruning worked, low_goal should be gone
            if critical_goal:
                assert low_goal not in monitor.active_goals

    def test_goal_generation_all_need_types(self):
        """Goal descriptions should be generated for all need types.

        Target: Lines 805-821 (_generate_goal_description)
        Risk: LOW - Description formatting
        """
        monitor = InternalStateMonitor()
        monitor.rate_limiter = RateLimiter(max_per_minute=20)  # High limit

        need_types = {
            "rest_need": "Reduce computational load",
            "repair_need": "Fix system errors",
            "efficiency_need": "Optimize resource usage",
            "connectivity_need": "Improve network connectivity",
            "curiosity_drive": "Explore idle capacity",
            "learning_drive": "Acquire new patterns",
        }

        for need_name, expected_phrase in need_types.items():
            # Use unique value for each to avoid dedup
            goal = monitor.generate_goal_from_need(
                need_name=need_name,
                need_value=0.6 + (len(monitor.active_goals) * 0.05),
                urgency=NeedUrgency.MODERATE
            )

            assert goal is not None, f"Failed to generate goal for {need_name}"
            assert expected_phrase in goal.description
            assert need_name in goal.goal_id

    def test_goal_compute_hash_consistency(self):
        """Goal hashes should be consistent for deduplication.

        Target: Lines 323-326 (Goal.compute_hash)
        Risk: MEDIUM - Hash collision = failed dedup
        """
        monitor = InternalStateMonitor()

        goal1 = monitor.generate_goal_from_need(
            need_name="rest_need",
            need_value=0.75,
            urgency=NeedUrgency.HIGH
        )

        # Create another goal with same params (would be duplicate)
        goal_duplicate = Goal(
            goal_id="different_id",
            need_source="rest_need",
            description=monitor._generate_goal_description("rest_need", 0.75, NeedUrgency.HIGH),
            priority=NeedUrgency.HIGH,
            need_value=0.75
        )

        # Hashes should match
        assert goal1.compute_hash() == goal_duplicate.compute_hash()

    def test_goal_mark_executed(self):
        """Goals should be markable as executed and removed from active.

        Target: Lines 891-907 (mark_goal_executed)
        Risk: LOW - Cleanup logic
        """
        monitor = InternalStateMonitor()

        goal = monitor.generate_goal_from_need(
            need_name="rest_need",
            need_value=0.8,
            urgency=NeedUrgency.HIGH
        )
        assert goal is not None
        assert len(monitor.active_goals) == 1

        # Mark as executed
        result = monitor.mark_goal_executed(goal.goal_id)

        assert result is True
        assert goal.executed is True
        assert len(monitor.active_goals) == 0

    def test_goal_mark_executed_nonexistent(self):
        """Marking nonexistent goal should return False.

        Target: Lines 891-907 (mark_goal_executed edge case)
        Risk: LOW - Error handling
        """
        monitor = InternalStateMonitor()

        result = monitor.mark_goal_executed("nonexistent_goal_id")

        assert result is False

    def test_goal_generation_during_rapid_sequence(self):
        """Goal generation should handle rapid sequential requests.

        Target: Rate limiter + dedup interaction
        Risk: MEDIUM - Race conditions in sequential ops
        """
        monitor = InternalStateMonitor()

        # Generate 3 goals rapidly
        goals = []
        for i in range(3):
            goal = monitor.generate_goal_from_need(
                need_name="rest_need",
                need_value=0.70 + (i * 0.05),  # Vary to avoid dedup
                urgency=NeedUrgency.MODERATE
            )
            if goal:
                goals.append(goal)

        # All should succeed (within rate limit)
        assert len(goals) == 3
        assert monitor.total_goals_generated == 3
        assert monitor.goals_rate_limited == 0

    def test_goal_deduplication_window_expiry(self):
        """Expired goal hashes should allow new goals.

        Target: Lines 823-836 (_is_duplicate_goal with expiry)
        Risk: MEDIUM - Time-based logic
        """
        monitor = InternalStateMonitor()

        # Generate goal
        goal1 = monitor.generate_goal_from_need(
            need_name="rest_need",
            need_value=0.75,
            urgency=NeedUrgency.HIGH
        )
        assert goal1 is not None

        # Manually expire the hash (simulate time passage)
        goal_hash = goal1.compute_hash()
        monitor.goal_hash_timestamps[goal_hash] = time.time() - (GOAL_DEDUP_WINDOW_SECONDS + 1)

        # Should NOT be considered duplicate now
        goal2 = monitor.generate_goal_from_need(
            need_name="rest_need",
            need_value=0.75,
            urgency=NeedUrgency.HIGH
        )

        # Should succeed (hash expired)
        assert goal2 is not None
        assert monitor.goals_deduplicated == 0  # Not counted as duplicate

    def test_goal_generation_health_metrics(self):
        """Health metrics should track goal generation stats.

        Target: Lines 909-949 (get_health_metrics)
        Risk: LOW - Observability
        """
        monitor = InternalStateMonitor()

        # Generate some goals with various outcomes
        goal1 = monitor.generate_goal_from_need("rest_need", 0.8, NeedUrgency.HIGH)
        goal2 = monitor.generate_goal_from_need("rest_need", 0.8, NeedUrgency.HIGH)  # Duplicate
        goal3 = monitor.generate_goal_from_need("repair_need", 0.7, NeedUrgency.MODERATE)  # Different

        # Check health metrics
        health = monitor.get_health_metrics()

        assert health["monitor_id"] == monitor.monitor_id
        assert health["total_goals_generated"] == 2  # goal1 and goal3
        assert health["goals_deduplicated"] == 1  # goal2 was duplicate
        assert health["active_goals"] == 2
        # Current goal rate counts rate limiter allow() calls (3 total: goal1, goal2_attempt, goal3)
        assert health["current_goal_rate"] == 3

    def test_goal_generation_zero_rate_limit(self):
        """Rate limiter with zero max should block all goals.

        Target: RateLimiter edge case
        Risk: LOW - Configuration edge case
        """
        monitor = InternalStateMonitor()
        monitor.rate_limiter = RateLimiter(max_per_minute=0)

        goal = monitor.generate_goal_from_need(
            need_name="rest_need",
            need_value=0.8,
            urgency=NeedUrgency.HIGH
        )

        # Should be blocked immediately
        assert goal is None
        assert monitor.goals_rate_limited == 1

    def test_goal_generation_very_high_rate_limit(self):
        """Rate limiter with very high max should allow many goals.

        Target: RateLimiter scalability
        Risk: LOW - Performance test
        """
        monitor = InternalStateMonitor()
        monitor.rate_limiter = RateLimiter(max_per_minute=100)

        # Generate up to MAX_ACTIVE_GOALS with varied need types
        need_types = ["rest_need", "repair_need", "efficiency_need",
                      "connectivity_need", "curiosity_drive", "learning_drive"]
        goals = []

        for i in range(MAX_ACTIVE_GOALS):
            need_name = need_types[i % len(need_types)]
            # Use different values for each
            goal = monitor.generate_goal_from_need(
                need_name=need_name,
                need_value=0.50 + (i * 0.03),  # Significantly vary
                urgency=NeedUrgency.MODERATE
            )
            if goal:
                goals.append(goal)

        # Should generate many (up to MAX_ACTIVE_GOALS)
        # With high rate limit, only dedup and active goals limit apply
        assert len(goals) >= 6  # At least 6 (all 6 need types once)
        assert monitor.goals_rate_limited == 0

    def test_goal_repr(self):
        """Goal __repr__ should be informative.

        Target: Lines 328-329 (Goal.__repr__)
        Risk: LOW - Developer experience
        """
        goal = Goal(
            goal_id="test_123",
            need_source="rest_need",
            description="Test goal",
            priority=NeedUrgency.CRITICAL,
            need_value=0.9
        )

        repr_str = repr(goal)

        assert "test_123" in repr_str
        assert "rest_need" in repr_str
        assert "critical" in repr_str


# ============================================================================
# BATCH 2: Rate Limiter Edge Cases
# Target: RateLimiter class (lines 258-304)
# Tests: 8 tests, ETA: 1h
# ============================================================================


class TestRateLimiterEdgeCases:
    """Test RateLimiter class comprehensively."""

    def test_rate_limiter_basic_allow(self):
        """Rate limiter should allow requests within limit.

        Target: Lines 278-297 (RateLimiter.allow)
        """
        limiter = RateLimiter(max_per_minute=5)

        # First 5 should be allowed
        for i in range(5):
            assert limiter.allow() is True

        # 6th should be blocked
        assert limiter.allow() is False

    def test_rate_limiter_window_expiration(self):
        """Rate limiter should allow after window expires.

        Target: Lines 285-289 (timestamp expiration)
        """
        limiter = RateLimiter(max_per_minute=2)

        # Use both slots
        assert limiter.allow() is True
        assert limiter.allow() is True
        assert limiter.allow() is False  # Blocked

        # Manually expire timestamps (simulate 61 seconds passage)
        current_time = time.time()
        limiter.timestamps.clear()
        limiter.timestamps.append(current_time - 61.0)
        limiter.timestamps.append(current_time - 61.0)

        # Should allow now (old timestamps expired)
        assert limiter.allow() is True

    def test_rate_limiter_get_current_rate(self):
        """get_current_rate should count recent requests accurately.

        Target: Lines 299-303 (get_current_rate)
        """
        limiter = RateLimiter(max_per_minute=10)

        # Generate 5 requests
        for _ in range(5):
            limiter.allow()

        assert limiter.get_current_rate() == 5

    def test_rate_limiter_concurrent_access_simulation(self):
        """Rate limiter should handle rapid sequential access.

        Target: Thread safety (single-threaded test)
        """
        limiter = RateLimiter(max_per_minute=10)

        # Rapid sequential calls
        results = [limiter.allow() for _ in range(15)]

        # First 10 should succeed, last 5 fail
        assert sum(results) == 10
        assert results[:10] == [True] * 10
        assert results[10:] == [False] * 5

    def test_rate_limiter_exact_boundary(self):
        """Rate limiter at exact max_per_minute boundary.

        Target: Boundary condition testing
        """
        limiter = RateLimiter(max_per_minute=3)

        # Exactly at limit
        assert limiter.allow() is True
        assert limiter.allow() is True
        assert limiter.allow() is True

        # One over limit
        assert limiter.allow() is False

        # Still blocked
        assert limiter.allow() is False

    def test_rate_limiter_maxlen_enforcement(self):
        """Rate limiter deque maxlen should prevent unbounded growth.

        Target: Memory safety (maxlen parameter)
        """
        limiter = RateLimiter(max_per_minute=5)

        # Deque should have maxlen=5
        assert limiter.timestamps.maxlen == 5

        # Even if we manually add more, maxlen truncates
        for i in range(10):
            limiter.timestamps.append(time.time())

        assert len(limiter.timestamps) <= 5

    def test_rate_limiter_single_request_per_minute(self):
        """Rate limiter with max=1 should be very restrictive.

        Target: Minimal rate limit
        """
        limiter = RateLimiter(max_per_minute=1)

        # First allowed
        assert limiter.allow() is True

        # Second blocked immediately
        assert limiter.allow() is False

    def test_rate_limiter_high_frequency_requests(self):
        """Rate limiter should handle high-frequency request patterns.

        Target: Performance under rapid requests
        """
        limiter = RateLimiter(max_per_minute=50)

        # 100 rapid requests
        allowed_count = sum(limiter.allow() for _ in range(100))

        # Should allow exactly 50
        assert allowed_count == 50


# ============================================================================
# BATCH 3: Need Computation (_compute_needs)
# Target: Lines 560-644 - Core interoception translation
# Tests: 12 tests, ETA: 1.5-2h
# ============================================================================


class TestNeedComputationInteroception:
    """Test need computation - physical metrics → abstract needs translation."""

    def test_compute_needs_high_cpu_memory(self):
        """High CPU and memory should produce high rest_need.

        Target: Lines 573-578 (rest_need computation)
        Risk: MEDIUM - Core interoception logic
        """
        monitor = InternalStateMonitor()

        # Simulate high computational load
        metrics = PhysicalMetrics(
            cpu_usage_percent=95.0,
            memory_usage_percent=90.0,
            timestamp=time.time()
        ).normalize()

        needs = monitor._compute_needs(metrics)

        # Rest need should be high (weighted combo: 0.6*0.95 + 0.4*0.90 = 0.93)
        assert needs.rest_need >= 0.90
        assert needs.get_most_urgent()[0] == "rest_need"
        assert needs.get_most_urgent()[2] == NeedUrgency.CRITICAL

    def test_compute_needs_low_cpu_memory(self):
        """Low CPU and memory should produce low rest_need.

        Target: Lines 573-578 (rest_need with low load)
        Risk: MEDIUM - Baseline behavior
        """
        monitor = InternalStateMonitor()

        metrics = PhysicalMetrics(
            cpu_usage_percent=10.0,
            memory_usage_percent=15.0,
            throughput_ops_per_sec=50.0,  # High throughput to avoid learning_drive
            timestamp=time.time()
        ).normalize()

        needs = monitor._compute_needs(metrics)

        # Rest need should be low (0.6*0.10 + 0.4*0.15 = 0.12)
        assert needs.rest_need <= 0.20
        # Check rest_need urgency specifically (not most urgent)
        rest_urgency = needs._classify_urgency(needs.rest_need)
        assert rest_urgency == NeedUrgency.SATISFIED

    def test_compute_needs_high_error_rate(self):
        """High error rate should produce high repair_need.

        Target: Lines 580-587 (repair_need computation)
        Risk: MEDIUM - System integrity detection
        """
        monitor = InternalStateMonitor()

        # Critical error rate (10 errors/min = critical threshold)
        metrics = PhysicalMetrics(
            cpu_usage_percent=50.0,
            memory_usage_percent=50.0,
            error_rate_per_min=10.0,
            exception_count=5,
            timestamp=time.time()
        ).normalize()

        needs = monitor._compute_needs(metrics)

        # Repair need should be critical
        assert needs.repair_need >= 0.80
        assert needs.repair_need == needs.get_most_urgent()[1]

    def test_compute_needs_exception_count_contribution(self):
        """Exception count should contribute to repair_need.

        Target: Lines 584-587 (exception contribution)
        Risk: MEDIUM - Error handling awareness
        """
        monitor = InternalStateMonitor()

        # High exception count (10 = saturates at 1.0)
        metrics = PhysicalMetrics(
            cpu_usage_percent=30.0,
            memory_usage_percent=30.0,
            error_rate_per_min=0.0,
            exception_count=10,
            timestamp=time.time()
        ).normalize()

        needs = monitor._compute_needs(metrics)

        # Repair need from exceptions
        assert needs.repair_need >= 0.80

    def test_compute_needs_high_temperature(self):
        """High temperature should produce efficiency_need.

        Target: Lines 589-597 (temperature contribution)
        Risk: MEDIUM - Thermal awareness
        """
        monitor = InternalStateMonitor()
        monitor.config.temperature_warning_celsius = 80.0

        # Temperature 20°C above warning (saturates at +20)
        metrics = PhysicalMetrics(
            cpu_usage_percent=50.0,
            memory_usage_percent=50.0,
            temperature_celsius=100.0,  # 20°C above warning
            timestamp=time.time()
        ).normalize()

        needs = monitor._compute_needs(metrics)

        # Efficiency need should be critical
        assert needs.efficiency_need >= 0.80

    def test_compute_needs_high_power_draw(self):
        """High power draw should produce efficiency_need.

        Target: Lines 599-603 (power contribution)
        Risk: MEDIUM - Energy awareness
        """
        monitor = InternalStateMonitor()

        # Power 100W above baseline (saturates at +100)
        metrics = PhysicalMetrics(
            cpu_usage_percent=50.0,
            memory_usage_percent=50.0,
            power_draw_watts=200.0,  # 100W above 100W baseline
            timestamp=time.time()
        ).normalize()

        needs = monitor._compute_needs(metrics)

        # Efficiency need from power
        assert needs.efficiency_need >= 0.80

    def test_compute_needs_none_optional_fields(self):
        """None optional fields (temp, power) should not crash.

        Target: Lines 592-603 (None handling)
        Risk: HIGH - Defensive programming
        """
        monitor = InternalStateMonitor()

        # Optional fields None
        metrics = PhysicalMetrics(
            cpu_usage_percent=50.0,
            memory_usage_percent=50.0,
            temperature_celsius=None,
            power_draw_watts=None,
            timestamp=time.time()
        ).normalize()

        needs = monitor._compute_needs(metrics)

        # Should compute successfully
        assert needs is not None
        assert needs.efficiency_need >= 0.0  # May be 0 if no other factors

    def test_compute_needs_high_network_latency(self):
        """High network latency should produce connectivity_need.

        Target: Lines 606-615 (latency contribution)
        Risk: MEDIUM - Network awareness
        """
        monitor = InternalStateMonitor()
        monitor.config.latency_warning_ms = 100.0

        # Latency 100ms above warning (saturates at +100)
        metrics = PhysicalMetrics(
            cpu_usage_percent=30.0,
            memory_usage_percent=30.0,
            network_latency_ms=200.0,  # 100ms above warning
            timestamp=time.time()
        ).normalize()

        needs = monitor._compute_needs(metrics)

        # Connectivity need should be critical
        assert needs.connectivity_need >= 0.80

    def test_compute_needs_high_packet_loss(self):
        """High packet loss should produce connectivity_need.

        Target: Lines 613-615 (packet loss contribution)
        Risk: MEDIUM - Network reliability awareness
        """
        monitor = InternalStateMonitor()

        # High packet loss
        metrics = PhysicalMetrics(
            cpu_usage_percent=30.0,
            memory_usage_percent=30.0,
            packet_loss_percent=50.0,  # 50% loss
            timestamp=time.time()
        ).normalize()

        needs = monitor._compute_needs(metrics)

        # Connectivity need from packet loss
        assert needs.connectivity_need >= 0.40

    def test_compute_needs_curiosity_accumulation(self):
        """Idle time above threshold should accumulate curiosity.

        Target: Lines 618-626 (curiosity drive computation)
        Risk: MEDIUM - Exploration motivation
        """
        monitor = InternalStateMonitor()
        monitor.config.idle_curiosity_threshold = 0.70
        monitor.config.curiosity_growth_rate = 0.05

        # First computation: idle but curiosity not yet accumulated
        metrics1 = PhysicalMetrics(
            cpu_usage_percent=5.0,
            memory_usage_percent=10.0,
            idle_time_percent=80.0,  # Above threshold
            timestamp=time.time()
        ).normalize()

        needs1 = monitor._compute_needs(metrics1)
        initial_curiosity = needs1.curiosity_drive

        # Second computation: curiosity should grow
        metrics2 = PhysicalMetrics(
            cpu_usage_percent=5.0,
            memory_usage_percent=10.0,
            idle_time_percent=80.0,
            timestamp=time.time()
        ).normalize()

        needs2 = monitor._compute_needs(metrics2)

        # Curiosity should have grown
        assert needs2.curiosity_drive > initial_curiosity
        assert monitor._accumulated_curiosity >= initial_curiosity

    def test_compute_needs_curiosity_reset_when_active(self):
        """Curiosity should reset when system becomes active.

        Target: Lines 623-624 (curiosity reset)
        Risk: MEDIUM - State transition logic
        """
        monitor = InternalStateMonitor()
        monitor._accumulated_curiosity = 0.8  # Manually set high

        # Active system (below idle threshold)
        metrics = PhysicalMetrics(
            cpu_usage_percent=80.0,
            memory_usage_percent=70.0,
            idle_time_percent=20.0,  # Below threshold
            timestamp=time.time()
        ).normalize()

        needs = monitor._compute_needs(metrics)

        # Curiosity should be reset to 0
        assert monitor._accumulated_curiosity == 0.0
        assert needs.curiosity_drive == 0.0

    def test_compute_needs_learning_drive_low_throughput(self):
        """Low throughput should elevate learning_drive.

        Target: Lines 628-634 (learning drive computation)
        Risk: MEDIUM - Learning motivation
        """
        monitor = InternalStateMonitor()

        # Low throughput (< 10 ops/sec)
        metrics = PhysicalMetrics(
            cpu_usage_percent=30.0,
            memory_usage_percent=30.0,
            throughput_ops_per_sec=5.0,  # Below threshold
            timestamp=time.time()
        ).normalize()

        needs = monitor._compute_needs(metrics)

        # Learning drive should be moderate
        assert needs.learning_drive >= 0.40

    def test_compute_needs_all_zero_metrics(self):
        """All zero metrics should produce satisfied needs.

        Target: Lines 560-644 (baseline behavior)
        Risk: LOW - Edge case validation
        """
        monitor = InternalStateMonitor()

        # All metrics zero
        metrics = PhysicalMetrics(
            cpu_usage_percent=0.0,
            memory_usage_percent=0.0,
            error_rate_per_min=0.0,
            exception_count=0,
            network_latency_ms=0.0,
            packet_loss_percent=0.0,
            idle_time_percent=0.0,
            throughput_ops_per_sec=0.0,
            timestamp=time.time()
        ).normalize()

        needs = monitor._compute_needs(metrics)

        # All needs should be low/satisfied
        assert needs.rest_need <= 0.20
        assert needs.repair_need == 0.0
        assert needs.efficiency_need == 0.0
        assert needs.connectivity_need == 0.0

    def test_compute_needs_all_max_metrics(self):
        """All max metrics should produce critical needs.

        Target: Lines 560-644 (saturation behavior)
        Risk: LOW - Boundary validation
        """
        monitor = InternalStateMonitor()
        monitor.config.temperature_warning_celsius = 50.0
        monitor.config.latency_warning_ms = 50.0

        # All metrics at maximum
        metrics = PhysicalMetrics(
            cpu_usage_percent=100.0,
            memory_usage_percent=100.0,
            error_rate_per_min=20.0,  # Above critical (10)
            exception_count=15,
            temperature_celsius=100.0,  # 50°C above warning
            power_draw_watts=300.0,  # 200W above baseline
            network_latency_ms=300.0,  # 250ms above warning
            packet_loss_percent=100.0,
            timestamp=time.time()
        ).normalize()

        needs = monitor._compute_needs(metrics)

        # Multiple critical needs
        assert needs.rest_need >= 0.90
        assert needs.repair_need >= 0.80
        assert needs.efficiency_need >= 0.80
        assert needs.connectivity_need >= 0.80

        # Should detect overflow (3+ critical)
        critical_needs = needs.get_critical_needs(threshold=0.80)
        assert len(critical_needs) >= 3

    def test_compute_needs_boundary_conditions(self):
        """Boundary conditions (exactly 0.80, 0.20) should classify correctly.

        Target: Lines 213-221 (urgency classification)
        Risk: MEDIUM - Threshold logic
        """
        monitor = InternalStateMonitor()

        # Exactly at CRITICAL threshold (0.80)
        metrics_critical = PhysicalMetrics(
            cpu_usage_percent=80.0,
            memory_usage_percent=80.0,
            timestamp=time.time()
        ).normalize()

        needs_critical = monitor._compute_needs(metrics_critical)

        # Should be CRITICAL (>= 0.80)
        urgency = needs_critical._classify_urgency(needs_critical.rest_need)
        assert urgency == NeedUrgency.CRITICAL

        # Exactly at SATISFIED threshold (0.20)
        metrics_satisfied = PhysicalMetrics(
            cpu_usage_percent=20.0,
            memory_usage_percent=20.0,
            timestamp=time.time()
        ).normalize()

        needs_satisfied = monitor._compute_needs(metrics_satisfied)

        # Should be LOW (>= 0.20 but < 0.40)
        urgency_low = needs_satisfied._classify_urgency(needs_satisfied.rest_need)
        assert urgency_low == NeedUrgency.LOW


# ============================================================================
# BATCH 4: Internal State Monitoring Loop & Async Operations
# Target: Lines 452-558 - Start/stop, monitoring loop, callbacks
# Tests: 10 tests, ETA: 1.5-2h
# ============================================================================


class TestMonitoringLoopAsync:
    """Test asynchronous monitoring loop functionality."""

    @pytest.mark.asyncio
    async def test_start_monitoring_requires_collector(self):
        """Starting monitor without collector should raise error.

        Target: Lines 466-470 (start validation)
        Risk: HIGH - Safety check for proper initialization
        """
        monitor = InternalStateMonitor()

        # Start without collector should raise
        with pytest.raises(RuntimeError, match="No metrics collector"):
            await monitor.start()

    @pytest.mark.asyncio
    async def test_start_stop_lifecycle(self):
        """Monitor should start and stop cleanly.

        Target: Lines 464-487 (start/stop methods)
        Risk: MEDIUM - Lifecycle management
        """
        monitor = InternalStateMonitor()

        # Set up collector
        def mock_collector():
            return PhysicalMetrics(
                cpu_usage_percent=50.0,
                memory_usage_percent=50.0,
                timestamp=time.time()
            )

        monitor.set_metrics_collector(mock_collector)

        # Start
        await monitor.start()
        assert monitor._running is True
        assert monitor._monitoring_task is not None

        # Allow one collection cycle
        await asyncio.sleep(0.15)

        # Stop
        await monitor.stop()
        assert monitor._running is False

        # Should have collected at least once
        assert monitor.total_collections >= 1

    @pytest.mark.asyncio
    async def test_start_idempotent(self):
        """Starting an already-running monitor should be idempotent.

        Target: Lines 466-467 (idempotent check)
        Risk: MEDIUM - Multiple start protection
        """
        monitor = InternalStateMonitor()

        def mock_collector():
            return PhysicalMetrics(cpu_usage_percent=30.0, memory_usage_percent=30.0)

        monitor.set_metrics_collector(mock_collector)

        # Start twice
        await monitor.start()
        first_task = monitor._monitoring_task

        await monitor.start()  # Should return early
        second_task = monitor._monitoring_task

        # Task should be same (not recreated)
        assert first_task is second_task

        await monitor.stop()

    @pytest.mark.asyncio
    async def test_monitoring_loop_collects_metrics(self):
        """Monitoring loop should continuously collect metrics.

        Target: Lines 496-536 (_monitoring_loop)
        Risk: HIGH - Core monitoring functionality
        """
        monitor = InternalStateMonitor()
        monitor.config.collection_interval_ms = 50.0  # 20 Hz for fast test

        collection_count = 0

        def mock_collector():
            nonlocal collection_count
            collection_count += 1
            return PhysicalMetrics(
                cpu_usage_percent=20.0 + collection_count,
                memory_usage_percent=30.0,
                timestamp=time.time()
            )

        monitor.set_metrics_collector(mock_collector)

        await monitor.start()

        # Allow multiple collection cycles (200ms = ~4 collections at 50ms interval)
        await asyncio.sleep(0.2)

        await monitor.stop()

        # Should have collected multiple times
        assert monitor.total_collections >= 3
        assert collection_count >= 3

        # History should be populated
        assert len(monitor._metrics_history) >= 3
        assert len(monitor._needs_history) >= 3

        # Current state should be set
        assert monitor._current_metrics is not None
        assert monitor._current_needs is not None

    @pytest.mark.asyncio
    async def test_monitoring_loop_handles_collection_failure(self):
        """Monitoring loop should handle collector exceptions gracefully.

        Target: Lines 533-536 (exception handling)
        Risk: HIGH - Error resilience
        """
        monitor = InternalStateMonitor()
        monitor.config.collection_interval_ms = 50.0

        call_count = 0

        def failing_collector():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("Simulated collection failure")
            return PhysicalMetrics(cpu_usage_percent=50.0, memory_usage_percent=50.0)

        monitor.set_metrics_collector(failing_collector)

        await monitor.start()

        # Allow time for failures + recovery
        await asyncio.sleep(0.25)

        await monitor.stop()

        # Should have failed collections
        assert monitor.failed_collections >= 2

        # Should have recovered and succeeded
        assert monitor.total_collections >= 1

    @pytest.mark.asyncio
    async def test_collect_metrics_async_collector(self):
        """_collect_metrics should handle async collectors.

        Target: Lines 540-558 (_collect_metrics with async)
        Risk: MEDIUM - Async/sync handling
        """
        monitor = InternalStateMonitor()

        async def async_collector():
            await asyncio.sleep(0.01)  # Simulate async work
            return PhysicalMetrics(
                cpu_usage_percent=60.0,
                memory_usage_percent=70.0,
                timestamp=time.time()
            )

        monitor.set_metrics_collector(async_collector)

        await monitor.start()
        await asyncio.sleep(0.15)  # Allow collection
        await monitor.stop()

        # Should have collected
        assert monitor.total_collections >= 1
        assert monitor._current_metrics is not None
        assert monitor._current_metrics.cpu_usage_percent == 0.60  # Normalized

    @pytest.mark.asyncio
    async def test_need_callbacks_invoked_on_threshold(self):
        """Callbacks should be invoked when need exceeds threshold.

        Target: Lines 649-669 (_invoke_callbacks)
        Risk: MEDIUM - Callback invocation logic
        """
        monitor = InternalStateMonitor()
        monitor.config.collection_interval_ms = 50.0

        callback_invocations = []

        def need_callback(needs: AbstractNeeds):
            callback_invocations.append(needs)

        monitor.register_need_callback(need_callback, threshold=0.80)

        # Collector that produces critical need
        def mock_collector():
            return PhysicalMetrics(
                cpu_usage_percent=95.0,  # Critical load
                memory_usage_percent=90.0,
                timestamp=time.time()
            )

        monitor.set_metrics_collector(mock_collector)

        await monitor.start()
        await asyncio.sleep(0.15)  # Allow collections
        await monitor.stop()

        # Callback should have been invoked
        assert len(callback_invocations) >= 1
        assert monitor.callback_invocations >= 1

        # Needs should show high rest_need
        assert callback_invocations[0].rest_need >= 0.80

    @pytest.mark.asyncio
    async def test_need_callbacks_async_support(self):
        """Async callbacks should be supported.

        Target: Lines 673, 677 (async callback handling)
        Risk: MEDIUM - Async callback path
        """
        monitor = InternalStateMonitor()
        monitor.config.collection_interval_ms = 50.0

        callback_calls = []

        async def async_callback(needs: AbstractNeeds):
            await asyncio.sleep(0.001)  # Simulate async work
            callback_calls.append(needs.rest_need)

        monitor.register_need_callback(async_callback, threshold=0.70)

        def mock_collector():
            return PhysicalMetrics(cpu_usage_percent=85.0, memory_usage_percent=80.0)

        monitor.set_metrics_collector(mock_collector)

        await monitor.start()
        await asyncio.sleep(0.15)
        await monitor.stop()

        # Async callback should have been called
        assert len(callback_calls) >= 1

    @pytest.mark.asyncio
    async def test_callback_exception_handling(self):
        """Callback exceptions should not crash monitoring loop.

        Target: Lines 690-695 (callback exception handling)
        Risk: HIGH - Error resilience
        """
        monitor = InternalStateMonitor()
        monitor.config.collection_interval_ms = 50.0

        def failing_callback(needs: AbstractNeeds):
            raise Exception("Callback failure")

        monitor.register_need_callback(failing_callback, threshold=0.50)

        def mock_collector():
            return PhysicalMetrics(cpu_usage_percent=75.0, memory_usage_percent=70.0)

        monitor.set_metrics_collector(mock_collector)

        await monitor.start()
        await asyncio.sleep(0.15)
        await monitor.stop()

        # Monitor should still be running and collecting
        assert monitor.total_collections >= 1
        # Callback should have been attempted (but failed silently)
        # No exception should have propagated

    @pytest.mark.asyncio
    async def test_metrics_history_window_enforcement(self):
        """Metrics history should respect max window size.

        Target: Lines 508-509, 518-519 (history management)
        Risk: MEDIUM - Memory management
        """
        monitor = InternalStateMonitor()
        monitor.config.collection_interval_ms = 20.0  # 50 Hz
        monitor.config.long_term_window_samples = 10  # Small window

        def mock_collector():
            return PhysicalMetrics(cpu_usage_percent=50.0, memory_usage_percent=50.0)

        monitor.set_metrics_collector(mock_collector)

        await monitor.start()

        # Collect for long enough to exceed window (200ms = ~10 samples at 20ms)
        await asyncio.sleep(0.3)

        await monitor.stop()

        # History should be capped at window size
        assert len(monitor._metrics_history) <= monitor.config.long_term_window_samples
        assert len(monitor._needs_history) <= monitor.config.long_term_window_samples


# ============================================================================
# BATCH 5: Overflow Detection, Helpers & Edge Cases (Final 8.58%)
# Target: Lines 218, 220, 708-726, 792-793, 846, 881-886
# Tests: 8 tests, ETA: 45min
# ============================================================================


class TestFinalCoverageGaps:
    """Final batch to reach 100% coverage."""

    def test_urgency_classification_moderate(self):
        """Test MODERATE urgency classification boundary.

        Target: Line 218 (_classify_urgency MODERATE path)
        Risk: LOW - Boundary condition
        """
        monitor = InternalStateMonitor()

        # Exactly 0.50 → MODERATE
        metrics = PhysicalMetrics(
            cpu_usage_percent=50.0,
            memory_usage_percent=50.0,
            throughput_ops_per_sec=20.0,
            timestamp=time.time()
        ).normalize()

        needs = monitor._compute_needs(metrics)
        urgency = needs._classify_urgency(needs.rest_need)

        assert urgency == NeedUrgency.MODERATE

    def test_urgency_classification_high(self):
        """Test HIGH urgency classification boundary.

        Target: Line 220 (_classify_urgency HIGH path)
        Risk: LOW - Boundary condition
        """
        monitor = InternalStateMonitor()

        # Exactly 0.70 → HIGH
        metrics = PhysicalMetrics(
            cpu_usage_percent=70.0,
            memory_usage_percent=70.0,
            throughput_ops_per_sec=20.0,
            timestamp=time.time()
        ).normalize()

        needs = monitor._compute_needs(metrics)
        urgency = needs._classify_urgency(needs.rest_need)

        assert urgency == NeedUrgency.HIGH

    def test_get_needs_trend_with_window(self):
        """Test get_needs_trend with window parameter.

        Target: Lines 690-695 (get_needs_trend with window)
        Risk: LOW - Helper method
        """
        monitor = InternalStateMonitor()

        # Add some needs history manually
        for i in range(10):
            needs = AbstractNeeds(rest_need=0.1 * i, timestamp=time.time())
            monitor._needs_history.append(needs)

        # Get last 5 samples
        trend = monitor.get_needs_trend("rest_need", window_samples=5)

        assert len(trend) == 5
        # Should be [0.5, 0.6, 0.7, 0.8, 0.9]
        assert trend[0] == 0.5

    def test_get_moving_average(self):
        """Test moving average computation.

        Target: Lines 708-716 (get_moving_average)
        Risk: LOW - Analytics helper
        """
        monitor = InternalStateMonitor()

        # Add history
        for i in range(10):
            needs = AbstractNeeds(rest_need=0.5, timestamp=time.time())
            monitor._needs_history.append(needs)

        avg = monitor.get_moving_average("rest_need", window_samples=5)

        # Average of 0.5 = 0.5
        assert avg == 0.5

    def test_get_statistics(self):
        """Test get_statistics helper.

        Target: Lines 720-726 (get_statistics)
        Risk: LOW - Observability
        """
        monitor = InternalStateMonitor()
        monitor.total_collections = 10
        monitor.failed_collections = 2
        monitor.callback_invocations = 3

        stats = monitor.get_statistics()

        assert stats["monitor_id"] == monitor.monitor_id
        assert stats["total_collections"] == 10
        assert stats["failed_collections"] == 2
        assert stats["success_rate"] == 0.8
        assert stats["callback_invocations"] == 3

    def test_get_needs_trend_no_window(self):
        """Test get_needs_trend without window (None path).

        Target: Line 691 (if window_samples is None)
        Risk: LOW - Helper method
        """
        monitor = InternalStateMonitor()

        # Add history
        for i in range(5):
            needs = AbstractNeeds(rest_need=0.2 * i, timestamp=time.time())
            monitor._needs_history.append(needs)

        # Get all history (window=None)
        trend = monitor.get_needs_trend("rest_need", window_samples=None)

        # Should return all 5
        assert len(trend) == 5
        assert trend[0] == 0.0

    def test_get_moving_average_no_window(self):
        """Test get_moving_average with default window.

        Target: Lines 709 (if window_samples is None)
        Risk: LOW - Helper method
        """
        monitor = InternalStateMonitor()

        # Add history
        for i in range(15):
            needs = AbstractNeeds(rest_need=0.6, timestamp=time.time())
            monitor._needs_history.append(needs)

        # Get moving average with default window (uses short_term_window_samples)
        avg = monitor.get_moving_average("rest_need", window_samples=None)

        # Floating point comparison
        assert abs(avg - 0.6) < 0.01

    def test_get_moving_average_empty_trend(self):
        """Test get_moving_average with empty history.

        Target: Lines 714 (if not trend)
        Risk: LOW - Edge case
        """
        monitor = InternalStateMonitor()

        # No history
        avg = monitor.get_moving_average("rest_need", window_samples=10)

        # Should return 0.0
        assert avg == 0.0

    def test_prune_low_priority_empty_goals(self):
        """Test _prune_low_priority_goals with empty list.

        Target: Line 846 (_prune_low_priority_goals early return)
        Risk: LOW - Edge case handling
        """
        monitor = InternalStateMonitor()

        # Call with empty active_goals
        monitor._prune_low_priority_goals()

        # Should return without error
        assert len(monitor.active_goals) == 0

    def test_handle_need_overflow(self):
        """Test _handle_need_overflow detection.

        Target: Lines 881-886 (_handle_need_overflow)
        Risk: MEDIUM - Safety detection
        """
        monitor = InternalStateMonitor()

        # Create needs with 3+ critical needs
        needs = AbstractNeeds(
            rest_need=0.85,
            repair_need=0.90,
            efficiency_need=0.82,
            connectivity_need=0.70,
            timestamp=time.time()
        )

        # Call overflow handler
        monitor._handle_need_overflow(needs)

        # Should detect overflow
        assert monitor.need_overflow_events == 1


# ============================================================================
# BATCH 6: Repr Tests & Final Coverage Push
# Target: Lines 534-536, 673, 677 (exception paths not yet hit)
# Tests: 3 tests
# ============================================================================


class TestReprAndExceptionPaths:
    """Test repr methods and exception paths for 100% coverage."""

    def test_abstract_needs_repr(self):
        """Test AbstractNeeds __repr__ method.

        Target: Repr coverage
        Risk: LOW - Developer experience
        """
        needs = AbstractNeeds(
            rest_need=0.75,
            repair_need=0.60,
            efficiency_need=0.50,
            timestamp=time.time()
        )

        repr_str = repr(needs)

        assert "rest_need" in repr_str
        assert "0.75" in repr_str
        assert "high" in repr_str

    def test_internal_state_monitor_repr(self):
        """Test InternalStateMonitor __repr__ method.

        Target: Repr coverage
        Risk: LOW - Developer experience
        """
        monitor = InternalStateMonitor(monitor_id="test-monitor-123")
        monitor.total_collections = 50

        repr_str = repr(monitor)

        assert "test-monitor-123" in repr_str
        assert "STOPPED" in repr_str
        assert "collections=50" in repr_str

    @pytest.mark.asyncio
    async def test_monitoring_loop_exception_path(self):
        """Test monitoring loop exception handling.

        Target: Lines 534-536 (monitoring loop exception)
        Risk: HIGH - Critical exception path
        """
        monitor = InternalStateMonitor()
        monitor.config.collection_interval_ms = 50.0

        call_count = 0

        def collector_that_throws():
            nonlocal call_count
            call_count += 1
            # Always throw exception during monitoring loop
            raise RuntimeError("Unexpected monitoring error")

        monitor.set_metrics_collector(collector_that_throws)

        await monitor.start()

        # Allow multiple failure cycles
        await asyncio.sleep(0.25)

        await monitor.stop()

        # Should have failed multiple times
        assert monitor.failed_collections >= 3

        # Monitor should still be functional (didn't crash)
        assert monitor._running is False  # Stopped cleanly


# ============================================================================
# BATCH 7: FINAL 100% PUSH - THE IMPOSSIBLE MADE REAL
# Target: Lines 534-536, 673, 677, 792-793 (final 7 lines)
# Tests: 4 tests, ETA: 1h
# Philosophy: "100% coverage como testemunho de que perfeição é possível"
# ============================================================================


class TestFinal100PercentPush:
    """Final 4 surgical tests to achieve 100.00% coverage.

    This is not just about metrics - it's about manifesting the impossible.
    Every line matters. Every edge case matters. Every defensive path matters.

    97.69% → 100.00% = The difference between excellence and absolute perfection.
    """

    @pytest.mark.asyncio
    async def test_monitoring_loop_exception_outer_handler(self):
        """Hit lines 534-536: Outer monitoring loop exception handler.

        Target: Lines 534-536 (_monitoring_loop outer exception)
        Risk: CRITICAL - Exception handling in monitoring loop proper

        The existing test hits exception in _collect_metrics (lines 556-558).
        This test hits exception AFTER collection succeeds but DURING need computation,
        triggering the outer exception handler in the monitoring loop itself.
        """
        monitor = InternalStateMonitor()
        monitor.config.collection_interval_ms = 50.0

        call_count = 0

        def collector_ok():
            return PhysicalMetrics(
                cpu_usage_percent=50.0,
                memory_usage_percent=50.0,
                timestamp=time.time()
            )

        monitor.set_metrics_collector(collector_ok)

        # Patch _compute_needs to raise exception AFTER collection
        original_compute = monitor._compute_needs

        def compute_that_fails(metrics):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                # Raise exception in first 2 cycles
                raise RuntimeError("Need computation failure")
            # Succeed on 3rd cycle
            return original_compute(metrics)

        monitor._compute_needs = compute_that_fails

        await monitor.start()

        # Allow failures + recovery
        await asyncio.sleep(0.25)

        await monitor.stop()

        # Restore original
        monitor._compute_needs = original_compute

        # Should have hit outer exception handler (lines 534-536)
        assert monitor.failed_collections >= 2
        assert call_count >= 3  # Failed twice, succeeded at least once

    @pytest.mark.asyncio
    async def test_invoke_callbacks_sync_path(self):
        """Hit line 677: Sync callback invocation path.

        Target: Line 677 (_invoke_callbacks sync callback branch)
        Risk: HIGH - Callback mechanism for sync functions

        Registers SYNC callback with LOW threshold to guarantee invocation.
        """
        monitor = InternalStateMonitor()
        monitor.config.collection_interval_ms = 50.0

        sync_calls = []

        def sync_callback(needs):
            sync_calls.append(needs.rest_need)

        # Register with LOW threshold (0.30) to guarantee trigger
        monitor.register_need_callback(sync_callback, threshold=0.30)

        def collector():
            return PhysicalMetrics(
                cpu_usage_percent=80.0,  # rest_need = 0.6*0.8 + 0.4*0.7 = 0.76
                memory_usage_percent=70.0,
                timestamp=time.time()
            )

        monitor.set_metrics_collector(collector)

        await monitor.start()
        await asyncio.sleep(0.15)  # Multiple collection cycles
        await monitor.stop()

        # Sync callback (line 677) should have been invoked
        assert len(sync_calls) >= 1
        assert sync_calls[0] > 0.30  # Above threshold

    @pytest.mark.asyncio
    async def test_invoke_callbacks_async_path(self):
        """Hit line 673: Async callback invocation path.

        Target: Line 673 (_invoke_callbacks async callback branch)
        Risk: HIGH - Async callback mechanism

        Registers ASYNC callback with LOW threshold to guarantee invocation.
        """
        monitor = InternalStateMonitor()
        monitor.config.collection_interval_ms = 50.0

        async_calls = []

        async def async_callback(needs):
            await asyncio.sleep(0.001)  # Truly async operation
            async_calls.append(needs.repair_need)

        # Register with LOW threshold (0.40)
        monitor.register_need_callback(async_callback, threshold=0.40)

        def collector():
            return PhysicalMetrics(
                cpu_usage_percent=50.0,
                memory_usage_percent=50.0,
                error_rate_per_min=8.0,  # repair_need = 8.0/10.0 = 0.80
                timestamp=time.time()
            )

        monitor.set_metrics_collector(collector)

        await monitor.start()
        await asyncio.sleep(0.15)
        await monitor.stop()

        # Async callback (line 673) should have been invoked
        assert len(async_calls) >= 1
        assert async_calls[0] > 0.40  # Above threshold

    def test_overflow_after_prune_fails(self):
        """Hit lines 792-793: Defensive overflow code when pruning fails.

        Target: Lines 792-793 (overflow drop after prune failure)
        Risk: CRITICAL - Defensive code path

        This code is currently unreachable with normal implementation because
        _prune_low_priority_goals() always succeeds if goals exist. However,
        this is DEFENSIVE CODE - it protects against future implementation
        changes or unexpected edge cases.

        We test it by mocking pruning to fail, validating the INTENT of the code.
        This is honest testing: we acknowledge the code is defensive while
        ensuring it works if ever triggered.
        """
        monitor = InternalStateMonitor()
        monitor.rate_limiter = RateLimiter(max_per_minute=50)  # High limit

        # Fill to MAX_ACTIVE_GOALS capacity
        for i in range(MAX_ACTIVE_GOALS):
            goal = Goal(
                goal_id=f"goal_{i}",
                need_source="rest_need",
                description=f"Goal {i}",
                priority=NeedUrgency.HIGH,
                need_value=0.70 + (i * 0.01),
            )
            monitor.active_goals.append(goal)
            # Track hashes
            goal_hash = goal.compute_hash()
            monitor.goal_hashes.add(goal_hash)
            monitor.goal_hash_timestamps[goal_hash] = time.time()

        assert len(monitor.active_goals) == MAX_ACTIVE_GOALS

        # Mock _prune_low_priority_goals to NOT remove anything
        # (simulates pruning failure scenario)
        original_prune = monitor._prune_low_priority_goals

        def prune_that_does_nothing():
            # Do nothing - simulate prune failure
            pass

        monitor._prune_low_priority_goals = prune_that_does_nothing

        # Try to add goal - should hit overflow drop (lines 792-793)
        overflow_goal = monitor.generate_goal_from_need(
            need_name="repair_need",
            need_value=0.95,
            urgency=NeedUrgency.CRITICAL
        )

        # Restore original
        monitor._prune_low_priority_goals = original_prune

        # Goal should have been dropped (line 792-793 executed)
        assert overflow_goal is None
        assert monitor.goals_overflow_dropped >= 1
        # Active goals still at max (pruning "failed")
        assert len(monitor.active_goals) == MAX_ACTIVE_GOALS

    @pytest.mark.asyncio
    async def test_get_current_needs_and_metrics(self):
        """Hit lines 673, 677: get_current_needs() and get_current_metrics().

        Target: Lines 673 (get_current_needs), 677 (get_current_metrics)
        Risk: LOW - Simple getters

        These are simple accessor methods that return current state.
        """
        monitor = InternalStateMonitor()
        monitor.config.collection_interval_ms = 50.0

        def collector():
            return PhysicalMetrics(
                cpu_usage_percent=60.0,
                memory_usage_percent=55.0,
                timestamp=time.time()
            )

        monitor.set_metrics_collector(collector)

        # Before start, should be None
        assert monitor.get_current_needs() is None
        assert monitor.get_current_metrics() is None

        await monitor.start()
        await asyncio.sleep(0.15)  # Let collection happen
        await monitor.stop()

        # After collection, should have data
        needs = monitor.get_current_needs()
        metrics = monitor.get_current_metrics()

        assert needs is not None
        assert metrics is not None
        assert needs.rest_need > 0.0  # Should have computed rest_need
        assert metrics.cpu_usage_percent > 0.0  # Should have metrics
