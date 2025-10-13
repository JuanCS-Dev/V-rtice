"""
RabbitMQ publishers for Adaptive Immune System.

Provides type-safe message publishing for APVs, remedies, and wargame results.
"""

import json
import logging
from typing import Union

from .client import RabbitMQClient
from ..models.apv import APVDispatchMessage, APVStatusUpdate
from ..models.wargame import WargameReportMessage

logger = logging.getLogger(__name__)


class APVPublisher:
    """Publish APV dispatch messages (Oráculo → Eureka)."""

    def __init__(self, client: RabbitMQClient):
        """Initialize APV publisher."""
        self.client = client
        self.routing_key_prefix = "oraculo.apv"

    async def dispatch_apv(self, apv_message: APVDispatchMessage) -> None:
        """
        Dispatch APV to Eureka for vulnerability confirmation.

        Args:
            apv_message: APV dispatch message

        Raises:
            RuntimeError: If publish fails
        """
        try:
            # Determine routing key based on priority
            routing_key = f"{self.routing_key_prefix}.priority.{apv_message.priority}"
            if apv_message.priority <= 3:
                routing_key = f"{self.routing_key_prefix}.critical"

            # Serialize message
            message_body = apv_message.model_dump_json()

            # Publish with priority
            await self.client.publish(
                routing_key=routing_key,
                message_body=message_body,
                priority=11 - apv_message.priority,  # Invert priority (1=highest)
            )

            logger.info(
                f"✅ APV dispatched: {apv_message.apv_code} "
                f"(priority={apv_message.priority}, cve={apv_message.cve_id})"
            )

        except Exception as e:
            logger.error(f"Failed to dispatch APV {apv_message.apv_code}: {e}")
            raise


class RemedyStatusPublisher:
    """Publish remedy status updates (Eureka → Oráculo)."""

    def __init__(self, client: RabbitMQClient):
        """Initialize remedy status publisher."""
        self.client = client
        self.routing_key = "eureka.remedy.status"

    async def publish_status(self, status_update: APVStatusUpdate) -> None:
        """
        Publish APV status update back to Oráculo.

        Args:
            status_update: Status update message
        """
        try:
            message_body = status_update.model_dump_json()

            await self.client.publish(
                routing_key=self.routing_key,
                message_body=message_body,
                priority=5,
            )

            logger.info(
                f"✅ Status update published: {status_update.apv_code} → {status_update.status}"
            )

        except Exception as e:
            logger.error(f"Failed to publish status update: {e}")
            raise


class WargameReportPublisher:
    """Publish wargame reports (GitHub Actions → Eureka)."""

    def __init__(self, client: RabbitMQClient):
        """Initialize wargame report publisher."""
        self.client = client
        self.routing_key = "wargaming.results"

    async def publish_report(self, report: WargameReportMessage) -> None:
        """
        Publish wargaming validation report.

        Args:
            report: Wargame report message
        """
        try:
            message_body = report.model_dump_json()

            # Priority based on verdict
            priority = 8 if report.verdict == "success" else 5

            await self.client.publish(
                routing_key=f"{self.routing_key}.{report.verdict}",
                message_body=message_body,
                priority=priority,
            )

            logger.info(
                f"✅ Wargame report published: {report.run_code} → {report.verdict}"
            )

        except Exception as e:
            logger.error(f"Failed to publish wargame report: {e}")
            raise
