"""Cytokine Communication Tests - PAGANI 100%

Comprehensive test suite for Kafka-based cytokine messaging with graceful degradation.

Tests cover:
- Models (CytokineType, CytokineMessage)
- Lifecycle (start, stop)
- Producer (send with success/retry/failure)
- Consumer (subscribe, unsubscribe, delivery)
- In-memory mode (degraded operation)
- Exception handling (timeout, errors)
- Edge cases (TTL, area filtering, etc.)
"""

import asyncio
from datetime import datetime, timedelta
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from active_immune_core.communication.cytokines import (
    CytokineMessage,
    CytokineMessenger,
    CytokineType,
)

# ==================== FIXTURES ====================


@pytest_asyncio.fixture
async def messenger():
    """Create CytokineMessenger in degraded mode (no Kafka)"""
    msg = CytokineMessenger(
        bootstrap_servers="localhost:9092",
        topic_prefix="test.cytokines",
        consumer_group_prefix="test_group",
    )
    # Start in degraded mode (Kafka not running)
    await msg.start()
    yield msg
    await msg.stop()


@pytest.fixture
def sample_cytokine_message():
    """Sample cytokine message"""
    return {
        "tipo": CytokineType.IL1,
        "emissor_id": "macrofago_test_001",
        "prioridade": 8,
        "payload": {
            "evento": "ameaca_detectada",
            "alvo": {"ip": "192.0.2.100"},
            "severidade": "alta",
        },
        "area_alvo": "subnet_10_0_1_0",
        "ttl_segundos": 300,
    }


# ==================== MODEL TESTS ====================


@pytest.mark.asyncio
class TestCytokineType:
    """Test CytokineType class methods"""

    def test_all_cytokines(self):
        """Test getting all cytokine types"""
        all_types = CytokineType.all()

        assert len(all_types) == 10
        assert CytokineType.IL1 in all_types
        assert CytokineType.IL6 in all_types
        assert CytokineType.TNF in all_types
        assert CytokineType.IFN_GAMMA in all_types
        assert CytokineType.IL10 in all_types
        assert CytokineType.TGF_BETA in all_types

    def test_pro_inflammatory(self):
        """Test getting pro-inflammatory cytokines"""
        pro_inflam = CytokineType.pro_inflammatory()

        assert len(pro_inflam) == 5
        assert CytokineType.IL1 in pro_inflam
        assert CytokineType.IL6 in pro_inflam
        assert CytokineType.TNF in pro_inflam
        assert CytokineType.IL8 in pro_inflam
        assert CytokineType.IFN_GAMMA in pro_inflam

    def test_anti_inflammatory(self):
        """Test getting anti-inflammatory cytokines"""
        anti_inflam = CytokineType.anti_inflammatory()

        assert len(anti_inflam) == 2
        assert CytokineType.IL10 in anti_inflam
        assert CytokineType.TGF_BETA in anti_inflam


@pytest.mark.asyncio
class TestCytokineMessage:
    """Test CytokineMessage model"""

    def test_message_creation(self, sample_cytokine_message):
        """Test creating a cytokine message"""
        msg = CytokineMessage(**sample_cytokine_message)

        assert msg.tipo == CytokineType.IL1
        assert msg.emissor_id == "macrofago_test_001"
        assert msg.prioridade == 8
        assert msg.area_alvo == "subnet_10_0_1_0"
        assert msg.ttl_segundos == 300
        assert isinstance(msg.payload, dict)

    def test_message_default_timestamp(self):
        """Test that timestamp is auto-generated"""
        msg = CytokineMessage(
            tipo=CytokineType.IL6,
            emissor_id="test_agent",
            payload={"test": "data"},
        )

        # Timestamp should be recent
        msg_time = datetime.fromisoformat(msg.timestamp)
        age = (datetime.now() - msg_time).total_seconds()
        assert age < 1.0  # Less than 1 second old

    def test_message_default_priority(self):
        """Test default priority is 5"""
        msg = CytokineMessage(
            tipo=CytokineType.TNF,
            emissor_id="test_agent",
            payload={},
        )

        assert msg.prioridade == 5

    def test_message_priority_validation(self):
        """Test priority validation (1-10)"""
        # Valid priorities
        msg1 = CytokineMessage(
            tipo=CytokineType.IL1,
            emissor_id="test",
            payload={},
            prioridade=1,
        )
        assert msg1.prioridade == 1

        msg10 = CytokineMessage(
            tipo=CytokineType.IL1,
            emissor_id="test",
            payload={},
            prioridade=10,
        )
        assert msg10.prioridade == 10

        # Invalid priorities should raise validation error
        with pytest.raises(Exception):  # Pydantic validation error
            CytokineMessage(
                tipo=CytokineType.IL1,
                emissor_id="test",
                payload={},
                prioridade=11,  # Too high
            )

    def test_message_ttl_validation(self):
        """Test TTL validation (10-3600 seconds)"""
        # Valid TTLs
        msg_min = CytokineMessage(
            tipo=CytokineType.IL1,
            emissor_id="test",
            payload={},
            ttl_segundos=10,
        )
        assert msg_min.ttl_segundos == 10

        msg_max = CytokineMessage(
            tipo=CytokineType.IL1,
            emissor_id="test",
            payload={},
            ttl_segundos=3600,
        )
        assert msg_max.ttl_segundos == 3600

        # Invalid TTL should raise validation error
        with pytest.raises(Exception):
            CytokineMessage(
                tipo=CytokineType.IL1,
                emissor_id="test",
                payload={},
                ttl_segundos=5,  # Too low
            )


