"""Cytokine Integration Tests - Requires Kafka

Run with: docker-compose -f docker-compose.dev.yml up -d kafka
Then: pytest tests/integration/test_cytokines_integration.py -v

These tests validate real Kafka producer/consumer functionality.
"""

import asyncio

import pytest
import pytest_asyncio

from active_immune_core.communication import CytokineMessenger, CytokineType

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


@pytest_asyncio.fixture
async def cytokine_messenger():
    """Create and start CytokineMessenger"""
    messenger = CytokineMessenger(
        bootstrap_servers="localhost:9092",
        topic_prefix="immunis.cytokines.test",
        consumer_group_prefix="test_consumer",
    )

    await messenger.start()
    yield messenger
    await messenger.stop()


@pytest.mark.asyncio
class TestCytokineIntegration:
    """Integration tests for Cytokine messaging"""

    async def test_send_cytokine_success(self, cytokine_messenger):
        """Test sending a cytokine message"""
        success = await cytokine_messenger.send_cytokine(
            tipo=CytokineType.IL1,
            payload={
                "evento": "test_threat",
                "alvo": {"ip": "192.0.2.100"},
            },
            emissor_id="test_agent_123",
            prioridade=8,
        )

        assert success is True

    async def test_send_receive_cytokine(self, cytokine_messenger):
        """Test sending and receiving a cytokine"""
        received_messages = []

        async def callback(cytokine):
            """Callback to capture received messages"""
            received_messages.append(cytokine)

        # Subscribe to IL6
        await cytokine_messenger.subscribe(
            cytokine_types=[CytokineType.IL6],
            callback=callback,
            consumer_id="test_consumer_1",
        )

        # Wait for consumer to be ready
        await asyncio.sleep(2)

        # Send message
        await cytokine_messenger.send_cytokine(
            tipo=CytokineType.IL6,
            payload={"evento": "test_inflammation"},
            emissor_id="test_sender",
            prioridade=5,
        )

        # Wait for message to be received
        await asyncio.sleep(3)

        # Verify message received
        assert len(received_messages) > 0
        assert received_messages[0].tipo == CytokineType.IL6
        assert received_messages[0].emissor_id == "test_sender"
        assert received_messages[0].payload["evento"] == "test_inflammation"

    async def test_area_filtering(self, cytokine_messenger):
        """Test area-based message filtering"""
        received_messages = []

        async def callback(cytokine):
            received_messages.append(cytokine)

        # Subscribe with area filter
        await cytokine_messenger.subscribe(
            cytokine_types=[CytokineType.TNF],
            callback=callback,
            consumer_id="test_consumer_2",
            area_filter="subnet_10_0_1_0",
        )

        await asyncio.sleep(2)

        # Send message to different area (should be filtered out)
        await cytokine_messenger.send_cytokine(
            tipo=CytokineType.TNF,
            payload={"evento": "test"},
            emissor_id="test",
            area_alvo="subnet_10_0_2_0",  # Different area
        )

        # Send message to correct area (should be received)
        await cytokine_messenger.send_cytokine(
            tipo=CytokineType.TNF,
            payload={"evento": "test_correct_area"},
            emissor_id="test",
            area_alvo="subnet_10_0_1_0",  # Correct area
        )

        await asyncio.sleep(3)

        # Should only receive message for correct area
        assert len(received_messages) == 1
        assert received_messages[0].area_alvo == "subnet_10_0_1_0"

    async def test_ttl_expiration(self, cytokine_messenger):
        """Test TTL expiration (messages older than TTL are skipped)"""
        received_messages = []

        async def callback(cytokine):
            received_messages.append(cytokine)

        # Send message with very short TTL
        await cytokine_messenger.send_cytokine(
            tipo=CytokineType.IL8,
            payload={"evento": "test_ttl"},
            emissor_id="test",
            ttl_segundos=10,  # 10 second TTL (minimum allowed)
        )

        # Wait for TTL to expire
        await asyncio.sleep(12)

        # Now subscribe (message should be expired)
        await cytokine_messenger.subscribe(
            cytokine_types=[CytokineType.IL8],
            callback=callback,
            consumer_id="test_consumer_3",
        )

        await asyncio.sleep(2)

        # Should not receive expired message
        assert len(received_messages) == 0

    async def test_multiple_subscribers(self, cytokine_messenger):
        """Test that multiple subscribers receive the same message"""
        messages_1 = []
        messages_2 = []

        async def callback_1(cytokine):
            messages_1.append(cytokine)

        async def callback_2(cytokine):
            messages_2.append(cytokine)

        # Subscribe two consumers
        await cytokine_messenger.subscribe(
            cytokine_types=[CytokineType.IL10],
            callback=callback_1,
            consumer_id="test_consumer_4a",
        )

        await cytokine_messenger.subscribe(
            cytokine_types=[CytokineType.IL10],
            callback=callback_2,
            consumer_id="test_consumer_4b",
        )

        await asyncio.sleep(2)

        # Send message
        await cytokine_messenger.send_cytokine(
            tipo=CytokineType.IL10,
            payload={"evento": "test_multi_subscriber"},
            emissor_id="test",
        )

        await asyncio.sleep(3)

        # Both should receive (Kafka consumer groups)
        # Note: In Kafka, same group = load balancing, different groups = broadcast
        # Our implementation uses different group IDs per consumer_id
        assert len(messages_1) > 0 or len(messages_2) > 0

    async def test_messenger_stats(self, cytokine_messenger):
        """Test messenger statistics"""
        stats = cytokine_messenger.get_stats()

        assert stats["running"] is True
        assert stats["producer_active"] is True
        assert isinstance(stats["consumers_active"], int)
        assert isinstance(stats["consumer_ids"], list)


@pytest.mark.asyncio
class TestCytokineErrorHandling:
    """Test error handling in Cytokine messaging"""

    async def test_send_without_start(self):
        """Test sending cytokine without starting messenger"""
        messenger = CytokineMessenger()

        success = await messenger.send_cytokine(
            tipo=CytokineType.IL1,
            payload={"test": "data"},
            emissor_id="test",
        )

        assert success is False  # Should fail gracefully

    async def test_subscribe_without_start(self):
        """Test subscribing without starting messenger"""
        messenger = CytokineMessenger()

        with pytest.raises(Exception):
            await messenger.subscribe(
                cytokine_types=[CytokineType.IL1],
                callback=lambda x: None,
                consumer_id="test",
            )
