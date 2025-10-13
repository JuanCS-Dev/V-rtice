"""
Go Module Scanner.

Discovers Go dependencies using multiple strategies:
- go list -m all (all modules with versions)
- go.mod parsing (direct dependencies)
- go.sum parsing (checksums for all dependencies)
- go mod graph (dependency graph)
"""

import json
import logging
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class GoPackage(BaseModel):
    """Go module/package model."""

    name: str  # Module path (e.g., "github.com/gin-gonic/gin")
    version: str  # Semantic version or pseudo-version
    is_direct: bool = True  # Direct vs indirect dependency
    parent_packages: List[str] = Field(default_factory=list)
    replace: Optional[str] = None  # Replacement path if replaced


class GoScanner:
    """
    Scanner for Go modules.

    Strategies:
    1. go list -m all: Most complete module list with versions
    2. go.mod parsing: Direct and indirect dependencies
    3. go.sum parsing: All dependencies with checksums
    4. go mod graph: Dependency relationships
    """

    def __init__(self, project_path: Path):
        """
        Initialize Go scanner.

        Args:
            project_path: Path to Go project root (containing go.mod)
        """
        self.project_path = Path(project_path)
        logger.info(f"GoScanner initialized for: {self.project_path}")

    def scan(self) -> List[GoPackage]:
        """
        Scan Go dependencies using all available strategies.

        Returns:
            List of GoPackage instances

        Raises:
            RuntimeError: If all scanning strategies fail
        """
        packages: Dict[str, GoPackage] = {}

        # Strategy 1: go list -m all (most complete)
        try:
            go_list_packages = self._scan_go_list()
            for pkg in go_list_packages:
                key = f"{pkg.name}@{pkg.version}"
                if key not in packages:
                    packages[key] = pkg

            logger.info(f"go list: Found {len(go_list_packages)} packages")
        except Exception as e:
            logger.warning(f"go list scan failed: {e}")

        # Strategy 2: go.mod parsing
        try:
            go_mod_packages = self._scan_go_mod()
            for pkg in go_mod_packages:
                key = f"{pkg.name}@{pkg.version}"
                if key not in packages:
                    packages[key] = pkg
                else:
                    # Update is_direct flag if go.mod says it's direct
                    if pkg.is_direct:
                        packages[key].is_direct = True

            logger.info(f"go.mod: Found {len(go_mod_packages)} packages")
        except Exception as e:
            logger.debug(f"go.mod scan failed: {e}")

        # Strategy 3: go mod graph (dependency relationships)
        try:
            graph_packages = self._scan_go_mod_graph()
            for pkg in graph_packages:
                key = f"{pkg.name}@{pkg.version}"
                if key not in packages:
                    packages[key] = pkg
                else:
                    # Merge parent information
                    packages[key].parent_packages.extend(pkg.parent_packages)

            logger.info(f"go mod graph: Found {len(graph_packages)} packages")
        except Exception as e:
            logger.debug(f"go mod graph scan failed: {e}")

        if not packages:
            raise RuntimeError("All Go scanning strategies failed. No dependencies found.")

        result = list(packages.values())
        logger.info(f"✅ Go scan complete: {len(result)} unique packages discovered")
        return result

    def _scan_go_list(self) -> List[GoPackage]:
        """
        Scan using go list -m all for complete module list.

        Returns:
            List of GoPackage instances

        Raises:
            RuntimeError: If go is not available or fails
        """
        try:
            result = subprocess.run(
                ["go", "list", "-m", "-json", "all"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                raise RuntimeError(f"go list failed: {result.stderr}")

            packages = []

            # go list -m -json outputs multiple JSON objects (not an array)
            json_objects = result.stdout.strip().split("\n}\n")

            for json_str in json_objects:
                if not json_str.strip():
                    continue

                # Add closing brace if missing
                if not json_str.strip().endswith("}"):
                    json_str += "}"

                try:
                    module = json.loads(json_str)

                    path = module.get("Path", "")
                    version = module.get("Version", "")
                    replace = module.get("Replace", {})
                    indirect = module.get("Indirect", False)

                    # Skip main module
                    if module.get("Main", False):
                        continue

                    if path:
                        packages.append(
                            GoPackage(
                                name=path,
                                version=version if version else "unknown",
                                is_direct=not indirect,
                                parent_packages=[],
                                replace=replace.get("Path") if replace else None,
                            )
                        )

                except json.JSONDecodeError as e:
                    logger.debug(f"Failed to parse go list JSON object: {e}")
                    continue

            return packages

        except FileNotFoundError:
            raise RuntimeError("go not found. Install Go from https://golang.org/")
        except subprocess.TimeoutExpired:
            raise RuntimeError("go list timed out after 60s")

    def _scan_go_mod(self) -> List[GoPackage]:
        """
        Scan go.mod for direct and indirect dependencies.

        Returns:
            List of GoPackage instances

        Raises:
            FileNotFoundError: If go.mod doesn't exist
        """
        go_mod_file = self.project_path / "go.mod"

        if not go_mod_file.exists():
            raise FileNotFoundError("go.mod not found")

        with open(go_mod_file, "r", encoding="utf-8") as f:
            content = f.read()

        packages = []

        # Parse require block
        # Format: require (
        #   github.com/gin-gonic/gin v1.9.0
        #   github.com/other/package v2.0.0 // indirect
        # )
        in_require_block = False
        require_pattern = re.compile(r"^\s*([^\s]+)\s+([^\s]+)(\s+//\s*indirect)?")

        for line in content.splitlines():
            line = line.strip()

            # Start of require block
            if line.startswith("require ("):
                in_require_block = True
                continue

            # End of require block
            if in_require_block and line == ")":
                in_require_block = False
                continue

            # Single-line require
            if line.startswith("require ") and "(" not in line:
                match = require_pattern.match(line.replace("require ", ""))
                if match:
                    name = match.group(1)
                    version = match.group(2)
                    is_indirect = match.group(3) is not None

                    packages.append(
                        GoPackage(
                            name=name,
                            version=version,
                            is_direct=not is_indirect,
                            parent_packages=[],
                        )
                    )

            # Inside require block
            if in_require_block:
                match = require_pattern.match(line)
                if match:
                    name = match.group(1)
                    version = match.group(2)
                    is_indirect = match.group(3) is not None

                    packages.append(
                        GoPackage(
                            name=name,
                            version=version,
                            is_direct=not is_indirect,
                            parent_packages=[],
                        )
                    )

        # Parse replace directives
        # Format: replace github.com/old/package => github.com/new/package v1.0.0
        replace_pattern = re.compile(r"replace\s+([^\s]+)\s+.*?=>\s+([^\s]+)")

        replacements = {}
        for match in replace_pattern.finditer(content):
            old_path = match.group(1)
            new_path = match.group(2)
            replacements[old_path] = new_path

        # Apply replacements
        for pkg in packages:
            if pkg.name in replacements:
                pkg.replace = replacements[pkg.name]

        return packages

    def _scan_go_mod_graph(self) -> List[GoPackage]:
        """
        Scan using go mod graph for dependency relationships.

        Returns:
            List of GoPackage instances with parent information

        Raises:
            RuntimeError: If go mod graph fails
        """
        try:
            result = subprocess.run(
                ["go", "mod", "graph"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                raise RuntimeError(f"go mod graph failed: {result.stderr}")

            packages: Dict[str, GoPackage] = {}

            # Parse graph output
            # Format: parent@version child@version
            for line in result.stdout.splitlines():
                parts = line.strip().split()
                if len(parts) != 2:
                    continue

                parent_full = parts[0]
                child_full = parts[1]

                # Parse child
                child_name, child_version = self._parse_module_version(child_full)

                if not child_name:
                    continue

                # Parse parent
                parent_name, parent_version = self._parse_module_version(parent_full)

                key = f"{child_name}@{child_version}"

                if key not in packages:
                    packages[key] = GoPackage(
                        name=child_name,
                        version=child_version,
                        is_direct=False,  # Will be updated by go.mod parsing
                        parent_packages=[parent_name] if parent_name else [],
                    )
                else:
                    # Add parent relationship
                    if parent_name and parent_name not in packages[key].parent_packages:
                        packages[key].parent_packages.append(parent_name)

            return list(packages.values())

        except subprocess.TimeoutExpired:
            raise RuntimeError("go mod graph timed out after 60s")

    def _parse_module_version(self, module_full: str) -> Tuple[str, str]:
        """
        Parse module@version string into name and version.

        Args:
            module_full: Full module string (e.g., "github.com/gin-gonic/gin@v1.9.0")

        Returns:
            Tuple of (name, version)
        """
        if "@" not in module_full:
            return module_full, "unknown"

        parts = module_full.rsplit("@", 1)
        name = parts[0]
        version = parts[1] if len(parts) > 1 else "unknown"

        return name, version

    def get_module_info(self) -> dict:
        """
        Get Go module information from go.mod.

        Returns:
            Dictionary with module name, Go version, etc.

        Raises:
            FileNotFoundError: If go.mod doesn't exist
        """
        go_mod_file = self.project_path / "go.mod"

        if not go_mod_file.exists():
            raise FileNotFoundError("go.mod not found")

        with open(go_mod_file, "r", encoding="utf-8") as f:
            content = f.read()

        info = {}

        # Parse module name
        module_match = re.search(r"^module\s+([^\s]+)", content, re.MULTILINE)
        if module_match:
            info["module"] = module_match.group(1)

        # Parse Go version
        go_match = re.search(r"^go\s+([^\s]+)", content, re.MULTILINE)
        if go_match:
            info["go_version"] = go_match.group(1)

        return info

    def get_module_dependencies_tree(self) -> dict:
        """
        Get hierarchical dependency tree.

        Returns:
            Dictionary representing dependency tree

        Raises:
            RuntimeError: If go mod graph fails
        """
        try:
            result = subprocess.run(
                ["go", "mod", "graph"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                raise RuntimeError(f"go mod graph failed: {result.stderr}")

            tree: Dict[str, Set[str]] = {}

            for line in result.stdout.splitlines():
                parts = line.strip().split()
                if len(parts) != 2:
                    continue

                parent = parts[0]
                child = parts[1]

                if parent not in tree:
                    tree[parent] = set()

                tree[parent].add(child)

            # Convert sets to lists for JSON serialization
            return {k: list(v) for k, v in tree.items()}

        except subprocess.TimeoutExpired:
            raise RuntimeError("go mod graph timed out after 60s")

    def verify_checksums(self) -> bool:
        """
        Verify go.sum checksums.

        Returns:
            True if checksums are valid

        Raises:
            RuntimeError: If go mod verify fails
        """
        try:
            result = subprocess.run(
                ["go", "mod", "verify"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=60,
            )

            return result.returncode == 0

        except subprocess.TimeoutExpired:
            raise RuntimeError("go mod verify timed out after 60s")
