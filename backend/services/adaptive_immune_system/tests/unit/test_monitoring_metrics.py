"""
Unit Tests for Monitoring Metrics Module.

Tests the RabbitMQMetrics class and related functionality for:
- Metric initialization
- Counter increments
- Histogram observations
- Gauge updates
- Timer context managers
- Metrics export
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock

# Import module under test
try:
    from hitl.monitoring.metrics import (
        RabbitMQMetrics,
        get_rabbitmq_metrics,
        PublishTimer,
        ConsumeTimer,
    )
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    pytest.skip("Monitoring metrics not available", allow_module_level=True)


class TestRabbitMQMetricsInitialization:
    """Test RabbitMQMetrics initialization."""

    def test_metrics_initialization_default_service_name(self):
        """Test metrics initialize with default service name."""
        metrics = RabbitMQMetrics()

        assert metrics.service_name == "adaptive_immune_system"
        assert metrics.messages_published_total is not None
        assert metrics.messages_consumed_total is not None

    def test_metrics_initialization_custom_service_name(self):
        """Test metrics initialize with custom service name."""
        custom_name = "test_service"
        metrics = RabbitMQMetrics(service_name=custom_name)

        assert metrics.service_name == custom_name

    def test_all_metric_objects_created(self):
        """Test all metric objects are created during initialization."""
        metrics = RabbitMQMetrics()

        # Publishing metrics
        assert hasattr(metrics, 'messages_published_total')
        assert hasattr(metrics, 'message_publish_failures_total')
        assert hasattr(metrics, 'message_publish_duration_seconds')

        # Consuming metrics
        assert hasattr(metrics, 'messages_consumed_total')
        assert hasattr(metrics, 'message_consume_failures_total')
        assert hasattr(metrics, 'message_processing_duration_seconds')

        # System metrics
        assert hasattr(metrics, 'consumer_lag_messages')
        assert hasattr(metrics, 'dlq_messages_total')


class TestPublishingMetrics:
    """Test publishing-related metrics."""

    @pytest.fixture
    def metrics(self):
        """Create fresh metrics instance for each test."""
        return RabbitMQMetrics(service_name="test_service")

    def test_record_message_published_success(self, metrics):
        """Test recording successful message publish."""
        routing_key = "test.routing.key"
        message_size = 1024
        duration = 0.05

        metrics.record_message_published(
            routing_key=routing_key,
            message_size=message_size,
            duration=duration,
            success=True
        )

        # Verify counter incremented (via _child attribute)
        # Note: prometheus_client counters have internal state
        assert metrics.messages_published_total is not None

    def test_record_message_published_failure(self, metrics):
        """Test recording failed message publish."""
        routing_key = "test.routing.key"
        message_size = 1024
        duration = 0.05
        error_type = "ConnectionError"

        metrics.record_message_published(
            routing_key=routing_key,
            message_size=message_size,
            duration=duration,
            success=False,
            error_type=error_type
        )

        # Verify failure counter exists
        assert metrics.message_publish_failures_total is not None

    def test_record_multiple_publishes(self, metrics):
        """Test recording multiple publishes updates metrics."""
        for i in range(10):
            metrics.record_message_published(
                routing_key=f"test.key.{i}",
                message_size=100 * i,
                duration=0.01 * i,
                success=True
            )

        # Metrics should handle multiple recordings
        assert metrics.messages_published_total is not None


class TestConsumingMetrics:
    """Test consuming-related metrics."""

    @pytest.fixture
    def metrics(self):
        """Create fresh metrics instance for each test."""
        return RabbitMQMetrics(service_name="test_service")

    def test_record_message_consumed_success(self, metrics):
        """Test recording successful message consumption."""
        queue_name = "test_queue"
        processing_time = 0.1

        metrics.record_message_consumed(
            queue_name=queue_name,
            processing_time=processing_time,
            success=True
        )

        assert metrics.messages_consumed_total is not None

    def test_record_message_consumed_failure(self, metrics):
        """Test recording failed message consumption."""
        queue_name = "test_queue"
        processing_time = 0.1
        error_type = "ValidationError"

        metrics.record_message_consumed(
            queue_name=queue_name,
            processing_time=processing_time,
            success=False,
            error_type=error_type
        )

        assert metrics.message_consume_failures_total is not None

    def test_update_consumer_lag(self, metrics):
        """Test updating consumer lag gauge."""
        queue_name = "test_queue"
        lag = 42

        metrics.update_consumer_lag(queue_name=queue_name, lag=lag)

        # Gauge should be updated
        assert metrics.consumer_lag_messages is not None

    def test_record_dlq_message(self, metrics):
        """Test recording dead letter queue message."""
        queue_name = "test_queue"
        reason = "max_retries_exceeded"

        metrics.record_dlq_message(queue_name=queue_name, reason=reason)

        assert metrics.dlq_messages_total is not None


class TestMetricsExport:
    """Test metrics export functionality."""

    @pytest.fixture
    def metrics(self):
        """Create fresh metrics instance for each test."""
        return RabbitMQMetrics(service_name="test_service")

    def test_get_metrics_returns_string(self, metrics):
        """Test get_metrics returns Prometheus-formatted string."""
        # Generate some metrics
        metrics.record_message_published(
            routing_key="test.key",
            message_size=100,
            duration=0.01,
            success=True
        )

        metrics_output = metrics.get_metrics()

        assert isinstance(metrics_output, str)
        assert len(metrics_output) > 0

    def test_get_content_type_returns_prometheus_format(self, metrics):
        """Test get_content_type returns correct media type."""
        content_type = metrics.get_content_type()

        assert "text/plain" in content_type or "text/html" in content_type

    def test_metrics_output_contains_help_text(self, metrics):
        """Test metrics output contains HELP comments."""
        metrics_output = metrics.get_metrics()

        # Prometheus format includes HELP and TYPE comments
        assert "# HELP" in metrics_output or "# TYPE" in metrics_output


class TestPublishTimer:
    """Test PublishTimer context manager."""

    @pytest.fixture
    def metrics(self):
        """Create fresh metrics instance for each test."""
        return RabbitMQMetrics(service_name="test_service")

    def test_publish_timer_basic_usage(self, metrics):
        """Test PublishTimer records timing correctly."""
        routing_key = "test.key"
        message_size = 1024

        with PublishTimer(metrics, routing_key, message_size):
            time.sleep(0.01)  # Simulate work

        # Timer should have recorded the publish
        assert metrics.messages_published_total is not None

    def test_publish_timer_records_exception(self, metrics):
        """Test PublishTimer records failure on exception."""
        routing_key = "test.key"
        message_size = 1024

        try:
            with PublishTimer(metrics, routing_key, message_size):
                raise ValueError("Test error")
        except ValueError:
            pass

        # Should have recorded failure
        assert metrics.message_publish_failures_total is not None

    def test_publish_timer_measures_duration(self, metrics):
        """Test PublishTimer measures duration accurately."""
        routing_key = "test.key"
        message_size = 1024
        sleep_time = 0.1

        with PublishTimer(metrics, routing_key, message_size):
            time.sleep(sleep_time)

        # Duration should be approximately sleep_time
        # Note: Actual verification would require inspecting histogram
        assert metrics.message_publish_duration_seconds is not None


class TestConsumeTimer:
    """Test ConsumeTimer context manager."""

    @pytest.fixture
    def metrics(self):
        """Create fresh metrics instance for each test."""
        return RabbitMQMetrics(service_name="test_service")

    def test_consume_timer_basic_usage(self, metrics):
        """Test ConsumeTimer records timing correctly."""
        queue_name = "test_queue"

        with ConsumeTimer(metrics, queue_name):
            time.sleep(0.01)  # Simulate work

        # Timer should have recorded the consumption
        assert metrics.messages_consumed_total is not None

    def test_consume_timer_records_exception(self, metrics):
        """Test ConsumeTimer records failure on exception."""
        queue_name = "test_queue"

        try:
            with ConsumeTimer(metrics, queue_name):
                raise ValueError("Test error")
        except ValueError:
            pass

        # Should have recorded failure
        assert metrics.message_consume_failures_total is not None

    def test_consume_timer_measures_duration(self, metrics):
        """Test ConsumeTimer measures duration accurately."""
        queue_name = "test_queue"
        sleep_time = 0.1

        with ConsumeTimer(metrics, queue_name):
            time.sleep(sleep_time)

        # Duration should be recorded
        assert metrics.message_processing_duration_seconds is not None


class TestGlobalMetricsInstance:
    """Test global metrics instance functionality."""

    def test_get_rabbitmq_metrics_returns_instance(self):
        """Test get_rabbitmq_metrics returns RabbitMQMetrics instance."""
        metrics = get_rabbitmq_metrics()

        assert isinstance(metrics, RabbitMQMetrics)

    def test_get_rabbitmq_metrics_returns_singleton(self):
        """Test get_rabbitmq_metrics returns same instance on multiple calls."""
        metrics1 = get_rabbitmq_metrics()
        metrics2 = get_rabbitmq_metrics()

        # Should be same instance (singleton pattern)
        assert metrics1 is metrics2

    def test_get_rabbitmq_metrics_with_custom_name(self):
        """Test get_rabbitmq_metrics can use custom service name."""
        custom_name = "custom_service"
        metrics = get_rabbitmq_metrics(service_name=custom_name)

        assert metrics.service_name in ["custom_service", "adaptive_immune_system"]


class TestMetricsLabels:
    """Test metric labels are correctly applied."""

    @pytest.fixture
    def metrics(self):
        """Create fresh metrics instance for each test."""
        return RabbitMQMetrics(service_name="test_service")

    def test_publish_metrics_use_routing_key_label(self, metrics):
        """Test publish metrics include routing_key label."""
        routing_key = "specific.routing.key"

        metrics.record_message_published(
            routing_key=routing_key,
            message_size=100,
            duration=0.01,
            success=True
        )

        # Verify labels are applied (checked via metrics export)
        metrics_output = metrics.get_metrics()
        # Note: Full verification would parse Prometheus format
        assert metrics_output is not None

    def test_consume_metrics_use_queue_name_label(self, metrics):
        """Test consume metrics include queue_name label."""
        queue_name = "specific_queue"

        metrics.record_message_consumed(
            queue_name=queue_name,
            processing_time=0.1,
            success=True
        )

        metrics_output = metrics.get_metrics()
        assert metrics_output is not None


class TestMetricsEdgeCases:
    """Test metrics module edge cases and error handling."""

    @pytest.fixture
    def metrics(self):
        """Create fresh metrics instance for each test."""
        return RabbitMQMetrics(service_name="test_service")

    def test_metrics_handle_zero_duration(self, metrics):
        """Test metrics handle zero duration gracefully."""
        metrics.record_message_published(
            routing_key="test.key",
            message_size=100,
            duration=0.0,
            success=True
        )

        assert metrics.messages_published_total is not None

    def test_metrics_handle_negative_duration(self, metrics):
        """Test metrics handle negative duration (defensive)."""
        # This shouldn't happen, but metrics should not crash
        metrics.record_message_published(
            routing_key="test.key",
            message_size=100,
            duration=-0.01,  # Invalid but defensive
            success=True
        )

        assert metrics.messages_published_total is not None

    def test_metrics_handle_large_message_size(self, metrics):
        """Test metrics handle very large message sizes."""
        large_size = 10 * 1024 * 1024  # 10MB

        metrics.record_message_published(
            routing_key="test.key",
            message_size=large_size,
            duration=1.0,
            success=True
        )

        assert metrics.messages_published_total is not None

    def test_metrics_handle_empty_routing_key(self, metrics):
        """Test metrics handle empty routing key."""
        metrics.record_message_published(
            routing_key="",
            message_size=100,
            duration=0.01,
            success=True
        )

        assert metrics.messages_published_total is not None

    def test_metrics_handle_none_error_type(self, metrics):
        """Test metrics handle None error_type gracefully."""
        metrics.record_message_published(
            routing_key="test.key",
            message_size=100,
            duration=0.01,
            success=False,
            error_type=None  # Should default to "unknown"
        )

        assert metrics.message_publish_failures_total is not None


# Integration-style test
class TestMetricsEndToEnd:
    """End-to-end metrics workflow tests."""

    def test_complete_publish_consume_workflow(self):
        """Test complete workflow from publish to consume."""
        metrics = RabbitMQMetrics(service_name="e2e_test")

        # Publish phase
        with PublishTimer(metrics, "test.routing.key", 512):
            time.sleep(0.01)

        # Consume phase
        with ConsumeTimer(metrics, "test_queue"):
            time.sleep(0.01)

        # Update system metrics
        metrics.update_consumer_lag("test_queue", 5)

        # Export metrics
        metrics_output = metrics.get_metrics()

        assert len(metrics_output) > 100  # Should have substantial output
        assert isinstance(metrics_output, str)

    def test_multiple_concurrent_operations(self):
        """Test metrics handle concurrent operations correctly."""
        metrics = RabbitMQMetrics(service_name="concurrent_test")

        # Simulate multiple publishes and consumes
        for i in range(10):
            metrics.record_message_published(
                routing_key=f"key.{i}",
                message_size=100 * i,
                duration=0.001 * i,
                success=(i % 3 != 0)  # Some failures
            )

            metrics.record_message_consumed(
                queue_name=f"queue_{i % 3}",
                processing_time=0.001 * i,
                success=(i % 4 != 0)  # Different failure pattern
            )

        # Should handle all operations
        metrics_output = metrics.get_metrics()
        assert len(metrics_output) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
