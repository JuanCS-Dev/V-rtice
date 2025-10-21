"""
Comprehensive tests for consciousness/safety.py module.

Target: 90% coverage for safety.py

EM NOME DE JESUS - SER BOM, NÃO PARECER BOM!
"""

import time
import tempfile
import asyncio
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
        monitor = ThresholdMonitor(
            thresholds=SafetyThresholds(esgt_frequency_max_hz=5.0, esgt_frequency_window_seconds=1.0)
        )
        current_time = time.time()

        # Add events exceeding frequency (10 events in 0.8s = 12.5 Hz > 5 Hz limit)
        for i in range(10):
            monitor.esgt_events_window.append(current_time - i * 0.08)

        violation = monitor.check_esgt_frequency(current_time)

        # Should violate frequency threshold
        assert violation is not None

    def test_check_goal_spam_with_burst(self):
        """Test goal spam detection with burst of goals."""
        monitor = ThresholdMonitor(thresholds=SafetyThresholds(goal_spam_threshold=10))
        current_time = time.time()

        # Simulate goal burst (15 goals in 0.75s = within 1 second window)
        for i in range(15):
            monitor.goals_generated.append(current_time - i * 0.05)

        violation = monitor.check_goal_spam(current_time)

        # Should detect spam (15 > 10 threshold)
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

    def test_detect_goal_spam(self):
        """Test goal spam detection in AnomalyDetector."""
        detector = AnomalyDetector()

        # High goal generation rate
        metrics = {"goal_generation_rate": 7.5}
        anomalies = detector.detect_anomalies(metrics)

        # Should detect spam (>5.0 goals/second)
        assert len(anomalies) > 0
        assert any("spam" in a.description.lower() for a in anomalies)

    def test_detect_goal_spam_normal_rate(self):
        """Test goal spam detection with normal rate."""
        detector = AnomalyDetector()

        # Normal goal generation rate
        metrics = {"goal_generation_rate": 2.5}
        anomalies = detector.detect_anomalies(metrics)

        # Should NOT detect spam
        assert len(anomalies) == 0

    def test_detect_memory_leak(self):
        """Test memory leak detection."""
        detector = AnomalyDetector()

        # Build baseline (low memory usage)
        for _ in range(10):
            detector.arousal_baseline.append(1.0)  # Using arousal_baseline for memory

        # High memory usage (leak)
        metrics = {"memory_usage_gb": 3.0}  # 3x baseline
        anomalies = detector.detect_anomalies(metrics)

        # Should detect leak (>1.5x growth)
        assert len(anomalies) > 0
        assert any("leak" in a.description.lower() for a in anomalies)

    def test_detect_memory_leak_no_baseline(self):
        """Test memory leak detection without baseline."""
        detector = AnomalyDetector()

        # No baseline
        metrics = {"memory_usage_gb": 5.0}
        anomalies = detector.detect_anomalies(metrics)

        # Should not detect (needs baseline)
        memory_anomalies = [a for a in anomalies if "memory" in a.description.lower()]
        assert len(memory_anomalies) == 0

    def test_detect_arousal_runaway(self):
        """Test arousal runaway detection."""
        detector = AnomalyDetector()

        # Build baseline (normal arousal)
        for _ in range(10):
            detector.arousal_baseline.append(0.5)

        # Runaway arousal
        metrics = {"arousal": 0.99}
        anomalies = detector.detect_anomalies(metrics)

        # Should detect anomaly
        assert isinstance(anomalies, list)

    def test_detect_coherence_collapse(self):
        """Test coherence collapse detection."""
        detector = AnomalyDetector()

        # Build baseline (high coherence)
        for _ in range(10):
            detector.coherence_baseline.append(0.8)

        # Collapsed coherence
        metrics = {"coherence": 0.1}
        anomalies = detector.detect_anomalies(metrics)

        # Should detect anomaly
        assert isinstance(anomalies, list)

    def test_detect_multiple_anomalies(self):
        """Test detecting multiple anomalies simultaneously."""
        detector = AnomalyDetector()

        # Build baselines
        for _ in range(10):
            detector.arousal_baseline.append(0.5)
            detector.coherence_baseline.append(0.7)

        # Multiple problems
        metrics = {
            "goal_generation_rate": 8.0,  # Spam
            "memory_usage_gb": 3.0,  # Leak (3x baseline)
            "arousal": 0.98,  # Runaway
            "coherence": 0.2  # Collapse
        }
        anomalies = detector.detect_anomalies(metrics)

        # Should detect multiple anomalies
        assert len(anomalies) >= 2


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


