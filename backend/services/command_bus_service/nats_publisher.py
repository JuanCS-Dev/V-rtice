"""NATS JetStream publisher for C2L commands."""

import json
from typing import Optional

import structlog
from nats.aio.client import Client as NATSClient
from nats.js import JetStreamContext

from config import settings
from models import C2LCommand, CommandReceipt, CommandStatus

logger = structlog.get_logger()


class NATSPublisher:
    """Publisher for C2L commands and confirmations."""

    def __init__(self) -> None:
        """Initialize publisher."""
        self.nc: Optional[NATSClient] = None
        self.js: Optional[JetStreamContext] = None

    async def connect(self) -> None:
        """Connect to NATS JetStream."""
        self.nc = NATSClient()
        await self.nc.connect(servers=[settings.nats_url])
        self.js = self.nc.jetstream()
        logger.info("nats_publisher_connected", url=settings.nats_url)

    async def disconnect(self) -> None:
        """Disconnect from NATS."""
        if self.nc:
            await self.nc.close()
            logger.info("nats_publisher_disconnected")

    async def publish_command(self, command: C2LCommand) -> None:
        """Publish command to sovereign.commands.{agent_id}."""
        if not self.js:
            raise RuntimeError("NATS not connected")

        for target_agent_id in command.target_agents:
            subject = f"{settings.nats_subject_commands}.{target_agent_id}"
            payload = command.model_dump_json().encode()

            ack = await self.js.publish(subject, payload)
            logger.info(
                "command_published",
                command_id=str(command.id),
                subject=subject,
                seq=ack.seq,
            )

    async def publish_confirmation(self, receipt: CommandReceipt) -> None:
        """Publish confirmation to sovereign.confirmations.{command_id}."""
        if not self.js:
            raise RuntimeError("NATS not connected")

        subject = f"{settings.nats_subject_confirmations}.{receipt.command_id}"
        payload = receipt.model_dump_json().encode()

        ack = await self.js.publish(subject, payload)
        logger.info(
            "confirmation_published",
            command_id=str(receipt.command_id),
            status=receipt.status,
            seq=ack.seq,
        )
