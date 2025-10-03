"""
VÉRTICE Interactive Shell
Modern, self-contained CLI with slash commands and autocomplete.
"""
import asyncio
import os
import sys
from typing import List, Optional, Dict, Any
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align

console = Console()

# Command registry
COMMANDS = {
    "auth": {
        "description": "Authentication and user management",
        "subcommands": {
            "login": "Login to VÉRTICE platform",
            "logout": "Logout from VÉRTICE",
            "status": "Check authentication status",
            "whoami": "Display current user info"
        }
    },
    "ip": {
        "description": "IP Intelligence and analysis operations",
        "subcommands": {
            "analyze": "Analyze an IP address",
            "my-ip": "Detect your public IP",
            "bulk": "Bulk IP analysis from file"
        }
    },
    "threat": {
        "description": "Threat intelligence operations",
        "subcommands": {
            "lookup": "Lookup threat information",
            "check": "Check for threats",
            "feed": "Access threat feeds"
        }
    },
    "adr": {
        "description": "ADR (Automated Detection & Response)",
        "subcommands": {
            "status": "Check ADR status",
            "metrics": "View ADR metrics",
            "alerts": "List active alerts"
        }
    },
    "malware": {
        "description": "Malware analysis and detection",
        "subcommands": {
            "analyze": "Analyze a file for malware",
            "yara": "Run YARA scan",
            "hash": "Hash lookup",
            "submit": "Submit file for analysis"
        }
    },
    "maximus": {
        "description": "Maximus AI - Central intelligence",
        "subcommands": {
            "ask": "Ask Maximus a question",
            "analyze": "AI-powered analysis",
            "investigate": "Incident investigation",
            "oraculo": "Self-improvement mode",
            "eureka": "Code analysis mode"
        }
    },
    "scan": {
        "description": "Network and port scanning",
        "subcommands": {
            "ports": "Port scanning",
            "nmap": "Nmap scan",
            "vulns": "Vulnerability scanning",
            "network": "Network discovery"
        }
    },
    "monitor": {
        "description": "Real-time monitoring",
        "subcommands": {
            "threats": "Monitor threats",
            "network": "Network monitoring",
            "logs": "Log monitoring"
        }
    },
    "hunt": {
        "description": "Threat hunting operations",
        "subcommands": {
            "search": "IOC search",
            "timeline": "Incident timeline",
            "pivot": "Pivot analysis",
            "correlate": "IOC correlation"
        }
    },
    "menu": {
        "description": "Interactive menu",
        "subcommands": {
            "interactive": "Launch interactive menu"
        }
    },
    "help": {
        "description": "Show help information",
        "subcommands": {}
    },
    "exit": {
        "description": "Exit VÉRTICE shell",
        "subcommands": {}
    },
    "clear": {
        "description": "Clear screen",
        "subcommands": {}
    }
}


class SlashCommandCompleter(Completer):
    """Autocompleter for slash commands."""

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor

        # Only complete if starts with /
        if not text.startswith('/'):
            return

        # Remove the leading slash
        text = text[1:]
        parts = text.split()

        if len(parts) == 0:
            # Show all commands
            for cmd in COMMANDS.keys():
                yield Completion(cmd, start_position=-len(text), display=f"/{cmd}")
        elif len(parts) == 1:
            # Complete command name
            word = parts[0]
            for cmd in COMMANDS.keys():
                if cmd.startswith(word):
                    remaining = cmd[len(word):]
                    yield Completion(
                        remaining,
                        start_position=0,
                        display=f"/{cmd}",
                        display_meta=COMMANDS[cmd]["description"]
                    )
        elif len(parts) == 2:
            # Complete subcommand
            cmd = parts[0]
            subword = parts[1]
            if cmd in COMMANDS and COMMANDS[cmd]["subcommands"]:
                for subcmd, desc in COMMANDS[cmd]["subcommands"].items():
                    if subcmd.startswith(subword):
                        remaining = subcmd[len(subword):]
                        yield Completion(
                            remaining,
                            start_position=0,
                            display=subcmd,
                            display_meta=desc
                        )


def display_banner():
    """Display the VÉRTICE banner."""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   ██╗   ██╗███████╗██████╗ ████████╗██╗ ██████╗███████╗  ║
