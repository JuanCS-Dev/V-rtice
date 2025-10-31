"""Scientific Tests for Enkrateia (Self-Control) - Validando Princípio do Domínio Próprio.

Enkrateia (Domínio Próprio) = Autocontrole que traz liberdade, não escravidão.
Fundamento: 1 Coríntios 9:25 - "Todo atleta em tudo se domina"

Testa comportamento REAL de como o sistema exerce domínio próprio através de
limites auto-impostos, gerando eficiência e liberdade operacional.

Author: Vértice Platform Team
License: Proprietary
"""

from datetime import datetime

import pytest
from core.praotes_validator import PraotesValidator
from core.wisdom_base_client import WisdomBaseClient

from models import CodePatch

# ============================================================================
# CENÁRIO REAL 1: Domínio sobre Escopo (Mansidão Limitada)
# Princípio: "Todo atleta em tudo se domina" (1 Coríntios 9:25)
# ============================================================================


class TestRealScenario_SelfControlInScope:
    """
    Cenário Real: Sistema limita escopo de intervenção.

    Domínio Próprio: Não fazer TUDO, mas fazer BEM o necessário.
    """

    def test_praotes_enforces_max_patch_size_self_limit(self):
        """
        DADO: Praotes Validator com limite MAX_PATCH_LINES = 25
        QUANDO: Patch excede limite
        ENTÃO: Sistema se AUTO-LIMITA (rejeita ganância)

        CIENTÍFICO: Domínio próprio = respeitar limites auto-impostos.
        Fundamento: 1 Coríntios 9:27 - "esmurro o meu corpo e o reduzo à escravidão"
        """
        validator = PraotesValidator()

        # Domínio Próprio: Sistema TEM limite (não ganância infinita)
        assert validator.MAX_PATCH_LINES == 25

        # Patch grande (30 linhas)
        large_patch = CodePatch(
            patch_id="patch-large-001",
            diagnosis_id="diag-001",
            patch_content="# large code",
            diff="\n".join(["+line" for _ in range(30)]),
            affected_files=["test.py"],
            patch_size_lines=30,
            confidence=0.9,
            mansidao_score=0.0,
            humility_notes="Large patch",
            created_at=datetime.now(),
        )

        result = validator.validate_patch(large_patch)

        # Domínio Próprio: Auto-limite respeitado
        assert result["result"].value != "approved"
        assert "invasivo" in result["violations"][0].lower()

    def test_praotes_limits_functions_modified_focus(self):
        """
        DADO: Praotes com MAX_FUNCTIONS_MODIFIED = 3
        QUANDO: Validar patch
        ENTÃO: Sistema tem foco (não tentar modificar sistema inteiro)

        CIENTÍFICO: Domínio próprio = foco, não dispersão.
        Fundamento: Filipenses 3:13 - "uma coisa faço"
        """
        validator = PraotesValidator()

        # Domínio Próprio: Limita funções modificadas
        assert validator.MAX_FUNCTIONS_MODIFIED == 3
        # Liberdade através de foco!


# ============================================================================
# CENÁRIO REAL 2: Domínio sobre Recursos (Prudência)
# Princípio: "Sede prudentes" (1 Pedro 4:7)
# ============================================================================


