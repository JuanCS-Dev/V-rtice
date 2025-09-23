# vertice_cli/utils.py

import time
from pathlib import Path
import pyfiglet
import git
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table
from datetime import datetime
import itertools
import questionary

# Inicializa o console do Rich para uma saída bonita
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
    """Exibe um banner estilizado moderno para o VÉRTICE CLI inspirado no Gemini CLI."""
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
    info_table.add_row("🚀 IA-Powered DevOps Assistant", "")
    info_table.add_row("⚡ Gemini Pro Integration", "")
    info_table.add_row(f"🕒 {current_time}", "")
    info_table.add_row("", "")
    info_table.add_row("💡 Oráculo", "🔬 Eureka", "📝 Review", "🔍 Lint")
    
    main_panel = Panel(
        Align.center(gradient_art),
        title="[bold bright_green]◈ PROJETO VÉRTICE ◈[/bold bright_green]",
        subtitle="[dim bright_cyan]Developed by Juan and Gemini for the dev community[/dim bright_cyan]",
        border_style="bright_green",
        padding=(1, 2)
    )
    
    info_panel = Panel(Align.center(info_table), border_style="bright_cyan", padding=(1, 2))
    
    console.print()
    console.print(main_panel)
    console.print()
    console.print(info_panel)
    console.print()
    
    separator = "─" * console.width
    separator_gradient = create_gradient_text(separator, green_gradient)
    console.print(separator_gradient)
    console.print()

def print_panel(text: str, title: str, color: str = "green"):
    """Imprime um texto dentro de um painel estilizado moderno."""
    color_schemes = {
        "green": {"border": "bright_green", "title": "bold bright_green", "icon": "🌟"},
        "magenta": {"border": "bright_magenta", "title": "bold bright_magenta", "icon": "🔮"},
        "cyan": {"border": "bright_cyan", "title": "bold bright_cyan", "icon": "💎"},
        "yellow": {"border": "bright_yellow", "title": "bold bright_yellow", "icon": "⚠️"},
        "red": {"border": "bright_red", "title": "bold bright_red", "icon": "🚨"}
    }
    scheme = color_schemes.get(color, color_schemes["green"])
    icon = scheme["icon"]
    styled_title = f"[{scheme['title']}]{icon} {title} {icon}[/{scheme['title']}]"
    console.print(Panel(text, title=styled_title, title_align="center", border_style=scheme["border"], padding=(1, 3), expand=False))

def thinking_stream(messages: list, delay: float = 0.8):
    """Exibe uma sequência de mensagens com spinners elaborados."""
    with Progress(SpinnerColumn(spinner_style="bright_green"), TextColumn("[bold bright_cyan]{task.description}"), transient=True) as progress:
        task = progress.add_task("thinking", total=len(messages))
        for message in messages:
            progress.update(task, description=message)
            time.sleep(delay)
    console.print()

def collect_files(root_path: str) -> list[Path]:
    """Coleta recursivamente todos os arquivos relevantes de um diretório."""
    files_found = []
    ignore_dirs = {'.venv', 'node_modules', '.git', '__pycache__', '.pytest_cache', 'dist', 'build'}
    root = Path(root_path)
    all_paths = list(root.rglob('*'))
    
    with Progress(SpinnerColumn("dots12", style="bright_green"), TextColumn("[bold bright_cyan]Escaneando {task.fields[num_files]} arquivos..."), transient=True) as progress:
        task = progress.add_task("scan", total=len(all_paths), num_files=len(all_paths))
        for path in all_paths:
            progress.update(task, advance=1)
            if any(ignored in path.parts for ignored in ignore_dirs):
                continue
            if path.is_file() and path.suffix in ['.js', '.py', '.md', '.sh', '.toml', '.yaml', '.yml', '.json']:
                files_found.append(path)
    return files_found

def print_success(message: str):
    """Imprime uma mensagem de sucesso estilizada."""
    console.print(f"✅ [bold bright_green]{message}[/bold bright_green]")

def print_warning(message: str):
    """Imprime uma mensagem de aviso estilizada."""
    console.print(f"⚠️  [bold bright_yellow]{message}[/bold bright_yellow]")

def print_error(message: str):
    """Imprime uma mensagem de erro estilizada."""
    console.print(f"🚨 [bold bright_red]{message}[/bold bright_red]")

def print_info(message: str):
    """Imprime uma mensagem informativa estilizada."""
    console.print(f"💡 [bold bright_cyan]{message}[/bold bright_cyan]")

def create_status_table(items: dict) -> Table:
    """Cria uma tabela de status moderna."""
    table = Table(show_header=True, header_style="bold bright_green")
    table.add_column("Item", style="bright_cyan", width=20)
    table.add_column("Status", style="bright_green", width=15)
    table.add_column("Detalhes", style="white")
    for item, data in items.items():
        table.add_row(item, data.get("status", ""), data.get("details", ""))
    return table

def git_safe_execute(action_func, repo_path: Path, command_name: str):
    """Executa uma função que modifica arquivos dentro de um protocolo de segurança Git."""
    try:
        repo = git.Repo(repo_path, search_parent_directories=True)
    except git.InvalidGitRepositoryError:
        print_warning("Este não é um repositório Git. O modo de segurança com rollback não pode ser ativado.")
        print_info("Executando a ação sem a rede de segurança. Tenha cuidado.")
        action_func()
        return

    if repo.is_dirty(untracked_files=True):
        print_warning("Seu repositório tem alterações não comitadas (sujas).")
        if not questionary.confirm("Deseja continuar mesmo assim? (Não recomendado)").ask():
            print_error("Operação cancelada pelo usuário.")
            return
    
    restore_commit_sha = repo.head.commit.hexsha
    print_info(f"🔐 Criando ponto de restauração Git ({restore_commit_sha[:7]})...")
    repo.git.add(A=True)
    repo.index.commit(f"VÉRTICE: Ponto de restauração automático antes de '{command_name}'")
    
    action_succeeded = action_func()

    if not action_succeeded:
        print_warning(f"Ação '{command_name}' falhou ou foi cancelada. Revertendo para o ponto de restauração...")
        repo.git.reset("--hard", restore_commit_sha)
        print_success("Rollback concluído. Seu código está seguro.")
        return
        
    console.print("\n✨ [bold]Alterações aplicadas. Revise o que mudou:[/bold]")
    
    diff_output = repo.git.diff("HEAD~1", "HEAD")
    console.print(Syntax(diff_output, "diff", theme="monokai", line_numbers=True))

    manter = questionary.confirm("Manter estas alterações?").ask()

    if manter:
        print_success("Alterações mantidas. O commit final foi mesclado.")
        repo.index.commit(f"feat(VÉRTICE): Aplica alterações via '{command_name}'", amend=True)
    else:
        print_warning("Revertendo alterações conforme solicitado...")
        repo.git.reset("--hard", restore_commit_sha)
        print_success("Rollback concluído. Seu código está seguro.")
