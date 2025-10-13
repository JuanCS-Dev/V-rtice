"""
Messaging module for Adaptive Immune System.

Provides RabbitMQ integration for Oráculo ↔ Eureka communication.
"""

from .client import RabbitMQClient, get_rabbitmq_client
from .publisher import APVPublisher, RemedyStatusPublisher, WargameReportPublisher
from .consumer import APVConsumer, RemedyStatusConsumer, WargameReportConsumer

__all__ = [
    "RabbitMQClient",
    "get_rabbitmq_client",
    "APVPublisher",
    "RemedyStatusPublisher",
    "WargameReportPublisher",
    "APVConsumer",
    "RemedyStatusConsumer",
    "WargameReportConsumer",
]
