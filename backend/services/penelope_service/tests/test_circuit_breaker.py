"""Tests for Circuit Breaker - Auto-Healing Protection.

Validates circuit breaker states, failure thresholds, and cooldown logic.

Biblical Foundation: Proverbs 14:15 - "The prudent gives thought to his steps"

Author: Vértice Platform Team
License: Proprietary
"""

import asyncio
import time

from core.circuit_breaker import HealingCircuitBreaker
import pytest

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def circuit_breaker():
    """HealingCircuitBreaker with default settings."""
    return HealingCircuitBreaker(
        failure_threshold=3, window_minutes=15, cooldown_minutes=60
    )


@pytest.fixture
def strict_circuit_breaker():
    """HealingCircuitBreaker with strict settings for testing."""
    return HealingCircuitBreaker(
        failure_threshold=2, window_minutes=1, cooldown_minutes=2
    )


# ============================================================================
# TESTS: Initialization
# ============================================================================


class TestInitialization:
    """Test circuit breaker initialization."""

    @pytest.mark.asyncio
    async def test_default_initialization(self):
        """
        GIVEN: Default circuit breaker parameters
        WHEN: HealingCircuitBreaker is created
        THEN: Correct thresholds and empty state
        """
        cb = HealingCircuitBreaker()

        assert cb.failure_threshold == 3
        assert cb.window_minutes == 15
        assert cb.cooldown_minutes == 60
        assert cb.failures == {}
        assert cb.state == {}
        assert cb.opened_at == {}

    @pytest.mark.asyncio
    async def test_custom_initialization(self):
        """
        GIVEN: Custom circuit breaker parameters
        WHEN: HealingCircuitBreaker is created
        THEN: Custom thresholds set correctly
        """
        cb = HealingCircuitBreaker(
            failure_threshold=5, window_minutes=30, cooldown_minutes=120
        )

        assert cb.failure_threshold == 5
        assert cb.window_minutes == 30
        assert cb.cooldown_minutes == 120


# ============================================================================
# TESTS: State - CLOSED (Normal Operation)
# ============================================================================


class TestClosedState:
    """Test circuit breaker in CLOSED state."""

    @pytest.mark.asyncio
    async def test_initial_state_closed(self, circuit_breaker):
        """
        GIVEN: New service (no failures)
        WHEN: is_allowed() is called
        THEN: Returns allowed=True, state=closed
        """
        allowed, reason = await circuit_breaker.is_allowed("service-1")

        assert allowed is True
        assert "closed" in reason.lower()

    @pytest.mark.asyncio
    async def test_multiple_allowed_when_closed(self, circuit_breaker):
        """
        GIVEN: Circuit in CLOSED state
        WHEN: Multiple is_allowed() calls
        THEN: All allowed
        """
        for _ in range(10):
            allowed, _ = await circuit_breaker.is_allowed("service-1")
            assert allowed is True

    @pytest.mark.asyncio
    async def test_success_in_closed_state(self, circuit_breaker):
        """
        GIVEN: Circuit in CLOSED state
        WHEN: record_success() is called
        THEN: Remains closed
        """
        await circuit_breaker.record_success("service-1")

        status = await circuit_breaker.get_status("service-1")
        assert status["state"] == "closed"


# ============================================================================
# TESTS: Failure Tracking
# ============================================================================


