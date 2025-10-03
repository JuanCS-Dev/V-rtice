from cryptography.fernet import Fernet
import json
import os
from pathlib import Path


class SecureStorage:
    def __init__(self):
        # Gera ou carrega chave de criptografia
        key_file = Path.home() / ".vertice" / ".key"
        if key_file.exists():
            with open(key_file, "rb") as f:
                self.key = f.read()
        else:
            self.key = Fernet.generate_key()
            key_file.parent.mkdir(exist_ok=True)
            with open(key_file, "wb") as f:
                f.write(self.key)
            # Protege a chave
            os.chmod(key_file, 0o600)
        self.cipher = Fernet(self.key)

    def encrypt_and_save(self, data: dict, filepath: Path):
        json_data = json.dumps(data)
        encrypted = self.cipher.encrypt(json_data.encode())
        with open(filepath, "wb") as f:
            f.write(encrypted)
        os.chmod(filepath, 0o600)

    def load_and_decrypt(self, filepath: Path) -> dict:
        with open(filepath, "rb") as f:
            encrypted = f.read()
        decrypted = self.cipher.decrypt(encrypted)
        return json.loads(decrypted.decode())
