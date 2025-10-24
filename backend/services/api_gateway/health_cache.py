"""
Health Check Caching Layer - 3-Layer Architecture

This module provides intelligent health check caching with:
- Layer 1: Local in-memory cache (5s TTL) - Ultra-fast
- Layer 2: Redis shared cache (30s TTL) - Cross-instance
- Layer 3: Circuit breaker per service - Fail-fast

Performance Targets:
- p50 latency: <1ms (cache hit)
- p99 latency: <2ms (local cache)
- Cache hit rate: >80%

Author: Vértice Team
Glory to YHWH! 🙏
"""

import asyncio
import enum
import logging
import time
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

import httpx
from cachetools import TTLCache
from prometheus_client import Counter, Gauge, Histogram

logger = logging.getLogger(__name__)

# Cache TTLs
LOCAL_CACHE_TTL = 5  # seconds - ultra-fast local cache
REDIS_CACHE_TTL = 30  # seconds - shared cache
HEALTH_CHECK_TIMEOUT = 2  # seconds - health check timeout

# Circuit breaker configuration
CIRCUIT_BREAKER_THRESHOLD = 3  # failures to open circuit
CIRCUIT_OPEN_TIMEOUT = 30  # seconds before HALF_OPEN
CIRCUIT_HALF_OPEN_TIMEOUT = 10  # seconds in HALF_OPEN

# Prometheus Metrics
health_cache_hits = Counter(
    'health_cache_hits_total',
    'Total health cache hits',
    ['cache_layer']
)
health_cache_misses = Counter(
    'health_cache_misses_total',
    'Total health cache misses'
)
health_check_duration = Histogram(
    'health_check_duration_seconds',
    'Health check duration',
    ['service_name', 'result'],
    buckets=[0.001, 0.002, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0]
)
health_circuit_breaker_state = Gauge(
    'health_circuit_breaker_state',
    'Circuit breaker state (0=CLOSED, 1=OPEN, 2=HALF_OPEN)',
    ['service_name']
)


class CircuitState(enum.Enum):
    """Circuit breaker states."""
    CLOSED = 0      # Normal operation
    OPEN = 1        # Failing, return cached/degraded
    HALF_OPEN = 2   # Testing recovery


@dataclass
class HealthStatus:
    """Health check result."""
    healthy: bool
    status_code: int
    response_time_ms: float
    timestamp: float
    cached: bool = False
    cache_layer: Optional[str] = None


class ServiceCircuitBreaker:
    """Per-service circuit breaker for health checks."""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.opened_at = 0.0
        self.last_check = 0.0

    def record_success(self):
        """Record successful health check."""
        if self.state == CircuitState.CLOSED:
            self.failure_count = 0
        elif self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= 2:
                self._transition_to_closed()

    def record_failure(self):
        """Record failed health check."""
        if self.state == CircuitState.CLOSED:
            self.failure_count += 1
            if self.failure_count >= CIRCUIT_BREAKER_THRESHOLD:
                self._transition_to_open()
        elif self.state == CircuitState.HALF_OPEN:
            self._transition_to_open()

    def should_attempt_check(self) -> bool:
        """Check if health check should be attempted."""
        now = time.time()

        if self.state == CircuitState.CLOSED:
            return True

        elif self.state == CircuitState.OPEN:
            # Check if we should transition to HALF_OPEN
            if now - self.opened_at >= CIRCUIT_OPEN_TIMEOUT:
                self._transition_to_half_open()
                return True
            return False

        elif self.state == CircuitState.HALF_OPEN:
            # Allow test requests
            return True

        return False

    def _transition_to_closed(self):
        """Transition to CLOSED (normal operation)."""
        logger.info(f"Circuit breaker {self.service_name}: {self.state.name} → CLOSED")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        health_circuit_breaker_state.labels(service_name=self.service_name).set(0)

    def _transition_to_open(self):
        """Transition to OPEN (failing)."""
        logger.warning(
            f"🔴 Circuit breaker {self.service_name}: {self.state.name} → OPEN "
            f"(failures: {self.failure_count})"
        )
        self.state = CircuitState.OPEN
        self.opened_at = time.time()
        self.success_count = 0
        health_circuit_breaker_state.labels(service_name=self.service_name).set(1)

    def _transition_to_half_open(self):
        """Transition to HALF_OPEN (testing recovery)."""
        logger.info(f"🟡 Circuit breaker {self.service_name}: OPEN → HALF_OPEN (testing)")
        self.state = CircuitState.HALF_OPEN
        self.failure_count = 0
        self.success_count = 0
        health_circuit_breaker_state.labels(service_name=self.service_name).set(2)


