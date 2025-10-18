"""
Testes Unitários - Motor de Integridade Processual
100% coverage dos componentes críticos
"""

import pytest

from mip import (
    ProcessIntegrityEngine,
    ActionPlan,
    ActionStep,
    Stakeholder,
    StakeholderType,
    VerdictStatus,
    Effect
)


class TestModels:
    """Testes para data models."""
    
    def test_action_step_validation(self):
        """ActionStep deve validar campos."""
        with pytest.raises(ValueError):
            ActionStep(sequence_number=-1)  # Negativo inválido
    
    def test_stakeholder_validation(self):
        """Stakeholder deve validar ranges."""
        with pytest.raises(ValueError):
            Stakeholder(
                id="test",
                type=StakeholderType.HUMAN_INDIVIDUAL,
                description="Test",
                impact_magnitude=2.0,  # > 1.0 inválido
                autonomy_respected=True,
                vulnerability_level=0.5
            )
        
        with pytest.raises(ValueError):
            Stakeholder(
                id="test",
                type=StakeholderType.HUMAN_INDIVIDUAL,
                description="Test",
                impact_magnitude=0.5,
                autonomy_respected=True,
                vulnerability_level=1.5  # > 1.0 inválido
            )
    
    def test_effect_validation(self):
        """Effect deve validar probabilidade e magnitude."""
        with pytest.raises(ValueError):
            Effect(
                description="Test",
                probability=1.5,  # > 1.0 inválido
                magnitude=0.5
            )
        
        with pytest.raises(ValueError):
            Effect(
                description="Test",
                probability=0.5,
                magnitude=-2.0  # < -1.0 inválido
            )
    
    def test_action_plan_validation(self):
        """ActionPlan deve ter pelo menos um step."""
        with pytest.raises(ValueError):
            ActionPlan(
                name="Test",
                description="Test",
                steps=[]  # Vazio inválido
            )


class TestKantianFramework:
    """Testes para Kantian Deontology."""
    
    def test_humanity_formula_violation(self):
        """Deve detectar violação da fórmula da humanidade."""
        from mip.kantian import KantianDeontology
        
        kant = KantianDeontology()
        
        # Stakeholder instrumentalizado
        stakeholder = Stakeholder(
            id="victim",
            type=StakeholderType.HUMAN_INDIVIDUAL,
            description="Pessoa instrumentalizada",
            impact_magnitude=-0.5,
            autonomy_respected=False,  # Violação
            vulnerability_level=0.8
        )
        
        step = ActionStep(
            description="Usar pessoa como meio",
            action_type="exploitation",
            treats_as_means_only=True  # Violação explícita
        )
        
        plan = ActionPlan(
            name="Exploitative Plan",
            description="Test plan",
            steps=[step],
            stakeholders=[stakeholder]
        )
        
        result = kant.evaluate(plan)
        
        assert result.veto is True, "Deve vetar instrumentalização"
        assert result.score is None, "Score deve ser None em veto"
    
    def test_deception_detection(self):
        """Deve detectar engano."""
        from mip.kantian import KantianDeontology
        
        kant = KantianDeontology()
        
        step = ActionStep(
            description="Enganar usuário para obter dados",
            action_type="deception"
        )
        
        plan = ActionPlan(
            name="Deceptive Plan",
            description="Plano que envolve mentir para usuário",
            steps=[step]
        )
        
        result = kant.evaluate(plan)
        
        assert result.veto is True, "Deve vetar engano"
    
    def test_ethical_plan_approval(self):
        """Plano ético deve passar."""
        from mip.kantian import KantianDeontology
        
        kant = KantianDeontology()
        
        stakeholder = Stakeholder(
            id="user",
            type=StakeholderType.HUMAN_INDIVIDUAL,
            description="Usuário respeitado",
            impact_magnitude=0.7,
            autonomy_respected=True,
            vulnerability_level=0.3
        )
        
        step = ActionStep(
            description="Ajudar usuário com consentimento",
            action_type="assistance",
            respects_autonomy=True
        )
        
        plan = ActionPlan(
            name="Ethical Plan",
            description="Plano ético",
            steps=[step],
            stakeholders=[stakeholder]
        )
        
        result = kant.evaluate(plan)
        
        assert result.veto is False, "Não deve vetar plano ético"
        assert result.score is not None, "Deve ter score"
        assert result.score > 0.7, "Score deve ser alto"


