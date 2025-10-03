import json
from contextlib import contextmanager
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.markdown import Markdown
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text
from rich.align import Align
from typing import Dict, Any, List
import questionary

# Instância única e global do console, para ser usada em toda a CLI.
console = Console()

def create_panel(content: Any, title: str, border_style: str) -> Panel:
    """Cria um painel Rich padronizado para consistência visual."""
    return Panel(content, title=f"[bold {border_style}]{title}[/bold {border_style}]", border_style=border_style, expand=False)

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

def output_json(data: Dict[str, Any]):
    """Imprime um dicionário como JSON formatado e com syntax highlighting."""
    if not isinstance(data, (dict, list)):
        print_error("A função output_json recebeu um tipo de dado inválido.")
        return
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    console.print(Syntax(json_str, "json", theme="monokai", line_numbers=True, word_wrap=True))

# Alias para compatibilidade
print_json = output_json

def print_table(data, title: str = "Data Table"):
    """
    Imprime dados como uma tabela Rich, com estilo VÉRTICE e tratamento para dados aninhados.

    Args:
        data: Dict ou List[Dict] para exibir
        title: Título da tabela
    """
    if not data:
        print_warning("Nenhum dado para exibir na tabela.")
        return

    table = Table(title=f"[bold cyan]{title}[/bold cyan]", show_header=True, header_style="bold magenta", border_style="cyan")

    # Se é uma lista de dicts, cria colunas dinamicamente
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        # Pega as keys do primeiro item
        columns = list(data[0].keys())
        for col in columns:
            table.add_column(str(col), style="bright_cyan")

        # Adiciona as rows
        for row in data:
            table.add_row(*[str(row.get(col, '')) for col in columns])

    # Se é um dict, formato chave-valor
    elif isinstance(data, dict):
        table.add_column("Campo", style="bright_cyan", no_wrap=True)
        table.add_column("Valor", style="white")

        for key, value in data.items():
            # Trata dados aninhados (listas, dicts) para exibição limpa
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value, indent=2, ensure_ascii=False)
                table.add_row(str(key), Syntax(value_str, "json", theme="monokai"))
            else:
                table.add_row(str(key), str(value))

    console.print(table)

def print_maximus_response(data: Dict[str, Any]):
    """
    Formata e imprime a resposta da Maximus AI de forma inteligente,
    detectando se o conteúdo é JSON, Markdown ou texto puro.
    """
    response_text = data.get("response", "[dim]Nenhuma resposta encontrada no payload.[/dim]")
    
    # Tenta interpretar a resposta como JSON
    try:
        # Remove ```json ... ``` se presente
        cleaned_text = response_text.strip()
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:-3].strip()
        
        parsed_json = json.loads(cleaned_text)
        content = Syntax(json.dumps(parsed_json, indent=2, ensure_ascii=False), "json", theme="monokai", line_numbers=True, word_wrap=True)
        title = "📄 Maximus AI (JSON)"

    except (json.JSONDecodeError, TypeError):
        # Se não for JSON, trata como Markdown (que também renderiza texto puro)
        content = Markdown(response_text)
        title = "🧠 Maximus AI (Markdown/Texto)"

    console.print(create_panel(content, title, "bright_magenta"))

def get_threat_color(level: str) -> str:
    """Retorna cor baseada em threat level para uso com Rich markup."""
    colors = {
        'critical': 'red',
        'high': 'orange3',
        'medium': 'yellow',
        'low': 'green',
        'unknown': 'dim'
    }
    return colors.get(str(level).lower(), 'white')

# ============================================================================
# SPINNERS MODERNOS (Quadradinhos/Aesthetic)
# ============================================================================

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
    # Spinner quadradinho customizado
    spinner = Spinner("aesthetic", text=f"[bold bright_cyan]{message}[/bold bright_cyan]", style="bright_green")

    with Live(spinner, console=console, transient=True, refresh_per_second=20):
        yield

# ============================================================================
# INPUT FORMATADO ESTILO GEMINI CLI (RETÂNGULO BONITO)
# ============================================================================

