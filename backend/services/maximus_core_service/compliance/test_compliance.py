"""
Compliance System Test Suite

Comprehensive tests for the compliance and certification system.
Tests all modules: base, compliance_engine, evidence_collector, gap_analyzer,
monitoring, and certifications.

Run with:
    pytest test_compliance.py -v

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
License: Proprietary - VÉRTICE Platform
"""

import os
import tempfile
from datetime import datetime, timedelta

import pytest

from .base import (
    ComplianceConfig,
    ComplianceStatus,
    Control,
    ControlCategory,
    Evidence,
    EvidenceType,
    Gap,
    Regulation,
    RegulationType,
    ViolationSeverity,
)
from .certifications import (
    IEEE7000Checker,
    ISO27001Checker,
    SOC2Checker,
)
from .compliance_engine import ComplianceEngine
from .evidence_collector import EvidenceCollector
from .gap_analyzer import GapAnalyzer
from .monitoring import ComplianceAlert, ComplianceMonitor
from .regulations import (
    get_regulation,
)

# ==============================================================================
# BASE CLASSES TESTS
# ==============================================================================


def test_regulation_creation():
    """Test Regulation dataclass creation and validation."""
    regulation = Regulation(
        regulation_type=RegulationType.ISO_27001,
        name="Test Regulation",
        version="1.0",
        effective_date=datetime(2024, 1, 1),
        jurisdiction="Test",
        description="Test regulation",
    )

    assert regulation.name == "Test Regulation"
    assert regulation.version == "1.0"
    assert len(regulation.controls) == 0

    # Test validation
    with pytest.raises(ValueError):
        Regulation(
            regulation_type=RegulationType.ISO_27001,
            name="",  # Empty name should fail
            version="1.0",
            effective_date=datetime(2024, 1, 1),
            jurisdiction="Test",
            description="Test",
        )


def test_control_creation():
    """Test Control dataclass creation and validation."""
    control = Control(
        control_id="TEST-001",
        regulation_type=RegulationType.ISO_27001,
        category=ControlCategory.TECHNICAL,
        title="Test Control",
        description="Test control description",
        mandatory=True,
        evidence_required=[EvidenceType.DOCUMENT, EvidenceType.TEST_RESULT],
    )

    assert control.control_id == "TEST-001"
    assert control.mandatory is True
    assert len(control.evidence_required) == 2

    # Test validation
    with pytest.raises(ValueError):
        Control(
            control_id="",  # Empty ID should fail
            regulation_type=RegulationType.ISO_27001,
            category=ControlCategory.TECHNICAL,
            title="Test",
            description="Test",
        )


def test_evidence_creation():
    """Test Evidence dataclass creation and methods."""
    evidence = Evidence(
        evidence_type=EvidenceType.DOCUMENT,
        control_id="TEST-001",
        title="Test Evidence",
        description="Test evidence description",
        file_hash="abc123",
        expiration_date=datetime.utcnow() + timedelta(days=90),
    )

    assert evidence.control_id == "TEST-001"
    assert evidence.is_expired() is False

    # Test verification
    evidence.verify("test_auditor")
    assert evidence.verified is True
    assert evidence.verified_by == "test_auditor"

    # Test expiration
    expired_evidence = Evidence(
        evidence_type=EvidenceType.DOCUMENT,
        control_id="TEST-002",
        title="Expired Evidence",
        description="Test",
        expiration_date=datetime.utcnow() - timedelta(days=1),
    )
    assert expired_evidence.is_expired() is True


# ==============================================================================
# COMPLIANCE ENGINE TESTS
# ==============================================================================


def test_check_control():
    """Test compliance engine control checking."""
    config = ComplianceConfig()
    engine = ComplianceEngine(config)

    # Create test control
    control = Control(
        control_id="TEST-001",
        regulation_type=RegulationType.ISO_27001,
        category=ControlCategory.DOCUMENTATION,
        title="Test Control",
        description="Test",
        evidence_required=[EvidenceType.DOCUMENT],
    )

    # Check without evidence
    result = engine.check_control(control)
    assert result.status == ComplianceStatus.EVIDENCE_REQUIRED

    # Check with evidence
    evidence = [
        Evidence(
            evidence_type=EvidenceType.DOCUMENT,
            control_id="TEST-001",
            title="Test Doc",
            description="Test",
        )
    ]
    result = engine.check_control(control, evidence)
    assert result.status == ComplianceStatus.COMPLIANT


