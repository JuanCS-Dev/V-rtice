"""Scientific Tests for Praotes Validator - Validando Princípio da Mansidão.

Praotes (Mansidão) = Força sob controle.
Fundamento: Mateus 5:5 - "Bem-aventurados os mansos, porque herdarão a terra"

Testa comportamento REAL de validação de patches segundo princípios bíblicos.

Author: Vértice Platform Team
License: Proprietary
"""

from datetime import datetime

import pytest
from core.praotes_validator import PraotesValidator

from models import CodePatch, ValidationResult

# ============================================================================
# HELPERS - Criar patches válidos
# ============================================================================


def create_patch(
    patch_id: str,
    diff: str,
    affected_files: list,
    patch_size_lines: int,
    description: str = "",
) -> CodePatch:
    """Helper para criar CodePatch válido com todos os campos."""
    return CodePatch(
        patch_id=patch_id,
        diagnosis_id=f"diag-{patch_id}",
        patch_content=diff,
        diff=diff,
        affected_files=affected_files,
        patch_size_lines=patch_size_lines,
        confidence=0.92,
        mansidao_score=0.0,  # Será calculado pelo validator
        humility_notes=description,
        created_at=datetime.now(),
    )


# ============================================================================
# FIXTURES - Patches Realísticos
# ============================================================================


@pytest.fixture
def validator():
    """Praotes Validator instance."""
    return PraotesValidator()


@pytest.fixture
def perfect_patch():
    """
    Patch PERFEITO segundo Mansidão:
    - 8 linhas (bem abaixo de 25)
    - 1 função modificada
    - 1 arquivo
    - Sem breaking changes
    - Alta reversibilidade
    """
    diff = """
+def calculate_discount(price: float, percentage: float) -> float:
+    '''Calculate discounted price.'''
+    if not 0 <= percentage <= 100:
+        raise ValueError('Percentage must be 0-100')
+    discount = price * (percentage / 100)
+    return price - discount
"""
    return create_patch(
        patch_id="perfect-001",
        diff=diff,
        affected_files=["pricing.py"],
        patch_size_lines=8,
        description="Add discount calculation helper",
    )


@pytest.fixture
def invasive_patch():
    """
    Patch INVASIVO:
    - 300 linhas (12x o limite)
    - Reescreve implementação interna da classe
    - Múltiplas funções modificadas
    - SEM breaking changes (apenas refactoring interno)
    """
    # Gerar diff longo realístico - refactoring interno sem quebrar API
    diff_lines = []
    diff_lines.append(" class AuthService:")  # Classe mantém mesmo nome
    for i in range(150):
        diff_lines.append(f"-    # Old implementation line {i}")
    for i in range(150):
        diff_lines.append(f"+    # Refactored implementation line {i}")

    diff = "\n".join(diff_lines)
    return create_patch(
        patch_id="invasive-001",
        diff=diff,
        affected_files=["auth_service.py"],
        patch_size_lines=300,
        description="Internal refactoring of AuthService (no API changes)",
    )


@pytest.fixture
def breaking_change_patch():
    """
    Patch com BREAKING CHANGE:
    - Remove endpoint público
    - Muda assinatura de API
    """
    diff = """
-@app.route('/api/v1/users', methods=['GET'])
-def get_users():
-    return jsonify(users)
+@app.route('/api/v2/users', methods=['GET'])
+def get_users(include_inactive: bool = False):
+    return jsonify(filter_users(include_inactive))
"""
    return create_patch(
        patch_id="breaking-001",
        diff=diff,
        affected_files=["routes.py"],
        patch_size_lines=10,
        description="Migrate to v2 API with breaking changes",
    )


@pytest.fixture
def irreversible_patch():
    """
    Patch DIFÍCIL DE REVERTER:
    - Mudanças em migration (dados)
    - Múltiplos arquivos
    - Configurações críticas
    - SEM breaking changes (campo opcional, não required)
    """
    diff = """
--- a/migrations/005_add_user_roles.sql
+++ b/migrations/005_add_user_roles.sql
+ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'user';
+UPDATE users SET role = 'admin' WHERE id IN (1, 2, 3);
--- a/settings.py
+++ b/settings.py
+ENABLE_ROLES = True
--- a/models.py
+++ b/models.py
+class User:
+    role: str = Field(default='user')
"""
    return create_patch(
        patch_id="irreversible-001",
        diff=diff,
        affected_files=[
            "migrations/005_add_user_roles.sql",
            "settings.py",
            "models.py",
        ],
        patch_size_lines=15,
        description="Add role-based access control (backward compatible)",
    )


# ============================================================================
# CENÁRIO REAL 1: Patch Perfeito (Mansidão Exemplar)
# Princípio: "O menor quando suficiente"
# ============================================================================


