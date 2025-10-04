"""
Plugin Loader
=============

Dynamic plugin loading with dependency checking and sandboxing.
"""

from typing import Optional, List, Dict, Any
from pathlib import Path
import sys
import subprocess
import logging

from .base import BasePlugin, PluginLoadError
from packaging import version

logger = logging.getLogger(__name__)


class PluginLoader:
    """
    Handles dynamic loading and validation of plugins.

    Features:
    - Dependency installation
    - Version compatibility checking
    - Sandboxed execution (future)
    - Plugin integrity validation

    Example:
        loader = PluginLoader()
        loader.install_dependencies("shodan-plugin")
        plugin_class = loader.load_module("shodan-plugin")
    """

    def __init__(self, vertice_version: str = "1.0.0"):
        """
        Initialize plugin loader.

        Args:
            vertice_version: Current Vértice CLI version
        """
        self.vertice_version = vertice_version
        logger.info(f"PluginLoader initialized (Vértice v{vertice_version})")

    def check_compatibility(
        self,
        plugin_min_version: str,
    ) -> bool:
        """
        Check if plugin is compatible with current Vértice version.

        Args:
            plugin_min_version: Minimum Vértice version required by plugin

        Returns:
            True if compatible

        Raises:
            PluginLoadError: If versions incompatible
        """
        try:
            current = version.parse(self.vertice_version)
            required = version.parse(plugin_min_version)

            if current < required:
                raise PluginLoadError(
                    f"Plugin requires Vértice >= {plugin_min_version}, "
                    f"but current version is {self.vertice_version}"
                )

            logger.debug(
                f"Version check passed: {self.vertice_version} >= {plugin_min_version}"
            )

            return True

        except Exception as e:
            raise PluginLoadError(f"Version compatibility check failed: {e}")

    def install_dependencies(
        self,
        dependencies: List[str],
        dry_run: bool = False
    ) -> bool:
        """
        Install plugin dependencies via pip.

        Args:
            dependencies: List of pip package specs (e.g., ["requests>=2.28.0"])
            dry_run: If True, only check if installed, don't install

        Returns:
            True if all dependencies satisfied

        Example:
            loader.install_dependencies([
                "requests>=2.28.0",
                "shodan==1.28.0",
            ])
        """
        if not dependencies:
            return True

        logger.info(f"Checking dependencies: {dependencies}")

        missing = []

        for dep in dependencies:
            if not self._check_dependency_installed(dep):
                missing.append(dep)

        if not missing:
            logger.info("All dependencies already installed")
            return True

        if dry_run:
            logger.info(f"Missing dependencies (dry-run): {missing}")
            return False

        # Install missing dependencies
        logger.info(f"Installing missing dependencies: {missing}")

        try:
            subprocess.check_call([
                sys.executable,
                "-m",
                "pip",
                "install",
                "--quiet",
                *missing
            ])

            logger.info(f"Dependencies installed successfully")
            return True

        except subprocess.CalledProcessError as e:
            raise PluginLoadError(f"Failed to install dependencies: {e}")

    def _check_dependency_installed(self, package_spec: str) -> bool:
        """
        Check if package is installed.

        Args:
            package_spec: Package specification (e.g., "requests>=2.28.0")

        Returns:
            True if installed
        """
        try:
            # Parse package name (strip version constraints)
            package_name = package_spec.split('>=')[0].split('==')[0].split('<')[0].strip()

            # Try to import
            __import__(package_name)

            return True

        except ImportError:
            return False

    def validate_plugin_structure(self, plugin_path: Path) -> bool:
        """
        Validate plugin directory structure.

        Required structure:
        plugin-name/
        ├── __init__.py
        ├── plugin.py  (contains BasePlugin subclass)
        └── requirements.txt  (optional)

        Args:
            plugin_path: Path to plugin directory

        Returns:
            True if valid

        Raises:
            PluginLoadError: If invalid structure
        """
        if not plugin_path.is_dir():
            raise PluginLoadError(f"Plugin path is not a directory: {plugin_path}")

        init_file = plugin_path / "__init__.py"
        if not init_file.exists():
            raise PluginLoadError(
                f"Plugin missing __init__.py: {plugin_path}"
            )

        logger.debug(f"Plugin structure validated: {plugin_path}")

        return True

    def calculate_integrity_hash(self, plugin_path: Path) -> str:
        """
        Calculate integrity hash for plugin.

        Used for:
        - Detecting tampering
        - Versioning
        - Marketplace verification

        Args:
            plugin_path: Path to plugin directory

        Returns:
            SHA256 hash
        """
        import hashlib

        hash_obj = hashlib.sha256()

        # Hash all .py files in order
        for py_file in sorted(plugin_path.rglob("*.py")):
            with open(py_file, 'rb') as f:
                hash_obj.update(f.read())

        return hash_obj.hexdigest()

    def load_from_file(
        self,
        file_path: Path,
        config: Optional[Dict[str, Any]] = None
    ) -> BasePlugin:
        """
        Load plugin from file path.

        Args:
            file_path: Path to plugin .py file or package directory
            config: Plugin configuration

        Returns:
            Loaded plugin instance
        """
        if not file_path.exists():
            raise PluginLoadError(f"Plugin file not found: {file_path}")

        # Add plugin directory to sys.path temporarily
        plugin_dir = file_path.parent if file_path.is_file() else file_path
        old_path = sys.path.copy()

        try:
            if str(plugin_dir) not in sys.path:
                sys.path.insert(0, str(plugin_dir))

            # Import module
            module_name = file_path.stem if file_path.is_file() else file_path.name

            # Dynamic import
            import importlib.util
            spec = importlib.util.spec_from_file_location(module_name, file_path)

            if not spec or not spec.loader:
                raise PluginLoadError(f"Could not load spec for {file_path}")

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find BasePlugin subclass
            plugin_class = None

            for attr_name in dir(module):
                attr = getattr(module, attr_name)

                if (isinstance(attr, type) and
                    issubclass(attr, BasePlugin) and
                    attr is not BasePlugin):
                    plugin_class = attr
                    break

            if not plugin_class:
                raise PluginLoadError(f"No BasePlugin subclass found in {file_path}")

            # Instantiate and initialize
            plugin_instance = plugin_class()
            plugin_instance.initialize(config or {})

            logger.info(f"Plugin loaded from file: {file_path}")

            return plugin_instance

        finally:
            # Restore sys.path
            sys.path = old_path
