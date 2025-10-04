"""
Plugin Base Classes
===================

Abstract base classes and metadata for Vértice plugins.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class PluginError(Exception):
    """Base exception for plugin errors."""
    pass


class PluginLoadError(PluginError):
    """Raised when plugin fails to load."""
    pass


class PluginExecutionError(PluginError):
    """Raised when plugin execution fails."""
    pass


@dataclass
class PluginMetadata:
    """
    Plugin metadata.

    Attributes:
        name: Plugin identifier (must be unique)
        version: Semantic version (e.g., "1.0.0")
        author: Plugin author/maintainer
        description: Short description
        homepage: URL to plugin homepage/repo
        license: License identifier (e.g., "MIT", "Apache-2.0")
        dependencies: Python dependencies (pip installable)
        vertice_min_version: Minimum Vértice CLI version required
    """
    name: str
    version: str
    author: str
    description: str = ""
    homepage: str = ""
    license: str = "MIT"
    dependencies: List[str] = field(default_factory=list)
    vertice_min_version: str = "1.0.0"

    # Categories for marketplace
    categories: List[str] = field(default_factory=list)  # e.g., ["recon", "osint"]
    tags: List[str] = field(default_factory=list)


class BasePlugin(ABC):
    """
    Abstract base class for all Vértice plugins.

    Plugins extend Vértice functionality by:
    - Hooking into events (on_host_discovered, on_scan_complete, etc.)
    - Adding new CLI commands
    - Integrating with external services
    - Adding new tool executors

    Lifecycle:
    1. Discovery: PluginRegistry finds plugin
    2. Load: PluginLoader instantiates plugin
    3. Initialize: Plugin.initialize() called
    4. Activate: Plugin.activate() called
    5. Execution: Hooks triggered by events
    6. Deactivate: Plugin.deactivate() called

    Example:
        class MyPlugin(BasePlugin):
            name = "my-plugin"
            version = "1.0.0"
            author = "me@example.com"

            def initialize(self, config):
                self.api_key = config.get("api_key")

            @hook("on_host_discovered")
            def enrich_host(self, host):
                # Custom logic
                return enriched_data
    """

    # Required metadata (override in subclass)
    name: str = ""
    version: str = "0.0.0"
    author: str = ""
    description: str = ""

    # Optional metadata
    homepage: str = ""
    license: str = "MIT"
    dependencies: List[str] = []
    vertice_min_version: str = "1.0.0"

    def __init__(self):
        """Initialize plugin instance."""
        if not self.name:
            raise PluginLoadError(f"Plugin must define 'name' attribute")

        if not self.version:
            raise PluginLoadError(f"Plugin {self.name} must define 'version' attribute")

        self._config: Dict[str, Any] = {}
        self._enabled: bool = False
        self._initialized: bool = False

        logger.info(f"Plugin {self.name} v{self.version} instantiated")

    def get_metadata(self) -> PluginMetadata:
        """
        Get plugin metadata.

        Returns:
            PluginMetadata object
        """
        return PluginMetadata(
            name=self.name,
            version=self.version,
            author=self.author,
            description=self.description,
            homepage=self.homepage,
            license=self.license,
            dependencies=self.dependencies,
            vertice_min_version=self.vertice_min_version,
        )

    def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize plugin with configuration.

        Called once after plugin is loaded.

        Args:
            config: Plugin configuration from config file or CLI

        Example:
            def initialize(self, config):
                self.api_key = config.get("api_key")
                if not self.api_key:
                    raise PluginLoadError("api_key required")
        """
        self._config = config
        self._initialized = True

        logger.info(f"Plugin {self.name} initialized")

    def activate(self) -> None:
        """
        Activate plugin.

        Called when plugin is enabled. Use for:
        - Starting background tasks
        - Opening connections
        - Registering CLI commands

        Example:
            def activate(self):
                self.client = SomeAPIClient(self._config["api_key"])
        """
        if not self._initialized:
            raise PluginError(f"Plugin {self.name} not initialized")

        self._enabled = True
        logger.info(f"Plugin {self.name} activated")

    def deactivate(self) -> None:
        """
        Deactivate plugin.

        Called when plugin is disabled or CLI exits. Use for:
        - Cleanup resources
        - Closing connections
        - Saving state

        Example:
            def deactivate(self):
                self.client.close()
        """
        self._enabled = False
        logger.info(f"Plugin {self.name} deactivated")

    def is_enabled(self) -> bool:
        """Check if plugin is enabled."""
        return self._enabled

    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.

        Args:
            key: Config key
            default: Default value if key not found

        Returns:
            Config value
        """
        return self._config.get(key, default)

    def set_config(self, key: str, value: Any) -> None:
        """
        Set configuration value.

        Args:
            key: Config key
            value: Config value
        """
        self._config[key] = value

    # ===== HOOK METHODS =====
    # These are examples - actual hooks defined via @hook decorator

    def on_host_discovered(self, host: Any) -> Optional[Dict[str, Any]]:
        """
        Hook: Called when new host is discovered.

        Args:
            host: Host object

        Returns:
            Enrichment data to add to host (optional)
        """
        pass

    def on_vulnerability_found(self, vulnerability: Any) -> Optional[Dict[str, Any]]:
        """
        Hook: Called when vulnerability is found.

        Args:
            vulnerability: Vulnerability object

        Returns:
            Enrichment data (optional)
        """
        pass

    def on_scan_complete(self, scan_result: Any) -> None:
        """
        Hook: Called when scan completes.

        Args:
            scan_result: Scan result object
        """
        pass

    def on_project_created(self, project: Any) -> None:
        """
        Hook: Called when project is created.

        Args:
            project: Project object
        """
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.name} v{self.version}>"
