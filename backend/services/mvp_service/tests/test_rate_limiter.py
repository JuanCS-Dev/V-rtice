"""Tests for Rate Limiter - Narrative Generation Rate Control.

Validates rate limiting logic, time windows, and per-service cooldowns.

Biblical Foundation: Ecclesiastes 3:1 - "A time for everything"

Author: Vértice Platform Team
License: Proprietary
"""

import asyncio
import time

from core.rate_limiter import NarrativeRateLimiter
import pytest

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def rate_limiter():
    """NarrativeRateLimiter with default limits."""
    return NarrativeRateLimiter(
        max_per_hour=100, max_per_day=1000, min_interval_seconds=60
    )


@pytest.fixture
def strict_rate_limiter():
    """NarrativeRateLimiter with very strict limits for testing."""
    return NarrativeRateLimiter(max_per_hour=5, max_per_day=10, min_interval_seconds=2)


# ============================================================================
# TESTS: Hourly Rate Limit
# ============================================================================


class TestHourlyRateLimit:
    """Test hourly rate limiting."""

    @pytest.mark.asyncio
    async def test_allows_requests_under_hourly_limit(self, rate_limiter):
        """
        GIVEN: Requests under hourly limit
        WHEN: check_rate_limit() is called
        THEN: All requests allowed
        """
        for i in range(10):
            allowed, reason, stats = await rate_limiter.check_rate_limit()
            assert allowed is True
            assert reason == "OK"
            assert stats["hour_count"] == i

    @pytest.mark.asyncio
    async def test_blocks_requests_over_hourly_limit(self, strict_rate_limiter):
        """
        GIVEN: Requests exceeding hourly limit
        WHEN: check_rate_limit() is called
        THEN: Excess requests blocked
        """
        # Allow 5 requests (max_per_hour=5)
        for i in range(5):
            allowed, _, _ = await strict_rate_limiter.check_rate_limit()
            assert allowed is True

        # 6th request should be blocked
        allowed, reason, stats = await strict_rate_limiter.check_rate_limit()
        assert allowed is False
        assert "Hourly limit reached" in reason
        assert stats["hour_remaining"] == 0

    @pytest.mark.asyncio
    async def test_hourly_window_sliding(self, strict_rate_limiter):
        """
        GIVEN: Requests at different times
        WHEN: Time passes beyond 1 hour
        THEN: Old requests removed from window
        """
        # Make 5 requests (at limit)
        for _ in range(5):
            await strict_rate_limiter.check_rate_limit()

        # Manually age the requests (simulate time passing)
        # Move all requests back 3601 seconds (beyond 1 hour window)
        now = time.time()
        strict_rate_limiter.request_history = [
            now - 3601 for _ in strict_rate_limiter.request_history
        ]

        # New request should be allowed (old ones outside window)
        allowed, reason, stats = await strict_rate_limiter.check_rate_limit()
        assert allowed is True
        assert stats["hour_count"] == 0  # Old requests cleaned up


# ============================================================================
# TESTS: Daily Rate Limit
# ============================================================================


class TestDailyRateLimit:
    """Test daily rate limiting."""

    @pytest.mark.asyncio
    async def test_allows_requests_under_daily_limit(self, rate_limiter):
        """
        GIVEN: Requests under daily limit
        WHEN: check_rate_limit() is called
        THEN: All requests allowed
        """
        for i in range(50):
            allowed, reason, stats = await rate_limiter.check_rate_limit()
            assert allowed is True
            assert stats["day_count"] == i

    @pytest.mark.asyncio
    async def test_blocks_requests_over_daily_limit(self):
        """
        GIVEN: Requests exceeding daily limit
        WHEN: check_rate_limit() is called
        THEN: Excess requests blocked
        """
        # Use custom limiter with high hourly but low daily
        limiter = NarrativeRateLimiter(
            max_per_hour=100, max_per_day=10, min_interval_seconds=1
        )

        # Allow 10 requests (max_per_day=10)
        for i in range(10):
            allowed, _, _ = await limiter.check_rate_limit()
            assert allowed is True

        # 11th request should be blocked
        allowed, reason, stats = await limiter.check_rate_limit()
        assert allowed is False
        assert "Daily limit reached" in reason
        assert stats["day_remaining"] == 0

    @pytest.mark.asyncio
    async def test_daily_window_sliding(self, strict_rate_limiter):
        """
        GIVEN: Requests older than 24 hours
        WHEN: check_rate_limit() is called
        THEN: Old requests removed from window
        """
        # Make 10 requests (at limit)
        for _ in range(10):
            await strict_rate_limiter.check_rate_limit()

        # Age all requests beyond 24 hours
        now = time.time()
        strict_rate_limiter.request_history = [
            now - 86401 for _ in strict_rate_limiter.request_history
        ]

        # New request should be allowed (old ones cleaned up)
        allowed, reason, stats = await strict_rate_limiter.check_rate_limit()
        assert allowed is True
        assert stats["day_count"] == 0


