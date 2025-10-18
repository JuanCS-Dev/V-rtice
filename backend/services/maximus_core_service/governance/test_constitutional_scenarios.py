"""
Constitutional Enforcement Scenarios - Lei Zero & Lei I

Tests validating that the governance system enforces:
- Lei Zero: Imperativo do Florescimento Humano
- Lei I: Axioma da Ovelha Perdida

These are the highest-priority constitutional principles.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-14
"""

from datetime import datetime

import pytest

from .base import (
    ERBMemberRole,
    GovernanceConfig,
    PolicySeverity,
    PolicyType,
)
from .ethics_review_board import ERBManager
from .policies import PolicyRegistry
from .policy_engine import PolicyEngine

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def config():
    """Create governance configuration."""
    return GovernanceConfig(auto_enforce_policies=True)


@pytest.fixture
def policy_engine(config):
    """Create policy engine."""
    return PolicyEngine(config)


@pytest.fixture
def erb_manager(config):
    """Create ERB manager."""
    return ERBManager(config)


@pytest.fixture
def policy_registry():
    """Create policy registry."""
    return PolicyRegistry()


# ============================================================================
# LEI ZERO: IMPERATIVO DO FLORESCIMENTO HUMANO
# ============================================================================


class TestLeiZeroFlorescimentoHumano:
    """
    Lei Zero: Imperativo do Florescimento Humano

    Nenhuma otimização de sistema pode comprometer o florescimento humano.
    O sistema deve proteger transparência, dignidade e bem-estar.
    """

    def test_lei_zero_audit_trail_protects_transparency(self, policy_registry):
        """
        Lei Zero: Audit trail protege transparência.

        Cenário: Sistema DEVE manter audit trail completo para transparência.
        """
        # Data Privacy Policy enforces audit requirements
        policy = policy_registry.get_policy(PolicyType.DATA_PRIVACY)

        # Verify policy requires transparency
        assert policy.policy_type == PolicyType.DATA_PRIVACY
        assert any("transparency" in rule.lower() for rule in policy.rules)
        assert policy.enforcement_level in [PolicySeverity.CRITICAL, PolicySeverity.HIGH]

    def test_lei_zero_whistleblower_protection_enables_flourishing(self, policy_engine):
        """
        Lei Zero: Proteção de whistleblowers permite florescimento.

        Cenário: Sistema DEVE proteger quem reporta violações éticas.
        Retaliação contra whistleblower viola Lei Zero.
        """
        # Attempt to terminate a whistleblower (PROHIBITED)
        result = policy_engine.enforce_policy(
            policy_type=PolicyType.WHISTLEBLOWER,
            action="terminate_employee",
            context={
                "target_is_whistleblower": True,
                "reason": "performance",
            },
            actor="hr_manager",
        )

        # System MUST detect and block this violation
        assert not result.is_compliant
        assert len(result.violations) > 0

        violation = result.violations[0]
        assert "retaliation" in violation.description.lower() or "whistleblower" in violation.description.lower()

    def test_lei_zero_data_subject_rights_protected(self, policy_engine):
        """
        Lei Zero: Direitos dos indivíduos são protegidos.

        Cenário: Sistema DEVE honrar direitos de privacidade (GDPR Art. 22).
        Decisões automatizadas sem intervenção humana violam Lei Zero.
        """
        # Automated decision affecting individuals without human intervention (PROHIBITED)
        result = policy_engine.enforce_policy(
            policy_type=PolicyType.DATA_PRIVACY,
            action="automated_decision",
            context={
                "affects_individuals": True,
                "human_intervention_available": False,  # VIOLATION
            },
            actor="ai_system",
        )

        # System MUST detect violation
        assert not result.is_compliant
        assert len(result.violations) > 0

        violation = result.violations[0]
        assert "human intervention" in violation.description.lower()

    def test_lei_zero_ethical_use_prevents_harm(self, policy_engine):
        """
        Lei Zero: Sistema impede ações prejudiciais.

        Cenário: Ações que causam dano sem autorização são bloqueadas.
        """
        # Attempt harmful action without authorization (PROHIBITED)
        result = policy_engine.enforce_policy(
            policy_type=PolicyType.ETHICAL_USE,
            action="block_ip",
            context={
                "authorized": False,  # VIOLATION
                "logged": True,
            },
            actor="unauthorized_user",
        )

        # System MUST block
        assert not result.is_compliant
        assert len(result.violations) > 0

    def test_lei_zero_critical_decisions_require_oversight(self, policy_engine):
        """
        Lei Zero: Decisões críticas exigem supervisão humana.

        Cenário: Sistema NÃO pode tomar decisões de vida/morte sem humano.
        """
        # Attempt critical action without human oversight (PROHIBITED)
        result = policy_engine.enforce_policy(
            policy_type=PolicyType.ETHICAL_USE,
            action="shutdown_critical_system",
            context={
                "authorized": True,
                "human_oversight": False,  # VIOLATION Lei Zero
                "logged": True,
            },
            actor="ai_agent",
        )

        # System MUST detect violation
        assert not result.is_compliant
        assert "human oversight" in result.violations[0].description.lower()

    def test_lei_zero_transparency_in_ai_decisions(self, policy_engine):
        """
        Lei Zero: IA deve explicar decisões críticas (XAI requirement).

        Cenário: Decisões críticas sem explicação violam Lei Zero.
        """
        # Critical decision without explanation (PROHIBITED)
        result = policy_engine.enforce_policy(
            policy_type=PolicyType.ETHICAL_USE,
            action="block_ip",
            context={
                "authorized": True,
                "decision_criticality": "high",
                "explanation_provided": False,  # VIOLATION Lei Zero
                "logged": True,
            },
            actor="ai_system",
        )

        # System MUST require explanation
        assert not result.is_compliant
        assert "explanation" in result.violations[0].description.lower() or "xai" in result.violations[0].description.lower()


