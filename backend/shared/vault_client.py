"""
HashiCorp Vault Client for Vértice Platform
============================================

PAGANI Quality - Secure Secrets Management

Client for accessing secrets from HashiCorp Vault:
- API keys
- Database credentials
- JWT secrets
- OAuth tokens
- Encryption keys

Features:
- AppRole authentication
- Automatic token renewal
- Caching with TTL
- Fallback to environment variables
- Type-safe secret retrieval

Usage:
    from shared.vault_client import VaultClient

    vault = VaultClient()

    # Get API key
    api_key = vault.get_secret("api-keys/virustotal", "api_key")

    # Get database credentials
    db_config = vault.get_secret("database/postgres")
    # Returns: {"host": "...", "port": "...", "username": "...", ...}

    # With fallback to env var
    api_key = vault.get_secret(
        "api-keys/shodan",
        "api_key",
        fallback_env="SHODAN_API_KEY"
    )

Environment Variables:
    VAULT_ADDR: Vault server URL (default: http://localhost:8200)
    VAULT_ROLE_ID: AppRole role ID
    VAULT_SECRET_ID: AppRole secret ID
    VAULT_TOKEN: Direct token (for dev/testing)
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Any

try:
    import hvac
    from hvac.exceptions import InvalidPath, VaultError
    HVAC_AVAILABLE = True
except ImportError:
    HVAC_AVAILABLE = False
    hvac = None
    VaultError = Exception
    InvalidPath = Exception


# ============================================================================
# CONFIGURATION
# ============================================================================

class VaultConfig:
    """Vault client configuration."""

    # Vault server URL
    ADDR = os.getenv("VAULT_ADDR", "http://localhost:8200")

    # Authentication (AppRole)
    ROLE_ID = os.getenv("VAULT_ROLE_ID")
    SECRET_ID = os.getenv("VAULT_SECRET_ID")

    # Or direct token (for dev/testing)
    TOKEN = os.getenv("VAULT_TOKEN")

    # Secrets path prefix
    MOUNT_POINT = "vertice"

    # Cache TTL (seconds)
    CACHE_TTL = 300  # 5 minutes

    # Fail behavior if Vault unavailable
    FAIL_OPEN = True  # True = use env vars as fallback


# ============================================================================
# VAULT CLIENT
# ============================================================================

class VaultClient:
    """
    Client for HashiCorp Vault.

    Handles authentication, token renewal, and secret retrieval.
    """

    def __init__(
        self,
        addr: str | None = None,
        role_id: str | None = None,
        secret_id: str | None = None,
        token: str | None = None
    ):
        self.addr = addr or VaultConfig.ADDR
        self.role_id = role_id or VaultConfig.ROLE_ID
        self.secret_id = secret_id or VaultConfig.SECRET_ID
        self.token = token or VaultConfig.TOKEN

        self.client: hvac.Client | None = None
        self.token_expiry: datetime | None = None

        # Cache for secrets
        self._cache: dict[str, dict[str, Any]] = {}
        self._cache_expiry: dict[str, datetime] = {}

        # Initialize client
        if HVAC_AVAILABLE:
            self._initialize_client()
        else:
            logging.warning("hvac library not available. Install with: pip install hvac")

    def _initialize_client(self):
        """Initialize Vault client and authenticate."""
        try:
            self.client = hvac.Client(url=self.addr)

            # Authenticate with AppRole or token
            if self.role_id and self.secret_id:
                self._login_approle()
            elif self.token:
                self.client.token = self.token
                self.token_expiry = datetime.now() + timedelta(hours=1)
            else:
                logging.warning("No Vault credentials provided. Using fallback mode.")

        except Exception as e:
            logging.error(f"Failed to initialize Vault client: {e}")
            if not VaultConfig.FAIL_OPEN:
                raise

    def _login_approle(self):
        """Authenticate using AppRole."""
        try:
            response = self.client.auth.approle.login(
                role_id=self.role_id,
                secret_id=self.secret_id
            )

            # Extract token and TTL
            self.client.token = response['auth']['client_token']
            lease_duration = response['auth']['lease_duration']
            self.token_expiry = datetime.now() + timedelta(seconds=lease_duration)

            logging.info(f"Authenticated with Vault. Token expires in {lease_duration}s")

        except Exception as e:
            logging.error(f"AppRole authentication failed: {e}")
            if not VaultConfig.FAIL_OPEN:
                raise

    def _renew_token_if_needed(self):
        """Renew token if close to expiry."""
        if not self.client or not self.token_expiry:
            return

        # Renew if less than 5 minutes remaining
        if datetime.now() + timedelta(minutes=5) >= self.token_expiry:
            try:
                logging.info("Renewing Vault token...")
                self._login_approle()
            except Exception as e:
                logging.error(f"Token renewal failed: {e}")

    def _get_from_cache(self, key: str) -> dict[str, Any] | None:
        """Get secret from cache if not expired."""
        if key in self._cache:
            expiry = self._cache_expiry.get(key)
            if expiry and datetime.now() < expiry:
                return self._cache[key]
        return None

    def _store_in_cache(self, key: str, value: dict[str, Any]):
        """Store secret in cache with TTL."""
        self._cache[key] = value
        self._cache_expiry[key] = datetime.now() + timedelta(seconds=VaultConfig.CACHE_TTL)

    def get_secret(
        self,
        path: str,
        key: str | None = None,
        fallback_env: str | None = None,
        use_cache: bool = True
    ) -> str | dict[str, Any] | None:
        """
        Get secret from Vault.

        Args:
            path: Secret path (e.g., "api-keys/virustotal")
            key: Specific key within secret (optional)
            fallback_env: Environment variable to use as fallback
            use_cache: Use cached value if available

        Returns:
            Secret value (str if key provided, dict if not)
            None if not found

        Examples:
            >>> client.get_secret("api-keys/shodan", "api_key")
            'YOUR_SHODAN_KEY'

            >>> client.get_secret("database/postgres")
            {'host': 'localhost', 'port': '5432', 'username': 'vertice', ...}
        """
        # Check cache first
        if use_cache:
            cached = self._get_from_cache(path)
            if cached is not None:
                if key:
                    return cached.get(key)
                return cached

        # Try Vault
        if self.client:
            try:
                self._renew_token_if_needed()

                # Read secret from KV v2
                response = self.client.secrets.kv.v2.read_secret_version(
                    path=path,
                    mount_point=VaultConfig.MOUNT_POINT
                )

                secret_data = response['data']['data']

                # Store in cache
                if use_cache:
                    self._store_in_cache(path, secret_data)

                # Return specific key or full dict
                if key:
                    return secret_data.get(key)
                return secret_data

            except (VaultError, InvalidPath) as e:
                logging.warning(f"Failed to get secret from Vault ({path}): {e}")

            except Exception as e:
                logging.error(f"Unexpected error getting secret ({path}): {e}")

        # Fallback to environment variable
        if fallback_env:
            env_value = os.getenv(fallback_env)
            if env_value:
                logging.info(f"Using fallback env var: {fallback_env}")
                return env_value

        # No secret found
        logging.warning(f"Secret not found: {path}")
        return None

    def set_secret(
        self,
        path: str,
        data: dict[str, Any]
    ) -> bool:
        """
        Store secret in Vault.

        Args:
            path: Secret path
            data: Secret data (key-value pairs)

        Returns:
            True if successful
        """
        if not self.client:
            logging.error("Vault client not initialized")
            return False

        try:
            self._renew_token_if_needed()

            # Write secret to KV v2
            self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=data,
                mount_point=VaultConfig.MOUNT_POINT
            )

            # Invalidate cache
            if path in self._cache:
                del self._cache[path]

            logging.info(f"Secret stored: {path}")
            return True

        except Exception as e:
            logging.error(f"Failed to store secret ({path}): {e}")
            return False

    def delete_secret(self, path: str) -> bool:
        """Delete secret from Vault."""
        if not self.client:
            return False

        try:
            self.client.secrets.kv.v2.delete_latest_version_of_secret(
                path=path,
                mount_point=VaultConfig.MOUNT_POINT
            )

            # Invalidate cache
            if path in self._cache:
                del self._cache[path]

            logging.info(f"Secret deleted: {path}")
            return True

        except Exception as e:
            logging.error(f"Failed to delete secret ({path}): {e}")
            return False

    def list_secrets(self, path: str = "") -> list:
        """List secrets at path."""
        if not self.client:
            return []

        try:
            response = self.client.secrets.kv.v2.list_secrets(
                path=path,
                mount_point=VaultConfig.MOUNT_POINT
            )
            return response['data']['keys']

        except Exception as e:
            logging.error(f"Failed to list secrets ({path}): {e}")
            return []


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

_global_vault_client: VaultClient | None = None

def get_vault_client() -> VaultClient:
    """Get global Vault client instance."""
    global _global_vault_client
    if _global_vault_client is None:
        _global_vault_client = VaultClient()
    return _global_vault_client


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def get_api_key(service: str, fallback_env: str | None = None) -> str | None:
    """
    Get API key for service.

    Args:
        service: Service name (e.g., "virustotal", "shodan")
        fallback_env: Environment variable fallback

    Returns:
        API key string or None
    """
    client = get_vault_client()
    return client.get_secret(
        f"api-keys/{service}",
        "api_key",
        fallback_env=fallback_env
    )


def get_database_config(db: str = "postgres") -> dict[str, Any] | None:
    """
    Get database configuration.

    Args:
        db: Database name ("postgres", "redis", etc.)

    Returns:
        Database config dict or None
    """
    client = get_vault_client()
    return client.get_secret(f"database/{db}")


def get_jwt_secret() -> str | None:
    """Get JWT secret key."""
    client = get_vault_client()
    return client.get_secret(
        "app/jwt",
        "secret_key",
        fallback_env="JWT_SECRET_KEY"
    )


# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    "VaultClient",
    "VaultConfig",
    "get_vault_client",
    "get_api_key",
    "get_database_config",
    "get_jwt_secret",
]
