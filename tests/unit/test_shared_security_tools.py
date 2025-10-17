"""Tests for backend/shared/security_tools - UPDATED to new API."""

import pytest
from backend.shared.security_tools.rate_limiter import RateLimiter, RateLimitConfig
from backend.shared.security_tools.vulnerability_scanner import VulnerabilityScanner


class TestRateLimiterBasic:
    """Basic tests for RateLimiter with new API."""
    
    @pytest.fixture
    def rate_limiter(self):
        """Create rate limiter instance with new API."""
        config = RateLimitConfig(max_requests=60, window_seconds=60)
        return RateLimiter(config=config)
    
    @pytest.mark.asyncio
    async def test_init(self, rate_limiter):
        """Test initialization."""
        assert rate_limiter.config.max_requests == 60
        assert rate_limiter.config.window_seconds == 60
    
    @pytest.mark.asyncio
    async def test_check_limit_allows_under_threshold(self, rate_limiter):
        """Test that requests under limit are allowed."""
        client_id = "test_client_1"
        for _ in range(5):
            allowed, _ = await rate_limiter.check_rate_limit(client_id)
            assert allowed is True
    
    @pytest.mark.asyncio
    async def test_reset_client(self, rate_limiter):
        """Test resetting client limits."""
        client_id = "test_client_3"
        await rate_limiter.check_rate_limit(client_id)
        await rate_limiter.reset(client_id)
        allowed, _ = await rate_limiter.check_rate_limit(client_id)
        assert allowed is True
    
    @pytest.mark.asyncio
    async def test_get_remaining(self, rate_limiter):
        """Test getting remaining requests."""
        client_id = "test_client_4"
        initial = await rate_limiter.get_remaining(client_id)
        assert initial >= 0
        
        await rate_limiter.check_rate_limit(client_id)
        after_check = await rate_limiter.get_remaining(client_id)
        assert after_check <= initial


class TestVulnerabilityScannerBasic:
    """Basic tests for VulnerabilityScanner with new API."""
    
    @pytest.fixture
    def scanner(self):
        """Create scanner instance."""
        return VulnerabilityScanner()
    
    def test_scan_initialization(self, scanner):
        """Test scanner initialization."""
        assert scanner is not None
        assert hasattr(scanner, 'run_full_scan')
    
    def test_scanner_configuration(self, scanner):
        """Test scanner has required attributes."""
        assert hasattr(scanner, 'requirements_path')
        assert hasattr(scanner, 'ignore_ids')
        assert hasattr(scanner, 'fail_on_severity')
