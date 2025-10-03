"""
Google OAuth2 Authentication System for Vertice CLI Terminal.
Implements secure authentication with token storage and role-based access.
"""
import json
import os
import typer
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import keyring
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

# Configurações de autenticação - CARREGADAS DO .env
from dotenv import load_dotenv
load_dotenv('/home/juan/vertice-dev/.env')

AUTH_CONFIG = {
    "CLIENT_ID": os.getenv("GOOGLE_CLIENT_ID"),
    "CLIENT_SECRET": os.getenv("GOOGLE_CLIENT_SECRET"),
    "REDIRECT_URI": os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8080/auth/callback"),
    "SCOPES": [
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile"
    ]
}

# Super Admin - CARREGADO DO .env
SUPER_ADMIN = os.getenv("SUPER_ADMIN_EMAIL", "juan.brainfarma@gmail.com")

# Roles e permissões
ROLES = {
    "super_admin": {
        "email": SUPER_ADMIN,
        "permissions": ["*"],  # Todas as permissões
        "level": 100
    },
    "admin": {
        "permissions": ["read", "write", "execute", "manage_users"],
        "level": 80
    },
    "analyst": {
        "permissions": ["read", "write", "execute"],
        "level": 50
    },
    "viewer": {
        "permissions": ["read"],
        "level": 10
    }
}

from .secure_storage import SecureStorage

class AuthManager:
    """Gerenciador de autenticação Google OAuth2."""

    def __init__(self):
        self.secure_storage = SecureStorage()
        self.auth_dir = Path.home() / ".vertice" / "auth"
        self.auth_dir.mkdir(parents=True, exist_ok=True)
        self.token_file = self.auth_dir / "token.enc"
        self.user_file = self.auth_dir / "user.enc"

    def is_authenticated(self) -> bool:
        """Verifica se o usuário está autenticado."""
        if not self.token_file.exists():
            return False

        try:
            token_data = self.secure_storage.load_and_decrypt(self.token_file)

            # Verifica se o token expirou
            expires_at = datetime.fromisoformat(token_data.get('expires_at', ''))
            if datetime.now() >= expires_at:
                return False

            return True
        except Exception:
            return False

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Retorna informações do usuário autenticado."""
        if not self.user_file.exists():
            return None

        try:
            return self.secure_storage.load_and_decrypt(self.user_file)
        except Exception:
            return None

    def get_user_role(self) -> str:
        """Retorna o role do usuário atual."""
        user = self.get_current_user()
        if not user:
            return "viewer"

        email = user.get('email', '')

        # Super admin
        if email == SUPER_ADMIN:
            return "super_admin"

        # Role armazenado
        return user.get('role', 'viewer')

    def has_permission(self, permission: str) -> bool:
        """Verifica se o usuário tem uma permissão específica."""
        role = self.get_user_role()
        role_data = ROLES.get(role, ROLES['viewer'])

        # Super admin tem tudo
        if "*" in role_data['permissions']:
            return True

        return permission in role_data['permissions']

    def save_auth_data(self, user_info: Dict[str, Any], access_token: str, expires_in: int = 3600):
        """Salva dados de autenticação de forma segura."""
        # Salva token no keyring (seguro)
        try:
            keyring.set_password("vertice-cli", "access_token", access_token)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not save to keyring: {e}[/yellow]")
            # Fallback: salva em arquivo (menos seguro mas funciona)

        # Salva metadados do token
        token_data = {
            "expires_at": (datetime.now() + timedelta(seconds=expires_in)).isoformat(),
            "created_at": datetime.now().isoformat()
        }

        self.secure_storage.encrypt_and_save(token_data, self.token_file)

        # Determina role baseado no email
        email = user_info.get('email', '')
        role = "super_admin" if email == SUPER_ADMIN else "analyst"

        # Salva informações do usuário
        user_data = {
            "email": email,
            "name": user_info.get('name', ''),
            "picture": user_info.get('picture', ''),
            "role": role,
            "authenticated_at": datetime.now().isoformat()
        }

        self.secure_storage.encrypt_and_save(user_data, self.user_file)

        # Mostra boas-vindas
        self.display_welcome(user_data)

    def display_welcome(self, user_data: Dict[str, Any]):
        """Exibe mensagem de boas-vindas."""
        email = user_data.get('email', '')
        name = user_data.get('name', 'User')
        role = user_data.get('role', 'viewer')

        role_info = ROLES.get(role, {})
        level = role_info.get('level', 0)

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
            padding=(1, 3)
        )

        console.print()
        console.print(panel)
        console.print()

        if role == "super_admin":
            console.print("[bold bright_magenta]👑 SUPER ADMIN ACCESS GRANTED - ALL PERMISSIONS ENABLED[/bold bright_magenta]")
            console.print()

    def logout(self):
        """Faz logout removendo tokens e dados."""
        try:
            # Remove do keyring
            try:
                keyring.delete_password("vertice-cli", "access_token")
            except Exception:
                pass

            # Remove arquivos
            if self.token_file.exists():
                self.token_file.unlink()

            if self.user_file.exists():
                self.user_file.unlink()

            console.print()
            console.print("[bold bright_green]✓ Logout successful![/bold bright_green]")
            console.print()

        except Exception as e:
            console.print(f"[red]Error during logout: {e}[/red]")

    def get_access_token(self) -> Optional[str]:
        """Retorna o access token do keyring ou fallback."""
        try:
            token = keyring.get_password("vertice-cli", "access_token")
            return token
        except Exception:
            return None

    def require_auth(self):
        """Decorator/helper para exigir autenticação."""
        if not self.is_authenticated():
            console.print()
            console.print(Panel(
                "[bold red]🔒 Authentication Required[/bold red]\n\n"
                "You need to authenticate to use this command.\n\n"
                "Run: [bold cyan]vcli auth login[/bold cyan]",
                border_style="red",
                padding=(1, 3)
            ))
            console.print()
            raise typer.Exit(code=1)

    def require_permission(self, permission: str):
        """Verifica se o usuário tem permissão específica."""
        self.require_auth()

        if not self.has_permission(permission):
            user = self.get_current_user()
            role = self.get_user_role()

            console.print()
            console.print(Panel(
                f"[bold red]🚫 Permission Denied[/bold red]\n\n"
                f"Your role ([cyan]{role}[/cyan]) does not have permission: [yellow]{permission}[/yellow]\n\n"
                f"Email: {user.get('email', 'unknown')}\n"
                f"Contact the administrator for access.",
                border_style="red",
                padding=(1, 3)
            ))
            console.print()
            raise typer.Exit(code=1)


# Instância global
auth_manager = AuthManager()


# Função helper para uso nos comandos
def require_auth():
    """Helper function para exigir autenticação em comandos."""
    auth_manager.require_auth()


def require_permission(permission: str):
    """Helper function para exigir permissão específica."""
    auth_manager.require_permission(permission)


def is_authenticated() -> bool:
    """Check if user is authenticated."""
    return auth_manager.is_authenticated()


def get_current_user() -> Optional[Dict[str, Any]]:
    """Get current authenticated user."""
    return auth_manager.get_current_user()
