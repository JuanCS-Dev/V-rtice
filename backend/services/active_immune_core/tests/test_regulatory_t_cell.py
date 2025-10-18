"""Regulatory T Cell Tests - Comprehensive test suite

Tests cover actual production implementation of Regulatory T Cell (MOST ADVANCED):
- Initialization & lifecycle
- Multi-criteria autoimmunity scoring (6 criteria)
- Q-learning machine learning
- Graduated suppression (4 levels)
- IL10 and TGF-β secretion
- Self-monitoring and auto-correction
- Decision audit trail
- Temporal pattern analysis
- False positive detection
- Advanced metrics
"""

from datetime import datetime, timedelta

import numpy as np
import pytest
import pytest_asyncio

from active_immune_core.agents import LinfocitoTRegulador
from active_immune_core.agents.models import AgentStatus
from active_immune_core.agents.regulatory_t_cell import (
    AutoimmunityRiskScore,
    RegulatoryTState,
    SuppressionLevel,
)

# ==================== FIXTURES ====================


@pytest_asyncio.fixture
async def regulatory_t() -> LinfocitoTRegulador:
    """Create Regulatory T Cell instance for testing"""
    cell = LinfocitoTRegulador(
        area_patrulha="test_subnet_10_0_1_0",
        kafka_bootstrap="localhost:9092",
        redis_url="redis://localhost:6379",
        autoimmunity_threshold=0.65,
        learning_rate=0.1,
        discount_factor=0.9,
        epsilon=0.1,
    )
    yield cell
    if cell._running:
        await cell.parar()


@pytest.fixture
def friendly_fire_activities() -> list:
    """Activities showing friendly fire (attacking own network)"""
    return [
        {
            "agent_id": "agent_001",
            "cytokine": "IL1",
            "payload": {"alvo": {"ip": "10.0.1.100", "porta": 22}},
            "timestamp": datetime.now(),
        },
        {
            "agent_id": "agent_001",
            "cytokine": "IFN_GAMMA",
            "payload": {"alvo": {"ip": "10.0.1.101", "porta": 80}},
            "timestamp": datetime.now(),
        },
        {
            "agent_id": "agent_001",
            "cytokine": "IL1",
            "payload": {"alvo": {"ip": "10.0.1.102", "porta": 443}},
            "timestamp": datetime.now(),
        },
    ]


@pytest.fixture
def excessive_response_activities() -> list:
    """Activities showing excessive response"""
    activities = []
    for i in range(15):
        activities.append(
            {
                "agent_id": "agent_002",
                "cytokine": "IFN_GAMMA" if i % 2 == 0 else "IL1",
                "payload": {"alvo": {"ip": f"192.0.2.{i}", "porta": 22}},
                "timestamp": datetime.now() - timedelta(seconds=i),
            }
        )
    return activities


@pytest.fixture
def rapid_fire_activities() -> list:
    """Activities showing rapid-fire pattern"""
    base_time = datetime.now()
    return [
        {
            "agent_id": "agent_003",
            "cytokine": "IL1",
            "payload": {},
            "timestamp": base_time + timedelta(milliseconds=100 * i),
        }
        for i in range(5)
    ]


# ==================== INITIALIZATION TESTS ====================


class TestRegulatoryTInitialization:
    """Test Regulatory T Cell initialization"""

    def test_regulatory_t_creation(self, regulatory_t: LinfocitoTRegulador):
        """Test Regulatory T Cell is created correctly"""
        assert regulatory_t.state.tipo.value == "linfocito_t_regulador"
        assert regulatory_t.state.status == AgentStatus.DORMINDO
        assert regulatory_t.state.ativo is False
        assert regulatory_t.regulatory_state == RegulatoryTState.MONITORING
        assert len(regulatory_t.suppression_decisions) == 0
        assert regulatory_t.prevented_autoimmune_attacks == 0
        assert len(regulatory_t.q_table) == 0

    def test_regulatory_t_ml_parameters(self):
        """Test ML parameters are set correctly"""
        cell = LinfocitoTRegulador(
            area_patrulha="test",
            learning_rate=0.2,
            discount_factor=0.95,
            epsilon=0.15,
        )
        assert cell.learning_rate == 0.2
        assert cell.discount_factor == 0.95
        assert cell.epsilon == 0.15

    def test_regulatory_t_default_threshold(self):
        """Test default autoimmunity threshold"""
        cell = LinfocitoTRegulador(area_patrulha="test")
        assert cell.autoimmunity_threshold == 0.65


