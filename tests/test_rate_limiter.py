"""
Tests for Rate Limiter
"""

import asyncio
import pytest
import time
from backend.shared.security_tools.rate_limiter import (
    RateLimiter,
    RateLimitConfig,
    RateLimitStrategy,
    RateLimitExceeded
)


@pytest.mark.asyncio
async def test_rate_limiter_allows_within_limit():
    """Test that requests within limit are allowed"""
    config = RateLimitConfig(max_requests=5, window_seconds=10)
    
    async with RateLimiter(config=config) as limiter:
        for i in range(5):
            allowed, _ = await limiter.check_rate_limit("user1")
            assert allowed, f"Request {i+1} should be allowed"


@pytest.mark.asyncio
async def test_rate_limiter_blocks_over_limit():
    """Test that requests over limit are blocked"""
    config = RateLimitConfig(max_requests=3, window_seconds=10)
    
    async with RateLimiter(config=config) as limiter:
        # First 3 should pass
        for i in range(3):
            await limiter.consume("user1")
        
        # 4th should fail
        with pytest.raises(RateLimitExceeded):
            await limiter.consume("user1")


@pytest.mark.asyncio
async def test_rate_limiter_reset():
    """Test rate limit reset functionality"""
    config = RateLimitConfig(max_requests=2, window_seconds=10)
    
    async with RateLimiter(config=config) as limiter:
        await limiter.consume("user1")
        await limiter.consume("user1")
        
        with pytest.raises(RateLimitExceeded):
            await limiter.consume("user1")
        
        # Reset and try again
        await limiter.reset("user1")
        
        allowed, _ = await limiter.check_rate_limit("user1")
        assert allowed


@pytest.mark.asyncio
async def test_rate_limiter_remaining():
    """Test getting remaining requests"""
    config = RateLimitConfig(max_requests=10, window_seconds=60)
    
    async with RateLimiter(config=config) as limiter:
        remaining = await limiter.get_remaining("user1")
        assert remaining == 10
        
        await limiter.consume("user1")
        remaining = await limiter.get_remaining("user1")
        assert remaining == 9


@pytest.mark.asyncio
async def test_rate_limiter_cost():
    """Test request cost multiplier"""
    config = RateLimitConfig(max_requests=10, window_seconds=60)
    
    async with RateLimiter(config=config) as limiter:
        # Expensive operation costs 5 tokens
        await limiter.consume("user1", cost=5)
        
        remaining = await limiter.get_remaining("user1")
        assert remaining == 5


@pytest.mark.asyncio
async def test_rate_limiter_multiple_users():
    """Test rate limiter isolates different users"""
    config = RateLimitConfig(max_requests=2, window_seconds=10)
    
    async with RateLimiter(config=config) as limiter:
        await limiter.consume("user1")
        await limiter.consume("user1")
        
        # user1 is blocked
        with pytest.raises(RateLimitExceeded):
            await limiter.consume("user1")
        
        # But user2 is fine
        allowed, _ = await limiter.check_rate_limit("user2")
        assert allowed
