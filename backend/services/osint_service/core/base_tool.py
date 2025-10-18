"""Maximus OSINT Service - Base Tool Abstract Class.

This module implements the foundational abstract base class for ALL OSINT tools
within the Maximus AI ecosystem. It enforces production-grade patterns including:

- Exponential backoff retry logic
- Circuit breaker fail-fast pattern
- Token bucket rate limiting
- Multi-tier caching (Redis + in-memory LRU)
- Prometheus metrics collection
- Structured JSON logging
- Async I/O with connection pooling
- Graceful error handling and degradation

Constitutional Compliance:
    - Article II (Pagani Standard): Production-ready code, no mocks/placeholders
    - Article III (Zero Trust): All external calls treated as potential failures
    - Article IV (Antifragility): System strengthens under load via circuit breakers

Author: Claude Code (Tactical Executor)
Date: 2025-10-14
Version: 1.0.0
"""

import asyncio
import hashlib
import json
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import aiohttp
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from core.cache_manager import CacheManager
from core.circuit_breaker import CircuitBreaker
from core.rate_limiter import RateLimiter
from monitoring.logger import StructuredLogger
from monitoring.metrics import MetricsCollector


class ToolException(Exception):
    """Base exception for all OSINT tool errors.

    Wraps external API errors and internal failures for consistent error handling.
    """

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        """Initialize ToolException.

        Args:
            message: Human-readable error description
            original_error: Original exception that caused this error (for traceability)
        """
        super().__init__(message)
        self.original_error = original_error
        self.timestamp = time.time()


