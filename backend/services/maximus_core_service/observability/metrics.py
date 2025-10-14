"""
Metrics Collector - Prometheus metrics for observability
========================================================

Provides Prometheus-compatible metrics collection for MAXIMUS components.

Metrics Types:
- Counters: Monotonically increasing values (e.g., total requests)
- Gauges: Values that can go up or down (e.g., queue depth)
- Histograms: Distribution of values (e.g., latencies)

Authors: Claude Code (Tactical Executor)
Date: 2025-10-14
Governance: Constituição Vértice v2.5 - Article IV (Operational Excellence)
"""

from prometheus_client import Counter, Gauge, Histogram
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Prometheus metrics collector for MAXIMUS components.

    Automatically creates and manages Prometheus metrics with
    consistent naming conventions.

    Usage:
        metrics = MetricsCollector("prefrontal_cortex")

        # Increment counter
        metrics.increment("signals_processed")

        # Set gauge value
        metrics.set_gauge("active_connections", 42)

        # Record histogram value (e.g., latency)
        metrics.observe("processing_time_seconds", 0.125)
    """

    # Class-level metric registries (prevents duplicate registration)
    _counters: Dict[str, Counter] = {}
    _gauges: Dict[str, Gauge] = {}
    _histograms: Dict[str, Histogram] = {}

    def __init__(self, service: str):
        """Initialize Metrics Collector.

        Args:
            service: Service name (used as metric prefix)
        """
        self.service = service
        self.prefix = f"maximus_{service.lower().replace('-', '_')}_"

        logger.info(f"MetricsCollector initialized: service={service}, prefix={self.prefix}")

    def increment(self, metric_name: str, value: float = 1.0, **labels: Any) -> None:
        """Increment a counter metric.

        Args:
            metric_name: Metric name (without prefix)
            value: Increment amount (default: 1.0)
            **labels: Optional labels (e.g., status="success")
        """
        full_name = f"{self.prefix}{metric_name}_total"

        # Get or create counter
        if full_name not in self._counters:
            self._counters[full_name] = Counter(
                full_name,
                f"{self.service} {metric_name} total",
                list(labels.keys()) if labels else []
            )

        # Increment
        if labels:
            self._counters[full_name].labels(**labels).inc(value)
        else:
            self._counters[full_name].inc(value)

    def set_gauge(self, metric_name: str, value: float, **labels: Any) -> None:
        """Set a gauge metric value.

        Args:
            metric_name: Metric name (without prefix)
            value: Current value
            **labels: Optional labels
        """
        full_name = f"{self.prefix}{metric_name}"

        # Get or create gauge
        if full_name not in self._gauges:
            self._gauges[full_name] = Gauge(
                full_name,
                f"{self.service} {metric_name}",
                list(labels.keys()) if labels else []
            )

        # Set value
        if labels:
            self._gauges[full_name].labels(**labels).set(value)
        else:
            self._gauges[full_name].set(value)

    def observe(self, metric_name: str, value: float, **labels: Any) -> None:
        """Observe a histogram metric value.

        Args:
            metric_name: Metric name (without prefix)
            value: Observed value (e.g., latency in seconds)
            **labels: Optional labels
        """
        full_name = f"{self.prefix}{metric_name}"

        # Get or create histogram
        if full_name not in self._histograms:
            self._histograms[full_name] = Histogram(
                full_name,
                f"{self.service} {metric_name}",
                list(labels.keys()) if labels else []
            )

        # Observe value
        if labels:
            self._histograms[full_name].labels(**labels).observe(value)
        else:
            self._histograms[full_name].observe(value)

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of registered metrics.

        Returns:
            Dictionary with metric counts by type
        """
        return {
            "service": self.service,
            "counters": len([k for k in self._counters if k.startswith(self.prefix)]),
            "gauges": len([k for k in self._gauges if k.startswith(self.prefix)]),
            "histograms": len([k for k in self._histograms if k.startswith(self.prefix)]),
        }

    def __repr__(self) -> str:
        summary = self.get_metrics_summary()
        return (
            f"MetricsCollector("
            f"service={self.service}, "
            f"counters={summary['counters']}, "
            f"gauges={summary['gauges']}, "
            f"histograms={summary['histograms']})"
        )
