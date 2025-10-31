"""
Tests for unified event schemas.

NO MOCKS, NO PLACEHOLDERS, NO TODOS.

Authors: Juan & Claude
Version: 1.0.0
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from backend.shared.messaging.event_schemas import (
    EventBase,
    EventPriority,
    EventSource,
    HomeostaticStateEvent,
    ImmuneResponseEvent,
    SeverityLevel,
    ThreatDetectionEvent,
)


class TestEventBase:
    """Test EventBase schema"""

    def test_event_base_minimal(self):
        """Test EventBase with minimal fields"""
        event = EventBase(
            event_type="test.event",
            source_service=EventSource.MAXIMUS_CORE,
        )

        assert event.event_id is not None
        assert event.event_type == "test.event"
        assert event.source_service == EventSource.MAXIMUS_CORE
        assert event.priority == EventPriority.NORMAL
        assert isinstance(event.timestamp, datetime)

    def test_event_base_full(self):
        """Test EventBase with all fields"""
        event = EventBase(
            event_type="test.event",
            source_service=EventSource.MONITORING,
            priority=EventPriority.HIGH,
            correlation_id="corr-123",
            metadata={"key": "value"},
        )

        assert event.priority == EventPriority.HIGH
        assert event.correlation_id == "corr-123"
        assert event.metadata == {"key": "value"}


class TestThreatDetectionEvent:
    """Test ThreatDetectionEvent schema"""

    def test_threat_detection_minimal(self):
        """Test ThreatDetectionEvent with minimal fields"""
        event = ThreatDetectionEvent(
            honeypot_id="hp_001",
            honeypot_type="ssh",
            attacker_ip="1.2.3.4",
            attack_type="brute_force",
            severity=SeverityLevel.HIGH,
        )

        assert event.event_type == "threat.detected"
        assert event.source_service == EventSource.REACTIVE_FABRIC
        assert event.honeypot_id == "hp_001"
        assert event.attacker_ip == "1.2.3.4"
        assert event.severity == SeverityLevel.HIGH
        assert event.confidence == 1.0

    def test_threat_detection_full(self):
        """Test ThreatDetectionEvent with all fields"""
        event = ThreatDetectionEvent(
            honeypot_id="hp_002",
            honeypot_type="http",
            attacker_ip="10.0.0.1",
            attacker_port=54321,
            attack_type="sql_injection",
            severity=SeverityLevel.CRITICAL,
            ttps=["T1190", "T1059"],
            iocs={
                "ips": ["10.0.0.1"],
                "domains": ["evil.com"],
                "hashes": ["abc123"],
            },
            confidence=0.95,
            attack_payload="' OR 1=1--",
            attack_commands=["whoami", "cat /etc/passwd"],
            session_duration=120.5,
        )

        assert event.attacker_port == 54321
        assert len(event.ttps) == 2
        assert "ips" in event.iocs
        assert event.confidence == 0.95
        assert event.attack_payload is not None

    def test_threat_detection_confidence_validation(self):
        """Test confidence score validation"""
        # Valid confidence
        event = ThreatDetectionEvent(
            honeypot_id="hp_001",
            honeypot_type="ssh",
            attacker_ip="1.2.3.4",
            attack_type="brute_force",
            severity=SeverityLevel.HIGH,
            confidence=0.5,
        )
        assert event.confidence == 0.5

        # Invalid confidence (too high)
        with pytest.raises(ValidationError):
            ThreatDetectionEvent(
                honeypot_id="hp_001",
                honeypot_type="ssh",
                attacker_ip="1.2.3.4",
                attack_type="brute_force",
                severity=SeverityLevel.HIGH,
                confidence=1.5,
            )

        # Invalid confidence (negative)
        with pytest.raises(ValidationError):
            ThreatDetectionEvent(
                honeypot_id="hp_001",
                honeypot_type="ssh",
                attacker_ip="1.2.3.4",
                attack_type="brute_force",
                severity=SeverityLevel.HIGH,
                confidence=-0.1,
            )


class TestImmuneResponseEvent:
    """Test ImmuneResponseEvent schema"""

    def test_immune_response_minimal(self):
        """Test ImmuneResponseEvent with minimal fields"""
        event = ImmuneResponseEvent(
            threat_id="threat-001",
            responder_agent_id="agent-nk-001",
            responder_agent_type="nk_cell",
            response_action="neutralize",
            response_status="success",
            response_time_ms=250.5,
            target="1.2.3.4",
        )

        assert event.event_type == "immune.response"
        assert event.source_service == EventSource.IMMUNE_SYSTEM
        assert event.threat_id == "threat-001"
        assert event.response_action == "neutralize"
        assert event.response_status == "success"
        assert event.response_time_ms == 250.5


class TestHomeostaticStateEvent:
    """Test HomeostaticStateEvent schema"""

    def test_homeostatic_state_minimal(self):
        """Test HomeostaticStateEvent with minimal fields"""
        event = HomeostaticStateEvent(
            lymphnode_id="ln-001",
            area="network_dmz",
            new_state="vigilancia",
            temperatura_regional=37.2,
            threat_density=0.05,
            recommended_action="increase_patrols",
        )

        assert event.event_type == "immune.homeostatic_change"
        assert event.lymphnode_id == "ln-001"
        assert event.new_state == "vigilancia"
        assert event.temperatura_regional == 37.2

    def test_homeostatic_temperature_validation(self):
        """Test temperature validation"""
        # Valid temperature
        event = HomeostaticStateEvent(
            lymphnode_id="ln-001",
            area="network_dmz",
            new_state="vigilancia",
            temperatura_regional=37.0,
            threat_density=0.05,
            recommended_action="monitor",
        )
        assert event.temperatura_regional == 37.0

        # Invalid temperature (too high)
        with pytest.raises(ValidationError):
            HomeostaticStateEvent(
                lymphnode_id="ln-001",
                area="network_dmz",
                new_state="inflamacao",
                temperatura_regional=50.0,
                threat_density=0.5,
                recommended_action="escalate",
            )

        # Invalid temperature (too low)
        with pytest.raises(ValidationError):
            HomeostaticStateEvent(
                lymphnode_id="ln-001",
                area="network_dmz",
                new_state="repouso",
                temperatura_regional=20.0,
                threat_density=0.0,
                recommended_action="monitor",
            )


class TestEventSerialization:
    """Test event serialization/deserialization"""

    def test_threat_event_json_serialization(self):
        """Test ThreatDetectionEvent JSON serialization"""
        event = ThreatDetectionEvent(
            honeypot_id="hp_001",
            honeypot_type="ssh",
            attacker_ip="1.2.3.4",
            attack_type="brute_force",
            severity=SeverityLevel.HIGH,
        )

        # Serialize to dict
        event_dict = event.model_dump()

        assert isinstance(event_dict, dict)
        assert event_dict["honeypot_id"] == "hp_001"
        assert event_dict["severity"] == "high"

        # Reconstruct from dict
        reconstructed = ThreatDetectionEvent(**event_dict)
        assert reconstructed.honeypot_id == event.honeypot_id
        assert reconstructed.severity == event.severity

    def test_event_json_with_timestamp(self):
        """Test event JSON with datetime serialization"""
        event = EventBase(
            event_type="test.event",
            source_service=EventSource.MONITORING,
        )

        # Serialize with JSON encoder
        event_dict = event.model_dump()

        assert "timestamp" in event_dict
        assert isinstance(event_dict["timestamp"], datetime)