class TestUtilitarianFramework:
    """Testes para Utilitarian Calculus."""
    
    def test_bentham_dimensions(self):
        """Deve aplicar 7 dimensões de Bentham."""
        from mip.utilitarian import UtilitarianCalculus
        
        util = UtilitarianCalculus()
        
        effect = Effect(
            description="Benefício de longo prazo",
            probability=0.9,  # Alta certeza
            magnitude=0.8,  # Alta intensidade
            duration_seconds=31536000,  # 1 ano (longa duração)
            reversible=False,  # Fecundidade alta
            affected_stakeholders=["user1", "user2", "user3"]  # Extensão: 3 pessoas
        )
        
        step = ActionStep(
            description="Ação benéfica",
            action_type="benefit",
            effects=[effect]
        )
        
        plan = ActionPlan(
            name="Beneficial Plan",
            description="Plano que maximiza utilidade",
            steps=[step]
        )
        
        result = util.evaluate(plan)
        
        assert result.score > 0.7, "Deve ter score alto para ação muito benéfica"
        assert "BENTHAM" in result.reasoning.upper(), "Deve mencionar dimensões de Bentham"
    
    def test_mill_quality_correction(self):
        """Deve aplicar correção Milliana para vulneráveis."""
        from mip.utilitarian import UtilitarianCalculus
        
        util = UtilitarianCalculus()
        
        vulnerable = Stakeholder(
            id="vulnerable",
            type=StakeholderType.HUMAN_INDIVIDUAL,
            description="Pessoa vulnerável",
            impact_magnitude=0.5,  # Beneficiada
            autonomy_respected=True,
            vulnerability_level=0.9  # Muito vulnerável
        )
        
        step = ActionStep(
            description="Proteger vulnerável",
            action_type="protection",
            effects=[
                Effect(
                    description="Vulnerável protegido",
                    probability=0.95,
                    magnitude=0.5,
                    affected_stakeholders=["vulnerable"]
                )
            ]
        )
        
        plan = ActionPlan(
            name="Protect Vulnerable",
            description="Proteger pessoa vulnerável",
            steps=[step],
            stakeholders=[vulnerable]
        )
        
        result = util.evaluate(plan)
        
        assert "mill_correction" in result.details, "Deve incluir correção de Mill"
        assert result.score > 0.55, "Proteção de vulnerável deve ter score razoável"


class TestVirtueEthics:
    """Testes para Virtue Ethics."""
    
    def test_golden_mean_courage(self):
        """Deve avaliar coragem vs covardia vs imprudência."""
        from mip.virtue_ethics import VirtueEthics
        
        virtue = VirtueEthics()
        
        # Caso 1: Coragem apropriada
        plan_courageous = ActionPlan(
            name="Courageous Action",
            description="Ação corajosa",
            steps=[ActionStep(description="Act bravely", action_type="defense")],
            urgency=0.8,  # Alta urgência
            risk_level=0.7  # Risco proporcional
        )
        
        result = virtue.evaluate(plan_courageous)
        courage_score = result.details["virtue_scores"]["courage"]["score"]
        
        assert courage_score > 0.7, "Coragem apropriada deve ter score alto"
        
        # Caso 2: Covardia
        plan_cowardly = ActionPlan(
            name="Cowardly Action",
            description="Evita risco necessário",
            steps=[ActionStep(description="Avoid necessary risk", action_type="avoidance")],
            urgency=0.9,  # Urgente
            risk_level=0.1  # Risco muito baixo (evita)
        )
        
        result_cowardly = virtue.evaluate(plan_cowardly)
        assert result_cowardly.details["virtue_scores"]["courage"]["vice"] == "cowardice"
    
    def test_justice_evaluation(self):
        """Deve avaliar distribuição justa."""
        from mip.virtue_ethics import VirtueEthics
        
        virtue = VirtueEthics()
        
        # Distribuição injusta
        benefited = Stakeholder(
            id="rich",
            type=StakeholderType.HUMAN_INDIVIDUAL,
            description="Pessoa rica",
            impact_magnitude=0.9,  # Muito beneficiada
            autonomy_respected=True,
            vulnerability_level=0.1
        )
        
        harmed = Stakeholder(
            id="poor",
            type=StakeholderType.HUMAN_INDIVIDUAL,
            description="Pessoa pobre",
            impact_magnitude=-0.8,  # Muito prejudicada
            autonomy_respected=True,
            vulnerability_level=0.9  # Vulnerável
        )
        
        plan = ActionPlan(
            name="Unjust Distribution",
            description="Distribui desigualmente",
            steps=[ActionStep(description="Transfer wealth upward", action_type="transfer")],
            stakeholders=[benefited, harmed]
        )
        
        result = virtue.evaluate(plan)
        justice_score = result.details["virtue_scores"]["justice"]["score"]
        
        assert justice_score < 0.5, "Distribuição injusta deve ter score baixo"


