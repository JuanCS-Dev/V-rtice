"""
Social Memory - SQLite Fallback Implementation
===============================================

SQLite-based implementation for development/testing when PostgreSQL unavailable.
Production systems should use PostgreSQL backend (social_memory.py).

This is a faithful implementation maintaining the same API as PostgreSQL version,
but using aiosqlite for async SQLite operations.

Authors: Claude Code (Executor Tático)
Date: 2025-10-14
Governance: Constituição Vértice v2.5 - Padrão Pagani
"""

import asyncio
import aiosqlite
import json
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


# ===========================================================================
# CONFIGURATION
# ===========================================================================

@dataclass
class SocialMemorySQLiteConfig:
    """Configuration for SQLite-based SocialMemory.

    Attributes:
        db_path: Path to SQLite database file
        cache_size: LRU cache size (number of agents)
    """

    db_path: str = ":memory:"  # In-memory by default for tests
    cache_size: int = 100


# ===========================================================================
# EXCEPTIONS
# ===========================================================================

class PatternNotFoundError(Exception):
    """Raised when pattern for agent_id is not found."""

    pass


# ===========================================================================
# LRU CACHE (Same as PostgreSQL version)
# ===========================================================================

class LRUCache:
    """LRU (Least Recently Used) cache implementation."""

    def __init__(self, capacity: int):
        if capacity < 1:
            raise ValueError(f"Cache capacity must be >= 1, got {capacity}")

        self.capacity = capacity
        self.cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        async with self._lock:
            if key in self.cache:
                self.cache.move_to_end(key)
                self.hits += 1
                return self.cache[key].copy()

            self.misses += 1
            return None

    async def put(self, key: str, value: Dict[str, Any]) -> None:
        async with self._lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            else:
                if len(self.cache) >= self.capacity:
                    self.cache.popitem(last=False)
                    self.evictions += 1

            self.cache[key] = value.copy()

    async def invalidate(self, key: str) -> None:
        async with self._lock:
            self.cache.pop(key, None)

    async def clear(self) -> None:
        async with self._lock:
            self.cache.clear()

    def get_stats(self) -> Dict[str, Any]:
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
# SOCIAL MEMORY (SQLite)
# ===========================================================================

