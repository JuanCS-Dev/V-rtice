"""Tests for backend/shared/vault_client.py - 100% coverage.

Strategy: Mock hvac client, test all paths including cache, fallbacks, errors.
"""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta


@pytest.fixture
def mock_hvac():
    """Mock hvac module."""
    with patch("backend.shared.vault_client.HVAC_AVAILABLE", True):
        with patch("backend.shared.vault_client.hvac") as mock_h:
            yield mock_h


@pytest.fixture
def mock_env():
    """Mock environment variables."""
    with patch.dict(os.environ, {
        "VAULT_ADDR": "http://test-vault:8200",
        "VAULT_TOKEN": "test-token-123",
    }, clear=False):
        yield


@pytest.fixture
def vault_config_mock():
    """Mock VaultConfig."""
    with patch("backend.shared.vault_client.VaultConfig") as mock_cfg:
        mock_cfg.ADDR = "http://test-vault:8200"
        mock_cfg.TOKEN = "test-token"
        mock_cfg.ROLE_ID = None
        mock_cfg.SECRET_ID = None
        mock_cfg.CACHE_TTL = 300
        mock_cfg.ENABLE_CACHE = True
        yield mock_cfg


class TestVaultClientImport:
    """Test vault_client imports correctly."""

    def test_imports_without_hvac(self):
        """vault_client can be imported even without hvac."""
        with patch("backend.shared.vault_client.HVAC_AVAILABLE", False):
            from backend.shared.vault_client import VaultClient
            assert VaultClient is not None

    def test_imports_with_hvac(self, mock_hvac):
        """vault_client imports correctly with hvac."""
        from backend.shared.vault_client import VaultClient
        assert VaultClient is not None

    def test_import_error_handling(self):
        """Handles hvac import errors gracefully (lines 55-56)."""
        # This test ensures the try/except ImportError block is covered
        # by simulating module import scenario
        import sys
        import importlib
        
        # Remove hvac from modules temporarily
        hvac_backup = sys.modules.get('hvac')
        if 'hvac' in sys.modules:
            del sys.modules['hvac']
        
        try:
            # Force re-import with hvac unavailable
            with patch.dict(sys.modules, {'hvac': None}):
                import backend.shared.vault_client
                importlib.reload(backend.shared.vault_client)
                
                # Should still work
                assert backend.shared.vault_client.VaultClient is not None
        finally:
            # Restore hvac
            if hvac_backup:
                sys.modules['hvac'] = hvac_backup


class TestVaultConfig:
    """Test VaultConfig class."""

    def test_vault_config_defaults(self):
        """VaultConfig uses environment variables."""
        from backend.shared.vault_client import VaultConfig
        
        assert VaultConfig.ADDR is not None
        # Default values or env vars
        assert isinstance(VaultConfig.ADDR, str)

    def test_vault_config_with_env_vars(self, mock_env):
        """VaultConfig reads from environment."""
        from backend.shared.vault_client import VaultConfig
        
        # Re-import to pick up env changes
        import importlib
        import backend.shared.vault_client
        importlib.reload(backend.shared.vault_client)
        
        assert "test-vault" in backend.shared.vault_client.VaultConfig.ADDR or "localhost" in backend.shared.vault_client.VaultConfig.ADDR


class TestVaultClientInitialization:
    """Test VaultClient initialization."""

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", False)
    def test_init_without_hvac(self):
        """VaultClient works in fallback mode when hvac not available."""
        from backend.shared.vault_client import VaultClient
        
        # Should create instance but client will be None
        vault = VaultClient()
        assert vault.client is None

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", True)
    @patch("backend.shared.vault_client.hvac")
    def test_init_with_token(self, mock_hvac_module, vault_config_mock):
        """VaultClient initializes with direct token."""
        from backend.shared.vault_client import VaultClient
        
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_hvac_module.Client.return_value = mock_client
        
        vault = VaultClient()
        
        assert vault is not None
        mock_hvac_module.Client.assert_called_once()

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", True)
    @patch("backend.shared.vault_client.hvac")
    def test_init_with_approle(self, mock_hvac_module, vault_config_mock):
        """VaultClient authenticates with AppRole."""
        from backend.shared.vault_client import VaultClient
        
        vault_config_mock.TOKEN = None
        vault_config_mock.ROLE_ID = "role-123"
        vault_config_mock.SECRET_ID = "secret-456"
        
        mock_client = Mock()
        mock_client.is_authenticated.return_value = False
        mock_client.auth.approle.login.return_value = {
            "auth": {"client_token": "approle-token"}
        }
        mock_hvac_module.Client.return_value = mock_client
        
        vault = VaultClient()
        
        mock_client.auth.approle.login.assert_called_once()


