"""End-to-End tests for Oráculo Engine.

Tests the complete pipeline:
OSV.dev → Dependency Graph → Relevance Filter → APV Generation → Kafka Publishing

Author: MAXIMUS Team
Date: 2025-10-11
Compliance: TDD | E2E Testing | Integration
"""

import sys
from pathlib import Path
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import tempfile

# Add parent to path
service_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(service_root))

from oraculo_engine import OraculoEngine
from services.maximus_oraculo.models.apv import APV


class TestOraculoEngine:
    """Test Oráculo Engine."""
    
    def test_engine_initialization(self):
        """Test engine initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = OraculoEngine(
                repo_root=Path(tmpdir),
                kafka_servers="localhost:9096"
            )
            
            assert engine.repo_root == Path(tmpdir)
            assert engine.kafka_servers == "localhost:9096"
            assert engine.dependency_graph is None  # Not initialized yet
            assert engine._metrics["vulnerabilities_fetched"] == 0
    
    @pytest.mark.asyncio
    async def test_engine_initialize_components(self):
        """Test engine component initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            
            # Create a test service
            svc_dir = repo_root / "test-service"
            svc_dir.mkdir()
            
            pyproject = {
                "tool": {
                    "poetry": {
                        "name": "test-service",
                        "dependencies": {
                            "django": ">=4.2"
                        }
                    }
                }
            }
            
            with open(svc_dir / "pyproject.toml", "wb") as f:
                import tomli_w
                tomli_w.dump(pyproject, f)
            
            engine = OraculoEngine(repo_root=repo_root)
            
            # Mock external components
            with patch('oraculo_engine.OSVClient') as mock_osv:
                with patch('oraculo_engine.APVPublisher') as mock_publisher:
                    mock_osv_instance = AsyncMock()
                    mock_osv.return_value = mock_osv_instance
                    
                    mock_publisher_instance = AsyncMock()
                    mock_publisher.return_value = mock_publisher_instance
                    
                    await engine.initialize()
                    
                    # Check components are initialized
                    assert engine.dependency_graph is not None
                    assert engine.relevance_filter is not None
                    assert engine.osv_client is not None
                    assert engine.apv_publisher is not None
                    
                    # Check graph was built
                    assert len(engine.dependency_graph.services) > 0
                    
                    await engine.shutdown()
    
    @pytest.mark.asyncio
    async def test_engine_shutdown(self):
        """Test engine shutdown."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = OraculoEngine(repo_root=Path(tmpdir))
            
            # Mock components
            engine.osv_client = AsyncMock()
            engine.apv_publisher = AsyncMock()
            
            await engine.shutdown()
            
            # Check close was called
            assert engine.osv_client.close.called
            assert engine.apv_publisher.stop.called
    
    @pytest.mark.asyncio
    async def test_scan_vulnerabilities_not_initialized(self):
        """Test scan fails if not initialized."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = OraculoEngine(repo_root=Path(tmpdir))
            
            with pytest.raises(RuntimeError) as exc_info:
                await engine.scan_vulnerabilities()
            
            assert "not initialized" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_fetch_vulnerabilities(self):
        """Test fetching vulnerabilities."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = OraculoEngine(repo_root=Path(tmpdir))
            
            # Mock OSV client
            mock_osv = AsyncMock()
            mock_osv.query_batch = AsyncMock(return_value={
                "django": [
                    {"id": "CVE-2024-001", "summary": "Test vuln 1"},
                    {"id": "CVE-2024-002", "summary": "Test vuln 2"}
                ],
                "requests": [
                    {"id": "CVE-2024-003", "summary": "Test vuln 3"}
                ]
            })
            engine.osv_client = mock_osv
            
            vulns = await engine._fetch_vulnerabilities(["django", "requests"])
            
            assert len(vulns) == 3
            assert mock_osv.query_batch.called
    
    @pytest.mark.asyncio
    async def test_generate_apvs(self):
        """Test APV generation from matches."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = OraculoEngine(repo_root=Path(tmpdir))
            
            # Create mock relevance matches
            from filtering.relevance_filter import RelevanceMatch
            
            matches = [
                RelevanceMatch(
                    cve_id="CVE-2024-12345",
                    package_name="django",
                    ecosystem="PyPI",
                    affected_services=["test-service"],
                    version_match=True,
                    severity_score=8.5
                )
            ]
            
            raw_vulns = [
                {
                    "id": "CVE-2024-12345",
                    "published": "2024-01-01T00:00:00Z",
                    "modified": "2024-01-02T00:00:00Z",
                    "summary": "Test vulnerability in Django",
                    "details": "Detailed description of the vulnerability affecting Django framework.",
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
            
            apvs = await engine._generate_apvs(matches, raw_vulns)
            
            assert len(apvs) == 1
            assert apvs[0].cve_id == "CVE-2024-12345"
            assert apvs[0].summary == "Test vulnerability in Django"
            assert len(apvs[0].affected_packages) > 0
            assert "test-service" in apvs[0].maximus_context["affected_services"]


class TestOraculoEngineE2E:
    """End-to-end tests for complete pipeline."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_full_pipeline_mock(self):
        """
        Test full pipeline with mocked external services.
        
        Pipeline: Fetch → Filter → Generate → Publish
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            
            # Create test services
            services = {
                "api-service": {"django": ">=4.2,<5.0"},
                "worker-service": {"celery": "^5.3.0"}
            }
            
            for svc_name, deps in services.items():
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
            
            engine = OraculoEngine(repo_root=repo_root)
            
            # Mock OSV client
            mock_osv = AsyncMock()
            mock_osv.query_batch = AsyncMock(return_value={
                "django": [
                    {
                        "id": "CVE-2024-DJANGO",
                        "published": "2024-01-01T00:00:00Z",
                        "modified": "2024-01-02T00:00:00Z",
                        "summary": "Django vulnerability",
                        "details": "Detailed description of Django vulnerability affecting multiple versions.",
                        "affected": [
                            {
                                "package": {
                                    "name": "django",
                                    "ecosystem": "PyPI"
                                },
                                "ranges": []
                            }
                        ]
                    }
                ]
            })
            
            # Mock Kafka publisher
            mock_publisher = AsyncMock()
            mock_publisher.start = AsyncMock()
            mock_publisher.stop = AsyncMock()
            mock_publisher.publish_batch = AsyncMock(return_value={
                "success": 1,
                "failed": 0,
                "total": 1
            })
            
            with patch('oraculo_engine.OSVClient', return_value=mock_osv):
                with patch('oraculo_engine.APVPublisher', return_value=mock_publisher):
                    # Initialize
                    await engine.initialize()
                    
                    # Run scan
                    results = await engine.scan_vulnerabilities(packages=["django"])
                    
                    # Verify results
                    assert results["packages_scanned"] == 1
                    assert results["vulnerabilities_fetched"] == 1
                    assert results["relevant_matches"] >= 1
                    assert results["apvs_generated"] >= 1
                    assert results["published"] >= 1
                    
                    # Verify publisher was called
                    assert mock_publisher.publish_batch.called
                    
                    # Check metrics
                    metrics = engine.get_metrics()
                    assert metrics["vulnerabilities_fetched"] == 1
                    assert metrics["last_run"] is not None
                    
                    await engine.shutdown()
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_pipeline_with_no_relevant_vulns(self):
        """Test pipeline when no vulnerabilities are relevant."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            
            # Create service with specific package
            svc_dir = repo_root / "test-service"
            svc_dir.mkdir()
            
            pyproject = {
                "tool": {
                    "poetry": {
                        "name": "test-service",
                        "dependencies": {
                            "flask": "^3.0.0"
                        }
                    }
                }
            }
            
            with open(svc_dir / "pyproject.toml", "wb") as f:
                import tomli_w
                tomli_w.dump(pyproject, f)
            
            engine = OraculoEngine(repo_root=repo_root)
            
            # Mock OSV client - return vuln for different package
            mock_osv = AsyncMock()
            mock_osv.query_batch = AsyncMock(return_value={
                "flask": [
                    {
                        "id": "CVE-2024-NOTFLASK",
                        "published": "2024-01-01T00:00:00Z",
                        "modified": "2024-01-02T00:00:00Z",
                        "summary": "Vuln for different package",
                        "details": "This vulnerability affects a completely different package.",
                        "affected": [
                            {
                                "package": {
                                    "name": "different-package",
                                    "ecosystem": "PyPI"
                                }
                            }
                        ]
                    }
                ]
            })
            
            mock_publisher = AsyncMock()
            mock_publisher.start = AsyncMock()
            mock_publisher.stop = AsyncMock()
            mock_publisher.publish_batch = AsyncMock(return_value={
                "success": 0,
                "failed": 0,
                "total": 0
            })
            
            with patch('oraculo_engine.OSVClient', return_value=mock_osv):
                with patch('oraculo_engine.APVPublisher', return_value=mock_publisher):
                    await engine.initialize()
                    
                    results = await engine.scan_vulnerabilities(packages=["flask"])
                    
                    # No relevant matches
                    assert results["relevant_matches"] == 0
                    assert results["apvs_generated"] == 0
                    assert results["published"] == 0
                    
                    await engine.shutdown()
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_pipeline_error_handling(self):
        """Test pipeline handles errors gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            
            svc_dir = repo_root / "test-service"
            svc_dir.mkdir()
            
            pyproject = {
                "tool": {
                    "poetry": {
                        "name": "test-service",
                        "dependencies": {"django": ">=4.2"}
                    }
                }
            }
            
            with open(svc_dir / "pyproject.toml", "wb") as f:
                import tomli_w
                tomli_w.dump(pyproject, f)
            
            engine = OraculoEngine(repo_root=repo_root)
            
            # Mock OSV client to raise error
            mock_osv = AsyncMock()
            mock_osv.query_batch = AsyncMock(side_effect=Exception("OSV API error"))
            
            mock_publisher = AsyncMock()
            mock_publisher.start = AsyncMock()
            mock_publisher.stop = AsyncMock()
            
            with patch('oraculo_engine.OSVClient', return_value=mock_osv):
                with patch('oraculo_engine.APVPublisher', return_value=mock_publisher):
                    await engine.initialize()
                    
                    # Should handle error gracefully
                    results = await engine.scan_vulnerabilities(packages=["django"])
                    
                    # Should still return results structure
                    assert "vulnerabilities_fetched" in results
                    assert results["vulnerabilities_fetched"] == 0  # Error means no vulns fetched
                    
                    await engine.shutdown()


# Run tests with:
# pytest tests/unit/test_oraculo_engine.py -v
# pytest tests/unit/test_oraculo_engine.py -v -m e2e

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
