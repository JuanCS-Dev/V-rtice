"""
Unit Tests: Plugin Architecture
================================

Tests for the plugin SDK, including:
- BasePlugin abstract class
- Hook system (decorator, registration, emission)
- Plugin registry (discovery, loading, lifecycle)
- Plugin loader (dependencies, validation)
"""

import pytest
from pathlib import Path
from typing import Dict, Any, Optional
from unittest.mock import Mock, MagicMock, patch, call
import tempfile
import shutil

from vertice.plugins import (
    BasePlugin,
    PluginMetadata,
    PluginError,
    PluginLoadError,
    hook,
    HookPriority,
    HookContext,
    HookSystem,
    PluginRegistry,
    PluginLoader,
)


# ========================================
# Test Plugins
# ========================================


class MinimalPlugin(BasePlugin):
    """Minimal plugin for testing."""

    name = "minimal"
    version = "1.0.0"
    author = "test@example.com"
    description = "Minimal test plugin"


class CompletePlugin(BasePlugin):
    """Complete plugin with all features."""

    name = "complete"
    version = "2.0.0"
    author = "test@example.com"
    description = "Complete test plugin"
    homepage = "https://example.com"
    license = "MIT"
    dependencies = ["requests>=2.28.0"]
    vertice_min_version = "1.0.0"

    def __init__(self):
        super().__init__()
        self.hook_called = False
        self.enrichment_data = {}

    @hook("on_host_discovered", priority=HookPriority.HIGH)
    def on_host_discovered_handler(self, context: HookContext):
        """Hook handler for host discovery."""
        self.hook_called = True
        host = context.data.get("host")

        # Return enrichment data
        return {
            "plugin_name": self.name,
            "enriched": True,
            "host_ip": getattr(host, "ip_address", None),
        }

    @hook("on_scan_complete", priority=HookPriority.LOW)
    def on_scan_complete_handler(self, context: HookContext):
        """Hook handler for scan completion."""
        return {"scan_processed": True}


