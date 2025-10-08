"""Communication Module

Cytokines (Kafka) and Hormones (Redis) messaging.
Kafka Event Producers and Consumers for external integration.
"""

from .cytokines import CytokineMessage, CytokineMessenger, CytokineType
from .hormones import HormoneMessage, HormoneMessenger, HormoneType
from .kafka_consumers import ExternalTopic, KafkaEventConsumer
from .kafka_events import EventTopic, KafkaEventProducer

__all__ = [
    "CytokineMessage",
    "CytokineMessenger",
    "CytokineType",
    "HormoneMessage",
    "HormoneMessenger",
    "HormoneType",
    "KafkaEventProducer",
    "EventTopic",
    "KafkaEventConsumer",
    "ExternalTopic",
]
