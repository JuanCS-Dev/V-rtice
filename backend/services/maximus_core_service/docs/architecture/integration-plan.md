# MAXIMUS Backend - Integration & Reintegration Plan

**Generated**: 2025-10-14
**Author**: Tactical Executor
**Purpose**: Actionable plan to achieve 100% integration across all backend components

---

## Executive Summary

**Current State**: 45% integrated (18/40 expected connections)
**Target State**: 95% integrated (38/40 connections - 2 deferred to Phase 4)
**Total Effort**: 86 hours (~10.75 working days)
**Critical Path**: 28 hours (3.5 days for P0 gaps)

### Integration Score Progression

- **Current**: 45% (Consciousness ✅, MIP ✅, CPF ❌ isolated)
- **After Phase 1**: 68% (ToM → ESGT connected)
- **After Phase 2**: 82% (CPF operational)
- **After Phase 3**: 95% (All P0+P1 gaps resolved)
- **After Phase 4**: 98% (All enhancements complete)

---

## Phase 1: Social Consciousness Integration (Week 1)

**Objective**: Connect ToM Engine to ESGT Coordinator - unblock social cognition
**Duration**: 3.5 days (28 hours)
**Priority**: P0 - CRITICAL
**Outcome**: Social predictions flow into consciousness global workspace

### Tasks

#### 1.1 ToM → ESGT Connection (GAP-001)
**Effort**: 8 hours
**Owner**: Backend Lead
**Acceptance Criteria**:
- [ ] ToM predictions routed to ESGT workspace candidates
- [ ] High-confidence social predictions trigger workspace broadcast
- [ ] Social content visible in phi calculations
- [ ] Tests validate ToM→ESGT data flow

**Implementation Checklist**:
```python
# File: consciousness/esgt/coordinator.py

# 1. Add ToM subscriber to __init__
def __init__(self, config: ESGTConfig, tom_engine: ToMEngine):
    self.tom_engine = tom_engine
    self.social_predictions: List[SocialPrediction] = []

# 2. Create social workspace evaluation method
async def evaluate_social_workspace_candidates(self) -> List[WorkspaceContent]:
    """Evaluate ToM predictions for workspace broadcast."""
    candidates = []
    for agent_id in self.active_agents:
        prediction = await self.tom_engine.predict_behavior(agent_id)
        if prediction.confidence > 0.7:  # High confidence threshold
            candidates.append(WorkspaceContent(
                type="social_prediction",
                data=prediction,
                salience=prediction.confidence * prediction.impact_score
            ))
    return candidates

# 3. Integrate into broadcast_to_workspace
async def broadcast_to_workspace(self):
    # Existing code...
    social_content = await self.evaluate_social_workspace_candidates()
    all_candidates.extend(social_content)
    # ... rest of broadcast logic
```

**Test Plan**:
```python
# File: tests/integration/test_tom_esgt_integration.py

async def test_high_confidence_social_prediction_triggers_broadcast():
    """ToM prediction with confidence>0.7 should enter workspace."""
    tom = ToMEngine()
    esgt = ESGTCoordinator(config, tom_engine=tom)

    # Setup: Create agent with clear intention
    await tom.infer_intention("agent_001", "help_user", confidence=0.85)

    # Act: Trigger workspace evaluation
    await esgt.evaluate_workspace_candidates()

    # Assert: Social prediction in workspace
    assert any(c.type == "social_prediction" for c in esgt.workspace_content)
    assert esgt.workspace_content[0].data.agent_id == "agent_001"

async def test_low_confidence_social_prediction_ignored():
    """ToM prediction with confidence<0.7 should not enter workspace."""
    # ... similar test with confidence=0.3
    assert not any(c.type == "social_prediction" for c in esgt.workspace_content)
```

**Dependencies**: None (ToM and ESGT both complete)
**Risk**: Low
**Rollback**: Remove ToM calls from ESGT, graceful degradation

---

#### 1.2 Compassion Planner Implementation (GAP-002)
**Effort**: 16 hours
**Owner**: Backend Lead
**Acceptance Criteria**:
- [ ] Compassion Planner generates helping action plans
- [ ] Integrates with ToM for mental state input
- [ ] Outputs compassionate actions with rationale
- [ ] Test coverage ≥90%

