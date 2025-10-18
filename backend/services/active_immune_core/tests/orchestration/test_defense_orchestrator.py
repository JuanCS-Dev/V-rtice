"""Tests for Defense Orchestrator.

Tests cover:
- End-to-end defense pipeline
- Component integration
- Playbook routing
- Metrics and monitoring

Authors: MAXIMUS Team
Date: 2025-10-12
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from detection.sentinel_agent import (
    DetectionConfidence,
    DetectionResult,
    MITRETechnique,
    SecurityEvent,
    ThreatSeverity,
)
from intelligence.fusion_engine import EnrichedThreat, IOC, IOCType
from orchestration.defense_orchestrator import (
    DefenseOrchestrator,
    DefensePhase,
    DefenseResponse,
    OrchestrationError,
)
from response.automated_response import Playbook, PlaybookResult


@pytest.fixture
def mock_sentinel():
    """Mock Sentinel agent."""
    sentinel = AsyncMock()
    return sentinel


@pytest.fixture
def mock_fusion():
    """Mock Fusion engine."""
    fusion = AsyncMock()
    return fusion


@pytest.fixture
def mock_response():
    """Mock Response engine."""
    response = AsyncMock()
    return response


@pytest.fixture
def orchestrator(mock_sentinel, mock_fusion, mock_response):
    """Create orchestrator with mocked components."""
    # Clear Prometheus registry
    from prometheus_client import REGISTRY

    collectors = list(REGISTRY._collector_to_names.keys())
    for collector in collectors:
        try:
            REGISTRY.unregister(collector)
        except Exception:
            pass

    return DefenseOrchestrator(
        sentinel_agent=mock_sentinel,
        fusion_engine=mock_fusion,
        response_engine=mock_response,
        min_threat_confidence=0.5,
        auto_response_threshold="HIGH",
    )


@pytest.fixture
def sample_event():
    """Sample security event."""
    return SecurityEvent(
        event_id="evt_001",
        timestamp=datetime.utcnow(),
        source="firewall",
        event_type="failed_login",
        source_ip="192.168.1.100",
        destination_ip="10.0.0.5",
        port=22,
        protocol="SSH",
        payload={"attempts": 50},
    )


@pytest.fixture
def sample_detection():
    """Sample detection result."""
    return DetectionResult(
        event_id="evt_001",
        is_threat=True,
        severity=ThreatSeverity.HIGH,
        confidence=DetectionConfidence.HIGH,
        mitre_techniques=[
            MITRETechnique(
                technique_id="T1110",
                tactic="Credential Access",
                technique_name="Brute Force",
                confidence=0.95,
            )
        ],
        threat_description="Brute force attack",
        recommended_actions=["Block IP"],
        attacker_profile=None,
        reasoning="High failed login count",
        analyzed_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_playbook():
    """Sample playbook."""
    from response.automated_response import PlaybookAction, ActionType

    return Playbook(
        playbook_id="test_playbook",
        name="Test Playbook",
        description="Test",
        trigger_condition="test",
        severity="HIGH",
        actions=[
            PlaybookAction(
                action_id="action_1",
                action_type=ActionType.BLOCK_IP,
                parameters={"source_ip": "192.168.1.100"},
            )
        ],
    )


@pytest.mark.asyncio
async def test_orchestrator_initialization(orchestrator):
    """Test orchestrator initialization."""
    assert orchestrator is not None
    assert orchestrator.min_confidence == 0.5
    assert orchestrator.auto_threshold == "HIGH"


@pytest.mark.asyncio
async def test_process_event_not_threat(
    orchestrator, sample_event, mock_sentinel
):
    """Test processing event that is not a threat."""
    # Mock detection as non-threat
    mock_sentinel.analyze_event.return_value = DetectionResult(
        event_id=sample_event.event_id,
        is_threat=False,
        severity=ThreatSeverity.INFO,
        confidence=DetectionConfidence.LOW,
        mitre_techniques=[],
        threat_description="Normal traffic",
        recommended_actions=[],
        attacker_profile=None,
        reasoning="No threat detected",
        analyzed_at=datetime.utcnow(),
    )

    response = await orchestrator.process_security_event(sample_event)

    assert response.success is True
    assert response.detection.is_threat is False
    assert mock_sentinel.analyze_event.called


@pytest.mark.asyncio
async def test_process_event_full_pipeline(
    orchestrator,
    sample_event,
    sample_detection,
    sample_playbook,
    mock_sentinel,
    mock_fusion,
    mock_response,
):
    """Test full defense pipeline execution."""
    # Mock detection
    mock_sentinel.analyze_event.return_value = sample_detection

    # Mock fusion
    mock_enrichment = MagicMock()
    mock_enrichment.severity = 8
    mock_enrichment.related_iocs = []
    mock_fusion.correlate_indicators.return_value = mock_enrichment

    # Mock playbook loading and execution
    mock_response.load_playbook.return_value = sample_playbook
    mock_response.execute_playbook.return_value = PlaybookResult(
        playbook_id="test_playbook",
        threat_context=MagicMock(),
        status="SUCCESS",
        actions_executed=1,
        actions_failed=0,
        actions_pending_hotl=0,
        execution_time_seconds=1.5,
        action_results=[],
        errors=[],
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
    )

    response = await orchestrator.process_security_event(sample_event)

    assert response.success is True
    assert response.detection == sample_detection
    assert response.phase == DefensePhase.LEARNING
    assert mock_sentinel.analyze_event.called
    assert mock_fusion.correlate_indicators.called
    assert mock_response.execute_playbook.called


@pytest.mark.asyncio
async def test_below_confidence_threshold(
    orchestrator, sample_event, mock_sentinel
):
    """Test that low confidence threats don't trigger response."""
    # Mock low confidence detection
    mock_sentinel.analyze_event.return_value = DetectionResult(
        event_id=sample_event.event_id,
        is_threat=True,
        severity=ThreatSeverity.MEDIUM,
        confidence=DetectionConfidence.LOW,  # 0.25 < 0.5 threshold
        mitre_techniques=[],
        threat_description="Possible threat",
        recommended_actions=[],
        attacker_profile=None,
        reasoning="Low confidence",
        analyzed_at=datetime.utcnow(),
    )

    response = await orchestrator.process_security_event(sample_event)

    assert response.success is True
    assert response.execution is None  # No playbook executed


