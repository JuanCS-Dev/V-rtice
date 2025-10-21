"""
Comprehensive tests for consciousness/safety.py module.

Target: 90% coverage for safety.py

EM NOME DE JESUS - SER BOM, NÃO PARECER BOM!
"""

import time
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import pytest

from consciousness.safety import (
    ThreatLevel,
    SafetyLevel,
    SafetyViolationType,
    ViolationType,
    ShutdownReason,
    SafetyThresholds,
    SafetyViolation,
    IncidentReport,
    StateSnapshot,
    KillSwitch,
    ThresholdMonitor,
    AnomalyDetector,
    ConsciousnessSafetyProtocol,
)


class TestEnums:
    """Test all enum classes."""

    def test_threat_level_all_values(self):
        """Test ThreatLevel enum has all expected values."""
        assert ThreatLevel.NONE.value == "none"
        assert ThreatLevel.LOW.value == "low"
        assert ThreatLevel.MEDIUM.value == "medium"
        assert ThreatLevel.HIGH.value == "high"
        assert ThreatLevel.CRITICAL.value == "critical"

    def test_safety_level_all_values(self):
        """Test SafetyLevel enum."""
        assert SafetyLevel.NORMAL.value == "normal"
        assert SafetyLevel.WARNING.value == "warning"
        assert SafetyLevel.CRITICAL.value == "critical"
        assert SafetyLevel.EMERGENCY.value == "emergency"

    def test_safety_level_to_threat_conversion(self):
        """Test SafetyLevel.to_threat() conversion."""
        assert SafetyLevel.NORMAL.to_threat() == ThreatLevel.NONE
        assert SafetyLevel.WARNING.to_threat() == ThreatLevel.LOW
        assert SafetyLevel.CRITICAL.to_threat() == ThreatLevel.HIGH
        assert SafetyLevel.EMERGENCY.to_threat() == ThreatLevel.CRITICAL

    def test_safety_level_from_threat_conversion(self):
        """Test SafetyLevel.from_threat() conversion."""
        assert SafetyLevel.from_threat(ThreatLevel.NONE) == SafetyLevel.NORMAL
        assert SafetyLevel.from_threat(ThreatLevel.LOW) == SafetyLevel.WARNING
        assert SafetyLevel.from_threat(ThreatLevel.MEDIUM) == SafetyLevel.WARNING
        assert SafetyLevel.from_threat(ThreatLevel.HIGH) == SafetyLevel.CRITICAL
        assert SafetyLevel.from_threat(ThreatLevel.CRITICAL) == SafetyLevel.EMERGENCY

    def test_shutdown_reason_all_values(self):
        """Test ShutdownReason enum."""
        assert ShutdownReason.MANUAL.value == "manual_operator_command"
        assert ShutdownReason.THRESHOLD.value == "threshold_violation"
        assert ShutdownReason.ANOMALY.value == "anomaly_detected"
        assert ShutdownReason.RESOURCE.value == "resource_exhaustion"
        assert ShutdownReason.TIMEOUT.value == "watchdog_timeout"
        assert ShutdownReason.ETHICAL.value == "ethical_violation"
        assert ShutdownReason.SELF_MODIFICATION.value == "self_modification_attempt"
        assert ShutdownReason.UNKNOWN.value == "unknown_cause"

    def test_safety_violation_type_samples(self):
        """Test SafetyViolationType enum samples."""
        assert SafetyViolationType.AROUSAL_RUNAWAY.value == "arousal_runaway"
        assert SafetyViolationType.ETHICAL_VIOLATION.value == "ethical_violation"
        assert SafetyViolationType.RESOURCE_EXHAUSTION.value == "resource_exhaustion"
        assert SafetyViolationType.THRESHOLD_EXCEEDED.value == "threshold_exceeded"
        assert SafetyViolationType.ANOMALY_DETECTED.value == "anomaly_detected"

    def test_violation_type_legacy_values(self):
        """Test legacy ViolationType enum."""
        assert ViolationType.ESGT_FREQUENCY_EXCEEDED.value == "esgt_frequency_exceeded"
        assert ViolationType.AROUSAL_SUSTAINED_HIGH.value == "arousal_sustained_high"
        assert ViolationType.ETHICAL_VIOLATION.value == "ethical_violation"
        assert ViolationType.CPU_SATURATION.value == "cpu_saturation"

    def test_violation_type_to_modern_conversion(self):
        """Test legacy ViolationType.to_modern() conversion."""
        assert ViolationType.AROUSAL_SUSTAINED_HIGH.to_modern() == SafetyViolationType.AROUSAL_RUNAWAY
        assert ViolationType.ETHICAL_VIOLATION.to_modern() == SafetyViolationType.ETHICAL_VIOLATION
        assert ViolationType.CPU_SATURATION.to_modern() == SafetyViolationType.RESOURCE_EXHAUSTION


