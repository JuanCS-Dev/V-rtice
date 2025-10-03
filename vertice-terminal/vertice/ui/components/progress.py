"""
📊 Progress Widget Primoroso
Barra de progresso com gradiente Verde → Azul
"""

from textual.widgets import Static
from textual.reactive import reactive
from rich.text import Text
from rich.progress import Progress as RichProgress, BarColumn, TextColumn, TimeRemainingColumn
from datetime import datetime
from typing import Optional

from ..themes import THEME


class ProgressWidget(Static):
    """
    Barra de progresso primorosa com gradiente.
    Suporta progresso determinado e indeterminado.
    """

    DEFAULT_CSS = """
    ProgressWidget {
        width: 100%;
        height: 3;
        padding: 1;
    }
    """

    # Estado reativo
    progress: reactive[float] = reactive(0.0)
    total: reactive[float] = reactive(100.0)
    description: reactive[str] = reactive("Processing...")
    is_indeterminate: reactive[bool] = reactive(False)

    def __init__(
        self,
        total: float = 100.0,
        description: str = "Processing...",
        indeterminate: bool = False,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.total = total
        self.description = description
        self.is_indeterminate = indeterminate

        # Tracking de velocidade para ETA
        self._start_time: Optional[datetime] = None
        self._last_update_time: Optional[datetime] = None
        self._last_progress: float = 0.0

    def render(self) -> Text:
        """Renderiza barra de progresso com gradiente"""
        from ...utils.banner import create_gradient_text

        if self.is_indeterminate:
            # Progresso indeterminado - spinner
            return self._render_indeterminate()
        else:
            # Progresso determinado - barra
            return self._render_determinate()

    def _render_determinate(self) -> Text:
        """Renderiza barra de progresso determinado"""
        # Calcula porcentagem
        percentage = (self.progress / self.total) * 100 if self.total > 0 else 0
        percentage = min(100, max(0, percentage))

        # Largura da barra (50 chars)
        bar_width = 50
        filled = int((percentage / 100) * bar_width)
        empty = bar_width - filled

        # Cria barra com gradiente
        bar_text = THEME.symbols.PROGRESS_FULL * filled + THEME.symbols.PROGRESS_EMPTY * empty

        from ...utils.banner import create_gradient_text
        bar_gradient = create_gradient_text(bar_text, THEME.get_gradient_colors())

        # Monta texto completo
        result = Text()
        result.append(self.description, style=THEME.colors.CINZA_TEXTO)
        result.append(" ")
        result.append(bar_gradient)
        result.append(f" {percentage:.1f}%", style=THEME.colors.CIANO_BRILHO)

        # Adiciona ETA se houver
        if self.progress > 0 and self.progress < self.total:
            result.append(f" [{self._estimate_time()}]", style=THEME.colors.CINZA_TEXTO)

        return result

    def _render_indeterminate(self) -> Text:
        """Renderiza barra indeterminada (pulsante)"""
        from ...utils.banner import create_gradient_text

        # Barra pulsante
        bar_text = "▓▓▓░░░▓▓▓░░░▓▓▓░░░▓▓▓░░░▓▓▓░░░▓▓▓░░░▓▓▓░░░▓▓▓"
        bar_gradient = create_gradient_text(bar_text, THEME.get_gradient_colors())

        result = Text()
        result.append(self.description, style=THEME.colors.CINZA_TEXTO)
        result.append(" ")
        result.append(bar_gradient)

        return result

    def _estimate_time(self) -> str:
        """Estima tempo restante baseado em velocidade real"""
        if not self._start_time or not self._last_update_time:
            return "~calculating..."

        # Calcula tempo decorrido
        elapsed = (datetime.now() - self._start_time).total_seconds()

        # Evita divisão por zero
        if elapsed < 0.1 or self.progress <= 0:
            return "~calculating..."

        # Calcula velocidade (unidades por segundo)
        speed = self.progress / elapsed

        # Calcula tempo restante
        remaining_units = self.total - self.progress
        remaining_seconds = remaining_units / speed if speed > 0 else 0

        # Formata tempo
        if remaining_seconds < 60:
            return f"~{int(remaining_seconds)}s"
        elif remaining_seconds < 3600:
            minutes = int(remaining_seconds / 60)
            return f"~{minutes}m"
        else:
            hours = int(remaining_seconds / 3600)
            return f"~{hours}h"

    def update(self, progress: float) -> None:
        """Atualiza progresso com tracking de velocidade"""
        now = datetime.now()

        # Inicializa tempos na primeira atualização
        if self._start_time is None:
            self._start_time = now

        # Atualiza tracking
        self._last_update_time = now
        self._last_progress = self.progress

        # Atualiza progresso
        self.progress = progress
        self.refresh()

    def advance(self, amount: float = 1.0) -> None:
        """Avança progresso com tracking"""
        now = datetime.now()

        # Inicializa tempos na primeira atualização
        if self._start_time is None:
            self._start_time = now

        # Atualiza tracking
        self._last_update_time = now
        self._last_progress = self.progress

        # Avança progresso
        self.progress = min(self.total, self.progress + amount)
        self.refresh()

    def complete(self) -> None:
        """Marca como completo"""
        self.progress = self.total
        self.refresh()

    def reset(self) -> None:
        """Reseta progresso e tracking"""
        self.progress = 0.0
        self._start_time = None
        self._last_update_time = None
        self._last_progress = 0.0
        self.refresh()