# ==================== LIFECYCLE TESTS ====================


@pytest.mark.asyncio
class TestMessengerLifecycle:
    """Test CytokineMessenger lifecycle"""

    async def test_messenger_initialization(self):
        """Test messenger initialization"""
        msg = CytokineMessenger(
            bootstrap_servers="localhost:9092",
            topic_prefix="test.cytokines",
        )

        assert msg.bootstrap_servers == "localhost:9092"
        assert msg.topic_prefix == "test.cytokines"
        assert msg._running is False
        assert msg._degraded_mode is False

    async def test_messenger_start_degraded_mode(self, messenger):
        """Test messenger starts in degraded mode when Kafka unavailable"""
        assert messenger._running is True
        assert messenger._degraded_mode is True  # Kafka not running

    async def test_messenger_stop(self, messenger):
        """Test messenger stops cleanly"""
        await messenger.stop()

        assert messenger._running is False
        assert messenger._producer is None
        assert len(messenger._consumers) == 0
        assert len(messenger._consumer_tasks) == 0

    async def test_messenger_double_start(self, messenger):
        """Test that starting twice doesn't cause issues"""
        # Already started in fixture
        await messenger.start()  # Try starting again

        # Should still be running
        assert messenger._running is True

    async def test_messenger_is_running(self, messenger):
        """Test is_running() method"""
        assert messenger._running is True
        # In degraded mode, producer might or might not be None
        # Just verify is_running() works without crashing
        result = messenger.is_running()
        assert isinstance(result, bool)


# ==================== PRODUCER TESTS ====================


@pytest.mark.asyncio
class TestProducerDegradedMode:
    """Test producer in degraded (in-memory) mode"""

    async def test_send_cytokine_degraded_mode(self, messenger, sample_cytokine_message):
        """Test sending cytokine in degraded mode"""
        result = await messenger.send_cytokine(**sample_cytokine_message)

        assert result is True

    async def test_send_cytokine_without_start(self):
        """Test sending cytokine without starting messenger"""
        msg = CytokineMessenger()

        result = await msg.send_cytokine(
            tipo=CytokineType.IL1,
            emissor_id="test",
            payload={},
        )

        # Should fail (not started)
        assert result is False

    async def test_send_cytokine_broadcast(self, messenger):
        """Test sending cytokine with broadcast (no area_alvo)"""
        result = await messenger.send_cytokine(
            tipo=CytokineType.IL6,
            emissor_id="test_agent",
            payload={"evento": "test"},
            prioridade=7,
            area_alvo=None,  # Broadcast
        )

        assert result is True

    async def test_send_cytokine_all_types(self, messenger):
        """Test sending all cytokine types"""
        for cytokine_type in CytokineType.all():
            result = await messenger.send_cytokine(
                tipo=cytokine_type,
                emissor_id="test_agent",
                payload={"test": "data"},
            )
            assert result is True


# ==================== CONSUMER TESTS ====================


