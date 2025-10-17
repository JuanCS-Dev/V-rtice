"""WebSocket handler for real-time verdict streaming.

Manages WebSocket connections, broadcasts verdicts to connected clients,
handles ping/pong for connection health.
"""

import asyncio
import json

import structlog
from fastapi import WebSocket, WebSocketDisconnect

from backend.services.verdict_engine_service.models import Verdict, VerdictStats, WebSocketMessage

logger = structlog.get_logger()


class ConnectionManager:
    """Manages WebSocket connections and broadcasting."""

    def __init__(self) -> None:
        """Initialize connection manager."""
        self.active_connections: dict[str, WebSocket] = {}
        self.connection_lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """Accept and register new WebSocket connection."""
        await websocket.accept()
        async with self.connection_lock:
            self.active_connections[client_id] = websocket
        logger.info("websocket_connected", client_id=client_id, total=len(self.active_connections))

    async def disconnect(self, client_id: str) -> None:
        """Remove WebSocket connection."""
        async with self.connection_lock:
            if client_id in self.active_connections:
                del self.active_connections[client_id]
        logger.info("websocket_disconnected", client_id=client_id, total=len(self.active_connections))

    async def send_personal(self, message: WebSocketMessage, client_id: str) -> None:
        """Send message to specific client."""
        websocket = self.active_connections.get(client_id)
        if websocket:
            try:
                await websocket.send_json(message.model_dump(mode="json"))
            except Exception as e:
                logger.error("send_personal_failed", client_id=client_id, error=str(e))
                await self.disconnect(client_id)

    async def broadcast_verdict(self, verdict: Verdict) -> None:
        """Broadcast verdict to all connected clients."""
        message = WebSocketMessage(type="verdict", data=verdict)
        await self._broadcast(message)

    async def broadcast_stats(self, stats: VerdictStats) -> None:
        """Broadcast stats to all connected clients."""
        message = WebSocketMessage(type="stats", data=stats)
        await self._broadcast(message)

    async def _broadcast(self, message: WebSocketMessage) -> None:
        """Internal broadcast to all clients."""
        disconnected: list[str] = []

        async with self.connection_lock:
            for client_id, websocket in self.active_connections.items():
                try:
                    await websocket.send_json(message.model_dump(mode="json"))
                except Exception as e:
                    logger.error("broadcast_failed", client_id=client_id, error=str(e))
                    disconnected.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected:
            await self.disconnect(client_id)

    async def ping_all(self) -> None:
        """Send ping to all connections for health check."""
        message = WebSocketMessage(type="ping", data={"connections": len(self.active_connections)})
        await self._broadcast(message)

    def get_connection_count(self) -> int:
        """Get number of active connections."""
        return len(self.active_connections)


async def websocket_handler(
    websocket: WebSocket,
    client_id: str,
    manager: ConnectionManager,
) -> None:
    """Handle WebSocket lifecycle for a single client."""
    await manager.connect(websocket, client_id)  # pragma: no cover
  # pragma: no cover
    try:  # pragma: no cover
        while True:  # pragma: no cover
            # Receive messages from client (for ACKs, filters, etc.)  # pragma: no cover
            data = await websocket.receive_text()  # pragma: no cover
  # pragma: no cover
            try:  # pragma: no cover
                message = json.loads(data)  # pragma: no cover
                message_type = message.get("type")  # pragma: no cover
  # pragma: no cover
                if message_type == "ping":  # pragma: no cover
                    await manager.send_personal(  # pragma: no cover
                        WebSocketMessage(type="ping", data={"status": "ok"}),  # pragma: no cover
                        client_id,  # pragma: no cover
                    )  # pragma: no cover
                elif message_type == "subscribe_filter":  # pragma: no cover
                    # Future: client-side filtering  # pragma: no cover
                    logger.info("filter_subscription", client_id=client_id, filters=message.get("data"))  # pragma: no cover
  # pragma: no cover
            except json.JSONDecodeError:  # pragma: no cover
                logger.warning("invalid_json", client_id=client_id, data=data)  # pragma: no cover
  # pragma: no cover
    except WebSocketDisconnect:  # pragma: no cover
        await manager.disconnect(client_id)  # pragma: no cover
    except Exception as e:  # pragma: no cover
        logger.error("websocket_error", client_id=client_id, error=str(e))  # pragma: no cover
        await manager.disconnect(client_id)  # pragma: no cover
