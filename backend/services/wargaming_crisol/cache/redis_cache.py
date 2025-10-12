"""
Redis caching layer for Wargaming Service.

Caches:
- ML predictions (TTL: 24h)
- A/B test results (TTL: 1h)
- Confusion matrix (TTL: 5min)
- APV vulnerability patterns (TTL: 12h)

Performance Target: <5ms cache hit

Fundamentação: Biological immune memory - rapid recall of previous encounters.
Digital equivalent: Redis cache for instant pattern recognition.
"""

from typing import Optional, Any, Dict
import json
import hashlib
from datetime import timedelta
import logging

try:
    import redis.asyncio as redis
except ImportError:
    # Fallback for older redis-py
    import redis
    redis.asyncio = redis

logger = logging.getLogger(__name__)


class WarGamingCache:
    """
    Async Redis cache for wargaming operations.
    
    Implements biological immune memory patterns:
    - Fast recall (<5ms) of previous validations
    - Automatic decay (TTL) like biological memory consolidation
    - Pattern-based retrieval similar to antigen recognition
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379/2"):
        """
        Initialize cache client.
        
        Args:
            redis_url: Redis connection URL with database selection
        """
        self.redis_url = redis_url
        self.client: Optional[redis.Redis] = None
    
    async def connect(self) -> None:
        """
        Initialize Redis connection pool.
        
        Raises:
            redis.ConnectionError: If cannot connect to Redis
        """
        try:
            self.client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=50  # Connection pooling for high throughput
            )
            # Test connection
            await self.client.ping()
            logger.info("✓ Redis cache connected (Phase 5.7.1)")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            raise
    
    async def close(self) -> None:
        """Close Redis connection gracefully."""
        if self.client:
            await self.client.close()
            logger.info("✓ Redis cache closed")
    
    def _make_key(self, prefix: str, identifier: str) -> str:
        """
        Generate namespaced cache key.
        
        Args:
            prefix: Key category (ml_pred, confusion, etc.)
            identifier: Unique identifier within category
            
        Returns:
            Namespaced key string
        """
        return f"wargaming:{prefix}:{identifier}"
    
    async def get_ml_prediction(self, apv_id: str) -> Optional[Dict]:
        """
        Retrieve cached ML prediction.
        
        Args:
            apv_id: APV identifier
            
        Returns:
            Cached prediction dict or None if not cached
        """
        if not self.client:
            return None
            
        key = self._make_key("ml_pred", apv_id)
        
        try:
            cached = await self.client.get(key)
            if cached:
                logger.debug(f"Cache hit: {key}")
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache get failed: {e}")
        
        return None
    
    async def set_ml_prediction(
        self, 
        apv_id: str, 
        prediction: Dict,
        ttl: timedelta = timedelta(hours=24)
    ) -> None:
        """
        Cache ML prediction.
        
        Args:
            apv_id: APV identifier
            prediction: Prediction result dict
            ttl: Time-to-live (default 24h)
        """
        if not self.client:
            return
            
        key = self._make_key("ml_pred", apv_id)
        
        try:
            await self.client.setex(
                key,
                int(ttl.total_seconds()),
                json.dumps(prediction)
            )
            logger.debug(f"Cache set: {key} (TTL: {ttl})")
        except Exception as e:
            logger.warning(f"Cache set failed: {e}")
    
    async def get_confusion_matrix(self, model_version: str) -> Optional[Dict]:
        """
        Retrieve cached confusion matrix.
        
        Args:
            model_version: ML model version identifier
            
        Returns:
            Cached confusion matrix or None
        """
        if not self.client:
            return None
            
        key = self._make_key("confusion", model_version)
        
        try:
            cached = await self.client.get(key)
            if cached:
                logger.debug(f"Cache hit: confusion matrix {model_version}")
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache get failed: {e}")
        
        return None
    
    async def set_confusion_matrix(
        self,
        model_version: str,
        matrix: Dict,
        ttl: timedelta = timedelta(minutes=5)
    ) -> None:
        """
        Cache confusion matrix (short TTL for near-realtime).
        
        Args:
            model_version: ML model version
            matrix: Confusion matrix data
            ttl: Time-to-live (default 5min for freshness)
        """
        if not self.client:
            return
            
        key = self._make_key("confusion", model_version)
        
        try:
            await self.client.setex(
                key,
                int(ttl.total_seconds()),
                json.dumps(matrix)
            )
            logger.debug(f"Cache set: confusion matrix {model_version} (TTL: {ttl})")
        except Exception as e:
            logger.warning(f"Cache set failed: {e}")
    
    async def get_vulnerability_pattern(self, pattern_hash: str) -> Optional[Dict]:
        """
        Retrieve cached vulnerability pattern analysis.
        
        Args:
            pattern_hash: Hash of vulnerability pattern
            
        Returns:
            Cached pattern analysis or None
        """
        if not self.client:
            return None
            
        key = self._make_key("vuln_pattern", pattern_hash)
        
        try:
            cached = await self.client.get(key)
            if cached:
                logger.debug(f"Cache hit: pattern {pattern_hash[:8]}...")
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache get failed: {e}")
        
        return None
    
    async def set_vulnerability_pattern(
        self,
        pattern: Dict,
        ttl: timedelta = timedelta(hours=12)
    ) -> str:
        """
        Cache vulnerability pattern.
        
        Args:
            pattern: Vulnerability pattern data
            ttl: Time-to-live (default 12h)
            
        Returns:
            Pattern hash used as key
        """
        if not self.client:
            return ""
            
        # Hash pattern for key
        pattern_str = json.dumps(pattern, sort_keys=True)
        pattern_hash = hashlib.sha256(pattern_str.encode()).hexdigest()[:16]
        
        key = self._make_key("vuln_pattern", pattern_hash)
        
        try:
            await self.client.setex(
                key,
                int(ttl.total_seconds()),
                json.dumps(pattern)
            )
            logger.debug(f"Cache set: pattern {pattern_hash[:8]}... (TTL: {ttl})")
        except Exception as e:
            logger.warning(f"Cache set failed: {e}")
        
        return pattern_hash
    
    async def invalidate_ml_cache(self, apv_id: Optional[str] = None) -> int:
        """
        Invalidate ML prediction cache.
        
        Use cases:
        - Model retraining (invalidate all)
        - APV update (invalidate specific)
        
        Args:
            apv_id: Specific APV to invalidate, or None for all
            
        Returns:
            Number of keys deleted
        """
        if not self.client:
            return 0
            
        try:
            if apv_id:
                # Invalidate specific
                key = self._make_key("ml_pred", apv_id)
                deleted = await self.client.delete(key)
                logger.info(f"Cache invalidated: {key}")
                return deleted
            else:
                # Invalidate all ML predictions
                pattern = self._make_key("ml_pred", "*")
                keys = []
                
                # Scan for keys matching pattern
                cursor = 0
                while True:
                    cursor, batch = await self.client.scan(
                        cursor, 
                        match=pattern, 
                        count=100
                    )
                    keys.extend(batch)
                    
                    if cursor == 0:
                        break
                
                if keys:
                    deleted = await self.client.delete(*keys)
                    logger.info(f"Cache invalidated: {deleted} ML predictions")
                    return deleted
                
                return 0
        except Exception as e:
            logger.error(f"Cache invalidation failed: {e}")
            return 0
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Retrieve cache statistics.
        
        Returns:
            Dict with cache metrics (memory, hits, misses, etc.)
        """
        if not self.client:
            return {"error": "Client not connected"}
        
        try:
            info = await self.client.info("stats")
            return {
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_ratio": info.get("keyspace_hits", 0) / max(
                    info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 
                    1
                ),
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "unknown")
            }
        except Exception as e:
            logger.error(f"Cache stats retrieval failed: {e}")
            return {"error": str(e)}


# Global cache instance
cache = WarGamingCache()
