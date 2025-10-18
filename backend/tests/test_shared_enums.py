"""
Test suite for backend/shared/enums.py
Tests all enum classes for value integrity and string behavior.
"""

import pytest
from enum import Enum

from backend.shared.enums import (
    # Service & System
    ServiceStatus,
    AnalysisStatus,
    ScanStatus,
    # Threat & Security
    ThreatLevel,
    ThreatType,
    MalwareFamily,
    AttackTactic,
    AttackTechnique,
    # Incident Response
    IncidentStatus,
    AlertPriority,
    EvidenceType,
    # Asset & Network
    AssetType,
    ProtocolType,
    IPVersion,
    # Data Handling
    DataClassification,
    ComplianceFramework,
    # User & Auth
    UserRole,
    Permission,
    # Analysis
    AnalysisEngine,
    ConfidenceLevel,
    DetectionMethod,
    # Automation
    AutomationAction,
    QueuePriority,
    # OSINT
    OSINTSource,
    ReputationScore,
    # Monitoring
    LogLevel,
    MetricType,
    ResponseStatus,
)


class TestServiceSystemEnums:
    """Test service and system status enums."""

    def test_service_status_values(self):
        """Test ServiceStatus enum values."""
        assert ServiceStatus.HEALTHY.value == "healthy"
        assert ServiceStatus.DEGRADED.value == "degraded"
        assert ServiceStatus.UNHEALTHY.value == "unhealthy"
        assert ServiceStatus.STARTING.value == "starting"
        assert ServiceStatus.STOPPING.value == "stopping"
        assert ServiceStatus.DOWN.value == "down"
        assert ServiceStatus.MAINTENANCE.value == "maintenance"
        assert ServiceStatus.UNKNOWN.value == "unknown"

    def test_service_status_is_string(self):
        """Test ServiceStatus is string-based."""
        assert isinstance(ServiceStatus.HEALTHY, str)
        assert isinstance(ServiceStatus.HEALTHY, Enum)

    def test_analysis_status_values(self):
        """Test AnalysisStatus enum values."""
        assert AnalysisStatus.PENDING.value == "pending"
        assert AnalysisStatus.QUEUED.value == "queued"
        assert AnalysisStatus.RUNNING.value == "running"
        assert AnalysisStatus.COMPLETED.value == "completed"
        assert AnalysisStatus.FAILED.value == "failed"
        assert AnalysisStatus.CANCELLED.value == "cancelled"
        assert AnalysisStatus.TIMEOUT.value == "timeout"
        assert AnalysisStatus.PARTIAL.value == "partial"

    def test_scan_status_values(self):
        """Test ScanStatus enum values."""
        assert ScanStatus.PENDING.value == "pending"
        assert ScanStatus.SCHEDULED.value == "scheduled"
        assert ScanStatus.RUNNING.value == "running"
        assert ScanStatus.COMPLETED.value == "completed"
        assert ScanStatus.FAILED.value == "failed"
        assert ScanStatus.CANCELLED.value == "cancelled"
        assert ScanStatus.PAUSED.value == "paused"
        assert ScanStatus.RESUMING.value == "resuming"


class TestThreatSecurityEnums:
    """Test threat and security enums."""

    def test_threat_level_values(self):
        """Test ThreatLevel enum values."""
        assert ThreatLevel.CRITICAL.value == "critical"
        assert ThreatLevel.HIGH.value == "high"
        assert ThreatLevel.MEDIUM.value == "medium"
        assert ThreatLevel.LOW.value == "low"
        assert ThreatLevel.INFO.value == "info"
        assert ThreatLevel.UNKNOWN.value == "unknown"

    def test_threat_type_values(self):
        """Test ThreatType enum values."""
        assert ThreatType.MALWARE.value == "malware"
        assert ThreatType.RANSOMWARE.value == "ransomware"
        assert ThreatType.PHISHING.value == "phishing"
        assert ThreatType.APT.value == "apt"
        assert ThreatType.ZERO_DAY.value == "zero_day"
        assert ThreatType.DDOS.value == "ddos"
        assert ThreatType.SQL_INJECTION.value == "sql_injection"
        assert ThreatType.XSS.value == "xss"

    def test_malware_family_values(self):
        """Test MalwareFamily enum values."""
        assert MalwareFamily.TROJAN.value == "trojan"
        assert MalwareFamily.WORM.value == "worm"
        assert MalwareFamily.ROOTKIT.value == "rootkit"
        assert MalwareFamily.RANSOMWARE.value == "ransomware"
        assert MalwareFamily.RAT.value == "rat"
        assert MalwareFamily.CRYPTOMINER.value == "cryptominer"

    def test_attack_tactic_mitre_alignment(self):
        """Test AttackTactic MITRE ATT&CK alignment."""
        assert AttackTactic.RECONNAISSANCE.value == "reconnaissance"
        assert AttackTactic.INITIAL_ACCESS.value == "initial_access"
        assert AttackTactic.EXECUTION.value == "execution"
        assert AttackTactic.PERSISTENCE.value == "persistence"
        assert AttackTactic.PRIVILEGE_ESCALATION.value == "privilege_escalation"
        assert AttackTactic.CREDENTIAL_ACCESS.value == "credential_access"
        assert AttackTactic.EXFILTRATION.value == "exfiltration"
        assert AttackTactic.IMPACT.value == "impact"

    def test_attack_technique_values(self):
        """Test AttackTechnique enum values."""
        assert AttackTechnique.T1566_PHISHING.value == "T1566"
        assert AttackTechnique.T1190_EXPLOIT_PUBLIC_APP.value == "T1190"
        assert AttackTechnique.T1059_COMMAND_SCRIPTING.value == "T1059"
        assert AttackTechnique.T1486_DATA_ENCRYPTED_IMPACT.value == "T1486"


