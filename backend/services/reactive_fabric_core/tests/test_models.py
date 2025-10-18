"""
Tests for Reactive Fabric Core models
Sprint 1: Basic validation
"""

import pytest
from datetime import datetime
from models import (
    HoneypotType, HoneypotStatus, AttackSeverity,
    HoneypotBase, HoneypotStats,
    AttackCreate,
    TTPFrequency,
    ThreatDetectedMessage
)
from uuid import uuid4


def test_honeypot_base() -> None:
    """Test HoneypotBase model validation."""
    honeypot = HoneypotBase(
        honeypot_id="ssh_001",
        type=HoneypotType.SSH,
        container_name="reactive-fabric-honeypot-ssh",
        port=2222
    )
    
    assert honeypot.honeypot_id == "ssh_001"
    assert honeypot.type == HoneypotType.SSH
    assert honeypot.port == 2222


def test_honeypot_stats() -> None:
    """Test HoneypotStats model."""
    stats = HoneypotStats(
        honeypot_id="ssh_001",
        type=HoneypotType.SSH,
        status=HoneypotStatus.ONLINE,
        total_attacks=10,
        unique_ips=5,
        last_attack=datetime.utcnow(),
        critical_attacks=1,
        high_attacks=3
    )
    
    assert stats.total_attacks == 10
    assert stats.unique_ips == 5
    assert stats.critical_attacks == 1


def test_attack_create() -> None:
    """Test AttackCreate model validation."""
    attack = AttackCreate(
        honeypot_id=uuid4(),
        attacker_ip="45.142.120.15",
        attack_type="brute_force",
        severity=AttackSeverity.MEDIUM,
        confidence=0.95,
        ttps=["T1110", "T1078"],
        iocs={"ips": ["45.142.120.15"], "usernames": ["admin", "root"]},
        payload="",  # Add missing required field (empty string)
        captured_at=datetime.utcnow()
    )
    
    assert attack.attacker_ip == "45.142.120.15"
    assert attack.severity == AttackSeverity.MEDIUM
    assert len(attack.ttps) == 2
    assert attack.confidence == 0.95


def test_threat_detected_message() -> None:
    """Test ThreatDetectedMessage Kafka model."""
    msg = ThreatDetectedMessage(
        event_id="rf_attack_12345",
        timestamp=datetime.utcnow(),
        honeypot_id="ssh_001",
        attacker_ip="45.142.120.15",
        attack_type="brute_force",
        severity=AttackSeverity.HIGH,
        ttps=["T1110"],
        iocs={"ips": ["45.142.120.15"]},
        confidence=0.98
    )
    
    assert msg.event_id == "rf_attack_12345"
    assert msg.severity == AttackSeverity.HIGH
    assert msg.confidence == 0.98
    assert "T1110" in msg.ttps


def test_ttp_frequency() -> None:
    """Test TTPFrequency model."""
    ttp = TTPFrequency(
        technique_id="T1110",
        technique_name="Brute Force",
        tactic="Credential Access",
        observed_count=15,
        last_observed=datetime.utcnow(),
        affected_honeypots=2
    )
    
    assert ttp.technique_id == "T1110"
    assert ttp.observed_count == 15
    assert ttp.affected_honeypots == 2


def test_attack_severity_enum() -> None:
    """Test AttackSeverity enum."""
    assert AttackSeverity.LOW.value == "low"
    assert AttackSeverity.MEDIUM.value == "medium"
    assert AttackSeverity.HIGH.value == "high"
    assert AttackSeverity.CRITICAL.value == "critical"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
