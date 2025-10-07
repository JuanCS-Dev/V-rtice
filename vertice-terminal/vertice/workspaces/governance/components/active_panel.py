"""
ActivePanel Component - Currently Reviewing Decision

Panel displaying the decision currently under active review by the operator.
Shows expanded details and SLA countdown timer.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from textual.containers import Container, VerticalScroll
from textual.widgets import Static, Label
from textual.app import ComposeResult
from textual.reactive import reactive
from typing import Optional, Dict
from datetime import datetime, timezone
from .event_card import EventCard


class ActivePanel(VerticalScroll):
    """
    Panel for the decision currently being reviewed.

    Displays expanded decision details with:
    - Full reasoning and context
    - SLA countdown timer
    - Threat intelligence data
    - Action history

    Attributes:
        active_event: Currently active decision dict (None if empty)
        time_remaining: Seconds until SLA violation
    """

    DEFAULT_CSS = """
    ActivePanel {
        border: solid $success;
        height: 100%;
        width: 1fr;
    }

    ActivePanel .empty-state {
        content-align: center middle;
        height: 100%;
        color: $text-muted;
    }

    ActivePanel .sla-timer {
        dock: top;
        height: 3;
        background: $panel;
        padding: 1;
        border-bottom: solid $primary;
        content-align: center middle;
    }

    ActivePanel .sla-warning {
        background: $warning;
        color: $text;
    }

    ActivePanel .sla-critical {
        background: $error;
        color: $text;
    }

    ActivePanel .context-section {
        padding: 1;
        margin: 1 0;
        border: solid $primary;
    }
    """

    # Reactive attributes
    active_event: reactive[Optional[Dict]] = reactive(None, recompose=True)
    time_remaining: reactive[int] = reactive(0)

    def __init__(self, **kwargs):
        """Initialize ActivePanel."""
        super().__init__(**kwargs)
        self.border_title = "👀 ACTIVE REVIEW"

    def compose(self) -> ComposeResult:
        """Compose panel content."""
        if self.active_event is None:
            yield Label(
                "[dim italic]No decision selected\n\nClick on a pending decision to review[/dim italic]",
                classes="empty-state",
            )
            return

        # SLA Timer
        time_remaining = self.time_remaining
        timer_class = ""
        if time_remaining < 60:
            timer_class = "sla-critical"
            timer_text = f"⚠ SLA: [bold red]{time_remaining}s[/bold red] CRITICAL"
        elif time_remaining < 300:  # 5 minutes
            timer_class = "sla-warning"
            timer_text = f"⚠ SLA: [bold yellow]{time_remaining}s[/bold yellow]"
        else:
            timer_text = f"🕒 SLA: [bold green]{time_remaining}s[/bold green]"

        yield Static(timer_text, classes=f"sla-timer {timer_class}")

        # Main event card
        yield EventCard(self.active_event, classes="event-card")

        # Additional context sections
        context = self.active_event.get("context", {})
        threat_score = self.active_event.get("threat_score", 0.0)
        threat_type = self.active_event.get("threat_type", "unknown")

        # Threat Intelligence section
        threat_content = f"""[bold]🛡️ Threat Intelligence[/bold]

[bold]Score:[/bold] {threat_score:.2%}
[bold]Type:[/bold] {threat_type}
[bold]Context:[/bold] {context if isinstance(context, str) else str(context)}"""

        yield Static(threat_content, classes="context-section")

    def set_active(self, event: Dict) -> None:
        """
        Set the active decision for review.

        Args:
            event: Decision event dictionary
        """
        self.active_event = event
        self._update_sla_timer()

    def clear_active(self) -> None:
        """Clear active decision."""
        self.active_event = None
        self.time_remaining = 0

    def _update_sla_timer(self) -> None:
        """Update SLA timer from event deadline."""
        if self.active_event is None:
            self.time_remaining = 0
            return

        sla_deadline = self.active_event.get("sla_deadline")
        if not sla_deadline:
            self.time_remaining = 0
            return

        try:
            deadline_dt = datetime.fromisoformat(sla_deadline.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            delta = (deadline_dt - now).total_seconds()
            self.time_remaining = max(0, int(delta))
        except (ValueError, AttributeError):
            self.time_remaining = 0

    def update_timer(self) -> None:
        """Update timer (call periodically)."""
        if self.active_event:
            self._update_sla_timer()
            # Trigger recompose if timer state changed significantly
            if self.time_remaining in [60, 300]:  # Threshold crossings
                self.refresh(recompose=True)
