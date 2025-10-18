"""
RabbitMQ consumers for Adaptive Immune System.

Provides type-safe message consumption for APVs, remedies, wargame results,
and HITL notifications/decisions.
"""

import json
import logging
from typing import Callable

import aio_pika

from .client import RabbitMQClient
from models.apv import APVDispatchMessage, APVStatusUpdate
from models.wargame import WargameReportMessage
from models.hitl import HITLNotificationMessage, HITLDecisionMessage, HITLStatusUpdate

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


class HITLNotificationConsumer:
    """Consume HITL notification messages (HITL Console service)."""

    def __init__(
        self, client: RabbitMQClient, callback: Callable[[HITLNotificationMessage], None]
    ):
        """
        Initialize HITL notification consumer.

        Consumes notifications of new APVs requiring human review.
        Used by HITL Console to display pending reviews.

        Args:
            client: RabbitMQ client
            callback: Async callback function to process notification
        """
        self.client = client
        self.callback = callback
        self.queue_name = RabbitMQClient.QUEUE_HITL_NOTIFICATIONS

    async def start(self) -> None:
        """Start consuming HITL notifications."""

        async def message_handler(message: aio_pika.IncomingMessage):
            """Handle incoming HITL notification."""
            try:
                # Parse message
                data = json.loads(message.body.decode())
                notification = HITLNotificationMessage(**data)

                logger.info(
                    f"📨 Received HITL notification: {notification.apv_code} "
                    f"(severity={notification.severity}, verdict={notification.wargame_verdict})"
                )

                # Process notification
                await self.callback(notification)

                logger.info(
                    f"✅ Processed HITL notification: {notification.apv_code} "
                    f"(msg_id={notification.message_id})"
                )

            except Exception as e:
                logger.error(f"Error processing HITL notification: {e}")
                raise  # Will be sent to DLQ after retries

        await self.client.consume(self.queue_name, message_handler, auto_ack=False)
        logger.info(f"✅ HITLNotificationConsumer started: {self.queue_name}")


class HITLDecisionConsumer:
    """Consume HITL decision messages (System/Eureka service)."""

    def __init__(self, client: RabbitMQClient, callback: Callable[[HITLDecisionMessage], None]):
        """
        Initialize HITL decision consumer.

        Consumes human decisions on APVs from HITL Console.
        Used by system to execute decisions (merge PR, close PR, etc).

        Args:
            client: RabbitMQ client
            callback: Async callback function to process decision
        """
        self.client = client
        self.callback = callback
        self.queue_name = RabbitMQClient.QUEUE_HITL_DECISIONS

    async def start(self) -> None:
        """Start consuming HITL decisions."""

        async def message_handler(message: aio_pika.IncomingMessage):
            """Handle incoming HITL decision."""
            try:
                # Parse message
                data = json.loads(message.body.decode())
                decision = HITLDecisionMessage(**data)

                logger.info(
                    f"📨 Received HITL decision: {decision.apv_code} → {decision.decision} "
                    f"(action={decision.action_type}, reviewer={decision.reviewer_name})"
                )

                # Process decision
                await self.callback(decision)

                logger.info(
                    f"✅ Processed HITL decision: {decision.apv_code} → {decision.decision} "
                    f"(msg_id={decision.message_id})"
                )

            except Exception as e:
                logger.error(f"Error processing HITL decision: {e}")
                raise  # Will be sent to DLQ after retries

        await self.client.consume(self.queue_name, message_handler, auto_ack=False)
        logger.info(f"✅ HITLDecisionConsumer started: {self.queue_name}")


class HITLStatusConsumer:
    """Consume HITL status updates (Monitoring/Alerting services)."""

    def __init__(self, client: RabbitMQClient, callback: Callable[[HITLStatusUpdate], None]):
        """
        Initialize HITL status consumer.

        Consumes periodic HITL system health updates.
        Used by monitoring/alerting systems to track HITL health.

        Args:
            client: RabbitMQ client
            callback: Async callback function to process status update
        """
        self.client = client
        self.callback = callback
        self.queue_name = RabbitMQClient.QUEUE_HITL_NOTIFICATIONS  # Reuse same queue

    async def start(self) -> None:
        """Start consuming HITL status updates."""

        async def message_handler(message: aio_pika.IncomingMessage):
            """Handle incoming HITL status update."""
            try:
                # Parse message
                data = json.loads(message.body.decode())

                # Check message type
                if data.get("message_type") != "hitl_status":
                    # Not a status message, skip
                    return

                status_update = HITLStatusUpdate(**data)

                logger.info(
                    f"📨 Received HITL status: pending={status_update.pending_reviews_count}, "
                    f"alert_level={status_update.alert_level}"
                )

                # Process status update
                await self.callback(status_update)

                logger.debug(f"✅ Processed HITL status (msg_id={status_update.message_id})")

            except Exception as e:
                logger.error(f"Error processing HITL status update: {e}")
                raise  # Will be sent to DLQ after retries

        await self.client.consume(self.queue_name, message_handler, auto_ack=False)
        logger.info(f"✅ HITLStatusConsumer started: {self.queue_name}")