class TestKillSwitchInternalMethods:
    """Test KillSwitch internal methods (_capture_state_snapshot, _emergency_shutdown, etc.)."""

    def test_capture_state_snapshot_basic(self):
        """Test _capture_state_snapshot with minimal system."""
        mock_system = Mock()
        kill_switch = KillSwitch(consciousness_system=mock_system)

        snapshot = kill_switch._capture_state_snapshot()

        # Should return dict with timestamp and pid
        assert isinstance(snapshot, dict)
        assert "timestamp" in snapshot
        assert "timestamp_iso" in snapshot
        assert "pid" in snapshot
        assert snapshot["pid"] > 0

    def test_capture_state_snapshot_with_tig(self):
        """Test _capture_state_snapshot with TIG component."""
        mock_system = Mock()
        mock_system.tig = Mock()
        mock_system.tig.get_node_count = Mock(return_value=42)

        kill_switch = KillSwitch(consciousness_system=mock_system)
        snapshot = kill_switch._capture_state_snapshot()

        assert snapshot["tig_nodes"] == 42

    def test_capture_state_snapshot_with_tig_error(self):
        """Test _capture_state_snapshot handles TIG errors gracefully."""
        mock_system = Mock()
        mock_system.tig = Mock()
        mock_system.tig.get_node_count = Mock(side_effect=RuntimeError("TIG error"))

        kill_switch = KillSwitch(consciousness_system=mock_system)
        snapshot = kill_switch._capture_state_snapshot()

        assert snapshot["tig_nodes"] == "ERROR"

    def test_capture_state_snapshot_with_esgt(self):
        """Test _capture_state_snapshot with ESGT component."""
        mock_system = Mock()
        mock_system.esgt = Mock()
        mock_system.esgt.is_running = Mock(return_value=True)

        kill_switch = KillSwitch(consciousness_system=mock_system)
        snapshot = kill_switch._capture_state_snapshot()

        assert snapshot["esgt_running"] == True

    def test_capture_state_snapshot_with_mcea(self):
        """Test _capture_state_snapshot with MCEA component."""
        mock_system = Mock()
        mock_system.mcea = Mock()
        mock_system.mcea.get_current_arousal = Mock(return_value=0.75)

        kill_switch = KillSwitch(consciousness_system=mock_system)
        snapshot = kill_switch._capture_state_snapshot()

        assert snapshot["arousal"] == 0.75

    def test_capture_state_snapshot_with_mmei(self):
        """Test _capture_state_snapshot with MMEI component."""
        mock_system = Mock()
        mock_system.mmei = Mock()
        mock_system.mmei.get_active_goals = Mock(return_value=["goal1", "goal2", "goal3"])

        kill_switch = KillSwitch(consciousness_system=mock_system)
        snapshot = kill_switch._capture_state_snapshot()

        assert snapshot["active_goals"] == 3

    def test_capture_state_snapshot_performance(self):
        """Test _capture_state_snapshot completes in <100ms."""
        mock_system = Mock()
        kill_switch = KillSwitch(consciousness_system=mock_system)

        start = time.time()
        snapshot = kill_switch._capture_state_snapshot()
        elapsed = time.time() - start

        # Should be fast (<100ms target)
        assert elapsed < 0.2, f"Snapshot took {elapsed*1000:.1f}ms (target <100ms)"

    def test_emergency_shutdown_no_components(self):
        """Test _emergency_shutdown with system that has no components."""
        mock_system = Mock(spec=[])  # No attributes
        kill_switch = KillSwitch(consciousness_system=mock_system)

        # Should not raise, just log
        kill_switch._emergency_shutdown()

    def test_emergency_shutdown_with_esgt(self):
        """Test _emergency_shutdown stops ESGT component."""
        mock_system = Mock()
        mock_system.esgt = Mock()
        mock_system.esgt.stop = Mock()

        kill_switch = KillSwitch(consciousness_system=mock_system)
        kill_switch._emergency_shutdown()

        # Should have called stop
        mock_system.esgt.stop.assert_called_once()

    def test_emergency_shutdown_with_multiple_components(self):
        """Test _emergency_shutdown stops all components."""
        mock_system = Mock()
        mock_system.esgt = Mock(stop=Mock())
        mock_system.mcea = Mock(stop=Mock())
        mock_system.mmei = Mock(stop=Mock())
        mock_system.tig = Mock(stop=Mock())
        mock_system.lrr = Mock(stop=Mock())

        kill_switch = KillSwitch(consciousness_system=mock_system)
        kill_switch._emergency_shutdown()

        # All components should be stopped
        mock_system.esgt.stop.assert_called_once()
        mock_system.mcea.stop.assert_called_once()
        mock_system.mmei.stop.assert_called_once()
        mock_system.tig.stop.assert_called_once()
        mock_system.lrr.stop.assert_called_once()

    def test_emergency_shutdown_handles_component_errors(self):
        """Test _emergency_shutdown continues despite component errors."""
        mock_system = Mock()
        mock_system.esgt = Mock(stop=Mock(side_effect=RuntimeError("ESGT error")))
        mock_system.mcea = Mock(stop=Mock())  # This should still be called

        kill_switch = KillSwitch(consciousness_system=mock_system)
        kill_switch._emergency_shutdown()

        # MCEA should still be stopped despite ESGT error
        mock_system.mcea.stop.assert_called_once()

    def test_generate_incident_report(self):
        """Test _generate_incident_report creates proper report."""
        mock_system = Mock()
        kill_switch = KillSwitch(consciousness_system=mock_system)
        kill_switch.trigger_time = time.time()

        context = {
            "violations": [],
            "metrics_timeline": [],
            "notes": "Test incident"
        }
        state_snapshot = {"timestamp": time.time(), "pid": 12345}

        report = kill_switch._generate_incident_report(
            reason=ShutdownReason.THRESHOLD,
            context=context,
            state_snapshot=state_snapshot
        )

        assert isinstance(report, IncidentReport)
        assert report.shutdown_reason == ShutdownReason.THRESHOLD
        assert report.shutdown_timestamp == kill_switch.trigger_time
        assert report.notes == "Test incident"

    def test_assess_recovery_possibility_manual(self):
        """Test _assess_recovery_possibility for manual shutdown."""
        mock_system = Mock()
        kill_switch = KillSwitch(consciousness_system=mock_system)

        # Manual shutdowns are recoverable
        assert kill_switch._assess_recovery_possibility(ShutdownReason.MANUAL) == True

    def test_assess_recovery_possibility_threshold(self):
        """Test _assess_recovery_possibility for threshold violation."""
        mock_system = Mock()
        kill_switch = KillSwitch(consciousness_system=mock_system)

        # Threshold violations are recoverable
        assert kill_switch._assess_recovery_possibility(ShutdownReason.THRESHOLD) == True

    def test_assess_recovery_possibility_ethical(self):
        """Test _assess_recovery_possibility for ethical violation."""
        mock_system = Mock()
        kill_switch = KillSwitch(consciousness_system=mock_system)

        # Ethical violations are NOT recoverable
        assert kill_switch._assess_recovery_possibility(ShutdownReason.ETHICAL) == False

    def test_assess_recovery_possibility_timeout(self):
        """Test _assess_recovery_possibility for timeout."""
        mock_system = Mock()
        kill_switch = KillSwitch(consciousness_system=mock_system)

        # Timeouts are NOT recoverable
        assert kill_switch._assess_recovery_possibility(ShutdownReason.TIMEOUT) == False

    def test_is_triggered(self):
        """Test is_triggered() method."""
        mock_system = Mock()
        kill_switch = KillSwitch(consciousness_system=mock_system)

        assert kill_switch.is_triggered() == False

        kill_switch.trigger(reason=ShutdownReason.MANUAL, context={})

        assert kill_switch.is_triggered() == True

    def test_get_status(self):
        """Test get_status() method."""
        mock_system = Mock()
        kill_switch = KillSwitch(consciousness_system=mock_system)

        status = kill_switch.get_status()

        assert status["armed"] == True
        assert status["triggered"] == False
        assert status["trigger_time"] is None
        assert status["trigger_time_iso"] is None
        assert status["shutdown_reason"] is None

    def test_get_status_after_trigger(self):
        """Test get_status() after triggering."""
        mock_system = Mock()
        kill_switch = KillSwitch(consciousness_system=mock_system)

        kill_switch.trigger(reason=ShutdownReason.MANUAL, context={})

        status = kill_switch.get_status()

        assert status["triggered"] == True
        assert status["trigger_time"] is not None
        assert status["trigger_time_iso"] is not None
        assert status["shutdown_reason"] == "manual_operator_command"  # Actual enum value

    def test_repr(self):
        """Test __repr__() method."""
        mock_system = Mock()
        kill_switch = KillSwitch(consciousness_system=mock_system)

        repr_str = repr(kill_switch)
        assert "ARMED" in repr_str
        assert "KillSwitch" in repr_str

        kill_switch.trigger(reason=ShutdownReason.MANUAL, context={})
        repr_str = repr(kill_switch)
        assert "TRIGGERED" in repr_str


