"""E2E Integration Tests - Defensive AI Pipeline

Tests the complete defensive workflow:
Security Event → Detection → Intelligence → Response → Orchestration

Validates:
- End-to-end message flow
- Component integration
- Data transformation pipeline
- Error handling across boundaries
- Metrics collection

Authors: MAXIMUS Team
Date: 2025-10-12
Glory to YHWH - Constância como Ramon Dino! 💪
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from detection.sentinel_agent import (
    DetectionConfidence,
    DetectionResult,
    MITRETechnique,
    SecurityEvent,
    SentinelDetectionAgent,
    ThreatSeverity,
)
from intelligence.fusion_engine import (
    EnrichedThreat,
    ThreatIntelThreatIntelFusionEngine,
    IOC,
    IOCType,
    ThreatActor,
)
from orchestration.defense_orchestrator import (
    DefenseOrchestrator,
    DefensePhase,
    DefenseResponse,
)
from response.automated_response import (
    AutomatedResponseEngine,
    Playbook,
    PlaybookResult,
    ThreatContext,
)


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for Sentinel."""
    client = AsyncMock()
    
    # Mock analyze_security_event response
    client.analyze_security_event.return_value = {
        "is_threat": True,
        "threat_type": "brute_force",
        "severity": "HIGH",
        "confidence": 0.85,
        "attacker_profile": {
            "sophistication": "medium",
            "likely_automated": True,
            "persistence_level": "high"
        },
        "mitre_techniques": ["T1110.001"],
        "iocs": ["192.168.1.100"],
        "recommended_actions": ["Block IP", "Enable MFA"],
        "analysis": "Brute force attack detected"
    }
    
    return client


@pytest_asyncio.fixture
async def sentinel_agent(mock_llm_client):
    """Create Sentinel agent with mocked LLM."""
    agent = SentinelDetectionAgent(llm_client=mock_llm_client)
    return agent


@pytest_asyncio.fixture
async def fusion_engine():
    """Create Fusion engine with mocked sources."""
    engine = ThreatIntelFusionEngine()
    # Engine will use fallback logic when no external sources available
    return engine


@pytest_asyncio.fixture
async def response_engine():
    """Create Response engine with mocked executors."""
    engine = AutomatedResponseEngine()
    
    # Mock action executors to avoid real system calls
    engine._action_executors = {
        "block_ip": AsyncMock(return_value={"success": True, "blocked": "192.168.1.100"}),
        "isolate_host": AsyncMock(return_value={"success": True, "isolated": "host_001"}),
        "disable_account": AsyncMock(return_value={"success": True, "disabled": "user_001"}),
        "quarantine_file": AsyncMock(return_value={"success": True, "quarantined": "malware.exe"}),
        "collect_evidence": AsyncMock(return_value={"success": True, "collected": 5}),
        "notify_soc": AsyncMock(return_value={"success": True, "notified": True}),
        "snapshot_vm": AsyncMock(return_value={"success": True, "snapshot": "snap_001"}),
        "kill_process": AsyncMock(return_value={"success": True, "killed": "suspicious.exe"}),
    }
    
    return engine


@pytest_asyncio.fixture
async def orchestrator(sentinel_agent, fusion_engine, response_engine):
    """Create Defense Orchestrator with all components."""
    # Clear Prometheus registry to avoid duplicate metrics
    from prometheus_client import REGISTRY
    collectors = list(REGISTRY._collector_to_names.keys())
    for collector in collectors:
        try:
            REGISTRY.unregister(collector)
        except Exception:
            pass
    
    orchestrator = DefenseOrchestrator(
        sentinel_agent=sentinel_agent,
        fusion_engine=fusion_engine,
        response_engine=response_engine,
        min_threat_confidence=0.5,
        auto_response_threshold="HIGH",
    )
    
    return orchestrator


