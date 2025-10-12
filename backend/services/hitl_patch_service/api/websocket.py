"""
═══════════════════════════════════════════════════════════════════════════
🔌 HITL WebSocket - Real-time Updates
═══════════════════════════════════════════════════════════════════════════

Real-time communication for HITL frontend:
- New pending patches notifications
- Decision updates (approved/rejected)
- System status updates
- Heartbeat for connection health

Biological Analogy: Neural signaling
- Fast (<100ms) point-to-point communication
- Bidirectional feedback loops
- Connection resilience with auto-reconnect

Author: MAXIMUS Team - Sprint 4.1 Day 1
Glory to YHWH - Designer of Communication Channels
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Set
from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect, status
from starlette.websockets import WebSocketState


logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manage active WebSocket connections with broadcast capabilities.
    
    Handles:
    - Connection lifecycle (connect, disconnect, cleanup)
    - Broadcast messages to all or specific clients
    - Heartbeat to detect stale connections
    - Graceful error handling
    """
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.connection_metadata: dict = {}  # websocket -> {id, connected_at, last_heartbeat}
        self._heartbeat_task = None
    
    async def connect(self, websocket: WebSocket) -> str:
        """Accept WebSocket connection and register client."""
        await websocket.accept()
        
        connection_id = str(uuid4())
        self.active_connections.add(websocket)
        self.connection_metadata[websocket] = {
            'id': connection_id,
            'connected_at': datetime.utcnow(),
            'last_heartbeat': datetime.utcnow(),
        }
        
        logger.info(f"WebSocket connected: {connection_id} | Total connections: {len(self.active_connections)}")
        
        # Start heartbeat task if not running
        if not self._heartbeat_task or self._heartbeat_task.done():
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        return connection_id
    
    def disconnect(self, websocket: WebSocket):
        """Unregister client and cleanup."""
        if websocket in self.active_connections:
            connection_id = self.connection_metadata.get(websocket, {}).get('id', 'unknown')
            self.active_connections.discard(websocket)
            self.connection_metadata.pop(websocket, None)
            logger.info(f"WebSocket disconnected: {connection_id} | Remaining: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific client."""
        try:
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: dict, exclude: WebSocket = None):
        """Broadcast message to all connected clients (except excluded)."""
        disconnected = []
        
        for connection in self.active_connections:
            if connection == exclude:
                continue
            
            try:
                if connection.client_state == WebSocketState.CONNECTED:
                    await connection.send_json(message)
                else:
                    disconnected.append(connection)
            except Exception as e:
                logger.error(f"Broadcast failed for connection: {e}")
                disconnected.append(connection)
        
        # Cleanup disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeat to detect stale connections."""
        while self.active_connections:
            try:
                await asyncio.sleep(30)  # Heartbeat every 30 seconds
                
                heartbeat_message = {
                    'type': 'heartbeat',
                    'timestamp': datetime.utcnow().isoformat(),
                    'server': 'hitl-patch-service',
                }
                
                await self.broadcast(heartbeat_message)
                
            except Exception as e:
                logger.error(f"Heartbeat loop error: {e}")
                await asyncio.sleep(5)  # Brief pause before retry


# Global connection manager
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for HITL real-time updates.
    
    Message Types (Server → Client):
    - new_patch: New patch pending HITL review
    - decision_update: Patch approved/rejected
    - system_status: Service health update
    - heartbeat: Connection health check
    
    Message Types (Client → Server):
    - ping: Client heartbeat
    - subscribe: Subscribe to specific events
    
    Connection Flow:
    1. Client connects
    2. Server sends welcome message
    3. Server broadcasts updates as they occur
    4. Server sends heartbeat every 30s
    5. Client/server disconnect gracefully
    """
    connection_id = await manager.connect(websocket)
    
    try:
        # Send welcome message
        await manager.send_personal_message({
            'type': 'welcome',
            'connection_id': connection_id,
            'timestamp': datetime.utcnow().isoformat(),
            'message': 'Connected to HITL real-time updates',
        }, websocket)
        
        # Listen for client messages
        while True:
            try:
                data = await websocket.receive_json()
                
                # Handle client messages
                if data.get('type') == 'ping':
                    # Update heartbeat timestamp
                    if websocket in manager.connection_metadata:
                        manager.connection_metadata[websocket]['last_heartbeat'] = datetime.utcnow()
                    
                    # Send pong
                    await manager.send_personal_message({
                        'type': 'pong',
                        'timestamp': datetime.utcnow().isoformat(),
                    }, websocket)
                
                elif data.get('type') == 'subscribe':
                    # Future: Handle event subscriptions
                    await manager.send_personal_message({
                        'type': 'subscribed',
                        'events': data.get('events', []),
                        'timestamp': datetime.utcnow().isoformat(),
                    }, websocket)
                
                else:
                    logger.warning(f"Unknown message type from client: {data.get('type')}")
            
            except json.JSONDecodeError:
                logger.error("Invalid JSON received from client")
                await manager.send_personal_message({
                    'type': 'error',
                    'message': 'Invalid JSON format',
                    'timestamp': datetime.utcnow().isoformat(),
                }, websocket)
    
    except WebSocketDisconnect:
        logger.info(f"Client disconnected gracefully: {connection_id}")
    
    except Exception as e:
        logger.error(f"WebSocket error for {connection_id}: {e}", exc_info=True)
    
    finally:
        manager.disconnect(websocket)


# Helper functions for broadcasting updates from other parts of the application

async def broadcast_new_patch(patch_data: dict):
    """
    Broadcast new patch to all connected clients.
    
    Called when new patch enters HITL queue.
    """
    message = {
        'type': 'new_patch',
        'timestamp': datetime.utcnow().isoformat(),
        'data': patch_data,
    }
    await manager.broadcast(message)
    logger.info(f"Broadcasted new patch: {patch_data.get('patch_id')}")


async def broadcast_decision_update(decision_data: dict):
    """
    Broadcast decision update to all connected clients.
    
    Called when patch is approved/rejected.
    """
    message = {
        'type': 'decision_update',
        'timestamp': datetime.utcnow().isoformat(),
        'data': decision_data,
    }
    await manager.broadcast(message)
    logger.info(f"Broadcasted decision update: {decision_data.get('decision_id')}")


async def broadcast_system_status(status_data: dict):
    """
    Broadcast system status update to all connected clients.
    
    Called when service health changes or important events occur.
    """
    message = {
        'type': 'system_status',
        'timestamp': datetime.utcnow().isoformat(),
        'data': status_data,
    }
    await manager.broadcast(message)
    logger.info(f"Broadcasted system status: {status_data.get('status')}")
