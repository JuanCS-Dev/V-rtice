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


class StatusPanel(Static):
    """Painel de status com informações em tempo real"""

    DEFAULT_CSS = """
    StatusPanel {
        height: 7;
        border: solid $primary;
        padding: 1;
        background: $panel;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static(self.render_status())

    def render_status(self) -> Text:
        """Renderiza status do sistema"""
        from ...utils.banner import create_gradient_text

        now = datetime.now().strftime("%H:%M:%S")
        status = Text()

        # Título com gradiente
        title = create_gradient_text("📊 System Status", [THEME.colors.VERDE_NEON, THEME.colors.CIANO_BRILHO])
        status.append(title)
        status.append("\n\n")

        # Status items
        status.append(f"{THEME.symbols.SUCCESS} ", style=THEME.colors.SUCCESS)
        status.append(f"Connected  ", style=THEME.colors.CINZA_TEXTO)
        status.append(f"  {THEME.symbols.CIRCLE} ", style=THEME.colors.CIANO_BRILHO)
        status.append(f"Online\n", style=THEME.colors.BRANCO)

        status.append(f"{THEME.symbols.INFO} ", style=THEME.colors.INFO)
        status.append(f"Time: {now}", style=THEME.colors.CINZA_TEXTO)

        return status


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
                    yield StatusPanel()

                with Vertical(classes="right-panel"):
                    yield QuickActionsPanel()

        yield Footer()

    def action_command_palette(self) -> None:
        """Abre command palette (Ctrl+P)"""
        self.notify("Command Palette - Coming Soon! 🚀", severity="information")

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
