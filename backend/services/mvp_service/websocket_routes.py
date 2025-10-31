"""
MVP WebSocket Routes - Real-time System Narratives & Anomalies

Provides WebSocket endpoints for:
- New narrative generation events
- Anomaly detection alerts
- System metrics updates
- System pulse real-time monitoring
- NQS score updates

Author: Vértice Platform Team
License: Proprietary
Governed by: Constituição Vértice v3.0
"""

import logging
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class MVPMessageType(str, Enum):
    """MVP-specific WebSocket message types"""

    # Client → Server
    PING = "ping"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"

    # Server → Client
    PONG = "pong"
    SUBSCRIBED = "subscribed"
    UNSUBSCRIBED = "unsubscribed"

    # MVP Events
    NARRATIVE_GENERATED = "narrative_generated"  # New narrative created
    ANOMALY_DETECTED = "anomaly_detected"  # New anomaly found
    METRICS_UPDATE = "metrics_update"  # System metrics changed
    PULSE_UPDATE = "pulse_update"  # System pulse updated
    NQS_UPDATE = "nqs_update"  # Narrative Quality Score updated

    # System
    ERROR = "error"
    INFO = "info"


class MVPChannel(str, Enum):
    """MVP subscription channels"""

    NARRATIVES = "mvp:narratives"
    ANOMALIES = "mvp:anomalies"
    METRICS = "mvp:metrics"
    PULSE = "mvp:pulse"
    NQS = "mvp:nqs"
    ALL = "mvp:all"


class MVPWebSocketMessage(BaseModel):
    """MVP WebSocket message format"""

    type: MVPMessageType
    channel: MVPChannel | None = None
    data: dict | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MVPConnectionManager:
    """
    Manages MVP WebSocket connections.

    Handles client connections, subscriptions, and real-time event broadcasting
    for narratives, anomalies, and system pulse.
    """

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.subscriptions: dict[str, set[MVPChannel]] = {}

    async def connect(self, client_id: str, websocket: WebSocket):
        """Register new WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.subscriptions[client_id] = set()

        logger.info(
            f"🔌 MVP client connected: {client_id} (total: {len(self.active_connections)})"
        )

        await self.send_personal_message(
            MVPWebSocketMessage(
                type=MVPMessageType.INFO,
                data={
                    "message": "Connected to MVP WebSocket",
                    "service": "MVP",
                    "port": 8153,
                },
            ),
            client_id,
        )

    def disconnect(self, client_id: str):
        """Remove WebSocket connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.subscriptions:
            del self.subscriptions[client_id]

        logger.info(
            f"🔌 MVP client disconnected: {client_id} (remaining: {len(self.active_connections)})"
        )

    async def subscribe(self, client_id: str, channel: MVPChannel):
        """Subscribe client to channel"""
        if client_id in self.subscriptions:
            self.subscriptions[client_id].add(channel)

            await self.send_personal_message(
                MVPWebSocketMessage(
                    type=MVPMessageType.SUBSCRIBED,
                    channel=channel,
                    data={"channel": channel.value},
                ),
                client_id,
            )

            logger.debug(f"📡 {client_id} subscribed to {channel.value}")

    async def unsubscribe(self, client_id: str, channel: MVPChannel):
        """Unsubscribe client from channel"""
        if client_id in self.subscriptions:
            self.subscriptions[client_id].discard(channel)

            await self.send_personal_message(
                MVPWebSocketMessage(
                    type=MVPMessageType.UNSUBSCRIBED,
                    channel=channel,
                    data={"channel": channel.value},
                ),
                client_id,
            )

            logger.debug(f"📡 {client_id} unsubscribed from {channel.value}")

    async def send_personal_message(self, message: MVPWebSocketMessage, client_id: str):
        """Send message to specific client"""
        if client_id in self.active_connections:
            try:
                websocket = self.active_connections[client_id]
                await websocket.send_json(message.model_dump(mode="json"))
            except Exception as e:
                logger.error(f"❌ Failed to send to {client_id}: {e}")
                raise

    async def broadcast_to_channel(
        self, message: MVPWebSocketMessage, channel: MVPChannel
    ):
        """Broadcast message to all clients subscribed to channel"""
        disconnected = []

        subscriptions_snapshot = list(self.subscriptions.items())

        for client_id, subscribed_channels in subscriptions_snapshot:
            if channel in subscribed_channels or MVPChannel.ALL in subscribed_channels:
                try:
                    await self.send_personal_message(message, client_id)
                except Exception as e:
                    logger.error(f"❌ Broadcast failed to {client_id}: {e}")
                    disconnected.append(client_id)

        for client_id in disconnected:
            self.disconnect(client_id)


# Global connection manager
mvp_manager = MVPConnectionManager()


# Router setup
router = APIRouter(prefix="/ws", tags=["WebSocket"])


