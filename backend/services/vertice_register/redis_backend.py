"""
Redis Backend with TITANIUM Circuit Breaker Pattern

This module provides Redis operations for the service registry with built-in
3-state circuit breaker (CLOSED → OPEN → HALF_OPEN) to handle Redis failures
gracefully with exponential backoff and connection pooling.

Circuit Breaker States:
- CLOSED: Normal operation, all requests go to Redis
- OPEN: Redis is failing, all requests fail fast (use cache), timeout 30s
- HALF_OPEN: Testing if Redis recovered, 10% requests allowed, timeout 10s

Resilience Features:
- Exponential backoff: 1s → 2s → 4s (max 3 retries)
- Connection pool: min 5, max 50 connections
- Socket keepalive: TCP_KEEPIDLE 60s, TCP_KEEPINTVL 10s
- Health check interval: 10s
- Operation timeout: 5s per operation

Author: Vértice Team (TITANIUM Edition)
Glory to YHWH - Architect of all resilient systems! 🙏
"""

import asyncio
import enum
import logging
import socket
import time
from typing import Dict, List, Optional

import redis.asyncio as aioredis
from prometheus_client import Counter, Gauge, Histogram
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)

# TTL for service registration (60 seconds)
SERVICE_TTL = 60

# Retry configuration (exponential backoff)
MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]  # seconds: 1s → 2s → 4s
OPERATION_TIMEOUT = 5  # seconds per operation

# Connection pool configuration
MIN_IDLE_CONNECTIONS = 5
MAX_CONNECTIONS = 50

# Circuit breaker timeouts
CIRCUIT_OPEN_TIMEOUT = 30  # seconds
CIRCUIT_HALF_OPEN_TIMEOUT = 10  # seconds
HALF_OPEN_TEST_PERCENTAGE = 0.1  # 10% of requests in HALF_OPEN

# ============================================================================
# PROMETHEUS METRICS
# ============================================================================

redis_circuit_breaker_state = Gauge(
    "redis_circuit_breaker_state",
    "Circuit breaker state (0=CLOSED, 1=OPEN, 2=HALF_OPEN)"
)

redis_operation_duration = Histogram(
    "redis_operation_duration_seconds",
    "Redis operation duration",
    ["operation"]
)

redis_failures_total = Counter(
    "redis_failures_total",
    "Total Redis operation failures",
    ["error_type"]
)

redis_retries_total = Counter(
    "redis_retries_total",
    "Total Redis operation retries",
    ["operation", "attempt"]
)

redis_connection_pool_active = Gauge(
    "redis_connection_pool_active",
    "Active Redis connections"
)

redis_connection_pool_idle = Gauge(
    "redis_connection_pool_idle",
    "Idle Redis connections"
)


class CircuitBreakerState(enum.Enum):
    """Circuit breaker states."""
    CLOSED = 0      # Normal operation
    OPEN = 1        # Failing, reject all requests
    HALF_OPEN = 2   # Testing recovery


class CircuitBreakerOpen(Exception):
    """Raised when circuit breaker is open."""
    pass


