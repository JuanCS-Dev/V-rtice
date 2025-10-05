"""
Redis Cache Manager for Cognitive Defense System.

Implements multi-tier caching strategy with category-specific TTLs,
LRU eviction, and async operations for high-performance lookups.
"""

import logging
import json
import hashlib
from typing import Optional, Any, Dict, List
from datetime import timedelta
from enum import Enum

import redis.asyncio as aioredis
from redis.asyncio import Redis
from redis.exceptions import RedisError

from .config import get_settings

logger = logging.getLogger(__name__)


class CacheCategory(str, Enum):
    """Cache categories with different TTL strategies."""
    NEWSGUARD = "newsguard"          # 7 days - source credibility rarely changes
    FACTCHECK = "factcheck"          # 30 days - fact-checks are persistent
    ANALYSIS = "analysis"            # 7 days - analysis results
    REPUTATION = "reputation"        # 1 day - dynamic reputation scores
    ENTITY_LINKING = "entity"        # 14 days - entity disambiguation
    PROPAGANDA_PATTERNS = "propaganda"  # 7 days - learned patterns
    MODEL_CACHE = "model"            # 1 hour - model inference cache


class CacheManager:
    """Manages Redis cache with multi-tier strategy."""

    def __init__(self):
        """Initialize cache manager."""
        self.redis: Optional[Redis] = None
        self.settings = get_settings()
        self._key_prefix = "cogdef:"

    async def initialize(self) -> None:
        """
        Initialize Redis connection pool.

        Creates async connection with optimal pooling for high concurrency.
        """
        if self.redis is not None:
            logger.warning("Cache already initialized, skipping")
            return

        try:
            self.redis = await aioredis.from_url(
                f"redis://{self.settings.REDIS_HOST}:{self.settings.REDIS_PORT}/{self.settings.REDIS_DB}",
                encoding="utf-8",
                decode_responses=True,
                max_connections=50,
                socket_timeout=5.0,
                socket_connect_timeout=5.0,
                retry_on_timeout=True,
            )

            # Test connection
            await self.redis.ping()

            logger.info(
                f"✅ Redis cache initialized: "
                f"{self.settings.REDIS_HOST}:{self.settings.REDIS_PORT}/{self.settings.REDIS_DB}"
            )

        except Exception as e:
            logger.error(f"❌ Failed to initialize Redis: {e}")
            raise

    async def close(self) -> None:
        """Close Redis connection."""
        if self.redis is not None:
            await self.redis.close()
            self.redis = None
            logger.info("✅ Redis connection closed")

    def _make_key(self, category: CacheCategory, identifier: str) -> str:
        """
        Generate namespaced cache key.

        Args:
            category: Cache category
            identifier: Unique identifier within category

        Returns:
            Namespaced key string
        """
        return f"{self._key_prefix}{category.value}:{identifier}"

    def _get_ttl(self, category: CacheCategory) -> int:
        """
        Get TTL in seconds for cache category.

        Args:
            category: Cache category

        Returns:
            TTL in seconds
        """
        ttl_map = {
            CacheCategory.NEWSGUARD: self.settings.CACHE_TTL_NEWSGUARD,
            CacheCategory.FACTCHECK: self.settings.CACHE_TTL_FACTCHECK,
            CacheCategory.ANALYSIS: self.settings.CACHE_TTL_ANALYSIS,
            CacheCategory.REPUTATION: self.settings.CACHE_TTL_REPUTATION,
            CacheCategory.ENTITY_LINKING: 1209600,  # 14 days
            CacheCategory.PROPAGANDA_PATTERNS: 604800,  # 7 days
            CacheCategory.MODEL_CACHE: 3600,  # 1 hour
        }
        return ttl_map.get(category, 3600)  # Default 1 hour

    async def get(
        self,
        category: CacheCategory,
        identifier: str,
        deserialize: bool = True
    ) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            category: Cache category
            identifier: Unique identifier
            deserialize: Whether to JSON deserialize (default True)

        Returns:
            Cached value or None if not found
        """
        if self.redis is None:
            logger.warning("Cache not initialized")
            return None

        try:
            key = self._make_key(category, identifier)
            value = await self.redis.get(key)

            if value is None:
                return None

            if deserialize:
                return json.loads(value)
            return value

        except RedisError as e:
            logger.error(f"Redis GET error for {category}/{identifier}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for {category}/{identifier}: {e}")
            return None

    async def set(
        self,
        category: CacheCategory,
        identifier: str,
        value: Any,
        ttl_override: Optional[int] = None,
        serialize: bool = True
    ) -> bool:
        """
        Set value in cache with TTL.

        Args:
            category: Cache category
            identifier: Unique identifier
            value: Value to cache
            ttl_override: Override default TTL (seconds)
            serialize: Whether to JSON serialize (default True)

        Returns:
            True if successful, False otherwise
        """
        if self.redis is None:
            logger.warning("Cache not initialized")
            return False

        try:
            key = self._make_key(category, identifier)
            ttl = ttl_override or self._get_ttl(category)

            if serialize:
                value = json.dumps(value)

            await self.redis.setex(key, ttl, value)
            return True

        except RedisError as e:
            logger.error(f"Redis SET error for {category}/{identifier}: {e}")
            return False
        except (TypeError, ValueError) as e:
            logger.error(f"Serialization error for {category}/{identifier}: {e}")
            return False

    async def delete(self, category: CacheCategory, identifier: str) -> bool:
        """
        Delete key from cache.

        Args:
            category: Cache category
            identifier: Unique identifier

        Returns:
            True if deleted, False otherwise
        """
        if self.redis is None:
            return False

        try:
            key = self._make_key(category, identifier)
            result = await self.redis.delete(key)
            return result > 0
        except RedisError as e:
            logger.error(f"Redis DELETE error for {category}/{identifier}: {e}")
            return False

    async def exists(self, category: CacheCategory, identifier: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            category: Cache category
            identifier: Unique identifier

        Returns:
            True if exists, False otherwise
        """
        if self.redis is None:
            return False

        try:
            key = self._make_key(category, identifier)
            return await self.redis.exists(key) > 0
        except RedisError as e:
            logger.error(f"Redis EXISTS error: {e}")
            return False

    async def get_or_set(
        self,
        category: CacheCategory,
        identifier: str,
        factory_func,
        ttl_override: Optional[int] = None
    ) -> Any:
        """
        Get from cache or compute and set (cache-aside pattern).

        Args:
            category: Cache category
            identifier: Unique identifier
            factory_func: Async function to compute value if not cached
            ttl_override: Override default TTL

        Returns:
            Cached or computed value
        """
        # Try cache first
        cached = await self.get(category, identifier)
        if cached is not None:
            return cached

        # Cache miss - compute value
        try:
            value = await factory_func()
            await self.set(category, identifier, value, ttl_override)
            return value
        except Exception as e:
            logger.error(f"Factory function error for {category}/{identifier}: {e}")
            raise

    async def increment(
        self,
        category: CacheCategory,
        identifier: str,
        amount: int = 1
    ) -> int:
        """
        Increment counter value.

        Args:
            category: Cache category
            identifier: Unique identifier
            amount: Increment amount

        Returns:
            New value after increment
        """
        if self.redis is None:
            return 0

        try:
            key = self._make_key(category, identifier)
            return await self.redis.incrby(key, amount)
        except RedisError as e:
            logger.error(f"Redis INCR error: {e}")
            return 0

    async def get_many(
        self,
        category: CacheCategory,
        identifiers: List[str]
    ) -> Dict[str, Any]:
        """
        Get multiple values in single round-trip.

        Args:
            category: Cache category
            identifiers: List of identifiers

        Returns:
            Dict mapping identifier to value
        """
        if self.redis is None or not identifiers:
            return {}

        try:
            keys = [self._make_key(category, ident) for ident in identifiers]
            values = await self.redis.mget(keys)

            result = {}
            for ident, value in zip(identifiers, values):
                if value:
                    try:
                        result[ident] = json.loads(value)
                    except json.JSONDecodeError:
                        result[ident] = value
            return result

        except RedisError as e:
            logger.error(f"Redis MGET error: {e}")
            return {}

    async def set_many(
        self,
        category: CacheCategory,
        items: Dict[str, Any],
        ttl_override: Optional[int] = None
    ) -> bool:
        """
        Set multiple values with pipeline for efficiency.

        Args:
            category: Cache category
            items: Dict mapping identifier to value
            ttl_override: Override default TTL

        Returns:
            True if successful
        """
        if self.redis is None or not items:
            return False

        try:
            ttl = ttl_override or self._get_ttl(category)
            pipe = self.redis.pipeline()

            for ident, value in items.items():
                key = self._make_key(category, ident)
                serialized = json.dumps(value)
                pipe.setex(key, ttl, serialized)

            await pipe.execute()
            return True

        except RedisError as e:
            logger.error(f"Redis pipeline error: {e}")
            return False

    async def clear_category(self, category: CacheCategory) -> int:
        """
        Clear all keys in a category.

        Args:
            category: Cache category to clear

        Returns:
            Number of keys deleted
        """
        if self.redis is None:
            return 0

        try:
            pattern = f"{self._key_prefix}{category.value}:*"
            cursor = 0
            deleted = 0

            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
                if keys:
                    deleted += await self.redis.delete(*keys)
                if cursor == 0:
                    break

            logger.info(f"Cleared {deleted} keys from category {category.value}")
            return deleted

        except RedisError as e:
            logger.error(f"Redis SCAN/DELETE error: {e}")
            return 0

    async def flush_all(self) -> bool:
        """
        Flush entire cache database.

        ⚠️  WARNING: Deletes ALL keys in Redis DB!

        Returns:
            True if successful
        """
        if self.redis is None:
            return False

        try:
            await self.redis.flushdb()
            logger.warning("⚠️  Redis database flushed")
            return True
        except RedisError as e:
            logger.error(f"Redis FLUSHDB error: {e}")
            return False

    async def health_check(self) -> bool:
        """
        Check Redis connectivity.

        Returns:
            True if healthy, False otherwise
        """
        if self.redis is None:
            return False

        try:
            await self.redis.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict with cache stats
        """
        if self.redis is None:
            return {}

        try:
            info = await self.redis.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "total_keys": await self.redis.dbsize(),
                "hit_rate": self._calculate_hit_rate(info),
                "evicted_keys": info.get("evicted_keys", 0),
            }
        except RedisError as e:
            logger.error(f"Failed to get Redis stats: {e}")
            return {}

    @staticmethod
    def _calculate_hit_rate(info: Dict) -> float:
        """Calculate cache hit rate from Redis info."""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        return (hits / total * 100) if total > 0 else 0.0

    @staticmethod
    def hash_content(content: str) -> str:
        """
        Generate SHA256 hash for content-based cache key.

        Args:
            content: Content to hash

        Returns:
            Hex digest string
        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest()


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

cache_manager = CacheManager()


# ============================================================================
# LIFESPAN MANAGEMENT FOR FASTAPI
# ============================================================================

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan_cache(app):
    """
    FastAPI lifespan context for cache initialization/cleanup.

    Usage:
        app = FastAPI(lifespan=lifespan_cache)
    """
    # Startup
    logger.info("🚀 Initializing Redis cache...")
    await cache_manager.initialize()

    yield

    # Shutdown
    logger.info("🛑 Closing Redis connection...")
    await cache_manager.close()
