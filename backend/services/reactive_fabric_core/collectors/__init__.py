"""
Reactive Fabric Intelligence Collectors.

This module implements passive intelligence collection from various sources
including honeypots, network traffic, file integrity monitoring, logs, and
threat intelligence feeds.

All collectors follow Phase 1 restrictions: PASSIVE ONLY, no automated responses.
"""

from .base_collector import BaseCollector, CollectorHealth, CollectorMetrics
from .log_aggregation_collector import LogAggregationCollector

__all__ = [
    "BaseCollector",
    "CollectorHealth",
    "CollectorMetrics",
    "LogAggregationCollector",
]