def test_check_compliance():
    """Test compliance engine regulation checking."""
    config = ComplianceConfig(enabled_regulations=[RegulationType.ISO_27001])
    engine = ComplianceEngine(config)

    # Check ISO 27001
    result = engine.check_compliance(RegulationType.ISO_27001)

    assert result.regulation_type == RegulationType.ISO_27001
    assert result.total_controls > 0
    assert result.compliance_percentage >= 0


def test_run_all_checks():
    """Test running compliance checks for all regulations."""
    config = ComplianceConfig(enabled_regulations=[RegulationType.ISO_27001, RegulationType.GDPR])
    engine = ComplianceEngine(config)

    snapshot = engine.run_all_checks()

    assert len(snapshot.regulation_results) == 2
    assert RegulationType.ISO_27001 in snapshot.regulation_results
    assert RegulationType.GDPR in snapshot.regulation_results
    assert 0 <= snapshot.overall_compliance_percentage <= 100


def test_generate_compliance_report():
    """Test compliance report generation."""
    config = ComplianceConfig(enabled_regulations=[RegulationType.ISO_27001])
    engine = ComplianceEngine(config)

    start_date = datetime.utcnow() - timedelta(days=30)
    end_date = datetime.utcnow()

    report = engine.generate_compliance_report(start_date, end_date)

    assert "report_id" in report
    assert "generated_at" in report
    assert "summary" in report
    assert "regulations" in report


# ==============================================================================
# EVIDENCE COLLECTOR TESTS
# ==============================================================================


def test_collect_evidence():
    """Test evidence collection from files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = ComplianceConfig(evidence_storage_path=tmpdir)
        collector = EvidenceCollector(config)

        # Create test control
        control = Control(
            control_id="TEST-001",
            regulation_type=RegulationType.ISO_27001,
            category=ControlCategory.DOCUMENTATION,
            title="Test",
            description="Test",
        )

        # Create test log file
        log_file = os.path.join(tmpdir, "test.log")
        with open(log_file, "w") as f:
            f.write("Test log content\n")

        # Collect log evidence
        evidence_item = collector.collect_log_evidence(
            control,
            log_file,
            "Test Log",
            "Test log evidence",
        )

        assert evidence_item is not None
        assert evidence_item.evidence.title == "Test Log"
        assert evidence_item.integrity_verified is True


def test_create_evidence_package():
    """Test evidence package creation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = ComplianceConfig(evidence_storage_path=tmpdir)
        collector = EvidenceCollector(config)

        # Create test control and evidence
        control = Control(
            control_id="TEST-001",
            regulation_type=RegulationType.ISO_27001,
            category=ControlCategory.DOCUMENTATION,
            title="Test",
            description="Test",
        )

        # Create test file
        doc_file = os.path.join(tmpdir, "test.txt")
        with open(doc_file, "w") as f:
            f.write("Test document\n")

        # Collect evidence
        collector.collect_document_evidence(
            control,
            doc_file,
            "Test Document",
            "Test",
        )

        # Create package
        package = collector.create_evidence_package(RegulationType.ISO_27001)

        assert package.regulation_type == RegulationType.ISO_27001
        assert len(package.evidence_items) > 0
        assert package.total_size_bytes > 0


