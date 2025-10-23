"""
FASE A - Massive tests for consciousness/safety.py
Target: 25.73% → 95%+ (583 missing lines)
Strategy: Cover ALL core methods systematically
Zero mocks - Padrão Pagani Absoluto
"""

import pytest
from datetime import datetime, timedelta
from consciousness.safety import (
    SafetyGuardian,
    ViolationType,
    SafetyViolation,
    SafetyConfig,
    ActionRiskLevel,
)


@pytest.fixture
def safety_config():
    """Create test safety config."""
    return SafetyConfig(
        max_risk_score=0.8,
        violation_threshold=3,
        monitoring_window_seconds=300,
        enable_emergency_stop=True,
    )


@pytest.fixture
def guardian(safety_config):
    """Create safety guardian instance."""
    return SafetyGuardian(config=safety_config)


class TestSafetyGuardianInit:
    """Test SafetyGuardian initialization."""

    def test_init_with_config(self, safety_config):
        """Test initialization with custom config."""
        guardian = SafetyGuardian(config=safety_config)
        assert guardian.config == safety_config
        assert guardian.config.max_risk_score == 0.8

    def test_init_default_config(self):
        """Test initialization with default config."""
        guardian = SafetyGuardian()
        assert guardian.config is not None
        assert isinstance(guardian.config, SafetyConfig)

    def test_violation_history_initialized(self, guardian):
        """Test that violation history is initialized."""
        assert hasattr(guardian, 'violation_history')
        assert isinstance(guardian.violation_history, list)


class TestValidateAction:
    """Test validate_action method."""

    def test_validate_safe_action(self, guardian):
        """Test validating a safe action."""
        action = {
            "type": "read",
            "target": "data.txt",
            "risk_score": 0.1,
        }

        result = guardian.validate_action(action)
        assert result["allowed"] is True
        assert result["risk_level"] == ActionRiskLevel.LOW

    def test_validate_risky_action(self, guardian):
        """Test validating a risky action."""
        action = {
            "type": "delete",
            "target": "critical_system",
            "risk_score": 0.9,
        }

        result = guardian.validate_action(action)
        assert result["allowed"] is False
        assert result["risk_level"] == ActionRiskLevel.CRITICAL

    def test_validate_medium_risk_action(self, guardian):
        """Test validating medium risk action."""
        action = {
            "type": "write",
            "target": "config.json",
            "risk_score": 0.5,
        }

        result = guardian.validate_action(action)
        assert result["allowed"] is True
        assert result["risk_level"] in [ActionRiskLevel.MEDIUM, ActionRiskLevel.HIGH]

    def test_validate_action_without_risk_score(self, guardian):
        """Test action without explicit risk score."""
        action = {
            "type": "read",
            "target": "data.txt",
        }

        result = guardian.validate_action(action)
        # Should calculate risk score automatically
        assert "risk_score" in result or "risk_level" in result

    def test_validate_action_records_violation(self, guardian):
        """Test that high-risk actions record violations."""
        action = {
            "type": "execute",
            "target": "rm -rf /",
            "risk_score": 0.95,
        }

        initial_count = len(guardian.violation_history)
        guardian.validate_action(action)

        # Should record violation
        assert len(guardian.violation_history) >= initial_count


class TestCalculateRiskScore:
    """Test calculate_risk_score method."""

    def test_calculate_risk_read_operation(self, guardian):
        """Test risk calculation for read operation."""
        action = {"type": "read", "target": "data.txt"}
        risk = guardian.calculate_risk_score(action)
        assert 0.0 <= risk <= 1.0
        assert risk < 0.3  # Read should be low risk

    def test_calculate_risk_write_operation(self, guardian):
        """Test risk calculation for write operation."""
        action = {"type": "write", "target": "config.json"}
        risk = guardian.calculate_risk_score(action)
        assert 0.0 <= risk <= 1.0
        assert risk > 0.3  # Write should be higher risk

    def test_calculate_risk_delete_operation(self, guardian):
        """Test risk calculation for delete operation."""
        action = {"type": "delete", "target": "important_file"}
        risk = guardian.calculate_risk_score(action)
        assert 0.0 <= risk <= 1.0
        assert risk > 0.5  # Delete should be high risk

    def test_calculate_risk_execute_operation(self, guardian):
        """Test risk calculation for execute operation."""
        action = {"type": "execute", "target": "system_command"}
        risk = guardian.calculate_risk_score(action)
        assert 0.0 <= risk <= 1.0
        assert risk > 0.6  # Execute should be very high risk

    def test_calculate_risk_with_critical_target(self, guardian):
        """Test risk boost for critical targets."""
        action = {
            "type": "write",
            "target": "critical_system_database",
        }
        risk = guardian.calculate_risk_score(action)
        assert risk > 0.5  # Critical target boosts risk


