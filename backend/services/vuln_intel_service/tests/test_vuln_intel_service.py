"""Unit tests for Vulnerability Intelligence Service.

DOUTRINA VÉRTICE - ARTIGO II: PAGANI Standard
Tests cover actual production implementation:
- Health check endpoint
- Query CVE information (found/not found)
- Correlate software vulnerabilities
- Nuclei vulnerability scanning
- Request validation
- Edge cases

Note: CVECorrelator and NucleiWrapper are mocked in tests to isolate
API logic (test infrastructure mocking, not production code).
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch

# Import the FastAPI app
import sys
sys.path.insert(0, "/home/juan/vertice-dev/backend/services/vuln_intel_service")
from api import app


# ==================== FIXTURES ====================


@pytest_asyncio.fixture
async def client():
    """Create async HTTP client for testing FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def mock_cve_correlator():
    """Mock CVECorrelator for testing."""
    with patch('api.cve_correlator') as mock_cve:
        mock_cve.get_cve_info = AsyncMock(return_value=None)  # Default: not found
        mock_cve.correlate_vulnerability = AsyncMock(return_value=[])  # Default: empty
        yield mock_cve


@pytest_asyncio.fixture
async def mock_nuclei_wrapper():
    """Mock NucleiWrapper for testing."""
    with patch('api.nuclei_wrapper') as mock_nuclei:
        mock_nuclei.run_scan = AsyncMock(return_value={"vulnerabilities": []})
        yield mock_nuclei


# ==================== HEALTH CHECK TESTS ====================


