"""
Reactive Fabric - Model Validation Tests.

Comprehensive test suite for all data models.
Validates Pydantic schemas, validators, and Phase 1 constraints.

Test Coverage:
- Model instantiation and validation
- Required field enforcement
- Enum value validation
- Custom validator logic
- Phase 1 safety constraints
- JSON serialization
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from backend.security.offensive.reactive_fabric.models import (
    # Threat models
    ThreatSeverity,
    ThreatCategory,
    DetectionSource,
    ThreatIndicator,
    MITREMapping,
    ThreatEvent,
    AssetType,
    AssetInteractionLevel,
    AssetStatus,
    AssetCredibility,
    AssetTelemetry,
    DeceptionAsset,
    AssetInteractionEvent,
    # Intelligence models
    IntelligenceType,
    IntelligenceConfidence,
    IntelligenceSource,
    APTGroup,
    TTPPattern,
    IntelligenceReport,
    IntelligenceMetrics,
    # HITL models
    ActionLevel,
    ActionType,
    DecisionStatus,
    DecisionRationale,
    AuthorizationRequest,
    AuthorizationDecision,
    ApproverProfile,
)


class TestThreatModels:
    """Test suite for threat event models."""
    
    def test_threat_indicator_valid_ioc_types(self):
        """Validate IoC type enforcement."""
        # Valid types
        for ioc_type in ['ip', 'domain', 'hash', 'url', 'email', 'file']:
            indicator = ThreatIndicator(
                type=ioc_type,
                value="test_value",
                confidence=0.85
            )
            assert indicator.type == ioc_type.lower()
    
    def test_threat_indicator_invalid_ioc_type(self):
        """Reject invalid IoC types."""
        with pytest.raises(ValueError):
            ThreatIndicator(
                type="invalid_type",
                value="test",
                confidence=0.5
            )
    
    def test_mitre_mapping_creation(self):
        """Validate MITRE ATT&CK mapping."""
        mapping = MITREMapping(
            tactic_id="TA0001",
            tactic_name="Initial Access",
            technique_id="T1190",
            technique_name="Exploit Public-Facing Application",
            confidence=0.9
        )
        assert mapping.tactic_id == "TA0001"
        assert mapping.confidence == 0.9
    
    def test_threat_event_creation_minimal(self):
        """Create threat event with minimal required fields."""
        event = ThreatEvent(
            source=DetectionSource.HONEYPOT,
            severity=ThreatSeverity.HIGH,
            category=ThreatCategory.INITIAL_ACCESS,
            title="SSH Brute Force Attempt",
            description="Multiple failed authentication attempts",
            source_ip="192.168.1.100",
            destination_ip="10.0.0.5"
        )
        assert event.id is not None
        assert event.timestamp is not None
        assert event.is_analyzed is False
    
    def test_threat_event_with_full_context(self):
        """Create threat event with complete intelligence context."""
        indicator = ThreatIndicator(
            type="ip",
            value="192.168.1.100",
            confidence=0.95
        )
        
        mitre = MITREMapping(
            tactic_id="TA0006",
            tactic_name="Credential Access",
            technique_id="T1110",
            technique_name="Brute Force",
            sub_technique_id="T1110.001",
            confidence=0.9
        )
        
        event = ThreatEvent(
            source=DetectionSource.HONEYPOT,
            severity=ThreatSeverity.HIGH,
            category=ThreatCategory.CREDENTIAL_ACCESS,
            title="SSH Brute Force with Credential Stuffing",
            description="Observed systematic credential testing",
            source_ip="192.168.1.100",
            source_port=54321,
            destination_ip="10.0.0.5",
            destination_port=22,
            protocol="tcp",
            indicators=[indicator],
            mitre_mapping=mitre,
            metadata={"attack_duration_seconds": 300}
        )
        
        assert len(event.indicators) == 1
        assert event.mitre_mapping.technique_id == "T1110"
        assert event.metadata["attack_duration_seconds"] == 300
    
    def test_threat_event_json_serialization(self):
        """Validate JSON serialization of threat events."""
        event = ThreatEvent(
            source=DetectionSource.IDS,
            severity=ThreatSeverity.MEDIUM,
            category=ThreatCategory.RECONNAISSANCE,
            title="Port Scan Detected",
            description="Sequential port scanning observed",
            source_ip="10.0.0.1",
            destination_ip="10.0.0.100"
        )
        
        json_data = event.json()
        assert isinstance(json_data, str)
        assert "Port Scan Detected" in json_data


class TestDeceptionModels:
    """Test suite for deception asset models."""
    
    def test_asset_credibility_creation(self):
        """Validate asset credibility tracking."""
        credibility = AssetCredibility(
            realism_score=0.85,
            service_authenticity=0.9,
            data_authenticity=0.8,
            network_integration=0.85,
            assessment_method="Manual review + automated checks"
        )
        assert credibility.realism_score == 0.85
        assert credibility.last_assessment is not None
    
    def test_asset_telemetry_configuration(self):
        """Validate telemetry configuration options."""
        telemetry = AssetTelemetry(
            capture_network_traffic=True,
            capture_commands=True,
            capture_file_operations=True,
            log_retention_days=90,
            storage_location="/var/log/honeypot"
        )
        assert telemetry.capture_commands is True
        assert telemetry.log_retention_days == 90
    
    def test_deception_asset_creation_low_interaction(self):
        """Create LOW interaction honeypot (Phase 1 compliant)."""
        credibility = AssetCredibility(
            realism_score=0.8,
            service_authenticity=0.85,
            data_authenticity=0.75,
            network_integration=0.8,
            assessment_method="Automated"
        )
        
        telemetry = AssetTelemetry(
            storage_location="/var/log/honeypot"
        )
        
        asset = DeceptionAsset(
            name="SSH-Honeypot-01",
            asset_type=AssetType.HONEYPOT_SSH,
            interaction_level=AssetInteractionLevel.LOW,
            ip_address="10.0.1.10",
            port=22,
            network_segment="DMZ-Honeypot",
            credibility=credibility,
            telemetry=telemetry,
            deployed_by="security_team"
        )
        
        assert asset.interaction_level == AssetInteractionLevel.LOW
        assert asset.status == AssetStatus.ACTIVE
        assert asset.total_interactions == 0
    
    def test_deception_asset_high_interaction_prohibited(self):
        """Enforce Phase 1 constraint: HIGH interaction prohibited."""
        credibility = AssetCredibility(
            realism_score=0.9,
            service_authenticity=0.9,
            data_authenticity=0.9,
            network_integration=0.9,
            assessment_method="Full system"
        )
        
        telemetry = AssetTelemetry(
            storage_location="/var/log/honeypot"
        )
        
        with pytest.raises(ValueError) as exc_info:
            DeceptionAsset(
                name="Full-System-Honeypot",
                asset_type=AssetType.HONEYPOT_SSH,
                interaction_level=AssetInteractionLevel.HIGH,
                ip_address="10.0.1.20",
                port=22,
                network_segment="Isolated",
                credibility=credibility,
                telemetry=telemetry,
                deployed_by="security_team"
            )
        
        assert "HIGH interaction assets prohibited" in str(exc_info.value)
    
    def test_asset_interaction_event_creation(self):
        """Track attacker interaction with deception asset."""
        asset_id = uuid4()
        
        interaction = AssetInteractionEvent(
            asset_id=asset_id,
            source_ip="192.168.1.50",
            source_port=45678,
            interaction_type="connection",
            command="ls -la",
            payload="SSH connection attempt",
            indicators_extracted=["192.168.1.50"],
            mitre_technique="T1078"
        )
        
        assert interaction.asset_id == asset_id
        assert interaction.command == "ls -la"


class TestIntelligenceModels:
    """Test suite for intelligence report models."""
    
    def test_apt_group_creation(self):
        """Create APT group profile."""
        apt = APTGroup(
            name="APT28",
            aliases=["Fancy Bear", "Sofacy"],
            attribution_confidence=IntelligenceConfidence.HIGH,
            origin_country="Russia",
            target_sectors=["Government", "Military", "Media"],
            known_ttps=["T1566.001", "T1078", "T1071"]
        )
        
        assert apt.name == "APT28"
        assert "Fancy Bear" in apt.aliases
        assert len(apt.known_ttps) == 3
    
    def test_ttp_pattern_creation(self):
        """Create TTP pattern for threat tracking."""
        pattern = TTPPattern(
            name="Credential Stuffing Campaign",
            description="Systematic credential testing across services",
            mitre_tactics=["TA0006"],
            mitre_techniques=["T1110.004"],
            behavioral_indicators=[
                "Sequential authentication attempts",
                "Common usernames tested",
                "Short intervals between attempts"
            ],
            confidence=IntelligenceConfidence.HIGH,
            observation_count=15
        )
        
        assert pattern.name == "Credential Stuffing Campaign"
        assert len(pattern.behavioral_indicators) == 3
    
    def test_intelligence_report_creation(self):
        """Create comprehensive intelligence report."""
        apt = APTGroup(
            name="APT29",
            aliases=["Cozy Bear"],
            attribution_confidence=IntelligenceConfidence.MEDIUM,
            known_ttps=["T1566.002", "T1059.001"]
        )
        
        pattern = TTPPattern(
            name="Spearphishing with Malicious Attachment",
            description="Targeted phishing campaign",
            mitre_tactics=["TA0001"],
            mitre_techniques=["T1566.001"],
            confidence=IntelligenceConfidence.HIGH
        )
        
        report = IntelligenceReport(
            report_number="INT-2024-001",
            title="APT29 Spearphishing Campaign Analysis",
            intelligence_type=IntelligenceType.OPERATIONAL,
            confidence=IntelligenceConfidence.HIGH,
            executive_summary="Observed coordinated phishing campaign",
            technical_analysis="Detailed technical indicators and TTP analysis",
            threat_actor=apt,
            ttp_patterns=[pattern],
            indicators_of_compromise=["evil@phish.com", "malicious.doc"],
            sources=[IntelligenceSource.INTERNAL_TELEMETRY, IntelligenceSource.OSINT],
            defensive_recommendations=["Deploy email filtering rules", "User awareness training"],
            analysis_period_start=datetime.utcnow() - timedelta(days=30),
            analysis_period_end=datetime.utcnow(),
            generated_by="Analyst John Doe"
        )
        
        assert report.report_number == "INT-2024-001"
        assert report.threat_actor.name == "APT29"
        assert len(report.ttp_patterns) == 1
        assert len(report.sources) == 2
    
    def test_intelligence_metrics_tracking(self):
        """Track Phase 1 success metrics."""
        metrics = IntelligenceMetrics(
            total_threat_events=250,
            unique_source_ips=75,
            unique_apt_groups_observed=3,
            novel_ttps_discovered=5,
            ttp_patterns_identified=12,
            reports_generated=8,
            tactical_reports=4,
            operational_reports=3,
            strategic_reports=1,
            detection_rules_created=15,
            hunt_hypotheses_validated=6,
            average_confidence_score=0.82,
            active_deception_assets=10,
            assets_with_interactions=7,
            average_asset_credibility=0.85
        )
        
        assert metrics.novel_ttps_discovered == 5
        assert metrics.detection_rules_created == 15


class TestHITLModels:
    """Test suite for human-in-the-loop models."""
    
    def test_authorization_request_level_1_passive(self):
        """Create Level 1 passive action (auto-approved)."""
        request = AuthorizationRequest(
            action_level=ActionLevel.LEVEL_1_PASSIVE,
            action_type=ActionType.COLLECT_TELEMETRY,
            action_description="Enable network traffic capture on honeypot",
            action_target="SSH-Honeypot-01",
            threat_context="New attacker detected",
            expected_outcome="Capture attack TTPs",
            risk_level="LOW",
            potential_impact=["Increased storage usage"],
            containment_measures=["Isolated network segment"],
            rollback_plan="Disable capture if storage fills",
            requested_by="telemetry_service",
            assigned_to="auto_approval",
            decision_deadline=datetime.utcnow() + timedelta(hours=1)
        )
        
        assert request.action_level == ActionLevel.LEVEL_1_PASSIVE
        assert request.decision_status == DecisionStatus.PENDING
    
    def test_authorization_request_level_3_deceptive(self):
        """Create Level 3 deceptive action (requires HITL)."""
        request = AuthorizationRequest(
            action_level=ActionLevel.LEVEL_3_DECEPTIVE,
            action_type=ActionType.DEPLOY_DECEPTION_ASSET,
            action_description="Deploy new SMB honeypot",
            action_target="Production DMZ",
            threat_context="Increase in SMB reconnaissance",
            expected_outcome="Capture SMB exploitation attempts",
            risk_level="MEDIUM",
            potential_impact=["Network exposure", "Attacker engagement"],
            containment_measures=["Isolated VLAN", "Strict firewall rules"],
            rollback_plan="Immediate shutdown and network isolation",
            requested_by="security_analyst",
            assigned_to="security_manager",
            decision_deadline=datetime.utcnow() + timedelta(hours=4)
        )
        
        assert request.action_level == ActionLevel.LEVEL_3_DECEPTIVE
        assert request.risk_level == "MEDIUM"
    
    def test_authorization_request_level_4_prohibited(self):
        """Enforce Phase 1 constraint: Level 4 offensive actions prohibited."""
        with pytest.raises(ValueError) as exc_info:
            AuthorizationRequest(
                action_level=ActionLevel.LEVEL_4_OFFENSIVE,
                action_type=ActionType.COUNTER_EXPLOIT,
                action_description="Deploy counter-exploit",
                action_target="Attacker infrastructure",
                threat_context="Active attack",
                expected_outcome="Disrupt attacker operations",
                risk_level="HIGH",
                potential_impact=["Legal liability", "Escalation"],
                containment_measures=["None"],
                rollback_plan="None",
                requested_by="system",
                assigned_to="manager",
                decision_deadline=datetime.utcnow() + timedelta(hours=1)
            )
        
        assert "Level 4 offensive actions prohibited" in str(exc_info.value)
    
    def test_authorization_decision_creation(self):
        """Create authorization decision with rationale."""
        request_id = uuid4()
        
        rationale = DecisionRationale(
            reasoning="Asset deployment justified by increased SMB scanning activity",
            risk_assessment="MEDIUM risk acceptable with proper isolation",
            alternative_considered="Could use existing honeypots, but need SMB coverage",
            lessons_learned="Need faster deployment process for threat response"
        )
        
        decision = AuthorizationDecision(
            request_id=request_id,
            decision_status=DecisionStatus.APPROVED,
            decided_by="security_manager_jane",
            decision_rationale=rationale
        )
        
        assert decision.decision_status == DecisionStatus.APPROVED
        assert decision.decided_by == "security_manager_jane"
    
    def test_authorization_decision_cannot_be_pending(self):
        """Prevent submitting PENDING as final decision."""
        request_id = uuid4()
        
        rationale = DecisionRationale(
            reasoning="Test",
            risk_assessment="Test"
        )
        
        with pytest.raises(ValueError):
            AuthorizationDecision(
                request_id=request_id,
                decision_status=DecisionStatus.PENDING,
                decided_by="user",
                decision_rationale=rationale
            )
    
    def test_approver_profile_creation(self):
        """Create human approver profile with authorization scope."""
        approver = ApproverProfile(
            username="security_manager_jane",
            full_name="Jane Doe",
            email="jane.doe@company.com",
            authorized_levels=[ActionLevel.LEVEL_1_PASSIVE, ActionLevel.LEVEL_2_ADAPTIVE, ActionLevel.LEVEL_3_DECEPTIVE],
            authorized_action_types=[
                ActionType.DEPLOY_DECEPTION_ASSET,
                ActionType.MODIFY_HONEYPOT_RESPONSE,
                ActionType.UPDATE_FIREWALL_RULE
            ],
            max_risk_level="HIGH",
            security_clearance="SECRET",
            training_completed=["Deception Operations", "Risk Management"],
            certification_date=datetime.utcnow() - timedelta(days=90),
            recertification_due=datetime.utcnow() + timedelta(days=275),
            escalation_contact="ciso@company.com"
        )
        
        assert len(approver.authorized_levels) == 3
        assert approver.max_risk_level == "HIGH"
        assert ActionLevel.LEVEL_4_OFFENSIVE not in approver.authorized_levels


def test_all_enums_have_valid_values():
    """Validate all enum definitions."""
    # Test enum instantiation
    assert ThreatSeverity.CRITICAL == "critical"
    assert ThreatCategory.RECONNAISSANCE == "reconnaissance"
    assert DetectionSource.HONEYPOT == "honeypot"
    assert AssetType.HONEYPOT_SSH == "honeypot_ssh"
    assert AssetInteractionLevel.LOW == "low"
    assert IntelligenceType.TACTICAL == "tactical"
    assert IntelligenceConfidence.HIGH == "high"
    assert ActionLevel.LEVEL_1_PASSIVE == "level_1_passive"
    assert ActionType.COLLECT_TELEMETRY == "collect_telemetry"
    assert DecisionStatus.APPROVED == "approved"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