class TestFailureTracking:
    """Test failure tracking and windowing."""

    @pytest.mark.asyncio
    async def test_single_failure_tracked(self, circuit_breaker):
        """
        GIVEN: No prior failures
        WHEN: record_failure() is called
        THEN: Failure count = 1, state remains closed
        """
        await circuit_breaker.record_failure("service-1", error="Test error")

        status = await circuit_breaker.get_status("service-1")
        assert status["failure_count"] == 1
        assert status["state"] == "closed"

    @pytest.mark.asyncio
    async def test_multiple_failures_below_threshold(self, circuit_breaker):
        """
        GIVEN: Failures below threshold
        WHEN: record_failure() called multiple times
        THEN: Failures tracked, circuit remains closed
        """
        await circuit_breaker.record_failure("service-1")
        await circuit_breaker.record_failure("service-1")

        status = await circuit_breaker.get_status("service-1")
        assert status["failure_count"] == 2
        assert status["state"] == "closed"

    @pytest.mark.asyncio
    async def test_failure_window_sliding(self, strict_circuit_breaker):
        """
        GIVEN: Failures older than time window
        WHEN: get_status() is called
        THEN: Old failures removed from count
        """
        # Add failures
        await strict_circuit_breaker.record_failure("service-1")

        # Manually age failures (simulate time passing)
        # Window is 1 minute, so age by 61 seconds
        now = time.time()
        strict_circuit_breaker.failures["service-1"] = [now - 61]

        # Clean up old entries
        await strict_circuit_breaker.cleanup_old_entries()

        status = await strict_circuit_breaker.get_status("service-1")
        assert status["failure_count"] == 0

    @pytest.mark.asyncio
    async def test_independent_service_tracking(self, circuit_breaker):
        """
        GIVEN: Multiple services
        WHEN: Failures recorded for different services
        THEN: Each tracked independently
        """
        await circuit_breaker.record_failure("service-1")
        await circuit_breaker.record_failure("service-1")
        await circuit_breaker.record_failure("service-2")

        status1 = await circuit_breaker.get_status("service-1")
        status2 = await circuit_breaker.get_status("service-2")

        assert status1["failure_count"] == 2
        assert status2["failure_count"] == 1


# ============================================================================
# TESTS: State - OPEN (Circuit Breaker Triggered)
# ============================================================================


class TestOpenState:
    """Test circuit breaker in OPEN state."""

    @pytest.mark.asyncio
    async def test_circuit_opens_at_threshold(self, strict_circuit_breaker):
        """
        GIVEN: Failures reaching threshold
        WHEN: record_failure() called
        THEN: Circuit opens, is_allowed() returns False
        """
        # Threshold is 2, so record 2 failures
        await strict_circuit_breaker.record_failure("service-1")
        await strict_circuit_breaker.record_failure("service-1")

        status = await strict_circuit_breaker.get_status("service-1")
        assert status["state"] == "open"

        allowed, reason = await strict_circuit_breaker.is_allowed("service-1")
        assert allowed is False
        assert "open" in reason.lower()

    @pytest.mark.asyncio
    async def test_multiple_blocked_when_open(self, strict_circuit_breaker):
        """
        GIVEN: Circuit in OPEN state
        WHEN: Multiple is_allowed() calls
        THEN: All blocked
        """
        # Open circuit
        await strict_circuit_breaker.record_failure("service-1")
        await strict_circuit_breaker.record_failure("service-1")

        # Try multiple times
        for _ in range(5):
            allowed, _ = await strict_circuit_breaker.is_allowed("service-1")
            assert allowed is False

    @pytest.mark.asyncio
    async def test_cooldown_remaining_calculated(self, strict_circuit_breaker):
        """
        GIVEN: Circuit in OPEN state
        WHEN: get_status() is called
        THEN: Cooldown remaining time is present
        """
        # Open circuit
        await strict_circuit_breaker.record_failure("service-1")
        await strict_circuit_breaker.record_failure("service-1")

        status = await strict_circuit_breaker.get_status("service-1")

        assert "cooldown_remaining_minutes" in status
        assert status["cooldown_remaining_minutes"] > 0
        assert (
            status["cooldown_remaining_minutes"]
            <= strict_circuit_breaker.cooldown_minutes
        )


# ============================================================================
# TESTS: State - HALF_OPEN (Testing Recovery)
# ============================================================================