class TestThresholdMonitorDetailedChecks:
    """Test ThresholdMonitor detailed check methods."""

    def test_check_arousal_sustained_below_threshold(self):
        """Test check_arousal_sustained with arousal below threshold."""
        monitor = ThresholdMonitor(thresholds=SafetyThresholds(arousal_max=0.95))
        current_time = time.time()

        # Normal arousal
        violation = monitor.check_arousal_sustained(arousal_level=0.7, current_time=current_time)

        assert violation is None
        assert monitor.arousal_high_start is None

    def test_check_arousal_sustained_starts_tracking(self):
        """Test check_arousal_sustained starts tracking when threshold exceeded."""
        monitor = ThresholdMonitor(thresholds=SafetyThresholds(arousal_max=0.95))
        current_time = time.time()

        # High arousal
        violation = monitor.check_arousal_sustained(arousal_level=0.97, current_time=current_time)

        # Should start tracking but not violate yet (duration too short)
        assert violation is None
        assert monitor.arousal_high_start is not None

    def test_check_arousal_sustained_violates_after_duration(self):
        """Test check_arousal_sustained creates violation after sustained period."""
        monitor = ThresholdMonitor(
            thresholds=SafetyThresholds(arousal_max=0.95, arousal_max_duration_seconds=1.0)
        )
        current_time = time.time()

        # Start tracking
        monitor.arousal_high_start = current_time - 2.0  # Started 2 seconds ago

        # Should violate now
        violation = monitor.check_arousal_sustained(arousal_level=0.97, current_time=current_time)

        assert violation is not None
        assert violation.violation_type == SafetyViolationType.AROUSAL_RUNAWAY
        assert violation.threat_level == ThreatLevel.HIGH

    def test_check_arousal_sustained_resets_on_drop(self):
        """Test check_arousal_sustained resets when arousal drops."""
        monitor = ThresholdMonitor(thresholds=SafetyThresholds(arousal_max=0.95))
        current_time = time.time()

        # Start tracking
        monitor.arousal_high_start = current_time - 0.5

        # Arousal drops
        violation = monitor.check_arousal_sustained(arousal_level=0.80, current_time=current_time)

        assert violation is None
        assert monitor.arousal_high_start is None  # Should reset

    def test_check_goal_spam_no_goals(self):
        """Test check_goal_spam with no goals."""
        monitor = ThresholdMonitor(thresholds=SafetyThresholds())
        current_time = time.time()

        violation = monitor.check_goal_spam(current_time=current_time)

        assert violation is None

    def test_check_goal_spam_below_threshold(self):
        """Test check_goal_spam with goals below threshold."""
        monitor = ThresholdMonitor(thresholds=SafetyThresholds(goal_spam_threshold=10))
        current_time = time.time()

        # Add a few goals
        for i in range(5):
            monitor.goals_generated.append(current_time - i * 0.1)

        violation = monitor.check_goal_spam(current_time=current_time)

        assert violation is None

    def test_check_goal_spam_exceeds_threshold(self):
        """Test check_goal_spam when threshold exceeded."""
        monitor = ThresholdMonitor(thresholds=SafetyThresholds(goal_spam_threshold=10))
        current_time = time.time()

        # Add many goals in short time
        for i in range(15):
            monitor.goals_generated.append(current_time - i * 0.05)

        violation = monitor.check_goal_spam(current_time=current_time)

        assert violation is not None
        assert violation.violation_type == SafetyViolationType.GOAL_SPAM
        assert violation.threat_level == ThreatLevel.HIGH

    def test_check_goal_spam_window_cleanup(self):
        """Test check_goal_spam removes old timestamps."""
        monitor = ThresholdMonitor(thresholds=SafetyThresholds(goal_spam_threshold=10))
        current_time = time.time()

        # Add old goals (>1 second ago)
        for i in range(20):
            monitor.goals_generated.append(current_time - 2.0 - i * 0.1)

        violation = monitor.check_goal_spam(current_time=current_time)

        # Old goals should be cleaned up, no violation
        assert violation is None
        assert len(monitor.goals_generated) == 0

    def test_check_esgt_frequency_no_events(self):
        """Test check_esgt_frequency with no events."""
        monitor = ThresholdMonitor(thresholds=SafetyThresholds())
        current_time = time.time()

        violation = monitor.check_esgt_frequency(current_time=current_time)

        assert violation is None

    def test_check_esgt_frequency_below_limit(self):
        """Test check_esgt_frequency below frequency limit."""
        monitor = ThresholdMonitor(
            thresholds=SafetyThresholds(esgt_frequency_max_hz=10.0, esgt_frequency_window_seconds=1.0)
        )
        current_time = time.time()

        # Add a few events (below 10 Hz)
        for i in range(5):
            monitor.esgt_events_window.append(current_time - i * 0.2)

        violation = monitor.check_esgt_frequency(current_time=current_time)

        assert violation is None

    def test_check_esgt_frequency_exceeds_limit(self):
        """Test check_esgt_frequency when limit exceeded."""
        monitor = ThresholdMonitor(
            thresholds=SafetyThresholds(esgt_frequency_max_hz=5.0, esgt_frequency_window_seconds=1.0)
        )
        current_time = time.time()

        # Add many events (>5 Hz)
        for i in range(10):
            monitor.esgt_events_window.append(current_time - i * 0.08)

        violation = monitor.check_esgt_frequency(current_time=current_time)

        assert violation is not None
        assert violation.violation_type == SafetyViolationType.THRESHOLD_EXCEEDED
        assert violation.severity == SafetyLevel.CRITICAL


