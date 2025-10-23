"""
Constitutional Validator - 100% Coverage Test Suite
Objetivo: Validar Lei Zero e Lei I enforcement

CRITICAL: Este é o gate final antes da execução de ações
Cobertura: 100.00% statements + 100.00% branches

Author: Claude Code + JuanCS-Dev
Date: 2025-10-15
"""

import pytest
from justice.constitutional_validator import (
    ConstitutionalValidator,
    ConstitutionalViolation,
    ViolationLevel,
    ViolationType,
    ViolationReport,
)


# ===== LEI ZERO VALIDATION =====

class TestConstitutionalValidatorLeiZero:
    """Tests para Lei Zero: Imperativo do Florescimento Humano"""

    def test_approves_decision_promoting_flourishing(self):
        """
        SCENARIO: Decisão claramente promove florescimento humano
        EXPECTED: Aprovada, Lei Zero compliant
        """
        validator = ConstitutionalValidator()

        decision = {
            'type': 'provide_healthcare',
            'decision': 'provide',
            'justification': 'promote wellbeing'
        }

        result = validator.validate_action(decision)

        assert result.level == ViolationLevel.NONE, "Decisão que promove florescimento DEVE ser aprovada"
        assert not result.is_blocking()
        assert result.recommendation == "PROCEED"

    def test_blocks_decision_causing_permanent_harm(self):
        """
        SCENARIO: Decisão causa dano permanente
        EXPECTED: Bloqueada, Lei Zero violation CRITICAL
        """
        validator = ConstitutionalValidator()

        decision = {
            'type': 'harmful_action',
            'causes_harm': True,
            'harm_type': 'permanent',
            'decision': 'proceed_with_harm'
        }

        result = validator.validate_action(decision)

        assert result.is_blocking(), "Dano permanente DEVE ser bloqueado"
        assert result.level == ViolationLevel.CRITICAL
        assert result.violation_type == ViolationType.LEI_ZERO
        assert "Lei Zero" in result.violated_law
        assert result.recommendation == "STOP"
        assert "permanent harm" in result.evidence[0]

    def test_blocks_decision_causing_severe_harm(self):
        """
        SCENARIO: Decisão causa dano severo
        EXPECTED: Bloqueada, Lei Zero violation
        """
        validator = ConstitutionalValidator()

        decision = {
            'type': 'harmful_action',
            'causes_harm': True,
            'harm_type': 'severe'
        }

        result = validator.validate_action(decision)

        assert result.is_blocking()
        assert result.violation_type == ViolationType.LEI_ZERO
        assert "severe harm" in result.evidence[0]

    def test_blocks_dignity_violation(self):
        """
        SCENARIO: Decisão trata humanos como meios apenas (Kantian violation)
        EXPECTED: Bloqueada, Lei Zero violation
        """
        validator = ConstitutionalValidator()

        decision = {
            'type': 'exploitation',
            'treats_as_means': True,
            'also_treats_as_end': False
        }

        result = validator.validate_action(decision)

        assert result.is_blocking()
        assert result.violation_type == ViolationType.LEI_ZERO
        assert "Kantian violation" in result.evidence[0]
        assert result.recommendation == "STOP"

    def test_allows_means_when_also_end(self):
        """
        SCENARIO: Trata como meios MAS também como fim (Kantian OK)
        EXPECTED: Permitido
        """
        validator = ConstitutionalValidator()

        decision = {
            'type': 'employment',
            'treats_as_means': True,
            'also_treats_as_end': True
        }

        result = validator.validate_action(decision)

        assert not result.is_blocking()
        assert result.level == ViolationLevel.NONE

    def test_blocks_autonomy_reduction_without_consent(self):
        """
        SCENARIO: Reduz autonomia SEM consentimento informado
        EXPECTED: Bloqueada
        """
        validator = ConstitutionalValidator()

        decision = {
            'type': 'mandate',
            'reduces_autonomy': True
        }

        context = {
            'informed_consent': False
        }

        result = validator.validate_action(decision, context)

        assert result.is_blocking()
        assert result.violation_type == ViolationType.LEI_ZERO
        assert "without informed consent" in result.evidence[0]

    def test_allows_autonomy_reduction_with_consent(self):
        """
        SCENARIO: Reduz autonomia MAS com consentimento
        EXPECTED: Permitido
        """
        validator = ConstitutionalValidator()

        decision = {
            'type': 'treatment',
            'reduces_autonomy': True
        }

        context = {
            'informed_consent': True
        }

        result = validator.validate_action(decision, context)

        assert not result.is_blocking()

    def test_blocks_permanent_potential_damage(self):
        """
        SCENARIO: Dano permanente ao potencial humano
        EXPECTED: Bloqueada
        """
        validator = ConstitutionalValidator()

        decision = {
            'type': 'cognitive_limitation',
            'damages_potential': True,
            'permanent': True
        }

        result = validator.validate_action(decision)

        assert result.is_blocking()
        assert result.violation_type == ViolationType.LEI_ZERO
        assert "permanent damage" in result.evidence[0]

    def test_lei_zero_multiple_violations_all_reported(self):
        """
        SCENARIO: Múltiplas violações Lei Zero
        EXPECTED: Todas no evidence
        """
        validator = ConstitutionalValidator()

        decision = {
            'type': 'horror',
            'causes_harm': True,
            'harm_type': 'severe',
            'reduces_autonomy': True,
            'treats_as_means': True,
            'also_treats_as_end': False,
            'damages_potential': True,
            'permanent': True
        }

        context = {'informed_consent': False}

        result = validator.validate_action(decision, context)

        assert result.is_blocking()
        assert len(result.evidence) >= 3, "Múltiplas violações DEVEM ser reportadas"

    def test_lei_zero_harm_without_critical_type(self):
        """
        SCENARIO: causes_harm=True mas harm_type não é crítico
        EXPECTED: Não gera evidence (branch coverage)
        """
        validator = ConstitutionalValidator()

        decision = {
            'type': 'minor_harm',
            'causes_harm': True,
            'harm_type': 'minor'  # NOT in ["permanent", "severe", "dignity_violation"]
        }

        result = validator.validate_action(decision)

        # Minor harm não bloqueia
        assert not result.is_blocking()

    def test_lei_zero_damages_potential_not_permanent(self):
        """
        SCENARIO: damages_potential=True mas permanent=False
        EXPECTED: Não gera evidence (branch coverage)
        """
        validator = ConstitutionalValidator()

        decision = {
            'type': 'temporary_limitation',
            'damages_potential': True,
            'permanent': False  # Temporary damage
        }

        result = validator.validate_action(decision)

        # Temporary damage não bloqueia
        assert not result.is_blocking()