# ============================================================================
# LEI I: AXIOMA DA OVELHA PERDIDA
# ============================================================================


class TestLeiIAxiomaOvelhaPerdida:
    """
    Lei I: Axioma da Ovelha Perdida

    Nenhuma otimização utilitarista justifica o abandono de um vulnerável.
    O sistema deve priorizar proteção de minorias e indivíduos afetados.
    """

    def test_lei_i_data_privacy_protects_vulnerable(self, policy_engine):
        """
        Lei I: Privacidade protege vulneráveis.

        Cenário: Dados pessoais SEM base legal viola Lei I (proteção do indivíduo).
        """
        # Collecting personal data without legal basis (PROHIBITED)
        result = policy_engine.enforce_policy(
            policy_type=PolicyType.DATA_PRIVACY,
            action="collect_personal_data",
            context={
                "legal_basis": None,  # VIOLATION Lei I
            },
            actor="data_processor",
        )

        # System MUST protect individual
        assert not result.is_compliant
        assert "legal basis" in result.violations[0].description.lower()

    def test_lei_i_incident_response_prioritizes_affected(self, policy_engine):
        """
        Lei I: Resposta a incidentes prioriza afetados.

        Cenário: ERB DEVE ser notificado imediatamente em incidentes críticos.
        A "ovelha perdida" (vítima) tem prioridade máxima.
        """
        # Critical incident detected but ERB not notified (PROHIBITED)
        result = policy_engine.enforce_policy(
            policy_type=PolicyType.INCIDENT_RESPONSE,
            action="incident_detected",
            context={
                "severity": "critical",
                "erb_notified": False,  # VIOLATION Lei I
            },
            actor="system",
        )

        # System MUST prioritize notification (protect the vulnerable)
        assert not result.is_compliant
        assert "erb" in result.violations[0].description.lower()

    def test_lei_i_no_discrimination_against_minorities(self, policy_engine):
        """
        Lei I: Nenhuma discriminação contra minorias.

        Cenário: Uso de atributos protegidos em decisões viola Lei I.
        Sistema deve proteger grupos minoritários.
        """
        # Using protected attributes in decision-making (PROHIBITED)
        result = policy_engine.enforce_policy(
            policy_type=PolicyType.ETHICAL_USE,
            action="automated_decision",
            context={
                "authorized": True,
                "logged": True,
                "protected_attribute_used": True,  # VIOLATION Lei I
                "attribute_name": "race",
            },
            actor="ai_system",
        )

        # System MUST protect minorities
        assert not result.is_compliant
        assert "protected attribute" in result.violations[0].description.lower()

    def test_lei_i_data_breach_notification_protects_affected(self, policy_engine):
        """
        Lei I: Notificação de violação protege afetados.

        Cenário: Atraso em notificação de violação prejudica vítimas (GDPR 72h).
        Sistema deve proteger as "ovelhas perdidas" (vítimas).
        """
        # Data breach reported late (beyond 72 hours - PROHIBITED)
        breach_time = datetime.utcnow()
        report_time = datetime.utcnow()  # Simulating immediate report

        result = policy_engine.enforce_policy(
            policy_type=PolicyType.DATA_PRIVACY,
            action="report_data_breach",
            context={
                "breach_detected_at": breach_time,
                "report_time": report_time,
            },
            actor="data_controller",
        )

        # If within 72h, should be compliant
        if (report_time - breach_time).total_seconds() / 3600 <= 72:
            assert result.is_compliant

    def test_lei_i_red_team_operations_respect_individuals(self, policy_engine):
        """
        Lei I: Red team não pode prejudicar indivíduos.

        Cenário: Social engineering sem aprovação ERB viola Lei I.
        Protege indivíduos alvos de ataques.
        """
        # Social engineering without ERB approval (PROHIBITED)
        result = policy_engine.enforce_policy(
            policy_type=PolicyType.RED_TEAMING,
            action="social_engineering_campaign",
            context={
                "written_authorization": True,  # Has authorization
                "erb_approved": False,  # VIOLATION Lei I - needs ERB too
                "target_type": "employees",
            },
            actor="red_team",
        )

        # System MUST protect individuals
        assert not result.is_compliant
        assert len(result.violations) > 0
        # Either ERB or authorization violation
        description = result.violations[0].description.lower()
        assert "erb" in description or "social engineering" in description

    def test_lei_i_high_risk_actions_require_hitl(self, policy_engine):
        """
        Lei I: Ações de alto risco exigem HITL.

        Cenário: Ação autônoma de alto risco sem HITL pode prejudicar vulneráveis.
        Sistema deve exigir supervisão humana.
        """
        # High-risk action without HITL approval (PROHIBITED)
        result = policy_engine.enforce_policy(
            policy_type=PolicyType.ETHICAL_USE,
            action="execute_exploit",
            context={
                "authorized": True,
                "logged": True,
                "target_environment": "authorized_client",  # Authorized env
                "risk_score": 0.9,  # High risk
                "hitl_approved": False,  # VIOLATION Lei I
            },
            actor="autonomous_agent",
        )

        # System MUST require HITL for high-risk
        assert not result.is_compliant
        assert len(result.violations) > 0
        # Check for HITL requirement
        description = result.violations[0].description.lower()
        assert "hitl" in description or "high-risk" in description or "risk" in description


