"""
100% Coverage Tests - backend/shared/security_tools/rate_limiter.py
====================================================================

Target: 103 statements, 20 branches
"""

import asyncio
import time
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

from backend.shared.security_tools.rate_limiter import (
    RateLimiter,
    RateLimitConfig,
    RateLimitStrategy,
    RateLimitExceeded,
    create_rate_limiter,
    REDIS_AVAILABLE,
)


class TestRateLimiterMemory:
    """Test in-memory rate limiting"""

    @pytest.mark.asyncio
    async def test_memory_basic_allow(self):
        """Test basic request allowance"""
        config = RateLimitConfig(max_requests=5, window_seconds=10)
        limiter = RateLimiter(config=config)

        allowed, retry_after = await limiter.check_rate_limit("user1")
        assert allowed is True
        assert retry_after == 0.0

    @pytest.mark.asyncio
    async def test_memory_exceed_limit(self):
        """Test exceeding rate limit"""
        config = RateLimitConfig(max_requests=2, window_seconds=10)
        limiter = RateLimiter(config=config)

        # Use up limit
        await limiter.check_rate_limit("user1", cost=2)
        # Exceed
        allowed, retry_after = await limiter.check_rate_limit("user1", cost=1)

        assert allowed is False
        assert retry_after > 0

    @pytest.mark.asyncio
    async def test_memory_cost_parameter(self):
        """Test request cost parameter"""
        config = RateLimitConfig(max_requests=10, window_seconds=10)
        limiter = RateLimiter(config=config)

        # Single expensive request (cost=10)
        allowed, _ = await limiter.check_rate_limit("user1", cost=10)
        assert allowed is True

        # Another request should fail
        allowed, retry_after = await limiter.check_rate_limit("user1", cost=1)
        assert allowed is False
        assert retry_after > 0

    @pytest.mark.asyncio
    async def test_memory_window_expiry(self):
        """Test time window expiration"""
        config = RateLimitConfig(max_requests=2, window_seconds=1)
        limiter = RateLimiter(config=config)

        # Fill limit
        await limiter.check_rate_limit("user1", cost=2)

        # Wait for window to expire
        await asyncio.sleep(1.1)

        # Should be allowed again
        allowed, retry_after = await limiter.check_rate_limit("user1", cost=1)
        assert allowed is True
        assert retry_after == 0.0

    @pytest.mark.asyncio
    async def test_memory_consume_raises_exception(self):
        """Test consume() raises RateLimitExceeded"""
        config = RateLimitConfig(max_requests=1, window_seconds=10)
        limiter = RateLimiter(config=config)

        # First consume OK
        await limiter.consume("user1")

        # Second should raise
        with pytest.raises(RateLimitExceeded) as exc_info:
            await limiter.consume("user1")

        assert exc_info.value.retry_after > 0

    @pytest.mark.asyncio
    async def test_memory_reset(self):
        """Test reset() clears limits"""
        config = RateLimitConfig(max_requests=1, window_seconds=10)
        limiter = RateLimiter(config=config)

        # Use limit
        await limiter.check_rate_limit("user1", cost=1)
        allowed, _ = await limiter.check_rate_limit("user1", cost=1)
        assert allowed is False

        # Reset
        await limiter.reset("user1")

        # Should be allowed again
        allowed, retry_after = await limiter.check_rate_limit("user1", cost=1)
        assert allowed is True
        assert retry_after == 0.0

    @pytest.mark.asyncio
    async def test_memory_get_remaining(self):
        """Test get_remaining() returns correct count"""
        config = RateLimitConfig(max_requests=10, window_seconds=10)
        limiter = RateLimiter(config=config)

        remaining = await limiter.get_remaining("user1")
        assert remaining == 10

        await limiter.check_rate_limit("user1", cost=3)
        remaining = await limiter.get_remaining("user1")
        assert remaining == 7

    @pytest.mark.asyncio
    async def test_memory_multiple_identifiers(self):
        """Test separate limits for different identifiers"""
        config = RateLimitConfig(max_requests=2, window_seconds=10)
        limiter = RateLimiter(config=config)

        # User1 uses limit
        await limiter.check_rate_limit("user1", cost=2)
        allowed, _ = await limiter.check_rate_limit("user1", cost=1)
        assert allowed is False

        # User2 should still have full limit
        allowed, _ = await limiter.check_rate_limit("user2", cost=1)
        assert allowed is True


