"""
Interactive Menu Command for Vertice CLI Terminal.
Modern, categorized menu with cascading navigation using Questionary.
"""

import typer
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from typing import Optional, List, Dict, Any

console = Console()

app = typer.Typer(
    name="menu",
    help="📋 Interactive menu with categorized tools",
    rich_markup_mode="rich",
)

# Menu categories and commands
MENU_STRUCTURE = {
    "🔍 Intelligence": {
        "icon": "🔍",
        "commands": [
            {"name": "IP Analysis", "command": "vcli ip analyze"},
            {"name": "My IP Detection", "command": "vcli ip my-ip"},
            {"name": "Bulk IP Analysis", "command": "vcli ip bulk"},
            {"name": "Threat Lookup", "command": "vcli threat lookup"},
            {"name": "Threat Check", "command": "vcli threat check"},
        ],
    },
    "🛡️ Defense": {
        "icon": "🛡️",
        "commands": [
            {"name": "ADR Status", "command": "vcli adr status"},
            {"name": "ADR Metrics", "command": "vcli adr metrics"},
            {"name": "Malware Analysis", "command": "vcli malware analyze"},
            {"name": "YARA Scan", "command": "vcli malware yara"},
            {"name": "Hash Lookup", "command": "vcli malware hash"},
        ],
    },
    "🤖 AI Operations": {
        "icon": "🤖",
        "commands": [
            {"name": "Ask Maximus", "command": "vcli maximus ask"},
            {"name": "Maximus Analysis", "command": "vcli maximus analyze"},
            {"name": "Incident Investigation", "command": "vcli maximus investigate"},
            {"name": "Oráculo (Self-improvement)", "command": "vcli maximus oraculo"},
            {"name": "Eureka (Code Analysis)", "command": "vcli maximus eureka"},
        ],
    },
    "🌐 Network Operations": {
        "icon": "🌐",
        "commands": [
            {"name": "Port Scan", "command": "vcli scan ports"},
            {"name": "Nmap Scan", "command": "vcli scan nmap"},
            {"name": "Vulnerability Scan", "command": "vcli scan vulns"},
            {"name": "Network Discovery", "command": "vcli scan network"},
            {"name": "Monitor Threats", "command": "vcli monitor threats"},
        ],
    },
    "🔎 Threat Hunting": {
        "icon": "🔎",
        "commands": [
            {"name": "IOC Search", "command": "vcli hunt search"},
            {"name": "Incident Timeline", "command": "vcli hunt timeline"},
            {"name": "Pivot Analysis", "command": "vcli hunt pivot"},
            {"name": "IOC Correlation", "command": "vcli hunt correlate"},
        ],
    },
    "⚙️  Configuration": {
        "icon": "⚙️",
        "commands": [
            {"name": "View Config", "command": "cat ~/.vertice/config.yaml"},
            {
                "name": "Edit Config",
                "command": "${EDITOR:-nano} ~/.vertice/config.yaml",
            },
            {"name": "Clear Cache", "command": "rm -rf ~/.vertice/cache/*"},
        ],
    },
}


def display_menu_header():
    """Display menu header with style."""
    title = Text()
    title.append("╔══════════════════════════════════════════╗\n", style="bright_cyan")
    title.append("║   ", style="bright_cyan")
    title.append("🎯 VÉRTICE CLI - Interactive Menu", style="bold bright_green")
    title.append("   ║\n", style="bright_cyan")
    title.append("╚══════════════════════════════════════════╝", style="bright_cyan")

    panel = Panel(Align.center(title), border_style="bright_green", padding=(1, 2))
    console.print()
    console.print(panel)
    console.print()


