from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from datetime import datetime
from rich.table import Table

console = Console()

def create_gradient_text(text: str, colors: list) -> Text:
    """Cria um texto com gradiente de cores."""
    gradient_text = Text()
    if not text:
        return gradient_text
    
    lines = text.strip('\n').split('\n')
    
    for i, line in enumerate(lines):
        color_index = min(int((i / len(lines)) * len(colors)), len(colors) - 1)
        gradient_text.append(line, style=colors[color_index])
        if i < len(lines) - 1:
            gradient_text.append("\n")
    
    return gradient_text

def exibir_banner():
    """Exibe um banner estilizado moderno para o VÉRTICE CLI."""
    console.clear()
    
    green_gradient = ["#00ff00", "#00dd44", "#00bb88", "#0099cc", "#0077ff"]
    
    # Usando uma raw triple-quoted string para evitar problemas de escape
    ascii_art = r"""
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
    info_table.add_column(style="#00ff00 bold", justify="center")
    info_table.add_column(style="#00bb88", justify="center")
    info_table.add_column(style="#0099cc", justify="center")
    info_table.add_column(style="#0077ff", justify="center")

    info_table.add_row("💡 Oráculo", "🔬 Eureka", "📝 Review", "🔍 Lint")
    
    main_panel = Panel(
        Align.center(gradient_art),
        title="[bold #00ff00]◈ PROJETO VÉRTICE ◈[/bold #00ff00]",
        subtitle="[dim #00bb88]Developed by Juan and Gemini for the dev community[/dim #00bb88]",
        border_style="#00dd44",
        padding=(1, 2)
    )
    
    info_panel = Panel(
        Align.center(
            f"🚀 IA-Powered DevOps Assistant  •  ⚡ Gemini Pro Integration\n🕒 {current_time}"
        ),
        border_style="#0099cc",
        padding=(1, 2)
    )

    console.print(main_panel)
    console.print(info_panel)
    console.print(Align.center(info_table))
    console.print()
