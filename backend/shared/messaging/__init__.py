"""
Unified Messaging Layer - Vértice Ecosystem Event Bus

Integrates all event-driven communication across the MAXIMUS organism.
Provides unified event schemas, Kafka topics, and routing.

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

from .event_router import EventRouter
from .event_schemas import (
    ClonalExpansionEvent,
    EventBase,
    HomeostaticStateEvent,
    HoneypotStatusEvent,
    ImmuneResponseEvent,
    SystemHealthEvent,
    ThreatDetectionEvent,
)
from .kafka_client import UnifiedKafkaClient
from .topics import EventTopic, get_topic_config

__all__ = [
    # Schemas
    "EventBase",
    "ThreatDetectionEvent",
    "HoneypotStatusEvent",
    "ImmuneResponseEvent",
    "ClonalExpansionEvent",
    "HomeostaticStateEvent",
    "SystemHealthEvent",
    # Topics
    "EventTopic",
    "get_topic_config",
    # Routing
    "EventRouter",
    # Client
    "UnifiedKafkaClient",
]