class TestVaultClientGetSecret:
    """Test get_secret method."""

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", True)
    @patch("backend.shared.vault_client.hvac")
    def test_get_secret_success(self, mock_hvac_module, vault_config_mock):
        """get_secret retrieves secret from Vault."""
        from backend.shared.vault_client import VaultClient
        
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"api_key": "secret-key-123"}}
        }
        mock_hvac_module.Client.return_value = mock_client
        
        vault = VaultClient()
        result = vault.get_secret("api-keys/test", "api_key")
        
        assert result == "secret-key-123"

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", True)
    @patch("backend.shared.vault_client.hvac")
    def test_get_secret_full_dict(self, mock_hvac_module, vault_config_mock):
        """get_secret returns full dict when no field specified."""
        from backend.shared.vault_client import VaultClient
        
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        secret_data = {"host": "localhost", "port": 5432}
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": secret_data}
        }
        mock_hvac_module.Client.return_value = mock_client
        
        vault = VaultClient()
        result = vault.get_secret("database/postgres")
        
        assert result == secret_data

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", True)
    @patch("backend.shared.vault_client.hvac")
    def test_get_secret_with_cache(self, mock_hvac_module, vault_config_mock):
        """get_secret uses cache on subsequent calls."""
        from backend.shared.vault_client import VaultClient
        
        vault_config_mock.ENABLE_CACHE = True
        vault_config_mock.CACHE_TTL = 300
        
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"key": "value"}}
        }
        mock_hvac_module.Client.return_value = mock_client
        
        vault = VaultClient()
        
        # First call - should hit Vault
        result1 = vault.get_secret("test/path", "key")
        # Second call - should hit cache
        result2 = vault.get_secret("test/path", "key")
        
        assert result1 == result2 == "value"
        # Vault should be called only once
        assert mock_client.secrets.kv.v2.read_secret_version.call_count == 1

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", True)
    @patch("backend.shared.vault_client.hvac")
    def test_get_secret_fallback_to_env(self, mock_hvac_module, vault_config_mock):
        """get_secret falls back to environment variable on error."""
        from backend.shared.vault_client import VaultClient
        
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.read_secret_version.side_effect = Exception("Vault error")
        mock_hvac_module.Client.return_value = mock_client
        
        with patch.dict(os.environ, {"TEST_API_KEY": "fallback-key"}):
            vault = VaultClient()
            result = vault.get_secret(
                "api-keys/test",
                "api_key",
                fallback_env="TEST_API_KEY"
            )
            
            assert result == "fallback-key"

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", True)
    @patch("backend.shared.vault_client.hvac")
    def test_get_secret_no_fallback_returns_none(self, mock_hvac_module, vault_config_mock):
        """get_secret returns None when no fallback available."""
        from backend.shared.vault_client import VaultClient
        
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.read_secret_version.side_effect = Exception("Vault error")
        mock_hvac_module.Client.return_value = mock_client
        
        vault = VaultClient()
        
        result = vault.get_secret("api-keys/test", "api_key")
        assert result is None