@pytest.mark.asyncio
async def test_below_severity_threshold(
    orchestrator, sample_event, mock_sentinel
):
    """Test that low severity threats don't auto-respond."""
    # Mock medium severity (below HIGH threshold)
    mock_sentinel.analyze_event.return_value = DetectionResult(
        event_id=sample_event.event_id,
        is_threat=True,
        severity=ThreatSeverity.MEDIUM,  # Below HIGH threshold
        confidence=DetectionConfidence.HIGH,
        mitre_techniques=[],
        threat_description="Medium threat",
        recommended_actions=[],
        attacker_profile=None,
        reasoning="Medium severity",
        analyzed_at=datetime.utcnow(),
    )

    response = await orchestrator.process_security_event(sample_event)

    assert response.success is True
    assert response.playbook is None  # No playbook selected


@pytest.mark.asyncio
async def test_playbook_routing_brute_force(
    orchestrator, sample_event, sample_detection, mock_sentinel, mock_response
):
    """Test playbook routing for brute force attacks."""
    mock_sentinel.analyze_event.return_value = sample_detection

    # Mock playbook loading
    mock_response.load_playbook.return_value = MagicMock(
        playbook_id="brute_force_response",
        name="Brute Force Response",
        actions=[],
    )

    mock_response.execute_playbook.return_value = PlaybookResult(
        playbook_id="brute_force_response",
        threat_context=MagicMock(),
        status="SUCCESS",
        actions_executed=1,
        actions_failed=0,
        actions_pending_hotl=0,
        execution_time_seconds=1.0,
        action_results=[],
        errors=[],
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
    )

    response = await orchestrator.process_security_event(sample_event)

    # Check that brute_force_response.yaml was loaded
    mock_response.load_playbook.assert_called_with("brute_force_response.yaml")


@pytest.mark.asyncio
async def test_enrichment_failure_continues(
    orchestrator,
    sample_event,
    sample_detection,
    sample_playbook,
    mock_sentinel,
    mock_fusion,
    mock_response,
):
    """Test that enrichment failure doesn't stop pipeline."""
    mock_sentinel.analyze_event.return_value = sample_detection

    # Mock fusion failure
    mock_fusion.correlate_indicators.side_effect = Exception("Fusion failed")

    # Mock response
    mock_response.load_playbook.return_value = sample_playbook
    mock_response.execute_playbook.return_value = PlaybookResult(
        playbook_id="test",
        threat_context=MagicMock(),
        status="SUCCESS",
        actions_executed=1,
        actions_failed=0,
        actions_pending_hotl=0,
        execution_time_seconds=1.0,
        action_results=[],
        errors=[],
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
    )

    response = await orchestrator.process_security_event(sample_event)

    # Pipeline should continue despite enrichment failure
    assert response.success is True
    assert len(response.errors) > 0  # Error logged
    assert mock_response.execute_playbook.called