def show_category_menu() -> Optional[str]:
    """Show main category selection menu."""
    display_menu_header()

    categories = list(MENU_STRUCTURE.keys()) + ["🚪 Exit"]

    choice = questionary.select(
        "Select a category:",
        choices=categories,
        style=questionary.Style(
            [
                ("qmark", "fg:#00ff00 bold"),
                ("question", "bold fg:#00ffff"),
                ("answer", "fg:#00ff00 bold"),
                ("pointer", "fg:#00ff00 bold"),
                ("highlighted", "fg:#00ff00 bold"),
                ("selected", "fg:#00ffaa"),
            ]
        ),
        use_indicator=True,
        use_shortcuts=True,
        instruction="(Use arrow keys)",
    ).ask()

    return choice


def show_command_menu(category: str) -> Optional[str]:
    """Show command selection menu for a category."""
    console.clear()

    # Header for category
    header = Text()
    header.append(f"\n{MENU_STRUCTURE[category]['icon']} ", style="bright_green")
    header.append(category, style="bold bright_cyan")
    header.append(" - Select Command\n", style="dim")

    console.print(Panel(Align.center(header), border_style="cyan", padding=(1, 2)))
    console.print()

    commands_data = MENU_STRUCTURE[category]["commands"]
    # Type annotation to satisfy mypy
    commands: List[Dict[str, Any]] = commands_data  # type: ignore
    command_names: List[str] = [cmd["name"] for cmd in commands] + [
        "⬅️  Back to Categories"
    ]

    choice = questionary.select(
        "Select a command:",
        choices=command_names,
        style=questionary.Style(
            [
                ("qmark", "fg:#00ffff bold"),
                ("question", "bold fg:#00ff00"),
                ("answer", "fg:#00ffff bold"),
                ("pointer", "fg:#00ffff bold"),
                ("highlighted", "fg:#00ffff bold"),
                ("selected", "fg:#00ffaa"),
            ]
        ),
        use_indicator=True,
        use_shortcuts=True,
        instruction="(Use arrow keys)",
    ).ask()

    if choice and choice != "⬅️  Back to Categories":
        # Find the actual command
        for cmd in commands:
            cmd_dict: Dict[str, Any] = cmd  # type: ignore
            if cmd_dict["name"] == choice:
                return cmd_dict["command"]

    return None


def execute_command(command: str):
    """Display command for user to execute."""
    console.print()
    console.print(
        Panel(
            f"[bold cyan]Command:[/bold cyan] [bright_green]{command}[/bright_green]\n\n"
            f"[dim]Copy and paste this command to execute it.[/dim]",
            title="[bold bright_yellow]⚡ Command Ready[/bold bright_yellow]",
            border_style="bright_yellow",
            padding=(1, 3),
        )
    )
    console.print()

    # Ask if user wants to continue
    continue_choice = questionary.confirm(
        "Return to menu?",
        default=True,
        style=questionary.Style(
            [
                ("qmark", "fg:#ffff00 bold"),
                ("question", "bold"),
                ("answer", "fg:#00ff00 bold"),
            ]
        ),
    ).ask()

    return continue_choice


@app.command(name="interactive")
def interactive():
    """
    Launch interactive menu with categorized tools.

    Navigate through categories and commands using arrow keys.
    Modern UI with cascading menus and visual feedback.

    Example:
        vcli menu interactive
    """
    console.clear()

    while True:
        # Show category menu
        category = show_category_menu()

        if not category or category == "🚪 Exit":
            console.print(
                "\n[bold bright_green]👋 Goodbye! Stay secure![/bold bright_green]\n"
            )
            break

        # Show command menu for selected category
        while True:
            command = show_command_menu(category)

            if not command:
                # User chose "Back to Categories"
                break

            # Execute/display command
            continue_menu = execute_command(command)

            if not continue_menu:
                console.print(
                    "\n[bold bright_green]👋 Goodbye! Stay secure![/bold bright_green]\n"
                )
                return

            console.clear()


@app.callback(invoke_without_command=True)
def menu_callback(ctx: typer.Context):
    """Default action when 'vcli menu' is called without subcommand."""
    if ctx.invoked_subcommand is None:
        # Launch interactive menu by default
        interactive()