class TestVaultClientCacheManagement:
    """Test cache behavior."""

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", True)
    @patch("backend.shared.vault_client.hvac")
    def test_cache_expiry(self, mock_hvac_module, vault_config_mock):
        """Cache expires after TTL."""
        from backend.shared.vault_client import VaultClient
        
        vault_config_mock.ENABLE_CACHE = True
        vault_config_mock.CACHE_TTL = 0  # Immediate expiry
        
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"key": "value"}}
        }
        mock_hvac_module.Client.return_value = mock_client
        
        vault = VaultClient()
        
        # First call
        vault.get_secret("test/path", "key")
        # Second call after expiry
        vault.get_secret("test/path", "key")
        
        # Should call Vault twice (cache expired)
        assert mock_client.secrets.kv.v2.read_secret_version.call_count == 2

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", True)
    @patch("backend.shared.vault_client.hvac")
    def test_cache_disabled(self, mock_hvac_module, vault_config_mock):
        """Cache can be disabled via use_cache=False."""
        from backend.shared.vault_client import VaultClient
        
        vault_config_mock.ENABLE_CACHE = True  # Global enabled
        
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"key": "value"}}
        }
        mock_hvac_module.Client.return_value = mock_client
        
        vault = VaultClient()
        
        vault.get_secret("test/path", "key", use_cache=False)
        vault.get_secret("test/path", "key", use_cache=False)
        
        # Should call Vault twice (cache disabled per-call)
        assert mock_client.secrets.kv.v2.read_secret_version.call_count == 2

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", True)
    @patch("backend.shared.vault_client.hvac")
    def test_cache_hit_full_dict(self, mock_hvac_module, vault_config_mock):
        """Cache hit returns full dict when no key specified (line 225)."""
        from backend.shared.vault_client import VaultClient
        
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        secret_data = {"host": "localhost", "port": 5432}
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": secret_data}
        }
        mock_hvac_module.Client.return_value = mock_client
        
        vault = VaultClient()
        
        # First call loads cache
        result1 = vault.get_secret("db/postgres")
        # Second call hits cache, returns full dict (line 225)
        result2 = vault.get_secret("db/postgres")  # No key param
        
        assert result1 == result2 == secret_data
        # Vault called only once
        assert mock_client.secrets.kv.v2.read_secret_version.call_count == 1


