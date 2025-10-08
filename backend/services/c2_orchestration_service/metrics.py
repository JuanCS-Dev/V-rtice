"""Maximus C2 Orchestration Service - Metrics Utilities.

This module provides utilities for collecting, tracking, and reporting
operational metrics within the Command and Control (C2) Orchestration service.
It enables Maximus AI to monitor the performance and efficiency of its command
execution, task coordination, and overall operational control.

Metrics collected can include:
- Number of commands issued and completed.
- Latency of command execution and task distribution.
- Success rates of various C2 operations.
- Uptime and health of integrated C2 frameworks (e.g., Metasploit, Cobalt Strike).

This module is crucial for performance monitoring, operational auditing, and
continuous improvement of the C2 Orchestration capabilities.
"""

from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, Optional


class MetricsCollector:
    """Collects, tracks, and reports operational metrics for the C2 Orchestration service.

    Enables Maximus AI to monitor the performance and efficiency of its command
    execution, task coordination, and overall operational control.
    """

    def __init__(self):
        """Initializes the MetricsCollector."""
        self.metrics: Dict[str, Any] = defaultdict(lambda: {"count": 0, "total_time": 0.0, "last_update": None})
        self.start_time = datetime.now()

    def record_metric(self, metric_name: str, value: Optional[float] = None):
        """Records a single metric event.

        Args:
            metric_name (str): The name of the metric.
            value (Optional[float]): An optional numerical value associated with the metric (e.g., latency).
        """
        self.metrics[metric_name]["count"] += 1
        if value is not None:
            self.metrics[metric_name]["total_time"] += value
        self.metrics[metric_name]["last_update"] = datetime.now().isoformat()

    def get_metric(self, metric_name: str) -> Dict[str, Any]:
        """Retrieves the current data for a specific metric.

        Args:
            metric_name (str): The name of the metric to retrieve.

        Returns:
            Dict[str, Any]: A dictionary containing the metric's count, total time, average time (if applicable), and last update.
        """
        metric_data = self.metrics[metric_name]
        if metric_data["count"] > 0 and metric_data["total_time"] > 0:
            metric_data["average_time"] = metric_data["total_time"] / metric_data["count"]
        else:
            metric_data["average_time"] = 0.0
        return dict(metric_data)

    def get_all_metrics(self) -> Dict[str, Any]:
        """Retrieves all recorded metrics.

        Returns:
            Dict[str, Any]: A dictionary containing all metrics and their data.
        """
        all_metrics = {}
        for name in self.metrics:
            all_metrics[name] = self.get_metric(name)
        return all_metrics

    def get_uptime(self) -> float:
        """Returns the uptime of the metrics collector in seconds.

        Returns:
            float: The uptime in seconds.
        """
        return (datetime.now() - self.start_time).total_seconds()
