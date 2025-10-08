"""WebSocket Connection Manager - PRODUCTION-READY

Manages WebSocket connections, rooms, and broadcasting.

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Set

from fastapi import WebSocket

from .events import WSEvent, WSEventType

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections and event broadcasting.

    Features:
    - Multiple concurrent connections
    - Room-based broadcasting
    - Event filtering per connection
    - Automatic cleanup on disconnect
    """

    def __init__(self):
        """Initialize connection manager"""
        # Active connections: {connection_id: websocket}
        self.active_connections: Dict[str, WebSocket] = {}

        # Room memberships: {room_name: set(connection_ids)}
        self.rooms: Dict[str, Set[str]] = {}

        # Event subscriptions: {connection_id: set(event_types)}
        self.subscriptions: Dict[str, Set[WSEventType]] = {}

        # Connection metadata: {connection_id: metadata_dict}
        self.connection_metadata: Dict[str, Dict] = {}

        # Statistics
        self.total_connections = 0
        self.total_disconnections = 0
        self.total_messages_sent = 0
        self.total_messages_received = 0

        logger.info("ConnectionManager initialized")

    async def connect(self, websocket: WebSocket, connection_id: str, metadata: Optional[Dict] = None) -> None:
        """
        Accept and register a new WebSocket connection.

        Args:
            websocket: WebSocket connection
            connection_id: Unique connection identifier
            metadata: Optional connection metadata (user_id, etc.)
        """
        await websocket.accept()

        self.active_connections[connection_id] = websocket
        self.subscriptions[connection_id] = set()
        self.connection_metadata[connection_id] = metadata or {}
        self.total_connections += 1

        logger.info(f"WebSocket connected: {connection_id} (total active: {len(self.active_connections)})")

        # Send welcome event
        welcome_event = WSEvent(
            event_type=WSEventType.CONNECTED,
            data={
                "connection_id": connection_id,
                "message": "Connected to Active Immune Core WebSocket",
                "timestamp": datetime.utcnow().isoformat(),
            },
            source="connection_manager",
        )

        await self.send_personal_message(welcome_event, connection_id)

    async def disconnect(self, connection_id: str) -> None:
        """
        Disconnect and cleanup a WebSocket connection.

        Args:
            connection_id: Connection identifier
        """
        if connection_id in self.active_connections:
            # Remove from all rooms
            for room_name in list(self.rooms.keys()):
                if connection_id in self.rooms[room_name]:
                    self.rooms[room_name].remove(connection_id)
                    if not self.rooms[room_name]:
                        del self.rooms[room_name]

            # Cleanup
            del self.active_connections[connection_id]
            del self.subscriptions[connection_id]
            del self.connection_metadata[connection_id]
            self.total_disconnections += 1

            logger.info(f"WebSocket disconnected: {connection_id} (total active: {len(self.active_connections)})")

    async def join_room(self, connection_id: str, room: str) -> bool:
        """
        Add connection to a room.

        Args:
            connection_id: Connection identifier
            room: Room name

        Returns:
            True if joined successfully
        """
        if connection_id not in self.active_connections:
            return False

        if room not in self.rooms:
            self.rooms[room] = set()

        self.rooms[room].add(connection_id)

        logger.info(f"Connection {connection_id} joined room '{room}'")
        return True

    async def leave_room(self, connection_id: str, room: str) -> bool:
        """
        Remove connection from a room.

        Args:
            connection_id: Connection identifier
            room: Room name

        Returns:
            True if left successfully
        """
        if room in self.rooms and connection_id in self.rooms[room]:
            self.rooms[room].remove(connection_id)

            if not self.rooms[room]:
                del self.rooms[room]

            logger.info(f"Connection {connection_id} left room '{room}'")
            return True

        return False

    async def subscribe(self, connection_id: str, event_types: List[WSEventType]) -> bool:
        """
        Subscribe connection to specific event types.

        Args:
            connection_id: Connection identifier
            event_types: List of event types to subscribe to

        Returns:
            True if subscribed successfully
        """
        if connection_id not in self.active_connections:
            return False

        self.subscriptions[connection_id].update(event_types)

        logger.info(f"Connection {connection_id} subscribed to: {[e.value for e in event_types]}")
        return True

    async def unsubscribe(self, connection_id: str, event_types: List[WSEventType]) -> bool:
        """
        Unsubscribe connection from specific event types.

        Args:
            connection_id: Connection identifier
            event_types: List of event types to unsubscribe from

        Returns:
            True if unsubscribed successfully
        """
        if connection_id not in self.active_connections:
            return False

        self.subscriptions[connection_id].difference_update(event_types)

        logger.info(f"Connection {connection_id} unsubscribed from: {[e.value for e in event_types]}")
        return True

    async def send_personal_message(self, event: WSEvent, connection_id: str) -> bool:
        """
        Send event to a specific connection.

        Args:
            event: Event to send
            connection_id: Target connection identifier

        Returns:
            True if sent successfully
        """
        if connection_id not in self.active_connections:
            return False

        try:
            websocket = self.active_connections[connection_id]
            await websocket.send_json(event.model_dump())
            self.total_messages_sent += 1
            return True

        except Exception as e:
            logger.error(
                f"Error sending message to {connection_id}: {e}",
                exc_info=True,
            )
            await self.disconnect(connection_id)
            return False

    async def broadcast(
        self,
        event: WSEvent,
        room: Optional[str] = None,
        exclude: Optional[Set[str]] = None,
    ) -> int:
        """
        Broadcast event to connections.

        Args:
            event: Event to broadcast
            room: Optional room to broadcast to (None = all connections)
            exclude: Optional set of connection IDs to exclude

        Returns:
            Number of connections that received the event
        """
        exclude = exclude or set()

        # Determine target connections
        if room:
            if room not in self.rooms:
                return 0
            target_connections = self.rooms[room] - exclude
        else:
            target_connections = set(self.active_connections.keys()) - exclude

        # Filter by subscriptions (if any)
        subscribed_connections = set()
        for conn_id in target_connections:
            # If no subscriptions, send all events
            if not self.subscriptions[conn_id]:
                subscribed_connections.add(conn_id)
            # If subscribed to this event type, send
            elif event.event_type in self.subscriptions[conn_id]:
                subscribed_connections.add(conn_id)

        # Send to all subscribed connections
        sent_count = 0
        for connection_id in subscribed_connections:
            success = await self.send_personal_message(event, connection_id)
            if success:
                sent_count += 1

        logger.debug(f"Broadcast {event.event_type.value} to {sent_count} connections (room: {room or 'all'})")

        return sent_count

    def get_statistics(self) -> Dict:
        """
        Get connection manager statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "active_connections": len(self.active_connections),
            "total_connections": self.total_connections,
            "total_disconnections": self.total_disconnections,
            "total_rooms": len(self.rooms),
            "messages_sent": self.total_messages_sent,
            "messages_received": self.total_messages_received,
            "rooms": {room: len(members) for room, members in self.rooms.items()},
        }

    def get_connection_info(self, connection_id: str) -> Optional[Dict]:
        """
        Get information about a specific connection.

        Args:
            connection_id: Connection identifier

        Returns:
            Connection info or None if not found
        """
        if connection_id not in self.active_connections:
            return None

        # Find which rooms this connection is in
        connection_rooms = [room for room, members in self.rooms.items() if connection_id in members]

        return {
            "connection_id": connection_id,
            "metadata": self.connection_metadata.get(connection_id, {}),
            "rooms": connection_rooms,
            "subscriptions": [e.value for e in self.subscriptions.get(connection_id, set())],
        }
