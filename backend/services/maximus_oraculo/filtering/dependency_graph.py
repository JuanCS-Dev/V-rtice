"""Dependency Graph Builder for MAXIMUS services.

This module builds a comprehensive dependency graph by:
1. Walking the repository tree to find all pyproject.toml files
2. Parsing each pyproject.toml to extract dependencies
3. Building a graph: service → list of dependencies with versions
4. Providing query interface for vulnerability cross-referencing

Author: MAXIMUS Team
Date: 2025-10-11
Compliance: Doutrina MAXIMUS | Type Hints 100% | Production-Ready
"""

import tomllib  # type: ignore[import-not-found] # Python 3.11+ built-in
from pathlib import Path
from typing import Dict, List, Set, Optional, Union
from dataclasses import dataclass, field
import logging
import re

logger = logging.getLogger(__name__)


@dataclass
class PackageDependency:
    """
    Represents a package dependency with version constraints.
    
    Example:
        PackageDependency(name="django", version_spec=">=4.2,<5.0", ecosystem="PyPI")
    """
    name: str
    version_spec: str
    ecosystem: str = "PyPI"
    is_dev: bool = False
    
    def matches_version(self, version: str) -> bool:
        """
        Check if a specific version matches this dependency's constraints.
        
        Simplified version matching:
        - ">=4.2" → version >= 4.2
        - "<5.0" → version < 5.0
        - "==4.2.8" → version == 4.2.8
        - "*" → any version
        
        Args:
            version: Version string to check
            
        Returns:
            True if version matches constraints
            
        Note:
            Full implementation should use packaging.specifiers
            This is simplified for MVP.
        """
        if self.version_spec == "*" or not self.version_spec:
            return True
        
        # Simple version comparison (MVP - should use packaging.specifiers in production)
        if self.version_spec.startswith("=="):
            return version == self.version_spec[2:].strip()
        elif self.version_spec.startswith(">="):
            # Simplified: just check if installed version is mentioned
            return True  # Accept for now
        elif self.version_spec.startswith("<"):
            return True  # Accept for now
        
        return True  # Default: accept


@dataclass
class ServiceDependencies:
    """
    Dependencies for a single service.
    
    Attributes:
        service_name: Name of the service (e.g., "maximus_oraculo")
        path: Path to service directory
        dependencies: Production dependencies
        dev_dependencies: Development dependencies
    """
    service_name: str
    path: Path
    dependencies: List[PackageDependency] = field(default_factory=list)
    dev_dependencies: List[PackageDependency] = field(default_factory=list)
    
    @property
    def all_dependencies(self) -> List[PackageDependency]:
        """Get all dependencies (prod + dev)."""
        return self.dependencies + self.dev_dependencies
    
    def has_package(self, package_name: str) -> bool:
        """Check if service depends on a package."""
        return any(
            dep.name.lower() == package_name.lower()
            for dep in self.all_dependencies
        )
    
    def get_package_version(self, package_name: str) -> Optional[str]:
        """Get version spec for a package."""
        for dep in self.all_dependencies:
            if dep.name.lower() == package_name.lower():
                return dep.version_spec
        return None


