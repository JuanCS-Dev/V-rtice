"""Prometheus metrics helpers for all services."""

from typing import Any

from prometheus_client import Counter, Gauge, Histogram, Info


def create_service_metrics(service_name: str) -> dict[str, Any]:
    """Create standard Prometheus metrics for a service."""
    prefix = service_name.replace("-", "_").replace(" ", "_").lower()

    return {
        "requests_total": Counter(
            f"{prefix}_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status"],
        ),
        "request_duration_seconds": Histogram(
            f"{prefix}_request_duration_seconds",
            "HTTP request duration in seconds",
            ["method", "endpoint"],
        ),
        "active_requests": Gauge(
            f"{prefix}_active_requests",
            "Number of active requests",
        ),
        "errors_total": Counter(
            f"{prefix}_errors_total",
            "Total errors",
            ["type", "endpoint"],
        ),
        "service_info": Info(
            f"{prefix}_service_info",
            "Service metadata",
        ),
    }
