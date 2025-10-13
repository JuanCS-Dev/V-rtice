"""
JavaScript/Node.js Dependency Scanner.

Discovers npm/yarn dependencies using multiple strategies:
- npm list --json (hierarchical dependency tree)
- package.json parsing
- package-lock.json parsing
- yarn.lock parsing
"""

import json
import logging
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class JavaScriptPackage(BaseModel):
    """JavaScript/npm package model."""

    name: str
    version: str
    is_direct: bool = True  # Direct vs transitive dependency
    parent_packages: List[str] = Field(default_factory=list)
    is_dev: bool = False  # Development dependency


class JavaScriptScanner:
    """
    Scanner for JavaScript/Node.js dependencies.

    Strategies:
    1. npm list --json: Most complete dependency tree
    2. package.json: Direct dependencies
    3. package-lock.json: Locked dependencies with full tree
    4. yarn.lock: Yarn-managed dependencies
    """

    def __init__(self, project_path: Path):
        """
        Initialize JavaScript scanner.

        Args:
            project_path: Path to JavaScript project root
        """
        self.project_path = Path(project_path)
        logger.info(f"JavaScriptScanner initialized for: {self.project_path}")

    def scan(self) -> List[JavaScriptPackage]:
        """
        Scan JavaScript dependencies using all available strategies.

        Returns:
            List of JavaScriptPackage instances

        Raises:
            RuntimeError: If all scanning strategies fail
        """
        packages: Dict[str, JavaScriptPackage] = {}

        # Strategy 1: npm list --json (most complete)
        try:
            npm_packages = self._scan_npm_list()
            for pkg in npm_packages:
                key = f"{pkg.name}@{pkg.version}"
                if key not in packages:
                    packages[key] = pkg
                else:
                    # Merge dependency information
                    packages[key].parent_packages.extend(pkg.parent_packages)
                    packages[key].is_direct = packages[key].is_direct or pkg.is_direct

            logger.info(f"npm list: Found {len(npm_packages)} packages")
        except Exception as e:
            logger.warning(f"npm list scan failed: {e}")

        # Strategy 2: package.json
        try:
            package_json_packages = self._scan_package_json()
            for pkg in package_json_packages:
                key = f"{pkg.name}@{pkg.version}"
                if key not in packages:
                    packages[key] = pkg

            logger.info(f"package.json: Found {len(package_json_packages)} packages")
        except Exception as e:
            logger.debug(f"package.json scan failed: {e}")

        # Strategy 3: package-lock.json
        try:
            package_lock_packages = self._scan_package_lock()
            for pkg in package_lock_packages:
                key = f"{pkg.name}@{pkg.version}"
                if key not in packages:
                    packages[key] = pkg

            logger.info(f"package-lock.json: Found {len(package_lock_packages)} packages")
        except Exception as e:
            logger.debug(f"package-lock.json scan failed: {e}")

        # Strategy 4: yarn.lock
        try:
            yarn_packages = self._scan_yarn_lock()
            for pkg in yarn_packages:
                key = f"{pkg.name}@{pkg.version}"
                if key not in packages:
                    packages[key] = pkg

            logger.info(f"yarn.lock: Found {len(yarn_packages)} packages")
        except Exception as e:
            logger.debug(f"yarn.lock scan failed: {e}")

        if not packages:
            raise RuntimeError("All JavaScript scanning strategies failed. No dependencies found.")

        result = list(packages.values())
        logger.info(f"✅ JavaScript scan complete: {len(result)} unique packages discovered")
        return result

    def _scan_npm_list(self) -> List[JavaScriptPackage]:
        """
        Scan using npm list --json for hierarchical dependency tree.

        Returns:
            List of JavaScriptPackage instances

        Raises:
            RuntimeError: If npm is not available or fails
        """
        try:
            # Run npm list with JSON output
            # Note: npm list exits with code 1 if there are issues, but still outputs JSON
            result = subprocess.run(
                ["npm", "list", "--json", "--all"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=120,
            )

            # npm list returns non-zero on warnings, but still produces valid JSON
            if not result.stdout:
                raise RuntimeError(f"npm list produced no output: {result.stderr}")

            tree = json.loads(result.stdout)

            packages = []
            self._extract_npm_packages(
                tree.get("dependencies", {}),
                packages,
                is_direct=True,
                parent_name=None,
            )

            return packages

        except FileNotFoundError:
            raise RuntimeError("npm not found. Install Node.js from https://nodejs.org/")
        except subprocess.TimeoutExpired:
            raise RuntimeError("npm list timed out after 120s")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse npm list JSON: {e}")

    def _extract_npm_packages(
        self,
        deps: dict,
        packages: List[JavaScriptPackage],
        is_direct: bool,
        parent_name: Optional[str],
    ) -> None:
        """
        Recursively extract packages from npm list tree.

        Args:
            deps: Dependencies dictionary from npm list
            packages: List to append packages to
            is_direct: Whether these are direct dependencies
            parent_name: Name of parent package
        """
        for name, info in deps.items():
            version = info.get("version", "unknown")

            parent_packages = [parent_name] if parent_name else []

            packages.append(
                JavaScriptPackage(
                    name=name,
                    version=version,
                    is_direct=is_direct,
                    parent_packages=parent_packages,
                    is_dev=False,
                )
            )

            # Recursively process nested dependencies
            if "dependencies" in info:
                self._extract_npm_packages(
                    info["dependencies"],
                    packages,
                    is_direct=False,
                    parent_name=name,
                )

    def _scan_package_json(self) -> List[JavaScriptPackage]:
        """
        Scan package.json for direct dependencies.

        Returns:
            List of JavaScriptPackage instances

        Raises:
            FileNotFoundError: If package.json doesn't exist
        """
        package_json_file = self.project_path / "package.json"

        if not package_json_file.exists():
            raise FileNotFoundError("package.json not found")

        with open(package_json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        packages = []

        # Production dependencies
        if "dependencies" in data:
            for name, version_spec in data["dependencies"].items():
                version = self._parse_npm_version(version_spec)
                packages.append(
                    JavaScriptPackage(
                        name=name,
                        version=version,
                        is_direct=True,
                        parent_packages=[],
                        is_dev=False,
                    )
                )

        # Development dependencies
        if "devDependencies" in data:
            for name, version_spec in data["devDependencies"].items():
                version = self._parse_npm_version(version_spec)
                packages.append(
                    JavaScriptPackage(
                        name=name,
                        version=version,
                        is_direct=True,
                        parent_packages=[],
                        is_dev=True,
                    )
                )

        return packages

    def _scan_package_lock(self) -> List[JavaScriptPackage]:
        """
        Scan package-lock.json for locked dependencies.

        Returns:
            List of JavaScriptPackage instances

        Raises:
            FileNotFoundError: If package-lock.json doesn't exist
        """
        package_lock_file = self.project_path / "package-lock.json"

        if not package_lock_file.exists():
            raise FileNotFoundError("package-lock.json not found")

        with open(package_lock_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        packages = []

        # package-lock.json v2+ format (npm 7+)
        if "packages" in data:
            for package_path, info in data["packages"].items():
                # Skip root package
                if package_path == "":
                    continue

                # Extract package name from path (node_modules/...)
                name = package_path.replace("node_modules/", "")
                version = info.get("version", "unknown")
                is_dev = info.get("dev", False)

                packages.append(
                    JavaScriptPackage(
                        name=name,
                        version=version,
                        is_direct=("node_modules/" not in package_path or package_path.count("/") == 1),
                        parent_packages=[],
                        is_dev=is_dev,
                    )
                )

        # package-lock.json v1 format (npm 6)
        elif "dependencies" in data:
            self._extract_package_lock_v1_deps(
                data["dependencies"],
                packages,
                is_direct=True,
            )

        return packages

    def _extract_package_lock_v1_deps(
        self,
        deps: dict,
        packages: List[JavaScriptPackage],
        is_direct: bool,
    ) -> None:
        """
        Recursively extract packages from package-lock.json v1.

        Args:
            deps: Dependencies dictionary
            packages: List to append packages to
            is_direct: Whether these are direct dependencies
        """
        for name, info in deps.items():
            version = info.get("version", "unknown")
            is_dev = info.get("dev", False)

            packages.append(
                JavaScriptPackage(
                    name=name,
                    version=version,
                    is_direct=is_direct,
                    parent_packages=[],
                    is_dev=is_dev,
                )
            )

            # Recursively process nested dependencies
            if "dependencies" in info:
                self._extract_package_lock_v1_deps(
                    info["dependencies"],
                    packages,
                    is_direct=False,
                )

    def _scan_yarn_lock(self) -> List[JavaScriptPackage]:
        """
        Scan yarn.lock for Yarn-managed dependencies.

        Returns:
            List of JavaScriptPackage instances

        Raises:
            FileNotFoundError: If yarn.lock doesn't exist
        """
        yarn_lock_file = self.project_path / "yarn.lock"

        if not yarn_lock_file.exists():
            raise FileNotFoundError("yarn.lock not found")

        with open(yarn_lock_file, "r", encoding="utf-8") as f:
            content = f.read()

        packages = []

        # Parse yarn.lock format (simplified parser)
        # Format: package-name@version:\n  version "x.y.z"
        pattern = re.compile(r'^"?([^@\s]+)@[^:]+:\s*\n\s+version\s+"([^"]+)"', re.MULTILINE)

        for match in pattern.finditer(content):
            name = match.group(1)
            version = match.group(2)

            packages.append(
                JavaScriptPackage(
                    name=name,
                    version=version,
                    is_direct=False,  # Can't determine from yarn.lock alone
                    parent_packages=[],
                    is_dev=False,
                )
            )

        # Deduplicate by name@version
        seen = set()
        unique_packages = []
        for pkg in packages:
            key = f"{pkg.name}@{pkg.version}"
            if key not in seen:
                seen.add(key)
                unique_packages.append(pkg)

        return unique_packages

    def _parse_npm_version(self, version_spec: str) -> str:
        """
        Parse npm version specifier into concrete version.

        Supports formats:
        - 1.0.0
        - ^1.0.0
        - ~1.0.0
        - >=1.0.0 <2.0.0
        - latest
        - git+https://...

        Args:
            version_spec: npm version specifier

        Returns:
            Parsed version string
        """
        # Git URLs
        if version_spec.startswith(("git+", "http://", "https://", "git://")):
            return "git"

        # File paths
        if version_spec.startswith(("file:", "./")):
            return "local"

        # Remove npm semver prefixes
        version = version_spec.replace("^", "").replace("~", "").replace(">=", "").replace("<=", "").strip()

        # Take first version in range
        if " " in version:
            version = version.split()[0]

        return version if version else "latest"

    def get_node_modules_packages(self) -> Dict[str, str]:
        """
        Get all packages installed in node_modules.

        Returns:
            Dictionary mapping package names to versions

        Raises:
            RuntimeError: If node_modules doesn't exist or is empty
        """
        node_modules = self.project_path / "node_modules"

        if not node_modules.exists():
            raise RuntimeError("node_modules directory not found")

        packages = {}

        for package_dir in node_modules.iterdir():
            # Skip hidden files and non-directories
            if not package_dir.is_dir() or package_dir.name.startswith("."):
                continue

            # Handle scoped packages (@scope/package)
            if package_dir.name.startswith("@"):
                for scoped_package in package_dir.iterdir():
                    if scoped_package.is_dir():
                        package_json = scoped_package / "package.json"
                        if package_json.exists():
                            try:
                                with open(package_json, "r", encoding="utf-8") as f:
                                    data = json.load(f)
                                    name = data.get("name", f"{package_dir.name}/{scoped_package.name}")
                                    version = data.get("version", "unknown")
                                    packages[name] = version
                            except Exception as e:
                                logger.debug(f"Failed to parse {package_json}: {e}")
            else:
                # Regular package
                package_json = package_dir / "package.json"
                if package_json.exists():
                    try:
                        with open(package_json, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            name = data.get("name", package_dir.name)
                            version = data.get("version", "unknown")
                            packages[name] = version
                    except Exception as e:
                        logger.debug(f"Failed to parse {package_json}: {e}")

        return packages
