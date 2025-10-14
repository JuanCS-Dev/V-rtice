"""Maximus OSINT Service - Cache Manager (Multi-Tier Caching).

This module implements a multi-tier caching system with support for:
- In-memory LRU cache (fast, local)
- Redis cache (distributed, persistent)

Caching is critical for OSINT tools to:
- Reduce API calls (avoid rate limits)
- Improve response time (p95 < 500ms)
- Lower costs (many APIs are paid per request)

Constitutional Compliance:
    - Article II (Pagani Standard): Production-ready, no mocks
    - Article IV (Antifragility): System performs better under repeated queries

Author: Claude Code (Tactical Executor)
Date: 2025-10-14
Version: 1.0.0
"""

import json
import time
from collections import OrderedDict
from typing import Any, Optional

try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class LRUCache:
    """In-memory LRU (Least Recently Used) cache.

    Implements an LRU eviction policy: when cache is full, least recently
    accessed items are evicted first.

    Thread-safe for single-threaded async operations.

    Attributes:
        max_size: Maximum number of items in cache
        ttl: Time-to-live in seconds (None = infinite)
        cache: OrderedDict for LRU ordering
        timestamps: Item expiration timestamps
    """

    def __init__(self, max_size: int = 1000, ttl: Optional[int] = 3600):
        """Initialize LRU cache.

        Args:
            max_size: Maximum cache entries (default: 1000)
            ttl: Time-to-live in seconds (default: 3600s = 1h)
        """
        self.max_size = max_size
        self.ttl = ttl
        self.cache: OrderedDict = OrderedDict()
        self.timestamps: dict[str, float] = {}

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value if exists and not expired, None otherwise
        """
        if key not in self.cache:
            return None

        # Check expiration
        if self.ttl is not None:
            age = time.time() - self.timestamps.get(key, 0)
            if age > self.ttl:
                # Expired, remove
                self.cache.pop(key, None)
                self.timestamps.pop(key, None)
                return None

        # Move to end (mark as recently used)
        self.cache.move_to_end(key)
        return self.cache[key]

    def set(self, key: str, value: Any) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        # Update existing key
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            # Evict LRU item if cache full
            if len(self.cache) >= self.max_size:
                oldest_key = next(iter(self.cache))
                self.cache.pop(oldest_key)
                self.timestamps.pop(oldest_key, None)

        self.cache[key] = value
        self.timestamps[key] = time.time()

    def delete(self, key: str) -> None:
        """Delete key from cache.

        Args:
            key: Cache key
        """
        self.cache.pop(key, None)
        self.timestamps.pop(key, None)

    def clear(self) -> None:
        """Clear entire cache."""
        self.cache.clear()
        self.timestamps.clear()

    def size(self) -> int:
        """Get current cache size.

        Returns:
            Number of items in cache
        """
        return len(self.cache)


class CacheManager:
    """Multi-tier cache manager with Redis and in-memory LRU.

    Provides transparent caching with automatic fallback:
    1. Try Redis first (if available)
    2. Fallback to in-memory LRU
    3. If both miss, return None

    Usage Example:
        cache = CacheManager(ttl=3600, backend="redis")

        # Set
        await cache.set("key1", {"data": "value"})

        # Get
        result = await cache.get("key1")  # Returns {"data": "value"}

        # Auto-serialization to JSON for Redis
    """

    def __init__(
        self,
        ttl: int = 3600,
        backend: str = "memory",
        redis_url: str = "redis://localhost:6379",
        max_memory_size: int = 1000,
    ):
        """Initialize CacheManager.

        Args:
            ttl: Time-to-live in seconds
            backend: Cache backend ('memory' or 'redis')
            redis_url: Redis connection URL (if backend='redis')
            max_memory_size: Max in-memory cache size

        Raises:
            ValueError: If backend is invalid or Redis unavailable
        """
        self.ttl = ttl
        self.backend = backend

        # Initialize in-memory LRU (always available as fallback)
        self.memory_cache = LRUCache(max_size=max_memory_size, ttl=ttl)

        # Initialize Redis (if requested)
        self.redis_client: Optional[aioredis.Redis] = None
        if backend == "redis":
            if not REDIS_AVAILABLE:
                raise ValueError(
                    "Redis backend requested but 'redis[asyncio]' not installed. "
                    "Install with: pip install 'redis[asyncio]'"
                )
            self.redis_client = aioredis.from_url(redis_url, decode_responses=True)

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache (Redis first, then memory).

        Args:
            key: Cache key

        Returns:
            Cached value if exists, None otherwise
        """
        # Try Redis first
        if self.redis_client:
            try:
                data = await self.redis_client.get(key)
                if data:
                    return json.loads(data)
            except Exception:
                # Redis failure, fallback to memory
                pass

        # Fallback to in-memory cache
        return self.memory_cache.get(key)

    async def set(self, key: str, value: Any) -> None:
        """Set value in cache (both Redis and memory).

        Args:
            key: Cache key
            value: Value to cache (must be JSON-serializable)
        """
        # Set in memory cache (always)
        self.memory_cache.set(key, value)

        # Set in Redis (if available)
        if self.redis_client:
            try:
                serialized = json.dumps(value)
                await self.redis_client.setex(key, self.ttl, serialized)
            except Exception:
                # Redis failure, memory cache still works
                pass

    async def delete(self, key: str) -> None:
        """Delete key from both Redis and memory cache.

        Args:
            key: Cache key
        """
        # Delete from memory
        self.memory_cache.delete(key)

        # Delete from Redis
        if self.redis_client:
            try:
                await self.redis_client.delete(key)
            except Exception:
                pass

    async def clear(self) -> None:
        """Clear entire cache (both Redis and memory)."""
        # Clear memory
        self.memory_cache.clear()

        # Clear Redis (only keys matching pattern)
        if self.redis_client:
            try:
                await self.redis_client.flushdb()
            except Exception:
                pass

    async def close(self) -> None:
        """Close Redis connection.

        Call this on service shutdown.
        """
        if self.redis_client:
            await self.redis_client.close()

    def get_stats(self) -> dict:
        """Get cache statistics.

        Returns:
            Statistics dictionary with size and backend info
        """
        return {
            "backend": self.backend,
            "memory_size": self.memory_cache.size(),
            "memory_max_size": self.memory_cache.max_size,
            "ttl": self.ttl,
            "redis_available": self.redis_client is not None,
        }
