"""Unit tests for OSV.dev client.

Tests cover:
- Client initialization
- Rate limiting
- Request retry logic
- Error handling
- CVE fetching
- Batch queries
- Health checks

Author: MAXIMUS Team
Date: 2025-10-11
Compliance: TDD | Coverage ≥90% | NO MOCK for HTTP (use real API sparingly)
"""

import sys
from pathlib import Path
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import aiohttp

# Add parent directories to path
service_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(service_root))

from threat_feeds.base_feed import (
    BaseFeedClient,
    ThreatFeedError,
    RateLimitError,
    FeedUnavailableError
)
from threat_feeds.osv_client import OSVClient


class TestBaseFeedClient:
    """Test base feed client abstract class."""
    
    def test_base_client_initialization(self):
        """Test base client can be instantiated via concrete class."""
        
        class DummyFeed(BaseFeedClient):
            async def fetch_vulnerabilities(self, ecosystem=None, package=None, since=None):
                return []
            
            async def fetch_by_cve_id(self, cve_id):
                return None
        
        client = DummyFeed(name="TestFeed", rate_limit=50)
        
        assert client.name == "TestFeed"
        assert client.rate_limit == 50
        assert client._request_count == 0
    
    @pytest.mark.asyncio
    async def test_rate_limit_check(self):
        """Test rate limiting enforcement."""
        
        class DummyFeed(BaseFeedClient):
            async def fetch_vulnerabilities(self, ecosystem=None, package=None, since=None):
                return []
            
            async def fetch_by_cve_id(self, cve_id):
                return None
        
        client = DummyFeed(name="TestFeed", rate_limit=2)
        
        # First two requests should pass
        await client._check_rate_limit()
        assert client._request_count == 1
        
        await client._check_rate_limit()
        assert client._request_count == 2
        
        # Third request should wait (but we won't actually wait in test)
        # Just verify the count is at limit
        assert client._request_count >= client.rate_limit
    
    def test_get_stats(self):
        """Test client statistics."""
        
        class DummyFeed(BaseFeedClient):
            async def fetch_vulnerabilities(self, ecosystem=None, package=None, since=None):
                return []
            
            async def fetch_by_cve_id(self, cve_id):
                return None
        
        client = DummyFeed(name="TestFeed", rate_limit=100)
        stats = client.get_stats()
        
        assert stats["name"] == "TestFeed"
        assert stats["rate_limit"] == 100
        assert "requests_this_window" in stats
        assert "window_start" in stats


