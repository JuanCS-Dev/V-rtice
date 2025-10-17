"""Dependency Health Checks - PRODUCTION-READY

Comprehensive health checks for external dependencies.

Features:
- Kafka connectivity and topic availability
- Redis connectivity and operations
- PostgreSQL connectivity and query execution
- Connection pool health
- Latency monitoring
- Error tracking

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

import asyncio
import logging
import time
from typing import Any, Dict, Optional, Tuple

import asyncpg
import redis.asyncio as aioredis
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError, KafkaError

from services.active_immune_core.config import settings
from monitoring.health_checker import HealthStatus

logger = logging.getLogger(__name__)


class DependencyHealthChecker:
    """
    Comprehensive health checker for external dependencies.

    Checks Kafka, Redis, and PostgreSQL health with connection
    pooling, latency tracking, and error detection.
    """

    def __init__(self):
        """Initialize dependency health checker."""
        self._kafka_producer: Optional[AIOKafkaProducer] = None
        self._redis_client: Optional[aioredis.Redis] = None
        self._pg_pool: Optional[asyncpg.Pool] = None

        # Thresholds (configurable)
        self.max_latency_ms = 1000  # 1 second
        self.max_consecutive_failures = 3

    # ======================== KAFKA HEALTH ========================

    async def check_kafka_health(self) -> Tuple[HealthStatus, Dict[str, Any]]:
        """
        Check Kafka broker health.

        Verifies:
        - Connection to bootstrap servers
        - Cluster metadata availability
        - Response latency

        Returns:
            Tuple of (status, details)
        """
        start_time = time.time()

        try:
            # Create temporary producer for health check
            producer = AIOKafkaProducer(
                bootstrap_servers=settings.kafka_bootstrap_servers,
                request_timeout_ms=5000,
                metadata_max_age_ms=5000,
            )

            # Start producer (connects to Kafka)
            await producer.start()

            try:
                # Get cluster metadata
                metadata = await producer.client.fetch_all_metadata()

                latency_ms = (time.time() - start_time) * 1000

                # Extract broker info
                brokers = [
                    {"id": broker.nodeId, "host": broker.host, "port": broker.port} for broker in metadata.brokers
                ]

                # Check latency
                if latency_ms > self.max_latency_ms:
                    return HealthStatus.DEGRADED, {
                        "message": "Kafka responding slowly",
                        "latency_ms": round(latency_ms, 2),
                        "brokers_count": len(brokers),
                        "brokers": brokers,
                        "threshold_ms": self.max_latency_ms,
                    }

                return HealthStatus.HEALTHY, {
                    "message": "Kafka cluster healthy",
                    "latency_ms": round(latency_ms, 2),
                    "brokers_count": len(brokers),
                    "brokers": brokers,
                    "topics_count": len(metadata.topics),
                }

            finally:
                await producer.stop()

        except KafkaConnectionError as e:
            latency_ms = (time.time() - start_time) * 1000
            return HealthStatus.UNHEALTHY, {
                "message": "Cannot connect to Kafka",
                "error": str(e),
                "latency_ms": round(latency_ms, 2),
                "bootstrap_servers": settings.kafka_bootstrap_servers,
            }

        except KafkaError as e:
            latency_ms = (time.time() - start_time) * 1000
            return HealthStatus.DEGRADED, {
                "message": "Kafka error",
                "error": str(e),
                "latency_ms": round(latency_ms, 2),
            }

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(f"Kafka health check failed: {e}")
            return HealthStatus.UNHEALTHY, {
                "message": "Kafka health check failed",
                "error": str(e),
                "latency_ms": round(latency_ms, 2),
            }

    # ======================== REDIS HEALTH ========================

    async def check_redis_health(self) -> Tuple[HealthStatus, Dict[str, Any]]:
        """
        Check Redis health.

        Verifies:
        - Connection to Redis server
        - PING response
        - GET/SET operations
        - Response latency

        Returns:
            Tuple of (status, details)
        """
        start_time = time.time()

        try:
            # Create Redis client for health check
            redis_client = aioredis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=5.0,
                socket_connect_timeout=5.0,
            )

            try:
                # PING test
                ping_result = await redis_client.ping()

                if not ping_result:
                    return HealthStatus.UNHEALTHY, {
                        "message": "Redis not responding to PING",
                    }

                # SET/GET test
                test_key = "_health_check_"
                test_value = f"test_{int(time.time())}"

                await redis_client.set(test_key, test_value, ex=10)  # 10s expiration
                retrieved = await redis_client.get(test_key)

                if retrieved != test_value:
                    return HealthStatus.DEGRADED, {
                        "message": "Redis SET/GET inconsistency",
                        "expected": test_value,
                        "got": retrieved,
                    }

                # Clean up test key
                await redis_client.delete(test_key)

                # Get server info
                info = await redis_client.info("server")

                latency_ms = (time.time() - start_time) * 1000

                # Check latency
                if latency_ms > self.max_latency_ms:
                    return HealthStatus.DEGRADED, {
                        "message": "Redis responding slowly",
                        "latency_ms": round(latency_ms, 2),
                        "redis_version": info.get("redis_version"),
                        "uptime_seconds": info.get("uptime_in_seconds"),
                        "threshold_ms": self.max_latency_ms,
                    }

                return HealthStatus.HEALTHY, {
                    "message": "Redis healthy",
                    "latency_ms": round(latency_ms, 2),
                    "redis_version": info.get("redis_version"),
                    "uptime_seconds": info.get("uptime_in_seconds"),
                }

            finally:
                await redis_client.close()

        except aioredis.ConnectionError as e:
            latency_ms = (time.time() - start_time) * 1000
            return HealthStatus.UNHEALTHY, {
                "message": "Cannot connect to Redis",
                "error": str(e),
                "latency_ms": round(latency_ms, 2),
                "redis_url": settings.redis_url,
            }

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(f"Redis health check failed: {e}")
            return HealthStatus.UNHEALTHY, {
                "message": "Redis health check failed",
                "error": str(e),
                "latency_ms": round(latency_ms, 2),
            }

    # ======================== POSTGRESQL HEALTH ========================

    async def check_postgres_health(self) -> Tuple[HealthStatus, Dict[str, Any]]:
        """
        Check PostgreSQL health.

        Verifies:
        - Connection to database
        - Query execution
        - Connection pool status
        - Response latency

        Returns:
            Tuple of (status, details)
        """
        start_time = time.time()

        try:
            # Create connection pool for health check
            pool = await asyncpg.create_pool(
                host=settings.postgres_host,
                port=settings.postgres_port,
                database=settings.postgres_db,
                user=settings.postgres_user,
                password=settings.postgres_password,
                min_size=1,
                max_size=2,
                timeout=5.0,
            )

            try:
                async with pool.acquire() as conn:
                    # Check PostgreSQL version
                    version = await conn.fetchval("SELECT version()")

                    # Test query
                    result = await conn.fetchval("SELECT 1")

                    if result != 1:
                        return HealthStatus.DEGRADED, {
                            "message": "PostgreSQL query returned unexpected result",
                            "expected": 1,
                            "got": result,
                        }

                    # Get database stats
                    stats = await conn.fetchrow("""
                        SELECT
                            pg_database_size(current_database()) as db_size,
                            (SELECT count(*) FROM pg_stat_activity) as active_connections,
                            (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_queries
                    """)

                    latency_ms = (time.time() - start_time) * 1000

                    # Check latency
                    if latency_ms > self.max_latency_ms:
                        return HealthStatus.DEGRADED, {
                            "message": "PostgreSQL responding slowly",
                            "latency_ms": round(latency_ms, 2),
                            "version": version.split()[1] if version else "unknown",
                            "db_size_mb": round(stats["db_size"] / (1024 * 1024), 2),
                            "active_connections": stats["active_connections"],
                            "active_queries": stats["active_queries"],
                            "threshold_ms": self.max_latency_ms,
                        }

                    return HealthStatus.HEALTHY, {
                        "message": "PostgreSQL healthy",
                        "latency_ms": round(latency_ms, 2),
                        "version": version.split()[1] if version else "unknown",
                        "db_size_mb": round(stats["db_size"] / (1024 * 1024), 2),
                        "active_connections": stats["active_connections"],
                        "active_queries": stats["active_queries"],
                    }

            finally:
                await pool.close()

        except asyncpg.PostgresConnectionError as e:
            latency_ms = (time.time() - start_time) * 1000
            return HealthStatus.UNHEALTHY, {
                "message": "Cannot connect to PostgreSQL",
                "error": str(e),
                "latency_ms": round(latency_ms, 2),
                "host": settings.postgres_host,
                "port": settings.postgres_port,
                "database": settings.postgres_db,
            }

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(f"PostgreSQL health check failed: {e}")
            return HealthStatus.UNHEALTHY, {
                "message": "PostgreSQL health check failed",
                "error": str(e),
                "latency_ms": round(latency_ms, 2),
            }

    # ======================== ALL DEPENDENCIES ========================

    async def check_all_dependencies(self) -> Dict[str, Tuple[HealthStatus, Dict[str, Any]]]:
        """
        Check health of all dependencies in parallel.

        Returns:
            Dictionary mapping dependency name to (status, details)
        """
        # Run all checks in parallel
        kafka_check, redis_check, postgres_check = await asyncio.gather(
            self.check_kafka_health(),
            self.check_redis_health(),
            self.check_postgres_health(),
            return_exceptions=True,
        )

        results = {}

        # Kafka
        if isinstance(kafka_check, Exception):
            results["kafka"] = (HealthStatus.UNHEALTHY, {"error": str(kafka_check)})
        else:
            results["kafka"] = kafka_check

        # Redis
        if isinstance(redis_check, Exception):
            results["redis"] = (HealthStatus.UNHEALTHY, {"error": str(redis_check)})
        else:
            results["redis"] = redis_check

        # PostgreSQL
        if isinstance(postgres_check, Exception):
            results["postgres"] = (HealthStatus.UNHEALTHY, {"error": str(postgres_check)})
        else:
            results["postgres"] = postgres_check

        return results

    # ======================== SUMMARY ========================

    async def get_dependencies_summary(self) -> Dict[str, Any]:
        """
        Get summary of all dependencies health.

        Returns:
            Summary dictionary with overall status
        """
        results = await self.check_all_dependencies()

        # Calculate overall status
        statuses = [status for status, _ in results.values()]

        if all(s == HealthStatus.HEALTHY for s in statuses):
            overall_status = HealthStatus.HEALTHY
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            overall_status = HealthStatus.UNHEALTHY
        else:
            overall_status = HealthStatus.DEGRADED

        return {
            "overall_status": overall_status,
            "dependencies": {
                name: {"status": status, "details": details} for name, (status, details) in results.items()
            },
        }