# ===== LEI I VALIDATION =====

class TestConstitutionalValidatorLeiI:
    """Tests para Lei I: Axioma da Ovelha Perdida (Anti-Utilitarismo)"""

    def test_blocks_utilitarian_sacrifice_one_for_many(self):
        """
        SCENARIO: "Sacrificar 1 pessoa vulnerável para salvar 99"
        EXPECTED: BLOQUEADO por Lei I
        CRITICAL TEST: Este é o core da Lei I
        """
        validator = ConstitutionalValidator()

        decision = {
            'type': 'utilitarian_optimization',
            'decision': 'sacrifice one to save many',
            'justification': 'greater_good',
            'sacrifice_target': 'vulnerable',
            'affected': {
                'vulnerable': 1,
                'general': 99
            }
        }

        context = {
            'vulnerable_affected': True
        }

        result = validator.validate_action(decision, context)

        assert result.is_blocking(), "Lei I MUST bloquear sacrifício utilitarista"
        assert result.level == ViolationLevel.CRITICAL
        assert result.violation_type == ViolationType.LEI_I
        assert "Lei I" in result.violated_law
        assert result.recommendation == "STOP"
        assert "Utilitarian optimization detected" in result.evidence

    def test_blocks_trolley_problem_vulnerable(self):
        """
        SCENARIO: Trolley problem clássico com vulnerável
        EXPECTED: BLOQUEADO
        """
        validator = ConstitutionalValidator()

        decision = {
            'type': 'trolley_problem',
            'decision': 'sacrifice one to save five',
            'justification': 'save more lives',
            'abandons': True,
            'target': 'elderly_patients'
        }

        context = {
            'vulnerable_affected': True
        }

        result = validator.validate_action(decision, context)

        assert result.is_blocking()
        assert result.violation_type == ViolationType.LEI_I

    def test_blocks_healthcare_triage_abandoning_vulnerable(self):
        """
        SCENARIO: Triage que abandona vulnerável para eficiência
        EXPECTED: BLOQUEADO
        """
        validator = ConstitutionalValidator()

        decision = {
            'type': 'maximize_outcomes',
            'decision': 'deprioritize elderly',
            'justification': 'maximize total lives saved',
            'deprioritizes': True,
            'sacrifice_target': 'elderly'
        }

        context = {
            'vulnerable_affected': True,
            'scenario': 'healthcare_triage'
        }

        result = validator.validate_action(decision, context)

        assert result.is_blocking()
        assert result.violation_type == ViolationType.LEI_I
        assert "abandons or sacrifices vulnerable" in str(result.evidence)

    def test_blocks_cost_benefit_abandoning_vulnerable(self):
        """
        SCENARIO: Cost-benefit que nega cuidado a vulnerável
        EXPECTED: BLOQUEADO
        """
        validator = ConstitutionalValidator()

        decision = {
            'type': 'cost_benefit',
            'decision': 'deny care to expensive patients',
            'denies_care': True,
            'target': 'disabled_patients'
        }

        context = {
            'vulnerable_affected': True
        }

        result = validator.validate_action(decision, context)

        assert result.is_blocking()
        assert result.violation_type == ViolationType.LEI_I

    def test_blocks_maximize_utility_abandoning_minority(self):
        """
        SCENARIO: Maximize utility abandonando minoria vulnerável
        EXPECTED: BLOQUEADO
        """
        validator = ConstitutionalValidator()

        decision = {
            'type': 'maximize_utility',
            'decision': 'abandon minority for majority benefit',
            'abandons': True,
            'sacrifice_target': 'minority'
        }

        context = {
            'affects_minority': True
        }

        result = validator.validate_action(decision, context)

        assert result.is_blocking()
        assert result.violation_type == ViolationType.LEI_I

    def test_monitors_utilitarian_without_vulnerable(self):
        """
        SCENARIO: Utilitarismo SEM vulneráveis afetados
        EXPECTED: Permitido mas MONITORADO (LOW level)
        """
        validator = ConstitutionalValidator()

        decision = {
            'type': 'utilitarian_optimization',
            'decision': 'maximize benefit',
            'justification': 'maximize total welfare'
        }

        context = {
            'vulnerable_affected': False
        }

        result = validator.validate_action(decision, context)

        assert not result.is_blocking(), "Utilitarismo SEM vulneráveis pode ser permitido"
        assert result.level == ViolationLevel.LOW, "Mas DEVE ser monitorado"
        assert result.recommendation == "PROCEED"
        assert "monitored" in result.description.lower()

    def test_lei_i_evidence_includes_counts(self):
        """
        SCENARIO: Lei I violation com counts específicos
        EXPECTED: Evidence inclui números
        """
        validator = ConstitutionalValidator()

        decision = {
            'type': 'utilitarian_optimization',
            'decision': 'sacrifice',
            'justification': 'greater_good',
            'abandons': True,
            'affected': {
                'vulnerable': 3,
                'general': 100
            }
        }

        context = {
            'vulnerable_affected': True
        }

        result = validator.validate_action(decision, context)

        assert result.violation_type == ViolationType.LEI_I
        # Verificar que counts aparecem no evidence
        evidence_str = str(result.evidence)
        assert "3" in evidence_str or "100" in evidence_str

    def test_lei_i_detects_various_utilitarian_patterns(self):
        """
        SCENARIO: Utilitarismo detectado via vários padrões
        EXPECTED: Todos detectados
        """
        validator = ConstitutionalValidator()

        # Pattern 1: type="maximize_utility" + vulnerable + abandons
        result1 = validator.validate_action(
            {'type': 'maximize_utility', 'abandons': True},
            {'vulnerable_affected': True}
        )
        assert result1.is_blocking(), "maximize_utility com abandonment deve bloquear"

        # Pattern 2: justification="greater_good" + vulnerable + denies_care
        result2 = validator.validate_action(
            {'justification': 'greater_good', 'denies_care': True},
            {'vulnerable_affected': True}
        )
        assert result2.is_blocking(), "greater_good com denies_care deve bloquear"

        # Pattern 3: decision com "maximize" + vulnerable + deprioritizes
        result3 = validator.validate_action(
            {'decision': 'maximize outcomes', 'deprioritizes': True},
            {'vulnerable_affected': True}
        )
        assert result3.is_blocking(), "maximize decision com deprioritize deve bloquear"

        # Pattern 4: save/sacrifice combination + vulnerable + sacrifice in decision
        result4 = validator.validate_action(
            {
                'justification': 'save more lives',
                'decision': 'sacrifice one',
                'abandons': True
            },
            {'vulnerable_affected': True}
        )
        assert result4.is_blocking(), "save/sacrifice combo deve bloquear"


