"""
Banner display utilities for Vertice CLI Terminal.
🎨 PREMIUM GRADIENT BANNER - Inspired by Gemini CLI but BETTER
"""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.table import Table
from datetime import datetime
from rich.color import Color

console = Console()


def interpolate_color(color1: str, color2: str, factor: float) -> str:
    """Interpola entre duas cores hex."""
    c1 = Color.parse(color1).triplet
    c2 = Color.parse(color2).triplet

    r = int(c1.red + (c2.red - c1.red) * factor)
    g = int(c1.green + (c2.green - c1.green) * factor)
    b = int(c1.blue + (c2.blue - c1.blue) * factor)

    return f"#{r:02x}{g:02x}{b:02x}"


def create_gradient_text(text: str, colors: list = None) -> Text:
    """
    Cria um texto com gradiente de cores PRIMOROSO.
    Implementação manual para controle total e gradientes suaves.

    Args:
        text: Texto para aplicar gradiente
        colors: Lista de cores hex (ex: ["#00ff87", "#00d4ff", "#0080ff"])

    Returns:
        Text com gradiente aplicado
    """
    if not colors:
        # Default: Verde → Ciano → Azul (Gemini-inspired MELHORADO)
        colors = ["#00ff87", "#00d4ff", "#0080ff"]

    gradient_text = Text()
    text_len = len(text)

    if text_len == 0:
        return gradient_text

    # Calcular quantos chars por segmento de cor
    num_segments = len(colors) - 1
    if num_segments == 0:
        # Só uma cor
        return Text(text, style=colors[0])

    chars_per_segment = text_len / num_segments

    for i, char in enumerate(text):
        # Determinar qual segmento e fator de interpolação
        segment_idx = min(int(i / chars_per_segment), num_segments - 1)
        local_pos = (i - segment_idx * chars_per_segment) / chars_per_segment
        local_pos = max(0.0, min(1.0, local_pos))

        # Interpolar cor
        color = interpolate_color(colors[segment_idx], colors[segment_idx + 1], local_pos)
        gradient_text.append(char, style=color)

    return gradient_text


def exibir_banner():
    """
    Exibe banner PRIMOROSO estilizado para o VÉRTICE CLI.
    🎨 GRADIENT VERDE → AZUL com sombra (supera Gemini CLI)
    """
    console.clear()

    # ASCII art limpo e elegante
    ascii_art = """
    ██╗   ██╗███████╗██████╗ ████████╗██╗ ██████╗███████╗
    ██║   ██║██╔════╝██╔══██╗╚══██╔══╝██║██╔════╝██╔════╝
    ██║   ██║█████╗  ██████╔╝   ██║   ██║██║     █████╗
    ╚██╗ ██╔╝██╔══╝  ██╔══██╗   ██║   ██║██║     ██╔══╝
     ╚████╔╝ ███████╗██║  ██║   ██║   ██║╚██████╗███████╗
      ╚═══╝  ╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝ ╚═════╝╚══════╝
    """

    # GRADIENT PRIMOROSO: Verde → Ciano → Azul (Gemini-style MELHORADO)
    gradient_art = create_gradient_text(ascii_art.strip())
    current_time = datetime.now().strftime("%d de %B de %Y • %H:%M:%S")

    # Features table com gradient sutil
    info_table = Table.grid(padding=(0, 3))
    info_table.add_column(justify="center")
    info_table.add_column(justify="center")
    info_table.add_column(justify="center")
    info_table.add_column(justify="center")

    feature_1 = create_gradient_text("💡 Oráculo", ["#00ff87", "#00d4ff"])
    feature_2 = create_gradient_text("🔬 Eureka", ["#00d4ff", "#0080ff"])
    feature_3 = create_gradient_text("📝 Review", ["#0080ff", "#0040ff"])
    feature_4 = create_gradient_text("🔍 Lint", ["#0040ff", "#0020ff"])
    info_table.add_row(feature_1, feature_2, feature_3, feature_4)

    # Subtitle com gradient
    subtitle = create_gradient_text(
        "🚀 IA-Powered CyberSecurity Terminal  ⚡ Maximus AI Integration",
        ["#00ff87", "#0080ff"]
    )
    time_text = Text(f"\n🕒 {current_time}", style="dim #0080ff")

    # Panel principal com border gradient
    main_panel = Panel(
        Align.center(gradient_art),
        title=create_gradient_text("◈ PROJETO VÉRTICE CLI ◈", ["#00ff87", "#0080ff"]),
        subtitle=Text("Developed by Juan for Cybersecurity Professionals", style="dim #0080ff"),
        border_style="#00d4ff",
        padding=(1, 2),
    )

    info_panel = Panel(
        Align.center(subtitle + time_text),
        border_style="#0080ff",
        padding=(1, 2)
    )

    features_panel = Panel(
        Align.center(info_table),
        title=create_gradient_text("🛠️  Available Features", ["#00ff87", "#0040ff"]),
        border_style="#0040ff",
        padding=(1, 2),
    )

    console.print()
    console.print(main_panel)
    console.print()
    console.print(info_panel)
    console.print()
    console.print(features_panel)
    console.print()

    # Separator com gradient suave
    separator = "─" * console.width
    separator_gradient = create_gradient_text(separator)
    console.print(separator_gradient)
    console.print()