class ConfigurablePlugin(BasePlugin):
    """Plugin requiring configuration."""

    name = "configurable"
    version = "1.0.0"
    author = "test@example.com"

    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize with required API key."""
        super().initialize(config)

        self.api_key = config.get("api_key")
        if not self.api_key:
            raise PluginLoadError("API key required")


# ========================================
# Test BasePlugin
# ========================================


class TestBasePlugin:
    """Test BasePlugin abstract class."""

    def test_create_minimal_plugin(self):
        """Test creating minimal plugin."""
        plugin = MinimalPlugin()

        assert plugin.name == "minimal"
        assert plugin.version == "1.0.0"
        assert plugin.author == "test@example.com"
        assert plugin.description == "Minimal test plugin"

    def test_plugin_metadata(self):
        """Test plugin metadata extraction."""
        plugin = CompletePlugin()
        metadata = plugin.get_metadata()

        assert isinstance(metadata, PluginMetadata)
        assert metadata.name == "complete"
        assert metadata.version == "2.0.0"
        assert metadata.author == "test@example.com"
        assert metadata.description == "Complete test plugin"
        assert metadata.homepage == "https://example.com"
        assert metadata.license == "MIT"
        assert metadata.dependencies == ["requests>=2.28.0"]
        assert metadata.vertice_min_version == "1.0.0"

    def test_plugin_initialization(self):
        """Test plugin initialization."""
        plugin = MinimalPlugin()
        config = {"setting1": "value1", "setting2": 42}

        plugin.initialize(config)

        assert plugin._initialized is True
        assert plugin._config == config

    def test_plugin_activation(self):
        """Test plugin activation."""
        plugin = MinimalPlugin()
        plugin.initialize({})  # Must initialize before activate

        assert plugin._enabled is False

        plugin.activate()

        assert plugin._enabled is True

    def test_plugin_deactivation(self):
        """Test plugin deactivation."""
        plugin = MinimalPlugin()
        plugin.initialize({})  # Must initialize before activate
        plugin.activate()

        assert plugin._enabled is True

        plugin.deactivate()

        assert plugin._enabled is False

    def test_plugin_lifecycle(self):
        """Test full plugin lifecycle."""
        plugin = MinimalPlugin()

        # Initial state
        assert plugin._initialized is False
        assert plugin._enabled is False

        # Initialize
        plugin.initialize({"key": "value"})
        assert plugin._initialized is True

        # Activate
        plugin.activate()
        assert plugin._enabled is True

        # Deactivate
        plugin.deactivate()
        assert plugin._enabled is False

    def test_configurable_plugin_requires_api_key(self):
        """Test plugin requiring configuration."""
        plugin = ConfigurablePlugin()

        # Should raise error without API key
        with pytest.raises(PluginLoadError, match="API key required"):
            plugin.initialize({})

        # Should succeed with API key
        plugin.initialize({"api_key": "secret_key_123"})
        assert plugin.api_key == "secret_key_123"


# ========================================
# Test Hook System
# ========================================


class TestHookDecorator:
    """Test @hook decorator."""

    def test_hook_decorator_adds_metadata(self):
        """Test decorator adds hook metadata."""
        plugin = CompletePlugin()
        handler = plugin.on_host_discovered_handler

        assert hasattr(handler, "_hook_metadata")
        assert len(handler._hook_metadata) == 1

        hook_meta = handler._hook_metadata[0]
        assert hook_meta["event_name"] == "on_host_discovered"
        assert hook_meta["priority"] == HookPriority.HIGH

    def test_hook_decorator_multiple_hooks(self):
        """Test multiple hooks on same method."""

        class MultiHookPlugin(BasePlugin):
            name = "multi"
            version = "1.0.0"
            author = "test"

            @hook("event_a")
            @hook("event_b", priority=HookPriority.HIGH)
            def multi_handler(self, context):
                pass

        plugin = MultiHookPlugin()
        assert len(plugin.multi_handler._hook_metadata) == 2


class TestHookSystem:
    """Test HookSystem event management."""

    @pytest.fixture
    def hook_system(self):
        """Create fresh HookSystem instance."""
        return HookSystem()

    def test_register_hook_handler(self, hook_system):
        """Test registering hook handler."""
        def handler(context):
            return {"result": "ok"}

        hook_system.register(
            event_name="on_test_event",
            handler=handler,
            priority=HookPriority.NORMAL,
            plugin_name="test_plugin",
        )

        assert "on_test_event" in hook_system._hooks
        assert len(hook_system._hooks["on_test_event"]) == 1

    def test_emit_hook_triggers_handler(self, hook_system):
        """Test emitting hook triggers handler."""
        handler_called = False

        def handler(context):
            nonlocal handler_called
            handler_called = True
            return {"result": "success"}

        hook_system.register(
            event_name="on_test_event",
            handler=handler,
            priority=HookPriority.NORMAL,
            plugin_name="test_plugin",
        )

        results = hook_system.emit("on_test_event", test_data="value")

        assert handler_called is True
        assert len(results) == 1
        assert results[0] == {"result": "success"}

    def test_hook_priority_ordering(self, hook_system):
        """Test hooks execute in priority order."""
        execution_order = []

        def handler_high(context):
            execution_order.append("high")

        def handler_normal(context):
            execution_order.append("normal")

        def handler_low(context):
            execution_order.append("low")

        # Register in random order
        hook_system.register("event", handler_normal, HookPriority.NORMAL, "p1")
        hook_system.register("event", handler_low, HookPriority.LOW, "p2")
        hook_system.register("event", handler_high, HookPriority.HIGH, "p3")

        hook_system.emit("event")

        assert execution_order == ["high", "normal", "low"]

    def test_hook_stop_propagation(self, hook_system):
        """Test stop_propagation prevents subsequent hooks."""
        handler1_called = False
        handler2_called = False

        def handler1(context):
            nonlocal handler1_called
            handler1_called = True
            context.stop_propagation = True

        def handler2(context):
            nonlocal handler2_called
            handler2_called = True

        hook_system.register("event", handler1, HookPriority.HIGH, "p1")
        hook_system.register("event", handler2, HookPriority.NORMAL, "p2")

        hook_system.emit("event")

        assert handler1_called is True
        assert handler2_called is False

    def test_hook_context_data(self, hook_system):
        """Test hook receives context data."""
        captured_context = None

        def handler(context):
            nonlocal captured_context
            captured_context = context

        hook_system.register("event", handler, HookPriority.NORMAL, "plugin")
        hook_system.emit("event", host="10.0.0.1", port=80)

        assert captured_context is not None
        assert captured_context.event_name == "event"
        assert captured_context.data["host"] == "10.0.0.1"
        assert captured_context.data["port"] == 80

    def test_unregister_plugin_hooks(self, hook_system):
        """Test unregistering all hooks for a plugin."""
        def handler1(context):
            pass

        def handler2(context):
            pass

        hook_system.register("event1", handler1, HookPriority.NORMAL, "plugin1")
        hook_system.register("event2", handler2, HookPriority.NORMAL, "plugin1")

        assert len(hook_system._hooks["event1"]) == 1
        assert len(hook_system._hooks["event2"]) == 1

        hook_system.unregister_plugin("plugin1")

        assert len(hook_system._hooks["event1"]) == 0
        assert len(hook_system._hooks["event2"]) == 0

    def test_get_hook_stats(self, hook_system):
        """Test hook system statistics."""
        def handler(context):
            pass

        hook_system.register("event1", handler, HookPriority.NORMAL, "plugin1")
        hook_system.register("event2", handler, HookPriority.HIGH, "plugin2")
        hook_system.register("event2", handler, HookPriority.LOW, "plugin3")

        stats = hook_system.get_stats()

        assert stats["total_hooks"] == 2  # 2 unique events
        assert stats["registered_handlers"] == 3  # 3 total handlers
        assert stats["active_plugins"] == 3  # 3 unique plugins


# ========================================
# Test PluginLoader
# ========================================


class TestPluginLoader:
    """Test PluginLoader dependency and validation."""

    @pytest.fixture
    def loader(self):
        """Create PluginLoader instance."""
        return PluginLoader(vertice_version="1.0.0")

    def test_version_compatibility_check_pass(self, loader):
        """Test version compatibility check passes."""
        result = loader.check_compatibility("0.9.0")
        assert result is True

    def test_version_compatibility_check_fail(self, loader):
        """Test version compatibility check fails."""
        with pytest.raises(PluginLoadError, match="requires Vértice >= 2.0.0"):
            loader.check_compatibility("2.0.0")

    @patch("subprocess.check_call")
    def test_install_dependencies_missing(self, mock_subprocess, loader):
        """Test installing missing dependencies."""
        # Mock that package is not installed
        with patch.object(loader, "_check_dependency_installed", return_value=False):
            result = loader.install_dependencies(["requests>=2.28.0"])

        assert result is True
        mock_subprocess.assert_called_once()

    def test_install_dependencies_already_installed(self, loader):
        """Test dependencies already installed."""
        # Mock that package is installed
        with patch.object(loader, "_check_dependency_installed", return_value=True):
            result = loader.install_dependencies(["requests>=2.28.0"])

        assert result is True

    def test_install_dependencies_dry_run(self, loader):
        """Test dry run mode."""
        with patch.object(loader, "_check_dependency_installed", return_value=False):
            result = loader.install_dependencies(["missing_package"], dry_run=True)

        assert result is False

    def test_load_from_file_success(self, loader):
        """Test loading plugin from file."""
        # Create temporary plugin file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("""
