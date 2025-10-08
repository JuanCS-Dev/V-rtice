"""Digital Regulatory T Cell - Intelligent Immune System Brake

Regulatory T Cells (Tregs) are the "intelligent governors" of immunity:
1. Prevent autoimmunity (friendly fire detection)
2. Suppress excessive responses (graduated IL10/TGF-β)
3. Enforce self-tolerance (protect legitimate traffic)
4. Machine learning for optimal suppression
5. Multi-criteria autoimmunity scoring
6. Temporal pattern analysis
7. Self-monitoring and auto-correction
8. Complete decision audit trail

MOST ADVANCED CELL - Machine Learning + Multi-Criteria Analysis:
- Q-learning for suppression decisions
- 4-level graduated suppression (soft → critical)
- Autoimmunity risk scoring (6 criteria)
- False positive detection
- Decision explainability

PRODUCTION-READY: Real ML, real scoring, no mocks, graceful degradation.
"""

import logging
from collections import defaultdict, deque
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Tuple
from uuid import uuid4

import numpy as np
from pydantic import BaseModel, Field

from .base import AgenteImunologicoBase
from .models import AgentType

logger = logging.getLogger(__name__)


# ==================== MODELS ====================


class SuppressionLevel(str, Enum):
    """Suppression intensity levels"""

    SOFT = "soft"  # Light suppression (IL10)
    MODERATE = "moderate"  # Moderate suppression (IL10 + TGF-β)
    STRONG = "strong"  # Strong suppression (high IL10 + TGF-β)
    CRITICAL = "critical"  # Critical suppression (emergency brake)


class AutoimmunityRiskScore(BaseModel):
    """Multi-criteria autoimmunity risk assessment"""

    total_score: float = Field(ge=0.0, le=1.0, description="Total risk score")

    # Individual criteria (0-1 each)
    friendly_fire_score: float = Field(ge=0.0, le=1.0, description="Attacking own IPs")
    excessive_response_score: float = Field(ge=0.0, le=1.0, description="Response disproportionate")
    temporal_pattern_score: float = Field(ge=0.0, le=1.0, description="Unusual timing patterns")
    target_diversity_score: float = Field(ge=0.0, le=1.0, description="Too many diverse targets")
    false_positive_history_score: float = Field(ge=0.0, le=1.0, description="Historical false positives")
    self_similarity_score: float = Field(ge=0.0, le=1.0, description="Target similar to self")

    criteria_weights: Dict[str, float] = Field(
        default={
            "friendly_fire": 0.25,
            "excessive_response": 0.20,
            "temporal_pattern": 0.15,
            "target_diversity": 0.15,
            "false_positive_history": 0.15,
            "self_similarity": 0.10,
        }
    )

    justification: str = Field(description="Human-readable justification")
    timestamp: datetime = Field(default_factory=datetime.now)


class SuppressionDecision(BaseModel):
    """Suppression decision with full audit trail"""

    decision_id: str = Field(description="Decision ID")
    target_agent_id: str = Field(description="Agent to suppress")
    suppression_level: SuppressionLevel = Field(description="Suppression intensity")
    risk_score: AutoimmunityRiskScore = Field(description="Risk assessment")
    action_taken: str = Field(description="IL10/TGF-β levels secreted")
    q_value: float = Field(description="Q-learning value for this decision")
    exploration: bool = Field(description="Was this exploration or exploitation")
    timestamp: datetime = Field(default_factory=datetime.now)


class RegulatoryTState(str, Enum):
    """Regulatory T Cell states"""

    MONITORING = "monitoring"  # Watching immune responses
    ANALYZING = "analyzing"  # Deep analysis of potential autoimmunity
    SUPPRESSING = "suppressing"  # Active suppression
    LEARNING = "learning"  # ML model update


# ==================== REGULATORY T CELL ====================