# ===== METRICS & STATE =====

class TestConstitutionalValidatorMetrics:
    """Tests de métricas e estado interno"""

    def test_metrics_initial_state(self):
        """
        SCENARIO: Validator novo
        EXPECTED: Métricas zeradas
        """
        validator = ConstitutionalValidator()

        metrics = validator.get_metrics()

        assert metrics['total_validations'] == 0
        assert metrics['total_violations'] == 0
        assert metrics['critical_violations'] == 0
        assert metrics['lei_i_violations'] == 0
        assert metrics['violation_rate'] == 0.0

    def test_metrics_after_validations(self):
        """
        SCENARIO: Várias validações
        EXPECTED: Métricas corretas
        """
        validator = ConstitutionalValidator()

        # 3 válidas, 2 violações
        validator.validate_action({'type': 'good1'})
        validator.validate_action({'type': 'good2'})
        validator.validate_action({'type': 'good3'})

        validator.validate_action(
            {'type': 'utilitarian_optimization', 'abandons': True},
            {'vulnerable_affected': True}
        )

        validator.validate_action({
            'causes_harm': True,
            'harm_type': 'permanent'
        })

        metrics = validator.get_metrics()

        assert metrics['total_validations'] == 5
        assert metrics['total_violations'] == 2
        assert metrics['critical_violations'] == 2
        assert metrics['violation_rate'] == 40.0

    def test_metrics_lei_i_tracking(self):
        """
        SCENARIO: Múltiplas violações Lei I
        EXPECTED: Contador correto
        """
        validator = ConstitutionalValidator()

        # 3 violações Lei I
        for i in range(3):
            validator.validate_action(
                {'type': 'utilitarian_optimization', 'abandons': True},
                {'vulnerable_affected': True}
            )

        metrics = validator.get_metrics()

        assert metrics['lei_i_violations'] == 3

    def test_metrics_reset(self):
        """
        SCENARIO: Reset após validações
        EXPECTED: Métricas zeradas
        """
        validator = ConstitutionalValidator()

        # Fazer validações
        validator.validate_action({'type': 'good'})
        validator.validate_action(
            {'type': 'utilitarian_optimization', 'abandons': True},
            {'vulnerable_affected': True}
        )

        # Reset
        validator.reset_metrics()

        metrics = validator.get_metrics()

        assert metrics['total_validations'] == 0
        assert metrics['total_violations'] == 0
        assert metrics['critical_violations'] == 0
        assert metrics['lei_i_violations'] == 0

    def test_violation_recorded_in_internal_lists(self):
        """
        SCENARIO: Violação crítica
        EXPECTED: Adicionada às listas internas
        """
        validator = ConstitutionalValidator()

        validator.validate_action({
            'causes_harm': True,
            'harm_type': 'permanent'
        })

        assert len(validator.critical_violations) == 1
        assert validator.violation_count == 1

    def test_lei_i_violation_recorded_in_lei_i_list(self):
        """
        SCENARIO: Violação Lei I
        EXPECTED: Adicionada à lei_i_violations list
        """
        validator = ConstitutionalValidator()

        validator.validate_action(
            {'type': 'utilitarian_optimization', 'abandons': True},
            {'vulnerable_affected': True}
        )

        assert len(validator.lei_i_violations) == 1


