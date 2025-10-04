"""
🔌 Vértice Plugin System
========================

Extensible plugin architecture for community-driven tool integrations.

Components:
- BasePlugin: Abstract base class for all plugins
- PluginRegistry: Discovery and loading of plugins
- HookSystem: Event-driven integration points
- PluginLoader: Dynamic plugin loading

Philosophy:
- Open ecosystem - anyone can create plugins
- Event-driven - plugins hook into Vértice events
- Sandboxed - plugins run in isolated context
- Zero core changes - plugins extend without modifying core

Example Plugin:
    from vertice.plugins import BasePlugin, hook

    class ShodanPlugin(BasePlugin):
        name = "shodan"
        version = "1.0.0"
        author = "security-researcher"

        @hook("on_host_discovered")
        def enrich_host(self, host):
            # Enrich host with Shodan data
            return shodan_client.host(host.ip)

Usage:
    from vertice.plugins import PluginRegistry

    registry = PluginRegistry()
    registry.load_plugins()
    registry.emit_event("on_host_discovered", host=host_obj)
"""

from .base import (
    BasePlugin,
    PluginMetadata,
    PluginError,
    PluginLoadError,
    PluginExecutionError,
)
from .hooks import (
    HookSystem,
    hook,
    HookPriority,
    HookContext,
)
from .registry import (
    PluginRegistry,
    PluginInfo,
)
from .loader import PluginLoader

__all__ = [
    "BasePlugin",
    "PluginMetadata",
    "PluginError",
    "PluginLoadError",
    "PluginExecutionError",
    "HookSystem",
    "hook",
    "HookPriority",
    "HookContext",
    "PluginRegistry",
    "PluginInfo",
    "PluginLoader",
]
