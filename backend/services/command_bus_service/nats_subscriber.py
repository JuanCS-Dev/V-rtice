"""NATS JetStream subscriber for C2L commands."""

import json

import structlog
from c2l_executor import C2LCommandExecutor
from backend.services.command_bus_service.config import settings
from backend.services.command_bus_service.models import C2LCommand
from nats.aio.client import Client as NATSClient
from nats.js import JetStreamContext
from nats.js.api import AckPolicy, ConsumerConfig

logger = structlog.get_logger()


class NATSSubscriber:
    """Subscriber for C2L commands."""

    def __init__(self, executor: C2LCommandExecutor) -> None:
        """Initialize subscriber."""
        self.nc: NATSClient | None = None
        self.js: JetStreamContext | None = None
        self.executor = executor

    async def connect(self) -> None:
        """Connect to NATS JetStream."""
        self.nc = NATSClient()
        await self.nc.connect(servers=[settings.nats_url])
        self.js = self.nc.jetstream()
        logger.info("nats_subscriber_connected", url=settings.nats_url)

    async def subscribe(self) -> None:
        """Subscribe to sovereign.commands.> wildcard."""
        if not self.js:
            raise RuntimeError("NATS not connected")

        # Durable consumer
        consumer_config = ConsumerConfig(
            durable_name="c2l-executor",
            ack_policy=AckPolicy.EXPLICIT,
            max_deliver=3,
            ack_wait=30,  # 30 seconds to ack
        )

        subscription = await self.js.subscribe(
            subject=f"{settings.nats_subject_commands}.>",
            config=consumer_config,
        )

        logger.info("subscribed", subject=f"{settings.nats_subject_commands}.>")

        async for msg in subscription.messages:
            try:
                command_data = json.loads(msg.data.decode())
                command = C2LCommand(**command_data)

                logger.info(
                    "command_received",
                    command_id=str(command.id),
                    type=command.command_type,
                    targets=command.target_agents,
                )

                # Execute command
                receipt = await self.executor.execute(command)

                # Publish confirmation
                await self.executor.publisher.publish_confirmation(receipt)

                # Ack message
                await msg.ack()

            except Exception as e:
                logger.error(
                    "command_processing_failed",
                    error=str(e),
                    exc_info=True,
                )
                # Nack with delay (retry)
                await msg.nak(delay=5)

    async def disconnect(self) -> None:
        """Disconnect from NATS."""
        if self.nc:
            await self.nc.close()
            logger.info("nats_subscriber_disconnected")
