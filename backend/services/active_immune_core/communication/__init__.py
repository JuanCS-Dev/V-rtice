"""Communication Module

Cytokines (Kafka) and Hormones (Redis) messaging.
Kafka Event Producers and Consumers for external integration.
"""

from .cytokines import CytokineMessage, CytokineMessenger, CytokineType
from .hormones import HormoneMessage, HormoneMessenger, HormoneType
from .kafka_events import KafkaEventProducer, EventTopic
from .kafka_consumers import KafkaEventConsumer, ExternalTopic

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