@router.websocket("/mvp/{client_id}")
async def mvp_websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    MVP WebSocket endpoint.

    Connect to: ws://localhost:8153/ws/mvp/{unique_client_id}

    Client Messages:
        Ping:
            {"type": "ping"}

        Subscribe to narratives:
            {"type": "subscribe", "channel": "mvp:narratives"}

        Subscribe to anomalies:
            {"type": "subscribe", "channel": "mvp:anomalies"}

        Subscribe to metrics:
            {"type": "subscribe", "channel": "mvp:metrics"}

        Subscribe to pulse:
            {"type": "subscribe", "channel": "mvp:pulse"}

        Subscribe to all:
            {"type": "subscribe", "channel": "mvp:all"}

        Unsubscribe:
            {"type": "unsubscribe", "channel": "mvp:narratives"}

    Server Messages:
        Narrative generated:
            {
                "type": "narrative_generated",
                "channel": "mvp:narratives",
                "data": {
                    "narrative_id": "narr-123",
                    "tone": "analytical",
                    "content": "System analysis reveals...",
                    "nqs": 0.92,
                    "word_count": 250
                }
            }

        Anomaly detected:
            {
                "type": "anomaly_detected",
                "channel": "mvp:anomalies",
                "data": {
                    "anomaly_id": "anom-456",
                    "severity": "critical",
                    "metric_name": "cpu_usage",
                    "threshold": "90%",
                    "current_value": "95%",
                    "detected_at": "2025-10-31T10:00:00Z"
                }
            }

        Metrics update:
            {
                "type": "metrics_update",
                "channel": "mvp:metrics",
                "data": {
                    "cpu_usage": 0.65,
                    "memory_usage": 0.72,
                    "request_rate": 125.5,
                    "error_rate": 0.02
                }
            }

        System pulse update:
            {
                "type": "pulse_update",
                "channel": "mvp:pulse",
                "data": {
                    "health": 0.85,
                    "status_messages": [
                        {
                            "timestamp": "2025-10-31T10:00:00Z",
                            "message": "All systems operational"
                        }
                    ]
                }
            }

        NQS update:
            {
                "type": "nqs_update",
                "channel": "mvp:nqs",
                "data": {
                    "narrative_id": "narr-123",
                    "nqs": 0.92,
                    "quality_metrics": {
                        "coherence": 0.95,
                        "relevance": 0.90,
                        "completeness": 0.91
                    }
                }
            }
    """
    await mvp_manager.connect(client_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            message = MVPWebSocketMessage(**data)

            if message.type == MVPMessageType.PING:
                await mvp_manager.send_personal_message(
                    MVPWebSocketMessage(type=MVPMessageType.PONG),
                    client_id,
                )

            elif message.type == MVPMessageType.SUBSCRIBE and message.channel:
                await mvp_manager.subscribe(client_id, message.channel)

            elif message.type == MVPMessageType.UNSUBSCRIBE and message.channel:
                await mvp_manager.unsubscribe(client_id, message.channel)

            else:
                await mvp_manager.send_personal_message(
                    MVPWebSocketMessage(
                        type=MVPMessageType.ERROR,
                        data={"error": "Unknown message type"},
                    ),
                    client_id,
                )

    except WebSocketDisconnect:
        mvp_manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"❌ WebSocket error for {client_id}: {e}")
        mvp_manager.disconnect(client_id)


# Helper functions for publishing events
async def publish_narrative_generated(narrative_data: dict):
    """Publish new narrative event"""
    await mvp_manager.broadcast_to_channel(
        MVPWebSocketMessage(
            type=MVPMessageType.NARRATIVE_GENERATED, data=narrative_data
        ),
        MVPChannel.NARRATIVES,
    )
    logger.info(f"📡 Published narrative: {narrative_data.get('narrative_id')}")


async def publish_anomaly_detected(anomaly_data: dict):
    """Publish anomaly detection event"""
    await mvp_manager.broadcast_to_channel(
        MVPWebSocketMessage(type=MVPMessageType.ANOMALY_DETECTED, data=anomaly_data),
        MVPChannel.ANOMALIES,
    )
    logger.warning(
        f"📡 Published anomaly: {anomaly_data.get('severity')} - {anomaly_data.get('metric_name')}"
    )


async def publish_metrics_update(metrics_data: dict):
    """Publish system metrics update"""
    await mvp_manager.broadcast_to_channel(
        MVPWebSocketMessage(type=MVPMessageType.METRICS_UPDATE, data=metrics_data),
        MVPChannel.METRICS,
    )
    logger.debug("📡 Published metrics update")


async def publish_pulse_update(pulse_data: dict):
    """Publish system pulse update"""
    await mvp_manager.broadcast_to_channel(
        MVPWebSocketMessage(type=MVPMessageType.PULSE_UPDATE, data=pulse_data),
        MVPChannel.PULSE,
    )
    logger.debug("📡 Published pulse update")


async def publish_nqs_update(nqs_data: dict):
    """Publish NQS score update"""
    await mvp_manager.broadcast_to_channel(
        MVPWebSocketMessage(type=MVPMessageType.NQS_UPDATE, data=nqs_data),
        MVPChannel.NQS,
    )
    logger.debug(f"📡 Published NQS update: {nqs_data.get('nqs')}")