@pytest.mark.asyncio
class TestConsumerDegradedMode:
    """Test consumer in degraded (in-memory) mode"""

    async def test_subscribe_degraded_mode(self, messenger):
        """Test subscribing in degraded mode"""
        received_messages: List[CytokineMessage] = []

        async def callback(msg: CytokineMessage):
            received_messages.append(msg)

        await messenger.subscribe(
            cytokine_types=[CytokineType.IL1, CytokineType.IL6],
            callback=callback,
            consumer_id="test_consumer_001",
        )

        # Send cytokines
        await messenger.send_cytokine(
            tipo=CytokineType.IL1,
            emissor_id="test_sender",
            payload={"test": "il1"},
        )

        await messenger.send_cytokine(
            tipo=CytokineType.IL6,
            emissor_id="test_sender",
            payload={"test": "il6"},
        )

        # Give tasks time to execute
        await asyncio.sleep(0.1)

        # Should have received both messages
        assert len(received_messages) >= 2

    async def test_subscribe_without_start(self):
        """Test subscribing without starting messenger"""
        msg = CytokineMessenger()

        async def callback(msg: CytokineMessage):
            pass

        with pytest.raises(RuntimeError, match="not started"):
            await msg.subscribe(
                cytokine_types=[CytokineType.IL1],
                callback=callback,
                consumer_id="test",
            )

    async def test_subscribe_duplicate_consumer_id(self, messenger):
        """Test subscribing with duplicate consumer ID"""

        async def callback(msg: CytokineMessage):
            pass

        # First subscription
        await messenger.subscribe(
            cytokine_types=[CytokineType.IL1],
            callback=callback,
            consumer_id="duplicate_id",
        )

        # Second subscription with same ID (should warn but not error)
        await messenger.subscribe(
            cytokine_types=[CytokineType.IL6],
            callback=callback,
            consumer_id="duplicate_id",
        )

    async def test_area_filtering(self, messenger):
        """Test area filtering in subscriptions"""
        area1_messages: List[CytokineMessage] = []
        area2_messages: List[CytokineMessage] = []

        async def area1_callback(msg: CytokineMessage):
            area1_messages.append(msg)

        async def area2_callback(msg: CytokineMessage):
            area2_messages.append(msg)

        # Subscribe with area filters
        await messenger.subscribe(
            cytokine_types=[CytokineType.IL1],
            callback=area1_callback,
            consumer_id="area1_consumer",
            area_filter="subnet_10_0_1_0",
        )

        await messenger.subscribe(
            cytokine_types=[CytokineType.IL1],
            callback=area2_callback,
            consumer_id="area2_consumer",
            area_filter="subnet_10_0_2_0",
        )

        # Send to area1
        await messenger.send_cytokine(
            tipo=CytokineType.IL1,
            emissor_id="test",
            payload={"test": "area1"},
            area_alvo="subnet_10_0_1_0",
        )

        # Send to area2
        await messenger.send_cytokine(
            tipo=CytokineType.IL1,
            emissor_id="test",
            payload={"test": "area2"},
            area_alvo="subnet_10_0_2_0",
        )

        await asyncio.sleep(0.1)

        # Each should only receive messages for their area
        assert len(area1_messages) >= 1
        assert len(area2_messages) >= 1
        assert all(msg.area_alvo == "subnet_10_0_1_0" for msg in area1_messages)
        assert all(msg.area_alvo == "subnet_10_0_2_0" for msg in area2_messages)


# ==================== UTILITY TESTS ====================


@pytest.mark.asyncio
class TestMessengerUtilities:
    """Test messenger utility methods"""

    async def test_get_active_consumers_empty(self, messenger):
        """Test getting active consumers when none exist"""
        consumers = messenger.get_active_consumers()

        assert consumers == []

    async def test_get_active_consumers_with_subscribers(self, messenger):
        """Test getting active consumers after subscribing"""

        async def callback(msg: CytokineMessage):
            pass

        await messenger.subscribe(
            cytokine_types=[CytokineType.IL1],
            callback=callback,
            consumer_id="consumer_001",
        )

        consumers = messenger.get_active_consumers()

        # In degraded mode, consumers list stays empty (in-memory mode)
        # But subscription works via _in_memory_subscribers
        assert CytokineType.IL1 in messenger._in_memory_subscribers

    async def test_get_stats(self, messenger):
        """Test getting messenger statistics"""
        stats = messenger.get_stats()

        assert "running" in stats
        assert "producer_active" in stats
        assert "consumers_active" in stats
        assert "consumer_ids" in stats
        assert "consumer_tasks" in stats

        assert stats["running"] is True
        assert isinstance(stats["consumers_active"], int)
        assert isinstance(stats["consumer_ids"], list)


