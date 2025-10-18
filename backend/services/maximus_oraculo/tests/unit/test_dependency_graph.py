"""Unit tests for Dependency Graph Builder.

Tests cover:
- pyproject.toml parsing (Poetry + PEP 621 formats)
- Dependency graph construction
- Package lookups
- Version matching
- Edge cases

Author: MAXIMUS Team  
Date: 2025-10-11
Compliance: TDD | Coverage ≥90%
"""

import sys
from pathlib import Path
import pytest
import tempfile

# Add parent to path
service_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(service_root))

from filtering.dependency_graph import (
    PackageDependency,
    ServiceDependencies,
    DependencyGraphBuilder
)


class TestPackageDependency:
    """Test PackageDependency dataclass."""
    
    def test_create_dependency(self):
        """Test creating a package dependency."""
        dep = PackageDependency(
            name="django",
            version_spec=">=4.2,<5.0",
            ecosystem="PyPI",
            is_dev=False
        )
        
        assert dep.name == "django"
        assert dep.version_spec == ">=4.2,<5.0"
        assert dep.ecosystem == "PyPI"
        assert dep.is_dev is False
    
    def test_matches_version_any(self):
        """Test version matching with wildcard."""
        dep = PackageDependency(name="requests", version_spec="*")
        
        assert dep.matches_version("2.28.0") is True
        assert dep.matches_version("1.0.0") is True
    
    def test_matches_version_exact(self):
        """Test exact version matching."""
        dep = PackageDependency(name="pytest", version_spec="==7.4.0")
        
        assert dep.matches_version("7.4.0") is True
        assert dep.matches_version("7.3.0") is False


class TestServiceDependencies:
    """Test ServiceDependencies dataclass."""
    
    def test_create_service_deps(self):
        """Test creating service dependencies."""
        svc = ServiceDependencies(
            service_name="maximus_oraculo",
            path=Path("/repo/backend/maximus_oraculo")
        )
        
        assert svc.service_name == "maximus_oraculo"
        assert len(svc.dependencies) == 0
        assert len(svc.dev_dependencies) == 0
    
    def test_all_dependencies_property(self):
        """Test all_dependencies combines prod + dev."""
        svc = ServiceDependencies(
            service_name="test_service",
            path=Path("/test")
        )
        
        svc.dependencies.append(PackageDependency("django", ">=4.2"))
        svc.dev_dependencies.append(PackageDependency("pytest", ">=7.0"))
        
        all_deps = svc.all_dependencies
        assert len(all_deps) == 2
        assert any(d.name == "django" for d in all_deps)
        assert any(d.name == "pytest" for d in all_deps)
    
    def test_has_package(self):
        """Test checking if service has a package."""
        svc = ServiceDependencies(service_name="test", path=Path("/test"))
        svc.dependencies.append(PackageDependency("flask", ">=2.0"))
        
        assert svc.has_package("flask") is True
        assert svc.has_package("Flask") is True  # Case insensitive
        assert svc.has_package("django") is False
    
    def test_get_package_version(self):
        """Test getting package version spec."""
        svc = ServiceDependencies(service_name="test", path=Path("/test"))
        svc.dependencies.append(PackageDependency("requests", ">=2.28.0"))
        
        version = svc.get_package_version("requests")
        assert version == ">=2.28.0"
        
        version = svc.get_package_version("nonexistent")
        assert version is None


