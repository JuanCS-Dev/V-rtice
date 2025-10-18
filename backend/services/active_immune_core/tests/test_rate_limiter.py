"""Tests for coordination/rate_limiter.py

100% deterministic tests - no flakiness allowed.

Authors: Juan + Claude
Date: 2025-10-07
"""

import asyncio
import time

import pytest

from coordination.exceptions import LymphnodeRateLimitError, LymphnodeResourceExhaustedError
from coordination.rate_limiter import ClonalExpansionRateLimiter, RateLimiter

# ==================== RATE LIMITER TESTS ====================


class TestRateLimiter:
    """Test basic token bucket rate limiter"""

    @pytest.mark.asyncio
    async def test_acquire_single_token_success(self):
        """Test acquiring a single token when bucket has tokens"""
        limiter = RateLimiter(max_rate=10.0, max_burst=20)

        result = await limiter.acquire(1)

        assert result is True
        assert limiter.total_requests == 1
        assert limiter.total_accepted == 1
        assert limiter.total_rejected == 0

    @pytest.mark.asyncio
    async def test_acquire_multiple_tokens_success(self):
        """Test acquiring multiple tokens at once"""
        limiter = RateLimiter(max_rate=10.0, max_burst=20)

        result = await limiter.acquire(5)

        assert result is True
        assert limiter.total_accepted == 1
        assert limiter.get_available_tokens() < 20  # Should be reduced

    @pytest.mark.asyncio
    async def test_acquire_exhausts_bucket(self):
        """Test that acquiring all tokens exhausts bucket"""
        limiter = RateLimiter(max_rate=10.0, max_burst=20)

        # Exhaust bucket
        result1 = await limiter.acquire(20)
        assert result1 is True

        # Next request should be rejected (no refill time)
        result2 = await limiter.acquire(1)
        assert result2 is False
        assert limiter.total_rejected == 1

    @pytest.mark.asyncio
    async def test_acquire_refills_over_time(self):
        """Test that bucket refills tokens over time"""
        limiter = RateLimiter(max_rate=100.0, max_burst=20, refill_interval=0.01)

        # Exhaust bucket
        await limiter.acquire(20)
        available_before = limiter.get_available_tokens()

        # Wait for refill
        await asyncio.sleep(0.1)  # Should refill ~10 tokens (100/sec * 0.1s)

        # Should be able to acquire again
        result = await limiter.acquire(5)
        assert result is True

    @pytest.mark.asyncio
    async def test_acquire_or_raise_success(self):
        """Test acquire_or_raise when tokens available"""
        limiter = RateLimiter(max_rate=10.0, max_burst=20)

        # Should not raise
        await limiter.acquire_or_raise(5)

        assert limiter.total_accepted == 1

    @pytest.mark.asyncio
    async def test_acquire_or_raise_failure(self):
        """Test acquire_or_raise raises when rate limited"""
        limiter = RateLimiter(max_rate=10.0, max_burst=20)

        # Exhaust bucket
        await limiter.acquire(20)

        # Should raise
        with pytest.raises(LymphnodeRateLimitError) as exc_info:
            await limiter.acquire_or_raise(1)

        assert "Rate limit exceeded" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_acquire_rejects_zero_tokens(self):
        """Test rejection of acquire(0)"""
        limiter = RateLimiter(max_rate=10.0, max_burst=20)

        with pytest.raises(ValueError) as exc_info:
            await limiter.acquire(0)

        assert "tokens must be >= 1" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_acquire_rejects_tokens_exceeding_burst(self):
        """Test rejection when requested tokens > max_burst"""
        limiter = RateLimiter(max_rate=10.0, max_burst=20)

        with pytest.raises(ValueError) as exc_info:
            await limiter.acquire(21)  # > max_burst

        assert "exceeds max_burst" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_wait_for_token_immediate_success(self):
        """Test wait_for_token when tokens immediately available"""
        limiter = RateLimiter(max_rate=10.0, max_burst=20)

        result = await limiter.wait_for_token(5, timeout=1.0)

        assert result is True

    @pytest.mark.asyncio
    async def test_wait_for_token_timeout(self):
        """Test wait_for_token times out when rate limited"""
        limiter = RateLimiter(max_rate=1.0, max_burst=1, refill_interval=0.1)

        # Exhaust bucket
        await limiter.acquire(1)

        # Wait with very short timeout (should timeout)
        start = time.monotonic()
        result = await limiter.wait_for_token(1, timeout=0.05)
        elapsed = time.monotonic() - start

        assert result is False
        assert elapsed >= 0.05  # Did wait for timeout
        assert elapsed < 0.2  # But not too long

    @pytest.mark.asyncio
    async def test_wait_for_token_success_after_refill(self):
        """Test wait_for_token succeeds after refill"""
        limiter = RateLimiter(max_rate=50.0, max_burst=10, refill_interval=0.01)

        # Exhaust bucket
        await limiter.acquire(10)

        # Wait for refill (should succeed within timeout)
        result = await limiter.wait_for_token(5, timeout=0.5)

        assert result is True

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Test statistics tracking"""
        limiter = RateLimiter(max_rate=10.0, max_burst=20)

        # Make some requests
        await limiter.acquire(5)  # Success
        await limiter.acquire(15)  # Success
        await limiter.acquire(1)  # Should fail (exhausted)

        stats = limiter.get_stats()

        assert stats["max_rate"] == 10.0
        assert stats["max_burst"] == 20
        assert stats["total_requests"] == 3
        assert stats["total_accepted"] == 2
        assert stats["total_rejected"] == 1
        assert stats["acceptance_rate"] == pytest.approx(2.0 / 3.0)

    @pytest.mark.asyncio
    async def test_reset(self):
        """Test reset clears statistics and refills bucket"""
        limiter = RateLimiter(max_rate=10.0, max_burst=20)

        # Exhaust bucket
        await limiter.acquire(20)
        assert limiter.total_requests == 1

        # Reset
        limiter.reset()

        # Should be able to acquire again
        result = await limiter.acquire(10)
        assert result is True
        assert limiter.total_requests == 1  # Reset count
        assert limiter.total_accepted == 1


# ==================== CLONAL EXPANSION RATE LIMITER TESTS ====================


class TestClonalExpansionRateLimiter:
    """Test specialized clonal expansion rate limiter"""

    @pytest.mark.asyncio
    async def test_check_clonal_expansion_success(self):
        """Test successful clonal expansion check"""
        limiter = ClonalExpansionRateLimiter(
            max_clones_per_minute=200,
            max_per_specialization=50,
            max_total_agents=1000,
        )

        # Should succeed
        await limiter.check_clonal_expansion(
            especializacao="threat_host-1",
            quantidade=10,
            current_total_agents=50,
        )

        # No exception raised = success

    @pytest.mark.asyncio
    async def test_check_clonal_expansion_global_rate_limit(self):
        """Test global rate limit enforcement"""
        limiter = ClonalExpansionRateLimiter(
            max_clones_per_minute=200,
            max_per_specialization=50,
            max_total_agents=1000,
        )

        # Exhaust global limit (200 clones) using multiple specializations
        # (each specialization limited to 50)
        await limiter.check_clonal_expansion("test1", 50, 0)
        await limiter.check_clonal_expansion("test2", 50, 50)
        await limiter.check_clonal_expansion("test3", 50, 100)
        await limiter.check_clonal_expansion("test4", 50, 150)

        # Next request should fail (global limit exhausted, no refill time)
        with pytest.raises(LymphnodeRateLimitError) as exc_info:
            await limiter.check_clonal_expansion("test5", 1, 200)

        assert "Rate limit exceeded" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_check_clonal_expansion_per_specialization_limit(self):
        """Test per-specialization limit enforcement"""
        limiter = ClonalExpansionRateLimiter(
            max_clones_per_minute=200,
            max_per_specialization=50,
            max_total_agents=1000,
        )

        # First request succeeds
        await limiter.check_clonal_expansion("threat_host-1", 30, 0)

        # Second request for same specialization (30+25=55 > 50) should fail
        with pytest.raises(LymphnodeRateLimitError) as exc_info:
            await limiter.check_clonal_expansion("threat_host-1", 25, 30)

        assert "Specialization limit exceeded" in str(exc_info.value)
        assert "threat_host-1" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_check_clonal_expansion_total_agents_limit(self):
        """Test total agents limit enforcement"""
        limiter = ClonalExpansionRateLimiter(
            max_clones_per_minute=200,
            max_per_specialization=50,
            max_total_agents=1000,
        )

        # Try to create clones that would exceed total limit
        with pytest.raises(LymphnodeResourceExhaustedError) as exc_info:
            await limiter.check_clonal_expansion("test", 50, 990)  # 990+50=1040 > 1000

        assert "Total agent limit exceeded" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_check_clonal_expansion_multiple_specializations(self):
        """Test that different specializations have independent limits"""
        limiter = ClonalExpansionRateLimiter(
            max_clones_per_minute=200,
            max_per_specialization=50,
            max_total_agents=1000,
        )

        # Create 40 clones for specialization A
        await limiter.check_clonal_expansion("threat_A", 40, 0)

        # Create 40 clones for specialization B (should succeed)
        await limiter.check_clonal_expansion("threat_B", 40, 40)

        # Both should be tracked independently
        stats = limiter.get_stats()
        assert stats["specialization_counts"]["threat_A"] == 40
        assert stats["specialization_counts"]["threat_B"] == 40

    @pytest.mark.asyncio
    async def test_release_clones(self):
        """Test releasing clones from specialization count"""
        limiter = ClonalExpansionRateLimiter(
            max_clones_per_minute=200,
            max_per_specialization=50,
            max_total_agents=1000,
        )

        # Create 45 clones
        await limiter.check_clonal_expansion("threat_host-1", 45, 0)

        stats_before = limiter.get_stats()
        assert stats_before["specialization_counts"]["threat_host-1"] == 45

        # Release 20 clones
        await limiter.release_clones("threat_host-1", 20)

        stats_after = limiter.get_stats()
        assert stats_after["specialization_counts"]["threat_host-1"] == 25

    @pytest.mark.asyncio
    async def test_release_clones_prevents_negative(self):
        """Test releasing more clones than exist doesn't go negative"""
        limiter = ClonalExpansionRateLimiter(
            max_clones_per_minute=200,
            max_per_specialization=50,
            max_total_agents=1000,
        )

        # Create 10 clones
        await limiter.check_clonal_expansion("test", 10, 0)

        # Release 20 clones (more than exist)
        await limiter.release_clones("test", 20)

        stats = limiter.get_stats()
        assert stats["specialization_counts"]["test"] == 0  # Should not go negative

    @pytest.mark.asyncio
    async def test_release_clones_allows_new_expansion(self):
        """Test that releasing clones allows new expansion"""
        limiter = ClonalExpansionRateLimiter(
            max_clones_per_minute=200,
            max_per_specialization=50,
            max_total_agents=1000,
        )

        # Fill specialization limit
        await limiter.check_clonal_expansion("threat_host-1", 50, 0)

        # Release all
        await limiter.release_clones("threat_host-1", 50)

        # Should be able to create more now
        await limiter.check_clonal_expansion("threat_host-1", 30, 0)

        stats = limiter.get_stats()
        assert stats["specialization_counts"]["threat_host-1"] == 30

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Test statistics retrieval"""
        limiter = ClonalExpansionRateLimiter(
            max_clones_per_minute=200,
            max_per_specialization=50,
            max_total_agents=1000,
        )

        # Create some clones
        await limiter.check_clonal_expansion("threat_A", 20, 0)
        await limiter.check_clonal_expansion("threat_B", 15, 20)

        stats = limiter.get_stats()

        assert stats["max_per_specialization"] == 50
        assert stats["max_total_agents"] == 1000
        assert stats["specialization_counts"]["threat_A"] == 20
        assert stats["specialization_counts"]["threat_B"] == 15
        # current_total_agents is set to the last value passed in check_clonal_expansion
        assert stats["current_total_agents"] == 20  # Last call had current_total_agents=20
        assert "global_limiter" in stats  # Includes nested global limiter stats

    @pytest.mark.asyncio
    async def test_zero_quantidade_rejected(self):
        """Test that quantidade=0 is rejected by global limiter"""
        limiter = ClonalExpansionRateLimiter(
            max_clones_per_minute=200,
            max_per_specialization=50,
            max_total_agents=1000,
        )

        # Should raise ValueError from RateLimiter.acquire()
        with pytest.raises(ValueError):
            await limiter.check_clonal_expansion("test", 0, 0)

    @pytest.mark.asyncio
    async def test_negative_quantidade_rejected(self):
        """Test that negative quantidade is rejected"""
        limiter = ClonalExpansionRateLimiter(
            max_clones_per_minute=200,
            max_per_specialization=50,
            max_total_agents=1000,
        )

        # Should raise ValueError from RateLimiter.acquire()
        with pytest.raises(ValueError):
            await limiter.check_clonal_expansion("test", -5, 0)


# ==================== INTEGRATION TESTS ====================


class TestRateLimiterIntegration:
    """Test rate limiter integration scenarios"""

    @pytest.mark.asyncio
    async def test_concurrent_acquire_safety(self):
        """Test that concurrent acquires don't cause race conditions"""
        limiter = RateLimiter(max_rate=100.0, max_burst=100)

        # Run 50 concurrent acquires (each taking 2 tokens)
        tasks = [limiter.acquire(2) for _ in range(50)]
        results = await asyncio.gather(*tasks)

        # Exactly 50 acquires should succeed (100 tokens / 2 per acquire)
        successes = sum(1 for r in results if r is True)
        failures = sum(1 for r in results if r is False)

        assert successes == 50
        assert failures == 0
        assert limiter.total_requests == 50
        assert limiter.total_accepted == 50

    @pytest.mark.asyncio
    async def test_burst_handling(self):
        """Test that burst capacity is properly enforced"""
        limiter = RateLimiter(max_rate=10.0, max_burst=5)

        # Burst of 5 requests (1 token each)
        results = []
        for _ in range(5):
            results.append(await limiter.acquire(1))

        # All 5 should succeed (burst capacity)
        assert all(results)

        # 6th request should fail immediately (no tokens left)
        result6 = await limiter.acquire(1)
        assert result6 is False

    @pytest.mark.asyncio
    async def test_realistic_clonal_expansion_scenario(self):
        """Test realistic multi-threat clonal expansion scenario"""
        limiter = ClonalExpansionRateLimiter(
            max_clones_per_minute=200,
            max_per_specialization=50,
            max_total_agents=1000,
        )

        # Simulate detecting 3 different threats
        await limiter.check_clonal_expansion("threat_sql_injection", 15, 100)
        await limiter.check_clonal_expansion("threat_port_scan", 20, 115)
        await limiter.check_clonal_expansion("threat_bruteforce", 10, 135)

        # All should succeed
        stats = limiter.get_stats()
        assert stats["specialization_counts"]["threat_sql_injection"] == 15
        assert stats["specialization_counts"]["threat_port_scan"] == 20
        assert stats["specialization_counts"]["threat_bruteforce"] == 10

        # Simulate destroying clones after threat neutralized
        await limiter.release_clones("threat_sql_injection", 15)

        # Should be able to create new specialization
        await limiter.check_clonal_expansion("threat_new", 15, 130)

        final_stats = limiter.get_stats()
        assert final_stats["specialization_counts"]["threat_sql_injection"] == 0
        assert final_stats["specialization_counts"]["threat_new"] == 15
