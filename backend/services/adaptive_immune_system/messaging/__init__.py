"""
Messaging module for Adaptive Immune System.

Provides comprehensive RabbitMQ integration with:
- Message publishing/consuming
- Prometheus metrics
- Circuit breaker pattern
- Retry logic with exponential backoff
- Message schema versioning
- Message compression
- Cluster support (high availability)
"""

from .client import RabbitMQClient, get_rabbitmq_client
from .publisher import APVPublisher, RemedyStatusPublisher, WargameReportPublisher
from .consumer import APVConsumer, RemedyStatusConsumer, WargameReportConsumer
from .metrics import RabbitMQMetrics, get_rabbitmq_metrics, PublishTimer, ConsumeTimer
from .circuit_breaker import CircuitBreaker, CircuitState, CircuitBreakerError, get_circuit_breaker
from .retry import (
    RetryConfig,
    retry_with_backoff,
    RetryDecorator,
    MessageRetryHeaders,
    RetryExhaustedError,
)
from .versioning import Version, VersionedMessage, MessageVersionRegistry, get_message_registry
from .compression import (
    CompressionAlgorithm,
    CompressionConfig,
    MessageCompressor,
    get_message_compressor,
)
from .cluster import RabbitMQCluster, ClusterConfig, BrokerNode, get_rabbitmq_cluster

__all__ = [
    # Core
    "RabbitMQClient",
    "get_rabbitmq_client",
    # Publishers
    "APVPublisher",
    "RemedyStatusPublisher",
    "WargameReportPublisher",
    # Consumers
    "APVConsumer",
    "RemedyStatusConsumer",
    "WargameReportConsumer",
    # Metrics
    "RabbitMQMetrics",
    "get_rabbitmq_metrics",
    "PublishTimer",
    "ConsumeTimer",
    # Circuit Breaker
    "CircuitBreaker",
    "CircuitState",
    "CircuitBreakerError",
    "get_circuit_breaker",
    # Retry
    "RetryConfig",
    "retry_with_backoff",
    "RetryDecorator",
    "MessageRetryHeaders",
    "RetryExhaustedError",
    # Versioning
    "Version",
    "VersionedMessage",
    "MessageVersionRegistry",
    "get_message_registry",
    # Compression
    "CompressionAlgorithm",
    "CompressionConfig",
    "MessageCompressor",
    "get_message_compressor",
    # Cluster
    "RabbitMQCluster",
    "ClusterConfig",
    "BrokerNode",
    "get_rabbitmq_cluster",
]
