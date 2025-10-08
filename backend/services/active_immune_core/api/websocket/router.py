"""WebSocket Router - PRODUCTION-READY

WebSocket endpoints and message handlers.

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Dict

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status
from fastapi.responses import JSONResponse

from .connection_manager import ConnectionManager
from .events import WSEvent, WSEventType, WSMessage, WSResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# Global connection manager instance
connection_manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str = Query(None, description="Optional client identifier"),
) -> None:
    """
    WebSocket endpoint for real-time communication.

    Args:
        websocket: WebSocket connection
        client_id: Optional client identifier (auto-generated if not provided)

    Protocol:
        Client -> Server:
        {
            "action": "subscribe|unsubscribe|join|leave|ping",
            "data": {...},
            "room": "room_name"  // optional
        }

        Server -> Client:
        {
            "event_type": "...",
            "timestamp": "...",
            "data": {...},
            "source": "...",
            "room": "..."
        }
    """
    # Generate connection ID
    connection_id = client_id or f"ws_{uuid.uuid4().hex[:12]}"

    try:
        # Connect
        await connection_manager.connect(
            websocket,
            connection_id,
            metadata={
                "connected_at": datetime.utcnow().isoformat(),
                "client_id": client_id,
            },
        )

        # Message loop
        while True:
            # Receive message
            data = await websocket.receive_text()
            connection_manager.total_messages_received += 1

            try:
                message_dict = json.loads(data)
                message = WSMessage(**message_dict)

                # Handle message
                response = await handle_message(connection_id, message)

                # Send response
                await websocket.send_json(response.model_dump())

            except json.JSONDecodeError:
                error_response = WSResponse(
                    success=False,
                    message="Invalid JSON format",
                )
                await websocket.send_json(error_response.model_dump())

            except Exception as e:
                logger.error(
                    f"Error handling message from {connection_id}: {e}",
                    exc_info=True,
                )
                error_response = WSResponse(
                    success=False,
                    message=f"Error processing message: {str(e)}",
                )
                await websocket.send_json(error_response.model_dump())

    except WebSocketDisconnect:
        logger.info(f"Client {connection_id} disconnected normally")

    except Exception as e:
        logger.error(
            f"Unexpected error in WebSocket {connection_id}: {e}",
            exc_info=True,
        )

    finally:
        # Cleanup
        await connection_manager.disconnect(connection_id)


async def handle_message(connection_id: str, message: WSMessage) -> WSResponse:
    """
    Handle WebSocket message from client.

    Args:
        connection_id: Connection identifier
        message: Parsed WebSocket message

    Returns:
        Response to send back to client
    """
    action = message.action.lower()

    if action == "ping":
        return WSResponse(
            success=True,
            message="pong",
            data={"timestamp": datetime.utcnow().isoformat()},
        )

    elif action == "subscribe":
        # Subscribe to event types
        event_types_str = message.data.get("event_types", []) if message.data else []

        try:
            event_types = [WSEventType(et) for et in event_types_str]
            success = await connection_manager.subscribe(connection_id, event_types)

            if success:
                return WSResponse(
                    success=True,
                    message=f"Subscribed to {len(event_types)} event types",
                    data={"event_types": event_types_str},
                )
            else:
                return WSResponse(
                    success=False,
                    message="Failed to subscribe",
                )

        except ValueError as e:
            return WSResponse(
                success=False,
                message=f"Invalid event type: {str(e)}",
            )

    elif action == "unsubscribe":
        # Unsubscribe from event types
        event_types_str = message.data.get("event_types", []) if message.data else []

        try:
            event_types = [WSEventType(et) for et in event_types_str]
            success = await connection_manager.unsubscribe(connection_id, event_types)

            if success:
                return WSResponse(
                    success=True,
                    message=f"Unsubscribed from {len(event_types)} event types",
                    data={"event_types": event_types_str},
                )
            else:
                return WSResponse(
                    success=False,
                    message="Failed to unsubscribe",
                )

        except ValueError as e:
            return WSResponse(
                success=False,
                message=f"Invalid event type: {str(e)}",
            )

    elif action == "join":
        # Join room
        room = message.room
        if not room:
            return WSResponse(
                success=False,
                message="Room name is required",
            )

        success = await connection_manager.join_room(connection_id, room)

        if success:
            return WSResponse(
                success=True,
                message=f"Joined room '{room}'",
                data={"room": room},
            )
        else:
            return WSResponse(
                success=False,
                message=f"Failed to join room '{room}'",
            )

    elif action == "leave":
        # Leave room
        room = message.room
        if not room:
            return WSResponse(
                success=False,
                message="Room name is required",
            )

        success = await connection_manager.leave_room(connection_id, room)

        if success:
            return WSResponse(
                success=True,
                message=f"Left room '{room}'",
                data={"room": room},
            )
        else:
            return WSResponse(
                success=False,
                message=f"Failed to leave room '{room}'",
            )

    elif action == "info":
        # Get connection info
        info = connection_manager.get_connection_info(connection_id)

        if info:
            return WSResponse(
                success=True,
                message="Connection information",
                data=info,
            )
        else:
            return WSResponse(
                success=False,
                message="Connection not found",
            )

    else:
        return WSResponse(
            success=False,
            message=f"Unknown action: {action}",
            data={
                "available_actions": [
                    "ping",
                    "subscribe",
                    "unsubscribe",
                    "join",
                    "leave",
                    "info",
                ]
            },
        )


@router.get("/ws/stats")
async def get_websocket_stats() -> Dict:
    """
    Get WebSocket connection statistics.

    Returns:
        WebSocket statistics
    """
    return connection_manager.get_statistics()


@router.post("/ws/broadcast")
async def broadcast_event(
    event_type: str,
    data: Dict,
    room: str = Query(None, description="Optional room to broadcast to"),
) -> JSONResponse:
    """
    Broadcast event to WebSocket clients.

    Args:
        event_type: Type of event to broadcast
        data: Event data payload
        room: Optional room to broadcast to

    Returns:
        Broadcast result

    Note:
        This endpoint is for internal use (e.g., from other services)
        Consider adding authentication in production
    """
    try:
        event_type_enum = WSEventType(event_type)

        event = WSEvent(
            event_type=event_type_enum,
            data=data,
            source="api_broadcast",
            room=room,
        )

        sent_count = await connection_manager.broadcast(event, room=room)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "message": f"Event broadcast to {sent_count} connections",
                "sent_count": sent_count,
                "event_type": event_type,
                "room": room,
            },
        )

    except ValueError:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "message": f"Invalid event type: {event_type}",
                "available_types": [e.value for e in WSEventType],
            },
        )

    except Exception as e:
        logger.error(f"Error broadcasting event: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": f"Error broadcasting event: {str(e)}",
            },
        )


# Helper function to get connection manager (for use in other modules)
def get_connection_manager() -> ConnectionManager:
    """
    Get the global connection manager instance.

    Returns:
        ConnectionManager instance
    """
    return connection_manager
