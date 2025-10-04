#!/usr/bin/env python3
# vertice/cli.py
import typer
from rich.console import Console
import importlib
import sys
import os

# Adiciona a raiz do projeto (vertice-terminal) ao Python path
# para permitir que o script seja executado diretamente.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importa a função do banner
from vertice.utils.banner import exibir_banner

# Lista dos nossos módulos de comando
COMMAND_MODULES = [
    "auth",
    "context",
    "ip",
    "threat",
    "adr",
    "malware",
    "maximus",
    "scan",
    "monitor",
    "hunt",
    "ask",  # AI Conversational Engine
    "policy",  # Policy-as-Code Engine
    "detect",  # Detection Engine (YARA/Sigma)
    "analytics",  # Advanced Analytics & ML
    "incident",  # Incident Response & Orchestration
    "compliance",  # Multi-framework Compliance & Reporting
    "threat_intel",  # Threat Intelligence Platform
    "dlp",  # Data Loss Prevention
    "siem",  # SIEM Integration & Log Management
    # AI-First Commands (Maximus Integration)
    "investigate",  # AI-Orchestrated Investigation
    "osint",  # OSINT Operations
    "cognitive",  # Cognitive Services
    "offensive",  # Offensive Security Arsenal
    "immunis",  # AI Immune System
    "hcl",  # Human-Centric Language
    "memory",  # Memory System Management
    "menu",
    "project",  # Workspace & State Management
]

console = Console()

# Cria a aplicação principal com Typer (o objeto 'app')
app = typer.Typer(
    name="vcli",
    help="🎯 VÉRTICE CLI - Cyber Security Command Center",
    rich_markup_mode="rich",
    add_completion=False,
)


def register_commands():
    """Importa e registra dinamicamente todos os módulos de comando."""
    for module_name in COMMAND_MODULES:
        try:
            module = importlib.import_module(
                f"vertice.commands.{module_name}"
            )
            app.add_typer(module.app, name=module_name)
        except (ImportError, AttributeError):
            # Captura tanto a falha de import quanto a ausência de 'app' no módulo
            console.print(
                f"[yellow]Aviso:[/yellow] Módulo de comando '[bold]{module_name}[/bold]' não encontrado ou com erro, pulando registro."
            )


# Registra os comandos dinamicamente
register_commands()


@app.command()
def tui():
    """
    🎨 Launch PRIMOROSO Text UI Dashboard (BETA).

    Enter a beautiful full-screen TUI with:
    - Gradiente Verde → Azul primoroso
    - Dashboard minimalista que supera Gemini CLI
    - Quick actions (1-4) para operações rápidas
    - Command Palette (Ctrl+P) para acesso completo
    - Real-time status e metrics

    Bindings:
        Ctrl+P  → Command Palette
        Ctrl+Q  → Quit
        1-4     → Quick Actions

    Example:
        vcli tui
    """
    try:
        from vertice.ui import run_tui

        run_tui()
    except ImportError as e:
        console.print(f"[red]Error: Could not load TUI: {e}[/red]")
        console.print(
            "[yellow]Install required dependencies: pip install textual textual-dev[/yellow]"
        )
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def shell():
    """
    🚀 Launch interactive VÉRTICE shell with slash commands.

    Enter an immersive cybersecurity command center with:
    - Slash commands (/) with autocomplete
    - Beautiful, contained interface
    - Command history and search
    - Real-time suggestions

    Example:
        vcli shell
    """
    try:
        from vertice.interactive_shell import main as shell_main

        shell_main()
    except ImportError as e:
        console.print(f"[red]Error: Could not load interactive shell: {e}[/red]")
        console.print(
            "[yellow]Install required dependencies: pip install prompt-toolkit[/yellow]"
        )
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error launching shell: {e}[/red]")
        raise typer.Exit(1)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False, "--version", "-v", help="Exibe a versão do vCli."
    ),
    no_banner: bool = typer.Option(
        False, "--no-banner", help="Não exibir o banner de inicialização."
    ),
    interactive: bool = typer.Option(
        False, "--interactive", "-i", help="Launch interactive shell"
    ),
):
    """
    Ponto de entrada principal do vCli.
    """
    if version:
        console.print("vCli Versão: 1.0.0")
        raise typer.Exit()

    if interactive:
        shell()
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        if not no_banner:
            exibir_banner()
        console.print(ctx.get_help())


if __name__ == "__main__":
    app()