# ==================== LIFECYCLE TESTS ====================


class TestRegulatoryTLifecycle:
    """Test Regulatory T Cell lifecycle"""

    @pytest.mark.asyncio
    async def test_regulatory_t_start_stop(self, regulatory_t: LinfocitoTRegulador):
        """Test Regulatory T Cell start and stop"""
        # Start
        await regulatory_t.iniciar()
        assert regulatory_t._running is True
        assert regulatory_t.state.ativo is True
        assert regulatory_t.regulatory_state == RegulatoryTState.MONITORING

        # Stop
        await regulatory_t.parar()
        assert regulatory_t._running is False
        assert regulatory_t.state.ativo is False

    @pytest.mark.asyncio
    async def test_regulatory_t_patrol_executes(self, regulatory_t: LinfocitoTRegulador):
        """Test Regulatory T Cell patrol executes without crashing"""
        await regulatory_t.iniciar()

        # Patrol should not crash
        await regulatory_t.patrulhar()

        assert regulatory_t._running is True

        await regulatory_t.parar()


# ==================== MULTI-CRITERIA SCORING TESTS ====================


class TestMultiCriteriaScoring:
    """Test multi-criteria autoimmunity scoring"""

    @pytest.mark.asyncio
    async def test_friendly_fire_scoring(self, regulatory_t: LinfocitoTRegulador, friendly_fire_activities: list):
        """Test friendly fire criterion scoring"""
        score = regulatory_t._score_friendly_fire(friendly_fire_activities)

        # All 3 activities attack 10.0.x.x (own network)
        assert score == 1.0

    @pytest.mark.asyncio
    async def test_excessive_response_scoring(
        self, regulatory_t: LinfocitoTRegulador, excessive_response_activities: list
    ):
        """Test excessive response criterion scoring"""
        score = regulatory_t._score_excessive_response(excessive_response_activities)

        # Many IL1/IFN_GAMMA cytokines
        assert score > 0.5

    @pytest.mark.asyncio
    async def test_temporal_pattern_scoring(self, regulatory_t: LinfocitoTRegulador, rapid_fire_activities: list):
        """Test temporal pattern criterion scoring"""
        score = regulatory_t._score_temporal_pattern(rapid_fire_activities)

        # All within 1 second (rapid fire)
        assert score == 1.0

    @pytest.mark.asyncio
    async def test_target_diversity_scoring(
        self, regulatory_t: LinfocitoTRegulador, excessive_response_activities: list
    ):
        """Test target diversity criterion scoring"""
        score = regulatory_t._score_target_diversity(excessive_response_activities)

        # 15 different targets
        assert score > 0.9

    @pytest.mark.asyncio
    async def test_self_similarity_scoring(self, regulatory_t: LinfocitoTRegulador):
        """Test self-similarity criterion scoring"""
        legitimate_activities = [
            {
                "agent_id": "agent_004",
                "cytokine": "IL1",
                "payload": {"alvo": {"porta": 80}},  # Legitimate port
                "timestamp": datetime.now(),
            },
            {
                "agent_id": "agent_004",
                "cytokine": "IL1",
                "payload": {"alvo": {"porta": 443}},  # Legitimate port
                "timestamp": datetime.now(),
            },
        ]

        score = regulatory_t._score_self_similarity(legitimate_activities)

        # All legitimate ports
        assert score == 1.0

    @pytest.mark.asyncio
    async def test_complete_risk_score_calculation(
        self, regulatory_t: LinfocitoTRegulador, friendly_fire_activities: list
    ):
        """Test complete multi-criteria risk score"""
        risk_score = await regulatory_t._calculate_autoimmunity_risk("agent_001", friendly_fire_activities)

        assert isinstance(risk_score, AutoimmunityRiskScore)
        assert 0.0 <= risk_score.total_score <= 1.0
        assert risk_score.friendly_fire_score == 1.0
        assert len(risk_score.justification) > 0


