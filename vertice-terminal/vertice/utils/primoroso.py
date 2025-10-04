"""
🎨 Output Helpers Primorosos - WOW Effect
API simples para comandos usarem componentes primorosos
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table as RichTable
from rich.text import Text
from rich.live import Live
from rich.progress import (
    Progress as RichProgress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeRemainingColumn,
    TaskID
)
from contextlib import contextmanager
from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio

from ..ui.themes import THEME
from ..utils.banner import create_gradient_text

# Console global
console = Console()


# ============================================================================
# STATUS MESSAGES COM ANIMAÇÕES
# ============================================================================

def success(message: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    ✓ Mensagem de sucesso com gradiente verde

    Args:
        message: Mensagem principal
        details: Dicionário opcional com detalhes (key: value)
    """
    # Símbolo com gradiente
    symbol = create_gradient_text("✓", [THEME.colors.SUCCESS, THEME.colors.VERDE_AGUA])

    # Mensagem principal
    text = Text()
    text.append(symbol)
    text.append(" ", style=THEME.colors.BRANCO)
    text.append(message, style=THEME.colors.SUCCESS)

    console.print(text)

    # Detalhes se houver
    if details:
        for key, value in details.items():
            detail_text = Text()
            detail_text.append("  ", style=THEME.colors.CINZA_ESCURO)
            detail_text.append(f"{key}: ", style=THEME.colors.CINZA_TEXTO)
            detail_text.append(str(value), style=THEME.colors.BRANCO)
            console.print(detail_text)


def error(message: str, details: Optional[Dict[str, Any]] = None, suggestion: Optional[str] = None) -> None:
    """
    ✗ Mensagem de erro com gradiente vermelho

    Args:
        message: Mensagem de erro
        details: Detalhes adicionais
        suggestion: Sugestão de correção
    """
    # Símbolo com gradiente vermelho
    symbol = create_gradient_text("✗", [THEME.colors.ERROR, "#cc0000"])

    text = Text()
    text.append(symbol)
    text.append(" ", style=THEME.colors.BRANCO)
    text.append(message, style=THEME.colors.ERROR)

    console.print(text)

    # Detalhes
    if details:
        for key, value in details.items():
            detail_text = Text()
            detail_text.append("  ", style=THEME.colors.CINZA_ESCURO)
            detail_text.append(f"{key}: ", style=THEME.colors.CINZA_TEXTO)
            detail_text.append(str(value), style=THEME.colors.ERROR)
            console.print(detail_text)

    # Sugestão
    if suggestion:
        console.print()
        suggestion_text = Text()
        suggestion_text.append("  💡 ", style=THEME.colors.INFO)
        suggestion_text.append(suggestion, style=THEME.colors.CIANO_BRILHO)
        console.print(suggestion_text)


