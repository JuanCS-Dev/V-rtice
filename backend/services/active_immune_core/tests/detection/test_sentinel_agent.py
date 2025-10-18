"""Tests for Sentinel Detection Agent.

Tests cover:
- Event analysis with various threat types
- MITRE ATT&CK mapping
- Attacker profiling (theory-of-mind)
- Alert triage
- Error handling

Authors: MAXIMUS Team
Date: 2025-10-12
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from detection.sentinel_agent import (
    AttackerProfile,
    DetectionConfidence,
    DetectionResult,
    MITRETechnique,
    SecurityEvent,
    SentinelAnalysisError,
    SentinelDetectionAgent,
    ThreatSeverity,
)


@pytest.fixture
def mock_llm_client():
    """Mock OpenAI async client."""
    client = AsyncMock()
    return client


@pytest.fixture
def sentinel_agent(mock_llm_client):
    """Create Sentinel agent with mocked dependencies."""
    # Clear Prometheus registry to avoid duplicates
    from prometheus_client import REGISTRY
    collectors = list(REGISTRY._collector_to_names.keys())
    for collector in collectors:
        try:
            REGISTRY.unregister(collector)
        except Exception:
            pass
    
    return SentinelDetectionAgent(
        llm_client=mock_llm_client,
        mitre_mapper=None,
        threat_intel_feed=None,
        event_history=None,
        model="gpt-4o",
        max_context_events=10,
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
        payload={"attempts": 50, "username": "admin"},
        context={},
    )


@pytest.fixture
def sample_brute_force_response():
    """Sample LLM response for brute force attack."""
    return {
        "is_threat": True,
        "severity": "HIGH",
        "confidence": 0.95,
        "mitre_techniques": [
            {
                "technique_id": "T1110",
                "tactic": "Credential Access",
                "technique_name": "Brute Force",
                "confidence": 0.95,
            }
        ],
        "threat_description": "Brute force attack detected against SSH service. "
        "50 failed login attempts from 192.168.1.100 in short timeframe.",
        "recommended_actions": [
            "Block source IP 192.168.1.100",
            "Enable rate limiting on SSH",
            "Deploy honeypot for TTP collection",
        ],
        "reasoning": "High number of failed login attempts (50) in rapid succession "
        "indicates automated brute force attack. Source IP not in whitelist.",
    }


class TestSecurityEvent:
    """Tests for SecurityEvent model."""

    def test_security_event_creation(self, sample_event):
        """Test creating security event."""
        assert sample_event.event_id == "evt_001"
        assert sample_event.source == "firewall"
        assert sample_event.event_type == "failed_login"
        assert sample_event.source_ip == "192.168.1.100"

    def test_security_event_to_dict(self, sample_event):
        """Test serialization to dict."""
        event_dict = sample_event.to_dict()
        
        assert event_dict["event_id"] == "evt_001"
        assert event_dict["source"] == "firewall"
        assert event_dict["source_ip"] == "192.168.1.100"
        assert "timestamp" in event_dict


class TestMITRETechnique:
    """Tests for MITRE technique model."""

    def test_mitre_technique_creation(self):
        """Test creating MITRE technique."""
        technique = MITRETechnique(
            technique_id="T1110",
            tactic="Credential Access",
            technique_name="Brute Force",
            confidence=0.95,
        )
        
        assert technique.technique_id == "T1110"
        assert technique.tactic == "Credential Access"
        assert technique.confidence == 0.95

    def test_mitre_technique_invalid_confidence(self):
        """Test validation of confidence range."""
        with pytest.raises(ValueError, match="Confidence must be 0.0-1.0"):
            MITRETechnique(
                technique_id="T1110",
                tactic="Credential Access",
                technique_name="Brute Force",
                confidence=1.5,  # Invalid
            )


class TestAttackerProfile:
    """Tests for AttackerProfile model."""

    def test_attacker_profile_creation(self):
        """Test creating attacker profile."""
        profile = AttackerProfile(
            profile_id="profile_001",
            skill_level="intermediate",
            tools_detected=["nmap", "hydra"],
            objectives=["credential_theft"],
            next_move_prediction="lateral_movement",
            confidence=0.85,
        )
        
        assert profile.profile_id == "profile_001"
        assert profile.skill_level == "intermediate"
        assert "nmap" in profile.tools_detected

    def test_attacker_profile_invalid_skill_level(self):
        """Test validation of skill level."""
        with pytest.raises(ValueError, match="Invalid skill_level"):
            AttackerProfile(
                profile_id="profile_001",
                skill_level="invalid",  # Not in valid_levels
            )


class TestSentinelDetectionAgent:
    """Tests for SentinelDetectionAgent."""

    @pytest.mark.asyncio
    async def test_analyze_event_threat_detected(
        self, sentinel_agent, sample_event, sample_brute_force_response, mock_llm_client
    ):
        """Test analyzing event that is a threat."""
        # Mock LLM response
        mock_response = AsyncMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content=json.dumps(sample_brute_force_response)
                )
            )
        ]
        mock_llm_client.chat.completions.create.return_value = mock_response
        
        # Analyze event
        result = await sentinel_agent.analyze_event(sample_event)
        
        # Assertions
        assert isinstance(result, DetectionResult)
        assert result.is_threat is True
        assert result.severity == ThreatSeverity.HIGH
        assert result.confidence == DetectionConfidence.CERTAIN
        assert len(result.mitre_techniques) == 1
        assert result.mitre_techniques[0].technique_id == "T1110"
        assert "brute force" in result.threat_description.lower()
        assert len(result.recommended_actions) > 0

    @pytest.mark.asyncio
    async def test_analyze_event_benign(
        self, sentinel_agent, sample_event, mock_llm_client
    ):
        """Test analyzing benign event."""
        # Mock benign response
        benign_response = {
            "is_threat": False,
            "severity": "INFO",
            "confidence": 0.2,
            "mitre_techniques": [],
            "threat_description": "Normal authentication event. No threat detected.",
            "recommended_actions": ["Continue monitoring"],
            "reasoning": "Single failed login attempt from known IP range.",
        }
        
        mock_response = AsyncMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps(benign_response)))
        ]
        mock_llm_client.chat.completions.create.return_value = mock_response
        
        result = await sentinel_agent.analyze_event(sample_event)
        
        assert result.is_threat is False
        assert result.severity == ThreatSeverity.INFO
        assert result.confidence == DetectionConfidence.LOW

    @pytest.mark.asyncio
    async def test_analyze_event_llm_failure(
        self, sentinel_agent, sample_event, mock_llm_client
    ):
        """Test handling LLM failure."""
        # Mock LLM error
        mock_llm_client.chat.completions.create.side_effect = Exception("API error")
        
        with pytest.raises(SentinelAnalysisError, match="Failed to analyze event"):
            await sentinel_agent.analyze_event(sample_event)

    @pytest.mark.asyncio
    async def test_predict_attacker_intent(
        self, sentinel_agent, sample_event, mock_llm_client
    ):
        """Test predicting attacker intent."""
        # Create event chain (attack progression)
        event_chain = [
            sample_event,
            SecurityEvent(
                event_id="evt_002",
                timestamp=datetime.utcnow() + timedelta(minutes=5),
                source="ids",
                event_type="port_scan",
                source_ip="192.168.1.100",
                destination_ip="10.0.0.0/24",
                payload={"ports_scanned": 1000},
            ),
            SecurityEvent(
                event_id="evt_003",
                timestamp=datetime.utcnow() + timedelta(minutes=10),
                source="endpoint",
                event_type="lateral_movement",
                source_ip="10.0.0.5",
                destination_ip="10.0.0.10",
                payload={"method": "psexec"},
            ),
        ]
        
        # Mock LLM profile response
        profile_response = {
            "skill_level": "intermediate",
            "tools_detected": ["nmap", "hydra", "psexec"],
            "ttps": [
                {
                    "technique_id": "T1046",
                    "tactic": "Discovery",
                    "technique_name": "Network Service Discovery",
                    "confidence": 0.9,
                },
                {
                    "technique_id": "T1110",
                    "tactic": "Credential Access",
                    "technique_name": "Brute Force",
                    "confidence": 0.95,
                },
                {
                    "technique_id": "T1021",
                    "tactic": "Lateral Movement",
                    "technique_name": "Remote Services",
                    "confidence": 0.85,
                },
            ],
            "objectives": ["initial_access", "lateral_movement", "credential_theft"],
            "next_move_prediction": "Attacker will likely attempt to escalate "
            "privileges on compromised host and establish persistence.",
            "confidence": 0.85,
        }
        
        mock_response = AsyncMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps(profile_response)))
        ]
        mock_llm_client.chat.completions.create.return_value = mock_response
        
        # Predict intent
        profile = await sentinel_agent.predict_attacker_intent(event_chain)
        
        # Assertions
        assert isinstance(profile, AttackerProfile)
        assert profile.skill_level == "intermediate"
        assert "nmap" in profile.tools_detected
        assert len(profile.ttps) == 3
        assert "T1046" in [t.technique_id for t in profile.ttps]
        assert "lateral_movement" in profile.objectives
        assert "privilege" in profile.next_move_prediction.lower()
        assert profile.confidence == 0.85

    @pytest.mark.asyncio
    async def test_predict_attacker_intent_empty_chain(self, sentinel_agent):
        """Test error handling for empty event chain."""
        with pytest.raises(ValueError, match="event_chain cannot be empty"):
            await sentinel_agent.predict_attacker_intent([])

    @pytest.mark.asyncio
    async def test_triage_alert_escalate(
        self, sentinel_agent, mock_llm_client
    ):
        """Test triaging alert that should escalate."""
        alert = {
            "alert_id": "alert_001",
            "type": "malware_detected",
            "severity": "HIGH",
            "source_ip": "192.168.1.100",
            "file_hash": "abc123",
        }
        
        # Mock triage response (escalate)
        triage_response = {
            "escalate": True,
            "reasoning": "New malware hash not seen before. High severity. "
            "Target is critical asset.",
            "confidence": 0.9,
        }
        
        mock_response = AsyncMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps(triage_response)))
        ]
        mock_llm_client.chat.completions.create.return_value = mock_response
        
        should_escalate = await sentinel_agent.triage_alert(alert)
        
        assert should_escalate is True

    @pytest.mark.asyncio
    async def test_triage_alert_false_positive(
        self, sentinel_agent, mock_llm_client
    ):
        """Test triaging alert that is false positive."""
        alert = {
            "alert_id": "alert_002",
            "type": "suspicious_outbound",
            "severity": "LOW",
            "source_ip": "10.0.0.5",
        }
        
        # Mock triage response (don't escalate)
        triage_response = {
            "escalate": False,
            "reasoning": "Similar alerts have 90% false positive rate. "
            "Likely automated backup traffic.",
            "confidence": 0.85,
        }
        
        mock_response = AsyncMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps(triage_response)))
        ]
        mock_llm_client.chat.completions.create.return_value = mock_response
        
        should_escalate = await sentinel_agent.triage_alert(alert)
        
        assert should_escalate is False

    @pytest.mark.asyncio
    async def test_triage_alert_error_escalates(
        self, sentinel_agent, mock_llm_client
    ):
        """Test that errors in triage cause escalation (fail-safe)."""
        alert = {"alert_id": "alert_003"}
        
        # Mock LLM error
        mock_llm_client.chat.completions.create.side_effect = Exception("API error")
        
        # Should escalate on error (fail-safe)
        should_escalate = await sentinel_agent.triage_alert(alert)
        
        assert should_escalate is True

    def test_build_detection_prompt(self, sentinel_agent, sample_event):
        """Test building detection prompt."""
        context = {
            "recent_events": [],
            "threat_intel": {},
            "asset_info": {},
            "network_baseline": {},
        }
        
        prompt = sentinel_agent._build_detection_prompt(sample_event, context)
        
        assert "evt_001" in prompt
        assert "192.168.1.100" in prompt
        assert "failed_login" in prompt
        assert "MITRE ATT&CK" in prompt

    def test_build_attack_narrative(self, sentinel_agent, sample_event):
        """Test building attack narrative."""
        event_chain = [
            sample_event,
            SecurityEvent(
                event_id="evt_002",
                timestamp=datetime.utcnow() + timedelta(minutes=5),
                source="ids",
                event_type="port_scan",
                source_ip="192.168.1.100",
                destination_ip="10.0.0.0/24",
            ),
        ]
        
        narrative = sentinel_agent._build_attack_narrative(event_chain)
        
        assert "1." in narrative
        assert "2." in narrative
        assert "failed_login" in narrative
        assert "port_scan" in narrative


class TestDetectionResultSerialization:
    """Tests for DetectionResult serialization."""

    def test_detection_result_to_dict(self):
        """Test converting detection result to dict."""
        result = DetectionResult(
            event_id="evt_001",
            is_threat=True,
            severity=ThreatSeverity.HIGH,
            confidence=DetectionConfidence.CERTAIN,
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
            attacker_profile=AttackerProfile(
                profile_id="profile_001",
                skill_level="intermediate",
            ),
            reasoning="High confidence detection",
            analyzed_at=datetime.utcnow(),
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["event_id"] == "evt_001"
        assert result_dict["is_threat"] is True
        assert result_dict["severity"] == "high"  # Enum.value is lowercase
        assert result_dict["confidence"] == 0.95
        assert len(result_dict["mitre_techniques"]) == 1
        assert result_dict["attacker_profile"]["skill_level"] == "intermediate"


    @pytest.mark.asyncio
    async def test_gather_context_with_history(self, sentinel_agent, sample_event):
        """Test gathering context with history."""
        # Mock history
        mock_history = AsyncMock()
        mock_history.get_recent_events.return_value = [
            {"event_id": "evt_old_1", "source_ip": "192.168.1.100"}
        ]
        sentinel_agent.history = mock_history
        
        context = await sentinel_agent._gather_context(sample_event)
        
        assert "recent_events" in context
        assert len(context["recent_events"]) > 0
        mock_history.get_recent_events.assert_called_once()

    @pytest.mark.asyncio
    async def test_gather_context_with_threat_intel(self, sentinel_agent, sample_event):
        """Test gathering context with threat intel."""
        # Mock threat intel
        mock_intel = AsyncMock()
        mock_intel.lookup_ip.return_value = {
            "reputation": "malicious",
            "category": "botnet"
        }
        sentinel_agent.threat_intel = mock_intel
        
        context = await sentinel_agent._gather_context(sample_event)
        
        assert "threat_intel" in context
        assert context["threat_intel"]["reputation"] == "malicious"
        mock_intel.lookup_ip.assert_called_once_with("192.168.1.100")

    @pytest.mark.asyncio
    async def test_gather_context_error_handling(self, sentinel_agent, sample_event):
        """Test graceful handling of context gathering errors."""
        # Mock history that throws error
        mock_history = AsyncMock()
        mock_history.get_recent_events.side_effect = Exception("DB error")
        sentinel_agent.history = mock_history
        
        # Should not raise, just log warning
        context = await sentinel_agent._gather_context(sample_event)
        
        assert "recent_events" in context
        assert context["recent_events"] == []

    @pytest.mark.asyncio
    async def test_predict_attacker_intent_with_intel(
        self, sentinel_agent, sample_event, mock_llm_client
    ):
        """Test attacker prediction with threat intel context."""
        # Mock threat intel
        mock_intel = AsyncMock()
        mock_intel.get_relevant_intel.return_value = "Known APT28 infrastructure"
        sentinel_agent.threat_intel = mock_intel
        
        event_chain = [sample_event]
        
        profile_response = {
            "skill_level": "nation_state",
            "tools_detected": ["custom_backdoor"],
            "ttps": [],
            "objectives": ["espionage"],
            "next_move_prediction": "data exfiltration",
            "confidence": 0.9,
        }
        
        mock_response = AsyncMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps(profile_response)))
        ]
        mock_llm_client.chat.completions.create.return_value = mock_response
        
        profile = await sentinel_agent.predict_attacker_intent(event_chain)
        
        assert profile.skill_level == "nation_state"
        mock_intel.get_relevant_intel.assert_called_once()

    @pytest.mark.asyncio
    async def test_parse_llm_response_invalid_json(self, sentinel_agent, sample_event):
        """Test error handling for invalid LLM response."""
        invalid_response = {
            "is_threat": True,
            "severity": "INVALID_SEVERITY",  # Invalid enum value
            "confidence": 0.8,
            "mitre_techniques": [],
            "threat_description": "Test",
            "recommended_actions": [],
            "reasoning": "Test",
        }
        
        with pytest.raises(SentinelAnalysisError, match="Invalid LLM response format"):
            await sentinel_agent._parse_llm_response(sample_event, invalid_response)

    @pytest.mark.asyncio
    async def test_triage_alert_with_history(
        self, sentinel_agent, mock_llm_client
    ):
        """Test alert triage with historical context."""
        alert = {
            "alert_id": "alert_004",
            "type": "scan_detected",
        }
        
        # Mock history with similar alerts
        mock_history = AsyncMock()
        mock_history.find_similar_alerts.return_value = [
            {"alert_id": "old_1", "false_positive": True},
            {"alert_id": "old_2", "false_positive": True},
            {"alert_id": "old_3", "false_positive": False},
        ]
        sentinel_agent.history = mock_history
        
        triage_response = {
            "escalate": False,
            "reasoning": "67% false positive rate historically",
            "confidence": 0.8,
        }
        
        mock_response = AsyncMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps(triage_response)))
        ]
        mock_llm_client.chat.completions.create.return_value = mock_response
        
        should_escalate = await sentinel_agent.triage_alert(alert)
        
        assert should_escalate is False
        mock_history.find_similar_alerts.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_llm_json_decode_error(self, sentinel_agent, mock_llm_client):
        """Test handling of invalid JSON from LLM."""
        # Mock LLM returning invalid JSON
        mock_response = AsyncMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="not valid json"))
        ]
        mock_llm_client.chat.completions.create.return_value = mock_response
        
        with pytest.raises(SentinelAnalysisError, match="Invalid JSON from LLM"):
            await sentinel_agent._query_llm("test prompt")

    def test_parse_attacker_profile_invalid_data(self, sentinel_agent):
        """Test parsing invalid attacker profile data."""
        invalid_response = {
            "skill_level": "advanced",
            "tools_detected": ["tool1"],
            "ttps": [
                {
                    "technique_id": "T1110",
                    "tactic": "Credential Access",
                    "technique_name": "Brute Force",
                    "confidence": "invalid",  # Should be float
                }
            ],
            "objectives": [],
            "next_move_prediction": "",
            "confidence": 0.8,
        }
        
        with pytest.raises(SentinelAnalysisError):
            sentinel_agent._parse_attacker_profile("192.168.1.1", invalid_response)


@pytest.mark.integration
class TestSentinelIntegration:
    """Integration tests (require actual LLM API)."""

    @pytest.mark.skip(reason="Requires actual OpenAI API key")
    @pytest.mark.asyncio
    async def test_real_llm_analysis(self):
        """Test with real LLM (manual test only)."""
        from openai import AsyncOpenAI
        
        llm = AsyncOpenAI()  # Requires OPENAI_API_KEY env var
        sentinel = SentinelDetectionAgent(llm_client=llm)
        
        event = SecurityEvent(
            event_id="evt_real_001",
            timestamp=datetime.utcnow(),
            source="firewall",
            event_type="failed_login",
            source_ip="192.168.1.100",
            destination_ip="10.0.0.5",
            port=22,
            payload={"attempts": 50},
        )
        
        result = await sentinel.analyze_event(event)
        
        assert isinstance(result, DetectionResult)
        assert result.event_id == "evt_real_001"
        # Actual assertions depend on LLM response