def styled_input(prompt: str, password: bool = False, default: str = "") -> str:
    """
    Input formatado com retângulo bonito estilo Gemini CLI.

    Args:
        prompt: Texto do prompt
        password: Se True, esconde o input
        default: Valor padrão

    Returns:
        String com o input do usuário

    Example:
        >>> ip = styled_input("Enter IP address")
        >>> password = styled_input("Enter password", password=True)
    """
    # Cria o prompt formatado em retângulo
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

    # Input com questionary (estilizado)
    if password:
        result = questionary.password(
            "➤ ",
            style=questionary.Style([
                ('qmark', 'fg:#00ff00 bold'),
                ('answer', 'fg:#00ffaa bold'),
            ])
        ).ask()
    else:
        result = questionary.text(
            "➤ ",
            default=default,
            style=questionary.Style([
                ('qmark', 'fg:#00ff00 bold'),
                ('answer', 'fg:#00ffaa bold'),
            ])
        ).ask()

    return result or ""

def styled_confirm(prompt: str, default: bool = True) -> bool:
    """
    Confirmação formatada com retângulo bonito.

    Args:
        prompt: Texto da pergunta
        default: Valor padrão (True/False)

    Returns:
        Boolean com a resposta do usuário
    """
    # Cria o prompt formatado
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
        style=questionary.Style([
            ('qmark', 'fg:#ffff00 bold'),
            ('question', 'bold'),
            ('answer', 'fg:#00ff00 bold'),
        ])
    ).ask()

    return result if result is not None else default

def styled_select(prompt: str, choices: List[str]) -> str:
    """
    Seleção formatada com retângulo bonito.

    Args:
        prompt: Texto do prompt
        choices: Lista de opções

    Returns:
        String com a opção selecionada
    """
    # Cria o prompt formatado
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
        style=questionary.Style([
            ('qmark', 'fg:#ff00ff bold'),
            ('question', 'bold fg:#00ffff'),
            ('answer', 'fg:#ff00ff bold'),
            ('pointer', 'fg:#ff00ff bold'),
            ('highlighted', 'fg:#ff00ff bold'),
            ('selected', 'fg:#ffaaff'),
        ]),
        use_indicator=True,
        use_shortcuts=True,
    ).ask()

    return result or ""

# ============================================================================
# FORMATTERS PARA COMANDOS ESPECÍFICOS
# ============================================================================

def format_ip_analysis(data: Dict[str, Any], console_instance: Console = None):
    """
    Formata análise de IP com Rich Panel e Table.

    Args:
        data: Dicionário com dados da análise
        console_instance: Console instance (opcional)
    """
    c = console_instance or console

    ip = data.get('ip', 'N/A')
    geo = data.get('geolocation', {})
    rep = data.get('reputation', {})
    network = data.get('network', {})

    # Tabela principal
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Field", style="bold cyan", no_wrap=True)
    table.add_column("Value", style="white")

    # Geolocation
    table.add_row("[bold bright_green]📍 Location[/bold bright_green]", "")
    table.add_row("  ├─ Country", geo.get('country', 'N/A'))
    table.add_row("  ├─ City", geo.get('city', 'N/A'))
    table.add_row("  ├─ ISP", geo.get('isp', 'N/A'))
    table.add_row("  └─ ASN", geo.get('asn', 'N/A'))
    table.add_row("", "")

    # Threat Assessment
    threat_score = rep.get('score', 0)
    threat_level = rep.get('threat_level', 'unknown')
    threat_color = get_threat_color(threat_level)

    status_icon = "✓" if threat_score < 50 else "⚠"
    status_text = "CLEAN" if threat_score < 50 else "MALICIOUS"

    table.add_row("[bold bright_yellow]🛡️  Threat Assessment[/bold bright_yellow]", "")
    table.add_row("  ├─ Score", f"{threat_score}/100 ([{threat_color}]{threat_level.upper()}[/{threat_color}])")
    table.add_row("  ├─ Status", f"[{threat_color}]{status_icon} {status_text}[/{threat_color}]")
    table.add_row("  └─ Reputation", rep.get('description', 'N/A'))
    table.add_row("", "")

    # Network Info
    if network:
        table.add_row("[bold bright_blue]🌐 Network[/bold bright_blue]", "")
        table.add_row("  ├─ Open Ports", str(network.get('open_ports', 'N/A')))
        table.add_row("  └─ PTR Record", network.get('ptr', 'N/A'))

    # Panel final
    panel = Panel(
        table,
        title=f"[bold bright_cyan]🔍 IP Analysis: {ip}[/bold bright_cyan]",
        border_style="bright_cyan",
        padding=(1, 2)
    )

    c.print(panel)
    c.print(f"\n[dim]⏱  Analysis completed[/dim]")
    c.print(f"[dim]💾 Cached for 1 hour[/dim]\n")