║   ██║   ██║██╔════╝██╔══██╗╚══██╔══╝██║██╔════╝██╔════╝  ║
║   ██║   ██║█████╗  ██████╔╝   ██║   ██║██║     █████╗    ║
║   ╚██╗ ██╔╝██╔══╝  ██╔══██╗   ██║   ██║██║     ██╔══╝    ║
║    ╚████╔╝ ███████╗██║  ██║   ██║   ██║╚██████╗███████╗  ║
║     ╚═══╝  ╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝ ╚═════╝╚══════╝  ║
║                                                           ║
║            🔒 Cybersecurity Command Center 🔒             ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
"""
    console.print(banner, style="bold cyan")
    console.print()
    console.print("  [bold green]Welcome to VÉRTICE Interactive Shell[/bold green]")
    console.print("  [dim]Type /help for available commands or start typing / for autocomplete[/dim]")
    console.print()


def display_help():
    """Display help information."""
    console.print("\n[bold cyan]╔══════════════════════════════════════════╗[/bold cyan]")
    console.print("[bold cyan]║[/bold cyan]  [bold green]VÉRTICE Available Commands[/bold green]          [bold cyan]║[/bold cyan]")
    console.print("[bold cyan]╚══════════════════════════════════════════╝[/bold cyan]\n")

    for cmd, info in COMMANDS.items():
        console.print(f"  [bold green]/{cmd}[/bold green]")
        console.print(f"    [dim]{info['description']}[/dim]")

        if info["subcommands"]:
            for subcmd, desc in info["subcommands"].items():
                console.print(f"      [cyan]/{cmd} {subcmd}[/cyan] - {desc}")
        console.print()


def get_bottom_toolbar():
    """Bottom toolbar with tips."""
    return HTML(
        '<b>[VÉRTICE]</b> '
        'Press <b>Ctrl+C</b> to cancel | '
        '<b>Ctrl+D</b> to exit | '
        'Type <b>/help</b> for commands'
    )


def create_prompt_style():
    """Create custom style for the prompt."""
    return Style.from_dict({
        'prompt': '#00ff00 bold',
        'bracket': '#00ffff',
        'path': '#ffff00',
        'bottom-toolbar': 'bg:#333333 #ffffff',
    })


async def execute_command(command: str) -> bool:
    """
    Execute a command.
    Returns False if should exit, True otherwise.
    """
    command = command.strip()

    if not command:
        return True

    # Handle slash commands
    if command.startswith('/'):
        parts = command[1:].split()
        if not parts:
            return True

        cmd = parts[0]
        args = parts[1:] if len(parts) > 1 else []

        # Built-in commands
        if cmd == "exit":
            return False
        elif cmd == "clear":
            console.clear()
            display_banner()
            return True
        elif cmd == "help":
            display_help()
            return True

        # External commands - call vcli
        if cmd in COMMANDS:
            vcli_cmd = ["python", "-m", "vertice.cli", cmd] + args

            console.print(f"[dim]Executing: {' '.join(vcli_cmd)}[/dim]")

            try:
                import subprocess
                result = subprocess.run(
                    vcli_cmd,
                    cwd="/home/juan/vertice-dev/vertice-terminal",
                    capture_output=False,
                    text=True
                )

                if result.returncode != 0:
                    console.print(f"[red]Command failed with exit code {result.returncode}[/red]")
            except Exception as e:
                console.print(f"[red]Error executing command: {e}[/red]")
        else:
            console.print(f"[yellow]Unknown command: /{cmd}[/yellow]")
            console.print("[dim]Type /help for available commands[/dim]")
    else:
        # No slash - show hint
        console.print("[yellow]Commands must start with /[/yellow]")
        console.print("[dim]Type /help for available commands[/dim]")

    return True


async def run_interactive_shell():
    """Main interactive shell loop."""
    # Clear and show banner
    console.clear()
    display_banner()

    # Create prompt session
    session = PromptSession(
        history=InMemoryHistory(),
        completer=SlashCommandCompleter(),
        complete_while_typing=True,
        bottom_toolbar=get_bottom_toolbar,
        style=create_prompt_style(),
        mouse_support=True,
        enable_history_search=True,
    )

    # Main loop
    while True:
        try:
            # Create prompt
            prompt_text = [
                ('class:bracket', '╭─['),
                ('class:prompt', 'VÉRTICE'),
                ('class:bracket', ']'),
                ('', '\n'),
                ('class:bracket', '╰─'),
                ('class:prompt', '> '),
            ]

            # Get input
            command = await session.prompt_async(prompt_text)

            # Execute command
            should_continue = await execute_command(command)

            if not should_continue:
                console.print("\n[bold green]👋 Exiting VÉRTICE. Stay secure![/bold green]\n")
                break

        except KeyboardInterrupt:
            # Ctrl+C - cancel current input
            console.print("[dim]^C[/dim]")
            continue
        except EOFError:
            # Ctrl+D - exit
            console.print("\n[bold green]👋 Exiting VÉRTICE. Stay secure![/bold green]\n")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            continue


def main():
    """Entry point for interactive shell."""
    try:
        asyncio.run(run_interactive_shell())
    except KeyboardInterrupt:
        console.print("\n[bold green]👋 Goodbye![/bold green]\n")
    except Exception as e:
        console.print(f"[red]Fatal error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
