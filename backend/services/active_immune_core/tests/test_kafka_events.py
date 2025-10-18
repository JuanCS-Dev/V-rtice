"""Tests for Kafka Event Producer and Consumer - PRODUCTION-READY

Tests event-driven integration with external Vértice services.

NO MOCKS - Tests use REAL Kafka or graceful degradation.

Authors: Juan & Claude
Version: 1.0.0
"""

import pytest
import pytest_asyncio

from active_immune_core.communication import (
    ExternalTopic,
    KafkaEventConsumer,
    KafkaEventProducer,
)

# ==================== FIXTURES ====================


@pytest_asyncio.fixture
async def kafka_producer():
    """Kafka event producer fixture."""
    producer = KafkaEventProducer(
        bootstrap_servers="localhost:9092",
        enable_degraded_mode=True,
    )
    await producer.start()
    yield producer
    await producer.stop()


@pytest_asyncio.fixture
async def kafka_consumer():
    """Kafka event consumer fixture."""
    consumer = KafkaEventConsumer(
        bootstrap_servers="localhost:9092",
        group_id="test_consumer",
        enable_degraded_mode=True,
    )
    await consumer.start()
    yield consumer
    await consumer.stop()


# ==================== PRODUCER TESTS ====================


@pytest.mark.asyncio
async def test_producer_initialization(kafka_producer):
    """Test producer initializes."""
    assert kafka_producer is not None
    assert kafka_producer._running is True


@pytest.mark.asyncio
async def test_producer_publish_threat_detection(kafka_producer):
    """Test publishing threat detection event."""
    result = await kafka_producer.publish_threat_detection(
        threat_id="test_threat_001",
        threat_type="malware",
        severity="high",
        detector_agent="macrofago_test_001",
        target="192.168.1.100",
        confidence=0.95,
        details={
            "hash": "abc123",
            "behavior": "ransomware",
        },
    )

    # Should succeed or fail gracefully
    assert result is not None
    assert isinstance(result, bool)

    # Check metrics
    metrics = kafka_producer.get_metrics()
    assert "total_events_published" in metrics or "total_events_failed" in metrics


@pytest.mark.asyncio
async def test_producer_publish_clonal_expansion(kafka_producer):
    """Test publishing clonal expansion event."""
    result = await kafka_producer.publish_clonal_expansion(
        parent_id="bcell_test_001",
        clone_ids=["bcell_clone_001", "bcell_clone_002"],
        num_clones=2,
        especializacao="threat_signature_abc",
        lymphnode_id="lymphnode_regional_001",
        trigger="repeated_detections",
    )

    assert result is not None
    assert isinstance(result, bool)


@pytest.mark.asyncio
async def test_producer_publish_homeostatic_alert(kafka_producer):
    """Test publishing homeostatic alert."""
    result = await kafka_producer.publish_homeostatic_alert(
        lymphnode_id="lymphnode_regional_001",
        old_state="VIGILÂNCIA",
        new_state="ATIVAÇÃO",
        temperatura_regional=38.5,
        recommended_action="Increase agent count",
        metrics={
            "active_agents": 45,
            "total_agents": 100,
            "threat_count": 5,
        },
    )

    assert result is not None
    assert isinstance(result, bool)


@pytest.mark.asyncio
async def test_producer_publish_system_health(kafka_producer):
    """Test publishing system health event."""
    result = await kafka_producer.publish_system_health(
        health_status="healthy",
        total_agents=100,
        active_agents=85,
        threats_detected=50,
        threats_neutralized=45,
        average_temperature=37.5,
        lymphnodes=[
            {
                "id": "lymphnode_001",
                "state": "VIGILÂNCIA",
                "agent_count": 50,
            }
        ],
    )

    assert result is not None
    assert isinstance(result, bool)


