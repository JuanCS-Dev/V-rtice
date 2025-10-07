"""
GovernanceWorkspace - Main TUI Screen for HITL Decision Review

Real-time workspace for reviewing AI ethical governance decisions.
Integrates SSE streaming, three-panel layout, and operator actions.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Header, Footer, Button, Static
from textual.screen import Screen
from textual import on
from typing import Optional, Dict
import asyncio
import logging

from .components import EventCard, PendingPanel, ActivePanel, HistoryPanel
from .workspace_manager import WorkspaceManager

logger = logging.getLogger(__name__)


class GovernanceWorkspace(Screen):
    """
    Main Governance Workspace screen.

    Features:
    - Three-panel reactive layout (Pending | Active | History)
    - Real-time SSE event streaming
    - Operator actions (approve/reject/escalate)
    - SLA monitoring with visual warnings
    - Decision audit trail

    Bindings:
        q: Quit workspace
        r: Refresh stats
        c: Clear history
        escape: Back to main menu
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("escape", "dismiss", "Back"),
        ("r", "refresh_stats", "Refresh"),
        ("c", "clear_history", "Clear History"),
    ]

    CSS = """
    GovernanceWorkspace {
        background: $surface;
    }

    #main-container {
        height: 100%;
        layout: horizontal;
    }

    #control-bar {
        dock: bottom;
        height: 3;
        background: $panel;
        padding: 0 2;
        border-top: solid $primary;
    }

    #control-bar Horizontal {
        height: 100%;
        align: center middle;
    }

    #status-text {
        width: 1fr;
        content-align: left middle;
    }

    .control-btn {
        margin: 0 1;
        min-width: 14;
    }
    """

    def __init__(
        self,
        operator_id: str,
        session_id: str,
        backend_url: str = "http://localhost:8000",
        **kwargs,
    ):
        """
        Initialize GovernanceWorkspace.

        Args:
            operator_id: Operator identifier
            session_id: Active session ID from backend
            backend_url: MAXIMUS backend base URL
        """
        super().__init__(**kwargs)
        self.operator_id = operator_id
        self.session_id = session_id
        self.backend_url = backend_url

        # Components (will be set in compose)
        self.pending_panel: Optional[PendingPanel] = None
        self.active_panel: Optional[ActivePanel] = None
        self.history_panel: Optional[HistoryPanel] = None

        # Workspace Manager
        self.manager = WorkspaceManager(
            backend_url=backend_url,
            operator_id=operator_id,
            session_id=session_id,
            on_event=self._handle_sse_event,
            on_error=self._handle_error,
        )

        # State
        self.is_connected = False
        self.timer_task: Optional[asyncio.Task] = None

    def compose(self) -> ComposeResult:
        """Compose the workspace layout."""
        yield Header(show_clock=True)

        # Main three-panel layout
        with Container(id="main-container"):
            self.pending_panel = PendingPanel(id="pending-panel")
            yield self.pending_panel

            self.active_panel = ActivePanel(id="active-panel")
            yield self.active_panel

            self.history_panel = HistoryPanel(id="history-panel")
            yield self.history_panel

        # Control bar
        with Container(id="control-bar"):
            with Horizontal():
                yield Static(
                    f"[bold]Operator:[/bold] {self.operator_id}  |  [dim]Connecting...[/dim]",
                    id="status-text",
                )
                yield Button("🔄 Refresh", variant="primary", id="refresh-btn", classes="control-btn")
                yield Button("🗑️ Clear", variant="default", id="clear-btn", classes="control-btn")

        yield Footer()

    async def on_mount(self) -> None:
        """Called when screen is mounted."""
        logger.info(f"GovernanceWorkspace mounted for operator {self.operator_id}")

        # Start SSE stream via manager
        try:
            await self.manager.start_stream()
            self._update_status("Connected to MAXIMUS", connected=True)
        except Exception as e:
            logger.error(f"Failed to start stream: {e}")
            self._update_status(f"Connection failed: {e}", connected=False)
            self.notify(f"Failed to connect: {e}", severity="error", timeout=10)

        # Start SLA timer update task
        self.timer_task = asyncio.create_task(self._update_timers())

    async def on_unmount(self) -> None:
        """Called when screen is unmounted."""
        logger.info("GovernanceWorkspace unmounting - cleaning up")

        # Stop manager and stream
        await self.manager.close()

        # Cancel timer task
        if self.timer_task and not self.timer_task.done():
            self.timer_task.cancel()
            try:
                await self.timer_task
            except asyncio.CancelledError:
                pass

    # ========================================================================
    # Button Actions
    # ========================================================================

    @on(Button.Pressed, "#refresh-btn")
    def action_refresh_stats(self) -> None:
        """Refresh statistics and panels."""
        logger.info("Refreshing stats")
        self.notify("Stats refreshed", severity="information")

    @on(Button.Pressed, "#clear-btn")
    def action_clear_history(self) -> None:
        """Clear history panel."""
        if self.history_panel:
            self.history_panel.clear_history()
        self.notify("History cleared", severity="information")

    # ========================================================================
    # Decision Actions (approve/reject/escalate)
    # ========================================================================

    @on(Button.Pressed, selector=".action-btn")
    async def handle_decision_action(self, event: Button.Pressed) -> None:
        """
        Handle decision action button presses.

        Button IDs format: "{action}-{decision_id}"
        """
        button_id = event.button.id
        if not button_id:
            return

        # Parse button ID
        parts = button_id.split("-", 1)
        if len(parts) != 2:
            return

        action, decision_id = parts

        logger.info(f"Decision action: {action} for {decision_id}")

        # Execute action (will be implemented in FASE 2.3 with WorkspaceManager)
        if action == "approve":
            await self._approve_decision(decision_id)
        elif action == "reject":
            await self._reject_decision(decision_id)
        elif action == "escalate":
            await self._escalate_decision(decision_id)

    async def _approve_decision(self, decision_id: str) -> None:
        """Approve a decision."""
        self.notify(f"✓ Approving {decision_id}...", severity="information")
        try:
            result = await self.manager.approve_decision(decision_id, comment="Approved via TUI")
            self.resolve_event(decision_id, "approved")
            self.notify(f"✓ Decision {decision_id} approved", severity="success")
        except Exception as e:
            logger.error(f"Approve failed: {e}")
            self.notify(f"Approve failed: {e}", severity="error", timeout=10)

    async def _reject_decision(self, decision_id: str) -> None:
        """Reject a decision."""
        self.notify(f"✗ Rejecting {decision_id}...", severity="warning")
        try:
            result = await self.manager.reject_decision(
                decision_id, reason="Rejected by operator via TUI", comment="Manual review"
            )
            self.resolve_event(decision_id, "rejected")
            self.notify(f"✗ Decision {decision_id} rejected", severity="warning")
        except Exception as e:
            logger.error(f"Reject failed: {e}")
            self.notify(f"Reject failed: {e}", severity="error", timeout=10)

    async def _escalate_decision(self, decision_id: str) -> None:
        """Escalate a decision."""
        self.notify(f"⬆ Escalating {decision_id}...", severity="warning")
        try:
            result = await self.manager.escalate_decision(
                decision_id,
                escalation_reason="Requires senior approval",
                escalation_target="senior_analyst",
                comment="Escalated via TUI",
            )
            self.resolve_event(decision_id, "escalated")
            self.notify(f"⬆ Decision {decision_id} escalated", severity="warning")
        except Exception as e:
            logger.error(f"Escalate failed: {e}")
            self.notify(f"Escalate failed: {e}", severity="error", timeout=10)

    # ========================================================================
    # Event Handling
    # ========================================================================

    def add_pending_event(self, event: Dict) -> None:
        """
        Add a new pending event from SSE stream.

        Args:
            event: Decision event dictionary
        """
        if self.pending_panel:
            self.pending_panel.add_event(event)

    def set_active_event(self, event: Dict) -> None:
        """
        Set the active event for review.

        Args:
            event: Decision event dictionary
        """
        if self.active_panel:
            self.active_panel.set_active(event)

    def resolve_event(self, decision_id: str, status: str) -> None:
        """
        Mark an event as resolved.

        Args:
            decision_id: Decision ID
            status: Resolution status (approved/rejected/escalated)
        """
        # Remove from pending
        if self.pending_panel:
            # Find event before removing
            event = next(
                (e for e in self.pending_panel.pending_events if e.get("decision_id") == decision_id),
                None,
            )
            self.pending_panel.remove_event(decision_id)

            # Add to history
            if event and self.history_panel:
                event["status"] = status
                self.history_panel.add_resolved(event)

        # Clear active if it's the current one
        if self.active_panel and self.active_panel.active_event:
            if self.active_panel.active_event.get("decision_id") == decision_id:
                self.active_panel.clear_active()

    # ========================================================================
    # Timer Updates
    # ========================================================================

    async def _update_timers(self) -> None:
        """Background task to update SLA timers."""
        while True:
            try:
                await asyncio.sleep(1)  # Update every second
                if self.active_panel:
                    self.active_panel.update_timer()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Timer update error: {e}", exc_info=True)

    # ========================================================================
    # Status Management
    # ========================================================================

    def _update_status(self, message: str, connected: bool = True) -> None:
        """
        Update status bar.

        Args:
            message: Status message
            connected: Connection status
        """
        self.is_connected = connected
        status_text = self.query_one("#status-text", Static)

        icon = "🟢" if connected else "🔴"
        status_text.update(f"[bold]Operator:[/bold] {self.operator_id}  |  {icon} {message}")

    # ========================================================================
    # SSE Event Handlers
    # ========================================================================

    def _handle_sse_event(self, event: Dict) -> None:
        """
        Handle incoming SSE event.

        Args:
            event: Parsed SSE event dict
        """
        event_type = event.get("event_type")
        data = event.get("data", {})

        logger.info(f"Handling SSE event: {event_type}")

        if event_type == "connected":
            # Connection confirmation
            self._update_status("Connected - receiving events", connected=True)
            self.notify("Connected to Governance Stream", severity="information")

        elif event_type == "decision_pending":
            # New pending decision
            decision_data = data.copy()
            # Ensure required fields
            if "decision_id" not in decision_data:
                logger.warning("Decision event missing decision_id")
                return

            self.add_pending_event(decision_data)
            self.notify(
                f"New decision: {decision_data.get('action_type', 'unknown')}",
                severity="information",
            )

        elif event_type == "decision_resolved":
            # Decision was resolved (possibly by another operator)
            decision_id = data.get("decision_id")
            status = data.get("status", "unknown")
            if decision_id:
                self.resolve_event(decision_id, status)
                self.notify(f"Decision {decision_id} resolved: {status}", severity="information")

        elif event_type == "sla_warning":
            # SLA warning
            decision_id = data.get("decision_id")
            time_remaining = data.get("time_remaining_seconds", 0)
            self.notify(
                f"⚠ SLA WARNING: {decision_id} ({time_remaining}s remaining)",
                severity="warning",
                timeout=10,
            )

        elif event_type == "sla_violation":
            # SLA violated
            decision_id = data.get("decision_id")
            self.notify(
                f"🚨 SLA VIOLATED: {decision_id}",
                severity="error",
                timeout=15,
            )

        elif event_type == "heartbeat":
            # Heartbeat - connection alive
            pass

        else:
            logger.warning(f"Unknown event type: {event_type}")

    def _handle_error(self, error: Exception) -> None:
        """
        Handle SSE stream error.

        Args:
            error: Exception that occurred
        """
        logger.error(f"Stream error: {error}", exc_info=True)
        self._update_status(f"Stream error: {error}", connected=False)
        self.notify(f"Stream error: {error}", severity="error", timeout=10)
