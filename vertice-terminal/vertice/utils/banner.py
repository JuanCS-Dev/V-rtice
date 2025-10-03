"""
Banner display utilities for Vertice CLI Terminal.
COPIED EXACTLY FROM: vertice_cli/utils.py:exibir_banner()
"""
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.table import Table
from datetime import datetime

console = Console()

def create_gradient_text(text: str, colors: list) -> Text:
    """Cria um texto com gradiente de cores."""
    gradient_text = Text()
    if len(text) <= 1:
        return Text(text, style=colors[0])

    chars_per_color = max(1, len(text) // len(colors))

    for i, char in enumerate(text):
        color_index = min(i // chars_per_color, len(colors) - 1)
        gradient_text.append(char, style=colors[color_index])

    return gradient_text

def exibir_banner():
    """
    Exibe banner estilizado moderno para o VÉRTICE CLI.
    ⚠️ COPIED EXACTLY FROM: vertice_cli/utils.py:exibir_banner()
    """
    console.clear()

    green_gradient = ["bright_green", "green", "bright_cyan", "cyan", "bright_blue"]

    ascii_art = """
    ██╗   ██╗███████╗██████╗ ████████╗██╗ ██████╗███████╗
    ██║   ██║██╔════╝██╔══██╗╚══██╔══╝██║██╔════╝██╔════╝
    ██║   ██║█████╗  ██████╔╝   ██║   ██║██║     █████╗
    ╚██╗ ██╔╝██╔══╝  ██╔══██╗   ██║   ██║██║     ██╔══╝
     ╚████╔╝ ███████╗██║  ██║   ██║   ██║╚██████╗███████╗
      ╚═══╝  ╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝ ╚═════╝╚══════╝
    """

    gradient_art = create_gradient_text(ascii_art, green_gradient)
    current_time = datetime.now().strftime("%d de %B de %Y • %H:%M:%S")

    info_table = Table.grid(padding=(0, 2))
    info_table.add_column(style="bright_green bold", justify="center")
    info_table.add_column(style="bright_cyan", justify="center")
    info_table.add_column(style="bright_blue", justify="center")
    info_table.add_column(style="cyan", justify="center")
    info_table.add_row("💡 Oráculo", "🔬 Eureka", "📝 Review", "🔍 Lint")

    subtitle_text = Text()
    subtitle_text.append("🚀 IA-Powered CyberSecurity Terminal  ", style="bright_green")
    subtitle_text.append("⚡ Maximus AI Integration\n", style="bright_cyan")
    subtitle_text.append(f"🕒 {current_time}", style="dim bright_cyan")

    main_panel = Panel(
        Align.center(gradient_art),
        title="[bold bright_green]◈ PROJETO VÉRTICE CLI ◈[/bold bright_green]",
        subtitle="[dim bright_cyan]Developed by Juan for Cybersecurity Professionals[/dim bright_cyan]",
        border_style="bright_green",
        padding=(1, 2)
    )

    info_panel = Panel(
        Align.center(subtitle_text),
        border_style="bright_cyan",
        padding=(1, 2)
    )

    features_panel = Panel(
        Align.center(info_table),
        title="[bold cyan]🛠️  Available Features[/bold cyan]",
        border_style="cyan",
        padding=(1, 2)
    )

    console.print()
    console.print(main_panel)
    console.print()
    console.print(info_panel)
    console.print()
    console.print(features_panel)
    console.print()

    separator = "─" * console.width
    separator_gradient = create_gradient_text(separator, green_gradient)
    console.print(separator_gradient)
    console.print()