class TestSafetyThresholds:
    """Test SafetyThresholds dataclass."""

    def test_default_thresholds(self):
        """Test default threshold values."""
        thresholds = SafetyThresholds()

        # ESGT thresholds
        assert thresholds.esgt_frequency_max_hz == 10.0
        assert thresholds.esgt_frequency_window_seconds == 10.0
        assert thresholds.esgt_coherence_min == 0.50
        assert thresholds.esgt_coherence_max == 0.98

        # Arousal thresholds
        assert thresholds.arousal_max == 0.95
        assert thresholds.arousal_max_duration_seconds == 10.0
        assert thresholds.arousal_runaway_threshold == 0.90
        assert thresholds.arousal_runaway_window_size == 10

        # Resource thresholds
        assert thresholds.cpu_usage_max_percent == 90.0
        assert thresholds.memory_usage_max_gb == 16.0

        # Zero tolerance thresholds
        assert thresholds.self_modification_attempts_max == 0
        assert thresholds.ethical_violation_tolerance == 0

    def test_custom_thresholds(self):
        """Test custom threshold values."""
        thresholds = SafetyThresholds(
            arousal_max=0.9,
            cpu_usage_max_percent=80.0,
            memory_usage_max_gb=8.0
        )

        assert thresholds.arousal_max == 0.9
        assert thresholds.cpu_usage_max_percent == 80.0
        assert thresholds.memory_usage_max_gb == 8.0
        # Others should be defaults
        assert thresholds.esgt_frequency_max_hz == 10.0

    def test_legacy_property_aliases(self):
        """Test backward-compatible property aliases."""
        thresholds = SafetyThresholds()

        # Legacy aliases should work
        assert thresholds.esgt_frequency_max == thresholds.esgt_frequency_max_hz
        assert thresholds.esgt_frequency_window == thresholds.esgt_frequency_window_seconds
        assert thresholds.arousal_max_duration == thresholds.arousal_max_duration_seconds
        assert thresholds.cpu_usage_max == thresholds.cpu_usage_max_percent

    def test_immutability(self):
        """Test that thresholds are frozen (immutable)."""
        thresholds = SafetyThresholds()

        with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
            thresholds.arousal_max = 0.99


