"""Tests for MessageBroker RabbitMQ wrapper."""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from agent_communication.broker import MessageBroker, MessageBrokerPool
from agent_communication.message import ACPMessage, AgentType, MessageType, TaskPriority


@pytest.fixture
def broker():
    """Create MessageBroker instance for testing."""
    return MessageBroker(connection_url="amqp://guest:guest@localhost:5672/")


@pytest.fixture
def sample_message():
    """Create sample ACPMessage for testing."""
    return ACPMessage(
        message_type=MessageType.TASK_ASSIGN,
        sender=AgentType.ORCHESTRATOR,
        recipient=AgentType.RECONNAISSANCE,
        payload={"task_type": "port_scan", "target": "10.0.0.1"},
    )


class TestMessageBrokerInitialization:
    """Test broker initialization and configuration."""

    def test_broker_init_default_params(self):
        """Test broker initialization with default parameters."""
        broker = MessageBroker()
        assert broker.connection_url == "amqp://guest:guest@localhost:5672/"
        assert broker.exchange_name == "agent_communication"
        assert broker.connection is None
        assert broker.channel is None

    def test_broker_init_custom_params(self):
        """Test broker initialization with custom parameters."""
        broker = MessageBroker(
            connection_url="amqp://user:pass@rabbit:5672/vhost",
            exchange_name="custom_exchange",
        )
        assert "user:pass" in broker.connection_url
        assert broker.exchange_name == "custom_exchange"


class TestMessageBrokerConnection:
    """Test broker connection management."""

    @pytest.mark.asyncio
    @patch("agent_communication.broker.aio_pika.connect_robust")
    async def test_connect_success(self, mock_connect, broker):
        """Test successful connection to RabbitMQ."""
        # Mock connection and channel
        mock_connection = AsyncMock()
        mock_channel = AsyncMock()
        mock_exchange = AsyncMock()

        mock_connect.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel
        mock_channel.declare_exchange.return_value = mock_exchange

        await broker.connect()

        assert broker.connection == mock_connection
        assert broker.channel == mock_channel
        assert broker.exchange == mock_exchange
        mock_channel.set_qos.assert_called_once_with(prefetch_count=1)

    @pytest.mark.asyncio
    async def test_disconnect(self, broker):
        """Test graceful disconnection."""
        # Mock connection
        broker.connection = AsyncMock()
        broker.connection.is_closed = False

        await broker.disconnect()

        broker.connection.close.assert_called_once()
        assert broker._consuming is False


class TestQueueDeclaration:
    """Test queue declaration and binding."""

    @pytest.mark.asyncio
    async def test_declare_queue_not_connected(self, broker):
        """Test queue declaration fails if not connected."""
        with pytest.raises(RuntimeError, match="Not connected"):
            await broker.declare_queue(AgentType.RECONNAISSANCE)

    @pytest.mark.asyncio
    @patch("agent_communication.broker.aio_pika.connect_robust")
    async def test_declare_queue_success(self, mock_connect, broker):
        """Test successful queue declaration."""
        # Setup mocks
        mock_connection = AsyncMock()
        mock_channel = AsyncMock()
        mock_exchange = AsyncMock()
        mock_queue = AsyncMock()

        mock_connect.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel
        mock_channel.declare_exchange.return_value = mock_exchange
        mock_channel.declare_queue.return_value = mock_queue

        await broker.connect()
        queue = await broker.declare_queue(AgentType.RECONNAISSANCE)

        assert queue == mock_queue
        assert AgentType.RECONNAISSANCE in broker.queues
        mock_channel.declare_queue.assert_called_once()

        # Verify queue name
        call_args = mock_channel.declare_queue.call_args
        assert call_args[0][0] == "agent.reconnaissance"


