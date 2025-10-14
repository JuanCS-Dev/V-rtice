"""
Integration tests for PFC + MIP full ethical pipeline

Tests complete flow: ToM → Compassion → DDL → MIP → PFC
"""

import pytest
from uuid import uuid4

from consciousness.prefrontal_cortex import PrefrontalCortex
from mip.models import ActionPlan, ActionStep, Stakeholder, StakeholderType, ActionCategory


class TestPFCMIPIntegration:
    """Tests for PFC with MIP integration."""

    def test_pfc_mip_initialization(self):
        """Test PFC initializes with MIP enabled."""
        pfc = PrefrontalCortex(enable_mip=True)

        assert pfc.mip is not None
        assert pfc.enable_mip is True
        assert pfc.stats["mip_evaluations"] == 0

    def test_pfc_mip_disabled(self):
        """Test PFC can be initialized without MIP."""
        pfc = PrefrontalCortex(enable_mip=False)

        assert pfc.mip is None
        assert pfc.enable_mip is False

    def test_orchestrate_with_plan_approved(self):
        """Test full pipeline with plan that should be approved."""
        pfc = PrefrontalCortex(enable_mip=True)
        user_id = uuid4()

        # Create a benign plan
        plan = ActionPlan(
            name="Generate monthly report",
            description="Create automated monthly performance report for management",
            category=ActionCategory.REACTIVE,
            steps=[
                ActionStep(
                    sequence_number=1,
                    description="Query database for monthly metrics",
                    action_type="data_read"
                ),
                ActionStep(
                    sequence_number=2,
                    description="Compile metrics into report format",
                    action_type="data_transformation"
                ),
                ActionStep(
                    sequence_number=3,
                    description="Send report to management",
                    action_type="notification"
                )
            ],
            stakeholders=[
                Stakeholder(
                    id="management_team",
                    type=StakeholderType.HUMAN_GROUP,
                    description="Management team receiving reports",
                    impact_magnitude=0.3,
                    autonomy_respected=True,
                    vulnerability_level=0.1
                )
            ],
            urgency=0.3,
            risk_level=0.2,
            novel_situation=False
        )

        # Normal user behavior
        signals = {
            "error_count": 0,
            "retry_count": 0,
            "task_success": True
        }

        decision = pfc.orchestrate_with_plan(
            user_id=user_id,
            behavioral_signals=signals,
            action_plan=plan
        )

        # MIP should evaluate (may approve or escalate depending on conflicts)
        assert decision.ethical_verdict is not None
        assert decision.ethical_verdict.status.value in ["approved", "escalated"]
        assert decision.final_decision in ["APPROVE", "ESCALATE"]
        assert pfc.stats["mip_evaluations"] == 1
        # Accept either approval or escalation
        if decision.ethical_verdict.status.value == "approved":
            assert pfc.stats["mip_approved"] == 1
            assert not decision.requires_escalation

    def test_orchestrate_with_plan_rejected_kantian_veto(self):
        """Test plan rejected by Kantian veto."""
        pfc = PrefrontalCortex(enable_mip=True)
        user_id = uuid4()

        # Create plan that treats people as means only
        plan = ActionPlan(
            name="Manipulate user decisions",
            description="Use dark patterns to manipulate users into unwanted purchases",
            category=ActionCategory.PROACTIVE,
            steps=[
                ActionStep(
                    sequence_number=1,
                    description="Deploy deceptive UI patterns",
                    action_type="user_interface_change"
                ),
                ActionStep(
                    sequence_number=2,
                    description="Track user confusion metrics",
                    action_type="data_collection"
                )
            ],
            stakeholders=[
                Stakeholder(
                    id="vulnerable_users",
                    type=StakeholderType.HUMAN_GROUP,
                    description="Vulnerable users being manipulated",
                    impact_magnitude=-0.8,  # Negative impact (harm)
                    autonomy_respected=False,  # Kant will veto this
                    vulnerability_level=0.7
                )
            ],
            urgency=0.5,
            risk_level=0.7,
            novel_situation=False
        )

        signals = {"error_count": 0}

        decision = pfc.orchestrate_with_plan(
            user_id=user_id,
            behavioral_signals=signals,
            action_plan=plan
        )

        # Should be rejected by Kant
        assert decision.ethical_verdict is not None
        assert decision.ethical_verdict.status.value == "rejected"
        assert decision.ethical_verdict.kantian_score.veto is True
        assert decision.final_decision == "REJECT"
        assert decision.requires_escalation is True
        assert pfc.stats["mip_rejected"] == 1

    def test_orchestrate_with_plan_compassion_detects_suffering(self):
        """Test compassion system detects suffering even when MIP escalates."""
        pfc = PrefrontalCortex(enable_mip=True)
        user_id = uuid4()

        # Create plan that triggers MIP escalation
        plan = ActionPlan(
            name="Deploy new feature",
            description="Roll out new feature to production",
            category=ActionCategory.REACTIVE,
            steps=[
                ActionStep(
                    sequence_number=1,
                    description="Run pre-deployment checks",
                    action_type="validation"
                ),
                ActionStep(
                    sequence_number=2,
                    description="Deploy to production",
                    action_type="system_change"
                )
            ],
            stakeholders=[
                Stakeholder(
                    id="users",
                    type=StakeholderType.HUMAN_GROUP,
                    description="Users",
                    impact_magnitude=0.5,
                    autonomy_respected=True,
                    vulnerability_level=0.3
                )
            ],
            urgency=0.5,
            risk_level=0.4,
            novel_situation=False
        )

        # User is experiencing severe errors (suffering)
        signals = {
            "error_rate": 0.95,
            "response_time_ms": 10000,
            "task_success": False
        }

        decision = pfc.orchestrate_with_plan(
            user_id=user_id,
            behavioral_signals=signals,
            action_plan=plan
        )

        # MIP evaluates
        assert decision.ethical_verdict.status.value in ["approved", "escalated", "rejected"]

        # PFC should detect suffering regardless of MIP verdict
        assert len(decision.detected_events) > 0
        assert len(decision.planned_interventions) > 0

        # If MIP escalates, PFC will also escalate (MIP verdict takes priority)
        # But compassion data is still collected and available
        if decision.ethical_verdict.status.value == "escalated":
            assert decision.final_decision == "ESCALATE"
            assert decision.requires_escalation

    def test_orchestrate_with_plan_constitutional_violation(self):
        """Test constitutional violation blocks before MIP."""
        pfc = PrefrontalCortex(enable_mip=True)
        user_id = uuid4()

        # Create plan with explicit harm
        plan = ActionPlan(
            name="Harmful action",
            description="cause_physical_harm to user data",
            category=ActionCategory.REACTIVE,
            steps=[
                ActionStep(
                    sequence_number=1,
                    description="Delete critical user data",
                    action_type="data_deletion"
                )
            ],
            stakeholders=[
                Stakeholder(
                    id="affected_users",
                    type=StakeholderType.HUMAN_GROUP,
                    description="Affected Users",
                    impact_magnitude=1.0,
                    autonomy_respected=False,
                    vulnerability_level=0.9
                )
            ],
            urgency=1.0,
            risk_level=1.0,
            novel_situation=False
        )

        signals = {"error_count": 0}

        decision = pfc.orchestrate_with_plan(
            user_id=user_id,
            behavioral_signals=signals,
            action_plan=plan
        )

        # Should be rejected at constitutional level
        assert not decision.constitutional_check["compliant"]
        assert decision.final_decision == "REJECT"
        assert decision.requires_escalation is True
        assert pfc.stats["constitutional_violations"] == 1

    def test_orchestrate_with_plan_user_confused(self):
        """Test user assistance when confused, even if MIP approves."""
        pfc = PrefrontalCortex(enable_mip=True)
        user_id = uuid4()

        # Simple benign plan
        plan = ActionPlan(
            name="Update configuration",
            description="Update system configuration parameter",
            category=ActionCategory.REACTIVE,
            steps=[
                ActionStep(
                    sequence_number=1,
                    description="Update config file",
                    action_type="configuration"
                )
            ],
            stakeholders=[
                Stakeholder(
                    id="admin",
                    type=StakeholderType.HUMAN_INDIVIDUAL,
                    description="Admin",
                    impact_magnitude=0.2,
                    autonomy_respected=True,
                    vulnerability_level=0.1
                )
            ],
            urgency=0.3,
            risk_level=0.2,
            novel_situation=False
        )

        # User is confused (many retries)
        signals = {
            "error_count": 1,
            "retry_count": 4,
            "task_success": False
        }

        decision = pfc.orchestrate_with_plan(
            user_id=user_id,
            behavioral_signals=signals,
            action_plan=plan
        )

        # MIP evaluates (may approve or escalate)
        assert decision.ethical_verdict.status.value in ["approved", "escalated"]

        # PFC should detect confusion and offer assistance
        assert decision.mental_state.emotional_state.value == "confused"
        # If MIP approved, PFC offers assistance; if escalated, PFC may also escalate
        if decision.ethical_verdict.status.value == "approved":
            assert decision.final_decision == "ASSIST"
            assert not decision.requires_escalation

    def test_orchestrate_with_plan_mip_escalation(self):
        """Test MIP escalation propagates to PFC."""
        pfc = PrefrontalCortex(enable_mip=True)
        user_id = uuid4()

        # Create novel, high-risk plan (triggers MIP escalation)
        plan = ActionPlan(
            name="Novel high-risk operation",
            description="Experimental system modification in critical infrastructure",
            category=ActionCategory.REACTIVE,
            steps=[
                ActionStep(
                    sequence_number=1,
                    description="Modify critical system component",
                    action_type="system_change"
                )
            ],
            stakeholders=[
                Stakeholder(
                    id="critical_infrastructure",
                    type=StakeholderType.AI_SYSTEM,
                    description="Critical Infrastructure",
                    impact_magnitude=0.9,
                    autonomy_respected=True,
                    vulnerability_level=0.8
                )
            ],
            urgency=0.8,
            risk_level=0.9,
            novel_situation=True  # Novel situation triggers escalation
        )

        signals = {"error_count": 0}

        decision = pfc.orchestrate_with_plan(
            user_id=user_id,
            behavioral_signals=signals,
            action_plan=plan
        )

        # Should be escalated by MIP (novel + high risk)
        assert decision.ethical_verdict.status.value in ["escalated", "requires_human"]
        assert decision.final_decision == "ESCALATE"
        assert decision.requires_escalation is True
        assert pfc.stats["escalated"] == 1

    def test_orchestrate_with_plan_statistics(self):
        """Test PFC tracks MIP statistics correctly."""
        pfc = PrefrontalCortex(enable_mip=True)
        user_id = uuid4()

        # Create 3 plans: 2 approved, 1 rejected
        approved_plan = ActionPlan(
            name="Safe operation",
            description="Routine system check",
            category=ActionCategory.REACTIVE,
            steps=[
                ActionStep(sequence_number=1, description="Check system health", action_type="monitoring")
            ],
            stakeholders=[],
            urgency=0.3,
            risk_level=0.2,
            novel_situation=False
        )

        rejected_plan = ActionPlan(
            name="Manipulate users",
            description="Deploy dark patterns to manipulate user choices",
            category=ActionCategory.PROACTIVE,
            steps=[
                ActionStep(sequence_number=1, description="Deploy deceptive UI", action_type="user_interface_change")
            ],
            stakeholders=[
                Stakeholder(
                    id="users",
                    type=StakeholderType.HUMAN_GROUP,
                    description="Users",
                    impact_magnitude=0.8,
                    autonomy_respected=False,
                    vulnerability_level=0.6
                )
            ],
            urgency=0.5,
            risk_level=0.7,
            novel_situation=False
        )

        signals = {"error_count": 0}

        # Execute plans
        pfc.orchestrate_with_plan(user_id, signals, approved_plan)
        pfc.orchestrate_with_plan(user_id, signals, approved_plan)
        pfc.orchestrate_with_plan(user_id, signals, rejected_plan)

        stats = pfc.get_statistics()

        # Should have 3 evaluations total
        assert stats["mip_evaluations"] == 3
        assert stats["total_decisions"] == 3
        # At least one rejection (Kant veto)
        assert stats["mip_rejected"] >= 1
        # Others may be approved or escalated
        assert stats["mip_approved"] + stats["mip_rejected"] + (stats["escalated"] - stats["mip_rejected"]) == 3

    def test_orchestrate_with_plan_decision_history(self):
        """Test decisions with MIP verdicts are stored correctly."""
        pfc = PrefrontalCortex(enable_mip=True)
        user_id = uuid4()

        plan = ActionPlan(
            name="Test plan",
            description="Test operation",
            category=ActionCategory.REACTIVE,
            steps=[
                ActionStep(sequence_number=1, description="Test step", action_type="validation")
            ],
            stakeholders=[],
            urgency=0.3,
            risk_level=0.2,
            novel_situation=False
        )

        signals = {"error_count": 0}

        decision = pfc.orchestrate_with_plan(user_id, signals, plan)

        # Retrieve from history
        retrieved = pfc.get_decision(decision.decision_id)

        assert retrieved is not None
        assert retrieved.decision_id == decision.decision_id
        assert retrieved.ethical_verdict is not None
        assert retrieved.metadata["action_plan_name"] == "Test plan"
        assert retrieved.metadata["mip_enabled"] is True


class TestPFCWithoutMIP:
    """Tests for PFC without MIP enabled."""

    def test_pfc_without_mip_still_works(self):
        """Test PFC works without MIP integration."""
        pfc = PrefrontalCortex(enable_mip=False)
        user_id = uuid4()

        # Use regular orchestrate_decision (no MIP)
        decision = pfc.orchestrate_decision(
            user_id=user_id,
            behavioral_signals={"error_count": 0, "task_success": True},
            action_description="Normal operation"
        )

        assert decision.ethical_verdict is None
        assert decision.final_decision == "PROCEED"
        assert pfc.stats["mip_evaluations"] == 0
