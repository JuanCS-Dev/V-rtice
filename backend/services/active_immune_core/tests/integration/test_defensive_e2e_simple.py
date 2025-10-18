"""Simple E2E Test - Defensive AI Pipeline

Validates complete defensive workflow end-to-end.

Authors: MAXIMUS Team
Date: 2025-10-12
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock

from detection.sentinel_agent import SecurityEvent
from orchestration.defense_orchestrator import DefenseOrchestrator, DefensePhase


@pytest.mark.asyncio
async def test_complete_defensive_pipeline():
    """Test complete pipeline: Event → Detection → Intel → Response."""
    # Clear metrics
    from prometheus_client import REGISTRY, CollectorRegistry
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
    
    # Create components
    from detection.sentinel_agent import SentinelDetectionAgent
    from intelligence.fusion_engine import ThreatIntelFusionEngine
    from response.automated_response import AutomatedResponseEngine
    
    sentinel = SentinelDetectionAgent(llm_client=mock_llm)
    
    # Create Fusion with minimal mocks
    fusion = ThreatIntelFusionEngine(
        sources={},  # No external sources
        llm_client=mock_llm,
        registry=CollectorRegistry(),
    )
    
    response = AutomatedResponseEngine()
    
    # Mock response actions
    response._action_executors = {
        "block_ip": AsyncMock(return_value={"success": True}),
        "notify_soc": AsyncMock(return_value={"success": True}),
    }
    
    # Create orchestrator
    orchestrator = DefenseOrchestrator(
        sentinel_agent=sentinel,
        fusion_engine=fusion,
        response_engine=response,
    )
    
    # Create security event
    event = SecurityEvent(
        event_id="e2e_001",
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
    
    # Validate
    assert result is not None
    assert result.success is True
    assert result.detection is not None
    assert result.detection.is_threat is True
    assert result.phase == DefensePhase.LEARNING  # Final phase
    assert result.latency_ms > 0
    
    print("✅ E2E Pipeline validated successfully!")


@pytest.mark.asyncio
async def test_low_confidence_skip():
    """Test pipeline skips response for low confidence."""
    # Setup
    from prometheus_client import REGISTRY, CollectorRegistry
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
        "confidence": 0.3,  # Low confidence
        "attacker_profile": {"sophistication": "low"},
        "mitre_techniques": [],
        "iocs": [],
        "recommended_actions": [],
        "analysis": "Maybe suspicious"
    }
    
    from detection.sentinel_agent import SentinelDetectionAgent
    from intelligence.fusion_engine import ThreatIntelFusionEngine
    from response.automated_response import AutomatedResponseEngine
    
    sentinel = SentinelDetectionAgent(llm_client=mock_llm)
    fusion = ThreatIntelFusionEngine(
        sources={},
        llm_client=mock_llm,
        registry=CollectorRegistry(),
    )
    response = AutomatedResponseEngine()
    
    orchestrator = DefenseOrchestrator(
        sentinel_agent=sentinel,
        fusion_engine=fusion,
        response_engine=response,
        min_threat_confidence=0.5,
    )
    
    event = SecurityEvent(
        event_id="low_001",
        timestamp=datetime.utcnow(),
        source="test",
        event_type="test",
        source_ip="10.0.0.1",
    )
    
    result = await orchestrator.process_security_event(event)
    
    # Should detect but not respond
    assert result.detection is not None
    assert result.playbook is None  # No response due to low confidence
    
    print("✅ Low confidence handling validated!")
