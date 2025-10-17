"""Tests for vertice_api.client module."""

import pytest
import httpx
from unittest.mock import AsyncMock, patch, Mock
from vertice_api.client import ServiceClient
from vertice_core import ServiceUnavailableError


class TestServiceClient:
    """Tests for ServiceClient."""

    @pytest.mark.asyncio()
    async def test_context_manager(self) -> None:
        """Test that client works as async context manager."""
        async with ServiceClient("http://test.local") as client:
            assert client._client is not None

    @pytest.mark.asyncio()
    async def test_raises_without_context(self) -> None:
        """Test that using client without context raises error."""
        client = ServiceClient("http://test.local")

        with pytest.raises(RuntimeError, match="not initialized"):
            await client.get("/test")

    @pytest.mark.asyncio()
    async def test_strips_trailing_slash(self) -> None:
        """Test that trailing slash is removed from base_url."""
        client = ServiceClient("http://test.local/")
        assert client.base_url == "http://test.local"

    @pytest.mark.asyncio()
    async def test_get_success(self) -> None:
        """Test successful GET request."""
        mock_response = Mock()
        mock_response.json.return_value = {"status": "ok"}
        mock_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            async with ServiceClient("http://test.local") as client:
                result = await client.get("/health")
                assert result == {"status": "ok"}

    @pytest.mark.asyncio()
    async def test_get_service_unavailable_500(self) -> None:
        """Test GET raises ServiceUnavailableError on 500+ status."""
        mock_response = Mock()
        mock_response.status_code = 500

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.HTTPStatusError(
                "Server Error", request=Mock(), response=mock_response
            )
            mock_client_class.return_value = mock_client

            async with ServiceClient("http://test.local") as client:
                with pytest.raises(ServiceUnavailableError):
                    await client.get("/test")

    @pytest.mark.asyncio()
    async def test_get_request_error(self) -> None:
        """Test GET raises ServiceUnavailableError on network errors."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.RequestError("Connection failed")
            mock_client_class.return_value = mock_client

            async with ServiceClient("http://test.local") as client:
                with pytest.raises(ServiceUnavailableError):
                    await client.get("/test")

    @pytest.mark.asyncio()
    async def test_post_success(self) -> None:
        """Test successful POST request."""
        mock_response = Mock()
        mock_response.json.return_value = {"created": True}
        mock_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            async with ServiceClient("http://test.local") as client:
                result = await client.post("/create", json={"name": "test"})
                assert result == {"created": True}

    @pytest.mark.asyncio()
    async def test_exit_without_client_initialized(self) -> None:
        """Test __aexit__ handles case where client is None."""
        client = ServiceClient("http://test.local")
        # Exit without ever entering - _client is None
        await client.__aexit__()  # Should not raise
