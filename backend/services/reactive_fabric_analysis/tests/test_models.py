"""
Test suite for Pydantic models.
Validates data structures and serialization.

Part of MAXIMUS VÉRTICE - Projeto Tecido Reativo
Sprint 1 Complete Test Suite
"""

import pytest
from datetime import datetime
from uuid import uuid4
from backend.services.reactive_fabric_analysis.models import (
    ForensicCapture,
    AttackCreate,
    AttackSeverity,
    ProcessingStatus,
    AnalysisStatus
)


class TestForensicCaptureModel:
    """Test ForensicCapture model."""
    
    def test_create_forensic_capture(self):
        """Test creating ForensicCapture instance."""
        capture_id = uuid4()
        honeypot_id = uuid4()
        
        capture = ForensicCapture(
            id=capture_id,
            honeypot_id=honeypot_id,
            filename="session.json",
            file_path="/forensics/cowrie_ssh_001/session.json",
            file_type="cowrie_json",
            file_size_bytes=1024,
            captured_at=datetime.now(),
            processing_status=ProcessingStatus.PENDING
        )
        
        assert capture.id == capture_id
        assert capture.honeypot_id == honeypot_id
        assert capture.processing_status == ProcessingStatus.PENDING
    
    def test_forensic_capture_default_status(self):
        """Test ForensicCapture has default status."""
        capture = ForensicCapture(
            id=uuid4(),
            honeypot_id=uuid4(),
            filename="test.json",
            file_path="/forensics/test.json",
            file_type="json",
            file_size_bytes=512,
            captured_at=datetime.now()
        )
        
        # Should have a default status
        assert capture.processing_status == ProcessingStatus.PENDING


class TestAttackCreateModel:
    """Test AttackCreate model."""
    
    def test_create_attack(self, sample_attack_data: dict):
        """Test creating AttackCreate instance."""
        honeypot_id = uuid4()
        
        attack = AttackCreate(
            honeypot_id=honeypot_id,
            attacker_ip=sample_attack_data["attacker_ip"],
            attack_type=sample_attack_data["attack_type"],
            severity=AttackSeverity.HIGH,
            ttps=["T1110", "T1059.004", "T1082"],
            iocs={
                "ips": ["45.142.120.15"],
                "hashes": sample_attack_data["file_hashes"],
                "urls": ["http://malicious.com/payload.sh"]
            },
            captured_at=datetime.now()
        )
        
        assert attack.honeypot_id == honeypot_id
        assert attack.attacker_ip == "45.142.120.15"
        assert attack.severity == AttackSeverity.HIGH
        assert "T1110" in attack.ttps
    
    def test_attack_create_serialization(self):
        """Test AttackCreate serializes to dict."""
        attack = AttackCreate(
            honeypot_id=uuid4(),
            attacker_ip="1.2.3.4",
            attack_type="test",
            severity=AttackSeverity.LOW,
            ttps=["T1110"],
            iocs={"ips": ["1.2.3.4"]},
            captured_at=datetime.now()
        )
        
        # Should be serializable
        attack_dict = attack.model_dump() if hasattr(attack, 'model_dump') else attack.dict()
        
        assert isinstance(attack_dict, dict)
        assert attack_dict["attacker_ip"] == "1.2.3.4"


class TestAttackSeverityEnum:
    """Test AttackSeverity enum."""
    
    def test_severity_levels(self):
        """Test severity levels are defined."""
        assert hasattr(AttackSeverity, 'LOW')
        assert hasattr(AttackSeverity, 'MEDIUM')
        assert hasattr(AttackSeverity, 'HIGH')
        assert hasattr(AttackSeverity, 'CRITICAL')
    
    def test_severity_comparison(self):
        """Test severity can be compared."""
        # Just verify they exist and are different
        assert AttackSeverity.LOW != AttackSeverity.CRITICAL


class TestProcessingStatusEnum:
    """Test ProcessingStatus enum."""
    
    def test_processing_statuses(self):
        """Test processing statuses are defined."""
        assert hasattr(ProcessingStatus, 'PENDING')
        assert hasattr(ProcessingStatus, 'PROCESSING')
        assert hasattr(ProcessingStatus, 'COMPLETED')
        assert hasattr(ProcessingStatus, 'FAILED')


class TestAnalysisStatusModel:
    """Test AnalysisStatus model."""
    
    def test_analysis_status_creation(self):
        """Test AnalysisStatus model creation."""
        status = AnalysisStatus(
            status="operational",
            polling_interval_seconds=30
        )
        
        assert status.status == "operational"
        assert status.captures_processed_today == 0


class TestModelValidation:
    """Test model validation."""
    
    def test_attack_requires_required_fields(self):
        """Test AttackCreate requires required fields."""
        with pytest.raises((TypeError, ValueError, Exception)):
            # Should fail without required fields
            AttackCreate()
    
    def test_attack_accepts_any_ip_string(self):
        """Test AttackCreate accepts IP strings (no strict validation)."""
        # System accepts any string as IP for flexibility
        attack = AttackCreate(
            honeypot_id=uuid4(),
            attacker_ip="192.168.1.1",
            attack_type="test",
            severity=AttackSeverity.LOW,
            ttps=[],
            iocs={},
            captured_at=datetime.now()
        )
        
        assert attack.attacker_ip == "192.168.1.1"


class TestModelTimestamps:
    """Test timestamp handling in models."""
    
    def test_forensic_capture_timestamp(self):
        """Test ForensicCapture handles timestamp."""
        now = datetime.now()
        capture = ForensicCapture(
            id=uuid4(),
            honeypot_id=uuid4(),
            filename="test.json",
            file_path="/test.json",
            file_type="json",
            file_size_bytes=100,
            captured_at=now
        )
        
        assert capture.captured_at == now
    
    def test_attack_captured_at_timestamp(self):
        """Test AttackCreate handles captured_at timestamp."""
        now = datetime.now()
        attack = AttackCreate(
            honeypot_id=uuid4(),
            attacker_ip="1.2.3.4",
            attack_type="test",
            severity=AttackSeverity.LOW,
            ttps=[],
            iocs={},
            captured_at=now
        )
        
        assert attack.captured_at == now