# ============================================================================
# TESTS: Per-Service Interval (Cooldown)
# ============================================================================


class TestPerServiceInterval:
    """Test per-service minimum interval (cooldown)."""

    @pytest.mark.asyncio
    async def test_allows_first_request_for_service(self, rate_limiter):
        """
        GIVEN: First request for a service
        WHEN: check_rate_limit() is called with service name
        THEN: Request allowed
        """
        allowed, reason, stats = await rate_limiter.check_rate_limit(service="svc-1")
        assert allowed is True
        assert reason == "OK"

    @pytest.mark.asyncio
    async def test_blocks_rapid_requests_same_service(self, strict_rate_limiter):
        """
        GIVEN: Two rapid requests for same service
        WHEN: Second request within min_interval
        THEN: Second request blocked
        """
        # First request allowed
        allowed1, _, _ = await strict_rate_limiter.check_rate_limit(service="svc-1")
        assert allowed1 is True

        # Immediate second request blocked (min_interval=2s)
        allowed2, reason2, stats2 = await strict_rate_limiter.check_rate_limit(
            service="svc-1"
        )
        assert allowed2 is False
        assert "Too soon" in reason2
        assert "svc-1" in reason2
        assert "service_cooldown_remaining" in stats2

    @pytest.mark.asyncio
    async def test_allows_request_after_interval(self, strict_rate_limiter):
        """
        GIVEN: Request after min_interval has passed
        WHEN: check_rate_limit() is called
        THEN: Request allowed
        """
        # First request
        await strict_rate_limiter.check_rate_limit(service="svc-1")

        # Wait for interval (2 seconds)
        await asyncio.sleep(2.1)

        # Second request should be allowed
        allowed, reason, _ = await strict_rate_limiter.check_rate_limit(service="svc-1")
        assert allowed is True
        assert reason == "OK"

    @pytest.mark.asyncio
    async def test_different_services_independent_cooldowns(self, strict_rate_limiter):
        """
        GIVEN: Requests for different services
        WHEN: check_rate_limit() called for each
        THEN: Each service has independent cooldown
        """
        # Service 1 request
        allowed1, _, _ = await strict_rate_limiter.check_rate_limit(service="svc-1")
        assert allowed1 is True

        # Service 2 request immediately (should be allowed)
        allowed2, _, _ = await strict_rate_limiter.check_rate_limit(service="svc-2")
        assert allowed2 is True

        # Service 1 rapid request (should be blocked)
        allowed3, reason3, _ = await strict_rate_limiter.check_rate_limit(
            service="svc-1"
        )
        assert allowed3 is False
        assert "svc-1" in reason3

        # Service 2 rapid request (should also be blocked)
        allowed4, reason4, _ = await strict_rate_limiter.check_rate_limit(
            service="svc-2"
        )
        assert allowed4 is False
        assert "svc-2" in reason4

    @pytest.mark.asyncio
    async def test_no_service_specified_skips_cooldown(self, strict_rate_limiter):
        """
        GIVEN: Requests without service name
        WHEN: check_rate_limit() called without service parameter
        THEN: Per-service cooldown not enforced
        """
        # Multiple rapid requests without service
        for _ in range(5):
            allowed, _, _ = await strict_rate_limiter.check_rate_limit()
            # All allowed (only global limits apply)
            assert allowed is True