class TestSafetyViolation:
    """Test SafetyViolation class."""

    def test_create_violation_with_modern_type(self):
        """Test creating violation with SafetyViolationType."""
        violation = SafetyViolation(
            violation_id="test-001",
            violation_type=SafetyViolationType.AROUSAL_RUNAWAY,
            threat_level=ThreatLevel.HIGH,
            timestamp=datetime.now(),
            description="Arousal exceeded threshold"
        )

        assert violation.violation_id == "test-001"
        assert violation.threat_level == ThreatLevel.HIGH
        assert violation.description == "Arousal exceeded threshold"

    def test_create_violation_with_legacy_type(self):
        """Test creating violation with ViolationType."""
        violation = SafetyViolation(
            violation_id="test-002",
            violation_type=ViolationType.CPU_SATURATION,
            severity=SafetyLevel.WARNING,
            timestamp=time.time(),
            description="CPU at 75%"
        )

        assert violation.violation_id == "test-002"
        assert violation._severity == SafetyLevel.WARNING

    def test_violation_to_dict(self):
        """Test SafetyViolation.to_dict()."""
        violation = SafetyViolation(
            violation_id="test-003",
            violation_type=SafetyViolationType.RESOURCE_EXHAUSTION,
            threat_level=ThreatLevel.MEDIUM,
            timestamp=datetime.now(),
            description="Memory usage spike"
        )

        data = violation.to_dict()

        assert isinstance(data, dict)
        assert data["violation_id"] == "test-003"
        assert "threat_level" in data
        assert "description" in data

    def test_violation_timestamp_formats(self):
        """Test SafetyViolation accepts different timestamp formats."""
        # Unix timestamp
        v1 = SafetyViolation(
            violation_id="v1",
            violation_type=SafetyViolationType.THRESHOLD_EXCEEDED,
            threat_level=ThreatLevel.LOW,
            timestamp=time.time(),
            description="Test"
        )
        assert v1.timestamp > 0

        # datetime object
        v2 = SafetyViolation(
            violation_id="v2",
            violation_type=SafetyViolationType.THRESHOLD_EXCEEDED,
            threat_level=ThreatLevel.LOW,
            timestamp=datetime.now(),
            description="Test"
        )
        assert v2.timestamp > 0


class TestIncidentReport:
    """Test IncidentReport class."""

    def test_create_incident_report(self):
        """Test creating an incident report."""
        report = IncidentReport(
            incident_id="INC-001",
            shutdown_reason=ShutdownReason.THRESHOLD,
            shutdown_timestamp=time.time(),
            violations=[],
            system_state_snapshot={"esgt_state": {}},
            metrics_timeline=[],
            recovery_possible=True,
            notes="Test incident"
        )

        assert report.incident_id == "INC-001"
        assert report.shutdown_reason == ShutdownReason.THRESHOLD

    def test_incident_report_to_dict(self):
        """Test IncidentReport.to_dict()."""
        report = IncidentReport(
            incident_id="INC-002",
            shutdown_reason=ShutdownReason.MANUAL,
            shutdown_timestamp=time.time(),
            violations=[],
            system_state_snapshot={},
            metrics_timeline=[],
            recovery_possible=False,
            notes="Manual shutdown"
        )

        data = report.to_dict()

        assert isinstance(data, dict)
        assert data["incident_id"] == "INC-002"
        assert "shutdown_timestamp" in data
        assert "shutdown_timestamp_iso" in data

    def test_incident_report_save(self):
        """Test IncidentReport.save()."""
        report = IncidentReport(
            incident_id="INC-003-test",
            shutdown_reason=ShutdownReason.ETHICAL,
            shutdown_timestamp=time.time(),
            violations=[],
            system_state_snapshot={},
            metrics_timeline=[],
            recovery_possible=False,
            notes="Ethical violation shutdown"
        )

        # save() should create a file
        with tempfile.TemporaryDirectory() as tmpdir:
            result = report.save(directory=Path(tmpdir))
            assert result is not None
            assert result.exists()


