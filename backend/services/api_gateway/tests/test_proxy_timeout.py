"""
API Gateway Proxy Timeout Tests
================================

Test suite for _proxy_request timeout and error handling.
Target: 100% coverage for timeout logic
Boris Cherny Pattern: Comprehensive testing for production reliability

Governed by: Constituição Vértice v2.7 - ADR-004 (Testing Strategy)
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from fastapi import HTTPException, Request
import httpx

# Import functions to test
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import (
    _proxy_request,
    get_timeout_for_endpoint,
    DEFAULT_BACKEND_TIMEOUT,
    ENDPOINT_TIMEOUTS,
)


# =============================================================================
# TIMEOUT CONFIGURATION TESTS
# =============================================================================


class TestTimeoutConfiguration:
    """Test timeout configuration logic."""

    def test_default_timeout_values(self):
        """Verify default timeout configuration."""
        assert DEFAULT_BACKEND_TIMEOUT.timeout == 60.0
        assert DEFAULT_BACKEND_TIMEOUT.connect == 5.0
        assert DEFAULT_BACKEND_TIMEOUT.read == 60.0
        assert DEFAULT_BACKEND_TIMEOUT.write == 10.0
        assert DEFAULT_BACKEND_TIMEOUT.pool == 5.0

    def test_endpoint_specific_timeouts_exist(self):
        """Verify endpoint-specific timeouts are configured."""
        assert "/api/osint" in ENDPOINT_TIMEOUTS
        assert "/api/malware/analyze" in ENDPOINT_TIMEOUTS
        assert "/api/scan" in ENDPOINT_TIMEOUTS
        assert "/api/offensive/scan" in ENDPOINT_TIMEOUTS
        assert "/api/defensive/analyze" in ENDPOINT_TIMEOUTS

    def test_osint_timeout_is_longer(self):
        """OSINT operations get 120s timeout."""
        timeout = get_timeout_for_endpoint("/api/osint/search")
        assert timeout.timeout == 120.0

    def test_malware_timeout_is_longest(self):
        """Malware analysis gets 180s timeout."""
        timeout = get_timeout_for_endpoint("/api/malware/analyze/file")
        assert timeout.timeout == 180.0

    def test_scan_timeout_is_medium(self):
        """Scan operations get 90s timeout."""
        timeout = get_timeout_for_endpoint("/api/scan/network")
        assert timeout.timeout == 90.0

    def test_default_timeout_for_unknown_endpoint(self):
        """Unknown endpoints use default 60s timeout."""
        timeout = get_timeout_for_endpoint("/api/unknown/endpoint")
        assert timeout.timeout == 60.0

    def test_timeout_pattern_matching(self):
        """Timeout pattern matching works with path prefixes."""
        # Should match /api/osint pattern
        assert get_timeout_for_endpoint("/api/osint/search").timeout == 120.0
        assert get_timeout_for_endpoint("/api/osint/domains/check").timeout == 120.0

        # Should match /api/malware/analyze pattern
        assert (
            get_timeout_for_endpoint("/api/malware/analyze/suspicious.exe").timeout
            == 180.0
        )


# =============================================================================
# PROXY REQUEST TIMEOUT TESTS
# =============================================================================


class TestProxyRequestTimeout:
    """Test _proxy_request timeout behavior."""

    @pytest.mark.asyncio
    async def test_timeout_exception_returns_504(self):
        """Timeout errors return 504 Gateway Timeout."""
        mock_request = Mock(spec=Request)
        mock_request.method = "GET"
        mock_request.headers = {}
        mock_request.query_params = {}

        with patch("httpx.AsyncClient") as mock_client:
            # Mock AsyncClient context manager
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance

            # Simulate timeout
            mock_instance.get.side_effect = httpx.TimeoutException("Request timeout")

            with pytest.raises(HTTPException) as exc_info:
                await _proxy_request(
                    "http://backend:8001", "api/test", mock_request
                )

            assert exc_info.value.status_code == 504
            assert "timeout" in exc_info.value.detail.lower()
            assert "60s" in exc_info.value.detail  # Default timeout

    @pytest.mark.asyncio
    async def test_connect_error_returns_503(self):
        """Connection errors return 503 Service Unavailable."""
        mock_request = Mock(spec=Request)
        mock_request.method = "GET"
        mock_request.headers = {}
        mock_request.query_params = {}

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance

            # Simulate connection error
            mock_instance.get.side_effect = httpx.ConnectError(
                "Connection refused"
            )

            with pytest.raises(HTTPException) as exc_info:
                await _proxy_request(
                    "http://backend:8001", "api/test", mock_request
                )

            assert exc_info.value.status_code == 503
            assert "cannot connect" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_request_error_returns_500(self):
        """Generic request errors return 500."""
        mock_request = Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.headers = {}
        mock_request.body = AsyncMock(return_value=b'{"data": "test"}')

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance

            # Simulate generic request error
            mock_instance.post.side_effect = httpx.RequestError(
                "Network unreachable"
            )

            with pytest.raises(HTTPException) as exc_info:
                await _proxy_request(
                    "http://backend:8001", "api/create", mock_request
                )

            assert exc_info.value.status_code == 500
            assert "communication error" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_http_status_error_proxied(self):
        """Backend HTTP errors are proxied to client."""
        mock_request = Mock(spec=Request)
        mock_request.method = "GET"
        mock_request.headers = {}
        mock_request.query_params = {}

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance

            # Create mock response for 404
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.text = "Resource not found"

            # Simulate HTTP status error
            mock_instance.get.side_effect = httpx.HTTPStatusError(
                "404 error",
                request=Mock(),
                response=mock_response,
            )

            with pytest.raises(HTTPException) as exc_info:
                await _proxy_request(
                    "http://backend:8001", "api/missing", mock_request
                )

            assert exc_info.value.status_code == 404
            assert "not found" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_successful_request(self):
        """Successful requests return JSONResponse."""
        mock_request = Mock(spec=Request)
        mock_request.method = "GET"
        mock_request.headers = {}
        mock_request.query_params = {}

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance

            # Mock successful response
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json = Mock(return_value={"data": "success"})
            mock_response.raise_for_status = Mock()

            mock_instance.get.return_value = mock_response

            result = await _proxy_request(
                "http://backend:8001", "api/data", mock_request
            )

            assert result.status_code == 200
            assert result.body is not None

    @pytest.mark.asyncio
    async def test_custom_timeout_for_osint(self):
        """OSINT endpoints use 120s timeout."""
        mock_request = Mock(spec=Request)
        mock_request.method = "GET"
        mock_request.headers = {}
        mock_request.query_params = {}

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance

            # Simulate timeout on OSINT endpoint
            mock_instance.get.side_effect = httpx.TimeoutException("Timeout")

            with pytest.raises(HTTPException) as exc_info:
                await _proxy_request(
                    "http://osint:8003", "api/osint/search", mock_request
                )

            assert exc_info.value.status_code == 504
            assert "120s" in exc_info.value.detail  # OSINT timeout

    @pytest.mark.asyncio
    async def test_post_request_with_body(self):
        """POST requests include body content."""
        mock_request = Mock(spec=Request)
        mock_request.method = "POST"
        mock_request.headers = {"content-type": "application/json"}
        mock_request.body = AsyncMock(return_value=b'{"name": "test"}')

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance

            # Mock successful response
            mock_response = AsyncMock()
            mock_response.status_code = 201
            mock_response.json = Mock(return_value={"id": 123})
            mock_response.raise_for_status = Mock()

            mock_instance.post.return_value = mock_response

            result = await _proxy_request(
                "http://backend:8001", "api/create", mock_request
            )

            # Verify body was passed
            mock_instance.post.assert_called_once()
            call_kwargs = mock_instance.post.call_args.kwargs
            assert call_kwargs["content"] == b'{"name": "test"}'

    @pytest.mark.asyncio
    async def test_unsupported_method_returns_405(self):
        """Unsupported HTTP methods return 405."""
        mock_request = Mock(spec=Request)
        mock_request.method = "PATCH"  # Not supported
        mock_request.headers = {}

        with pytest.raises(HTTPException) as exc_info:
            await _proxy_request("http://backend:8001", "api/test", mock_request)

        assert exc_info.value.status_code == 405
        assert "not allowed" in exc_info.value.detail.lower()


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestProxyIntegration:
    """Integration tests for complete proxy flows."""

    @pytest.mark.asyncio
    async def test_complete_get_flow(self):
        """Test complete GET request flow with timeout config."""
        mock_request = Mock(spec=Request)
        mock_request.method = "GET"
        mock_request.headers = {
            "authorization": "Bearer token123",
            "user-agent": "TestClient",
        }
        mock_request.query_params = {"filter": "active"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance

            # Mock response
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json = Mock(return_value={"items": [1, 2, 3]})
            mock_response.raise_for_status = Mock()

            mock_instance.get.return_value = mock_response

            result = await _proxy_request(
                "http://backend:8001", "api/items", mock_request
            )

            # Verify headers were forwarded (excluding host/content-length)
            call_kwargs = mock_instance.get.call_args.kwargs
            assert "authorization" in call_kwargs["headers"]
            assert "user-agent" in call_kwargs["headers"]
            assert "host" not in call_kwargs["headers"]
            assert "content-length" not in call_kwargs["headers"]

    @pytest.mark.asyncio
    async def test_timeout_error_logging(self):
        """Verify timeout errors are logged with structured data."""
        mock_request = Mock(spec=Request)
        mock_request.method = "GET"
        mock_request.headers = {}
        mock_request.query_params = {}

        with patch("httpx.AsyncClient") as mock_client, patch(
            "main.logger"
        ) as mock_logger:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance

            mock_instance.get.side_effect = httpx.TimeoutException("Timeout")

            with pytest.raises(HTTPException):
                await _proxy_request(
                    "http://backend:8001", "api/slow", mock_request
                )

            # Verify structured logging
            mock_logger.error.assert_called()
            call_args = mock_logger.error.call_args
            assert "timeout" in call_args[0][0].lower()
            assert "extra" in call_args[1]
            assert "timeout_config" in call_args[1]["extra"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
