"""
Primordial Panel Builder para VÉRTICE CLI
UI/UX Blueprint v1.2 - Production Ready

Características:
- Bordas com gradiente
- Padding consistente
- Title/subtitle styling
- Status indicators
- Layout inteligente
- Implementação completa
"""

from rich.panel import Panel
from rich.console import Console, RenderableType
from rich.text import Text
from rich.align import Align
from rich.table import Table
from typing import Optional, Literal, Union
from ..banner import create_gradient_text
from ...ui.themes import THEME


class PrimordialPanel:
    """
    Classe builder para painéis primorosos estilo Vértice.

    Example:
        panel = PrimordialPanel(
            content="Analysis complete",
            title="IP Intelligence"
        )
        panel.with_status("success")
        panel.render()
    """

    def __init__(
        self,
        content: Union[str, RenderableType],
        title: Optional[str] = None,
        subtitle: Optional[str] = None,
        console: Optional[Console] = None,
    ):
        """
        Inicializa builder de painel.

        Args:
            content: Conteúdo do painel (string ou Rich renderable)
            title: Título (aplicará gradiente se não for marcação)
            subtitle: Subtítulo
            console: Instância do Rich Console
        """
        self.console = console or Console()
        self._content = content
        self._title = title
        self._subtitle = subtitle

        # Valores padrão do Blueprint
        self._border_style = THEME.colors.BORDA_PADRAO
        self._padding = (1, 2)  # Blueprint padding consistente
        self._expand = False
        self._highlight = False
        self._title_align = "left"
        self._subtitle_align = "left"

    def with_status(
        self,
        status: Literal["success", "warning", "error", "info"],
    ) -> "PrimordialPanel":
        """
        Aplica cor de status ao painel.

        Args:
            status: Tipo de status (muda border_style)

        Returns:
            Self para method chaining
        """
        status_colors = {
            "success": THEME.colors.SUCCESS,
            "warning": THEME.colors.WARNING,
            "error": THEME.colors.ERROR,
            "info": THEME.colors.INFO,
        }

        self._border_style = status_colors.get(status, THEME.colors.BORDA_PADRAO)
        return self

    def with_gradient_border(self) -> "PrimordialPanel":
        """
        Aplica borda com cor de acento principal.

        Returns:
            Self para method chaining
        """
        self._border_style = THEME.colors.ACENTO_PRINCIPAL
        return self

    def with_padding(self, padding: tuple) -> "PrimordialPanel":
        """
        Define padding customizado.

        Args:
            padding: Tuple (vertical, horizontal)

        Returns:
            Self para method chaining
        """
        self._padding = padding
        return self

    def expanded(self) -> "PrimordialPanel":
        """
        Expande painel para largura completa.

        Returns:
            Self para method chaining
        """
        self._expand = True
        return self

    def with_highlight(self) -> "PrimordialPanel":
        """
        Ativa highlight ao passar mouse.

        Returns:
            Self para method chaining
        """
        self._highlight = True
        return self

    def center_title(self) -> "PrimordialPanel":
        """
        Centraliza o título.

        Returns:
            Self para method chaining
        """
        self._title_align = "center"
        return self

    def _create_title(self) -> Optional[Union[str, Text]]:
        """Cria título com gradiente se necessário."""
        if not self._title:
            return None

        # Se já tem marcação Rich, retorna como está
        if "[" in self._title and "]" in self._title:
            return self._title

        # Senão, aplica gradiente primoroso
        return create_gradient_text(
            self._title,
            THEME.get_gradient_colors()
        )

    def _create_subtitle(self) -> Optional[str]:
        """Cria subtítulo com cor secundária."""
        if not self._subtitle:
            return None

        # Se já tem marcação, retorna como está
        if "[" in self._subtitle and "]" in self._subtitle:
            return self._subtitle

        # Aplica cor de texto secundário do Blueprint
        return f"[{THEME.colors.TEXTO_SECUNDARIO}]{self._subtitle}[/{THEME.colors.TEXTO_SECUNDARIO}]"

    def render(self) -> None:
        """Renderiza o painel no console."""
        panel = Panel(
            self._content,
            title=self._create_title(),
            subtitle=self._create_subtitle(),
            border_style=self._border_style,
            padding=self._padding,
            expand=self._expand,
            highlight=self._highlight,
            title_align=self._title_align,
            subtitle_align=self._subtitle_align,
        )

        self.console.print(panel)

    def get_panel(self) -> Panel:
        """
        Retorna o painel Rich para uso avançado.

        Returns:
            Instância Rich Panel
        """
        return Panel(
            self._content,
            title=self._create_title(),
            subtitle=self._create_subtitle(),
            border_style=self._border_style,
            padding=self._padding,
            expand=self._expand,
            highlight=self._highlight,
            title_align=self._title_align,
            subtitle_align=self._subtitle_align,
        )

    @staticmethod
    def success(
        content: Union[str, RenderableType],
        title: str = "✓ Success",
        console: Optional[Console] = None,
    ) -> None:
        """
        Helper estático para painel de sucesso.

        Args:
            content: Conteúdo
            title: Título
            console: Console instance
        """
        panel = PrimordialPanel(content, title=title, console=console)
        panel.with_status("success").render()

    @staticmethod
    def error(
        content: Union[str, RenderableType],
        title: str = "✗ Error",
        console: Optional[Console] = None,
    ) -> None:
        """
        Helper estático para painel de erro.

        Args:
            content: Conteúdo
            title: Título
            console: Console instance
        """
        panel = PrimordialPanel(content, title=title, console=console)
        panel.with_status("error").render()

    @staticmethod
    def warning(
        content: Union[str, RenderableType],
        title: str = "⚠ Warning",
        console: Optional[Console] = None,
    ) -> None:
        """
        Helper estático para painel de aviso.

        Args:
            content: Conteúdo
            title: Título
            console: Console instance
        """
        panel = PrimordialPanel(content, title=title, console=console)
        panel.with_status("warning").render()

    @staticmethod
    def info(
        content: Union[str, RenderableType],
        title: str = "ℹ Info",
        console: Optional[Console] = None,
    ) -> None:
        """
        Helper estático para painel informativo.

        Args:
            content: Conteúdo
            title: Título
            console: Console instance
        """
        panel = PrimordialPanel(content, title=title, console=console)
        panel.with_status("info").render()

    @staticmethod
    def metrics_panel(
        metrics: dict,
        title: str = "📊 Metrics",
        console: Optional[Console] = None,
    ) -> None:
        """
        Helper estático para painel de métricas.

        Args:
            metrics: Dicionário de métricas {key: value}
            title: Título
            console: Console instance
        """
        table = Table.grid(padding=(0, 2))
        table.add_column(style=f"bold {THEME.colors.ACENTO_PRINCIPAL}", no_wrap=True)
        table.add_column(style=THEME.colors.TEXTO_PRIMARIO)

        for key, value in metrics.items():
            table.add_row(f"{THEME.symbols.BULLET} {key}:", str(value))

        panel = PrimordialPanel(table, title=title, console=console)
        panel.with_gradient_border().render()

    @staticmethod
    def centered(
        content: Union[str, RenderableType],
        title: Optional[str] = None,
        console: Optional[Console] = None,
    ) -> None:
        """
        Helper estático para painel centralizado.

        Args:
            content: Conteúdo
            title: Título
            console: Console instance
        """
        aligned_content = Align.center(content)
        panel = PrimordialPanel(aligned_content, title=title, console=console)
        panel.center_title().expanded().render()

    @staticmethod
    def status_grid(
        items: list,
        columns: int = 2,
        title: str = "Status",
        console: Optional[Console] = None,
    ) -> None:
        """
        Helper estático para grid de status.

        Args:
            items: Lista de tuplas (label, value, status)
            columns: Número de colunas
            title: Título
            console: Console instance

        Example:
            PrimordialPanel.status_grid([
                ("API Gateway", "Online", "success"),
                ("Database", "Degraded", "warning"),
            ])
        """
        table = Table.grid(padding=(0, 3))

        for _ in range(columns):
            table.add_column()

        # Agrupa items em rows
        for i in range(0, len(items), columns):
            row_items = items[i:i + columns]

            row_content = []
            for item in row_items:
                label, value, status = item

                status_colors = {
                    "success": THEME.colors.SUCCESS,
                    "warning": THEME.colors.WARNING,
                    "error": THEME.colors.ERROR,
                    "info": THEME.colors.INFO,
                }

                status_icons = {
                    "success": "🟢",
                    "warning": "🟡",
                    "error": "🔴",
                    "info": "🔵",
                }

                color = status_colors.get(status, THEME.colors.INFO)
                icon = status_icons.get(status, "⚪")

                text = Text()
                text.append(f"{label}: ", style=THEME.colors.TEXTO_SECUNDARIO)
                text.append(f"{icon} {value}", style=color)

                row_content.append(text)

            # Preenche colunas vazias se necessário
            while len(row_content) < columns:
                row_content.append(Text(""))

            table.add_row(*row_content)

        panel = PrimordialPanel(table, title=title, console=console)
        panel.with_gradient_border().render()


__all__ = ["PrimordialPanel"]
