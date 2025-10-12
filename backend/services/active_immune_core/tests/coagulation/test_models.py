"""Tests for Coagulation Models

Tests data structures and enums for coagulation system.

Authors: MAXIMUS Team
Date: 2025-10-12
"""

import pytest
from datetime import datetime, timedelta

from coagulation.models import (
    Asset,
    BlastRadius,
    ContainmentResult,
    EnrichedThreat,
    FibrinMeshHealth,
    HealthCheck,
    HealthStatus,
    NeutralizedThreat,
    QuarantineLevel,
    RestoreResult,
    ThreatSeverity,
    ThreatSource,
    TrustLevel,
    ValidationResult,
)


class TestThreatSeverity:
    """Test ThreatSeverity enum"""

    def test_severity_levels(self):
        """Test all severity levels exist"""
        assert ThreatSeverity.LOW.value == "low"
        assert ThreatSeverity.MEDIUM.value == "medium"
        assert ThreatSeverity.HIGH.value == "high"
        assert ThreatSeverity.CRITICAL.value == "critical"
        assert ThreatSeverity.CATASTROPHIC.value == "catastrophic"

    def test_severity_comparison(self):
        """Test severity can be compared"""
        low = ThreatSeverity.LOW
        high = ThreatSeverity.HIGH
        assert low != high
        assert low == ThreatSeverity.LOW


class TestQuarantineLevel:
    """Test QuarantineLevel enum"""

    def test_quarantine_levels(self):
        """Test quarantine levels are ordered"""
        assert QuarantineLevel.NONE.value == 0
        assert QuarantineLevel.NETWORK.value == 1
        assert QuarantineLevel.HOST.value == 2
        assert QuarantineLevel.APPLICATION.value == 3
        assert QuarantineLevel.DATA.value == 4

    def test_quarantine_comparison(self):
        """Test quarantine levels can be compared by value"""
        assert QuarantineLevel.NETWORK.value < QuarantineLevel.HOST.value
        assert QuarantineLevel.DATA.value > QuarantineLevel.APPLICATION.value


class TestTrustLevel:
    """Test TrustLevel enum"""

    def test_trust_levels(self):
        """Test trust levels exist"""
        assert TrustLevel.UNTRUSTED.value == 0
        assert TrustLevel.LIMITED.value == 1
        assert TrustLevel.RESTRICTED.value == 2
        assert TrustLevel.CRITICAL.value == 3


class TestThreatSource:
    """Test ThreatSource dataclass"""

    def test_minimal_source(self):
        """Test source with only IP"""
        source = ThreatSource(ip="192.168.1.100")
        assert source.ip == "192.168.1.100"
        assert source.port is None
        assert source.hostname is None

    def test_full_source(self):
        """Test source with all fields"""
        source = ThreatSource(
            ip="10.0.0.50",
            port=8080,
            hostname="malicious.example.com",
            subnet="10.0.0.0/24",
            geolocation={"country": "XX", "city": "Unknown"},
        )
        assert source.ip == "10.0.0.50"
        assert source.port == 8080
        assert source.hostname == "malicious.example.com"
        assert source.subnet == "10.0.0.0/24"
        assert source.geolocation["country"] == "XX"


class TestBlastRadius:
    """Test BlastRadius dataclass"""

    def test_empty_blast_radius(self):
        """Test empty blast radius"""
        radius = BlastRadius()
        assert radius.affected_hosts == []
        assert radius.affected_zones == []
        assert radius.estimated_spread_rate == 0.0
        assert radius.max_impact_score == 0.0

    def test_blast_radius_with_data(self):
        """Test blast radius with data"""
        radius = BlastRadius(
            affected_hosts=["host1", "host2"],
            affected_zones=["DMZ", "APP"],
            estimated_spread_rate=2.5,
            max_impact_score=0.8,
        )
        assert len(radius.affected_hosts) == 2
        assert "DMZ" in radius.affected_zones
        assert radius.estimated_spread_rate == 2.5


class TestEnrichedThreat:
    """Test EnrichedThreat dataclass"""

    def test_minimal_threat(self):
        """Test threat with minimal fields"""
        source = ThreatSource(ip="1.2.3.4")
        threat = EnrichedThreat(
            threat_id="threat_001",
            source=source,
            severity=ThreatSeverity.HIGH,
            threat_type="malware",
        )
        assert threat.threat_id == "threat_001"
        assert threat.severity == ThreatSeverity.HIGH
        assert threat.threat_type == "malware"
        assert threat.confidence == 0.0

    def test_full_threat(self):
        """Test threat with all fields"""
        source = ThreatSource(ip="1.2.3.4")
        blast_radius = BlastRadius(affected_hosts=["host1"])
        threat = EnrichedThreat(
            threat_id="threat_002",
            source=source,
            severity=ThreatSeverity.CRITICAL,
            threat_type="intrusion",
            signature="ransomware_wannacry",
            ttps=["T1059", "T1027"],
            iocs={"md5": "abc123"},
            blast_radius=blast_radius,
            targeted_ports=[445, 139],
            compromised_credentials=["admin"],
            affected_hosts=["host1"],
            confidence=0.95,
            attribution="APT28",
        )
        assert threat.threat_id == "threat_002"
        assert len(threat.ttps) == 2
        assert 445 in threat.targeted_ports
        assert threat.confidence == 0.95
        assert threat.attribution == "APT28"