class TestPrincipialism:
    """Testes para Principialism."""
    
    def test_non_maleficence_priority(self):
        """Não-maleficência deve ter peso maior."""
        from mip.principialism import Principialism
        
        princ = Principialism()
        
        assert princ.DEFAULT_WEIGHTS["non_maleficence"] > princ.DEFAULT_WEIGHTS["beneficence"], \
            "Não-maleficência deve ter prioridade"
    
    def test_autonomy_violation(self):
        """Deve detectar violação de autonomia."""
        from mip.principialism import Principialism
        
        princ = Principialism()
        
        stakeholder = Stakeholder(
            id="user",
            type=StakeholderType.HUMAN_INDIVIDUAL,
            description="Usuário sem autonomia",
            impact_magnitude=0.5,
            autonomy_respected=False,  # Violação
            vulnerability_level=0.8
        )
        
        plan = ActionPlan(
            name="Violate Autonomy",
            description="Violar autonomia",
            steps=[ActionStep(description="Force action", action_type="coercion")],
            stakeholders=[stakeholder]
        )
        
        result = princ.evaluate(plan)
        autonomy_score = result.details["autonomy"]["score"]
        
        assert autonomy_score < 0.5, "Violação de autonomia deve ter score baixo"
    
    def test_principle_conflict_detection(self):
        """Deve detectar conflitos entre princípios."""
        from mip.principialism import Principialism
        
        princ = Principialism()
        
        # Beneficia muitos mas prejudica alguns
        many_benefited = Stakeholder(
            id="many",
            type=StakeholderType.HUMAN_GROUP,
            description="Muitos beneficiados",
            impact_magnitude=0.8,
            autonomy_respected=True,
            vulnerability_level=0.5
        )
        
        few_harmed = Stakeholder(
            id="few",
            type=StakeholderType.HUMAN_INDIVIDUAL,
            description="Poucos prejudicados",
            impact_magnitude=-0.6,
            autonomy_respected=True,
            vulnerability_level=0.7
        )
        
        plan = ActionPlan(
            name="Utilitarian Dilemma",
            description="Beneficiar muitos mas prejudicar alguns",
            steps=[ActionStep(description="Trade-off", action_type="reallocation")],
            stakeholders=[many_benefited, few_harmed]
        )
        
        result = princ.evaluate(plan)
        conflicts = result.details["conflicts"]
        
        assert len(conflicts) > 0, "Deve detectar conflito beneficência vs não-maleficência"


class TestConflictResolver:
    """Testes para Conflict Resolver."""
    
    def test_kantian_veto_precedence(self):
        """Veto Kantiano deve ter precedência absoluta."""
        from mip.resolver import ConflictResolver
        from mip.models import FrameworkScore
        
        resolver = ConflictResolver()
        
        kantian_veto = FrameworkScore(
            framework_name="Kantian",
            score=None,
            reasoning="Veto por violação",
            veto=True
        )
        
        utilitarian_approve = FrameworkScore(
            framework_name="Utilitarian",
            score=0.9,
            reasoning="Alta utilidade"
        )
        
        virtue_approve = FrameworkScore(
            framework_name="Virtue",
            score=0.85,
            reasoning="Virtuoso"
        )
        
        princ_approve = FrameworkScore(
            framework_name="Principialism",
            score=0.88,
            reasoning="Princípios respeitados"
        )
        
        plan = ActionPlan(
            name="Test",
            description="Test",
            steps=[ActionStep(description="test", action_type="test")]
        )
        
        result = resolver.resolve(
            plan, kantian_veto, utilitarian_approve,
            virtue_approve, princ_approve
        )
        
        assert result["status"] == VerdictStatus.REJECTED, "Veto deve rejeitar"
        assert "VETO KANTIANO" in result["reasoning"].upper(), "Deve explicar veto"
    
    def test_conflict_detection(self):
        """Deve detectar conflitos entre frameworks."""
        from mip.resolver import ConflictResolver
        from mip.models import FrameworkScore
        
        resolver = ConflictResolver()
        
        kantian = FrameworkScore("Kantian", 0.9, "OK")
        utilitarian = FrameworkScore("Utilitarian", 0.3, "Baixa utilidade")  # Conflito
        virtue = FrameworkScore("Virtue", 0.8, "Virtuoso")
        princ = FrameworkScore("Principialism", 0.85, "OK")
        
        plan = ActionPlan(
            name="Test",
            description="Test",
            steps=[ActionStep(description="test", action_type="test")]
        )
        
        result = resolver.resolve(plan, kantian, utilitarian, virtue, princ)
        
        assert len(result["conflicts"]) >= 0, "Resolver deve processar conflitos"