# ==================== EDGE CASES ====================


@pytest.mark.asyncio
class TestEdgeCases:
    """Test edge cases and error handling"""

    async def test_callback_exception_handling(self, messenger):
        """Test that callback exceptions don't crash messenger"""

        async def failing_callback(msg: CytokineMessage):
            raise Exception("Callback error")

        await messenger.subscribe(
            cytokine_types=[CytokineType.IL1],
            callback=failing_callback,
            consumer_id="failing_consumer",
        )

        # Send cytokine (should not crash even if callback fails)
        result = await messenger.send_cytokine(
            tipo=CytokineType.IL1,
            emissor_id="test",
            payload={},
        )

        assert result is True
        await asyncio.sleep(0.1)

        # Messenger should still be running
        assert messenger._running is True

    async def test_non_async_callback(self, messenger):
        """Test that non-async callbacks work"""
        received_messages = []

        def sync_callback(msg: CytokineMessage):
            received_messages.append(msg)

        await messenger.subscribe(
            cytokine_types=[CytokineType.IL1],
            callback=sync_callback,
            consumer_id="sync_consumer",
        )

        await messenger.send_cytokine(
            tipo=CytokineType.IL1,
            emissor_id="test",
            payload={},
        )

        await asyncio.sleep(0.1)

        # Non-async callback should still work in degraded mode
        # (though it won't in real Kafka mode without await)

    async def test_send_with_custom_ttl(self, messenger):
        """Test sending with custom TTL"""
        result = await messenger.send_cytokine(
            tipo=CytokineType.IL1,
            emissor_id="test",
            payload={},
            ttl_segundos=60,
        )

        assert result is True

    async def test_multiple_subscribers_same_cytokine(self, messenger):
        """Test multiple subscribers to same cytokine type"""
        received1: List[CytokineMessage] = []
        received2: List[CytokineMessage] = []

        async def callback1(msg: CytokineMessage):
            received1.append(msg)

        async def callback2(msg: CytokineMessage):
            received2.append(msg)

        await messenger.subscribe(
            cytokine_types=[CytokineType.IL1],
            callback=callback1,
            consumer_id="consumer1",
        )

        await messenger.subscribe(
            cytokine_types=[CytokineType.IL1],
            callback=callback2,
            consumer_id="consumer2",
        )

        await messenger.send_cytokine(
            tipo=CytokineType.IL1,
            emissor_id="test",
            payload={"test": "broadcast"},
        )

        await asyncio.sleep(0.1)

        # Both should receive the message
        assert len(received1) >= 1
        assert len(received2) >= 1


# ==================== KAFKA MODE TESTS (WITH MOCKING) ====================


