"""Authentication utilities for Vertice CLI."""

import time
import typer
from typing import Optional, Dict, Any
from rich.console import Console
from rich.panel import Panel

from .token_storage import TokenStorage
from .user_manager import UserManager
from .permission_manager import PermissionManager, ROLES, SUPER_ADMIN
from .auth_ui import display_welcome

console = Console()


class AuthManager:
    """Main authentication manager - Facade Pattern."""

    def __init__(self):
        self.tokens = TokenStorage()
        self.users = UserManager()
        self.permissions = PermissionManager()

    def save_auth_data(self, user_info: Dict, token: str, expires_in: int):
        email = user_info["email"]
        role = self.permissions.get_user_role(email)
        user_info["role"] = role

        self.tokens.save_token(email, token, expires_in)
        self.users.save_user(user_info)
        display_welcome(user_info)

    def is_authenticated(self) -> bool:
        """Checks if the current user is authenticated and the token is not expired."""
        metadata = self.tokens.get_token_metadata()
        if not metadata:
            return False

        # Check for token expiration
        expires_at = metadata.get("expires_at", 0)
        if time.time() >= expires_at:
            return False

        # Check if token exists in keyring
        user = self.users.get_user()
        if not user or not self.tokens.get_token(user["email"]):
            return False

        return True

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        return self.users.get_user()

    def get_access_token(self) -> Optional[str]:
        user = self.get_current_user()
        if not user:
            return None
        return self.tokens.get_token(user["email"])

    def get_user_role(self) -> str:
        user = self.get_current_user()
        if not user:
            return "viewer"
        return self.permissions.get_user_role(user["email"])

    def has_permission(self, permission: str) -> bool:
        user = self.get_current_user()
        if not user:
            return False
        return self.permissions.has_permission(user["email"], permission)

    def logout(self):
        """Logs out the user by deleting all stored data."""
        user = self.users.get_user()
        if user:
            self.tokens.delete_token(user["email"])
        self.users.delete_user()
        console.print("\n[bold bright_green]✓ Logout successful![/bold bright_green]\n")

    def require_auth(self):
        """Helper to be used in commands that need authentication."""
        if not self.is_authenticated():
            console.print(
                Panel(
                    "[bold red]🔒 Authentication Required[/bold red]\n\n"
                    "You need to authenticate to use this command.\n\n"
                    "Run: [bold cyan]vcli auth login[/bold cyan]",
                    border_style="red",
                    padding=(1, 3),
                )
            )
            raise typer.Exit(code=1)

    def require_permission(self, permission: str):
        """Helper to be used in commands that need a specific permission."""
        self.require_auth()
        if not self.has_permission(permission):
            user = self.get_current_user()
            role = self.get_user_role()
            console.print(
                Panel(
                    f"[bold red]🚫 Permission Denied[/bold red]\n\n"
                    f"Your role ([cyan]{role}[/cyan]) does not have permission: [yellow]{permission}[/yellow]\n\n"
                    f"Email: {user.get('email', 'unknown') if user else 'unknown'}\n"
                    f"Contact the administrator for access.",
                    border_style="red",
                    padding=(1, 3),
                )
            )
            raise typer.Exit(code=1)


# Global instance for easy access throughout the CLI
auth_manager = AuthManager()


# Helper functions for direct use in commands
def require_auth():
    auth_manager.require_auth()


def require_permission(permission: str):
    auth_manager.require_permission(permission)


def is_authenticated() -> bool:
    return auth_manager.is_authenticated()


def get_current_user() -> Optional[Dict[str, Any]]:
    return auth_manager.get_current_user()


__all__ = [
    "auth_manager",
    "require_auth",
    "require_permission",
    "is_authenticated",
    "get_current_user",
    "ROLES",
    "SUPER_ADMIN",
]
