"""
RabbitMQ client for Adaptive Immune System.

Provides connection management, channel handling, and queue declarations.
"""

import asyncio
import logging
from typing import Callable, Optional

import aio_pika
from aio_pika import Channel, ExchangeType, Message, connect_robust
from aio_pika.abc import AbstractRobustConnection

logger = logging.getLogger(__name__)


class RabbitMQClient:
    """
    RabbitMQ client with automatic reconnection and queue management.

    Manages connections, channels, and queue declarations for
    Oráculo ↔ Eureka ↔ Wargaming communication.
    """

    # Queue names
    QUEUE_APV_DISPATCH = "oraculo.apv.dispatch"
    QUEUE_REMEDY_STATUS = "eureka.remedy.status"
    QUEUE_WARGAME_RESULTS = "wargaming.results"
    QUEUE_HITL_NOTIFICATIONS = "hitl.notifications"
    QUEUE_HITL_DECISIONS = "hitl.decisions"

    # Dead-letter queues
    DLQ_APV_DISPATCH = "oraculo.apv.dispatch.dlq"
    DLQ_REMEDY_STATUS = "eureka.remedy.status.dlq"
    DLQ_WARGAME_RESULTS = "wargaming.results.dlq"
    DLQ_HITL_NOTIFICATIONS = "hitl.notifications.dlq"
    DLQ_HITL_DECISIONS = "hitl.decisions.dlq"

    # Exchange
    EXCHANGE_NAME = "adaptive_immune_system"

    def __init__(
        self,
        rabbitmq_url: str = "amqp://guest:guest@localhost:5672/",
        prefetch_count: int = 10,
    ):
        """
        Initialize RabbitMQ client.

        Args:
            rabbitmq_url: RabbitMQ connection URL
            prefetch_count: Number of messages to prefetch
        """
        self.rabbitmq_url = rabbitmq_url
        self.prefetch_count = prefetch_count

        self.connection: Optional[AbstractRobustConnection] = None
        self.channel: Optional[Channel] = None

        self._is_connected = False
        self._reconnect_task: Optional[asyncio.Task] = None

        logger.info(f"RabbitMQClient initialized: prefetch_count={prefetch_count}")

    async def connect(self) -> None:
        """
        Connect to RabbitMQ and declare queues.

        Raises:
            ConnectionError: If connection fails
        """
        try:
            logger.info(f"Connecting to RabbitMQ: {self.rabbitmq_url}")

            self.connection = await connect_robust(
                self.rabbitmq_url,
                timeout=30,
                reconnect_interval=5,
            )

            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=self.prefetch_count)

            # Declare exchange
            exchange = await self.channel.declare_exchange(
                self.EXCHANGE_NAME,
                ExchangeType.TOPIC,
                durable=True,
            )

            # Declare queues with DLQ
            await self._declare_queues()

            self._is_connected = True
            logger.info("✅ RabbitMQ connected successfully")

        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise ConnectionError(f"RabbitMQ connection failed: {e}")

    async def _declare_queues(self) -> None:
        """Declare all queues with dead-letter handling."""
        queues_config = [
            (
                self.QUEUE_APV_DISPATCH,
                self.DLQ_APV_DISPATCH,
                "oraculo.apv.#",
            ),
            (
                self.QUEUE_REMEDY_STATUS,
                self.DLQ_REMEDY_STATUS,
                "eureka.remedy.#",
            ),
            (
                self.QUEUE_WARGAME_RESULTS,
                self.DLQ_WARGAME_RESULTS,
                "wargaming.results.#",
            ),
            (
                self.QUEUE_HITL_NOTIFICATIONS,
                self.DLQ_HITL_NOTIFICATIONS,
                "hitl.notifications.#",
            ),
            (
                self.QUEUE_HITL_DECISIONS,
                self.DLQ_HITL_DECISIONS,
                "hitl.decisions.#",
            ),
        ]

        for queue_name, dlq_name, routing_key in queues_config:
            # Declare DLQ first
            await self.channel.declare_queue(
                dlq_name,
                durable=True,
                arguments={
                    "x-message-ttl": 86400000,  # 24 hours
                },
            )

            # Declare main queue with DLQ
            queue = await self.channel.declare_queue(
                queue_name,
                durable=True,
                arguments={
                    "x-dead-letter-exchange": "",
                    "x-dead-letter-routing-key": dlq_name,
                    "x-max-retries": 3,
                },
            )

            # Bind to exchange
            await queue.bind(self.EXCHANGE_NAME, routing_key=routing_key)

            logger.info(f"✅ Queue declared: {queue_name} → {dlq_name}")

    async def publish(
        self,
        routing_key: str,
        message_body: str,
        priority: int = 5,
    ) -> None:
        """
        Publish message to exchange.

        Args:
            routing_key: Routing key for message
            message_body: JSON-serialized message
            priority: Message priority (0-10)

        Raises:
            RuntimeError: If not connected
        """
        if not self._is_connected or not self.channel:
            raise RuntimeError("RabbitMQ not connected. Call connect() first.")

        try:
            message = Message(
                body=message_body.encode(),
                priority=priority,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            )

            exchange = await self.channel.get_exchange(self.EXCHANGE_NAME)
            await exchange.publish(message, routing_key=routing_key)

            logger.debug(f"Published message: routing_key={routing_key}")

        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            raise

    async def consume(
        self,
        queue_name: str,
        callback: Callable,
        auto_ack: bool = False,
    ) -> None:
        """
        Start consuming messages from queue.

        Args:
            queue_name: Queue to consume from
            callback: Async callback function(message)
            auto_ack: Auto-acknowledge messages

        Raises:
            RuntimeError: If not connected
        """
        if not self._is_connected or not self.channel:
            raise RuntimeError("RabbitMQ not connected. Call connect() first.")

        try:
            queue = await self.channel.get_queue(queue_name)

            async def message_handler(message: aio_pika.IncomingMessage):
                """Handle incoming message with error handling."""
                async with message.process(ignore_processed=auto_ack):
                    try:
                        await callback(message)
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        # Message will be requeued or sent to DLQ
                        raise

            await queue.consume(message_handler)
            logger.info(f"✅ Started consuming: {queue_name}")

        except Exception as e:
            logger.error(f"Failed to start consumer: {e}")
            raise

    async def close(self) -> None:
        """Close RabbitMQ connection."""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            self._is_connected = False
            logger.info("RabbitMQ connection closed")

    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self._is_connected and self.connection and not self.connection.is_closed

    async def health_check(self) -> bool:
        """
        Check RabbitMQ connectivity.

        Returns:
            True if connected and healthy, False otherwise
        """
        try:
            if not self.is_connected():
                return False

            # Try to declare a temporary queue
            await self.channel.declare_queue(
                "health_check",
                auto_delete=True,
                exclusive=True,
            )
            return True

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False


# Global RabbitMQ client instance
_rabbitmq_client: Optional[RabbitMQClient] = None


def initialize_rabbitmq_client(rabbitmq_url: str, **kwargs) -> RabbitMQClient:
    """
    Initialize global RabbitMQ client.

    Args:
        rabbitmq_url: RabbitMQ connection URL
        **kwargs: Additional arguments for RabbitMQClient

    Returns:
        Initialized RabbitMQClient instance
    """
    global _rabbitmq_client
    _rabbitmq_client = RabbitMQClient(rabbitmq_url, **kwargs)
    logger.info("Global RabbitMQ client initialized")
    return _rabbitmq_client


def get_rabbitmq_client() -> RabbitMQClient:
    """
    Get global RabbitMQ client instance.

    Returns:
        RabbitMQClient instance

    Raises:
        RuntimeError: If client not initialized
    """
    if _rabbitmq_client is None:
        raise RuntimeError(
            "RabbitMQ client not initialized. "
            "Call initialize_rabbitmq_client() first."
        )
    return _rabbitmq_client