class TestContainmentResult:
    """Test ContainmentResult dataclass"""

    def test_successful_containment(self):
        """Test successful containment result"""
        result = ContainmentResult(
            status="CONTAINED",
            containment_type="primary",
            affected_zones=["DMZ"],
        )
        assert result.status == "CONTAINED"
        assert result.containment_type == "primary"
        assert isinstance(result.contained_at, datetime)


class TestNeutralizedThreat:
    """Test NeutralizedThreat dataclass"""

    def test_neutralized_threat(self):
        """Test neutralized threat"""
        source = ThreatSource(ip="1.2.3.4")
        original = EnrichedThreat(
            threat_id="threat_003",
            source=source,
            severity=ThreatSeverity.HIGH,
            threat_type="malware",
        )

        neutralized = NeutralizedThreat(
            threat_id="threat_003",
            original_threat=original,
            neutralization_method="cytotoxic_t",
            artifacts_collected=["memory_dump.bin"],
        )

        assert neutralized.threat_id == "threat_003"
        assert neutralized.neutralization_method == "cytotoxic_t"
        assert neutralized.forensics_required is True
        assert isinstance(neutralized.neutralized_at, datetime)


class TestAsset:
    """Test Asset dataclass"""

    def test_minimal_asset(self):
        """Test asset with minimal fields"""
        asset = Asset(
            id="asset_001",
            asset_type="host",
        )
        assert asset.id == "asset_001"
        assert asset.asset_type == "host"
        assert asset.zone == "unknown"
        assert asset.criticality == 1

    def test_full_asset(self):
        """Test asset with all fields"""
        asset = Asset(
            id="asset_002",
            asset_type="service",
            ip="10.0.1.50",
            hostname="api.example.com",
            zone="APPLICATION",
            criticality=5,
            business_impact=0.9,
            services=["api", "web"],
            data_stores=["postgres"],
            applications=["backend"],
        )
        assert asset.criticality == 5
        assert asset.business_impact == 0.9
        assert "api" in asset.services


class TestHealthCheck:
    """Test HealthCheck dataclass"""

    def test_passed_check(self):
        """Test passed health check"""
        check = HealthCheck(
            check_name="service_health",
            passed=True,
            details="All services responding",
        )
        assert check.passed is True
        assert check.check_name == "service_health"
        assert isinstance(check.timestamp, datetime)

    def test_failed_check(self):
        """Test failed health check"""
        check = HealthCheck(
            check_name="error_rates",
            passed=False,
            details="Error rate above threshold",
        )
        assert check.passed is False


class TestHealthStatus:
    """Test HealthStatus dataclass"""

    def test_healthy_status(self):
        """Test healthy asset status"""
        asset = Asset(id="asset_001", asset_type="host")
        check = HealthCheck(
            check_name="service_health", passed=True, details="OK"
        )
        status = HealthStatus(
            asset=asset,
            healthy=True,
            checks=[check],
        )
        assert status.healthy is True
        assert len(status.checks) == 1

    def test_unhealthy_status(self):
        """Test unhealthy asset status"""
        asset = Asset(id="asset_002", asset_type="host")
        check = HealthCheck(
            check_name="service_health", passed=False, details="Service down"
        )
        status = HealthStatus(
            asset=asset,
            healthy=False,
            checks=[check],
            unhealthy_reason="Service unavailable",
        )
        assert status.healthy is False
        assert status.unhealthy_reason == "Service unavailable"


class TestValidationResult:
    """Test ValidationResult dataclass"""

    def test_safe_validation(self):
        """Test safe validation result"""
        result = ValidationResult(
            safe_to_restore=True,
            checks={"malware": True, "backdoors": True},
        )
        assert result.safe_to_restore is True
        assert all(result.checks.values())

    def test_unsafe_validation(self):
        """Test unsafe validation result"""
        result = ValidationResult(
            safe_to_restore=False,
            checks={"malware": True, "backdoors": False},
            reason="Backdoors still present",
        )
        assert result.safe_to_restore is False
        assert result.reason == "Backdoors still present"


class TestRestoreResult:
    """Test RestoreResult dataclass"""

    def test_successful_restore(self):
        """Test successful restore result"""
        asset = Asset(id="asset_001", asset_type="host")
        result = RestoreResult(
            asset=asset,
            status="RESTORED",
        )
        assert result.status == "RESTORED"
        assert result.error is None

    def test_failed_restore(self):
        """Test failed restore result"""
        asset = Asset(id="asset_002", asset_type="service")
        result = RestoreResult(
            asset=asset,
            status="FAILED",
            error="Connection timeout",
        )
        assert result.status == "FAILED"
        assert result.error == "Connection timeout"


class TestFibrinMeshHealth:
    """Test FibrinMeshHealth dataclass"""

    def test_healthy_mesh(self):
        """Test healthy mesh status"""
        health = FibrinMeshHealth(
            mesh_id="mesh_001",
            effectiveness=0.95,
            zone_health={"status": "healthy"},
            traffic_health={"status": "healthy"},
            status="HEALTHY",
        )
        assert health.effectiveness == 0.95
        assert health.status == "HEALTHY"

    def test_degraded_mesh(self):
        """Test degraded mesh status"""
        health = FibrinMeshHealth(
            mesh_id="mesh_002",
            effectiveness=0.75,
            zone_health={"status": "degraded"},
            traffic_health={"status": "healthy"},
            status="DEGRADED",
        )
        assert health.effectiveness == 0.75
        assert health.status == "DEGRADED"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
