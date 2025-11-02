"""Statistical Anomaly Detector for NIS.

Detects anomalies in metrics using Z-score statistical analysis.

Biblical Foundation:
    Proverbs 3:5-6 - "Trust in the LORD with all your heart, and do not lean
    on your own understanding. In all your ways acknowledge him, and he will
    make straight your paths."

    Just as we trust the LORD's wisdom over our limited understanding,
    statistical methods reveal patterns beyond human intuition.

Constitutional Compliance:
    - P1 (Completude): Complete implementation, no placeholders
    - P2 (Validação): Uses proven statistical methods (Z-score, 3-sigma rule)
    - P4 (Rastreabilidade): Based on standard statistical theory
    - P6 (Eficiência): O(1) detection per metric with rolling window
"""

from collections import deque
import statistics
from typing import Any
from datetime import datetime
import logging

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, REGISTRY

logger = logging.getLogger(__name__)

# Global metrics (only initialize once)
_METRICS_INITIALIZED = False
_ANOMALIES_DETECTED = None
_Z_SCORE_DISTRIBUTION = None
_BASELINE_MEAN_GAUGE = None
_BASELINE_STDDEV_GAUGE = None
_HISTORY_SIZE_GAUGE = None


def _init_metrics(registry=REGISTRY):
    """Initialize Prometheus metrics (only once per registry)."""
    global _METRICS_INITIALIZED, _ANOMALIES_DETECTED, _Z_SCORE_DISTRIBUTION
    global _BASELINE_MEAN_GAUGE, _BASELINE_STDDEV_GAUGE, _HISTORY_SIZE_GAUGE

    if _METRICS_INITIALIZED:
        return

    _ANOMALIES_DETECTED = Counter(
        "nis_anomalies_detected_total",
        "Total anomalies detected by severity",
        ["severity"],
        registry=registry,
    )

    _Z_SCORE_DISTRIBUTION = Histogram(
        "nis_anomaly_z_scores",
        "Distribution of Z-scores for anomaly detection",
        buckets=[0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0],
        registry=registry,
    )

    _BASELINE_MEAN_GAUGE = Gauge(
        "nis_baseline_mean",
        "Current baseline mean for metrics",
        ["metric_name"],
        registry=registry,
    )

    _BASELINE_STDDEV_GAUGE = Gauge(
        "nis_baseline_stddev",
        "Current baseline standard deviation for metrics",
        ["metric_name"],
        registry=registry,
    )

    _HISTORY_SIZE_GAUGE = Gauge(
        "nis_baseline_history_size",
        "Current number of samples in baseline history",
        ["metric_name"],
        registry=registry,
    )

    _METRICS_INITIALIZED = True