class BaseTool(ABC):
    """Abstract base class for ALL OSINT tools.

    Provides mandatory production-grade infrastructure:
    - Async I/O with connection pooling
    - Automatic retry with exponential backoff
    - Circuit breaker for fail-fast behavior
    - Token bucket rate limiting
    - Multi-tier caching (Redis + in-memory)
    - Prometheus metrics
    - Structured JSON logging

    All concrete OSINT tools MUST inherit from this class and implement:
    - _query_impl(): Core query logic specific to the tool

    Usage Example:
        class ShodanTool(BaseTool):
            async def _query_impl(self, target: str, **params) -> Dict[str, Any]:
                url = f"{self.BASE_URL}/shodan/host/{target}"
                return await self._make_request(url, params=params)

        async with ShodanTool(api_key="xxx", rate_limit=1.0) as shodan:
            result = await shodan.query("8.8.8.8")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        rate_limit: float = 1.0,
        timeout: int = 30,
        max_retries: int = 3,
        cache_ttl: int = 3600,
        cache_backend: str = "memory",
        circuit_breaker_threshold: int = 5,
        circuit_breaker_timeout: int = 60,
    ):
        """Initialize BaseTool with production-grade configuration.

        Args:
            api_key: API key for external service (if required)
            rate_limit: Max requests per second (token bucket rate)
            timeout: HTTP request timeout in seconds
            max_retries: Max retry attempts on transient failures
            cache_ttl: Cache time-to-live in seconds
            cache_backend: Cache backend ('memory' or 'redis')
            circuit_breaker_threshold: Failures before circuit opens
            circuit_breaker_timeout: Seconds before circuit attempts recovery
        """
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries

        # Core infrastructure components
        self.rate_limiter = RateLimiter(rate=rate_limit)
        self.cache = CacheManager(ttl=cache_ttl, backend=cache_backend)
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=circuit_breaker_threshold,
            recovery_timeout=circuit_breaker_timeout,
        )

        # Observability components
        tool_name = self.__class__.__name__
        self.metrics = MetricsCollector(tool_name=tool_name)
        self.logger = StructuredLogger(tool_name=tool_name)

        # HTTP session (initialized in __aenter__)
        self.session: Optional[aiohttp.ClientSession] = None

        self.logger.info("tool_initialized", config={
            "rate_limit": rate_limit,
            "timeout": timeout,
            "max_retries": max_retries,
            "cache_ttl": cache_ttl,
            "cache_backend": cache_backend,
            "circuit_breaker_threshold": circuit_breaker_threshold,
        })

    async def __aenter__(self):
        """Async context manager entry: initialize HTTP session with connection pooling."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            connector=aiohttp.TCPConnector(
                limit=100,  # Max connections in pool
                limit_per_host=10,  # Max connections per host
                ttl_dns_cache=300,  # DNS cache TTL
            ),
        )
        self.logger.info("session_opened", session_id=id(self.session))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit: close HTTP session gracefully."""
        if self.session:
            await self.session.close()
            self.logger.info("session_closed", session_id=id(self.session))

    @retry(
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def _make_request(
        self,
        url: str,
        method: str = "GET",
        **kwargs,
    ) -> Dict[str, Any]:
        """Execute HTTP request with retry, circuit breaker, and rate limiting.

        This is the core method that ALL external API calls MUST go through.
        It provides:
        - Rate limiting (prevents API rate limit violations)
        - Circuit breaker (fail-fast on repeated failures)
        - Exponential backoff retry (handles transient failures)
        - Metrics collection (latency, errors, status codes)
        - Structured logging (request/response details)

        Args:
            url: Target URL
            method: HTTP method (GET, POST, PUT, DELETE)
            **kwargs: Additional arguments passed to aiohttp.request()

        Returns:
            Parsed JSON response as dictionary

        Raises:
            ToolException: On request failure after retries exhausted
        """
        if not self.session:
            raise ToolException("HTTP session not initialized. Use 'async with' context manager.")

        # Rate limiting: wait for token availability
        await self.rate_limiter.acquire()

        # Circuit breaker: check if circuit is open
        if not self.circuit_breaker.can_execute():
            self.metrics.increment_circuit_open()
            raise ToolException(
                f"Circuit breaker is OPEN. Service unavailable for {self.circuit_breaker.recovery_timeout}s."
            )

        # Metrics: track request
        request_start = time.time()
        self.metrics.increment_request(method=method)

        try:
            self.logger.info("request_started", url=url, method=method)

            async with self.session.request(method, url, **kwargs) as resp:
                latency_ms = (time.time() - request_start) * 1000

                # Record latency
                self.metrics.observe_latency(method=method, latency_seconds=latency_ms / 1000)

                # Handle HTTP errors
                if resp.status >= 400:
                    error_body = await resp.text()
                    self.logger.error(
                        "request_failed_http_error",
                        url=url,
                        status=resp.status,
                        error_body=error_body[:200],  # Truncate long errors
                        latency_ms=latency_ms,
                    )
                    self.metrics.increment_error(error_type=f"http_{resp.status}")
                    self.circuit_breaker.record_failure()

                    raise ToolException(
                        f"HTTP {resp.status} error for {url}: {error_body[:100]}"
                    )

                # Parse JSON response
                try:
                    data = await resp.json()
                except json.JSONDecodeError as e:
                    self.logger.error(
                        "request_failed_json_decode",
                        url=url,
                        status=resp.status,
                        error=str(e),
                    )
                    self.metrics.increment_error(error_type="json_decode_error")
                    self.circuit_breaker.record_failure()
                    raise ToolException(f"Invalid JSON response from {url}", original_error=e)

                # Success
                self.logger.info(
                    "request_success",
                    url=url,
                    status=resp.status,
                    latency_ms=latency_ms,
                )
                self.circuit_breaker.record_success()
                return data

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            latency_ms = (time.time() - request_start) * 1000
            self.logger.error(
                "request_failed_network_error",
                url=url,
                error=str(e),
                error_type=type(e).__name__,
                latency_ms=latency_ms,
            )
            self.metrics.increment_error(error_type=type(e).__name__)
            self.circuit_breaker.record_failure()
            raise ToolException(f"Network error for {url}: {e}", original_error=e)

    async def query(self, target: str, use_cache: bool = True, **params) -> Dict[str, Any]:
        """Execute OSINT query with automatic caching.

        This is the main public interface for all OSINT tools. It:
        1. Checks cache first (if enabled)
        2. Executes _query_impl() on cache miss
        3. Stores result in cache
        4. Returns result

        Args:
            target: Primary target identifier (e.g., IP, username, email)
            use_cache: Whether to use cache (default: True)
            **params: Additional query parameters specific to the tool

        Returns:
            Query result as dictionary

        Raises:
            ToolException: On query failure
        """
        # Build deterministic cache key
        cache_key = self._build_cache_key(target, params)

        # Cache check
        if use_cache:
            cached = await self.cache.get(cache_key)
            if cached is not None:
                self.metrics.increment_cache_hit()
                self.logger.info("cache_hit", target=target, cache_key=cache_key)
                return cached

        # Cache miss
        self.metrics.increment_cache_miss()
        self.logger.info("cache_miss", target=target, cache_key=cache_key)

        # Execute query
        query_start = time.time()
        try:
            result = await self._query_impl(target, **params)
            query_duration = time.time() - query_start

            self.logger.info(
                "query_success",
                target=target,
                duration_ms=query_duration * 1000,
            )

            # Store in cache
            if use_cache:
                await self.cache.set(cache_key, result)
                self.logger.info("cache_set", cache_key=cache_key)

            return result

        except Exception as e:
            query_duration = time.time() - query_start
            self.logger.error(
                "query_failed",
                target=target,
                error=str(e),
                error_type=type(e).__name__,
                duration_ms=query_duration * 1000,
            )
            self.metrics.increment_error(error_type="query_failure")
            raise

    @abstractmethod
    async def _query_impl(self, target: str, **params) -> Dict[str, Any]:
        """Core query logic specific to each OSINT tool.

        Subclasses MUST implement this method with their tool-specific logic.
        This method should use self._make_request() for all HTTP calls.

        Args:
            target: Primary target identifier
            **params: Tool-specific query parameters

        Returns:
            Query result as dictionary

        Raises:
            ToolException: On query failure
        """
        pass

    def _build_cache_key(self, target: str, params: Dict[str, Any]) -> str:
        """Build deterministic cache key from target and parameters.

        Args:
            target: Primary target identifier
            params: Query parameters

        Returns:
            SHA256 hash of target + sorted params (deterministic)
        """
        key_data = f"{target}:{json.dumps(params, sort_keys=True)}"
        return hashlib.sha256(key_data.encode()).hexdigest()

    async def health_check(self) -> Dict[str, Any]:
        """Check tool health status.

        Returns:
            Health status dictionary with circuit breaker state and metrics
        """
        return {
            "tool": self.__class__.__name__,
            "healthy": self.circuit_breaker.can_execute(),
            "circuit_state": self.circuit_breaker.state,
            "total_requests": self.metrics.get_request_count(),
            "total_errors": self.metrics.get_error_count(),
            "cache_hit_rate": self.metrics.get_cache_hit_rate(),
        }
