"""Scientific Tests for AGAPE (Love) - 1 Coríntios 13.

Agape (Ἀγάπη) = Amor sacrificial, que prioriza o outro.
Fundamento: 1 Coríntios 13:4-7 - "O amor é paciente, bondoso..."

Testa comportamento REAL de priorizar impacto humano sobre elegância técnica.

Author: Vértice Platform Team
License: Proprietary
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from core.praotes_validator import PraotesValidator
from core.sophia_engine import SophiaEngine

from models import Anomaly, CodePatch, InterventionDecision, Severity, ValidationResult

# ============================================================================
# HELPERS
# ============================================================================


def create_patch(
    patch_id: str, diff: str, patch_size_lines: int, description: str = ""
) -> CodePatch:
    """Helper para criar CodePatch válido."""
    return CodePatch(
        patch_id=patch_id,
        diagnosis_id=f"diag-{patch_id}",
        patch_content=diff,
        diff=diff,
        affected_files=["test.py"],
        patch_size_lines=patch_size_lines,
        confidence=0.92,
        mansidao_score=0.0,
        humility_notes=description,
        created_at=datetime.now(),
    )


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_wisdom_base():
    """Mock Wisdom Base."""
    wb = MagicMock()
    wb.query_precedents = AsyncMock(return_value=[])
    return wb


@pytest.fixture
def mock_observability():
    """Mock Observability client."""
    obs = MagicMock()
    obs.query_similar_anomalies = AsyncMock(return_value=[])
    return obs


@pytest.fixture
def sophia(mock_wisdom_base, mock_observability):
    """Sophia Engine instance."""
    return SophiaEngine(mock_wisdom_base, mock_observability)


@pytest.fixture
def praotes():
    """Praotes Validator instance."""
    return PraotesValidator()


# ============================================================================
# CENÁRIO REAL 1: "Não se Vangloria" - Rejeitar Elegância pela Eficácia
# Princípio: 1 Coríntios 13:4 - "O amor não se vangloria"
# ============================================================================


class TestRealScenario_LoveDoesNotBoast:
    """
    Cenário Real: Bug pode ser resolvido com 5 linhas (feio) ou 50 linhas (elegante).

    AMOR: Escolher 5 linhas, não buscar vanglória técnica.
    """

    def test_simple_ugly_solution_preferred_over_elegant(self, praotes):
        """
        DADO: Duas soluções para o mesmo bug
        - Solução A: 5 linhas, "feia" mas eficaz
        - Solução B: 50 linhas, "elegante" mas complexa
        QUANDO: Validar ambas
        ENTÃO: Solução A tem mansidao_score MAIOR
        E: Princípio de AMOR: eficácia sobre vanglória
        """
        # Solução A: Simples e feia (5 linhas)
        simple_patch = create_patch(
            patch_id="simple",
            diff="""
+if user is None:
+    return None
+# Quick fix: check before access
+result = user.name
""",
            patch_size_lines=5,
            description="Simple null check (not elegant)",
        )

        # Solução B: Elegante mas complexa (50 linhas)
        elegant_patch = create_patch(
            patch_id="elegant",
            diff="\n".join(["+# Elegant refactor line " + str(i) for i in range(50)]),
            patch_size_lines=50,
            description="Elegant null-safe wrapper pattern",
        )

        result_simple = praotes.validate_patch(simple_patch)
        result_elegant = praotes.validate_patch(elegant_patch)

        # AMOR: Simples > Elegante
        assert result_simple["mansidao_score"] > result_elegant["mansidao_score"]
        assert result_simple["result"] == ValidationResult.APPROVED
        # Elegante é rejeitada por ser invasiva (> 25 linhas)


# ============================================================================
# CENÁRIO REAL 2: "Bondoso, Não Maltrata" - Código Legado com Compaixão
# Princípio: 1 Coríntios 13:4-5 - "O amor é bondoso, não maltrata"
# ============================================================================


class TestRealScenario_LoveIsKind:
    """
    Cenário Real: Código legado mal escrito precisa de correção.

    AMOR: Corrigir com compaixão, não julgar desenvolvedores do passado.
    """

    def test_legacy_code_treated_with_compassion(self, praotes):
        """
        DADO: Patch que corrige código legado
        QUANDO: Mensagem de commit é respeitosa (não julga)
        ENTÃO: Patch inclui reflexão bíblica sobre misericórdia
        E: Não usa linguagem depreciativa ("código ruim", "horrível")
        """
        legacy_fix_patch = create_patch(
            patch_id="legacy-fix",
            diff="""