**Implementation Checklist**:
```python
# File: compassion/compassion_planner.py

from dataclasses import dataclass
from typing import List, Dict, Any
from compassion.tom_engine import ToMEngine, MentalState

@dataclass
class CompassionateAction:
    """A helping behavior plan."""
    action_type: str  # "reassure", "provide_resource", "reduce_obstacle"
    target_agent: str
    description: str
    expected_impact: float  # 0-1 (suffering reduction)
    reasoning: str
    cost: float  # 0-1 (resource/time cost)

class CompassionPlanner:
    """Generate compassionate action plans based on ToM predictions.

    Aligns with Article III (ethical foundation) and CPF architecture.
    """

    def __init__(self, tom_engine: ToMEngine):
        self.tom_engine = tom_engine
        self.total_plans_generated = 0
        self.logger = StructuredLogger("CompassionPlanner")
        self.metrics = MetricsCollector("CompassionPlanner")

    async def generate_compassionate_action(
        self, agent_id: str, context: Dict[str, Any]
    ) -> List[CompassionateAction]:
        """Generate helping action plans for agent.

        Args:
            agent_id: Target agent to help
            context: Situational context (task, resources, constraints)

        Returns:
            List of ranked compassionate actions
        """
        # 1. Infer mental state
        mental_state = await self.tom_engine.predict_behavior(agent_id)

        # 2. Assess suffering level
        suffering_score = self._evaluate_suffering(mental_state, context)

        if suffering_score < 0.3:
            return []  # No intervention needed

        # 3. Generate action candidates
        candidates = []

        # Reassurance (low cost, moderate impact)
        if mental_state.emotions.get("anxiety", 0) > 0.6:
            candidates.append(CompassionateAction(
                action_type="reassure",
                target_agent=agent_id,
                description=f"Provide emotional support regarding {mental_state.concern}",
                expected_impact=0.4,
                reasoning="High anxiety detected, reassurance may reduce stress",
                cost=0.1
            ))

        # Provide resource (high cost, high impact)
        if mental_state.desires.get("resource_lacking"):
            resource = mental_state.desires["resource_lacking"]
            candidates.append(CompassionateAction(
                action_type="provide_resource",
                target_agent=agent_id,
                description=f"Provide {resource} to enable goal completion",
                expected_impact=0.8,
                reasoning=f"Agent lacks {resource} to achieve goal",
                cost=0.6
            ))

        # Reduce obstacle (moderate cost, high impact)
        if mental_state.obstacles:
            obstacle = mental_state.obstacles[0]
            candidates.append(CompassionateAction(
                action_type="reduce_obstacle",
                target_agent=agent_id,
                description=f"Remove or reduce {obstacle}",
                expected_impact=0.7,
                reasoning=f"Obstacle {obstacle} blocking progress",
                cost=0.4
            ))

        # 4. Rank by impact/cost ratio
        ranked = sorted(candidates, key=lambda a: a.expected_impact / (a.cost + 0.1), reverse=True)

        self.total_plans_generated += len(ranked)
        self.metrics.increment("plans_generated", len(ranked))

        return ranked[:3]  # Top 3 actions

    def _evaluate_suffering(self, mental_state: MentalState, context: Dict) -> float:
        """Quantify agent suffering (0-1)."""
        suffering = 0.0

        # Negative emotions
        suffering += mental_state.emotions.get("anxiety", 0) * 0.3
        suffering += mental_state.emotions.get("frustration", 0) * 0.4
        suffering += mental_state.emotions.get("distress", 0) * 0.5

        # Blocked goals
        if mental_state.goals_blocked > 0:
            suffering += min(mental_state.goals_blocked * 0.2, 0.4)

        # Resource scarcity
        if mental_state.desires.get("resource_lacking"):
            suffering += 0.3

        return min(suffering, 1.0)

    async def prioritize_interventions(
        self, candidates: List[CompassionateAction]
    ) -> List[CompassionateAction]:
        """Rank helping actions by urgency."""
        # For now, simple impact/cost ratio
        # Future: Integrate with MIP for ethical evaluation
        return sorted(candidates, key=lambda a: a.expected_impact / (a.cost + 0.1), reverse=True)

    async def get_status(self) -> Dict[str, Any]:
        """Get planner statistics."""
        return {
            "tool": "CompassionPlanner",
            "total_plans_generated": self.total_plans_generated,
            "status": "operational"
        }

    def __repr__(self) -> str:
        return f"CompassionPlanner(plans={self.total_plans_generated})"
```

**Test Plan**:
```python
# File: compassion/tests/test_compassion_planner.py

@pytest.mark.asyncio
async def test_generate_compassionate_action_high_anxiety():
    """Should generate reassurance action for anxious agent."""
    tom = ToMEngine()
    planner = CompassionPlanner(tom_engine=tom)

    # Setup: Agent with high anxiety
    await tom.infer_emotion("agent_001", "anxiety", 0.8)

    # Act
    actions = await planner.generate_compassionate_action(
        "agent_001", context={"task": "high_stakes"}
    )

    # Assert
    assert len(actions) > 0
    assert actions[0].action_type == "reassure"
    assert actions[0].expected_impact > 0.3

@pytest.mark.asyncio
async def test_generate_compassionate_action_resource_lacking():
    """Should generate resource provision for agent lacking resources."""
    tom = ToMEngine()
    planner = CompassionPlanner(tom_engine=tom)

    # Setup: Agent needs resource
    await tom.infer_desire("agent_001", "resource_lacking", "compute_power")

    # Act
    actions = await planner.generate_compassionate_action(
        "agent_001", context={}
    )

    # Assert
    assert any(a.action_type == "provide_resource" for a in actions)
    assert "compute_power" in actions[0].description

@pytest.mark.asyncio
async def test_no_intervention_for_low_suffering():
    """Should not generate actions if agent is fine."""
    tom = ToMEngine()
    planner = CompassionPlanner(tom_engine=tom)

    # Setup: Agent is neutral/happy
    await tom.infer_emotion("agent_001", "contentment", 0.7)

    # Act
    actions = await planner.generate_compassionate_action(
        "agent_001", context={}
    )

    # Assert
    assert len(actions) == 0  # No intervention needed

@pytest.mark.asyncio
async def test_prioritize_interventions_by_impact_cost():
    """Should rank actions by impact/cost ratio."""
    planner = CompassionPlanner(tom_engine=ToMEngine())

    candidates = [
        CompassionateAction("low_impact", "a", "desc", 0.3, "reason", 0.5),
        CompassionateAction("high_impact", "a", "desc", 0.9, "reason", 0.4),
        CompassionateAction("medium_impact", "a", "desc", 0.6, "reason", 0.3),
    ]

    ranked = await planner.prioritize_interventions(candidates)

    assert ranked[0].action_type == "high_impact"  # 0.9/0.4 = 2.25
    assert ranked[1].action_type == "medium_impact"  # 0.6/0.3 = 2.0

@pytest.mark.asyncio
async def test_get_status():
    """Should return planner statistics."""
    planner = CompassionPlanner(tom_engine=ToMEngine())

    status = await planner.get_status()

    assert status["tool"] == "CompassionPlanner"
    assert status["total_plans_generated"] == 0
```

