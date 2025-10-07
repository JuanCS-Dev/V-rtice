"""
Unit tests for KafkaEventConsumer - External Event Integration

Tests cover production implementation:
- Initialization and lifecycle
- Event handler registration/unregistration
- Event consumption and routing
- Default event handlers (threat intel, network, endpoint)
- Degraded mode (Kafka unavailable)
- Metrics tracking
- Error handling
"""

import asyncio
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from active_immune_core.communication.kafka_consumers import (
    KafkaEventConsumer,
    ExternalTopic,
)


# ==================== FIXTURES ====================


@pytest_asyncio.fixture
async def consumer() -> KafkaEventConsumer:
    """Create KafkaEventConsumer instance for testing."""
    consumer = KafkaEventConsumer(
        bootstrap_servers="localhost:9092",
        group_id="test_consumer_group",
        enable_degraded_mode=True,
    )
    yield consumer
    if consumer._running:
        await consumer.stop()


# ==================== INITIALIZATION TESTS ====================


@pytest.mark.asyncio
async def test_consumer_initialization():
    """Test KafkaEventConsumer initialization."""
    consumer = KafkaEventConsumer(
        bootstrap_servers="kafka:9092",
        group_id="test_group",
        enable_degraded_mode=False,
    )

    assert consumer.bootstrap_servers == "kafka:9092"
    assert consumer.group_id == "test_group"
    assert consumer.enable_degraded_mode is False
    assert consumer._running is False
    assert consumer._kafka_available is False
    assert consumer.total_events_consumed == 0
    assert consumer.total_events_processed == 0
    assert consumer.total_events_failed == 0


@pytest.mark.asyncio
async def test_consumer_initialization_default_values():
    """Test consumer uses default values."""
    consumer = KafkaEventConsumer()

    assert consumer.bootstrap_servers == "localhost:9092"
    assert consumer.group_id == "active_immune_core_consumer"
    assert consumer.enable_degraded_mode is True


@pytest.mark.asyncio
async def test_external_topic_enum():
    """Test ExternalTopic enum values."""
    assert ExternalTopic.THREATS_INTEL == "vertice.threats.intel"
    assert ExternalTopic.NETWORK_EVENTS == "vertice.network.events"
    assert ExternalTopic.ENDPOINT_EVENTS == "vertice.endpoint.events"


@pytest.mark.asyncio
async def test_consumer_initializes_handlers_for_all_topics(consumer: KafkaEventConsumer):
    """Test consumer initializes handler lists for all topics."""
    for topic in ExternalTopic:
        assert topic in consumer._handlers
        assert isinstance(consumer._handlers[topic], list)
        assert len(consumer._handlers[topic]) == 0


# ==================== LIFECYCLE TESTS ====================


@pytest.mark.asyncio
async def test_start_consumer_success():
    """Test starting consumer with mocked Kafka."""
    consumer = KafkaEventConsumer()

    # Mock AIOKafkaConsumer
    mock_kafka_consumer = AsyncMock()
    mock_kafka_consumer.start = AsyncMock()

    with patch("active_immune_core.communication.kafka_consumers.AIOKafkaConsumer", return_value=mock_kafka_consumer):
        await consumer.start()

        assert consumer._running is True
        assert consumer._kafka_available is True
        mock_kafka_consumer.start.assert_called_once()

        await consumer.stop()


@pytest.mark.asyncio
async def test_start_consumer_already_running():
    """Test starting already running consumer is idempotent."""
    consumer = KafkaEventConsumer()

    mock_kafka_consumer = AsyncMock()
    mock_kafka_consumer.start = AsyncMock()

    with patch("active_immune_core.communication.kafka_consumers.AIOKafkaConsumer", return_value=mock_kafka_consumer):
        await consumer.start()
        first_start_count = mock_kafka_consumer.start.call_count

        # Start again
        await consumer.start()

        # Should not start twice
        assert mock_kafka_consumer.start.call_count == first_start_count

        await consumer.stop()