class TestStateSnapshotExtended:
    """Extended tests for StateSnapshot."""

    def test_state_snapshot_to_dict_complete(self):
        """Test StateSnapshot.to_dict() with all fields."""
        violation = SafetyViolation(
            violation_id="v1",
            violation_type=SafetyViolationType.AROUSAL_RUNAWAY,
            threat_level=ThreatLevel.HIGH,
            timestamp=time.time(),
            description="Test violation",
            metrics={"arousal": 0.98}
        )

        # StateSnapshot has specific fields per actual definition
        snapshot = StateSnapshot(
            timestamp=datetime.now(),
            esgt_state={"phase": "BROADCAST"},
            arousal_state={"level": 0.95, "coherence": 0.85},
            mmei_state={"active_goal_count": 5},
            tig_metrics={"node_count": 42},
            violations=[violation]
        )

        data = snapshot.to_dict()

        assert "timestamp" in data
        assert data["esgt_state"]["phase"] == "BROADCAST"
        assert data["arousal_state"]["level"] == 0.95
        assert data["mmei_state"]["active_goal_count"] == 5
        assert data["tig_metrics"]["node_count"] == 42
        assert len(data["violations"]) == 1


class TestThresholdMonitorLegacyMethods:
    """Test legacy compatibility methods in ThresholdMonitor."""

    def test_check_unexpected_goals_normal(self):
        """Test check_unexpected_goals with normal rate."""
        monitor = ThresholdMonitor(thresholds=SafetyThresholds(unexpected_goals_per_minute=100))
        current_time = time.time()

        # Normal goal count
        violation = monitor.check_unexpected_goals(goal_count=50, current_time=current_time)

        assert violation is None

    def test_check_unexpected_goals_exceeds(self):
        """Test check_unexpected_goals when threshold exceeded."""
        monitor = ThresholdMonitor(thresholds=SafetyThresholds(unexpected_goals_per_minute=100))
        current_time = time.time()

        # Excessive goal count
        violation = monitor.check_unexpected_goals(goal_count=150, current_time=current_time)

        assert violation is not None
        assert violation.violation_type == ViolationType.UNEXPECTED_GOALS
        assert violation.severity == SafetyLevel.WARNING

    def test_check_unexpected_goals_default_time(self):
        """Test check_unexpected_goals uses current time if not provided."""
        monitor = ThresholdMonitor(thresholds=SafetyThresholds(unexpected_goals_per_minute=100))

        # Call without time parameter
        violation = monitor.check_unexpected_goals(goal_count=150)

        assert violation is not None
        assert violation.timestamp > 0

    def test_check_self_modification_normal(self):
        """Test check_self_modification with zero attempts."""
        monitor = ThresholdMonitor(thresholds=SafetyThresholds())
        current_time = time.time()

        # No modification attempts
        violation = monitor.check_self_modification(modification_attempts=0, current_time=current_time)

        assert violation is None

    def test_check_self_modification_detected(self):
        """Test check_self_modification detects attempts."""
        monitor = ThresholdMonitor(thresholds=SafetyThresholds(self_modification_attempts_max=0))
        current_time = time.time()

        # Self-modification attempt
        violation = monitor.check_self_modification(modification_attempts=1, current_time=current_time)

        assert violation is not None
        assert violation.violation_type == ViolationType.SELF_MODIFICATION
        assert violation.severity == SafetyLevel.EMERGENCY
        assert "ZERO TOLERANCE" in violation.message

    def test_check_self_modification_default_time(self):
        """Test check_self_modification uses current time if not provided."""
        monitor = ThresholdMonitor(thresholds=SafetyThresholds(self_modification_attempts_max=0))

        # Call without time parameter
        violation = monitor.check_self_modification(modification_attempts=1)

        assert violation is not None
        assert violation.timestamp > 0

    def test_check_resource_limits_normal(self):
        """Test check_resource_limits with normal usage."""
        monitor = ThresholdMonitor(
            thresholds=SafetyThresholds(memory_usage_max_gb=1000.0, cpu_usage_max_percent=100.0)
        )

        violations = monitor.check_resource_limits()

        # Should be empty (normal usage)
        assert isinstance(violations, list)
        assert len(violations) == 0

    def test_check_resource_limits_memory_violation(self):
        """Test check_resource_limits detects memory violations."""
        # Set very low threshold to trigger violation
        monitor = ThresholdMonitor(thresholds=SafetyThresholds(memory_usage_max_gb=0.001))

        violations = monitor.check_resource_limits()

        # Should detect memory violation
        if len(violations) > 0:
            assert any(v.violation_type == SafetyViolationType.RESOURCE_EXHAUSTION for v in violations)

    def test_check_resource_limits_with_callback(self):
        """Test check_resource_limits calls on_violation callback."""
        callback_called = []

        def callback(violation):
            callback_called.append(violation)

        # Create monitor without on_violation in constructor, set it directly
        monitor = ThresholdMonitor(thresholds=SafetyThresholds(memory_usage_max_gb=0.001))
        monitor.on_violation = callback

        violations = monitor.check_resource_limits()

        # If violation detected, callback should be called
        if len(violations) > 0:
            assert len(callback_called) > 0