class TestDependencyGraphBuilder:
    """Test DependencyGraphBuilder."""
    
    @pytest.fixture
    def temp_repo(self):
        """Create temporary repository structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            
            # Create service1 with Poetry format
            service1_dir = repo_root / "backend" / "service1"
            service1_dir.mkdir(parents=True)
            
            pyproject1 = {
                "tool": {
                    "poetry": {
                        "name": "service1",
                        "dependencies": {
                            "python": "^3.11",
                            "django": ">=4.2,<5.0",
                            "requests": "^2.28.0"
                        },
                        "dev-dependencies": {
                            "pytest": "^7.4.0"
                        }
                    }
                }
            }
            
            with open(service1_dir / "pyproject.toml", "wb") as f:
                import tomli_w
                tomli_w.dump(pyproject1, f)
            
            # Create service2 with PEP 621 format
            service2_dir = repo_root / "backend" / "service2"
            service2_dir.mkdir(parents=True)
            
            pyproject2 = {
                "project": {
                    "name": "service2",
                    "dependencies": [
                        "flask>=2.0",
                        "requests>=2.28.0"
                    ],
                    "optional-dependencies": {
                        "dev": [
                            "pytest>=7.0"
                        ]
                    }
                }
            }
            
            with open(service2_dir / "pyproject.toml", "wb") as f:
                import tomli_w
                tomli_w.dump(pyproject2, f)
            
            yield repo_root
    
    def test_builder_initialization(self, temp_repo):
        """Test builder initialization."""
        builder = DependencyGraphBuilder(temp_repo)
        
        assert builder.repo_root == temp_repo
        assert len(builder.services) == 0
    
    def test_build_graph(self, temp_repo):
        """Test building dependency graph."""
        builder = DependencyGraphBuilder(temp_repo)
        builder.build_graph()
        
        # Should find 2 services
        assert len(builder.services) == 2
        assert "service1" in builder.services
        assert "service2" in builder.services
    
    def test_get_services_using_package(self, temp_repo):
        """Test finding services that use a package."""
        builder = DependencyGraphBuilder(temp_repo)
        builder.build_graph()
        
        # Both services use requests
        services = builder.get_services_using_package("requests")
        assert len(services) == 2
        service_names = [s.service_name for s in services]
        assert "service1" in service_names
        assert "service2" in service_names
        
        # Only service1 uses django
        services = builder.get_services_using_package("django")
        assert len(services) == 1
        assert services[0].service_name == "service1"
        
        # Only service2 uses flask
        services = builder.get_services_using_package("flask")
        assert len(services) == 1
        assert services[0].service_name == "service2"
    
    def test_get_all_packages(self, temp_repo):
        """Test getting all unique packages."""
        builder = DependencyGraphBuilder(temp_repo)
        builder.build_graph()
        
        packages = builder.get_all_packages()
        
        # Should have: django, requests, flask, pytest
        assert "django" in packages
        assert "requests" in packages
        assert "flask" in packages
        assert "pytest" in packages
    
    def test_get_stats(self, temp_repo):
        """Test graph statistics."""
        builder = DependencyGraphBuilder(temp_repo)
        builder.build_graph()
        
        stats = builder.get_stats()
        
        assert stats["total_services"] == 2
        assert stats["total_packages"] >= 4  # At least django, requests, flask, pytest
        assert stats["total_dependencies"] >= 6  # At least 3 per service
        assert stats["avg_deps_per_service"] > 0
    
    def test_parse_pep508_dependency(self):
        """Test parsing PEP 508 dependency strings."""
        builder = DependencyGraphBuilder(Path("/tmp"))
        
        # Simple dependency
        dep = builder._parse_pep508_dependency("django>=4.2")
        assert dep is not None
        assert dep.name == "django"
        assert dep.version_spec == ">=4.2"
        
        # Dependency with extras
        dep = builder._parse_pep508_dependency("requests[security]>=2.28.0")
        assert dep is not None
        assert dep.name == "requests"
        assert "[" not in dep.name
        
        # Dependency with environment marker
        dep = builder._parse_pep508_dependency("pytest==7.4.0; python_version>='3.8'")
        assert dep is not None
        assert dep.name == "pytest"
        assert ";" not in dep.version_spec
    
    def test_case_insensitive_lookup(self, temp_repo):
        """Test package lookup is case insensitive."""
        builder = DependencyGraphBuilder(temp_repo)
        builder.build_graph()
        
        # Should work with different cases
        services1 = builder.get_services_using_package("Django")
        services2 = builder.get_services_using_package("django")
        services3 = builder.get_services_using_package("DJANGO")
        
        assert len(services1) == len(services2) == len(services3)


class TestDependencyGraphIntegration:
    """Integration tests with real MAXIMUS repository."""
    
    @pytest.mark.integration
    def test_build_real_maximus_graph(self):
        """
        Integration test: Build graph from real MAXIMUS repo.
        
        Tests that we can parse real pyproject.toml files.
        """
        # Use actual MAXIMUS repo root
        repo_root = Path(__file__).parent.parent.parent.parent.parent
        
        if not (repo_root / "backend").exists():
            pytest.skip("Not in MAXIMUS repo")
        
        builder = DependencyGraphBuilder(repo_root)
        builder.build_graph()
        
        # Should find multiple services
        assert len(builder.services) > 0
        
        # Should have common packages like pydantic, fastapi
        all_packages = builder.get_all_packages()
        
        # Log stats for visibility
        stats = builder.get_stats()
        print(f"\nMAXIMUS Dependency Graph Stats:")
        print(f"  Services: {stats['total_services']}")
        print(f"  Unique Packages: {stats['total_packages']}")
        print(f"  Total Dependencies: {stats['total_dependencies']}")
        print(f"  Avg Deps/Service: {stats['avg_deps_per_service']:.1f}")


# Run tests with:
# pytest tests/unit/test_dependency_graph.py -v
# pytest tests/unit/test_dependency_graph.py -v -m integration

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
