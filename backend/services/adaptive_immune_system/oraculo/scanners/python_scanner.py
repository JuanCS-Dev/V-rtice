"""
Python Dependency Scanner.

Discovers Python dependencies using multiple strategies:
- pipdeptree (hierarchical dependency tree)
- requirements.txt parsing
- pyproject.toml parsing
- poetry.lock parsing
"""

import json
import logging
import subprocess
import tomllib
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PythonPackage(BaseModel):
    """Python package model."""

    name: str
    version: str
    is_direct: bool = True  # Direct vs transitive dependency
    parent_packages: List[str] = Field(default_factory=list)
    location: Optional[str] = None


class PythonScanner:
    """
    Scanner for Python dependencies.

    Strategies:
    1. pipdeptree: Most complete dependency tree
    2. requirements.txt: Simple direct dependencies
    3. pyproject.toml: Modern Python packaging
    4. poetry.lock: Poetry-managed dependencies
    """

    def __init__(self, project_path: Path):
        """
        Initialize Python scanner.

        Args:
            project_path: Path to Python project root
        """
        self.project_path = Path(project_path)
        logger.info(f"PythonScanner initialized for: {self.project_path}")

    def scan(self) -> List[PythonPackage]:
        """
        Scan Python dependencies using all available strategies.

        Returns:
            List of PythonPackage instances

        Raises:
            RuntimeError: If all scanning strategies fail
        """
        packages: Dict[str, PythonPackage] = {}

        # Strategy 1: pipdeptree (most complete)
        try:
            pipdeptree_packages = self._scan_pipdeptree()
            for pkg in pipdeptree_packages:
                key = f"{pkg.name}@{pkg.version}"
                if key not in packages:
                    packages[key] = pkg
                else:
                    # Merge dependency information
                    packages[key].parent_packages.extend(pkg.parent_packages)
                    packages[key].is_direct = packages[key].is_direct or pkg.is_direct

            logger.info(f"pipdeptree: Found {len(pipdeptree_packages)} packages")
        except Exception as e:
            logger.warning(f"pipdeptree scan failed: {e}")

        # Strategy 2: requirements.txt
        try:
            requirements_packages = self._scan_requirements_txt()
            for pkg in requirements_packages:
                key = f"{pkg.name}@{pkg.version}"
                if key not in packages:
                    packages[key] = pkg

            logger.info(f"requirements.txt: Found {len(requirements_packages)} packages")
        except Exception as e:
            logger.debug(f"requirements.txt scan failed: {e}")

        # Strategy 3: pyproject.toml
        try:
            pyproject_packages = self._scan_pyproject_toml()
            for pkg in pyproject_packages:
                key = f"{pkg.name}@{pkg.version}"
                if key not in packages:
                    packages[key] = pkg

            logger.info(f"pyproject.toml: Found {len(pyproject_packages)} packages")
        except Exception as e:
            logger.debug(f"pyproject.toml scan failed: {e}")

        # Strategy 4: poetry.lock
        try:
            poetry_packages = self._scan_poetry_lock()
            for pkg in poetry_packages:
                key = f"{pkg.name}@{pkg.version}"
                if key not in packages:
                    packages[key] = pkg

            logger.info(f"poetry.lock: Found {len(poetry_packages)} packages")
        except Exception as e:
            logger.debug(f"poetry.lock scan failed: {e}")

        if not packages:
            raise RuntimeError("All Python scanning strategies failed. No dependencies found.")

        result = list(packages.values())
        logger.info(f"✅ Python scan complete: {len(result)} unique packages discovered")
        return result

    def _scan_pipdeptree(self) -> List[PythonPackage]:
        """
        Scan using pipdeptree for hierarchical dependency tree.

        Returns:
            List of PythonPackage instances

        Raises:
            RuntimeError: If pipdeptree is not available or fails
        """
        try:
            # Run pipdeptree with JSON output
            result = subprocess.run(
                ["pipdeptree", "--json", "--warn", "silence"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                raise RuntimeError(f"pipdeptree failed: {result.stderr}")

            tree = json.loads(result.stdout)

            packages = []
            for node in tree:
                package = node.get("package", {})
                dependencies = node.get("dependencies", [])

                # Add root package (direct dependency)
                pkg_name = package.get("package_name", "").lower()
                pkg_version = package.get("installed_version", "unknown")

                if pkg_name:
                    packages.append(
                        PythonPackage(
                            name=pkg_name,
                            version=pkg_version,
                            is_direct=True,
                            parent_packages=[],
                            location=package.get("location"),
                        )
                    )

                # Add transitive dependencies
                for dep in dependencies:
                    dep_name = dep.get("package_name", "").lower()
                    dep_version = dep.get("installed_version", "unknown")

                    if dep_name:
                        packages.append(
                            PythonPackage(
                                name=dep_name,
                                version=dep_version,
                                is_direct=False,
                                parent_packages=[pkg_name],
                            )
                        )

            return packages

        except FileNotFoundError:
            raise RuntimeError(
                "pipdeptree not found. Install with: pip install pipdeptree"
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("pipdeptree timed out after 60s")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse pipdeptree JSON: {e}")

    def _scan_requirements_txt(self) -> List[PythonPackage]:
        """
        Scan requirements.txt for direct dependencies.

        Returns:
            List of PythonPackage instances

        Raises:
            FileNotFoundError: If requirements.txt doesn't exist
        """
        requirements_files = [
            self.project_path / "requirements.txt",
            self.project_path / "requirements" / "base.txt",
            self.project_path / "requirements" / "production.txt",
        ]

        packages = []
        found_any = False

        for req_file in requirements_files:
            if not req_file.exists():
                continue

            found_any = True

            with open(req_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()

                    # Skip comments and empty lines
                    if not line or line.startswith("#") or line.startswith("-"):
                        continue

                    # Parse package name and version
                    name, version = self._parse_requirement_line(line)

                    if name:
                        packages.append(
                            PythonPackage(
                                name=name.lower(),
                                version=version,
                                is_direct=True,
                                parent_packages=[],
                            )
                        )

        if not found_any:
            raise FileNotFoundError("No requirements.txt files found")

        return packages

    def _scan_pyproject_toml(self) -> List[PythonPackage]:
        """
        Scan pyproject.toml for dependencies (PEP 518/621).

        Returns:
            List of PythonPackage instances

        Raises:
            FileNotFoundError: If pyproject.toml doesn't exist
        """
        pyproject_file = self.project_path / "pyproject.toml"

        if not pyproject_file.exists():
            raise FileNotFoundError("pyproject.toml not found")

        with open(pyproject_file, "rb") as f:
            data = tomllib.load(f)

        packages = []

        # PEP 621 dependencies
        if "project" in data and "dependencies" in data["project"]:
            for dep in data["project"]["dependencies"]:
                name, version = self._parse_requirement_line(dep)
                if name:
                    packages.append(
                        PythonPackage(
                            name=name.lower(),
                            version=version,
                            is_direct=True,
                            parent_packages=[],
                        )
                    )

        # Poetry dependencies
        if "tool" in data and "poetry" in data["tool"]:
            poetry_deps = data["tool"]["poetry"].get("dependencies", {})
            for name, spec in poetry_deps.items():
                if name == "python":  # Skip Python version spec
                    continue

                version = self._parse_poetry_version(spec)
                packages.append(
                    PythonPackage(
                        name=name.lower(),
                        version=version,
                        is_direct=True,
                        parent_packages=[],
                    )
                )

        return packages

    def _scan_poetry_lock(self) -> List[PythonPackage]:
        """
        Scan poetry.lock for locked dependencies.

        Returns:
            List of PythonPackage instances

        Raises:
            FileNotFoundError: If poetry.lock doesn't exist
        """
        poetry_lock_file = self.project_path / "poetry.lock"

        if not poetry_lock_file.exists():
            raise FileNotFoundError("poetry.lock not found")

        with open(poetry_lock_file, "rb") as f:
            data = tomllib.load(f)

        packages = []

        if "package" in data:
            for pkg in data["package"]:
                name = pkg.get("name", "").lower()
                version = pkg.get("version", "unknown")
                category = pkg.get("category", "main")

                if name:
                    packages.append(
                        PythonPackage(
                            name=name,
                            version=version,
                            is_direct=(category == "main"),
                            parent_packages=[],
                        )
                    )

        return packages

    def _parse_requirement_line(self, line: str) -> Tuple[str, str]:
        """
        Parse requirement line into package name and version.

        Supports formats:
        - package==1.0.0
        - package>=1.0.0,<2.0.0
        - package~=1.0.0
        - package[extra]==1.0.0
        - git+https://...

        Args:
            line: Requirement line

        Returns:
            Tuple of (name, version_spec)
        """
        # Skip git URLs and other special cases
        if line.startswith(("git+", "http://", "https://", "file://")):
            return "", "unknown"

        # Remove extras: package[extra] -> package
        if "[" in line:
            line = line.split("[")[0]

        # Split on version specifiers
        for separator in ["==", ">=", "<=", "~=", ">", "<", "!="]:
            if separator in line:
                parts = line.split(separator, 1)
                name = parts[0].strip()
                version = parts[1].strip().split(",")[0].strip()  # Take first constraint
                return name, version

        # No version specified
        return line.strip(), "latest"

    def _parse_poetry_version(self, spec) -> str:
        """
        Parse Poetry version spec.

        Args:
            spec: Version specification (string or dict)

        Returns:
            Version string
        """
        if isinstance(spec, str):
            # Remove caret/tilde constraints
            version = spec.replace("^", "").replace("~", "").strip()
            return version if version else "latest"

        if isinstance(spec, dict):
            return spec.get("version", "latest").replace("^", "").replace("~", "").strip()

        return "latest"

    def get_installed_packages(self) -> Dict[str, str]:
        """
        Get all installed packages in current environment.

        Returns:
            Dictionary mapping package names to versions

        Raises:
            RuntimeError: If pip list fails
        """
        try:
            result = subprocess.run(
                ["pip", "list", "--format=json"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                raise RuntimeError(f"pip list failed: {result.stderr}")

            packages = json.loads(result.stdout)

            return {
                pkg["name"].lower(): pkg["version"]
                for pkg in packages
            }

        except subprocess.TimeoutExpired:
            raise RuntimeError("pip list timed out after 30s")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse pip list JSON: {e}")
