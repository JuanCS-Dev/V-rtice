import json
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.markdown import Markdown
from typing import Dict, Any

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
    if not isinstance(data, dict):
        print_error("A função output_json recebeu um tipo de dado inválido.")
        return
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    console.print(Syntax(json_str, "json", theme="monokai", line_numbers=True, word_wrap=True))

def print_table(data: Dict[str, Any], title: str):
    """Imprime dados como uma tabela Rich, com estilo VÉRTICE e tratamento para dados aninhados."""
    if not data:
        print_warning("Nenhum dado para exibir na tabela.")
        return

    table = Table(title=f"[bold cyan]{title}[/bold cyan]", show_header=True, header_style="bold magenta", border_style="cyan")
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

def print_aurora_response(data: Dict[str, Any]):
    """
    Formata e imprime a resposta da Aurora AI de forma inteligente,
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
        title = "📄 Aurora AI (JSON)"

    except (json.JSONDecodeError, TypeError):
        # Se não for JSON, trata como Markdown (que também renderiza texto puro)
        content = Markdown(response_text)
        title = "🧠 Aurora AI (Markdown/Texto)"

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
