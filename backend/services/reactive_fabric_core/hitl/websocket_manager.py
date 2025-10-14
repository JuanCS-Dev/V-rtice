"""
WebSocket Manager
Real-time alerts and notifications for HITL Console
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Set, Optional, Any
from enum import Enum

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class AlertType(str, Enum):
    """Alert notification types"""
    NEW_DECISION = "new_decision"
    CRITICAL_THREAT = "critical_threat"
    APT_DETECTED = "apt_detected"
    HONEYTOKEN_TRIGGERED = "honeytoken_triggered"
    DECISION_REQUIRED = "decision_required"
    SYSTEM_ALERT = "system_alert"
    INCIDENT_ESCALATED = "incident_escalated"


class AlertPriority(str, Enum):
    """Alert priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Alert(BaseModel):
    """Real-time alert model"""
    alert_id: str
    alert_type: AlertType
    priority: AlertPriority
    title: str
    message: str
    data: Dict[str, Any]
    timestamp: datetime
    requires_action: bool = False


class ConnectionManager:
    """
    WebSocket connection manager for real-time alerts

    Features:
    - Multiple concurrent connections
    - User-specific subscriptions
    - Broadcast and unicast messaging
    - Heartbeat/ping-pong
    - Automatic reconnection support
    """

    def __init__(self):
        # Active connections: username -> Set[WebSocket]
        self.active_connections: Dict[str, Set[WebSocket]] = {}

        # Subscriptions: username -> Set[AlertType]
        self.subscriptions: Dict[str, Set[AlertType]] = {}

        # Connection metadata
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}

        # Statistics
        self.stats = {
            "total_connections": 0,
            "total_alerts_sent": 0,
            "total_disconnects": 0
        }

    async def connect(self, websocket: WebSocket, username: str):
        """
        Connect new WebSocket client

        Args:
            websocket: WebSocket connection
            username: Username of connecting user
        """
        await websocket.accept()

        # Add to active connections
        if username not in self.active_connections:
            self.active_connections[username] = set()

        self.active_connections[username].add(websocket)

        # Initialize subscriptions (subscribe to all by default)
        if username not in self.subscriptions:
            self.subscriptions[username] = set(AlertType)

        # Store metadata
        self.connection_metadata[websocket] = {
            "username": username,
            "connected_at": datetime.now(),
            "last_ping": datetime.now()
        }

        self.stats["total_connections"] += 1

        logger.info(f"WebSocket connected: {username} (total: {len(self.active_connections)})")

        # Send welcome message
        await self.send_personal_message(
            {
                "type": "connection",
                "status": "connected",
                "message": "Connected to HITL Console real-time feed",
                "timestamp": datetime.now().isoformat()
            },
            websocket
        )

    def disconnect(self, websocket: WebSocket):
        """
        Disconnect WebSocket client

        Args:
            websocket: WebSocket connection to disconnect
        """
        metadata = self.connection_metadata.get(websocket, {})
        username = metadata.get("username", "unknown")

        # Remove from active connections
        if username in self.active_connections:
            self.active_connections[username].discard(websocket)

            if not self.active_connections[username]:
                del self.active_connections[username]

        # Remove metadata
        if websocket in self.connection_metadata:
            del self.connection_metadata[websocket]

        self.stats["total_disconnects"] += 1

        logger.info(f"WebSocket disconnected: {username} (total: {len(self.active_connections)})")

    async def send_personal_message(self, message: Dict, websocket: WebSocket):
        """
        Send message to specific WebSocket

        Args:
            message: Message data
            websocket: Target WebSocket connection
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self.disconnect(websocket)

    async def send_to_user(self, message: Dict, username: str):
        """
        Send message to all connections of a user

        Args:
            message: Message data
            username: Target username
        """
        if username in self.active_connections:
            disconnected = set()

            for websocket in self.active_connections[username]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to {username}: {e}")
                    disconnected.add(websocket)

            # Clean up disconnected sockets
            for ws in disconnected:
                self.disconnect(ws)

    async def broadcast(self, message: Dict, alert_type: Optional[AlertType] = None):
        """
        Broadcast message to all connected users

        Args:
            message: Message data
            alert_type: Optional alert type for subscription filtering
        """
        for username, websockets in list(self.active_connections.items()):
            # Check subscription
            if alert_type and alert_type not in self.subscriptions.get(username, set()):
                continue

            disconnected = set()

            for websocket in websockets:
                try:
                    await websocket.send_json(message)
                    self.stats["total_alerts_sent"] += 1
                except Exception as e:
                    logger.error(f"Broadcast error to {username}: {e}")
                    disconnected.add(websocket)

            # Clean up disconnected sockets
            for ws in disconnected:
                self.disconnect(ws)

    async def send_alert(self, alert: Alert, target_username: Optional[str] = None):
        """
        Send alert notification

        Args:
            alert: Alert object
            target_username: Optional specific user, otherwise broadcast
        """
        message = {
            "type": "alert",
            "alert": {
                "alert_id": alert.alert_id,
                "alert_type": alert.alert_type.value,
                "priority": alert.priority.value,
                "title": alert.title,
                "message": alert.message,
                "data": alert.data,
                "timestamp": alert.timestamp.isoformat(),
                "requires_action": alert.requires_action
            }
        }

        if target_username:
            await self.send_to_user(message, target_username)
        else:
            await self.broadcast(message, alert.alert_type)

        logger.info(
            f"Alert sent: {alert.alert_type.value} (priority: {alert.priority.value}) "
            f"to {'all' if not target_username else target_username}"
        )

    async def send_heartbeat(self):
        """Send heartbeat/ping to all connections"""
        message = {
            "type": "heartbeat",
            "timestamp": datetime.now().isoformat()
        }

        await self.broadcast(message)

    def subscribe(self, username: str, alert_types: Set[AlertType]):
        """
        Set user subscriptions

        Args:
            username: Username
            alert_types: Set of alert types to subscribe to
        """
        self.subscriptions[username] = alert_types
        logger.info(f"User {username} subscribed to: {[t.value for t in alert_types]}")

    def unsubscribe(self, username: str, alert_types: Set[AlertType]):
        """
        Remove user subscriptions

        Args:
            username: Username
            alert_types: Set of alert types to unsubscribe from
        """
        if username in self.subscriptions:
            self.subscriptions[username] -= alert_types
            logger.info(f"User {username} unsubscribed from: {[t.value for t in alert_types]}")

    def get_connection_count(self) -> int:
        """Get total number of active connections"""
        return sum(len(ws_set) for ws_set in self.active_connections.values())

    def get_user_count(self) -> int:
        """Get number of unique connected users"""
        return len(self.active_connections)

    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            **self.stats,
            "current_connections": self.get_connection_count(),
            "current_users": self.get_user_count()
        }


# Global connection manager instance
manager = ConnectionManager()


# ============================================================================
# HEARTBEAT TASK
# ============================================================================

async def heartbeat_task():
    """Background task to send periodic heartbeats"""
    while True:
        await asyncio.sleep(30)  # Every 30 seconds
        try:
            await manager.send_heartbeat()
        except Exception as e:
            logger.error(f"Heartbeat error: {e}")


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def notify_new_decision(decision_data: Dict[str, Any]):
    """
    Notify about new decision request

    Args:
        decision_data: Decision request data
    """
    alert = Alert(
        alert_id=f"alert_{datetime.now().timestamp()}",
        alert_type=AlertType.NEW_DECISION,
        priority=AlertPriority[decision_data.get("priority", "MEDIUM").upper()],
        title="New Decision Required",
        message=f"New decision request from {decision_data.get('source_ip')}",
        data=decision_data,
        timestamp=datetime.now(),
        requires_action=True
    )

    await manager.send_alert(alert)


async def notify_critical_threat(threat_data: Dict[str, Any]):
    """
    Notify about critical threat

    Args:
        threat_data: Threat data
    """
    alert = Alert(
        alert_id=f"alert_{datetime.now().timestamp()}",
        alert_type=AlertType.CRITICAL_THREAT,
        priority=AlertPriority.CRITICAL,
        title="CRITICAL THREAT DETECTED",
        message=f"APT activity detected from {threat_data.get('source_ip')}",
        data=threat_data,
        timestamp=datetime.now(),
        requires_action=True
    )

    await manager.send_alert(alert)


async def notify_apt_detection(apt_data: Dict[str, Any]):
    """
    Notify about APT detection

    Args:
        apt_data: APT detection data
    """
    alert = Alert(
        alert_id=f"alert_{datetime.now().timestamp()}",
        alert_type=AlertType.APT_DETECTED,
        priority=AlertPriority.CRITICAL,
        title=f"APT Detected: {apt_data.get('attributed_actor', 'Unknown')}",
        message=f"Attribution confidence: {apt_data.get('confidence', 0)}%",
        data=apt_data,
        timestamp=datetime.now(),
        requires_action=True
    )

    await manager.send_alert(alert)


async def notify_honeytoken_triggered(token_data: Dict[str, Any]):
    """
    Notify about honeytoken trigger

    Args:
        token_data: Honeytoken data
    """
    alert = Alert(
        alert_id=f"alert_{datetime.now().timestamp()}",
        alert_type=AlertType.HONEYTOKEN_TRIGGERED,
        priority=AlertPriority.CRITICAL,
        title="HONEYTOKEN TRIGGERED!",
        message=f"Token type: {token_data.get('token_type')} from {token_data.get('source_ip')}",
        data=token_data,
        timestamp=datetime.now(),
        requires_action=True
    )

    await manager.send_alert(alert)


async def notify_incident_escalated(incident_data: Dict[str, Any]):
    """
    Notify about incident escalation

    Args:
        incident_data: Incident data
    """
    alert = Alert(
        alert_id=f"alert_{datetime.now().timestamp()}",
        alert_type=AlertType.INCIDENT_ESCALATED,
        priority=AlertPriority.HIGH,
        title="Incident Escalated",
        message=f"Incident {incident_data.get('incident_id')} escalated to {incident_data.get('threat_level')}",
        data=incident_data,
        timestamp=datetime.now(),
        requires_action=False
    )

    await manager.send_alert(alert)
