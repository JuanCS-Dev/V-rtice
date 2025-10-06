"""Event Bridge - Real-time Event Streaming - PRODUCTION-READY

Bridge between Core System events (Kafka/Redis) and WebSocket clients.

This module provides:
- WebSocket connection management
- Kafka cytokine streaming (Kafka → WebSocket)
- Redis hormone streaming (Redis → WebSocket)
- Agent state change streaming
- Event filtering and routing

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Set, Dict, Any, Optional, List
from collections import defaultdict

from fastapi import WebSocket
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaConnectionError
import redis.asyncio as aioredis

from .core_manager import CoreManager

logger = logging.getLogger(__name__)


class EventBridgeError(Exception):
    """Base exception for EventBridge errors"""
    pass


class EventBridge:
    """
    Event Bridge - Real-time event streaming.

    Responsibilities:
    - Manage WebSocket connections
    - Stream Kafka events (cytokines) to WebSocket clients
    - Stream Redis events (hormones) to WebSocket clients
    - Filter and route events based on client subscriptions
    - Graceful degradation when Kafka/Redis unavailable

    Usage:
        bridge = EventBridge()
        await bridge.start()

        # WebSocket endpoint
        @app.websocket("/ws/events")
        async def websocket_endpoint(websocket: WebSocket):
            await bridge.connect(websocket)
            try:
                while True:
                    data = await websocket.receive_text()
                    # Handle client messages (subscriptions, etc.)
            except:
                await bridge.disconnect(websocket)
    """

    def __init__(
        self,
        kafka_bootstrap: str = "localhost:9092",
        redis_url: str = "redis://localhost:6379",
    ):
        """
        Initialize Event Bridge.

        Args:
            kafka_bootstrap: Kafka broker address
            redis_url: Redis connection URL
        """
        self.kafka_bootstrap = kafka_bootstrap
        self.redis_url = redis_url

        # WebSocket connections
        self._connections: Set[WebSocket] = set()
        self._connection_subscriptions: Dict[WebSocket, Set[str]] = defaultdict(set)

        # Kafka/Redis consumers
        self._kafka_consumer: Optional[AIOKafkaConsumer] = None
        self._redis_client: Optional[aioredis.Redis] = None
        self._redis_pubsub: Optional[aioredis.client.PubSub] = None

        # Background tasks
        self._tasks: List[asyncio.Task] = []
        self._running = False

        # Metrics
        self.total_events_streamed: int = 0
        self.total_connections: int = 0
        self.peak_connections: int = 0

        logger.info("EventBridge initialized")

    # ==================== LIFECYCLE ====================

    async def start(self) -> None:
        """
        Start Event Bridge.

        Starts background tasks for:
        - Kafka cytokine streaming
        - Redis hormone streaming
        """
        if self._running:
            logger.warning("EventBridge already running")
            return

        logger.info("Starting EventBridge...")

        self._running = True

        # Start Kafka consumer
        self._tasks.append(
            asyncio.create_task(self._stream_kafka_events(), name="kafka_stream")
        )

        # Start Redis consumer
        self._tasks.append(
            asyncio.create_task(self._stream_redis_events(), name="redis_stream")
        )

        logger.info("✓ EventBridge started (2 background tasks)")

    async def stop(self) -> None:
        """
        Stop Event Bridge.

        Stops all background tasks and closes connections.
        """
        if not self._running:
            logger.warning("EventBridge not running")
            return

        logger.info("Stopping EventBridge...")

        self._running = False

        # Cancel background tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()

        # Wait for tasks to finish
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

        # Close Kafka consumer
        if self._kafka_consumer:
            await self._kafka_consumer.stop()
            logger.info("✓ Kafka consumer stopped")

        # Close Redis client
        if self._redis_pubsub:
            await self._redis_pubsub.unsubscribe()
            await self._redis_pubsub.close()
        if self._redis_client:
            await self._redis_client.close()
            logger.info("✓ Redis client stopped")

        # Close all WebSocket connections
        for ws in list(self._connections):
            await self.disconnect(ws)

        logger.info("✓ EventBridge stopped")

    # ==================== CONNECTION MANAGEMENT ====================

    async def connect(
        self,
        websocket: WebSocket,
        subscriptions: Optional[Set[str]] = None,
    ) -> None:
        """
        Accept WebSocket connection.

        Args:
            websocket: WebSocket connection
            subscriptions: Set of event types to subscribe to (None = all)
        """
        await websocket.accept()
        self._connections.add(websocket)

        # Set subscriptions (None = subscribe to all)
        if subscriptions:
            self._connection_subscriptions[websocket] = subscriptions
        else:
            self._connection_subscriptions[websocket] = {
                "cytokine",
                "hormone",
                "agent_state",
                "threat_detection",
                "clone_creation",
                "homeostatic_state",
                "system_health",
            }

        # Update metrics
        self.total_connections += 1
        self.peak_connections = max(self.peak_connections, len(self._connections))

        logger.info(
            f"WebSocket connected (total={len(self._connections)}, "
            f"subscriptions={self._connection_subscriptions[websocket]})"
        )

        # Send welcome message
        await self._send_to_websocket(
            websocket,
            {
                "event": "connected",
                "data": {
                    "message": "Connected to Active Immune Core Event Stream",
                    "subscriptions": list(self._connection_subscriptions[websocket]),
                    "timestamp": datetime.utcnow().isoformat(),
                },
            },
        )

    async def disconnect(self, websocket: WebSocket) -> None:
        """
        Remove WebSocket connection.

        Args:
            websocket: WebSocket connection
        """
        self._connections.discard(websocket)
        self._connection_subscriptions.pop(websocket, None)

        try:
            await websocket.close()
        except:
            pass

        logger.info(f"WebSocket disconnected (total={len(self._connections)})")

    async def update_subscriptions(
        self,
        websocket: WebSocket,
        subscriptions: Set[str],
    ) -> None:
        """
        Update client subscriptions.

        Args:
            websocket: WebSocket connection
            subscriptions: New set of event types
        """
        if websocket in self._connections:
            self._connection_subscriptions[websocket] = subscriptions
            logger.debug(f"Updated subscriptions for client: {subscriptions}")

    # ==================== EVENT STREAMING ====================

    async def _stream_kafka_events(self) -> None:
        """
        Stream Kafka cytokine events to WebSocket clients.

        Consumes from all cytokine topics and broadcasts to subscribed clients.
        """
        try:
            # Create Kafka consumer
            self._kafka_consumer = AIOKafkaConsumer(
                "immunis.cytokines.IL1",
                "immunis.cytokines.IL6",
                "immunis.cytokines.IL8",
                "immunis.cytokines.IL10",
                "immunis.cytokines.IL12",
                "immunis.cytokines.TNF",
                "immunis.cytokines.IFNgamma",
                "immunis.cytokines.TGFbeta",
                bootstrap_servers=self.kafka_bootstrap,
                group_id="event_bridge_consumer",
                auto_offset_reset="latest",
            )

            await self._kafka_consumer.start()
            logger.info("✓ Kafka consumer started for event streaming")

            # Consume events
            async for msg in self._kafka_consumer:
                if not self._running:
                    break

                try:
                    # Parse cytokine event
                    cytokine_data = json.loads(msg.value.decode())

                    # Create WebSocket event
                    event = {
                        "event": "cytokine",
                        "data": {
                            "cytokine_type": msg.topic.split(".")[-1],
                            "source_agent": cytokine_data.get("source_agent", "unknown"),
                            "target_area": cytokine_data.get("target_area"),
                            "concentration": cytokine_data.get("concentration", 1.0),
                            "message": cytokine_data,
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                    }

                    # Broadcast to subscribed clients
                    await self._broadcast_event(event)

                except Exception as e:
                    logger.error(f"Error processing Kafka event: {e}")

        except KafkaConnectionError:
            logger.warning(
                "Kafka unavailable for event streaming (running in degraded mode)"
            )
        except Exception as e:
            logger.error(f"Kafka streaming error: {e}", exc_info=True)

    async def _stream_redis_events(self) -> None:
        """
        Stream Redis hormone events to WebSocket clients.

        Subscribes to hormone channels and broadcasts to subscribed clients.
        """
        try:
            # Create Redis client
            self._redis_client = aioredis.from_url(
                self.redis_url,
                decode_responses=True,
            )

            # Subscribe to hormone channels
            self._redis_pubsub = self._redis_client.pubsub()
            await self._redis_pubsub.subscribe(
                "hormonio:cortisol",
                "hormonio:adrenalina",
                "hormonio:melatonina",
            )

            logger.info("✓ Redis pubsub started for event streaming")

            # Consume events
            async for msg in self._redis_pubsub.listen():
                if not self._running:
                    break

                if msg["type"] != "message":
                    continue

                try:
                    # Parse hormone event
                    hormone_data = json.loads(msg["data"])

                    # Create WebSocket event
                    event = {
                        "event": "hormone",
                        "data": {
                            "hormone_type": msg["channel"].split(":")[-1],
                            "level": hormone_data.get("level", 1.0),
                            "source": hormone_data.get("source", "unknown"),
                            "message": hormone_data,
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                    }

                    # Broadcast to subscribed clients
                    await self._broadcast_event(event)

                except Exception as e:
                    logger.error(f"Error processing Redis event: {e}")

        except Exception as e:
            logger.warning(
                f"Redis unavailable for event streaming (running in degraded mode): {e}"
            )

    async def _broadcast_event(self, event: Dict[str, Any]) -> None:
        """
        Broadcast event to all subscribed WebSocket clients.

        Args:
            event: Event dictionary with 'event' and 'data' keys
        """
        event_type = event.get("event", "unknown")

        # Find subscribed clients
        subscribers = [
            ws
            for ws in self._connections
            if event_type in self._connection_subscriptions.get(ws, set())
        ]

        if not subscribers:
            return

        # Send to all subscribers concurrently
        send_tasks = [self._send_to_websocket(ws, event) for ws in subscribers]
        await asyncio.gather(*send_tasks, return_exceptions=True)

        self.total_events_streamed += len(subscribers)

    async def _send_to_websocket(
        self,
        websocket: WebSocket,
        event: Dict[str, Any],
    ) -> None:
        """
        Send event to WebSocket client.

        Args:
            websocket: WebSocket connection
            event: Event dictionary
        """
        try:
            await websocket.send_json(event)
        except Exception as e:
            logger.error(f"Failed to send event to WebSocket: {e}")
            # Connection might be broken, remove it
            await self.disconnect(websocket)

    # ==================== MANUAL EVENT EMISSION ====================

    async def emit_agent_state_event(
        self,
        agent_id: str,
        agent_type: str,
        old_status: Optional[str],
        new_status: str,
        area_patrulha: str,
        message: Dict[str, Any],
    ) -> None:
        """
        Manually emit agent state change event.

        Args:
            agent_id: Agent identifier
            agent_type: Agent type
            old_status: Previous status
            new_status: New status
            area_patrulha: Patrol area
            message: Additional details
        """
        event = {
            "event": "agent_state",
            "data": {
                "agent_id": agent_id,
                "agent_type": agent_type,
                "old_status": old_status,
                "new_status": new_status,
                "area_patrulha": area_patrulha,
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
            },
        }

        await self._broadcast_event(event)

    async def emit_threat_detection(
        self,
        threat_id: str,
        threat_type: str,
        severity: str,
        detector_agent: str,
        target: str,
        confidence: float,
        details: Dict[str, Any],
    ) -> None:
        """
        Manually emit threat detection event.
        """
        event = {
            "event": "threat_detection",
            "data": {
                "threat_id": threat_id,
                "threat_type": threat_type,
                "severity": severity,
                "detector_agent": detector_agent,
                "target": target,
                "confidence": confidence,
                "details": details,
                "timestamp": datetime.utcnow().isoformat(),
            },
        }

        await self._broadcast_event(event)

    # ==================== METRICS ====================

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get Event Bridge metrics.

        Returns:
            Dict with streaming metrics
        """
        return {
            "running": self._running,
            "active_connections": len(self._connections),
            "total_connections": self.total_connections,
            "peak_connections": self.peak_connections,
            "total_events_streamed": self.total_events_streamed,
            "kafka_connected": self._kafka_consumer is not None,
            "redis_connected": self._redis_client is not None,
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"EventBridge(running={self._running}, "
            f"connections={len(self._connections)}, "
            f"events_streamed={self.total_events_streamed})"
        )
