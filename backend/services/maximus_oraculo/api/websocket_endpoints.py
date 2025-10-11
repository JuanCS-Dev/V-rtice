"""
WebSocket endpoints for real-time APV streaming.

Provides WebSocket connection for frontend clients to receive
real-time APV (Ameaças Potenciais Verificadas) updates.

Endpoint:
    ws://localhost:8001/ws/adaptive-immunity

Message Format (JSON):
    {
        "type": "apv" | "patch" | "metrics" | "heartbeat",
        "timestamp": "ISO8601",
        "payload": { ... }
    }
"""

import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from websocket.apv_stream_manager import APVStreamManager


logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])

# Global stream manager instance (initialized in main.py)
_stream_manager: Optional[APVStreamManager] = None


def initialize_stream_manager(stream_manager: APVStreamManager) -> None:
    """
    Initialize the global stream manager.
    
    Called from main.py on application startup.
    
    Args:
        stream_manager: Initialized APVStreamManager instance
    """
    global _stream_manager
    _stream_manager = stream_manager
    logger.info("WebSocket endpoints initialized with stream manager")


@router.websocket("/ws/adaptive-immunity")
async def websocket_adaptive_immunity(
    websocket: WebSocket,
    token: Optional[str] = Query(None, description="Optional JWT token for auth"),
) -> None:
    """
    WebSocket endpoint for real-time APV streaming.
    
    Clients connect to receive:
    - Real-time APV notifications when new CVEs detected
    - Patch status updates
    - System metrics snapshots
    - Heartbeat keep-alive messages (every 30s)
    
    Args:
        websocket: FastAPI WebSocket connection
        token: Optional JWT token for authentication
    
    Example (JavaScript):
        const ws = new WebSocket('ws://localhost:8001/ws/adaptive-immunity');
        ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            if (message.type === 'apv') {
                console.log('New APV:', message.payload);
            }
        };
    """
    if not _stream_manager:
        logger.error("Stream manager not initialized")
        await websocket.close(code=1011, reason="Service unavailable")
        return
    
    # Accept connection
    await websocket.accept()
    logger.info(f"WebSocket connection accepted from {websocket.client}")
    
    # Register with stream manager
    connection_id = await _stream_manager.connect(websocket)
    
    try:
        # Keep connection alive
        # Stream manager handles message broadcasting via Kafka consumer
        while True:
            # Wait for any client messages (optional - can be used for control)
            message = await websocket.receive_text()
            logger.debug(f"Received message from {connection_id}: {message}")
            
            # TODO: Handle client control messages if needed
            # Example: {"action": "pause"}, {"action": "resume"}
    
    except WebSocketDisconnect:
        logger.info(f"Client {connection_id} disconnected normally")
    
    except Exception as e:
        logger.error(f"Error in WebSocket {connection_id}: {e}", exc_info=True)
    
    finally:
        # Cleanup
        await _stream_manager.disconnect(connection_id)


@router.get("/ws/status")
async def websocket_status() -> dict:
    """
    Get WebSocket stream manager status.
    
    Returns:
        Metrics including active connections, messages broadcast, uptime.
    """
    if not _stream_manager:
        return {
            "status": "unavailable",
            "message": "Stream manager not initialized",
        }
    
    return {
        "status": "operational",
        **_stream_manager.get_metrics(),
    }
