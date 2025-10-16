"""Tests for vertice_api.client module."""

import pytest

from vertice_api.client import ServiceClient


class TestServiceClient:
    """Tests for ServiceClient."""

    @pytest.mark.asyncio
    async def test_context_manager(self) -> None:
        """Test that client works as async context manager."""
        async with ServiceClient("http://test.local") as client:
            assert client._client is not None

    @pytest.mark.asyncio
    async def test_raises_without_context(self) -> None:
        """Test that using client without context raises error."""
        client = ServiceClient("http://test.local")

        with pytest.raises(RuntimeError, match="not initialized"):
            await client.get("/test")

    @pytest.mark.asyncio
    async def test_strips_trailing_slash(self) -> None:
        """Test that trailing slash is removed from base_url."""
        client = ServiceClient("http://test.local/")
        assert client.base_url == "http://test.local"
