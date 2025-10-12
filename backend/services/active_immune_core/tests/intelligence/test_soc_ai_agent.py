"""Tests for SOC AI Agent - Theory of Mind for Attackers

Tests adversarial intent modeling and next-step prediction capabilities.

Authors: MAXIMUS Team
Date: 2025-10-12
"""

import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from active_immune_core.intelligence.soc_ai_agent import (
    AttackIntent,
    NextStepPrediction,
    SOCAIAgent,
    SOCAIAgentError,
    SecurityEvent,
    ThreatAssessment,
)


@pytest.fixture
def mock_llm_client():
    """Mock OpenAI client."""
    client = AsyncMock()
    return client


@pytest.fixture
def soc_agent(mock_llm_client):
    """Create SOC AI Agent instance."""
    return SOCAIAgent(llm_client=mock_llm_client)


@pytest.fixture
def sample_security_events():
    """Create sample security events."""
    return [
        SecurityEvent(
            event_id="evt_001",
            timestamp=datetime.utcnow(),
            source_system="IDS",
            event_type="network_scan",
            severity="MEDIUM",
            raw_data={
                "description": "Port scan detected from 192.168.1.100",
                "ports_scanned": [22, 80, 443, 3389],
            },
        ),
        SecurityEvent(
            event_id="evt_002",
            timestamp=datetime.utcnow() + timedelta(minutes=5),
            source_system="EDR",
            event_type="suspicious_process",
            severity="HIGH",
            raw_data={
                "description": "Mimikatz execution detected",
                "process": "mimikatz.exe",
            },
        ),
        SecurityEvent(
            event_id="evt_003",
            timestamp=datetime.utcnow() + timedelta(minutes=10),
            source_system="Firewall",
            event_type="outbound_connection",
            severity="HIGH",
            raw_data={
                "description": "Large data transfer to external IP",
                "bytes_transferred": 500_000_000,
                "destination": "203.0.113.42",
            },
        ),
    ]