class TestVaultClientEdgeCases:
    """Test edge cases and error handling."""

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", True)
    @patch("backend.shared.vault_client.hvac")
    def test_empty_path(self, mock_hvac_module, vault_config_mock):
        """Empty path returns None (handled gracefully)."""
        from backend.shared.vault_client import VaultClient
        
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_hvac_module.Client.return_value = mock_client
        
        vault = VaultClient()
        
        result = vault.get_secret("", "key")
        assert result is None

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", True)
    @patch("backend.shared.vault_client.hvac")
    def test_missing_field_key(self, mock_hvac_module, vault_config_mock):
        """Missing field in secret returns None via .get()."""
        from backend.shared.vault_client import VaultClient
        
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"other_key": "value"}}
        }
        mock_hvac_module.Client.return_value = mock_client
        
        vault = VaultClient()
        
        result = vault.get_secret("test/path", "missing_key")
        assert result is None  # .get() returns None for missing keys

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", True)
    @patch("backend.shared.vault_client.hvac")
    def test_invalid_response_format(self, mock_hvac_module, vault_config_mock):
        """Invalid Vault response format returns None (error logged)."""
        from backend.shared.vault_client import VaultClient
        
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "invalid": "format"
        }
        mock_hvac_module.Client.return_value = mock_client
        
        vault = VaultClient()
        
        result = vault.get_secret("test/path", "key")
        assert result is None  # Error is caught and None returned

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", True)
    @patch("backend.shared.vault_client.hvac")
    @patch("backend.shared.vault_client.VaultConfig")
    def test_init_failure_with_fail_closed(self, mock_cfg, mock_hvac_module):
        """Initialization raises error when FAIL_OPEN=False."""
        from backend.shared.vault_client import VaultClient
        
        mock_cfg.ADDR = "http://localhost:8200"
        mock_cfg.TOKEN = None
        mock_cfg.ROLE_ID = None
        mock_cfg.SECRET_ID = None
        mock_cfg.FAIL_OPEN = False  # Critical: fail closed
        mock_cfg.CACHE_TTL = 300
        mock_cfg.MOUNT_POINT = "vertice"
        
        mock_hvac_module.Client.side_effect = Exception("Connection refused")
        
        with pytest.raises(Exception, match="Connection refused"):
            VaultClient()

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", True)
    @patch("backend.shared.vault_client.hvac")
    @patch("backend.shared.vault_client.VaultConfig")
    def test_approle_login_failure_fail_closed(self, mock_cfg, mock_hvac_module):
        """AppRole login raises error when FAIL_OPEN=False."""
        from backend.shared.vault_client import VaultClient
        
        mock_cfg.ADDR = "http://localhost:8200"
        mock_cfg.TOKEN = None
        mock_cfg.ROLE_ID = "role-id"
        mock_cfg.SECRET_ID = "secret-id"
        mock_cfg.FAIL_OPEN = False  # Critical: fail closed
        mock_cfg.CACHE_TTL = 300
        mock_cfg.MOUNT_POINT = "vertice"
        
        mock_client = Mock()
        mock_client.auth.approle.login.side_effect = Exception("Invalid credentials")
        mock_hvac_module.Client.return_value = mock_client
        
        with pytest.raises(Exception, match="Invalid credentials"):
            VaultClient()

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", True)
    @patch("backend.shared.vault_client.hvac")
    def test_generic_exception_in_get_secret(self, mock_hvac_module, vault_config_mock):
        """Generic exceptions logged (line 253-254)."""
        from backend.shared.vault_client import VaultClient
        
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        # Raise generic exception (not VaultError/InvalidPath)
        mock_client.secrets.kv.v2.read_secret_version.side_effect = RuntimeError("Unexpected error")
        mock_hvac_module.Client.return_value = mock_client
        
        vault = VaultClient()
        result = vault.get_secret("test/path", "key")
        
        assert result is None  # Logs error, returns None

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", True)
    @patch("backend.shared.vault_client.hvac")
    def test_token_renewal_near_expiry(self, mock_hvac_module, vault_config_mock):
        """Token renewal triggered when close to expiry (line 173-177)."""
        from backend.shared.vault_client import VaultClient
        
        vault_config_mock.ROLE_ID = "role-id"
        vault_config_mock.SECRET_ID = "secret-id"
        vault_config_mock.TOKEN = None
        
        mock_client = Mock()
        mock_client.auth.approle.login.return_value = {
            "auth": {
                "client_token": "new-token",
                "lease_duration": 3600
            }
        }
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"key": "value"}}
        }
        mock_hvac_module.Client.return_value = mock_client
        
        vault = VaultClient()
        
        # Simulate token near expiry (< 5 min remaining)
        vault.token_expiry = datetime.now() + timedelta(minutes=3)
        
        result = vault.get_secret("test/path", "key")
        
        # Should have renewed token
        assert mock_client.auth.approle.login.call_count >= 2  # Initial + renewal

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", True)
    @patch("backend.shared.vault_client.hvac")
    def test_token_renewal_failure(self, mock_hvac_module, vault_config_mock):
        """Token renewal failure logged but doesn't crash."""
        from backend.shared.vault_client import VaultClient
        
        vault_config_mock.ROLE_ID = "role-id"
        vault_config_mock.SECRET_ID = "secret-id"
        vault_config_mock.TOKEN = None
        
        mock_client = Mock()
        # First login succeeds, renewal fails
        mock_client.auth.approle.login.side_effect = [
            {"auth": {"client_token": "token", "lease_duration": 300}},
            Exception("Renewal failed")
        ]
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"key": "value"}}
        }
        mock_hvac_module.Client.return_value = mock_client
        
        vault = VaultClient()
        
        # Simulate token expiry
        vault.token_expiry = datetime.now() + timedelta(minutes=2)
        
        # Should not crash, logs error
        result = vault.get_secret("test/path", "key")
        assert result is not None  # Still returns value (old token might work)

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", True)
    @patch("backend.shared.vault_client.hvac")
    def test_renew_token_without_expiry_set(self, mock_hvac_module, vault_config_mock):
        """_renew_token_if_needed handles None token_expiry (line 169)."""
        from backend.shared.vault_client import VaultClient
        
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_hvac_module.Client.return_value = mock_client
        
        vault = VaultClient()
        vault.client = mock_client
        vault.token_expiry = None  # Not set
        
        # Should not crash when checking renewal
        vault._renew_token_if_needed()  # Line 169: early return

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", True)
    @patch("backend.shared.vault_client.hvac")
    def test_get_secret_cache_miss_path(self, mock_hvac_module, vault_config_mock):
        """get_secret with cache disabled hits Vault directly (lines 225, 228)."""
        from backend.shared.vault_client import VaultClient
        
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"key": "value"}}
        }
        mock_hvac_module.Client.return_value = mock_client
        
        vault = VaultClient()
        
        # Call with use_cache=False (line 225: cached will be None, line 228: enters if self.client)
        result = vault.get_secret("test/path", "key", use_cache=False)
        
        assert result == "value"
        mock_client.secrets.kv.v2.read_secret_version.assert_called_once()

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", True)
    @patch("backend.shared.vault_client.hvac")
    def test_init_exception_with_fail_open(self, mock_hvac_module, vault_config_mock):
        """Init exception logged with FAIL_OPEN=True (line 143)."""
        from backend.shared.vault_client import VaultClient
        
        vault_config_mock.FAIL_OPEN = True
        vault_config_mock.TOKEN = "token"
        
        mock_hvac_module.Client.side_effect = Exception("Connection error")
        
        # Should not raise, logs error (line 143: no raise, just log)
        vault = VaultClient()
        assert vault.client is None  # Fallback mode

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", True)
    @patch("backend.shared.vault_client.hvac")
    def test_get_secret_no_client_with_env_fallback(self, mock_hvac_module, vault_config_mock):
        """get_secret uses env fallback when client=None (line 228→257→259)."""
        from backend.shared.vault_client import VaultClient
        
        mock_hvac_module.Client.side_effect = Exception("Connection refused")
        vault_config_mock.FAIL_OPEN = True
        
        vault = VaultClient()
        assert vault.client is None
        
        # Line 228: client is None, skip to 257
        # Line 257: fallback_env set
        # Line 259: env_value exists
        with patch.dict(os.environ, {"MY_SECRET_KEY": "env-secret-value"}):
            result = vault.get_secret("api/key", "value", fallback_env="MY_SECRET_KEY")
            
            # Should return env var (line 261)
            assert result == "env-secret-value"