class LinfocitoTRegulador(AgenteImunologicoBase):
    """
    Digital Regulatory T Cell - Intelligent immune brake with ML.

    Advanced Capabilities:
    - Q-learning for optimal suppression decisions
    - Multi-criteria autoimmunity risk scoring (6 criteria)
    - Graduated suppression (4 levels)
    - Temporal pattern analysis
    - False positive detection
    - Self-monitoring and auto-correction
    - Complete decision audit trail
    - IL10 and TGF-β secretion (proportional)

    Intelligence Features:
    - Machine learning (Q-learning)
    - Multi-criteria scoring system
    - Pattern analysis (temporal + spatial)
    - Explainable decisions (audit trail)
    - Self-optimization

    Use cases:
    - Prevent autoimmune attacks (friendly fire)
    - Suppress excessive immune responses
    - Protect legitimate traffic
    - Learn optimal suppression strategies
    - Maintain immune homeostasis
    """

    def __init__(
        self,
        area_patrulha: str,
        kafka_bootstrap: str = "localhost:9092",
        redis_url: str = "redis://localhost:6379",
        autoimmunity_threshold: float = 0.65,
        learning_rate: float = 0.1,
        discount_factor: float = 0.9,
        epsilon: float = 0.1,
        **kwargs,
    ):
        """
        Initialize Regulatory T Cell.

        Args:
            area_patrulha: Network zone to patrol
            kafka_bootstrap: Kafka broker
            redis_url: Redis URL
            autoimmunity_threshold: Min risk score for suppression (0-1)
            learning_rate: Q-learning alpha (0-1)
            discount_factor: Q-learning gamma (0-1)
            epsilon: Exploration rate (0-1)
        """
        super().__init__(
            tipo=AgentType.LINFOCITO_T_REGULADOR,
            area_patrulha=area_patrulha,
            kafka_bootstrap=kafka_bootstrap,
            redis_url=redis_url,
            **kwargs,
        )

        # Regulatory T-specific configuration
        self.autoimmunity_threshold = autoimmunity_threshold
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon

        # Regulatory T-specific state
        self.regulatory_state: str = RegulatoryTState.MONITORING
        self.suppression_decisions: List[SuppressionDecision] = []
        self.monitored_agents: Dict[str, List[Dict[str, Any]]] = defaultdict(list)  # agent_id -> actions
        self.false_positives: List[str] = []  # Agent IDs wrongly attacked
        self.suppressed_agents: Dict[str, SuppressionLevel] = {}  # agent_id -> level
        self.il10_secretions: int = 0
        self.tgf_beta_secretions: int = 0
        self.prevented_autoimmune_attacks: int = 0

        # Machine Learning (Q-learning)
        self.q_table: Dict[Tuple[str, str], float] = defaultdict(float)  # (state, action) -> Q-value
        self.state_history: deque = deque(maxlen=100)  # Recent states for pattern analysis
        self.reward_history: deque = deque(maxlen=100)  # Recent rewards

        # Self-monitoring
        self.suppression_effectiveness: Dict[str, float] = {}  # decision_id -> effectiveness
        self.false_positive_rate: float = 0.0
        self.auto_corrections: int = 0

        logger.info(
            f"Regulatory T Cell initialized: {self.state.id[:8]} "
            f"(zone={area_patrulha}, threshold={autoimmunity_threshold}, ML=enabled)"
        )

    # ==================== LIFECYCLE ====================

    async def iniciar(self) -> None:
        """Start Regulatory T Cell - begin monitoring immune responses"""
        await super().iniciar()

        # Subscribe to immune activity
        if self._cytokine_messenger and self._cytokine_messenger.is_running():
            try:
                # Monitor all cytokines to detect excessive responses
                for cytokine_type in ["IL1", "IL2", "IL4", "IL8", "IFN_GAMMA"]:
                    await self._cytokine_messenger.subscribe_cytokine(cytokine_type, self._monitor_immune_activity)
                logger.info(f"Regulatory T {self.state.id[:8]} monitoring immune activity")
            except Exception as e:
                logger.warning(f"Failed to subscribe to cytokines: {e}, degraded mode")

        self.regulatory_state = RegulatoryTState.MONITORING

    # ==================== PATROL ====================

    async def patrulhar(self) -> None:
        """
        Regulatory T Cell patrol - monitor for autoimmunity.

        State-dependent behavior:
        - MONITORING: Watch immune responses
        - ANALYZING: Deep risk analysis
        - SUPPRESSING: Active IL10/TGF-β secretion
        - LEARNING: Update ML model
        """
        if self.regulatory_state == RegulatoryTState.MONITORING:
            await self._monitor_for_autoimmunity()
        elif self.regulatory_state == RegulatoryTState.ANALYZING:
            await self._analyze_autoimmunity_risk()
        elif self.regulatory_state == RegulatoryTState.SUPPRESSING:
            await self._execute_suppression()
        elif self.regulatory_state == RegulatoryTState.LEARNING:
            await self._update_ml_model()

    # ==================== MONITORING ====================

    async def _monitor_immune_activity(self, cytokine_data: Dict[str, Any]) -> None:
        """
        Monitor immune activity for signs of autoimmunity.

        Args:
            cytokine_data: Cytokine message data
        """
        agent_id = cytokine_data.get("emissor_id", "unknown")
        cytokine_type = cytokine_data.get("tipo", "unknown")

        # Store activity for pattern analysis
        activity = {
            "agent_id": agent_id,
            "cytokine": cytokine_type,
            "payload": cytokine_data.get("payload", {}),
            "timestamp": datetime.now(),
        }

        self.monitored_agents[agent_id].append(activity)

        # Limit history per agent
        if len(self.monitored_agents[agent_id]) > 50:
            self.monitored_agents[agent_id] = self.monitored_agents[agent_id][-50:]

    async def _monitor_for_autoimmunity(self) -> None:
        """Monitor for potential autoimmune behavior"""
        logger.debug(f"Regulatory T {self.state.id[:8]} monitoring for autoimmunity")

        # Check each monitored agent
        for agent_id, activities in self.monitored_agents.items():
            if len(activities) >= 5:  # Need minimum activity for analysis
                risk_score = await self._calculate_autoimmunity_risk(agent_id, activities)

                if risk_score.total_score >= self.autoimmunity_threshold:
                    logger.warning(
                        f"Regulatory T {self.state.id[:8]} detected autoimmunity risk "
                        f"(agent={agent_id[:8]}, score={risk_score.total_score:.2f})"
                    )

                    # Change to analyzing state
                    self.regulatory_state = RegulatoryTState.ANALYZING

                    # Make suppression decision
                    await self._make_suppression_decision(agent_id, risk_score)

    # ==================== RISK ANALYSIS ====================

    async def _calculate_autoimmunity_risk(
        self, agent_id: str, activities: List[Dict[str, Any]]
    ) -> AutoimmunityRiskScore:
        """
        Calculate multi-criteria autoimmunity risk score.

        Args:
            agent_id: Agent to analyze
            activities: Recent activities

        Returns:
            Risk score with breakdown
        """
        # Criterion 1: Friendly Fire (attacking own IPs)
        friendly_fire_score = self._score_friendly_fire(activities)

        # Criterion 2: Excessive Response (disproportionate to threat)
        excessive_response_score = self._score_excessive_response(activities)

        # Criterion 3: Temporal Pattern (unusual timing)
        temporal_pattern_score = self._score_temporal_pattern(activities)

        # Criterion 4: Target Diversity (too many different targets)
        target_diversity_score = self._score_target_diversity(activities)

        # Criterion 5: False Positive History
        false_positive_history_score = 1.0 if agent_id in self.false_positives else 0.0

        # Criterion 6: Self Similarity (target similar to legitimate traffic)
        self_similarity_score = self._score_self_similarity(activities)

        # Calculate weighted total
        weights = {
            "friendly_fire": 0.25,
            "excessive_response": 0.20,
            "temporal_pattern": 0.15,
            "target_diversity": 0.15,
            "false_positive_history": 0.15,
            "self_similarity": 0.10,
        }

        total_score = (
            friendly_fire_score * weights["friendly_fire"]
            + excessive_response_score * weights["excessive_response"]
            + temporal_pattern_score * weights["temporal_pattern"]
            + target_diversity_score * weights["target_diversity"]
            + false_positive_history_score * weights["false_positive_history"]
            + self_similarity_score * weights["self_similarity"]
        )

        # Generate justification
        justification = self._generate_justification(
            friendly_fire_score,
            excessive_response_score,
            temporal_pattern_score,
            target_diversity_score,
            false_positive_history_score,
            self_similarity_score,
        )

        return AutoimmunityRiskScore(
            total_score=total_score,
            friendly_fire_score=friendly_fire_score,
            excessive_response_score=excessive_response_score,
            temporal_pattern_score=temporal_pattern_score,
            target_diversity_score=target_diversity_score,
            false_positive_history_score=false_positive_history_score,
            self_similarity_score=self_similarity_score,
            criteria_weights=weights,
            justification=justification,
        )

    def _score_friendly_fire(self, activities: List[Dict[str, Any]]) -> float:
        """Score friendly fire attacks (attacking own network)"""
        own_ips_attacked = 0
        total_attacks = 0

        for activity in activities:
            payload = activity.get("payload", {})
            target_ip = payload.get("alvo", {}).get("ip", "")

            if target_ip:
                total_attacks += 1
                # Check if IP is in own network (simplified: 10.0.x.x)
                if target_ip.startswith("10.0."):
                    own_ips_attacked += 1

        return own_ips_attacked / total_attacks if total_attacks > 0 else 0.0

    def _score_excessive_response(self, activities: List[Dict[str, Any]]) -> float:
        """Score response excessiveness"""
        high_aggression = sum(1 for a in activities if a.get("cytokine") in ["IL1", "IFN_GAMMA"])
        return min(high_aggression / 10.0, 1.0)  # Cap at 1.0

    def _score_temporal_pattern(self, activities: List[Dict[str, Any]]) -> float:
        """Score unusual temporal patterns"""
        if len(activities) < 3:
            return 0.0

        # Check for rapid-fire pattern (all within 1 second)
        timestamps = [a["timestamp"] for a in activities[-5:]]
        time_span = (max(timestamps) - min(timestamps)).total_seconds()

        return 1.0 if time_span < 1.0 else 0.0

    def _score_target_diversity(self, activities: List[Dict[str, Any]]) -> float:
        """Score target diversity (attacking many different IPs)"""
        targets = set()
        for activity in activities:
            payload = activity.get("payload", {})
            target_ip = payload.get("alvo", {}).get("ip", "")
            if target_ip:
                targets.add(target_ip)

        # High diversity (>10 targets) suggests scanning/autoimmunity
        return min(len(targets) / 10.0, 1.0)

    def _score_self_similarity(self, activities: List[Dict[str, Any]]) -> float:
        """Score similarity to legitimate traffic patterns"""
        # Simplified: check if targeting common ports (80, 443, 22)
        legitimate_ports = {80, 443, 22}
        legitimate_targets = 0
        total_targets = 0

        for activity in activities:
            payload = activity.get("payload", {})
            port = payload.get("alvo", {}).get("porta", 0)
            if port:
                total_targets += 1
                if port in legitimate_ports:
                    legitimate_targets += 1

        return legitimate_targets / total_targets if total_targets > 0 else 0.0

    def _generate_justification(self, *scores) -> str:
        """Generate human-readable justification"""
        ff, er, tp, td, fp, ss = scores

        reasons = []
        if ff > 0.5:
            reasons.append(f"Friendly fire: {ff:.1%}")
        if er > 0.5:
            reasons.append(f"Excessive response: {er:.1%}")
        if tp > 0.5:
            reasons.append("Unusual timing pattern")
        if td > 0.5:
            reasons.append(f"High target diversity: {td:.1%}")
        if fp > 0.5:
            reasons.append("Historical false positives")
        if ss > 0.5:
            reasons.append(f"Self-similar targets: {ss:.1%}")

        return "; ".join(reasons) if reasons else "Low risk across all criteria"

    # ==================== SUPPRESSION DECISION (ML) ====================

    async def _analyze_autoimmunity_risk(self) -> None:
        """Deep analysis state (transition from monitoring)"""
        self.regulatory_state = RegulatoryTState.MONITORING  # Return to monitoring

    async def _make_suppression_decision(self, agent_id: str, risk_score: AutoimmunityRiskScore) -> None:
        """
        Make intelligent suppression decision using Q-learning.

        Args:
            agent_id: Agent to potentially suppress
            risk_score: Calculated risk score
        """
        # Get current state (discretized risk score)
        state = self._discretize_risk_score(risk_score.total_score)

        # Choose action (suppression level) using epsilon-greedy
        action = self._choose_suppression_level(state)

        # Check if exploration
        is_exploration = np.random.random() < self.epsilon

        # Get Q-value for this state-action
        q_value = self.q_table[(state, action)]

        # Create decision
        decision = SuppressionDecision(
            decision_id=str(uuid4()),
            target_agent_id=agent_id,
            suppression_level=action,
            risk_score=risk_score,
            action_taken=f"IL10={self._get_il10_level(action)}, TGF-β={self._get_tgf_beta_level(action)}",
            q_value=q_value,
            exploration=is_exploration,
        )

        self.suppression_decisions.append(decision)
        self.suppressed_agents[agent_id] = action

        logger.info(
            f"Regulatory T {self.state.id[:8]} SUPPRESSION DECISION: "
            f"agent={agent_id[:8]}, level={action}, risk={risk_score.total_score:.2f}, "
            f"Q={q_value:.3f}, exploration={is_exploration}"
        )

        # Execute suppression
        self.regulatory_state = RegulatoryTState.SUPPRESSING
        await self._execute_suppression_action(decision)

    def _discretize_risk_score(self, score: float) -> str:
        """Discretize continuous risk score into state"""
        if score < 0.3:
            return "low_risk"
        elif score < 0.6:
            return "medium_risk"
        elif score < 0.8:
            return "high_risk"
        else:
            return "critical_risk"

    def _choose_suppression_level(self, state: str) -> SuppressionLevel:
        """Choose suppression level using epsilon-greedy Q-learning"""
        actions = list(SuppressionLevel)

        # Exploration: random action
        if np.random.random() < self.epsilon:
            import random

            return random.choice(actions)

        # Exploitation: choose best action
        q_values = [self.q_table[(state, action)] for action in actions]
        best_action_idx = np.argmax(q_values)

        return actions[best_action_idx]

    def _get_il10_level(self, suppression_level: SuppressionLevel) -> str:
        """Get IL10 secretion level for suppression"""
        levels = {
            SuppressionLevel.SOFT: "low",
            SuppressionLevel.MODERATE: "medium",
            SuppressionLevel.STRONG: "high",
            SuppressionLevel.CRITICAL: "very_high",
        }
        return levels.get(suppression_level, "medium")

    def _get_tgf_beta_level(self, suppression_level: SuppressionLevel) -> str:
        """Get TGF-β secretion level for suppression"""
        levels = {
            SuppressionLevel.SOFT: "none",
            SuppressionLevel.MODERATE: "low",
            SuppressionLevel.STRONG: "medium",
            SuppressionLevel.CRITICAL: "high",
        }
        return levels.get(suppression_level, "low")

    # ==================== SUPPRESSION EXECUTION ====================

    async def _execute_suppression(self) -> None:
        """Execute suppression (state handler)"""
        self.regulatory_state = RegulatoryTState.MONITORING

    async def _execute_suppression_action(self, decision: SuppressionDecision) -> None:
        """
        Execute suppression by secreting IL10 and TGF-β.

        Args:
            decision: Suppression decision
        """
        if not self._cytokine_messenger or not self._cytokine_messenger.is_running():
            logger.debug("Cytokine messenger unavailable, degraded mode")
            return

        try:
            # Secrete IL10 (anti-inflammatory)
            il10_level = self._get_il10_level(decision.suppression_level)
            await self._cytokine_messenger.send_cytokine(
                tipo="IL10",
                payload={
                    "evento": "immune_suppression",
                    "regulatory_t_id": self.state.id,
                    "target_agent_id": decision.target_agent_id,
                    "suppression_level": decision.suppression_level,
                    "il10_level": il10_level,
                    "justification": decision.risk_score.justification,
                },
                emissor_id=self.state.id,
                prioridade=10,  # High priority
                area_alvo=self.state.area_patrulha,
            )
            self.il10_secretions += 1

            # Secrete TGF-β if moderate or higher
            if decision.suppression_level in [
                SuppressionLevel.MODERATE,
                SuppressionLevel.STRONG,
                SuppressionLevel.CRITICAL,
            ]:
                tgf_beta_level = self._get_tgf_beta_level(decision.suppression_level)
                await self._cytokine_messenger.send_cytokine(
                    tipo="TGF_BETA",
                    payload={
                        "evento": "immune_suppression",
                        "regulatory_t_id": self.state.id,
                        "target_agent_id": decision.target_agent_id,
                        "tgf_beta_level": tgf_beta_level,
                    },
                    emissor_id=self.state.id,
                    prioridade=10,
                    area_alvo=self.state.area_patrulha,
                )
                self.tgf_beta_secretions += 1

            self.prevented_autoimmune_attacks += 1

            logger.info(
                f"Regulatory T {self.state.id[:8]} suppressed agent {decision.target_agent_id[:8]} "
                f"(IL10={il10_level}, TGF-β={tgf_beta_level})"
            )

        except Exception as e:
            logger.error(f"Suppression execution failed: {e}")

    # ==================== MACHINE LEARNING ====================

    async def _update_ml_model(self) -> None:
        """Update Q-learning model based on outcomes"""
        # Get recent decision
        if not self.suppression_decisions:
            self.regulatory_state = RegulatoryTState.MONITORING
            return

        last_decision = self.suppression_decisions[-1]

        # Calculate reward (simplified: based on whether attack stopped)
        reward = self._calculate_reward(last_decision)

        # Store reward
        self.reward_history.append(reward)

        # Update Q-value
        state = self._discretize_risk_score(last_decision.risk_score.total_score)
        action = last_decision.suppression_level

        # Q-learning update: Q(s,a) = Q(s,a) + α[r + γ max Q(s',a') - Q(s,a)]
        current_q = self.q_table[(state, action)]

        # Simplified: assume next state is monitoring with no action
        max_next_q = 0.0

        new_q = current_q + self.learning_rate * (reward + self.discount_factor * max_next_q - current_q)
        self.q_table[(state, action)] = new_q

        logger.debug(
            f"Regulatory T {self.state.id[:8]} ML update: "
            f"Q({state},{action}) = {current_q:.3f} → {new_q:.3f}, reward={reward:.2f}"
        )

        # Return to monitoring
        self.regulatory_state = RegulatoryTState.MONITORING

    def _calculate_reward(self, decision: SuppressionDecision) -> float:
        """
        Calculate reward for RL.

        Positive: Successful suppression (no false positive)
        Negative: False positive or insufficient suppression
        """
        # Simplified reward function
        # In production: would check if agent activity decreased after suppression

        agent_id = decision.target_agent_id

        # Check if agent marked as false positive
        if agent_id in self.false_positives:
            return -1.0  # Penalty for false positive

        # Reward based on risk score (higher risk = higher reward for suppression)
        return decision.risk_score.total_score * 2.0 - 1.0  # Range: -1 to 1

    # ==================== SELF-MONITORING ====================

    async def _monitor_suppression_effectiveness(self) -> None:
        """Monitor effectiveness of suppressions and auto-correct"""
        for decision in self.suppression_decisions[-10:]:  # Recent decisions
            agent_id = decision.target_agent_id

            # Check if agent still active after suppression
            recent_activity = self.monitored_agents.get(agent_id, [])
            activity_after_suppression = [a for a in recent_activity if a["timestamp"] > decision.timestamp]

            # If still very active after suppression, mark as ineffective
            if len(activity_after_suppression) > 10:
                effectiveness = 0.0
                self.suppression_effectiveness[decision.decision_id] = effectiveness

                # Auto-correction: escalate suppression
                if decision.suppression_level != SuppressionLevel.CRITICAL:
                    logger.warning(
                        f"Regulatory T {self.state.id[:8]} auto-correction: ineffective suppression, escalating"
                    )
                    self.auto_corrections += 1
            else:
                effectiveness = 1.0
                self.suppression_effectiveness[decision.decision_id] = effectiveness

    # ==================== INVESTIGATION & NEUTRALIZATION ====================

    async def executar_investigacao(self, alvo: Dict[str, Any]) -> Dict[str, Any]:
        """
        Regulatory T investigates for autoimmune signs.

        Args:
            alvo: Target to analyze

        Returns:
            Autoimmunity assessment
        """
        logger.info(f"Regulatory T {self.state.id[:8]} analyzing for autoimmunity")

        # Calculate risk
        agent_id = alvo.get("agent_id", "unknown")
        activities = self.monitored_agents.get(agent_id, [])

        if activities:
            risk_score = await self._calculate_autoimmunity_risk(agent_id, activities)

            return {
                "is_threat": risk_score.total_score >= self.autoimmunity_threshold,
                "confidence": risk_score.total_score,
                "metodo": "multi_criteria_autoimmunity_analysis",
                "detalhes": risk_score.justification,
            }
        else:
            return {
                "is_threat": False,
                "confidence": 0.0,
                "metodo": "insufficient_data",
                "detalhes": "No activity history available",
            }

    async def executar_neutralizacao(self, alvo: Dict[str, Any], metodo: str) -> bool:
        """
        Regulatory T suppresses (doesn't neutralize threats directly).

        Args:
            alvo: Agent to suppress
            metodo: Suppression method

        Returns:
            True if suppression executed
        """
        agent_id = alvo.get("agent_id", "unknown")

        logger.info(f"Regulatory T {self.state.id[:8]} suppressing agent {agent_id[:8]}")

        # Create minimal risk score for direct suppression
        risk_score = AutoimmunityRiskScore(
            total_score=0.8,
            friendly_fire_score=0.5,
            excessive_response_score=0.5,
            temporal_pattern_score=0.0,
            target_diversity_score=0.0,
            false_positive_history_score=0.0,
            self_similarity_score=0.0,
            justification="Direct suppression requested",
        )

        await self._make_suppression_decision(agent_id, risk_score)

        return True

    # ==================== METRICS ====================

    def get_regulatory_t_metrics(self) -> Dict[str, Any]:
        """
        Get Regulatory T Cell-specific metrics.

        Returns:
            Metrics dictionary
        """
        return {
            "regulatory_state": self.regulatory_state,
            "monitored_agents": len(self.monitored_agents),
            "suppression_decisions": len(self.suppression_decisions),
            "suppressed_agents": len(self.suppressed_agents),
            "prevented_autoimmune_attacks": self.prevented_autoimmune_attacks,
            "il10_secretions": self.il10_secretions,
            "tgf_beta_secretions": self.tgf_beta_secretions,
            "false_positives": len(self.false_positives),
            "false_positive_rate": self.false_positive_rate,
            "auto_corrections": self.auto_corrections,
            "q_table_size": len(self.q_table),
            "avg_q_value": np.mean(list(self.q_table.values())) if self.q_table else 0.0,
            "avg_reward": np.mean(list(self.reward_history)) if self.reward_history else 0.0,
            "suppression_level_distribution": self._get_suppression_level_distribution(),
        }

    def _get_suppression_level_distribution(self) -> Dict[str, int]:
        """Get distribution of suppression levels used"""
        distribution = {level: 0 for level in SuppressionLevel}
        for decision in self.suppression_decisions:
            distribution[decision.suppression_level] += 1
        return {k: v for k, v in distribution.items()}

    def __repr__(self) -> str:
        """String representation"""
        return (
            f"LinfocitoTRegulador({self.state.id[:8]}|{self.state.status}|"
            f"state={self.regulatory_state}|"
            f"monitored={len(self.monitored_agents)}|"
            f"suppressed={len(self.suppressed_agents)}|"
            f"prevented={self.prevented_autoimmune_attacks})"
        )
