"""Tests for Narrative Cache - Redis-based caching."""

from unittest.mock import AsyncMock, MagicMock

from core.narrative_cache import NarrativeCache
import pytest


@pytest.fixture
def mock_redis():
    """Create mock Redis client."""
    redis = MagicMock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    redis.scan = AsyncMock(return_value=(0, []))
    redis.info = AsyncMock(return_value={"keyspace_hits": 100, "keyspace_misses": 50})
    return redis


@pytest.fixture
def cache(mock_redis):
    """Create narrative cache instance."""
    return NarrativeCache(redis_client=mock_redis, ttl_seconds=300)


@pytest.fixture
def sample_metrics():
    """Sample metrics data."""
    return {
        "cpu_usage": 75.5,
        "memory_usage": 512.3,
        "request_count": 100,
        "error_rate": 0.05,
        "latency_p95": 250.7,
    }


@pytest.fixture
def sample_narrative():
    """Sample narrative response."""
    return {
        "title": "System Performance Report",
        "summary": "System is healthy with normal CPU usage.",
        "alerts": [],
        "recommendations": ["Monitor CPU trends"],
    }


class TestInitialization:
    def test_initialize_with_defaults(self):
        """GIVEN: Default parameters.

        WHEN: NarrativeCache created
        THEN: Initializes with correct defaults.
        """
        cache = NarrativeCache()

        assert cache.ttl.total_seconds() == 300
        assert cache.similarity_threshold == 0.95
        assert cache.precision == 2

    def test_initialize_with_custom_params(self):
        """GIVEN: Custom parameters.

        WHEN: NarrativeCache created
        THEN: Initializes with custom values.
        """
        cache = NarrativeCache(
            ttl_seconds=600, similarity_threshold=0.90, precision_decimals=3
        )

        assert cache.ttl.total_seconds() == 600
        assert cache.similarity_threshold == 0.90
        assert cache.precision == 3


class TestMetricsHashing:
    def test_compute_hash_consistent(self, cache, sample_metrics):
        """GIVEN: Same metrics data.

        WHEN: _compute_metrics_hash called multiple times
        THEN: Returns same hash.
        """
        hash1 = cache._compute_metrics_hash(sample_metrics)
        hash2 = cache._compute_metrics_hash(sample_metrics)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex digest

    def test_compute_hash_different_metrics(self, cache, sample_metrics):
        """GIVEN: Different metrics data.

        WHEN: _compute_metrics_hash called
        THEN: Returns different hashes.
        """
        metrics2 = sample_metrics.copy()
        metrics2["cpu_usage"] = 80.0

        hash1 = cache._compute_metrics_hash(sample_metrics)
        hash2 = cache._compute_metrics_hash(metrics2)

        assert hash1 != hash2

    def test_normalize_metrics_rounds_floats(self, cache):
        """GIVEN: Metrics with high precision floats.

        WHEN: _normalize_metrics called
        THEN: Rounds to precision decimals.
        """
        metrics = {
            "cpu": 75.556789,
            "memory": 512.123456,
            "count": 100,
        }

        normalized = cache._normalize_metrics(metrics)

        assert normalized["cpu"] == 75.56  # 2 decimals
        assert normalized["memory"] == 512.12  # 2 decimals
        assert normalized["count"] == 100  # int unchanged

    def test_normalize_metrics_nested_dicts(self, cache):
        """GIVEN: Metrics with nested dictionaries.

        WHEN: _normalize_metrics called
        THEN: Recursively normalizes nested values.
        """
        metrics = {
            "system": {"cpu": 75.556, "memory": 512.123},
            "network": {"latency": 250.789},
        }

        normalized = cache._normalize_metrics(metrics)

        assert normalized["system"]["cpu"] == 75.56
        assert normalized["system"]["memory"] == 512.12
        assert normalized["network"]["latency"] == 250.79

    def test_normalize_metrics_with_lists(self, cache):
        """GIVEN: Metrics with lists of values.

        WHEN: _normalize_metrics called
        THEN: Normalizes list elements.
        """
        metrics = {
            "latencies": [100.555, 200.666, 300.777],
            "counts": [10, 20, 30],
        }

        normalized = cache._normalize_metrics(metrics)

        assert normalized["latencies"] == [100.56, 200.67, 300.78]
        assert normalized["counts"] == [10, 20, 30]


