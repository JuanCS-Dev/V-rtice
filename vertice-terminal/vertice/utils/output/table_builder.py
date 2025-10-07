"""
Gemini-Style Table Builder para VÉRTICE CLI
UI/UX Blueprint v1.2 - Production Ready

Características:
- Headers com gradiente
- Row striping sutil
- Alignment inteligente
- Truncation com ellipsis
- Status icons contextuais
- Implementação completa
"""

from rich.table import Table
from rich.console import Console
from rich.text import Text
from typing import List, Dict, Any, Optional, Literal
from ..banner import create_gradient_text
from ...ui.themes import THEME


class GeminiStyleTable:
    """
    Classe builder para tabelas primorosas estilo Gemini CLI.

    Example:
        table = GeminiStyleTable(title="Threat Analysis")
        table.add_column("IP", width=15)
        table.add_column("Threat Level", alignment="center")
        table.add_row("192.168.1.1", "🔴 High")
        table.render()
    """

    def __init__(
        self,
        title: str = "",
        console: Optional[Console] = None,
        show_header: bool = True,
        show_footer: bool = False,
        expand: bool = False,
        highlight: bool = False,
        row_styles: Optional[List[str]] = None,
    ):
        """
        Inicializa builder de tabela.

        Args:
            title: Título da tabela (aplicará gradiente)
            console: Instância do Rich Console
            show_header: Mostrar cabeçalho
            show_footer: Mostrar rodapé
            expand: Expandir largura completa
            highlight: Highlight na célula com mouse
            row_styles: Estilos alternados das linhas
        """
        self.console = console or Console()
        self._title = title
        self._show_header = show_header
        self._show_footer = show_footer
        self._expand = expand
        self._highlight = highlight

        # Row striping sutil do Blueprint
        self._row_styles = row_styles or ["", "dim"]

        # Cria tabela interna com estilo Blueprint
        self._table = Table(
            title=self._create_gradient_title() if title else None,
            show_header=show_header,
            show_footer=show_footer,
            header_style=f"bold {THEME.colors.ACENTO_SECUNDARIO}",
            border_style=THEME.colors.BORDA_PADRAO,
            row_styles=self._row_styles,
            expand=expand,
            highlight=highlight,
            padding=(0, 1),  # Padding consistente
        )

        self._columns = []
        self._rows = []

    def _create_gradient_title(self) -> Text:
        """Cria título com gradiente primoroso."""
        return create_gradient_text(
            f"📊 {self._title}",
            THEME.get_gradient_colors()
        )

    def add_column(
        self,
        header: str,
        *,
        width: Optional[int] = None,
        min_width: Optional[int] = None,
        max_width: Optional[int] = None,
        alignment: Literal["left", "center", "right"] = "left",
        no_wrap: bool = False,
        overflow: Literal["crop", "fold", "ellipsis"] = "ellipsis",
        style: Optional[str] = None,
    ) -> "GeminiStyleTable":
        """
        Adiciona coluna à tabela.

        Args:
            header: Nome do cabeçalho
            width: Largura fixa
            min_width: Largura mínima
            max_width: Largura máxima
            alignment: Alinhamento (left/center/right)
            no_wrap: Não quebrar linha
            overflow: Comportamento de overflow (ellipsis do Blueprint)
            style: Estilo customizado (default: deep_sky_blue1)

        Returns:
            Self para method chaining
        """
        column_style = style or THEME.colors.ACENTO_PRINCIPAL

        self._table.add_column(
            header,
            width=width,
            min_width=min_width,
            max_width=max_width,
            justify=alignment,
            no_wrap=no_wrap,
            overflow=overflow,
            style=column_style,
        )

        self._columns.append(header)
        return self

    def add_row(self, *values: Any, style: Optional[str] = None) -> "GeminiStyleTable":
        """
        Adiciona linha à tabela.

        Args:
            *values: Valores das células (ordem das colunas)
            style: Estilo customizado para esta linha

        Returns:
            Self para method chaining
        """
        # Converte valores para string
        str_values = [str(v) if v is not None else "N/A" for v in values]

        if style:
            self._table.add_row(*str_values, style=style)
        else:
            self._table.add_row(*str_values)

        self._rows.append(str_values)
        return self

    def add_row_with_status(
        self,
        *values: Any,
        status: Literal["success", "warning", "error", "info"] = "info",
    ) -> "GeminiStyleTable":
        """
        Adiciona linha com status icon e cor contextual.

        Args:
            *values: Valores das células
            status: Tipo de status (aplica cor do Blueprint)

        Returns:
            Self para method chaining
        """
        status_styles = {
            "success": THEME.colors.SUCCESS,
            "warning": THEME.colors.WARNING,
            "error": THEME.colors.ERROR,
            "info": THEME.colors.INFO,
        }

        status_icons = {
            "success": "✓",
            "warning": "⚠",
            "error": "✗",
            "info": "ℹ",
        }

        style = status_styles.get(status, THEME.colors.INFO)
        icon = status_icons.get(status, "•")

        # Adiciona icon na primeira célula
        first_value = f"{icon} {values[0]}" if values else icon
        remaining_values = values[1:] if len(values) > 1 else []

        return self.add_row(first_value, *remaining_values, style=style)

    def add_section(self, title: str) -> "GeminiStyleTable":
        """
        Adiciona seção separadora (linha com colspan).

        Args:
            title: Título da seção

        Returns:
            Self para method chaining
        """
        section_text = Text(f"\n{THEME.symbols.DIAMOND} {title}", style="bold")
        self._table.add_row(section_text)
        return self

    def render(self) -> None:
        """Renderiza a tabela no console."""
        self.console.print(self._table)

    def get_table(self) -> Table:
        """
        Retorna a tabela Rich interna para uso avançado.

        Returns:
            Instância Rich Table
        """
        return self._table

    @staticmethod
    def quick_table(
        data: List[Dict[str, Any]],
        title: str = "Data",
        console: Optional[Console] = None,
    ) -> None:
        """
        Helper estático para criar e renderizar tabela rapidamente.

        Args:
            data: Lista de dicionários (keys = colunas)
            title: Título da tabela
            console: Console instance

        Example:
            GeminiStyleTable.quick_table(
                [{"Name": "Alice", "Score": 95}, {"Name": "Bob", "Score": 87}],
                title="Results"
            )
        """
        if not data:
            console = console or Console()
            console.print(f"[{THEME.colors.WARNING}]No data to display[/{THEME.colors.WARNING}]")
            return

        table = GeminiStyleTable(title=title, console=console)

        # Adiciona colunas baseado nas keys do primeiro item
        columns = list(data[0].keys())
        for col in columns:
            table.add_column(col)

        # Adiciona linhas
        for row_data in data:
            values = [row_data.get(col, "N/A") for col in columns]
            table.add_row(*values)

        table.render()

    @staticmethod
    def threat_table(
        threats: List[Dict[str, Any]],
        console: Optional[Console] = None,
    ) -> None:
        """
        Helper estático para tabela de threats com cores contextuais.

        Args:
            threats: Lista de threats (deve ter 'level' field)
            console: Console instance

        Expected fields:
            - name: Nome da ameaça
            - level: critical/high/medium/low
            - source: Fonte
        """
        if not threats:
            console = console or Console()
            console.print(f"[{THEME.colors.SUCCESS}]No threats detected[/{THEME.colors.SUCCESS}]")
            return

        table = GeminiStyleTable(title="Threat Analysis", console=console)
        table.add_column("Threat", width=30)
        table.add_column("Level", alignment="center", width=15)
        table.add_column("Source", width=20)

        for threat in threats:
            level = threat.get("level", "unknown").lower()

            # Mapeia level para status
            status_map = {
                "critical": "error",
                "high": "error",
                "medium": "warning",
                "low": "info",
                "unknown": "info",
            }

            table.add_row_with_status(
                threat.get("name", "Unknown"),
                level.upper(),
                threat.get("source", "N/A"),
                status=status_map.get(level, "info"),
            )

        table.render()


__all__ = ["GeminiStyleTable"]
