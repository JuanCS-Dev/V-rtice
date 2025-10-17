"""Tests for VerdictCache."""

from uuid import uuid4

import pytest
from verdict_engine_service.cache import VerdictCache


@pytest.mark.asyncio
async def test_cache_connect_disconnect():
    """Test cache connection lifecycle."""
    cache = VerdictCache()

    assert cache.client is None

    # Note: In real test, would need Redis running
    # Here we test structure only


@pytest.mark.asyncio
async def test_cache_verdict_no_client(sample_verdict):
    """Test cache_verdict without connected client."""
    cache = VerdictCache()

    # Should not raise, just return silently
    await cache.cache_verdict(sample_verdict)


@pytest.mark.asyncio
async def test_get_verdict_no_client():
    """Test get_verdict without connected client."""
    cache = VerdictCache()
    verdict_id = uuid4()

    result = await cache.get_verdict(verdict_id)
    assert result is None


@pytest.mark.asyncio
async def test_cache_stats_no_client(sample_stats):
    """Test cache_stats without connected client."""
    cache = VerdictCache()

    await cache.cache_stats(sample_stats)
    # Should not raise


@pytest.mark.asyncio
async def test_get_stats_no_client():
    """Test get_stats without connected client."""
    cache = VerdictCache()

    result = await cache.get_stats()
    assert result is None


@pytest.mark.asyncio
async def test_invalidate_verdict_no_client():
    """Test invalidate_verdict without connected client."""
    cache = VerdictCache()
    verdict_id = uuid4()

    await cache.invalidate_verdict(verdict_id)
    # Should not raise


@pytest.mark.asyncio
async def test_invalidate_stats_no_client():
    """Test invalidate_stats without connected client."""
    cache = VerdictCache()

    await cache.invalidate_stats()
    # Should not raise


def test_serialize_verdict(sample_verdict):
    """Test verdict serialization."""
    cache = VerdictCache()

    serialized = cache._serialize(sample_verdict)

    assert isinstance(serialized, str)
    assert str(sample_verdict.id) in serialized
    assert sample_verdict.title in serialized


def test_serialize_stats(sample_stats):
    """Test stats serialization."""
    cache = VerdictCache()

    serialized = cache._serialize(sample_stats)

    assert isinstance(serialized, str)
    assert str(sample_stats.total_count) in serialized


def test_encode_special_types(sample_verdict):
    """Test encoding of UUID, Decimal, datetime."""
    cache = VerdictCache()

    data = {
        "id": sample_verdict.id,
        "confidence": sample_verdict.confidence,
        "timestamp": sample_verdict.timestamp,
        "nested": {
            "uuid": sample_verdict.id,
        },
        "list": [sample_verdict.id, sample_verdict.confidence],
    }

    encoded = cache._encode_special_types(data)

    # UUIDs and Decimals should be strings
    assert isinstance(encoded["id"], str)
    assert isinstance(encoded["confidence"], str)
    assert isinstance(encoded["timestamp"], str)
    assert isinstance(encoded["nested"]["uuid"], str)


def test_serialize_non_model_object():
    """Test serialization of non-Verdict/non-VerdictStats object."""
    cache = VerdictCache()

    # Test with dict (line 45 fallback)
    data = {"key": "value", "number": 42}
    serialized = cache._serialize(data)

    assert isinstance(serialized, str)
    assert "key" in serialized
    assert "value" in serialized