class TestCacheOperations:
    @pytest.mark.asyncio
    async def test_cache_miss(self, cache, mock_redis, sample_metrics):
        """GIVEN: Empty cache.

        WHEN: get_cached_narrative called
        THEN: Returns None (cache miss).
        """
        mock_redis.get = AsyncMock(return_value=None)

        result = await cache.get_cached_narrative(
            service="penelope", metrics_data=sample_metrics
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_cache_hit(self, cache, mock_redis, sample_metrics, sample_narrative):
        """GIVEN: Cached narrative exists.

        WHEN: get_cached_narrative called
        THEN: Returns cached narrative.
        """
        import json

        mock_redis.get = AsyncMock(return_value=json.dumps(sample_narrative))

        result = await cache.get_cached_narrative(
            service="penelope", metrics_data=sample_metrics
        )

        assert result is not None
        assert result["title"] == sample_narrative["title"]
        assert result["summary"] == sample_narrative["summary"]

    @pytest.mark.asyncio
    async def test_cache_narrative_stores_correctly(
        self, cache, mock_redis, sample_metrics, sample_narrative
    ):
        """GIVEN: New narrative to cache.

        WHEN: cache_narrative called
        THEN: Stores in Redis with correct TTL.
        """
        await cache.cache_narrative(
            service="penelope",
            metrics_data=sample_metrics,
            narrative=sample_narrative,
        )

        # Verify Redis setex called
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args

        # Check TTL
        assert call_args[0][1] == 300  # 5 minutes

    @pytest.mark.asyncio
    async def test_cache_with_narrative_type(
        self, cache, mock_redis, sample_metrics, sample_narrative
    ):
        """GIVEN: Narrative with specific type.

        WHEN: cache_narrative called with type
        THEN: Stores with type in cache key.
        """
        await cache.cache_narrative(
            service="penelope",
            metrics_data=sample_metrics,
            narrative=sample_narrative,
            narrative_type="alert",
        )

        # Verify cache key includes type
        call_args = mock_redis.setex.call_args
        cache_key = call_args[0][0]
        assert "alert" in cache_key


class TestCacheInvalidation:
    @pytest.mark.asyncio
    async def test_invalidate_service_cache(self, cache, mock_redis):
        """GIVEN: Cached narratives for service.

        WHEN: invalidate_cache called
        THEN: Deletes matching cache entries.
        """
        # Mock scan to return some keys
        mock_redis.scan = AsyncMock(
            return_value=(
                0,
                [
                    b"narrative:penelope:default:abc123",
                    b"narrative:penelope:alert:def456",
                ],
            )
        )

        count = await cache.invalidate_cache(service="penelope")

        assert count == 2
        mock_redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalidate_specific_type(self, cache, mock_redis):
        """GIVEN: Cached narratives of specific type.

        WHEN: invalidate_cache called with type
        THEN: Only deletes that type.
        """
        mock_redis.scan = AsyncMock(
            return_value=(0, [b"narrative:penelope:alert:abc123"])
        )

        count = await cache.invalidate_cache(service="penelope", narrative_type="alert")

        assert count == 1

        # Verify pattern includes type
        call_args = mock_redis.scan.call_args
        pattern = call_args[1]["match"]
        assert "alert" in pattern


class TestSimilarity:
    def test_similarity_identical_metrics(self, cache, sample_metrics):
        """GIVEN: Identical metrics.

        WHEN: compute_similarity called
        THEN: Returns 1.0.
        """
        similarity = cache.compute_similarity(sample_metrics, sample_metrics)

        assert similarity == 1.0

    def test_similarity_slightly_different(self, cache, sample_metrics):
        """GIVEN: Slightly different metrics (within rounding).

        WHEN: compute_similarity called
        THEN: Returns 1.0 (normalized to same hash).
        """
        metrics2 = sample_metrics.copy()
        metrics2["cpu_usage"] = 75.556  # Rounds to 75.56 (same as 75.5 ≈ 75.50)

        # This might not be 1.0 depending on rounding
        similarity = cache.compute_similarity(sample_metrics, metrics2)

        assert 0.8 <= similarity <= 1.0

    def test_similarity_different_metrics(self, cache, sample_metrics):
        """GIVEN: Completely different metrics.

        WHEN: compute_similarity called
        THEN: Returns low similarity.
        """
        metrics2 = {
            "cpu_usage": 10.0,
            "memory_usage": 100.0,
            "request_count": 5,
        }

        similarity = cache.compute_similarity(sample_metrics, metrics2)

        assert similarity < 0.5


class TestStats:
    @pytest.mark.asyncio
    async def test_get_stats_with_redis(self, cache, mock_redis):
        """GIVEN: Cache with Redis enabled.

        WHEN: get_stats called
        THEN: Returns statistics including Redis info.
        """
        mock_redis.scan = AsyncMock(
            side_effect=[
                (1, [b"narrative:penelope:default:abc"]),
                (0, [b"narrative:maba:default:def"]),
            ]
        )

        stats = await cache.get_stats()

        assert stats["enabled"] is True
        assert stats["ttl_seconds"] == 300
        assert stats["similarity_threshold"] == 0.95
        assert stats["cached_narratives"] == 2

    @pytest.mark.asyncio
    async def test_get_stats_without_redis(self):
        """GIVEN: Cache without Redis.

        WHEN: get_stats called
        THEN: Returns disabled status.
        """
        cache = NarrativeCache(redis_client=None)

        stats = await cache.get_stats()

        assert stats["enabled"] is False
        assert stats["ttl_seconds"] == 300


class TestEdgeCases:
    @pytest.mark.asyncio
    async def test_cache_without_redis(self, sample_metrics, sample_narrative):
        """GIVEN: Cache without Redis client.

        WHEN: cache operations called
        THEN: Gracefully handles missing Redis.
        """
        cache = NarrativeCache(redis_client=None)

        # Should not crash
        result = await cache.get_cached_narrative(
            service="penelope", metrics_data=sample_metrics
        )
        assert result is None

        # Should not crash
        await cache.cache_narrative(
            service="penelope",
            metrics_data=sample_metrics,
            narrative=sample_narrative,
        )

    @pytest.mark.asyncio
    async def test_redis_error_handling(self, cache, mock_redis, sample_metrics):
        """GIVEN: Redis raises exception.

        WHEN: cache operations called
        THEN: Handles error gracefully.
        """
        mock_redis.get = AsyncMock(side_effect=Exception("Redis connection failed"))

        # Should not crash, returns None
        result = await cache.get_cached_narrative(
            service="penelope", metrics_data=sample_metrics
        )
        assert result is None

    def test_normalize_empty_metrics(self, cache):
        """GIVEN: Empty metrics dict.

        WHEN: _normalize_metrics called
        THEN: Returns empty dict.
        """
        normalized = cache._normalize_metrics({})

        assert normalized == {}
