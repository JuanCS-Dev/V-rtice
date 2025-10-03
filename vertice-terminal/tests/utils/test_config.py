
import pytest
from unittest.mock import patch, mock_open
from pathlib import Path
from vertice.utils.config import Config

# YAML content for mocking
DEFAULT_YAML = """
services:
  ip_intelligence:
    url: http://default-ip-service.com
    timeout: 10
  adr_core:
    url: http://default-adr-service.com
logging:
  level: INFO
"""

USER_YAML = """
# User overrides default
services:
  ip_intelligence:
    url: http://user-ip-service.com # Override URL
    # Timeout is inherited
  new_service:
    url: http://new-service.com
logging:
  level: DEBUG # Override level
"""

USER_YAML_INVALID = "services: [,,,"

@pytest.fixture
def mock_paths(monkeypatch):
    # Mock Path.home() and Path(__file__) to control where the config class looks for files
    monkeypatch.setattr(Path, 'home', lambda: Path('/fake/home'))
    # We need to mock the __file__ attribute of the config module itself
    monkeypatch.setattr('vertice.utils.config.Path.home', lambda: Path('/fake/home'))
    monkeypatch.setattr('vertice.utils.config.Path.exists', lambda self: str(self) == '/fake/home/.vertice/config.yaml')



def test_config_loading_defaults_only():
    # Test loading when only the default config file exists
    with patch("builtins.open", mock_open(read_data=DEFAULT_YAML)) as mock_file:
        # Mock Path.exists to return False for the user file
        with patch('pathlib.Path.exists', return_value=False):
            config_manager = Config()
            # Assert that the default file was opened
            # Note: This assertion is tricky because Config is instantiated once globally.
            # For a real test suite, you'd need to reload the module or structure it differently.
            # Here, we'll just check the loaded values.
            assert config_manager.get("services.ip_intelligence.url") == "http://default-ip-service.com"
            assert config_manager.get("logging.level") == "INFO"

def test_config_loading_with_user_override():
    # Test when user config overrides default config
    def open_side_effect(file, mode='r'):
        if 'default.yaml' in str(file):
            return mock_open(read_data=DEFAULT_YAML).return_value
        elif 'config.yaml' in str(file):
            return mock_open(read_data=USER_YAML).return_value
        return mock_open(read_data='').return_value

    with patch("builtins.open", side_effect=open_side_effect):
        with patch('pathlib.Path.exists', return_value=True):
            config_manager = Config()
            # Assert that user values override default values
            assert config_manager.get("services.ip_intelligence.url") == "http://user-ip-service.com"
            assert config_manager.get("logging.level") == "DEBUG"
            # Assert that new keys from user config are added
            assert config_manager.get("services.new_service.url") == "http://new-service.com"
            # Assert that values from default are inherited if not overridden
            assert config_manager.get("services.ip_intelligence.timeout") == 10

def test_get_nested_key():
    with patch("builtins.open", mock_open(read_data=DEFAULT_YAML)):
        with patch('pathlib.Path.exists', return_value=False):
            config_manager = Config()
            assert config_manager.get("services.adr_core.url") == "http://default-adr-service.com"

def test_get_nonexistent_key():
    with patch("builtins.open", mock_open(read_data=DEFAULT_YAML)):
        with patch('pathlib.Path.exists', return_value=False):
            config_manager = Config()
            # Test getting a key that doesn't exist, should return default (None)
            assert config_manager.get("non.existent.key") is None
            # Test with a provided default value
            assert config_manager.get("non.existent.key", "default_value") == "default_value"

def test_invalid_user_yaml(capsys):
    # Test that a warning is printed for invalid user YAML
    def open_side_effect(file, mode='r'):
        if 'default.yaml' in str(file):
            return mock_open(read_data=DEFAULT_YAML).return_value
        elif 'config.yaml' in str(file):
            return mock_open(read_data=USER_YAML_INVALID).return_value
        return mock_open(read_data='').return_value

    with patch("builtins.open", side_effect=open_side_effect):
        with patch('pathlib.Path.exists', return_value=True):
            Config()
            captured = capsys.readouterr()
            assert "Warning: Could not parse user config file" in captured.out
