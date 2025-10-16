"""Tests for vertice_core.metrics module."""

from vertice_core.metrics import create_service_metrics


class TestCreateServiceMetrics:
    """Tests for create_service_metrics function."""

    def test_creates_all_standard_metrics(self) -> None:
        """Test that all standard metrics are created."""
        metrics = create_service_metrics("unique_test_service")

        assert "requests_total" in metrics
        assert "request_duration_seconds" in metrics
        assert "active_requests" in metrics
        assert "errors_total" in metrics
        assert "service_info" in metrics

    def test_normalizes_service_name(self) -> None:
        """Test that service name is normalized for metric names."""
        metrics = create_service_metrics("my-test-service")

        metric_name = str(metrics["requests_total"])
        assert "my_test_service" in metric_name
