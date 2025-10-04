"""
Plugin Registry
===============

Discovery, loading, and management of plugins.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Type, Any
from pathlib import Path
import logging
import importlib
import inspect

from .base import BasePlugin, PluginMetadata, PluginLoadError
from .hooks import get_hook_system, HookPriority

logger = logging.getLogger(__name__)


@dataclass
class PluginInfo:
    """
    Information about a loaded plugin.

    Attributes:
        name: Plugin name
        instance: Plugin instance
        metadata: Plugin metadata
        module_path: Path to plugin module
        enabled: Whether plugin is enabled
    """
    name: str
    instance: BasePlugin
    metadata: PluginMetadata
    module_path: str
    enabled: bool = False


class PluginRegistry:
    """
    Central registry for plugin discovery and management.

    Features:
    - Auto-discovery of installed plugins
    - Dynamic loading
    - Dependency checking
    - Hook registration
    - Lifecycle management

    Plugin Discovery Paths:
    1. ~/.vertice/plugins/  (user plugins)
    2. /usr/share/vertice/plugins/  (system plugins)
    3. <venv>/lib/pythonX.X/site-packages/vertice_plugins/  (pip installed)

    Example:
        registry = PluginRegistry()
        registry.discover_plugins()
        registry.load_all()

        # Use plugin
        shodan = registry.get_plugin("shodan")
        result = shodan.search_ip("1.2.3.4")
    """

    def __init__(self, plugin_dirs: Optional[List[Path]] = None):
        """
        Initialize plugin registry.

        Args:
            plugin_dirs: Additional plugin search directories
        """
        self._plugins: Dict[str, PluginInfo] = {}
        self._hook_system = get_hook_system()

        # Default plugin search paths
        self._plugin_dirs = [
            Path.home() / ".vertice" / "plugins",
            Path("/usr/share/vertice/plugins"),
        ]

        if plugin_dirs:
            self._plugin_dirs.extend(plugin_dirs)

        logger.info(f"PluginRegistry initialized with {len(self._plugin_dirs)} search paths")

    def discover_plugins(self) -> List[str]:
        """
        Discover available plugins in search paths.

        Returns:
            List of discovered plugin names
        """
        discovered = []

        for plugin_dir in self._plugin_dirs:
            if not plugin_dir.exists():
                logger.debug(f"Plugin directory does not exist: {plugin_dir}")
                continue

            logger.debug(f"Scanning for plugins in: {plugin_dir}")

            # Look for Python files or packages
            for item in plugin_dir.iterdir():
                if item.is_file() and item.suffix == ".py":
                    # Single-file plugin
                    plugin_name = item.stem
                    if plugin_name not in discovered:
                        discovered.append(plugin_name)
                        logger.debug(f"Discovered plugin: {plugin_name} ({item})")

                elif item.is_dir() and (item / "__init__.py").exists():
                    # Package plugin
                    plugin_name = item.name
                    if plugin_name not in discovered:
                        discovered.append(plugin_name)
                        logger.debug(f"Discovered plugin package: {plugin_name} ({item})")

        logger.info(f"Discovered {len(discovered)} plugins")

        return discovered

    def load_plugin(
        self,
        plugin_name: str,
        config: Optional[Dict[str, Any]] = None
    ) -> BasePlugin:
        """
        Load and initialize plugin.

        Args:
            plugin_name: Plugin name (module name)
            config: Plugin configuration

        Returns:
            Loaded plugin instance

        Raises:
            PluginLoadError: If plugin fails to load
        """
        if plugin_name in self._plugins:
            logger.warning(f"Plugin already loaded: {plugin_name}")
            return self._plugins[plugin_name].instance

        config = config or {}

        try:
            # Import plugin module
            module = importlib.import_module(f"vertice_plugins.{plugin_name}")

            # Find BasePlugin subclass
            plugin_class = self._find_plugin_class(module)

            if not plugin_class:
                raise PluginLoadError(f"No BasePlugin subclass found in {plugin_name}")

            # Instantiate plugin
            plugin_instance = plugin_class()

            # Initialize
            plugin_instance.initialize(config)

            # Get metadata
            metadata = plugin_instance.get_metadata()

            # Register hooks
            self._register_plugin_hooks(plugin_instance)

            # Store plugin info
            plugin_info = PluginInfo(
                name=plugin_name,
                instance=plugin_instance,
                metadata=metadata,
                module_path=module.__file__,
                enabled=False,
            )

            self._plugins[plugin_name] = plugin_info

            logger.info(f"Plugin loaded: {plugin_name} v{metadata.version}")

            return plugin_instance

        except ImportError as e:
            raise PluginLoadError(f"Failed to import plugin {plugin_name}: {e}")

        except Exception as e:
            raise PluginLoadError(f"Failed to load plugin {plugin_name}: {e}")

    def _find_plugin_class(self, module) -> Optional[Type[BasePlugin]]:
        """
        Find BasePlugin subclass in module.

        Args:
            module: Imported module

        Returns:
            Plugin class or None
        """
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, BasePlugin) and obj is not BasePlugin:
                return obj

        return None

    def _register_plugin_hooks(self, plugin: BasePlugin) -> None:
        """
        Register plugin's hook methods.

        Args:
            plugin: Plugin instance
        """
        # Find methods with _hook_metadata attribute
        for method_name in dir(plugin):
            method = getattr(plugin, method_name)

            if hasattr(method, '_hook_metadata'):
                # Method decorated with @hook
                for hook_meta in method._hook_metadata:
                    self._hook_system.register(
                        event_name=hook_meta["event_name"],
                        handler=method,
                        priority=hook_meta["priority"],
                        plugin_name=plugin.name,
                    )

                    logger.debug(
                        f"Registered hook: {plugin.name}.{method_name} "
                        f"→ {hook_meta['event_name']}"
                    )

    def load_all(self, config: Optional[Dict[str, Dict[str, Any]]] = None) -> List[str]:
        """
        Load all discovered plugins.

        Args:
            config: Dict of plugin configs (plugin_name → config dict)

        Returns:
            List of loaded plugin names
        """
        config = config or {}
        discovered = self.discover_plugins()
        loaded = []

        for plugin_name in discovered:
            try:
                plugin_config = config.get(plugin_name, {})
                self.load_plugin(plugin_name, plugin_config)
                loaded.append(plugin_name)

            except PluginLoadError as e:
                logger.error(f"Failed to load plugin {plugin_name}: {e}")
                continue

        logger.info(f"Loaded {len(loaded)}/{len(discovered)} plugins")

        return loaded

    def enable_plugin(self, plugin_name: str) -> None:
        """
        Enable plugin.

        Args:
            plugin_name: Plugin name
        """
        if plugin_name not in self._plugins:
            raise PluginLoadError(f"Plugin not loaded: {plugin_name}")

        plugin_info = self._plugins[plugin_name]

        if plugin_info.enabled:
            logger.warning(f"Plugin already enabled: {plugin_name}")
            return

        # Activate plugin
        plugin_info.instance.activate()
        plugin_info.enabled = True

        logger.info(f"Plugin enabled: {plugin_name}")

    def disable_plugin(self, plugin_name: str) -> None:
        """
        Disable plugin.

        Args:
            plugin_name: Plugin name
        """
        if plugin_name not in self._plugins:
            logger.warning(f"Plugin not loaded: {plugin_name}")
            return

        plugin_info = self._plugins[plugin_name]

        if not plugin_info.enabled:
            logger.warning(f"Plugin already disabled: {plugin_name}")
            return

        # Deactivate plugin
        plugin_info.instance.deactivate()
        plugin_info.enabled = False

        # Unregister hooks
        self._hook_system.unregister_plugin(plugin_name)

        logger.info(f"Plugin disabled: {plugin_name}")

    def unload_plugin(self, plugin_name: str) -> None:
        """
        Unload plugin completely.

        Args:
            plugin_name: Plugin name
        """
        if plugin_name not in self._plugins:
            return

        # Disable first
        if self._plugins[plugin_name].enabled:
            self.disable_plugin(plugin_name)

        # Remove from registry
        del self._plugins[plugin_name]

        logger.info(f"Plugin unloaded: {plugin_name}")

    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """
        Get loaded plugin instance.

        Args:
            plugin_name: Plugin name

        Returns:
            Plugin instance or None
        """
        plugin_info = self._plugins.get(plugin_name)
        return plugin_info.instance if plugin_info else None

    def list_plugins(self, enabled_only: bool = False) -> List[PluginInfo]:
        """
        List loaded plugins.

        Args:
            enabled_only: Only return enabled plugins

        Returns:
            List of PluginInfo
        """
        plugins = list(self._plugins.values())

        if enabled_only:
            plugins = [p for p in plugins if p.enabled]

        return plugins

    def get_stats(self) -> Dict[str, Any]:
        """
        Get registry statistics.

        Returns:
            Stats dict
        """
        total = len(self._plugins)
        enabled = sum(1 for p in self._plugins.values() if p.enabled)

        return {
            "total_plugins": total,
            "enabled_plugins": enabled,
            "disabled_plugins": total - enabled,
            "plugins": {
                name: {
                    "version": info.metadata.version,
                    "enabled": info.enabled,
                }
                for name, info in self._plugins.items()
            },
            "hook_stats": self._hook_system.get_stats(),
        }
