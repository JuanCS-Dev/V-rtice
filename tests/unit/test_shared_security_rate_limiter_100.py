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

    @pytest.mark.asyncio
    async def test_redis_context_manager_with_url(self):
        """Test context manager initializes Redis client"""
        if not REDIS_AVAILABLE:
            pytest.skip("Redis library not available")
        
        config = RateLimitConfig(max_requests=5, window_seconds=10)
        
        # Mock Redis connection
        with patch("backend.shared.security_tools.rate_limiter.aioredis") as mock_aioredis:
            mock_redis = AsyncMock()
            # from_url is async, needs to be awaitable
            mock_aioredis.from_url = AsyncMock(return_value=mock_redis)
            
            async with RateLimiter(config=config, redis_url="redis://localhost:6379") as limiter:
                assert limiter._redis_client is not None
                mock_aioredis.from_url.assert_called_once()
            
            # Should close on exit
            mock_redis.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_redis_check_rate_limit_allowed(self):
        """Test Redis-based check_rate_limit allows request"""
        if not REDIS_AVAILABLE:
            pytest.skip("Redis library not available")
        
        config = RateLimitConfig(max_requests=10, window_seconds=60)
        
        with patch("backend.shared.security_tools.rate_limiter.aioredis") as mock_aioredis:
            # Create proper pipeline mock
            class MockPipeline:
                def zremrangebyscore(self, *args): return self
                def zcard(self, *args): return self
                def zadd(self, *args, **kwargs): return self
                def expire(self, *args): return self
                async def execute(self): return [None, 5, None, None]
            
            mock_redis = MagicMock()  # Use MagicMock for sync methods
            mock_redis.pipeline = MagicMock(return_value=MockPipeline())  # Sync call, returns pipeline
            mock_redis.close = AsyncMock()  # Close is async
            
            mock_aioredis.from_url = AsyncMock(return_value=mock_redis)
            
            async with RateLimiter(config=config, redis_url="redis://localhost:6379") as limiter:
                allowed, retry_after = await limiter.check_rate_limit("user1", cost=1)
                
                assert allowed is True
                assert retry_after == 0.0

    @pytest.mark.asyncio
    async def test_redis_check_rate_limit_exceeded(self):
        """Test Redis-based check_rate_limit blocks when exceeded"""
        if not REDIS_AVAILABLE:
            pytest.skip("Redis library not available")
        
        config = RateLimitConfig(max_requests=10, window_seconds=60)
        
        with patch("backend.shared.security_tools.rate_limiter.aioredis") as mock_aioredis:
            # Create proper pipeline mock - 10 requests already exist
            class MockPipeline:
                def zremrangebyscore(self, *args): return self
                def zcard(self, *args): return self
                def zadd(self, *args, **kwargs): return self
                def expire(self, *args): return self
                async def execute(self): return [None, 10, None, None]
            
            mock_redis = MagicMock()
            mock_redis.pipeline = MagicMock(return_value=MockPipeline())
            mock_redis.close = AsyncMock()
            
            # Mock zrange for retry_after calculation
            current_time = time.time()
            oldest_time = current_time - 30  # 30s ago
            mock_redis.zrange = AsyncMock(return_value=[("req1", oldest_time)])
            
            mock_aioredis.from_url = AsyncMock(return_value=mock_redis)
            
            async with RateLimiter(config=config, redis_url="redis://localhost:6379") as limiter:
                allowed, retry_after = await limiter.check_rate_limit("user1", cost=1)
                
                assert allowed is False
                assert retry_after > 0
                assert retry_after <= 60  # Should be within window

    @pytest.mark.asyncio
    async def test_redis_check_rate_limit_exceeded_no_oldest(self):
        """Test Redis retry_after when no oldest timestamp available"""
        if not REDIS_AVAILABLE:
            pytest.skip("Redis library not available")
        
        config = RateLimitConfig(max_requests=10, window_seconds=60)
        
        with patch("backend.shared.security_tools.rate_limiter.aioredis") as mock_aioredis:
            # Create proper pipeline mock - over limit
            class MockPipeline:
                def zremrangebyscore(self, *args): return self
                def zcard(self, *args): return self
                def zadd(self, *args, **kwargs): return self
                def expire(self, *args): return self
                async def execute(self): return [None, 15, None, None]
            
            mock_redis = MagicMock()
            mock_redis.pipeline = MagicMock(return_value=MockPipeline())
            mock_redis.close = AsyncMock()
            
            # zrange returns empty list
            mock_redis.zrange = AsyncMock(return_value=[])
            
            mock_aioredis.from_url = AsyncMock(return_value=mock_redis)
            
            async with RateLimiter(config=config, redis_url="redis://localhost:6379") as limiter:
                allowed, retry_after = await limiter.check_rate_limit("user1", cost=1)
                
                assert allowed is False
                assert retry_after == 60  # Full window_seconds

    @pytest.mark.asyncio
    async def test_redis_reset(self):
        """Test Redis-based reset()"""
        if not REDIS_AVAILABLE:
            pytest.skip("Redis library not available")
        
        config = RateLimitConfig(max_requests=10, window_seconds=60)
        
        with patch("backend.shared.security_tools.rate_limiter.aioredis") as mock_aioredis:
            mock_redis = MagicMock()
            mock_redis.delete = AsyncMock()
            mock_redis.close = AsyncMock()
            mock_aioredis.from_url = AsyncMock(return_value=mock_redis)
            
            async with RateLimiter(config=config, redis_url="redis://localhost:6379") as limiter:
                await limiter.reset("user1")
                
                mock_redis.delete.assert_called_once()
                # Verify correct key format
                call_args = mock_redis.delete.call_args[0][0]
                assert call_args == "ratelimit:user1"

    @pytest.mark.asyncio
    async def test_redis_get_remaining(self):
        """Test Redis-based get_remaining()"""
        if not REDIS_AVAILABLE:
            pytest.skip("Redis library not available")
        
        config = RateLimitConfig(max_requests=10, window_seconds=60)
        
        with patch("backend.shared.security_tools.rate_limiter.aioredis") as mock_aioredis:
            mock_redis = MagicMock()
            mock_redis.zcount = AsyncMock(return_value=3)  # 3 requests in window
            mock_redis.close = AsyncMock()
            mock_aioredis.from_url = AsyncMock(return_value=mock_redis)
            
            async with RateLimiter(config=config, redis_url="redis://localhost:6379") as limiter:
                remaining = await limiter.get_remaining("user1")
                
                assert remaining == 7  # 10 - 3
                mock_redis.zcount.assert_called_once()

    @pytest.mark.asyncio
    async def test_redis_get_remaining_over_limit(self):
        """Test Redis get_remaining when over limit returns 0"""
        if not REDIS_AVAILABLE:
            pytest.skip("Redis library not available")
        
        config = RateLimitConfig(max_requests=10, window_seconds=60)
        
        with patch("backend.shared.security_tools.rate_limiter.aioredis") as mock_aioredis:
            mock_redis = MagicMock()
            mock_redis.zcount = AsyncMock(return_value=15)  # Over limit
            mock_redis.close = AsyncMock()
            mock_aioredis.from_url = AsyncMock(return_value=mock_redis)
            
            async with RateLimiter(config=config, redis_url="redis://localhost:6379") as limiter:
                remaining = await limiter.get_remaining("user1")
                
                assert remaining == 0  # max(0, 10 - 15)


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