from vertice.plugins import BasePlugin

class TestPlugin(BasePlugin):
    name = "test"
    version = "1.0.0"
    author = "test"
    description = "Test plugin"
""")
            temp_path = Path(f.name)

        try:
            plugin = loader.load_from_file(temp_path, config={})

            assert plugin is not None
            assert plugin.name == "test"
            assert plugin.version == "1.0.0"

        finally:
            temp_path.unlink()

    def test_load_from_file_not_found(self, loader):
        """Test loading from non-existent file."""
        with pytest.raises(PluginLoadError, match="not found"):
            loader.load_from_file(Path("/nonexistent/plugin.py"))

    def test_load_from_file_no_plugin_class(self, loader):
        """Test loading file without BasePlugin subclass."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("""
# No BasePlugin subclass here
def some_function():
    pass
""")
            temp_path = Path(f.name)

        try:
            with pytest.raises(PluginLoadError, match="No BasePlugin subclass found"):
                loader.load_from_file(temp_path)

        finally:
            temp_path.unlink()


# ========================================
# Test PluginRegistry
# ========================================


class TestPluginRegistry:
    """Test PluginRegistry discovery and management."""

    @pytest.fixture
    def temp_plugin_dir(self):
        """Create temporary plugin directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def registry(self, temp_plugin_dir):
        """Create PluginRegistry with temporary directory."""
        return PluginRegistry(plugin_dirs=[temp_plugin_dir])

    def test_discover_plugins_empty(self, registry, temp_plugin_dir):
        """Test discovering plugins in empty directory."""
        discovered = registry.discover_plugins()
        assert discovered == []

    def test_discover_plugins_single_file(self, registry, temp_plugin_dir):
        """Test discovering single-file plugin."""
        # Create plugin file
        plugin_file = temp_plugin_dir / "test_plugin.py"
        plugin_file.write_text("""
from vertice.plugins import BasePlugin

class TestPlugin(BasePlugin):
    name = "test"
    version = "1.0.0"
    author = "test"
""")

        discovered = registry.discover_plugins()
        assert "test_plugin" in discovered

    def test_discover_plugins_package(self, registry, temp_plugin_dir):
        """Test discovering plugin package."""
        # Create plugin package
        plugin_pkg = temp_plugin_dir / "my_plugin"
        plugin_pkg.mkdir()
        (plugin_pkg / "__init__.py").write_text("""
from vertice.plugins import BasePlugin

class MyPlugin(BasePlugin):
    name = "my_plugin"
    version = "1.0.0"
    author = "test"
""")

        discovered = registry.discover_plugins()
        assert "my_plugin" in discovered

    def test_get_plugin_not_loaded(self, registry):
        """Test getting plugin that's not loaded."""
        plugin = registry.get_plugin("nonexistent")
        assert plugin is None

    def test_list_plugins_empty(self, registry):
        """Test listing plugins when none loaded."""
        plugins = registry.list_plugins()
        assert len(plugins) == 0

    def test_list_plugins_enabled_only(self, registry):
        """Test listing only enabled plugins."""
        # This would require loading actual plugins
        # For now, test with empty registry
        plugins = registry.list_plugins(enabled_only=True)
        assert len(plugins) == 0

    def test_get_stats_empty(self, registry):
        """Test statistics for empty registry."""
        stats = registry.get_stats()

        assert stats["total_plugins"] == 0
        assert stats["enabled_plugins"] == 0
        assert stats["disabled_plugins"] == 0
        assert stats["plugins"] == {}


