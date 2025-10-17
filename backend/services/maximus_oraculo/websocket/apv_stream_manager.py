"""
WebSocket APV Stream Manager.

Manages real-time streaming of APVs (Ameaças Potenciais Verificadas)
to connected frontend clients via WebSocket connections.

Architectural Role:
- Subscribes to Kafka topic: maximus.adaptive-immunity.apv
- Maintains connection pool of active WebSocket clients
- Broadcasts APVs to all connected clients in real-time
- Handles connection lifecycle (connect, disconnect, errors)

Biological Metaphor:
Like sensory neurons broadcasting threat signals to consciousness centers,
this system streams threat intelligence to monitoring dashboards.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, Set
from uuid import uuid4

from aiokafka import AIOKafkaConsumer
from fastapi import WebSocket
from pydantic import ValidationError

from services.maximus_oraculo.models.apv import APV


logger = logging.getLogger(__name__)


@dataclass
class WebSocketConnection:
    """
    Represents an active WebSocket connection.
    
    Attributes:
        connection_id: Unique identifier for this connection
        websocket: FastAPI WebSocket instance
        connected_at: Timestamp when connection established
        messages_sent: Count of messages broadcast to this connection
    """
    
    connection_id: str
    websocket: WebSocket
    connected_at: datetime = field(default_factory=datetime.utcnow)
    messages_sent: int = 0


@dataclass
class StreamMessage:
    """
    Message envelope for WebSocket streaming.
    
    Supports multiple message types:
    - apv: New APV detected
    - patch: Remediation patch applied
    - metrics: System metrics snapshot
    - heartbeat: Keep-alive ping
    """
    
    type: str  # "apv" | "patch" | "metrics" | "heartbeat"
    timestamp: str
    payload: Dict


class APVStreamManager:
    """
    Manages WebSocket APV streaming to frontend clients.
    
    Responsibilities:
    1. Maintain pool of active WebSocket connections
    2. Subscribe to Kafka APV topic
    3. Broadcast APVs to all connected clients
    4. Handle connection errors and cleanup
    5. Provide metrics on streaming status
    
    Usage:
        manager = APVStreamManager(kafka_bootstrap_servers="localhost:9092")
        await manager.start()
        
        # In WebSocket endpoint
        connection_id = await manager.connect(websocket)
        # ... keep connection alive ...
        await manager.disconnect(connection_id)
    """
    
    def __init__(
        self,
        kafka_bootstrap_servers: str = "localhost:9092",
        kafka_topic: str = "maximus.adaptive-immunity.apv",
        kafka_group_id: str = "apv-stream-manager",
    ) -> None:
        """
        Initialize APV Stream Manager.
        
        Args:
            kafka_bootstrap_servers: Kafka broker addresses
            kafka_topic: Topic to subscribe for APVs
            kafka_group_id: Consumer group ID
        """
        self._kafka_bootstrap_servers = kafka_bootstrap_servers
        self._kafka_topic = kafka_topic
        self._kafka_group_id = kafka_group_id
        
        # Connection pool: connection_id -> WebSocketConnection
        self._connections: Dict[str, WebSocketConnection] = {}
        
        # Kafka consumer
        self._kafka_consumer: Optional[AIOKafkaConsumer] = None
        
        # Background tasks
        self._consumer_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        
        # Metrics
        self._total_messages_broadcast: int = 0
        self._started_at: Optional[datetime] = None
        self._is_running: bool = False
        
        logger.info(
            f"APVStreamManager initialized - "
            f"Kafka: {kafka_bootstrap_servers}, Topic: {kafka_topic}"
        )
    
    async def start(self) -> None:
        """
        Start the stream manager.
        
        Initializes:
        - Kafka consumer connection
        - Background consumer task
        - Heartbeat task for keep-alive
        
        Raises:
            RuntimeError: If already running
        """
        if self._is_running:
            logger.warning("APVStreamManager already running")
            return
        
        logger.info("Starting APVStreamManager...")
        
        # Initialize Kafka consumer
        self._kafka_consumer = AIOKafkaConsumer(
            self._kafka_topic,
            bootstrap_servers=self._kafka_bootstrap_servers,
            group_id=self._kafka_group_id,
            value_deserializer=lambda m: m.decode('utf-8'),
            auto_offset_reset='latest',  # Only new messages
            enable_auto_commit=True,
        )
        
        await self._kafka_consumer.start()
        logger.info(f"Kafka consumer started - subscribed to {self._kafka_topic}")
        
        # Start background tasks
        self._consumer_task = asyncio.create_task(self._consume_kafka_messages())
        self._heartbeat_task = asyncio.create_task(self._send_heartbeats())
        
        self._started_at = datetime.utcnow()
        self._is_running = True
        
        logger.info("APVStreamManager started successfully")
    
    async def stop(self) -> None:
        """
        Stop the stream manager gracefully.
        
        Steps:
        1. Cancel background tasks
        2. Close all active WebSocket connections
        3. Stop Kafka consumer
        """
        if not self._is_running:
            return
        
        logger.info("Stopping APVStreamManager...")
        
        # Cancel background tasks
        if self._consumer_task:
            self._consumer_task.cancel()
            try:
                await self._consumer_task
            except asyncio.CancelledError:
                pass
        
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        
        # Close all connections
        connection_ids = list(self._connections.keys())
        for conn_id in connection_ids:
            await self.disconnect(conn_id, reason="Server shutting down")
        
        # Stop Kafka consumer
        if self._kafka_consumer:
            await self._kafka_consumer.stop()
            logger.info("Kafka consumer stopped")
        
        self._is_running = False
        logger.info("APVStreamManager stopped")
    
    async def connect(self, websocket: WebSocket) -> str:
        """
        Register a new WebSocket connection.
        
        Args:
            websocket: FastAPI WebSocket instance
            
        Returns:
            connection_id: Unique identifier for this connection
        """
        connection_id = str(uuid4())
        
        connection = WebSocketConnection(
            connection_id=connection_id,
            websocket=websocket,
        )
        
        self._connections[connection_id] = connection
        
        logger.info(
            f"WebSocket connected - ID: {connection_id}, "
            f"Total connections: {len(self._connections)}"
        )
        
        # Send welcome message
        await self._send_to_connection(
            connection_id,
            StreamMessage(
                type="heartbeat",
                timestamp=datetime.utcnow().isoformat(),
                payload={
                    "status": "connected",
                    "connection_id": connection_id,
                    "message": "APV stream active",
                },
            ),
        )
        
        return connection_id
    
    async def disconnect(
        self,
        connection_id: str,
        reason: str = "Client disconnected",
    ) -> None:
        """
        Unregister a WebSocket connection.
        
        Args:
            connection_id: Unique connection identifier
            reason: Reason for disconnection (for logging)
        """
        connection = self._connections.pop(connection_id, None)
        
        if not connection:
            logger.warning(f"Connection {connection_id} not found for disconnect")
            return
        
        try:
            await connection.websocket.close()
        except Exception as e:
            logger.warning(f"Error closing WebSocket {connection_id}: {e}")
        
        logger.info(
            f"WebSocket disconnected - ID: {connection_id}, Reason: {reason}, "
            f"Messages sent: {connection.messages_sent}, "
            f"Remaining connections: {len(self._connections)}"
        )
    
    async def broadcast_apv(self, apv: APV) -> None:
        """
        Broadcast an APV to all connected clients.
        
        Args:
            apv: APV to broadcast
        """
        if not self._connections:
            logger.debug("No active connections - skipping broadcast")
            return
        
        message = StreamMessage(
            type="apv",
            timestamp=datetime.utcnow().isoformat(),
            payload=apv.model_dump(mode="json"),
        )
        
        logger.info(
            f"Broadcasting APV {apv.cve_id} to {len(self._connections)} clients"
        )
        
        # Broadcast to all connections
        failed_connections: Set[str] = set()
        
        for connection_id in self._connections:
            success = await self._send_to_connection(connection_id, message)
            if not success:
                failed_connections.add(connection_id)
        
        # Clean up failed connections
        for conn_id in failed_connections:
            await self.disconnect(conn_id, reason="Send failed")
        
        self._total_messages_broadcast += 1
    
    async def _consume_kafka_messages(self) -> None:
        """
        Background task: Consume APVs from Kafka and broadcast.
        
        Runs continuously until cancelled.
        """
        logger.info("Kafka consumer task started")
        
        try:
            async for message in self._kafka_consumer:  # type: ignore
                try:
                    # Deserialize APV
                    apv_data = json.loads(message.value)
                    apv = APV(**apv_data)
                    
                    # Broadcast to all connections
                    await self.broadcast_apv(apv)
                    
                except ValidationError as e:
                    logger.error(f"Invalid APV message from Kafka: {e}")
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON from Kafka: {e}")
                except Exception as e:
                    logger.error(f"Error processing Kafka message: {e}", exc_info=True)
        
        except asyncio.CancelledError:
            logger.info("Kafka consumer task cancelled")
            raise
        except Exception as e:
            logger.error(f"Fatal error in Kafka consumer: {e}", exc_info=True)
    
    async def _send_heartbeats(self) -> None:
        """
        Background task: Send periodic heartbeats to all connections.
        
        Sends every 30 seconds to keep connections alive.
        """
        logger.info("Heartbeat task started")
        
        try:
            while True:
                await asyncio.sleep(30)
                
                if not self._connections:
                    continue
                
                message = StreamMessage(
                    type="heartbeat",
                    timestamp=datetime.utcnow().isoformat(),
                    payload={
                        "status": "alive",
                        "active_connections": len(self._connections),
                    },
                )
                
                # Send to all connections
                failed_connections: Set[str] = set()
                
                for connection_id in self._connections:
                    success = await self._send_to_connection(connection_id, message)
                    if not success:
                        failed_connections.add(connection_id)
                
                # Clean up failed connections
                for conn_id in failed_connections:
                    await self.disconnect(conn_id, reason="Heartbeat failed")
        
        except asyncio.CancelledError:
            logger.info("Heartbeat task cancelled")
            raise
    
    async def _send_to_connection(
        self,
        connection_id: str,
        message: StreamMessage,
    ) -> bool:
        """
        Send a message to a specific connection.
        
        Args:
            connection_id: Target connection
            message: Message to send
            
        Returns:
            True if successful, False if failed
        """
        connection = self._connections.get(connection_id)
        
        if not connection:
            return False
        
        try:
            # Serialize message to JSON
            message_json = json.dumps({
                "type": message.type,
                "timestamp": message.timestamp,
                "payload": message.payload,
            })
            
            # Send via WebSocket
            await connection.websocket.send_text(message_json)
            
            connection.messages_sent += 1
            return True
        
        except Exception as e:
            logger.error(
                f"Error sending to connection {connection_id}: {e}",
                exc_info=True,
            )
            return False
    
    def get_metrics(self) -> Dict:
        """
        Get current streaming metrics.
        
        Returns:
            Dict with metrics:
            - active_connections: Number of connected clients
            - total_messages_broadcast: Total APVs broadcast
            - uptime_seconds: Time since start
            - is_running: Service status
        """
        uptime_seconds = 0.0
        if self._started_at:
            uptime_seconds = (datetime.utcnow() - self._started_at).total_seconds()
        
        return {
            "active_connections": len(self._connections),
            "total_messages_broadcast": self._total_messages_broadcast,
            "uptime_seconds": uptime_seconds,
            "is_running": self._is_running,
            "kafka_topic": self._kafka_topic,
        }