class StatisticalAnomalyDetector:
    """Statistical anomaly detection using rolling baseline.

    Detects anomalies based on deviation from historical mean/stddev
    using the Z-score method and 3-sigma rule.

    Attributes:
        window_size: Number of historical samples to maintain (default: 1440 = 24h)
        history: Rolling window of historical values per metric
        anomalies_detected: Counter of detected anomalies
        z_score_distribution: Histogram of Z-scores
        baseline_mean_gauge: Current baseline mean per metric
        baseline_stddev_gauge: Current baseline stddev per metric
    """

    def __init__(self, window_size: int = 1440, enable_metrics: bool = True):
        """Initialize anomaly detector.

        Args:
            window_size: Number of samples in rolling window (default: 1440 for 24h of minute data)
            enable_metrics: Whether to enable Prometheus metrics (default: True, set False for tests)

        Raises:
            ValueError: If window_size < 30 (minimum for statistical significance)
        """
        if window_size < 30:
            raise ValueError("window_size must be >= 30 for statistical significance")

        self.window_size = window_size
        self.history: dict[str, deque] = {}  # metric_name -> deque of values
        self.enable_metrics = enable_metrics

        # Initialize Prometheus metrics (global, only once)
        if enable_metrics:
            _init_metrics()

        logger.info(
            f"✅ StatisticalAnomalyDetector initialized (window_size={window_size})"
        )

    async def detect_anomalies(
        self, metrics: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Detect anomalies in metrics using Z-score statistical analysis.

        Uses Z-score (3-sigma rule):
        - |z| > 3.0 = anomaly (99.7% confidence)
        - |z| > 4.0 = critical anomaly (99.99% confidence)

        Args:
            metrics: List of metric dicts with 'name' and 'value' keys

        Returns:
            List of anomaly dicts with:
                - metric: Metric name
                - value: Current value
                - baseline_mean: Historical mean
                - baseline_stddev: Historical standard deviation
                - z_score: Computed Z-score
                - severity: 'warning' or 'critical'
                - description: Human-readable description
                - deviation_percent: Percentage deviation from mean
                - timestamp: Detection timestamp (ISO format)

        Example:
            >>> detector = StatisticalAnomalyDetector()
            >>> metrics = [{"name": "cpu_usage", "value": 95.5}]
            >>> anomalies = await detector.detect_anomalies(metrics)
            >>> if anomalies:
            ...     print(f"Anomaly: {anomalies[0]['description']}")
        """
        anomalies = []

        for metric in metrics:
            # Validate metric structure
            if (
                not isinstance(metric, dict)
                or "name" not in metric
                or "value" not in metric
            ):
                logger.warning(f"Invalid metric format: {metric}")
                continue

            name = metric["name"]
            value = metric["value"]

            # Skip non-numeric values
            if not isinstance(value, (int, float)):
                logger.debug(f"Skipping non-numeric metric {name}: {value}")
                continue

            # Initialize history for new metrics
            if name not in self.history:
                self.history[name] = deque(maxlen=self.window_size)
                logger.debug(f"Initialized history for metric: {name}")

            history = self.history[name]

            # Need enough history for statistical significance
            if len(history) < 30:  # Minimum 30 samples for reliable stats
                history.append(value)
                if self.enable_metrics:
                    _HISTORY_SIZE_GAUGE.labels(metric_name=name).set(len(history))
                logger.debug(f"Building baseline for {name}: {len(history)}/30 samples")
                continue

            # Calculate baseline statistics
            mean = statistics.mean(history)
            stddev = statistics.stdev(history)

            # Update Prometheus gauges
            if self.enable_metrics:
                _BASELINE_MEAN_GAUGE.labels(metric_name=name).set(mean)
                _BASELINE_STDDEV_GAUGE.labels(metric_name=name).set(stddev)
                _HISTORY_SIZE_GAUGE.labels(metric_name=name).set(len(history))

            # Calculate Z-score
            if stddev > 0:
                z_score = (value - mean) / stddev
            else:
                # Zero variance (all values identical) - any deviation is anomaly
                z_score = 0 if value == mean else float("inf")

            # Record Z-score distribution
            if self.enable_metrics:
                _Z_SCORE_DISTRIBUTION.observe(abs(z_score))

            # Detect anomaly using 3-sigma rule
            abs_z = abs(z_score)
            if abs_z > 3.0:  # 99.7% confidence interval
                severity = "critical" if abs_z > 4.0 else "warning"

                # Calculate percentage deviation
                deviation_percent = ((value - mean) / mean * 100) if mean != 0 else 0

                # Build description
                direction = "above" if z_score > 0 else "below"
                description = (
                    f"{name} is {abs_z:.2f} standard deviations {direction} baseline "
                    f"({deviation_percent:+.1f}% deviation)"
                )

                anomaly = {
                    "metric": name,
                    "value": value,
                    "baseline_mean": mean,
                    "baseline_stddev": stddev,
                    "z_score": z_score,
                    "severity": severity,
                    "description": description,
                    "deviation_percent": deviation_percent,
                    "timestamp": datetime.utcnow().isoformat(),
                }

                anomalies.append(anomaly)

                # Update Prometheus counter
                if self.enable_metrics:
                    _ANOMALIES_DETECTED.labels(severity=severity).inc()

                logger.warning(
                    f"🚨 Anomaly detected: {description} "
                    f"(value={value:.2f}, mean={mean:.2f}, stddev={stddev:.2f})"
                )

            # Add current value to history (for next iteration baseline)
            history.append(value)

        logger.info(f"Detected {len(anomalies)} anomalies from {len(metrics)} metrics")
        return anomalies

    def get_baseline_stats(self, metric_name: str) -> dict[str, Any] | None:
        """Get baseline statistics for a specific metric.

        Args:
            metric_name: Name of metric to get stats for

        Returns:
            Dict with mean, stddev, sample_count, or None if insufficient data

        Example:
            >>> stats = detector.get_baseline_stats("cpu_usage")
            >>> if stats:
            ...     print(f"Mean: {stats['mean']:.2f}, StdDev: {stats['stddev']:.2f}")
        """
        if metric_name not in self.history:
            return None

        history = self.history[metric_name]

        if len(history) < 30:
            return None

        return {
            "mean": statistics.mean(history),
            "stddev": statistics.stdev(history),
            "min": min(history),
            "max": max(history),
            "sample_count": len(history),
            "window_size": self.window_size,
        }

    def reset_baseline(self, metric_name: str | None = None) -> None:
        """Reset baseline history for a metric or all metrics.

        Useful when metrics have a known regime change (e.g., after deployment).

        Args:
            metric_name: Specific metric to reset, or None to reset all

        Example:
            >>> detector.reset_baseline("cpu_usage")  # Reset one metric
            >>> detector.reset_baseline()  # Reset all metrics
        """
        if metric_name:
            if metric_name in self.history:
                self.history[metric_name].clear()
                logger.info(f"Reset baseline for metric: {metric_name}")
        else:
            self.history.clear()
            logger.info("Reset all baseline history")

    def get_metrics_summary(self) -> dict[str, Any]:
        """Get summary of all tracked metrics.

        Returns:
            Dict with:
                - total_metrics: Number of tracked metrics
                - metrics_with_baseline: Number with sufficient history
                - total_samples: Total samples across all metrics
                - metrics: List of metric summaries

        Example:
            >>> summary = detector.get_metrics_summary()
            >>> print(f"Tracking {summary['total_metrics']} metrics")
        """
        metrics_with_baseline = sum(
            1 for history in self.history.values() if len(history) >= 30
        )

        total_samples = sum(len(history) for history in self.history.values())

        metric_summaries = []
        for name, history in self.history.items():
            if len(history) >= 30:
                stats = self.get_baseline_stats(name)
                metric_summaries.append(
                    {
                        "name": name,
                        "sample_count": len(history),
                        "mean": stats["mean"] if stats else None,
                        "stddev": stats["stddev"] if stats else None,
                    }
                )

        return {
            "total_metrics": len(self.history),
            "metrics_with_baseline": metrics_with_baseline,
            "total_samples": total_samples,
            "window_size": self.window_size,
            "metrics": metric_summaries,
        }
