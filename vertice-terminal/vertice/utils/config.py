import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """Configuration manager for the Vertice CLI.

    Loads default configuration and overrides with user-specific settings.
    """

    def __init__(self):
        self.config_dir = Path.home() / ".vertice"
        self.config_file = self.config_dir / "config.yaml"
        # Path to the default config file within the package
        self.default_config_path = (
            Path(__file__).parent.parent / "config" / "default.yaml"
        )
        self.config = self._load()

    def _load(self) -> Dict[str, Any]:
        """
        Loads configuration by first loading defaults and then overriding with user settings.

        Returns:
            Dict[str, Any]: The merged configuration dictionary.
        """
        # Load default configuration
        with open(self.default_config_path, "r") as f:
            config = yaml.safe_load(f)

        # Override with user configuration if it exists
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    user_config = yaml.safe_load(f)
                    if user_config:
                        self._deep_merge(config, user_config)
            except yaml.YAMLError as e:
                print(
                    f"Warning: Could not parse user config file {self.config_file}: {e}"
                )
            except Exception as e:
                print(
                    f"Warning: Unexpected error loading user config file {self.config_file}: {e}"
                )

        return config

    def _deep_merge(self, default_dict: Dict, user_dict: Dict):
        """
        Recursively merges user_dict into default_dict.
        """
        for key, value in user_dict.items():
            if (
                key in default_dict
                and isinstance(default_dict[key], dict)
                and isinstance(value, dict)
            ):
                self._deep_merge(default_dict[key], value)
            else:
                default_dict[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieves a configuration value using a dot-separated key path.

        Args:
            key (str): The dot-separated path to the configuration value (e.g., "api.base_url").
            default (Any): The default value to return if the key is not found.

        Returns:
            Any: The configuration value, or the default if not found.
        """
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default  # Key path diverged from dictionary structure
            if value is None:
                return default

        return value


# Global instance of the Config manager for easy access throughout the CLI
config = Config()