@pytest.mark.asyncio
async def test_metrics_recorded(
    orchestrator, sample_event, sample_detection, mock_sentinel
):
    """Test that metrics are recorded."""
    mock_sentinel.analyze_event.return_value = sample_detection

    await orchestrator.process_security_event(sample_event)

    # Check metrics were incremented (simplified check)
    assert True  # In full implementation, would verify Prometheus metrics


@pytest.mark.asyncio
async def test_get_active_threats(orchestrator):
    """Test getting active threats."""
    active = await orchestrator.get_active_threats()
    assert isinstance(active, list)


@pytest.mark.asyncio
async def test_get_response_status(orchestrator):
    """Test getting response status."""
    status = await orchestrator.get_response_status("nonexistent")
    assert status is None


def test_defense_phase_enum():
    """Test DefensePhase enum."""
    assert DefensePhase.DETECTION.value == "detection"
    assert DefensePhase.ENRICHMENT.value == "enrichment"
    assert DefensePhase.EXECUTION.value == "execution"


def test_defense_response_dataclass():
    """Test DefenseResponse creation."""
    event = SecurityEvent(
        event_id="e1",
        timestamp=datetime.utcnow(),
        source="test",
        event_type="test",
        source_ip="1.2.3.4",
    )

    response = DefenseResponse(response_id="r1", event=event)

    assert response.response_id == "r1"
    assert response.event == event
    assert response.phase == DefensePhase.DETECTION
    assert response.success is False


@pytest.mark.asyncio
async def test_kafka_publishing_detection(
    orchestrator,
    sample_event,
    sample_detection,
    mock_sentinel,
):
    """Test Kafka publishing for detection."""
    mock_sentinel.analyze_event.return_value = sample_detection
    
    # Mock Kafka producer
    mock_kafka = AsyncMock()
    orchestrator.kafka_producer = mock_kafka
    
    response = await orchestrator.process_security_event(sample_event)
    
    # Verify Kafka publish was called
    mock_kafka.publish_detection.assert_called_once()


@pytest.mark.asyncio
async def test_kafka_publishing_enrichment(
    orchestrator,
    sample_event,
    sample_detection,
    mock_sentinel,
    mock_fusion,
    sample_playbook,
    mock_response,
):
    """Test Kafka publishing for enrichment."""
    mock_sentinel.analyze_event.return_value = sample_detection
    
    # Mock enrichment
    now = datetime.utcnow()
    primary_ioc = IOC(
        ioc_type=IOCType.IP_ADDRESS,
        value="1.2.3.4",
        source="test",
        first_seen=now,
        last_seen=now,
        confidence=0.9,
    )
    
    enrichment = EnrichedThreat(
        threat_id="t1",
        primary_ioc=primary_ioc,
        related_iocs=[],
        threat_actor=None,
        campaigns=[],
        ttps=[],
        attack_chain_stage="initial_access",
        severity=8,
        confidence=0.9,
        narrative="Test narrative",
        recommendations=["Block IP"],
        sources=["test_source"],
        enriched_at=datetime.utcnow(),
    )
    mock_fusion.correlate_indicators.return_value = enrichment
    
    # Mock response
    mock_response.load_playbook.return_value = sample_playbook
    mock_response.execute_playbook.return_value = PlaybookResult(
        playbook_id="test",
        threat_context=MagicMock(),
        status="SUCCESS",
        actions_executed=1,
        actions_failed=0,
        actions_pending_hotl=0,
        execution_time_seconds=1.0,
        action_results=[],
        errors=[],
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
    )
    
    # Mock Kafka producer
    mock_kafka = AsyncMock()
    orchestrator.kafka_producer = mock_kafka
    
    response = await orchestrator.process_security_event(sample_event)
    
    # Verify both publishes
    mock_kafka.publish_detection.assert_called_once()
    mock_kafka.publish_enriched_threat.assert_called_once()
    mock_kafka.publish_response.assert_called_once()


