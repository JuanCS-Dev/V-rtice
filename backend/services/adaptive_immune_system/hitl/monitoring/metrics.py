"""
Prometheus metrics for HITL API.

Provides comprehensive metrics for monitoring application health and performance.

Usage:
    from hitl.monitoring import http_requests_total, track_request_metrics

    @track_request_metrics("/hitl/reviews")
    async def get_reviews():
        ...

    # Or manual instrumentation:
    http_requests_total.labels(method="GET", endpoint="/hitl/reviews", status=200).inc()
"""

from prometheus_client import Counter, Histogram, Gauge, Info
from functools import wraps
import time
from typing import Callable


# --- Application Info ---

app_info = Info("hitl_app", "Application information")
app_info.info({
    "name": "Adaptive Immune System - HITL API",
    "version": "1.0.0",
    "component": "hitl_api",
})


# --- Counters ---

http_requests_total = Counter(
    "hitl_http_requests_total",
    "Total HTTP requests processed",
    ["method", "endpoint", "status"],
)

decisions_total = Counter(
    "hitl_decisions_total",
    "Total HITL decisions made",
    ["decision_type", "severity"],
)

websocket_connections_total = Counter(
    "hitl_websocket_connections_total",
    "Total WebSocket connections established",
)

websocket_messages_sent = Counter(
    "hitl_websocket_messages_sent",
    "Total WebSocket messages sent",
    ["channel", "message_type"],
)

wargame_runs_total = Counter(
    "hitl_wargame_runs_total",
    "Total wargaming runs executed",
    ["verdict"],
)

# --- Gauges ---

active_apv_reviews = Gauge(
    "hitl_active_apv_reviews",
    "Number of APVs currently pending review",
)

websocket_connections_active = Gauge(
    "hitl_websocket_connections_active",
    "Number of active WebSocket connections",
)

# --- Histograms ---

http_request_duration = Histogram(
    "hitl_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

decision_processing_duration = Histogram(
    "hitl_decision_processing_duration_seconds",
    "Time to process a HITL decision in seconds",
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0),
)

websocket_message_size = Histogram(
    "hitl_websocket_message_size_bytes",
    "WebSocket message size in bytes",
    ["message_type"],
    buckets=(100, 500, 1000, 5000, 10000, 50000, 100000),
)


# --- Decorator for Automatic Request Tracking ---

def track_request_metrics(endpoint: str) -> Callable:
    """
    Decorator to automatically track HTTP request metrics.

    Args:
        endpoint: Endpoint name for labeling (e.g., "/hitl/reviews")

    Usage:
        @track_request_metrics("/hitl/reviews")
        async def get_reviews():
            ...

    Tracks:
        - Request count (http_requests_total)
        - Request duration (http_request_duration)
        - Status code (200 for success, 500 for exceptions)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = 200

            try:
                result = await func(*args, **kwargs)
                return result

            except Exception as e:
                status = 500
                raise

            finally:
                duration = time.time() - start_time

                # Record metrics
                http_requests_total.labels(
                    method="GET",  # TODO: Extract from request
                    endpoint=endpoint,
                    status=status,
                ).inc()

                http_request_duration.labels(
                    method="GET",
                    endpoint=endpoint,
                ).observe(duration)

        return wrapper
    return decorator


# --- Helper Functions ---

def record_decision(decision_type: str, severity: str) -> None:
    """
    Record a HITL decision in metrics.

    Args:
        decision_type: Type of decision (approve, reject, modify, escalate)
        severity: APV severity (CRITICAL, HIGH, MEDIUM, LOW)
    """
    decisions_total.labels(
        decision_type=decision_type,
        severity=severity,
    ).inc()


def record_wargame_run(verdict: str) -> None:
    """
    Record a wargaming run in metrics.

    Args:
        verdict: Wargame verdict (PATCH_EFFECTIVE, INCONCLUSIVE, PATCH_INSUFFICIENT)
    """
    wargame_runs_total.labels(verdict=verdict).inc()


def update_active_reviews(count: int) -> None:
    """
    Update the count of active APV reviews.

    Args:
        count: Current number of pending reviews
    """
    active_apv_reviews.set(count)


def increment_websocket_connections() -> None:
    """Increment WebSocket connection counters."""
    websocket_connections_total.inc()
    websocket_connections_active.inc()


def decrement_websocket_connections() -> None:
    """Decrement WebSocket active connection counter."""
    websocket_connections_active.dec()


def record_websocket_message(channel: str, message_type: str, size_bytes: int) -> None:
    """
    Record WebSocket message metrics.

    Args:
        channel: Channel name (apvs, decisions, stats)
        message_type: Message type (new_apv, decision_made, stats_update)
        size_bytes: Message size in bytes
    """
    websocket_messages_sent.labels(
        channel=channel,
        message_type=message_type,
    ).inc()

    websocket_message_size.labels(
        message_type=message_type,
    ).observe(size_bytes)