**Dependencies**: ToM Engine (already complete)
**Risk**: Medium (new component, needs thorough testing)
**Rollback**: Remove component, CPF reverts to inference-only

---

#### 1.3 MIP Validation for Compassionate Actions (GAP-003)
**Effort**: 4 hours
**Owner**: Backend Lead
**Acceptance Criteria**:
- [ ] MIP Decision Arbiter accepts `compassion_action` type
- [ ] Compassionate actions evaluated against 4 frameworks
- [ ] Audit trail includes compassion-specific metadata
- [ ] Integration test validates full flow: ToM → Compassion → MIP → HITL

**Implementation Checklist**:
```python
# File: motor_integridade_processual/decision_arbiter.py

# 1. Add compassion action type
class ActionType(Enum):
    SYSTEM_ACTION = "system_action"
    USER_REQUEST = "user_request"
    COMPASSION_ACTION = "compassion_action"  # NEW

# 2. Add specialized evaluation
async def evaluate_compassion_action(
    self, action: CompassionateAction
) -> EthicalDecision:
    """Evaluate compassionate action against frameworks.

    Compassionate actions prioritize beneficence and non-maleficence.
    """
    # Convert to standard ActionPlan format
    action_plan = ActionPlan(
        action_id=f"compassion_{uuid.uuid4()}",
        action_type=ActionType.COMPASSION_ACTION,
        description=action.description,
        target_agent=action.target_agent,
        expected_outcomes={
            "suffering_reduction": action.expected_impact,
            "resource_cost": action.cost
        },
        stakeholders=[action.target_agent, "system"]
    )

    # Evaluate (prioritize Principialism for medical ethics angle)
    results = await self.evaluate(action_plan)

    # Compassion-specific logic: auto-approve low-cost, high-impact
    if action.cost < 0.3 and action.expected_impact > 0.6:
        results.decision = Decision.APPROVE
        results.reasoning += " [Compassion fast-track: low cost, high benefit]"

    return results

# 3. Update audit trail
async def _log_to_audit_trail(self, decision: EthicalDecision):
    # Existing code...
    metadata = {
        "action_type": decision.action_plan.action_type.value,
    }
    if decision.action_plan.action_type == ActionType.COMPASSION_ACTION:
        metadata["compassion_metadata"] = {
            "suffering_reduction": decision.action_plan.expected_outcomes.get("suffering_reduction"),
            "cost": decision.action_plan.expected_outcomes.get("resource_cost")
        }
    await self.audit_trail.log(decision, metadata)
```

**Test Plan**:
```python
# File: tests/integration/test_compassion_mip_integration.py

@pytest.mark.asyncio
async def test_compassion_action_approved_by_mip():
    """Low-cost, high-impact compassionate action should be approved."""
    tom = ToMEngine()
    planner = CompassionPlanner(tom)
    arbiter = DecisionArbiter()

    # Generate compassionate action
    await tom.infer_emotion("agent_001", "distress", 0.9)
    actions = await planner.generate_compassionate_action("agent_001", {})

    # Evaluate with MIP
    decision = await arbiter.evaluate_compassion_action(actions[0])

    # Assert
    assert decision.decision == Decision.APPROVE
    assert "Compassion fast-track" in decision.reasoning

@pytest.mark.asyncio
async def test_high_cost_compassion_escalated_to_hitl():
    """High-cost compassionate action should escalate to HITL."""
    # ... create high-cost action (cost=0.9)
    decision = await arbiter.evaluate_compassion_action(high_cost_action)

    assert decision.decision == Decision.ESCALATE
    # Verify HITL queue entry
```

**Dependencies**: GAP-002 (Compassion Planner must exist first)
**Risk**: Low (extends existing MIP logic)
**Rollback**: Remove compassion action type from arbiter

---

### Phase 1 Deliverables

