"""
PENELOPE WebSocket Routes - Real-time Healing Events

Provides WebSocket endpoints for:
- Healing events (patches applied, outcomes)
- 9 Fruits status updates
- Sabbath mode notifications
- Wisdom Base queries
- Live system health metrics

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


class PenelopeMessageType(str, Enum):
    """PENELOPE-specific WebSocket message types"""

    # Client → Server
    PING = "ping"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"

    # Server → Client
    PONG = "pong"
    SUBSCRIBED = "subscribed"
    UNSUBSCRIBED = "unsubscribed"

    # PENELOPE Events
    HEALING_EVENT = "healing_event"  # New patch applied
    FRUIT_UPDATE = "fruit_update"  # 9 Frutos status changed
    SABBATH_MODE = "sabbath_mode"  # Sabbath activated/deactivated
    WISDOM_INSIGHT = "wisdom_insight"  # New wisdom discovered
    HEALTH_STATUS = "health_status"  # Service health update

    # System
    ERROR = "error"
    INFO = "info"


class PenelopeChannel(str, Enum):
    """PENELOPE subscription channels"""

    HEALING = "penelope:healing"
    FRUITS = "penelope:fruits"
    SABBATH = "penelope:sabbath"
    WISDOM = "penelope:wisdom"
    HEALTH = "penelope:health"
    ALL = "penelope:all"


class PenelopeWebSocketMessage(BaseModel):
    """PENELOPE WebSocket message format"""

    type: PenelopeMessageType
    channel: PenelopeChannel | None = None
    data: dict | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PenelopeConnectionManager:
    """
    Manages PENELOPE WebSocket connections.

    Handles client connections, subscriptions, and real-time event broadcasting
    for healing events, fruit updates, and Sabbath notifications.
    """

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.subscriptions: dict[str, set[PenelopeChannel]] = {}

    async def connect(self, client_id: str, websocket: WebSocket):
        """Register new WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.subscriptions[client_id] = set()

        logger.info(
            f"🔌 PENELOPE client connected: {client_id} (total: {len(self.active_connections)})"
        )

        # Send welcome message with Sabbath status
        await self.send_personal_message(
            PenelopeWebSocketMessage(
                type=PenelopeMessageType.INFO,
                data={
                    "message": "Connected to PENELOPE WebSocket",
                    "service": "PENELOPE",
                    "port": 8154,
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
            f"🔌 PENELOPE client disconnected: {client_id} (remaining: {len(self.active_connections)})"
        )

    async def subscribe(self, client_id: str, channel: PenelopeChannel):
        """Subscribe client to channel"""
        if client_id in self.subscriptions:
            self.subscriptions[client_id].add(channel)

            await self.send_personal_message(
                PenelopeWebSocketMessage(
                    type=PenelopeMessageType.SUBSCRIBED,
                    channel=channel,
                    data={"channel": channel.value},
                ),
                client_id,
            )

            logger.debug(f"📡 {client_id} subscribed to {channel.value}")

    async def unsubscribe(self, client_id: str, channel: PenelopeChannel):
        """Unsubscribe client from channel"""
        if client_id in self.subscriptions:
            self.subscriptions[client_id].discard(channel)

            await self.send_personal_message(
                PenelopeWebSocketMessage(
                    type=PenelopeMessageType.UNSUBSCRIBED,
                    channel=channel,
                    data={"channel": channel.value},
                ),
                client_id,
            )

            logger.debug(f"📡 {client_id} unsubscribed from {channel.value}")

    async def send_personal_message(
        self, message: PenelopeWebSocketMessage, client_id: str
    ):
        """Send message to specific client"""
        if client_id in self.active_connections:
            try:
                websocket = self.active_connections[client_id]
                await websocket.send_json(message.model_dump(mode="json"))
            except Exception as e:
                logger.error(f"❌ Failed to send to {client_id}: {e}")
                raise

    async def broadcast_to_channel(
        self, message: PenelopeWebSocketMessage, channel: PenelopeChannel
    ):
        """Broadcast message to all clients subscribed to channel"""
        disconnected = []

        subscriptions_snapshot = list(self.subscriptions.items())

        for client_id, subscribed_channels in subscriptions_snapshot:
            # Check if subscribed to specific channel or ALL
            if (
                channel in subscribed_channels
                or PenelopeChannel.ALL in subscribed_channels
            ):
                try:
                    await self.send_personal_message(message, client_id)
                except Exception as e:
                    logger.error(f"❌ Broadcast failed to {client_id}: {e}")
                    disconnected.append(client_id)

        # Cleanup disconnected clients
        for client_id in disconnected:
            self.disconnect(client_id)


# Global connection manager
penelope_manager = PenelopeConnectionManager()


# Router setup
router = APIRouter(prefix="/ws", tags=["WebSocket"])


@router.websocket("/penelope/{client_id}")
async def penelope_websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    PENELOPE WebSocket endpoint.

    Connect to: ws://localhost:8154/ws/penelope/{unique_client_id}

    Client Messages:
        Ping:
            {"type": "ping"}

        Subscribe to healing events:
            {"type": "subscribe", "channel": "penelope:healing"}

        Subscribe to fruit updates:
            {"type": "subscribe", "channel": "penelope:fruits"}

        Subscribe to all:
            {"type": "subscribe", "channel": "penelope:all"}

        Unsubscribe:
            {"type": "unsubscribe", "channel": "penelope:healing"}

    Server Messages:
        Healing event:
            {
                "type": "healing_event",
                "channel": "penelope:healing",
                "data": {
                    "event_id": "heal-123",
                    "anomaly_type": "memory_leak",
                    "action_taken": "intervene",
                    "outcome": "success",
                    "patch_size_lines": 15,
                    "mansidao_score": 0.92
                }
            }

        Fruit update:
            {
                "type": "fruit_update",
                "channel": "penelope:fruits",
                "data": {
                    "amor_agape": {"score": 0.92},
                    "overall_score": 0.91
                }
            }

        Sabbath notification:
            {
                "type": "sabbath_mode",
                "channel": "penelope:sabbath",
                "data": {
                    "active": true,
                    "message": "Sabbath mode activated. Read-only operations until Monday."
                }
            }
    """
    await penelope_manager.connect(client_id, websocket)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message = PenelopeWebSocketMessage(**data)

            # Handle client messages
            if message.type == PenelopeMessageType.PING:
                await penelope_manager.send_personal_message(
                    PenelopeWebSocketMessage(type=PenelopeMessageType.PONG),
                    client_id,
                )

            elif message.type == PenelopeMessageType.SUBSCRIBE and message.channel:
                await penelope_manager.subscribe(client_id, message.channel)

            elif message.type == PenelopeMessageType.UNSUBSCRIBE and message.channel:
                await penelope_manager.unsubscribe(client_id, message.channel)

            else:
                await penelope_manager.send_personal_message(
                    PenelopeWebSocketMessage(
                        type=PenelopeMessageType.ERROR,
                        data={"error": "Unknown message type"},
                    ),
                    client_id,
                )

    except WebSocketDisconnect:
        penelope_manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"❌ WebSocket error for {client_id}: {e}")
        penelope_manager.disconnect(client_id)


# Helper functions for publishing events
async def publish_healing_event(event_data: dict):
    """
    Publish healing event to all subscribed clients.

    Args:
        event_data: Dict with event_id, anomaly_type, action_taken, outcome, etc.
    """
    await penelope_manager.broadcast_to_channel(
        PenelopeWebSocketMessage(
            type=PenelopeMessageType.HEALING_EVENT, data=event_data
        ),
        PenelopeChannel.HEALING,
    )
    logger.info(f"📡 Published healing event: {event_data.get('event_id')}")


async def publish_fruit_update(fruits_data: dict):
    """
    Publish 9 Frutos status update.

    Args:
        fruits_data: Dict with all fruits scores and overall_score
    """
    await penelope_manager.broadcast_to_channel(
        PenelopeWebSocketMessage(
            type=PenelopeMessageType.FRUIT_UPDATE, data=fruits_data
        ),
        PenelopeChannel.FRUITS,
    )
    logger.debug("📡 Published fruits update")


async def publish_sabbath_notification(active: bool, message: str):
    """
    Publish Sabbath mode status change.

    Args:
        active: True if Sabbath mode is active
        message: Notification message
    """
    await penelope_manager.broadcast_to_channel(
        PenelopeWebSocketMessage(
            type=PenelopeMessageType.SABBATH_MODE,
            data={"active": active, "message": message},
        ),
        PenelopeChannel.SABBATH,
    )
    logger.info(f"📡 Published Sabbath notification: {message}")


async def publish_wisdom_insight(insight_data: dict):
    """
    Publish Wisdom Base insight.

    Args:
        insight_data: Dict with insight details
    """
    await penelope_manager.broadcast_to_channel(
        PenelopeWebSocketMessage(
            type=PenelopeMessageType.WISDOM_INSIGHT, data=insight_data
        ),
        PenelopeChannel.WISDOM,
    )
    logger.info("📡 Published wisdom insight")


async def publish_health_status(health_data: dict):
    """
    Publish service health status.

    Args:
        health_data: Dict with status, uptime, sabbath_mode, etc.
    """
    await penelope_manager.broadcast_to_channel(
        PenelopeWebSocketMessage(
            type=PenelopeMessageType.HEALTH_STATUS, data=health_data
        ),
        PenelopeChannel.HEALTH,
    )
    logger.debug("📡 Published health status")