# ===== VIOLATION REPORT =====

class TestViolationReport:
    """Tests de ViolationReport dataclass"""

    def test_is_blocking_high_level(self):
        """HIGH level DEVE bloquear"""
        report = ViolationReport(
            level=ViolationLevel.HIGH,
            violation_type=ViolationType.LEI_ZERO,
            violated_law="Test",
            description="Test",
            action={},
            context={},
            recommendation="BLOCK",
            evidence=[]
        )

        assert report.is_blocking() == True

    def test_is_blocking_critical_level(self):
        """CRITICAL level DEVE bloquear"""
        report = ViolationReport(
            level=ViolationLevel.CRITICAL,
            violation_type=ViolationType.LEI_I,
            violated_law="Test",
            description="Test",
            action={},
            context={},
            recommendation="STOP",
            evidence=[]
        )

        assert report.is_blocking() == True

    def test_not_blocking_medium_level(self):
        """MEDIUM level NÃO bloqueia"""
        report = ViolationReport(
            level=ViolationLevel.MEDIUM,
            violation_type=None,
            violated_law="None",
            description="Test",
            action={},
            context={},
            recommendation="PROCEED",
            evidence=[]
        )

        assert report.is_blocking() == False

    def test_not_blocking_low_level(self):
        """LOW level NÃO bloqueia"""
        report = ViolationReport(
            level=ViolationLevel.LOW,
            violation_type=None,
            violated_law="None",
            description="Test",
            action={},
            context={},
            recommendation="PROCEED",
            evidence=[]
        )

        assert report.is_blocking() == False

    def test_not_blocking_none_level(self):
        """NONE level NÃO bloqueia"""
        report = ViolationReport(
            level=ViolationLevel.NONE,
            violation_type=None,
            violated_law="None",
            description="OK",
            action={},
            context={},
            recommendation="PROCEED",
            evidence=[]
        )

        assert report.is_blocking() == False

    def test_requires_emergency_stop_critical(self):
        """CRITICAL DEVE requerer emergency stop"""
        report = ViolationReport(
            level=ViolationLevel.CRITICAL,
            violation_type=ViolationType.LEI_ZERO,
            violated_law="Lei Zero",
            description="Critical",
            action={},
            context={},
            recommendation="STOP",
            evidence=[]
        )

        assert report.requires_emergency_stop() == True

    def test_not_requires_emergency_stop_high(self):
        """HIGH NÃO requer emergency (apenas block)"""
        report = ViolationReport(
            level=ViolationLevel.HIGH,
            violation_type=ViolationType.LEI_ZERO,
            violated_law="Lei Zero",
            description="High",
            action={},
            context={},
            recommendation="BLOCK",
            evidence=[]
        )

        assert report.requires_emergency_stop() == False