@pytest.mark.asyncio
async def test_start_consumer_kafka_unavailable_degraded_mode():
    """Test starting consumer with Kafka unavailable (degraded mode)."""
    from aiokafka.errors import KafkaConnectionError

    consumer = KafkaEventConsumer(enable_degraded_mode=True)

    async def raise_kafka_error(*args, **kwargs):
        raise KafkaConnectionError("Kafka unavailable")

    mock_kafka_consumer = AsyncMock()
    mock_kafka_consumer.start = raise_kafka_error

    with patch("active_immune_core.communication.kafka_consumers.AIOKafkaConsumer", return_value=mock_kafka_consumer):
        # Should not raise exception
        await consumer.start()

        assert consumer._running is True
        assert consumer._kafka_available is False  # Degraded mode

        await consumer.stop()


@pytest.mark.asyncio
async def test_start_consumer_kafka_unavailable_no_degraded_mode():
    """Test starting consumer with Kafka unavailable (no degraded mode)."""
    from aiokafka.errors import KafkaConnectionError

    consumer = KafkaEventConsumer(enable_degraded_mode=False)

    async def raise_kafka_error(*args, **kwargs):
        raise KafkaConnectionError("Kafka unavailable")

    mock_kafka_consumer = AsyncMock()
    mock_kafka_consumer.start = raise_kafka_error

    with patch("active_immune_core.communication.kafka_consumers.AIOKafkaConsumer", return_value=mock_kafka_consumer):
        # Should raise exception
        with pytest.raises(KafkaConnectionError):
            await consumer.start()


@pytest.mark.asyncio
async def test_stop_consumer():
    """Test stopping consumer cleans up resources."""
    consumer = KafkaEventConsumer()

    mock_kafka_consumer = AsyncMock()
    mock_kafka_consumer.start = AsyncMock()
    mock_kafka_consumer.stop = AsyncMock()

    with patch("active_immune_core.communication.kafka_consumers.AIOKafkaConsumer", return_value=mock_kafka_consumer):
        await consumer.start()
        await consumer.stop()

        assert consumer._running is False
        assert consumer._kafka_available is False
        mock_kafka_consumer.stop.assert_called_once()


@pytest.mark.asyncio
async def test_stop_consumer_not_running(consumer: KafkaEventConsumer):
    """Test stopping consumer that was never started."""
    # Should not raise exception
    await consumer.stop()
    assert consumer._running is False


@pytest.mark.asyncio
async def test_is_available_running_and_kafka_ok():
    """Test is_available returns True when running and Kafka OK."""
    consumer = KafkaEventConsumer()

    mock_kafka_consumer = AsyncMock()
    mock_kafka_consumer.start = AsyncMock()

    with patch("active_immune_core.communication.kafka_consumers.AIOKafkaConsumer", return_value=mock_kafka_consumer):
        await consumer.start()

        assert consumer.is_available() is True

        await consumer.stop()


@pytest.mark.asyncio
async def test_is_available_degraded_mode(consumer: KafkaEventConsumer):
    """Test is_available returns False in degraded mode."""
    from aiokafka.errors import KafkaConnectionError

    async def raise_kafka_error(*args, **kwargs):
        raise KafkaConnectionError("Kafka unavailable")

    mock_kafka_consumer = AsyncMock()
    mock_kafka_consumer.start = raise_kafka_error

    with patch("active_immune_core.communication.kafka_consumers.AIOKafkaConsumer", return_value=mock_kafka_consumer):
        await consumer.start()

        # Running but Kafka not available
        assert consumer.is_available() is False

        await consumer.stop()


# ==================== HANDLER REGISTRATION TESTS ====================


