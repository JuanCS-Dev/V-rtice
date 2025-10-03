"""
📈 Chart Widget Primoroso
Sparklines e mini-gráficos com gradiente
"""

from textual.widgets import Static
from textual.reactive import reactive
from rich.text import Text
from typing import List, Optional

from ..themes import THEME


class SparklineWidget(Static):
    """
    Sparkline primoroso - mini gráfico de linha inline.
    Perfeito para mostrar métricas em tempo real.
    """

    DEFAULT_CSS = """
    SparklineWidget {
        height: 3;
        padding: 0 1;
    }
    """

    # Caracteres para sparkline (8 níveis de altura)
    SPARKLINE_CHARS = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']

    data: reactive[List[float]] = reactive(list)
    title: reactive[str] = reactive("")
    max_points: reactive[int] = reactive(50)

    def __init__(
        self,
        title: str = "Metric",
        max_points: int = 50,
        initial_data: Optional[List[float]] = None,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.title = title
        self.max_points = max_points
        self.data = initial_data or []

    def render(self) -> Text:
        """Renderiza sparkline com gradiente"""
        from ...utils.banner import create_gradient_text

        if not self.data:
            return Text("No data", style=THEME.colors.CINZA_TEXTO)

        # Título
        result = Text()
        title_gradient = create_gradient_text(
            f"{self.title}: ",
            [THEME.colors.VERDE_NEON, THEME.colors.CIANO_BRILHO]
        )
        result.append(title_gradient)

        # Estatísticas
        current = self.data[-1] if self.data else 0
        min_val = min(self.data) if self.data else 0
        max_val = max(self.data) if self.data else 0
        avg_val = sum(self.data) / len(self.data) if self.data else 0

        result.append(f"{current:.1f} ", style=THEME.colors.CIANO_BRILHO)
        result.append(f"(min: {min_val:.1f} max: {max_val:.1f} avg: {avg_val:.1f})\n",
                     style=THEME.colors.CINZA_TEXTO)

        # Sparkline
        sparkline = self._create_sparkline()
        sparkline_gradient = create_gradient_text(sparkline, THEME.get_gradient_colors())
        result.append(sparkline_gradient)

        return result

    def _create_sparkline(self) -> str:
        """Cria string do sparkline"""
        if not self.data:
            return ""

        # Normaliza dados para 0-7 (8 níveis)
        min_val = min(self.data)
        max_val = max(self.data)
        range_val = max_val - min_val if max_val != min_val else 1

        sparkline = ""
        for value in self.data[-self.max_points:]:
            # Normaliza para 0-7
            normalized = int(((value - min_val) / range_val) * 7)
            normalized = max(0, min(7, normalized))
            sparkline += self.SPARKLINE_CHARS[normalized]

        return sparkline

    def add_data_point(self, value: float) -> None:
        """Adiciona ponto de dados"""
        self.data.append(value)

        # Limita tamanho
        if len(self.data) > self.max_points:
            self.data = self.data[-self.max_points:]

        self.refresh()

    def set_data(self, data: List[float]) -> None:
        """Define dados completos"""
        self.data = data[-self.max_points:] if len(data) > self.max_points else data
        self.refresh()

    def clear_data(self) -> None:
        """Limpa dados"""
        self.data = []
        self.refresh()


class BarChartWidget(Static):
    """
    Bar chart horizontal primoroso.
    Perfeito para comparações rápidas.
    """

    DEFAULT_CSS = """
    BarChartWidget {
        height: auto;
        padding: 1;
    }
    """

    data: reactive[dict] = reactive(dict)
    max_bar_width: reactive[int] = reactive(40)

    def __init__(
        self,
        data: Optional[dict] = None,
        max_bar_width: int = 40,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.data = data or {}
        self.max_bar_width = max_bar_width

    def render(self) -> Text:
        """Renderiza bar chart com gradiente"""
        from ...utils.banner import create_gradient_text

        if not self.data:
            return Text("No data", style=THEME.colors.CINZA_TEXTO)

        result = Text()

        # Calcula max value para normalização
        max_value = max(self.data.values()) if self.data else 1

        # Cores do gradiente para as barras
        colors = THEME.get_gradient_colors()
        num_items = len(self.data)

        for idx, (label, value) in enumerate(self.data.items()):
            # Label
            result.append(f"{label:12} ", style=THEME.colors.CINZA_TEXTO)

            # Barra
            bar_length = int((value / max_value) * self.max_bar_width) if max_value > 0 else 0
            bar = THEME.symbols.PROGRESS_FULL * bar_length

            # Gradiente para cada barra
            color_idx = int((idx / num_items) * (len(colors) - 1)) if num_items > 1 else 0
            bar_gradient = create_gradient_text(bar, [colors[color_idx], colors[min(color_idx + 1, len(colors) - 1)]])
            result.append(bar_gradient)

            # Valor
            result.append(f" {value}", style=THEME.colors.CIANO_BRILHO)
            result.append("\n")

        return result

    def set_data(self, data: dict) -> None:
        """Define dados"""
        self.data = data
        self.refresh()

    def update_value(self, label: str, value: float) -> None:
        """Atualiza valor de um item"""
        self.data[label] = value
        self.refresh()