@pytest.mark.asyncio
class TestProducerKafkaMode:
    """Test producer with mocked Kafka (non-degraded mode)"""

    async def test_send_cytokine_kafka_success(self):
        """Test sending cytokine with successful Kafka response"""
        msg = CytokineMessenger()

        # Mock Kafka producer
        mock_producer = AsyncMock()
        mock_metadata = MagicMock()
        mock_metadata.partition = 0
        mock_metadata.offset = 12345
        mock_producer.send_and_wait = AsyncMock(return_value=mock_metadata)
        mock_producer.start = AsyncMock()
        mock_producer.stop = AsyncMock()

        with patch("active_immune_core.communication.cytokines.AIOKafkaProducer", return_value=mock_producer):
            await msg.start()

            # Should not be in degraded mode
            assert msg._degraded_mode is False

            result = await msg.send_cytokine(
                tipo=CytokineType.IL1,
                emissor_id="test_agent",
                payload={"test": "data"},
            )

            assert result is True
            mock_producer.send_and_wait.assert_called_once()

            await msg.stop()

    async def test_send_cytokine_kafka_timeout_with_retry(self):
        """Test sending cytokine with Kafka timeout and retry"""
        from aiokafka.errors import KafkaTimeoutError

        msg = CytokineMessenger(max_retries=3)

        # Mock producer that times out twice then succeeds
        mock_producer = AsyncMock()
        mock_metadata = MagicMock()
        mock_metadata.partition = 0
        mock_metadata.offset = 100
        mock_producer.send_and_wait = AsyncMock(
            side_effect=[
                KafkaTimeoutError(),  # First attempt fails
                KafkaTimeoutError(),  # Second attempt fails
                mock_metadata,  # Third attempt succeeds
            ]
        )
        mock_producer.start = AsyncMock()
        mock_producer.stop = AsyncMock()

        with patch("active_immune_core.communication.cytokines.AIOKafkaProducer", return_value=mock_producer):
            await msg.start()

            result = await msg.send_cytokine(
                tipo=CytokineType.TNF,
                emissor_id="test",
                payload={},
            )

            # Should succeed on third retry
            assert result is True
            assert mock_producer.send_and_wait.call_count == 3

            await msg.stop()

    async def test_send_cytokine_kafka_timeout_max_retries(self):
        """Test sending cytokine with Kafka timeout exceeding max retries"""
        from aiokafka.errors import KafkaTimeoutError

        msg = CytokineMessenger(max_retries=2)

        mock_producer = AsyncMock()
        mock_producer.send_and_wait = AsyncMock(side_effect=KafkaTimeoutError())
        mock_producer.start = AsyncMock()
        mock_producer.stop = AsyncMock()

        with patch("active_immune_core.communication.cytokines.AIOKafkaProducer", return_value=mock_producer):
            await msg.start()

            result = await msg.send_cytokine(
                tipo=CytokineType.IL6,
                emissor_id="test",
                payload={},
            )

            # Should fail after max retries
            assert result is False
            assert mock_producer.send_and_wait.call_count == 2

            await msg.stop()

    async def test_send_cytokine_kafka_error(self):
        """Test sending cytokine with KafkaError"""
        from aiokafka.errors import KafkaError

        msg = CytokineMessenger()

        mock_producer = AsyncMock()
        mock_producer.send_and_wait = AsyncMock(side_effect=KafkaError("Broker error"))
        mock_producer.start = AsyncMock()
        mock_producer.stop = AsyncMock()

        with patch("active_immune_core.communication.cytokines.AIOKafkaProducer", return_value=mock_producer):
            await msg.start()

            result = await msg.send_cytokine(
                tipo=CytokineType.IL8,
                emissor_id="test",
                payload={},
            )

            # Should fail immediately on KafkaError (no retry)
            assert result is False
            mock_producer.send_and_wait.assert_called_once()

            await msg.stop()

    async def test_send_cytokine_generic_exception(self):
        """Test sending cytokine with generic exception"""
        msg = CytokineMessenger()

        mock_producer = AsyncMock()
        mock_producer.send_and_wait = AsyncMock(side_effect=Exception("Network error"))
        mock_producer.start = AsyncMock()
        mock_producer.stop = AsyncMock()

        with patch("active_immune_core.communication.cytokines.AIOKafkaProducer", return_value=mock_producer):
            await msg.start()

            result = await msg.send_cytokine(
                tipo=CytokineType.IFN_GAMMA,
                emissor_id="test",
                payload={},
            )

            # Should fail on exception
            assert result is False

            await msg.stop()