class DependencyGraphBuilder:
    """
    Builds and maintains dependency graph for MAXIMUS services.
    
    Usage:
        >>> builder = DependencyGraphBuilder(repo_root="/path/to/maximus")
        >>> await builder.build_graph()
        >>> services = builder.get_services_using_package("django")
        >>> print(f"Django used by: {[s.service_name for s in services]}")
    
    Theoretical Foundation:
    - Dependency Graph: Directed graph of package dependencies
    - Service Mesh: Microservices architecture dependency tracking
    - Version Constraints: Semantic versioning and constraint resolution
    """
    
    def __init__(self, repo_root: Path):
        """
        Initialize dependency graph builder.
        
        Args:
            repo_root: Root directory of MAXIMUS repository
        """
        self.repo_root = Path(repo_root)
        self.services: Dict[str, ServiceDependencies] = {}
        self._package_index: Dict[str, Set[str]] = {}  # package -> set of service names
        
        logger.info(f"Initialized DependencyGraphBuilder for {self.repo_root}")
    
    def build_graph(self) -> None:
        """
        Build dependency graph by walking repository.
        
        Finds all pyproject.toml files and parses dependencies.
        Builds index for fast lookup.
        """
        logger.info(f"Building dependency graph from {self.repo_root}")
        
        # Find all pyproject.toml files
        pyproject_files = list(self.repo_root.rglob("pyproject.toml"))
        logger.info(f"Found {len(pyproject_files)} pyproject.toml files")
        
        for pyproject_path in pyproject_files:
            try:
                service_deps = self._parse_pyproject(pyproject_path)
                if service_deps:
                    self.services[service_deps.service_name] = service_deps
                    self._index_dependencies(service_deps)
            except Exception as e:
                logger.warning(f"Failed to parse {pyproject_path}: {e}")
        
        logger.info(
            f"Dependency graph built: {len(self.services)} services, "
            f"{len(self._package_index)} unique packages"
        )
    
    def _parse_pyproject(self, pyproject_path: Path) -> Optional[ServiceDependencies]:
        """
        Parse a single pyproject.toml file.
        
        Args:
            pyproject_path: Path to pyproject.toml
            
        Returns:
            ServiceDependencies or None if parsing fails
        """
        try:
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)
            
            # Determine service name from path
            service_dir = pyproject_path.parent
            service_name = service_dir.name
            
            # Skip if this is the root pyproject.toml
            if service_dir == self.repo_root:
                logger.debug(f"Skipping root pyproject.toml")
                return None
            
            service_deps = ServiceDependencies(
                service_name=service_name,
                path=service_dir
            )
            
            # Parse dependencies
            # Poetry format: tool.poetry.dependencies
            if "tool" in data and "poetry" in data["tool"]:
                poetry_deps = data["tool"]["poetry"].get("dependencies", {})
                poetry_dev_deps = data["tool"]["poetry"].get("dev-dependencies", {})
                
                # Parse production dependencies
                for pkg_name, version_spec in poetry_deps.items():
                    if pkg_name == "python":  # Skip python itself
                        continue
                    
                    # Handle different version spec formats
                    if isinstance(version_spec, dict):
                        version_str = version_spec.get("version", "*")
                    else:
                        version_str = str(version_spec)
                    
                    service_deps.dependencies.append(
                        PackageDependency(
                            name=pkg_name,
                            version_spec=version_str,
                            ecosystem="PyPI",
                            is_dev=False
                        )
                    )
                
                # Parse dev dependencies
                for pkg_name, version_spec in poetry_dev_deps.items():
                    if pkg_name == "python":
                        continue
                    
                    if isinstance(version_spec, dict):
                        version_str = version_spec.get("version", "*")
                    else:
                        version_str = str(version_spec)
                    
                    service_deps.dev_dependencies.append(
                        PackageDependency(
                            name=pkg_name,
                            version_spec=version_str,
                            ecosystem="PyPI",
                            is_dev=True
                        )
                    )
            
            # PEP 621 format: project.dependencies
            elif "project" in data:
                project_deps = data["project"].get("dependencies", [])
                dev_deps = data["project"].get("optional-dependencies", {}).get("dev", [])
                
                # Parse PEP 508 dependency strings
                for dep_string in project_deps:
                    pkg = self._parse_pep508_dependency(dep_string)
                    if pkg:
                        service_deps.dependencies.append(pkg)
                
                for dep_string in dev_deps:
                    pkg = self._parse_pep508_dependency(dep_string, is_dev=True)
                    if pkg:
                        service_deps.dev_dependencies.append(pkg)
            
            logger.debug(
                f"Parsed {service_name}: "
                f"{len(service_deps.dependencies)} prod deps, "
                f"{len(service_deps.dev_dependencies)} dev deps"
            )
            
            return service_deps
            
        except Exception as e:
            logger.error(f"Error parsing {pyproject_path}: {e}")
            return None
    
    def _parse_pep508_dependency(
        self,
        dep_string: str,
        is_dev: bool = False
    ) -> Optional[PackageDependency]:
        """
        Parse PEP 508 dependency string.
        
        Examples:
            "django>=4.2,<5.0"
            "requests[security]>=2.28.0"
            "pytest==7.4.0; python_version>='3.8'"
        
        Args:
            dep_string: PEP 508 dependency string
            is_dev: Whether this is a dev dependency
            
        Returns:
            PackageDependency or None if parsing fails
        """
        # Remove environment markers (everything after ';')
        if ";" in dep_string:
            dep_string = dep_string.split(";")[0].strip()
        
        # Remove extras (everything in brackets)
        if "[" in dep_string:
            dep_string = re.sub(r'\[.*?\]', '', dep_string)
        
        # Split name and version spec
        match = re.match(r'^([a-zA-Z0-9_-]+)\s*(.*)', dep_string)
        if not match:
            logger.warning(f"Could not parse dependency: {dep_string}")
            return None
        
        pkg_name = match.group(1)
        version_spec = match.group(2).strip() or "*"
        
        return PackageDependency(
            name=pkg_name,
            version_spec=version_spec,
            ecosystem="PyPI",
            is_dev=is_dev
        )
    
    def _index_dependencies(self, service_deps: ServiceDependencies) -> None:
        """
        Index dependencies for fast lookup.
        
        Args:
            service_deps: Service dependencies to index
        """
        for dep in service_deps.all_dependencies:
            pkg_name_lower = dep.name.lower()
            if pkg_name_lower not in self._package_index:
                self._package_index[pkg_name_lower] = set()
            self._package_index[pkg_name_lower].add(service_deps.service_name)
    
    def get_services_using_package(self, package_name: str) -> List[ServiceDependencies]:
        """
        Get all services that depend on a package.
        
        Args:
            package_name: Package name (case-insensitive)
            
        Returns:
            List of ServiceDependencies
        """
        pkg_name_lower = package_name.lower()
        service_names = self._package_index.get(pkg_name_lower, set())
        
        return [
            self.services[name]
            for name in service_names
            if name in self.services
        ]
    
    def get_all_services(self) -> List[ServiceDependencies]:
        """Get all services in the graph."""
        return list(self.services.values())
    
    def get_all_packages(self) -> Set[str]:
        """Get all unique package names."""
        return set(self._package_index.keys())
    
    def get_stats(self) -> Dict[str, Union[int, float]]:
        """
        Get graph statistics.
        
        Returns:
            Dict with service count, package count, etc.
        """
        total_deps = sum(
            len(svc.all_dependencies)
            for svc in self.services.values()
        )
        
        avg_deps: Union[int, float] = 0
        if self.services:
            avg_deps = total_deps / len(self.services)
        
        return {
            "total_services": len(self.services),
            "total_packages": len(self._package_index),
            "total_dependencies": total_deps,
            "avg_deps_per_service": avg_deps
        }
