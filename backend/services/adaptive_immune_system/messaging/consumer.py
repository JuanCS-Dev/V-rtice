"""
RabbitMQ consumers for Adaptive Immune System.

Provides type-safe message consumption for APVs, remedies, and wargame results.
"""

import json
import logging
from typing import Callable

import aio_pika

from .client import RabbitMQClient
from ..models.apv import APVDispatchMessage, APVStatusUpdate
from ..models.wargame import WargameReportMessage

logger = logging.getLogger(__name__)


class APVConsumer:
    """Consume APV dispatch messages (Eureka service)."""

    def __init__(self, client: RabbitMQClient, callback: Callable[[APVDispatchMessage], None]):
        """
        Initialize APV consumer.

        Args:
            client: RabbitMQ client
            callback: Async callback function to process APV
        """
        self.client = client
        self.callback = callback
        self.queue_name = RabbitMQClient.QUEUE_APV_DISPATCH

    async def start(self) -> None:
        """Start consuming APV messages."""

        async def message_handler(message: aio_pika.IncomingMessage):
            """Handle incoming APV message."""
            try:
                # Parse message
                data = json.loads(message.body.decode())
                apv_message = APVDispatchMessage(**data)

                logger.info(f"📨 Received APV: {apv_message.apv_code} (CVE: {apv_message.cve_id})")

                # Process APV
                await self.callback(apv_message)

                logger.info(f"✅ Processed APV: {apv_message.apv_code}")

            except Exception as e:
                logger.error(f"Error processing APV message: {e}")
                raise  # Will be sent to DLQ after retries

        await self.client.consume(self.queue_name, message_handler, auto_ack=False)
        logger.info(f"✅ APVConsumer started: {self.queue_name}")


class RemedyStatusConsumer:
    """Consume remedy status updates (Oráculo service)."""

    def __init__(self, client: RabbitMQClient, callback: Callable[[APVStatusUpdate], None]):
        """
        Initialize remedy status consumer.

        Args:
            client: RabbitMQ client
            callback: Async callback function to process status update
        """
        self.client = client
        self.callback = callback
        self.queue_name = RabbitMQClient.QUEUE_REMEDY_STATUS

    async def start(self) -> None:
        """Start consuming status updates."""

        async def message_handler(message: aio_pika.IncomingMessage):
            """Handle incoming status update message."""
            try:
                data = json.loads(message.body.decode())
                status_update = APVStatusUpdate(**data)

                logger.info(
                    f"📨 Received status update: {status_update.apv_code} → {status_update.status}"
                )

                # Process status update
                await self.callback(status_update)

                logger.info(f"✅ Processed status update: {status_update.apv_code}")

            except Exception as e:
                logger.error(f"Error processing status update: {e}")
                raise

        await self.client.consume(self.queue_name, message_handler, auto_ack=False)
        logger.info(f"✅ RemedyStatusConsumer started: {self.queue_name}")


class WargameReportConsumer:
    """Consume wargame reports (Eureka service)."""

    def __init__(self, client: RabbitMQClient, callback: Callable[[WargameReportMessage], None]):
        """
        Initialize wargame report consumer.

        Args:
            client: RabbitMQ client
            callback: Async callback function to process wargame report
        """
        self.client = client
        self.callback = callback
        self.queue_name = RabbitMQClient.QUEUE_WARGAME_RESULTS

    async def start(self) -> None:
        """Start consuming wargame reports."""

        async def message_handler(message: aio_pika.IncomingMessage):
            """Handle incoming wargame report."""
            try:
                data = json.loads(message.body.decode())
                report = WargameReportMessage(**data)

                logger.info(
                    f"📨 Received wargame report: {report.run_code} → {report.verdict}"
                )

                # Process wargame report
                await self.callback(report)

                logger.info(f"✅ Processed wargame report: {report.run_code}")

            except Exception as e:
                logger.error(f"Error processing wargame report: {e}")
                raise

        await self.client.consume(self.queue_name, message_handler, auto_ack=False)
        logger.info(f"✅ WargameReportConsumer started: {self.queue_name}")
