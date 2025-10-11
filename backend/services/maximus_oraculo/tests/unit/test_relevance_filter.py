"""Integration tests for Relevance Filter.

Tests cover:
- Cross-referencing with real dependency graph
- Version matching edge cases
- Severity filtering
- RelevanceMatch generation
- Stats calculation

Author: MAXIMUS Team
Date: 2025-10-11
Compliance: TDD | Coverage ≥90% | Integration Testing
"""

import sys
from pathlib import Path
import pytest
import tempfile
from datetime import datetime

# Add parent to path
service_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(service_root))

from filtering.dependency_graph import DependencyGraphBuilder, PackageDependency, ServiceDependencies
from filtering.relevance_filter import RelevanceFilter, RelevanceMatch


class TestRelevanceMatch:
    """Test RelevanceMatch dataclass."""
    
    def test_create_relevance_match(self):
        """Test creating a relevance match."""
        match = RelevanceMatch(
            cve_id="CVE-2024-12345",
            package_name="django",
            ecosystem="PyPI",
            affected_services=["backend-api", "admin-service"],
            version_match=True,
            severity_score=8.5
        )
        
        assert match.cve_id == "CVE-2024-12345"
        assert match.package_name == "django"
        assert len(match.affected_services) == 2
        assert match.version_match is True
        assert match.severity_score == 8.5


