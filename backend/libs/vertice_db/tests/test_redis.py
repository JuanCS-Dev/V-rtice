"""Tests for vertice_db.redis_client module."""

import pytest
from fakeredis import FakeAsyncRedis
from vertice_db import RedisClient, create_redis_client


@pytest.fixture()
async def redis_client():
    """Create fake Redis client."""
    client = create_redis_client("redis://localhost:6379")
    client._client = FakeAsyncRedis(decode_responses=True)
    return client


@pytest.mark.asyncio()
async def test_create_redis_client():
    """Test create_redis_client factory."""
    client = create_redis_client("redis://localhost:6379")
    assert isinstance(client, RedisClient)


@pytest.mark.asyncio()
async def test_redis_set_and_get(redis_client):
    """Test set and get operations."""
    await redis_client.set("test_key", {"data": "value"})
    result = await redis_client.get("test_key")
    assert result == {"data": "value"}


@pytest.mark.asyncio()
async def test_redis_get_nonexistent(redis_client):
    """Test get returns None for nonexistent key."""
    result = await redis_client.get("nonexistent")
    assert result is None


@pytest.mark.asyncio()
async def test_redis_set_with_ttl(redis_client):
    """Test set with TTL."""
    await redis_client.set("ttl_key", {"data": "value"}, ttl=60)
    result = await redis_client.get("ttl_key")
    assert result == {"data": "value"}


@pytest.mark.asyncio()
async def test_redis_delete(redis_client):
    """Test delete operation."""
    await redis_client.set("delete_key", {"data": "value"})
    await redis_client.delete("delete_key")
    result = await redis_client.get("delete_key")
    assert result is None


@pytest.mark.asyncio()
async def test_redis_client_direct_instantiation():
    """Test RedisClient can be instantiated directly."""
    client = RedisClient("redis://localhost:6379")
    assert client.url == "redis://localhost:6379"
    assert client._client is not None
    await client.close()


@pytest.mark.asyncio()
async def test_redis_get_with_falsy_value():
    """Test Redis get handles values that evaluate to False (empty string, 0, False)."""
    from unittest.mock import AsyncMock, MagicMock

    client = RedisClient("redis://localhost:6379")

    # Mock _client.get to return empty string (falsy but not None)
    client._client = MagicMock()
    client._client.get = AsyncMock(return_value="")  # Empty string is falsy
    client._client.close = AsyncMock()  # Mock close as well

    # Should return None for falsy values (empty string)
    result = await client.get("empty_key")
    assert result is None

    await client.close()


@pytest.mark.asyncio()
async def test_redis_get_with_json_encoded_null():
    """Test Redis get handles JSON-encoded null correctly."""
    from unittest.mock import AsyncMock, MagicMock

    client = RedisClient("redis://localhost:6379")

    # Mock _client.get to return JSON-encoded null
    client._client = MagicMock()
    client._client.get = AsyncMock(return_value="null")  # JSON string "null"
    client._client.close = AsyncMock()

    # Should parse as Python None
    result = await client.get("null_key")
    assert result is None

    await client.close()