def test_verify_evidence_integrity():
    """Test evidence integrity verification."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = ComplianceConfig(evidence_storage_path=tmpdir)
        collector = EvidenceCollector(config)

        # Create test file
        test_file = os.path.join(tmpdir, "test.txt")
        with open(test_file, "w") as f:
            f.write("Test content\n")

        control = Control(
            control_id="TEST-001",
            regulation_type=RegulationType.ISO_27001,
            category=ControlCategory.DOCUMENTATION,
            title="Test",
            description="Test",
        )

        # Collect evidence
        collector.collect_document_evidence(control, test_file, "Test", "Test")

        # Verify all evidence
        results = collector.verify_all_evidence()

        assert len(results) > 0
        assert all(v is True for v in results.values())


# ==============================================================================
# GAP ANALYZER TESTS
# ==============================================================================


def test_analyze_compliance_gaps():
    """Test gap analysis."""
    config = ComplianceConfig(enabled_regulations=[RegulationType.ISO_27001])
    engine = ComplianceEngine(config)
    analyzer = GapAnalyzer(config)

    # Run compliance check
    compliance_result = engine.check_compliance(RegulationType.ISO_27001)

    # Analyze gaps
    gap_analysis = analyzer.analyze_compliance_gaps(compliance_result)

    assert gap_analysis.regulation_type == RegulationType.ISO_27001
    assert gap_analysis.total_controls > 0
    assert gap_analysis.compliance_percentage >= 0
    assert len(gap_analysis.gaps) >= 0


def test_create_remediation_plan():
    """Test remediation plan creation."""
    config = ComplianceConfig(enabled_regulations=[RegulationType.ISO_27001])
    engine = ComplianceEngine(config)
    analyzer = GapAnalyzer(config)

    # Run compliance check and gap analysis
    compliance_result = engine.check_compliance(RegulationType.ISO_27001)
    gap_analysis = analyzer.analyze_compliance_gaps(compliance_result)

    # Create remediation plan
    plan = analyzer.create_remediation_plan(gap_analysis, target_completion_days=180)

    assert plan.regulation_type == RegulationType.ISO_27001
    assert len(plan.gaps) == len(gap_analysis.gaps)
    assert len(plan.actions) > 0
    assert plan.status == "draft"


def test_prioritize_gaps():
    """Test gap prioritization."""
    analyzer = GapAnalyzer()

    # Create test gaps
    gaps = [
        Gap(
            control_id="TEST-001",
            regulation_type=RegulationType.ISO_27001,
            title="Low Priority Gap",
            description="Test",
            severity=ViolationSeverity.LOW,
            current_state="Missing",
            required_state="Implemented",
            estimated_effort_hours=10,
            priority=4,
        ),
        Gap(
            control_id="TEST-002",
            regulation_type=RegulationType.ISO_27001,
            title="Critical Gap",
            description="Test",
            severity=ViolationSeverity.CRITICAL,
            current_state="Missing",
            required_state="Implemented",
            estimated_effort_hours=80,
            priority=1,
        ),
    ]

    # Prioritize by risk
    prioritized = analyzer.prioritize_gaps(gaps, criteria="risk")
    assert prioritized[0].severity == ViolationSeverity.CRITICAL

    # Prioritize by effort (quick wins)
    prioritized = analyzer.prioritize_gaps(gaps, criteria="effort")
    assert prioritized[0].estimated_effort_hours == 10


# ==============================================================================
# MONITORING TESTS
# ==============================================================================


def test_monitoring_initialization():
    """Test compliance monitor initialization."""
    config = ComplianceConfig()
    engine = ComplianceEngine(config)
    monitor = ComplianceMonitor(engine, config=config)

    assert monitor.engine == engine
    assert monitor.config == config
    assert monitor._monitoring is False


def test_alert_generation():
    """Test compliance alert generation."""
    alert = ComplianceAlert(
        alert_type="violation",
        severity=ViolationSeverity.CRITICAL,
        title="Test Alert",
        message="Test alert message",
        regulation_type=RegulationType.ISO_27001,
    )

    assert alert.alert_type == "violation"
    assert alert.acknowledged is False

    # Test acknowledgement
    alert.acknowledge("test_user")
    assert alert.acknowledged is True
    assert alert.acknowledged_by == "test_user"


def test_metrics_tracking():
    """Test monitoring metrics tracking."""
    config = ComplianceConfig(enabled_regulations=[RegulationType.ISO_27001])
    engine = ComplianceEngine(config)
    monitor = ComplianceMonitor(engine, config=config)

    # Run monitoring checks manually
    monitor._run_monitoring_checks()

    # Get current metrics
    metrics = monitor.get_current_metrics()

    assert metrics is not None
    assert 0 <= metrics.overall_compliance_percentage <= 100
    assert metrics.compliance_trend in ["improving", "stable", "declining"]


# ==============================================================================
# CERTIFICATION TESTS
# ==============================================================================


def test_iso27001_checker():
    """Test ISO 27001 certification checker."""
    config = ComplianceConfig(enabled_regulations=[RegulationType.ISO_27001])
    engine = ComplianceEngine(config)
    checker = ISO27001Checker(engine)

    result = checker.check_certification_readiness()

    assert result.regulation_type == RegulationType.ISO_27001
    assert 0 <= result.compliance_percentage <= 100
    assert result.required_threshold == 95.0
    assert len(result.recommendations) > 0


def test_soc2_checker():
    """Test SOC 2 Type II certification checker."""
    config = ComplianceConfig(enabled_regulations=[RegulationType.SOC2_TYPE_II])
    engine = ComplianceEngine(config)
    checker = SOC2Checker(engine)

    result = checker.check_certification_readiness(audit_period_months=6)

    assert result.regulation_type == RegulationType.SOC2_TYPE_II
    assert 0 <= result.compliance_percentage <= 100
    assert result.required_threshold == 95.0
    assert len(result.recommendations) > 0


def test_ieee7000_checker():
    """Test IEEE 7000 certification checker."""
    config = ComplianceConfig(enabled_regulations=[RegulationType.IEEE_7000])
    engine = ComplianceEngine(config)
    checker = IEEE7000Checker(engine)

    result = checker.check_certification_readiness()

    assert result.regulation_type == RegulationType.IEEE_7000
    assert 0 <= result.compliance_percentage <= 100
    assert result.required_threshold == 90.0
    assert len(result.recommendations) > 0


# ==============================================================================
# INTEGRATION TESTS
# ==============================================================================


def test_end_to_end_compliance_check():
    """Test complete end-to-end compliance check workflow."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Initialize components
        config = ComplianceConfig(
            enabled_regulations=[RegulationType.ISO_27001],
            evidence_storage_path=tmpdir,
        )
        engine = ComplianceEngine(config)
        collector = EvidenceCollector(config)
        analyzer = GapAnalyzer(config)

        # 1. Collect evidence
        control = get_regulation(RegulationType.ISO_27001).controls[0]

        test_file = os.path.join(tmpdir, "test_policy.pdf")
        with open(test_file, "w") as f:
            f.write("Test policy document\n")

        collector.collect_policy_evidence(
            control,
            test_file,
            "Information Security Policy",
            "Test policy",
        )

        # 2. Run compliance check
        evidence = collector.get_all_evidence()
        compliance_result = engine.check_compliance(RegulationType.ISO_27001, evidence)

        assert compliance_result.total_controls > 0

        # 3. Analyze gaps
        gap_analysis = analyzer.analyze_compliance_gaps(compliance_result)

        assert gap_analysis.total_controls == compliance_result.total_controls

        # 4. Create remediation plan
        plan = analyzer.create_remediation_plan(gap_analysis)

        assert len(plan.actions) > 0


