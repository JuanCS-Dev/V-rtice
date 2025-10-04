"""
Integration Tests: SIEM + Findings
===================================

Test forwarding findings to SIEM systems.
"""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile

from vertice.workspace import WorkspaceManager
from vertice.siem_integration import (
    SplunkConnector,
    ElasticsearchConnector,
    CEFFormatter,
    LEEFFormatter,
)


class TestSIEMFindingsIntegration:
    """Test SIEM integration with findings."""

    @pytest.fixture
    def workspace_dir(self):
        """Create temporary workspace directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def workspace(self, workspace_dir):
        """Create workspace manager instance."""
        return WorkspaceManager(workspace_root=workspace_dir)

    @pytest.fixture
    def cef_formatter(self):
        """Create CEF formatter instance."""
        return CEFFormatter()

    @pytest.fixture
    def leef_formatter(self):
        """Create LEEF formatter instance."""
        return LEEFFormatter()

    def test_vulnerability_to_cef_format(self, workspace, cef_formatter):
        """Test converting vulnerability finding to CEF format."""
        project = workspace.create_project("siem-cef-test")
        workspace.switch_project("siem-cef-test")

        # Add host and vulnerability
        host = workspace.add_host(
            ip_address="10.10.1.100",
            hostname="vuln-server.test.com",
        )

        vuln = workspace.add_vulnerability(
            host_id=host.id,
            cve_id="CVE-2021-44228",
            title="Apache Log4j RCE",
            severity="critical",
            cvss_score=10.0,
            description="Remote code execution via JNDI injection",
        )

        # Convert to event dict
        event = {
            "name": vuln.title,
            "severity": vuln.severity,
            "src": host.ip_address,
            "message": vuln.description,
            "cve": vuln.cve_id,
            "cvss": vuln.cvss_score,
        }

        # Format as CEF
        cef_string = cef_formatter.format(event)

        # Verify CEF format
        assert cef_string.startswith("CEF:")
        assert "CVE-2021-44228" in cef_string
        assert "critical" in cef_string.lower() or "10" in cef_string  # severity
        assert "10.10.1.100" in cef_string

    def test_vulnerability_to_leef_format(self, workspace, leef_formatter):
        """Test converting vulnerability finding to LEEF format."""
        project = workspace.create_project("siem-leef-test")
        workspace.switch_project("siem-leef-test")

        # Add host and vulnerability
        host = workspace.add_host(ip_address="10.10.1.200")

        vuln = workspace.add_vulnerability(
            host_id=host.id,
            cve_id="CVE-2020-1472",
            title="Zerologon",
            severity="critical",
        )

        # Convert to event dict
        event = {
            "name": vuln.title,
            "severity": vuln.severity,
            "src": host.ip_address,
            "message": f"Vulnerability {vuln.cve_id} detected",
        }

        # Format as LEEF
        leef_string = leef_formatter.format(event)

        # Verify LEEF format
        assert leef_string.startswith("LEEF:")
        assert "CVE-2020-1472" in leef_string
        assert "10.10.1.200" in leef_string

    def test_batch_findings_to_siem(self, workspace, cef_formatter):
        """Test batching multiple findings for SIEM forwarding."""
        project = workspace.create_project("siem-batch-test")
        workspace.switch_project("siem-batch-test")

        # Add multiple hosts with findings
        events = []

        for i in range(5):
            host = workspace.add_host(ip_address=f"10.10.1.{i+1}")

            vuln = workspace.add_vulnerability(
                host_id=host.id,
                cve_id=f"CVE-2021-{i}",
                title=f"Test Vulnerability {i}",
                severity="high" if i < 3 else "medium",
            )

            event = {
                "name": vuln.title,
                "severity": vuln.severity,
                "src": host.ip_address,
                "message": f"Vulnerability detected on {host.ip_address}",
            }

            events.append(event)

        # Format all events
        formatted_events = [cef_formatter.format(event) for event in events]

        # Verify batch
        assert len(formatted_events) == 5
        assert all(e.startswith("CEF:") for e in formatted_events)

    def test_siem_event_enrichment(self, workspace):
        """Test enriching SIEM events with workspace context."""
        project = workspace.create_project("siem-enrichment-test")
        workspace.switch_project("siem-enrichment-test")

        # Add host with multiple findings
        host = workspace.add_host(
            ip_address="10.10.1.50",
            hostname="web-server.test.com",
            os_family="Linux",
        )

        # Add port
        port = workspace.add_port(
            host_id=host.id,
            port=80,
            protocol="tcp",
            state="open",
            service="http",
            version="Apache 2.4.41",
        )

        # Add vulnerability
        vuln = workspace.add_vulnerability(
            host_id=host.id,
            port_id=port.id,
            cve_id="CVE-2021-44228",
            title="Log4Shell",
            severity="critical",
        )

        # Enrich event with workspace context
        enriched_event = {
            # Core finding
            "name": vuln.title,
            "severity": vuln.severity,
            "cve": vuln.cve_id,
            # Context from workspace
            "src": host.ip_address,
            "shost": host.hostname,
            "dport": port.port,
            "app": port.service,
            "appVersion": port.version,
            "os": host.os_family,
            # Metadata
            "project": project.name,
            "discovered_at": vuln.discovered_at.isoformat() if vuln.discovered_at else None,
        }

        # Verify enrichment
        assert enriched_event["src"] == "10.10.1.50"
        assert enriched_event["shost"] == "web-server.test.com"
        assert enriched_event["dport"] == 80
        assert enriched_event["app"] == "http"
        assert enriched_event["appVersion"] == "Apache 2.4.41"
        assert enriched_event["os"] == "Linux"
        assert enriched_event["project"] == "siem-enrichment-test"

    def test_severity_filtering_for_siem(self, workspace):
        """Test filtering findings by severity before SIEM forwarding."""
        project = workspace.create_project("siem-filter-test")
        workspace.switch_project("siem-filter-test")

        # Add findings with different severities
        severities = ["critical", "high", "medium", "low", "info"]

        for i, severity in enumerate(severities):
            host = workspace.add_host(ip_address=f"10.10.1.{i+1}")

            workspace.add_vulnerability(
                host_id=host.id,
                cve_id=f"CVE-2021-{i}",
                severity=severity,
            )

        # Get only critical and high severity findings
        all_vulns = workspace.query_vulnerabilities()
        high_severity_vulns = [
            v for v in all_vulns if v.severity in ["critical", "high"]
        ]

        # Verify filtering
        assert len(all_vulns) == 5
        assert len(high_severity_vulns) == 2

        # These would be sent to SIEM
        assert all(v.severity in ["critical", "high"] for v in high_severity_vulns)