class TestIncidentResponseEnums:
    """Test incident response enums."""

    def test_incident_status_values(self):
        """Test IncidentStatus enum values."""
        assert IncidentStatus.NEW.value == "new"
        assert IncidentStatus.TRIAGED.value == "triaged"
        assert IncidentStatus.INVESTIGATING.value == "investigating"
        assert IncidentStatus.CONTAINED.value == "contained"
        assert IncidentStatus.RESOLVED.value == "resolved"
        assert IncidentStatus.CLOSED.value == "closed"

    def test_alert_priority_sla_structure(self):
        """Test AlertPriority enum values."""
        assert AlertPriority.P0_CRITICAL.value == "p0_critical"
        assert AlertPriority.P1_HIGH.value == "p1_high"
        assert AlertPriority.P2_MEDIUM.value == "p2_medium"
        assert AlertPriority.P3_LOW.value == "p3_low"
        assert AlertPriority.P4_INFO.value == "p4_info"

    def test_evidence_type_values(self):
        """Test EvidenceType enum values."""
        assert EvidenceType.NETWORK_TRAFFIC.value == "network_traffic"
        assert EvidenceType.SYSTEM_LOG.value == "system_log"
        assert EvidenceType.MEMORY_DUMP.value == "memory_dump"
        assert EvidenceType.PACKET_CAPTURE.value == "packet_capture"
        assert EvidenceType.IOC.value == "ioc"


class TestAssetNetworkEnums:
    """Test asset and network enums."""

    def test_asset_type_values(self):
        """Test AssetType enum values."""
        assert AssetType.SERVER.value == "server"
        assert AssetType.WORKSTATION.value == "workstation"
        assert AssetType.CONTAINER.value == "container"
        assert AssetType.VIRTUAL_MACHINE.value == "virtual_machine"
        assert AssetType.CLOUD_INSTANCE.value == "cloud_instance"

    def test_protocol_type_values(self):
        """Test ProtocolType enum values."""
        assert ProtocolType.TCP.value == "tcp"
        assert ProtocolType.HTTP.value == "http"
        assert ProtocolType.HTTPS.value == "https"
        assert ProtocolType.DNS.value == "dns"
        assert ProtocolType.SSH.value == "ssh"
        assert ProtocolType.WEBSOCKET.value == "websocket"

    def test_ip_version_values(self):
        """Test IPVersion enum values."""
        assert IPVersion.IPV4.value == "ipv4"
        assert IPVersion.IPV6.value == "ipv6"


class TestDataHandlingEnums:
    """Test data classification enums."""

    def test_data_classification_values(self):
        """Test DataClassification enum values."""
        assert DataClassification.PUBLIC.value == "public"
        assert DataClassification.INTERNAL.value == "internal"
        assert DataClassification.CONFIDENTIAL.value == "confidential"
        assert DataClassification.RESTRICTED.value == "restricted"

    def test_compliance_framework_values(self):
        """Test ComplianceFramework enum values (if exists)."""
        if hasattr(ComplianceFramework, "GDPR"):
            assert ComplianceFramework.GDPR.value == "gdpr"


class TestUserAuthEnums:
    """Test user and authentication enums."""

    def test_user_role_values(self):
        """Test UserRole enum values."""
        values = [m.value for m in UserRole]
        assert "admin" in values or "ADMIN" in values

    def test_permission_values(self):
        """Test Permission enum values (basic check)."""
        assert isinstance(list(Permission)[0], str)


