"""Maximus OSINT Service - Prometheus Metrics Collector.

This module implements Prometheus metrics collection for OSINT tools, providing
observability into:
- Request rates and volumes
- Latency percentiles (p50, p95, p99)
- Error rates by type
- Cache hit rates
- Circuit breaker states

Metrics are exposed via `/metrics` endpoint for Prometheus scraping.

Constitutional Compliance:
    - Article II (Pagani Standard): Production-ready observability
    - Article V (Prior Legislation): Monitoring before deployment

Author: Claude Code (Tactical Executor)
Date: 2025-10-14
Version: 1.0.0
"""

from prometheus_client import Counter, Gauge, Histogram


class MetricsCollector:
    """Prometheus metrics collector for OSINT tools.

    Provides standardized metrics for all tools:
    - Requests: Total count, rate
    - Latency: p50, p95, p99
    - Errors: Count by error type
    - Cache: Hit/miss rates
    - Circuit breaker: State

    Usage Example:
        metrics = MetricsCollector(tool_name="ShodanTool")

        # Track request
        metrics.increment_request(method="GET")

        # Track latency
        metrics.observe_latency(method="GET", latency_seconds=0.350)

        # Track error
        metrics.increment_error(error_type="http_429")

        # Track cache
        metrics.increment_cache_hit()
        metrics.increment_cache_miss()

        # Get stats
        stats = metrics.get_request_count()
    """

    # Class-level metrics (shared across all instances)
    # This prevents duplicate metrics registration

    _requests_total = Counter(
        "osint_requests_total",
        "Total OSINT API requests",
        ["tool", "method"],
    )

    _request_duration = Histogram(
        "osint_request_duration_seconds",
        "Request duration in seconds",
        ["tool", "method"],
        buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    )

    _errors_total = Counter(
        "osint_errors_total",
        "Total errors by type",
        ["tool", "error_type"],
    )

    _cache_hits = Counter(
        "osint_cache_hits_total",
        "Total cache hits",
        ["tool"],
    )

    _cache_misses = Counter(
        "osint_cache_misses_total",
        "Total cache misses",
        ["tool"],
    )

    _circuit_breaker_state = Gauge(
        "osint_circuit_breaker_state",
        "Circuit breaker state (0=CLOSED, 1=OPEN, 2=HALF_OPEN)",
        ["tool"],
    )

    _circuit_open_total = Counter(
        "osint_circuit_open_total",
        "Total times circuit opened",
        ["tool"],
    )

    def __init__(self, tool_name: str):
        """Initialize MetricsCollector for a specific tool.

        Args:
            tool_name: Name of the OSINT tool (e.g., "ShodanTool")
        """
        self.tool_name = tool_name

        # Local counters for get_* methods
        self._local_request_count = 0
        self._local_error_count = 0
        self._local_cache_hits = 0
        self._local_cache_misses = 0

    def increment_request(self, method: str = "GET") -> None:
        """Increment request counter.

        Args:
            method: HTTP method (GET, POST, etc.)
        """
        self._requests_total.labels(tool=self.tool_name, method=method).inc()
        self._local_request_count += 1

    def observe_latency(self, method: str, latency_seconds: float) -> None:
        """Record request latency.

        Args:
            method: HTTP method
            latency_seconds: Request duration in seconds
        """
        self._request_duration.labels(tool=self.tool_name, method=method).observe(latency_seconds)

    def increment_error(self, error_type: str) -> None:
        """Increment error counter by type.

        Args:
            error_type: Error type (e.g., "http_429", "timeout", "json_decode_error")
        """
        self._errors_total.labels(tool=self.tool_name, error_type=error_type).inc()
        self._local_error_count += 1

    def increment_cache_hit(self) -> None:
        """Increment cache hit counter."""
        self._cache_hits.labels(tool=self.tool_name).inc()
        self._local_cache_hits += 1

    def increment_cache_miss(self) -> None:
        """Increment cache miss counter."""
        self._cache_misses.labels(tool=self.tool_name).inc()
        self._local_cache_misses += 1

    def set_circuit_breaker_state(self, state: str) -> None:
        """Set circuit breaker state gauge.

        Args:
            state: Circuit state ("CLOSED", "OPEN", "HALF_OPEN")
        """
        state_map = {
            "CLOSED": 0,
            "OPEN": 1,
            "HALF_OPEN": 2,
        }
        self._circuit_breaker_state.labels(tool=self.tool_name).set(state_map.get(state, -1))

    def increment_circuit_open(self) -> None:
        """Increment circuit open counter."""
        self._circuit_open_total.labels(tool=self.tool_name).inc()

    def get_request_count(self) -> int:
        """Get total request count (local counter).

        Returns:
            Total requests made by this tool instance
        """
        return self._local_request_count

    def get_error_count(self) -> int:
        """Get total error count (local counter).

        Returns:
            Total errors encountered by this tool instance
        """
        return self._local_error_count

    def get_cache_hit_rate(self) -> float:
        """Calculate cache hit rate (local counters).

        Returns:
            Cache hit rate as percentage (0-100), or 0 if no cache operations
        """
        total = self._local_cache_hits + self._local_cache_misses
        if total == 0:
            return 0.0
        return (self._local_cache_hits / total) * 100

    def get_metrics_summary(self) -> dict:
        """Get metrics summary for health checks.

        Returns:
            Dictionary with current metrics snapshot
        """
        return {
            "tool": self.tool_name,
            "requests": self._local_request_count,
            "errors": self._local_error_count,
            "cache_hits": self._local_cache_hits,
            "cache_misses": self._local_cache_misses,
            "cache_hit_rate_percent": round(self.get_cache_hit_rate(), 2),
        }