@pytest.mark.asyncio
async def test_register_handler(consumer: KafkaEventConsumer):
    """Test registering event handler."""
    async def test_handler(event_data: Dict[str, Any]) -> None:
        pass

    consumer.register_handler(ExternalTopic.THREATS_INTEL, test_handler)

    assert len(consumer._handlers[ExternalTopic.THREATS_INTEL]) == 1
    assert test_handler in consumer._handlers[ExternalTopic.THREATS_INTEL]


@pytest.mark.asyncio
async def test_register_multiple_handlers(consumer: KafkaEventConsumer):
    """Test registering multiple handlers for same topic."""
    async def handler1(event_data: Dict[str, Any]) -> None:
        pass

    async def handler2(event_data: Dict[str, Any]) -> None:
        pass

    consumer.register_handler(ExternalTopic.NETWORK_EVENTS, handler1)
    consumer.register_handler(ExternalTopic.NETWORK_EVENTS, handler2)

    assert len(consumer._handlers[ExternalTopic.NETWORK_EVENTS]) == 2


@pytest.mark.asyncio
async def test_unregister_handler(consumer: KafkaEventConsumer):
    """Test unregistering event handler."""
    async def test_handler(event_data: Dict[str, Any]) -> None:
        pass

    consumer.register_handler(ExternalTopic.ENDPOINT_EVENTS, test_handler)
    assert len(consumer._handlers[ExternalTopic.ENDPOINT_EVENTS]) == 1

    consumer.unregister_handler(ExternalTopic.ENDPOINT_EVENTS, test_handler)
    assert len(consumer._handlers[ExternalTopic.ENDPOINT_EVENTS]) == 0


@pytest.mark.asyncio
async def test_unregister_handler_not_registered(consumer: KafkaEventConsumer):
    """Test unregistering handler that was not registered."""
    async def test_handler(event_data: Dict[str, Any]) -> None:
        pass

    # Should not raise exception
    consumer.unregister_handler(ExternalTopic.THREATS_INTEL, test_handler)


# ==================== EVENT ROUTING TESTS ====================


@pytest.mark.asyncio
async def test_route_event_with_async_handler(consumer: KafkaEventConsumer):
    """Test routing event to async handler."""
    handler_called = False
    received_data = {}

    async def test_handler(event_data: Dict[str, Any]) -> None:
        nonlocal handler_called, received_data
        handler_called = True
        received_data = event_data

    consumer.register_handler(ExternalTopic.THREATS_INTEL, test_handler)

    event_data = {"threat_type": "malware", "severity": "high"}
    await consumer._route_event(ExternalTopic.THREATS_INTEL, event_data)

    assert handler_called is True
    assert received_data == event_data
    assert consumer.total_events_processed == 1


@pytest.mark.asyncio
async def test_route_event_with_sync_handler(consumer: KafkaEventConsumer):
    """Test routing event to sync handler."""
    handler_called = False

    def test_handler(event_data: Dict[str, Any]) -> None:
        nonlocal handler_called
        handler_called = True

    consumer.register_handler(ExternalTopic.NETWORK_EVENTS, test_handler)

    event_data = {"event_type": "anomaly"}
    await consumer._route_event(ExternalTopic.NETWORK_EVENTS, event_data)

    assert handler_called is True
    assert consumer.total_events_processed == 1


@pytest.mark.asyncio
async def test_route_event_no_handlers(consumer: KafkaEventConsumer):
    """Test routing event with no registered handlers."""
    event_data = {"test": "data"}

    # Should not raise exception
    await consumer._route_event(ExternalTopic.ENDPOINT_EVENTS, event_data)

    # No handlers, so no events processed
    assert consumer.total_events_processed == 0


@pytest.mark.asyncio
async def test_route_event_handler_error(consumer: KafkaEventConsumer):
    """Test routing event when handler raises exception."""
    async def failing_handler(event_data: Dict[str, Any]) -> None:
        raise ValueError("Handler error")

    consumer.register_handler(ExternalTopic.THREATS_INTEL, failing_handler)

    event_data = {"test": "data"}
    await consumer._route_event(ExternalTopic.THREATS_INTEL, event_data)

    # Should handle error gracefully
    assert consumer.total_events_failed == 1