class TestAnalysisEnums:
    """Test analysis engine enums."""

    def test_analysis_engine_values(self):
        """Test AnalysisEngine enum values (basic check)."""
        engines = list(AnalysisEngine)
        assert len(engines) > 0
        assert isinstance(engines[0], str)

    def test_confidence_level_values(self):
        """Test ConfidenceLevel enum values."""
        assert ConfidenceLevel.HIGH.value == "high"
        assert ConfidenceLevel.MEDIUM.value == "medium"
        assert ConfidenceLevel.LOW.value == "low"

    def test_detection_method_values(self):
        """Test DetectionMethod enum values (basic check)."""
        methods = list(DetectionMethod)
        assert len(methods) > 0


class TestAutomationEnums:
    """Test automation enums."""

    def test_automation_action_values(self):
        """Test AutomationAction enum values (basic check)."""
        actions = list(AutomationAction)
        assert len(actions) > 0
        assert isinstance(actions[0], str)

    def test_queue_priority_values(self):
        """Test QueuePriority enum values (basic check)."""
        priorities = list(QueuePriority)
        assert len(priorities) > 0


class TestOSINTEnums:
    """Test OSINT enums."""

    def test_osint_source_values(self):
        """Test OSINTSource enum values (basic check)."""
        sources = list(OSINTSource)
        assert len(sources) > 0
        assert isinstance(sources[0], str)

    def test_reputation_score_values(self):
        """Test ReputationScore enum values (basic check)."""
        scores = list(ReputationScore)
        assert len(scores) > 0


class TestMonitoringEnums:
    """Test monitoring and logging enums."""

    def test_log_level_values(self):
        """Test LogLevel enum values."""
        levels = [m.value for m in LogLevel]
        assert any("debug" in level.lower() or "DEBUG" in level for level in levels)

    def test_metric_type_values(self):
        """Test MetricType enum values (basic check)."""
        metrics = list(MetricType)
        assert len(metrics) > 0

    def test_response_status_values(self):
        """Test ResponseStatus enum values (basic check)."""
        statuses = list(ResponseStatus)
        assert len(statuses) > 0


class TestEnumCommonBehavior:
    """Test common enum behaviors and patterns."""

    def test_all_enums_are_str_based(self):
        """Test that all enums extend str."""
        enums = [
            ServiceStatus,
            ThreatLevel,
            IncidentStatus,
            AssetType,
            UserRole,
        ]
        for enum_class in enums:
            for member in enum_class:
                assert isinstance(member, str)
                assert isinstance(member, Enum)

    def test_enum_value_uniqueness(self):
        """Test that enum values are unique within their class."""
        enums_to_test = [
            ServiceStatus,
            ThreatLevel,
            MalwareFamily,
            ProtocolType,
        ]
        for enum_class in enums_to_test:
            values = [member.value for member in enum_class]
            assert len(values) == len(set(values)), f"Duplicate values in {enum_class.__name__}"

    def test_enum_name_consistency(self):
        """Test that enum names match expected patterns."""
        assert ThreatLevel.CRITICAL.name == "CRITICAL"
        assert ServiceStatus.HEALTHY.name == "HEALTHY"

    def test_enum_json_serialization(self):
        """Test that enum values can be used in JSON serialization."""
        import json

        data = {
            "status": ServiceStatus.HEALTHY.value,
            "threat": ThreatLevel.HIGH.value,
            "asset": AssetType.SERVER.value,
        }
        json_str = json.dumps(data)
        loaded = json.loads(json_str)
        
        assert loaded["status"] == "healthy"
        assert loaded["threat"] == "high"
        assert loaded["asset"] == "server"

    def test_enum_comparison(self):
        """Test enum comparison behavior."""
        assert ServiceStatus.HEALTHY == ServiceStatus.HEALTHY
        assert ServiceStatus.HEALTHY != ServiceStatus.DEGRADED
        
        # Test string comparison
        assert ServiceStatus.HEALTHY == "healthy"
        assert ServiceStatus.HEALTHY.value == "healthy"

    def test_enum_iteration(self):
        """Test that enums can be iterated."""
        status_list = list(ServiceStatus)
        assert len(status_list) >= 8
        assert ServiceStatus.HEALTHY in status_list

    def test_enum_membership(self):
        """Test enum membership checks."""
        assert "healthy" in [s.value for s in ServiceStatus]
        assert "invalid" not in [s.value for s in ServiceStatus]