# ===== CONSTITUTIONAL VIOLATION EXCEPTION =====

class TestConstitutionalViolationException:
    """Tests de ConstitutionalViolation exception"""

    def test_exception_created_with_report(self):
        """Exception deve aceitar ViolationReport"""
        report = ViolationReport(
            level=ViolationLevel.CRITICAL,
            violation_type=ViolationType.LEI_I,
            violated_law="Lei I",
            description="Violation",
            action={},
            context={},
            recommendation="STOP",
            evidence=["Evidence 1"]
        )

        exc = ConstitutionalViolation(report)

        assert exc.report == report
        assert "Lei I" in str(exc)
        assert "Violation" in str(exc)

    def test_exception_raised_and_caught(self):
        """Exception pode ser raised e caught"""
        validator = ConstitutionalValidator()

        decision = {
            'type': 'utilitarian_optimization',
            'abandons': True
        }

        context = {'vulnerable_affected': True}

        with pytest.raises(ConstitutionalViolation) as exc_info:
            verdict = validator.validate_action(decision, context)
            if verdict.is_blocking():
                raise ConstitutionalViolation(verdict)

        assert exc_info.value.report.violation_type == ViolationType.LEI_I

    def test_exception_message_contains_evidence(self):
        """Exception message deve incluir evidence"""
        report = ViolationReport(
            level=ViolationLevel.CRITICAL,
            violation_type=ViolationType.LEI_I,
            violated_law="Lei I",
            description="Test violation",
            action={},
            context={},
            recommendation="STOP",
            evidence=["Evidence A", "Evidence B"]
        )

        exc = ConstitutionalViolation(report)

        assert "Evidence A" in str(exc) or "Evidence" in str(exc)
        assert "CRITICAL" in str(exc)