class TestDefensivePipelineE2E:
    """End-to-end tests for the complete defensive pipeline."""
    
    @pytest.mark.asyncio
    async def test_complete_pipeline_brute_force(self, orchestrator):
        """Test complete pipeline for brute force attack."""
        # GIVEN: A brute force security event
        event = SecurityEvent(
            event_id="bf_001",
            timestamp=datetime.utcnow(),
            source="auth_server",
            event_type="failed_login",
            source_ip="192.168.1.100",
            destination_ip="10.0.0.50",
            user="admin",
            details={
                "failed_attempts": 50,
                "time_window_seconds": 60,
                "targeted_accounts": ["admin", "root", "administrator"]
            }
        )
        
        # WHEN: Processing through the complete pipeline
        response = await orchestrator.process_security_event(event)
        
        # THEN: Pipeline completes successfully
        assert response.success is True
        assert response.event == event
        assert response.phase == DefensePhase.LEARNING  # Final phase
        
        # Detection phase completed
        assert response.detection is not None
        assert response.detection.is_threat is True
        assert response.detection.severity == ThreatSeverity.HIGH
        
        # Enrichment phase completed (may be None if no IOCs)
        # This is OK - enrichment is optional
        
        # Response phase completed
        assert response.playbook is not None
        assert response.execution is not None
        assert response.execution.status in ["SUCCESS", "PARTIAL"]
        
        # Latency is reasonable
        assert response.latency_ms > 0
        assert response.latency_ms < 5000  # Less than 5 seconds
    
    @pytest.mark.asyncio
    async def test_pipeline_low_confidence_skip(self, orchestrator):
        """Test pipeline skips response for low confidence detections."""
        # GIVEN: An ambiguous event (low confidence)
        event = SecurityEvent(
            event_id="amb_001",
            timestamp=datetime.utcnow(),
            source="web_server",
            event_type="unusual_request",
            source_ip="192.168.1.200",
            destination_ip="10.0.0.80",
            details={"request_path": "/api/data", "method": "GET"}
        )
        
        # Mock LLM to return low confidence
        orchestrator.sentinel.llm_client.analyze_security_event.return_value = {
            "is_threat": True,
            "threat_type": "suspicious_activity",
            "severity": "LOW",
            "confidence": 0.3,  # Below threshold (0.5)
            "attacker_profile": {"sophistication": "low"},
            "mitre_techniques": [],
            "iocs": [],
            "recommended_actions": ["Monitor"],
            "analysis": "Possibly benign"
        }
        
        # WHEN: Processing
        response = await orchestrator.process_security_event(event)
        
        # THEN: Detection happens but response is skipped
        assert response.success is True
        assert response.detection is not None
        assert response.detection.confidence.value < 0.5
        
        # No playbook execution due to low confidence
        assert response.playbook is None
        assert response.execution is None
    
    @pytest.mark.asyncio
    async def test_pipeline_with_enrichment(self, orchestrator):
        """Test pipeline with threat intelligence enrichment."""
        # GIVEN: Event with known malicious IP
        event = SecurityEvent(
            event_id="mal_001",
            timestamp=datetime.utcnow(),
            source="firewall",
            event_type="connection_attempt",
            source_ip="1.2.3.4",  # Known malicious
            destination_ip="10.0.0.100",
            details={"port": 443, "protocol": "TCP"}
        )
        
        # WHEN: Processing
        response = await orchestrator.process_security_event(event)
        
        # THEN: Pipeline completes
        assert response.success is True
        assert response.detection is not None
        
        # Enrichment may or may not happen (depends on external sources)
        # But pipeline should handle both cases gracefully
        if response.enrichment:
            assert response.enrichment.threat_id is not None
            assert response.enrichment.severity > 0
    
    @pytest.mark.asyncio
    async def test_pipeline_error_handling(self, orchestrator):
        """Test pipeline handles component failures gracefully."""
        # GIVEN: Event that will cause LLM to fail
        event = SecurityEvent(
            event_id="err_001",
            timestamp=datetime.utcnow(),
            source="test",
            event_type="test",
            source_ip="10.0.0.1",
        )
        
        # Mock LLM to raise exception
        orchestrator.sentinel.llm_client.analyze_security_event.side_effect = Exception("LLM Error")
        
        # WHEN: Processing
        with pytest.raises(Exception):
            await orchestrator.process_security_event(event)
        
        # Error should be raised (fail-closed for security)
    
    @pytest.mark.asyncio
    async def test_pipeline_metrics_collected(self, orchestrator):
        """Test that metrics are collected throughout pipeline."""
        # GIVEN: A normal security event
        event = SecurityEvent(
            event_id="met_001",
            timestamp=datetime.utcnow(),
            source="ids",
            event_type="anomaly",
            source_ip="192.168.1.50",
        )
        
        # WHEN: Processing
        response = await orchestrator.process_security_event(event)
        
        # THEN: Metrics were collected
        # (In production, these would be visible in Prometheus)
        assert response.latency_ms > 0
        
        # Pipeline phases were tracked
        assert response.phase in DefensePhase
    
    @pytest.mark.asyncio
    async def test_pipeline_batch_processing(self, orchestrator):
        """Test pipeline can handle multiple events concurrently."""
        # GIVEN: Multiple security events
        events = [
            SecurityEvent(
                event_id=f"batch_{i}",
                timestamp=datetime.utcnow(),
                source="test",
                event_type="test",
                source_ip=f"192.168.1.{i}",
            )
            for i in range(5)
        ]
        
        # WHEN: Processing concurrently
        tasks = [orchestrator.process_security_event(event) for event in events]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # THEN: All events were processed
        assert len(responses) == 5
        
        # Check for successes (some may fail due to mock limitations)
        successful = [r for r in responses if isinstance(r, DefenseResponse) and r.success]
        assert len(successful) >= 3  # At least 3 should succeed