@pytest.mark.asyncio
async def test_route_event_multiple_handlers(consumer: KafkaEventConsumer):
    """Test routing event to multiple handlers."""
    handler1_called = False
    handler2_called = False

    async def handler1(event_data: Dict[str, Any]) -> None:
        nonlocal handler1_called
        handler1_called = True

    async def handler2(event_data: Dict[str, Any]) -> None:
        nonlocal handler2_called
        handler2_called = True

    consumer.register_handler(ExternalTopic.NETWORK_EVENTS, handler1)
    consumer.register_handler(ExternalTopic.NETWORK_EVENTS, handler2)

    event_data = {"test": "data"}
    await consumer._route_event(ExternalTopic.NETWORK_EVENTS, event_data)

    assert handler1_called is True
    assert handler2_called is True
    assert consumer.total_events_processed == 2


# ==================== DEFAULT HANDLER TESTS ====================


@pytest.mark.asyncio
async def test_handle_threat_intel():
    """Test default threat intel handler."""
    event_data = {
        "threat_type": "ransomware",
        "signature": "abc123",
        "iocs": ["1.2.3.4", "malware.exe"],
        "severity": "high",
    }

    # Should not raise exception
    await KafkaEventConsumer.handle_threat_intel(event_data)


@pytest.mark.asyncio
async def test_handle_network_event():
    """Test default network event handler."""
    event_data = {
        "event_type": "anomaly",
        "source_ip": "192.168.1.100",
        "dest_ip": "10.0.0.50",
        "protocol": "TCP",
        "anomaly_score": 8.5,
    }

    # Should not raise exception
    await KafkaEventConsumer.handle_network_event(event_data)


@pytest.mark.asyncio
async def test_handle_endpoint_event():
    """Test default endpoint event handler."""
    event_data = {
        "event_type": "process_start",
        "hostname": "workstation-01",
        "process_name": "suspicious.exe",
        "file_hash": "abc123def456",
        "threat_level": "high",
    }

    # Should not raise exception
    await KafkaEventConsumer.handle_endpoint_event(event_data)


@pytest.mark.asyncio
async def test_handle_threat_intel_missing_fields():
    """Test threat intel handler with missing fields."""
    event_data = {}

    # Should handle gracefully
    await KafkaEventConsumer.handle_threat_intel(event_data)


@pytest.mark.asyncio
async def test_handle_network_event_missing_fields():
    """Test network event handler with missing fields."""
    event_data = {}

    # Should handle gracefully
    await KafkaEventConsumer.handle_network_event(event_data)


@pytest.mark.asyncio
async def test_handle_endpoint_event_missing_fields():
    """Test endpoint event handler with missing fields."""
    event_data = {}

    # Should handle gracefully
    await KafkaEventConsumer.handle_endpoint_event(event_data)


# ==================== METRICS TESTS ====================


@pytest.mark.asyncio
async def test_get_metrics_initial_state(consumer: KafkaEventConsumer):
    """Test get_metrics returns initial state."""
    metrics = consumer.get_metrics()

    assert metrics["running"] is False
    assert metrics["kafka_available"] is False
    assert metrics["total_events_consumed"] == 0
    assert metrics["total_events_processed"] == 0
    assert metrics["total_events_failed"] == 0
    assert "events_by_topic" in metrics
    assert "registered_handlers" in metrics


@pytest.mark.asyncio
async def test_get_metrics_after_event_processing(consumer: KafkaEventConsumer):
    """Test get_metrics tracks event processing."""
    async def test_handler(event_data: Dict[str, Any]) -> None:
        pass

    consumer.register_handler(ExternalTopic.THREATS_INTEL, test_handler)

    event_data = {"test": "data"}
    await consumer._route_event(ExternalTopic.THREATS_INTEL, event_data)

    metrics = consumer.get_metrics()

    assert metrics["total_events_processed"] == 1
    assert metrics["registered_handlers"][ExternalTopic.THREATS_INTEL.value] == 1


