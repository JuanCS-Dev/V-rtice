"""
POC - Ethical Governance Workspace (Spike Técnico)

Validação de arquitetura TUI para Human-in-the-Loop (HITL).
Demonstra viabilidade de:
- Layout reativo 3-painéis (Pending | Active | History)
- SSE streaming em tempo real
- Estado distribuído e reativo
- Interação usuário (approve/reject)
- Performance e responsividade

Production-ready code - Regra de Ouro.
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, Button, Label
from textual.reactive import reactive
from textual import on
import httpx
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
import json
import logging
import signal
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EventCard(Container):
    """
    Card visual para um evento individual de governança.

    Exibe informações do evento com styling baseado em risk_level.
    """

    def __init__(self, event_data: Dict, **kwargs):
        super().__init__(**kwargs)
        self.event_data = event_data
        self.border_title = f"Event {event_data['id']}"

    def compose(self) -> ComposeResult:
        """Renderiza conteúdo do card."""
        risk_level = self.event_data.get("risk_level", "medium")
        risk_colors = {
            "critical": "red",
            "high": "yellow",
            "medium": "blue",
            "low": "green"
        }
        risk_color = risk_colors.get(risk_level, "white")

        action_type = self.event_data.get("action_type", "unknown").replace("_", " ").title()
        target = self.event_data.get("target", "N/A")
        concern = self.event_data.get("ethical_concern", "No concern specified")
        recommendation = self.event_data.get("recommended_action", "review")
        timestamp = self.event_data.get("timestamp", "")[:19]  # Trunca milliseconds

        content = f"""[bold {risk_color}]⚠ {risk_level.upper()}: {action_type}[/bold {risk_color}]

[dim]{timestamp}[/dim]
[bold]Target:[/bold] {target}

[italic]{concern}[/italic]

