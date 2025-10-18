"""
Social Memory - PostgreSQL Backend with LRU Cache
==================================================

Stores long-term behavioral patterns and preferences for each agent.
Optimized for:
- Scalability: PostgreSQL for 10k+ agents
- Performance: LRU cache (p95 retrieval < 50ms)
- Concurrency: asyncpg connection pooling
- Cache efficiency: ≥ 80% hit rate

Architecture:
- Primary storage: PostgreSQL (social_patterns table)
- Cache layer: LRU cache (100 most recent agents)
- Update strategy: EMA (Exponential Moving Average) for pattern evolution

Authors: Claude Code (Executor Tático)
Date: 2025-10-14
Governance: Constituição Vértice v2.5 - Padrão Pagani
"""

import asyncio
import asyncpg
from collections import OrderedDict
from dataclasses import dataclass
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


# ===========================================================================
# CONFIGURATION
# ===========================================================================

@dataclass
class SocialMemoryConfig:
    """Configuration for SocialMemory PostgreSQL backend.

    Attributes:
        host: PostgreSQL host
        port: PostgreSQL port
        database: Database name
        user: Database user
        password: Database password
        pool_size: Connection pool size
        cache_size: LRU cache size (number of agents)
    """

    host: str = "localhost"
    port: int = 5432
    database: str = "maximus_dev"
    user: str = "maximus"
    password: str = "dev_password"
    pool_size: int = 10
    cache_size: int = 100


# ===========================================================================
# EXCEPTIONS
# ===========================================================================

class PatternNotFoundError(Exception):
    """Raised when pattern for agent_id is not found."""

    pass


# ===========================================================================
# LRU CACHE
# ===========================================================================

