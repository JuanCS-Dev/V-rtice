"""
PendingPanel Component - Pending Decisions List

Scrollable panel displaying all pending decisions awaiting human approval.
Reactively updates when new decisions arrive via SSE stream.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from textual.containers import ScrollableContainer, VerticalScroll
from textual.widgets import Static, Label
from textual.app import ComposeResult
from textual.reactive import reactive
from typing import List, Dict
from .event_card import EventCard


class PendingPanel(VerticalScroll):
    """
    Panel for pending decisions awaiting approval.

    Displays a scrollable list of EventCard widgets, sorted by
    priority (risk_level: critical > high > medium > low).

    Attributes:
        pending_events: Reactive list of pending decision dicts
        count: Number of pending decisions
    """

    DEFAULT_CSS = """
    PendingPanel {
        border: solid $accent;
        height: 100%;
        width: 1fr;
    }

    PendingPanel .empty-state {
        dock: top;
        content-align: center middle;
        height: 100%;
        color: $text-muted;
    }

    PendingPanel .panel-stats {
        dock: top;
        height: 3;
        background: $panel;
        padding: 1;
        border-bottom: solid $primary;
    }
    """

    # Reactive attributes
    pending_events: reactive[List[Dict]] = reactive([], recompose=True)

    def __init__(self, **kwargs):
        """Initialize PendingPanel."""
        super().__init__(**kwargs)
        self.border_title = "⏳ PENDING APPROVAL"

    def compose(self) -> ComposeResult:
        """Compose panel content."""
        # Stats bar
        count = len(self.pending_events)
        critical_count = sum(1 for e in self.pending_events if e.get("risk_level", "").lower() == "critical")
        high_count = sum(1 for e in self.pending_events if e.get("risk_level", "").lower() == "high")

        stats_text = f"Total: [bold]{count}[/bold]  |  🔴 Critical: {critical_count}  |  🟡 High: {high_count}"
        yield Static(stats_text, classes="panel-stats")

        # Event cards or empty state
        if not self.pending_events:
            yield Label(
                "[dim italic]No pending decisions\n\nWaiting for events from MAXIMUS...[/dim italic]",
                classes="empty-state",
            )
        else:
            # Sort by risk level priority
            risk_priority = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            sorted_events = sorted(
                self.pending_events,
                key=lambda e: risk_priority.get(e.get("risk_level", "medium").lower(), 4),
            )

            for event in sorted_events:
                yield EventCard(event, classes="event-card")

    def add_event(self, event: Dict) -> None:
        """
        Add a new pending event.

        Args:
            event: Decision event dictionary
        """
        # Avoid duplicates
        if not any(e.get("decision_id") == event.get("decision_id") for e in self.pending_events):
            self.pending_events = [*self.pending_events, event]

    def remove_event(self, decision_id: str) -> None:
        """
        Remove an event by decision_id.

        Args:
            decision_id: Decision identifier to remove
        """
        self.pending_events = [
            e for e in self.pending_events if e.get("decision_id") != decision_id
        ]

    def clear_events(self) -> None:
        """Clear all pending events."""
        self.pending_events = []

    @property
    def count(self) -> int:
        """Get count of pending events."""
        return len(self.pending_events)
