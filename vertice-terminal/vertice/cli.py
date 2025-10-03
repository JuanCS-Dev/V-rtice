# vertice/cli.py
import typer
from rich.console import Console
import importlib
import sys

# Importa a função do banner
from .utils.banner import exibir_banner

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
    "menu",
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
                f".commands.{module_name}", package="vertice"
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
        from .interactive_shell import main as shell_main

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
        None, "--version", "-v", help="Exibe a versão do vCli."
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