class HealthCheckCache:
    """3-Layer health check cache with circuit breakers."""

    def __init__(self, redis_client=None):
        """
        Initialize health check cache.

        Args:
            redis_client: Optional Redis client for Layer 2 cache
        """
        # Layer 1: Local in-memory cache (5s TTL)
        self._local_cache: TTLCache = TTLCache(maxsize=500, ttl=LOCAL_CACHE_TTL)

        # Layer 2: Redis shared cache (optional)
        self._redis = redis_client

        # Circuit breakers per service
        self._circuit_breakers: Dict[str, ServiceCircuitBreaker] = {}

        # HTTP client for health checks
        self._http_client = httpx.AsyncClient(timeout=HEALTH_CHECK_TIMEOUT)

        logger.info("✅ Health Check Cache initialized (3-layer architecture)")

    async def get_health(
        self,
        service_name: str,
        service_url: str,
        health_endpoint: str = "/health"
    ) -> HealthStatus:
        """
        Get service health with 3-layer caching.

        Resolution order:
        1. Local cache (5s TTL) - <1ms
        2. Redis cache (30s TTL) - <5ms
        3. Direct health check - <2s
        4. Circuit breaker fallback - <1ms

        Args:
            service_name: Service identifier
            service_url: Service base URL
            health_endpoint: Health check endpoint path

        Returns:
            HealthStatus with health information
        """
        start_time = time.time()

        # Layer 1: Local cache lookup (fastest)
        cache_key = f"health:{service_name}"
        if cache_key in self._local_cache:
            health_cache_hits.labels(cache_layer="local").inc()
            status = self._local_cache[cache_key]
            logger.debug(f"Cache HIT (local): {service_name} - {status.healthy}")
            return status

        # Layer 2: Redis cache lookup (if available)
        if self._redis:
            redis_status = await self._get_from_redis(service_name)
            if redis_status:
                health_cache_hits.labels(cache_layer="redis").inc()
                # Promote to local cache
                self._local_cache[cache_key] = redis_status
                logger.debug(f"Cache HIT (redis): {service_name} - {redis_status.healthy}")
                return redis_status

        # Cache miss - need to perform health check
        health_cache_misses.inc()

        # Get or create circuit breaker
        circuit_breaker = self._get_circuit_breaker(service_name)

        # Check circuit breaker state
        if not circuit_breaker.should_attempt_check():
            # Circuit is OPEN - return degraded/cached status
            logger.warning(f"Circuit OPEN for {service_name}, returning degraded status")
            duration_ms = (time.time() - start_time) * 1000
            health_check_duration.labels(
                service_name=service_name,
                result="circuit_open"
            ).observe(time.time() - start_time)

            return HealthStatus(
                healthy=False,
                status_code=503,
                response_time_ms=duration_ms,
                timestamp=time.time(),
                cached=False
            )

        # Layer 3: Perform actual health check
        health_status = await self._perform_health_check(
            service_name,
            service_url,
            health_endpoint,
            circuit_breaker
        )

        # Cache the result
        self._local_cache[cache_key] = health_status

        # Write to Redis (if available)
        if self._redis and health_status.healthy:
            await self._write_to_redis(service_name, health_status)

        return health_status

    async def _perform_health_check(
        self,
        service_name: str,
        service_url: str,
        health_endpoint: str,
        circuit_breaker: ServiceCircuitBreaker
    ) -> HealthStatus:
        """Perform actual HTTP health check."""
        start_time = time.time()
        url = f"{service_url.rstrip('/')}{health_endpoint}"

        try:
            response = await self._http_client.get(url)
            duration_ms = (time.time() - start_time) * 1000

            healthy = 200 <= response.status_code < 300

            if healthy:
                circuit_breaker.record_success()
                health_check_duration.labels(
                    service_name=service_name,
                    result="success"
                ).observe(time.time() - start_time)
            else:
                circuit_breaker.record_failure()
                health_check_duration.labels(
                    service_name=service_name,
                    result="unhealthy"
                ).observe(time.time() - start_time)

            logger.debug(
                f"Health check {service_name}: {response.status_code} ({duration_ms:.1f}ms)"
            )

            return HealthStatus(
                healthy=healthy,
                status_code=response.status_code,
                response_time_ms=duration_ms,
                timestamp=time.time(),
                cached=False
            )

        except (httpx.TimeoutException, httpx.RequestError) as e:
            circuit_breaker.record_failure()
            duration_ms = (time.time() - start_time) * 1000

            health_check_duration.labels(
                service_name=service_name,
                result="error"
            ).observe(time.time() - start_time)

            logger.warning(f"Health check failed for {service_name}: {e}")

            return HealthStatus(
                healthy=False,
                status_code=503,
                response_time_ms=duration_ms,
                timestamp=time.time(),
                cached=False
            )

    async def _get_from_redis(self, service_name: str) -> Optional[HealthStatus]:
        """Get health status from Redis cache."""
        try:
            key = f"health:{service_name}"
            data = await self._redis.hgetall(key)

            if not data:
                return None

            return HealthStatus(
                healthy=data.get("healthy") == "true",
                status_code=int(data.get("status_code", 200)),
                response_time_ms=float(data.get("response_time_ms", 0)),
                timestamp=float(data.get("timestamp", 0)),
                cached=True,
                cache_layer="redis"
            )
        except Exception as e:
            logger.warning(f"Redis cache read failed: {e}")
            return None

    async def _write_to_redis(self, service_name: str, status: HealthStatus):
        """Write health status to Redis cache."""
        try:
            key = f"health:{service_name}"
            await self._redis.hset(key, mapping={
                "healthy": "true" if status.healthy else "false",
                "status_code": status.status_code,
                "response_time_ms": status.response_time_ms,
                "timestamp": status.timestamp
            })
            await self._redis.expire(key, REDIS_CACHE_TTL)
        except Exception as e:
            logger.warning(f"Redis cache write failed: {e}")

    def _get_circuit_breaker(self, service_name: str) -> ServiceCircuitBreaker:
        """Get or create circuit breaker for service."""
        if service_name not in self._circuit_breakers:
            self._circuit_breakers[service_name] = ServiceCircuitBreaker(service_name)
        return self._circuit_breakers[service_name]

    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        return {
            "local_cache_size": len(self._local_cache),
            "local_cache_max": self._local_cache.maxsize,
            "circuit_breakers": {
                name: {
                    "state": cb.state.name,
                    "failure_count": cb.failure_count,
                    "success_count": cb.success_count
                }
                for name, cb in self._circuit_breakers.items()
            }
        }

    async def close(self):
        """Close HTTP client."""
        await self._http_client.aclose()
        logger.info("Health Check Cache closed")
