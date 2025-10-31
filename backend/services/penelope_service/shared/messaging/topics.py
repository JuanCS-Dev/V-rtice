"""
Unified Kafka Topics Configuration

Central registry of all Kafka topics in the Vértice ecosystem.
Provides topic names, configurations, and routing rules.

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

from enum import Enum

from pydantic import BaseModel


class EventTopic(str, Enum):
    """
    Unified Kafka topics for Vértice MAXIMUS ecosystem.

    Naming convention: maximus.<domain>.<entity>.<action>
    """

    # Threat detection pipeline
    THREATS_DETECTED = "maximus.threats.detected"
    THREATS_ENRICHED = "maximus.threats.enriched"
    THREATS_ANALYZED = "maximus.threats.analyzed"

    # Immune system responses
    IMMUNE_RESPONSES = "maximus.immune.responses"
    IMMUNE_CLONING = "maximus.immune.cloning"
    IMMUNE_HOMEOSTASIS = "maximus.immune.homeostasis"
    IMMUNE_ALERTS = "maximus.immune.alerts"

    # Honeypot management
    HONEYPOTS_STATUS = "maximus.honeypots.status"
    HONEYPOTS_COMMANDS = "maximus.honeypots.commands"

    # System health
    SYSTEM_HEALTH = "maximus.system.health"
    SYSTEM_METRICS = "maximus.system.metrics"

    # Integration
    INTEGRATION_EVENTS = "maximus.integration.events"

    # Audit and compliance
    AUDIT_LOGS = "maximus.audit.logs"


class TopicConfig(BaseModel):
    """Kafka topic configuration"""

    name: str
    partitions: int = 3
    replication_factor: int = 3
    retention_ms: int = 604800000  # 7 days
    compression_type: str = "gzip"
    cleanup_policy: str = "delete"
    description: str = ""

    # Routing
    producers: list[str] = []  # Services that produce to this topic
    consumers: list[str] = []  # Services that consume from this topic


# Topic configurations registry
TOPIC_CONFIGS: dict[EventTopic, TopicConfig] = {
    EventTopic.THREATS_DETECTED: TopicConfig(
        name=EventTopic.THREATS_DETECTED.value,
        partitions=6,
        retention_ms=2592000000,  # 30 days
        description="Raw threat detections from honeypots",
        producers=["reactive_fabric_core"],
        consumers=["active_immune_core", "siem", "analytics"],
    ),
    EventTopic.THREATS_ENRICHED: TopicConfig(
        name=EventTopic.THREATS_ENRICHED.value,
        partitions=6,
        retention_ms=2592000000,  # 30 days
        description="Enriched threat intelligence",
        producers=["threat_intel_service"],
        consumers=["active_immune_core", "analytics"],
    ),
    EventTopic.IMMUNE_RESPONSES: TopicConfig(
        name=EventTopic.IMMUNE_RESPONSES.value,
        partitions=6,
        retention_ms=1209600000,  # 14 days
        description="Immune system responses to threats",
        producers=["active_immune_core"],
        consumers=["reactive_fabric_core", "monitoring", "analytics"],
    ),
    EventTopic.IMMUNE_CLONING: TopicConfig(
        name=EventTopic.IMMUNE_CLONING.value,
        partitions=3,
        retention_ms=604800000,  # 7 days
        description="Clonal expansion events",
        producers=["active_immune_core"],
        consumers=["monitoring", "homeostatic_controller"],
    ),
    EventTopic.IMMUNE_HOMEOSTASIS: TopicConfig(
        name=EventTopic.IMMUNE_HOMEOSTASIS.value,
        partitions=3,
        retention_ms=604800000,  # 7 days
        description="Homeostatic state changes",
        producers=["active_immune_core"],
        consumers=["all_immune_components", "monitoring"],
    ),
    EventTopic.HONEYPOTS_STATUS: TopicConfig(
        name=EventTopic.HONEYPOTS_STATUS.value,
        partitions=3,
        retention_ms=86400000,  # 1 day
        description="Honeypot status updates",
        producers=["reactive_fabric_core"],
        consumers=["monitoring", "orchestrator"],
    ),
    EventTopic.SYSTEM_HEALTH: TopicConfig(
        name=EventTopic.SYSTEM_HEALTH.value,
        partitions=1,
        retention_ms=86400000,  # 1 day
        description="System-wide health metrics",
        producers=["all_services"],
        consumers=["monitoring", "alerting"],
    ),
}


def get_topic_config(topic: EventTopic) -> TopicConfig:
    """
    Get topic configuration.

    Args:
        topic: Event topic

    Returns:
        Topic configuration

    Raises:
        ValueError: If topic not configured
    """
    if topic not in TOPIC_CONFIGS:
        raise ValueError(f"Topic {topic} not configured")
    return TOPIC_CONFIGS[topic]


def get_producer_topics(service_name: str) -> list[EventTopic]:
    """
    Get topics that a service produces to.

    Args:
        service_name: Service name

    Returns:
        List of topics
    """
    topics = []
    for topic, config in TOPIC_CONFIGS.items():
        if service_name in config.producers:
            topics.append(topic)
    return topics


def get_consumer_topics(service_name: str) -> list[EventTopic]:
    """
    Get topics that a service consumes from.

    Args:
        service_name: Service name

    Returns:
        List of topics
    """
    topics = []
    for topic, config in TOPIC_CONFIGS.items():
        if service_name in config.consumers:
            topics.append(topic)
    return topics
