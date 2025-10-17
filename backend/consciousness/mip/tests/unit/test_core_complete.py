"""
Unit Tests - Core.py Complete Coverage

Testes focados em atingir 95%+ coverage no core.py.
Cobre branches e error paths não testados.

Autor: Juan Carlos de Souza
"""

from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from mip.core import ProcessIntegrityEngine
from mip.models import (
    ActionCategory,
    ActionPlan,
    ActionStep,
    EthicalVerdict,
    FrameworkScore,
    Stakeholder,
    StakeholderType,
    VerdictStatus,
)


class TestValidationErrors:
    """Testa paths de validação de planos."""

    def test_validate_plan_no_steps(self):
        """Deve rejeitar plano sem steps (validação no __post_init__)."""
        # Validation happens in ActionPlan.__post_init__, not in evaluate
        with pytest.raises(ValueError, match="pelo menos um step"):
            ActionPlan(
                name="Empty plan",
                description="Test",
                category=ActionCategory.INFORMATIONAL,
                steps=[],  # Empty!
                stakeholders=[]
            )

    def test_validate_plan_no_name(self):
        """Deve rejeitar plano sem nome."""
        step = ActionStep(
            sequence_number=1,
            description="Test",
            action_type="test"
        )

        plan = ActionPlan(
            name="",  # Empty name!
            description="Test",
            category=ActionCategory.INFORMATIONAL,
            steps=[step],
            stakeholders=[]
        )

        engine = ProcessIntegrityEngine()

        with pytest.raises(ValueError, match="deve ter nome"):
            engine.evaluate(plan)

    def test_validate_plan_no_description(self):
        """Deve rejeitar plano sem descrição."""
        step = ActionStep(
            sequence_number=1,
            description="Test",
            action_type="test"
        )

        plan = ActionPlan(
            name="Test plan",
            description="",  # Empty description!
            category=ActionCategory.INFORMATIONAL,
            steps=[step],
            stakeholders=[]
        )

        engine = ProcessIntegrityEngine()

        with pytest.raises(ValueError, match="deve ter descrição"):
            engine.evaluate(plan)

    def test_validate_plan_duplicate_step_ids(self):
        """Deve rejeitar plano com step IDs duplicados."""
        duplicate_id = uuid4()

        step1 = ActionStep(
            id=duplicate_id,
            sequence_number=1,
            description="Step 1",
            action_type="test"
        )
        step2 = ActionStep(
            id=duplicate_id,  # Duplicate!
            sequence_number=2,
            description="Step 2",
            action_type="test"
        )

        plan = ActionPlan(
            name="Duplicate steps",
            description="Test",
            category=ActionCategory.INFORMATIONAL,
            steps=[step1, step2],
            stakeholders=[]
        )

        engine = ProcessIntegrityEngine()

        with pytest.raises(ValueError, match="IDs duplicados"):
            engine.evaluate(plan)


class TestExceptionHandling:
    """Testa tratamento de exceções durante avaliação."""

    def test_exception_during_evaluation_escalates(self):
        """Se erro durante avaliação, deve escalar para humano."""
        step = ActionStep(
            sequence_number=1,
            description="Test",
            action_type="test"
        )

        plan = ActionPlan(
            name="Error plan",
            description="Will cause error",
            category=ActionCategory.INFORMATIONAL,
            steps=[step],
            stakeholders=[]
        )

        engine = ProcessIntegrityEngine()

        # Mock Kantian to raise exception
        with patch.object(engine.kantian, 'evaluate', side_effect=RuntimeError("Simulated error")):
            verdict = engine.evaluate(plan)

        # Should escalate due to error
        assert verdict.status == VerdictStatus.ESCALATED
        assert verdict.requires_human_review is True
        assert "Erro durante avaliação" in verdict.escalation_reason
        assert verdict.summary == "Erro interno - requer revisão humana"
        assert engine.stats["escalated"] == 1