# ========================================
# Integration Tests
# ========================================


class TestPluginIntegration:
    """Integration tests for complete plugin workflow."""

    def test_complete_plugin_lifecycle(self):
        """Test complete plugin lifecycle: register hooks → emit events → receive data."""
        # Create plugin
        plugin = CompletePlugin()
        plugin.initialize({})
        plugin.activate()

        # Create hook system
        hook_system = HookSystem()

        # Register plugin hooks manually (simulating PluginRegistry behavior)
        for method_name in dir(plugin):
            method = getattr(plugin, method_name)
            if hasattr(method, "_hook_metadata"):
                for hook_meta in method._hook_metadata:
                    hook_system.register(
                        event_name=hook_meta["event_name"],
                        handler=method,
                        priority=hook_meta["priority"],
                        plugin_name=plugin.name,
                    )

        # Emit event
        mock_host = Mock(ip_address="10.0.0.1")
        results = hook_system.emit("on_host_discovered", host=mock_host)

        # Verify plugin received event
        assert plugin.hook_called is True
        assert len(results) == 1
        assert results[0]["plugin_name"] == "complete"
        assert results[0]["enriched"] is True
        assert results[0]["host_ip"] == "10.0.0.1"

    def test_multiple_plugins_same_hook(self):
        """Test multiple plugins handling same hook."""
        plugin1 = CompletePlugin()
        plugin1.name = "plugin1"

        plugin2 = CompletePlugin()
        plugin2.name = "plugin2"

        hook_system = HookSystem()

        # Register both plugins
        for plugin in [plugin1, plugin2]:
            for method_name in dir(plugin):
                method = getattr(plugin, method_name)
                if hasattr(method, "_hook_metadata"):
                    for hook_meta in method._hook_metadata:
                        hook_system.register(
                            event_name=hook_meta["event_name"],
                            handler=method,
                            priority=hook_meta["priority"],
                            plugin_name=plugin.name,
                        )

        # Emit event
        mock_host = Mock(ip_address="10.0.0.1")
        results = hook_system.emit("on_host_discovered", host=mock_host)

        # Both plugins should have processed the event
        assert len(results) == 2
        assert results[0]["plugin_name"] == "plugin1"
        assert results[1]["plugin_name"] == "plugin2"
