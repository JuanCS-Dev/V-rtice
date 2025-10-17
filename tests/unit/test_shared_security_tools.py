"""Tests for backend/shared/security_tools - 100% coverage target."""

import pytest
from unittest.mock import Mock, MagicMock
from backend.shared.security_tools.rate_limiter import RateLimiter
from backend.shared.security_tools.vulnerability_scanner import VulnerabilityScanner


class TestRateLimiter:
    """Tests for RateLimiter."""
    
    @pytest.fixture
    def rate_limiter(self):
        """Create rate limiter instance."""
        return RateLimiter(requests_per_minute=60, burst_size=10)
    
    def test_init(self, rate_limiter):
        """Test initialization."""
        assert rate_limiter.requests_per_minute == 60
        assert rate_limiter.burst_size == 10
    
    def test_check_limit_allows_under_threshold(self, rate_limiter):
        """Test that requests under limit are allowed."""
        client_id = "test_client_1"
        for _ in range(5):
            assert rate_limiter.check(client_id) is True
    
    def test_check_limit_blocks_over_threshold(self, rate_limiter):
        """Test that excessive requests are blocked."""
        client_id = "test_client_2"
        # Fill burst capacity
        for _ in range(10):
            rate_limiter.check(client_id)
        
        # Next request should be rate-limited
        result = rate_limiter.check(client_id)
        assert result is False or rate_limiter.is_limited(client_id)
    
    def test_reset_client(self, rate_limiter):
        """Test resetting client limits."""
        client_id = "test_client_3"
        rate_limiter.check(client_id)
        rate_limiter.reset(client_id)
        assert rate_limiter.check(client_id) is True
    
    def test_get_remaining(self, rate_limiter):
        """Test getting remaining requests."""
        client_id = "test_client_4"
        initial = rate_limiter.get_remaining(client_id)
        assert initial >= 0
        
        rate_limiter.check(client_id)
        after_check = rate_limiter.get_remaining(client_id)
        assert after_check <= initial


class TestVulnerabilityScanner:
    """Tests for VulnerabilityScanner."""
    
    @pytest.fixture
    def scanner(self):
        """Create scanner instance."""
        return VulnerabilityScanner()
    
    @pytest.mark.asyncio
    async def test_scan_initialization(self, scanner):
        """Test scanner initialization."""
        assert scanner is not None
        assert hasattr(scanner, 'scan')
    
    @pytest.mark.asyncio
    async def test_scan_basic(self, scanner):
        """Test basic scanning functionality."""
        result = await scanner.scan("127.0.0.1")
        assert isinstance(result, (dict, list))
    
    @pytest.mark.asyncio
    async def test_scan_with_options(self, scanner):
        """Test scanning with options."""
        result = await scanner.scan(
            "127.0.0.1",
            ports=[80, 443],
            deep_scan=False
        )
        assert isinstance(result, (dict, list))
    
    def test_scanner_configuration(self, scanner):
        """Test scanner configuration."""
        assert hasattr(scanner, 'config') or hasattr(scanner, 'settings')


class TestSecurityIntegration:
    """Integration tests for security tools."""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_with_scanner(self):
        """Test rate limiter protecting scanner."""
        limiter = RateLimiter(requests_per_minute=5, burst_size=2)
        scanner = VulnerabilityScanner()
        
        client = "scan_client"
        successful_scans = 0
        
        for _ in range(5):
            if limiter.check(client):
                result = await scanner.scan("127.0.0.1")
                successful_scans += 1
        
        # Should have completed some but hit rate limit
        assert successful_scans <= 2  # Burst size limit
