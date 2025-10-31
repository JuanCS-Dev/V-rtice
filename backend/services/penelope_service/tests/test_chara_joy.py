"""Scientific Tests for Chara (Joy) - Validando Princípio da Alegria.

Chara (Alegria) = Alegria profunda que vem do Senhor, independente de circunstâncias.
Fundamento: Filipenses 4:4 - "Alegrai-vos sempre no Senhor; outra vez digo: alegrai-vos!"

Testa comportamento REAL de como o sistema expressa alegria em sucessos,
aprende alegremente com falhas, e celebra progresso.

Author: Vértice Platform Team
License: Proprietary
"""

from datetime import datetime

import pytest
from core.tapeinophrosyne_monitor import TapeinophrosyneMonitor
from core.wisdom_base_client import WisdomBaseClient

from models import CodePatch

# ============================================================================
# CENÁRIO REAL 1: Alegria em Sucessos (Celebrar Vitórias)
# Princípio: "A alegria do SENHOR é a vossa força" (Neemias 8:10)
# ============================================================================


class TestRealScenario_JoyInSuccess:
    """
    Cenário Real: Sistema completa intervenção bem-sucedida.

    Alegria: Celebrar sucesso, registrar aprendizado positivo, encorajar.
    """

    @pytest.mark.asyncio
    async def test_successful_intervention_stores_joyful_precedent(self):
        """
        DADO: Intervenção bem-sucedida (bug corrigido, sistema restaurado)
        QUANDO: Resultado registrado na Wisdom Base
        ENTÃO: Precedente armazenado com métricas de melhoria
        E: Sucesso pode ser recuperado para inspirar futuras decisões

        CIENTÍFICO: Sistema aprende alegremente com sucessos, não apenas falhas.
        Fundamento: Filipenses 4:4 - "Alegrai-vos sempre"
        """
        # DADO: Setup
        wisdom_base = WisdomBaseClient()

        # Sucesso real: Latência alta corrigida
        successful_intervention = {
            "anomaly_type": "high_latency",
            "service": "api-gateway",
            "outcome": "SUCCESS",
            "metrics_before": {"latency_p99_ms": 2500, "affected_users": 1200},
            "metrics_after": {"latency_p99_ms": 180, "affected_users": 0},
            "timestamp": datetime.now().isoformat(),
        }

        # QUANDO: Armazenar precedente
        precedent_id = await wisdom_base.store_precedent(successful_intervention)

        # ENTÃO: Precedente armazenado
        assert precedent_id is not None
        assert len(wisdom_base.precedents) == 1

        # Alegria: Sucesso pode ser recuperado
        precedents = await wisdom_base.query_precedents(
            anomaly_type="high_latency", service="api-gateway"
        )
        assert len(precedents) == 1
        assert precedents[0]["outcome"] == "SUCCESS"

    @pytest.mark.asyncio
    async def test_success_metrics_show_improvement_joy(self):
        """
        DADO: Múltiplas intervenções bem-sucedidas ao longo do tempo
        QUANDO: Consultar estatísticas da Wisdom Base
        ENTÃO: Estatísticas mostram tendência positiva

        CIENTÍFICO: Progresso mensurável gera alegria objetiva.
        Fundamento: Neemias 8:10 - "A alegria do SENHOR é a vossa força"
        """
        # DADO: Setup com múltiplos sucessos
        wisdom_base = WisdomBaseClient()

        # Simular 10 intervenções bem-sucedidas
        for i in range(10):
            await wisdom_base.store_precedent(
                {
                    "anomaly_type": f"bug_{i}",
                    "service": "test-service",
                    "outcome": "SUCCESS",
                    "timestamp": datetime.now().isoformat(),
                }
            )

        # QUANDO: Contar precedentes
        total = len(wisdom_base.precedents)

        # ENTÃO: Alegria nas métricas
        assert total == 10
        # Todos os precedentes armazenados (crescimento)


# ============================================================================
# CENÁRIO REAL 2: Alegria no Aprendizado (Mesmo em Falhas)
# Princípio: "Tende por motivo de grande alegria o passardes por várias
#             provações, sabendo que a provação da vossa fé produz perseverança"
#             (Tiago 1:2-3)
# ============================================================================


