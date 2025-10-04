"""
Unit Tests: Advanced AI Features
=================================

Tests for Phase 2.2 Advanced AI capabilities:
- Chain-of-Thought Reasoning
- Self-Reflection & Improvement
- Multi-Agent Orchestration
- Tool Learning & Adaptation
- Explainable AI (XAI)
"""

import pytest
from datetime import datetime

from vertice.ai import (
    # Chain-of-Thought
    CoTReasoner,
    ReasoningStrategy,
    ReasoningResult,
    StepType,
    # Self-Reflection
    SelfReflector,
    OutcomeType,
    ReflectionType,
    # Multi-Agent
    MultiAgentOrchestrator,
    AgentRole,
    TaskPriority,
    TaskStatus,
    # Tool Learning
    ToolLearner,
    ToolCategory,
    # Explainability
    ExplainableAI,
    DecisionType,
)


# ========================================
# Test Chain-of-Thought Reasoning
# ========================================


class TestCoTReasoner:
    """Test Chain-of-Thought reasoning engine."""

    @pytest.fixture
    def reasoner(self):
        return CoTReasoner(min_confidence=0.5, max_steps=20)

    def test_create_reasoner(self, reasoner):
        """Test reasoner initialization."""
        assert reasoner.min_confidence == 0.5
        assert reasoner.max_steps == 20

    def test_security_investigation_reasoning(self, reasoner):
        """Test security investigation strategy."""
        result = reasoner.reason(
            problem="Investigate suspicious lateral movement from 10.0.0.5",
            context={"source_ip": "10.0.0.5", "dest_ips": ["10.0.0.10", "10.0.0.11"]},
            strategy=ReasoningStrategy.SECURITY_INVESTIGATION
        )

        assert isinstance(result, ReasoningResult)
        assert result.problem == "Investigate suspicious lateral movement from 10.0.0.5"
        assert len(result.reasoning_trace) > 0
        assert 0.0 <= result.confidence <= 1.0

    def test_reasoning_trace_has_steps(self, reasoner):
        """Test reasoning produces step-by-step trace."""
        result = reasoner.reason(
            problem="Analyze attack pattern",
            context={"iocs": [1, 2, 3]},
            strategy=ReasoningStrategy.THREAT_HUNTING
        )

        assert len(result.reasoning_trace) >= 3
        assert any(step.step_type == StepType.OBSERVATION for step in result.reasoning_trace)
        assert any(step.step_type == StepType.CONCLUSION for step in result.reasoning_trace)

    def test_explain_reasoning(self, reasoner):
        """Test reasoning explanation generation."""
        result = reasoner.reason(
            problem="Test problem",
            context={},
            strategy=ReasoningStrategy.GENERAL
        )

        explanation = reasoner.explain_reasoning(result)
        assert isinstance(explanation, str)
        assert "Problem:" in explanation
        assert "Conclusion:" in explanation


# ========================================
# Test Self-Reflection
# ========================================


class TestSelfReflector:
    """Test self-reflection and improvement system."""

    @pytest.fixture
    def reflector(self):
        return SelfReflector(reflection_window_days=30)

    def test_record_successful_action(self, reflector):
        """Test recording successful action."""
        record = reflector.record_action(
            action="Blocked IP address",
            context={"ip": "1.2.3.4", "reason": "bruteforce"},
            expected_outcome="Attack stopped",
            actual_outcome="Attack stopped successfully",
            outcome_type=OutcomeType.SUCCESS,
            confidence=0.9
        )

        assert record.action == "Blocked IP address"
        assert record.outcome_type == OutcomeType.SUCCESS
        assert record.confidence == 0.9

    def test_record_failure_triggers_reflection(self, reflector):
        """Test failure automatically triggers reflection."""
        record = reflector.record_action(
            action="Classified alert as false positive",
            context={"alert_id": 123},
            expected_outcome="No incident",
            actual_outcome="Was actually real attack",
            outcome_type=OutcomeType.FALSE_POSITIVE
        )

        assert len(reflector._reflection_history) > 0
        reflection = reflector._reflection_history[0]
        assert reflection.what_went_wrong is not None
        assert len(reflection.improvement_suggestions) > 0

    def test_pattern_recognition(self, reflector):
        """Test recurring error pattern detection."""
        # Record same failure multiple times
        for i in range(5):
            reflector.record_action(
                action="Scan with nmap",
                context={"target": f"10.0.0.{i}"},
                expected_outcome="Success",
                actual_outcome="Timeout",
                outcome_type=OutcomeType.FAILURE
            )

        patterns = reflector.get_error_patterns(min_occurrences=3)
        assert len(patterns) > 0

    def test_get_improvements(self, reflector):
        """Test improvement suggestions retrieval."""
        reflector.record_action(
            action="Test action",
            context={},
            expected_outcome="A",
            actual_outcome="B",
            outcome_type=OutcomeType.FAILURE
        )

        improvements = reflector.get_improvements(min_priority=0.0)
        assert isinstance(improvements, list)