class TestRealScenario_PerfectPatch:
    """
    Cenário Real: Desenvolvedora adiciona helper simples de 8 linhas.

    Mansidão: Intervenção mínima, cirúrgica, reversível.
    """

    def test_perfect_patch_is_approved(self, validator, perfect_patch):
        """
        DADO: Patch pequeno (8 linhas), 1 função, 1 arquivo
        QUANDO: Validado por Praotes
        ENTÃO: APPROVED com alto score de Mansidão (>= 0.80)
        E: Reflexão bíblica sobre mansidão

        CIENTÍFICO: Score de 0.80+ indica patch de alta qualidade
        (size_score ~0.76 + reversibility 1.0 + functions ~0.67 = ~0.86)
        """
        result = validator.validate_patch(perfect_patch)

        assert result["result"] == ValidationResult.APPROVED
        assert (
            result["mansidao_score"] >= 0.80
        ), f"Score {result['mansidao_score']} deve ser >= 0.80"
        assert len(result["violations"]) == 0
        assert "mansidão" in result["biblical_reflection"].lower()

    def test_perfect_patch_metrics(self, validator, perfect_patch):
        """
        VALIDAR: Métricas calculadas corretamente

        CIENTÍFICO: Contagem exclui linhas vazias (6 linhas de código real)
        """
        result = validator.validate_patch(perfect_patch)
        metrics = result["metrics"]

        assert metrics["lines_changed"] == 6, "6 linhas de código (excluindo vazias)"
        assert (
            metrics["functions_modified"] == 1
        ), "1 função modificada (calculate_discount)"
        assert metrics["api_contracts_broken"] == 0, "Sem breaking changes"
        assert (
            metrics["reversibility_score"] >= 0.90
        ), "Alta reversibilidade (1 arquivo, sem migrations)"


# ============================================================================
# CENÁRIO REAL 2: Patch Invasivo (Falta de Mansidão)
# Princípio: "Preferir incrementos pequenos sobre rewrites"
# ============================================================================


class TestRealScenario_InvasivePatch:
    """
    Cenário Real: Desenvolvedor reescreve classe inteira (300 linhas).

    Anti-Mansidão: Mudança massiva quando pequenos passos seriam melhores.
    """

    def test_invasive_patch_is_rejected(self, validator, invasive_patch):
        """
        DADO: Patch gigante (300 linhas)
        QUANDO: Validado por Praotes
        ENTÃO: TOO_INVASIVE com score baixo
        E: Violação explícita do limite
        """
        result = validator.validate_patch(invasive_patch)

        assert result["result"] == ValidationResult.TOO_INVASIVE
        assert result["mansidao_score"] < 0.30
        assert len(result["violations"]) > 0
        assert any("invasivo" in v.lower() for v in result["violations"])

    def test_invasive_patch_gets_suggestions(self, validator, invasive_patch):
        """
        MANSIDÃO: Mesmo rejeitando, oferecer caminho manso
        """
        suggestions = validator.suggest_improvements(invasive_patch)

        assert len(suggestions) > 0
        # Deve sugerir divisão em patches menores
        assert any(
            "dividir" in s.lower() or "incrementa" in s.lower() for s in suggestions
        )


# ============================================================================
# CENÁRIO REAL 3: Breaking Change (Quebra de Contrato)
# Princípio: "Respeitar compromissos estabelecidos"
# ============================================================================


class TestRealScenario_BreakingChange:
    """
    Cenário Real: Patch remove endpoint público sem deprecation.

    Mansidão: Respeitar contratos, não quebrar expectativas dos outros.
    """

    def test_breaking_change_requires_human_review(
        self, validator, breaking_change_patch
    ):
        """
        DADO: Patch remove/muda API pública
        QUANDO: Validado por Praotes
        ENTÃO: REQUIRES_HUMAN_REVIEW (não auto-aprovar)
        E: Breaking changes detectados nas métricas
        """
        result = validator.validate_patch(breaking_change_patch)

        assert result["result"] == ValidationResult.REQUIRES_HUMAN_REVIEW
        assert result["metrics"]["api_contracts_broken"] > 0
        assert result["mansidao_score"] == 0.0  # Breaking = score zero

    def test_breaking_change_detection_finds_removed_route(
        self, validator, breaking_change_patch
    ):
        """
        VALIDAR: Detector de breaking changes funciona
        """
        count = validator._detect_breaking_changes(breaking_change_patch.diff)

        assert count > 0  # Deve detectar remoção do @app.route


# ============================================================================
# CENÁRIO REAL 4: Mudança Irreversível (Migration + Configs)
# Princípio: "Escolher caminhos que permitem retorno"
# ============================================================================