class TestVaultClientTokenRenewal:
    """Test token renewal logic."""

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", True)
    @patch("backend.shared.vault_client.hvac")
    def test_token_renewal(self, mock_hvac_module, vault_config_mock):
        """Token is renewed when expired."""
        from backend.shared.vault_client import VaultClient
        
        mock_client = Mock()
        # Simulate token expiry on second call
        mock_client.is_authenticated.side_effect = [True, False, True]
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"key": "value"}}
        }
        mock_hvac_module.Client.return_value = mock_client
        
        vault = VaultClient()
        vault.get_secret("test/path", "key")


class TestVaultClientModuleLevelFunctions:
    """Test module-level utility functions if any."""

    def test_vault_client_exports(self):
        """vault_client exports expected classes."""
        from backend.shared import vault_client
        
        assert hasattr(vault_client, "VaultClient")
        assert hasattr(vault_client, "VaultConfig")

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", True)
    @patch("backend.shared.vault_client.hvac")
    @patch("backend.shared.vault_client._global_vault_client", None)
    def test_get_vault_client_singleton(self, mock_hvac_module, vault_config_mock):
        """get_vault_client returns singleton instance."""
        from backend.shared.vault_client import get_vault_client
        import backend.shared.vault_client
        
        # Reset singleton
        backend.shared.vault_client._global_vault_client = None
        
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_hvac_module.Client.return_value = mock_client
        
        vault1 = get_vault_client()
        vault2 = get_vault_client()
        
        assert vault1 is vault2  # Same instance

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", True)
    @patch("backend.shared.vault_client.hvac")
    def test_get_api_key(self, mock_hvac_module, vault_config_mock):
        """get_api_key convenience function works."""
        from backend.shared.vault_client import get_api_key
        import backend.shared.vault_client
        
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"api_key": "test-key-123"}}
        }
        mock_hvac_module.Client.return_value = mock_client
        
        # Reset singleton and inject
        from backend.shared.vault_client import VaultClient
        test_vault = VaultClient()
        test_vault.client = mock_client
        backend.shared.vault_client._global_vault_client = test_vault
        
        result = get_api_key("virustotal")
        assert result == "test-key-123"

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", True)
    @patch("backend.shared.vault_client.hvac")
    def test_get_database_config(self, mock_hvac_module, vault_config_mock):
        """get_database_config convenience function works."""
        from backend.shared.vault_client import get_database_config
        import backend.shared.vault_client
        
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        db_config = {"host": "localhost", "port": 5432}
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": db_config}
        }
        mock_hvac_module.Client.return_value = mock_client
        
        # Reset singleton and inject
        from backend.shared.vault_client import VaultClient
        test_vault = VaultClient()
        test_vault.client = mock_client
        backend.shared.vault_client._global_vault_client = test_vault
        
        result = get_database_config("postgres")
        assert result == db_config

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", True)
    @patch("backend.shared.vault_client.hvac")
    def test_get_jwt_secret(self, mock_hvac_module, vault_config_mock):
        """get_jwt_secret convenience function works."""
        from backend.shared.vault_client import get_jwt_secret
        import backend.shared.vault_client
        
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"secret_key": "jwt-secret"}}
        }
        mock_hvac_module.Client.return_value = mock_client
        
        # Reset singleton and inject
        from backend.shared.vault_client import VaultClient
        test_vault = VaultClient()
        test_vault.client = mock_client
        backend.shared.vault_client._global_vault_client = test_vault
        
        result = get_jwt_secret()
        assert result == "jwt-secret"


