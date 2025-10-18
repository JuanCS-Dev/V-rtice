"""
Tests for Rate Limiting Middleware.

Sprint 6 - Issue #11
Author: MAXIMUS Team
Glory to YHWH - Source of Testing Wisdom
"""

import pytest
import time
from fastapi import FastAPI
from fastapi.testclient import TestClient

from middleware.rate_limiter import (
    SlidingWindowRateLimiter,
    RateLimitMiddleware
)


class TestSlidingWindowRateLimiter:
    """Test sliding window rate limiter logic."""
    
    def test_limiter_initialization(self):
        """Limiter should initialize with correct defaults."""
        limiter = SlidingWindowRateLimiter(
            default_limit=100,
            window_seconds=60
        )
        
        assert limiter.default_limit == 100
        assert limiter.window_seconds == 60
        assert limiter.burst_limit == 200  # 2x default
    
    def test_allows_requests_under_limit(self):
        """Should allow requests under the limit."""
        limiter = SlidingWindowRateLimiter(default_limit=5, window_seconds=60)
        
        # Make 5 requests
        for i in range(5):
            allowed, info = limiter.is_allowed("client1", "/api/test")
            assert allowed is True
            assert info["remaining"] == 4 - i
    
    def test_blocks_requests_over_limit(self):
        """Should block requests exceeding the limit."""
        limiter = SlidingWindowRateLimiter(default_limit=5, window_seconds=60)
        
        # Make 5 requests (up to limit)
        for _ in range(5):
            allowed, _ = limiter.is_allowed("client1", "/api/test")
            assert allowed is True
        
        # 6th request should be blocked
        allowed, info = limiter.is_allowed("client1", "/api/test")
        assert allowed is False
        assert info["reason"] == "rate_limit_exceeded"
        assert info["retry_after"] > 0
    
    def test_burst_limit_enforcement(self):
        """Should enforce burst limits."""
        limiter = SlidingWindowRateLimiter(
            default_limit=100,
            window_seconds=60,
            burst_limit=10
        )
        
        # Make 10 burst requests (1-second window)
        for _ in range(10):
            allowed, _ = limiter.is_allowed("client1", "/api/test")
            assert allowed is True
        
        # 11th request should hit burst limit
        allowed, info = limiter.is_allowed("client1", "/api/test")
        assert allowed is False
        assert info["reason"] == "burst_limit_exceeded"
        assert info["retry_after"] == 1
    
    def test_window_sliding_cleanup(self):
        """Old timestamps should be cleaned up."""
        limiter = SlidingWindowRateLimiter(default_limit=5, window_seconds=2)
        
        # Make 5 requests
        for _ in range(5):
            limiter.is_allowed("client1", "/api/test")
        
        # Should be at limit
        allowed, _ = limiter.is_allowed("client1", "/api/test")
        assert allowed is False
        
        # Wait for window to slide
        time.sleep(2.1)
        
        # Should be allowed again
        allowed, _ = limiter.is_allowed("client1", "/api/test")
        assert allowed is True
    
    def test_per_endpoint_limits(self):
        """Should support per-endpoint rate limits."""
        limiter = SlidingWindowRateLimiter(default_limit=100, window_seconds=60)
        limiter.set_endpoint_limit("/api/expensive", limit=5, window_seconds=60)
        
        # Use different clients to avoid burst limit interference
        # Default endpoint should allow 100
        for i in range(10):
            allowed, _ = limiter.is_allowed(f"client_default_{i}", "/api/default")
            assert allowed is True
        
        # Expensive endpoint should allow only 5 per client
        for _ in range(5):
            allowed, _ = limiter.is_allowed("client_expensive", "/api/expensive")
            assert allowed is True
        
        allowed, _ = limiter.is_allowed("client_expensive", "/api/expensive")
        assert allowed is False
    
    def test_metrics_tracking(self):
        """Should track metrics correctly."""
        limiter = SlidingWindowRateLimiter(default_limit=5, window_seconds=60)
        
        # Make requests
        for _ in range(7):  # 5 allowed + 2 blocked
            limiter.is_allowed("client1", "/api/test")
        
        metrics = limiter.get_metrics()
        assert metrics["total_hits"] == 5
        assert metrics["total_blocks"] == 2
        assert metrics["block_rate"] == 2 / 5
        assert metrics["active_clients"] == 1


