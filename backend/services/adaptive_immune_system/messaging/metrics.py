"""
RabbitMQ Prometheus Metrics.

Provides comprehensive metrics for RabbitMQ message publishing and consuming:
- Message throughput (publish/consume rates)
- Message latency (publish time, processing time)
- Error rates (publish failures, consumer failures)
- Queue depth
- Consumer lag
- Message priority distribution
- DLQ metrics

Integration with Prometheus for monitoring and alerting.
"""

import time
from typing import Optional

try:
    from prometheus_client import Counter, Gauge, Histogram, Summary
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False


class RabbitMQMetrics:
    """
    Prometheus metrics for RabbitMQ operations.

    Tracks all aspects of message publishing and consuming for observability.
    """

    def __init__(self, service_name: str = "adaptive_immune_system"):
        """
        Initialize RabbitMQ metrics.

        Args:
            service_name: Service name for metric labels
        """
        self.service_name = service_name
        self.enabled = PROMETHEUS_AVAILABLE

        if not self.enabled:
            return

        # --- Publishing Metrics ---

        self.messages_published_total = Counter(
            "rabbitmq_messages_published_total",
            "Total number of messages published",
            ["service", "queue", "routing_key", "priority"],
        )

        self.messages_publish_failures_total = Counter(
            "rabbitmq_messages_publish_failures_total",
            "Total number of failed message publishes",
            ["service", "queue", "error_type"],
        )

        self.message_publish_duration_seconds = Histogram(
            "rabbitmq_message_publish_duration_seconds",
            "Time spent publishing messages",
            ["service", "queue"],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
        )

        self.message_size_bytes = Histogram(
            "rabbitmq_message_size_bytes",
            "Size of published messages in bytes",
            ["service", "queue"],
            buckets=[100, 500, 1000, 5000, 10000, 50000, 100000, 500000, 1000000],
        )

        # --- Consuming Metrics ---

        self.messages_consumed_total = Counter(
            "rabbitmq_messages_consumed_total",
            "Total number of messages consumed",
            ["service", "queue", "status"],  # status: success/failure
        )

        self.message_processing_duration_seconds = Histogram(
            "rabbitmq_message_processing_duration_seconds",
            "Time spent processing consumed messages",
            ["service", "queue"],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
        )

        self.consumer_lag_messages = Gauge(
            "rabbitmq_consumer_lag_messages",
            "Number of messages waiting to be consumed (queue depth)",
            ["service", "queue"],
        )

        # --- Dead Letter Queue Metrics ---

        self.dlq_messages_total = Counter(
            "rabbitmq_dlq_messages_total",
            "Total number of messages sent to dead letter queue",
            ["service", "original_queue", "error_reason"],
        )

        # --- Connection Metrics ---

        self.connection_status = Gauge(
            "rabbitmq_connection_status",
            "RabbitMQ connection status (1=connected, 0=disconnected)",
            ["service"],
        )

        self.connection_errors_total = Counter(
            "rabbitmq_connection_errors_total",
            "Total number of connection errors",
            ["service", "error_type"],
        )

        self.connection_reconnects_total = Counter(
            "rabbitmq_connection_reconnects_total",
            "Total number of connection reconnect attempts",
            ["service", "status"],  # status: success/failure
        )

        # --- Message Priority Distribution ---

        self.message_priority_distribution = Counter(
            "rabbitmq_message_priority_total",
            "Distribution of message priorities",
            ["service", "queue", "priority_level"],  # priority_level: low/medium/high/critical
        )

        # --- End-to-End Latency ---

        self.message_e2e_latency_seconds = Summary(
            "rabbitmq_message_e2e_latency_seconds",
            "End-to-end message latency (publish to consume)",
            ["service", "queue"],
        )

    # --- Publishing Metrics Methods ---

    def record_message_published(
        self,
        queue: str,
        routing_key: str,
        priority: int,
        message_size: int,
        duration: float,
    ) -> None:
        """
        Record successful message publish.

        Args:
            queue: Queue name
            routing_key: Routing key used
            priority: Message priority (0-10)
            message_size: Message size in bytes
            duration: Publish duration in seconds
        """
        if not self.enabled:
            return

        self.messages_published_total.labels(
            service=self.service_name,
            queue=queue,
            routing_key=routing_key,
            priority=priority,
        ).inc()

        self.message_publish_duration_seconds.labels(
            service=self.service_name,
            queue=queue,
        ).observe(duration)

        self.message_size_bytes.labels(
            service=self.service_name,
            queue=queue,
        ).observe(message_size)

        # Record priority distribution
        priority_level = self._priority_to_level(priority)
        self.message_priority_distribution.labels(
            service=self.service_name,
            queue=queue,
            priority_level=priority_level,
        ).inc()

    def record_publish_failure(
        self, queue: str, error_type: str
    ) -> None:
        """
        Record failed message publish.

        Args:
            queue: Queue name
            error_type: Type of error (e.g., ConnectionError, TimeoutError)
        """
        if not self.enabled:
            return

        self.messages_publish_failures_total.labels(
            service=self.service_name,
            queue=queue,
            error_type=error_type,
        ).inc()

    # --- Consuming Metrics Methods ---

    def record_message_consumed(
        self,
        queue: str,
        success: bool,
        processing_duration: float,
        e2e_latency: Optional[float] = None,
    ) -> None:
        """
        Record message consumption.

        Args:
            queue: Queue name
            success: Whether processing succeeded
            processing_duration: Time spent processing in seconds
            e2e_latency: End-to-end latency (publish to consume) in seconds
        """
        if not self.enabled:
            return

        status = "success" if success else "failure"
        self.messages_consumed_total.labels(
            service=self.service_name,
            queue=queue,
            status=status,
        ).inc()

        self.message_processing_duration_seconds.labels(
            service=self.service_name,
            queue=queue,
        ).observe(processing_duration)

        if e2e_latency is not None:
            self.message_e2e_latency_seconds.labels(
                service=self.service_name,
                queue=queue,
            ).observe(e2e_latency)

    def update_consumer_lag(self, queue: str, lag_messages: int) -> None:
        """
        Update consumer lag metric.

        Args:
            queue: Queue name
            lag_messages: Number of messages in queue
        """
        if not self.enabled:
            return

        self.consumer_lag_messages.labels(
            service=self.service_name,
            queue=queue,
        ).set(lag_messages)

    # --- DLQ Metrics Methods ---

    def record_dlq_message(
        self, original_queue: str, error_reason: str
    ) -> None:
        """
        Record message sent to dead letter queue.

        Args:
            original_queue: Original queue name
            error_reason: Reason for DLQ (e.g., processing_failure, ttl_exceeded)
        """
        if not self.enabled:
            return

        self.dlq_messages_total.labels(
            service=self.service_name,
            original_queue=original_queue,
            error_reason=error_reason,
        ).inc()

    # --- Connection Metrics Methods ---

    def set_connection_status(self, connected: bool) -> None:
        """
        Set RabbitMQ connection status.

        Args:
            connected: True if connected, False otherwise
        """
        if not self.enabled:
            return

        self.connection_status.labels(
            service=self.service_name,
        ).set(1 if connected else 0)

    def record_connection_error(self, error_type: str) -> None:
        """
        Record connection error.

        Args:
            error_type: Type of connection error
        """
        if not self.enabled:
            return

        self.connection_errors_total.labels(
            service=self.service_name,
            error_type=error_type,
        ).inc()

    def record_reconnect_attempt(self, success: bool) -> None:
        """
        Record reconnection attempt.

        Args:
            success: Whether reconnection succeeded
        """
        if not self.enabled:
            return

        status = "success" if success else "failure"
        self.connection_reconnects_total.labels(
            service=self.service_name,
            status=status,
        ).inc()

    # --- Helper Methods ---

    @staticmethod
    def _priority_to_level(priority: int) -> str:
        """
        Convert numeric priority to level.

        Args:
            priority: Priority value (0-10)

        Returns:
            Priority level string
        """
        if priority >= 9:
            return "critical"
        elif priority >= 7:
            return "high"
        elif priority >= 4:
            return "medium"
        else:
            return "low"