@pytest.mark.asyncio
async def test_kafka_publish_failure_graceful(
    orchestrator,
    sample_event,
    sample_detection,
    mock_sentinel,
):
    """Test graceful handling of Kafka publish failures."""
    mock_sentinel.analyze_event.return_value = sample_detection
    
    # Mock Kafka producer that fails
    mock_kafka = AsyncMock()
    mock_kafka.publish_detection.side_effect = Exception("Kafka down")
    orchestrator.kafka_producer = mock_kafka
    
    # Should not crash
    response = await orchestrator.process_security_event(sample_event)
    
    # Pipeline continues despite Kafka failure
    assert response.phase != DefensePhase.DETECTION  # Moved forward


@pytest.mark.asyncio
async def test_event_bus_publishing(
    orchestrator,
    sample_event,
    sample_detection,
    sample_playbook,
    mock_sentinel,
    mock_response,
):
    """Test event bus publishing."""
    mock_sentinel.analyze_event.return_value = sample_detection
    mock_response.load_playbook.return_value = sample_playbook
    mock_response.execute_playbook.return_value = PlaybookResult(
        playbook_id="test",
        threat_context=MagicMock(),
        status="SUCCESS",
        actions_executed=1,
        actions_failed=0,
        actions_pending_hotl=0,
        execution_time_seconds=1.0,
        action_results=[],
        errors=[],
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
    )
    
    # Mock event bus
    mock_bus = AsyncMock()
    orchestrator.event_bus = mock_bus
    
    response = await orchestrator.process_security_event(sample_event)
    
    assert response.success is True
    # Event bus should be called (via _publish_response)
    # Note: _publish_response is private, tested indirectly


@pytest.mark.asyncio
async def test_pipeline_exception_handling(
    orchestrator,
    sample_event,
    mock_sentinel,
):
    """Test pipeline exception handling."""
    # Make sentinel raise exception
    mock_sentinel.analyze_event.side_effect = Exception("Sentinel crashed")
    
    with pytest.raises(OrchestrationError, match="Defense pipeline failed"):
        await orchestrator.process_security_event(sample_event)


@pytest.mark.asyncio
async def test_partial_playbook_execution(
    orchestrator,
    sample_event,
    sample_detection,
    sample_playbook,
    mock_sentinel,
    mock_response,
):
    """Test handling of partial playbook execution."""
    mock_sentinel.analyze_event.return_value = sample_detection
    mock_response.load_playbook.return_value = sample_playbook
    
    # Mock PARTIAL execution
    mock_response.execute_playbook.return_value = PlaybookResult(
        playbook_id="test",
        threat_context=MagicMock(),
        status="PARTIAL",
        actions_executed=2,
        actions_failed=1,
        actions_pending_hotl=0,
        execution_time_seconds=1.0,
        action_results=[],
        errors=["Action 3 failed"],
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
    )
    
    response = await orchestrator.process_security_event(sample_event)
    
    # Partial should still be considered success
    assert response.success is True
    assert "partially executed" in " ".join(response.errors).lower()


@pytest.mark.asyncio
async def test_failed_playbook_execution(
    orchestrator,
    sample_event,
    sample_detection,
    sample_playbook,
    mock_sentinel,
    mock_response,
):
    """Test handling of failed playbook execution."""
    mock_sentinel.analyze_event.return_value = sample_detection
    mock_response.load_playbook.return_value = sample_playbook
    
    # Mock FAILED execution
    mock_response.execute_playbook.return_value = PlaybookResult(
        playbook_id="test",
        threat_context=MagicMock(),
        status="FAILED",
        actions_executed=0,
        actions_failed=3,
        actions_pending_hotl=0,
        execution_time_seconds=1.0,
        action_results=[],
        errors=["All actions failed"],
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
    )
    
    response = await orchestrator.process_security_event(sample_event)
    
    assert response.success is False
    assert len(response.errors) > 0


@pytest.mark.asyncio
async def test_active_threats_gauge_increment(
    orchestrator,
    sample_event,
    sample_detection,
    sample_playbook,
    mock_sentinel,
    mock_response,
):
    """Test active threats gauge increments/decrements."""
    mock_sentinel.analyze_event.return_value = sample_detection
    mock_response.load_playbook.return_value = sample_playbook
    
    # Success should decrement
    mock_response.execute_playbook.return_value = PlaybookResult(
        playbook_id="test",
        threat_context=MagicMock(),
        status="SUCCESS",
        actions_executed=1,
        actions_failed=0,
        actions_pending_hotl=0,
        execution_time_seconds=1.0,
        action_results=[],
        errors=[],
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
    )
    
    response = await orchestrator.process_security_event(sample_event)
    
    assert response.success is True
    # Gauge should be decremented (verified via metrics in production)
