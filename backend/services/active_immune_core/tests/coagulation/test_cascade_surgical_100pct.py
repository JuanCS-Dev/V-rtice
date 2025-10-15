"""Coagulation Cascade - Surgical Tests for 100% Coverage"""

import pytest
from datetime import datetime
from prometheus_client import REGISTRY
from coagulation.cascade import (
    CoagulationCascadeSystem,
    CascadeResult,
    CascadeState,
    CascadePhase,
)
from coagulation.models import EnrichedThreat, ThreatSeverity, ThreatSource


@pytest.fixture(autouse=True)
def clear_registry():
    """Clear prometheus registry"""
    collectors = list(REGISTRY._collector_to_names.keys())
    for c in collectors:
        try:
            REGISTRY.unregister(c)
        except:
            pass
    yield


@pytest.fixture
def threat():
    """Create test threat"""
    return EnrichedThreat(
        threat_id="t1",
        source=ThreatSource(ip="192.168.1.100"),
        severity=ThreatSeverity.MEDIUM,
        threat_type="intrusion",
    )


class TestCascadeResultMissingLines:
    """Target Line 106"""

    def test_get_duration_with_no_completed_at(self, threat):
        """Line 106: get_duration returns 0.0 when not completed"""
        state = CascadeState(
            cascade_id="test",
            threat=threat,
            phase=CascadePhase.PRIMARY,
            started_at=datetime.utcnow(),
        )
        # Don't set completed_at
        result = CascadeResult(
            cascade_id="test",
            status="SUCCESS",
            state=state
        )
        
        # Should return 0.0 (line 106)
        assert result.get_duration() == 0.0


class TestNeutralizationSucceededMissingLines:
    """Target Line 430"""

    def test_neutralization_succeeded_false_path(self):
        """Line 430: _neutralization_succeeded returns False for non-dict"""
        system = CoagulationCascadeSystem()
        
        # Non-dict inputs (line 430 return False)
        assert system._neutralization_succeeded(None) == False
        assert system._neutralization_succeeded("invalid") == False
        assert system._neutralization_succeeded(123) == False
        
        # Dict with wrong status
        assert system._neutralization_succeeded({"status": "failed"}) == False
        assert system._neutralization_succeeded({}) == False


@pytest.mark.asyncio
class TestCascadeSkipPaths:
    """Target Lines 267, 290, 349-350, 411-412"""

    async def test_primary_sufficient_skips_secondary(self, threat, monkeypatch):
        """Line 267: Primary sufficient, skip secondary"""
        system = CoagulationCascadeSystem()
        
        # Make primary sufficient
        monkeypatch.setattr(system, "_needs_secondary", lambda p: False)
        
        async def mock_primary(state):
            return {"status": "CONTAINED"}
        
        async def mock_neut(state):
            return {"status": "neutralized"}
        
        monkeypatch.setattr(system, "_execute_primary", mock_primary)
        monkeypatch.setattr(system, "_execute_neutralization", mock_neut)
        
        result = await system.initiate_cascade(threat)
        
        # Secondary should be None (skipped, line 267)
        assert result.state.secondary_result is None

    async def test_neutralization_fails_skips_fibrinolysis(self, threat, monkeypatch):
        """Line 290: Neutralization incomplete, skip restoration"""
        system = CoagulationCascadeSystem()
        
        async def mock_primary(state):
            return {"status": "CONTAINED"}
        
        async def mock_neut_fail(state):
            return {"status": "FAILED"}  # Not neutralized
        
        monkeypatch.setattr(system, "_execute_primary", mock_primary)
        monkeypatch.setattr(system, "_execute_neutralization", mock_neut_fail)
        monkeypatch.setattr(system, "_needs_secondary", lambda p: False)
        
        result = await system.initiate_cascade(threat)
        
        # Restoration should be None (skipped, line 290)
        assert result.state.restoration_result is None

    async def test_execute_primary_without_rte(self, threat):
        """Lines 349-350: _execute_primary without RTE dependency"""
        system = CoagulationCascadeSystem()
        system.reflex_triage_engine = None  # No RTE
        
        state = CascadeState(
            cascade_id="test",
            threat=threat,
            phase=CascadePhase.PRIMARY,
            started_at=datetime.utcnow(),
        )
        
        # Should use fallback (lines 349-350)
        result = await system._execute_primary(state)
        
        assert result.status == "CONTAINED"
        assert result.containment_type == "primary"

    async def test_execute_neutralization_without_response_engine(self, threat):
        """Lines 411-412: _execute_neutralization without response engine"""
        system = CoagulationCascadeSystem()
        system.automated_response = None  # No response engine
        
        state = CascadeState(
            cascade_id="test",
            threat=threat,
            phase=CascadePhase.NEUTRALIZATION,
            started_at=datetime.utcnow(),
        )
        
        # Should use fallback (lines 411-412)
        result = await system._execute_neutralization(state)
        
        assert result["status"] == "neutralized"
        assert result["method"] == "simulated"