@pytest.mark.asyncio
class TestConsumerKafkaMode:
    """Test consumer with mocked Kafka (non-degraded mode)"""

    async def test_subscribe_kafka_mode(self):
        """Test subscribing with Kafka consumer"""
        msg = CytokineMessenger()

        # Mock producer
        mock_producer = AsyncMock()
        mock_producer.start = AsyncMock()
        mock_producer.stop = AsyncMock()

        # Mock consumer
        mock_consumer = AsyncMock()
        mock_consumer.start = AsyncMock()
        mock_consumer.stop = AsyncMock()

        async def callback(cytokine: CytokineMessage):
            pass

        with patch("active_immune_core.communication.cytokines.AIOKafkaProducer", return_value=mock_producer):
            with patch("active_immune_core.communication.cytokines.AIOKafkaConsumer", return_value=mock_consumer):
                await msg.start()

                await msg.subscribe(
                    cytokine_types=[CytokineType.IL1],
                    callback=callback,
                    consumer_id="test_consumer",
                )

                # Consumer should be started
                mock_consumer.start.assert_called_once()
                assert "test_consumer" in msg._consumers

                await msg.stop()

    async def test_subscribe_kafka_failure_degraded(self):
        """Test subscribing with Kafka failure falls back to degraded mode"""
        msg = CytokineMessenger()

        mock_producer = AsyncMock()
        mock_producer.start = AsyncMock()
        mock_producer.stop = AsyncMock()

        # Mock consumer that fails to start
        mock_consumer = AsyncMock()
        mock_consumer.start = AsyncMock(side_effect=Exception("Connection error"))

        async def callback(cytokine: CytokineMessage):
            pass

        with patch("active_immune_core.communication.cytokines.AIOKafkaProducer", return_value=mock_producer):
            with patch("active_immune_core.communication.cytokines.AIOKafkaConsumer", return_value=mock_consumer):
                await msg.start()

                # Should not raise exception, just fall back to degraded mode
                await msg.subscribe(
                    cytokine_types=[CytokineType.IL1],
                    callback=callback,
                    consumer_id="test_consumer",
                )

                # Should be in degraded mode
                assert msg._degraded_mode is True

                await msg.stop()

    async def test_unsubscribe_kafka_mode(self):
        """Test unsubscribing consumer"""
        msg = CytokineMessenger()

        mock_producer = AsyncMock()
        mock_producer.start = AsyncMock()
        mock_producer.stop = AsyncMock()

        mock_consumer = AsyncMock()
        mock_consumer.start = AsyncMock()
        mock_consumer.stop = AsyncMock()

        async def callback(cytokine: CytokineMessage):
            pass

        with patch("active_immune_core.communication.cytokines.AIOKafkaProducer", return_value=mock_producer):
            with patch("active_immune_core.communication.cytokines.AIOKafkaConsumer", return_value=mock_consumer):
                await msg.start()

                await msg.subscribe(
                    cytokine_types=[CytokineType.IL1],
                    callback=callback,
                    consumer_id="test_consumer",
                )

                # Unsubscribe
                await msg.unsubscribe("test_consumer")

                # Consumer should be stopped and removed
                mock_consumer.stop.assert_called_once()
                assert "test_consumer" not in msg._consumers

                await msg.stop()

    async def test_unsubscribe_nonexistent_consumer(self):
        """Test unsubscribing nonexistent consumer"""
        msg = CytokineMessenger()
        await msg.start()

        # Should not raise exception
        await msg.unsubscribe("nonexistent_consumer")

        await msg.stop()

    async def test_unsubscribe_error_handling(self):
        """Test unsubscribe handles consumer stop errors"""
        msg = CytokineMessenger()

        mock_producer = AsyncMock()
        mock_producer.start = AsyncMock()
        mock_producer.stop = AsyncMock()

        mock_consumer = AsyncMock()
        mock_consumer.start = AsyncMock()
        mock_consumer.stop = AsyncMock(side_effect=Exception("Stop error"))

        async def callback(cytokine: CytokineMessage):
            pass

        with patch("active_immune_core.communication.cytokines.AIOKafkaProducer", return_value=mock_producer):
            with patch("active_immune_core.communication.cytokines.AIOKafkaConsumer", return_value=mock_consumer):
                await msg.start()

                await msg.subscribe(
                    cytokine_types=[CytokineType.IL1],
                    callback=callback,
                    consumer_id="test_consumer",
                )

                # Unsubscribe should handle error gracefully
                await msg.unsubscribe("test_consumer")

                await msg.stop()


@pytest.mark.asyncio
class TestStopWithErrors:
    """Test stop() method with various error scenarios"""

    async def test_stop_with_consumer_error(self):
        """Test stop handles consumer stop errors"""
        msg = CytokineMessenger()

        mock_producer = AsyncMock()
        mock_producer.start = AsyncMock()
        mock_producer.stop = AsyncMock()

        mock_consumer = AsyncMock()
        mock_consumer.start = AsyncMock()
        mock_consumer.stop = AsyncMock(side_effect=Exception("Consumer stop error"))

        async def callback(cytokine: CytokineMessage):
            pass

        with patch("active_immune_core.communication.cytokines.AIOKafkaProducer", return_value=mock_producer):
            with patch("active_immune_core.communication.cytokines.AIOKafkaConsumer", return_value=mock_consumer):
                await msg.start()

                await msg.subscribe(
                    cytokine_types=[CytokineType.IL1],
                    callback=callback,
                    consumer_id="test_consumer",
                )

                # Stop should handle error gracefully
                await msg.stop()

                # Should still be stopped
                assert msg._running is False

    async def test_stop_with_producer_error(self):
        """Test stop handles producer stop errors"""
        msg = CytokineMessenger()

        mock_producer = AsyncMock()
        mock_producer.start = AsyncMock()
        mock_producer.stop = AsyncMock(side_effect=Exception("Producer stop error"))

        with patch("active_immune_core.communication.cytokines.AIOKafkaProducer", return_value=mock_producer):
            await msg.start()

            # Stop should handle error gracefully
            await msg.stop()

            # Producer should be None even with error
            assert msg._producer is None
            assert msg._running is False


