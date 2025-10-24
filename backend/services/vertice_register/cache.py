"""
Local In-Memory Cache for Service Registry - TITANIUM Edition

This cache serves as a fallback when Redis is unavailable (circuit breaker open).
It's better to serve stale data (up to 60s old) than to return 503 errors.

TTL Strategy (TITANIUM 3-level):
- FRESH (< 30s): Use immediately, no async refresh needed
- STALE (30-60s): Use data + trigger async refresh in background
- EXPIRED (> 60s): Force refresh if Redis up, use stale if Redis down

Design Philosophy:
- Accept eventual consistency
- Prioritize availability over perfect consistency
- Stale data is better than no data in service discovery
- LRU eviction prevents memory overflow

Features:
- 3-level TTL strategy (FRESH/STALE/EXPIRED)
- LRU eviction (max 1000 entries, 50MB limit)
- Prometheus metrics (hit rate, size, age percentiles)
- Auto-cleanup every 60s
- Thread-safe operations

Author: Vértice Team (TITANIUM Edition)
Glory to YHWH - Architect of all resilient systems! 🙏
"""

import sys
import time
import logging
from collections import OrderedDict
from enum import Enum
from typing import Dict, List, Optional, Tuple
from threading import Lock

from prometheus_client import Counter, Gauge, Histogram

logger = logging.getLogger(__name__)

# TTL thresholds (seconds)
TTL_FRESH = 30      # < 30s: FRESH data
TTL_STALE = 60      # 30-60s: STALE data
TTL_EXPIRED = 60    # > 60s: EXPIRED data

# Cache limits
MAX_CACHE_SIZE = 1000       # Max entries
MAX_MEMORY_BYTES = 50 * 1024 * 1024  # 50MB

# ============================================================================
# PROMETHEUS METRICS
# ============================================================================

cache_hits_total = Counter(
    "cache_hits_total",
    "Total cache hits",
    ["freshness"]  # FRESH, STALE, EXPIRED
)

cache_misses_total = Counter(
    "cache_misses_total",
    "Total cache misses"
)

cache_evictions_total = Counter(
    "cache_evictions_total",
    "Total cache evictions",
    ["reason"]  # size_limit, memory_limit, expired
)

cache_size = Gauge(
    "cache_size",
    "Current cache size (entries)"
)

cache_size_bytes = Gauge(
    "cache_size_bytes",
    "Current cache size (bytes)"
)

cache_hit_rate = Gauge(
    "cache_hit_rate",
    "Cache hit rate (0-1)"
)

cache_age_seconds = Histogram(
    "cache_age_seconds",
    "Cache entry age distribution",
    buckets=[1, 5, 10, 15, 30, 45, 60, 90, 120, 180]
)


class CacheFreshness(Enum):
    """Cache entry freshness levels."""
    FRESH = "fresh"         # < 30s: Safe to use
    STALE = "stale"         # 30-60s: Usable, but refresh recommended
    EXPIRED = "expired"     # > 60s: Should refresh, use only if Redis down