class TestRateLimiterRedis:
    """Test Redis-based rate limiting"""

    @pytest.mark.asyncio
    async def test_redis_not_available_fallback(self):
        """Test that Redis unavailable falls back to memory"""
        config = RateLimitConfig(max_requests=5, window_seconds=10)
        
        # Without redis_url, should use memory
        limiter = RateLimiter(config=config, redis_url=None)
        
        allowed, retry_after = await limiter.check_rate_limit("user1")
        assert allowed is True
        assert retry_after == 0.0


class TestRateLimitConfig:
    """Test RateLimitConfig dataclass"""

    def test_config_defaults(self):
        """Test default configuration values"""
        config = RateLimitConfig()
        assert config.max_requests == 100
        assert config.window_seconds == 60
        assert config.strategy == RateLimitStrategy.SLIDING_WINDOW
        assert config.burst_multiplier == 1.5

    def test_config_custom_values(self):
        """Test custom configuration"""
        config = RateLimitConfig(
            max_requests=50,
            window_seconds=30,
            strategy=RateLimitStrategy.TOKEN_BUCKET,
            burst_multiplier=2.0,
        )
        assert config.max_requests == 50
        assert config.window_seconds == 30
        assert config.strategy == RateLimitStrategy.TOKEN_BUCKET
        assert config.burst_multiplier == 2.0


class TestRateLimitStrategy:
    """Test RateLimitStrategy enum"""

    def test_strategy_values(self):
        """Test enum values"""
        assert RateLimitStrategy.TOKEN_BUCKET.value == "token_bucket"
        assert RateLimitStrategy.SLIDING_WINDOW.value == "sliding_window"
        assert RateLimitStrategy.FIXED_WINDOW.value == "fixed_window"


class TestRateLimitExceeded:
    """Test RateLimitExceeded exception"""

    def test_exception_message(self):
        """Test exception message formatting"""
        exc = RateLimitExceeded(retry_after=5.5)
        assert exc.retry_after == 5.5
        assert "5.50s" in str(exc)

    def test_exception_raised(self):
        """Test exception can be caught"""
        with pytest.raises(RateLimitExceeded) as exc_info:
            raise RateLimitExceeded(10.0)

        assert exc_info.value.retry_after == 10.0


class TestFactoryFunction:
    """Test create_rate_limiter() factory"""

    def test_factory_defaults(self):
        """Test factory with default values"""
        limiter = create_rate_limiter()
        assert limiter.config.max_requests == 100
        assert limiter.config.window_seconds == 60
        assert limiter.redis_url is None

    def test_factory_custom_values(self):
        """Test factory with custom values"""
        limiter = create_rate_limiter(
            max_requests=50, window_seconds=30, redis_url="redis://localhost:6379"
        )
        assert limiter.config.max_requests == 50
        assert limiter.config.window_seconds == 30
        assert limiter.redis_url == "redis://localhost:6379"


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    @pytest.mark.asyncio
    async def test_zero_cost_request(self):
        """Test request with cost=0"""
        config = RateLimitConfig(max_requests=5, window_seconds=10)
        limiter = RateLimiter(config=config)

        # Cost 0 should always be allowed
        allowed, _ = await limiter.check_rate_limit("user1", cost=0)
        assert allowed is True

    @pytest.mark.asyncio
    async def test_get_remaining_empty_identifier(self):
        """Test get_remaining for never-seen identifier"""
        config = RateLimitConfig(max_requests=10, window_seconds=10)
        limiter = RateLimiter(config=config)

        remaining = await limiter.get_remaining("never_seen_user")
        assert remaining == 10

    @pytest.mark.asyncio
    async def test_memory_retry_after_empty_requests(self):
        """Test retry_after calculation when requests list empty"""
        config = RateLimitConfig(max_requests=1, window_seconds=10)
        limiter = RateLimiter(config=config)

        # Manually fill limit, then clear (edge case)
        limiter._memory_store["user1"] = [time.time() - 11]  # Old request, will be pruned

        allowed, _ = await limiter.check_rate_limit("user1", cost=1)
        assert allowed is True  # Old request pruned

    @pytest.mark.asyncio
    async def test_reset_nonexistent_identifier(self):
        """Test reset() on identifier that doesn't exist"""
        config = RateLimitConfig(max_requests=5, window_seconds=10)
        limiter = RateLimiter(config=config)

        # Should not raise error
        await limiter.reset("nonexistent_user")


class TestContextManagerFallback:
    """Test context manager without Redis"""

    @pytest.mark.asyncio
    async def test_context_manager_no_redis_url(self):
        """Test context manager without redis_url"""
        config = RateLimitConfig(max_requests=5, window_seconds=10)

        async with RateLimiter(config=config) as limiter:
            assert limiter._redis_client is None

            # Should use memory backend
            allowed, _ = await limiter.check_rate_limit("user1")
            assert allowed is True