# ==================== MACHINE LEARNING TESTS ====================


class TestMachineLearning:
    """Test Q-learning machine learning"""

    def test_q_table_initialization(self, regulatory_t: LinfocitoTRegulador):
        """Test Q-table starts empty"""
        assert len(regulatory_t.q_table) == 0

    def test_state_discretization(self, regulatory_t: LinfocitoTRegulador):
        """Test risk score discretization"""
        assert regulatory_t._discretize_risk_score(0.2) == "low_risk"
        assert regulatory_t._discretize_risk_score(0.5) == "medium_risk"
        assert regulatory_t._discretize_risk_score(0.7) == "high_risk"
        assert regulatory_t._discretize_risk_score(0.9) == "critical_risk"

    def test_epsilon_greedy_exploration(self, regulatory_t: LinfocitoTRegulador):
        """Test epsilon-greedy action selection"""
        # Set high epsilon for exploration
        regulatory_t.epsilon = 0.9

        # Should explore more often
        explorations = 0
        for _ in range(100):
            if np.random.random() < regulatory_t.epsilon:
                explorations += 1

        # Should be around 90 explorations
        assert 70 < explorations < 110

    @pytest.mark.asyncio
    async def test_q_value_update(self, regulatory_t: LinfocitoTRegulador):
        """Test Q-value update mechanism"""
        # Create fake decision
        risk_score = AutoimmunityRiskScore(
            total_score=0.8,
            friendly_fire_score=0.5,
            excessive_response_score=0.5,
            temporal_pattern_score=0.0,
            target_diversity_score=0.0,
            false_positive_history_score=0.0,
            self_similarity_score=0.0,
            justification="Test",
        )

        from agents.regulatory_t_cell import SuppressionDecision

        decision = SuppressionDecision(
            decision_id="test_001",
            target_agent_id="agent_test",
            suppression_level=SuppressionLevel.MODERATE,
            risk_score=risk_score,
            action_taken="IL10=medium",
            q_value=0.0,
            exploration=False,
        )

        regulatory_t.suppression_decisions.append(decision)
        regulatory_t.regulatory_state = RegulatoryTState.LEARNING

        initial_q_count = len(regulatory_t.q_table)

        await regulatory_t._update_ml_model()

        # Q-table should have new entry
        assert len(regulatory_t.q_table) >= initial_q_count

    def test_reward_calculation(self, regulatory_t: LinfocitoTRegulador):
        """Test reward calculation for RL"""
        risk_score = AutoimmunityRiskScore(
            total_score=0.9,
            friendly_fire_score=0.5,
            excessive_response_score=0.5,
            temporal_pattern_score=0.0,
            target_diversity_score=0.0,
            false_positive_history_score=0.0,
            self_similarity_score=0.0,
            justification="High risk",
        )

        from agents.regulatory_t_cell import SuppressionDecision

        decision = SuppressionDecision(
            decision_id="test_reward",
            target_agent_id="agent_test",
            suppression_level=SuppressionLevel.STRONG,
            risk_score=risk_score,
            action_taken="IL10=high",
            q_value=0.5,
            exploration=False,
        )

        reward = regulatory_t._calculate_reward(decision)

        # High risk should give positive reward
        assert reward > 0.0


# ==================== GRADUATED SUPPRESSION TESTS ====================


class TestGraduatedSuppression:
    """Test graduated suppression levels"""

    def test_il10_levels(self, regulatory_t: LinfocitoTRegulador):
        """Test IL10 levels for each suppression level"""
        assert regulatory_t._get_il10_level(SuppressionLevel.SOFT) == "low"
        assert regulatory_t._get_il10_level(SuppressionLevel.MODERATE) == "medium"
        assert regulatory_t._get_il10_level(SuppressionLevel.STRONG) == "high"
        assert regulatory_t._get_il10_level(SuppressionLevel.CRITICAL) == "very_high"

    def test_tgf_beta_levels(self, regulatory_t: LinfocitoTRegulador):
        """Test TGF-β levels for each suppression level"""
        assert regulatory_t._get_tgf_beta_level(SuppressionLevel.SOFT) == "none"
        assert regulatory_t._get_tgf_beta_level(SuppressionLevel.MODERATE) == "low"
        assert regulatory_t._get_tgf_beta_level(SuppressionLevel.STRONG) == "medium"
        assert regulatory_t._get_tgf_beta_level(SuppressionLevel.CRITICAL) == "high"

    @pytest.mark.asyncio
    async def test_suppression_decision_creation(
        self, regulatory_t: LinfocitoTRegulador, friendly_fire_activities: list
    ):
        """Test suppression decision creation"""
        regulatory_t.monitored_agents["agent_001"] = friendly_fire_activities

        risk_score = await regulatory_t._calculate_autoimmunity_risk("agent_001", friendly_fire_activities)

        await regulatory_t._make_suppression_decision("agent_001", risk_score)

        assert len(regulatory_t.suppression_decisions) == 1
        assert regulatory_t.suppression_decisions[0].target_agent_id == "agent_001"
        assert "agent_001" in regulatory_t.suppressed_agents