# --- Context Managers for Automatic Timing ---


class PublishTimer:
    """
    Context manager for timing message publishes.

    Usage:
        with PublishTimer(metrics, queue, routing_key, priority, message_size):
            await client.publish(...)
    """

    def __init__(
        self,
        metrics: RabbitMQMetrics,
        queue: str,
        routing_key: str,
        priority: int,
        message_size: int,
    ):
        self.metrics = metrics
        self.queue = queue
        self.routing_key = routing_key
        self.priority = priority
        self.message_size = message_size
        self.start_time: Optional[float] = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time

        if exc_type is None:
            # Success
            self.metrics.record_message_published(
                self.queue,
                self.routing_key,
                self.priority,
                self.message_size,
                duration,
            )
        else:
            # Failure
            error_type = exc_type.__name__ if exc_type else "UnknownError"
            self.metrics.record_publish_failure(self.queue, error_type)

        return False  # Don't suppress exceptions


class ConsumeTimer:
    """
    Context manager for timing message consumption.

    Usage:
        with ConsumeTimer(metrics, queue):
            await process_message(msg)
    """

    def __init__(
        self,
        metrics: RabbitMQMetrics,
        queue: str,
        e2e_latency: Optional[float] = None,
    ):
        self.metrics = metrics
        self.queue = queue
        self.e2e_latency = e2e_latency
        self.start_time: Optional[float] = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        success = exc_type is None

        self.metrics.record_message_consumed(
            self.queue,
            success,
            duration,
            self.e2e_latency,
        )

        return False  # Don't suppress exceptions


# --- Global Metrics Instance ---

# Create global metrics instance
_global_metrics: Optional[RabbitMQMetrics] = None


def get_rabbitmq_metrics(service_name: str = "adaptive_immune_system") -> RabbitMQMetrics:
    """
    Get global RabbitMQ metrics instance.

    Args:
        service_name: Service name for metrics

    Returns:
        RabbitMQMetrics instance
    """
    global _global_metrics

    if _global_metrics is None:
        _global_metrics = RabbitMQMetrics(service_name)

    return _global_metrics