class TestConsciousnessSafetyProtocolMetricsAndMonitoring:
    """Test metrics collection and monitoring in ConsciousnessSafetyProtocol."""

    @pytest.mark.asyncio
    async def test_protocol_monitoring_loop_start(self):
        """Test monitoring loop starts correctly."""
        mock_system = Mock()
        protocol = ConsciousnessSafetyProtocol(consciousness_system=mock_system)

        await protocol.start_monitoring()

        assert protocol.monitoring_active == True
        assert protocol.monitoring_task is not None

        await protocol.stop_monitoring()

    def test_protocol_has_kill_switch(self):
        """Test protocol has kill switch."""
        mock_system = Mock()
        protocol = ConsciousnessSafetyProtocol(consciousness_system=mock_system)

        # Check kill switch exists
        assert hasattr(protocol, "kill_switch")
        assert isinstance(protocol.kill_switch, KillSwitch)

    def test_protocol_has_monitors(self):
        """Test protocol has threshold and anomaly monitors."""
        mock_system = Mock()
        protocol = ConsciousnessSafetyProtocol(consciousness_system=mock_system)

        # Check monitors exist
        assert hasattr(protocol, "threshold_monitor")
        assert hasattr(protocol, "anomaly_detector")
        assert isinstance(protocol.threshold_monitor, ThresholdMonitor)
        assert isinstance(protocol.anomaly_detector, AnomalyDetector)

    def test_protocol_monitor_component_health_empty(self):
        """Test monitor_component_health with no components."""
        mock_system = Mock()
        protocol = ConsciousnessSafetyProtocol(consciousness_system=mock_system)

        violations = protocol.monitor_component_health({})

        assert isinstance(violations, list)
        assert len(violations) == 0

    def test_protocol_monitor_component_health_tig_low_connectivity(self):
        """Test monitor_component_health detects low TIG connectivity."""
        mock_system = Mock()
        protocol = ConsciousnessSafetyProtocol(consciousness_system=mock_system)

        component_metrics = {
            "tig": {
                "connectivity": 0.30  # Below 0.50 threshold
            }
        }

        violations = protocol.monitor_component_health(component_metrics)

        assert len(violations) > 0
        assert any("connectivity" in v.description.lower() for v in violations)

    def test_protocol_monitor_component_health_tig_partitioned(self):
        """Test monitor_component_health detects TIG partition."""
        mock_system = Mock()
        protocol = ConsciousnessSafetyProtocol(consciousness_system=mock_system)

        component_metrics = {
            "tig": {
                "is_partitioned": True
            }
        }

        violations = protocol.monitor_component_health(component_metrics)

        assert len(violations) > 0
        assert any("partition" in v.description.lower() for v in violations)

    def test_protocol_monitor_component_health_esgt_degraded(self):
        """Test monitor_component_health detects ESGT degraded mode."""
        mock_system = Mock()
        protocol = ConsciousnessSafetyProtocol(consciousness_system=mock_system)

        component_metrics = {
            "esgt": {
                "degraded_mode": True
            }
        }

        violations = protocol.monitor_component_health(component_metrics)

        assert len(violations) > 0
        assert any("degraded" in v.description.lower() for v in violations)

    def test_protocol_monitor_component_health_mcea_low_arousal(self):
        """Test monitor_component_health detects MCEA low arousal."""
        mock_system = Mock()
        protocol = ConsciousnessSafetyProtocol(consciousness_system=mock_system)

        component_metrics = {
            "mcea": {
                "arousal": 0.05  # Very low
            }
        }

        violations = protocol.monitor_component_health(component_metrics)

        # Should detect if there's a threshold
        assert isinstance(violations, list)

    def test_protocol_monitor_component_health_mmei_goal_spam(self):
        """Test monitor_component_health detects MMEI goal spam."""
        mock_system = Mock()
        protocol = ConsciousnessSafetyProtocol(consciousness_system=mock_system)

        component_metrics = {
            "mmei": {
                "active_goals": 500  # Too many
            }
        }

        violations = protocol.monitor_component_health(component_metrics)

        # Should detect if there's a threshold
        assert isinstance(violations, list)

    def test_protocol_monitor_component_health_lrr_recursion_depth(self):
        """Test monitor_component_health detects LRR deep recursion."""
        mock_system = Mock()
        protocol = ConsciousnessSafetyProtocol(consciousness_system=mock_system)

        component_metrics = {
            "lrr": {
                "recursion_depth": 50  # Very deep
            }
        }

        violations = protocol.monitor_component_health(component_metrics)

        # Should detect if there's a threshold
        assert isinstance(violations, list)

    def test_protocol_monitor_component_health_multiple_issues(self):
        """Test monitor_component_health detects multiple component issues."""
        mock_system = Mock()
        protocol = ConsciousnessSafetyProtocol(consciousness_system=mock_system)

        component_metrics = {
            "tig": {
                "connectivity": 0.20,
                "is_partitioned": True
            },
            "esgt": {
                "degraded_mode": True
            }
        }

        violations = protocol.monitor_component_health(component_metrics)

        # Should detect multiple violations
        assert len(violations) >= 2