class TestSOCAIAgent:
    """Test SOC AI Agent functionality."""
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, mock_llm_client):
        """Test agent initializes correctly."""
        agent = SOCAIAgent(llm_client=mock_llm_client)
        
        assert agent.llm == mock_llm_client
        assert agent.model == "gpt-4o"
        assert agent.attack_graph is not None
        assert len(agent.active_threats) == 0
    
    @pytest.mark.asyncio
    async def test_analyze_threat_success(
        self,
        soc_agent,
        sample_security_events,
        mock_llm_client,
    ):
        """Test successful threat analysis."""
        # Mock LLM responses
        mock_llm_client.chat.completions.create = AsyncMock(
            side_effect=[
                # TTP identification
                MagicMock(
                    choices=[
                        MagicMock(
                            message=MagicMock(
                                content=json.dumps({
                                    "technique_id": "T1078",
                                    "technique_name": "Valid Accounts",
                                    "confidence": 0.85,
                                    "reasoning": "Multiple failed login attempts",
                                })
                            )
                        )
                    ]
                ),
                # Intent inference
                MagicMock(
                    choices=[
                        MagicMock(
                            message=MagicMock(
                                content=json.dumps({
                                    "intent": "credential_access",
                                    "confidence": 0.8,
                                    "reasoning": "Mimikatz execution indicates credential theft",
                                })
                            )
                        )
                    ]
                ),
                # Next steps prediction
                MagicMock(
                    choices=[
                        MagicMock(
                            message=MagicMock(
                                content=json.dumps({
                                    "predictions": [
                                        {
                                            "technique_id": "T1021",
                                            "technique_name": "Remote Services",
                                            "probability": 0.75,
                                            "required_conditions": ["Valid credentials"],
                                            "indicators": ["RDP connections"],
                                            "recommended_actions": ["Monitor RDP"],
                                        }
                                    ]
                                })
                            )
                        )
                    ]
                ),
                # Explanation generation
                MagicMock(
                    choices=[
                        MagicMock(
                            message=MagicMock(
                                content="The attacker is attempting to steal credentials using Mimikatz."
                            )
                        )
                    ]
                ),
            ]
        )
        
        # Execute analysis
        assessment = await soc_agent.analyze_threat(
            raw_events=sample_security_events,
            threat_id="threat_test_001",
        )
        
        # Assertions
        assert isinstance(assessment, ThreatAssessment)
        assert assessment.threat_id == "threat_test_001"
        assert assessment.current_ttp == "T1078"
        assert assessment.inferred_intent == AttackIntent.CREDENTIAL_ACCESS
        assert len(assessment.next_steps) > 0
        assert 0.0 <= assessment.confidence <= 1.0
        assert 0.0 <= assessment.risk_score <= 100.0
        assert assessment.events_analyzed == 3
        assert len(assessment.recommended_response) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_threat_auto_generate_id(
        self,
        soc_agent,
        sample_security_events,
        mock_llm_client,
    ):
        """Test threat ID is auto-generated if not provided."""
        # Mock LLM responses (minimal)
        mock_llm_client.chat.completions.create = AsyncMock(
            return_value=MagicMock(
                choices=[
                    MagicMock(
                        message=MagicMock(
                            content=json.dumps({
                                "technique_id": "T0000",
                                "confidence": 0.5,
                            })
                        )
                    )
                ]
            )
        )
        
        # Execute without threat_id
        assessment = await soc_agent.analyze_threat(
            raw_events=sample_security_events
        )
        
        # Assertions
        assert assessment.threat_id.startswith("threat_")
        assert len(assessment.threat_id) > 7  # threat_ + hash
    
    @pytest.mark.asyncio
    async def test_identify_current_ttp(self, soc_agent, sample_security_events):
        """Test TTP identification from events."""
        # Mock LLM response
        soc_agent.llm.chat.completions.create = AsyncMock(
            return_value=MagicMock(
                choices=[
                    MagicMock(
                        message=MagicMock(
                            content=json.dumps({
                                "technique_id": "T1595",
                                "technique_name": "Active Scanning",
                                "confidence": 0.9,
                                "reasoning": "Port scan detected",
                            })
                        )
                    )
                ]
            )
        )
        
        ttp, confidence = await soc_agent._identify_current_ttp(
            sample_security_events
        )
        
        assert ttp == "T1595"
        assert 0.0 <= confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_infer_intent(self, soc_agent, sample_security_events):
        """Test intent inference."""
        # Mock LLM response
        soc_agent.llm.chat.completions.create = AsyncMock(
            return_value=MagicMock(
                choices=[
                    MagicMock(
                        message=MagicMock(
                            content=json.dumps({
                                "intent": "exfiltration",
                                "confidence": 0.85,
                                "reasoning": "Large outbound data transfer",
                            })
                        )
                    )
                ]
            )
        )
        
        intent, confidence = await soc_agent._infer_intent(
            events=sample_security_events,
            current_ttp="T1041",
        )
        
        assert intent == AttackIntent.EXFILTRATION
        assert 0.0 <= confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_predict_next_steps(self, soc_agent, sample_security_events):
        """Test next step prediction."""
        # Mock LLM response
        soc_agent.llm.chat.completions.create = AsyncMock(
            return_value=MagicMock(
                choices=[
                    MagicMock(
                        message=MagicMock(
                            content=json.dumps({
                                "predictions": [
                                    {
                                        "technique_id": "T1087",
                                        "technique_name": "Account Discovery",
                                        "probability": 0.8,
                                        "required_conditions": ["Access to domain"],
                                        "indicators": ["LDAP queries"],
                                        "recommended_actions": ["Monitor LDAP"],
                                    },
                                    {
                                        "technique_id": "T1083",
                                        "technique_name": "File Discovery",
                                        "probability": 0.7,
                                        "required_conditions": ["File system access"],
                                        "indicators": ["Directory enumeration"],
                                        "recommended_actions": ["Monitor file access"],
                                    },
                                ]
                            })
                        )
                    )
                ]
            )
        )
        
        next_steps = await soc_agent._predict_next_steps(
            current_ttp="T1078",
            inferred_intent=AttackIntent.CREDENTIAL_ACCESS,
            context=sample_security_events,
        )
        
        assert len(next_steps) == 2
        assert all(isinstance(step, NextStepPrediction) for step in next_steps)
        assert all(0.0 <= step.probability <= 1.0 for step in next_steps)
    
    def test_build_attack_graph_viz(self, soc_agent):
        """Test attack graph visualization generation."""
        next_steps = [
            NextStepPrediction(
                technique_id="T1021",
                technique_name="Remote Services",
                probability=0.75,
                required_conditions=[],
                indicators=[],
                recommended_actions=[],
            ),
            NextStepPrediction(
                technique_id="T1083",
                technique_name="File Discovery",
                probability=0.6,
                required_conditions=[],
                indicators=[],
                recommended_actions=[],
            ),
        ]
        
        graph = soc_agent._build_attack_graph_viz(
            current_ttp="T1078",
            next_steps=next_steps,
        )
        
        assert "nodes" in graph
        assert "edges" in graph
        assert "metadata" in graph
        assert len(graph["nodes"]) == 3  # 1 current + 2 predicted
        assert len(graph["edges"]) == 2
    
    @pytest.mark.asyncio
    async def test_generate_explanation(self, soc_agent, sample_security_events):
        """Test explanation generation."""
        # Mock LLM response
        soc_agent.llm.chat.completions.create = AsyncMock(
            return_value=MagicMock(
                choices=[
                    MagicMock(
                        message=MagicMock(
                            content="The attacker performed network reconnaissance."
                        )
                    )
                ]
            )
        )
        
        explanation = await soc_agent._generate_explanation(
            events=sample_security_events,
            current_ttp="T1595",
            inferred_intent=AttackIntent.RECONNAISSANCE,
            next_steps=[],
        )
        
        assert len(explanation) > 0
        assert "attacker" in explanation.lower()
    
    def test_recommend_defensive_actions(self, soc_agent):
        """Test defensive action recommendations."""
        next_steps = [
            NextStepPrediction(
                technique_id="T1021",
                technique_name="Remote Services",
                probability=0.75,
                required_conditions=[],
                indicators=[],
                recommended_actions=["Block RDP", "Enable MFA"],
            ),
        ]
        
        actions = soc_agent._recommend_defensive_actions(
            inferred_intent=AttackIntent.LATERAL_MOVEMENT,
            next_steps=next_steps,
        )
        
        assert len(actions) > 0
        assert all(isinstance(action, str) for action in actions)
        assert len(actions) <= 10  # Max 10 actions
    
    def test_calculate_risk_score(self, soc_agent):
        """Test risk score calculation."""
        # High-risk intent with high confidence
        risk_high = soc_agent._calculate_risk_score(
            inferred_intent=AttackIntent.EXFILTRATION,
            confidence=0.9,
            events_count=10,
        )
        
        # Low-risk intent with low confidence
        risk_low = soc_agent._calculate_risk_score(
            inferred_intent=AttackIntent.RECONNAISSANCE,
            confidence=0.3,
            events_count=2,
        )
        
        assert 0.0 <= risk_high <= 100.0
        assert 0.0 <= risk_low <= 100.0
        assert risk_high > risk_low  # High-risk should be higher
    
    def test_threat_assessment_to_dict(self):
        """Test ThreatAssessment serialization."""
        assessment = ThreatAssessment(
            assessment_id="assess_001",
            threat_id="threat_001",
            created_at=datetime.utcnow(),
            current_ttp="T1078",
            inferred_intent=AttackIntent.CREDENTIAL_ACCESS,
            next_steps=[],
            confidence=0.85,
            explanation="Test explanation",
            attack_graph={},
            recommended_response=["action1", "action2"],
            events_analyzed=5,
            risk_score=75.0,
        )
        
        data = assessment.to_dict()
        
        assert data["assessment_id"] == "assess_001"
        assert data["threat_id"] == "threat_001"
        assert data["current_ttp"] == "T1078"
        assert data["inferred_intent"] == "credential_access"
        assert data["confidence"] == 0.85
        assert data["risk_score"] == 75.0
    
    def test_security_event_to_dict(self):
        """Test SecurityEvent serialization."""
        event = SecurityEvent(
            event_id="evt_001",
            timestamp=datetime.utcnow(),
            source_system="IDS",
            event_type="network_scan",
            severity="HIGH",
            raw_data={"test": "data"},
        )
        
        data = event.to_dict()
        
        assert data["event_id"] == "evt_001"
        assert data["source_system"] == "IDS"
        assert data["event_type"] == "network_scan"
        assert data["severity"] == "HIGH"
    
    @pytest.mark.asyncio
    async def test_analyze_threat_handles_llm_failure(
        self,
        soc_agent,
        sample_security_events,
    ):
        """Test graceful handling of LLM failures (degraded mode)."""
        # Mock LLM to raise exception
        soc_agent.llm.chat.completions.create = AsyncMock(
            side_effect=Exception("LLM API error")
        )
        
        # Should complete with degraded/default values (resilient)
        assessment = await soc_agent.analyze_threat(
            raw_events=sample_security_events,
            threat_id="threat_fail",
        )
        
        # Assertions - should get default/low-confidence assessment
        assert assessment.threat_id == "threat_fail"
        assert assessment.current_ttp == "T0000"  # Default unknown
        assert assessment.inferred_intent == AttackIntent.UNKNOWN
        assert assessment.confidence < 0.5  # Low confidence
        assert len(assessment.next_steps) == 0  # No predictions
    
    def test_metrics_tracking(self, soc_agent):
        """Test metrics are tracked correctly."""
        metrics = soc_agent.metrics
        
        assert metrics.assessments_created is not None
        assert metrics.assessment_duration is not None
        assert metrics.confidence_score is not None
        assert metrics.intent_predictions is not None
        assert metrics.active_threats is not None


