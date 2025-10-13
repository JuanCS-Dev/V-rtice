"""
WebSocket Manager - Manages WebSocket connections and broadcasts.

Handles client connections, subscriptions, and message broadcasting.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Set

from fastapi import WebSocket

from hitl.websocket_models import (
    ConnectionAckMessage,
    DecisionNotification,
    NewAPVNotification,
    StatsUpdateNotification,
    WebSocketMessage,
    WebSocketMessageType,
)

logger = logging.getLogger(__name__)


class WebSocketConnectionManager:
    """Manages WebSocket connections and message broadcasting."""

    def __init__(self) -> None:
        """Initialize WebSocket manager."""
        # Active connections: client_id → WebSocket
        self.active_connections: Dict[str, WebSocket] = {}

        # Subscriptions: client_id → Set[channel_name]
        self.subscriptions: Dict[str, Set[str]] = {}

        logger.info("WebSocket manager initialized")

    async def connect(self, websocket: WebSocket) -> str:
        """
        Accept new WebSocket connection.

        Args:
            websocket: WebSocket connection

        Returns:
            client_id: Unique client ID assigned
        """
        await websocket.accept()

        # Generate unique client ID
        client_id = str(uuid.uuid4())

        # Store connection
        self.active_connections[client_id] = websocket
        self.subscriptions[client_id] = set()

        # Send connection acknowledgment
        ack_message = ConnectionAckMessage(
            client_id=client_id,
            message=f"Connected to HITL WebSocket. Client ID: {client_id}",
        )
        await self._send_to_client(client_id, ack_message.model_dump(mode='json'))

        logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")

        return client_id

    async def disconnect(self, client_id: str) -> None:
        """
        Disconnect client.

        Args:
            client_id: Client ID to disconnect
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]

        if client_id in self.subscriptions:
            del self.subscriptions[client_id]

        logger.info(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")

    async def subscribe(self, client_id: str, channels: List[str]) -> None:
        """
        Subscribe client to channels.

        Args:
            client_id: Client ID
            channels: List of channel names (e.g., ['apvs', 'decisions', 'stats'])
        """
        if client_id not in self.subscriptions:
            self.subscriptions[client_id] = set()

        self.subscriptions[client_id].update(channels)

        logger.info(f"Client {client_id} subscribed to channels: {channels}")

    async def unsubscribe(self, client_id: str, channels: List[str]) -> None:
        """
        Unsubscribe client from channels.

        Args:
            client_id: Client ID
            channels: List of channel names to unsubscribe from
        """
        if client_id in self.subscriptions:
            self.subscriptions[client_id].difference_update(channels)

        logger.info(f"Client {client_id} unsubscribed from channels: {channels}")

    async def _send_to_client(self, client_id: str, message: dict) -> bool:
        """
        Send message to specific client.

        Args:
            client_id: Client ID
            message: Message dict to send

        Returns:
            True if sent successfully, False otherwise
        """
        if client_id not in self.active_connections:
            return False

        websocket = self.active_connections[client_id]

        try:
            await websocket.send_json(message)
            return True
        except Exception as e:
            logger.error(f"Failed to send message to client {client_id}: {e}")
            # Remove failed connection
            await self.disconnect(client_id)
            return False

    async def broadcast(self, channel: str, message: dict) -> int:
        """
        Broadcast message to all subscribers of a channel.

        Args:
            channel: Channel name (e.g., 'apvs', 'decisions', 'stats')
            message: Message dict to broadcast

        Returns:
            Number of clients message was sent to
        """
        sent_count = 0

        for client_id, subscribed_channels in self.subscriptions.items():
            if channel in subscribed_channels:
                success = await self._send_to_client(client_id, message)
                if success:
                    sent_count += 1

        logger.info(f"Broadcasted message to {sent_count} clients on channel '{channel}'")

        return sent_count

    async def broadcast_new_apv(self, apv_id: str, apv_code: str, severity: str, cve_id: str, package_name: str) -> int:
        """
        Broadcast new APV notification.

        Args:
            apv_id: APV ID
            apv_code: APV code
            severity: Severity level
            cve_id: CVE ID
            package_name: Package name

        Returns:
            Number of clients notified
        """
        notification = NewAPVNotification(
            apv_id=apv_id,
            apv_code=apv_code,
            severity=severity,
            cve_id=cve_id,
            package_name=package_name,
        )

        return await self.broadcast("apvs", notification.model_dump(mode='json'))

    async def broadcast_decision(
        self,
        decision_id: str,
        apv_id: str,
        apv_code: str,
        decision: str,
        reviewer_name: str,
        action_taken: str,
    ) -> int:
        """
        Broadcast decision notification.

        Args:
            decision_id: Decision ID
            apv_id: APV ID
            apv_code: APV code
            decision: Decision type (approve/reject/modify/escalate)
            reviewer_name: Reviewer name
            action_taken: Action taken (pr_merged/pr_closed/etc)

        Returns:
            Number of clients notified
        """
        notification = DecisionNotification(
            decision_id=decision_id,
            apv_id=apv_id,
            apv_code=apv_code,
            decision=decision,
            reviewer_name=reviewer_name,
            action_taken=action_taken,
        )

        return await self.broadcast("decisions", notification.model_dump(mode='json'))

    async def broadcast_stats_update(self, pending_reviews: int, total_decisions: int, decisions_today: int) -> int:
        """
        Broadcast stats update notification.

        Args:
            pending_reviews: Number of pending reviews
            total_decisions: Total decisions made
            decisions_today: Decisions made today

        Returns:
            Number of clients notified
        """
        notification = StatsUpdateNotification(
            pending_reviews=pending_reviews,
            total_decisions=total_decisions,
            decisions_today=decisions_today,
        )

        return await self.broadcast("stats", notification.model_dump(mode='json'))

    def get_connection_count(self) -> int:
        """Get number of active connections."""
        return len(self.active_connections)

    def get_subscriber_count(self, channel: str) -> int:
        """Get number of subscribers for a channel."""
        count = sum(1 for subscriptions in self.subscriptions.values() if channel in subscriptions)
        return count