class TestRealScenario_JoyInLearning:
    """
    Cenário Real: Sistema falha, mas aprende com o erro.

    Alegria: Não desespero, mas alegria no crescimento através da provação.
    """

    @pytest.mark.asyncio
    async def test_failure_generates_joyful_lesson_not_despair(self):
        """
        DADO: Patch aplicado falhou (causou regressão)
        QUANDO: Sistema aprende com falha
        ENTÃO: Lição armazenada com recomendações de melhoria
        E: Falha transformada em oportunidade de crescimento

        CIENTÍFICO: Falhas são oportunidades de crescimento, não motivo de desespero.
        Fundamento: Tiago 1:2 - "Tende por motivo de grande alegria as provações"
        """
        # DADO: Setup
        wisdom_base = WisdomBaseClient()
        tapeinophrosyne = TapeinophrosyneMonitor(wisdom_base)

        # Falha real: Patch causou regressão
        failed_patch = CodePatch(
            patch_id="patch-regression-001",
            diagnosis_id="diag-001",
            patch_content="# broken code",
            diff="+broken_line",
            affected_files=["auth.py"],
            patch_size_lines=1,
            confidence=0.88,
            mansidao_score=0.85,
            humility_notes="First time patching auth",
            created_at=datetime.now(),
        )

        actual_outcome = "REGRESSION: Authentication failed after patch deployment"

        # QUANDO: Aprender com falha
        lesson = await tapeinophrosyne.learn_from_failure(
            failed_patch=failed_patch, actual_outcome=actual_outcome
        )

        # ENTÃO: Lição é construtiva (alegria no aprendizado)
        assert "lesson_learned" in lesson
        assert "adjustment_needed" in lesson
        # Alegria: Sempre tem recomendação de melhoria
        assert lesson["adjustment_needed"] is not None

    @pytest.mark.asyncio
    async def test_learned_lessons_are_stored_for_future_reference(self):
        """
        DADO: Sistema aprende lição de uma falha
        QUANDO: Lição armazenada na Wisdom Base
        ENTÃO: Lição pode ser consultada no futuro
        E: Conhecimento permanece (não se perde)

        CIENTÍFICO: Aprendizado efetivo (conhecimento persistente).
        Fundamento: Provérbios 4:11 - "Ensino-te o caminho da sabedoria"
        """
        # DADO: Setup
        wisdom_base = WisdomBaseClient()

        # Lição aprendida
        lesson = {
            "context": "auth_changes",
            "lesson_learned": "Always run integration tests before deploying auth changes",
            "affected_files": ["auth.py"],
            "timestamp": datetime.now().isoformat(),
        }

        # QUANDO: Armazenar lição
        lesson_id = await wisdom_base.store_lesson(lesson)

        # ENTÃO: Lição armazenada
        assert lesson_id is not None
        assert len(wisdom_base.lessons) == 1

        # Alegria: Conhecimento permanece
        stored_lesson = wisdom_base.lessons[0]
        assert "lesson_learned" in stored_lesson


# ============================================================================
# CENÁRIO REAL 3: Alegria no Progresso (Métricas de Melhoria)
# Princípio: "O caminho dos justos é como a luz da aurora, que brilha cada
#             vez mais até ser dia perfeito" (Provérbios 4:18)
# ============================================================================


class TestRealScenario_JoyInProgress:
    """
    Cenário Real: Sistema melhora ao longo do tempo.

    Alegria: Celebrar progresso incremental, não apenas perfeição final.
    """

    @pytest.mark.asyncio
    async def test_wisdom_base_grows_over_time_showing_progress(self):
        """
        DADO: Sistema opera por período de tempo
        QUANDO: Precedentes e lições acumulados
        ENTÃO: Wisdom Base cresce (conhecimento aumenta)

        CIENTÍFICO: Crescimento demonstrável = alegria objetiva.
        Fundamento: Provérbios 4:18 - "brilha cada vez mais"
        """
        # DADO: Setup
        wisdom_base = WisdomBaseClient()

        # Simular crescimento ao longo do tempo
        initial_size = len(wisdom_base.precedents) + len(wisdom_base.lessons)

        # Adicionar conhecimento
        for i in range(5):
            await wisdom_base.store_precedent(
                {
                    "anomaly_type": f"case_{i}",
                    "service": "test",
                    "outcome": "SUCCESS",
                    "timestamp": datetime.now().isoformat(),
                }
            )

        for i in range(3):
            await wisdom_base.store_lesson(
                {
                    "context": f"lesson_{i}",
                    "lesson_learned": f"Learned something {i}",
                    "timestamp": datetime.now().isoformat(),
                }
            )

        # QUANDO: Medir crescimento
        final_size = len(wisdom_base.precedents) + len(wisdom_base.lessons)

        # ENTÃO: Progresso visível
        growth = final_size - initial_size
        assert growth == 8  # 5 precedentes + 3 lições
        # Alegria: Conhecimento aumentou


# ============================================================================
# CONFORMIDADE CONSTITUCIONAL - Alegria (Chara)
# ============================================================================


