"""
🌀 Spinner Widget Primoroso
Animações suaves com gradiente Verde → Azul
"""

from textual.widgets import Static
from textual.reactive import reactive
from rich.text import Text
from datetime import datetime
import asyncio

from ..themes import THEME


class SpinnerWidget(Static):
    """
    Spinner animado primoroso com gradiente.
    Usa os spinners do Design System.
    """

    DEFAULT_CSS = """
    SpinnerWidget {
        width: auto;
        height: 1;
        content-align: center middle;
    }
    """

    # Estado reativo
    frame_index: reactive[int] = reactive(0)
    is_spinning: reactive[bool] = reactive(False)
    message: reactive[str] = reactive("")

    def __init__(
        self,
        message: str = "Loading...",
        spinner_type: str = "dots",
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.message = message
        self.spinner_type = spinner_type
        self._task = None

        # Seleciona spinner do theme
        if spinner_type == "dots":
            self.frames = THEME.animation.SPINNER_DOTS
        elif spinner_type == "line":
            self.frames = THEME.animation.SPINNER_LINE
        elif spinner_type == "clock":
            self.frames = THEME.animation.SPINNER_CLOCK
        elif spinner_type == "arrow":
            self.frames = THEME.animation.SPINNER_ARROW
        else:
            self.frames = THEME.animation.SPINNER_DOTS

    def on_mount(self) -> None:
        """Inicia animação quando montado"""
        self.start()

    def render(self) -> Text:
        """Renderiza spinner com gradiente"""
        from ...utils.banner import create_gradient_text

        if not self.is_spinning:
            return Text("")

        # Frame atual do spinner
        current_frame = self.frames[self.frame_index % len(self.frames)]

        # Cria texto com gradiente
        spinner_text = create_gradient_text(
            current_frame,
            THEME.get_gradient_colors()
        )

        # Adiciona mensagem
        result = Text()
        result.append(spinner_text)
        result.append(" ", style=THEME.colors.BRANCO)
        result.append(self.message, style=THEME.colors.CINZA_TEXTO)

        return result

    async def _animate(self) -> None:
        """Loop de animação"""
        while self.is_spinning:
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.refresh()
            await asyncio.sleep(0.1)  # 100ms por frame

    def start(self) -> None:
        """Inicia spinner"""
        if not self.is_spinning:
            self.is_spinning = True
            self._task = asyncio.create_task(self._animate())

    def stop(self) -> None:
        """Para spinner"""
        self.is_spinning = False
        if self._task:
            self._task.cancel()
            self._task = None

    def update_message(self, message: str) -> None:
        """Atualiza mensagem do spinner"""
        self.message = message
        self.refresh()
