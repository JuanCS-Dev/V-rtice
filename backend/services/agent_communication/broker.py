"""Message Broker implementation for Agent Communication.

Provides async RabbitMQ abstraction for reliable message passing between agents.
Handles connection management, queue declaration, and message delivery.
"""
import logging
from typing import Callable, Dict, Optional

import aio_pika
from aio_pika import DeliveryMode, ExchangeType, Message
from aio_pika.abc import AbstractChannel, AbstractConnection, AbstractQueue

from .message import ACPMessage, AgentType

logger = logging.getLogger(__name__)


class MessageBroker:
    """RabbitMQ-based message broker for agent communication.

    This class provides a high-level interface for agents to send and receive
    messages through RabbitMQ queues. It handles:
    - Connection pooling and reconnection
    - Queue declaration and binding
    - Message serialization/deserialization
    - Asynchronous message consumption
    - Graceful shutdown

    Architecture:
    - Each agent has a dedicated queue (named by AgentType)
    - Direct exchange for point-to-point messaging
    - Persistent messages for reliability
    - Prefetch count of 1 for load balancing

    Example:
        ```python
        broker = MessageBroker("amqp://guest:guest@localhost/")
        await broker.connect()

        # Send message
        msg = ACPMessage(
            message_type=MessageType.TASK_ASSIGN,
            sender=AgentType.ORCHESTRATOR,
            recipient=AgentType.RECONNAISSANCE,
            payload={"task_type": "port_scan", "target": "10.0.0.1"}
        )
        await broker.send_message(msg)

        # Receive messages
        await broker.consume_messages(
            AgentType.RECONNAISSANCE,
            callback=my_handler_function
        )
        ```
    """

    def __init__(
        self,
        connection_url: str = "amqp://guest:guest@localhost:5672/",
        exchange_name: str = "agent_communication",
    ):
        """Initialize MessageBroker.

        Args:
            connection_url: AMQP connection URL
            exchange_name: RabbitMQ exchange name for agent messages
        """
        self.connection_url = connection_url
        self.exchange_name = exchange_name
        self.connection: Optional[AbstractConnection] = None
        self.channel: Optional[AbstractChannel] = None
        self.exchange: Optional[aio_pika.abc.AbstractExchange] = None
        self.queues: Dict[AgentType, AbstractQueue] = {}
        self._consuming = False

    async def connect(self) -> None:
        """Establish connection to RabbitMQ broker.

        Creates connection, channel, and declares the exchange.

        Raises:
            aio_pika.AMQPException: If connection fails
        """
        logger.info(f"Connecting to RabbitMQ at {self.connection_url}")
        self.connection = await aio_pika.connect_robust(
            self.connection_url,
            heartbeat=60,
            timeout=10,
        )
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=1)

        # Declare exchange
        self.exchange = await self.channel.declare_exchange(
            self.exchange_name,
            ExchangeType.DIRECT,
            durable=True,
        )
        logger.info("Connected to RabbitMQ successfully")

    async def disconnect(self) -> None:
        """Gracefully close connection to RabbitMQ."""
        logger.info("Disconnecting from RabbitMQ")
        self._consuming = False
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
        logger.info("Disconnected from RabbitMQ")

    async def declare_queue(self, agent_type: AgentType) -> AbstractQueue:
        """Declare a queue for a specific agent type.

        Args:
            agent_type: Type of agent (determines queue name)

        Returns:
            Declared queue object

        Raises:
            RuntimeError: If not connected to broker
        """
        if not self.channel:
            raise RuntimeError("Not connected to message broker")

        queue_name = f"agent.{agent_type.value}"
        queue = await self.channel.declare_queue(
            queue_name,
            durable=True,
            arguments={"x-message-ttl": 3600000},  # 1 hour TTL
        )

        # Bind queue to exchange with routing key = queue name
        await queue.bind(self.exchange, routing_key=queue_name)

        self.queues[agent_type] = queue
        logger.info(f"Declared queue: {queue_name}")
        return queue

    async def send_message(self, message: ACPMessage) -> None:
        """Send message to specified recipient agent.

        Args:
            message: ACP message to send

        Raises:
            RuntimeError: If not connected to broker
        """
        if not self.exchange:
            raise RuntimeError("Not connected to message broker")

        routing_key = f"agent.{message.recipient.value}"
        aio_message = Message(
            body=message.to_json().encode(),
            delivery_mode=DeliveryMode.PERSISTENT,
            content_type="application/json",
            message_id=str(message.message_id),
            correlation_id=str(message.correlation_id) if message.correlation_id else None,
            priority=self._priority_to_int(message.priority),
        )

        await self.exchange.publish(
            aio_message,
            routing_key=routing_key,
        )
        logger.debug(
            f"Sent {message.message_type.value} from {message.sender.value} "
            f"to {message.recipient.value}"
        )

    async def consume_messages(
        self,
        agent_type: AgentType,
        callback: Callable[[ACPMessage], None],
    ) -> None:
        """Start consuming messages for a specific agent.

        This is a blocking call that runs until disconnect() is called.

        Args:
            agent_type: Type of agent to consume messages for
            callback: Async function to handle received messages

        Raises:
            RuntimeError: If not connected to broker
        """
        if agent_type not in self.queues:
            await self.declare_queue(agent_type)

        queue = self.queues[agent_type]
        self._consuming = True

        logger.info(f"Starting message consumption for {agent_type.value}")

        async with queue.iterator() as queue_iter:
            async for aio_message in queue_iter:
                if not self._consuming:
                    break

                async with aio_message.process():
                    try:
                        message = ACPMessage.from_json(aio_message.body.decode())
                        logger.debug(
                            f"Received {message.message_type.value} "
                            f"for {agent_type.value}"
                        )
                        await callback(message)
                    except Exception as e:
                        logger.error(f"Error processing message: {e}", exc_info=True)

    @staticmethod
    def _priority_to_int(priority) -> int:
        """Convert TaskPriority enum to int for RabbitMQ."""
        priority_map = {"low": 1, "medium": 5, "high": 8, "critical": 10}
        return priority_map.get(priority.value, 5)


class MessageBrokerPool:
    """Pool of MessageBroker connections for high-throughput scenarios.

    Maintains multiple broker connections to distribute load.
    """

    def __init__(self, connection_url: str, pool_size: int = 5):
        """Initialize broker pool.

        Args:
            connection_url: AMQP connection URL
            pool_size: Number of connections to maintain
        """
        self.connection_url = connection_url
        self.pool_size = pool_size
        self.brokers: list[MessageBroker] = []
        self._current_index = 0

    async def initialize(self) -> None:
        """Create and connect all brokers in pool."""
        for _ in range(self.pool_size):
            broker = MessageBroker(self.connection_url)
            await broker.connect()
            self.brokers.append(broker)
        logger.info(f"Initialized MessageBroker pool with {self.pool_size} connections")

    async def shutdown(self) -> None:
        """Disconnect all brokers in pool."""
        for broker in self.brokers:
            await broker.disconnect()
        self.brokers.clear()

    def get_broker(self) -> MessageBroker:
        """Get next broker from pool (round-robin)."""
        broker = self.brokers[self._current_index]
        self._current_index = (self._current_index + 1) % self.pool_size
        return broker
