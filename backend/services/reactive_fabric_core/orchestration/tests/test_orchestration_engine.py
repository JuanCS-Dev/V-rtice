"""
Tests for Orchestration Engine.

Tests event correlation, pattern detection, and threat scoring.
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ..orchestration_engine import (
    OrchestrationEngine,
    OrchestrationConfig,
    OrchestrationEvent,
    CorrelationRule,
    ThreatScore,
    ThreatCategory,
    EventCorrelationWindow,
    EventCorrelator,
    PatternDetector,
    ThreatScorer
)


@pytest.fixture
def config():
    """Create test configuration."""
    return OrchestrationConfig(
        correlation_window_minutes=15,
        max_events_per_window=1000,
        base_score_threshold=0.3,
        critical_score_threshold=0.8,
        min_events_for_pattern=2,
        anomaly_sensitivity=0.7
    )


@pytest.fixture
def engine(config):
    """Create test orchestration engine."""
    return OrchestrationEngine(config)


@pytest.fixture
def sample_events():
    """Create sample events for testing."""
    now = datetime.utcnow()
    return [
        OrchestrationEvent(
            collector_type="NetworkCollector",
            source="network:eth0",
            severity="medium",
            raw_data={
                "source_ip": "192.168.1.100",
                "target": "server01",
                "type": "port_scan"
            },
            timestamp=now - timedelta(minutes=10)
        ),
        OrchestrationEvent(
            collector_type="LogAggregation",
            source="elasticsearch:logs",
            severity="high",
            raw_data={
                "source_ip": "192.168.1.100",
                "target": "server01",
                "pattern_name": "failed_authentication",
                "count": 10
            },
            timestamp=now - timedelta(minutes=5)
        ),
        OrchestrationEvent(
            collector_type="HoneypotCollector",
            source="honeypot:ssh",
            severity="high",
            raw_data={
                "source_ip": "192.168.1.100",
                "command": "sudo su",
                "type": "privilege_escalation"
            },
            timestamp=now - timedelta(minutes=2)
        )
    ]


class TestOrchestrationEngine:
    """Test suite for OrchestrationEngine."""

    @pytest.mark.asyncio
    async def test_engine_initialization(self, engine):
        """Test engine initialization."""
        assert engine.config is not None
        assert engine.correlator is not None
        assert engine.pattern_detector is not None
        assert engine.threat_scorer is not None
        assert len(engine.rules) > 0
        assert engine.processed_events == 0
        assert len(engine.detected_threats) == 0

    @pytest.mark.asyncio
    async def test_process_single_event(self, engine):
        """Test processing a single event."""
        event_data = {
            "collector_type": "NetworkCollector",
            "source": "network:eth0",
            "severity": "low",
            "parsed_data": {
                "source_ip": "10.0.0.1",
                "target": "server01",
                "type": "connection"
            }
        }

        threat_score = await engine.process_event(event_data)

        # Single event shouldn't trigger threat
        assert threat_score is None
        assert engine.processed_events == 1

    @pytest.mark.asyncio
    async def test_detect_reconnaissance_pattern(self, engine):
        """Test detection of reconnaissance pattern."""
        # Simulate multiple scan events from same source
        events = [
            {
                "collector_type": "NetworkCollector",
                "source": "network:eth0",
                "severity": "medium",
                "parsed_data": {
                    "source_ip": "192.168.1.100",
                    "target": "server01",
                    "type": "port_scan"
                }
            }
            for _ in range(3)
        ]

        threat_scores = []
        for event in events:
            score = await engine.process_event(event)
            if score:
                threat_scores.append(score)

        # Should detect reconnaissance pattern
        assert len(threat_scores) > 0
        assert threat_scores[-1].category == ThreatCategory.RECONNAISSANCE

    @pytest.mark.asyncio
    async def test_detect_brute_force_pattern(self, engine):
        """Test detection of brute force attack."""
        # Simulate multiple failed auth attempts
        events = []
        for i in range(6):
            events.append({
                "collector_type": "LogAggregation",
                "source": "elasticsearch:logs",
                "severity": "high",
                "parsed_data": {
                    "source_ip": "10.0.0.50",
                    "target": "server02",
                    "pattern_name": "authentication",
                    "message": "Failed authentication attempt"
                }
            })

        threat_scores = []
        for event in events:
            score = await engine.process_event(event)
            if score:
                threat_scores.append(score)

        # Should detect brute force pattern
        assert len(threat_scores) > 0
        threat = threat_scores[-1]
        assert threat.category == ThreatCategory.CREDENTIAL_ACCESS
        assert threat.base_score >= 0.6

    @pytest.mark.asyncio
    async def test_correlation_across_collectors(self, engine):
        """Test correlation of events from multiple collectors."""
        events = [
            # Multiple network scans from same source (to trigger pattern)
            {
                "collector_type": "NetworkCollector",
                "source": "network",
                "severity": "medium",
                "parsed_data": {
                    "source_ip": "192.168.1.200",
                    "target": "web-server",
                    "type": "port_scan"
                }
            },
            {
                "collector_type": "NetworkCollector",
                "source": "network",
                "severity": "medium",
                "parsed_data": {
                    "source_ip": "192.168.1.200",
                    "target": "web-server",
                    "type": "port_scan"
                }
            },
            # Honeypot trigger from same source
            {
                "collector_type": "HoneypotCollector",
                "source": "honeypot",
                "severity": "high",
                "parsed_data": {
                    "source_ip": "192.168.1.200",
                    "target": "web-server",
                    "service": "ssh"
                }
            },
            # More network activity to meet min_occurrences
            {
                "collector_type": "NetworkCollector",
                "source": "network",
                "severity": "high",
                "parsed_data": {
                    "source_ip": "192.168.1.200",
                    "target": "web-server",
                    "type": "port_scan"
                }
            }
        ]

        threat_scores = []
        for event in events:
            score = await engine.process_event(event)
            if score:
                threat_scores.append(score)

        # Should correlate events from same source
        assert len(threat_scores) > 0
        threat = threat_scores[-1]
        assert len(threat.correlated_events) >= 3
        assert "192.168.1.200" in threat.source_ips

    @pytest.mark.asyncio
    async def test_threat_scoring(self, engine):
        """Test threat scoring calculation."""
        # Create events that match multiple rules
        events = [
            {
                "collector_type": "NetworkCollector",
                "source": "network",
                "severity": "high",
                "parsed_data": {
                    "source_ip": "10.0.0.100",
                    "target": "database",
                    "type": "port_scan"
                }
            },
            {
                "collector_type": "LogAggregation",
                "source": "logs",
                "severity": "critical",
                "parsed_data": {
                    "source_ip": "10.0.0.100",
                    "target": "database",
                    "pattern_name": "privilege_escalation"
                }
            },
            {
                "collector_type": "NetworkCollector",
                "source": "network",
                "severity": "critical",
                "parsed_data": {
                    "source_ip": "10.0.0.100",
                    "target": "database",
                    "bytes_transferred": 1000000000,
                    "type": "exfiltration"
                }
            }
        ]

        threat_scores = []
        for event in events:
            score = await engine.process_event(event)
            if score:
                threat_scores.append(score)

        # Should have high threat score
        assert len(threat_scores) > 0
        threat = threat_scores[-1]
        assert threat.severity in ["high", "critical"]
        assert threat.base_score >= 0.6

    @pytest.mark.asyncio
    async def test_analyze_threat_landscape(self, engine):
        """Test threat landscape analysis."""
        # Process some threatening events
        events = [
            {
                "collector_type": "NetworkCollector",
                "source": "network",
                "severity": "high",
                "parsed_data": {
                    "source_ip": f"10.0.0.{i}",
                    "target": "server",
                    "type": "port_scan"
                }
            }
            for i in range(5)
        ]

        for event in events:
            await engine.process_event(event)
            await engine.process_event(event)  # Duplicate for pattern
            await engine.process_event(event)  # Triplicate for pattern

        # Analyze landscape
        analysis = await engine.analyze_threat_landscape()

        assert analysis["status"] == "active_threats"
        assert analysis["threats_detected"] > 0
        assert analysis["events_processed"] == 15
        assert "threat_categories" in analysis
        assert "top_threat_sources" in analysis
        assert "severity_breakdown" in analysis

    @pytest.mark.asyncio
    async def test_event_correlator(self, config, sample_events):
        """Test EventCorrelator functionality."""
        correlator = EventCorrelator(config)

        # Add events
        for event in sample_events:
            correlator.add_event(event)

        # Find correlated events
        correlated = correlator.find_correlated_events(
            sample_events[-1],
            EventCorrelationWindow.MEDIUM
        )

        # Should find events from same source IP
        assert len(correlated) >= 2
        for event in correlated:
            assert event.raw_data.get("source_ip") == "192.168.1.100"

    @pytest.mark.asyncio
    async def test_pattern_detector(self):
        """Test PatternDetector functionality."""
        rules = [
            CorrelationRule(
                rule_id="TEST001",
                name="Test Pattern",
                description="Test pattern detection",
                category=ThreatCategory.RECONNAISSANCE,
                event_types=["NetworkCollector"],
                time_window=EventCorrelationWindow.SHORT,
                min_occurrences=2,
                base_score=0.5,
                mitre_tactics=["TA0043"],
                mitre_techniques=["T1595"]
            )
        ]

        detector = PatternDetector(rules)

        events = [
            OrchestrationEvent(
                collector_type="NetworkCollector",
                source="test",
                severity="medium",
                raw_data={"type": "port_scan"},
                timestamp=datetime.utcnow()
            )
            for _ in range(3)
        ]

        patterns = detector.detect_patterns(events)

        assert len(patterns) == 1
        rule, matched_events = patterns[0]
        assert rule.rule_id == "TEST001"
        assert len(matched_events) == 3

    @pytest.mark.asyncio
    async def test_threat_scorer(self, config):
        """Test ThreatScorer functionality."""
        scorer = ThreatScorer(config)

        rule = CorrelationRule(
            rule_id="TEST001",
            name="Test Rule",
            description="Test",
            category=ThreatCategory.EXFILTRATION,
            event_types=["NetworkCollector"],
            time_window=EventCorrelationWindow.MEDIUM,
            min_occurrences=2,
            base_score=0.7,
            score_multiplier=1.5,
            mitre_tactics=["TA0010"],
            mitre_techniques=["T1041"]
        )

        events = [
            OrchestrationEvent(
                collector_type="NetworkCollector",
                source="test",
                severity="high",
                raw_data={
                    "source_ip": "10.0.0.1",
                    "target": "server"
                }
            )
            for _ in range(3)
        ]

        patterns = [(rule, events)]
        threat_score = scorer.calculate_score(patterns)

        assert threat_score is not None
        assert threat_score.base_score >= 0.7
        assert threat_score.category == ThreatCategory.EXFILTRATION
        assert len(threat_score.correlated_events) == 3
        assert "10.0.0.1" in threat_score.source_ips

    @pytest.mark.asyncio
    async def test_start_stop(self, engine):
        """Test engine start and stop."""
        await engine.start()
        assert engine._running is True

        await engine.stop()
        assert engine._running is False

    @pytest.mark.asyncio
    async def test_get_metrics(self, engine):
        """Test metrics retrieval."""
        # Process some events
        for _ in range(5):
            await engine.process_event({
                "collector_type": "NetworkCollector",
                "source": "test",
                "severity": "low",
                "parsed_data": {}
            })

        metrics = engine.get_metrics()

        assert metrics["running"] is False
        assert metrics["events_processed"] == 5
        assert metrics["correlation_rules"] == len(engine.rules)
        assert "memory_events" in metrics

    @pytest.mark.asyncio
    async def test_mitre_attack_mapping(self, engine):
        """Test MITRE ATT&CK tactic/technique mapping."""
        # Process events that match patterns with MITRE mappings
        events = [
            {
                "collector_type": "NetworkCollector",
                "source": "network",
                "severity": "high",
                "parsed_data": {
                    "source_ip": "10.0.0.50",
                    "target": "fileserver",
                    "type": "port_scan"
                }
            }
            for _ in range(3)
        ]

        threat_scores = []
        for event in events:
            score = await engine.process_event(event)
            if score:
                threat_scores.append(score)

        # Check MITRE mapping
        assert len(threat_scores) > 0
        threat = threat_scores[-1]
        assert len(threat.mitre_tactics) > 0
        assert len(threat.mitre_techniques) > 0
        assert "T1595" in threat.mitre_techniques or "T1046" in threat.mitre_techniques

    @pytest.mark.asyncio
    async def test_empty_threat_landscape(self, engine):
        """Test threat landscape with no threats."""
        analysis = await engine.analyze_threat_landscape()

        assert analysis["status"] == "clear"
        assert analysis["threats_detected"] == 0
        assert analysis["events_processed"] == 0

    @pytest.mark.asyncio
    async def test_old_event_cleanup(self, config):
        """Test cleanup of old events."""
        config.event_ttl_minutes = 1  # Short TTL for testing
        correlator = EventCorrelator(config)

        # Add old event
        old_event = OrchestrationEvent(
            collector_type="NetworkCollector",
            source="test",
            severity="low",
            raw_data={"source_ip": "10.0.0.1"},
            timestamp=datetime.utcnow() - timedelta(minutes=5)
        )
        correlator.add_event(old_event)

        # Add recent event
        new_event = OrchestrationEvent(
            collector_type="NetworkCollector",
            source="test",
            severity="low",
            raw_data={"source_ip": "10.0.0.2"},
            timestamp=datetime.utcnow()
        )
        correlator.add_event(new_event)

        # Old event should be cleaned up
        assert len(correlator.events_by_source["10.0.0.1"]) == 0
        assert len(correlator.events_by_source["10.0.0.2"]) == 1

    def test_repr(self, engine):
        """Test string representation."""
        repr_str = repr(engine)
        assert "OrchestrationEngine" in repr_str
        assert "running=" in repr_str
        assert "events=" in repr_str
        assert "threats=" in repr_str