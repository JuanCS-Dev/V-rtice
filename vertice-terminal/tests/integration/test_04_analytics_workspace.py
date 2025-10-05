"""
Integration Tests: Analytics + Workspace
=========================================

Test that analytics components work with workspace data.
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile

from vertice.workspace import WorkspaceManager
from vertice.analytics import (
    BehavioralAnalytics,
    RiskScorer,
    RiskFactor,
    AnomalyType,
)


class TestAnalyticsWorkspaceIntegration:
    """Test analytics integration with workspace."""

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
    def analytics(self):
        """Create behavioral analytics instance."""
        return BehavioralAnalytics(use_backend=False)

    @pytest.fixture
    def scorer(self):
        """Create risk scorer instance."""
        return RiskScorer(use_backend=False)

    def test_risk_scoring_from_workspace_findings(self, workspace, scorer):
        """Test calculating risk scores from workspace vulnerability data."""
        project = workspace.create_project("risk-scoring-test")
        workspace.switch_project("risk-scoring-test")

        # Add host with vulnerabilities
        host = workspace.add_host(
            ip_address="10.10.1.100",
            hostname="critical-server.test.com",
        )

        # Add critical vulnerabilities
        workspace.add_vulnerability(
            host_id=host.id,
            cve_id="CVE-2021-44228",
            title="Log4Shell RCE",
            severity="critical",
            cvss_score=10.0,
        )

        workspace.add_vulnerability(
            host_id=host.id,
            cve_id="CVE-2020-1472",
            title="Zerologon",
            severity="critical",
            cvss_score=10.0,
        )

        # Get vulnerabilities from workspace
        vulns = host.vulnerabilities

        # Convert to risk factors
        risk_factors = []
        for vuln in vulns:
            factor = RiskFactor(
                name=f"Vulnerability: {vuln.cve_id}",
                category="vulnerability",
                score_impact=(vuln.cvss_score / 10.0) * 100,  # 0-100 scale
                weight=1.0,
                description=vuln.description or "",
                evidence={"cve_id": vuln.cve_id, "severity": vuln.severity},
            )
            risk_factors.append(factor)

        # Calculate risk score
        risk_score = scorer.calculate_risk_score(
            entity_id=f"host_{host.id}",
            entity_type="endpoint",
            risk_factors=risk_factors,
        )

        # Verify risk score
        assert risk_score.entity_id == f"host_{host.id}"
        assert risk_score.vulnerability_score == 100.0  # Max impact from CVSS 10
        assert risk_score.total_score > 0

    def test_behavioral_baseline_from_workspace_events(self, workspace, analytics):
        """Test learning behavioral baseline from workspace event data."""
        project = workspace.create_project("behavioral-test")
        workspace.switch_project("behavioral-test")

        # Simulate 30 days of normal login events stored in workspace
        historical_events = []
        now = datetime.now()

        for day in range(30):
            date = now - timedelta(days=day)

            # Normal pattern: login at 9am from office
            event = {
                "type": "login",
                "timestamp": date.replace(hour=9, minute=0).isoformat(),
                "source_ip": "192.168.1.100",
                "user": "analyst@test.com",
            }
            historical_events.append(event)

        # Learn baseline
        baseline = analytics.learn_baseline(
            entity_id="analyst@test.com",
            entity_type="user",
            historical_events=historical_events,
        )

        # Verify baseline was learned
        assert baseline.entity_id == "analyst@test.com"
        assert 9 in baseline.typical_login_hours
        assert "192.168.1.100" in baseline.typical_locations

        # Detect anomaly: unusual time
        unusual_event = {
            "type": "login",
            "timestamp": datetime.now().replace(hour=3).isoformat(),
            "source_ip": "192.168.1.100",
            "user": "analyst@test.com",
        }

        anomalies = analytics.detect_anomalies("analyst@test.com", unusual_event)

        # Should detect time anomaly
        assert len(anomalies) > 0
        assert any(a.anomaly_type == AnomalyType.LOGIN_TIME for a in anomalies)

    def test_workspace_enrichment_with_analytics(self, workspace, analytics, scorer):
        """Test enriching workspace data with analytics insights."""
        project = workspace.create_project("enrichment-test")
        workspace.switch_project("enrichment-test")

        # Add multiple hosts
        hosts = []
        for i in range(5):
            host = workspace.add_host(ip_address=f"10.10.1.{i+1}")
            hosts.append(host)

        # Add vulnerabilities to first 2 hosts (high risk)
        for host in hosts[:2]:
            workspace.add_vulnerability(
                host_id=host.id,
                cve_id="CVE-2021-44228",
                title="Log4Shell",
                severity="critical",
                cvss_score=10.0,
            )

        # Calculate risk scores for all hosts
        risk_scores = {}

        for host in hosts:
            vulns = host.vulnerabilities

            risk_factors = [
                RiskFactor(
                    name=f"Vuln: {v.cve_id}",
                    category="vulnerability",
                    score_impact=(v.cvss_score / 10.0) * 100,
                    weight=1.0,
                )
                for v in vulns
            ]

            if risk_factors:
                risk_score = scorer.calculate_risk_score(
                    entity_id=f"host_{host.id}",
                    entity_type="endpoint",
                    risk_factors=risk_factors,
                )
                risk_scores[host.id] = risk_score

        # Get high-risk hosts
        high_risk_hosts = [
            host_id
            for host_id, score in risk_scores.items()
            if score.total_score >= 20  # Risk threshold
        ]

        # Verify that first 2 hosts are high-risk
        assert len(high_risk_hosts) == 2
        assert hosts[0].id in high_risk_hosts
        assert hosts[1].id in high_risk_hosts

    def test_analytics_driven_prioritization(self, workspace, scorer):
        """Test using analytics to prioritize remediation efforts."""
        project = workspace.create_project("prioritization-test")
        workspace.switch_project("prioritization-test")

        # Create hosts with varying risk levels
        test_scenarios = [
            {
                "ip": "10.10.1.1",
                "vulns": [
                    {"cve": "CVE-2021-44228", "severity": "critical", "cvss": 10.0},
                    {"cve": "CVE-2020-1472", "severity": "critical", "cvss": 10.0},
                ],
            },
            {
                "ip": "10.10.1.2",
                "vulns": [
                    {"cve": "CVE-2021-3156", "severity": "high", "cvss": 7.8},
                ],
            },
            {
                "ip": "10.10.1.3",
                "vulns": [
                    {"cve": "CVE-2022-1234", "severity": "medium", "cvss": 5.0},
                ],
            },
        ]

        host_risk_scores = []

        for scenario in test_scenarios:
            host = workspace.add_host(ip_address=scenario["ip"])

            for vuln_data in scenario["vulns"]:
                workspace.add_vulnerability(
                    host_id=host.id,
                    cve_id=vuln_data["cve"],
                    title=vuln_data["cve"],
                    severity=vuln_data["severity"],
                    cvss_score=vuln_data["cvss"],
                )

            # Calculate risk
            vulns = host.vulnerabilities
            risk_factors = [
                RiskFactor(
                    name=v.cve_id,
                    category="vulnerability",
                    score_impact=(v.cvss_score / 10.0) * 100,
                    weight=1.0,
                )
                for v in vulns
            ]

            risk_score = scorer.calculate_risk_score(
                entity_id=f"host_{host.id}",
                entity_type="endpoint",
                risk_factors=risk_factors,
            )

            host_risk_scores.append((host, risk_score))

        # Sort by risk score (highest first)
        prioritized = sorted(
            host_risk_scores,
            key=lambda x: x[1].total_score,
            reverse=True,
        )

        # Verify prioritization
        assert prioritized[0][0].ip_address == "10.10.1.1"  # 2 critical vulns
        assert prioritized[1][0].ip_address == "10.10.1.2"  # 1 high vuln
        assert prioritized[2][0].ip_address == "10.10.1.3"  # 1 medium vuln