@pytest.mark.asyncio
async def test_get_metrics_tracks_failures(consumer: KafkaEventConsumer):
    """Test get_metrics tracks handler failures."""
    async def failing_handler(event_data: Dict[str, Any]) -> None:
        raise Exception("Handler error")

    consumer.register_handler(ExternalTopic.NETWORK_EVENTS, failing_handler)

    event_data = {"test": "data"}
    await consumer._route_event(ExternalTopic.NETWORK_EVENTS, event_data)

    metrics = consumer.get_metrics()

    assert metrics["total_events_failed"] == 1


# ==================== REPR TEST ====================


@pytest.mark.asyncio
async def test_repr(consumer: KafkaEventConsumer):
    """Test string representation."""
    repr_str = repr(consumer)

    assert "KafkaEventConsumer" in repr_str
    assert "running=False" in repr_str
    assert "kafka_available=False" in repr_str
    assert "consumed=0" in repr_str


@pytest.mark.asyncio
async def test_repr_after_start():
    """Test string representation after starting."""
    consumer = KafkaEventConsumer()

    mock_kafka_consumer = AsyncMock()
    mock_kafka_consumer.start = AsyncMock()

    with patch("active_immune_core.communication.kafka_consumers.AIOKafkaConsumer", return_value=mock_kafka_consumer):
        await consumer.start()

        repr_str = repr(consumer)

        assert "running=True" in repr_str
        assert "kafka_available=True" in repr_str

        await consumer.stop()


# ==================== PHASE 2: EVENT CONSUMPTION COVERAGE (81%→85%+) ====================


@pytest.mark.asyncio
async def test_consume_events_with_messages():
    """Test _consume_events processes messages from Kafka."""
    consumer = KafkaEventConsumer()

    # Track handler calls
    handler_called = False
    received_data = {}

    async def test_handler(event_data: Dict[str, Any]) -> None:
        nonlocal handler_called, received_data
        handler_called = True
        received_data = event_data

    consumer.register_handler(ExternalTopic.THREATS_INTEL, test_handler)

    # Mock Kafka message
    mock_msg = MagicMock()
    mock_msg.topic = "vertice.threats.intel"
    mock_msg.value = {"threat_type": "malware", "severity": "high"}

    # Mock async iterator that yields one message then stops
    async def mock_aiter(self):
        yield mock_msg
        # After yielding, consumer will be stopped
        consumer._running = False

    mock_kafka_consumer = AsyncMock()
    mock_kafka_consumer.start = AsyncMock()
    mock_kafka_consumer.stop = AsyncMock()
    mock_kafka_consumer.__aiter__ = mock_aiter

    with patch("active_immune_core.communication.kafka_consumers.AIOKafkaConsumer", return_value=mock_kafka_consumer):
        await consumer.start()

        # Wait for message to be processed
        await asyncio.sleep(0.2)

        await consumer.stop()

        # Handler should have been called
        assert handler_called is True
        assert received_data == {"threat_type": "malware", "severity": "high"}
        assert consumer.total_events_consumed == 1
        assert consumer.total_events_processed == 1


@pytest.mark.asyncio
async def test_consume_events_unknown_topic():
    """Test _consume_events handles unknown topic gracefully."""
    consumer = KafkaEventConsumer()

    # Mock message with unknown topic
    mock_msg = MagicMock()
    mock_msg.topic = "unknown.topic"
    mock_msg.value = {"data": "test"}

    async def mock_aiter(self):
        yield mock_msg
        consumer._running = False

    mock_kafka_consumer = AsyncMock()
    mock_kafka_consumer.start = AsyncMock()
    mock_kafka_consumer.stop = AsyncMock()
    mock_kafka_consumer.__aiter__ = mock_aiter

    with patch("active_immune_core.communication.kafka_consumers.AIOKafkaConsumer", return_value=mock_kafka_consumer):
        await consumer.start()
        await asyncio.sleep(0.2)
        await consumer.stop()

        # Should have consumed but not processed (unknown topic)
        assert consumer.total_events_consumed == 0  # ValueError prevents increment