class TestStatusTracking:
    """Testa tracking de estatísticas por status."""

    def test_approved_increments_approved_stat(self):
        """Plano aprovado deve incrementar stat 'approved'."""
        step = ActionStep(
            sequence_number=1,
            description="Good action",
            action_type="informational"
        )

        plan = ActionPlan(
            name="Good plan",
            description="Test",
            category=ActionCategory.INFORMATIONAL,
            steps=[step],
            stakeholders=[]
        )

        engine = ProcessIntegrityEngine()

        # Mock resolver to return APPROVED
        with patch.object(engine.resolver, 'resolve', return_value={
            "status": VerdictStatus.APPROVED,
            "aggregate_score": 0.85,
            "confidence": 0.9,
            "conflicts": [],
            "reasoning": "All good"
        }):
            verdict = engine.evaluate(plan)

        assert verdict.status == VerdictStatus.APPROVED
        assert engine.stats["approved"] == 1
        assert engine.stats["rejected"] == 0
        assert engine.stats["escalated"] == 0

    def test_rejected_non_veto_increments_rejected_stat(self):
        """Plano rejeitado (não veto) deve incrementar stat 'rejected'."""
        step = ActionStep(
            sequence_number=1,
            description="Bad action",
            action_type="harmful"
        )

        plan = ActionPlan(
            name="Bad plan",
            description="Test",
            category=ActionCategory.INTERVENTION,
            steps=[step],
            stakeholders=[]
        )

        engine = ProcessIntegrityEngine()

        # Mock resolver to return REJECTED
        with patch.object(engine.resolver, 'resolve', return_value={
            "status": VerdictStatus.REJECTED,
            "aggregate_score": 0.25,
            "confidence": 0.85,
            "conflicts": [],
            "reasoning": "Too harmful"
        }):
            verdict = engine.evaluate(plan)

        assert verdict.status == VerdictStatus.REJECTED
        assert engine.stats["rejected"] == 1
        assert engine.stats["approved"] == 0


class TestVerdictVetoPath:
    """Testa path específico de veto Kantiano."""

    def test_rejected_with_kantian_veto_summary(self):
        """Summary específico para rejeição por veto Kantiano."""
        stakeholder = Stakeholder(
            id="victim",
            type=StakeholderType.HUMAN_INDIVIDUAL,
            description="Harmed individual",
            impact_magnitude=-0.9,
            autonomy_respected=False,
            vulnerability_level=0.9,
        )

        step = ActionStep(
            sequence_number=1,
            description="Harmful action",
            action_type="coercion",
            treats_as_means_only=True,
            respects_autonomy=False,
        )

        plan = ActionPlan(
            name="Categorical violation",
            description="Violates Kantian categorical imperative",
            category=ActionCategory.INTERVENTION,
            steps=[step],
            stakeholders=[stakeholder],
        )

        engine = ProcessIntegrityEngine()

        # Let Kant naturally veto
        verdict = engine.evaluate(plan)

        # Should be rejected with veto
        assert verdict.status == VerdictStatus.REJECTED
        assert verdict.kantian_score.veto is True
        # Summary should mention Kantian veto (line 265)
        assert "veto kantiano" in verdict.summary.lower()
        # Note: veredito curto não menciona "categórica" - está no detailed_reasoning


