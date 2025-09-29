# vertice_cli/utils/auth.py

import os
import json
import questionary
import requests
from pathlib import Path
from typing import Optional
from .console_utils import print_success, print_error, print_info

class AuthManager:
    """Gerencia autenticação para o CLI do Vértice"""

    def __init__(self):
        self.config_dir = Path.home() / ".vertice_cli"
        self.config_file = self.config_dir / "auth.json"
        self.config_dir.mkdir(exist_ok=True)

    def login(self, email: str = None, password: str = None, base_url: str = "http://localhost:8000") -> bool:
        """Realiza login e salva token"""
        if not email:
            email = questionary.text("Email:").ask()

        if not password:
            password = questionary.password("Senha:").ask()

        try:
            response = requests.post(f"{base_url}/auth/token", {
                "username": email,
                "password": password
            }, timeout=10)

            if response.ok:
                token_data = response.json()
                self._save_token(token_data["access_token"], email)
                print_success("Login realizado com sucesso!")
                return True
            else:
                print_error("Credenciais inválidas")
                return False

        except requests.exceptions.ConnectionError:
            print_error("Erro de conexão com o servidor de autenticação")
            return False
        except Exception as e:
            print_error(f"Erro no login: {str(e)}")
            return False

    def logout(self) -> None:
        """Remove token armazenado"""
        if self.config_file.exists():
            self.config_file.unlink()
        print_success("Logout realizado com sucesso!")

    def get_token(self) -> Optional[str]:
        """Retorna token armazenado"""
        if not self.config_file.exists():
            return None

        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                return config.get("access_token")
        except:
            return None

    def is_authenticated(self) -> bool:
        """Verifica se usuário está autenticado"""
        return self.get_token() is not None

    def get_user_info(self) -> Optional[dict]:
        """Retorna informações do usuário autenticado"""
        if not self.config_file.exists():
            return None

        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                return {
                    "email": config.get("email"),
                    "authenticated": True
                }
        except:
            return None

    def require_auth(self) -> bool:
        """Verifica autenticação, solicita login se necessário"""
        if self.is_authenticated():
            return True

        print_info("Autenticação necessária para continuar")
        return self.login()

    def _save_token(self, token: str, email: str) -> None:
        """Salva token no arquivo de configuração"""
        config = {
            "access_token": token,
            "email": email
        }

        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)