class TestHalfOpenState:
    """Test circuit breaker in HALF_OPEN state."""

    @pytest.mark.asyncio
    async def test_transition_to_half_open_after_cooldown(self, strict_circuit_breaker):
        """
        GIVEN: Circuit in OPEN state with expired cooldown
        WHEN: is_allowed() is called
        THEN: Transitions to HALF_OPEN, allows request
        """
        # Open circuit
        await strict_circuit_breaker.record_failure("service-1")
        await strict_circuit_breaker.record_failure("service-1")

        # Manually expire cooldown (cooldown is 2 minutes)
        strict_circuit_breaker.opened_at["service-1"] = time.time() - (2.1 * 60)

        allowed, reason = await strict_circuit_breaker.is_allowed("service-1")

        assert allowed is True
        assert "half" in reason.lower()

        status = await strict_circuit_breaker.get_status("service-1")
        assert status["state"] == "half_open"

    @pytest.mark.asyncio
    async def test_half_open_success_closes_circuit(self, strict_circuit_breaker):
        """
        GIVEN: Circuit in HALF_OPEN state
        WHEN: record_success() is called
        THEN: Circuit closes, failures cleared
        """
        # Open circuit
        await strict_circuit_breaker.record_failure("service-1")
        await strict_circuit_breaker.record_failure("service-1")

        # Transition to half-open
        strict_circuit_breaker.opened_at["service-1"] = time.time() - (2.1 * 60)
        await strict_circuit_breaker.is_allowed("service-1")

        # Record success
        await strict_circuit_breaker.record_success("service-1")

        status = await strict_circuit_breaker.get_status("service-1")
        assert status["state"] == "closed"
        assert status["failure_count"] == 0

    @pytest.mark.asyncio
    async def test_half_open_failure_reopens_circuit(self, strict_circuit_breaker):
        """
        GIVEN: Circuit in HALF_OPEN state
        WHEN: record_failure() is called
        THEN: Circuit reopens, cooldown resets
        """
        # Open circuit
        await strict_circuit_breaker.record_failure("service-1")
        await strict_circuit_breaker.record_failure("service-1")

        # Transition to half-open
        strict_circuit_breaker.opened_at["service-1"] = time.time() - (2.1 * 60)
        await strict_circuit_breaker.is_allowed("service-1")

        # Record failure (test failed)
        await strict_circuit_breaker.record_failure("service-1")

        status = await strict_circuit_breaker.get_status("service-1")
        assert status["state"] == "open"


# ============================================================================
# TESTS: Administrative Operations
# ============================================================================


class TestAdministrativeOperations:
    """Test admin operations like reset_circuit."""

    @pytest.mark.asyncio
    async def test_reset_circuit_clears_state(self, strict_circuit_breaker):
        """
        GIVEN: Circuit in OPEN state with failures
        WHEN: reset_circuit() is called
        THEN: Circuit closed, failures cleared
        """
        # Open circuit
        await strict_circuit_breaker.record_failure("service-1")
        await strict_circuit_breaker.record_failure("service-1")

        # Reset
        await strict_circuit_breaker.reset_circuit("service-1")

        status = await strict_circuit_breaker.get_status("service-1")
        assert status["state"] == "closed"
        assert status["failure_count"] == 0

        allowed, _ = await strict_circuit_breaker.is_allowed("service-1")
        assert allowed is True

    @pytest.mark.asyncio
    async def test_get_all_statuses(self, circuit_breaker):
        """
        GIVEN: Multiple services with different states
        WHEN: get_all_statuses() is called
        THEN: Returns status for all services
        """
        await circuit_breaker.record_failure("service-1")
        await circuit_breaker.record_failure("service-2")
        await circuit_breaker.record_failure("service-2")

        statuses = await circuit_breaker.get_all_statuses()

        assert "service-1" in statuses
        assert "service-2" in statuses
        assert statuses["service-1"]["failure_count"] == 1
        assert statuses["service-2"]["failure_count"] == 2

    @pytest.mark.asyncio
    async def test_cleanup_old_entries(self, strict_circuit_breaker):
        """
        GIVEN: Mix of recent and old failures
        WHEN: cleanup_old_entries() is called
        THEN: Old entries removed
        """
        # Add failures
        await strict_circuit_breaker.record_failure("service-1")
        await strict_circuit_breaker.record_failure("service-2")

        # Manually age service-1 failures
        now = time.time()
        strict_circuit_breaker.failures["service-1"] = [now - 61]

        # Cleanup
        cleaned = await strict_circuit_breaker.cleanup_old_entries()

        assert cleaned >= 1
        status1 = await strict_circuit_breaker.get_status("service-1")
        assert status1["failure_count"] == 0


# ============================================================================
# TESTS: Concurrency and Thread Safety
# ============================================================================