class TestRelevanceFilter:
    """Test RelevanceFilter."""
    
    @pytest.fixture
    def mock_dependency_graph(self):
        """Create a mock dependency graph for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            
            # Create test services
            service1_dir = repo_root / "service1"
            service1_dir.mkdir()
            
            # Create pyproject.toml for service1
            pyproject1 = {
                "tool": {
                    "poetry": {
                        "name": "service1",
                        "dependencies": {
                            "django": ">=4.2,<5.0",
                            "requests": "^2.28.0"
                        }
                    }
                }
            }
            
            with open(service1_dir / "pyproject.toml", "wb") as f:
                import tomli_w
                tomli_w.dump(pyproject1, f)
            
            # Build graph
            graph = DependencyGraphBuilder(repo_root)
            graph.build_graph()
            
            yield graph
    
    def test_filter_initialization(self, mock_dependency_graph):
        """Test filter initialization."""
        filter = RelevanceFilter(mock_dependency_graph)
        
        assert filter.dependency_graph == mock_dependency_graph
        assert len(filter._ecosystem_map) > 0
    
    def test_filter_vulnerabilities_empty_list(self, mock_dependency_graph):
        """Test filtering empty vulnerability list."""
        filter = RelevanceFilter(mock_dependency_graph)
        
        relevant = filter.filter_vulnerabilities([])
        
        assert len(relevant) == 0
    
    def test_filter_vulnerabilities_no_match(self, mock_dependency_graph):
        """Test filtering vulnerabilities with no matches."""
        filter = RelevanceFilter(mock_dependency_graph)
        
        # Vulnerability for package we don't use
        vulns = [
            {
                "id": "CVE-2024-00001",
                "affected": [
                    {
                        "package": {
                            "name": "nonexistent-package",
                            "ecosystem": "PyPI"
                        }
                    }
                ]
            }
        ]
        
        relevant = filter.filter_vulnerabilities(vulns)
        
        assert len(relevant) == 0
    
    def test_filter_vulnerabilities_with_match(self, mock_dependency_graph):
        """Test filtering vulnerabilities with matches."""
        filter = RelevanceFilter(mock_dependency_graph)
        
        # Vulnerability for django (which service1 uses)
        vulns = [
            {
                "id": "CVE-2024-12345",
                "affected": [
                    {
                        "package": {
                            "name": "django",
                            "ecosystem": "PyPI"
                        },
                        "ranges": [
                            {
                                "type": "ECOSYSTEM",
                                "events": [
                                    {"introduced": "4.0"},
                                    {"fixed": "4.2.5"}
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
        
        relevant = filter.filter_vulnerabilities(vulns)
        
        assert len(relevant) > 0
        assert relevant[0].cve_id == "CVE-2024-12345"
        assert relevant[0].package_name == "django"
        assert "service1" in relevant[0].affected_services
    
    def test_filter_by_severity(self, mock_dependency_graph):
        """Test filtering by minimum severity."""
        filter = RelevanceFilter(mock_dependency_graph)
        
        # Create vulnerabilities with different severities
        vulns = [
            {
                "id": "CVE-2024-HIGH",
                "affected": [{"package": {"name": "django", "ecosystem": "PyPI"}}],
                "database_specific": {"cvss_score": 8.5}
            },
            {
                "id": "CVE-2024-LOW",
                "affected": [{"package": {"name": "django", "ecosystem": "PyPI"}}],
                "database_specific": {"cvss_score": 3.0}
            }
        ]
        
        # Filter with min_severity=7.0
        relevant = filter.filter_vulnerabilities(vulns, min_severity=7.0)
        
        # Should only have the high severity one
        cve_ids = [m.cve_id for m in relevant]
        assert "CVE-2024-HIGH" in cve_ids
        assert "CVE-2024-LOW" not in cve_ids
    
    def test_extract_cvss_score(self, mock_dependency_graph):
        """Test CVSS score extraction."""
        filter = RelevanceFilter(mock_dependency_graph)
        
        # Vulnerability with CVSS in database_specific
        vuln = {
            "id": "CVE-2024-12345",
            "database_specific": {
                "cvss_score": 7.5
            }
        }
        
        score = filter._extract_cvss_score(vuln)
        assert score == 7.5
        
        # Vulnerability without CVSS
        vuln_no_cvss = {
            "id": "CVE-2024-00002"
        }
        
        score = filter._extract_cvss_score(vuln_no_cvss)
        assert score is None
    
    def test_check_version_match_no_constraints(self, mock_dependency_graph):
        """Test version matching with no constraints."""
        filter = RelevanceFilter(mock_dependency_graph)
        
        # Get service1
        service = mock_dependency_graph.services.get("service1")
        assert service is not None
        
        # No ranges or versions means all versions affected
        match = filter._check_version_match(service, "django", [], [])
        
        assert match is True
    
    def test_check_version_match_with_ranges(self, mock_dependency_graph):
        """Test version matching with ranges."""
        filter = RelevanceFilter(mock_dependency_graph)
        
        service = mock_dependency_graph.services.get("service1")
        assert service is not None
        
        # Range that affects versions
        ranges = [
            {
                "type": "ECOSYSTEM",
                "events": [
                    {"introduced": "4.0"},
                    {"fixed": "4.2.5"}
                ]
            }
        ]
        
        match = filter._check_version_match(service, "django", ranges, [])
        
        # Should match (service uses >=4.2,<5.0)
        assert match is True
    
    def test_get_most_critical(self, mock_dependency_graph):
        """Test getting most critical vulnerabilities."""
        filter = RelevanceFilter(mock_dependency_graph)
        
        matches = [
            RelevanceMatch(
                cve_id="CVE-LOW",
                package_name="pkg1",
                ecosystem="PyPI",
                affected_services=["svc1"],
                version_match=True,
                severity_score=3.0
            ),
            RelevanceMatch(
                cve_id="CVE-HIGH",
                package_name="pkg2",
                ecosystem="PyPI",
                affected_services=["svc1", "svc2", "svc3"],
                version_match=True,
                severity_score=8.5
            ),
            RelevanceMatch(
                cve_id="CVE-MEDIUM",
                package_name="pkg3",
                ecosystem="PyPI",
                affected_services=["svc1", "svc2"],
                version_match=True,
                severity_score=6.0
            )
        ]
        
        critical = filter.get_most_critical(matches, limit=2)
        
        assert len(critical) == 2
        # Should be sorted by affected services count, then severity
        assert critical[0].cve_id == "CVE-HIGH"  # 3 services, 8.5 severity
        assert critical[1].cve_id == "CVE-MEDIUM"  # 2 services, 6.0 severity
    
    def test_get_stats_empty(self, mock_dependency_graph):
        """Test stats with empty matches."""
        filter = RelevanceFilter(mock_dependency_graph)
        
        stats = filter.get_stats([])
        
        assert stats["total_matches"] == 0
        assert stats["unique_cves"] == 0
        assert stats["unique_packages"] == 0
    
    def test_get_stats_with_matches(self, mock_dependency_graph):
        """Test stats with matches."""
        filter = RelevanceFilter(mock_dependency_graph)
        
        matches = [
            RelevanceMatch(
                cve_id="CVE-2024-001",
                package_name="django",
                ecosystem="PyPI",
                affected_services=["svc1", "svc2"],
                version_match=True
            ),
            RelevanceMatch(
                cve_id="CVE-2024-002",
                package_name="flask",
                ecosystem="PyPI",
                affected_services=["svc3"],
                version_match=False
            )
        ]
        
        stats = filter.get_stats(matches)
        
        assert stats["total_matches"] == 2
        assert stats["unique_cves"] == 2
        assert stats["unique_packages"] == 2
        assert stats["total_affected_services"] == 3
        assert stats["version_matches"] == 1
        assert stats["version_match_rate"] == 0.5
    
    def test_increment_version(self, mock_dependency_graph):
        """Test version incrementing."""
        filter = RelevanceFilter(mock_dependency_graph)
        
        # Semantic version
        incremented = filter._increment_version("4.2.7")
        assert incremented == "4.2.8"
        
        # Another semantic version
        incremented = filter._increment_version("1.0.0")
        assert incremented == "1.0.1"


class TestRelevanceFilterIntegration:
    """Integration tests with more realistic scenarios."""
    
    @pytest.fixture
    def realistic_graph(self):
        """Create a more realistic dependency graph."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            
            # Create multiple services with overlapping dependencies
            services_config = {
                "api-service": {
                    "django": ">=4.2,<5.0",
                    "requests": "^2.28.0",
                    "pydantic": "^2.0.0"
                },
                "worker-service": {
                    "celery": "^5.3.0",
                    "requests": "^2.28.0",
                    "redis": "^4.5.0"
                },
                "admin-service": {
                    "django": ">=4.2,<5.0",
                    "jinja2": "^3.1.0"
                }
            }
            
            for svc_name, deps in services_config.items():
                svc_dir = repo_root / svc_name
                svc_dir.mkdir()
                
                pyproject = {
                    "tool": {
                        "poetry": {
                            "name": svc_name,
                            "dependencies": deps
                        }
                    }
                }
                
                with open(svc_dir / "pyproject.toml", "wb") as f:
                    import tomli_w
                    tomli_w.dump(pyproject, f)
            
            graph = DependencyGraphBuilder(repo_root)
            graph.build_graph()
            
            yield graph
    
    def test_filter_multiple_services_affected(self, realistic_graph):
        """Test filtering when multiple services are affected."""
        filter = RelevanceFilter(realistic_graph)
        
        # Django vulnerability affects api-service and admin-service
        vulns = [
            {
                "id": "CVE-2024-DJANGO",
                "affected": [
                    {
                        "package": {
                            "name": "django",
                            "ecosystem": "PyPI"
                        }
                    }
                ]
            }
        ]
        
        relevant = filter.filter_vulnerabilities(vulns)
        
        assert len(relevant) >= 2  # At least 2 matches (one per service)
        
        # Check both services are in affected services
        all_affected = []
        for match in relevant:
            all_affected.extend(match.affected_services)
        
        assert "api-service" in all_affected
        assert "admin-service" in all_affected
    
    def test_filter_shared_dependency(self, realistic_graph):
        """Test filtering shared dependency (requests)."""
        filter = RelevanceFilter(realistic_graph)
        
        # requests vulnerability affects both api-service and worker-service
        vulns = [
            {
                "id": "CVE-2024-REQUESTS",
                "affected": [
                    {
                        "package": {
                            "name": "requests",
                            "ecosystem": "PyPI"
                        }
                    }
                ]
            }
        ]
        
        relevant = filter.filter_vulnerabilities(vulns)
        
        assert len(relevant) >= 2
        
        all_affected = []
        for match in relevant:
            all_affected.extend(match.affected_services)
        
        assert "api-service" in all_affected
        assert "worker-service" in all_affected


# Run tests with:
# pytest tests/unit/test_relevance_filter.py -v
# pytest tests/unit/test_relevance_filter.py -v --cov=filtering

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
