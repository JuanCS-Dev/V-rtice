"""WebSocket Routes - PRODUCTION-READY

WebSocket endpoint for real-time event streaming.

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

import logging
from typing import Optional, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from api.core_integration import EventBridge

logger = logging.getLogger(__name__)

router = APIRouter()

# EventBridge instance (initialized on startup)
_event_bridge: Optional[EventBridge] = None


def get_event_bridge() -> EventBridge:
    """Get EventBridge instance."""
    global _event_bridge
    if _event_bridge is None:
        _event_bridge = EventBridge()
    return _event_bridge


@router.websocket("/ws/events")
async def websocket_events_endpoint(
    websocket: WebSocket,
    subscriptions: Optional[str] = Query(
        None,
        description="Comma-separated event types to subscribe to (e.g., 'cytokine,hormone')",
    ),
):
    """
    WebSocket endpoint for real-time event streaming.

    Clients can subscribe to specific event types or receive all events.

    Available event types:
    - cytokine: Cytokine signaling events (from Kafka)
    - hormone: Hormone signaling events (from Redis)
    - agent_state: Agent state changes
    - threat_detection: Threat detection events
    - clone_creation: Clone creation events
    - homeostatic_state: Homeostatic state changes
    - system_health: System health updates

    Query Parameters:
        subscriptions: Comma-separated list of event types (default: all)

    Example:
        ws://localhost:8000/api/v1/ws/events?subscriptions=cytokine,threat_detection
    """
    bridge = get_event_bridge()

    # Parse subscriptions
    subscription_set: Optional[Set[str]] = None
    if subscriptions:
        subscription_set = set(sub.strip() for sub in subscriptions.split(",") if sub.strip())

    # Connect client
    await bridge.connect(websocket, subscriptions=subscription_set)

    try:
        # Keep connection alive and handle client messages
        while True:
            # Receive text to keep connection alive
            # Client can send subscription updates here
            data = await websocket.receive_text()

            # Parse client message (optional subscription updates)
            if data.startswith("subscribe:"):
                # Update subscriptions: "subscribe:cytokine,hormone"
                new_subs = data.replace("subscribe:", "").split(",")
                new_subscription_set = set(sub.strip() for sub in new_subs if sub.strip())
                await bridge.update_subscriptions(websocket, new_subscription_set)

                # Send confirmation
                await websocket.send_json({
                    "event": "subscription_updated",
                    "data": {
                        "subscriptions": list(new_subscription_set),
                        "message": "Subscriptions updated successfully",
                    },
                })

    except WebSocketDisconnect:
        # Client disconnected
        await bridge.disconnect(websocket)
        logger.info("WebSocket client disconnected")

    except Exception as e:
        # Error occurred
        logger.error(f"WebSocket error: {e}", exc_info=True)
        await bridge.disconnect(websocket)