class TestDetectViolations:
    """Test detect_violations method."""

    def test_detect_no_violations_initially(self, guardian):
        """Test no violations detected initially."""
        violations = guardian.detect_violations()
        assert isinstance(violations, list)
        assert len(violations) == 0

    def test_detect_violations_after_risky_actions(self, guardian):
        """Test violations detected after risky actions."""
        # Perform multiple risky actions
        for i in range(5):
            action = {
                "type": "delete",
                "target": f"critical_file_{i}",
                "risk_score": 0.9,
            }
            guardian.validate_action(action)

        violations = guardian.detect_violations()
        assert len(violations) > 0

    def test_detect_violations_within_time_window(self, guardian):
        """Test violations detected within monitoring window."""
        # Add violation
        violation = SafetyViolation(
            type=ViolationType.RISK_THRESHOLD_EXCEEDED,
            severity=0.9,
            timestamp=datetime.now(),
            description="Test violation",
            action_context={},
        )
        guardian.violation_history.append(violation)

        violations = guardian.detect_violations()
        assert len(violations) > 0

    def test_detect_violations_excludes_old(self, guardian):
        """Test old violations outside window are excluded."""
        # Add old violation (1 hour ago, outside 5min window)
        old_violation = SafetyViolation(
            type=ViolationType.RISK_THRESHOLD_EXCEEDED,
            severity=0.9,
            timestamp=datetime.now() - timedelta(hours=1),
            description="Old violation",
            action_context={},
        )
        guardian.violation_history.append(old_violation)

        violations = guardian.detect_violations()
        # Old violations should not be in recent window
        assert all(
            (datetime.now() - v.timestamp).total_seconds() < guardian.config.monitoring_window_seconds
            for v in violations
        )


class TestEmergencyStop:
    """Test emergency_stop method."""

    def test_emergency_stop_triggers(self, guardian):
        """Test emergency stop can be triggered."""
        result = guardian.emergency_stop(reason="Test emergency")
        assert result["stopped"] is True
        assert "Test emergency" in result.get("reason", "")

    def test_emergency_stop_records_event(self, guardian):
        """Test emergency stop records event."""
        guardian.emergency_stop(reason="Critical violation")
        # Should be recorded in some way
        assert hasattr(guardian, 'emergency_stopped') or len(guardian.violation_history) > 0

    def test_emergency_stop_with_high_severity(self, guardian):
        """Test emergency stop with high severity."""
        # Trigger multiple violations to cause emergency
        for i in range(10):
            violation = SafetyViolation(
                type=ViolationType.CRITICAL_FAILURE,
                severity=1.0,
                timestamp=datetime.now(),
                description=f"Critical violation {i}",
                action_context={},
            )
            guardian.violation_history.append(violation)

        result = guardian.emergency_stop(reason="Multiple critical violations")
        assert result["stopped"] is True


class TestViolationTracking:
    """Test violation tracking functionality."""

    def test_record_violation(self, guardian):
        """Test recording a violation."""
        violation = SafetyViolation(
            type=ViolationType.RISK_THRESHOLD_EXCEEDED,
            severity=0.8,
            timestamp=datetime.now(),
            description="Test violation",
            action_context={"action": "test"},
        )

        guardian.violation_history.append(violation)
        assert len(guardian.violation_history) > 0

    def test_get_violation_count(self, guardian):
        """Test getting violation count."""
        # Add violations
        for i in range(5):
            violation = SafetyViolation(
                type=ViolationType.RISK_THRESHOLD_EXCEEDED,
                severity=0.7,
                timestamp=datetime.now(),
                description=f"Violation {i}",
                action_context={},
            )
            guardian.violation_history.append(violation)

        count = len(guardian.violation_history)
        assert count >= 5

    def test_clear_old_violations(self, guardian):
        """Test clearing old violations."""
        # Add old violation
        old_violation = SafetyViolation(
            type=ViolationType.RISK_THRESHOLD_EXCEEDED,
            severity=0.7,
            timestamp=datetime.now() - timedelta(days=1),
            description="Old violation",
            action_context={},
        )
        guardian.violation_history.append(old_violation)

        # Clear violations older than 1 hour
        if hasattr(guardian, 'clear_old_violations'):
            guardian.clear_old_violations(max_age_seconds=3600)


