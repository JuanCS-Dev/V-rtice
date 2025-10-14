"""Maximus OSINT Service - Monitoring Module.

This package provides observability infrastructure for OSINT tools:
- MetricsCollector: Prometheus metrics (requests, latency, errors, cache)
- StructuredLogger: JSON structured logging for log aggregation

Author: Claude Code (Tactical Executor)
Date: 2025-10-14
"""

from monitoring.logger import StructuredLogger, service_logger
from monitoring.metrics import MetricsCollector

__all__ = [
    "MetricsCollector",
    "StructuredLogger",
    "service_logger",
]