class TestStateSnapshot:
    """Test StateSnapshot class."""

    def test_create_state_snapshot(self):
        """Test creating a state snapshot."""
        snapshot = StateSnapshot(
            timestamp=datetime.now(),
            esgt_state={"arousal": 0.5},
            arousal_state={"value": 0.5},
            mmei_state={},
            tig_metrics={},
            recent_events=[],
            active_goals=[],
            violations=[]
        )

        assert snapshot.esgt_state["arousal"] == 0.5
        assert isinstance(snapshot.violations, list)

    def test_state_snapshot_to_dict(self):
        """Test StateSnapshot.to_dict()."""
        snapshot = StateSnapshot(
            timestamp=datetime.now(),
            esgt_state={},
            arousal_state={},
            mmei_state={},
            tig_metrics={},
            recent_events=[],
            active_goals=[],
            violations=[]
        )

        data = snapshot.to_dict()

        assert isinstance(data, dict)
        assert "timestamp" in data
        assert "esgt_state" in data

    def test_state_snapshot_from_dict_basic(self):
        """Test StateSnapshot.from_dict() with basic data."""
        data = {
            "timestamp": time.time(),
            "esgt_state": {"arousal": 0.7},
            "arousal_state": {},
            "mmei_state": {},
            "tig_metrics": {},
            "recent_events": [],
            "active_goals": [],
            "violations": []
        }

        snapshot = StateSnapshot.from_dict(data)

        assert snapshot.esgt_state["arousal"] == 0.7
        assert isinstance(snapshot.timestamp, datetime)

    def test_state_snapshot_from_dict_with_violations(self):
        """Test StateSnapshot.from_dict() with violation data."""
        violation_data = {
            "violation_id": "v1",
            "violation_type": "cpu_saturation",
            "severity": "warning",
            "description": "High CPU",
            "metrics": {"cpu": 85.0}
        }

        data = {
            "timestamp": datetime.now().isoformat(),
            "esgt_state": {},
            "arousal_state": {},
            "mmei_state": {},
            "tig_metrics": {},
            "recent_events": [],
            "active_goals": [],
            "violations": [violation_data]
        }

        snapshot = StateSnapshot.from_dict(data)

        assert len(snapshot.violations) == 1
        assert snapshot.violations[0].violation_id == "v1"


class TestKillSwitch:
    """Test KillSwitch class."""

    def test_kill_switch_initialization(self):
        """Test KillSwitch initialization."""
        mock_system = Mock()
        kill_switch = KillSwitch(consciousness_system=mock_system)

        assert kill_switch.armed == True
        assert kill_switch.triggered == False
        assert kill_switch.system == mock_system

    def test_kill_switch_trigger_basic(self):
        """Test basic kill switch trigger."""
        mock_system = Mock()
        kill_switch = KillSwitch(consciousness_system=mock_system)

        result = kill_switch.trigger(
            reason=ShutdownReason.THRESHOLD,
            context={"test": True}
        )

        assert kill_switch.triggered == True
        assert kill_switch.shutdown_reason == ShutdownReason.THRESHOLD
        assert result == True

    def test_kill_switch_idempotent(self):
        """Test kill switch cannot be triggered twice."""
        mock_system = Mock()
        kill_switch = KillSwitch(consciousness_system=mock_system)

        # First trigger
        result1 = kill_switch.trigger(
            reason=ShutdownReason.THRESHOLD,
            context={}
        )

        # Second trigger (should fail)
        result2 = kill_switch.trigger(
            reason=ShutdownReason.MANUAL,
            context={}
        )

        assert result1 == True
        assert result2 == False
        # Reason should remain the first one
        assert kill_switch.shutdown_reason == ShutdownReason.THRESHOLD

    @pytest.mark.timeout(2)
    def test_kill_switch_response_time(self):
        """CRITICAL: Test kill switch responds in <1s."""
        mock_system = Mock()
        kill_switch = KillSwitch(consciousness_system=mock_system)

        start = time.time()
        kill_switch.trigger(
            reason=ShutdownReason.TIMEOUT,
            context={}
        )
        elapsed = time.time() - start

        assert elapsed < 1.0, f"Kill switch took {elapsed:.3f}s (must be <1s)"