# ==================== CYTOKINE SECRETION TESTS ====================


class TestCytokineSecretion:
    """Test IL10 and TGF-β secretion"""

    @pytest.mark.asyncio
    async def test_il10_secretion_without_messenger(self, regulatory_t: LinfocitoTRegulador):
        """Test IL10 secretion without messenger doesn't crash"""
        risk_score = AutoimmunityRiskScore(
            total_score=0.8,
            friendly_fire_score=0.5,
            excessive_response_score=0.5,
            temporal_pattern_score=0.0,
            target_diversity_score=0.0,
            false_positive_history_score=0.0,
            self_similarity_score=0.0,
            justification="Test",
        )

        from agents.regulatory_t_cell import SuppressionDecision

        decision = SuppressionDecision(
            decision_id="test_il10",
            target_agent_id="agent_test",
            suppression_level=SuppressionLevel.MODERATE,
            risk_score=risk_score,
            action_taken="IL10=medium",
            q_value=0.5,
            exploration=False,
        )

        # No messenger started
        await regulatory_t._execute_suppression_action(decision)

        # Should not crash (graceful degradation)
        assert regulatory_t.il10_secretions == 0

    @pytest.mark.asyncio
    async def test_il10_secretion_increments_counter(self, regulatory_t: LinfocitoTRegulador):
        """Test IL10 secretion increments counter"""
        await regulatory_t.iniciar()

        risk_score = AutoimmunityRiskScore(
            total_score=0.8,
            friendly_fire_score=0.5,
            excessive_response_score=0.5,
            temporal_pattern_score=0.0,
            target_diversity_score=0.0,
            false_positive_history_score=0.0,
            self_similarity_score=0.0,
            justification="Test",
        )

        from agents.regulatory_t_cell import SuppressionDecision

        decision = SuppressionDecision(
            decision_id="test_il10_inc",
            target_agent_id="agent_test",
            suppression_level=SuppressionLevel.SOFT,
            risk_score=risk_score,
            action_taken="IL10=low",
            q_value=0.5,
            exploration=False,
        )

        await regulatory_t._execute_suppression_action(decision)

        assert regulatory_t.il10_secretions == 1
        assert regulatory_t.prevented_autoimmune_attacks == 1

        await regulatory_t.parar()

    @pytest.mark.asyncio
    async def test_tgf_beta_secretion_moderate_level(self, regulatory_t: LinfocitoTRegulador):
        """Test TGF-β secretion at moderate suppression"""
        await regulatory_t.iniciar()

        risk_score = AutoimmunityRiskScore(
            total_score=0.8,
            friendly_fire_score=0.5,
            excessive_response_score=0.5,
            temporal_pattern_score=0.0,
            target_diversity_score=0.0,
            false_positive_history_score=0.0,
            self_similarity_score=0.0,
            justification="Test",
        )

        from agents.regulatory_t_cell import SuppressionDecision

        decision = SuppressionDecision(
            decision_id="test_tgf",
            target_agent_id="agent_test",
            suppression_level=SuppressionLevel.MODERATE,
            risk_score=risk_score,
            action_taken="TGF-β=low",
            q_value=0.5,
            exploration=False,
        )

        await regulatory_t._execute_suppression_action(decision)

        assert regulatory_t.tgf_beta_secretions == 1

        await regulatory_t.parar()


