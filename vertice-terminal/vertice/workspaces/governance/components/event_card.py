"""
EventCard Component - Decision Card Widget

Visual card component for displaying a single HITL decision with
metadata, risk indicators, and action buttons.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from textual.containers import Container, Horizontal
from textual.widgets import Button, Label, Static
from textual.app import ComposeResult
from typing import Dict, Optional
from datetime import datetime


class EventCard(Container):
    """
    Card widget for a single governance decision event.

    Displays:
    - Risk level with color coding
    - Action type and target
    - Ethical concern description
    - Recommended action
    - Timestamp
    - Approve/Reject/Escalate buttons

    Attributes:
        event_data: Decision event dictionary from SSE stream
        decision_id: Unique decision identifier
    """

    DEFAULT_CSS = """
    EventCard {
        height: auto;
        border: solid $primary;
        padding: 1;
        margin: 1 0;
    }

    EventCard.critical {
        border: heavy red;
    }

    EventCard.high {
        border: heavy yellow;
    }

    EventCard.medium {
        border: solid blue;
    }

    EventCard.low {
        border: solid green;
    }

    EventCard .event-content {
        height: auto;
        padding: 0 1;
    }

    EventCard .button-row {
        height: 3;
        align: center middle;
        padding: 1 0 0 0;
    }

    EventCard Button {
        min-width: 12;
        margin: 0 1;
    }
    """

    def __init__(self, event_data: Dict, **kwargs):
        """
        Initialize EventCard.

        Args:
            event_data: Decision event dictionary with keys:
                - decision_id: str
                - risk_level: str (critical/high/medium/low)
                - action_type: str
                - target: str
                - reasoning: str
                - recommended_action: str
                - created_at: str (ISO timestamp)
                - confidence: float
        """
        super().__init__(**kwargs)
        self.event_data = event_data
        self.decision_id = event_data.get("decision_id", "unknown")

        # Set CSS classes based on risk level
        risk_level = event_data.get("risk_level", "medium").lower()
        self.add_class(risk_level)

    def compose(self) -> ComposeResult:
        """Compose the card layout."""
        # Extract data
        risk_level = self.event_data.get("risk_level", "medium").upper()
        action_type = self.event_data.get("action_type", "unknown").replace("_", " ").title()
        target = self.event_data.get("target", "N/A")
        reasoning = self.event_data.get("reasoning", "No reasoning provided")
        recommended = self.event_data.get("recommended_action", "review")
        confidence = self.event_data.get("confidence", 0.0)
        created_at = self.event_data.get("created_at", "")

        # Format timestamp
        try:
            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            timestamp_str = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except (ValueError, AttributeError):
            timestamp_str = created_at[:19] if created_at else "Unknown"

        # Risk level colors
        risk_colors = {
            "CRITICAL": "red",
            "HIGH": "yellow",
            "MEDIUM": "blue",
            "LOW": "green",
        }
        risk_color = risk_colors.get(risk_level, "white")

        # Build content markup
        content = f"""[bold {risk_color}]⚠ {risk_level}: {action_type}[/bold {risk_color}]

[dim]🕒 {timestamp_str}[/dim]
[bold]🎯 Target:[/bold] {target}
[bold]🤖 Confidence:[/bold] {confidence:.2%}

[italic]💭 {reasoning}[/italic]

[bold cyan]→ Recommended:[/bold cyan] [bold]{recommended}[/bold]"""

        # Render content label
        yield Static(content, classes="event-content")

        # Action buttons
        yield Horizontal(
            Button("✓ Approve", variant="success", id=f"approve-{self.decision_id}", classes="action-btn"),
            Button("✗ Reject", variant="error", id=f"reject-{self.decision_id}", classes="action-btn"),
            Button("⬆ Escalate", variant="warning", id=f"escalate-{self.decision_id}", classes="action-btn"),
            classes="button-row",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        Handle button press events.

        Emits custom messages for parent to handle:
        - approve-{decision_id}
        - reject-{decision_id}
        - escalate-{decision_id}
        """
        # Button IDs are formatted as "{action}-{decision_id}"
        # The parent screen will handle via @on() decorators
        pass