# ============================================================================
# TESTS: Statistics and Monitoring
# ============================================================================


class TestStatistics:
    """Test get_rate_limit_status() and statistics."""

    @pytest.mark.asyncio
    async def test_get_status_no_usage(self, rate_limiter):
        """
        GIVEN: No requests yet
        WHEN: get_rate_limit_status() is called
        THEN: Returns zero counts, full capacity
        """
        status = await rate_limiter.get_rate_limit_status()

        assert status["hour_count"] == 0
        assert status["day_count"] == 0
        assert status["hour_remaining"] == 100
        assert status["day_remaining"] == 1000
        assert status["hour_percent_used"] == 0
        assert status["day_percent_used"] == 0
        assert status["active_services"] == 0

    @pytest.mark.asyncio
    async def test_get_status_with_usage(self, rate_limiter):
        """
        GIVEN: Some requests made
        WHEN: get_rate_limit_status() is called
        THEN: Returns accurate counts and remaining
        """
        # Make 10 requests
        for _ in range(10):
            await rate_limiter.check_rate_limit()

        status = await rate_limiter.get_rate_limit_status()

        assert status["hour_count"] == 10
        assert status["day_count"] == 10
        assert status["hour_remaining"] == 90
        assert status["day_remaining"] == 990
        assert status["hour_percent_used"] == pytest.approx(10.0)
        assert status["day_percent_used"] == pytest.approx(1.0)

    @pytest.mark.asyncio
    async def test_get_status_tracks_active_services(self, rate_limiter):
        """
        GIVEN: Requests for multiple services
        WHEN: get_rate_limit_status() is called
        THEN: active_services count is correct
        """
        await rate_limiter.check_rate_limit(service="svc-1")
        await rate_limiter.check_rate_limit(service="svc-2")
        await rate_limiter.check_rate_limit(service="svc-3")

        status = await rate_limiter.get_rate_limit_status()
        assert status["active_services"] == 3


# ============================================================================
# TESTS: Service Cooldown Management
# ============================================================================


class TestServiceCooldownManagement:
    """Test service-specific cooldown queries and management."""

    @pytest.mark.asyncio
    async def test_get_service_cooldown_no_requests(self, rate_limiter):
        """
        GIVEN: Service with no requests
        WHEN: get_service_cooldown() is called
        THEN: Returns not on cooldown
        """
        cooldown = await rate_limiter.get_service_cooldown("svc-1")

        assert cooldown["on_cooldown"] is False
        assert cooldown["remaining_seconds"] == 0.0
        assert cooldown["last_request_time"] is None

    @pytest.mark.asyncio
    async def test_get_service_cooldown_on_cooldown(self, strict_rate_limiter):
        """
        GIVEN: Recent request for service
        WHEN: get_service_cooldown() is called
        THEN: Returns on cooldown with remaining time
        """
        await strict_rate_limiter.check_rate_limit(service="svc-1")

        cooldown = await strict_rate_limiter.get_service_cooldown("svc-1")

        assert cooldown["on_cooldown"] is True
        assert cooldown["remaining_seconds"] > 0
        assert cooldown["last_request_time"] is not None

    @pytest.mark.asyncio
    async def test_reset_service_cooldown(self, strict_rate_limiter):
        """
        GIVEN: Service on cooldown
        WHEN: reset_service_cooldown() is called
        THEN: Cooldown cleared, next request allowed
        """
        # Create cooldown
        await strict_rate_limiter.check_rate_limit(service="svc-1")

        # Reset cooldown
        await strict_rate_limiter.reset_service_cooldown("svc-1")

        # Immediate request should now be allowed
        allowed, _, _ = await strict_rate_limiter.check_rate_limit(service="svc-1")
        assert allowed is True


# ============================================================================
# TESTS: Administrative Operations
# ============================================================================