class TestConcurrency:
    """Test thread-safe concurrent access."""

    @pytest.mark.asyncio
    async def test_concurrent_failures(self, circuit_breaker):
        """
        GIVEN: Multiple concurrent failures
        WHEN: record_failure() called concurrently
        THEN: All failures tracked correctly (no race conditions)
        """

        async def record_failure_wrapper(service):
            await circuit_breaker.record_failure(service)

        # Record 10 concurrent failures for service-1
        await asyncio.gather(*[record_failure_wrapper("service-1") for _ in range(10)])

        status = await circuit_breaker.get_status("service-1")
        assert status["failure_count"] == 10

    @pytest.mark.asyncio
    async def test_concurrent_is_allowed_checks(self, circuit_breaker):
        """
        GIVEN: Multiple concurrent is_allowed() checks
        WHEN: Called for same service
        THEN: All return consistent results
        """

        async def check_allowed(service):
            allowed, _ = await circuit_breaker.is_allowed(service)
            return allowed

        # Check 20 concurrent times
        results = await asyncio.gather(*[check_allowed("service-1") for _ in range(20)])

        # All should be True (circuit closed)
        assert all(results)


# ============================================================================
# INTEGRATION TEST: Full Circuit Breaker Workflow
# ============================================================================


class TestFullWorkflow:
    """Test complete circuit breaker lifecycle."""

    @pytest.mark.asyncio
    async def test_full_circuit_breaker_lifecycle(self, strict_circuit_breaker):
        """
        GIVEN: HealingCircuitBreaker initialized
        WHEN: Complete workflow executed
        THEN: All state transitions work correctly
        """
        # Step 1: Initial state (CLOSED)
        allowed, _ = await strict_circuit_breaker.is_allowed("service-1")
        assert allowed is True

        status = await strict_circuit_breaker.get_status("service-1")
        assert status["state"] == "closed"
        assert status["failure_count"] == 0

        # Step 2: Record failures (below threshold)
        await strict_circuit_breaker.record_failure("service-1", error="Error 1")

        status = await strict_circuit_breaker.get_status("service-1")
        assert status["state"] == "closed"
        assert status["failure_count"] == 1

        # Step 3: Reach threshold (OPEN)
        await strict_circuit_breaker.record_failure("service-1", error="Error 2")

        status = await strict_circuit_breaker.get_status("service-1")
        assert status["state"] == "open"
        assert status["failure_count"] == 2

        # Step 4: Verify blocked
        allowed, _ = await strict_circuit_breaker.is_allowed("service-1")
        assert allowed is False

        # Step 5: Wait for cooldown (simulate)
        strict_circuit_breaker.opened_at["service-1"] = time.time() - (2.1 * 60)

        # Step 6: Transition to HALF_OPEN
        allowed, _ = await strict_circuit_breaker.is_allowed("service-1")
        assert allowed is True

        status = await strict_circuit_breaker.get_status("service-1")
        assert status["state"] == "half_open"

        # Step 7: Success in HALF_OPEN -> CLOSED
        await strict_circuit_breaker.record_success("service-1")

        status = await strict_circuit_breaker.get_status("service-1")
        assert status["state"] == "closed"
        assert status["failure_count"] == 0

        # Step 8: Verify normal operation resumed
        allowed, _ = await strict_circuit_breaker.is_allowed("service-1")
        assert allowed is True


# ============================================================================
# TESTS: Edge Cases
# ============================================================================


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_get_status_nonexistent_service(self, circuit_breaker):
        """
        GIVEN: Service never seen before
        WHEN: get_status() is called
        THEN: Returns default closed state
        """
        status = await circuit_breaker.get_status("nonexistent-service")

        assert status["state"] == "closed"
        assert status["failure_count"] == 0

    @pytest.mark.asyncio
    async def test_reset_nonexistent_service(self, circuit_breaker):
        """
        GIVEN: Service never seen before
        WHEN: reset_circuit() is called
        THEN: No error, just logs warning
        """
        # Should not raise exception
        await circuit_breaker.reset_circuit("nonexistent-service")

        status = await circuit_breaker.get_status("nonexistent-service")
        assert status["state"] == "closed"

    @pytest.mark.asyncio
    async def test_empty_get_all_statuses(self, circuit_breaker):
        """
        GIVEN: No services tracked
        WHEN: get_all_statuses() is called
        THEN: Returns empty dict
        """
        statuses = await circuit_breaker.get_all_statuses()
        assert statuses == {}

    @pytest.mark.asyncio
    async def test_cleanup_with_no_failures(self, circuit_breaker):
        """
        GIVEN: No failures tracked
        WHEN: cleanup_old_entries() is called
        THEN: Returns 0, no errors
        """
        cleaned = await circuit_breaker.cleanup_old_entries()
        assert cleaned == 0