[bold cyan]→[/bold cyan] Recommended: {recommendation}"""

        yield Label(content)
        yield Horizontal(
            Button("✓ Approve", variant="success", id=f"approve-{self.event_data['id']}", classes="action-btn"),
            Button("✗ Reject", variant="error", id=f"reject-{self.event_data['id']}", classes="action-btn"),
            classes="button-row"
        )


class PendingPanel(ScrollableContainer):
    """
    Painel de eventos pendentes aguardando aprovação humana.
    Atualiza reativamente quando novos eventos chegam.
    """

    pending_events: reactive[List[Dict]] = reactive([], recompose=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.border_title = "⏳ PENDING APPROVAL"

    def compose(self) -> ComposeResult:
        """Renderiza eventos pendentes."""
        if not self.pending_events:
            yield Label("[dim]No pending events[/dim]", classes="empty-state")
        else:
            for event in self.pending_events:
                yield EventCard(event, classes="event-card")


class ActivePanel(Container):
    """
    Painel de ações ativas (aprovadas e em execução).
    """

    active_count: reactive[int] = reactive(0)
    recent_approvals: reactive[List[str]] = reactive([])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.border_title = "🔄 ACTIVE ACTIONS"

    def compose(self) -> ComposeResult:
        """Renderiza contador de ações ativas."""
        status_text = f"[bold green]⚡ {self.active_count} actions in progress[/bold green]"
        yield Label(status_text, id="active-status")

        if self.recent_approvals:
            yield Label("\n[bold]Recent Approvals:[/bold]")
            for approval_id in self.recent_approvals[-5:]:  # Last 5
                yield Label(f"[dim]✓[/dim] {approval_id}")


class HistoryPanel(Container):
    """
    Painel de histórico de decisões.
    """

    history_count: reactive[int] = reactive(0)
    approved_count: reactive[int] = reactive(0)
    rejected_count: reactive[int] = reactive(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.border_title = "📚 DECISION HISTORY"

    def compose(self) -> ComposeResult:
        """Renderiza estatísticas de histórico."""
        total_text = f"[bold]Total Decisions:[/bold] {self.history_count}"
        approved_text = f"[green]✓ Approved:[/green] {self.approved_count}"
        rejected_text = f"[red]✗ Rejected:[/red] {self.rejected_count}"

        yield Label(total_text)
        yield Label(approved_text)
        yield Label(rejected_text)

        if self.history_count > 0:
            approval_rate = (self.approved_count / self.history_count) * 100
            yield Label(f"\n[bold cyan]Approval Rate:[/bold cyan] {approval_rate:.1f}%")


class GovernanceWorkspacePOC(App):
    """
    POC do Workspace de Governança Ética.

    Valida arquitetura de:
    - SSE streaming
    - Layout reativo
    - State management
    - User interaction
    """

    CSS = """
    Screen {
        layout: grid;
        grid-size: 3 1;
        grid-gutter: 1;
        background: $surface;
    }

    PendingPanel {
        background: $panel;
        border: solid $primary;
        height: 100%;
        padding: 1;
    }

    ActivePanel {
        background: $panel;
        border: solid $success;
        height: 100%;
        padding: 1;
    }

    HistoryPanel {
        background: $panel;
        border: solid $accent;
        height: 100%;
        padding: 1;
    }

    .event-card {
        background: $boost;
        margin: 0 0 1 0;
        padding: 1;
        border: solid $primary;
        height: auto;
    }

    .button-row {
        height: auto;
        margin: 1 0 0 0;
        align: center middle;
    }

    .action-btn {
        margin: 0 1;
        min-width: 12;
    }

    .empty-state {
        padding: 2;
        text-align: center;
    }

    #active-status {
        padding: 1;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("escape", "quit", "Quit"),  # ESC também sai
        ("ctrl+c", "quit", "Quit"),  # Ctrl+C sempre funciona
        ("r", "refresh_stats", "Refresh"),
        ("t", "trigger_test", "Test Event"),
    ]

    TITLE = "Ethical Governance Workspace - POC"

    def __init__(self):
        super().__init__()
        self.sse_task: Optional[asyncio.Task] = None
        self.pending_events: List[Dict] = []
        self.active_count = 0
        self.history_count = 0
        self.approved_count = 0
        self.rejected_count = 0
        self.recent_approvals: List[str] = []

    def compose(self) -> ComposeResult:
        """Compõe layout principal."""
        yield Header()
        yield PendingPanel(id="pending-panel")
        yield ActivePanel(id="active-panel")
        yield HistoryPanel(id="history-panel")
        yield Footer()

    async def on_mount(self) -> None:
        """Inicialização quando app monta."""
        self.notify("Connecting to SSE stream...", severity="information")

        # Inicia SSE listener em background task
        self.sse_task = asyncio.create_task(self._listen_sse_stream())

        # Atualiza painéis periodicamente
        self.set_interval(0.5, self._update_panels)

        logger.info("Governance Workspace POC montado e conectado")

    async def _listen_sse_stream(self) -> None:
        """
        Escuta stream SSE do backend mock.
        Adiciona eventos recebidos à lista de pending.
        """
        sse_url = "http://localhost:8001/stream/ethical-events"

        try:
            # Timeout de 60s para evitar loops infinitos
            async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, read=None)) as client:
                async with client.stream("GET", sse_url) as response:
                    if response.status_code != 200:
                        self.notify(
                            f"SSE connection failed: {response.status_code}",
                            severity="error"
                        )
                        return

                    self.notify("✓ Connected to SSE stream", severity="information")

                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            try:
                                event_data = json.loads(line[6:])
                                self.pending_events.append(event_data)

                                # Limita a 15 eventos pendentes
                                if len(self.pending_events) > 15:
                                    self.pending_events.pop(0)

                                logger.debug(f"Evento recebido via SSE: {event_data['id']}")

                            except json.JSONDecodeError as e:
                                logger.error(f"Erro ao parsear evento SSE: {e}")

        except httpx.ConnectError:
            self.notify(
                "Cannot connect to SSE server. Start mock_sse_server.py first!",
                severity="error",
                timeout=10
            )
            logger.error("SSE connection failed - server não está rodando")

        except Exception as e:
            self.notify(f"SSE error: {e}", severity="error")
            logger.exception("Erro no SSE listener")

    def _update_panels(self) -> None:
        """Atualiza painéis reativos com estado atual."""
        try:
            # Atualiza Pending Panel
            pending_panel = self.query_one("#pending-panel", PendingPanel)
            pending_panel.pending_events = self.pending_events.copy()

            # Atualiza Active Panel
            active_panel = self.query_one("#active-panel", ActivePanel)
            active_panel.active_count = self.active_count
            active_panel.recent_approvals = self.recent_approvals.copy()

            # Atualiza History Panel
            history_panel = self.query_one("#history-panel", HistoryPanel)
            history_panel.history_count = self.history_count
            history_panel.approved_count = self.approved_count
            history_panel.rejected_count = self.rejected_count

        except Exception as e:
            logger.error(f"Erro ao atualizar painéis: {e}")

    @on(Button.Pressed, "#approve-*")
    def handle_approve(self, event: Button.Pressed) -> None:
        """Handler para botão Approve."""
        event_id = event.button.id.replace("approve-", "")

        # Remove de pending
        self.pending_events = [e for e in self.pending_events if e["id"] != event_id]

        # Atualiza contadores
        self.active_count += 1
        self.history_count += 1
        self.approved_count += 1
        self.recent_approvals.append(event_id)

        # Feedback visual
        self.notify(f"✓ Approved: {event_id}", severity="information")
        logger.info(f"Evento aprovado: {event_id}")

        # Simula conclusão da ação após 3s
        asyncio.create_task(self._complete_action(event_id))

    @on(Button.Pressed, "#reject-*")
    def handle_reject(self, event: Button.Pressed) -> None:
        """Handler para botão Reject."""
        event_id = event.button.id.replace("reject-", "")

        # Remove de pending
        self.pending_events = [e for e in self.pending_events if e["id"] != event_id]

        # Atualiza contadores
        self.history_count += 1
        self.rejected_count += 1

        # Feedback visual
        self.notify(f"✗ Rejected: {event_id}", severity="warning")
        logger.info(f"Evento rejeitado: {event_id}")

    async def _complete_action(self, event_id: str) -> None:
        """Simula conclusão de ação aprovada."""
        await asyncio.sleep(3.0)
        self.active_count = max(0, self.active_count - 1)
        logger.debug(f"Ação completada: {event_id}")

    def action_quit(self) -> None:
        """Encerra app e cleanup."""
        if self.sse_task:
            self.sse_task.cancel()
        logger.info("Encerrando Governance Workspace POC")
        self.exit()

    def action_refresh_stats(self) -> None:
        """Força refresh dos painéis."""
        self._update_panels()
        self.notify("Stats refreshed", severity="information")

    async def action_trigger_test(self) -> None:
        """Dispara evento de teste via API do mock server."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post("http://localhost:8001/spike/trigger-high-risk")
                if response.status_code == 200:
                    self.notify("✓ Test event triggered", severity="information")
                else:
                    self.notify(f"Failed to trigger test: {response.status_code}", severity="error")
        except Exception as e:
            self.notify(f"Error triggering test: {e}", severity="error")


def main():
    """Entry point para execução do POC."""
    logger.info("Iniciando Governance Workspace POC...")
    logger.info("Certifique-se de que mock_sse_server.py está rodando em http://localhost:8001")

    # Signal handling robusto - Ctrl+C sempre funciona
    def signal_handler(sig, frame):
        logger.info("Sinal de interrupção recebido - encerrando gracefully...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        app = GovernanceWorkspacePOC()
        app.run()
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt - encerrando...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Erro fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
