"""Narrative Cache - Redis-based caching for narrative generation.

Reduces API costs by caching narratives and reusing when metrics are similar.

Biblical Foundation:
- Proverbs 13:16: "Every prudent man acts with knowledge,
  but a fool flaunts his folly"

Features:
- Redis-based persistent cache
- Metrics hash computation (2 decimal precision)
- TTL-based expiration (5 min default)
- Cache hit/miss metrics
- Similarity threshold for cache invalidation

Author: Vértice Platform Team
Created: 2025-11-01
"""

import hashlib
import json
import logging
from datetime import timedelta
from typing import Any

from prometheus_client import Counter, Histogram

logger = logging.getLogger(__name__)


# Prometheus metrics
cache_hits = Counter(
    "nis_narrative_cache_hits_total", "Total cache hits for narrative generation"
)

cache_misses = Counter(
    "nis_narrative_cache_misses_total", "Total cache misses for narrative generation"
)

cache_invalidations = Counter(
    "nis_narrative_cache_invalidations_total",
    "Total cache invalidations due to metrics change",
)

cache_lookup_duration = Histogram(
    "nis_narrative_cache_lookup_duration_seconds", "Cache lookup duration"
)


class NarrativeCache:
    """Redis-based cache for narratives with intelligent invalidation.

    Caches narratives based on metrics signature. Invalidates when metrics
    change beyond similarity threshold.

    Biblical Principle: Proverbs 13:16 - "Every prudent man acts with knowledge"
    """

    def __init__(
        self,
        redis_client: Any = None,
        ttl_seconds: int = 300,  # 5 minutes
        similarity_threshold: float = 0.95,  # 95% similarity to reuse cache
        precision_decimals: int = 2,  # Round to 2 decimals
    ):
        """Initialize narrative cache.

        Args:
            redis_client: Redis client instance (optional for testing)
            ttl_seconds: Cache TTL in seconds (default 5 min)
            similarity_threshold: Minimum similarity to reuse cached narrative (0-1)
            precision_decimals: Decimal precision for metrics rounding (reduces cache misses)

        """
        self.redis = redis_client
        self.ttl = timedelta(seconds=ttl_seconds)
        self.similarity_threshold = similarity_threshold
        self.precision = precision_decimals

        logger.info(
            f"NarrativeCache initialized (ttl={ttl_seconds}s, threshold={similarity_threshold})"
        )

    def _compute_metrics_hash(self, metrics_data: dict[str, Any]) -> str:
        """Compute hash of metrics data for cache key.

        Rounds numerical values to reduce cache misses from minor fluctuations.

        Args:
            metrics_data: Metrics dictionary to hash

        Returns:
            SHA256 hash of normalized metrics

        """
        # Normalize metrics by rounding numbers
        normalized = self._normalize_metrics(metrics_data)

        # Sort keys for consistent hashing
        json_str = json.dumps(normalized, sort_keys=True)

        # Compute SHA256 hash
        hash_obj = hashlib.sha256(json_str.encode("utf-8"))
        return hash_obj.hexdigest()

    def _normalize_metrics(self, metrics: dict[str, Any]) -> dict[str, Any]:
        """Normalize metrics by rounding numerical values.

        Args:
            metrics: Raw metrics dictionary

        Returns:
            Normalized metrics with rounded values

        """
        normalized: dict[str, Any] = {}

        for key, value in metrics.items():
            if isinstance(value, float):
                # Round to precision
                normalized[key] = round(value, self.precision)
            elif isinstance(value, int):
                normalized[key] = value
            elif isinstance(value, dict):
                # Recursive normalization
                normalized[key] = self._normalize_metrics(value)  # type: ignore[assignment]
            elif isinstance(value, list):
                # Normalize list elements
                normalized[key] = [  # type: ignore[assignment]
                    (
                        self._normalize_metrics(item)
                        if isinstance(item, dict)
                        else (
                            round(item, self.precision)
                            if isinstance(item, float)
                            else item
                        )
                    )
                    for item in value
                ]
            else:
                normalized[key] = value

        return normalized

    async def get_cached_narrative(
        self,
        service: str,
        metrics_data: dict[str, Any],
        narrative_type: str = "default",
    ) -> dict[str, Any] | None:
        """Get cached narrative if available and metrics match.

        Args:
            service: Service name (e.g., "penelope", "maba")
            metrics_data: Current metrics data
            narrative_type: Type of narrative (e.g., "default", "alert")

        Returns:
            Cached narrative dict if hit, None if miss

        """
        with cache_lookup_duration.time():
            try:
                # Compute cache key
                metrics_hash = self._compute_metrics_hash(metrics_data)
                cache_key = f"narrative:{service}:{narrative_type}:{metrics_hash}"

                # Check Redis
                if not self.redis:
                    logger.debug("Redis not configured, cache disabled")
                    cache_misses.inc()
                    return None

                cached_data = await self.redis.get(cache_key)

                if cached_data:
                    # Parse cached JSON
                    narrative: dict[str, Any] = json.loads(cached_data)

                    cache_hits.inc()
                    logger.info(
                        f"✅ Cache HIT for {service}/{narrative_type} (hash={metrics_hash[:8]})"
                    )
                    return narrative

                # Cache miss
                cache_misses.inc()
                logger.debug(
                    f"❌ Cache MISS for {service}/{narrative_type} (hash={metrics_hash[:8]})"
                )
                return None

            except Exception as e:
                logger.error(f"Cache lookup failed: {e}", exc_info=True)
                cache_misses.inc()
                return None

    async def cache_narrative(
        self,
        service: str,
        metrics_data: dict[str, Any],
        narrative: dict[str, Any],
        narrative_type: str = "default",
    ) -> None:
        """Store narrative in cache with TTL.

        Args:
            service: Service name
            metrics_data: Metrics data used to generate narrative
            narrative: Generated narrative to cache
            narrative_type: Type of narrative

        """
        try:
            # Compute cache key
            metrics_hash = self._compute_metrics_hash(metrics_data)
            cache_key = f"narrative:{service}:{narrative_type}:{metrics_hash}"

            if not self.redis:
                logger.debug("Redis not configured, skipping cache")
                return

            # Serialize narrative
            narrative_json = json.dumps(narrative)

            # Store with TTL
            await self.redis.setex(
                cache_key, int(self.ttl.total_seconds()), narrative_json
            )

            logger.info(
                f"💾 Cached narrative for {service}/{narrative_type} "
                f"(hash={metrics_hash[:8]}, ttl={self.ttl.total_seconds()}s)"
            )

        except Exception as e:
            logger.error(f"Failed to cache narrative: {e}", exc_info=True)

    async def invalidate_cache(
        self, service: str, narrative_type: str | None = None
    ) -> int:
        """Invalidate cached narratives for a service.

        Args:
            service: Service name to invalidate
            narrative_type: Optional specific narrative type to invalidate

        Returns:
            Number of cache entries invalidated

        """
        try:
            if not self.redis:
                return 0

            # Build pattern
            if narrative_type:
                pattern = f"narrative:{service}:{narrative_type}:*"
            else:
                pattern = f"narrative:{service}:*"

            # Find matching keys
            cursor = 0
            count = 0

            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)

                if keys:
                    await self.redis.delete(*keys)
                    count += len(keys)

                if cursor == 0:
                    break

            cache_invalidations.inc(count)
            logger.info(f"🗑️  Invalidated {count} cache entries for {service}")
            return count

        except Exception as e:
            logger.error(f"Cache invalidation failed: {e}", exc_info=True)
            return 0

    async def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache metrics

        """
        try:
            if not self.redis:
                return {
                    "enabled": False,
                    "ttl_seconds": self.ttl.total_seconds(),
                    "similarity_threshold": self.similarity_threshold,
                }

            # Get Redis info
            info = await self.redis.info("stats")

            # Count narrative cache keys
            cursor = 0
            cached_narratives = 0

            while True:
                cursor, keys = await self.redis.scan(
                    cursor, match="narrative:*", count=100
                )
                cached_narratives += len(keys)

                if cursor == 0:
                    break

            return {
                "enabled": True,
                "ttl_seconds": self.ttl.total_seconds(),
                "similarity_threshold": self.similarity_threshold,
                "precision_decimals": self.precision,
                "cached_narratives": cached_narratives,
                "redis_keyspace_hits": info.get("keyspace_hits", 0),
                "redis_keyspace_misses": info.get("keyspace_misses", 0),
            }

        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}", exc_info=True)
            return {
                "enabled": False,
                "error": str(e),
            }

    def compute_similarity(
        self, metrics1: dict[str, Any], metrics2: dict[str, Any]
    ) -> float:
        """Compute similarity score between two metrics dictionaries.

        Uses normalized metrics hash comparison.

        Args:
            metrics1: First metrics dict
            metrics2: Second metrics dict

        Returns:
            Similarity score (0-1, where 1.0 is identical)

        """
        hash1 = self._compute_metrics_hash(metrics1)
        hash2 = self._compute_metrics_hash(metrics2)

        # Exact match
        if hash1 == hash2:
            return 1.0

        # Compare normalized values
        norm1 = self._normalize_metrics(metrics1)
        norm2 = self._normalize_metrics(metrics2)

        # Simple similarity: count matching keys and values
        all_keys = set(norm1.keys()) | set(norm2.keys())
        if not all_keys:
            return 0.0

        matching_keys = sum(1 for k in all_keys if norm1.get(k) == norm2.get(k))

        return matching_keys / len(all_keys)
