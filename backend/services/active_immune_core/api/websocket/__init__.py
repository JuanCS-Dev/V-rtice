"""WebSocket Module - PRODUCTION-READY

Real-time communication via WebSocket for Active Immune Core system.

Features:
- Connection management
- Event broadcasting
- Room/channel support
- Automatic reconnection support
- Message filtering

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

from . import broadcaster
from .connection_manager import ConnectionManager
from .events import WSEvent, WSEventType, WSMessage, WSResponse
from .router import get_connection_manager, router

__all__ = [
    "ConnectionManager",
    "WSEvent",
    "WSEventType",
    "WSMessage",
    "WSResponse",
    "router",
    "get_connection_manager",
    "broadcaster",
]
