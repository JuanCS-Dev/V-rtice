"""
HistoryPanel Component - Resolved Decisions History

Panel displaying recently resolved decisions with their outcomes.
Provides audit trail and metrics for operator review.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from textual.containers import VerticalScroll
from textual.widgets import Static, Label
from textual.app import ComposeResult
from textual.reactive import reactive
from typing import List, Dict
from datetime import datetime


class HistoryPanel(VerticalScroll):
    """
    Panel for resolved decision history.

    Displays a chronological list of resolved decisions with:
    - Final status (approved/rejected/escalated)
    - Operator who handled it
    - Resolution time
    - Limited to last 50 decisions

    Attributes:
        history_events: Reactive list of resolved decision dicts
        max_history: Maximum number of entries to keep (default 50)
    """

    DEFAULT_CSS = """
    HistoryPanel {
        border: solid $primary;
        height: 100%;
        width: 1fr;
    }

    HistoryPanel .empty-state {
        content-align: center middle;
        height: 100%;
        color: $text-muted;
    }

    HistoryPanel .panel-stats {
        dock: top;
        height: 3;
        background: $panel;
        padding: 1;
        border-bottom: solid $primary;
    }

    HistoryPanel .history-item {
        padding: 1;
        margin: 1 0;
        border-left: thick $primary;
        height: auto;
    }

    HistoryPanel .history-item.approved {
        border-left: thick $success;
        background: $success 10%;
    }

    HistoryPanel .history-item.rejected {
        border-left: thick $error;
        background: $error 10%;
    }

    HistoryPanel .history-item.escalated {
        border-left: thick $warning;
        background: $warning 10%;
    }
    """

    # Reactive attributes
    history_events: reactive[List[Dict]] = reactive([], recompose=True)
    max_history: int = 50

    def __init__(self, **kwargs):
        """Initialize HistoryPanel."""
        super().__init__(**kwargs)
        self.border_title = "📜 HISTORY"

    def compose(self) -> ComposeResult:
        """Compose panel content."""
        # Stats bar
        count = len(self.history_events)
        approved = sum(1 for e in self.history_events if e.get("status") == "approved")
        rejected = sum(1 for e in self.history_events if e.get("status") == "rejected")
        escalated = sum(1 for e in self.history_events if e.get("status") == "escalated")

        stats_text = f"Total: [bold]{count}[/bold]  |  ✓ {approved}  |  ✗ {rejected}  |  ⬆ {escalated}"
        yield Static(stats_text, classes="panel-stats")

        # History items or empty state
        if not self.history_events:
            yield Label(
                "[dim italic]No history yet\n\nResolved decisions will appear here[/dim italic]",
                classes="empty-state",
            )
        else:
            # Show most recent first
            for event in reversed(self.history_events):
                yield self._create_history_item(event)

    def _create_history_item(self, event: Dict) -> Static:
        """
        Create a history item widget.

        Args:
            event: Resolved decision event

        Returns:
            Static widget with history item content
        """
        decision_id = event.get("decision_id", "unknown")
        status = event.get("status", "unknown")
        action_type = event.get("action_type", "unknown").replace("_", " ").title()
        target = event.get("target", "N/A")
        operator = event.get("operator_id", "system")
        resolved_at = event.get("resolved_at", "")

        # Format timestamp
        try:
            dt = datetime.fromisoformat(resolved_at.replace("Z", "+00:00"))
            time_str = dt.strftime("%H:%M:%S")
        except (ValueError, AttributeError):
            time_str = "Unknown"

        # Status symbols and colors
        status_icons = {
            "approved": "✓",
            "rejected": "✗",
            "escalated": "⬆",
        }
        icon = status_icons.get(status, "?")

        content = f"""[bold]{icon} {status.upper()}[/bold]  |  [dim]{time_str}[/dim]
[bold]Action:[/bold] {action_type}  →  {target}
[dim]By: {operator}[/dim]"""

        widget = Static(content, classes=f"history-item {status}")
        return widget

    def add_resolved(self, event: Dict) -> None:
        """
        Add a resolved decision to history.

        Args:
            event: Resolved decision event dict
        """
        # Add timestamp if not present
        if "resolved_at" not in event:
            event["resolved_at"] = datetime.now().isoformat()

        # Add to history
        new_history = [*self.history_events, event]

        # Limit to max_history
        if len(new_history) > self.max_history:
            new_history = new_history[-self.max_history :]

        self.history_events = new_history

    def clear_history(self) -> None:
        """Clear all history."""
        self.history_events = []

    @property
    def count(self) -> int:
        """Get count of history items."""
        return len(self.history_events)