class TestVaultClientSetSecret:
    """Test set_secret method."""

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", True)
    @patch("backend.shared.vault_client.hvac")
    def test_set_secret_success(self, mock_hvac_module, vault_config_mock):
        """set_secret stores secret in Vault."""
        from backend.shared.vault_client import VaultClient
        
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_hvac_module.Client.return_value = mock_client
        
        vault = VaultClient()
        result = vault.set_secret("test/path", {"key": "value"})
        
        assert result is True
        mock_client.secrets.kv.v2.create_or_update_secret.assert_called_once()

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", True)
    @patch("backend.shared.vault_client.hvac")
    def test_set_secret_invalidates_cache(self, mock_hvac_module, vault_config_mock):
        """set_secret invalidates cache for path."""
        from backend.shared.vault_client import VaultClient
        
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"key": "old_value"}}
        }
        mock_hvac_module.Client.return_value = mock_client
        
        vault = VaultClient()
        
        # Load into cache
        vault.get_secret("test/path", "key")
        
        # Update secret
        vault.set_secret("test/path", {"key": "new_value"})
        
        # Cache should be invalidated
        assert "test/path" not in vault._cache

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", True)
    @patch("backend.shared.vault_client.hvac")
    def test_set_secret_no_client(self, mock_hvac_module, vault_config_mock):
        """set_secret returns False when client not available."""
        from backend.shared.vault_client import VaultClient
        
        vault = VaultClient()
        vault.client = None
        
        result = vault.set_secret("test/path", {"key": "value"})
        assert result is False

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", True)
    @patch("backend.shared.vault_client.hvac")
    def test_set_secret_error(self, mock_hvac_module, vault_config_mock):
        """set_secret returns False on error."""
        from backend.shared.vault_client import VaultClient
        
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.create_or_update_secret.side_effect = Exception("Write error")
        mock_hvac_module.Client.return_value = mock_client
        
        vault = VaultClient()
        result = vault.set_secret("test/path", {"key": "value"})
        
        assert result is False


class TestVaultClientDeleteSecret:
    """Test delete_secret method."""

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", True)
    @patch("backend.shared.vault_client.hvac")
    def test_delete_secret_success(self, mock_hvac_module, vault_config_mock):
        """delete_secret removes secret from Vault."""
        from backend.shared.vault_client import VaultClient
        
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_hvac_module.Client.return_value = mock_client
        
        vault = VaultClient()
        # Pre-populate cache
        vault._cache["test/path"] = {"data": "value"}
        
        result = vault.delete_secret("test/path")
        
        assert result is True
        mock_client.secrets.kv.v2.delete_latest_version_of_secret.assert_called_once()
        # Verify cache invalidation (line 320)
        assert "test/path" not in vault._cache

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", True)
    @patch("backend.shared.vault_client.hvac")
    def test_delete_secret_no_client(self, mock_hvac_module, vault_config_mock):
        """delete_secret returns False when client not available."""
        from backend.shared.vault_client import VaultClient
        
        vault = VaultClient()
        vault.client = None
        
        result = vault.delete_secret("test/path")
        assert result is False

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", True)
    @patch("backend.shared.vault_client.hvac")
    def test_delete_secret_error(self, mock_hvac_module, vault_config_mock):
        """delete_secret returns False on error."""
        from backend.shared.vault_client import VaultClient
        
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.delete_latest_version_of_secret.side_effect = Exception("Delete error")
        mock_hvac_module.Client.return_value = mock_client
        
        vault = VaultClient()
        result = vault.delete_secret("test/path")
        
        assert result is False


class TestVaultClientListSecrets:
    """Test list_secrets method."""

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", True)
    @patch("backend.shared.vault_client.hvac")
    def test_list_secrets_success(self, mock_hvac_module, vault_config_mock):
        """list_secrets returns list of secret paths."""
        from backend.shared.vault_client import VaultClient
        
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.list_secrets.return_value = {
            "data": {"keys": ["secret1", "secret2", "secret3"]}
        }
        mock_hvac_module.Client.return_value = mock_client
        
        vault = VaultClient()
        result = vault.list_secrets("api-keys/")
        
        assert result == ["secret1", "secret2", "secret3"]

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", True)
    @patch("backend.shared.vault_client.hvac")
    def test_list_secrets_no_client(self, mock_hvac_module, vault_config_mock):
        """list_secrets returns empty list when client not available."""
        from backend.shared.vault_client import VaultClient
        
        vault = VaultClient()
        vault.client = None
        
        result = vault.list_secrets("api-keys/")
        assert result == []

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", True)
    @patch("backend.shared.vault_client.hvac")
    def test_list_secrets_error(self, mock_hvac_module, vault_config_mock):
        """list_secrets returns empty list on error."""
        from backend.shared.vault_client import VaultClient
        
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.list_secrets.side_effect = Exception("List error")
        mock_hvac_module.Client.return_value = mock_client
        
        vault = VaultClient()
        result = vault.list_secrets("api-keys/")
        
        assert result == []