@pytest.mark.asyncio
async def test_consume_events_processing_error():
    """Test _consume_events handles processing errors."""
    consumer = KafkaEventConsumer()

    # Register handler that raises error
    async def failing_handler(event_data: Dict[str, Any]) -> None:
        raise Exception("Handler error")

    consumer.register_handler(ExternalTopic.NETWORK_EVENTS, failing_handler)

    mock_msg = MagicMock()
    mock_msg.topic = "vertice.network.events"
    mock_msg.value = {"event_type": "anomaly"}

    async def mock_aiter(self):
        yield mock_msg
        consumer._running = False

    mock_kafka_consumer = AsyncMock()
    mock_kafka_consumer.start = AsyncMock()
    mock_kafka_consumer.stop = AsyncMock()
    mock_kafka_consumer.__aiter__ = mock_aiter

    with patch("active_immune_core.communication.kafka_consumers.AIOKafkaConsumer", return_value=mock_kafka_consumer):
        await consumer.start()
        await asyncio.sleep(0.2)
        await consumer.stop()

        # Should have consumed and failed
        assert consumer.total_events_consumed == 1
        assert consumer.total_events_failed == 1


@pytest.mark.asyncio
async def test_consume_events_cancelled():
    """Test _consume_events handles CancelledError."""
    consumer = KafkaEventConsumer()

    async def mock_aiter(self):
        # Raise CancelledError during iteration
        raise asyncio.CancelledError()

    mock_kafka_consumer = AsyncMock()
    mock_kafka_consumer.start = AsyncMock()
    mock_kafka_consumer.stop = AsyncMock()
    mock_kafka_consumer.__aiter__ = mock_aiter

    with patch("active_immune_core.communication.kafka_consumers.AIOKafkaConsumer", return_value=mock_kafka_consumer):
        await consumer.start()
        await asyncio.sleep(0.1)
        await consumer.stop()


@pytest.mark.asyncio
async def test_consume_events_no_consumer():
    """Test _consume_events handles missing consumer gracefully."""
    consumer = KafkaEventConsumer()
    consumer._consumer = None

    # Should return immediately without crashing
    await consumer._consume_events()


@pytest.mark.asyncio
async def test_consume_events_generic_exception():
    """Test _consume_events handles generic exception in loop."""
    consumer = KafkaEventConsumer()

    async def mock_aiter(self):
        # Raise generic exception
        raise RuntimeError("Consumer error")

    mock_kafka_consumer = AsyncMock()
    mock_kafka_consumer.start = AsyncMock()
    mock_kafka_consumer.stop = AsyncMock()
    mock_kafka_consumer.__aiter__ = mock_aiter

    with patch("active_immune_core.communication.kafka_consumers.AIOKafkaConsumer", return_value=mock_kafka_consumer):
        await consumer.start()
        await asyncio.sleep(0.2)

        # kafka_available should be set to False after exception
        assert consumer._kafka_available is False

        await consumer.stop()


@pytest.mark.asyncio
async def test_route_event_handler_invocation_error(consumer: KafkaEventConsumer):
    """Test _route_event handles handler invocation error."""
    # Register handler that will cause invocation error
    def bad_handler(event_data: Dict[str, Any]) -> None:
        # This is intentionally wrong signature (sync instead of async)
        pass

    # Manually add to handlers to bypass register_handler
    consumer._handlers[ExternalTopic.ENDPOINT_EVENTS].append(bad_handler)

    event_data = {"test": "data"}

    # Should handle invocation error gracefully
    await consumer._route_event(ExternalTopic.ENDPOINT_EVENTS, event_data)
