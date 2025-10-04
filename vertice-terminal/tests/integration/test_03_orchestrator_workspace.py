"""
Integration Tests: Tool Orchestration + Workspace
==================================================

Test that scan results from tool executors are properly stored in workspace.
"""

import pytest
from pathlib import Path
import tempfile

from vertice.workspace import WorkspaceManager


class TestOrchestratorWorkspaceIntegration:
    """Test tool orchestration integration with workspace."""

    @pytest.fixture
    def workspace_dir(self):
        """Create temporary workspace directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def workspace(self, workspace_dir):
        """Create workspace manager instance."""
        return WorkspaceManager(workspace_root=workspace_dir)


    def test_nmap_scan_stores_hosts(self, workspace):
        """Test that Nmap scan results are stored in workspace."""
        # Create project
        project = workspace.create_project("integration-test-nmap")
        workspace.switch_project("integration-test-nmap")

        # Simulate Nmap scan results (in real test, would execute actual scan)
        nmap_results = {
            "scan_type": "nmap",
            "target": "scanme.nmap.org",
            "hosts": [
                {
                    "ip": "45.33.32.156",
                    "hostname": "scanme.nmap.org",
                    "state": "up",
                    "ports": [
                        {
                            "port": 22,
                            "protocol": "tcp",
                            "state": "open",
                            "service": "ssh",
                            "version": "OpenSSH 6.6.1p1",
                        },
                        {
                            "port": 80,
                            "protocol": "tcp",
                            "state": "open",
                            "service": "http",
                            "version": "Apache httpd 2.4.7",
                        },
                    ],
                }
            ],
        }

        # Store results in workspace
        for host_data in nmap_results["hosts"]:
            host = workspace.add_host(
                ip_address=host_data["ip"],
                hostname=host_data.get("hostname"),
                state=host_data.get("state", "unknown"),
            )

            for port_data in host_data.get("ports", []):
                workspace.add_port(
                    host_id=host.id,
                    port=port_data["port"],
                    protocol=port_data["protocol"],
                    state=port_data["state"],
                    service=port_data.get("service"),
                    version=port_data.get("version"),
                )

        # Verify hosts were stored
        hosts = workspace.query_hosts()
        assert len(hosts) == 1
        assert hosts[0].ip_address == "45.33.32.156"
        assert hosts[0].hostname == "scanme.nmap.org"

        # Verify ports were stored
        ports = workspace.query_ports(host_id=hosts[0].id)
        assert len(ports) == 2
        assert any(p.port == 22 and p.service == "ssh" for p in ports)
        assert any(p.port == 80 and p.service == "http" for p in ports)

    def test_nuclei_scan_stores_vulnerabilities(self, workspace):
        """Test that Nuclei scan results store vulnerabilities."""
        project = workspace.create_project("integration-test-nuclei")
        workspace.switch_project("integration-test-nuclei")

        # Add host first
        host = workspace.add_host(
            ip_address="192.168.1.100",
            hostname="test.example.com",
        )

        # Simulate Nuclei vulnerability findings
        nuclei_findings = [
            {
                "template_id": "CVE-2021-44228",
                "name": "Apache Log4j RCE",
                "severity": "critical",
                "description": "Remote code execution via JNDI injection",
                "matched_at": "http://test.example.com:8080",
            },
            {
                "template_id": "CVE-2021-3156",
                "name": "Sudo Heap Overflow",
                "severity": "high",
                "description": "Privilege escalation vulnerability",
                "matched_at": "ssh://test.example.com:22",
            },
        ]

        # Store vulnerabilities
        for finding in nuclei_findings:
            workspace.add_vulnerability(
                host_id=host.id,
                cve_id=finding["template_id"],
                title=finding["name"],
                severity=finding["severity"],
                description=finding["description"],
            )

        # Verify vulnerabilities were stored
        vulns = workspace.get_vulnerabilities(host_id=host.id)
        assert len(vulns) == 2
        assert any(v.cve_id == "CVE-2021-44228" and v.severity == "critical" for v in vulns)
        assert any(v.cve_id == "CVE-2021-3156" and v.severity == "high" for v in vulns)

    def test_workspace_query_after_scan(self, workspace):
        """Test querying workspace after multiple scans."""
        project = workspace.create_project("integration-test-query")
        workspace.switch_project("integration-test-query")

        # Populate workspace with scan results
        for i in range(3):
            host = workspace.add_host(
                ip_address=f"10.10.1.{i+1}",
                hostname=f"host{i+1}.test.com",
            )

            # Add SSH port
            workspace.add_port(
                host_id=host.id,
                port=22,
                protocol="tcp",
                state="open",
                service="ssh",
                version=f"OpenSSH 7.{i}",
            )

            # Add HTTP port to some hosts
            if i < 2:
                workspace.add_port(
                    host_id=host.id,
                    port=80,
                    protocol="tcp",
                    state="open",
                    service="http",
                )

        # Query: All hosts
        all_hosts = workspace.query_hosts()
        assert len(all_hosts) == 3

        # Query: Hosts with HTTP
        http_hosts = workspace.query_hosts_by_service("http")
        assert len(http_hosts) == 2

        # Query: Hosts with SSH
        ssh_hosts = workspace.query_hosts_by_service("ssh")
        assert len(ssh_hosts) == 3

    def test_workspace_statistics(self, workspace):
        """Test workspace statistics generation."""
        project = workspace.create_project("integration-test-stats")
        workspace.switch_project("integration-test-stats")

        # Add hosts and vulnerabilities
        for i in range(5):
            host = workspace.add_host(ip_address=f"10.10.1.{i+1}")

            # Add critical vuln to first 2 hosts
            if i < 2:
                workspace.add_vulnerability(
                    host_id=host.id,
                    cve_id=f"CVE-2021-{i}",
                    severity="critical",
                )

            # Add medium vuln to last 3 hosts
            if i >= 2:
                workspace.add_vulnerability(
                    host_id=host.id,
                    cve_id=f"CVE-2022-{i}",
                    severity="medium",
                )

        # Get statistics
        stats = workspace.get_statistics()

        assert stats["total_hosts"] == 5
        assert stats["total_vulnerabilities"] == 5
        assert stats["critical_vulns"] == 2
        assert stats["high_vulns"] == 0
        assert stats["medium_vulns"] == 3
