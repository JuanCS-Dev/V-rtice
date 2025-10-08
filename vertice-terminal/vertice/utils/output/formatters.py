"""Data formatters for CLI output."""

import json
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table
from rich.markdown import Markdown
from rich.panel import Panel
from typing import Dict, Any, List

from .console_utils import print_error, print_warning, create_panel

console = Console()


def output_json(data: Dict[str, Any]):
    """Imprime um dicionário como JSON formatado e com syntax highlighting."""
    if not isinstance(data, (dict, list)):
        print_error("A função output_json recebeu um tipo de dado inválido.")
        return
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    console.print(
        Syntax(json_str, "json", theme="monokai", line_numbers=True, word_wrap=True)
    )


print_json = output_json


def print_table(data, title: str = "Data Table"):
    """
    Imprime dados como uma tabela Rich, com estilo VÉRTICE e tratamento para dados aninhados.
    Alinhada ao Blueprint UI/UX v1.2 (Gemini-style)
    """
    if not data:
        print_warning("Nenhum dado para exibir na tabela.")
        return

    table = Table(
        title=f"[bold deep_sky_blue1]{title}[/bold deep_sky_blue1]",
        show_header=True,
        header_style="bold medium_purple",
        border_style="grey50",
        row_styles=["", "dim"],  # Row striping sutil
    )

    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        columns = list(data[0].keys())
        for col in columns:
            table.add_column(str(col), style="deep_sky_blue1")
        for row in data:
            table.add_row(*[str(row.get(col, "")) for col in columns])
    elif isinstance(data, dict):
        table.add_column("Campo", style="deep_sky_blue1", no_wrap=True)
        table.add_column("Valor", style="bright_white")
        for key, value in data.items():
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
    response_text = data.get(
        "response", "[dim]Nenhuma resposta encontrada no payload.[/dim]"
    )

    try:
        cleaned_text = response_text.strip()
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:-3].strip()

        parsed_json = json.loads(cleaned_text)
        content = Syntax(
            json.dumps(parsed_json, indent=2, ensure_ascii=False),
            "json",
            theme="monokai",
            line_numbers=True,
            word_wrap=True,
        )
        title = "📄 Maximus AI (JSON)"

    except (json.JSONDecodeError, TypeError):
        markdown_content = Markdown(response_text)
        title = "🧠 Maximus AI (Markdown/Texto)"
        console.print(create_panel(markdown_content, title, "bright_magenta"))
        return

    console.print(create_panel(content, title, "bright_magenta"))


def get_threat_color(level: str) -> str:
    """
    Retorna cor baseada em threat level para uso com Rich markup.
    Alinhada ao Blueprint UI/UX v1.2
    """
    colors = {
        "critical": "bright_red",      # Blueprint
        "high": "gold1",                # Blueprint (warning)
        "medium": "gold1",              # Blueprint (warning)
        "low": "green_yellow",          # Blueprint (success)
        "unknown": "grey70",            # Blueprint (secondary text)
    }
    return colors.get(str(level).lower(), "bright_white")


def format_ip_analysis(data: Dict[str, Any], console_instance: Console = None):
    """
    Formata análise de IP com Rich Panel e Table.
    Alinhada ao Blueprint UI/UX v1.2 (Gemini-style)
    """
    c = console_instance or console

    ip = data.get("ip", "N/A")
    geo = data.get("geolocation", {})
    rep = data.get("reputation", {})
    network = data.get("network", {})

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Field", style="bold deep_sky_blue1", no_wrap=True)
    table.add_column("Value", style="bright_white")

    table.add_row("[bold green_yellow]📍 Location[/bold green_yellow]", "")
    table.add_row("  ├─ Country", geo.get("country", "N/A"))
    table.add_row("  ├─ City", geo.get("city", "N/A"))
    table.add_row("  ├─ ISP", geo.get("isp", "N/A"))
    table.add_row("  └─ ASN", geo.get("asn", "N/A"))
    table.add_row("", "")

    threat_score = rep.get("score", 0)
    threat_level = rep.get("threat_level", "unknown")
    threat_color = get_threat_color(threat_level)

    status_icon = "✓" if threat_score < 50 else "⚠"
    status_text = "CLEAN" if threat_score < 50 else "MALICIOUS"

    table.add_row("[bold gold1]🛡️  Threat Assessment[/bold gold1]", "")
    table.add_row(
        "  ├─ Score",
        f"{threat_score}/100 ([{threat_color}]{threat_level.upper()}[/{threat_color}])",
    )
    table.add_row(
        "  ├─ Status", f"[{threat_color}]{status_icon} {status_text}[/{threat_color}]"
    )
    table.add_row("  └─ Reputation", rep.get("description", "N/A"))
    table.add_row("", "")

    if network:
        table.add_row("[bold deep_sky_blue1]🌐 Network[/bold deep_sky_blue1]", "")
        table.add_row("  ├─ Open Ports", str(network.get("open_ports", "N/A")))
        table.add_row("  └─ PTR Record", network.get("ptr", "N/A"))

    panel = Panel(
        table,
        title=f"[bold deep_sky_blue1]🔍 IP Analysis: {ip}[/bold deep_sky_blue1]",
        border_style="grey50",
        padding=(1, 2),
    )

    c.print(panel)
    c.print(f"\n[grey70]⏱  Analysis completed[/grey70]")
    c.print(f"[grey70]💾 Cached for 1 hour[/grey70]\n")