class SocialMemorySQLite:
    """SQLite-based social memory storage (development fallback).

    API-compatible with PostgreSQL version for seamless switching.
    """

    def __init__(self, config: SocialMemorySQLiteConfig):
        self.config = config
        self.db: Optional[aiosqlite.Connection] = None
        self.cache = LRUCache(capacity=config.cache_size)
        self._closed = False

    async def initialize(self) -> None:
        """Initialize SQLite database and create schema."""
        if self._closed:
            raise RuntimeError("Cannot initialize closed SocialMemory")

        try:
            self.db = await aiosqlite.connect(self.config.db_path)
            self.db.row_factory = aiosqlite.Row

            # Create schema
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS social_patterns (
                    agent_id TEXT PRIMARY KEY,
                    patterns TEXT NOT NULL,
                    last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
                    interaction_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await self.db.execute("""
                CREATE INDEX IF NOT EXISTS idx_last_updated
                ON social_patterns(last_updated DESC)
            """)

            await self.db.commit()

            logger.info(f"SocialMemorySQLite initialized: {self.config.db_path}")

        except Exception as e:
            raise ConnectionError(f"Failed to initialize SQLite: {e}") from e

    async def close(self) -> None:
        """Close database connection (idempotent)."""
        if self._closed:
            return

        if self.db:
            await self.db.close()
            logger.info("SocialMemorySQLite closed")

        await self.cache.clear()
        self._closed = True

    def _check_not_closed(self) -> None:
        if self._closed:
            raise RuntimeError("Operation on closed SocialMemory")

    async def store_pattern(self, agent_id: str, patterns: Dict[str, Any]) -> None:
        """Store or update pattern for agent."""
        self._check_not_closed()

        patterns_json = json.dumps(patterns)

        await self.db.execute("""
            INSERT INTO social_patterns (agent_id, patterns, interaction_count)
            VALUES (?, ?, 0)
            ON CONFLICT(agent_id)
            DO UPDATE SET
                patterns = excluded.patterns,
                last_updated = CURRENT_TIMESTAMP
        """, (agent_id, patterns_json))

        await self.db.commit()
        await self.cache.invalidate(agent_id)

        logger.debug(f"Stored pattern for {agent_id}: {patterns}")

    async def retrieve_patterns(self, agent_id: str) -> Dict[str, Any]:
        """Retrieve patterns for agent (cache-aware)."""
        self._check_not_closed()

        # Check cache
        cached = await self.cache.get(agent_id)
        if cached is not None:
            logger.debug(f"Cache HIT for {agent_id}")
            return cached

        logger.debug(f"Cache MISS for {agent_id}")

        # Query database
        async with self.db.execute(
            "SELECT patterns FROM social_patterns WHERE agent_id = ?",
            (agent_id,)
        ) as cursor:
            row = await cursor.fetchone()

        if row is None:
            raise PatternNotFoundError(f"No patterns found for agent_id: {agent_id}")

        patterns = json.loads(row["patterns"])
        await self.cache.put(agent_id, patterns)

        return patterns

    async def update_from_interaction(
        self, agent_id: str, interaction: Dict[str, float]
    ) -> None:
        """Update patterns from new interaction using EMA."""
        self._check_not_closed()

        # Retrieve current patterns
        try:
            current_patterns = await self.retrieve_patterns(agent_id)
        except PatternNotFoundError:
            await self.store_pattern(agent_id, interaction)
            return

        # Apply EMA
        updated_patterns = current_patterns.copy()

        for key, observed_value in interaction.items():
            if key in updated_patterns:
                old_value = updated_patterns[key]
                updated_patterns[key] = 0.8 * old_value + 0.2 * observed_value
            else:
                updated_patterns[key] = observed_value

        # Update
        patterns_json = json.dumps(updated_patterns)

        await self.db.execute("""
            UPDATE social_patterns
            SET
                patterns = ?,
                interaction_count = interaction_count + 1,
                last_updated = CURRENT_TIMESTAMP
            WHERE agent_id = ?
        """, (patterns_json, agent_id))

        await self.db.commit()
        await self.cache.invalidate(agent_id)

        logger.debug(f"Updated pattern for {agent_id} from interaction")

    async def get_agent_stats(self, agent_id: str) -> Dict[str, Any]:
        """Get statistics for specific agent."""
        self._check_not_closed()

        async with self.db.execute("""
            SELECT
                interaction_count,
                last_updated,
                (julianday('now') - julianday(last_updated)) * 24 AS hours_since_update
            FROM social_patterns
            WHERE agent_id = ?
        """, (agent_id,)) as cursor:
            row = await cursor.fetchone()

        if row is None:
            raise PatternNotFoundError(f"Agent not found: {agent_id}")

        return {
            "interaction_count": row["interaction_count"],
            "last_updated": datetime.fromisoformat(row["last_updated"]),
            "hours_since_last_update": float(row["hours_since_update"]),
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics."""
        cache_stats = self.cache.get_stats()

        return {
            "cache_hit_rate": cache_stats["hit_rate"],
            "cache_size": cache_stats["size"],
            "cache_hits": cache_stats["hits"],
            "cache_misses": cache_stats["misses"],
            "cache_evictions": cache_stats["evictions"],
            "total_agents": None,  # Computed lazily
        }

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache-only statistics."""
        return self.cache.get_stats()

    async def get_total_agents(self) -> int:
        """Get total number of agents in database."""
        self._check_not_closed()

        async with self.db.execute("SELECT COUNT(*) FROM social_patterns") as cursor:
            row = await cursor.fetchone()
            return row[0]

    def __repr__(self) -> str:
        status = "CLOSED" if self._closed else "OPEN"
        cache_stats = self.cache.get_stats()
        return (
            f"SocialMemorySQLite(status={status}, "
            f"db={self.config.db_path}, "
            f"cache_size={cache_stats['size']}/{self.config.cache_size}, "
            f"hit_rate={cache_stats['hit_rate']:.1%})"
        )


# ===========================================================================
# FACTORY FUNCTION (Auto-detect backend)
# ===========================================================================

async def create_social_memory(use_sqlite: bool = False, **kwargs) -> Any:
    """Factory function to create appropriate SocialMemory backend.

    Args:
        use_sqlite: Force SQLite backend (default: auto-detect)
        **kwargs: Configuration parameters

    Returns:
        Initialized SocialMemory instance (PostgreSQL or SQLite)
    """
    if use_sqlite:
        config = SocialMemorySQLiteConfig(**kwargs)
        memory = SocialMemorySQLite(config)
        await memory.initialize()
        return memory

    # Try PostgreSQL first
    try:
        from compassion.social_memory import SocialMemory, SocialMemoryConfig

        config = SocialMemoryConfig(**kwargs)
        memory = SocialMemory(config)
        await memory.initialize()
        logger.info("Using PostgreSQL backend")
        return memory

    except Exception as e:
        logger.warning(f"PostgreSQL unavailable ({e}), falling back to SQLite")

        config = SocialMemorySQLiteConfig(**kwargs)
        memory = SocialMemorySQLite(config)
        await memory.initialize()
        return memory