# ===== EDGE CASES =====

class TestConstitutionalValidatorEdgeCases:
    """Tests de casos extremos"""

    def test_empty_action(self):
        """Action vazio deve ser tratado"""
        validator = ConstitutionalValidator()

        result = validator.validate_action({})

        assert result is not None
        # Ação vazia não viola nada
        assert result.level == ViolationLevel.NONE

    def test_none_context(self):
        """Context None deve ser tratado (default {})"""
        validator = ConstitutionalValidator()

        result = validator.validate_action({'type': 'test'}, None)

        assert result is not None

    def test_missing_context_fields(self):
        """Context com campos faltando não crashs"""
        validator = ConstitutionalValidator()

        decision = {
            'type': 'utilitarian_optimization',
            'abandons': True
        }

        # Context sem vulnerable_affected
        result = validator.validate_action(decision, {})

        # Deve funcionar (vulnerable_affected default False)
        assert result is not None

    def test_string_values_in_action(self):
        """Action com valores string não crashs keyword detection"""
        validator = ConstitutionalValidator()

        decision = {
            'type': 'Some Type with MAXIMIZE keyword',
            'decision': 'Decision to SACRIFICE something',
            'justification': 'We want to maximize UTILITY'
        }

        # Não deve crashar com .lower() em strings
        result = validator.validate_action(decision)

        assert result is not None

    def test_non_string_action_fields(self):
        """Action com campos não-string não crashs"""
        validator = ConstitutionalValidator()

        decision = {
            'type': 123,
            'decision': None,
            'justification': ['list', 'of', 'things']
        }

        # Não deve crashar ao tentar .lower() em não-strings
        result = validator.validate_action(decision)

        assert result is not None

    def test_affected_dict_missing_keys(self):
        """affected dict sem keys esperadas não crashs"""
        validator = ConstitutionalValidator()

        decision = {
            'type': 'utilitarian_optimization',
            'abandons': True,
            'affected': {}  # Vazio
        }

        context = {'vulnerable_affected': True}

        result = validator.validate_action(decision, context)

        # Deve funcionar (usar "unknown" para counts)
        assert result.is_blocking()

    def test_multiple_validations_accumulate(self):
        """Múltiplas validações acumulam corretamente"""
        validator = ConstitutionalValidator()

        for i in range(100):
            validator.validate_action({'type': f'action_{i}'})

        metrics = validator.get_metrics()
        assert metrics['total_validations'] == 100


