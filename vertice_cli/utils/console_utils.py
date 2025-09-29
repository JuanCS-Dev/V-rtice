# vertice_cli/utils/console_utils.py

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# Console global para output formatado
console = Console()

def print_success(message: str) -> None:
    """Imprime mensagem de sucesso em verde"""
    console.print(f"✅ {message}", style="green")

def print_error(message: str) -> None:
    """Imprime mensagem de erro em vermelho"""
    console.print(f"❌ {message}", style="red")

def print_warning(message: str) -> None:
    """Imprime mensagem de aviso em amarelo"""
    console.print(f"⚠️ {message}", style="yellow")

def print_info(message: str) -> None:
    """Imprime mensagem informativa em azul"""
    console.print(f"ℹ️ {message}", style="blue")

def print_banner():
    """Imprime banner do Vértice CLI"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║        🚀 VÉRTICE CLI - CYBER SECURITY TOOLKIT 🚀           ║
    ║                                                              ║
    ║        Ferramentas avançadas para especialistas em          ║
    ║              segurança e inteligência digital               ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╛
    """
    console.print(Panel(banner, style="cyan"))

def create_results_table(title: str, data: dict, headers: list = None) -> Table:
    """Cria tabela formatada para resultados"""
    table = Table(title=title, show_header=True, header_style="bold magenta")

    if headers:
        for header in headers:
            table.add_column(header)
    else:
        table.add_column("Campo", style="cyan")
        table.add_column("Valor", style="white")

    if isinstance(data, dict):
        for key, value in data.items():
            table.add_row(str(key), str(value))

    return table

def format_vulnerability_result(vuln_data: dict) -> None:
    """Formata e exibe resultados de vulnerabilidade"""
    if not vuln_data:
        print_error("Nenhum dado de vulnerabilidade para exibir")
        return

    # Criar tabela principal
    table = Table(title="🎯 Vulnerabilidades Detectadas", show_header=True)
    table.add_column("Severidade", style="red")
    table.add_column("Serviço", style="cyan")
    table.add_column("Porta", style="yellow")
    table.add_column("Descrição", style="white")

    vulnerabilities = vuln_data.get("vulnerabilities", [])
    for vuln in vulnerabilities:
        severity_style = {
            "critical": "bold red",
            "high": "red",
            "medium": "yellow",
            "low": "green"
        }.get(vuln.get("severity", "").lower(), "white")

        table.add_row(
            f"[{severity_style}]{vuln.get('severity', 'N/A')}[/{severity_style}]",
            vuln.get("service", "N/A"),
            str(vuln.get("port", "N/A")),
            vuln.get("description", "N/A")[:50] + "..." if len(vuln.get("description", "")) > 50 else vuln.get("description", "N/A")
        )

    console.print(table)

def format_osint_result(osint_data: dict, result_type: str) -> None:
    """Formata resultados OSINT baseado no tipo"""
    if not osint_data:
        print_error(f"Nenhum dado OSINT para exibir ({result_type})")
        return

    if result_type == "email":
        _format_email_result(osint_data)
    elif result_type == "phone":
        _format_phone_result(osint_data)
    elif result_type == "social":
        _format_social_result(osint_data)
    else:
        # Formato genérico
        table = create_results_table(f"📊 Resultados {result_type.upper()}", osint_data)
        console.print(table)

def _format_email_result(data: dict) -> None:
    """Formatar resultado de análise de email"""
    console.print(Panel.fit(f"📧 Análise de Email: [cyan]{data.get('email', 'N/A')}[/cyan]"))

    # Info básica
    basic_table = Table(title="Informações Básicas", show_header=False)
    basic_table.add_column("Campo", style="cyan")
    basic_table.add_column("Valor")

    basic_table.add_row("Domínio", data.get("domain", "N/A"))
    basic_table.add_row("Formato Válido", "✅ Sim" if data.get("valid_format") else "❌ Não")
    basic_table.add_row("Spam Listed", "❌ Sim" if data.get("reputation", {}).get("spam_listed") else "✅ Não")

    console.print(basic_table)

    # Vazamentos
    if data.get("breaches"):
        breach_table = Table(title="🚨 Vazamentos Detectados", show_header=True)
        breach_table.add_column("Fonte", style="red")
        breach_table.add_column("Ano", style="yellow")
        breach_table.add_column("Severidade", style="orange")

        for breach in data["breaches"]:
            breach_table.add_row(
                breach.get("source", "N/A"),
                str(breach.get("year", "N/A")),
                breach.get("severity", "N/A")
            )
        console.print(breach_table)

def _format_phone_result(data: dict) -> None:
    """Formatar resultado de análise de telefone"""
    console.print(Panel.fit(f"📱 Análise de Telefone: [cyan]{data.get('phone', 'N/A')}[/cyan]"))

    # TODO: Implementar formatação específica para telefone

def _format_social_result(data: dict) -> None:
    """Formatar resultado de análise de redes sociais"""
    console.print(Panel.fit(f"🌐 Perfil Social: [cyan]{data.get('identifier', 'N/A')}[/cyan] - {data.get('platform', 'N/A')}"))

    # TODO: Implementar formatação específica para redes sociais