"""
Tests for VaultClient - 100% Coverage Target

Tests Vault integration with comprehensive mocking of hvac library.
Covers all code paths including error conditions, caching, and fallbacks.
"""

import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest

from shared.vault_client import (
    VaultClient,
    VaultConfig,
    get_api_key,
    get_database_config,
    get_jwt_secret,
    get_vault_client,
)


class TestVaultConfig:
    """Test Vault configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        assert VaultConfig.ADDR == os.getenv("VAULT_ADDR", "http://localhost:8200")
        assert VaultConfig.MOUNT_POINT == "vertice"
        assert VaultConfig.CACHE_TTL == 300
        assert VaultConfig.FAIL_OPEN is True

    def test_env_var_override(self, monkeypatch):
        """Test environment variable overrides."""
        monkeypatch.setenv("VAULT_ADDR", "https://vault.example.com")
        monkeypatch.setenv("VAULT_ROLE_ID", "test-role-id")
        monkeypatch.setenv("VAULT_SECRET_ID", "test-secret-id")

        # Force re-import to pick up new env vars
        import importlib
        import shared.vault_client
        importlib.reload(shared.vault_client)

        assert shared.vault_client.VaultConfig.ADDR == "https://vault.example.com"


class TestVaultClientInitialization:
    """Test VaultClient initialization."""

    @patch('shared.vault_client.HVAC_AVAILABLE', False)
    def test_init_without_hvac(self):
        """Test initialization when hvac library not available."""
        client = VaultClient(addr="http://custom:8200")
        assert client.client is None
        assert client.addr == "http://custom:8200"

    @patch('shared.vault_client.HVAC_AVAILABLE', True)
    @patch('shared.vault_client.hvac')
    def test_init_with_token(self, mock_hvac):
        """Test initialization with direct token."""
        mock_hvac_client = MagicMock()
        mock_hvac.Client.return_value = mock_hvac_client

        client = VaultClient(addr="http://test:8200", token="test-token")

        assert client.token == "test-token"
        # Token set successfully
        assert client.client is not None

    @patch('shared.vault_client.HVAC_AVAILABLE', True)
    @patch('shared.vault_client.hvac')
    def test_init_with_approle(self, mock_hvac):
        """Test initialization with AppRole credentials."""
        mock_hvac_client = MagicMock()
        mock_hvac.Client.return_value = mock_hvac_client

        # Mock AppRole login response
        mock_hvac_client.auth.approle.login.return_value = {
            'auth': {
                'client_token': 'approle-token',
                'lease_duration': 3600
            }
        }

        client = VaultClient(
            addr="http://test:8200",
            role_id="test-role",
            secret_id="test-secret"
        )

        assert client.role_id == "test-role"
        assert client.secret_id == "test-secret"
        mock_hvac_client.auth.approle.login.assert_called_once()

    @patch('shared.vault_client.HVAC_AVAILABLE', True)
    @patch('shared.vault_client.hvac')
    def test_init_without_credentials(self, mock_hvac):
        """Test initialization without any credentials (explicit params)."""
        mock_hvac_client = MagicMock()
        mock_hvac.Client.return_value = mock_hvac_client

        # Explicitly pass None for all auth params
        client = VaultClient(addr="http://test:8200", role_id=None, secret_id=None, token=None)

        assert client.client is not None

    @patch('shared.vault_client.HVAC_AVAILABLE', True)
    @patch('shared.vault_client.hvac')
    def test_init_approle_failure_fail_open(self, mock_hvac):
        """Test AppRole login failure with fail_open=True."""
        mock_hvac_client = MagicMock()
        mock_hvac.Client.return_value = mock_hvac_client
        mock_hvac_client.auth.approle.login.side_effect = Exception("Auth failed")

        # Should not raise due to FAIL_OPEN=True
        client = VaultClient(role_id="test-role", secret_id="test-secret")
        assert client is not None

    @patch('shared.vault_client.HVAC_AVAILABLE', True)
    @patch('shared.vault_client.hvac')
    @patch('shared.vault_client.VaultConfig.FAIL_OPEN', False)
    def test_init_failure_no_fail_open(self, mock_hvac):
        """Test initialization failure with fail_open=False."""
        mock_hvac.Client.side_effect = Exception("Connection failed")

        with pytest.raises(Exception):
            VaultClient()


class TestVaultClientCaching:
    """Test secret caching functionality."""

    @patch('shared.vault_client.HVAC_AVAILABLE', True)
    @patch('shared.vault_client.hvac')
    def test_cache_store_and_retrieve(self, mock_hvac):
        """Test storing and retrieving from cache."""
        client = VaultClient(token="test-token")
        
        test_data = {"key": "value"}
        client._store_in_cache("test/path", test_data)

        cached = client._get_from_cache("test/path")
        assert cached == test_data

    @patch('shared.vault_client.HVAC_AVAILABLE', True)
    @patch('shared.vault_client.hvac')
    def test_cache_expiry(self, mock_hvac):
        """Test cache expiration."""
        client = VaultClient(token="test-token")
        
        test_data = {"key": "value"}
        client._store_in_cache("test/path", test_data)

        # Manually expire cache
        client._cache_expiry["test/path"] = datetime.now() - timedelta(seconds=1)

        cached = client._get_from_cache("test/path")
        assert cached is None

    @patch('shared.vault_client.HVAC_AVAILABLE', True)
    @patch('shared.vault_client.hvac')
    def test_cache_miss(self, mock_hvac):
        """Test cache miss."""
        client = VaultClient(token="test-token")
        
        cached = client._get_from_cache("nonexistent/path")
        assert cached is None


class TestVaultClientGetSecret:
    """Test secret retrieval functionality."""

    @patch('shared.vault_client.HVAC_AVAILABLE', True)
    @patch('shared.vault_client.hvac')
    def test_get_secret_success(self, mock_hvac):
        """Test successful secret retrieval."""
        mock_hvac_client = MagicMock()
        mock_hvac.Client.return_value = mock_hvac_client

        mock_hvac_client.secrets.kv.v2.read_secret_version.return_value = {
            'data': {
                'data': {
                    'api_key': 'secret-key-123',
                    'username': 'admin'
                }
            }
        }

        client = VaultClient(token="test-token")
        result = client.get_secret("api-keys/service", "api_key")

        assert result == 'secret-key-123'

    @patch('shared.vault_client.HVAC_AVAILABLE', True)
    @patch('shared.vault_client.hvac')
    def test_get_secret_full_dict(self, mock_hvac):
        """Test retrieving full secret dictionary."""
        mock_hvac_client = MagicMock()
        mock_hvac.Client.return_value = mock_hvac_client

        secret_data = {'api_key': 'key123', 'username': 'user'}
        mock_hvac_client.secrets.kv.v2.read_secret_version.return_value = {
            'data': {'data': secret_data}
        }

        client = VaultClient(token="test-token")
        result = client.get_secret("api-keys/service")

        assert result == secret_data

    @patch('shared.vault_client.HVAC_AVAILABLE', True)
    @patch('shared.vault_client.hvac')
    def test_get_secret_from_cache(self, mock_hvac):
        """Test retrieving secret from cache."""
        mock_hvac_client = MagicMock()
        mock_hvac.Client.return_value = mock_hvac_client

        client = VaultClient(token="test-token")
        
        # Pre-populate cache
        test_data = {'api_key': 'cached-key'}
        client._store_in_cache("test/path", test_data)

        # Should not call Vault
        result = client.get_secret("test/path", "api_key", use_cache=True)

        assert result == 'cached-key'
        mock_hvac_client.secrets.kv.v2.read_secret_version.assert_not_called()

    @patch('shared.vault_client.HVAC_AVAILABLE', True)
    @patch('shared.vault_client.hvac')
    def test_get_secret_bypass_cache(self, mock_hvac):
        """Test bypassing cache."""
        mock_hvac_client = MagicMock()
        mock_hvac.Client.return_value = mock_hvac_client

        mock_hvac_client.secrets.kv.v2.read_secret_version.return_value = {
            'data': {'data': {'api_key': 'fresh-key'}}
        }

        client = VaultClient(token="test-token")
        
        # Pre-populate cache with different value
        client._store_in_cache("test/path", {'api_key': 'cached-key'})

        # Bypass cache
        result = client.get_secret("test/path", "api_key", use_cache=False)

        assert result == 'fresh-key'

    @patch('shared.vault_client.HVAC_AVAILABLE', True)
    @patch('shared.vault_client.hvac')
    @patch('shared.vault_client.InvalidPath', Exception)
    def test_get_secret_not_found_with_fallback(self, mock_hvac, monkeypatch):
        """Test secret not found with env fallback."""
        mock_hvac_client = MagicMock()
        mock_hvac.Client.return_value = mock_hvac_client
        
        # Simulate InvalidPath - but mock_hvac.exceptions needs to exist
        from unittest.mock import Mock
        invalid_path_exc = type('InvalidPath', (Exception,), {})
        mock_hvac_client.secrets.kv.v2.read_secret_version.side_effect = invalid_path_exc("Not found")

        monkeypatch.setenv("FALLBACK_KEY", "env-fallback-value")

        client = VaultClient(addr="http://test:8200", token="test-token")
        result = client.get_secret("missing/path", "api_key", fallback_env="FALLBACK_KEY")

        assert result == "env-fallback-value"

    @patch('shared.vault_client.HVAC_AVAILABLE', True)
    @patch('shared.vault_client.hvac')
    def test_get_secret_vault_error_fallback(self, mock_hvac, monkeypatch):
        """Test VaultError exception with fallback."""
        mock_hvac_client = MagicMock()
        mock_hvac.Client.return_value = mock_hvac_client
        
        vault_error = type('VaultError', (Exception,), {})
        mock_hvac_client.secrets.kv.v2.read_secret_version.side_effect = vault_error("Vault error")

        monkeypatch.setenv("VAULT_FALLBACK", "vault-error-fallback")

        client = VaultClient(addr="http://test:8200", token="test-token")
        result = client.get_secret("error/path", fallback_env="VAULT_FALLBACK")

        assert result == "vault-error-fallback"

    @patch('shared.vault_client.HVAC_AVAILABLE', True)
    @patch('shared.vault_client.hvac')
    def test_get_secret_unexpected_error(self, mock_hvac):
        """Test unexpected error during secret retrieval."""
        mock_hvac_client = MagicMock()
        mock_hvac.Client.return_value = mock_hvac_client
        mock_hvac_client.secrets.kv.v2.read_secret_version.side_effect = RuntimeError("Unexpected")

        client = VaultClient(addr="http://test:8200", token="test-token")
        result = client.get_secret("error/path")

        assert result is None

    @patch('shared.vault_client.HVAC_AVAILABLE', True)
    @patch('shared.vault_client.hvac')
    def test_get_secret_not_found_no_fallback(self, mock_hvac):
        """Test secret not found without fallback."""
        mock_hvac_client = MagicMock()
        mock_hvac.Client.return_value = mock_hvac_client
        mock_hvac_client.secrets.kv.v2.read_secret_version.side_effect = Exception("Not found")

        client = VaultClient(token="test-token")
        result = client.get_secret("missing/path", "api_key")

        assert result is None

    @patch('shared.vault_client.HVAC_AVAILABLE', False)
    def test_get_secret_no_hvac_with_fallback(self, monkeypatch):
        """Test secret retrieval without hvac, using env fallback."""
        monkeypatch.setenv("FALLBACK_KEY", "env-value")

        client = VaultClient()
        result = client.get_secret("any/path", "api_key", fallback_env="FALLBACK_KEY")

        assert result == "env-value"

    @patch('shared.vault_client.HVAC_AVAILABLE', False)
    def test_get_secret_no_hvac_no_fallback(self):
        """Test secret retrieval without hvac and no fallback."""
        client = VaultClient()
        result = client.get_secret("any/path", "api_key")

        assert result is None


class TestVaultClientTokenRenewal:
    """Test token renewal functionality."""

    @patch('shared.vault_client.HVAC_AVAILABLE', True)
    @patch('shared.vault_client.hvac')
    def test_renew_token_if_needed_not_needed(self, mock_hvac):
        """Test token renewal when not needed."""
        mock_hvac_client = MagicMock()
        mock_hvac.Client.return_value = mock_hvac_client

        client = VaultClient(token="test-token")
        client.token_expiry = datetime.now() + timedelta(hours=1)

        # Should not renew
        client._renew_token_if_needed()

    @patch('shared.vault_client.HVAC_AVAILABLE', True)
    @patch('shared.vault_client.hvac')
    def test_renew_token_if_needed_required(self, mock_hvac):
        """Test token renewal when required."""
        mock_hvac_client = MagicMock()
        mock_hvac.Client.return_value = mock_hvac_client

        mock_hvac_client.auth.approle.login.return_value = {
            'auth': {
                'client_token': 'renewed-token',
                'lease_duration': 3600
            }
        }

        client = VaultClient(role_id="test-role", secret_id="test-secret")
        # Force expiry soon
        client.token_expiry = datetime.now() + timedelta(minutes=2)

        client._renew_token_if_needed()

    @patch('shared.vault_client.HVAC_AVAILABLE', True)
    @patch('shared.vault_client.hvac')
    def test_renew_token_failure(self, mock_hvac):
        """Test token renewal failure handling."""
        mock_hvac_client = MagicMock()
        mock_hvac.Client.return_value = mock_hvac_client

        mock_hvac_client.auth.approle.login.side_effect = Exception("Renewal failed")

        client = VaultClient(role_id="test-role", secret_id="test-secret")
        client.token_expiry = datetime.now() + timedelta(minutes=2)

        # Should not raise
        client._renew_token_if_needed()

    @patch('shared.vault_client.HVAC_AVAILABLE', True)
    @patch('shared.vault_client.hvac')
    def test_renew_token_no_client(self, mock_hvac):
        """Test renewal with no client."""
        client = VaultClient()
        client.client = None

        # Should not raise
        client._renew_token_if_needed()


class TestVaultClientSetSecret:
    """Test secret storage functionality."""

    @patch('shared.vault_client.HVAC_AVAILABLE', True)
    @patch('shared.vault_client.hvac')
    def test_set_secret_success(self, mock_hvac):
        """Test successful secret storage."""
        mock_hvac_client = MagicMock()
        mock_hvac.Client.return_value = mock_hvac_client

        client = VaultClient(token="test-token")
        result = client.set_secret("test/path", {"key": "value"})

        assert result is True
        mock_hvac_client.secrets.kv.v2.create_or_update_secret.assert_called_once()

    @patch('shared.vault_client.HVAC_AVAILABLE', True)
    @patch('shared.vault_client.hvac')
    def test_set_secret_invalidates_cache(self, mock_hvac):
        """Test that set_secret invalidates cache."""
        mock_hvac_client = MagicMock()
        mock_hvac.Client.return_value = mock_hvac_client

        client = VaultClient(token="test-token")
        
        # Pre-populate cache
        client._store_in_cache("test/path", {"old": "value"})
        assert "test/path" in client._cache

        client.set_secret("test/path", {"new": "value"})

        assert "test/path" not in client._cache

    @patch('shared.vault_client.HVAC_AVAILABLE', True)
    @patch('shared.vault_client.hvac')
    def test_set_secret_failure(self, mock_hvac):
        """Test secret storage failure."""
        mock_hvac_client = MagicMock()
        mock_hvac.Client.return_value = mock_hvac_client
        mock_hvac_client.secrets.kv.v2.create_or_update_secret.side_effect = Exception("Write failed")

        client = VaultClient(token="test-token")
        result = client.set_secret("test/path", {"key": "value"})

        assert result is False

    @patch('shared.vault_client.HVAC_AVAILABLE', False)
    def test_set_secret_no_client(self):
        """Test set_secret without client."""
        client = VaultClient()
        result = client.set_secret("test/path", {"key": "value"})

        assert result is False


class TestVaultClientDeleteSecret:
    """Test secret deletion functionality."""

    @patch('shared.vault_client.HVAC_AVAILABLE', True)
    @patch('shared.vault_client.hvac')
    def test_delete_secret_success(self, mock_hvac):
        """Test successful secret deletion."""
        mock_hvac_client = MagicMock()
        mock_hvac.Client.return_value = mock_hvac_client

        client = VaultClient(token="test-token")
        result = client.delete_secret("test/path")

        assert result is True
        mock_hvac_client.secrets.kv.v2.delete_latest_version_of_secret.assert_called_once()

    @patch('shared.vault_client.HVAC_AVAILABLE', True)
    @patch('shared.vault_client.hvac')
    def test_delete_secret_invalidates_cache(self, mock_hvac):
        """Test that delete_secret invalidates cache."""
        mock_hvac_client = MagicMock()
        mock_hvac.Client.return_value = mock_hvac_client

        client = VaultClient(token="test-token")
        
        # Pre-populate cache
        client._store_in_cache("test/path", {"key": "value"})
        assert "test/path" in client._cache

        client.delete_secret("test/path")

        assert "test/path" not in client._cache

    @patch('shared.vault_client.HVAC_AVAILABLE', True)
    @patch('shared.vault_client.hvac')
    def test_delete_secret_failure(self, mock_hvac):
        """Test secret deletion failure."""
        mock_hvac_client = MagicMock()
        mock_hvac.Client.return_value = mock_hvac_client
        mock_hvac_client.secrets.kv.v2.delete_latest_version_of_secret.side_effect = Exception("Delete failed")

        client = VaultClient(token="test-token")
        result = client.delete_secret("test/path")

        assert result is False

    @patch('shared.vault_client.HVAC_AVAILABLE', False)
    def test_delete_secret_no_client(self):
        """Test delete_secret without client."""
        client = VaultClient()
        result = client.delete_secret("test/path")

        assert result is False


class TestVaultClientListSecrets:
    """Test secret listing functionality."""

    @patch('shared.vault_client.HVAC_AVAILABLE', True)
    @patch('shared.vault_client.hvac')
    def test_list_secrets_success(self, mock_hvac):
        """Test successful secret listing."""
        mock_hvac_client = MagicMock()
        mock_hvac.Client.return_value = mock_hvac_client

        mock_hvac_client.secrets.kv.v2.list_secrets.return_value = {
            'data': {'keys': ['secret1', 'secret2', 'secret3']}
        }

        client = VaultClient(token="test-token")
        result = client.list_secrets("api-keys/")

        assert result == ['secret1', 'secret2', 'secret3']

    @patch('shared.vault_client.HVAC_AVAILABLE', True)
    @patch('shared.vault_client.hvac')
    def test_list_secrets_failure(self, mock_hvac):
        """Test secret listing failure."""
        mock_hvac_client = MagicMock()
        mock_hvac.Client.return_value = mock_hvac_client
        mock_hvac_client.secrets.kv.v2.list_secrets.side_effect = Exception("List failed")

        client = VaultClient(token="test-token")
        result = client.list_secrets("api-keys/")

        assert result == []

    @patch('shared.vault_client.HVAC_AVAILABLE', False)
    def test_list_secrets_no_client(self):
        """Test list_secrets without client."""
        client = VaultClient()
        result = client.list_secrets("api-keys/")

        assert result == []


class TestGlobalVaultClient:
    """Test global Vault client instance."""

    def test_get_vault_client_singleton(self):
        """Test global client is singleton."""
        import shared.vault_client
        shared.vault_client._global_vault_client = None

        client1 = get_vault_client()
        client2 = get_vault_client()

        assert client1 is client2


class TestConvenienceFunctions:
    """Test convenience wrapper functions."""

    @patch('shared.vault_client.get_vault_client')
    def test_get_api_key(self, mock_get_client):
        """Test get_api_key convenience function."""
        mock_client = MagicMock()
        mock_client.get_secret.return_value = "test-api-key"
        mock_get_client.return_value = mock_client

        result = get_api_key("virustotal", fallback_env="VT_API_KEY")

        assert result == "test-api-key"
        mock_client.get_secret.assert_called_once_with(
            "api-keys/virustotal",
            "api_key",
            fallback_env="VT_API_KEY"
        )

    @patch('shared.vault_client.get_vault_client')
    def test_get_database_config(self, mock_get_client):
        """Test get_database_config convenience function."""
        mock_client = MagicMock()
        mock_client.get_secret.return_value = {"host": "localhost", "port": "5432"}
        mock_get_client.return_value = mock_client

        result = get_database_config("postgres")

        assert result == {"host": "localhost", "port": "5432"}
        mock_client.get_secret.assert_called_once_with("database/postgres")

    @patch('shared.vault_client.get_vault_client')
    def test_get_jwt_secret(self, mock_get_client):
        """Test get_jwt_secret convenience function."""
        mock_client = MagicMock()
        mock_client.get_secret.return_value = "jwt-secret-key"
        mock_get_client.return_value = mock_client

        result = get_jwt_secret()

        assert result == "jwt-secret-key"
        mock_client.get_secret.assert_called_once_with(
            "app/jwt",
            "secret_key",
            fallback_env="JWT_SECRET_KEY"
        )