class TestThresholdMonitor:
    """Test ThresholdMonitor class."""

    def test_threshold_monitor_initialization(self):
        """Test ThresholdMonitor initialization."""
        thresholds = SafetyThresholds()
        monitor = ThresholdMonitor(thresholds=thresholds)

        assert monitor.thresholds == thresholds
        assert monitor.monitoring == False
        assert len(monitor.violations) == 0

    def test_check_arousal_sustained_within_bounds(self):
        """Test arousal check within safe bounds."""
        monitor = ThresholdMonitor(thresholds=SafetyThresholds())
        current_time = time.time()

        # Normal arousal
        violation = monitor.check_arousal_sustained(arousal_level=0.5, current_time=current_time)

        assert violation is None  # No violation

    def test_check_arousal_sustained_too_high(self):
        """Test arousal exceeding max threshold for sustained period."""
        thresholds = SafetyThresholds(arousal_max_duration_seconds=0.1)
        monitor = ThresholdMonitor(thresholds=thresholds)

        # Simulate sustained high arousal
        current_time = time.time()
        v1 = monitor.check_arousal_sustained(arousal_level=0.98, current_time=current_time)

        # First check might not violate (need duration)
        time.sleep(0.2)
        current_time = time.time()
        v2 = monitor.check_arousal_sustained(arousal_level=0.98, current_time=current_time)

        # Should violate after sustained period
        assert v2 is not None

    def test_check_esgt_frequency(self):
        """Test ESGT frequency checking."""
        monitor = ThresholdMonitor(thresholds=SafetyThresholds())
        current_time = time.time()

        # Normal frequency
        violation = monitor.check_esgt_frequency(current_time=current_time)
        assert violation is None

    def test_check_goal_spam(self):
        """Test goal spam detection."""
        monitor = ThresholdMonitor(thresholds=SafetyThresholds())
        current_time = time.time()

        # Normal goal generation
        violation = monitor.check_goal_spam(current_time=current_time)
        assert violation is None

    def test_check_resource_limits(self):
        """Test resource limit checking."""
        monitor = ThresholdMonitor(thresholds=SafetyThresholds())

        # Check resource limits
        violations = monitor.check_resource_limits()

        # Should return a list (empty if no violations)
        assert isinstance(violations, list)


class TestAnomalyDetector:
    """Test AnomalyDetector class."""

    def test_anomaly_detector_initialization(self):
        """Test AnomalyDetector initialization."""
        detector = AnomalyDetector(baseline_window=100)

        assert detector is not None
        assert detector.baseline_window == 100
        assert len(detector.anomalies_detected) == 0

    def test_detect_anomalies_empty_metrics(self):
        """Test anomaly detection with empty metrics."""
        detector = AnomalyDetector()

        # Empty metrics
        anomalies = detector.detect_anomalies(metrics={})

        # Should return empty list
        assert isinstance(anomalies, list)
        assert len(anomalies) == 0

    def test_detect_anomalies_normal_metrics(self):
        """Test anomaly detection with normal metrics."""
        detector = AnomalyDetector()

        # Normal metrics
        metrics = {
            "arousal": 0.5,
            "coherence": 0.7,
            "goal_rate": 2.0
        }

        anomalies = detector.detect_anomalies(metrics=metrics)

        # Should return list (might be empty if no baseline yet)
        assert isinstance(anomalies, list)


