"""Cache Actuator - Redis Cache Management"""

import logging
import redis.asyncio as redis
from typing import Dict, List, Optional, Any
import json

logger = logging.getLogger(__name__)


class CacheActuator:
    """Manage Redis cache operations and optimization."""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        dry_run_mode: bool = True
    ):
        self.redis_url = redis_url
        self.dry_run_mode = dry_run_mode
        self.action_log = []
        self.client: Optional[redis.Redis] = None

    async def connect(self):
        """Establish Redis connection."""
        if not self.client:
            try:
                self.client = await redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                await self.client.ping()
                logger.info("Redis client connected successfully")
            except Exception as e:
                logger.error(f"Redis connection failed: {e}")
                self.client = None

    async def flush_cache(
        self,
        pattern: Optional[str] = None,
        database: int = 0
    ) -> Dict:
        """Flush cache entries matching pattern.

        Args:
            pattern: Key pattern to flush (e.g., 'user:*', 'session:*')
                    If None, flush entire database
            database: Redis database number (0-15)
        """
        await self.connect()

        if not self.client:
            return {'success': False, 'error': 'Redis client unavailable'}

        if self.dry_run_mode:
            logger.info(f"DRY-RUN: Flush cache db={database} pattern={pattern or 'ALL'}")
            self.action_log.append({
                'action': 'flush_cache',
                'pattern': pattern,
                'database': database,
                'executed': False,
                'dry_run': True
            })
            return {'success': True, 'dry_run': True}

        try:
            # Select database
            if database != 0:
                await self.client.select(database)

            if pattern:
                # Flush specific pattern
                keys = []
                async for key in self.client.scan_iter(match=pattern, count=1000):
                    keys.append(key)

                if keys:
                    deleted_count = await self.client.delete(*keys)
                else:
                    deleted_count = 0

                logger.info(f"Flushed {deleted_count} keys matching '{pattern}'")
            else:
                # Flush entire database
                await self.client.flushdb()
                deleted_count = -1  # Unknown count
                logger.info(f"Flushed entire database {database}")

            self.action_log.append({
                'action': 'flush_cache',
                'pattern': pattern,
                'database': database,
                'deleted_count': deleted_count,
                'executed': True,
                'success': True
            })

            return {
                'success': True,
                'database': database,
                'pattern': pattern,
                'deleted_count': deleted_count
            }

        except Exception as e:
            logger.error(f"Cache flush error: {e}")
            return {'success': False, 'error': str(e)}

    async def warm_cache(
        self,
        key_value_pairs: List[Dict[str, Any]],
        ttl_seconds: int = 3600
    ) -> Dict:
        """Preload cache with key-value pairs.

        Args:
            key_value_pairs: List of {'key': 'foo', 'value': {...}}
            ttl_seconds: Time to live in seconds
        """
        await self.connect()

        if not self.client:
            return {'success': False, 'error': 'Redis client unavailable'}

        if self.dry_run_mode:
            logger.info(f"DRY-RUN: Warm cache with {len(key_value_pairs)} entries (TTL={ttl_seconds}s)")
            self.action_log.append({
                'action': 'warm_cache',
                'entry_count': len(key_value_pairs),
                'ttl_seconds': ttl_seconds,
                'executed': False,
                'dry_run': True
            })
            return {'success': True, 'dry_run': True}

        try:
            pipeline = self.client.pipeline()

            for entry in key_value_pairs:
                key = entry['key']
                value = entry['value']

                # Serialize value if not string
                if not isinstance(value, str):
                    value = json.dumps(value)

                pipeline.setex(key, ttl_seconds, value)

            await pipeline.execute()

            self.action_log.append({
                'action': 'warm_cache',
                'entry_count': len(key_value_pairs),
                'ttl_seconds': ttl_seconds,
                'executed': True,
                'success': True
            })

            logger.info(f"Cache warmed with {len(key_value_pairs)} entries")

            return {
                'success': True,
                'entry_count': len(key_value_pairs),
                'ttl_seconds': ttl_seconds
            }

        except Exception as e:
            logger.error(f"Cache warming error: {e}")
            return {'success': False, 'error': str(e)}

    async def adjust_maxmemory(self, maxmemory_mb: int, policy: str = 'allkeys-lru') -> Dict:
        """Adjust Redis maxmemory and eviction policy.

        Args:
            maxmemory_mb: Maximum memory in MB (256-8192)
            policy: Eviction policy ('allkeys-lru', 'volatile-lru', 'allkeys-lfu', 'volatile-ttl')
        """
        await self.connect()

        if not self.client:
            return {'success': False, 'error': 'Redis client unavailable'}

        if self.dry_run_mode:
            logger.info(f"DRY-RUN: SET maxmemory={maxmemory_mb}MB, policy={policy}")
            self.action_log.append({
                'action': 'adjust_maxmemory',
                'maxmemory_mb': maxmemory_mb,
                'policy': policy,
                'executed': False,
                'dry_run': True
            })
            return {'success': True, 'dry_run': True}

        try:
            maxmemory_bytes = maxmemory_mb * 1024 * 1024

            # Set maxmemory
            await self.client.config_set('maxmemory', maxmemory_bytes)

            # Set eviction policy
            await self.client.config_set('maxmemory-policy', policy)

            # Persist changes
            await self.client.config_rewrite()

            self.action_log.append({
                'action': 'adjust_maxmemory',
                'maxmemory_mb': maxmemory_mb,
                'policy': policy,
                'executed': True,
                'success': True
            })

            logger.info(f"Redis maxmemory set to {maxmemory_mb}MB, policy={policy}")

            return {
                'success': True,
                'maxmemory_mb': maxmemory_mb,
                'policy': policy
            }

        except Exception as e:
            logger.error(f"Maxmemory adjustment error: {e}")
            return {'success': False, 'error': str(e)}

    async def get_cache_stats(self) -> Dict:
        """Get Redis cache statistics."""
        await self.connect()

        if not self.client:
            return {'success': False, 'error': 'Redis client unavailable'}

        try:
            info = await self.client.info()
            stats = await self.client.info('stats')

            # Memory stats
            used_memory_mb = info['used_memory'] / (1024 * 1024)
            maxmemory = info.get('maxmemory', 0)
            maxmemory_mb = maxmemory / (1024 * 1024) if maxmemory > 0 else 0
            memory_fragmentation = info.get('mem_fragmentation_ratio', 0)

            # Hit ratio
            keyspace_hits = stats.get('keyspace_hits', 0)
            keyspace_misses = stats.get('keyspace_misses', 0)
            total_requests = keyspace_hits + keyspace_misses
            hit_ratio = (keyspace_hits / total_requests * 100) if total_requests > 0 else 0

            # Key count
            db0_keys = 0
            if 'db0' in info:
                db0_keys = info['db0']['keys']

            # Eviction stats
            evicted_keys = stats.get('evicted_keys', 0)

            return {
                'success': True,
                'memory': {
                    'used_mb': round(used_memory_mb, 2),
                    'max_mb': round(maxmemory_mb, 2) if maxmemory_mb > 0 else None,
                    'fragmentation_ratio': round(memory_fragmentation, 2)
                },
                'performance': {
                    'hit_ratio_percent': round(hit_ratio, 2),
                    'hits': keyspace_hits,
                    'misses': keyspace_misses
                },
                'keys': {
                    'total': db0_keys,
                    'evicted': evicted_keys
                },
                'connections': {
                    'connected_clients': info.get('connected_clients', 0),
                    'blocked_clients': info.get('blocked_clients', 0)
                }
            }

        except Exception as e:
            logger.error(f"Stats retrieval error: {e}")
            return {'success': False, 'error': str(e)}

    async def set_cache_strategy(self, strategy: str) -> Dict:
        """Change cache strategy (aggressive, balanced, conservative).

        Args:
            strategy: 'aggressive' (80% maxmemory, allkeys-lru)
                     'balanced' (60% maxmemory, volatile-lru)
                     'conservative' (40% maxmemory, volatile-ttl)
        """
        strategies = {
            'aggressive': {
                'maxmemory_mb': 2048,  # 80% of 2.5GB
                'policy': 'allkeys-lru',
                'ttl_seconds': 3600
            },
            'balanced': {
                'maxmemory_mb': 1536,  # 60% of 2.5GB
                'policy': 'volatile-lru',
                'ttl_seconds': 1800
            },
            'conservative': {
                'maxmemory_mb': 1024,  # 40% of 2.5GB
                'policy': 'volatile-ttl',
                'ttl_seconds': 900
            }
        }

        if strategy not in strategies:
            return {'success': False, 'error': f'Invalid strategy: {strategy}'}

        config = strategies[strategy]

        result = await self.adjust_maxmemory(
            config['maxmemory_mb'],
            config['policy']
        )

        if result['success']:
            logger.info(f"Cache strategy set to '{strategy}'")
            return {
                'success': True,
                'strategy': strategy,
                'maxmemory_mb': config['maxmemory_mb'],
                'policy': config['policy'],
                'default_ttl_seconds': config['ttl_seconds']
            }
        else:
            return result

    async def close(self):
        """Close Redis connection."""
        if self.client:
            await self.client.close()

    def get_action_log(self) -> List[Dict]:
        """Return action history for audit."""
        return self.action_log