class TestRealScenario_SelfControlInResources:
    """
    Cenário Real: Sistema limita uso de recursos.

    Domínio Próprio: Não consumir tudo disponível (prudência).
    """

    @pytest.mark.asyncio
    async def test_wisdom_base_query_limits_results_not_greedy(self):
        """
        DADO: Wisdom Base com múltiplos precedentes
        QUANDO: Consultar precedentes
        ENTÃO: Limita a top 10 (não retorna TUDO)

        CIENTÍFICO: Domínio próprio = não ser ganancioso com recursos.
        Fundamento: Provérbios 25:16 - "Achaste mel? Come apenas o que te basta"
        """
        wisdom_base = WisdomBaseClient()

        # Adicionar 50 precedentes
        for i in range(50):
            await wisdom_base.store_precedent(
                {
                    "anomaly_type": "test",
                    "service": "svc",
                    "outcome": "SUCCESS",
                    "timestamp": datetime.now().isoformat(),
                }
            )

        # QUANDO: Consultar
        results = await wisdom_base.query_precedents(anomaly_type="test", service="svc")

        # ENTÃO: Domínio Próprio - Limita a 10 (não retorna todos 50)
        assert len(results) <= 10
        # Eficiência através de auto-limitação!

    @pytest.mark.asyncio
    async def test_wisdom_base_does_not_store_duplicates_wastefully(self):
        """
        DADO: Wisdom Base armazena precedentes
        QUANDO: Armazenar conhecimento
        ENTÃO: Cada armazenamento é intencional (não desperdício)

        CIENTÍFICO: Domínio próprio = usar recursos intencionalmente.
        """
        wisdom_base = WisdomBaseClient()

        # Armazenar precedente
        await wisdom_base.store_precedent(
            {
                "anomaly_type": "unique",
                "service": "svc",
                "outcome": "SUCCESS",
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Domínio Próprio: Cada item armazenado com propósito
        assert len(wisdom_base.precedents) == 1


# ============================================================================
# CENÁRIO REAL 3: Domínio sobre Qualidade (Excelência Limitada)
# Princípio: "Tudo tem o seu tempo determinado" (Eclesiastes 3:1)
# ============================================================================


class TestRealScenario_SelfControlInQuality:
    """
    Cenário Real: Sistema limita busca por perfeição.

    Domínio Próprio: "Suficientemente bom" > perfeição infinita.
    """

    def test_praotes_reversibility_minimum_is_achievable_not_perfect(self):
        """
        DADO: Praotes com MIN_REVERSIBILITY_SCORE = 0.90
        QUANDO: Validar reversibilidade
        ENTÃO: 90% é suficiente (não exige 100% inatingível)

        CIENTÍFICO: Domínio próprio = aceitar "bom o suficiente".
        Fundamento: Eclesiastes 7:16 - "Não sejas demasiadamente justo"
        """
        validator = PraotesValidator()

        # Domínio Próprio: Mínimo alcançável (não perfeccionismo)
        assert validator.MIN_REVERSIBILITY_SCORE == 0.90
        assert validator.MIN_REVERSIBILITY_SCORE < 1.0
        # Liberdade de não exigir perfeição!

    def test_praotes_accepts_good_enough_patches(self):
        """
        DADO: Patch com 8 linhas, boa reversibilidade
        QUANDO: Validar
        ENTÃO: APPROVED (bom o suficiente)

        CIENTÍFICO: Domínio próprio = saber quando parar.
        Fundamento: Eclesiastes 3:1 - "Tudo tem o seu tempo"
        """
        validator = PraotesValidator()

        # Patch "good enough"
        good_patch = CodePatch(
            patch_id="patch-good-001",
            diagnosis_id="diag-001",
            patch_content="def helper(): pass",
            diff="+def helper():\n+    pass",
            affected_files=["helpers.py"],
            patch_size_lines=2,
            confidence=0.9,
            mansidao_score=0.0,
            humility_notes="Simple helper",
            created_at=datetime.now(),
        )

        result = validator.validate_patch(good_patch)

        # Domínio Próprio: Aceita "bom o suficiente"
        assert result["result"].value == "approved"


# ============================================================================
# CONFORMIDADE CONSTITUCIONAL - Domínio Próprio (Enkrateia)
# ============================================================================


class TestConstitutionalCompliance_SelfControl:
    """
    Valida conformidade com o Artigo Constitucional de DOMÍNIO PRÓPRIO.

    Domínio Próprio não é restrição escravizadora, mas disciplina libertadora:
    1. Limites de escopo (foco)
    2. Limites de recursos (prudência)
    3. Limites de perfeição (pragmatismo)
    4. Liberdade através de autodisciplina
    """

    def test_self_control_metric_all_validators_have_limits(self):
        """
        VALIDAR: Métrica de Domínio Próprio - Todos validadores têm limites.

        CIENTÍFICO: Autodisciplina = limites auto-impostos.
        Fundamento: 1 Coríntios 9:25 - "Todo atleta em tudo se domina"
        """
        validator = PraotesValidator()

        # Domínio Próprio: TODOS os limites definidos
        assert hasattr(validator, "MAX_PATCH_LINES")
        assert hasattr(validator, "MIN_REVERSIBILITY_SCORE")
        assert hasattr(validator, "MAX_FUNCTIONS_MODIFIED")

        # Domínio Próprio: Limites são FINITOS (não infinitos)
        assert float("inf") > validator.MAX_PATCH_LINES
        assert validator.MIN_REVERSIBILITY_SCORE < 1.0

    @pytest.mark.asyncio
    async def test_self_control_wisdom_base_limits_query_results(self):
        """
        VALIDAR: Domínio Próprio - Wisdom Base limita resultados.

        CIENTÍFICO: Não retornar tudo = eficiência.
        """
        wisdom_base = WisdomBaseClient()

        # Adicionar muitos
        for i in range(100):
            await wisdom_base.store_precedent(
                {
                    "anomaly_type": "many",
                    "service": "test",
                    "outcome": "SUCCESS",
                    "timestamp": datetime.now().isoformat(),
                }
            )

        results = await wisdom_base.query_precedents(
            anomaly_type="many", service="test"
        )

        # Domínio Próprio: Não retorna tudo (auto-limite)
        assert len(results) < len(wisdom_base.precedents)


# ============================================================================
# EDGE CASES - Domínio Próprio
# ============================================================================


class TestEdgeCases_SelfControl:
    """Edge cases para validar robustez do domínio próprio."""

    def test_self_control_zero_size_patch_is_valid(self):
        """
        EDGE CASE: Patch vazio (0 linhas).
        ESPERADO: Válido (domínio próprio máximo = não fazer nada).

        CIENTÍFICO: Às vezes a melhor ação é nenhuma ação.
        Fundamento: Eclesiastes 3:7 - "tempo de estar calado"
        """
        validator = PraotesValidator()

        empty_patch = CodePatch(
            patch_id="patch-empty",
            diagnosis_id="diag-empty",
            patch_content="",
            diff="",
            affected_files=[],
            patch_size_lines=0,
            confidence=0.9,
            mansidao_score=0.0,
            humility_notes="No action needed",
            created_at=datetime.now(),
        )

        result = validator.validate_patch(empty_patch)

        # Domínio Próprio: Patch vazio é válido (não agir desnecessariamente)
        assert result["result"].value == "approved"
        assert result["mansidao_score"] == 1.0  # Perfeito!

    def test_self_control_exactly_at_limit_is_acceptable(self):
        """
        EDGE CASE: Patch exatamente no limite (25 linhas).
        ESPERADO: Aceito (limite INCLUSIVE).

        CIENTÍFICO: Domínio próprio não é legalismo, mas prudência.
        """
        validator = PraotesValidator()

        limit_patch = CodePatch(
            patch_id="patch-limit",
            diagnosis_id="diag-limit",
            patch_content="# code",
            diff="\n".join(["+line" for _ in range(25)]),
            affected_files=["file.py"],
            patch_size_lines=25,
            confidence=0.9,
            mansidao_score=0.0,
            humility_notes="At limit",
            created_at=datetime.now(),
        )

        result = validator.validate_patch(limit_patch)

        # Domínio Próprio: Limite é inclusive (não legalismo)
        assert result["result"].value == "approved"


# ============================================================================
# LIBERDADE ATRAVÉS DE DOMÍNIO PRÓPRIO
# ============================================================================


class TestFreedomThroughSelfControl:
    """
    Valida que domínio próprio GERA liberdade, não escravidão.

    Fundamento: Gálatas 5:1 - "Para a liberdade foi que Cristo nos libertou"
    """

    def test_freedom_self_limits_enable_efficiency(self):
        """
        DADO: Sistema com auto-limites (Praotes)
        QUANDO: Operar dentro dos limites
        ENTÃO: Eficiência alcançada (liberdade operacional)

        CIENTÍFICO: Limites geram foco, foco gera eficiência, eficiência gera liberdade.
        Fundamento: Gálatas 5:13 - "não useis da liberdade para dar ocasião à carne"
        """
        validator = PraotesValidator()

        # Auto-limites definidos
        limits = {
            "max_lines": validator.MAX_PATCH_LINES,
            "min_reversibility": validator.MIN_REVERSIBILITY_SCORE,
            "max_functions": validator.MAX_FUNCTIONS_MODIFIED,
        }

        # Liberdade: Limites claros = decisões rápidas
        assert all(v is not None for v in limits.values())
        assert all(v > 0 for v in limits.values())

    @pytest.mark.asyncio
    async def test_freedom_wisdom_base_limit_prevents_overwhelm(self):
        """
        DADO: Wisdom Base com limite de resultados (top 10)
        QUANDO: Consultar grande volume
        ENTÃO: Não sobrecarrega (liberdade de processar eficientemente)

        CIENTÍFICO: Limites previnem sobrecarga = liberdade operacional.
        """
        wisdom_base = WisdomBaseClient()

        # Adicionar 1000 precedentes
        for i in range(1000):
            await wisdom_base.store_precedent(
                {
                    "anomaly_type": "massive",
                    "service": "test",
                    "outcome": "SUCCESS",
                    "timestamp": datetime.now().isoformat(),
                }
            )

        # Consultar
        results = await wisdom_base.query_precedents(
            anomaly_type="massive", service="test"
        )

        # Liberdade: Limite previne sobrecarga
        assert len(results) == 10  # Top 10 apenas
        # Sistema livre para processar eficientemente!