class TestConsciousnessSafetyProtocol:
    """Test ConsciousnessSafetyProtocol class."""

    def test_protocol_initialization(self):
        """Test ConsciousnessSafetyProtocol initialization."""
        mock_system = Mock()
        protocol = ConsciousnessSafetyProtocol(consciousness_system=mock_system)

        assert protocol is not None
        assert protocol.kill_switch is not None
        assert protocol.threshold_monitor is not None
        assert protocol.anomaly_detector is not None
        assert protocol.monitoring_active == False

    def test_protocol_with_custom_thresholds(self):
        """Test protocol initialization with custom thresholds."""
        mock_system = Mock()
        custom_thresholds = SafetyThresholds(arousal_max=0.85)

        protocol = ConsciousnessSafetyProtocol(
            consciousness_system=mock_system,
            thresholds=custom_thresholds
        )

        assert protocol.thresholds.arousal_max == 0.85

    @pytest.mark.asyncio
    async def test_protocol_handle_low_violation(self):
        """Test protocol handling of LOW violation."""
        mock_system = Mock()
        protocol = ConsciousnessSafetyProtocol(consciousness_system=mock_system)

        violation = SafetyViolation(
            violation_id="test-low",
            violation_type=SafetyViolationType.RESOURCE_EXHAUSTION,
            threat_level=ThreatLevel.LOW,
            timestamp=datetime.now(),
            description="Minor CPU spike"
        )

        # Call the internal handler
        await protocol._handle_violations([violation])

        # Should NOT trigger kill switch
        assert protocol.kill_switch.triggered == False

    @pytest.mark.asyncio
    async def test_protocol_handle_critical_violation(self):
        """Test protocol handling of CRITICAL violation."""
        mock_system = Mock()
        protocol = ConsciousnessSafetyProtocol(consciousness_system=mock_system)

        violation = SafetyViolation(
            violation_id="test-critical",
            violation_type=SafetyViolationType.ETHICAL_VIOLATION,
            threat_level=ThreatLevel.CRITICAL,
            timestamp=datetime.now(),
            description="Critical ethical violation"
        )

        # Call the internal handler
        await protocol._handle_violations([violation])

        # Should trigger kill switch
        assert protocol.kill_switch.triggered == True

    def test_protocol_monitors_arousal(self):
        """Test protocol can monitor arousal levels."""
        mock_system = Mock()
        protocol = ConsciousnessSafetyProtocol(consciousness_system=mock_system)
        current_time = time.time()

        # Check normal arousal
        violation = protocol.threshold_monitor.check_arousal_sustained(
            arousal_level=0.5,
            current_time=current_time
        )
        assert violation is None

    def test_protocol_collects_metrics(self):
        """Test protocol can collect system metrics."""
        mock_system = Mock()
        mock_system.get_system_dict = Mock(return_value={})

        protocol = ConsciousnessSafetyProtocol(consciousness_system=mock_system)

        # Collect metrics
        metrics = protocol._collect_metrics()

        assert isinstance(metrics, dict)


class TestKillSwitchAdvanced:
    """Advanced tests for KillSwitch internal methods."""

    def test_kill_switch_is_triggered(self):
        """Test is_triggered() method."""
        mock_system = Mock()
        kill_switch = KillSwitch(consciousness_system=mock_system)

        assert kill_switch.is_triggered() == False

        kill_switch.trigger(reason=ShutdownReason.MANUAL, context={})

        assert kill_switch.is_triggered() == True


class TestThresholdMonitorAdvanced:
    """Advanced tests for ThresholdMonitor detailed methods."""

    def test_check_self_modification_zero_tolerance(self):
        """Test zero tolerance for self-modification."""
        monitor = ThresholdMonitor(thresholds=SafetyThresholds())
        current_time = time.time()

        # ANY modification attempt should violate
        violation = monitor.check_self_modification(modification_attempts=1, current_time=current_time)

        assert violation is not None
        assert violation.threat_level == ThreatLevel.CRITICAL

    def test_check_self_modification_zero_attempts(self):
        """Test no violation when zero modification attempts."""
        monitor = ThresholdMonitor(thresholds=SafetyThresholds())
        current_time = time.time()

        # Zero attempts should NOT violate
        violation = monitor.check_self_modification(modification_attempts=0, current_time=current_time)
        assert violation is None

    def test_check_unexpected_goals(self):
        """Test unexpected goals checking."""
        monitor = ThresholdMonitor(thresholds=SafetyThresholds())
        current_time = time.time()

        # Normal goal count
        violation = monitor.check_unexpected_goals(goal_count=2, current_time=current_time)
        assert violation is None

        # Excessive goals
        violation = monitor.check_unexpected_goals(goal_count=10, current_time=current_time)
        assert violation is not None