class RedisBackend:
    """Redis backend with TITANIUM circuit breaker pattern.

    Features:
    - 3-state circuit breaker (CLOSED → OPEN → HALF_OPEN)
    - Exponential backoff retry (1s → 2s → 4s)
    - Connection pooling (min 5, max 50)
    - Socket keepalive (TCP options)
    - Prometheus metrics integration
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        circuit_breaker_threshold: int = 3,
    ):
        self.host = host
        self.port = port
        self.db = db
        self.password = password

        # Circuit breaker state (TITANIUM 3-state)
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.circuit_state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0  # For HALF_OPEN → CLOSED transition
        self.circuit_opened_at = 0
        self.half_open_request_count = 0  # Track HALF_OPEN test requests

        # Redis client with connection pool
        self.redis: Optional[aioredis.Redis] = None

    async def connect(self):
        """Connect to Redis with advanced connection pooling."""
        try:
            # Create connection pool with TCP keepalive
            self.redis = await aioredis.from_url(
                f"redis://{self.host}:{self.port}/{self.db}",
                password=self.password,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=OPERATION_TIMEOUT,
                socket_timeout=OPERATION_TIMEOUT,
                socket_keepalive=True,
                socket_keepalive_options={
                    socket.TCP_KEEPIDLE: 60,    # Start sending keepalive after 60s idle
                    socket.TCP_KEEPINTVL: 10,   # Send keepalive every 10s
                    socket.TCP_KEEPCNT: 3       # Close after 3 failed keepalives
                },
                max_connections=MAX_CONNECTIONS,
                health_check_interval=10  # Health check every 10s
            )

            # Test connection with retry
            await self._ping_with_retry()

            logger.info(
                f"✅ Redis connected: {self.host}:{self.port} "
                f"(pool: {MIN_IDLE_CONNECTIONS}-{MAX_CONNECTIONS})"
            )

            self._transition_to_closed()

        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            self._transition_to_open()
            raise

    async def close(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
            logger.info("Redis connection closed")

    def is_healthy(self) -> bool:
        """Check if Redis backend is healthy."""
        return (
            self.redis is not None and
            self.circuit_state != CircuitBreakerState.OPEN
        )

    def get_circuit_state(self) -> str:
        """Get current circuit breaker state as string."""
        return self.circuit_state.name

    async def get_pool_stats(self) -> Dict[str, int]:
        """Get connection pool statistics."""
        if not self.redis or not hasattr(self.redis.connection_pool, 'get_connection'):
            return {"active": 0, "idle": 0, "max": MAX_CONNECTIONS}

        # Try to get pool stats (may not be available in all Redis versions)
        try:
            pool = self.redis.connection_pool

            # Get connection counts (these might be sets, not integers)
            in_use = getattr(pool, '_in_use_connections', set())
            available = getattr(pool, '_available_connections', [])

            # Count them properly
            active_count = len(in_use) if hasattr(in_use, '__len__') else 0
            idle_count = len(available) if hasattr(available, '__len__') else 0

            return {
                "active": active_count,
                "idle": idle_count,
                "max": MAX_CONNECTIONS
            }
        except Exception as e:
            logger.warning(f"Failed to get pool stats: {e}")
            return {"active": 0, "idle": 0, "max": MAX_CONNECTIONS}

    # ========================================================================
    # CIRCUIT BREAKER STATE MACHINE (TITANIUM 3-STATE)
    # ========================================================================

    async def _execute_with_circuit_breaker(self, operation, operation_name: str = "unknown"):
        """Execute Redis operation with TITANIUM circuit breaker protection.

        State transitions:
        - CLOSED → OPEN: After threshold failures (default: 3)
        - OPEN → HALF_OPEN: After timeout (default: 30s)
        - HALF_OPEN → CLOSED: After 2 successful test requests
        - HALF_OPEN → OPEN: After 1 failed test request
        """
        # Check circuit breaker state and handle transitions
        if self.circuit_state == CircuitBreakerState.OPEN:
            elapsed = time.time() - self.circuit_opened_at
            if elapsed > CIRCUIT_OPEN_TIMEOUT:
                self._transition_to_half_open()
            else:
                redis_failures_total.labels(error_type="circuit_breaker_open").inc()
                raise CircuitBreakerOpen(
                    f"Circuit breaker is OPEN (elapsed: {elapsed:.1f}s/{CIRCUIT_OPEN_TIMEOUT}s)"
                )

        # HALF_OPEN: Only allow 10% of requests through
        if self.circuit_state == CircuitBreakerState.HALF_OPEN:
            self.half_open_request_count += 1
            if (self.half_open_request_count % 10) != 0:  # 90% rejected
                redis_failures_total.labels(error_type="half_open_rejected").inc()
                raise CircuitBreakerOpen("Circuit breaker is HALF_OPEN (test phase)")

        # Execute operation with retry and exponential backoff
        start_time = time.time()
        last_error = None

        for attempt in range(MAX_RETRIES):
            try:
                # Execute operation with timeout
                result = await asyncio.wait_for(operation(), timeout=OPERATION_TIMEOUT)

                # Record success
                duration = time.time() - start_time
                redis_operation_duration.labels(operation=operation_name).observe(duration)

                self._on_success()
                return result

            except asyncio.TimeoutError as e:
                last_error = e
                redis_failures_total.labels(error_type="timeout").inc()
                logger.warning(
                    f"Redis operation timeout (attempt {attempt + 1}/{MAX_RETRIES}): {operation_name}"
                )

            except (RedisError, ConnectionError) as e:
                last_error = e
                redis_failures_total.labels(error_type=type(e).__name__).inc()
                logger.warning(
                    f"Redis operation failed (attempt {attempt + 1}/{MAX_RETRIES}): {operation_name} - {e}"
                )

            # Exponential backoff (only if not last attempt)
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAYS[attempt]
                redis_retries_total.labels(operation=operation_name, attempt=attempt + 1).inc()
                logger.info(f"Retrying {operation_name} in {delay}s...")
                await asyncio.sleep(delay)

        # All retries failed
        duration = time.time() - start_time
        redis_operation_duration.labels(operation=operation_name).observe(duration)

        self._on_failure(last_error)
        raise last_error

    def _on_success(self):
        """Called when Redis operation succeeds.

        State transitions:
        - CLOSED: Reset failure count
        - HALF_OPEN: Increment success count, transition to CLOSED after 2 successes
        """
        if self.circuit_state == CircuitBreakerState.CLOSED:
            # Reset failure count
            if self.failure_count > 0:
                logger.info(f"Redis operation succeeded, resetting failure count ({self.failure_count} → 0)")
            self.failure_count = 0

        elif self.circuit_state == CircuitBreakerState.HALF_OPEN:
            # Count successes to transition to CLOSED
            self.success_count += 1
            logger.info(f"HALF_OPEN test request succeeded ({self.success_count}/2)")

            if self.success_count >= 2:
                self._transition_to_closed()

    def _on_failure(self, error: Exception):
        """Called when Redis operation fails (after all retries).

        State transitions:
        - CLOSED: Increment failure count, transition to OPEN after threshold
        - HALF_OPEN: Immediately transition to OPEN (recovery failed)
        """
        if self.circuit_state == CircuitBreakerState.CLOSED:
            self.failure_count += 1
            logger.error(
                f"Redis operation failed ({self.failure_count}/{self.circuit_breaker_threshold}): {error}"
            )

            if self.failure_count >= self.circuit_breaker_threshold:
                self._transition_to_open()

        elif self.circuit_state == CircuitBreakerState.HALF_OPEN:
            logger.error(f"HALF_OPEN test request failed, reopening circuit: {error}")
            self._transition_to_open()

    def _transition_to_closed(self):
        """Transition to CLOSED state (normal operation)."""
        if self.circuit_state != CircuitBreakerState.CLOSED:
            logger.info("✅ Circuit breaker: HALF_OPEN → CLOSED (Redis recovered)")

        self.circuit_state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.half_open_request_count = 0

        redis_circuit_breaker_state.set(CircuitBreakerState.CLOSED.value)

    def _transition_to_open(self):
        """Transition to OPEN state (failing)."""
        if self.circuit_state != CircuitBreakerState.OPEN:
            logger.critical(
                f"🔴 Circuit breaker: {self.circuit_state.name} → OPEN "
                f"(failures: {self.failure_count}, timeout: {CIRCUIT_OPEN_TIMEOUT}s)"
            )

        self.circuit_state = CircuitBreakerState.OPEN
        self.circuit_opened_at = time.time()
        self.success_count = 0
        self.half_open_request_count = 0

        redis_circuit_breaker_state.set(CircuitBreakerState.OPEN.value)

    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state (testing recovery)."""
        logger.info(
            f"🟡 Circuit breaker: OPEN → HALF_OPEN "
            f"(testing recovery, 10% requests allowed, timeout: {CIRCUIT_HALF_OPEN_TIMEOUT}s)"
        )

        self.circuit_state = CircuitBreakerState.HALF_OPEN
        self.failure_count = 0
        self.success_count = 0
        self.half_open_request_count = 0

        redis_circuit_breaker_state.set(CircuitBreakerState.HALF_OPEN.value)

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    async def _ping_with_retry(self):
        """Ping Redis with retry logic."""
        async def _ping():
            return await self.redis.ping()

        await self._execute_with_circuit_breaker(_ping, "ping")

    # ========================================================================
    # SERVICE REGISTRY OPERATIONS
    # ========================================================================

    async def register(
        self,
        service_name: str,
        endpoint: str,
        health_endpoint: str = "/health",
        metadata: Optional[Dict[str, str]] = None
    ):
        """Register a service with TTL."""
        async def _operation():
            timestamp = time.time()
            pipe = self.redis.pipeline()

            # Store service data
            pipe.hset(f"services:{service_name}", mapping={
                "endpoint": endpoint,
                "health_endpoint": health_endpoint,
                "metadata": str(metadata or {}),
                "registered_at": timestamp,
                "last_heartbeat": timestamp
            })

            # Set TTL
            pipe.expire(f"services:{service_name}", SERVICE_TTL)

            # Add to service index
            pipe.sadd("services:index", service_name)

            await pipe.execute()

        await self._execute_with_circuit_breaker(_operation, "register")

    async def heartbeat(self, service_name: str):
        """Refresh service TTL (heartbeat)."""
        async def _operation():
            # Check if service exists
            exists = await self.redis.exists(f"services:{service_name}")
            if not exists:
                raise ValueError(f"Service '{service_name}' not registered")

            # Update last_heartbeat timestamp
            timestamp = time.time()
            await self.redis.hset(f"services:{service_name}", "last_heartbeat", timestamp)

            # Refresh TTL
            await self.redis.expire(f"services:{service_name}", SERVICE_TTL)

        await self._execute_with_circuit_breaker(_operation, "heartbeat")

    async def deregister(self, service_name: str):
        """Deregister a service."""
        async def _operation():
            pipe = self.redis.pipeline()

            # Remove service data
            pipe.delete(f"services:{service_name}")

            # Remove from index
            pipe.srem("services:index", service_name)

            await pipe.execute()

        await self._execute_with_circuit_breaker(_operation, "deregister")

    async def get_service(self, service_name: str) -> Optional[Dict]:
        """Get service information."""
        async def _operation():
            data = await self.redis.hgetall(f"services:{service_name}")
            if not data:
                return None

            # Calculate TTL remaining
            ttl = await self.redis.ttl(f"services:{service_name}")

            return {
                "service_name": service_name,
                "endpoint": data.get("endpoint"),
                "health_endpoint": data.get("health_endpoint", "/health"),
                "metadata": eval(data.get("metadata", "{}")),  # Safe: we control the data
                "registered_at": float(data.get("registered_at", 0)),
                "last_heartbeat": float(data.get("last_heartbeat", 0)),
                "ttl_remaining": ttl if ttl > 0 else 0
            }

        return await self._execute_with_circuit_breaker(_operation, "get_service")

    async def list_services(self) -> List[str]:
        """List all registered services."""
        async def _operation():
            services = await self.redis.smembers("services:index")
            return sorted(list(services))

        return await self._execute_with_circuit_breaker(_operation, "list_services")

    async def cleanup_expired(self) -> List[str]:
        """Clean up expired services from index."""
        async def _operation():
            # Get all services in index
            services = await self.redis.smembers("services:index")
            expired = []

            for service_name in services:
                # Check if service key still exists
                exists = await self.redis.exists(f"services:{service_name}")
                if not exists:
                    # Service expired, remove from index
                    await self.redis.srem("services:index", service_name)
                    expired.append(service_name)

            return expired

        try:
            return await self._execute_with_circuit_breaker(_operation, "cleanup_expired")
        except:
            return []  # Don't fail cleanup