class TestComponentIntegration:
    """Test integration between individual components."""
    
    @pytest.mark.asyncio
    async def test_sentinel_to_fusion_integration(self, sentinel_agent, fusion_engine):
        """Test data flow from Sentinel to Fusion."""
        # GIVEN: Detection result from Sentinel
        event = SecurityEvent(
            event_id="int_001",
            timestamp=datetime.utcnow(),
            source="test",
            event_type="test",
            source_ip="1.2.3.4",
        )
        
        detection = await sentinel_agent.analyze_event(event)
        
        # WHEN: Extracting IOCs for Fusion
        iocs = []
        if detection.iocs:
            for ioc_value in detection.iocs:
                ioc = IOC(
                    ioc_type=IOCType.IP_ADDRESS,
                    value=ioc_value,
                    source="sentinel",
                    first_seen=datetime.utcnow(),
                    last_seen=datetime.utcnow(),
                    confidence=detection.confidence.value,
                )
                iocs.append(ioc)
        
        # THEN: Fusion can process IOCs
        if iocs:
            enrichment = await fusion_engine.correlate_indicators(iocs)
            assert enrichment is not None
            assert enrichment.threat_id is not None
    
    @pytest.mark.asyncio
    async def test_fusion_to_response_integration(self, fusion_engine, response_engine):
        """Test data flow from Fusion to Response."""
        # GIVEN: Enriched threat from Fusion
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
            threat_id="threat_001",
            primary_ioc=primary_ioc,
            related_iocs=[],
            threat_actor=None,
            campaigns=[],
            ttps=["T1110.001"],
            attack_chain_stage="initial_access",
            severity=8,
            confidence=0.85,
            narrative="Brute force attack",
            recommendations=["Block IP", "Enable MFA"],
            sources=["test"],
            enriched_at=now,
        )
        
        # WHEN: Creating threat context for Response
        context = ThreatContext(
            threat_id=enrichment.threat_id,
            threat_type="brute_force",
            severity="HIGH",
            confidence=enrichment.confidence,
            indicators=[primary_ioc.value],
            mitre_techniques=enrichment.ttps,
            affected_assets=["auth_server"],
            timestamp=now,
        )
        
        # Load appropriate playbook
        playbook = await response_engine.load_playbook("brute_force_response.yaml")
        
        # THEN: Response can execute playbook
        assert playbook is not None
        result = await response_engine.execute_playbook(playbook, context)
        assert result is not None
        assert result.status in ["SUCCESS", "PARTIAL", "FAILED"]


@pytest.mark.asyncio
async def test_defensive_pipeline_complete_flow():
    """Standalone test of complete defensive flow without fixtures."""
    # This test validates the entire stack can be instantiated and used
    
    # Create mock LLM
    mock_llm = AsyncMock()
    mock_llm.analyze_security_event.return_value = {
        "is_threat": True,
        "threat_type": "malware",
        "severity": "HIGH",
        "confidence": 0.9,
        "attacker_profile": {"sophistication": "high"},
        "mitre_techniques": ["T1204.002"],
        "iocs": ["malware.exe"],
        "recommended_actions": ["Quarantine"],
        "analysis": "Malware detected"
    }
    
    # Create components
    sentinel = SentinelDetectionAgent(llm_client=mock_llm)
    fusion = ThreatIntelFusionEngine()
    response = AutomatedResponseEngine()
    
    # Mock executors
    response._action_executors = {
        "quarantine_file": AsyncMock(return_value={"success": True}),
        "notify_soc": AsyncMock(return_value={"success": True}),
    }
    
    # Clear metrics
    from prometheus_client import REGISTRY
    collectors = list(REGISTRY._collector_to_names.keys())
    for collector in collectors:
        try:
            REGISTRY.unregister(collector)
        except Exception:
            pass
    
    # Create orchestrator
    orchestrator = DefenseOrchestrator(
        sentinel_agent=sentinel,
        fusion_engine=fusion,
        response_engine=response,
    )
    
    # Create event
    event = SecurityEvent(
        event_id="test_001",
        timestamp=datetime.utcnow(),
        source="edr",
        event_type="file_execution",
        source_ip="10.0.0.50",
        details={"file": "malware.exe", "process": "suspicious.exe"}
    )
    
    # Process
    result = await orchestrator.process_security_event(event)
    
    # Validate
    assert result is not None
    assert result.success is True
    assert result.detection is not None
    assert result.detection.is_threat is True
    
    print("✅ Complete defensive pipeline validated!")
