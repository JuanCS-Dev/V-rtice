# vertice_cli/main_cli.py

import typer
import questionary
from rich.panel import Panel
from modules import cyber, osint
from utils import console, print_banner, AuthManager

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
    """📊 Status dos serviços do Vértice"""
    console.print("[yellow]🔄 Verificando status dos serviços...[/yellow]")

    # TODO: Implementar verificação de status dos microserviços
    services = [
        ("API Gateway", "http://localhost:8000", "🟢 Online"),
        ("OSINT Service", "http://localhost:8001", "🟢 Online"),
        ("IP Intel Service", "http://localhost:8002", "🟢 Online"),
        ("Vulnerability Scanner", "http://localhost:8011", "🟡 Protegido"),
        ("Social Engineering", "http://localhost:8012", "🟡 Protegido")
    ]

    from rich.table import Table
    table = Table(title="Status dos Serviços Vértice")
    table.add_column("Serviço", style="cyan")
    table.add_column("URL", style="blue")
    table.add_column("Status", style="white")

    for service, url, status in services:
        table.add_row(service, url, status)

    console.print(table)

if __name__ == "__main__":
    app()