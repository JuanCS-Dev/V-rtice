"""
🎨 VÉRTICE DASHBOARD - Main TUI Screen
Dashboard principal primoroso que SUPERA Gemini CLI
"""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button
from textual.binding import Binding
from rich.text import Text
from datetime import datetime

from ..themes import THEME


class GradientHeader(Static):
    """Header com gradiente primoroso Verde → Azul"""

    def compose(self) -> ComposeResult:
        yield Static(self.render_header())

    def render_header(self) -> Text:
        """Renderiza header com gradiente"""
        from ...utils.banner import create_gradient_text

        header_text = "◈ VÉRTICE TERMINAL ◈"
        gradient_header = create_gradient_text(header_text, THEME.get_gradient_colors())

        return gradient_header


class BackendStatusPanel(Static):
    """Painel de status com dados REAIS do API Gateway"""

    DEFAULT_CSS = """
    BackendStatusPanel {
        height: auto;
        min-height: 10;
        border: solid $primary;
        padding: 1;
        background: $panel;
    }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._connector = None
        self._last_status = None
        self._is_loading = True
        self._interval_timer = None

    def on_mount(self) -> None:
        """Quando montado, inicia polling do backend"""
        self._interval_timer = self.set_interval(5.0, self._refresh_status)
        self._refresh_status()

    async def _refresh_status(self) -> None:
        """Atualiza status do backend a cada 5 segundos"""
        from ...connectors.api_gateway import APIGatewayConnector

        if self._connector is None:
            self._connector = APIGatewayConnector()

        try:
            # Verifica health do gateway
            is_healthy = await self._connector.health_check()

            if is_healthy:
                # Obtém status de todos os serviços
                self._last_status = await self._connector.get_services_status()
                self._is_loading = False
            else:
                self._last_status = None
                self._is_loading = False
        except Exception as e:
            self._last_status = None
            self._is_loading = False

        self.refresh()

    def render(self) -> Text:
        """Renderiza status do backend"""
        from ...utils.banner import create_gradient_text

        now = datetime.now().strftime("%H:%M:%S")
        status = Text()

        # Título com gradiente
        title = create_gradient_text("📊 Backend Services", [THEME.colors.VERDE_NEON, THEME.colors.CIANO_BRILHO])
        status.append(title)
        status.append("\n\n")

        if self._is_loading:
            # Estado de carregamento
            status.append(f"{THEME.symbols.INFO} ", style=THEME.colors.INFO)
            status.append("Loading backend status...\n", style=THEME.colors.CINZA_TEXTO)
        elif self._last_status is None:
            # Gateway offline
            status.append(f"{THEME.symbols.ERROR} ", style=THEME.colors.ERROR)
            status.append("API Gateway ", style=THEME.colors.CINZA_TEXTO)
            status.append("OFFLINE", style=THEME.colors.ERROR)
            status.append(f"\n{THEME.symbols.INFO} ", style=THEME.colors.CINZA_TEXTO)
            status.append(f"Last check: {now}", style=THEME.colors.CINZA_TEXTO)
        else:
            # Gateway online - mostra status
            services = self._last_status.get("services", {})
            total_services = len(services)
            online_services = sum(1 for s in services.values() if s.get("status") == "healthy")

            # Status summary
            status.append(f"{THEME.symbols.SUCCESS} ", style=THEME.colors.SUCCESS)
            status.append(f"API Gateway ", style=THEME.colors.CINZA_TEXTO)
            status.append("ONLINE", style=THEME.colors.SUCCESS)
            status.append(f"\n{THEME.symbols.CIRCLE} ", style=THEME.colors.CIANO_BRILHO)
            status.append(f"Services: ", style=THEME.colors.CINZA_TEXTO)
            status.append(f"{online_services}/{total_services}", style=THEME.colors.VERDE_NEON)
            status.append(f"\n{THEME.symbols.INFO} ", style=THEME.colors.CINZA_TEXTO)
            status.append(f"Updated: {now}", style=THEME.colors.CINZA_TEXTO)

        return status

    async def on_unmount(self) -> None:
        """Fecha conexão quando desmontado"""
        if self._connector:
            await self._connector.close()


class LiveMetricsPanel(Static):
    """Painel de métricas ao vivo (CPU, Mem, Network)"""

    DEFAULT_CSS = """
    LiveMetricsPanel {
        height: auto;
        min-height: 10;
        border: solid $accent;
        padding: 1;
        background: $panel;
    }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._connector = None
        self._last_metrics = None
        self._is_loading = True
        self._interval_timer = None

    def on_mount(self) -> None:
        """Quando montado, inicia polling de métricas"""
        self._interval_timer = self.set_interval(2.0, self._refresh_metrics)
        self._refresh_metrics()

    async def _refresh_metrics(self) -> None:
        """Atualiza métricas a cada 2 segundos"""
        from ...connectors.api_gateway import APIGatewayConnector

        if self._connector is None:
            self._connector = APIGatewayConnector()

        try:
            self._last_metrics = await self._connector.get_metrics()
            self._is_loading = False
        except Exception:
            self._last_metrics = None
            self._is_loading = False

        self.refresh()

    def render(self) -> Text:
        """Renderiza métricas ao vivo"""
        from ...utils.banner import create_gradient_text

        metrics = Text()

        # Título com gradiente
        title = create_gradient_text("📈 Live Metrics", [THEME.colors.CIANO_BRILHO, THEME.colors.AZUL_PROFUNDO])
        metrics.append(title)
        metrics.append("\n\n")

        if self._is_loading:
            metrics.append(f"{THEME.symbols.INFO} ", style=THEME.colors.INFO)
            metrics.append("Loading metrics...\n", style=THEME.colors.CINZA_TEXTO)
        elif self._last_metrics is None:
            metrics.append(f"{THEME.symbols.WARNING} ", style=THEME.colors.WARNING)
            metrics.append("Metrics unavailable\n", style=THEME.colors.CINZA_TEXTO)
        else:
            # CPU
            cpu = self._last_metrics.get("cpu", {})
            cpu_percent = cpu.get("percent", 0)
            cpu_color = self._get_metric_color(cpu_percent)
            metrics.append("CPU:  ", style=THEME.colors.CINZA_TEXTO)
            metrics.append(f"{cpu_percent:.1f}%", style=cpu_color)
            metrics.append(self._get_bar(cpu_percent), style=cpu_color)
            metrics.append("\n")

            # Memory
            mem = self._last_metrics.get("memory", {})
            mem_percent = mem.get("percent", 0)
            mem_color = self._get_metric_color(mem_percent)
            metrics.append("MEM:  ", style=THEME.colors.CINZA_TEXTO)
            metrics.append(f"{mem_percent:.1f}%", style=mem_color)
            metrics.append(self._get_bar(mem_percent), style=mem_color)
            metrics.append("\n")

            # Network
            net = self._last_metrics.get("network", {})
            net_sent = net.get("sent_mb", 0)
            net_recv = net.get("recv_mb", 0)
            metrics.append("NET:  ", style=THEME.colors.CINZA_TEXTO)
            metrics.append(f"↑{net_sent:.1f}MB ", style=THEME.colors.VERDE_NEON)
            metrics.append(f"↓{net_recv:.1f}MB", style=THEME.colors.CIANO_BRILHO)

        return metrics

    def _get_metric_color(self, percent: float) -> str:
        """Retorna cor baseada na porcentagem"""
        if percent < 50:
            return THEME.colors.SUCCESS
        elif percent < 80:
            return THEME.colors.WARNING
        else:
            return THEME.colors.ERROR

    def _get_bar(self, percent: float, width: int = 10) -> str:
        """Gera barra visual de progresso"""
        filled = int((percent / 100) * width)
        empty = width - filled
        return f" [{THEME.symbols.PROGRESS_FULL * filled}{THEME.symbols.PROGRESS_EMPTY * empty}]"

    async def on_unmount(self) -> None:
        """Fecha conexão quando desmontado"""
        if self._connector:
            await self._connector.close()


