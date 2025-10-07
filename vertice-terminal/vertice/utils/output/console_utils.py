"""
Console output utilities.
Alinhadas ao Blueprint UI/UX v1.2 (Gemini-style refinado)
"""

from rich.console import Console
from rich.panel import Panel
from typing import Any

# Instância única e global do console, para ser usada em toda a CLI.
console = Console()


def create_panel(content: Any, title: str, border_style: str) -> Panel:
    """
    Cria um painel Rich padronizado para consistência visual.
    Alinhado ao Blueprint UI/UX v1.2
    """
    return Panel(
        content,
        title=f"[bold {border_style}]{title}[/bold {border_style}]",
        border_style=border_style,
        expand=False,
        padding=(1, 2),  # Padding consistente do Blueprint
    )


def print_success(message: str):
    """
    Imprime uma mensagem de sucesso padronizada.
    Usa green_yellow do Blueprint
    """
    console.print(f"[bold green_yellow]✓ SUCCESS:[/] [green_yellow]{message}[/green_yellow]")


def print_error(message: str, title: str = "✗ ERROR"):
    """
    Imprime uma mensagem de erro padronizada, com destaque visual.
    Usa bright_red do Blueprint
    """
    console.print(create_panel(message, title, "bright_red"))


def print_warning(message: str, title: str = "⚠ WARNING"):
    """
    Imprime uma mensagem de aviso padronizada, com destaque visual.
    Usa gold1 do Blueprint
    """
    console.print(create_panel(message, title, "gold1"))


def print_info(message: str):
    """
    Imprime uma mensagem informativa padronizada.
    Usa deep_sky_blue1 do Blueprint
    """
    console.print(f"[bold deep_sky_blue1]ℹ INFO:[/] [bright_white]{message}[/bright_white]")