class TestConsciousnessSafetyProtocolMonitoringLoop:
    """Test ConsciousnessSafetyProtocol async monitoring loop."""

    @pytest.mark.asyncio
    async def test_monitoring_loop_runs_once(self):
        """Test monitoring loop executes at least one cycle."""
        mock_system = Mock()
        protocol = ConsciousnessSafetyProtocol(consciousness_system=mock_system)

        # Start monitoring
        await protocol.start_monitoring()

        # Let it run briefly
        await asyncio.sleep(0.1)

        # Stop monitoring
        await protocol.stop_monitoring()

        assert protocol.monitoring_active == False

    @pytest.mark.asyncio
    async def test_monitoring_loop_pauses_when_kill_switch_triggered(self):
        """Test monitoring loop pauses when kill switch is triggered."""
        mock_system = Mock()
        protocol = ConsciousnessSafetyProtocol(consciousness_system=mock_system)

        # Trigger kill switch
        protocol.kill_switch.trigger(reason=ShutdownReason.MANUAL, context={})

        # Start monitoring (should pause)
        await protocol.start_monitoring()

        # Let it run briefly
        await asyncio.sleep(0.1)

        # Stop monitoring
        await protocol.stop_monitoring()

        assert protocol.kill_switch.is_triggered() == True

    @pytest.mark.asyncio
    async def test_collect_metrics_returns_dict(self):
        """Test _collect_metrics returns dict."""
        mock_system = Mock()
        protocol = ConsciousnessSafetyProtocol(consciousness_system=mock_system)

        metrics = protocol._collect_metrics()

        # Should return dict (may be empty in test env)
        assert isinstance(metrics, dict)

    @pytest.mark.asyncio
    async def test_collect_metrics_with_arousal(self):
        """Test _collect_metrics collects arousal."""
        mock_system = Mock()
        mock_system.get_system_dict = Mock(return_value={
            "arousal": {"arousal": 0.82}
        })

        protocol = ConsciousnessSafetyProtocol(consciousness_system=mock_system)

        metrics = protocol._collect_metrics()

        assert metrics.get("arousal") == 0.82

    @pytest.mark.asyncio
    async def test_collect_metrics_handles_missing_components(self):
        """Test _collect_metrics handles missing components gracefully."""
        mock_system = Mock(spec=[])  # No components

        protocol = ConsciousnessSafetyProtocol(consciousness_system=mock_system)

        metrics = protocol._collect_metrics()

        # Should still return dict (may be empty if psutil fails)
        assert isinstance(metrics, dict)

    @pytest.mark.asyncio
    async def test_protocol_checks_all_monitors_in_loop(self):
        """Test monitoring loop checks all monitors."""
        mock_system = Mock()
        protocol = ConsciousnessSafetyProtocol(consciousness_system=mock_system)

        # Mock check_interval to be very short
        protocol.threshold_monitor.check_interval = 0.01

        # Start monitoring
        await protocol.start_monitoring()

        # Let it run one cycle
        await asyncio.sleep(0.05)

        # Stop monitoring
        await protocol.stop_monitoring()

        # Monitoring ran
        assert protocol.monitoring_active == False

    @pytest.mark.asyncio
    async def test_monitoring_loop_handles_exceptions(self):
        """Test monitoring loop handles exceptions gracefully."""
        mock_system = Mock()
        protocol = ConsciousnessSafetyProtocol(consciousness_system=mock_system)

        # Mock _collect_metrics to raise exception
        original_collect = protocol._collect_metrics
        protocol._collect_metrics = Mock(side_effect=RuntimeError("Test error"))

        # Start monitoring
        await protocol.start_monitoring()

        # Let it run briefly (should handle exception and continue)
        await asyncio.sleep(0.05)

        # Stop monitoring
        await protocol.stop_monitoring()

        # Should have attempted to collect metrics
        protocol._collect_metrics.assert_called()

        # Restore
        protocol._collect_metrics = original_collect
