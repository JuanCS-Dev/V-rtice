"""Metrics collection and aggregation for the ADR Core Service.

This module provides a `MetricsCollector` class to handle the tracking of
various service metrics like counters, timers, and gauges. It is used to
monitor the performance and behavior of the application in a centralized way.

Typical usage example:

  metrics = MetricsCollector()
  metrics.increment("requests.total")
  
  start_time = time.time()
  # ... some operation ...
  duration = (time.time() - start_time) * 1000
  metrics.record_time("operation.duration_ms", duration)
  
  summary = metrics.get_summary()
"""

import time
from typing import Dict, Any
from datetime import datetime
from collections import defaultdict


class MetricsCollector:
    """Collects and aggregates service metrics in memory.

    This class provides a simple, in-memory solution for tracking application
    metrics. It is not thread-safe by default and is intended for use in a
    single-threaded or async context where access is controlled.

    Attributes:
        start_time (float): The timestamp when the collector was instantiated.
        counters (defaultdict): A dictionary to store counter metrics.
        timers (defaultdict): A dictionary to store lists of timing metrics.
        gauges (dict): A dictionary to store gauge metrics.
    """

    def __init__(self):
        """Initializes the MetricsCollector and sets the start time."""
        self.start_time = time.time()
        self.counters = defaultdict(int)
        self.timers = defaultdict(list)
        self.gauges = {}

    def increment(self, metric: str, value: int = 1):
        """Increments a counter metric by a given value.

        If the metric does not exist, it is created with the given value.

        Args:
            metric (str): The name of the counter metric.
            value (int, optional): The value to increment by. Defaults to 1.
        """
        self.counters[metric] += value

    def record_time(self, metric: str, duration_ms: float):
        """Records a timing measurement for a metric.

        Appends the duration to a list of measurements for the specified metric.

        Args:
            metric (str): The name of the timer metric.
            duration_ms (float): The duration in milliseconds to record.
        """
        self.timers[metric].append(duration_ms)

    def set_gauge(self, metric: str, value: Any):
        """Sets the value of a gauge metric.

        Gauges represent a value that can go up or down, like the number of
        active connections.

        Args:
            metric (str): The name of the gauge metric.
            value (Any): The value to set.
        """
        self.gauges[metric] = value

    def get_uptime(self) -> int:
        """Calculates the service uptime in seconds.

        Returns:
            int: The number of seconds since the collector was initialized.
        """
        return int(time.time() - self.start_time)

    def get_summary(self) -> Dict[str, Any]:
        """Generates a summary of all collected metrics.

        This method compiles all counters, gauges, and timer statistics (count,
        average, min, max) into a single dictionary.

        Returns:
            Dict[str, Any]: A dictionary containing the metrics summary.
        """
        summary = {
            'timestamp': datetime.utcnow().isoformat(),
            'uptime_seconds': self.get_uptime(),
            'counters': dict(self.counters),
            'gauges': dict(self.gauges),
            'timers': {}
        }

        # Calculate timer statistics
        for metric, times in self.timers.items():
            if times:
                summary['timers'][metric] = {
                    'count': len(times),
                    'avg_ms': sum(times) / len(times),
                    'min_ms': min(times),
                    'max_ms': max(times)
                }

        return summary

    def reset(self):
        """Resets all collected metrics to their initial state."""
        self.counters.clear()
        self.timers.clear()
        self.gauges.clear()