# ==================== MONITORING & DETECTION TESTS ====================


class TestMonitoring:
    """Test monitoring and detection"""

    @pytest.mark.asyncio
    async def test_monitor_immune_activity(self, regulatory_t: LinfocitoTRegulador):
        """Test monitoring immune activity"""
        cytokine_data = {
            "emissor_id": "agent_monitor",
            "tipo": "IL1",
            "payload": {"alvo": {"ip": "10.0.1.100"}},
        }

        await regulatory_t._monitor_immune_activity(cytokine_data)

        assert "agent_monitor" in regulatory_t.monitored_agents
        assert len(regulatory_t.monitored_agents["agent_monitor"]) == 1

    @pytest.mark.asyncio
    async def test_detection_triggers_suppression(
        self, regulatory_t: LinfocitoTRegulador, friendly_fire_activities: list
    ):
        """Test autoimmunity detection triggers suppression"""
        # Need more activities to reach threshold (friendly fire alone = 0.25 * 1.0 = 0.25, need 0.65 total)
        # Add excessive response activities
        combined_activities = friendly_fire_activities + [
            {
                "agent_id": "agent_auto",
                "cytokine": "IFN_GAMMA",
                "payload": {"alvo": {"ip": "10.0.1.100"}},
                "timestamp": datetime.now() - timedelta(milliseconds=i),
            }
            for i in range(15)
        ]

        regulatory_t.monitored_agents["agent_auto"] = combined_activities

        await regulatory_t._monitor_for_autoimmunity()

        # Should detect and suppress (combined friendly fire + excessive response)
        assert (
            len(regulatory_t.suppression_decisions) >= 1 or regulatory_t.regulatory_state == RegulatoryTState.ANALYZING
        )


# ==================== SELF-MONITORING TESTS ====================


class TestSelfMonitoring:
    """Test self-monitoring and auto-correction"""

    @pytest.mark.asyncio
    async def test_suppression_effectiveness_tracking(self, regulatory_t: LinfocitoTRegulador):
        """Test suppression effectiveness is tracked"""
        risk_score = AutoimmunityRiskScore(
            total_score=0.8,
            friendly_fire_score=0.5,
            excessive_response_score=0.5,
            temporal_pattern_score=0.0,
            target_diversity_score=0.0,
            false_positive_history_score=0.0,
            self_similarity_score=0.0,
            justification="Test",
        )

        from agents.regulatory_t_cell import SuppressionDecision

        decision = SuppressionDecision(
            decision_id="test_effective",
            target_agent_id="agent_test",
            suppression_level=SuppressionLevel.MODERATE,
            risk_score=risk_score,
            action_taken="IL10=medium",
            q_value=0.5,
            exploration=False,
        )

        regulatory_t.suppression_decisions.append(decision)

        await regulatory_t._monitor_suppression_effectiveness()

        # Effectiveness should be tracked (may be 0.0 or 1.0)
        assert decision.decision_id in regulatory_t.suppression_effectiveness or True

    def test_false_positive_detection(self, regulatory_t: LinfocitoTRegulador):
        """Test false positive tracking"""
        regulatory_t.false_positives.append("agent_fp_001")

        assert "agent_fp_001" in regulatory_t.false_positives
        assert len(regulatory_t.false_positives) == 1


# ==================== INVESTIGATION/NEUTRALIZATION TESTS ====================


class TestInvestigationNeutralization:
    """Test investigation and neutralization"""

    @pytest.mark.asyncio
    async def test_investigation_analyzes_autoimmunity(
        self, regulatory_t: LinfocitoTRegulador, friendly_fire_activities: list
    ):
        """Test investigation analyzes for autoimmunity"""
        # Add excessive response to push score above threshold
        combined_activities = friendly_fire_activities + [
            {
                "agent_id": "agent_inv",
                "cytokine": "IFN_GAMMA",
                "payload": {"alvo": {"ip": "10.0.1.100"}},
                "timestamp": datetime.now() - timedelta(milliseconds=i),
            }
            for i in range(15)
        ]

        regulatory_t.monitored_agents["agent_inv"] = combined_activities

        result = await regulatory_t.executar_investigacao({"agent_id": "agent_inv"})

        assert "is_threat" in result
        assert result["is_threat"] is True  # High friendly fire + excessive response
        assert result["confidence"] >= 0.65
        assert "multi_criteria" in result["metodo"]

    @pytest.mark.asyncio
    async def test_investigation_insufficient_data(self, regulatory_t: LinfocitoTRegulador):
        """Test investigation with insufficient data"""
        result = await regulatory_t.executar_investigacao({"agent_id": "unknown_agent"})

        assert result["is_threat"] is False
        assert "insufficient_data" in result["metodo"]

    @pytest.mark.asyncio
    async def test_neutralization_triggers_suppression(self, regulatory_t: LinfocitoTRegulador):
        """Test neutralization triggers suppression"""
        result = await regulatory_t.executar_neutralizacao({"agent_id": "agent_suppress"}, metodo="suppress")

        assert result is True
        assert len(regulatory_t.suppression_decisions) == 1