class TestNextStepPrediction:
    """Test NextStepPrediction model."""
    
    def test_valid_prediction(self):
        """Test valid prediction creation."""
        pred = NextStepPrediction(
            technique_id="T1021",
            technique_name="Remote Services",
            probability=0.75,
            required_conditions=["Credentials"],
            indicators=["RDP traffic"],
            recommended_actions=["Monitor RDP"],
        )
        
        assert pred.technique_id == "T1021"
        assert pred.probability == 0.75
        assert len(pred.required_conditions) == 1
    
    def test_invalid_probability(self):
        """Test invalid probability raises error."""
        with pytest.raises(ValueError):
            NextStepPrediction(
                technique_id="T1021",
                technique_name="Test",
                probability=1.5,  # Invalid > 1.0
            )


class TestAttackIntent:
    """Test AttackIntent enum."""
    
    def test_intent_values(self):
        """Test all intent values are valid."""
        assert AttackIntent.RECONNAISSANCE.value == "reconnaissance"
        assert AttackIntent.EXFILTRATION.value == "exfiltration"
        assert AttackIntent.IMPACT.value == "impact"
        assert AttackIntent.UNKNOWN.value == "unknown"
    
    def test_intent_from_string(self):
        """Test creating intent from string."""
        intent = AttackIntent("credential_access")
        assert intent == AttackIntent.CREDENTIAL_ACCESS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