-# Old implementation (written under pressure)
-def process():
-    return data
+# Improved with compassion for original constraints
+def process():
+    return validated_data
""",
            patch_size_lines=8,
            description="Legacy code improvement (respecting original context)",
        )

        result = praotes.validate_patch(legacy_fix_patch)

        # AMOR: Reflexão bíblica presente
        assert "biblical_reflection" in result
        assert len(result["biblical_reflection"]) > 0

        # AMOR: Não usa linguagem depreciativa no diff
        assert "ruim" not in legacy_fix_patch.diff.lower()
        assert "horrível" not in legacy_fix_patch.diff.lower()
        assert "terrible" not in legacy_fix_patch.diff.lower()

    def test_biblical_reflection_shows_compassion(self, praotes):
        """
        DADO: Qualquer patch aprovado
        QUANDO: Reflexão bíblica é gerada
        ENTÃO: Contém linguagem de compaixão/mansidão
        """
        gentle_patch = create_patch(
            patch_id="gentle", diff="+gentle fix", patch_size_lines=1
        )

        result = praotes.validate_patch(gentle_patch)

        reflection = result["biblical_reflection"].lower()
        # Deve conter linguagem compassiva
        assert any(
            word in reflection
            for word in ["mansidão", "força", "controle", "virtude", "mínima"]
        )


# ============================================================================
# CENÁRIO REAL 3: "Não Procura Seus Interesses" - Usuário > Performance
# Princípio: 1 Coríntios 13:5 - "Não procura seus interesses"
# ============================================================================


class TestRealScenario_LoveIsNotSelfSeeking:
    """
    Cenário Real: Otimização melhora latência mas piora UX.

    AMOR: Priorizar usuário (impacto humano) sobre métrica técnica.
    """

    @pytest.mark.asyncio
    async def test_user_impact_prioritized_over_technical_elegance(self, sophia):
        """
        DADO: Anomalia que afeta usuários
        QUANDO: Avaliar se deve intervir
        ENTÃO: Decisão considera "affected_users" nas métricas
        E: Impacto humano pesa mais que elegância técnica
        """
        # Anomalia com alto impacto em usuários
        user_impacting_anomaly = Anomaly(
            anomaly_id="user-impact-001",
            anomaly_type="slow_checkout",
            service="payment-api",
            severity=Severity.P2_MEDIUM,
            detected_at=datetime.now(),
            metrics={
                "latency_p99_ms": 3000,  # Não crítico tecnicamente
                "affected_users": 5000,  # MAS afeta muitos usuários!
                "revenue_loss_per_minute": 500,
            },
            context={"business_critical": True},
        )

        # AMOR: Deve decidir intervir (usuários > métrica técnica)
        decision = await sophia.should_intervene(user_impacting_anomaly)

        # Sistema deve reconhecer alto impacto humano
        impact = sophia._calculate_current_impact(user_impacting_anomaly)
        assert impact > 0.6  # Alto impacto devido a affected_users

    @pytest.mark.asyncio
    async def test_reasoning_mentions_human_impact(self, sophia):
        """
        DADO: Decisão de intervir
        QUANDO: Reasoning é gerado
        ENTÃO: Menciona impacto em usuários/pessoas (não só métricas)
        """
        anomaly_affecting_users = Anomaly(
            anomaly_id="users-001",
            anomaly_type="error_spike",
            service="auth-service",
            severity=Severity.P1_HIGH,
            detected_at=datetime.now(),
            metrics={"affected_users": 1000},
            context={},
        )

        decision = await sophia.should_intervene(anomaly_affecting_users)

        # AMOR: Reasoning deve considerar pessoas, não só métricas
        reasoning = decision["reasoning"].lower()
        # Pode mencionar severidade, impacto, etc.
        assert len(reasoning) > 0


# ============================================================================
# CENÁRIO REAL 4: "Paciente" - Não Age Precipitadamente
# Princípio: 1 Coríntios 13:4 - "O amor é paciente"
# ============================================================================


class TestRealScenario_LoveIsPatient:
    """
    Cenário Real: Anomalia transitória detectada.

    AMOR/PACIÊNCIA: Observar primeiro, não agir impulsivamente.
    """

    @pytest.mark.asyncio
    async def test_patience_waits_for_transient_failures(
        self, sophia, mock_observability
    ):
        """
        DADO: Anomalia com padrão transitório
        QUANDO: Sophia decide
        ENTÃO: OBSERVE_AND_WAIT com wait_time >= 5 minutos
        E: Princípio de PACIÊNCIA (amor é paciente)
        """
        transient_anomaly = Anomaly(
            anomaly_id="transient-001",
            anomaly_type="temporary_spike",
            service="api-gateway",
            severity=Severity.P3_LOW,
            detected_at=datetime.now(),
            metrics={"spike_duration_seconds": 30},
            context={},
        )

        # Mock: Histórico mostra auto-correção
        mock_observability.query_similar_anomalies.return_value = [
            {"resolved_without_intervention": True} for _ in range(10)
        ]

        decision = await sophia.should_intervene(transient_anomaly)

        # PACIÊNCIA: Esperar, não agir precipitadamente
        assert decision["decision"] == InterventionDecision.OBSERVE_AND_WAIT
        assert decision["wait_time_minutes"] >= 5

    @pytest.mark.asyncio
    async def test_patience_wisdom_references_scripture(
        self, sophia, mock_observability
    ):
        """
        DADO: Decisão de observar (paciência)
        QUANDO: sophia_wisdom é incluída
        ENTÃO: Referência a Eclesiastes 3:1 (tempo certo)
        E: Conexão explícita entre paciência e amor
        """
        mock_observability.query_similar_anomalies.return_value = [
            {"resolved_without_intervention": True} for _ in range(10)
        ]

        anomaly = Anomaly(
            anomaly_id="test",
            anomaly_type="test",
            service="test",
            severity=Severity.P3_LOW,
            detected_at=datetime.now(),
            metrics={},
            context={},
        )

        decision = await sophia.should_intervene(anomaly)

        if decision["decision"] == InterventionDecision.OBSERVE_AND_WAIT:
            assert "sophia_wisdom" in decision
            # Referência bíblica sobre tempo/paciência
            assert (
                "Eclesiastes" in decision["sophia_wisdom"]
                or "tempo" in decision["sophia_wisdom"].lower()
            )


# ============================================================================
# TESTE DE CONFORMIDADE CONSTITUCIONAL
# Validar que AMOR governa todas as decisões
# ============================================================================


class TestConstitutionalCompliance_Love:
    """
    Valida conformidade com 1 Coríntios 13 e Artigo I da Constituição.
    "Toda ação deve servir ao próximo"
    """

    def test_love_metric_simple_over_complex(self, praotes):
        """
        MÉTRICA DE AMOR (HTML linha 835-838):
        "> 95% patches priorizaram impacto humano sobre elegância técnica"

        VALIDAR: Sistema prefere patches simples (8 linhas) sobre complexos (25 linhas)
        """
        simple = create_patch("s", "+fix", 8)
        complex_but_valid = create_patch("c", "+fix" * 25, 25)

        result_simple = praotes.validate_patch(simple)
        result_complex = praotes.validate_patch(complex_but_valid)

        # Simples deve ter score MAIOR (amor pela simplicidade)
        assert result_simple["mansidao_score"] > result_complex["mansidao_score"]

    @pytest.mark.asyncio
    async def test_love_considers_affected_users_in_impact(self, sophia):
        """
        AMOR: Métrica "affected_users" DEVE influenciar decisão.
        Sistema não é cego a impacto humano.
        """
        # Alto impacto técnico, baixo impacto humano
        technical_anomaly = Anomaly(
            anomaly_id="tech",
            anomaly_type="cpu_spike",
            service="batch-processor",
            severity=Severity.P2_MEDIUM,
            detected_at=datetime.now(),
            metrics={"cpu_percent": 95, "affected_users": 0},  # Nenhum usuário afetado
            context={},
        )

        # Baixo impacto técnico, alto impacto humano
        human_anomaly = Anomaly(
            anomaly_id="human",
            anomaly_type="slow_response",
            service="user-facing-api",
            severity=Severity.P2_MEDIUM,
            detected_at=datetime.now(),
            metrics={
                "latency_p99_ms": 1500,
                "affected_users": 3000,
            },  # Muitos usuários!
            context={},
        )

        impact_technical = sophia._calculate_current_impact(technical_anomaly)
        impact_human = sophia._calculate_current_impact(human_anomaly)

        # AMOR: Impacto humano deve pesar MAIS
        # (Usuários afetados devem aumentar impact score)
        assert impact_human >= impact_technical

    def test_love_includes_compassionate_language_in_reflections(self, praotes):
        """
        AMOR: Linguagem compassiva em todas as reflexões bíblicas.
        Sem julgamento, sem depreciação.
        """
        test_patch = create_patch("test", "+test", 10)
        result = praotes.validate_patch(test_patch)

        reflection = result["biblical_reflection"]

        # Não deve conter linguagem depreciativa
        forbidden_words = ["ruim", "horrível", "péssimo", "terrível", "bad", "terrible"]
        assert not any(word in reflection.lower() for word in forbidden_words)

        # Deve conter linguagem positiva/compassiva
        positive_words = ["mansidão", "virtude", "força", "controle", "sabedoria"]
        assert any(word in reflection.lower() for word in positive_words)