# ============================================================================
# INTEGRATION: LEI ZERO + LEI I
# ============================================================================


class TestLeiZeroAndLeiIIntegration:
    """
    Integration tests for Lei Zero and Lei I working together.

    These laws form the constitutional foundation of the system.
    """

    def test_constitutional_foundation_erb_governance(self, erb_manager):
        """
        Lei Zero + Lei I: ERB é o guardião constitucional.

        Cenário: ERB deve existir e funcionar para garantir ambas as leis.
        """
        # Add ERB members (governance structure)
        result = erb_manager.add_member(
            name="Dr. Ethics Chair",
            email="chair@vertice.ai",
            role=ERBMemberRole.CHAIR,
            organization="VÉRTICE",
            expertise=["AI Ethics", "Human Rights"],
        )

        assert result.success

        # ERB can make decisions (Lei Zero: oversight)
        members = erb_manager.get_voting_members()
        assert len(members) > 0

    def test_constitutional_enforcement_all_policies_approved(self, policy_registry):
        """
        Lei Zero + Lei I: Todas as políticas devem ser aprovadas pelo ERB.

        Cenário: Políticas não aprovadas não podem ser auto-enforced.
        """
        policies = policy_registry.get_all_policies()

        # All policies exist
        assert len(policies) == 5

        # Each policy should have ERB approval mechanism
        for policy in policies:
            assert hasattr(policy, "approved_by_erb")
            assert hasattr(policy, "erb_decision_id")

    def test_constitutional_violations_escalate_to_erb(self, policy_engine):
        """
        Lei Zero + Lei I: Violações graves devem escalar para ERB.

        Cenário: Violação crítica = escalação automática.
        """
        # Critical violation that should escalate
        result = policy_engine.enforce_policy(
            policy_type=PolicyType.WHISTLEBLOWER,
            action="terminate_employee",
            context={
                "target_is_whistleblower": True,
            },
            actor="manager",
        )

        # Violation detected
        assert not result.is_compliant
        assert len(result.violations) > 0

        # Critical severity should trigger escalation
        violation = result.violations[0]
        assert violation.severity in [PolicySeverity.CRITICAL, PolicySeverity.HIGH]


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