class TestConstitutionalCompliance_Joy:
    """
    Valida conformidade com o Artigo Constitucional de ALEGRIA.

    Alegria não é otimismo cego, mas confiança fundamentada em:
    1. Sucessos celebrados objetivamente
    2. Falhas transformadas em aprendizado
    3. Progresso incremental validado
    4. Conhecimento compartilhado para encorajar
    """

    @pytest.mark.asyncio
    async def test_joy_metric_wisdom_base_accepts_both_success_and_failure(self):
        """
        VALIDAR: Métrica de Alegria - Sistema aceita AMBOS sucessos e falhas.

        CIENTÍFICO: Alegria verdadeira não nega realidade, mas encontra
        crescimento em ambas circunstâncias.

        Fundamento: Romanos 5:3-4 - "nos gloriamos até nas tribulações,
        sabendo que a tribulação produz perseverança"
        """
        wisdom_base = WisdomBaseClient()

        # Adicionar sucessos E falhas
        await wisdom_base.store_precedent(
            {
                "anomaly_type": "success_case",
                "service": "test",
                "outcome": "SUCCESS",
                "timestamp": datetime.now().isoformat(),
            }
        )

        await wisdom_base.store_lesson(
            {
                "context": "failure_case",
                "lesson_learned": "Learned from failure",
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Alegria: Ambos armazenados (verdade completa)
        assert len(wisdom_base.precedents) == 1
        assert len(wisdom_base.lessons) == 1

    @pytest.mark.asyncio
    async def test_joy_in_learning_all_failures_can_generate_lessons(self):
        """
        VALIDAR: Alegria no Aprendizado - Falhas podem gerar lições.

        CIENTÍFICO: Capacidade de transformar falha em crescimento.
        Fundamento: Tiago 1:2 - "Tende por motivo de grande alegria as provações"
        """
        wisdom_base = WisdomBaseClient()
        tapeinophrosyne = TapeinophrosyneMonitor(wisdom_base)

        # Simular falha
        patch = CodePatch(
            patch_id="patch-001",
            diagnosis_id="diag-001",
            patch_content="# code",
            diff="+line",
            affected_files=["test.py"],
            patch_size_lines=1,
            confidence=0.9,
            mansidao_score=0.9,
            humility_notes="test",
            created_at=datetime.now(),
        )

        # Aprender com falha
        lesson = await tapeinophrosyne.learn_from_failure(patch, "ERROR: Test failed")

        # Alegria: Falha virou aprendizado
        assert "lesson_learned" in lesson
        assert lesson["lesson_learned"] is not None


# ============================================================================
# EDGE CASES - Alegria
# ============================================================================


class TestEdgeCases_Joy:
    """Edge cases para validar robustez da alegria."""

    @pytest.mark.asyncio
    async def test_joy_persists_even_with_zero_successes_initially(self):
        """
        EDGE CASE: Sistema novo (0 sucessos ainda).
        ESPERADO: Alegria não depende de sucessos passados, mas de esperança.

        CIENTÍFICO: Alegria vem do Senhor, não apenas de sucessos acumulados.
        Fundamento: Habacuque 3:17-18 - "Ainda que a figueira não floresça...
                    todavia, eu me alegro no SENHOR"
        """
        wisdom_base = WisdomBaseClient()

        # Sistema vazio (sem sucessos)
        assert len(wisdom_base.precedents) == 0
        assert len(wisdom_base.lessons) == 0

        # Alegria: Estrutura pronta para registrar primeiro sucesso
        # (esperança, não desespero)
        assert wisdom_base.precedents is not None
        assert wisdom_base.lessons is not None

    @pytest.mark.asyncio
    async def test_joy_acknowledges_reality_stores_both_outcomes(self):
        """
        EDGE CASE: Sistema com sucessos E falhas.
        ESPERADO: Alegria honesta (não otimismo cego).

        CIENTÍFICO: Alegria baseada em verdade (Aletheia), não em ilusão.
        """
        wisdom_base = WisdomBaseClient()

        # Armazenar sucessos e falhas
        await wisdom_base.store_precedent(
            {
                "anomaly_type": "success",
                "service": "test",
                "outcome": "SUCCESS",
                "timestamp": datetime.now().isoformat(),
            }
        )

        await wisdom_base.store_lesson(
            {
                "context": "failure",
                "lesson_learned": "Failed but learned",
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Alegria honesta: Ambos armazenados (verdade completa)
        assert len(wisdom_base.precedents) == 1
        assert len(wisdom_base.lessons) == 1
        # Não esconder falhas, mas aprender com elas
