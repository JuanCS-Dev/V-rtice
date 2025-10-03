"""Authentication UI components."""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from typing import Dict, Any

from .permission_manager import ROLES

console = Console()


def display_welcome(user_data: Dict[str, Any]):
    """Exibe mensagem de boas-vindas."""
    email = user_data.get("email", "")
    name = user_data.get("name", "User")
    role = user_data.get("role", "viewer")

    role_info = ROLES.get(role, {})
    level: int = role_info.get("level", 0)

    # Banner de boas-vindas
    welcome_text = Text()
    welcome_text.append("🎉 ", style="bright_yellow")
    welcome_text.append("Authentication Successful!\n\n", style="bold bright_green")
    welcome_text.append(f"Welcome, {name}!\n", style="bright_cyan")
    welcome_text.append(f"📧 Email: {email}\n", style="dim")

    # Role com cor baseada no nível
    if role == "super_admin":
        role_style = "bold bright_magenta"
        role_icon = "👑"
    elif level >= 80:
        role_style = "bold bright_yellow"
        role_icon = "⭐"
    elif level >= 50:
        role_style = "bright_green"
        role_icon = "🔑"
    else:
        role_style = "bright_blue"
        role_icon = "👤"

    welcome_text.append(f"\n{role_icon} Role: ", style="bold")
    welcome_text.append(f"{role.upper()}", style=role_style)
    welcome_text.append(f" (Level {level})", style="dim")

    panel = Panel(
        welcome_text,
        title="[bold bright_green]✓ Authenticated[/bold bright_green]",
        border_style="bright_green",
        padding=(1, 3),
    )

    console.print()
    console.print(panel)
    console.print()

    if role == "super_admin":
        console.print(
            "[bold bright_magenta]👑 SUPERADMIN ACCESS GRANTED - ALL PERMISSIONS ENABLED[/bold bright_magenta]"
        )
        console.print()