class TestRedisImportFallback:
    """Test behavior when Redis not available"""

    def test_redis_available_flag(self):
        """Test REDIS_AVAILABLE flag"""
        # This tests the import try/except block
        assert isinstance(REDIS_AVAILABLE, bool)

    @pytest.mark.asyncio
    async def test_context_manager_redis_unavailable_mock(self):
        """Test context manager when REDIS_AVAILABLE=False"""
        config = RateLimitConfig(max_requests=5, window_seconds=10)
        
        # Even with redis_url, if Redis not available, should fallback
        with patch("backend.shared.security_tools.rate_limiter.REDIS_AVAILABLE", False):
            async with RateLimiter(config=config, redis_url="redis://localhost") as limiter:
                assert limiter._redis_client is None
                
                # Should use memory
                allowed, _ = await limiter.check_rate_limit("user1")
                assert allowed is True

    def test_redis_import_error_branch(self):
        """Test ImportError branch when redis.asyncio cannot be imported"""
        import sys
        import importlib
        
        # Temporarily hide redis module to trigger ImportError
        original_modules = sys.modules.copy()
        redis_modules = {k: v for k, v in sys.modules.items() if k.startswith('redis')}
        
        # Remove redis from sys.modules
        for module in redis_modules:
            if module in sys.modules:
                del sys.modules[module]
        
        # Mock import to raise ImportError
        import builtins
        original_import = builtins.__import__
        
        def mock_import(name, *args, **kwargs):
            if 'redis.asyncio' in name or name == 'redis.asyncio':
                raise ImportError("Mock: redis.asyncio not installed")
            return original_import(name, *args, **kwargs)
        
        builtins.__import__ = mock_import
        
        try:
            # Force reload module to re-execute try/except
            import backend.shared.security_tools.rate_limiter as rl_module
            importlib.reload(rl_module)
            
            # After ImportError, REDIS_AVAILABLE should be False
            assert rl_module.REDIS_AVAILABLE is False
        finally:
            # Restore original state
            builtins.__import__ = original_import
            sys.modules.update(original_modules)
            importlib.reload(rl_module)

    @pytest.mark.asyncio
    async def test_check_redis_fallback_to_memory(self):
        """Test _check_redis fallback when _redis_client becomes None"""
        if not REDIS_AVAILABLE:
            pytest.skip("Redis library not available")
        
        config = RateLimitConfig(max_requests=10, window_seconds=60)
        
        with patch("backend.shared.security_tools.rate_limiter.aioredis") as mock_aioredis:
            mock_redis = MagicMock()
            mock_redis.close = AsyncMock()
            mock_aioredis.from_url = AsyncMock(return_value=mock_redis)
            
            async with RateLimiter(config=config, redis_url="redis://localhost:6379") as limiter:
                # Manually set _redis_client to None to trigger line 115 fallback
                limiter._redis_client = None
                
                # Should fallback to memory
                allowed, retry_after = await limiter._check_redis("user1", 1)
                assert allowed is True
                assert retry_after == 0.0