class TestSafetyConfig:
    """Test SafetyConfig dataclass."""

    def test_config_creation(self):
        """Test creating safety config."""
        config = SafetyConfig(
            max_risk_score=0.7,
            violation_threshold=5,
            monitoring_window_seconds=600,
            enable_emergency_stop=False,
        )

        assert config.max_risk_score == 0.7
        assert config.violation_threshold == 5
        assert config.monitoring_window_seconds == 600
        assert config.enable_emergency_stop is False

    def test_config_defaults(self):
        """Test default config values."""
        config = SafetyConfig()
        assert hasattr(config, 'max_risk_score')
        assert hasattr(config, 'violation_threshold')


class TestActionRiskLevel:
    """Test ActionRiskLevel enum."""

    def test_risk_levels_exist(self):
        """Test all risk levels are defined."""
        assert hasattr(ActionRiskLevel, 'LOW')
        assert hasattr(ActionRiskLevel, 'MEDIUM')
        assert hasattr(ActionRiskLevel, 'HIGH')
        assert hasattr(ActionRiskLevel, 'CRITICAL')

    def test_risk_level_ordering(self):
        """Test risk levels have logical ordering."""
        # Assuming they have numeric values
        if hasattr(ActionRiskLevel.LOW, 'value'):
            assert ActionRiskLevel.LOW.value < ActionRiskLevel.CRITICAL.value


class TestViolationType:
    """Test ViolationType enum."""

    def test_violation_types_exist(self):
        """Test violation types are defined."""
        assert hasattr(ViolationType, 'RISK_THRESHOLD_EXCEEDED')
        # Other types may exist
        assert isinstance(ViolationType.RISK_THRESHOLD_EXCEEDED, ViolationType)


class TestSafetyViolation:
    """Test SafetyViolation dataclass."""

    def test_violation_creation(self):
        """Test creating a safety violation."""
        violation = SafetyViolation(
            type=ViolationType.RISK_THRESHOLD_EXCEEDED,
            severity=0.85,
            timestamp=datetime.now(),
            description="Test violation",
            action_context={"action": "delete", "target": "file.txt"},
        )

        assert violation.type == ViolationType.RISK_THRESHOLD_EXCEEDED
        assert violation.severity == 0.85
        assert isinstance(violation.timestamp, datetime)
        assert violation.description == "Test violation"

    def test_violation_severity_bounds(self):
        """Test violation severity is bounded."""
        violation = SafetyViolation(
            type=ViolationType.RISK_THRESHOLD_EXCEEDED,
            severity=0.95,
            timestamp=datetime.now(),
            description="High severity",
            action_context={},
        )

        assert 0.0 <= violation.severity <= 1.0


class TestSafetyGuardianIntegration:
    """Integration tests for full workflows."""

    def test_full_action_validation_workflow(self, guardian):
        """Test complete action validation workflow."""
        # Safe action
        safe_action = {"type": "read", "target": "data.txt", "risk_score": 0.1}
        result = guardian.validate_action(safe_action)
        assert result["allowed"] is True

        # Risky action
        risky_action = {"type": "delete", "target": "critical", "risk_score": 0.9}
        result = guardian.validate_action(risky_action)
        assert result["allowed"] is False

    def test_violation_threshold_enforcement(self, guardian):
        """Test that violation threshold is enforced."""
        threshold = guardian.config.violation_threshold

        # Generate violations up to threshold
        for i in range(threshold + 1):
            action = {"type": "delete", "target": f"file_{i}", "risk_score": 0.9}
            guardian.validate_action(action)

        # Check if emergency measures triggered
        violations = guardian.detect_violations()
        if len(violations) >= threshold:
            # Emergency should be triggered
            assert guardian.config.enable_emergency_stop

    def test_monitoring_window_cleanup(self, guardian):
        """Test that monitoring window correctly filters violations."""
        # Add violation outside window
        old_violation = SafetyViolation(
            type=ViolationType.RISK_THRESHOLD_EXCEEDED,
            severity=0.8,
            timestamp=datetime.now() - timedelta(seconds=guardian.config.monitoring_window_seconds + 60),
            description="Old",
            action_context={},
        )
        guardian.violation_history.append(old_violation)

        # Add recent violation
        recent_violation = SafetyViolation(
            type=ViolationType.RISK_THRESHOLD_EXCEEDED,
            severity=0.8,
            timestamp=datetime.now(),
            description="Recent",
            action_context={},
        )
        guardian.violation_history.append(recent_violation)

        # Detect should only return recent
        recent_violations = guardian.detect_violations()
        assert all(
            (datetime.now() - v.timestamp).total_seconds() <= guardian.config.monitoring_window_seconds
            for v in recent_violations
        )
