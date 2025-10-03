"""User information management."""

from pathlib import Path
from typing import Optional, Dict
from ..secure_storage import SecureStorage


class UserManager:
    """Manages user data storage."""

    def __init__(self):
        self.storage = SecureStorage()
        self.user_file = Path.home() / ".vertice" / "auth" / "user.enc"
        self.user_file.parent.mkdir(parents=True, exist_ok=True)

    def save_user(self, user_info: Dict):
        """Save user info encrypted."""
        self.storage.encrypt_and_save(user_info, self.user_file)

    def get_user(self) -> Optional[Dict]:
        """Get user info."""
        if not self.user_file.exists():
            return None
        try:
            return self.storage.load_and_decrypt(self.user_file)
        except Exception:
            return None

    def delete_user(self):
        """Delete user data."""
        if self.user_file.exists():
            self.user_file.unlink()