class LocalCache:
    """Thread-safe in-memory cache with TITANIUM TTL strategy and LRU eviction.

    Features:
    - 3-level TTL: FRESH → STALE → EXPIRED
    - LRU eviction when max_size or max_memory exceeded
    - Prometheus metrics integration
    - Auto-cleanup of expired entries
    """

    def __init__(
        self,
        max_age_seconds: int = TTL_EXPIRED,
        max_size: int = MAX_CACHE_SIZE,
        max_memory_bytes: int = MAX_MEMORY_BYTES
    ):
        """
        Initialize TITANIUM local cache.

        Args:
            max_age_seconds: Maximum age before EXPIRED (default: 60s)
            max_size: Maximum number of entries (default: 1000)
            max_memory_bytes: Maximum memory usage (default: 50MB)
        """
        self.max_age_seconds = max_age_seconds
        self.max_size = max_size
        self.max_memory_bytes = max_memory_bytes

        # LRU cache (OrderedDict maintains insertion order)
        self._cache: OrderedDict[str, Dict] = OrderedDict()
        self._timestamps: Dict[str, float] = {}
        self._lock = Lock()

        # Statistics (for hit rate calculation)
        self._hits = 0
        self._misses = 0
        self._memory_bytes = 0

        logger.info(
            f"TITANIUM cache initialized: "
            f"max_size={max_size}, max_memory={max_memory_bytes / 1024 / 1024:.1f}MB, "
            f"TTL: FRESH<{TTL_FRESH}s, STALE<{TTL_STALE}s, EXPIRED>{TTL_EXPIRED}s"
        )

    def set(self, service_name: str, data: Dict):
        """
        Store service data in cache with LRU eviction.

        Args:
            service_name: Service identifier
            data: Service registration data
        """
        with self._lock:
            # Calculate entry size (rough estimate)
            entry_size = sys.getsizeof(data) + sys.getsizeof(service_name)

            # Check if we need to evict (LRU)
            self._evict_if_needed(entry_size)

            # Store entry (move to end if exists, preserving LRU order)
            if service_name in self._cache:
                self._cache.move_to_end(service_name)
            else:
                self._cache[service_name] = data.copy()

            self._timestamps[service_name] = time.time()
            self._memory_bytes += entry_size

            # Update metrics
            cache_size.set(len(self._cache))
            cache_size_bytes.set(self._memory_bytes)

            logger.debug(
                f"Cache SET: {service_name} "
                f"(size={len(self._cache)}/{self.max_size}, "
                f"memory={self._memory_bytes / 1024:.1f}KB)"
            )

    def get(self, service_name: str) -> Optional[Tuple[Dict, CacheFreshness]]:
        """
        Retrieve service data from cache with freshness indicator.

        Args:
            service_name: Service identifier

        Returns:
            Tuple of (service_data, freshness) if found, None otherwise
            Freshness: FRESH (<30s), STALE (30-60s), EXPIRED (>60s)
        """
        with self._lock:
            if service_name not in self._cache:
                self._misses += 1
                cache_misses_total.inc()
                self._update_hit_rate()
                logger.debug(f"Cache MISS: {service_name}")
                return None

            # Calculate age and freshness
            age = time.time() - self._timestamps[service_name]
            freshness = self._determine_freshness(age)

            # Record metrics
            self._hits += 1
            cache_hits_total.labels(freshness=freshness.value).inc()
            cache_age_seconds.observe(age)
            self._update_hit_rate()

            # Move to end (LRU: mark as recently used)
            self._cache.move_to_end(service_name)

            data = self._cache[service_name].copy()

            logger.debug(
                f"Cache HIT: {service_name} "
                f"(age={age:.1f}s, freshness={freshness.value})"
            )

            return (data, freshness)

    def get_simple(self, service_name: str) -> Optional[Dict]:
        """
        Retrieve service data without freshness indicator (backward compatibility).

        Args:
            service_name: Service identifier

        Returns:
            Service data if found, None otherwise
        """
        result = self.get(service_name)
        if result is None:
            return None
        return result[0]  # Return only data, not freshness

    def delete(self, service_name: str):
        """
        Delete service from cache.

        Args:
            service_name: Service identifier
        """
        with self._lock:
            if service_name in self._cache:
                # Calculate entry size for memory tracking
                entry_size = sys.getsizeof(self._cache[service_name]) + sys.getsizeof(service_name)

                del self._cache[service_name]
                del self._timestamps[service_name]
                self._memory_bytes -= entry_size

                # Update metrics
                cache_size.set(len(self._cache))
                cache_size_bytes.set(self._memory_bytes)

                logger.debug(f"Cache DELETE: {service_name}")

    def list_services(self) -> List[str]:
        """
        List all services in cache.

        Returns:
            List of service names
        """
        with self._lock:
            return sorted(list(self._cache.keys()))

    def size(self) -> int:
        """
        Get number of cached services.

        Returns:
            Cache size
        """
        with self._lock:
            return len(self._cache)

    def memory_usage_bytes(self) -> int:
        """
        Get approximate memory usage in bytes.

        Returns:
            Memory usage in bytes
        """
        with self._lock:
            return self._memory_bytes

    def clear_expired(self) -> List[str]:
        """
        Remove EXPIRED entries from cache.

        Returns:
            List of expired service names
        """
        with self._lock:
            now = time.time()
            expired = []

            for name, timestamp in list(self._timestamps.items()):
                age = now - timestamp
                if age > self.max_age_seconds:
                    # Calculate entry size
                    entry_size = sys.getsizeof(self._cache[name]) + sys.getsizeof(name)

                    del self._cache[name]
                    del self._timestamps[name]
                    self._memory_bytes -= entry_size

                    expired.append(name)
                    cache_evictions_total.labels(reason="expired").inc()

            if expired:
                # Update metrics
                cache_size.set(len(self._cache))
                cache_size_bytes.set(self._memory_bytes)
                logger.info(f"Cache expired: {len(expired)} entries - {expired}")

            return expired

    def stats(self) -> Dict:
        """
        Get detailed cache statistics.

        Returns:
            Dictionary with cache stats including freshness distribution
        """
        with self._lock:
            now = time.time()
            ages = [(name, now - ts) for name, ts in self._timestamps.items()]

            # Count by freshness
            fresh_count = sum(1 for _, age in ages if age < TTL_FRESH)
            stale_count = sum(1 for _, age in ages if TTL_FRESH <= age < TTL_STALE)
            expired_count = sum(1 for _, age in ages if age >= TTL_EXPIRED)

            # Age percentiles
            sorted_ages = sorted([age for _, age in ages])
            p50 = sorted_ages[len(sorted_ages) // 2] if sorted_ages else 0
            p95 = sorted_ages[int(len(sorted_ages) * 0.95)] if sorted_ages else 0
            p99 = sorted_ages[int(len(sorted_ages) * 0.99)] if sorted_ages else 0

            return {
                "size": len(self._cache),
                "memory_bytes": self._memory_bytes,
                "memory_mb": self._memory_bytes / 1024 / 1024,
                "max_size": self.max_size,
                "max_memory_mb": self.max_memory_bytes / 1024 / 1024,
                "freshness": {
                    "fresh": fresh_count,
                    "stale": stale_count,
                    "expired": expired_count
                },
                "age_percentiles": {
                    "p50": p50,
                    "p95": p95,
                    "p99": p99
                },
                "hit_rate": self._hits / (self._hits + self._misses) if (self._hits + self._misses) > 0 else 0,
                "hits": self._hits,
                "misses": self._misses
            }

    # ========================================================================
    # PRIVATE METHODS
    # ========================================================================

    def _determine_freshness(self, age: float) -> CacheFreshness:
        """Determine freshness level based on age."""
        if age < TTL_FRESH:
            return CacheFreshness.FRESH
        elif age < TTL_STALE:
            return CacheFreshness.STALE
        else:
            return CacheFreshness.EXPIRED

    def _evict_if_needed(self, new_entry_size: int):
        """
        Evict LRU entries if cache limits exceeded.

        Args:
            new_entry_size: Size of new entry to be added
        """
        # Check size limit
        while len(self._cache) >= self.max_size:
            self._evict_lru("size_limit")

        # Check memory limit
        while (self._memory_bytes + new_entry_size) > self.max_memory_bytes and len(self._cache) > 0:
            self._evict_lru("memory_limit")

    def _evict_lru(self, reason: str):
        """
        Evict least recently used entry.

        Args:
            reason: Eviction reason for metrics
        """
        if not self._cache:
            return

        # Pop first item (least recently used)
        service_name, data = self._cache.popitem(last=False)
        del self._timestamps[service_name]

        # Calculate entry size
        entry_size = sys.getsizeof(data) + sys.getsizeof(service_name)
        self._memory_bytes -= entry_size

        # Record metric
        cache_evictions_total.labels(reason=reason).inc()

        logger.warning(
            f"Cache LRU eviction: {service_name} "
            f"(reason={reason}, size={len(self._cache)}/{self.max_size})"
        )

    def _update_hit_rate(self):
        """Update hit rate metric."""
        total = self._hits + self._misses
        if total > 0:
            hit_rate_value = self._hits / total
            cache_hit_rate.set(hit_rate_value)