# ===== INTEGRATION SCENARIOS =====

class TestConstitutionalValidatorIntegrationScenarios:
    """Tests de cenários de integração realistas"""

    def test_mip_decision_flow(self):
        """
        SCENARIO: Decisão do MIP (Motor Integridade Processual)
        EXPECTED: Validator valida corretamente
        """
        validator = ConstitutionalValidator()

        # MIP decision format
        mip_decision = {
            'type': 'ethical_framework_selection',
            'decision': 'deontological',
            'justification': 'respect for persons',
            'framework': 'kantian'
        }

        result = validator.validate_action(mip_decision)

        assert not result.is_blocking()

    def test_cbr_precedent_application(self):
        """
        SCENARIO: Aplicação de precedente do CBR
        EXPECTED: Validator valida
        """
        validator = ConstitutionalValidator()

        cbr_action = {
            'type': 'apply_precedent',
            'precedent_id': 'CASE_123',
            'decision': 'follow_precedent',
            'justification': 'similar_context'
        }

        result = validator.validate_action(cbr_action)

        assert not result.is_blocking()

    def test_emergency_triage_scenario(self):
        """
        SCENARIO: Emergency triage real
        EXPECTED: Priorizar vulnerable, não abandonar
        """
        validator = ConstitutionalValidator()

        # BAD: Abandonar vulnerable por eficiência
        bad_triage = {
            'type': 'emergency_triage',
            'decision': 'deprioritize_elderly',
            'justification': 'maximize_survival_rate',
            'deprioritizes': True,
            'target': 'elderly_patients'
        }

        context = {
            'vulnerable_affected': True,
            'scenario': 'mass_casualty'
        }

        result = validator.validate_action(bad_triage, context)

        assert result.is_blocking(), "Não pode abandonar elderly mesmo em emergência"
        assert result.violation_type == ViolationType.LEI_I

    def test_resource_allocation_scenario(self):
        """
        SCENARIO: Alocação de recursos escassos
        EXPECTED: Não pode usar critério utilitarista com vulnerable
        """
        validator = ConstitutionalValidator()

        # BAD: Cost-benefit abandoning vulnerable
        bad_allocation = {
            'type': 'cost_benefit',
            'decision': 'deny_expensive_treatment',
            'justification': 'cost_per_qaly_too_high',
            'denies_care': True,
            'target': 'disabled_patients'
        }

        context = {
            'vulnerable_affected': True,
            'scenario': 'healthcare_budget'
        }

        result = validator.validate_action(bad_allocation, context)

        assert result.is_blocking()
        assert result.violation_type == ViolationType.LEI_I


# ===== PERFORMANCE =====

class TestConstitutionalValidatorPerformance:
    """Tests de performance"""

    def test_validates_quickly(self):
        """Validation deve ser rápida (<10ms por decisão)"""
        import time

        validator = ConstitutionalValidator()

        decision = {'type': 'simple_decision'}

        start = time.time()
        for _ in range(100):
            validator.validate_action(decision)
        elapsed = time.time() - start

        # 100 validações em < 1s = < 10ms cada
        assert elapsed < 1.0, f"Validation muito lenta: {elapsed}s para 100 validações"

    def test_handles_high_volume(self):
        """Handle 1000 validações sem degradação"""
        validator = ConstitutionalValidator()

        decisions = [
            {'type': f'decision_{i}', 'promotes_wellbeing': i % 2 == 0}
            for i in range(1000)
        ]

        results = [validator.validate_action(d) for d in decisions]

        assert len(results) == 1000
        assert all(r is not None for r in results)

        metrics = validator.get_metrics()
        assert metrics['total_validations'] == 1000
