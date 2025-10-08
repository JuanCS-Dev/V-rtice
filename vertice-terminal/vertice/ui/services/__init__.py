"""
UI Services for Vértice TUI
Backend integration and real-time communication
"""

from .event_stream import EventStreamClient
from .context_manager import TUIContextManager

__all__ = [
    "EventStreamClient",
    "TUIContextManager",
]