✅ **ToM predictions visible in ESGT workspace** (consciousness/esgt/coordinator.py modified)
✅ **Compassion Planner operational** (compassion/compassion_planner.py created, 16 tests passing)
✅ **MIP validates compassionate actions** (motor_integridade_processual/decision_arbiter.py extended)
✅ **Integration tests passing** (tests/integration/test_compassion_flow.py - 5 scenarios)

### Phase 1 Success Metrics

- Integration score increases: 45% → 68%
- 3 new connections: ToM→ESGT, ToM→CompassionPlanner, CompassionPlanner→MIP
- 0 Article III violations (Compassion Planner compliant)
- Test coverage maintained ≥90% on new components

---

## Phase 2: Deontic Reasoning (Weeks 2-3)

**Objective**: Add social obligation reasoning - enable "ought" judgments
**Duration**: 5 days (36 hours)
**Priority**: P1 - HIGH
**Outcome**: System can reason about permissions, prohibitions, obligations in social contexts

### Tasks

#### 2.1 DDL Engine Implementation (GAP-004)
**Effort**: 20 hours
**Owner**: Backend Lead
**Acceptance Criteria**:
- [ ] DDL Engine implements Dynamic Deontic Logic formalization
- [ ] Infers obligations from social context + ToM predictions
- [ ] Resolves conflicts between competing obligations
- [ ] Test coverage ≥90%

**Implementation Checklist**:
```python
# File: compassion/deontic_engine.py

from enum import Enum
from dataclasses import dataclass
from typing import List, Set, Dict, Any
from compassion.tom_engine import ToMEngine

class DeonticModality(Enum):
    """Deontic operators."""
    OBLIGATORY = "O"  # Must do
    PERMITTED = "P"   # May do
    FORBIDDEN = "F"   # Must not do

@dataclass
class DeonticStatement:
    """A deontic proposition."""
    modality: DeonticModality
    action: str
    agent: str
    context: Dict[str, Any]
    confidence: float  # 0-1
    reasoning: str

class DeonticEngine:
    """Dynamic Deontic Logic engine for social obligation reasoning.

    Implements DDL formalization:
    - O(φ): φ is obligatory
    - P(φ): φ is permitted
    - F(φ): φ is forbidden

    Axioms:
    - O(φ) → P(φ)  (obligatory implies permitted)
    - F(φ) ↔ ¬P(φ) (forbidden iff not permitted)
    - O(φ) ↔ F(¬φ) (obligatory iff omission forbidden)
    """

    def __init__(self, tom_engine: ToMEngine):
        self.tom_engine = tom_engine
        self.social_norms: Dict[str, DeonticStatement] = {}
        self.logger = StructuredLogger("DeonticEngine")
        self.metrics = MetricsCollector("DeonticEngine")

    async def infer_obligations(
        self, agent_id: str, context: Dict[str, Any]
    ) -> List[DeonticStatement]:
        """Infer social obligations for agent in context.

        Args:
            agent_id: Agent to reason about
            context: Situational context (role, relationships, promises)

        Returns:
            List of deontic statements (obligations, permissions, prohibitions)
        """
        obligations = []

        # 1. Get mental state from ToM
        mental_state = await self.tom_engine.predict_behavior(agent_id)

        # 2. Check role-based obligations
        if context.get("role") == "caregiver":
            obligations.append(DeonticStatement(
                modality=DeonticModality.OBLIGATORY,
                action="provide_care",
                agent=agent_id,
                context=context,
                confidence=0.9,
                reasoning="Caregiver role entails care obligation"
            ))

        # 3. Check promise-based obligations
        if mental_state.commitments:
            for commitment in mental_state.commitments:
                obligations.append(DeonticStatement(
                    modality=DeonticModality.OBLIGATORY,
                    action=f"fulfill_{commitment}",
                    agent=agent_id,
                    context=context,
                    confidence=0.95,
                    reasoning=f"Agent committed to {commitment}"
                ))

        # 4. Check harm prevention (universal obligation)
        if context.get("harm_risk"):
            obligations.append(DeonticStatement(
                modality=DeonticModality.OBLIGATORY,
                action="prevent_harm",
                agent=agent_id,
                context=context,
                confidence=1.0,
                reasoning="Universal obligation to prevent harm"
            ))

        # 5. Infer permissions (anything not forbidden)
        permitted_actions = self._infer_permissions(context)
        for action in permitted_actions:
            obligations.append(DeonticStatement(
                modality=DeonticModality.PERMITTED,
                action=action,
                agent=agent_id,
                context=context,
                confidence=0.7,
                reasoning="No prohibition detected"
            ))

        return obligations

    def _infer_permissions(self, context: Dict) -> Set[str]:
        """Infer permitted actions (default: everything not explicitly forbidden)."""
        all_actions = {"communicate", "request_help", "decline", "negotiate"}
        forbidden = set(context.get("forbidden_actions", []))
        return all_actions - forbidden

    async def resolve_conflicts(
        self, obligations: List[DeonticStatement]
    ) -> DeonticStatement:
        """Resolve conflicts between competing obligations.

        Priority: Harm prevention > Promises > Role obligations > Permissions
        """
        if not obligations:
            return None

        # Filter by priority
        harm_prevention = [o for o in obligations if "prevent_harm" in o.action]
        if harm_prevention:
            return harm_prevention[0]  # Highest priority

        promises = [o for o in obligations if "fulfill_" in o.action]
        if promises:
            return max(promises, key=lambda o: o.confidence)

        role_obligations = [o for o in obligations if o.modality == DeonticModality.OBLIGATORY]
        if role_obligations:
            return max(role_obligations, key=lambda o: o.confidence)

        # Default: highest confidence
        return max(obligations, key=lambda o: o.confidence)

    async def check_permission(self, agent_id: str, action: str, context: Dict) -> bool:
        """Check if action is permitted for agent in context."""
        obligations = await self.infer_obligations(agent_id, context)

        # Forbidden if any F(action)
        if any(o.modality == DeonticModality.FORBIDDEN and o.action == action for o in obligations):
            return False

        # Permitted if P(action) or O(action)
        if any(o.action == action and o.modality in [DeonticModality.PERMITTED, DeonticModality.OBLIGATORY] for o in obligations):
            return True

        # Default: permitted (permissive logic)
        return True

    async def get_status(self) -> Dict[str, Any]:
        return {
            "tool": "DeonticEngine",
            "social_norms_loaded": len(self.social_norms),
            "status": "operational"
        }

    def __repr__(self) -> str:
        return f"DeonticEngine(norms={len(self.social_norms)})"
```

