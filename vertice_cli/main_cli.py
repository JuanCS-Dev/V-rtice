# vertice_cli/main_cli.py

import typer
import questionary
from rich.panel import Panel
from rich.table import Table
from modules import cyber, osint
from utils import console, print_banner, AuthManager, print_info, print_error
from utils.api_client import VerticeAPI

app = typer.Typer(
    help="🚀 VÉRTICE CLI - Cyber Security Toolkit para especialistas",
    rich_markup_mode="rich"
)

# Adicionar submódulos
app.add_typer(cyber.app, name="cyber", help="🛡️ Cyber Security Module")
app.add_typer(osint.app, name="osint", help="🔍 OSINT Module")

@app.command()
def login(email: str = typer.Option(None, help="Email para login")):
    """🔐 Realizar login no sistema Vértice"""
    auth = AuthManager()
    if auth.login(email):
        console.print("✅ [green]Login realizado com sucesso![/green]")
    else:
        console.print("❌ [red]Falha no login[/red]")

@app.command()
def logout():
    """🚪 Realizar logout do sistema"""
    auth = AuthManager()
    auth.logout()

@app.command()
def menu():
    """🎯 Menu interativo principal do Vértice CLI"""
    auth = AuthManager()

    print_banner()

    if not auth.is_authenticated():
        console.print("[yellow]⚠️ Você não está autenticado[/yellow]")
        do_login = questionary.confirm("Deseja fazer login?").ask()
        if do_login:
            if not auth.login():
                console.print("[red]❌ Login necessário para continuar[/red]")
                return
        else:
            console.print("[red]❌ Autenticação necessária para usar o Vértice CLI[/red]")
            return

    user_info = auth.get_user_info()
    console.print(f"[green]👤 Logado como: {user_info['email']}[/green]\n")

    while True:
        choices = [
            "🛡️ Cyber Security Module",
            "🔍 OSINT Module",
            "📊 Network Monitor Module [EM BREVE]",
            "🔐 Configurações de Autenticação",
            "🚪 Sair"
        ]

        choice = questionary.select(
            "Selecione um módulo:",
            choices=choices
        ).ask()

        if "Cyber Security" in choice:
            cyber.menu()
        elif "OSINT" in choice:
            osint.menu()
        elif "Autenticação" in choice:
            auth_menu(auth)
        elif "Sair" in choice:
            console.print("[cyan]👋 Até logo![/cyan]")
            break
        else:
            console.print("[yellow]⚠️ Módulo em desenvolvimento[/yellow]")

def auth_menu(auth: AuthManager):
    """Menu de configurações de autenticação"""
    while True:
        choices = [
            "👤 Informações da conta",
            "🚪 Logout",
            "🔙 Voltar"
        ]

        choice = questionary.select(
            "Configurações:",
            choices=choices
        ).ask()

        if "Informações" in choice:
            user_info = auth.get_user_info()
            info_panel = Panel.fit(
                f"[cyan]Email:[/cyan] {user_info['email']}\n"
                f"[cyan]Status:[/cyan] {'✅ Autenticado' if user_info['authenticated'] else '❌ Não autenticado'}"
            )
            console.print(info_panel)
        elif "Logout" in choice:
            auth.logout()
            console.print("[green]✅ Logout realizado com sucesso![/green]")
            break
        else:
            break

@app.command()
def status():
    """📊 Verifica o status dos microserviços do Vértice."""
    print_info("🔄 Verificando status dos serviços do Vértice...")
    api = VerticeAPI()

    services_to_check = {
        "API Gateway": {"url": "http://localhost:8000", "endpoint": "/health"},
        "Auth Service": {"url": "http://localhost:8000", "endpoint": "/auth/health"}, # Assuming auth is part of API Gateway or has a health endpoint
        "OSINT Service": {"url": "http://localhost:8001", "endpoint": "/health"},
        "IP Intel Service": {"url": "http://localhost:8002", "endpoint": "/health"},
        "Vulnerability Scanner": {"url": "http://localhost:8011", "endpoint": "/health"},
        "Social Engineering": {"url": "http://localhost:8012", "endpoint": "/health"},
        # Adicione outros serviços conforme necessário
    }

    table = Table(title="Status dos Serviços Vértice", show_header=True, header_style="bold bright_cyan")
    table.add_column("Serviço", style="cyan", justify="left")
    table.add_column("URL Base", style="blue", justify="left")
    table.add_column("Status", style="white", justify="center")
    table.add_column("Detalhes", style="dim", justify="left")

    for service_name, service_data in services_to_check.items():
        base_url = service_data["url"]
        endpoint = service_data["endpoint"]
        full_url = f"{base_url}{endpoint}"
        
        try:
            response = api.check_service_health(base_url, endpoint)
            if response and response.get("status") == "ok":
                status_text = "[bold green]🟢 Online[/bold green]"
                details = response.get("message", "N/A")
            else:
                status_text = "[bold red]🔴 Offline[/bold red]"
                details = response.get("message", "Não respondeu ou status inválido")
        except Exception as e:
            status_text = "[bold red]🔴 Offline[/bold red]"
            details = f"Erro de conexão: {e}"
        
        table.add_row(service_name, base_url, status_text, details)

    console.print(table)
    print_info("Verificação de status concluída.")

if __name__ == "__main__":
    app()