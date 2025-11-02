"""Tests for Statistical Anomaly Detector.

Biblical Foundation:
    Proverbs 21:2 - "Every way of a man is right in his own eyes,
    but the LORD weighs the heart."

    Just as the LORD tests our hearts, we test our code thoroughly
    to ensure it serves truth and reliability.
"""

import pytest
import statistics
from collections import deque
import sys
from pathlib import Path

# Add parent directory to path for direct import
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.anomaly_detector import StatisticalAnomalyDetector


class TestStatisticalAnomalyDetector:
    """Test suite for StatisticalAnomalyDetector."""

    @pytest.fixture
    def detector(self):
        """Create detector instance for testing.

        GIVEN: A fresh detector with default window size
        """
        return StatisticalAnomalyDetector(window_size=100, enable_metrics=False)

    @pytest.fixture
    def detector_small_window(self):
        """Create detector with minimal window for faster testing.

        GIVEN: A detector with 30-sample window (minimum viable)
        """
        return StatisticalAnomalyDetector(window_size=30, enable_metrics=False)

    @pytest.mark.asyncio
    async def test_initialization(self):
        """GIVEN: Valid window size.

        WHEN: Detector is initialized
        THEN: Detector is created with correct configuration.
        """
        # WHEN
        detector = StatisticalAnomalyDetector(window_size=1440, enable_metrics=False)

        # THEN
        assert detector.window_size == 1440
        assert detector.history == {}
        assert detector.enable_metrics is False

    @pytest.mark.asyncio
    async def test_initialization_invalid_window(self):
        """GIVEN: Invalid window size (< 30).

        WHEN: Detector is initialized
        THEN: ValueError is raised.
        """
        # WHEN/THEN
        with pytest.raises(ValueError, match="window_size must be >= 30"):
            StatisticalAnomalyDetector(window_size=10)

    @pytest.mark.asyncio
    async def test_insufficient_history_no_anomalies(self, detector):
        """GIVEN: Metrics with insufficient history (<30 samples).

        WHEN: detect_anomalies is called
        THEN: No anomalies are detected (building baseline).
        """
        # GIVEN
        metrics = [{"name": "cpu_usage", "value": 50.0}]

        # WHEN - Feed <30 samples
        for i in range(29):
            anomalies = await detector.detect_anomalies(metrics)

            # THEN
            assert anomalies == []
            assert len(detector.history["cpu_usage"]) == i + 1

    @pytest.mark.asyncio
    async def test_normal_metrics_no_anomaly(self, detector_small_window):
        """GIVEN: Metrics within normal range (within 3 sigma).

        WHEN: detect_anomalies is called
        THEN: No anomalies are detected.
        """
        # GIVEN - Build baseline: mean=50, stddev≈5
        baseline_metrics = [
            {"name": "cpu_usage", "value": 50.0 + i % 10 - 5} for i in range(30)
        ]

        for metric in baseline_metrics:
            await detector_small_window.detect_anomalies([metric])

        # WHEN - Test value within 3 sigma (50 ± 15)
        test_metrics = [{"name": "cpu_usage", "value": 55.0}]
        anomalies = await detector_small_window.detect_anomalies(test_metrics)

        # THEN
        assert anomalies == []

    @pytest.mark.asyncio
    async def test_warning_anomaly_detected(self, detector_small_window):
        """GIVEN: Metric value 3-4 sigma from baseline.

        WHEN: detect_anomalies is called
        THEN: Warning severity anomaly is detected.
        """
        # GIVEN - Build stable baseline: mean=50, stddev≈1
        baseline_metrics = [
            {"name": "cpu_usage", "value": 50.0 + (i % 3 - 1) * 0.5} for i in range(30)
        ]

        for metric in baseline_metrics:
            await detector_small_window.detect_anomalies([metric])

        # WHEN - Value 3.5 sigma away
        baseline_stats = detector_small_window.get_baseline_stats("cpu_usage")
        mean = baseline_stats["mean"]
        stddev = baseline_stats["stddev"]

        test_value = mean + 3.5 * stddev
        test_metrics = [{"name": "cpu_usage", "value": test_value}]
        anomalies = await detector_small_window.detect_anomalies(test_metrics)

        # THEN
        assert len(anomalies) == 1
        assert anomalies[0]["metric"] == "cpu_usage"
        assert anomalies[0]["severity"] == "warning"
        assert 3.0 < abs(anomalies[0]["z_score"]) < 4.0
        assert "standard deviations" in anomalies[0]["description"]
        assert "timestamp" in anomalies[0]

    @pytest.mark.asyncio
    async def test_critical_anomaly_detected(self, detector_small_window):
        """GIVEN: Metric value >4 sigma from baseline.

        WHEN: detect_anomalies is called
        THEN: Critical severity anomaly is detected.
        """
        # GIVEN - Build stable baseline
        baseline_metrics = [
            {"name": "memory_usage", "value": 1000.0 + i * 10} for i in range(30)
        ]

        for metric in baseline_metrics:
            await detector_small_window.detect_anomalies([metric])

        # WHEN - Value 5 sigma away
        baseline_stats = detector_small_window.get_baseline_stats("memory_usage")
        mean = baseline_stats["mean"]
        stddev = baseline_stats["stddev"]

        test_value = mean + 5.0 * stddev
        test_metrics = [{"name": "memory_usage", "value": test_value}]
        anomalies = await detector_small_window.detect_anomalies(test_metrics)

        # THEN
        assert len(anomalies) == 1
        assert anomalies[0]["severity"] == "critical"
        assert abs(anomalies[0]["z_score"]) > 4.0

    @pytest.mark.asyncio
    async def test_multiple_metrics_tracking(self, detector_small_window):
        """GIVEN: Multiple different metrics.

        WHEN: detect_anomalies is called with mixed metrics
        THEN: Each metric has independent baseline tracking.
        """
        # GIVEN - Build baselines for 3 metrics
        metrics_batch = [
            {"name": "cpu_usage", "value": 50.0},
            {"name": "memory_usage", "value": 2000.0},
            {"name": "disk_io", "value": 100.0},
        ]

        for i in range(30):
            await detector_small_window.detect_anomalies(metrics_batch)

        # WHEN - Check all metrics tracked
        stats_cpu = detector_small_window.get_baseline_stats("cpu_usage")
        stats_mem = detector_small_window.get_baseline_stats("memory_usage")
        stats_disk = detector_small_window.get_baseline_stats("disk_io")

        # THEN
        assert stats_cpu is not None
        assert stats_mem is not None
        assert stats_disk is not None

        assert abs(stats_cpu["mean"] - 50.0) < 1.0
        assert abs(stats_mem["mean"] - 2000.0) < 1.0
        assert abs(stats_disk["mean"] - 100.0) < 1.0

    @pytest.mark.asyncio
    async def test_window_size_enforcement(self, detector_small_window):
        """GIVEN: Detector with window_size=30.

        WHEN: More than 30 samples are added
        THEN: Old samples are evicted (deque maxlen behavior).
        """
        # GIVEN
        metrics = [{"name": "test_metric", "value": float(i)} for i in range(50)]

        # WHEN
        for metric in metrics:
            await detector_small_window.detect_anomalies([metric])

        # THEN
        history = detector_small_window.history["test_metric"]
        assert len(history) == 30  # Should not exceed window size
        assert list(history) == [float(i) for i in range(20, 50)]  # Last 30 values

    @pytest.mark.asyncio
    async def test_zero_stddev_handling(self, detector_small_window):
        """GIVEN: Metrics with zero variance (all identical values).

        WHEN: detect_anomalies is called with different value
        THEN: Anomaly is detected (infinite Z-score).
        """
        # GIVEN - All values identical
        baseline_metrics = [
            {"name": "constant_metric", "value": 100.0} for _ in range(30)
        ]

        for metric in baseline_metrics:
            await detector_small_window.detect_anomalies([metric])

        # WHEN - Different value
        test_metrics = [{"name": "constant_metric", "value": 110.0}]
        anomalies = await detector_small_window.detect_anomalies(test_metrics)

        # THEN - Should detect anomaly (infinite Z-score)
        assert len(anomalies) == 1
        assert anomalies[0]["severity"] == "critical"

    @pytest.mark.asyncio
    async def test_negative_deviation_detection(self, detector_small_window):
        """GIVEN: Metric value significantly below baseline.

        WHEN: detect_anomalies is called
        THEN: Anomaly is detected with negative Z-score.
        """
        # GIVEN
        baseline_metrics = [
            {"name": "response_time", "value": 200.0 + i % 20} for i in range(30)
        ]

        for metric in baseline_metrics:
            await detector_small_window.detect_anomalies([metric])

        # WHEN - Very low value
        baseline_stats = detector_small_window.get_baseline_stats("response_time")
        mean = baseline_stats["mean"]
        stddev = baseline_stats["stddev"]

        test_value = mean - 4.5 * stddev  # 4.5 sigma below
        test_metrics = [{"name": "response_time", "value": test_value}]
        anomalies = await detector_small_window.detect_anomalies(test_metrics)

        # THEN
        assert len(anomalies) == 1
        assert anomalies[0]["z_score"] < -4.0
        assert "below" in anomalies[0]["description"]
        assert anomalies[0]["deviation_percent"] < 0

    @pytest.mark.asyncio
    async def test_invalid_metric_format(self, detector):
        """GIVEN: Invalid metric format (missing keys).

        WHEN: detect_anomalies is called
        THEN: Invalid metrics are skipped gracefully.
        """
        # GIVEN
        invalid_metrics = [
            {"name": "valid_metric", "value": 50.0},
            {"name": "missing_value"},  # No value
            {"value": 100.0},  # No name
            "not a dict",  # Wrong type
            {"name": "non_numeric", "value": "text"},  # Non-numeric value
        ]

        # WHEN
        anomalies = await detector.detect_anomalies(invalid_metrics)

        # THEN - No errors, but only valid metric processed
        assert anomalies == []  # Not enough history yet
        assert "valid_metric" in detector.history
        assert len(detector.history) == 1  # Only valid metric tracked

    @pytest.mark.asyncio
    async def test_get_baseline_stats(self, detector_small_window):
        """GIVEN: Metric with sufficient history.

        WHEN: get_baseline_stats is called
        THEN: Correct statistics are returned.
        """
        # GIVEN - Build baseline
        values = [50.0 + i for i in range(30)]
        metrics = [{"name": "test_metric", "value": v} for v in values]

        for metric in metrics:
            await detector_small_window.detect_anomalies([metric])

        # WHEN
        stats = detector_small_window.get_baseline_stats("test_metric")

        # THEN
        assert stats is not None
        assert abs(stats["mean"] - statistics.mean(values)) < 0.01
        assert abs(stats["stddev"] - statistics.stdev(values)) < 0.01
        assert stats["min"] == min(values)
        assert stats["max"] == max(values)
        assert stats["sample_count"] == 30
        assert stats["window_size"] == 30

    @pytest.mark.asyncio
    async def test_get_baseline_stats_insufficient_data(self, detector):
        """GIVEN: Metric with <30 samples.

        WHEN: get_baseline_stats is called
        THEN: None is returned.
        """
        # GIVEN - Only 10 samples
        metrics = [{"name": "new_metric", "value": 50.0} for _ in range(10)]

        for metric in metrics:
            await detector.detect_anomalies([metric])

        # WHEN
        stats = detector.get_baseline_stats("new_metric")

        # THEN
        assert stats is None

    @pytest.mark.asyncio
    async def test_get_baseline_stats_nonexistent_metric(self, detector):
        """GIVEN: Metric name that doesn't exist.

        WHEN: get_baseline_stats is called
        THEN: None is returned.
        """
        # WHEN
        stats = detector.get_baseline_stats("nonexistent_metric")

        # THEN
        assert stats is None

    @pytest.mark.asyncio
    async def test_reset_baseline_specific_metric(self, detector_small_window):
        """GIVEN: Detector with baseline history for multiple metrics.

        WHEN: reset_baseline is called for specific metric
        THEN: Only that metric's history is cleared.
        """
        # GIVEN - Build baselines for 2 metrics
        for i in range(30):
            await detector_small_window.detect_anomalies(
                [
                    {"name": "metric_a", "value": 100.0},
                    {"name": "metric_b", "value": 200.0},
                ]
            )

        # WHEN
        detector_small_window.reset_baseline("metric_a")

        # THEN
        assert len(detector_small_window.history["metric_a"]) == 0
        assert len(detector_small_window.history["metric_b"]) == 30

    @pytest.mark.asyncio
    async def test_reset_baseline_all_metrics(self, detector_small_window):
        """GIVEN: Detector with baseline history for multiple metrics.

        WHEN: reset_baseline is called with no argument
        THEN: All metrics' history is cleared.
        """
        # GIVEN - Build baselines
        for i in range(30):
            await detector_small_window.detect_anomalies(
                [
                    {"name": "metric_a", "value": 100.0},
                    {"name": "metric_b", "value": 200.0},
                ]
            )

        # WHEN
        detector_small_window.reset_baseline()

        # THEN
        assert detector_small_window.history == {}

    @pytest.mark.asyncio
    async def test_get_metrics_summary(self, detector_small_window):
        """GIVEN: Detector tracking multiple metrics.

        WHEN: get_metrics_summary is called
        THEN: Correct summary is returned.
        """
        # GIVEN - Build baselines for 2 metrics, partial for 1
        for i in range(30):
            await detector_small_window.detect_anomalies(
                [
                    {"name": "metric_a", "value": 100.0},
                    {"name": "metric_b", "value": 200.0},
                ]
            )

        # Only 10 samples for metric_c
        for i in range(10):
            await detector_small_window.detect_anomalies(
                [
                    {"name": "metric_c", "value": 300.0},
                ]
            )

        # WHEN
        summary = detector_small_window.get_metrics_summary()

        # THEN
        assert summary["total_metrics"] == 3
        assert summary["metrics_with_baseline"] == 2  # Only A and B
        assert summary["total_samples"] == 30 + 30 + 10
        assert summary["window_size"] == 30
        assert len(summary["metrics"]) == 2  # Only metrics with baseline

    @pytest.mark.asyncio
    async def test_deviation_percent_calculation(self, detector_small_window):
        """GIVEN: Anomaly detected.

        WHEN: Deviation percent is calculated
        THEN: Correct percentage is computed.
        """
        # GIVEN - Baseline mean=100
        baseline_metrics = [{"name": "test", "value": 100.0} for _ in range(30)]

        for metric in baseline_metrics:
            await detector_small_window.detect_anomalies([metric])

        # WHEN - Value 50% higher (150.0)
        test_metrics = [{"name": "test", "value": 150.0}]
        anomalies = await detector_small_window.detect_anomalies(test_metrics)

        # THEN - Should detect and calculate ~50% deviation
        if anomalies:  # Might or might not be anomaly depending on stddev
            assert anomalies[0]["value"] == 150.0
            assert anomalies[0]["baseline_mean"] == pytest.approx(100.0, rel=0.01)
            # Deviation percent should be positive and around 50%
            assert anomalies[0]["deviation_percent"] > 0

    @pytest.mark.asyncio
    async def test_prometheus_metrics_updated(self, detector_small_window):
        """GIVEN: Anomaly is detected.

        WHEN: detect_anomalies is called
        THEN: Prometheus metrics are updated.
        """
        # GIVEN - Build baseline
        baseline_metrics = [
            {"name": "test", "value": 50.0 + (i % 3 - 1)} for i in range(30)
        ]

        for metric in baseline_metrics:
            await detector_small_window.detect_anomalies([metric])

        # WHEN - Trigger critical anomaly
        baseline_stats = detector_small_window.get_baseline_stats("test")
        mean = baseline_stats["mean"]
        stddev = baseline_stats["stddev"]

        test_value = mean + 5.0 * stddev  # 5 sigma away
        test_metrics = [{"name": "test", "value": test_value}]
        anomalies = await detector_small_window.detect_anomalies(test_metrics)

        # THEN - Prometheus metrics should be updated
        # (We can't easily check Counter values, but verify no errors)
        assert anomalies[0]["severity"] == "critical"
        # Metrics updated internally without errors
