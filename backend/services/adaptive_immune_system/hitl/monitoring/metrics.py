"""
Prometheus metrics for HITL API.

Implements RED method (Request rate, Error rate, Duration) and USE method
(Utilization, Saturation, Errors) for comprehensive observability.
"""

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Summary,
    CollectorRegistry,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
from typing import Optional


# Create custom registry (avoids conflicts with other Prometheus clients)
registry = CollectorRegistry()


# ============================================================================
# REQUEST METRICS (RED Method)
# ============================================================================

# Request counter
http_requests_total = Counter(
    name="http_requests_total",
    documentation="Total HTTP requests",
    labelnames=["method", "endpoint", "status"],
    registry=registry,
)

# Request duration histogram
http_request_duration_seconds = Histogram(
    name="http_request_duration_seconds",
    documentation="HTTP request duration in seconds",
    labelnames=["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0),
    registry=registry,
)

# Request size
http_request_size_bytes = Summary(
    name="http_request_size_bytes",
    documentation="HTTP request size in bytes",
    labelnames=["method", "endpoint"],
    registry=registry,
)

# Response size
http_response_size_bytes = Summary(
    name="http_response_size_bytes",
    documentation="HTTP response size in bytes",
    labelnames=["method", "endpoint"],
    registry=registry,
)


# ============================================================================
# BUSINESS METRICS
# ============================================================================

# Review operations
review_created_total = Counter(
    name="review_created_total",
    documentation="Total reviews created",
    labelnames=["severity", "source"],
    registry=registry,
)

review_decision_total = Counter(
    name="review_decision_total",
    documentation="Total review decisions made",
    labelnames=["decision", "severity"],
    registry=registry,
)

review_decision_duration_seconds = Histogram(
    name="review_decision_duration_seconds",
    documentation="Time taken to make review decision",
    labelnames=["decision"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
    registry=registry,
)

# APV (Anomalous Pattern Validation) metrics
apv_validation_total = Counter(
    name="apv_validation_total",
    documentation="Total APV validations performed",
    labelnames=["pattern_type", "result"],
    registry=registry,
)

apv_validation_duration_seconds = Histogram(
    name="apv_validation_duration_seconds",
    documentation="APV validation duration",
    labelnames=["pattern_type"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
    registry=registry,
)


# ============================================================================
# SYSTEM METRICS (USE Method)
# ============================================================================

# Database metrics
db_connections_active = Gauge(
    name="db_connections_active",
    documentation="Active database connections",
    registry=registry,
)

db_connections_idle = Gauge(
    name="db_connections_idle",
    documentation="Idle database connections",
    registry=registry,
)

db_query_duration_seconds = Histogram(
    name="db_query_duration_seconds",
    documentation="Database query duration",
    labelnames=["query_type"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
    registry=registry,
)

db_query_errors_total = Counter(
    name="db_query_errors_total",
    documentation="Total database query errors",
    labelnames=["query_type", "error_type"],
    registry=registry,
)

# Cache metrics
cache_operations_total = Counter(
    name="cache_operations_total",
    documentation="Total cache operations",
    labelnames=["operation", "result"],
    registry=registry,
)

cache_hit_ratio = Gauge(
    name="cache_hit_ratio",
    documentation="Cache hit ratio (0-1)",
    registry=registry,
)

cache_evictions_total = Counter(
    name="cache_evictions_total",
    documentation="Total cache evictions",
    registry=registry,
)


# ============================================================================
# ERROR METRICS
# ============================================================================

# Application errors
app_errors_total = Counter(
    name="app_errors_total",
    documentation="Total application errors",
    labelnames=["error_type", "severity"],
    registry=registry,
)

app_exceptions_total = Counter(
    name="app_exceptions_total",
    documentation="Total unhandled exceptions",
    labelnames=["exception_type"],
    registry=registry,
)


# ============================================================================
# SLO METRICS
# ============================================================================

# Availability
service_up = Gauge(
    name="service_up",
    documentation="Service availability (1=up, 0=down)",
    registry=registry,
)
service_up.set(1)  # Initialize as up

# SLO tracking
slo_requests_total = Counter(
    name="slo_requests_total",
    documentation="Total requests for SLO calculation",
    registry=registry,
)

slo_requests_good = Counter(
    name="slo_requests_good",
    documentation="Requests meeting SLO criteria",
    labelnames=["slo_type"],
    registry=registry,
)

slo_requests_bad = Counter(
    name="slo_requests_bad",
    documentation="Requests failing SLO criteria",
    labelnames=["slo_type"],
    registry=registry,
)


# ============================================================================
# HELPER CLASSES
# ============================================================================

class MetricsCollector:
    """Centralized metrics collector with helper methods."""

    def __init__(self):
        self.registry = registry

    def get_metrics(self) -> bytes:
        """Generate latest metrics in Prometheus format."""
        return generate_latest(self.registry)

    def get_content_type(self) -> str:
        """Get Prometheus content type."""
        return CONTENT_TYPE_LATEST

    def record_request(
        self,
        method: str,
        endpoint: str,
        status: int,
        duration: float,
        request_size: Optional[int] = None,
        response_size: Optional[int] = None,
    ):
        """Record HTTP request metrics."""
        http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
        http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)

        if request_size is not None:
            http_request_size_bytes.labels(method=method, endpoint=endpoint).observe(request_size)

        if response_size is not None:
            http_response_size_bytes.labels(method=method, endpoint=endpoint).observe(response_size)

        # Track SLO
        slo_requests_total.inc()
        if status < 500 and duration < 0.5:
            slo_requests_good.labels(slo_type="availability").inc()
            slo_requests_good.labels(slo_type="latency").inc()
        else:
            if status >= 500:
                slo_requests_bad.labels(slo_type="availability").inc()
            if duration >= 0.5:
                slo_requests_bad.labels(slo_type="latency").inc()

    def record_review_created(self, severity: str, source: str):
        """Record review creation."""
        review_created_total.labels(severity=severity, source=source).inc()

    def record_review_decision(self, decision: str, severity: str, duration: float):
        """Record review decision."""
        review_decision_total.labels(decision=decision, severity=severity).inc()
        review_decision_duration_seconds.labels(decision=decision).observe(duration)

    def record_apv_validation(self, pattern_type: str, result: str, duration: float):
        """Record APV validation."""
        apv_validation_total.labels(pattern_type=pattern_type, result=result).inc()
        apv_validation_duration_seconds.labels(pattern_type=pattern_type).observe(duration)

    def record_db_query(self, query_type: str, duration: float, error: Optional[str] = None):
        """Record database query."""
        db_query_duration_seconds.labels(query_type=query_type).observe(duration)
        if error:
            db_query_errors_total.labels(query_type=query_type, error_type=error).inc()

    def record_cache_operation(self, operation: str, result: str):
        """Record cache operation."""
        cache_operations_total.labels(operation=operation, result=result).inc()

    def update_db_connections(self, active: int, idle: int):
        """Update database connection gauges."""
        db_connections_active.set(active)
        db_connections_idle.set(idle)

    def update_cache_hit_ratio(self, ratio: float):
        """Update cache hit ratio."""
        cache_hit_ratio.set(ratio)

    def record_error(self, error_type: str, severity: str):
        """Record application error."""
        app_errors_total.labels(error_type=error_type, severity=severity).inc()

    def record_exception(self, exception_type: str):
        """Record unhandled exception."""
        app_exceptions_total.labels(exception_type=exception_type).inc()

    def set_service_status(self, is_up: bool):
        """Set service availability status."""
        service_up.set(1 if is_up else 0)


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

# Singleton metrics collector
metrics = MetricsCollector()


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def record_request(
    method: str,
    endpoint: str,
    status: int,
    duration: float,
    request_size: Optional[int] = None,
    response_size: Optional[int] = None,
):
    """Record HTTP request metrics (convenience function)."""
    metrics.record_request(method, endpoint, status, duration, request_size, response_size)


def record_review_created(severity: str, source: str):
    """Record review creation (convenience function)."""
    metrics.record_review_created(severity, source)


def record_review_decision(decision: str, severity: str, duration: float):
    """Record review decision (convenience function)."""
    metrics.record_review_decision(decision, severity, duration)


def record_db_query(query_type: str, duration: float, error: Optional[str] = None):
    """Record database query (convenience function)."""
    metrics.record_db_query(query_type, duration, error)


def record_cache_operation(operation: str, result: str):
    """Record cache operation (convenience function)."""
    metrics.record_cache_operation(operation, result)
