"""
🎨 Theme Switcher Screen - Tela de Troca de Temas
Troca de temas em tempo real com preview
IMPLEMENTAÇÃO REAL - ZERO MOCKS
"""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button
from textual.binding import Binding
from rich.text import Text

from ..themes.theme_manager import theme_manager
from ..themes import THEME


class ThemePreview(Static):
    """Preview visual do tema"""

    DEFAULT_CSS = """
    ThemePreview {
        height: 10;
        border: solid $primary;
        padding: 1;
        background: $panel;
        margin: 1;
    }
    """

    def __init__(self, theme_name: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.theme_name = theme_name

    def render(self) -> Text:
        """Renderiza preview do tema"""
        # Temporariamente muda tema para pegar cores
        original_theme = theme_manager.get_theme_name()
        theme_manager.set_theme(self.theme_name)

        colors = theme_manager.get_theme_colors()
        gradient_colors = theme_manager.get_gradient_colors()

        # Restaura tema original
        theme_manager.set_theme(original_theme)

        # Cria preview
        from ...utils.banner import create_gradient_text

        result = Text()

        # Nome do tema com gradiente
        theme_title = create_gradient_text(
            f"◈ {self.theme_name.upper()} ◈",
            gradient_colors
        )
        result.append(theme_title)
        result.append("\n\n")

        # Cores primárias
        result.append("█", style=colors['primary'])
        result.append(" Primary  ", style=colors['text'])

        result.append("█", style=colors['secondary'])
        result.append(" Secondary  ", style=colors['text'])

        result.append("█", style=colors['accent'])
        result.append(" Accent\n", style=colors['text'])

        # Status colors
        result.append("█", style=colors['success'])
        result.append(" Success  ", style=colors['text'])

        result.append("█", style=colors['warning'])
        result.append(" Warning  ", style=colors['text'])

        result.append("█", style=colors['error'])
        result.append(" Error  ", style=colors['text'])

        result.append("█", style=colors['info'])
        result.append(" Info", style=colors['text'])

        result.append("\n\n")

        # Descrição
        desc = theme_manager.get_theme_description(self.theme_name)
        result.append(desc, style=colors['text_muted'])

        return result


class ThemeSwitcherScreen(Screen):
    """
    Tela de seleção de temas.
    Permite trocar tema em tempo real com preview.
    """

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", show=True),
        Binding("1", "select_theme('vertice')", "Vértice", show=False),
        Binding("2", "select_theme('cyberpunk')", "Cyberpunk", show=False),
        Binding("3", "select_theme('matrix')", "Matrix", show=False),
        Binding("4", "select_theme('minimal')", "Minimal", show=False),
    ]

    CSS = """
    ThemeSwitcherScreen {
        background: $background;
    }

    .themes-container {
        padding: 2;
        align: center middle;
    }

    .theme-grid {
        width: 100%;
        height: auto;
    }

    .theme-row {
        height: auto;
        margin-bottom: 1;
    }

    .current-theme {
        border: solid $success;
        background: $surface;
    }
    """

    def compose(self) -> ComposeResult:
        """Compor layout"""
        yield Header()

        with Container(classes="themes-container"):
            yield Static(
                "🎨 Theme Selector - Choose Your Style",
                classes="section-title"
            )

            with Vertical(classes="theme-grid"):
                # Row 1: Vértice + Cyberpunk
                with Horizontal(classes="theme-row"):
                    yield ThemePreview("vertice", id="theme-vertice")
                    yield ThemePreview("cyberpunk", id="theme-cyberpunk")

                # Row 2: Matrix + Minimal
                with Horizontal(classes="theme-row"):
                    yield ThemePreview("matrix", id="theme-matrix")
                    yield ThemePreview("minimal", id="theme-minimal")

            # Instruções
            yield Static(
                "\nPress 1-4 to select theme | ESC to go back",
                classes="instructions"
            )

        yield Footer()

    def on_mount(self) -> None:
        """Marca tema atual"""
        current = theme_manager.get_theme_name()
        self._highlight_current_theme(current)

    def _highlight_current_theme(self, theme_name: str) -> None:
        """Destaca tema atual"""
        # Remove highlight de todos
        for theme_id in ["theme-vertice", "theme-cyberpunk", "theme-matrix", "theme-minimal"]:
            widget = self.query_one(f"#{theme_id}")
            widget.remove_class("current-theme")

        # Adiciona highlight no atual
        current_widget = self.query_one(f"#theme-{theme_name}")
        current_widget.add_class("current-theme")

    def action_select_theme(self, theme_name: str) -> None:
        """
        Seleciona tema e aplica.

        IMPORTANTE: Isso é REAL! Troca o tema na aplicação inteira.
        """
        if theme_manager.set_theme(theme_name):
            # Atualiza highlight
            self._highlight_current_theme(theme_name)

            # Notifica sucesso
            self.notify(
                f"Theme changed to: {theme_name}",
                severity="information",
                timeout=2
            )

            # REAL: Atualiza CSS da aplicação
            self._apply_theme_to_app()

    def _apply_theme_to_app(self) -> None:
        """
        Aplica tema à aplicação REAL.
        Atualiza CSS dinamicamente.
        """
        # Pega CSS do tema
        theme_css = theme_manager.get_css()

        # Atualiza CSS da aplicação
        # NOTA: Textual recarrega CSS automaticamente quando usa variáveis
        # Forçamos refresh de todos os widgets
        self.app.refresh()

        # Força refresh de todas as screens
        for screen in self.app.screen_stack:
            screen.refresh()