# ========================================
# Test Multi-Agent Orchestration
# ========================================


class TestMultiAgentOrchestrator:
    """Test multi-agent orchestration system."""

    @pytest.fixture
    def orchestrator(self):
        return MultiAgentOrchestrator()

    def test_register_agent(self, orchestrator):
        """Test agent registration."""
        agent = orchestrator.register_agent(
            agent_id="hunter1",
            role=AgentRole.HUNTER,
            specialization="Threat hunting",
            capabilities=["hunt_threats", "analyze_iocs"]
        )

        assert agent.agent_id == "hunter1"
        assert agent.role == AgentRole.HUNTER
        assert len(agent.capabilities) == 2

    def test_create_task(self, orchestrator):
        """Test task creation."""
        task = orchestrator.create_task(
            description="Analyze suspicious process",
            required_capabilities=["process_analysis"],
            context={"process_id": 1234},
            priority=TaskPriority.HIGH
        )

        assert task.description == "Analyze suspicious process"
        assert task.priority == TaskPriority.HIGH
        assert task.status == TaskStatus.PENDING

    def test_assign_task_to_capable_agent(self, orchestrator):
        """Test task assignment to agent with required capabilities."""
        orchestrator.register_agent(
            agent_id="analyst1",
            role=AgentRole.ANALYST,
            specialization="Log analysis",
            capabilities=["log_analysis", "correlation"]
        )

        task = orchestrator.create_task(
            description="Analyze logs",
            required_capabilities=["log_analysis"],
            context={}
        )

        agent = orchestrator.assign_task(task)
        assert agent is not None
        assert agent.agent_id == "analyst1"
        assert task.status == TaskStatus.ASSIGNED

    def test_collaborative_task_execution(self, orchestrator):
        """Test multi-agent collaboration."""
        # Register multiple agents
        orchestrator.register_agent(
            agent_id="hunter1",
            role=AgentRole.HUNTER,
            specialization="Hunting",
            capabilities=["hunt_execution", "hypothesis_generation"]
        )

        orchestrator.register_agent(
            agent_id="analyst1",
            role=AgentRole.ANALYST,
            specialization="Analysis",
            capabilities=["log_analysis", "timeline_analysis"]
        )

        result = orchestrator.execute_collaborative_task(
            task="Investigate APT campaign",
            context={"iocs": [1, 2, 3]},
            num_agents=2
        )

        assert len(result.agent_contributions) > 0
        assert 0.0 <= result.consensus_score <= 1.0
        assert result.execution_time_seconds >= 0


# ========================================
# Test Tool Learning
# ========================================


class TestToolLearner:
    """Test tool learning and adaptation."""

    @pytest.fixture
    def learner(self):
        return ToolLearner(learning_window_days=90)

    def test_record_tool_usage(self, learner):
        """Test recording tool usage."""
        usage = learner.record_tool_usage(
            tool="nmap",
            category=ToolCategory.SCANNER,
            context={"target_type": "web_server"},
            outcome="success",
            effectiveness=0.95,
            execution_time_seconds=10.5
        )

        assert usage.tool_name == "nmap"
        assert usage.effectiveness == 0.95
        assert usage.outcome == "success"

    def test_recommend_tool(self, learner):
        """Test tool recommendation."""
        # Record some usages
        for i in range(5):
            learner.record_tool_usage(
                tool="nmap",
                category=ToolCategory.SCANNER,
                context={"target": "network"},
                outcome="success",
                effectiveness=0.9
            )

        recommendation = learner.recommend_tool(
            task="scan network",
            context={"target": "network"}
        )

        assert recommendation.tool_name == "nmap"
        assert recommendation.confidence > 0.0

    def test_tool_performance_profile(self, learner):
        """Test tool performance profiling."""
        # Record multiple usages
        for i in range(10):
            learner.record_tool_usage(
                tool="metasploit",
                category=ToolCategory.EXPLOITER,
                context={},
                outcome="success" if i < 8 else "failure",
                effectiveness=0.9 if i < 8 else 0.2
            )

        profile = learner.get_tool_profile("metasploit")

        assert profile.tool_name == "metasploit"
        assert profile.total_uses == 10
        assert 0.7 <= profile.success_rate <= 0.9
        assert profile.avg_effectiveness > 0.5


# ========================================
# Test Explainable AI
# ========================================


