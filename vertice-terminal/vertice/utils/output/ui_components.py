"""Interactive UI components for the CLI."""

from contextlib import contextmanager
from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text
import questionary
from typing import List

console = Console()


@contextmanager
def spinner_task(message: str, spinner_style: str = "aesthetic"):
    """
    Context manager para exibir spinner durante tarefas.
    Spinner quadradinho moderno.

    Usage:
        with spinner_task("Processing..."):
            # do work
            pass
    """
    spinner = Spinner(
        "aesthetic",
        text=f"[bold bright_cyan]{message}[/bold bright_cyan]",
        style="bright_green",
    )
    with Live(spinner, console=console, transient=True, refresh_per_second=20):
        yield


def styled_input(prompt: str, password: bool = False, default: str = "") -> str:
    """
    Input formatado com retângulo bonito estilo Gemini CLI.
    """
    prompt_text = Text()
    prompt_text.append("┌─", style="bright_cyan")
    prompt_text.append("─" * (len(prompt) + 4), style="bright_cyan")
    prompt_text.append("─┐\n", style="bright_cyan")
    prompt_text.append("│ ", style="bright_cyan")
    prompt_text.append(prompt, style="bold bright_green")
    prompt_text.append("  │\n", style="bright_cyan")
    prompt_text.append("└─", style="bright_cyan")
    prompt_text.append("─" * (len(prompt) + 4), style="bright_cyan")
    prompt_text.append("─┘", style="bright_cyan")

    console.print(prompt_text)
    console.print()

    if password:
        result = questionary.password(
            "➤ ",
            style=questionary.Style(
                [
                    ("qmark", "fg:#00ff00 bold"),
                    ("answer", "fg:#00ffaa bold"),
                ]
            ),
        ).ask()
    else:
        result = questionary.text(
            "➤ ",
            default=default,
            style=questionary.Style(
                [
                    ("qmark", "fg:#00ff00 bold"),
                    ("answer", "fg:#00ffaa bold"),
                ]
            ),
        ).ask()

    return result or ""


def styled_confirm(prompt: str, default: bool = True) -> bool:
    """
    Confirmação formatada com retângulo bonito.
    """
    prompt_text = Text()
    prompt_text.append("┌─", style="bright_yellow")
    prompt_text.append("─" * (len(prompt) + 4), style="bright_yellow")
    prompt_text.append("─┐\n", style="bright_yellow")
    prompt_text.append("│ ", style="bright_yellow")
    prompt_text.append(prompt, style="bold bright_white")
    prompt_text.append("  │\n", style="bright_yellow")
    prompt_text.append("└─", style="bright_yellow")
    prompt_text.append("─" * (len(prompt) + 4), style="bright_yellow")
    prompt_text.append("─┘", style="bright_yellow")

    console.print(prompt_text)
    console.print()

    result = questionary.confirm(
        "➤ ",
        default=default,
        style=questionary.Style(
            [
                ("qmark", "fg:#ffff00 bold"),
                ("question", "bold"),
                ("answer", "fg:#00ff00 bold"),
            ]
        ),
    ).ask()

    return result if result is not None else default


def styled_select(prompt: str, choices: List[str]) -> str:
    """
    Seleção formatada com retângulo bonito.
    """
    prompt_text = Text()
    prompt_text.append("┌─", style="bright_magenta")
    prompt_text.append("─" * (len(prompt) + 4), style="bright_magenta")
    prompt_text.append("─┐\n", style="bright_magenta")
    prompt_text.append("│ ", style="bright_magenta")
    prompt_text.append(prompt, style="bold bright_white")
    prompt_text.append("  │\n", style="bright_magenta")
    prompt_text.append("└─", style="bright_magenta")
    prompt_text.append("─" * (len(prompt) + 4), style="bright_magenta")
    prompt_text.append("─┘", style="bright_magenta")

    console.print(prompt_text)
    console.print()

    result = questionary.select(
        "➤ ",
        choices=choices,
        style=questionary.Style(
            [
                ("qmark", "fg:#ff00ff bold"),
                ("question", "bold fg:#00ffff"),
                ("answer", "fg:#ff00ff bold"),
                ("pointer", "fg:#ff00ff bold"),
                ("highlighted", "fg:#ff00ff bold"),
                ("selected", "fg:#ffaaff"),
            ]
        ),
        use_indicator=True,
        use_shortcuts=True,
    ).ask()

    return result or ""
