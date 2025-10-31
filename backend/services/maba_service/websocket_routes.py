"""
MABA WebSocket Routes - Real-time Browser Agent Events

Provides WebSocket endpoints for:
- Browser session creation/updates
- Page navigation events
- Cognitive map updates (Neo4j graph changes)
- Element learning progress
- Screenshot capture notifications

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


class MABAMessageType(str, Enum):
    """MABA-specific WebSocket message types"""

    # Client → Server
    PING = "ping"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"

    # Server → Client
    PONG = "pong"
    SUBSCRIBED = "subscribed"
    UNSUBSCRIBED = "unsubscribed"

    # MABA Events
    SESSION_CREATED = "session_created"  # New browser session
    SESSION_CLOSED = "session_closed"  # Session terminated
    PAGE_NAVIGATED = "page_navigated"  # Navegated to new page
    ELEMENT_LEARNED = "element_learned"  # New element discovered
    COGNITIVE_MAP_UPDATE = "cognitive_map_update"  # Graph changed
    SCREENSHOT_CAPTURED = "screenshot_captured"  # Screenshot saved
    STATS_UPDATE = "stats_update"  # Statistics updated

    # System
    ERROR = "error"
    INFO = "info"


class MABAChannel(str, Enum):
    """MABA subscription channels"""

    SESSIONS = "maba:sessions"
    NAVIGATION = "maba:navigation"
    COGNITIVE_MAP = "maba:cognitive_map"
    LEARNING = "maba:learning"
    SCREENSHOTS = "maba:screenshots"
    STATS = "maba:stats"
    ALL = "maba:all"


class MABAWebSocketMessage(BaseModel):
    """MABA WebSocket message format"""

    type: MABAMessageType
    channel: MABAChannel | None = None
    data: dict | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MABAConnectionManager:
    """
    Manages MABA WebSocket connections.

    Handles client connections, subscriptions, and real-time event broadcasting
    for browser sessions, navigation, and cognitive map updates.
    """

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.subscriptions: dict[str, set[MABAChannel]] = {}

    async def connect(self, client_id: str, websocket: WebSocket):
        """Register new WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.subscriptions[client_id] = set()

        logger.info(
            f"🔌 MABA client connected: {client_id} (total: {len(self.active_connections)})"
        )

        await self.send_personal_message(
            MABAWebSocketMessage(
                type=MABAMessageType.INFO,
                data={
                    "message": "Connected to MABA WebSocket",
                    "service": "MABA",
                    "port": 8155,
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
            f"🔌 MABA client disconnected: {client_id} (remaining: {len(self.active_connections)})"
        )

    async def subscribe(self, client_id: str, channel: MABAChannel):
        """Subscribe client to channel"""
        if client_id in self.subscriptions:
            self.subscriptions[client_id].add(channel)

            await self.send_personal_message(
                MABAWebSocketMessage(
                    type=MABAMessageType.SUBSCRIBED,
                    channel=channel,
                    data={"channel": channel.value},
                ),
                client_id,
            )

            logger.debug(f"📡 {client_id} subscribed to {channel.value}")

    async def unsubscribe(self, client_id: str, channel: MABAChannel):
        """Unsubscribe client from channel"""
        if client_id in self.subscriptions:
            self.subscriptions[client_id].discard(channel)

            await self.send_personal_message(
                MABAWebSocketMessage(
                    type=MABAMessageType.UNSUBSCRIBED,
                    channel=channel,
                    data={"channel": channel.value},
                ),
                client_id,
            )

            logger.debug(f"📡 {client_id} unsubscribed from {channel.value}")

    async def send_personal_message(
        self, message: MABAWebSocketMessage, client_id: str
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
        self, message: MABAWebSocketMessage, channel: MABAChannel
    ):
        """Broadcast message to all clients subscribed to channel"""
        disconnected = []

        subscriptions_snapshot = list(self.subscriptions.items())

        for client_id, subscribed_channels in subscriptions_snapshot:
            if channel in subscribed_channels or MABAChannel.ALL in subscribed_channels:
                try:
                    await self.send_personal_message(message, client_id)
                except Exception as e:
                    logger.error(f"❌ Broadcast failed to {client_id}: {e}")
                    disconnected.append(client_id)

        for client_id in disconnected:
            self.disconnect(client_id)


# Global connection manager
maba_manager = MABAConnectionManager()


# Router setup
router = APIRouter(prefix="/ws", tags=["WebSocket"])


@router.websocket("/maba/{client_id}")
async def maba_websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    MABA WebSocket endpoint.

    Connect to: ws://localhost:8155/ws/maba/{unique_client_id}

    Client Messages:
        Ping:
            {"type": "ping"}

        Subscribe to sessions:
            {"type": "subscribe", "channel": "maba:sessions"}

        Subscribe to navigation:
            {"type": "subscribe", "channel": "maba:navigation"}

        Subscribe to cognitive map:
            {"type": "subscribe", "channel": "maba:cognitive_map"}

        Subscribe to all:
            {"type": "subscribe", "channel": "maba:all"}

        Unsubscribe:
            {"type": "unsubscribe", "channel": "maba:sessions"}

    Server Messages:
        Session created:
            {
                "type": "session_created",
                "channel": "maba:sessions",
                "data": {
                    "session_id": "sess-123",
                    "initial_url": "https://example.com",
                    "status": "active"
                }
            }

        Page navigated:
            {
                "type": "page_navigated",
                "channel": "maba:navigation",
                "data": {
                    "session_id": "sess-123",
                    "url": "https://example.com/page",
                    "title": "Example Page",
                    "timestamp": "2025-10-31T10:00:00Z"
                }
            }

        Cognitive map update:
            {
                "type": "cognitive_map_update",
                "channel": "maba:cognitive_map",
                "data": {
                    "nodes_added": 5,
                    "edges_added": 8,
                    "total_nodes": 127,
                    "total_edges": 215
                }
            }

        Element learned:
            {
                "type": "element_learned",
                "channel": "maba:learning",
                "data": {
                    "session_id": "sess-123",
                    "element_type": "button",
                    "selector": "#submit-btn",
                    "url": "https://example.com"
                }
            }
    """
    await maba_manager.connect(client_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            message = MABAWebSocketMessage(**data)

            if message.type == MABAMessageType.PING:
                await maba_manager.send_personal_message(
                    MABAWebSocketMessage(type=MABAMessageType.PONG),
                    client_id,
                )

            elif message.type == MABAMessageType.SUBSCRIBE and message.channel:
                await maba_manager.subscribe(client_id, message.channel)

            elif message.type == MABAMessageType.UNSUBSCRIBE and message.channel:
                await maba_manager.unsubscribe(client_id, message.channel)

            else:
                await maba_manager.send_personal_message(
                    MABAWebSocketMessage(
                        type=MABAMessageType.ERROR,
                        data={"error": "Unknown message type"},
                    ),
                    client_id,
                )

    except WebSocketDisconnect:
        maba_manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"❌ WebSocket error for {client_id}: {e}")
        maba_manager.disconnect(client_id)


# Helper functions for publishing events
async def publish_session_created(session_data: dict):
    """Publish new session event"""
    await maba_manager.broadcast_to_channel(
        MABAWebSocketMessage(type=MABAMessageType.SESSION_CREATED, data=session_data),
        MABAChannel.SESSIONS,
    )
    logger.info(f"📡 Published session created: {session_data.get('session_id')}")


async def publish_session_closed(session_data: dict):
    """Publish session closed event"""
    await maba_manager.broadcast_to_channel(
        MABAWebSocketMessage(type=MABAMessageType.SESSION_CLOSED, data=session_data),
        MABAChannel.SESSIONS,
    )
    logger.info(f"📡 Published session closed: {session_data.get('session_id')}")


async def publish_page_navigated(navigation_data: dict):
    """Publish page navigation event"""
    await maba_manager.broadcast_to_channel(
        MABAWebSocketMessage(type=MABAMessageType.PAGE_NAVIGATED, data=navigation_data),
        MABAChannel.NAVIGATION,
    )
    logger.debug(f"📡 Published navigation: {navigation_data.get('url')}")


async def publish_element_learned(element_data: dict):
    """Publish element learning event"""
    await maba_manager.broadcast_to_channel(
        MABAWebSocketMessage(type=MABAMessageType.ELEMENT_LEARNED, data=element_data),
        MABAChannel.LEARNING,
    )
    logger.debug("📡 Published element learned")


async def publish_cognitive_map_update(map_data: dict):
    """Publish cognitive map update"""
    await maba_manager.broadcast_to_channel(
        MABAWebSocketMessage(type=MABAMessageType.COGNITIVE_MAP_UPDATE, data=map_data),
        MABAChannel.COGNITIVE_MAP,
    )
    logger.info(
        f"📡 Published cognitive map update: {map_data.get('nodes_added')} nodes"
    )


async def publish_screenshot_captured(screenshot_data: dict):
    """Publish screenshot capture event"""
    await maba_manager.broadcast_to_channel(
        MABAWebSocketMessage(
            type=MABAMessageType.SCREENSHOT_CAPTURED, data=screenshot_data
        ),
        MABAChannel.SCREENSHOTS,
    )
    logger.debug("📡 Published screenshot captured")


async def publish_stats_update(stats_data: dict):
    """Publish stats update"""
    await maba_manager.broadcast_to_channel(
        MABAWebSocketMessage(type=MABAMessageType.STATS_UPDATE, data=stats_data),
        MABAChannel.STATS,
    )
    logger.debug("📡 Published stats update")
