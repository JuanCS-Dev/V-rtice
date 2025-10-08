"""Hormone Integration Tests - Requires Redis

Run with: docker-compose -f docker-compose.dev.yml up -d redis
Then: pytest tests/integration/test_hormones_integration.py -v

These tests validate real Redis Pub/Sub functionality.
"""

import asyncio

import pytest
import pytest_asyncio

from active_immune_core.communication import HormoneMessenger, HormoneType

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


@pytest_asyncio.fixture
async def hormone_messenger():
    """Create and start HormoneMessenger"""
    messenger = HormoneMessenger(
        redis_url="redis://localhost:6379",
        channel_prefix="hormonio_test",
    )

    await messenger.start()
    yield messenger
    await messenger.stop()


@pytest.mark.asyncio
class TestHormoneIntegration:
    """Integration tests for Hormone messaging"""

    async def test_publish_hormone_success(self, hormone_messenger):
        """Test publishing a hormone message"""
        num_subscribers = await hormone_messenger.publish_hormone(
            tipo=HormoneType.CORTISOL,
            nivel=7.5,
            payload={
                "evento": "test_stress",
                "temperatura_global": 39.0,
            },
            emissor="test_lymphnode",
        )

        # num_subscribers may be 0 if no subscribers yet
        assert isinstance(num_subscribers, int)
        assert num_subscribers >= 0

    async def test_publish_subscribe_hormone(self, hormone_messenger):
        """Test publishing and receiving a hormone"""
        received_messages = []

        async def callback(hormone):
            """Callback to capture received messages"""
            received_messages.append(hormone)

        # Subscribe to ADRENALINE
        await hormone_messenger.subscribe(
            hormone_types=[HormoneType.ADRENALINE],
            callback=callback,
            subscriber_id="test_subscriber_1",
        )

        # Wait for subscriber to be ready
        await asyncio.sleep(1)

        # Publish message
        await hormone_messenger.publish_hormone(
            tipo=HormoneType.ADRENALINE,
            nivel=9.0,
            payload={"evento": "test_fight_or_flight"},
            emissor="test_global",
        )

        # Wait for message to be received
        await asyncio.sleep(2)

        # Verify message received
        assert len(received_messages) > 0
        assert received_messages[0].tipo == HormoneType.ADRENALINE
        assert received_messages[0].nivel == 9.0
        assert received_messages[0].emissor == "test_global"
        assert received_messages[0].payload["evento"] == "test_fight_or_flight"

    async def test_multiple_subscribers_broadcast(self, hormone_messenger):
        """Test that multiple subscribers all receive the same message (broadcast)"""
        messages_1 = []
        messages_2 = []
        messages_3 = []

        async def callback_1(hormone):
            messages_1.append(hormone)

        async def callback_2(hormone):
            messages_2.append(hormone)

        async def callback_3(hormone):
            messages_3.append(hormone)

        # Subscribe three subscribers to the same hormone
        await hormone_messenger.subscribe(
            hormone_types=[HormoneType.MELATONIN],
            callback=callback_1,
            subscriber_id="test_subscriber_2a",
        )

        await hormone_messenger.subscribe(
            hormone_types=[HormoneType.MELATONIN],
            callback=callback_2,
            subscriber_id="test_subscriber_2b",
        )

        await hormone_messenger.subscribe(
            hormone_types=[HormoneType.MELATONIN],
            callback=callback_3,
            subscriber_id="test_subscriber_2c",
        )

        await asyncio.sleep(1)

        # Publish message
        num_subscribers = await hormone_messenger.publish_hormone(
            tipo=HormoneType.MELATONIN,
            nivel=5.0,
            payload={"evento": "circadian_sleep"},
            emissor="test",
        )

        await asyncio.sleep(2)

        # All three should receive (Redis Pub/Sub broadcasts to all)
        assert num_subscribers == 3
        assert len(messages_1) > 0
        assert len(messages_2) > 0
        assert len(messages_3) > 0

    async def test_agent_state_management(self, hormone_messenger):
        """Test storing and retrieving agent state"""
        agent_id = "test_agent_123"
        state = {
            "tipo": "macrofago",
            "status": "patrulhando",
            "energia": 85.0,
            "temperatura": 37.5,
        }

        # Set state
        success = await hormone_messenger.set_agent_state(agent_id=agent_id, state=state, ttl=60)
        assert success is True

        # Get state
        retrieved_state = await hormone_messenger.get_agent_state(agent_id)
        assert retrieved_state is not None
        assert retrieved_state["tipo"] == "macrofago"
        assert retrieved_state["energia"] == 85.0

        # Delete state
        success = await hormone_messenger.delete_agent_state(agent_id)
        assert success is True

        # Verify deleted
        retrieved_state = await hormone_messenger.get_agent_state(agent_id)
        assert retrieved_state is None

    async def test_get_all_agent_states(self, hormone_messenger):
        """Test retrieving all agent states"""
        # Set multiple agent states
        states = {
            "agent_1": {"tipo": "macrofago", "energia": 90.0},
            "agent_2": {"tipo": "nk_cell", "energia": 75.0},
            "agent_3": {"tipo": "neutrofilo", "energia": 60.0},
        }

        for agent_id, state in states.items():
            await hormone_messenger.set_agent_state(agent_id, state, ttl=60)

        # Get all states
        all_states = await hormone_messenger.get_all_agent_states()

        # Verify all states retrieved
        assert len(all_states) >= 3
        assert "agent_1" in all_states
        assert "agent_2" in all_states
        assert "agent_3" in all_states

        # Cleanup
        for agent_id in states.keys():
            await hormone_messenger.delete_agent_state(agent_id)

    async def test_agent_state_ttl_expiration(self, hormone_messenger):
        """Test that agent state expires after TTL"""
        agent_id = "test_agent_ttl"
        state = {"tipo": "test", "energia": 100.0}

        # Set state with 2 second TTL
        await hormone_messenger.set_agent_state(agent_id, state, ttl=2)

        # Verify state exists
        retrieved = await hormone_messenger.get_agent_state(agent_id)
        assert retrieved is not None

        # Wait for TTL to expire
        await asyncio.sleep(3)

        # Verify state expired
        retrieved = await hormone_messenger.get_agent_state(agent_id)
        assert retrieved is None

    async def test_messenger_stats(self, hormone_messenger):
        """Test messenger statistics"""
        stats = hormone_messenger.get_stats()

        assert stats["running"] is True
        assert stats["client_active"] is True
        assert isinstance(stats["subscribers_active"], int)
        assert isinstance(stats["subscriber_ids"], list)


@pytest.mark.asyncio
class TestHormoneErrorHandling:
    """Test error handling in Hormone messaging"""

    async def test_publish_without_start(self):
        """Test publishing hormone without starting messenger"""
        messenger = HormoneMessenger()

        num_subscribers = await messenger.publish_hormone(
            tipo=HormoneType.CORTISOL,
            nivel=5.0,
            payload={"test": "data"},
        )

        assert num_subscribers == 0  # Should fail gracefully

    async def test_subscribe_without_start(self):
        """Test subscribing without starting messenger"""
        messenger = HormoneMessenger()

        with pytest.raises(RuntimeError, match="Redis client not started"):
            await messenger.subscribe(
                hormone_types=[HormoneType.CORTISOL],
                callback=lambda x: None,
                subscriber_id="test",
            )

    async def test_state_operations_without_start(self):
        """Test state operations without starting messenger"""
        messenger = HormoneMessenger()

        # Set state
        success = await messenger.set_agent_state("test", {"data": "test"})
        assert success is False

        # Get state
        state = await messenger.get_agent_state("test")
        assert state is None

        # Delete state
        success = await messenger.delete_agent_state("test")
        assert success is False
