"""
Governance Workspace Components

Reusable Textual widgets for the Governance Workspace.

Components:
- EventCard: Individual decision card with actions
- PendingPanel: Scrollable list of pending decisions
- ActivePanel: Currently reviewing decision
- HistoryPanel: Recently resolved decisions
"""

from .event_card import EventCard
from .pending_panel import PendingPanel
from .active_panel import ActivePanel
from .history_panel import HistoryPanel

__all__ = [
    "EventCard",
    "PendingPanel",
    "ActivePanel",
    "HistoryPanel",
]