class TestExplainableAI:
    """Test explainability and transparency."""

    @pytest.fixture
    def xai(self):
        return ExplainableAI(enable_counterfactuals=True)

    def test_explain_decision(self, xai):
        """Test decision explanation generation."""
        explanation = xai.explain_decision(
            decision="Block IP 1.2.3.4",
            decision_type=DecisionType.CLASSIFICATION,
            factors={
                "threat_score": 95,
                "geo_location": "suspicious",
                "failed_logins": 100
            },
            confidence=0.92
        )

        assert explanation.decision == "Block IP 1.2.3.4"
        assert explanation.confidence == 0.92
        assert len(explanation.confidence_factors) == 3
        assert len(explanation.feature_importance) == 3

    def test_natural_language_explanation(self, xai):
        """Test human-readable explanation generation."""
        explanation = xai.explain_decision(
            decision="Escalate alert",
            decision_type=DecisionType.RECOMMENDATION,
            factors={"severity": "high", "asset_value": "critical"},
            confidence=0.85
        )

        nl_explanation = explanation.natural_language()
        assert "Decision:" in nl_explanation
        assert "Confidence:" in nl_explanation
        assert "Key Factors:" in nl_explanation

    def test_counterfactual_generation(self, xai):
        """Test what-if scenario generation."""
        explanation = xai.explain_decision(
            decision="Block",
            decision_type=DecisionType.CLASSIFICATION,
            factors={"threat_detected": True, "severity_score": 85},
            confidence=0.9
        )

        assert len(explanation.counterfactuals) > 0
        cf = explanation.counterfactuals[0]
        assert "change" in cf
        assert "result" in cf

    def test_feature_importance_ranking(self, xai):
        """Test feature importance calculation."""
        explanation = xai.explain_decision(
            decision="Alert",
            decision_type=DecisionType.DETECTION,
            factors={
                "factor_a": 10,
                "factor_b": 90,
                "factor_c": 50
            },
            confidence=0.8
        )

        assert len(explanation.feature_importance) == 3
        assert all(0.0 <= importance <= 1.0 for importance in explanation.feature_importance.values())

    def test_compare_decisions(self, xai):
        """Test decision comparison."""
        exp1 = xai.explain_decision(
            decision="Allow",
            decision_type=DecisionType.CLASSIFICATION,
            factors={"risk": 20},
            confidence=0.6
        )

        exp2 = xai.explain_decision(
            decision="Block",
            decision_type=DecisionType.CLASSIFICATION,
            factors={"risk": 90},
            confidence=0.95
        )

        comparison = xai.compare_decisions(exp1, exp2)

        assert comparison["decision1"] == "Allow"
        assert comparison["decision2"] == "Block"
        assert comparison["confidence_delta"] > 0


# ========================================
# Integration Tests
# ========================================


class TestAdvancedAIIntegration:
    """Integration tests combining multiple AI features."""

    def test_reasoning_with_reflection(self):
        """Test combining CoT reasoning with self-reflection."""
        reasoner = CoTReasoner()
        reflector = SelfReflector()

        # Perform reasoning
        result = reasoner.reason(
            problem="Investigate alert",
            context={"alert_id": 123},
            strategy=ReasoningStrategy.SECURITY_INVESTIGATION
        )

        # Reflect on reasoning outcome
        reflector.record_action(
            action=f"Reasoning: {result.problem}",
            context={"steps": len(result.reasoning_trace)},
            expected_outcome="High confidence conclusion",
            actual_outcome=f"Confidence {result.confidence:.0%}",
            outcome_type=OutcomeType.SUCCESS if result.confidence > 0.7 else OutcomeType.SUBOPTIMAL
        )

        stats = reflector.get_stats()
        assert stats["total_actions"] == 1

    def test_tool_learning_with_explainability(self):
        """Test combining tool learning with XAI."""
        learner = ToolLearner()
        xai = ExplainableAI()

        # Record tool usage
        learner.record_tool_usage(
            tool="nmap",
            category=ToolCategory.SCANNER,
            context={"network": "internal"},
            outcome="success",
            effectiveness=0.9
        )

        # Get recommendation
        rec = learner.recommend_tool(
            task="scan network",
            context={"network": "internal"}
        )

        # Explain recommendation
        explanation = xai.explain_decision(
            decision=f"Recommend {rec.tool_name}",
            decision_type=DecisionType.RECOMMENDATION,
            factors={"confidence": rec.confidence, "effectiveness": rec.estimated_effectiveness},
            confidence=rec.confidence
        )

        assert explanation.decision == f"Recommend {rec.tool_name}"
        assert explanation.confidence > 0.0