**Test Plan**:
```python
# File: compassion/tests/test_deontic_engine.py

@pytest.mark.asyncio
async def test_infer_obligations_caregiver_role():
    """Caregiver role should entail care obligation."""
    tom = ToMEngine()
    ddl = DeonticEngine(tom)

    obligations = await ddl.infer_obligations(
        "agent_001",
        context={"role": "caregiver"}
    )

    assert any(o.modality == DeonticModality.OBLIGATORY and o.action == "provide_care" for o in obligations)

@pytest.mark.asyncio
async def test_promise_creates_obligation():
    """Agent promise should create obligation."""
    tom = ToMEngine()
    ddl = DeonticEngine(tom)

    # Setup: Agent made promise
    await tom.record_commitment("agent_001", "deliver_report")

    obligations = await ddl.infer_obligations("agent_001", {})

    assert any("fulfill_deliver_report" in o.action for o in obligations)

@pytest.mark.asyncio
async def test_harm_prevention_highest_priority():
    """Harm prevention should override other obligations."""
    ddl = DeonticEngine(ToMEngine())

    obligations = [
        DeonticStatement(DeonticModality.OBLIGATORY, "fulfill_promise", "a", {}, 0.9, "Promise"),
        DeonticStatement(DeonticModality.OBLIGATORY, "prevent_harm", "a", {}, 1.0, "Harm prevention"),
    ]

    resolved = await ddl.resolve_conflicts(obligations)

    assert resolved.action == "prevent_harm"

@pytest.mark.asyncio
async def test_check_permission_forbidden_action():
    """Forbidden action should not be permitted."""
    ddl = DeonticEngine(ToMEngine())

    permitted = await ddl.check_permission(
        "agent_001",
        "reveal_secret",
        context={"forbidden_actions": ["reveal_secret"]}
    )

    assert permitted is False
```

**Dependencies**: ToM Engine
**Risk**: Medium (complex logic, needs validation)
**Rollback**: Remove DDL Engine, CPF loses obligation reasoning

---

#### 2.2 Metacognition Monitor Enhancement (GAP-005)
**Effort**: 12 hours
**Owner**: Backend Lead
**Acceptance Criteria**:
- [ ] Detects cognitive biases (confirmation bias, anchoring, availability heuristic)
- [ ] Triggers strategy shifts when reasoning quality drops
- [ ] Integrates with ESGT for metacognitive workspace content
- [ ] Test coverage ≥90%

