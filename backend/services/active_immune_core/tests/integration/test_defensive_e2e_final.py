"""E2E Test - Defensive AI Pipeline (FINAL)

Validates complete defensive workflow end-to-end.

Authors: MAXIMUS Team  
Date: 2025-10-12
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from detection.sentinel_agent import SecurityEvent
from orchestration.defense_orchestrator import DefenseOrchestrator, DefensePhase
from response.automated_response import PlaybookResult


@pytest.mark.asyncio
async def test_e2e_defensive_pipeline_complete():
    """Test complete E2E pipeline with all components."""
    # Clear metrics
    from prometheus_client import REGISTRY
    collectors = list(REGISTRY._collector_to_names.keys())
    for collector in collectors:
        try:
            REGISTRY.unregister(collector)
        except Exception:
            pass
    
    # Create mock LLM
    mock_llm = AsyncMock()
    mock_llm.analyze_security_event.return_value = {
        "is_threat": True,
        "threat_type": "brute_force",
        "severity": "HIGH",
        "confidence": 0.85,
        "attacker_profile": {"sophistication": "medium"},
        "mitre_techniques": ["T1110.001"],
        "iocs": ["192.168.1.100"],
        "recommended_actions": ["Block IP"],
        "analysis": "Brute force detected"
    }
    
    # Create Sentinel
    from detection.sentinel_agent import SentinelDetectionAgent
    sentinel = SentinelDetectionAgent(llm_client=mock_llm)
    
    # Mock Fusion Engine
    fusion = AsyncMock()
    
    # Mock Response Engine
    response = AsyncMock()
    response.load_playbook.return_value = MagicMock(
        name="brute_force_response",
        actions=[]
    )
    response.execute_playbook.return_value = PlaybookResult(
        playbook_id="brute_force_response",
        threat_context=MagicMock(),
        status="SUCCESS",
        actions_executed=2,
        actions_failed=0,
        actions_pending_hotl=0,
        execution_time_seconds=1.5,
        action_results=[],
        errors=[],
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
    )
    
    # Create orchestrator
    orchestrator = DefenseOrchestrator(
        sentinel_agent=sentinel,
        fusion_engine=fusion,
        response_engine=response,
    )
    
    # Create security event
    event = SecurityEvent(
        event_id="e2e_final",
        timestamp=datetime.utcnow(),
        source="auth_server",
        event_type="failed_login",
        source_ip="192.168.1.100",
        destination_ip="10.0.0.50",
        user="admin",
        details={"failed_attempts": 50}
    )
    
    # Execute pipeline
    result = await orchestrator.process_security_event(event)
    
    # Validate END-TO-END flow
    assert result is not None, "Pipeline should return result"
    assert result.success is True, "Pipeline should succeed"
    assert result.detection is not None, "Detection phase should complete"
    assert result.detection.is_threat is True, "Should detect threat"
    assert result.phase == DefensePhase.LEARNING, "Should reach final phase"
    assert result.latency_ms > 0, "Should track latency"
    assert result.execution is not None, "Should execute playbook"
    assert result.execution.status == "SUCCESS", "Playbook should succeed"
    
    print("✅ E2E Pipeline SUCCESS!")
    print(f"   Latency: {result.latency_ms:.0f}ms")
    print(f"   Phases: {result.phase.value}")
    print(f"   Actions: {result.execution.actions_executed}")


@pytest.mark.asyncio  
async def test_e2e_low_confidence_no_response():
    """Test pipeline skips response for low confidence threats."""
    from prometheus_client import REGISTRY
    collectors = list(REGISTRY._collector_to_names.keys())
    for collector in collectors:
        try:
            REGISTRY.unregister(collector)
        except Exception:
            pass
    
    mock_llm = AsyncMock()
    mock_llm.analyze_security_event.return_value = {
        "is_threat": True,
        "threat_type": "suspicious",
        "severity": "LOW",
        "confidence": 0.3,  # Below threshold
        "attacker_profile": {"sophistication": "low"},
        "mitre_techniques": [],
        "iocs": [],
        "recommended_actions": [],
        "analysis": "Possibly benign"
    }
    
    from detection.sentinel_agent import SentinelDetectionAgent
    sentinel = SentinelDetectionAgent(llm_client=mock_llm)
    fusion = AsyncMock()
    response = AsyncMock()
    
    orchestrator = DefenseOrchestrator(
        sentinel_agent=sentinel,
        fusion_engine=fusion,
        response_engine=response,
        min_threat_confidence=0.5,
    )
    
    event = SecurityEvent(
        event_id="low_conf",
        timestamp=datetime.utcnow(),
        source="test",
        event_type="test",
        source_ip="10.0.0.1",
    )
    
    result = await orchestrator.process_security_event(event)
    
    # Should detect but NOT respond
    assert result.detection is not None, "Should detect"
    assert result.playbook is None, "Should skip playbook (low confidence)"
    assert result.execution is None, "Should not execute (low confidence)"
    
    print("✅ Low confidence handling validated!")