@pytest.mark.asyncio
class TestHealthEndpoint:
    """Test health check endpoint."""

    async def test_health_check_returns_healthy_status(self, client):
        """Test health endpoint returns operational status."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "operational" in data["message"].lower()


# ==================== QUERY CVE TESTS ====================


@pytest.mark.asyncio
class TestQueryCVEEndpoint:
    """Test CVE query endpoint."""

    async def test_query_cve_found(self, client, mock_cve_correlator, mock_nuclei_wrapper):
        """Test querying existing CVE."""
        mock_cve_correlator.get_cve_info.return_value = {
            "cve_id": "CVE-2023-1234",
            "description": "Remote code execution vulnerability",
            "cvss_score": 9.8,
            "severity": "CRITICAL"
        }

        payload = {"cve_id": "CVE-2023-1234"}
        response = await client.post("/query_cve", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "cve_info" in data
        assert data["cve_info"]["cve_id"] == "CVE-2023-1234"
        assert data["cve_info"]["severity"] == "CRITICAL"

        mock_cve_correlator.get_cve_info.assert_called_once_with("CVE-2023-1234")

    async def test_query_cve_not_found(self, client, mock_cve_correlator, mock_nuclei_wrapper):
        """Test querying non-existent CVE."""
        mock_cve_correlator.get_cve_info.return_value = None

        payload = {"cve_id": "CVE-9999-9999"}
        response = await client.post("/query_cve", json=payload)

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    async def test_query_cve_with_different_formats(self, client, mock_cve_correlator, mock_nuclei_wrapper):
        """Test querying CVEs with different ID formats."""
        mock_cve_correlator.get_cve_info.return_value = {"cve_id": "test"}

        cve_ids = [
            "CVE-2023-1234",
            "CVE-2024-0001",
            "CVE-2020-99999"
        ]

        for cve_id in cve_ids:
            payload = {"cve_id": cve_id}
            response = await client.post("/query_cve", json=payload)
            assert response.status_code == 200

    async def test_query_cve_includes_timestamp(self, client, mock_cve_correlator, mock_nuclei_wrapper):
        """Test that response includes timestamp."""
        mock_cve_correlator.get_cve_info.return_value = {"cve_id": "CVE-2023-1234"}

        payload = {"cve_id": "CVE-2023-1234"}
        response = await client.post("/query_cve", json=payload)

        data = response.json()
        assert "timestamp" in data
        # Verify ISO format
        from datetime import datetime
        datetime.fromisoformat(data["timestamp"])


# ==================== CORRELATE SOFTWARE VULNS TESTS ====================


@pytest.mark.asyncio
class TestCorrelateSoftwareVulnsEndpoint:
    """Test software vulnerability correlation endpoint."""

    async def test_correlate_software_vulns_found(self, client, mock_cve_correlator, mock_nuclei_wrapper):
        """Test correlating software with known vulnerabilities."""
        mock_cve_correlator.correlate_vulnerability.return_value = [
            {"cve_id": "CVE-2023-1111", "severity": "HIGH"},
            {"cve_id": "CVE-2023-2222", "severity": "MEDIUM"}
        ]

        payload = {
            "software_name": "Apache",
            "software_version": "2.4.49"
        }
        response = await client.post("/correlate_software_vulns", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["correlated_cves"]) == 2
        assert data["correlated_cves"][0]["cve_id"] == "CVE-2023-1111"

        mock_cve_correlator.correlate_vulnerability.assert_called_once_with("Apache", "2.4.49")

    async def test_correlate_software_vulns_no_vulns(self, client, mock_cve_correlator, mock_nuclei_wrapper):
        """Test correlating software with no known vulnerabilities."""
        mock_cve_correlator.correlate_vulnerability.return_value = []

        payload = {
            "software_name": "SafeSoftware",
            "software_version": "1.0.0"
        }
        response = await client.post("/correlate_software_vulns", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["correlated_cves"]) == 0

    async def test_correlate_different_software(self, client, mock_cve_correlator, mock_nuclei_wrapper):
        """Test correlating different software products."""
        mock_cve_correlator.correlate_vulnerability.return_value = [{"cve_id": "test"}]

        software_list = [
            ("Apache", "2.4.49"),
            ("nginx", "1.18.0"),
            ("OpenSSL", "1.1.1k"),
            ("WordPress", "5.8.0")
        ]

        for sw_name, sw_version in software_list:
            payload = {
                "software_name": sw_name,
                "software_version": sw_version
            }
            response = await client.post("/correlate_software_vulns", json=payload)
            assert response.status_code == 200

    async def test_correlate_includes_timestamp(self, client, mock_cve_correlator, mock_nuclei_wrapper):
        """Test that response includes timestamp."""
        mock_cve_correlator.correlate_vulnerability.return_value = []

        payload = {"software_name": "Test", "software_version": "1.0"}
        response = await client.post("/correlate_software_vulns", json=payload)

        data = response.json()
        assert "timestamp" in data


# ==================== NUCLEI SCAN TESTS ====================


@pytest.mark.asyncio
class TestNucleiScanEndpoint:
    """Test Nuclei vulnerability scan endpoint."""

    async def test_nuclei_scan_basic(self, client, mock_cve_correlator, mock_nuclei_wrapper):
        """Test basic Nuclei scan."""
        mock_nuclei_wrapper.run_scan.return_value = {
            "vulnerabilities": [
                {"template": "cve-2023-1234", "severity": "critical", "url": "http://target.com"}
            ]
        }

        payload = {"target": "http://target.com"}
        response = await client.post("/nuclei_scan", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "nuclei_results" in data
        assert len(data["nuclei_results"]["vulnerabilities"]) == 1

        mock_nuclei_wrapper.run_scan.assert_called_once_with("http://target.com", None, None)

    async def test_nuclei_scan_with_template(self, client, mock_cve_correlator, mock_nuclei_wrapper):
        """Test Nuclei scan with custom template."""
        mock_nuclei_wrapper.run_scan.return_value = {"vulnerabilities": []}

        payload = {
            "target": "http://target.com",
            "template_path": "/templates/cves/"
        }
        response = await client.post("/nuclei_scan", json=payload)

        assert response.status_code == 200
        mock_nuclei_wrapper.run_scan.assert_called_once_with(
            "http://target.com",
            "/templates/cves/",
            None
        )

    async def test_nuclei_scan_with_options(self, client, mock_cve_correlator, mock_nuclei_wrapper):
        """Test Nuclei scan with custom options."""
        mock_nuclei_wrapper.run_scan.return_value = {"vulnerabilities": []}

        payload = {
            "target": "http://target.com",
            "options": ["-severity", "high,critical", "-rate-limit", "150"]
        }
        response = await client.post("/nuclei_scan", json=payload)

        assert response.status_code == 200
        call_args = mock_nuclei_wrapper.run_scan.call_args
        assert call_args[0][2] == ["-severity", "high,critical", "-rate-limit", "150"]

    async def test_nuclei_scan_no_vulns_found(self, client, mock_cve_correlator, mock_nuclei_wrapper):
        """Test Nuclei scan with no vulnerabilities found."""
        mock_nuclei_wrapper.run_scan.return_value = {"vulnerabilities": []}

        payload = {"target": "http://safe-site.com"}
        response = await client.post("/nuclei_scan", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert len(data["nuclei_results"]["vulnerabilities"]) == 0

    async def test_nuclei_scan_includes_timestamp(self, client, mock_cve_correlator, mock_nuclei_wrapper):
        """Test that response includes timestamp."""
        mock_nuclei_wrapper.run_scan.return_value = {"vulnerabilities": []}

        payload = {"target": "http://target.com"}
        response = await client.post("/nuclei_scan", json=payload)

        data = response.json()
        assert "timestamp" in data


# ==================== REQUEST VALIDATION TESTS ====================


@pytest.mark.asyncio
class TestRequestValidation:
    """Test request validation."""

    async def test_query_cve_missing_cve_id_returns_422(self, client, mock_cve_correlator, mock_nuclei_wrapper):
        """Test CVE query without cve_id."""
        payload = {}

        response = await client.post("/query_cve", json=payload)
        assert response.status_code == 422

    async def test_correlate_missing_software_name_returns_422(self, client, mock_cve_correlator, mock_nuclei_wrapper):
        """Test correlation without software_name."""
        payload = {"software_version": "1.0"}

        response = await client.post("/correlate_software_vulns", json=payload)
        assert response.status_code == 422

    async def test_correlate_missing_software_version_returns_422(self, client, mock_cve_correlator, mock_nuclei_wrapper):
        """Test correlation without software_version."""
        payload = {"software_name": "Apache"}

        response = await client.post("/correlate_software_vulns", json=payload)
        assert response.status_code == 422

    async def test_nuclei_scan_missing_target_returns_422(self, client, mock_cve_correlator, mock_nuclei_wrapper):
        """Test Nuclei scan without target."""
        payload = {}

        response = await client.post("/nuclei_scan", json=payload)
        assert response.status_code == 422


# ==================== EDGE CASES ====================


@pytest.mark.asyncio
class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    async def test_query_cve_empty_string(self, client, mock_cve_correlator, mock_nuclei_wrapper):
        """Test querying with empty CVE ID."""
        mock_cve_correlator.get_cve_info.return_value = None

        payload = {"cve_id": ""}
        response = await client.post("/query_cve", json=payload)

        # Should be accepted (validation happens in correlator)
        assert response.status_code in [200, 404]

    async def test_correlate_with_special_characters(self, client, mock_cve_correlator, mock_nuclei_wrapper):
        """Test correlation with special characters in software name."""
        mock_cve_correlator.correlate_vulnerability.return_value = []

        payload = {
            "software_name": "Apache HTTP Server (mod_ssl)",
            "software_version": "2.4.49-r1"
        }
        response = await client.post("/correlate_software_vulns", json=payload)

        assert response.status_code == 200

    async def test_nuclei_scan_different_target_formats(self, client, mock_cve_correlator, mock_nuclei_wrapper):
        """Test Nuclei scan with different target formats."""
        mock_nuclei_wrapper.run_scan.return_value = {"vulnerabilities": []}

        targets = [
            "http://target.com",
            "https://target.com:8443",
            "192.168.1.1",
            "file:///path/to/targets.txt"
        ]

        for target in targets:
            payload = {"target": target}
            response = await client.post("/nuclei_scan", json=payload)
            assert response.status_code == 200

    async def test_nuclei_scan_empty_options(self, client, mock_cve_correlator, mock_nuclei_wrapper):
        """Test Nuclei scan with empty options list."""
        mock_nuclei_wrapper.run_scan.return_value = {"vulnerabilities": []}

        payload = {
            "target": "http://target.com",
            "options": []
        }
        response = await client.post("/nuclei_scan", json=payload)

        assert response.status_code == 200

    async def test_query_cve_with_complex_response(self, client, mock_cve_correlator, mock_nuclei_wrapper):
        """Test CVE query with complex nested response."""
        mock_cve_correlator.get_cve_info.return_value = {
            "cve_id": "CVE-2023-1234",
            "description": "Test vulnerability",
            "cvss_v3": {
                "base_score": 9.8,
                "vector_string": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
            },
            "references": [
                {"url": "https://nvd.nist.gov/vuln/detail/CVE-2023-1234"},
                {"url": "https://github.com/advisories/GHSA-xxxx"}
            ],
            "exploits": ["metasploit", "exploit-db"]
        }

        payload = {"cve_id": "CVE-2023-1234"}
        response = await client.post("/query_cve", json=payload)

        data = response.json()
        assert data["cve_info"]["cvss_v3"]["base_score"] == 9.8
        assert len(data["cve_info"]["exploits"]) == 2