class QuickActionsPanel(Static):
    """Painel de ações rápidas"""

    DEFAULT_CSS = """
    QuickActionsPanel {
        height: 10;
        border: solid $secondary;
        padding: 1;
        background: $panel;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static(self.render_actions())

    def render_actions(self) -> Text:
        """Renderiza ações rápidas"""
        from ...utils.banner import create_gradient_text

        actions = Text()

        # Título
        title = create_gradient_text("⚡ Quick Actions", [THEME.colors.CIANO_BRILHO, THEME.colors.AZUL_PROFUNDO])
        actions.append(title)
        actions.append("\n\n")

        # Actions com gradiente
        action_1 = create_gradient_text("1", [THEME.colors.VERDE_NEON, THEME.colors.CIANO_BRILHO])
        actions.append(action_1)
        actions.append(" IP Analysis\n", style=THEME.colors.BRANCO)

        action_2 = create_gradient_text("2", [THEME.colors.CIANO_BRILHO, THEME.colors.AZUL_PROFUNDO])
        actions.append(action_2)
        actions.append(" Threat Hunt\n", style=THEME.colors.BRANCO)

        action_3 = create_gradient_text("3", [THEME.colors.AZUL_PROFUNDO, THEME.colors.AZUL_ESCURO])
        actions.append(action_3)
        actions.append(" Malware Scan\n", style=THEME.colors.BRANCO)

        action_4 = create_gradient_text("4", [THEME.colors.AZUL_ESCURO, THEME.colors.AZUL_NOTURNO])
        actions.append(action_4)
        actions.append(" AI Assistant", style=THEME.colors.BRANCO)

        return actions


class CommandPalette(Static):
    """Command palette minimalista (Ctrl+P style)"""

    DEFAULT_CSS = """
    CommandPalette {
        height: 3;
        border: solid $accent;
        padding: 0 1;
        background: $surface;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static(self.render_palette())

    def render_palette(self) -> Text:
        """Renderiza command palette"""
        palette = Text()
        palette.append("❯ ", style=THEME.colors.VERDE_NEON)
        palette.append("Type a command or press ", style=THEME.colors.CINZA_TEXTO)
        palette.append("Ctrl+P", style=THEME.colors.CIANO_BRILHO)
        palette.append(" for quick access", style=THEME.colors.CINZA_TEXTO)

        return palette


class VerticeDashboard(Screen):
    """
    Dashboard principal Vértice
    UI primorosa que supera Gemini CLI
    """

    BINDINGS = [
        Binding("ctrl+p", "command_palette", "Command Palette", show=True),
        Binding("ctrl+w", "widgets_demo", "Widgets Demo", show=True),
        Binding("ctrl+t", "theme_switcher", "Themes", show=True),
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("1", "action_ip", "IP Analysis", show=False),
        Binding("2", "action_hunt", "Threat Hunt", show=False),
        Binding("3", "action_malware", "Malware Scan", show=False),
        Binding("4", "action_ai", "AI Assistant", show=False),
    ]

    CSS = """
    VerticeDashboard {
        background: $background;
    }

    .container {
        padding: 1 2;
    }

    .panels {
        height: 1fr;
    }

    .left-panel {
        width: 1fr;
    }

    .center-panel {
        width: 1fr;
    }

    .right-panel {
        width: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        """Compor layout do dashboard"""
        yield GradientHeader()

        with Container(classes="container"):
            yield CommandPalette()

            with Horizontal(classes="panels"):
                with Vertical(classes="left-panel"):
                    yield BackendStatusPanel()

                with Vertical(classes="center-panel"):
                    yield LiveMetricsPanel()

                with Vertical(classes="right-panel"):
                    yield QuickActionsPanel()

        yield Footer()

    def action_command_palette(self) -> None:
        """Abre command palette (Ctrl+P)"""
        self.notify("Command Palette - Coming Soon! 🚀", severity="information")

    def action_widgets_demo(self) -> None:
        """Abre widgets demo (Ctrl+W)"""
        from .widgets_demo import WidgetsDemoScreen
        self.app.push_screen(WidgetsDemoScreen())

    def action_theme_switcher(self) -> None:
        """Abre theme switcher (Ctrl+T)"""
        from .theme_switcher import ThemeSwitcherScreen
        self.app.push_screen(ThemeSwitcherScreen())

    def action_quit(self) -> None:
        """Sai da aplicação"""
        self.app.exit()

    def action_ip(self) -> None:
        """IP Analysis"""
        self.notify("IP Analysis - Coming Soon! 🔍", severity="information")

    def action_hunt(self) -> None:
        """Threat Hunt"""
        self.notify("Threat Hunt - Coming Soon! 🎯", severity="information")

    def action_malware(self) -> None:
        """Malware Scan"""
        self.notify("Malware Scan - Coming Soon! 🦠", severity="information")

    def action_ai(self) -> None:
        """AI Assistant"""
        self.notify("AI Assistant - Coming Soon! 🤖", severity="information")
