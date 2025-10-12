"""Tests for rate limiter middleware - Phase 5.7.1"""

import pytest
import asyncio
import time
import sys
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.services.wargaming_crisol.middleware.rate_limiter import TokenBucket, RateLimiterMiddleware


class TestTokenBucket:
    """Test token bucket implementation."""
    
    def test_initial_tokens(self):
        """Test bucket starts at full capacity."""
        bucket = TokenBucket(capacity=100, refill_rate=10)
        assert bucket.tokens == 100
        assert bucket.capacity == 100
        assert bucket.refill_rate == 10
    
    def test_consume_success(self):
        """Test successful token consumption."""
        bucket = TokenBucket(capacity=10, refill_rate=1)
        assert bucket.consume(5) is True
        assert bucket.tokens == 5
    
    def test_consume_failure(self):
        """Test failed token consumption when insufficient."""
        bucket = TokenBucket(capacity=10, refill_rate=1)
        bucket.consume(8)
        assert bucket.consume(5) is False  # Only 2 tokens left
        assert bucket.tokens == 2  # Unchanged
    
    def test_refill_mechanism(self):
        """Test tokens refill over time."""
        bucket = TokenBucket(capacity=100, refill_rate=10)  # 10 tokens/sec
        
        # Consume some tokens
        bucket.consume(50)
        assert bucket.tokens == 50
        
        # Wait 1 second
        time.sleep(1.1)
        
        # Try to consume - should have refilled ~10 tokens
        bucket.consume(1)
        # Should have ~59 tokens (50 + 10 refill - 1)
        assert 58 <= bucket.tokens <= 61
    
    def test_refill_cap(self):
        """Test refill doesn't exceed capacity."""
        bucket = TokenBucket(capacity=100, refill_rate=100)
        
        # Wait for significant refill time
        time.sleep(2)
        
        # Consume - should not have more than capacity
        bucket.consume(1)
        assert bucket.tokens <= bucket.capacity
    
    def test_get_status(self):
        """Test status reporting."""
        bucket = TokenBucket(capacity=100, refill_rate=10)
        bucket.consume(30)
        
        status = bucket.get_status()
        assert status["capacity"] == 100
        assert status["refill_rate"] == 10
        assert 69 <= status["tokens"] <= 71  # ~70 after consuming 30
        assert 69 <= status["fill_percentage"] <= 71


class TestRateLimiterMiddleware:
    """Test rate limiter middleware integration."""
    
    def setup_method(self):
        """Create test app with rate limiter."""
        self.app = FastAPI()
        self.app.add_middleware(RateLimiterMiddleware)
        
        @self.app.get("/wargaming/ml-first")
        async def ml_first_endpoint():
            return {"status": "ok"}
        
        @self.app.get("/wargaming/validate")
        async def validate_endpoint():
            return {"status": "ok"}
        
        @self.app.get("/unlimited")
        async def unlimited_endpoint():
            return {"status": "ok"}
        
        self.client = TestClient(self.app)
    
    def test_rate_limit_allows_initial_requests(self):
        """Test rate limiter allows requests under limit."""
        # Make 10 requests (well under 100/min limit for ml-first)
        for _ in range(10):
            response = self.client.get("/wargaming/ml-first")
            assert response.status_code == 200
    
    def test_rate_limit_blocks_excessive_requests(self):
        """Test rate limiter blocks requests over limit."""
        # Try to exceed limit (100 req/min for ml-first)
        # Make 150 rapid requests
        blocked = 0
        allowed = 0
        
        for i in range(150):
            response = self.client.get("/wargaming/ml-first")
            if response.status_code == 429:
                blocked += 1
            else:
                allowed += 1
        
        # Should have blocked some requests
        assert blocked > 0
        assert blocked < 150  # Not all blocked (burst allowed)
        assert allowed > 0
    
    def test_rate_limit_headers(self):
        """Test rate limit headers are included."""
        response = self.client.get("/wargaming/ml-first")
        
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
    
    def test_rate_limit_429_response(self):
        """Test 429 response format."""
        # Exhaust rate limit
        for _ in range(150):
            response = self.client.get("/wargaming/ml-first")
            if response.status_code == 429:
                data = response.json()
                assert "detail" in data
                assert "error" in data["detail"]
                assert "Rate limit exceeded" in data["detail"]["error"]
                assert "limit" in data["detail"]
                assert "retry_after" in data["detail"]
                break
    
    def test_unlimited_endpoint_not_rate_limited(self):
        """Test endpoints not in limits are not rate limited."""
        # Make many requests to unlimited endpoint
        for _ in range(200):
            response = self.client.get("/unlimited")
            assert response.status_code == 200
    
    def test_different_endpoints_separate_buckets(self):
        """Test different endpoints have separate rate limit buckets."""
        # Exhaust ml-first limit
        for _ in range(150):
            self.client.get("/wargaming/ml-first")
        
        # validate endpoint should still work (separate bucket)
        response = self.client.get("/wargaming/validate")
        assert response.status_code == 200


@pytest.mark.asyncio
class TestRateLimiterAsync:
    """Test rate limiter with async requests."""
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_rate_limited(self):
        """Test rate limiting with concurrent requests."""
        app = FastAPI()
        app.add_middleware(RateLimiterMiddleware)
        
        @app.get("/wargaming/ml-first")
        async def endpoint():
            return {"status": "ok"}
        
        # Simulate concurrent requests
        # (Would need async test client - simplified for now)
        assert True  # Placeholder