def warning(message: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    ⚠ Mensagem de warning com gradiente amarelo

    Args:
        message: Mensagem de aviso
        details: Detalhes adicionais
    """
    symbol = create_gradient_text("⚠", [THEME.colors.WARNING, "#ff8800"])

    text = Text()
    text.append(symbol)
    text.append(" ", style=THEME.colors.BRANCO)
    text.append(message, style=THEME.colors.WARNING)

    console.print(text)

    if details:
        for key, value in details.items():
            detail_text = Text()
            detail_text.append("  ", style=THEME.colors.CINZA_ESCURO)
            detail_text.append(f"{key}: ", style=THEME.colors.CINZA_TEXTO)
            detail_text.append(str(value), style=THEME.colors.WARNING)
            console.print(detail_text)


def info(message: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    ℹ Mensagem informativa com gradiente azul

    Args:
        message: Mensagem informativa
        details: Detalhes adicionais
    """
    symbol = create_gradient_text("ℹ", [THEME.colors.INFO, THEME.colors.AZUL_PROFUNDO])

    text = Text()
    text.append(symbol)
    text.append(" ", style=THEME.colors.BRANCO)
    text.append(message, style=THEME.colors.INFO)

    console.print(text)

    if details:
        for key, value in details.items():
            detail_text = Text()
            detail_text.append("  ", style=THEME.colors.CINZA_ESCURO)
            detail_text.append(f"{key}: ", style=THEME.colors.CINZA_TEXTO)
            detail_text.append(str(value), style=THEME.colors.INFO)
            console.print(detail_text)


# ============================================================================
# SPINNER PRIMOROSO (Context Manager)
# ============================================================================

class PrimorosoSpinner:
    """Spinner primoroso com gradiente - Context Manager"""

    def __init__(self, message: str = "Loading...", spinner_type: str = "dots"):
        self.message = message
        self.spinner_type = spinner_type
        self._live = None

        # Frames do spinner
        if spinner_type == "dots":
            self.frames = list(THEME.animation.SPINNER_DOTS)
        elif spinner_type == "arrow":
            self.frames = list(THEME.animation.SPINNER_ARROW)
        else:
            self.frames = list(THEME.animation.SPINNER_DOTS)

        self.frame_idx = 0

    def __enter__(self):
        # Cria Live display
        self._live = Live(self._render(), console=console, refresh_per_second=10)
        self._live.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._live:
            self._live.stop()

    def _render(self) -> Text:
        """Renderiza frame atual com gradiente"""
        frame = self.frames[self.frame_idx % len(self.frames)]
        self.frame_idx += 1

        # Spinner com gradiente
        spinner_text = create_gradient_text(frame, THEME.get_gradient_colors())

        result = Text()
        result.append(spinner_text)
        result.append("  ", style=THEME.colors.BRANCO)
        result.append(self.message, style=THEME.colors.CINZA_TEXTO)

        return result

    def update(self, message: str) -> None:
        """Atualiza mensagem do spinner"""
        self.message = message
        if self._live:
            self._live.update(self._render())


@contextmanager
def spinner(message: str = "Loading...", spinner_type: str = "dots"):
    """
    Context manager para spinner primoroso

    Usage:
        with spinner("Processing...") as s:
            # trabalho...
            s.update("Still processing...")
    """
    s = PrimorosoSpinner(message, spinner_type)
    try:
        s.__enter__()
        yield s
    finally:
        s.__exit__(None, None, None)


# ============================================================================
# PROGRESS BAR PRIMOROSO
# ============================================================================

@contextmanager
def progress(description: str = "Processing...", total: int = 100):
    """
    Progress bar primoroso com gradiente e ETA

    Usage:
        with progress("Scanning files", total=100) as p:
            for i in range(100):
                p.update(i)
                # trabalho...
    """
    # Cria progress com gradiente
    prog = RichProgress(
        SpinnerColumn(spinner_name="dots", style=THEME.colors.CIANO_BRILHO),
        TextColumn("[bold]{task.description}", style=THEME.colors.CINZA_TEXTO),
        BarColumn(
            complete_style=THEME.colors.SUCCESS,
            finished_style=THEME.colors.VERDE_NEON,
            pulse_style=THEME.colors.CIANO_BRILHO
        ),
        TextColumn("[bold]{task.percentage:>3.0f}%", style=THEME.colors.CIANO_BRILHO),
        TimeRemainingColumn(compact=True, elapsed_when_finished=True),
        console=console
    )

    with prog:
        task_id = prog.add_task(description, total=total)

        class ProgressUpdater:
            def update(self, completed: int):
                prog.update(task_id, completed=completed)

            def advance(self, amount: int = 1):
                prog.advance(task_id, advance=amount)

        yield ProgressUpdater()


# ============================================================================
# PANEL PRIMOROSO
# ============================================================================

def panel(
    content: str,
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
    gradient_title: bool = True,
    border_style: str = "cyan"
) -> None:
    """
    Panel primoroso com bordas rounded e título com gradiente

    Args:
        content: Conteúdo do panel
        title: Título (com gradiente se gradient_title=True)
        subtitle: Subtítulo
        gradient_title: Aplicar gradiente no título
        border_style: Estilo da borda
    """
    # Título com gradiente
    if title and gradient_title:
        title_text = create_gradient_text(title, THEME.get_gradient_colors())
    else:
        title_text = Text(title) if title else None

    # Cria panel
    p = Panel(
        Text(content, style=THEME.colors.BRANCO),
        title=title_text,
        subtitle=subtitle,
        border_style=border_style,
        box=__import__('rich.box', fromlist=['ROUNDED']).ROUNDED,
        padding=(1, 2)
    )

    console.print(p)


# ============================================================================
# TABLE PRIMOROSA
# ============================================================================

def table(
    title: str,
    columns: List[str],
    rows: List[List[str]],
    gradient_header: bool = True,
    show_header: bool = True
) -> None:
    """
    Tabela primorosa com headers com gradiente

    Args:
        title: Título da tabela
        columns: Lista de nomes de colunas
        rows: Lista de listas com dados
        gradient_header: Aplicar gradiente nos headers
        show_header: Mostrar header
    """
    # Cria tabela
    t = RichTable(
        title=create_gradient_text(title, THEME.get_gradient_colors()) if gradient_header else title,
        show_header=show_header,
        header_style=THEME.colors.CIANO_BRILHO if not gradient_header else None,
        border_style=THEME.colors.CINZA_MEDIO,
        box=__import__('rich.box', fromlist=['ROUNDED']).ROUNDED
    )

    # Adiciona colunas
    for col in columns:
        if gradient_header:
            col_text = create_gradient_text(col, THEME.get_gradient_colors())
            t.add_column(col_text, style=THEME.colors.BRANCO)
        else:
            t.add_column(col, style=THEME.colors.BRANCO)

    # Adiciona linhas
    for row in rows:
        t.add_row(*row)

    console.print(t)


# ============================================================================
# UTILITIES
# ============================================================================

def print_json(data: Dict[str, Any]) -> None:
    """Imprime JSON com syntax highlighting primoroso"""
    import json
    from rich.syntax import Syntax

    json_str = json.dumps(data, indent=2)
    syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
    console.print(syntax)


def separator(char: str = "─", color: Optional[str] = None) -> None:
    """Separador visual primoroso"""
    color = color or THEME.colors.CINZA_MEDIO
    console.print(char * console.width, style=color)


def newline(count: int = 1) -> None:
    """Adiciona linhas vazias (breathing room)"""
    for _ in range(count):
        console.print()
