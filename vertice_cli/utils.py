# vertice_cli/utils.py

import time
from pathlib import Path
import pyfiglet
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from datetime import datetime

# Inicializa o console do Rich para uma saída bonita
console = Console()

def exibir_banner():
    """Exibe um banner estilizado para o VÉRTICE CLI usando pyfiglet e rich."""
    figlet_text = pyfiglet.figlet_format("V E R T I C E", font="slant")
    
    rich_text = Text(figlet_text, justify="center", style="bold cyan")

    current_time = datetime.now().strftime("%d de %B de %Y, %H:%M")
    subtitle_text = f"[bold]IA-Powered DevOps Assistant[/bold]\n[dim]{current_time}[/dim]"
    
    panel = Panel(
        rich_text,
        title="[bold white]Projeto VÉRTICE[/bold white]",
        subtitle=subtitle_text,
        subtitle_align="center",
        border_style="magenta",
        padding=(2, 10)
    )
    console.print(panel)

def print_panel(text: str, title: str, color: str = "green"):
    """Imprime um texto dentro de um painel estilizado."""
    console.print(
        Panel(text, title=title, title_align="left", border_style=color, padding=(1, 2))
    )

def thinking_stream(messages: list, delay: float = 0.5):
    """Exibe uma sequência de mensagens com um spinner, simulando 'pensamento'."""
    with console.status("[bold blue]Processando...") as status:
        for message in messages:
            status.update(message)
            time.sleep(delay)
    console.print()

def collect_files(root_path: str) -> list[Path]:
    """
    Coleta recursivamente todos os arquivos relevantes de um diretório.
    Ignora pastas comuns de desenvolvimento.
    """
    files_found = []
    ignore_dirs = {'.venv', 'node_modules', '.git', '__pycache__'}
    
    root = Path(root_path)
    for path in root.rglob('*'):
        if any(ignored in path.parts for ignored in ignore_dirs):
            continue
            
        if path.is_file() and path.suffix in ['.js', '.py', '.md', '.sh', '.toml']:
            files_found.append(path)
            
    return files_found
