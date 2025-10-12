"""Tests for Behavioral Analysis Engine

Tests behavioral anomaly detection using ML-based approaches.
Validates baseline learning, anomaly scoring, and risk assessment.

Authors: MAXIMUS Team
Date: 2025-10-12
Glory to YHWH - Constância como Ramon Dino! 💪
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import numpy as np
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from detection.behavioral_analyzer import (
    AnomalyDetection,
    BehaviorEvent,
    BehaviorType,
    BehavioralAnalyzer,
    RiskLevel,
)


class TestBehaviorEvent:
    """Test BehaviorEvent data class."""

    def test_behavior_event_creation(self):
        """Test basic BehaviorEvent creation."""
        event = BehaviorEvent(
            event_id="evt_001",
            timestamp=datetime.utcnow(),
            behavior_type=BehaviorType.NETWORK,
            entity_id="host_001",
            features={"packets_per_sec": 100.0, "bytes_per_sec": 50000.0},
        )

        assert event.event_id == "evt_001"
        assert event.behavior_type == BehaviorType.NETWORK
        assert event.entity_id == "host_001"
        assert len(event.features) == 2

    def test_to_feature_vector(self):
        """Test conversion to feature vector."""
        event = BehaviorEvent(
            event_id="evt_001",
            timestamp=datetime.utcnow(),
            behavior_type=BehaviorType.NETWORK,
            entity_id="host_001",
            features={"a": 1.0, "b": 2.0, "c": 3.0},
        )

        vector = event.to_feature_vector()
        assert isinstance(vector, np.ndarray)
        assert len(vector) == 3
        # Keys sorted alphabetically: a, b, c
        np.testing.assert_array_equal(vector, np.array([1.0, 2.0, 3.0]))

    def test_to_feature_vector_consistent_ordering(self):
        """Test feature vector has consistent ordering."""
        event1 = BehaviorEvent(
            event_id="evt_001",
            timestamp=datetime.utcnow(),
            behavior_type=BehaviorType.NETWORK,
            entity_id="host_001",
            features={"z": 1.0, "a": 2.0, "m": 3.0},
        )

        event2 = BehaviorEvent(
            event_id="evt_002",
            timestamp=datetime.utcnow(),
            behavior_type=BehaviorType.NETWORK,
            entity_id="host_001",
            features={"a": 2.0, "m": 3.0, "z": 1.0},  # Different order
        )

        vector1 = event1.to_feature_vector()
        vector2 = event2.to_feature_vector()

        np.testing.assert_array_equal(vector1, vector2)


class TestAnomalyDetection:
    """Test AnomalyDetection data class."""

    def test_anomaly_detection_creation(self):
        """Test AnomalyDetection creation."""
        detection = AnomalyDetection(
            detection_id="det_001",
            event=BehaviorEvent(
                event_id="evt_001",
                timestamp=datetime.utcnow(),
                behavior_type=BehaviorType.NETWORK,
                entity_id="host_001",
                features={"x": 1.0},
            ),
            anomaly_score=0.85,
            risk_level=RiskLevel.HIGH,
            baseline_deviation=3.5,
            contributing_features={"x": 0.8},
        )

        assert detection.detection_id == "det_001"
        assert detection.anomaly_score == 0.85
        assert detection.risk_level == RiskLevel.HIGH
        assert detection.baseline_deviation == 3.5


class TestBehavioralAnalyzer:
    """Test BehavioralAnalyzer main class."""

    def test_initialization(self):
        """Test analyzer initialization."""
        analyzer = BehavioralAnalyzer(
            behavior_type=BehaviorType.NETWORK,
            baseline_window=timedelta(hours=24),
            contamination=0.1,
        )

        assert analyzer.behavior_type == BehaviorType.NETWORK
        assert analyzer.baseline_window == timedelta(hours=24)
        assert analyzer.contamination == 0.1
        assert not analyzer.is_baseline_learned

    def test_initialization_with_custom_params(self):
        """Test initialization with custom parameters."""
        analyzer = BehavioralAnalyzer(
            behavior_type=BehaviorType.USER,
            baseline_window=timedelta(hours=12),
            contamination=0.05,
            n_estimators=150,
            max_samples=512,
        )

        assert analyzer.behavior_type == BehaviorType.USER
        assert analyzer.contamination == 0.05

    def test_learn_baseline_basic(self):
        """Test baseline learning with normal events."""
        analyzer = BehavioralAnalyzer(behavior_type=BehaviorType.NETWORK)

        # Generate training events (normal behavior)
        training_events = []
        for i in range(100):
            event = BehaviorEvent(
                event_id=f"evt_{i}",
                timestamp=datetime.utcnow() - timedelta(hours=i),
                behavior_type=BehaviorType.NETWORK,
                entity_id="host_001",
                features={
                    "packets_per_sec": 100.0 + np.random.randn() * 10,
                    "bytes_per_sec": 50000.0 + np.random.randn() * 5000,
                },
            )
            training_events.append(event)

        analyzer.learn_baseline(training_events)

        assert analyzer.is_baseline_learned
        assert analyzer.baseline_events == training_events
        assert analyzer.model is not None
        assert analyzer.scaler is not None

    def test_learn_baseline_insufficient_data(self):
        """Test baseline learning with insufficient data."""
        analyzer = BehavioralAnalyzer(behavior_type=BehaviorType.NETWORK)

        # Too few events
        training_events = [
            BehaviorEvent(
                event_id="evt_001",
                timestamp=datetime.utcnow(),
                behavior_type=BehaviorType.NETWORK,
                entity_id="host_001",
                features={"x": 1.0},
            )
        ]

        with pytest.raises(ValueError, match="Need at least"):
            analyzer.learn_baseline(training_events)

    def test_analyze_event_without_baseline(self):
        """Test analyzing event before learning baseline."""
        analyzer = BehavioralAnalyzer(behavior_type=BehaviorType.NETWORK)

        event = BehaviorEvent(
            event_id="evt_001",
            timestamp=datetime.utcnow(),
            behavior_type=BehaviorType.NETWORK,
            entity_id="host_001",
            features={"x": 1.0},
        )

        with pytest.raises(ValueError, match="Baseline not learned"):
            analyzer.analyze_event(event)

    def test_analyze_event_normal(self):
        """Test analyzing normal event after baseline."""
        analyzer = BehavioralAnalyzer(behavior_type=BehaviorType.NETWORK)

        # Learn baseline with normal events
        training_events = []
        for i in range(100):
            event = BehaviorEvent(
                event_id=f"evt_{i}",
                timestamp=datetime.utcnow(),
                behavior_type=BehaviorType.NETWORK,
                entity_id="host_001",
                features={
                    "packets_per_sec": 100.0 + np.random.randn() * 5,
                    "bytes_per_sec": 50000.0 + np.random.randn() * 2500,
                },
            )
            training_events.append(event)

        analyzer.learn_baseline(training_events)

        # Analyze similar (normal) event
        test_event = BehaviorEvent(
            event_id="test_evt",
            timestamp=datetime.utcnow(),
            behavior_type=BehaviorType.NETWORK,
            entity_id="host_001",
            features={"packets_per_sec": 102.0, "bytes_per_sec": 51000.0},
        )

        detection = analyzer.analyze_event(test_event)

        assert detection.event == test_event
        assert detection.anomaly_score < 0.5  # Should be low for normal event
        assert detection.risk_level in [RiskLevel.BASELINE, RiskLevel.LOW]

    def test_analyze_event_anomalous(self):
        """Test analyzing anomalous event."""
        analyzer = BehavioralAnalyzer(behavior_type=BehaviorType.NETWORK)

        # Learn baseline with normal events (tight distribution)
        training_events = []
        for i in range(100):
            event = BehaviorEvent(
                event_id=f"evt_{i}",
                timestamp=datetime.utcnow(),
                behavior_type=BehaviorType.NETWORK,
                entity_id="host_001",
                features={
                    "packets_per_sec": 100.0,  # Constant
                    "bytes_per_sec": 50000.0,  # Constant
                },
            )
            training_events.append(event)

        analyzer.learn_baseline(training_events)

        # Analyze very different (anomalous) event
        anomalous_event = BehaviorEvent(
            event_id="anomaly_evt",
            timestamp=datetime.utcnow(),
            behavior_type=BehaviorType.NETWORK,
            entity_id="host_001",
            features={
                "packets_per_sec": 10000.0,  # 100x normal
                "bytes_per_sec": 5000000.0,  # 100x normal
            },
        )

        detection = analyzer.analyze_event(anomalous_event)

        assert detection.anomaly_score > 0.7  # Should be high for anomaly
        assert detection.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]

    def test_determine_risk_level(self):
        """Test risk level determination from anomaly score."""
        analyzer = BehavioralAnalyzer(behavior_type=BehaviorType.NETWORK)

        assert analyzer._determine_risk_level(0.0) == RiskLevel.BASELINE
        assert analyzer._determine_risk_level(0.1) == RiskLevel.BASELINE
        assert analyzer._determine_risk_level(0.3) == RiskLevel.LOW
        assert analyzer._determine_risk_level(0.5) == RiskLevel.MEDIUM
        assert analyzer._determine_risk_level(0.7) == RiskLevel.HIGH
        assert analyzer._determine_risk_level(0.9) == RiskLevel.CRITICAL
        assert analyzer._determine_risk_level(1.0) == RiskLevel.CRITICAL

    def test_analyze_batch(self):
        """Test batch analysis of multiple events."""
        analyzer = BehavioralAnalyzer(behavior_type=BehaviorType.NETWORK)

        # Learn baseline
        training_events = []
        for i in range(100):
            event = BehaviorEvent(
                event_id=f"evt_{i}",
                timestamp=datetime.utcnow(),
                behavior_type=BehaviorType.NETWORK,
                entity_id="host_001",
                features={"x": 100.0 + np.random.randn() * 5},
            )
            training_events.append(event)

        analyzer.learn_baseline(training_events)

        # Analyze batch
        test_events = [
            BehaviorEvent(
                event_id=f"test_{i}",
                timestamp=datetime.utcnow(),
                behavior_type=BehaviorType.NETWORK,
                entity_id="host_001",
                features={"x": 101.0},
            )
            for i in range(5)
        ]

        detections = analyzer.analyze_batch(test_events)

        assert len(detections) == 5
        for detection in detections:
            assert isinstance(detection, AnomalyDetection)

    def test_update_baseline(self):
        """Test updating baseline with new normal events."""
        analyzer = BehavioralAnalyzer(behavior_type=BehaviorType.NETWORK)

        # Initial baseline
        initial_events = []
        for i in range(50):
            event = BehaviorEvent(
                event_id=f"init_{i}",
                timestamp=datetime.utcnow() - timedelta(hours=48),
                behavior_type=BehaviorType.NETWORK,
                entity_id="host_001",
                features={"x": 100.0},
            )
            initial_events.append(event)

        analyzer.learn_baseline(initial_events)

        # New normal events
        new_events = []
        for i in range(30):
            event = BehaviorEvent(
                event_id=f"new_{i}",
                timestamp=datetime.utcnow(),
                behavior_type=BehaviorType.NETWORK,
                entity_id="host_001",
                features={"x": 100.0},
            )
            new_events.append(event)

        analyzer.update_baseline(new_events)

        # Baseline should include recent events
        assert len(analyzer.baseline_events) > len(initial_events)

    def test_get_feature_importance(self):
        """Test feature importance extraction."""
        analyzer = BehavioralAnalyzer(behavior_type=BehaviorType.NETWORK)

        # Learn baseline
        training_events = []
        for i in range(100):
            event = BehaviorEvent(
                event_id=f"evt_{i}",
                timestamp=datetime.utcnow(),
                behavior_type=BehaviorType.NETWORK,
                entity_id="host_001",
                features={
                    "a": 100.0 + np.random.randn() * 50,  # High variance
                    "b": 50.0 + np.random.randn() * 5,  # Low variance
                },
            )
            training_events.append(event)

        analyzer.learn_baseline(training_events)

        # Anomalous event
        test_event = BehaviorEvent(
            event_id="test",
            timestamp=datetime.utcnow(),
            behavior_type=BehaviorType.NETWORK,
            entity_id="host_001",
            features={"a": 500.0, "b": 51.0},
        )

        detection = analyzer.analyze_event(test_event)

        assert "a" in detection.contributing_features
        assert "b" in detection.contributing_features

        # Feature 'a' should contribute more (larger deviation)
        assert detection.contributing_features["a"] > detection.contributing_features["b"]

    def test_metrics_incremented(self):
        """Test that Prometheus metrics are incremented."""
        analyzer = BehavioralAnalyzer(behavior_type=BehaviorType.NETWORK)

        # Learn baseline
        training_events = []
        for i in range(100):
            event = BehaviorEvent(
                event_id=f"evt_{i}",
                timestamp=datetime.utcnow(),
                behavior_type=BehaviorType.NETWORK,
                entity_id="host_001",
                features={"x": 100.0},
            )
            training_events.append(event)

        analyzer.learn_baseline(training_events)

        # Analyze event
        test_event = BehaviorEvent(
            event_id="test",
            timestamp=datetime.utcnow(),
            behavior_type=BehaviorType.NETWORK,
            entity_id="host_001",
            features={"x": 1000.0},  # Anomalous
        )

        initial_count = analyzer.events_analyzed._value.get()
        detection = analyzer.analyze_event(test_event)
        final_count = analyzer.events_analyzed._value.get()

        assert final_count > initial_count


class TestBehavioralAnalyzerIntegration:
    """Integration tests for BehavioralAnalyzer."""

    def test_multi_entity_analysis(self):
        """Test analyzing multiple entities separately."""
        analyzer_host1 = BehavioralAnalyzer(behavior_type=BehaviorType.NETWORK)
        analyzer_host2 = BehavioralAnalyzer(behavior_type=BehaviorType.NETWORK)

        # Learn baselines for two hosts with different patterns
        events_host1 = []
        for i in range(100):
            event = BehaviorEvent(
                event_id=f"h1_evt_{i}",
                timestamp=datetime.utcnow(),
                behavior_type=BehaviorType.NETWORK,
                entity_id="host_001",
                features={"packets_per_sec": 100.0 + np.random.randn() * 10},
            )
            events_host1.append(event)

        events_host2 = []
        for i in range(100):
            event = BehaviorEvent(
                event_id=f"h2_evt_{i}",
                timestamp=datetime.utcnow(),
                behavior_type=BehaviorType.NETWORK,
                entity_id="host_002",
                features={"packets_per_sec": 1000.0 + np.random.randn() * 100},  # Different baseline
            )
            events_host2.append(event)

        analyzer_host1.learn_baseline(events_host1)
        analyzer_host2.learn_baseline(events_host2)

        # Test that normal for host1 would be anomalous for host2
        normal_for_host1 = BehaviorEvent(
            event_id="test",
            timestamp=datetime.utcnow(),
            behavior_type=BehaviorType.NETWORK,
            entity_id="host_001",
            features={"packets_per_sec": 105.0},
        )

        detection_h1 = analyzer_host1.analyze_event(normal_for_host1)
        detection_h2 = analyzer_host2.analyze_event(normal_for_host1)

        assert detection_h1.risk_level <= RiskLevel.LOW
        assert detection_h2.risk_level >= RiskLevel.HIGH  # Should be anomalous for host2


class TestRealWorldScenarios:
    """Test real-world behavioral analysis scenarios."""

    def test_data_exfiltration_detection(self):
        """Test detecting data exfiltration through traffic spike."""
        analyzer = BehavioralAnalyzer(behavior_type=BehaviorType.NETWORK)

        # Normal baseline: low data transfer
        baseline_events = []
        for i in range(100):
            event = BehaviorEvent(
                event_id=f"evt_{i}",
                timestamp=datetime.utcnow() - timedelta(hours=100 - i),
                behavior_type=BehaviorType.NETWORK,
                entity_id="user_001",
                features={
                    "bytes_uploaded": 1000.0 + np.random.randn() * 100,  # KB
                    "connections_count": 5.0 + np.random.randn() * 2,
                },
            )
            baseline_events.append(event)

        analyzer.learn_baseline(baseline_events)

        # Exfiltration event: massive data upload
        exfiltration_event = BehaviorEvent(
            event_id="exfil",
            timestamp=datetime.utcnow(),
            behavior_type=BehaviorType.NETWORK,
            entity_id="user_001",
            features={
                "bytes_uploaded": 1000000.0,  # 1 GB - 1000x normal
                "connections_count": 50.0,  # 10x normal
            },
        )

        detection = analyzer.analyze_event(exfiltration_event)

        assert detection.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        assert detection.anomaly_score > 0.8

    def test_insider_threat_detection(self):
        """Test detecting insider threat through access pattern changes."""
        analyzer = BehavioralAnalyzer(behavior_type=BehaviorType.DATA_ACCESS)

        # Normal: user accesses only their department files
        baseline_events = []
        for i in range(100):
            event = BehaviorEvent(
                event_id=f"evt_{i}",
                timestamp=datetime.utcnow() - timedelta(days=100 - i),
                behavior_type=BehaviorType.DATA_ACCESS,
                entity_id="employee_123",
                features={
                    "files_accessed": 10.0 + np.random.randn() * 2,
                    "sensitive_files": 0.0,  # Never accesses sensitive files
                    "access_hours": 9.0 + np.random.randn() * 4,  # During work hours
                },
            )
            baseline_events.append(event)

        analyzer.learn_baseline(baseline_events)

        # Suspicious: accessing many sensitive files at odd hours
        suspicious_event = BehaviorEvent(
            event_id="suspicious",
            timestamp=datetime.utcnow(),
            behavior_type=BehaviorType.DATA_ACCESS,
            entity_id="employee_123",
            features={
                "files_accessed": 50.0,  # 5x normal
                "sensitive_files": 20.0,  # Previously 0
                "access_hours": 2.0,  # 2 AM
            },
        )

        detection = analyzer.analyze_event(suspicious_event)

        assert detection.risk_level >= RiskLevel.HIGH
        assert "sensitive_files" in detection.contributing_features