**Implementation Checklist**:
```python
# File: consciousness/metacognition/monitor.py (expand existing)

class BiasType(Enum):
    CONFIRMATION_BIAS = "confirmation_bias"
    ANCHORING = "anchoring"
    AVAILABILITY_HEURISTIC = "availability"
    OVERCONFIDENCE = "overconfidence"

@dataclass
class BiasDetection:
    bias_type: BiasType
    severity: float  # 0-1
    evidence: str
    recommendation: str

class MetacognitionMonitor:
    """Self-monitoring and self-regulation for reasoning quality."""

    def __init__(self, esgt_coordinator):
        self.esgt = esgt_coordinator
        self.reasoning_history: List[Dict] = []
        self.bias_detections: List[BiasDetection] = []
        self.logger = StructuredLogger("MetacognitionMonitor")

    async def monitor_reasoning_quality(
        self, decision: Dict[str, Any]
    ) -> float:
        """Evaluate reasoning quality (0-1)."""
        quality = 1.0

        # Check for biases
        biases = await self.detect_cognitive_bias(decision)
        for bias in biases:
            quality -= bias.severity * 0.2

        # Check for logical consistency
        if not self._check_logical_consistency(decision):
            quality -= 0.3

        # Check evidence quality
        evidence_score = self._evaluate_evidence(decision.get("evidence", []))
        quality = quality * evidence_score

        return max(quality, 0.0)

    async def detect_cognitive_bias(
        self, decision: Dict[str, Any]
    ) -> List[BiasDetection]:
        """Identify reasoning biases."""
        biases = []

        # 1. Confirmation bias: only seeking confirming evidence
        if decision.get("evidence"):
            confirming = sum(1 for e in decision["evidence"] if e["supports_hypothesis"])
            total = len(decision["evidence"])
            if confirming / total > 0.9:  # >90% confirming
                biases.append(BiasDetection(
                    bias_type=BiasType.CONFIRMATION_BIAS,
                    severity=0.7,
                    evidence=f"{confirming}/{total} evidence confirms hypothesis",
                    recommendation="Seek disconfirming evidence"
                ))

        # 2. Anchoring: overreliance on first information
        if len(self.reasoning_history) > 5:
            recent_decisions = self.reasoning_history[-5:]
            first_value = recent_decisions[0].get("initial_estimate")
            if all(abs(d.get("estimate", 0) - first_value) < 0.1 for d in recent_decisions):
                biases.append(BiasDetection(
                    bias_type=BiasType.ANCHORING,
                    severity=0.6,
                    evidence="Estimates clustered around initial anchor",
                    recommendation="Re-evaluate from first principles"
                ))

        # 3. Availability heuristic: overweighting recent events
        if decision.get("risk_assessment"):
            recent_events = self._get_recent_similar_events()
            if len(recent_events) > 3 and all(e["outcome"] == "negative" for e in recent_events):
                biases.append(BiasDetection(
                    bias_type=BiasType.AVAILABILITY_HEURISTIC,
                    severity=0.5,
                    evidence="Recent negative events may inflate risk perception",
                    recommendation="Consider base rates, not just recent cases"
                ))

        self.bias_detections.extend(biases)
        return biases

    async def trigger_strategy_shift(self, current_strategy: str) -> str:
        """Change reasoning strategy when stuck."""
        # If same strategy failing repeatedly, switch
        recent_failures = [d for d in self.reasoning_history[-10:] if d.get("success") is False]

        if len(recent_failures) > 5:
            if current_strategy == "deductive":
                return "abductive"  # Switch to inference to best explanation
            elif current_strategy == "abductive":
                return "analogical"  # Switch to case-based reasoning
            else:
                return "deductive"  # Return to first principles

        return current_strategy  # Keep current

    def _check_logical_consistency(self, decision: Dict) -> bool:
        """Check for logical contradictions."""
        # Simplified: check if conclusion follows from premises
        premises = decision.get("premises", [])
        conclusion = decision.get("conclusion")

        # Basic contradiction check (placeholder for full logic engine)
        if "not" in conclusion and any(conclusion.replace("not ", "") in p for p in premises):
            return False  # Contradiction

        return True

    def _evaluate_evidence(self, evidence: List[Dict]) -> float:
        """Score evidence quality."""
        if not evidence:
            return 0.5  # Neutral

        # Score based on: recency, source reliability, independence
        total_score = 0.0
        for e in evidence:
            score = 0.0
            score += e.get("recency", 0.5) * 0.3
            score += e.get("reliability", 0.5) * 0.5
            score += e.get("independence", 0.5) * 0.2
            total_score += score

        return total_score / len(evidence)
```

**Test Plan**: Similar structure to DDL tests (bias detection, strategy shift, quality scoring)

**Dependencies**: ESGT Coordinator
**Risk**: Low (extends existing stub)
**Rollback**: Revert to basic monitoring

---

#### 2.3 Redis Cache Deployment (GAP-006)
**Effort**: 4 hours
**Owner**: DevOps / Backend Lead
**Acceptance Criteria**:
- [ ] Redis deployed to K8s cluster
- [ ] ToM Engine using Redis for prediction caching
- [ ] Cache hit rate >60% for repeated queries
- [ ] Prometheus metrics for cache performance

**Implementation Checklist**:
```yaml
# File: k8s/redis-deployment.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: maximus
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "200m"
---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: maximus
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
```

```python
# File: compassion/tom_engine.py (add caching)

import redis.asyncio as redis

class ToMEngine:
    def __init__(self, redis_url: str = "redis://redis:6379"):
        self.redis = redis.from_url(redis_url)
        # ... existing init

    async def predict_behavior(self, agent_id: str) -> MentalState:
        # Check cache first
        cache_key = f"tom:prediction:{agent_id}"
        cached = await self.redis.get(cache_key)

        if cached:
            self.metrics.increment("cache_hit")
            return MentalState.from_json(cached)

        # Cache miss - compute
        self.metrics.increment("cache_miss")
        prediction = await self._compute_prediction(agent_id)

        # Store in cache (TTL: 60 seconds)
        await self.redis.setex(cache_key, 60, prediction.to_json())

        return prediction
```

**Test Plan**: Deploy to staging, run load test, verify cache hit rate

**Dependencies**: Kubernetes cluster
**Risk**: Low (standard Redis deployment)
**Rollback**: Remove Redis, ToM falls back to direct computation

---

### Phase 2 Deliverables