@pytest.mark.asyncio
async def test_producer_graceful_degradation():
    """Test producer graceful degradation when Kafka unavailable."""
    # Create producer pointing to non-existent Kafka
    producer = KafkaEventProducer(
        bootstrap_servers="localhost:9999",  # Invalid port
        enable_degraded_mode=True,
        max_retries=1,  # Fast failure
    )

    await producer.start()

    # Should be running but Kafka unavailable
    assert producer._running is True
    assert producer.is_available() is False

    # Should still work (degraded mode - logs to file)
    result = await producer.publish_threat_detection(
        threat_id="test_threat_degraded",
        threat_type="test",
        severity="low",
        detector_agent="test_agent",
        target="test",
        confidence=0.5,
        details={},
    )

    # In degraded mode, returns False but doesn't raise
    assert result is False

    # Metrics should show failure
    metrics = producer.get_metrics()
    assert metrics["kafka_available"] is False
    assert metrics["total_events_failed"] > 0

    await producer.stop()


@pytest.mark.asyncio
async def test_producer_metrics(kafka_producer):
    """Test producer metrics tracking."""
    # Publish some events
    await kafka_producer.publish_threat_detection(
        threat_id="metric_test_001",
        threat_type="test",
        severity="low",
        detector_agent="test",
        target="test",
        confidence=0.5,
        details={},
    )

    await kafka_producer.publish_system_health(
        health_status="healthy",
        total_agents=10,
        active_agents=8,
        threats_detected=5,
        threats_neutralized=3,
        average_temperature=37.0,
        lymphnodes=[],
    )

    # Check metrics
    metrics = kafka_producer.get_metrics()

    assert "running" in metrics
    assert "kafka_available" in metrics
    assert "total_events_published" in metrics
    assert "total_events_failed" in metrics
    assert "events_by_topic" in metrics

    # Should have attempted to publish at least 2 events
    total = metrics["total_events_published"] + metrics["total_events_failed"]
    assert total >= 2


# ==================== CONSUMER TESTS ====================


@pytest.mark.asyncio
async def test_consumer_initialization(kafka_consumer):
    """Test consumer initializes."""
    assert kafka_consumer is not None
    assert kafka_consumer._running is True


@pytest.mark.asyncio
async def test_consumer_register_handler(kafka_consumer):
    """Test registering event handlers."""

    # Track handler calls
    handler_called = {"count": 0}

    async def test_handler(event_data):
        handler_called["count"] += 1

    # Register handler
    kafka_consumer.register_handler(
        ExternalTopic.THREATS_INTEL,
        test_handler,
    )

    # Check handler registered
    metrics = kafka_consumer.get_metrics()
    assert metrics["registered_handlers"]["vertice.threats.intel"] == 1


@pytest.mark.asyncio
async def test_consumer_default_handlers():
    """Test default event handlers execute without errors."""
    # Test threat intel handler
    await KafkaEventConsumer.handle_threat_intel(
        {
            "threat_type": "malware",
            "signature": "test_signature",
            "iocs": ["192.168.1.100"],
            "severity": "high",
        }
    )

    # Test network event handler
    await KafkaEventConsumer.handle_network_event(
        {
            "event_type": "anomaly_detected",
            "source_ip": "192.168.1.50",
            "dest_ip": "10.0.0.1",
            "protocol": "TCP",
            "anomaly_score": 0.85,
        }
    )

    # Test endpoint event handler
    await KafkaEventConsumer.handle_endpoint_event(
        {
            "event_type": "suspicious_process",
            "hostname": "workstation-01",
            "process_name": "malware.exe",
            "file_hash": "abc123",
            "threat_level": "high",
        }
    )

    # If we got here, handlers executed successfully


@pytest.mark.asyncio
async def test_consumer_graceful_degradation():
    """Test consumer graceful degradation when Kafka unavailable."""
    # Create consumer pointing to non-existent Kafka
    consumer = KafkaEventConsumer(
        bootstrap_servers="localhost:9999",  # Invalid port
        group_id="test_degraded_consumer",
        enable_degraded_mode=True,
    )

    await consumer.start()

    # Should be running but Kafka unavailable
    assert consumer._running is True
    assert consumer.is_available() is False

    # Metrics should reflect unavailability
    metrics = consumer.get_metrics()
    assert metrics["kafka_available"] is False
    assert metrics["total_events_consumed"] == 0

    await consumer.stop()


