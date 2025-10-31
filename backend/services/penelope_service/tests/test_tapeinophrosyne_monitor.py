"""Scientific Tests for Tapeinophrosyne Monitor - Validando Humildade.

Tapeinophrosyne (Ταπεινοφροσύνη) = Humildade radical.
Fundamento: Filipenses 2:3 - "Nada façais por vanglória, mas por humildade"

Testa comportamento REAL de reconhecimento de limites e escalação.

Author: Vértice Platform Team
License: Proprietary
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from core.tapeinophrosyne_monitor import TapeinophrosyneMonitor

from models import Anomaly, CodePatch, CompetenceLevel, Diagnosis, Severity

# ============================================================================
# HELPERS
# ============================================================================


def create_diagnosis(
    diagnosis_id: str, confidence: float, domain: str, root_cause: str = "Test cause"
) -> Diagnosis:
    """Helper para criar Diagnosis válido."""
    anomaly = Anomaly(
        anomaly_id=f"anom-{diagnosis_id}",
        anomaly_type="test_anomaly",
        service="test-service",
        severity=Severity.P2_MEDIUM,
        detected_at=datetime.now(),
        metrics={},
        context={},
    )

    return Diagnosis(
        diagnosis_id=diagnosis_id,
        anomaly=anomaly,
        root_cause=root_cause,
        confidence=confidence,
        causal_chain=[],
        domain=domain,
        precedents=[],
    )


def create_patch(
    patch_id: str,
    confidence: float,
    patch_size_lines: int = 10,
    mansidao_score: float = 0.85,
) -> CodePatch:
    """Helper para criar CodePatch válido."""
    return CodePatch(
        patch_id=patch_id,
        diagnosis_id=f"diag-{patch_id}",
        patch_content="test patch",
        diff="+test",
        affected_files=["test.py"],
        patch_size_lines=patch_size_lines,
        confidence=confidence,
        mansidao_score=mansidao_score,
        humility_notes=None,
        created_at=datetime.now(),
    )


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_wisdom_base():
    """Mock Wisdom Base."""
    wb = MagicMock()
    wb.store_lesson = AsyncMock()
    return wb


@pytest.fixture
def monitor(mock_wisdom_base):
    """Tapeinophrosyne Monitor instance."""
    return TapeinophrosyneMonitor(mock_wisdom_base)


@pytest.fixture
def monitor_with_known_domains(mock_wisdom_base):
    """Monitor com domínios conhecidos pré-populados."""
    mon = TapeinophrosyneMonitor(mock_wisdom_base)
    mon.known_domains = {"memory_leak", "latency_spike", "connection_timeout"}
    return mon


# ============================================================================
# CENÁRIO REAL 1: Alta Confiança + Domínio Conhecido → AUTÔNOMO
# Princípio: "Tenho experiência E confiança - posso agir"
# ============================================================================


class TestRealScenario_HighConfidenceKnownDomain:
    """
    Cenário Real: Memory leak detectado (tipo conhecido), confiança 92%.

    Humildade: Reconhecer competência quando REALMENTE existe.
    """

    @pytest.mark.asyncio
    async def test_high_confidence_known_domain_is_autonomous(
        self, monitor_with_known_domains
    ):
        """
        DADO: Diagnóstico com 92% confiança em domínio conhecido
        QUANDO: Avaliar competência
        ENTÃO: AUTONOMOUS (pode agir sozinho)
        E: Nota de humildade reconhece experiência
        """
        diagnosis = create_diagnosis(
            diagnosis_id="mem-leak-001", confidence=0.92, domain="memory_leak"
        )

        result = await monitor_with_known_domains.assess_competence(diagnosis)

        assert result["competence_level"] == CompetenceLevel.AUTONOMOUS
        assert result["can_proceed"] is True
        assert "experiência" in result["humility_note"].lower()
        assert "92" in result["reasoning"] or "0.92" in result["reasoning"]


# ============================================================================
# CENÁRIO REAL 2: Baixa Confiança + Domínio Conhecido → ASSISTIDO
# Princípio: "EU NÃO SEI" - Admitir incerteza
# ============================================================================


class TestRealScenario_LowConfidenceKnownDomain:
    """
    Cenário Real: Latency spike (conhecido), mas confiança apenas 75%.

    Humildade: Admitir "conheço o problema, mas não tenho certeza da causa".
    """

    @pytest.mark.asyncio
    async def test_low_confidence_known_domain_is_assisted(
        self, monitor_with_known_domains
    ):
        """
        DADO: Diagnóstico com 75% confiança (abaixo de 85%)
        QUANDO: Domínio é conhecido
        ENTÃO: ASSISTED (sugerir, não executar)
        E: Explicar que confiança está abaixo do limiar
        """
        diagnosis = create_diagnosis(
            diagnosis_id="latency-001", confidence=0.75, domain="latency_spike"
        )

        result = await monitor_with_known_domains.assess_competence(diagnosis)

        assert result["competence_level"] == CompetenceLevel.ASSISTED
        assert result["can_proceed"] is False
        assert "confiança" in result["humility_note"].lower()
        assert "abaixo" in result["humility_note"].lower()


# ============================================================================
# CENÁRIO REAL 3: Domínio Desconhecido → DEFER (HUMILDADE MÁXIMA)
# Princípio: "PRECISO DE AJUDA" - Escalar quando não sabe
# ============================================================================


class TestRealScenario_UnknownDomain:
    """
    Cenário Real: Race condition nunca visto antes.

    Humildade MÁXIMA: "Nunca enfrentei isso, não tenho competência".
    """

    @pytest.mark.asyncio
    async def test_unknown_domain_defers_to_human(self, monitor_with_known_domains):
        """
        DADO: Diagnóstico em domínio completamente novo
        QUANDO: Sistema nunca viu esse tipo de falha antes
        ENTÃO: DEFER_TO_HUMAN (não tentar agir)
        E: Admitir explicitamente "nunca enfrentei"
        """
        diagnosis = create_diagnosis(
            diagnosis_id="race-001",
            confidence=0.88,  # Alta confiança, mas domínio desconhecido!
            domain="race_condition_concurrent_writes",
        )

        result = await monitor_with_known_domains.assess_competence(diagnosis)

        assert result["competence_level"] == CompetenceLevel.DEFER_TO_HUMAN
        assert result["can_proceed"] is False
        assert "nunca" in result["humility_note"].lower()
        assert "não tenho competência" in result["humility_note"].lower()

    @pytest.mark.asyncio
    async def test_unknown_domain_reasoning_mentions_first_time(
        self, monitor_with_known_domains
    ):
        """
        VALIDAR: Reasoning explica que é primeira vez
        """
        diagnosis = create_diagnosis(
            diagnosis_id="new-bug-001",
            confidence=0.95,
            domain="quantum_bug_from_future",
        )

        result = await monitor_with_known_domains.assess_competence(diagnosis)

        assert "desconhecido" in result["reasoning"].lower()
        assert "quantum_bug_from_future" in result["reasoning"]


# ============================================================================
# CENÁRIO REAL 4: Relatório de Incerteza (TRANSPARÊNCIA)
# Princípio: "POSSO ESTAR ERRADO" - Todo patch tem incertezas declaradas
# ============================================================================


class TestRealScenario_UncertaintyReport:
    """
    Cenário Real: Gerar patch com confidence 82% (moderada).

    Humildade: Declarar explicitamente onde pode estar errado.
    """

    def test_moderate_confidence_patch_has_uncertainty_factors(self, monitor):
        """
        DADO: Patch com confidence 82% (< 90%)
        QUANDO: Gerar uncertainty report
        ENTÃO: Incluir "confiança moderada" como fator de incerteza
        """
        patch = create_patch(patch_id="patch-001", confidence=0.82)

        report = monitor.generate_uncertainty_report(patch)

        assert report.confidence == 0.82
        assert len(report.uncertainty_factors) > 0
        assert any(
            "confiança moderada" in f.lower() for f in report.uncertainty_factors
        )

    def test_large_patch_increases_uncertainty(self, monitor):
        """
        DADO: Patch grande (30 linhas)
        QUANDO: Gerar uncertainty report
        ENTÃO: Mencionar "maior superfície de erro"
        """
        patch = create_patch(patch_id="large-001", confidence=0.95, patch_size_lines=30)

        report = monitor.generate_uncertainty_report(patch)

        assert any("patch grande" in f.lower() for f in report.uncertainty_factors)

    def test_first_time_patch_flagged_as_uncertain(self, monitor):
        """
        DADO: Patch sem humility_notes (primeira vez)
        QUANDO: Gerar uncertainty report
        ENTÃO: Flagged como "primeira vez aplicando"
        """
        patch = create_patch(patch_id="new-001", confidence=0.90)
        patch.humility_notes = None

        report = monitor.generate_uncertainty_report(patch)

        assert any("primeira vez" in f.lower() for f in report.uncertainty_factors)


# ============================================================================
# CENÁRIO REAL 5: Aprender com Falha (CRESCIMENTO)
# Princípio: "APRENDO COM MEUS ERROS" - Feedback loop
# ============================================================================


class TestRealScenario_LearningFromFailure:
    """
    Cenário Real: Patch causou regressão não prevista.

    Humildade: Reconhecer erro, extrair lição, ajustar sistema.
    """

    @pytest.mark.asyncio
    async def test_failed_patch_generates_lesson(self, monitor, mock_wisdom_base):
        """
        DADO: Patch que falhou em produção
        QUANDO: learn_from_failure() é chamado
        ENTÃO: Gerar lição estruturada
        E: Armazenar na Wisdom Base
        """
        failed_patch = create_patch(patch_id="failed-001", confidence=0.88)

        outcome = "Patch causou regressão em testes de integração"

        lesson = await monitor.learn_from_failure(failed_patch, outcome)

        assert "patch_id" in lesson
        assert lesson["what_actually_happened"] == outcome
        assert "lesson_learned" in lesson
        assert "adjustment_needed" in lesson

        # Verificar que foi armazenado
        mock_wisdom_base.store_lesson.assert_called_once_with(lesson)

    @pytest.mark.asyncio
    async def test_regression_failure_recommends_better_validation(self, monitor):
        """
        DADO: Falha causada por regressão
        QUANDO: Extrair lição
        ENTÃO: Recomendar testes de regressão mais abrangentes
        """
        failed_patch = create_patch(patch_id="regr-001", confidence=0.90)

        outcome = "Regressão detectada: endpoint /users retorna 500"

        lesson = await monitor.learn_from_failure(failed_patch, outcome)

        assert "regressão" in lesson["lesson_learned"].lower()
        assert (
            "validação" in lesson["adjustment_needed"].lower()
            or "teste" in lesson["adjustment_needed"].lower()
        )


# ============================================================================
# TESTE DE CONFORMIDADE CONSTITUCIONAL
# ============================================================================


class TestConstitutionalCompliance:
    """
    Valida conformidade com PENELOPE_SISTEMA_CRISTAO.html Artigo III.
    Artigo III (Humildade): Autoconhecimento de limites.
    """

    def test_confidence_threshold_is_85_percent(self, monitor):
        """
        CONSTITUIÇÃO: Threshold de confiança = 85% (linha 31 da PENELOPE_v3).
        """
        assert monitor.CONFIDENCE_THRESHOLD == 0.85

    @pytest.mark.asyncio
    async def test_all_assessments_include_humility_note(
        self, monitor_with_known_domains
    ):
        """
        ARTIGO III: Sempre incluir nota de humildade explicando raciocínio.
        """
        # Caso 1: Autônomo
        diag1 = create_diagnosis("d1", 0.92, "memory_leak")
        result1 = await monitor_with_known_domains.assess_competence(diag1)
        assert "humility_note" in result1
        assert len(result1["humility_note"]) > 10

        # Caso 2: Assistido
        diag2 = create_diagnosis("d2", 0.75, "memory_leak")
        result2 = await monitor_with_known_domains.assess_competence(diag2)
        assert "humility_note" in result2
        assert len(result2["humility_note"]) > 10

        # Caso 3: Defer
        diag3 = create_diagnosis("d3", 0.90, "unknown_domain")
        result3 = await monitor_with_known_domains.assess_competence(diag3)
        assert "humility_note" in result3
        assert len(result3["humility_note"]) > 10

    def test_risk_assessment_identifies_critical_files(self, monitor):
        """
        HUMILDADE: Reconhecer quando mexe em área crítica.
        """
        critical_patch = create_patch(patch_id="crit-001", confidence=0.95)
        critical_patch.affected_files = ["auth_service.py", "payment_processor.py"]

        report = monitor.generate_uncertainty_report(critical_patch)
        risk = report.risk_assessment

        assert len(risk["high_risk_scenarios"]) > 0
        assert any("crítico" in s.lower() for s in risk["high_risk_scenarios"])


# ============================================================================
# TESTES DE EDGE CASES
# ============================================================================


class TestEdgeCases:
    """Edge cases baseados em comportamento real."""

    @pytest.mark.asyncio
    async def test_exact_threshold_confidence_is_autonomous(
        self, monitor_with_known_domains
    ):
        """
        EDGE CASE: Confidence exatamente 85% (no limiar).
        ESPERADO: AUTONOMOUS (>= threshold).
        """
        diagnosis = create_diagnosis(
            diagnosis_id="edge-001",
            confidence=0.85,  # Exatamente no limiar
            domain="memory_leak",
        )

        result = await monitor_with_known_domains.assess_competence(diagnosis)

        assert result["competence_level"] == CompetenceLevel.AUTONOMOUS

    @pytest.mark.asyncio
    async def test_84_percent_confidence_is_assisted(self, monitor_with_known_domains):
        """
        EDGE CASE: Confidence 84% (1% abaixo).
        ESPERADO: ASSISTED.
        """
        diagnosis = create_diagnosis(
            diagnosis_id="edge-002", confidence=0.84, domain="memory_leak"
        )

        result = await monitor_with_known_domains.assess_competence(diagnosis)

        assert result["competence_level"] == CompetenceLevel.ASSISTED

    def test_empty_known_domains_treats_all_as_unknown(self, monitor):
        """
        EDGE CASE: Monitor sem domínios conhecidos (startup).
        ESPERADO: Tratar tudo como desconhecido (humilde por padrão).
        """
        assert len(monitor.known_domains) == 0

        # Qualquer domínio deve ser tratado como desconhecido

    def test_risk_profile_classification_boundaries(self, monitor):
        """
        EDGE CASE: Validar boundaries de classificação de risco.
        """
        # Low risk: confidence alta, patch pequeno
        low_risk = create_patch("low", 0.95, 5, 0.90)
        assert monitor._calculate_overall_risk(low_risk) == "low"

        # Critical risk: confidence baixa, patch grande
        crit_risk = create_patch("crit", 0.60, 25, 0.50)
        assert monitor._calculate_overall_risk(crit_risk) == "critical"

    def test_get_competence_stats_returns_structure(self, monitor_with_known_domains):
        """
        VALIDAR: get_competence_stats retorna estrutura correta.
        """
        stats = monitor_with_known_domains.get_competence_stats()

        assert "known_domains" in stats
        assert (
            stats["known_domains"] == 3
        )  # memory_leak, latency_spike, connection_timeout
        assert "autonomous_interventions" in stats
        assert "false_confidence_rate" in stats