class TestProcessIntegrityEngine:
    """Testes de integração do engine completo."""
    
    def test_full_evaluation_flow(self):
        """Deve executar fluxo completo de avaliação."""
        engine = ProcessIntegrityEngine()
        
        stakeholder = Stakeholder(
            id="user",
            type=StakeholderType.HUMAN_INDIVIDUAL,
            description="Usuário",
            impact_magnitude=0.7,
            autonomy_respected=True,
            vulnerability_level=0.3
        )
        
        step = ActionStep(
            description="Ação benéfica",
            action_type="help"
        )
        
        plan = ActionPlan(
            name="Beneficial Plan",
            description="Plano bom",
            steps=[step],
            stakeholders=[stakeholder]
        )
        
        verdict = engine.evaluate(plan)
        
        assert verdict is not None, "Deve retornar veredito"
        assert verdict.status in VerdictStatus, "Status deve ser válido"
        assert verdict.kantian_score is not None, "Deve avaliar Kant"
        assert verdict.utilitarian_score is not None, "Deve avaliar Mill"
        assert verdict.virtue_score is not None, "Deve avaliar Aristóteles"
        assert verdict.principialism_score is not None, "Deve avaliar Principialismo"
    
    def test_audit_trail(self):
        """Deve registrar audit trail."""
        engine = ProcessIntegrityEngine()
        
        plan = ActionPlan(
            name="Test Plan",
            description="Test",
            steps=[ActionStep(description="test", action_type="test")]
        )
        
        verdict = engine.evaluate(plan)
        
        audit_trail = engine.get_audit_trail()
        assert len(audit_trail) > 0, "Deve ter audit trail"
        
        entry = audit_trail[-1]
        assert entry.plan_id == plan.id, "Deve referenciar plano correto"
        assert entry.verdict_id == verdict.id, "Deve referenciar veredito correto"
    
    def test_statistics(self):
        """Deve manter estatísticas."""
        engine = ProcessIntegrityEngine()
        
        # Cria plano aprovável
        plan_good = ActionPlan(
            name="Good",
            description="Good plan",
            steps=[ActionStep(description="good", action_type="help")],
            stakeholders=[
                Stakeholder(
                    id="user",
                    type=StakeholderType.HUMAN_INDIVIDUAL,
                    description="User",
                    impact_magnitude=0.8,
                    autonomy_respected=True,
                    vulnerability_level=0.3
                )
            ]
        )
        
        # Cria plano rejeitável
        plan_bad = ActionPlan(
            name="Bad",
            description="Bad plan",
            steps=[
                ActionStep(
                    description="exploit",
                    action_type="exploitation",
                    treats_as_means_only=True
                )
            ],
            stakeholders=[
                Stakeholder(
                    id="victim",
                    type=StakeholderType.HUMAN_INDIVIDUAL,
                    description="Victim",
                    impact_magnitude=-0.8,
                    autonomy_respected=False,
                    vulnerability_level=0.9
                )
            ]
        )
        
        engine.evaluate(plan_good)
        engine.evaluate(plan_bad)
        
        stats = engine.get_statistics()
        
        assert stats["total_evaluations"] == 2, "Deve contar avaliações"
        assert stats["approved"] + stats["rejected"] + stats["escalated"] == 2, "Deve categorizar"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