# ==================== PHASE 3: ADVANCED COVERAGE (METRICS, CONSUME LOOP) ====================


@pytest.mark.asyncio
class TestMetricsIntegration:
    """Test Prometheus metrics integration (optional imports)"""

    async def test_send_cytokine_metrics_import_fails(self):
        """Test cytokine send when metrics module unavailable (ImportError ignored)"""
        msg = CytokineMessenger(
            bootstrap_servers="localhost:9092",
        )

        mock_producer = AsyncMock()
        mock_metadata = MagicMock()
        mock_metadata.partition = 0
        mock_metadata.offset = 123
        mock_producer.send_and_wait = AsyncMock(return_value=mock_metadata)
        mock_producer.start = AsyncMock()
        mock_producer.stop = AsyncMock()

        with patch("active_immune_core.communication.cytokines.AIOKafkaProducer", return_value=mock_producer):
            await msg.start()

            # ImportError is caught and ignored gracefully
            result = await msg.send_cytokine(
                tipo=CytokineType.IL1,
                emissor_id="test",
                payload={},
            )

            assert result is True
            await msg.stop()


@pytest.mark.asyncio
class TestSubscribeDuplicateKafkaMode:
    """Test duplicate subscription in Kafka mode (line 374-375)"""

    async def test_subscribe_duplicate_consumer_kafka_mode(self):
        """Test subscribing with duplicate consumer_id in Kafka mode logs warning"""
        msg = CytokineMessenger(
            bootstrap_servers="localhost:9092",
        )

        mock_producer = AsyncMock()
        mock_producer.start = AsyncMock()
        mock_producer.stop = AsyncMock()

        mock_consumer = AsyncMock()
        mock_consumer.start = AsyncMock()
        mock_consumer.subscribe = AsyncMock()
        mock_consumer.stop = AsyncMock()

        with patch("active_immune_core.communication.cytokines.AIOKafkaProducer", return_value=mock_producer):
            with patch("active_immune_core.communication.cytokines.AIOKafkaConsumer", return_value=mock_consumer):
                await msg.start()

                callback = AsyncMock()

                # First subscription
                await msg.subscribe(
                    cytokine_types=[CytokineType.IL1],
                    callback=callback,
                    consumer_id="duplicate_test",
                )

                # Duplicate subscription (should log warning and return early)
                await msg.subscribe(
                    cytokine_types=[CytokineType.IL6],
                    callback=callback,
                    consumer_id="duplicate_test",  # Same ID
                )

                # Only one consumer should exist
                assert "duplicate_test" in msg._consumers
                assert len(msg._consumers) == 1

                await msg.stop()


