"""Console output utilities."""

from rich.console import Console
from rich.panel import Panel
from typing import Any

# Instância única e global do console, para ser usada em toda a CLI.
console = Console()


def create_panel(content: Any, title: str, border_style: str) -> Panel:
    """Cria um painel Rich padronizado para consistência visual."""
    return Panel(
        content,
        title=f"[bold {border_style}]{title}[/bold {border_style}]",
        border_style=border_style,
        expand=False,
    )


def print_success(message: str):
    """Imprime uma mensagem de sucesso padronizada."""
    console.print(f"[bold green]✅ SUCESSO:[/] [green]{message}[/green]")


def print_error(message: str, title: str = "✗ ERRO"):
    """Imprime uma mensagem de erro padronizada, com destaque visual."""
    console.print(create_panel(message, title, "red"))


def print_warning(message: str, title: str = "⚠ AVISO"):
    """Imprime uma mensagem de aviso padronizada, com destaque visual."""
    console.print(create_panel(message, title, "yellow"))


def print_info(message: str):
    """Imprime uma mensagem informativa padronizada."""
    console.print(f"[bold blue]ℹ️ INFO:[/] {message}")