class TestMessageSending:
    """Test message sending functionality."""

    @pytest.mark.asyncio
    async def test_send_message_not_connected(self, broker, sample_message):
        """Test sending message fails if not connected."""
        with pytest.raises(RuntimeError, match="Not connected"):
            await broker.send_message(sample_message)

    @pytest.mark.asyncio
    @patch("agent_communication.broker.aio_pika.connect_robust")
    async def test_send_message_success(self, mock_connect, broker, sample_message):
        """Test successful message sending."""
        # Setup mocks
        mock_connection = AsyncMock()
        mock_channel = AsyncMock()
        mock_exchange = AsyncMock()

        mock_connect.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel
        mock_channel.declare_exchange.return_value = mock_exchange

        await broker.connect()
        await broker.send_message(sample_message)

        # Verify message was published
        mock_exchange.publish.assert_called_once()
        call_args = mock_exchange.publish.call_args

        # Check routing key
        assert call_args[1]["routing_key"] == "agent.reconnaissance"

        # Check message content
        message_arg = call_args[0][0]
        assert message_arg.message_id == str(sample_message.message_id)

    @pytest.mark.asyncio
    @patch("agent_communication.broker.aio_pika.connect_robust")
    async def test_send_message_priority_mapping(self, mock_connect, broker):
        """Test message priority is correctly mapped to RabbitMQ priority."""
        mock_connection = AsyncMock()
        mock_channel = AsyncMock()
        mock_exchange = AsyncMock()

        mock_connect.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel
        mock_channel.declare_exchange.return_value = mock_exchange

        await broker.connect()

        # Test each priority level
        priority_map = {
            TaskPriority.LOW: 1,
            TaskPriority.MEDIUM: 5,
            TaskPriority.HIGH: 8,
            TaskPriority.CRITICAL: 10,
        }

        for priority, expected_int in priority_map.items():
            msg = ACPMessage(
                message_type=MessageType.TASK_ASSIGN,
                sender=AgentType.ORCHESTRATOR,
                recipient=AgentType.RECONNAISSANCE,
                priority=priority,
                payload={},
            )
            await broker.send_message(msg)

            # Check priority was set correctly
            call_args = mock_exchange.publish.call_args
            message_arg = call_args[0][0]
            assert message_arg.priority == expected_int


class TestMessageConsumption:
    """Test message consumption functionality."""

    @pytest.mark.skip(reason="Complex async mock - integration test needed")
    @pytest.mark.asyncio
    async def test_consume_messages_declares_queue_if_needed(self, broker):
        """Test consumption declares queue if not already declared.

        Note: This requires proper RabbitMQ integration test setup.
        Mocking async iterators is complex and fragile.
        """
        pass


class TestMessageBrokerPool:
    """Test MessageBrokerPool for high-throughput scenarios."""

    @pytest.mark.asyncio
    @patch("agent_communication.broker.aio_pika.connect_robust")
    async def test_pool_initialization(self, mock_connect):
        """Test broker pool initialization."""
        mock_connection = AsyncMock()
        mock_channel = AsyncMock()
        mock_exchange = AsyncMock()

        mock_connect.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel
        mock_channel.declare_exchange.return_value = mock_exchange

        pool = MessageBrokerPool("amqp://localhost/", pool_size=3)
        await pool.initialize()

        assert len(pool.brokers) == 3
        assert all(isinstance(b, MessageBroker) for b in pool.brokers)

    @pytest.mark.asyncio
    @patch("agent_communication.broker.aio_pika.connect_robust")
    async def test_pool_round_robin(self, mock_connect):
        """Test broker pool uses round-robin selection."""
        mock_connection = AsyncMock()
        mock_channel = AsyncMock()
        mock_exchange = AsyncMock()

        mock_connect.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel
        mock_channel.declare_exchange.return_value = mock_exchange

        pool = MessageBrokerPool("amqp://localhost/", pool_size=3)
        await pool.initialize()

        # Get brokers in sequence
        brokers_sequence = [pool.get_broker() for _ in range(6)]

        # Should cycle through pool twice
        assert brokers_sequence[0] == brokers_sequence[3]
        assert brokers_sequence[1] == brokers_sequence[4]
        assert brokers_sequence[2] == brokers_sequence[5]

    @pytest.mark.asyncio
    @patch("agent_communication.broker.aio_pika.connect_robust")
    async def test_pool_shutdown(self, mock_connect):
        """Test broker pool graceful shutdown."""
        mock_connection = AsyncMock()
        mock_channel = AsyncMock()
        mock_exchange = AsyncMock()

        mock_connect.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel
        mock_channel.declare_exchange.return_value = mock_exchange

        pool = MessageBrokerPool("amqp://localhost/", pool_size=2)
        await pool.initialize()
        await pool.shutdown()

        assert len(pool.brokers) == 0


class TestBrokerHelperMethods:
    """Test helper methods in MessageBroker."""

    def test_priority_to_int_all_levels(self, broker):
        """Test priority enum to integer conversion."""
        assert broker._priority_to_int(TaskPriority.LOW) == 1
        assert broker._priority_to_int(TaskPriority.MEDIUM) == 5
        assert broker._priority_to_int(TaskPriority.HIGH) == 8
        assert broker._priority_to_int(TaskPriority.CRITICAL) == 10
