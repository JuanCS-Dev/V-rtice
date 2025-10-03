"""
🚀 VÉRTICE TUI APPLICATION
Aplicação TUI principal - Interface primorosa que supera Gemini CLI
"""

from textual.app import App
from .screens.dashboard import VerticeDashboard
from .themes import THEME


class VerticeApp(App):
    """
    Aplicação principal Vértice TUI
    UI Primorosa com gradiente Verde → Azul
    """

    CSS = f"""
    /* Cores globais baseadas no Design System */
    App {{
        background: {THEME.colors.BG_PRIMARY};
    }}

    /* Primary, Secondary, Accent */
    $primary: {THEME.colors.VERDE_NEON};
    $secondary: {THEME.colors.CIANO_BRILHO};
    $accent: {THEME.colors.AZUL_PROFUNDO};

    /* Backgrounds */
    $background: {THEME.colors.BG_PRIMARY};
    $surface: {THEME.colors.BG_SECONDARY};
    $panel: {THEME.colors.BG_PANEL};

    /* Text */
    $text: {THEME.colors.BRANCO};
    $text-muted: {THEME.colors.CINZA_TEXTO};

    /* Status */
    $success: {THEME.colors.SUCCESS};
    $warning: {THEME.colors.WARNING};
    $error: {THEME.colors.ERROR};
    $info: {THEME.colors.INFO};

    /* Header e Footer com gradiente */
    Header {{
        background: {THEME.colors.BG_SECONDARY};
        color: {THEME.colors.VERDE_NEON};
        border-bottom: solid {THEME.colors.CIANO_BRILHO};
    }}

    Footer {{
        background: {THEME.colors.BG_SECONDARY};
        color: {THEME.colors.CIANO_BRILHO};
        border-top: solid {THEME.colors.AZUL_PROFUNDO};
    }}

    /* Notifications com cores do theme */
    Notification {{
        background: {THEME.colors.BG_PANEL};
        border: solid {THEME.colors.CIANO_BRILHO};
    }}

    Notification.-information {{
        border: solid {THEME.colors.INFO};
    }}

    Notification.-warning {{
        border: solid {THEME.colors.WARNING};
    }}

    Notification.-error {{
        border: solid {THEME.colors.ERROR};
    }}
    """

    TITLE = "◈ Vértice Terminal ◈"
    SUB_TITLE = "🚀 IA-Powered Cybersecurity CLI"

    def on_mount(self) -> None:
        """Inicializa a aplicação"""
        self.push_screen(VerticeDashboard())


def run_tui():
    """Entry point para rodar a TUI"""
    app = VerticeApp()
    app.run()


if __name__ == "__main__":
    run_tui()
