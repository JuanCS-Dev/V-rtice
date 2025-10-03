"""
📝 Log Widget Primoroso
Logs com syntax highlighting e scroll infinito
"""

from textual.widgets import RichLog
from textual.reactive import reactive
from rich.text import Text
from rich.syntax import Syntax
from datetime import datetime
from typing import Optional

from ..themes import THEME


class LogWidget(RichLog):
    """
    Widget de logs primoroso com syntax highlighting.
    Suporta logs coloridos por nível e scroll infinito.
    """

    DEFAULT_CSS = """
    LogWidget {
        border: solid $primary;
        background: $panel;
        padding: 1;
        height: 100%;
    }
    """

    max_lines: reactive[int] = reactive(1000)
    show_timestamp: reactive[bool] = reactive(True)
    auto_scroll: reactive[bool] = reactive(True)

    def __init__(
        self,
        max_lines: int = 1000,
        show_timestamp: bool = True,
        auto_scroll: bool = True,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.max_lines = max_lines
        self.show_timestamp = show_timestamp
        self.auto_scroll = auto_scroll
        self.highlight = True
        self.markup = True

    def log_info(self, message: str) -> None:
        """Log de informação"""
        self._log_with_level("INFO", message, THEME.colors.INFO)

    def log_success(self, message: str) -> None:
        """Log de sucesso"""
        self._log_with_level("SUCCESS", message, THEME.colors.SUCCESS)

    def log_warning(self, message: str) -> None:
        """Log de warning"""
        self._log_with_level("WARNING", message, THEME.colors.WARNING)

    def log_error(self, message: str) -> None:
        """Log de erro"""
        self._log_with_level("ERROR", message, THEME.colors.ERROR)

    def log_debug(self, message: str) -> None:
        """Log de debug"""
        self._log_with_level("DEBUG", message, THEME.colors.CINZA_TEXTO)

    def _log_with_level(self, level: str, message: str, color: str) -> None:
        """Log interno com nível"""
        text = Text()

        # Timestamp
        if self.show_timestamp:
            timestamp = datetime.now().strftime("%H:%M:%S")
            text.append(f"[{timestamp}] ", style=THEME.colors.CINZA_TEXTO)

        # Level com cor
        level_width = 8
        level_padded = f"{level:^{level_width}}"
        text.append(f"{level_padded} ", style=f"bold {color}")

        # Símbolo
        symbol = self._get_level_symbol(level)
        text.append(f"{symbol} ", style=color)

        # Mensagem
        text.append(message, style=THEME.colors.BRANCO)

        self.write(text)

        # Auto-scroll
        if self.auto_scroll:
            self.scroll_end(animate=False)

    def _get_level_symbol(self, level: str) -> str:
        """Retorna símbolo do nível"""
        symbols = {
            "INFO": THEME.symbols.INFO,
            "SUCCESS": THEME.symbols.SUCCESS,
            "WARNING": THEME.symbols.WARNING,
            "ERROR": THEME.symbols.ERROR,
            "DEBUG": THEME.symbols.BULLET,
        }
        return symbols.get(level, THEME.symbols.BULLET)

    def log_json(self, data: dict, title: str = "JSON") -> None:
        """Log de JSON com syntax highlighting"""
        import json
        json_str = json.dumps(data, indent=2)

        # Syntax highlighting
        syntax = Syntax(
            json_str,
            "json",
            theme="monokai",
            line_numbers=False,
            background_color=THEME.colors.BG_PANEL
        )

        text = Text()
        if self.show_timestamp:
            timestamp = datetime.now().strftime("%H:%M:%S")
            text.append(f"[{timestamp}] ", style=THEME.colors.CINZA_TEXTO)

        text.append(f"{title}:", style=THEME.colors.CIANO_BRILHO)
        self.write(text)
        self.write(syntax)

    def log_code(self, code: str, language: str = "python", title: Optional[str] = None) -> None:
        """Log de código com syntax highlighting"""
        syntax = Syntax(
            code,
            language,
            theme="monokai",
            line_numbers=True,
            background_color=THEME.colors.BG_PANEL
        )

        if title:
            text = Text()
            if self.show_timestamp:
                timestamp = datetime.now().strftime("%H:%M:%S")
                text.append(f"[{timestamp}] ", style=THEME.colors.CINZA_TEXTO)

            text.append(f"{title}:", style=THEME.colors.CIANO_BRILHO)
            self.write(text)

        self.write(syntax)

    def clear_logs(self) -> None:
        """Limpa todos os logs"""
        self.clear()
        self.log_info("Logs cleared")