✅ **DDL Engine operational** (compassion/deontic_engine.py created, 12 tests passing)
✅ **Metacognition Monitor enhanced** (consciousness/metacognition/monitor.py expanded, bias detection working)
✅ **Redis cache deployed** (K8s manifests applied, ToM using cache, >60% hit rate)

### Phase 2 Success Metrics

- Integration score: 68% → 82%
- 2 new connections: ToM→DDL, Metacognition→ESGT
- Performance improvement: ToM latency reduced 40% (cache)
- Test coverage maintained ≥90%

---

## Phase 3: Production Hardening (Week 4)

**Objective**: Finalize production readiness for all P0+P1 components
**Duration**: 2 days (14 hours)
**Priority**: P2 - MEDIUM
**Outcome**: All components Article IV compliant

### Tasks

#### 3.1 Governance Engine Hardening (GAP-007)
**Effort**: 6 hours
**Owner**: Backend Lead
**Acceptance Criteria**:
- [ ] POC warning removed from docstring
- [ ] Error handling production-grade (no unhandled exceptions)
- [ ] Test coverage ≥90%
- [ ] Observability added (logging + metrics)

**Implementation Checklist**:
- Remove `⚠️ POC IMPLEMENTATION` from docstring
- Add try-except blocks with specific exception handling
- Add Prometheus metrics for decision throughput
- Expand test suite to 90% coverage
- Add structured logging for all operations

**Dependencies**: Existing POC must be stable
**Risk**: Low (already functional)
**Rollback**: Revert to POC if issues found

---

#### 3.2 Integration Testing Suite
**Effort**: 8 hours
**Owner**: Backend Lead
**Acceptance Criteria**:
- [ ] End-to-end tests for all critical flows
- [ ] Tests cover: ToM→ESGT→MCEA, ToM→Compassion→MIP→HITL, DDL→ToM
- [ ] Performance tests (latency <100ms for ToM predictions)
- [ ] Chaos engineering tests (component failures)

**Test Scenarios**:
1. **Social Consciousness Flow**: ToM detects distress → ESGT broadcasts → MCEA adjusts arousal → Compassion plans action → MIP validates → HITL escalates
2. **Deontic Reasoning**: DDL infers obligation → ToM updates mental state → Compassion generates helping action
3. **Metacognitive Control**: Bias detected → Strategy shift → ESGT workspace updated
4. **Failure Modes**: Redis down (cache miss), ToM confidence low (no broadcast), MIP reject (HITL escalation)

**Dependencies**: All P0+P1 components complete
**Risk**: Low
**Rollback**: N/A (test-only)

---

### Phase 3 Deliverables

✅ **Governance Engine production-ready** (POC warning removed, 90% coverage)
✅ **Integration test suite complete** (tests/integration/ - 15 scenarios, all passing)

### Phase 3 Success Metrics

- Integration score: 82% → 95%
- 0 Article IV violations (all production-ready)
- Performance validated (<100ms latency)
- Failure modes tested and handled gracefully

---

## Phase 4: Advanced Enhancements (Month 2+)

**Objective**: Add nice-to-have features for advanced capabilities
**Duration**: 3 days (22 hours)
**Priority**: P2 - LOW
**Outcome**: CBR learning, full metacognition

### Tasks

#### 4.1 Case-Based Reasoning Engine (GAP-008)
**Effort**: 16 hours
**Owner**: Backend Lead
**Acceptance Criteria**:
- [ ] CBR retrieves similar past social episodes
- [ ] Adapts past cases for new context
- [ ] ToM improves predictions using CBR
- [ ] Test coverage ≥90%

**Implementation**: (Similar structure to DDL - retrieval, adaptation, learning)

**Dependencies**: Social Memory
**Risk**: Medium (complex ML logic)
**Rollback**: Remove CBR, ToM reverts to static inference

---

#### 4.2 Full Metacognitive Control Loop
**Effort**: 6 hours
**Owner**: Backend Lead
**Acceptance Criteria**:
- [ ] Metacognition triggers ESGT strategy changes
- [ ] Bias corrections logged and validated
- [ ] Self-regulation metrics tracked

**Dependencies**: Phase 2.2 (Metacognition Monitor)
**Risk**: Low
**Rollback**: Disable control loop, keep monitoring only

---

### Phase 4 Deliverables

✅ **CBR Engine operational**
✅ **Full metacognitive control active**

### Phase 4 Success Metrics

- Integration score: 95% → 98%
- ToM prediction accuracy improves 15% (CBR learning)
- Bias detection rate >80%

---

## Execution Gantt Chart

```
Week 1: [=================ToM→ESGT===][========CompassionPlanner=========][==MIP==]
Week 2: [============DDL Engine==============][======Metacognition======]
Week 3: [==Redis==][=======================Integration Testing=======================]
Week 4: [==Gov Hardening==][===Integration Tests===]
Month 2: [=================CBR Engine==================][==Metacog Control==]
```

---

## Resource Requirements

**Personnel**:
- 1 Backend Lead (full-time, 4 weeks)
- 1 DevOps Engineer (part-time for Redis deployment, 4 hours)
- 1 QA Engineer (part-time for integration testing, 16 hours)