class LRUCache:
    """LRU (Least Recently Used) cache implementation.

    Thread-safe, bounded cache with O(1) get/put operations.
    """

    def __init__(self, capacity: int):
        """Initialize LRU cache.

        Args:
            capacity: Maximum number of items to cache
        """
        if capacity < 1:
            raise ValueError(f"Cache capacity must be >= 1, got {capacity}")

        self.capacity = capacity
        self.cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get value from cache (mark as recently used).

        Args:
            key: Cache key

        Returns:
            Cached value if present, None otherwise
        """
        async with self._lock:
            if key in self.cache:
                # Move to end (mark as recently used)
                self.cache.move_to_end(key)
                self.hits += 1
                return self.cache[key].copy()  # Return copy to prevent mutation

            self.misses += 1
            return None

    async def put(self, key: str, value: Dict[str, Any]) -> None:
        """Put value in cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        async with self._lock:
            if key in self.cache:
                # Update existing entry and move to end
                self.cache.move_to_end(key)
            else:
                # New entry
                if len(self.cache) >= self.capacity:
                    # Evict LRU (first item)
                    self.cache.popitem(last=False)
                    self.evictions += 1

            self.cache[key] = value.copy()

    async def invalidate(self, key: str) -> None:
        """Invalidate cache entry.

        Args:
            key: Cache key to invalidate
        """
        async with self._lock:
            self.cache.pop(key, None)

    async def clear(self) -> None:
        """Clear entire cache."""
        async with self._lock:
            self.cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dict with hits, misses, hit_rate, size, evictions
        """
        total_accesses = self.hits + self.misses
        hit_rate = self.hits / total_accesses if total_accesses > 0 else 0.0

        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "size": len(self.cache),
            "capacity": self.capacity,
            "evictions": self.evictions,
        }


# ===========================================================================
# SOCIAL MEMORY
# ===========================================================================

class SocialMemory:
    """Social memory storage with PostgreSQL backend and LRU cache.

    Usage:
        >>> config = SocialMemoryConfig(database="maximus_dev")
        >>> memory = SocialMemory(config)
        >>> await memory.initialize()
        >>>
        >>> # Store pattern
        >>> await memory.store_pattern("user_123", {"confusion_history": 0.7})
        >>>
        >>> # Retrieve pattern
        >>> patterns = await memory.retrieve_patterns("user_123")
        >>>
        >>> # Update from interaction (EMA)
        >>> await memory.update_from_interaction("user_123", {"confusion_history": 0.5})
        >>>
        >>> await memory.close()
    """

    def __init__(self, config: SocialMemoryConfig):
        """Initialize SocialMemory.

        Args:
            config: Database and cache configuration
        """
        self.config = config
        self.pool: Optional[asyncpg.Pool] = None
        self.cache = LRUCache(capacity=config.cache_size)
        self._closed = False

    async def initialize(self) -> None:
        """Initialize database connection pool.

        Raises:
            ConnectionError: If unable to connect to database
        """
        if self._closed:
            raise RuntimeError("Cannot initialize closed SocialMemory")

        try:
            self.pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password,
                min_size=2,
                max_size=self.config.pool_size,
                command_timeout=10.0,
            )

            logger.info(
                f"SocialMemory initialized: {self.config.database}@{self.config.host}"
            )

        except Exception as e:
            raise ConnectionError(
                f"Failed to connect to PostgreSQL: {e}"
            ) from e

    async def close(self) -> None:
        """Close database connection pool (idempotent)."""
        if self._closed:
            return

        if self.pool:
            await self.pool.close()
            logger.info("SocialMemory pool closed")

        await self.cache.clear()
        self._closed = True

    def _check_not_closed(self) -> None:
        """Raise RuntimeError if closed."""
        if self._closed:
            raise RuntimeError("Operation on closed SocialMemory")

    async def store_pattern(
        self, agent_id: str, patterns: Dict[str, Any]
    ) -> None:
        """Store or update pattern for agent.

        Uses INSERT ON CONFLICT UPDATE (upsert).

        Args:
            agent_id: Unique agent identifier
            patterns: Pattern dict (JSONB)

        Raises:
            RuntimeError: If SocialMemory is closed
        """
        self._check_not_closed()

        query = """
            INSERT INTO social_patterns (agent_id, patterns, interaction_count)
            VALUES ($1, $2::jsonb, 0)
            ON CONFLICT (agent_id)
            DO UPDATE SET
                patterns = $2::jsonb,
                last_updated = NOW()
        """

        async with self.pool.acquire() as conn:
            await conn.execute(query, agent_id, patterns)

        # Invalidate cache (pattern updated)
        await self.cache.invalidate(agent_id)

        logger.debug(f"Stored pattern for {agent_id}: {patterns}")

    async def retrieve_patterns(self, agent_id: str) -> Dict[str, Any]:
        """Retrieve patterns for agent (cache-aware).

        Args:
            agent_id: Unique agent identifier

        Returns:
            Pattern dict

        Raises:
            PatternNotFoundError: If agent not found
            RuntimeError: If SocialMemory is closed
        """
        self._check_not_closed()

        # Check cache first
        cached = await self.cache.get(agent_id)
        if cached is not None:
            logger.debug(f"Cache HIT for {agent_id}")
            return cached

        # Cache miss - query database
        logger.debug(f"Cache MISS for {agent_id}")

        query = """
            SELECT patterns
            FROM social_patterns
            WHERE agent_id = $1
        """

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, agent_id)

        if row is None:
            raise PatternNotFoundError(
                f"No patterns found for agent_id: {agent_id}"
            )

        patterns = dict(row["patterns"])

        # Populate cache
        await self.cache.put(agent_id, patterns)

        return patterns

    async def update_from_interaction(
        self, agent_id: str, interaction: Dict[str, float]
    ) -> None:
        """Update patterns from new interaction using EMA.

        Formula: new_value = 0.8 * old_value + 0.2 * observed_value

        Also increments interaction_count atomically.

        Args:
            agent_id: Unique agent identifier
            interaction: New observations (e.g., {"confusion_history": 0.9})

        Raises:
            RuntimeError: If SocialMemory is closed
        """
        self._check_not_closed()

        # Retrieve current patterns
        try:
            current_patterns = await self.retrieve_patterns(agent_id)
        except PatternNotFoundError:
            # Agent doesn't exist yet - create with interaction as initial pattern
            await self.store_pattern(agent_id, interaction)
            return

        # Apply EMA (Exponential Moving Average)
        updated_patterns = current_patterns.copy()

        for key, observed_value in interaction.items():
            if key in updated_patterns:
                # EMA: 0.8 * old + 0.2 * new
                old_value = updated_patterns[key]
                updated_patterns[key] = 0.8 * old_value + 0.2 * observed_value
            else:
                # New pattern dimension - use observed value
                updated_patterns[key] = observed_value

        # Update patterns and increment interaction counter atomically
        query = """
            UPDATE social_patterns
            SET
                patterns = $2::jsonb,
                interaction_count = interaction_count + 1,
                last_updated = NOW()
            WHERE agent_id = $1
        """

        async with self.pool.acquire() as conn:
            await conn.execute(query, agent_id, updated_patterns)

        # Invalidate cache
        await self.cache.invalidate(agent_id)

        logger.debug(f"Updated pattern for {agent_id} from interaction")

    async def get_agent_stats(self, agent_id: str) -> Dict[str, Any]:
        """Get statistics for specific agent.

        Args:
            agent_id: Unique agent identifier

        Returns:
            Dict with interaction_count, last_updated, hours_since_last_update

        Raises:
            PatternNotFoundError: If agent not found
        """
        self._check_not_closed()

        query = """
            SELECT
                interaction_count,
                last_updated,
                EXTRACT(EPOCH FROM (NOW() - last_updated)) / 3600 AS hours_since_update
            FROM social_patterns
            WHERE agent_id = $1
        """

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, agent_id)

        if row is None:
            raise PatternNotFoundError(f"Agent not found: {agent_id}")

        return {
            "interaction_count": row["interaction_count"],
            "last_updated": row["last_updated"],
            "hours_since_last_update": float(row["hours_since_update"]),
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics.

        Returns:
            Dict with total_agents, cache stats, pool stats
        """
        cache_stats = self.cache.get_stats()

        # Get pool stats (if available)
        pool_stats = {}
        if self.pool:
            pool_stats = {
                "pool_size": self.pool.get_size(),
                "pool_active_connections": self.pool.get_size()
                - self.pool.get_idle_size(),
                "pool_idle_connections": self.pool.get_idle_size(),
            }

        # Note: total_agents requires a database query (expensive)
        # We'll compute it lazily only when needed
        return {
            "cache_hit_rate": cache_stats["hit_rate"],
            "cache_size": cache_stats["size"],
            "cache_hits": cache_stats["hits"],
            "cache_misses": cache_stats["misses"],
            "cache_evictions": cache_stats["evictions"],
            **pool_stats,
            "total_agents": None,  # Computed lazily via get_total_agents()
        }

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache-only statistics.

        Returns:
            Dict with cache metrics
        """
        return self.cache.get_stats()

    async def get_total_agents(self) -> int:
        """Get total number of agents in database (expensive query).

        Returns:
            Count of agents
        """
        self._check_not_closed()

        query = "SELECT COUNT(*) FROM social_patterns"

        async with self.pool.acquire() as conn:
            count = await conn.fetchval(query)

        return count

    def __repr__(self) -> str:
        """String representation."""
        status = "CLOSED" if self._closed else "OPEN"
        cache_stats = self.cache.get_stats()
        return (
            f"SocialMemory(status={status}, "
            f"cache_size={cache_stats['size']}/{self.config.cache_size}, "
            f"hit_rate={cache_stats['hit_rate']:.1%})"
        )