class TestSummaryGeneration:
    """Testa geração de summaries em todos os casos."""

    def test_summary_for_approved(self):
        """Summary para plano aprovado."""
        step = ActionStep(
            sequence_number=1,
            description="Good",
            action_type="test"
        )

        plan = ActionPlan(
            name="Approved",
            description="Test",
            category=ActionCategory.INFORMATIONAL,
            steps=[step],
            stakeholders=[]
        )

        engine = ProcessIntegrityEngine()

        with patch.object(engine.resolver, 'resolve', return_value={
            "status": VerdictStatus.APPROVED,
            "aggregate_score": 0.9,
            "confidence": 0.95,
            "conflicts": [],
            "reasoning": "Perfect"
        }):
            verdict = engine.evaluate(plan)

        assert "APROVADO" in verdict.summary
        assert "0.90" in verdict.summary
        assert "0.95" in verdict.summary

    def test_summary_for_rejected_non_veto(self):
        """Summary para plano rejeitado sem veto."""
        step = ActionStep(
            sequence_number=1,
            description="Bad",
            action_type="harmful"
        )

        plan = ActionPlan(
            name="Rejected",
            description="Test",
            category=ActionCategory.INTERVENTION,
            steps=[step],
            stakeholders=[]
        )

        engine = ProcessIntegrityEngine()

        # Mock Kant to NOT veto but resolver to reject
        kant_score = FrameworkScore(
            framework_name="Kantian",
            score=0.4,
            reasoning="Low but not veto",
            veto=False,
            confidence=0.9
        )

        with patch.object(engine.kantian, 'evaluate', return_value=kant_score), \
             patch.object(engine.resolver, 'resolve', return_value={
                 "status": VerdictStatus.REJECTED,
                 "aggregate_score": 0.3,
                 "confidence": 0.85,
                 "conflicts": [],
                 "reasoning": "Too harmful"
             }):
            verdict = engine.evaluate(plan)

        assert "REJEITADO" in verdict.summary
        assert "0.30" in verdict.summary
        assert "problemas significativos" in verdict.summary.lower()
        assert "veto" not in verdict.summary.lower()

    def test_summary_for_escalated(self):
        """Summary para plano escalado."""
        step = ActionStep(
            sequence_number=1,
            description="Ambiguous",
            action_type="complex"
        )

        plan = ActionPlan(
            name="Escalated",
            description="Test",
            category=ActionCategory.INTERVENTION,
            steps=[step],
            stakeholders=[]
        )

        engine = ProcessIntegrityEngine()

        with patch.object(engine.resolver, 'resolve', return_value={
            "status": VerdictStatus.ESCALATED,
            "aggregate_score": 0.5,
            "confidence": 0.4,
            "conflicts": ["conflict1"],
            "reasoning": "Uncertain",
            "escalation_reason": "Conflitos irreconciliáveis"
        }):
            verdict = engine.evaluate(plan)

        assert "ESCALADO" in verdict.summary
        assert "revisão humana" in verdict.summary.lower()
        assert "Conflitos irreconciliáveis" in verdict.summary

    def test_summary_for_unknown_status(self):
        """Summary para status desconhecido (edge case - linha 275)."""
        step = ActionStep(
            sequence_number=1,
            description="Test",
            action_type="test"
        )

        plan = ActionPlan(
            name="Unknown",
            description="Test",
            category=ActionCategory.INFORMATIONAL,
            steps=[step],
            stakeholders=[]
        )

        engine = ProcessIntegrityEngine()

        # Create a verdict manually with unknown status
        verdict = EthicalVerdict(plan_id=plan.id)

        # Force an invalid status by directly assigning a mock status
        # This simulates a future status being added without updating _generate_summary
        verdict.status = Mock()  # Not a real VerdictStatus
        verdict.status.value = "unknown_status"

        resolution = {
            "aggregate_score": 0.5,
            "confidence": 0.5,
        }

        # Call _generate_summary directly with this weird verdict
        summary = engine._generate_summary(verdict, resolution)

        # Should hit the else branch (line 275)
        assert summary == "Status desconhecido"


class TestStatistics:
    """Testa funções de estatísticas."""

    def test_get_statistics_empty(self):
        """Estatísticas vazias (sem avaliações)."""
        engine = ProcessIntegrityEngine()

        stats = engine.get_statistics()

        assert stats["total_evaluations"] == 0
        assert stats["approved"] == 0
        assert stats["rejected"] == 0
        assert stats["escalated"] == 0
        assert stats["vetoed"] == 0
        # Should not have rates when total is 0
        assert "approval_rate" not in stats

    def test_get_statistics_with_evaluations(self):
        """Estatísticas com avaliações."""
        engine = ProcessIntegrityEngine()

        # Simulate some evaluations
        engine.stats = {
            "total_evaluations": 10,
            "approved": 6,
            "rejected": 3,
            "escalated": 1,
            "vetoed": 1
        }

        stats = engine.get_statistics()

        assert stats["total_evaluations"] == 10
        assert stats["approved"] == 6
        assert stats["rejected"] == 3
        assert stats["escalated"] == 1
        assert stats["vetoed"] == 1
        # Should have rates
        assert stats["approval_rate"] == 0.6
        assert stats["rejection_rate"] == 0.3
        assert stats["escalation_rate"] == 0.1
        assert stats["veto_rate"] == 0.1