class TestAdministrativeOperations:
    """Test admin operations like reset_all_limits."""

    @pytest.mark.asyncio
    async def test_reset_all_limits(self, strict_rate_limiter):
        """
        GIVEN: Rate limits at maximum
        WHEN: reset_all_limits() is called
        THEN: All limits cleared, requests allowed
        """
        # Reach limits
        for _ in range(10):
            await strict_rate_limiter.check_rate_limit()

        # Should be blocked now
        allowed1, _, _ = await strict_rate_limiter.check_rate_limit()
        assert allowed1 is False

        # Reset all limits
        await strict_rate_limiter.reset_all_limits()

        # Should be allowed again
        allowed2, _, _ = await strict_rate_limiter.check_rate_limit()
        assert allowed2 is True

    @pytest.mark.asyncio
    async def test_cleanup_old_entries(self, rate_limiter):
        """
        GIVEN: Mix of recent and old entries
        WHEN: cleanup_old_entries() is called
        THEN: Old entries removed, recent kept
        """
        # Add some requests
        for _ in range(10):
            await rate_limiter.check_rate_limit()

        # Manually add old entries (beyond 24 hours)
        now = time.time()
        rate_limiter.request_history.extend([now - 86401 for _ in range(5)])

        # Cleanup
        removed = await rate_limiter.cleanup_old_entries()

        assert removed == 5
        assert len(rate_limiter.request_history) == 10


# ============================================================================
# TESTS: Concurrency and Thread Safety
# ============================================================================


class TestConcurrency:
    """Test thread-safe concurrent access."""

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, rate_limiter):
        """
        GIVEN: Multiple concurrent requests
        WHEN: check_rate_limit() called concurrently
        THEN: All handled correctly (no race conditions)
        """

        async def make_request(i):
            # Use unique service per request to avoid cooldown conflicts
            allowed, _, stats = await rate_limiter.check_rate_limit(service=f"svc-{i}")
            return allowed

        # Run 50 concurrent requests
        results = await asyncio.gather(*[make_request(i) for i in range(50)])

        # All should be allowed (under limits, unique services)
        assert all(results)

        # Check final status
        status = await rate_limiter.get_rate_limit_status()
        assert status["hour_count"] == 50
        assert status["day_count"] == 50
        assert status["active_services"] == 50


# ============================================================================
# INTEGRATION TEST: Full Rate Limiting Workflow
# ============================================================================


class TestFullWorkflow:
    """Test complete rate limiting workflow."""

    @pytest.mark.asyncio
    async def test_full_rate_limiting_lifecycle(self, strict_rate_limiter):
        """
        GIVEN: NarrativeRateLimiter initialized
        WHEN: Multiple operations performed
        THEN: All rate limits enforced correctly
        """
        # Step 1: Make requests under limits
        for i in range(3):
            allowed, reason, stats = await strict_rate_limiter.check_rate_limit(
                service=f"svc-{i}"
            )
            assert allowed is True
            # Stats are calculated BEFORE adding current request
            # So after i requests, remaining should be 5 - i (not -1)
            assert stats["hour_remaining"] == 5 - i

        # Step 2: Check status
        status = await strict_rate_limiter.get_rate_limit_status()
        assert status["hour_count"] == 3
        assert status["active_services"] == 3

        # Step 3: Try rapid request for same service (blocked)
        allowed, reason, _ = await strict_rate_limiter.check_rate_limit(service="svc-0")
        assert allowed is False
        assert "Too soon" in reason

        # Step 4: Check service cooldown
        cooldown = await strict_rate_limiter.get_service_cooldown("svc-0")
        assert cooldown["on_cooldown"] is True

        # Step 5: Wait for cooldown
        await asyncio.sleep(2.1)

        # Step 6: Try again (should work)
        allowed, _, _ = await strict_rate_limiter.check_rate_limit(service="svc-0")
        assert allowed is True

        # Step 7: Reach hourly limit
        await strict_rate_limiter.check_rate_limit()  # 5th request

        # Step 8: Verify hourly limit enforced
        allowed, reason, _ = await strict_rate_limiter.check_rate_limit()
        assert allowed is False
        assert "Hourly limit" in reason