class TestRealScenario_IrreversiblePatch:
    """
    Cenário Real: Patch altera migration SQL + configs + models.

    Mansidão: Preferir mudanças reversíveis, evitar migrações de dados.
    """

    def test_irreversible_patch_is_flagged(self, validator, irreversible_patch):
        """
        DADO: Patch com migration + múltiplos arquivos
        QUANDO: Validado por Praotes
        ENTÃO: NOT_EASILY_REVERSIBLE
        E: Score de reversibilidade baixo
        """
        result = validator.validate_patch(irreversible_patch)

        assert result["result"] == ValidationResult.NOT_EASILY_REVERSIBLE
        assert result["metrics"]["reversibility_score"] < 0.90

    def test_irreversible_patch_reversibility_factors(
        self, validator, irreversible_patch
    ):
        """
        VALIDAR: Cálculo de reversibilidade considera:
        - Migrations (-0.3)
        - Múltiplos arquivos (-0.1 por arquivo extra)
        - Settings críticos (-0.2)
        """
        score = validator._calculate_reversibility_score(irreversible_patch)

        # 1.0 - 0.3 (migration) - 0.2 (3 arquivos: -0.1 * 2) - 0.2 (settings) = 0.3
        assert score < 0.50


# ============================================================================
# TESTE DE CONFORMIDADE CONSTITUCIONAL
# Valida que Praotes implementa Artigo II da Constituição
# ============================================================================


class TestConstitutionalCompliance:
    """
    Valida conformidade com PENELOPE_SISTEMA_CRISTAO.html linhas 540-573.
    Artigo II (Mansidão): "Força sob controle"
    """

    def test_praotes_enforces_25_line_limit(self, validator):
        """
        CONSTITUIÇÃO: Limite de 25 linhas por patch (linha 549 do HTML).
        """
        assert validator.MAX_PATCH_LINES == 25

    def test_praotes_enforces_reversibility_minimum(self, validator):
        """
        CONSTITUIÇÃO: Reversibilidade ≥ 90%.
        """
        assert validator.MIN_REVERSIBILITY_SCORE == 0.90

    def test_all_validations_include_biblical_reflection(
        self, validator, perfect_patch
    ):
        """
        ARTIGO I: Glorificar a Deus através de sabedoria.
        ENTÃO: Toda validação inclui reflexão bíblica.
        """
        result = validator.validate_patch(perfect_patch)

        assert "biblical_reflection" in result
        assert len(result["biblical_reflection"]) > 10

    def test_validator_prefers_smaller_patches(self, validator):
        """
        MANSIDÃO: "Preferir 8 linhas sobre 300, mesmo quando capaz de 300"
        """
        # Patch pequeno (8 linhas)
        small_patch = create_patch(
            patch_id="small",
            diff="\n".join(["+line" for _ in range(8)]),
            affected_files=["file.py"],
            patch_size_lines=8,
            description="Small",
        )

        # Patch médio (20 linhas, ainda dentro do limite)
        medium_patch = create_patch(
            patch_id="medium",
            diff="\n".join(["+line" for _ in range(20)]),
            affected_files=["file.py"],
            patch_size_lines=20,
            description="Medium",
        )

        result_small = validator.validate_patch(small_patch)
        result_medium = validator.validate_patch(medium_patch)

        # Menor deve ter score MAIOR (preferência)
        assert result_small["mansidao_score"] > result_medium["mansidao_score"]


# ============================================================================
# TESTES DE EDGE CASES REAIS
# ============================================================================


class TestEdgeCases:
    """Edge cases baseados em comportamento real do código."""

    def test_empty_patch_is_approved(self, validator):
        """
        EDGE CASE: Patch vazio (0 linhas mudadas).
        ESPERADO: Approved com score máximo (nada mais manso que não fazer nada).
        """
        empty_patch = create_patch(
            patch_id="empty",
            diff="",
            affected_files=[],
            patch_size_lines=0,
            description="No changes",
        )

        result = validator.validate_patch(empty_patch)

        assert result["result"] == ValidationResult.APPROVED
        assert result["mansidao_score"] == 1.0

    def test_exactly_25_lines_is_approved(self, validator):
        """
        EDGE CASE: Exatamente no limite (25 linhas).
        ESPERADO: Approved (no edge, ainda válido).
        """
        limit_patch = create_patch(
            patch_id="limit",
            diff="\n".join(["+line" for _ in range(25)]),
            affected_files=["file.py"],
            patch_size_lines=25,
            description="At limit",
        )

        result = validator.validate_patch(limit_patch)

        assert result["result"] == ValidationResult.APPROVED

    def test_26_lines_is_rejected(self, validator):
        """
        EDGE CASE: 1 linha acima do limite (26 linhas).
        ESPERADO: TOO_INVASIVE (linha 63-67 do código).
        """
        over_limit_patch = create_patch(
            patch_id="over",
            diff="\n".join(["+line" for _ in range(26)]),
            affected_files=["file.py"],
            patch_size_lines=26,
            description="Over limit",
        )

        result = validator.validate_patch(over_limit_patch)

        assert result["result"] == ValidationResult.TOO_INVASIVE

    def test_function_count_edge_case(self, validator):
        """
        EDGE CASE: Exatamente 3 funções (no limite).
        ESPERADO: Approved.
        """
        three_functions_diff = """
+def func1():
+    pass
+
+def func2():
+    pass
+
+def func3():
+    pass
"""
        count = validator._count_functions_modified(three_functions_diff)

        assert count == 3  # Detecta corretamente
