"""
Callback Client - Status updates back to Oráculo.

Sends APV status updates through RabbitMQ:
- Confirmation results
- Remedy generation status
- PR creation events
- Validation results

Integrates with Oráculo's state machine.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

import aio_pika
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class APVStatusUpdate(BaseModel):
    """
    APV status update message.

    Mirrors the model from oraculo/models.py for consistency.
    """

    apv_id: str
    status: str  # "confirmed", "false_positive", "remedy_generated", "pr_created", etc.
    timestamp: datetime
    metadata: Dict[str, Any]


class CallbackClient:
    """
    RabbitMQ client for sending status callbacks to Oráculo.

    Features:
    - Async message publishing
    - Automatic reconnection
    - Message durability
    - Error handling with retries
    - Dead letter queue support
    """

    def __init__(
        self,
        rabbitmq_url: str,
        exchange_name: str = "eureka.status",
        routing_key: str = "apv.status.update",
    ):
        """
        Initialize callback client.

        Args:
            rabbitmq_url: RabbitMQ connection URL (amqp://user:pass@host:port/vhost)
            exchange_name: Exchange for status updates
            routing_key: Routing key for messages
        """
        self.rabbitmq_url = rabbitmq_url
        self.exchange_name = exchange_name
        self.routing_key = routing_key

        self.connection: Optional[aio_pika.abc.AbstractRobustConnection] = None
        self.channel: Optional[aio_pika.abc.AbstractChannel] = None
        self.exchange: Optional[aio_pika.abc.AbstractExchange] = None

        logger.info(
            f"CallbackClient initialized: exchange={exchange_name}, routing_key={routing_key}"
        )

    async def connect(self) -> None:
        """
        Connect to RabbitMQ and declare exchange.

        Raises:
            RuntimeError: If connection fails
        """
        try:
            # Create robust connection (auto-reconnect)
            self.connection = await aio_pika.connect_robust(
                self.rabbitmq_url,
                timeout=30,
            )

            # Create channel
            self.channel = await self.connection.channel()

            # Set QoS (prefetch)
            await self.channel.set_qos(prefetch_count=10)

            # Declare exchange (topic for routing)
            self.exchange = await self.channel.declare_exchange(
                self.exchange_name,
                aio_pika.ExchangeType.TOPIC,
                durable=True,
            )

            logger.info(f"✅ Connected to RabbitMQ: {self.exchange_name}")

        except Exception as e:
            logger.error(f"❌ Failed to connect to RabbitMQ: {e}")
            raise RuntimeError(f"RabbitMQ connection failed: {e}")

    async def disconnect(self) -> None:
        """Disconnect from RabbitMQ."""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            logger.info("✅ Disconnected from RabbitMQ")

    async def send_status_update(
        self,
        apv_id: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Send APV status update to Oráculo.

        Args:
            apv_id: APV identifier
            status: New status (e.g., "confirmed", "pr_created")
            metadata: Additional context

        Raises:
            RuntimeError: If send fails after retries
        """
        if not self.connection or self.connection.is_closed:
            await self.connect()

        update = APVStatusUpdate(
            apv_id=apv_id,
            status=status,
            timestamp=datetime.utcnow(),
            metadata=metadata or {},
        )

        # Serialize to JSON
        message_body = update.model_dump_json().encode()

        # Create message with properties
        message = aio_pika.Message(
            body=message_body,
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,  # Survive broker restart
            content_type="application/json",
            content_encoding="utf-8",
            timestamp=datetime.utcnow(),
            message_id=f"{apv_id}-{status}-{int(datetime.utcnow().timestamp())}",
            app_id="eureka",
        )

        # Retry logic
        max_retries = 3
        retry_delay = 2.0

        for attempt in range(1, max_retries + 1):
            try:
                await self.exchange.publish(
                    message,
                    routing_key=self.routing_key,
                )

                logger.info(
                    f"✅ Sent status update: apv_id={apv_id}, status={status}"
                )
                return

            except Exception as e:
                logger.warning(
                    f"⚠️ Failed to send status update (attempt {attempt}/{max_retries}): {e}"
                )

                if attempt < max_retries:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(
                        f"❌ Failed to send status update after {max_retries} attempts"
                    )
                    raise RuntimeError(f"Failed to send status update: {e}")

    async def send_confirmation_result(
        self,
        apv_id: str,
        confirmed: bool,
        confidence: float,
        static_confidence: float,
        dynamic_confidence: float,
        false_positive_probability: float,
        analysis_details: Dict[str, Any],
    ) -> None:
        """
        Send vulnerability confirmation result.

        Args:
            apv_id: APV identifier
            confirmed: Whether vulnerability is confirmed
            confidence: Final confidence score (0-1)
            static_confidence: Static analysis confidence
            dynamic_confidence: Dynamic analysis confidence
            false_positive_probability: False positive probability
            analysis_details: Additional analysis data
        """
        status = "confirmed" if confirmed else "false_positive"

        metadata = {
            "confidence": confidence,
            "static_confidence": static_confidence,
            "dynamic_confidence": dynamic_confidence,
            "false_positive_probability": false_positive_probability,
            "analysis_details": analysis_details,
        }

        await self.send_status_update(apv_id, status, metadata)

    async def send_remedy_generated(
        self,
        apv_id: str,
        patch_strategy: str,
        patch_description: str,
        confidence: float,
        risk_level: str,
        file_changes: Dict[str, str],
    ) -> None:
        """
        Send remedy generation success.

        Args:
            apv_id: APV identifier
            patch_strategy: Strategy used (version_bump, code_rewrite, etc.)
            patch_description: Human-readable description
            confidence: Patch confidence (0-1)
            risk_level: Risk level (low, medium, high)
            file_changes: Files modified
        """
        metadata = {
            "patch_strategy": patch_strategy,
            "patch_description": patch_description,
            "confidence": confidence,
            "risk_level": risk_level,
            "file_count": len(file_changes),
            "files": list(file_changes.keys()),
        }

        await self.send_status_update(apv_id, "remedy_generated", metadata)

    async def send_remedy_failed(
        self,
        apv_id: str,
        error_message: str,
        attempted_strategies: list[str],
    ) -> None:
        """
        Send remedy generation failure.

        Args:
            apv_id: APV identifier
            error_message: Error description
            attempted_strategies: Strategies that were tried
        """
        metadata = {
            "error": error_message,
            "attempted_strategies": attempted_strategies,
        }

        await self.send_status_update(apv_id, "remedy_failed", metadata)

    async def send_pr_created(
        self,
        apv_id: str,
        pr_number: int,
        pr_url: str,
        branch_name: str,
        commit_sha: str,
    ) -> None:
        """
        Send PR creation success.

        Args:
            apv_id: APV identifier
            pr_number: GitHub PR number
            pr_url: PR URL
            branch_name: Branch name
            commit_sha: Commit SHA
        """
        metadata = {
            "pr_number": pr_number,
            "pr_url": pr_url,
            "branch_name": branch_name,
            "commit_sha": commit_sha,
        }

        await self.send_status_update(apv_id, "pr_created", metadata)

    async def send_pr_failed(
        self,
        apv_id: str,
        error_message: str,
    ) -> None:
        """
        Send PR creation failure.

        Args:
            apv_id: APV identifier
            error_message: Error description
        """
        metadata = {
            "error": error_message,
        }

        await self.send_status_update(apv_id, "pr_failed", metadata)

    async def send_validation_result(
        self,
        apv_id: str,
        passed: bool,
        confidence: float,
        checks_passed: int,
        checks_total: int,
        validation_details: Dict[str, Any],
    ) -> None:
        """
        Send patch validation result.

        Args:
            apv_id: APV identifier
            passed: Whether validation passed
            confidence: Validation confidence (0-1)
            checks_passed: Number of checks passed
            checks_total: Total number of checks
            validation_details: Detailed results
        """
        status = "validation_passed" if passed else "validation_failed"

        metadata = {
            "confidence": confidence,
            "checks_passed": checks_passed,
            "checks_total": checks_total,
            "validation_details": validation_details,
        }

        await self.send_status_update(apv_id, status, metadata)

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