**Infrastructure**:
- Staging Kubernetes cluster (for Redis deployment validation)
- PostgreSQL database (already provisioned)
- Prometheus monitoring (already provisioned)

**External Dependencies**:
- None (all components internal to MAXIMUS)

---

## Risk Management

### High-Risk Tasks

1. **DDL Engine** (GAP-004) - Complex logic, needs validation
   - **Mitigation**: Extensive unit tests, formal logic review
   - **Fallback**: Defer to Phase 4 if issues found

2. **ToM → ESGT Integration** (GAP-001) - Critical path, blocks other work
   - **Mitigation**: Start with simple integration, iterate
   - **Fallback**: Keep ToM isolated if ESGT stability compromised

### Medium-Risk Tasks

1. **Compassion Planner** (GAP-002) - New component, untested
   - **Mitigation**: Start with simple heuristics, expand incrementally
   - **Fallback**: Remove if performance unacceptable

2. **CBR Engine** (GAP-008) - Advanced ML, may be complex
   - **Mitigation**: Use simple k-NN for MVP, enhance later
   - **Fallback**: Defer indefinitely (not critical)

### Low-Risk Tasks

- All others (MIP extension, Redis deployment, Governance hardening)

---

## Success Criteria

### Phase 1 Complete
- [ ] ToM predictions visible in ESGT workspace
- [ ] Compassion Planner generates ≥3 helping actions per distressed agent
- [ ] MIP evaluates compassionate actions with >90% accuracy
- [ ] Integration score ≥68%
- [ ] All P0 tests passing

### Phase 2 Complete
- [ ] DDL infers obligations with >85% accuracy (validated against ethics test cases)
- [ ] Metacognition detects ≥3 bias types
- [ ] Redis cache hit rate >60%
- [ ] Integration score ≥82%
- [ ] All P0+P1 tests passing

### Phase 3 Complete
- [ ] Governance Engine POC warning removed
- [ ] End-to-end integration tests passing (15 scenarios)
- [ ] Performance validated (<100ms ToM latency)
- [ ] Integration score ≥95%
- [ ] 0 Article IV violations

### Phase 4 Complete (Optional)
- [ ] CBR improves ToM accuracy by ≥15%
- [ ] Metacognitive control loop active
- [ ] Integration score ≥98%

---

## Rollback Plan

### Per-Component Rollback
Each component has independent rollback (see task checklists above):
- **ToM→ESGT**: Remove ToM calls from ESGT
- **Compassion Planner**: Delete component, CPF inference-only
- **DDL**: Remove engine, no obligation reasoning
- **Metacognition**: Revert to basic monitoring
- **Redis**: Remove deployment, direct computation
- **CBR**: Delete engine, static ToM

### Full Rollback (Emergency)
If critical issues found:
1. Revert all Phase commits
2. Redeploy last stable version (pre-integration)
3. Document issues in `docs/architecture/rollback-report.md`

**Trigger**: >3 P0 bugs in production OR integration score drops below 40%

---

## Monitoring & Validation

### Key Metrics (Prometheus)

**Consciousness**:
- `esgt_workspace_ignitions_total{type="social"}` - Social content broadcasts
- `tom_predictions_total` - ToM inference count
- `mcea_arousal_level` - Arousal response to social events

**CPF**:
- `compassion_plans_generated_total` - Helping actions created
- `ddl_obligations_inferred_total` - Deontic statements
- `tom_cache_hit_rate` - Redis performance

**MIP**:
- `mip_compassion_evaluations_total{decision}` - Approve/Reject/Escalate
- `mip_framework_agreement_rate` - Consensus among frameworks

**Integration**:
- `integration_score` - Overall connectivity (target: 0.95)
- `component_coupling` - Dependency health

### Dashboards

Create Grafana dashboards:
1. **Social Consciousness Dashboard**: ToM → ESGT → Compassion flow
2. **CPF Health Dashboard**: DDL, ToM, Compassion, Metacognition
3. **Integration Health**: Connection status, test pass rates

---

## Communication Plan

### Stakeholder Updates

**Weekly**: Email update to leadership
- Phase progress (% complete)
- Integration score delta
- Blockers / risks

**Daily**: Slack standup in #maximus-backend
- Yesterday: tasks completed
- Today: tasks in progress
- Blockers

**Milestone**: Demo session
- End of Phase 1: Demo compassionate action flow
- End of Phase 2: Demo deontic reasoning
- End of Phase 3: Full integration demo

---

## Conclusion

This integration plan transforms MAXIMUS from **45% integrated** to **95% integrated** in 4 weeks (86 hours total effort).

**Critical Path**: Phase 1 (ToM→ESGT + Compassion) - unblocks all downstream work
**Highest ROI**: ToM→ESGT integration (8 hours, massive capability unlock)
**Recommended Execution**: Sequential phases (Phase 1 → Phase 2 → Phase 3), Phase 4 optional

**Expected Outcome**: Fully functional social cognition system with compassionate action generation, ethical validation, and deontic reasoning - all integrated into consciousness global workspace.

---

**End of Integration Plan**

Generated by Tactical Executor on 2025-10-14
Total Effort Estimated: 86 hours
Critical Path: 28 hours
Target Integration Score: 95%
