"""Secure token storage using system keyring and encrypted metadata."""

import keyring
import time
from pathlib import Path
from typing import Optional, Dict, Any
from ..secure_storage import SecureStorage
from rich.console import Console

console = Console()


class TokenStorage:
    """Manages secure storage of OAuth tokens and their metadata."""

    def __init__(self):
        self.service_name = "vertice-cli"
        self.storage = SecureStorage()
        self.token_meta_file = Path.home() / ".vertice" / "auth" / "token.enc"
        self.token_meta_file.parent.mkdir(parents=True, exist_ok=True)

    def save_token(self, email: str, token: str, expires_in: int):
        """Saves the access token to the system keyring and its metadata to an encrypted file."""
        try:
            keyring.set_password(self.service_name, email, token)
        except Exception as e:
            console.print(
                f"[yellow]Warning: Could not save token to keyring: {e}. Feature may not work as expected.[/yellow]"
            )

        metadata = {
            "email": email,
            "expires_at": time.time() + expires_in,
            "created_at": time.time(),
        }
        self.storage.encrypt_and_save(metadata, self.token_meta_file)

    def get_token(self, email: str) -> Optional[str]:
        """Retrieves the access token from the system keyring."""
        try:
            return keyring.get_password(self.service_name, email)
        except Exception as e:
            console.print(
                f"[yellow]Warning: Could not retrieve token from keyring: {e}.[/yellow]"
            )
            return None

    def get_token_metadata(self) -> Optional[Dict[str, Any]]:
        """Loads and decrypts the token metadata."""
        if not self.token_meta_file.exists():
            return None
        try:
            return self.storage.load_and_decrypt(self.token_meta_file)
        except Exception:
            return None

    def delete_token(self, email: str):
        """Deletes the token from the keyring and removes the metadata file."""
        try:
            keyring.delete_password(self.service_name, email)
        except Exception:
            # Ignore if it fails, maybe it was never there
            pass

        if self.token_meta_file.exists():
            self.token_meta_file.unlink()