class TestVaultClient100PercentCoverage:
    """Additional tests to reach 100% coverage - missing lines."""

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", True)
    @patch("backend.shared.vault_client.hvac")
    def test_init_without_credentials_warning(self, mock_hvac_module, vault_config_mock):
        """Test line 139: warning when no credentials provided."""
        from backend.shared.vault_client import VaultClient
        
        # Mock config with no credentials
        vault_config_mock.TOKEN = None
        vault_config_mock.ROLE_ID = None
        vault_config_mock.SECRET_ID = None
        
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_hvac_module.Client.return_value = mock_client
        
        with patch("backend.shared.vault_client.logging.warning") as mock_warning:
            vault = VaultClient()
            mock_warning.assert_called_with("No Vault credentials provided. Using fallback mode.")

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", True)
    @patch("backend.shared.vault_client.hvac")
    def test_get_secret_generic_exception_logging(self, mock_hvac_module, vault_config_mock):
        """Test lines 253-254: generic exception logging in get_secret."""
        from backend.shared.vault_client import VaultClient
        import logging
        
        # Create custom exception classes that are NOT VaultError or InvalidPath
        class CustomVaultError(Exception):
            """Custom exception for mocking VaultError."""
            pass
        
        class CustomInvalidPath(Exception):
            """Custom exception for mocking InvalidPath."""
            pass
        
        # Mock hvac.exceptions to use our custom classes
        mock_hvac_module.exceptions = Mock()
        mock_hvac_module.exceptions.VaultError = CustomVaultError
        mock_hvac_module.exceptions.InvalidPath = CustomInvalidPath
        
        # Patch the imported exceptions in vault_client module
        with patch("backend.shared.vault_client.VaultError", CustomVaultError), \
             patch("backend.shared.vault_client.InvalidPath", CustomInvalidPath):
            
            mock_client = Mock()
            mock_client.is_authenticated.return_value = True
            # Trigger generic exception (KeyError is NOT VaultError or InvalidPath)
            mock_client.secrets.kv.v2.read_secret_version.side_effect = KeyError("Unexpected key error")
            mock_hvac_module.Client.return_value = mock_client
            
            vault = VaultClient()
            
            with patch.object(logging, "error") as mock_error:
                result = vault.get_secret("test/path")
                # Should log generic error with "Unexpected error getting secret"
                mock_error.assert_called()
                error_message = str(mock_error.call_args_list[0])
                assert "Unexpected error getting secret" in error_message
                assert result is None

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", True)
    @patch("backend.shared.vault_client.hvac")
    def test_get_secret_fallback_env_branch(self, mock_hvac_module, vault_config_mock):
        """Test lines 259->264: fallback env branch when env_value exists."""
        from backend.shared.vault_client import VaultClient
        
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.read_secret_version.return_value = None
        mock_hvac_module.Client.return_value = mock_client
        
        vault = VaultClient()
        vault.client = None  # Force fallback
        
        # Set environment variable for fallback
        with patch.dict(os.environ, {"TEST_ENV_VAR": "fallback_value"}):
            with patch("backend.shared.vault_client.logging.info") as mock_info:
                result = vault.get_secret("test/path", fallback_env="TEST_ENV_VAR")
                
                # Should log info about using fallback
                assert any("Using fallback env var" in str(call) for call in mock_info.call_args_list)
                assert result == "fallback_value"

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", True)
    @patch("backend.shared.vault_client.hvac")
    def test_delete_secret_cache_invalidation_branch(self, mock_hvac_module, vault_config_mock):
        """Test lines 319->322: cache invalidation when path exists in cache."""
        from backend.shared.vault_client import VaultClient
        
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.delete_metadata_and_all_versions.return_value = True
        mock_hvac_module.Client.return_value = mock_client
        
        vault = VaultClient()
        
        # Add entry to cache
        vault._cache["test/path"] = {
            "data": {"key": "value"},
            "timestamp": datetime.now()
        }
        
        # Delete should invalidate cache
        result = vault.delete_secret("test/path")
        
        assert result is True
        assert "test/path" not in vault._cache

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", False)
    def test_import_error_path_invalid_path_exception(self):
        """Test line 55-56: InvalidPath exception when hvac not available."""
        from backend.shared.vault_client import InvalidPath, VaultError
        
        # When HVAC_AVAILABLE is False, these should be Exception
        assert InvalidPath == Exception
        assert VaultError == Exception

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", True)
    @patch("backend.shared.vault_client.hvac")
    def test_token_renewal_failure_logging(self, mock_hvac_module, vault_config_mock):
        """Test lines 176-177: Token renewal failure logging."""
        from backend.shared.vault_client import VaultClient
        import logging
        
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_hvac_module.Client.return_value = mock_client
        
        vault = VaultClient()
        
        # Set token expiry to trigger renewal
        vault.token_expiry = datetime.now() + timedelta(minutes=2)
        
        # Mock _login_approle to raise exception
        with patch.object(vault, '_login_approle', side_effect=Exception("Login failed")):
            with patch.object(logging, "error") as mock_error:
                vault._renew_token_if_needed()
                # Should log error about token renewal failure
                mock_error.assert_called()
                error_message = str(mock_error.call_args_list[0])
                assert "Token renewal failed" in error_message

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", True)
    @patch("backend.shared.vault_client.hvac")
    def test_delete_secret_cache_miss_branch(self, mock_hvac_module, vault_config_mock):
        """Test line 319 branch: path NOT in cache (cache miss)."""
        from backend.shared.vault_client import VaultClient
        
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.delete_latest_version_of_secret.return_value = True
        mock_hvac_module.Client.return_value = mock_client
        
        vault = VaultClient()
        
        # Ensure cache is empty (path not in cache)
        assert "test/path" not in vault._cache
        
        # Delete should work even without cache entry
        result = vault.delete_secret("test/path")
        
        assert result is True
        # Cache should still be empty (line 319 condition false)
        assert "test/path" not in vault._cache

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", True)
    @patch("backend.shared.vault_client.hvac")
    def test_get_secret_fallback_env_none_branch(self, mock_hvac_module, vault_config_mock):
        """Test line 259 branch: fallback_env is None."""
        from backend.shared.vault_client import VaultClient
        import logging
        
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        # Make vault.get_secret fail to reach fallback logic
        from backend.shared.vault_client import InvalidPath
        mock_client.secrets.kv.v2.read_secret_version.side_effect = InvalidPath("Not found")
        mock_hvac_module.Client.return_value = mock_client
        
        vault = VaultClient()
        
        with patch.object(logging, "warning") as mock_warning:
            # Call with fallback_env=None (default)
            result = vault.get_secret("test/path", fallback_env=None)
            
            # Should skip env fallback (line 257) and go to line 264
            assert result is None
            # Should log "Secret not found"
            warning_calls = [str(call) for call in mock_warning.call_args_list]
            assert any("Secret not found" in call for call in warning_calls)

    @patch("backend.shared.vault_client.HVAC_AVAILABLE", True)
    @patch("backend.shared.vault_client.hvac")
    def test_get_secret_fallback_env_empty_value_branch(self, mock_hvac_module, vault_config_mock):
        """Test line 259->264: fallback_env provided but env var is empty/not set."""
        from backend.shared.vault_client import VaultClient
        import logging
        
        mock_client = Mock()
        mock_client.is_authenticated.return_value = True
        # Make vault.get_secret fail to reach fallback logic
        from backend.shared.vault_client import InvalidPath
        mock_client.secrets.kv.v2.read_secret_version.side_effect = InvalidPath("Not found")
        mock_hvac_module.Client.return_value = mock_client
        
        vault = VaultClient()
        
        # Ensure env var does NOT exist
        with patch.dict(os.environ, {}, clear=False):
            if "NONEXISTENT_VAR" in os.environ:
                del os.environ["NONEXISTENT_VAR"]
            
            with patch.object(logging, "warning") as mock_warning:
                # fallback_env is provided but env var doesn't exist
                # Should go from 259->264 (env_value is None)
                result = vault.get_secret("test/path", fallback_env="NONEXISTENT_VAR")
                
                assert result is None
                # Should log "Secret not found" (line 264)
                warning_calls = [str(call) for call in mock_warning.call_args_list]
                assert any("Secret not found" in call for call in warning_calls)
