"""
Monitoring module for Adaptive Immune System - HITL API.

Provides:
- Prometheus metrics instrumentation
- OpenTelemetry distributed tracing
- Custom middleware for automatic instrumentation
"""

from .metrics import (
    metrics,
    record_request,
    record_review_created,
    record_review_decision,
    record_db_query,
    record_cache_operation,
)
from .tracing import setup_tracing, trace_operation
from .middleware import PrometheusMiddleware, TracingMiddleware

__all__ = [
    # Metrics
    "metrics",
    "record_request",
    "record_review_created",
    "record_review_decision",
    "record_db_query",
    "record_cache_operation",
    # Tracing
    "setup_tracing",
    "trace_operation",
    # Middleware
    "PrometheusMiddleware",
    "TracingMiddleware",
]