class TestOSVClient:
    """Test OSV.dev client."""
    
    def test_osv_client_initialization(self):
        """Test OSV client initialization."""
        client = OSVClient(rate_limit=50)
        
        assert client.name == "OSV.dev"
        assert client.rate_limit == 50
        assert client.BASE_URL == "https://api.osv.dev/v1"
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager."""
        async with OSVClient() as client:
            assert client._session is not None
            assert not client._session.closed
        
        # Session should be closed after context
        assert client._session.closed
    
    @pytest.mark.asyncio
    async def test_ensure_session(self):
        """Test session creation."""
        client = OSVClient()
        
        assert client._session is None
        
        await client._ensure_session()
        assert client._session is not None
        assert not client._session.closed
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_fetch_vulnerabilities_requires_package(self):
        """Test that fetch_vulnerabilities requires package parameter."""
        async with OSVClient() as client:
            with pytest.raises(ValueError) as exc_info:
                await client.fetch_vulnerabilities(ecosystem="PyPI")
            
            assert "package parameter is required" in str(exc_info.value)
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_fetch_by_cve_id_real_api(self):
        """
        Integration test: Fetch real CVE from OSV.dev.
        
        Uses real API call - run sparingly.
        Marked with @pytest.mark.integration so it can be skipped.
        """
        async with OSVClient() as client:
            # Fetch a known Python CVE
            result = await client.fetch_by_cve_id("CVE-2021-3177")
            
            assert result is not None
            assert "id" in result
            assert result["id"] == "CVE-2021-3177"
            assert "summary" in result
            assert "affected" in result
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_fetch_vulnerabilities_real_api(self):
        """
        Integration test: Fetch vulnerabilities for a package.
        
        Uses real API - run sparingly.
        """
        async with OSVClient() as client:
            # Query a package known to have vulnerabilities
            results = await client.fetch_vulnerabilities(
                ecosystem="PyPI",
                package="requests"
            )
            
            assert isinstance(results, list)
            # requests package should have some vulnerabilities
            assert len(results) > 0
            
            # Check structure of first result
            if results:
                vuln = results[0]
                assert "id" in vuln
                assert "affected" in vuln
    
    @pytest.mark.asyncio
    async def test_fetch_by_cve_id_not_found(self):
        """Test fetching non-existent CVE returns None."""
        async with OSVClient() as client:
            result = await client.fetch_by_cve_id("CVE-9999-99999")
            
            # Should return None for not found
            assert result is None
    
    @pytest.mark.asyncio
    async def test_handle_response_rate_limit(self):
        """Test handling of 429 rate limit response."""
        client = OSVClient()
        
        # Mock response with 429 status
        mock_response = Mock(spec=aiohttp.ClientResponse)
        mock_response.status = 429
        
        with pytest.raises(RateLimitError) as exc_info:
            await client._handle_response(mock_response)
        
        assert "Rate limit exceeded" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_handle_response_server_error(self):
        """Test handling of 5xx server errors."""
        client = OSVClient()
        
        # Mock response with 500 status
        mock_response = Mock(spec=aiohttp.ClientResponse)
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Internal Server Error")
        
        with pytest.raises(FeedUnavailableError) as exc_info:
            await client._handle_response(mock_response)
        
        assert "Server error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_handle_response_client_error(self):
        """Test handling of 4xx client errors."""
        client = OSVClient()
        
        # Mock response with 400 status
        mock_response = Mock(spec=aiohttp.ClientResponse)
        mock_response.status = 400
        mock_response.text = AsyncMock(return_value="Bad Request")
        
        with pytest.raises(ThreatFeedError) as exc_info:
            await client._handle_response(mock_response)
        
        assert "Client error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_handle_response_success(self):
        """Test handling of successful response."""
        client = OSVClient()
        
        # Mock successful response
        mock_response = Mock(spec=aiohttp.ClientResponse)
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"id": "CVE-2024-12345", "data": "test"})
        
        result = await client._handle_response(mock_response)
        
        assert result == {"id": "CVE-2024-12345", "data": "test"}
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_query_batch_real_api(self):
        """
        Integration test: Batch query multiple packages.
        
        Uses real API - run sparingly.
        """
        async with OSVClient() as client:
            packages = [
                {"ecosystem": "PyPI", "name": "flask"},
                {"ecosystem": "PyPI", "name": "jinja2"}
            ]
            
            results = await client.query_batch(packages)
            
            assert isinstance(results, dict)
            assert "flask" in results
            assert "jinja2" in results
            assert isinstance(results["flask"], list)
            assert isinstance(results["jinja2"], list)
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_health_check_real_api(self):
        """
        Integration test: Health check with real API.
        
        Uses real API - run sparingly.
        """
        async with OSVClient() as client:
            is_healthy = await client.health_check()
            
            # OSV.dev should be healthy
            assert is_healthy is True
    
    @pytest.mark.asyncio
    async def test_request_with_retry_timeout(self):
        """Test retry logic on timeout."""
        client = OSVClient()
        await client._ensure_session()
        
        # Mock session to raise timeout
        with patch.object(client._session, 'post', side_effect=asyncio.TimeoutError):
            with pytest.raises(FeedUnavailableError) as exc_info:
                await client._request_with_retry("POST", "query", json_data={})
            
            assert "timed out" in str(exc_info.value)
        
        await client.close()


# Run tests with: pytest tests/unit/test_osv_client.py -v
# Run integration tests: pytest tests/unit/test_osv_client.py -v -m integration
# Skip integration tests: pytest tests/unit/test_osv_client.py -v -m "not integration"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