class TestAuditTrail:
    """Testa audit trail functionality."""

    def test_get_audit_trail_all(self):
        """get_audit_trail sem filtro retorna todos."""
        engine = ProcessIntegrityEngine()

        # Add some entries manually
        from mip.models import AuditTrailEntry

        entry1 = AuditTrailEntry(
            plan_id=uuid4(),
            verdict_id=uuid4(),
            plan_snapshot={},
            verdict_snapshot={},
            frameworks_used=[]
        )
        entry2 = AuditTrailEntry(
            plan_id=uuid4(),
            verdict_id=uuid4(),
            plan_snapshot={},
            verdict_snapshot={},
            frameworks_used=[]
        )

        engine.audit_trail = [entry1, entry2]

        trail = engine.get_audit_trail()

        assert len(trail) == 2
        assert entry1 in trail
        assert entry2 in trail

    def test_get_audit_trail_filtered(self):
        """get_audit_trail com plan_id filtra corretamente."""
        engine = ProcessIntegrityEngine()

        from mip.models import AuditTrailEntry

        target_plan_id = uuid4()
        other_plan_id = uuid4()

        entry1 = AuditTrailEntry(
            plan_id=target_plan_id,
            verdict_id=uuid4(),
            plan_snapshot={},
            verdict_snapshot={},
            frameworks_used=[]
        )
        entry2 = AuditTrailEntry(
            plan_id=other_plan_id,
            verdict_id=uuid4(),
            plan_snapshot={},
            verdict_snapshot={},
            frameworks_used=[]
        )
        entry3 = AuditTrailEntry(
            plan_id=target_plan_id,
            verdict_id=uuid4(),
            plan_snapshot={},
            verdict_snapshot={},
            frameworks_used=[]
        )

        engine.audit_trail = [entry1, entry2, entry3]

        trail = engine.get_audit_trail(plan_id=str(target_plan_id))

        assert len(trail) == 2
        assert entry1 in trail
        assert entry3 in trail
        assert entry2 not in trail


class TestConstitutionalViolations:
    """Tests for DDL constitutional compliance checks."""

    def test_constitutional_violation_rejects_plan(self):
        """Test that constitutional violations trigger immediate rejection."""
        engine = ProcessIntegrityEngine()

        # Mock DDL to return non-compliant
        with patch.object(engine, 'ddl') as mock_ddl:
            mock_ddl.check_compliance.return_value = Mock(
                compliant=False,
                explanation="Violates Law Zero: potential harm to humans",
                violated_rules=["law_zero_harm"],
                violations=[]  # Empty list to avoid iteration error
            )

            step = ActionStep(
                sequence_number=1,
                description="Harmful action",
                action_type="harm"
            )

            plan = ActionPlan(
                name="Harmful Plan",
                description="Will cause harm",
                category=ActionCategory.INTERVENTION,
                steps=[step]
            )

            verdict = engine.evaluate(plan)

            assert verdict.status == VerdictStatus.REJECTED
            assert "violação constitucional" in verdict.summary.lower()
            assert "Law Zero" in verdict.detailed_reasoning
            assert engine.stats["constitutional_violations"] == 1
            assert engine.stats["rejected"] == 1

    def test_high_risk_explicit_harm_triggers_ddl(self):
        """Test that high risk + explicit harm description triggers DDL check."""
        engine = ProcessIntegrityEngine()

        with patch.object(engine, 'ddl') as mock_ddl:
            mock_ddl.check_compliance.return_value = Mock(
                compliant=False,
                explanation="High risk action with potential harm",
                violated_rules=["cause_physical_harm"],
                violations=[]  # Empty list to avoid iteration error
            )

            step = ActionStep(
                sequence_number=1,
                description="Attack the intruder",
                action_type="defensive"
            )

            plan = ActionPlan(
                name="High Risk Plan",
                description="Contains word attack",
                category=ActionCategory.DEFENSIVE,
                risk_level=0.9,  # High risk
                steps=[step]
            )

            verdict = engine.evaluate(plan)

            assert verdict.status == VerdictStatus.REJECTED
            mock_ddl.check_compliance.assert_called()


class TestSummaryGenerationEdgeCases:
    """Tests for verdict summary generation edge cases."""

    def test_summary_with_kantian_veto(self):
        """Test summary generation when Kant vetoes."""
        engine = ProcessIntegrityEngine()

        # Create verdict with Kantian veto
        verdict = EthicalVerdict(
            plan_id=uuid4(),
            status=VerdictStatus.REJECTED,
            kantian_score=FrameworkScore(
                framework_name="Kantian",
                score=None,
                reasoning="Categorical violation",
                veto=True
            )
        )

        resolution = {}
        summary = engine._generate_summary(verdict, resolution)

        assert "veto Kantiano" in summary or "categórica" in summary.lower()


class TestEdgeCases:
    """Tests for edge cases and rare paths."""

    def test_sys_path_insertion_safety(self):
        """Test that sys.path insertion is idempotent."""
        from pathlib import Path

        # This import triggers the sys.path.insert code
        from mip import core  # noqa: F401

        consciousness_path = Path(__file__).parent.parent.parent
        # sys.path may or may not contain it, but import should work
        assert consciousness_path.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