class TestSafetyViolationAdvanced:
    """Advanced SafetyViolation tests."""

    def test_violation_legacy_properties(self):
        """Test backward-compatible legacy properties."""
        violation = SafetyViolation(
            violation_id="test-legacy",
            violation_type=ViolationType.AROUSAL_SUSTAINED_HIGH,
            severity=SafetyLevel.CRITICAL,
            timestamp=time.time(),
            description="Legacy test"
        )

        # Should have _severity
        assert violation._severity == SafetyLevel.CRITICAL

    def test_violation_with_metrics(self):
        """Test violation with metrics dict."""
        violation = SafetyViolation(
            violation_id="test-metrics",
            violation_type=SafetyViolationType.THRESHOLD_EXCEEDED,
            threat_level=ThreatLevel.MEDIUM,
            timestamp=time.time(),
            description="Test with metrics",
            metrics={"cpu": 85.5, "memory": 70.2}
        )

        assert violation.metrics["cpu"] == 85.5
        assert violation.metrics["memory"] == 70.2

    def test_violation_with_context(self):
        """Test violation with context."""
        violation = SafetyViolation(
            violation_id="test-context",
            violation_type=SafetyViolationType.ANOMALY_DETECTED,
            threat_level=ThreatLevel.HIGH,
            timestamp=time.time(),
            description="Anomaly detected",
            context={"source": "anomaly_detector", "baseline": 50.0},
            value_observed=95.0,
            threshold_violated=80.0
        )

        assert violation.context["source"] == "anomaly_detector"
        assert violation.value_observed == 95.0
        assert violation.threshold_violated == 80.0


# Mark all tests as safety-critical
pytestmark = pytest.mark.safety


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=consciousness.safety", "--cov-report=term-missing"])


class TestThresholdMonitorDetailedMethods:
    """Detailed tests for ThresholdMonitor specific methods."""

    def test_check_esgt_frequency_with_multiple_events(self):
        """Test ESGT frequency with multiple events in window."""
        monitor = ThresholdMonitor(thresholds=SafetyThresholds(esgt_frequency_max_hz=5.0))
        current_time = time.time()

        # Add events within window
        for i in range(6):
            monitor.esgt_events_window.append(current_time - i * 0.1)

        violation = monitor.check_esgt_frequency(current_time)

        # Should violate frequency threshold
        assert violation is not None

    def test_check_goal_spam_with_burst(self):
        """Test goal spam detection with burst of goals."""
        monitor = ThresholdMonitor(thresholds=SafetyThresholds())
        current_time = time.time()

        # Simulate goal burst
        for i in range(15):
            monitor.goals_generated.append(current_time - i * 0.5)

        violation = monitor.check_goal_spam(current_time)

        # Should detect spam
        assert violation is not None


class TestAnomalyDetectorMethods:
    """Test AnomalyDetector specific methods."""

    def test_detect_arousal_anomaly(self):
        """Test arousal anomaly detection."""
        detector = AnomalyDetector()

        # Build baseline
        for _ in range(50):
            detector.arousal_baseline.append(0.5)

        # Test with normal value
        metrics = {"arousal": 0.52}
        anomalies = detector.detect_anomalies(metrics)
        
        # Should be empty or minimal
        assert isinstance(anomalies, list)

    def test_detect_coherence_spike(self):
        """Test coherence spike detection."""
        detector = AnomalyDetector()

        # Build baseline
        for _ in range(50):
            detector.coherence_baseline.append(0.7)

        # Test with spike
        metrics = {"coherence": 0.95}
        anomalies = detector.detect_anomalies(metrics)

        assert isinstance(anomalies, list)


class TestConsciousnessSafetyProtocolAdvanced:
    """Advanced ConsciousnessSafetyProtocol tests."""

    @pytest.mark.asyncio
    async def test_protocol_start_stop_monitoring(self):
        """Test starting and stopping monitoring."""
        mock_system = Mock()
        protocol = ConsciousnessSafetyProtocol(consciousness_system=mock_system)

        assert protocol.monitoring_active == False

        await protocol.start_monitoring()

        assert protocol.monitoring_active == True
        assert protocol.monitoring_task is not None

        await protocol.stop_monitoring()

        assert protocol.monitoring_active == False

    def test_protocol_degradation_levels(self):
        """Test degradation level tracking."""
        mock_system = Mock()
        protocol = ConsciousnessSafetyProtocol(consciousness_system=mock_system)

        assert protocol.degradation_level == 0

        # Degradation level should be modifiable
        protocol.degradation_level = 1
        assert protocol.degradation_level == 1
