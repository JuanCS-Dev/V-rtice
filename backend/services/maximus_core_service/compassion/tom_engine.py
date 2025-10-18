"""
Theory of Mind (ToM) Engine - Complete Implementation
======================================================

Integrates all ToM components:
- Social Memory (persistent belief storage)
- Confidence Tracker (temporal decay)
- Contradiction Detector (belief validation)
- Sally-Anne Benchmark (accuracy validation)

Implements complete ToM inference pipeline for MAXIMUS Organismo.

Authors: Claude Code (Executor Tático)
Date: 2025-10-14
Governance: Constituição Vértice v2.5 - Padrão Pagani
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import json

from compassion.social_memory_sqlite import (
    SocialMemorySQLite,
    SocialMemorySQLiteConfig,
    PatternNotFoundError,
)
from compassion.confidence_tracker import ConfidenceTracker
from compassion.contradiction_detector import ContradictionDetector

logger = logging.getLogger(__name__)

# Optional Redis import
try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("redis not available - ToM caching disabled")


class ToMEngine:
    """Complete Theory of Mind engine for mental state inference.

    Combines social memory, confidence tracking, and contradiction detection
    to build robust models of other agents' beliefs, intentions, and knowledge.

    Key Capabilities:
    - False belief tracking (Sally-Anne scenarios)
    - Confidence decay over time
    - Contradiction detection
    - Persistent social memory

    Attributes:
        social_memory: Persistent storage for agent beliefs
        confidence_tracker: Temporal decay for belief confidence
        contradiction_detector: Validation for belief updates
    """

    def __init__(
        self,
        db_path: str = ":memory:",
        cache_size: int = 100,
        decay_lambda: float = 0.01,
        contradiction_threshold: float = 0.5,
        redis_url: Optional[str] = None,
        redis_ttl: int = 60,
    ):
        """Initialize ToM Engine with all components.

        Args:
            db_path: SQLite database path (default: in-memory)
            cache_size: LRU cache capacity
            decay_lambda: Confidence decay rate per hour
            contradiction_threshold: Minimum delta for contradiction detection
            redis_url: Redis URL for caching (e.g., "redis://localhost:6379")
            redis_ttl: Redis cache TTL in seconds (default: 60)
        """
        # Social Memory (FASE 1)
        config = SocialMemorySQLiteConfig(db_path=db_path, cache_size=cache_size)
        self.social_memory = SocialMemorySQLite(config)

        # Confidence Tracker (FASE 2)
        self.confidence_tracker = ConfidenceTracker(
            decay_lambda=decay_lambda, min_confidence=0.1
        )

        # Contradiction Detector (FASE 2)
        self.contradiction_detector = ContradictionDetector(
            threshold=contradiction_threshold
        )

        # Redis caching (optional)
        self.redis_url = redis_url
        self.redis_ttl = redis_ttl
        self.redis: Optional[aioredis.Redis] = None
        self._redis_enabled = False

        # Cache statistics
        self.cache_hits = 0
        self.cache_misses = 0

        self._initialized = False

        logger.info(
            f"ToMEngine created: db={db_path}, cache={cache_size}, "
            f"λ={decay_lambda}, threshold={contradiction_threshold}, "
            f"redis={'enabled' if redis_url else 'disabled'}"
        )

    async def initialize(self) -> None:
        """Initialize ToM Engine (async setup)."""
        if self._initialized:
            logger.warning("ToMEngine already initialized")
            return

        await self.social_memory.initialize()

        # Initialize Redis if configured
        if self.redis_url and REDIS_AVAILABLE:
            try:
                self.redis = aioredis.from_url(self.redis_url, decode_responses=True)
                # Test connection
                await self.redis.ping()
                self._redis_enabled = True
                logger.info(f"Redis cache enabled: {self.redis_url}, TTL={self.redis_ttl}s")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}, continuing without cache")
                self.redis = None
                self._redis_enabled = False

        self._initialized = True

        logger.info("ToMEngine initialized successfully")

    async def close(self) -> None:
        """Close ToM Engine and cleanup resources."""
        if not self._initialized:
            return

        await self.social_memory.close()

        # Close Redis connection
        if self.redis:
            await self.redis.close()
            logger.info("Redis connection closed")

        self._initialized = False

        logger.info("ToMEngine closed")

    def _check_initialized(self) -> None:
        """Check engine is initialized, raise if not."""
        if not self._initialized:
            raise RuntimeError("ToMEngine not initialized. Call initialize() first.")

    async def infer_belief(
        self, agent_id: str, belief_key: str, observed_value: float
    ) -> Dict[str, Any]:
        """Infer and update belief for an agent.

        Args:
            agent_id: Unique agent identifier
            belief_key: Belief identifier (e.g., "knows_marble_location")
            observed_value: Observed belief value [0.0, 1.0]

        Returns:
            Inference result with belief, confidence, and contradiction flag
        """
        self._check_initialized()

        # Get current belief (if exists)
        try:
            current_beliefs = await self.social_memory.retrieve_patterns(agent_id)
            old_value = current_beliefs.get(belief_key, 0.5)  # Default: uncertain
        except PatternNotFoundError:
            old_value = 0.5  # No prior belief

        # Check for contradiction
        contradiction_detected = await self.contradiction_detector.record_update(
            agent_id, belief_key, old_value, observed_value
        )

        # Update belief in social memory (EMA)
        await self.social_memory.update_from_interaction(
            agent_id, {belief_key: observed_value}
        )

        # Record timestamp for confidence tracking
        await self.confidence_tracker.record_belief(
            agent_id, belief_key, observed_value
        )

        # Calculate confidence
        confidence = self.confidence_tracker.calculate_confidence(agent_id, belief_key)

        # Get updated belief from memory
        updated_beliefs = await self.social_memory.retrieve_patterns(agent_id)
        final_value = updated_beliefs[belief_key]

        result = {
            "agent_id": agent_id,
            "belief_key": belief_key,
            "old_value": old_value,
            "observed_value": observed_value,
            "updated_value": final_value,
            "confidence": confidence,
            "contradiction": contradiction_detected,
            "timestamp": datetime.utcnow(),
        }

        logger.info(
            f"Belief inferred: agent={agent_id}, key={belief_key}, "
            f"value={final_value:.2f}, confidence={confidence:.2f}, "
            f"contradiction={contradiction_detected}"
        )

        return result

    async def get_agent_beliefs(
        self, agent_id: str, include_confidence: bool = True
    ) -> Dict[str, Any]:
        """Get all beliefs for an agent with confidence scores.

        Args:
            agent_id: Agent identifier
            include_confidence: Include confidence scores

        Returns:
            Dictionary with beliefs and optional confidence scores
        """
        self._check_initialized()

        # Try Redis cache first
        if self._redis_enabled:
            cache_key = f"tom:beliefs:{agent_id}:{include_confidence}"
            try:
                cached = await self.redis.get(cache_key)
                if cached:
                    self.cache_hits += 1
                    return json.loads(cached)
                else:
                    self.cache_misses += 1
            except Exception as e:
                logger.debug(f"Redis cache read failed: {e}")
                # Continue without cache

        # Cache miss - compute from database
        try:
            beliefs = await self.social_memory.retrieve_patterns(agent_id)
        except PatternNotFoundError:
            return {}

        if not include_confidence:
            result = beliefs
        else:
            # Add confidence scores
            result = {}
            for belief_key, value in beliefs.items():
                confidence = self.confidence_tracker.calculate_confidence(
                    agent_id, belief_key
                )
                result[belief_key] = {"value": value, "confidence": confidence}

        # Store in Redis cache
        if self._redis_enabled and result:
            cache_key = f"tom:beliefs:{agent_id}:{include_confidence}"
            try:
                await self.redis.setex(
                    cache_key,
                    self.redis_ttl,
                    json.dumps(result)
                )
            except Exception as e:
                logger.debug(f"Redis cache write failed: {e}")

        return result

    async def predict_action(
        self, agent_id: str, belief_key: str, scenarios: Dict[str, float]
    ) -> str:
        """Predict agent's action based on their belief.

        Args:
            agent_id: Agent identifier
            belief_key: Belief to use for prediction
            scenarios: Map of action → belief_value_required

        Returns:
            Predicted action (key from scenarios)
        """
        self._check_initialized()

        try:
            beliefs = await self.social_memory.retrieve_patterns(agent_id)
            belief_value = beliefs.get(belief_key, 0.5)
        except PatternNotFoundError:
            belief_value = 0.5  # Uncertain

        # Find closest matching scenario
        best_action = None
        min_distance = float("inf")

        for action, required_value in scenarios.items():
            distance = abs(belief_value - required_value)
            if distance < min_distance:
                min_distance = distance
                best_action = action

        logger.info(
            f"Action predicted: agent={agent_id}, belief_key={belief_key}, "
            f"belief_value={belief_value:.2f}, action={best_action}"
        )

        return best_action

    def get_contradictions(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get all contradictions detected for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            List of contradiction records
        """
        return self.contradiction_detector.get_contradictions(agent_id)

    def get_contradiction_rate(self, agent_id: str) -> float:
        """Get contradiction rate for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Contradiction rate [0.0, 1.0]
        """
        return self.contradiction_detector.get_contradiction_rate(agent_id)

    async def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive ToM Engine statistics.

        Returns:
            Statistics dictionary
        """
        self._check_initialized()

        memory_stats = self.social_memory.get_stats()
        total_agents = await self.social_memory.get_total_agents()
        contradiction_stats = self.contradiction_detector.get_stats()

        # Calculate Redis cache hit rate
        total_cache_requests = self.cache_hits + self.cache_misses
        cache_hit_rate = (
            self.cache_hits / total_cache_requests
            if total_cache_requests > 0
            else 0.0
        )

        stats = {
            "total_agents": total_agents,
            "memory": {
                "cache_hit_rate": memory_stats["cache_hit_rate"],
                "cache_size": memory_stats["cache_size"],
            },
            "contradictions": {
                "total": contradiction_stats["total_contradictions"],
                "rate": contradiction_stats["global_contradiction_rate"],
            },
        }

        # Add Redis cache stats if enabled
        if self._redis_enabled:
            stats["redis_cache"] = {
                "enabled": True,
                "hits": self.cache_hits,
                "misses": self.cache_misses,
                "hit_rate": cache_hit_rate,
                "ttl_seconds": self.redis_ttl,
            }
        else:
            stats["redis_cache"] = {"enabled": False}

        return stats

    def __repr__(self) -> str:
        status = "INITIALIZED" if self._initialized else "NOT_INITIALIZED"
        return f"ToMEngine(status={status})"