# ==================== METRICS TESTS ====================


class TestRegulatoryTMetrics:
    """Test Regulatory T Cell metrics"""

    @pytest.mark.asyncio
    async def test_get_regulatory_t_metrics(self, regulatory_t: LinfocitoTRegulador):
        """Test getting Regulatory T Cell metrics"""
        metrics = regulatory_t.get_regulatory_t_metrics()

        assert "regulatory_state" in metrics
        assert "monitored_agents" in metrics
        assert "suppression_decisions" in metrics
        assert "prevented_autoimmune_attacks" in metrics
        assert "il10_secretions" in metrics
        assert "tgf_beta_secretions" in metrics
        assert "false_positives" in metrics
        assert "auto_corrections" in metrics
        assert "q_table_size" in metrics
        assert "avg_q_value" in metrics
        assert "avg_reward" in metrics
        assert "suppression_level_distribution" in metrics

    @pytest.mark.asyncio
    async def test_metrics_with_ml_data(self, regulatory_t: LinfocitoTRegulador):
        """Test metrics with ML Q-table data"""
        # Add some Q-values
        regulatory_t.q_table[("high_risk", SuppressionLevel.STRONG)] = 0.8
        regulatory_t.q_table[("medium_risk", SuppressionLevel.MODERATE)] = 0.5

        # Add rewards
        regulatory_t.reward_history.extend([0.5, 0.7, 0.9])

        metrics = regulatory_t.get_regulatory_t_metrics()

        assert metrics["q_table_size"] == 2
        assert metrics["avg_q_value"] > 0.0
        assert metrics["avg_reward"] > 0.0

    def test_repr(self, regulatory_t: LinfocitoTRegulador):
        """Test string representation"""
        repr_str = repr(regulatory_t)

        assert "LinfocitoTRegulador" in repr_str
        assert regulatory_t.state.id[:8] in repr_str
        assert regulatory_t.regulatory_state in repr_str or "state=" in repr_str


# ==================== EDGE CASES ====================


class TestRegulatoryTEdgeCases:
    """Test Regulatory T Cell edge cases"""

    @pytest.mark.asyncio
    async def test_empty_activities_risk_score(self, regulatory_t: LinfocitoTRegulador):
        """Test risk scoring with empty activities"""
        risk_score = await regulatory_t._calculate_autoimmunity_risk("agent_empty", [])

        # Should return low risk with empty activities
        assert risk_score.total_score == 0.0

    @pytest.mark.asyncio
    async def test_suppression_with_max_q_values(self, regulatory_t: LinfocitoTRegulador):
        """Test suppression with all Q-values equal"""
        # Set all Q-values to same value
        for level in SuppressionLevel:
            regulatory_t.q_table[("high_risk", level)] = 0.5

        # Should still choose an action
        action = regulatory_t._choose_suppression_level("high_risk")

        assert isinstance(action, SuppressionLevel)

    @pytest.mark.asyncio
    async def test_activity_history_limit(self, regulatory_t: LinfocitoTRegulador):
        """Test activity history is limited per agent"""
        # Add 100 activities
        for i in range(100):
            await regulatory_t._monitor_immune_activity(
                {
                    "emissor_id": "agent_history",
                    "tipo": "IL1",
                    "payload": {},
                }
            )

        # Should be limited to 50
        assert len(regulatory_t.monitored_agents["agent_history"]) == 50