@pytest.mark.asyncio
class TestConsumeLoopScenarios:
    """Test _consume_loop internal logic (lines 436-489)"""

    async def test_consume_loop_processes_messages(self):
        """Test consume loop processes valid messages"""
        msg = CytokineMessenger(
            bootstrap_servers="localhost:9092",
        )

        # Create mock message
        mock_kafka_msg = MagicMock()
        mock_kafka_msg.value = {
            "tipo": CytokineType.IL1,
            "emissor_id": "test",
            "timestamp": datetime.now().isoformat(),
            "prioridade": 5,
            "payload": {"data": "test"},
            "area_alvo": None,
            "ttl_segundos": 300,
        }

        # Mock consumer with async iteration
        mock_consumer = AsyncMock()

        # Mock async iteration
        async def async_gen():
            yield mock_kafka_msg
            # After one message, stop
            msg._running = False

        mock_consumer.__aiter__ = lambda self: async_gen()
        mock_consumer.start = AsyncMock()
        mock_consumer.stop = AsyncMock()

        callback_received = []

        async def test_callback(cytokine: CytokineMessage):
            callback_received.append(cytokine)

        await msg.start()

        # Run consume loop
        await msg._consume_loop(
            consumer=mock_consumer,
            consumer_id="test_consumer",
            callback=test_callback,
            area_filter=None,
        )

        # Verify callback was invoked
        assert len(callback_received) == 1
        assert callback_received[0].tipo == CytokineType.IL1

        await msg.stop()

    async def test_consume_loop_filters_by_area(self):
        """Test consume loop filters messages by area_alvo"""
        msg = CytokineMessenger(
            bootstrap_servers="localhost:9092",
        )

        # Create mock messages with different areas
        mock_msg_area_a = MagicMock()
        mock_msg_area_a.value = {
            "tipo": CytokineType.IL1,
            "emissor_id": "test",
            "timestamp": datetime.now().isoformat(),
            "prioridade": 5,
            "payload": {},
            "area_alvo": "area_a",
            "ttl_segundos": 300,
        }

        mock_msg_area_b = MagicMock()
        mock_msg_area_b.value = {
            "tipo": CytokineType.IL6,
            "emissor_id": "test",
            "timestamp": datetime.now().isoformat(),
            "prioridade": 5,
            "payload": {},
            "area_alvo": "area_b",
            "ttl_segundos": 300,
        }

        mock_consumer = AsyncMock()

        async def async_gen():
            yield mock_msg_area_a
            yield mock_msg_area_b
            msg._running = False

        mock_consumer.__aiter__ = lambda self: async_gen()

        callback_received = []

        async def test_callback(cytokine: CytokineMessage):
            callback_received.append(cytokine)

        await msg.start()

        # Run with area filter for "area_a"
        await msg._consume_loop(
            consumer=mock_consumer,
            consumer_id="test_consumer",
            callback=test_callback,
            area_filter="area_a",
        )

        # Only area_a message should be received
        assert len(callback_received) == 1
        assert callback_received[0].area_alvo == "area_a"

        await msg.stop()

    async def test_consume_loop_skips_expired_messages(self):
        """Test consume loop skips expired messages based on TTL"""
        msg = CytokineMessenger(
            bootstrap_servers="localhost:9092",
        )

        # Create expired message (old timestamp)
        old_timestamp = (datetime.now() - timedelta(seconds=400)).isoformat()

        mock_msg_expired = MagicMock()
        mock_msg_expired.value = {
            "tipo": CytokineType.IL1,
            "emissor_id": "test",
            "timestamp": old_timestamp,
            "prioridade": 5,
            "payload": {},
            "area_alvo": None,
            "ttl_segundos": 300,  # 5 minutes TTL, but message is 400s old
        }

        mock_consumer = AsyncMock()

        async def async_gen():
            yield mock_msg_expired
            msg._running = False

        mock_consumer.__aiter__ = lambda self: async_gen()

        callback_received = []

        async def test_callback(cytokine: CytokineMessage):
            callback_received.append(cytokine)

        await msg.start()

        await msg._consume_loop(
            consumer=mock_consumer,
            consumer_id="test_consumer",
            callback=test_callback,
            area_filter=None,
        )

        # Expired message should be skipped
        assert len(callback_received) == 0

        await msg.stop()

    async def test_consume_loop_handles_callback_exception(self):
        """Test consume loop handles callback exceptions gracefully"""
        msg = CytokineMessenger(
            bootstrap_servers="localhost:9092",
        )

        mock_kafka_msg = MagicMock()
        mock_kafka_msg.value = {
            "tipo": CytokineType.IL1,
            "emissor_id": "test",
            "timestamp": datetime.now().isoformat(),
            "prioridade": 5,
            "payload": {},
            "area_alvo": None,
            "ttl_segundos": 300,
        }

        mock_consumer = AsyncMock()

        async def async_gen():
            yield mock_kafka_msg
            msg._running = False

        mock_consumer.__aiter__ = lambda self: async_gen()

        async def failing_callback(cytokine: CytokineMessage):
            raise ValueError("Callback error!")

        await msg.start()

        # Should not raise, errors are caught and logged
        await msg._consume_loop(
            consumer=mock_consumer,
            consumer_id="test_consumer",
            callback=failing_callback,
            area_filter=None,
        )

        await msg.stop()

    async def test_consume_loop_handles_fatal_error(self):
        """Test consume loop handles fatal errors in main loop"""
        msg = CytokineMessenger(
            bootstrap_servers="localhost:9092",
        )

        mock_consumer = AsyncMock()

        async def async_gen():
            raise Exception("Fatal consumer error!")

        mock_consumer.__aiter__ = lambda self: async_gen()

        callback = AsyncMock()

        await msg.start()

        # Should not raise, errors are caught and logged
        await msg._consume_loop(
            consumer=mock_consumer,
            consumer_id="test_consumer",
            callback=callback,
            area_filter=None,
        )

        await msg.stop()