class TestRateLimitMiddleware:
    """Test FastAPI middleware integration."""
    
    def create_app(self, limiter: SlidingWindowRateLimiter):
        """Helper to create test app with rate limiting."""
        app = FastAPI()
        
        app.add_middleware(
            RateLimitMiddleware,
            limiter=limiter,
            exclude_paths=["/health"]
        )
        
        @app.get("/")
        async def root():
            return {"message": "ok"}
        
        @app.get("/health")
        async def health():
            return {"status": "healthy"}
        
        @app.get("/api/test")
        async def test_endpoint():
            return {"result": "success"}
        
        return app
    
    def test_middleware_adds_headers(self):
        """Middleware should add rate limit headers."""
        limiter = SlidingWindowRateLimiter(default_limit=10, window_seconds=60)
        app = self.create_app(limiter)
        client = TestClient(app)
        
        response = client.get("/")
        
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
        assert response.headers["X-RateLimit-Limit"] == "10"
    
    def test_middleware_blocks_excess_requests(self):
        """Middleware should return 429 when limit exceeded."""
        limiter = SlidingWindowRateLimiter(default_limit=3, window_seconds=60)
        app = self.create_app(limiter)
        client = TestClient(app)
        
        # Make 3 allowed requests
        for _ in range(3):
            response = client.get("/")
            assert response.status_code == 200
        
        # 4th request should be blocked
        response = client.get("/")
        assert response.status_code == 429
        assert "retry_after" in response.json()
    
    def test_middleware_excludes_paths(self):
        """Middleware should not limit excluded paths."""
        limiter = SlidingWindowRateLimiter(default_limit=3, window_seconds=60)
        app = self.create_app(limiter)
        client = TestClient(app)
        
        # Make 10 requests to excluded path
        for _ in range(10):
            response = client.get("/health")
            assert response.status_code == 200
        
        # Should NOT have rate limit headers
        assert "X-RateLimit-Limit" not in response.headers
    
    def test_middleware_isolates_clients(self):
        """Different clients should have independent limits."""
        limiter = SlidingWindowRateLimiter(default_limit=3, window_seconds=60)
        app = self.create_app(limiter)
        
        # TestClient uses same client ID "testclient" by default
        # We need to test the logic directly since TestClient doesn't simulate multiple IPs
        
        # Simulate client 1 using up limit
        for _ in range(3):
            allowed, _ = limiter.is_allowed("client1", "/")
            assert allowed is True
        
        # Client 1 should be blocked
        allowed, _ = limiter.is_allowed("client1", "/")
        assert allowed is False
        
        # Client 2 should still be allowed (independent limit)
        allowed, _ = limiter.is_allowed("client2", "/")
        assert allowed is True


@pytest.mark.integration
class TestRateLimitingIntegration:
    """Integration tests with real API."""
    
    def test_real_world_scenario(self):
        """Test realistic usage pattern."""
        limiter = SlidingWindowRateLimiter(
            default_limit=100,
            window_seconds=60,
            burst_limit=20
        )
        
        app = FastAPI()
        app.add_middleware(RateLimitMiddleware, limiter=limiter)
        
        @app.get("/api/v1/data")
        async def get_data():
            return {"data": "sample"}
        
        client = TestClient(app)
        
        # Simulate normal traffic (10 req/s for 3 seconds = 30 requests)
        for _ in range(30):
            response = client.get("/api/v1/data")
            assert response.status_code == 200
            time.sleep(0.1)  # 100ms between requests
        
        # All should succeed (under both limits)
        assert limiter.get_metrics()["total_blocks"] == 0
    
    def test_burst_attack_scenario(self):
        """Test protection against burst attacks."""
        limiter = SlidingWindowRateLimiter(
            default_limit=100,
            window_seconds=60,
            burst_limit=10
        )
        
        app = FastAPI()
        app.add_middleware(RateLimitMiddleware, limiter=limiter)
        
        @app.get("/api/v1/data")
        async def get_data():
            return {"data": "sample"}
        
        client = TestClient(app)
        
        # Simulate burst attack (20 instant requests)
        blocked_count = 0
        for _ in range(20):
            response = client.get("/api/v1/data")
            if response.status_code == 429:
                blocked_count += 1
        
        # Should block at least 10 requests (after burst limit)
        assert blocked_count >= 10
        assert limiter.get_metrics()["total_blocks"] >= 10