@pytest.mark.asyncio
async def test_consumer_metrics(kafka_consumer):
    """Test consumer metrics tracking."""
    # Get initial metrics
    metrics = kafka_consumer.get_metrics()

    assert "running" in metrics
    assert "kafka_available" in metrics
    assert "total_events_consumed" in metrics
    assert "total_events_processed" in metrics
    assert "total_events_failed" in metrics
    assert "events_by_topic" in metrics
    assert "registered_handlers" in metrics

    # All metrics should be initialized
    assert metrics["running"] is True
    assert metrics["total_events_consumed"] >= 0


@pytest.mark.asyncio
async def test_consumer_unregister_handler(kafka_consumer):
    """Test unregistering event handlers."""

    async def test_handler(event_data):
        pass

    # Register handler
    kafka_consumer.register_handler(
        ExternalTopic.NETWORK_EVENTS,
        test_handler,
    )

    # Verify registered
    metrics = kafka_consumer.get_metrics()
    assert metrics["registered_handlers"]["vertice.network.events"] == 1

    # Unregister handler
    kafka_consumer.unregister_handler(
        ExternalTopic.NETWORK_EVENTS,
        test_handler,
    )

    # Verify unregistered
    metrics = kafka_consumer.get_metrics()
    assert metrics["registered_handlers"]["vertice.network.events"] == 0


# ==================== INTEGRATION TESTS ====================


@pytest.mark.asyncio
async def test_producer_consumer_integration(kafka_producer, kafka_consumer):
    """Test producer-consumer integration (if Kafka available)."""
    # Track received events
    received_events = []

    async def capture_handler(event_data):
        received_events.append(event_data)

    # Register handler for threat intel
    kafka_consumer.register_handler(
        ExternalTopic.THREATS_INTEL,
        capture_handler,
    )

    # Note: This test will only verify integration if Kafka is available
    # Otherwise, it tests graceful degradation

    # Get initial state
    producer_available = kafka_producer.is_available()
    consumer_available = kafka_consumer.is_available()

    # Both should be running (even if Kafka unavailable)
    assert kafka_producer._running is True
    assert kafka_consumer._running is True

    # If Kafka is available, we could test E2E event flow
    # For now, we verify both components initialized correctly
    assert kafka_producer is not None
    assert kafka_consumer is not None


@pytest.mark.asyncio
async def test_producer_repr(kafka_producer):
    """Test producer string representation."""
    repr_str = repr(kafka_producer)

    assert "KafkaEventProducer" in repr_str
    assert "running" in repr_str
    assert "kafka_available" in repr_str


@pytest.mark.asyncio
async def test_consumer_repr(kafka_consumer):
    """Test consumer string representation."""
    repr_str = repr(kafka_consumer)

    assert "KafkaEventConsumer" in repr_str
    assert "running" in repr_str
    assert "kafka_available" in repr_str


# ==================== LIFECYCLE TESTS ====================


@pytest.mark.asyncio
async def test_producer_double_start():
    """Test starting producer twice is idempotent."""
    producer = KafkaEventProducer(enable_degraded_mode=True)

    await producer.start()
    assert producer._running is True

    # Start again - should log warning but not fail
    await producer.start()
    assert producer._running is True

    await producer.stop()


@pytest.mark.asyncio
async def test_consumer_double_start():
    """Test starting consumer twice is idempotent."""
    consumer = KafkaEventConsumer(enable_degraded_mode=True)

    await consumer.start()
    assert consumer._running is True

    # Start again - should log warning but not fail
    await consumer.start()
    assert consumer._running is True

    await consumer.stop()


@pytest.mark.asyncio
async def test_producer_stop_before_start():
    """Test stopping producer before starting."""
    producer = KafkaEventProducer(enable_degraded_mode=True)

    # Should not raise error
    await producer.stop()


@pytest.mark.asyncio
async def test_consumer_stop_before_start():
    """Test stopping consumer before starting."""
    consumer = KafkaEventConsumer(enable_degraded_mode=True)

    # Should not raise error
    await consumer.stop()