def test_certification_readiness_workflow():
    """Test complete certification readiness workflow."""
    # Initialize components
    config = ComplianceConfig(enabled_regulations=[RegulationType.ISO_27001])
    engine = ComplianceEngine(config)
    checker = ISO27001Checker(engine)

    # Check certification readiness
    result = checker.check_certification_readiness()

    assert result.regulation_type == RegulationType.ISO_27001

    # Verify result structure
    assert hasattr(result, "certification_ready")
    assert hasattr(result, "compliance_percentage")
    assert hasattr(result, "gaps_to_certification")
    assert hasattr(result, "recommendations")
    assert hasattr(result, "estimated_days_to_certification")

    # Verify recommendations are actionable
    assert len(result.recommendations) > 0

    # Get summary
    summary = result.get_summary()
    assert isinstance(summary, str)
    assert len(summary) > 0


# ==============================================================================
# ADDITIONAL TESTS
# ==============================================================================


def test_regulation_registry():
    """Test regulation registry functionality."""
    # Get regulation from registry
    iso27001 = get_regulation(RegulationType.ISO_27001)

    assert iso27001.regulation_type == RegulationType.ISO_27001
    assert len(iso27001.controls) > 0

    # Test mandatory controls filtering
    mandatory = iso27001.get_mandatory_controls()
    assert len(mandatory) > 0
    assert all(c.mandatory for c in mandatory)

    # Test category filtering
    technical = iso27001.get_controls_by_category(ControlCategory.TECHNICAL)
    assert all(c.category == ControlCategory.TECHNICAL for c in technical)


def test_config_validation():
    """Test compliance configuration validation."""
    # Valid config
    config = ComplianceConfig(
        enabled_regulations=[RegulationType.ISO_27001],
        alert_threshold_percentage=80.0,
    )
    assert config.is_regulation_enabled(RegulationType.ISO_27001)

    # Invalid config - should raise error
    with pytest.raises(ValueError):
        ComplianceConfig(
            enabled_regulations=[],  # Empty list should fail
        )

    with pytest.raises(ValueError):
        ComplianceConfig(
            alert_threshold_percentage=150.0,  # Out of range
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
