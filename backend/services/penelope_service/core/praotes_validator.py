"""Praotes Validator - Validador de Mansidão (Artigo II).

Implementa o Princípio da Mansidão: garantir que patches sigam o princípio
da mínima intervenção necessária.

Fundamento Bíblico: Mateus 5:5
"Bem-aventurados os mansos, porque herdarão a terra."

Author: Vértice Platform Team
License: Proprietary
"""

import logging
import re

from models import CodePatch, ValidationResult

logger = logging.getLogger(__name__)


class PraotesValidator:
    """
    Validador de Mansidão: Garante intervenção mínima.

    Princípios:
    1. Tamanho máximo: 25 linhas por patch
    2. Reversibilidade: Score ≥ 0.90
    3. Contratos de API: Zero breaking changes
    4. Preferência por configuração sobre código
    """

    MAX_PATCH_LINES = 25
    MIN_REVERSIBILITY_SCORE = 0.90
    MAX_FUNCTIONS_MODIFIED = 3

    def __init__(self):
        """Inicializa Praotes Validator."""
        pass

    def validate_patch(self, patch: CodePatch) -> dict[str, any]:
        """
        Valida patch segundo princípio de Mansidão.

        Args:
            patch: Patch a validar

        Returns:
            Dict com resultado e métricas
        """
        logger.info(f"[Praotes] Validating patch {patch.patch_id}")

        # Contar linhas do diff (evitar contar string vazia como 1 linha)
        lines_changed = (
            len([line for line in patch.diff.split("\n") if line.strip()])
            if patch.diff
            else 0
        )

        metrics = {
            "lines_changed": lines_changed,
            "functions_modified": self._count_functions_modified(patch.diff),
            "api_contracts_broken": self._detect_breaking_changes(patch.diff),
            "reversibility_score": self._calculate_reversibility_score(patch),
        }

        violations = []

        # Princípio 1: Tamanho da mudança
        if metrics["lines_changed"] > self.MAX_PATCH_LINES:
            violations.append(
                f"Patch muito invasivo: {metrics['lines_changed']} linhas "
                f"(máximo: {self.MAX_PATCH_LINES})"
            )

        # Princípio 2: Número de funções
        if metrics["functions_modified"] > self.MAX_FUNCTIONS_MODIFIED:
            violations.append(
                f"Muitas funções modificadas: {metrics['functions_modified']} "
                f"(máximo: {self.MAX_FUNCTIONS_MODIFIED})"
            )

        # Princípio 3: Breaking changes
        if metrics["api_contracts_broken"] > 0:
            violations.append(
                f"Breaking changes detectados: {metrics['api_contracts_broken']}"
            )

        # Princípio 4: Reversibilidade
        if metrics["reversibility_score"] < self.MIN_REVERSIBILITY_SCORE:
            violations.append(
                f"Baixa reversibilidade: {metrics['reversibility_score']:.2f} "
                f"(mínimo: {self.MIN_REVERSIBILITY_SCORE})"
            )

        # Determinar resultado
        # PRIORIZAÇÃO: Breaking changes > Tamanho > Reversibilidade
        if not violations:
            result = ValidationResult.APPROVED
            mansidao_score = self._calculate_mansidao_score(metrics)
        elif metrics["api_contracts_broken"] > 0:
            # PRIORIDADE 1: Breaking changes requerem humano
            result = ValidationResult.REQUIRES_HUMAN_REVIEW
            mansidao_score = 0.0
        elif metrics["lines_changed"] > self.MAX_PATCH_LINES:
            # PRIORIDADE 2: Tamanho excessivo
            result = ValidationResult.TOO_INVASIVE
            mansidao_score = max(0.0, 1.0 - (metrics["lines_changed"] / 100.0))
        elif metrics["reversibility_score"] < self.MIN_REVERSIBILITY_SCORE:
            # PRIORIDADE 3: Reversibilidade baixa
            result = ValidationResult.NOT_EASILY_REVERSIBLE
            mansidao_score = metrics["reversibility_score"] * 0.5
        else:
            # Outras violações (ex: muitas funções)
            result = ValidationResult.TOO_INVASIVE
            mansidao_score = max(0.0, 1.0 - (metrics["lines_changed"] / 100.0))

        logger.info(
            f"[Praotes] Patch {patch.patch_id}: {result.value} "
            f"(Mansidão: {mansidao_score:.2f})"
        )

        return {
            "result": result,
            "mansidao_score": mansidao_score,
            "metrics": metrics,
            "violations": violations,
            "biblical_reflection": self._get_biblical_reflection(result),
        }

    def _count_functions_modified(self, diff: str) -> int:
        """Conta número de funções modificadas no diff."""
        # Detectar definições de função (Python, TypeScript, etc.)
        # NOTA: Padrões devem considerar o prefixo + ou - do diff
        function_patterns = [
            r"[+-]\s*def\s+\w+\(",  # Python
            r"[+-]\s*async\s+def\s+\w+\(",  # Python async
            r"[+-]\s*function\s+\w+\(",  # JavaScript
            r"[+-]\s*const\s+\w+\s*=\s*\(",  # Arrow functions
        ]

        functions_found = set()
        for line in diff.split("\n"):
            if line.startswith("+") or line.startswith("-"):
                for pattern in function_patterns:
                    if re.search(pattern, line):
                        # Extrair nome da função (após def/function/const)
                        match = re.search(r"(def|function|const)\s+(\w+)", line)
                        if match:
                            functions_found.add(match.group(2))

        return len(functions_found)

    def _detect_breaking_changes(self, diff: str) -> int:
        """Detecta breaking changes (API contracts quebrados)."""
        breaking_changes = 0

        # Padrões de breaking changes
        breaking_patterns = [
            r"^\-\s*def\s+\w+\(",  # Função removida
            r"^\-\s*class\s+\w+",  # Classe removida
            r"^\-\s*@\w+\.route\(",  # Endpoint removido
            r"^\+.*required=True",  # Campo obrigatório adicionado
            r"^\-.*\):\s*$",  # Assinatura mudou (parâmetro removido)
        ]

        for line in diff.split("\n"):
            for pattern in breaking_patterns:
                if re.search(pattern, line):
                    breaking_changes += 1
                    break

        return breaking_changes

    def _calculate_reversibility_score(self, patch: CodePatch) -> float:
        """
        Calcula quão facilmente o patch pode ser revertido.

        Fatores:
        - Número de arquivos afetados
        - Complexidade das mudanças
        - Presença de migrações de dados
        - Mudanças em configurações críticas

        CIENTÍFICO: Patches até 25 linhas (limite) devem ter score >= 0.90
        """
        score = 1.0

        # Penalizar múltiplos arquivos
        num_files = len(patch.affected_files)
        if num_files > 1:
            score -= (num_files - 1) * 0.1

        # Penalizar mudanças em migrações
        if any("migration" in f.lower() for f in patch.affected_files):
            score -= 0.3

        # Penalizar mudanças em configs críticas
        critical_files = ["settings.py", "config.py", "docker-compose.yml"]
        if any(cf in f for cf in critical_files for f in patch.affected_files):
            score -= 0.2

        # Penalizar patches grandes (mais suave: 0.01 por linha > 15)
        # Permite que 25 linhas fiquem em 0.90 (1.0 - 10*0.01 = 0.90)
        if patch.patch_size_lines > 15:
            score -= (patch.patch_size_lines - 15) * 0.01

        return max(0.0, min(score, 1.0))

    def _calculate_mansidao_score(self, metrics: dict[str, any]) -> float:
        """
        Calcula score geral de Mansidão (0.0 - 1.0).

        Leva em conta:
        - Tamanho (quanto menor, melhor)
        - Reversibilidade (quanto maior, melhor)
        - Número de funções (quanto menor, melhor)
        - Breaking changes (0 = perfeito)
        """
        # EDGE CASE: Patch vazio (0 linhas) = score perfeito
        if metrics["lines_changed"] == 0:
            return 1.0

        # Componente 1: Tamanho (inverted: 1 linha = 1.0, 25 linhas = 0.0)
        size_score = max(0.0, 1.0 - (metrics["lines_changed"] / self.MAX_PATCH_LINES))

        # Componente 2: Reversibilidade (direto)
        reversibility_score = metrics["reversibility_score"]

        # Componente 3: Funções modificadas (inverted)
        functions_score = max(
            0.0, 1.0 - (metrics["functions_modified"] / self.MAX_FUNCTIONS_MODIFIED)
        )

        # Componente 4: Breaking changes (0 = 1.0, >0 = 0.0)
        breaking_score = 1.0 if metrics["api_contracts_broken"] == 0 else 0.0

        # Média ponderada
        mansidao_score = (
            size_score * 0.3
            + reversibility_score * 0.3
            + functions_score * 0.2
            + breaking_score * 0.2
        )

        return mansidao_score

    def _get_biblical_reflection(self, result: ValidationResult) -> str:
        """Retorna reflexão bíblica apropriada ao resultado."""
        reflections = {
            ValidationResult.APPROVED: (
                "A mansidão é força sob controle. "
                "Este patch demonstra a virtude da intervenção mínima."
            ),
            ValidationResult.TOO_INVASIVE: (
                "A mansidão nos ensina a preferir o menor quando suficiente. "
                "Este patch excede o necessário."
            ),
            ValidationResult.NOT_EASILY_REVERSIBLE: (
                "A prudência nos guia a escolher caminhos reversíveis. "
                "Este patch dificulta o retorno."
            ),
            ValidationResult.REQUIRES_HUMAN_REVIEW: (
                "Há decisões que requerem a sabedoria humana. "
                "Mudanças em contratos de API são deste tipo."
            ),
        }

        return reflections.get(
            result,
            "Avalie cuidadosamente cada mudança, buscando sempre o caminho mais gentil.",
        )

    def suggest_improvements(self, patch: CodePatch) -> list[str]:
        """
        Sugere melhorias para aumentar mansidão do patch.

        Args:
            patch: Patch a melhorar

        Returns:
            Lista de sugestões
        """
        suggestions = []

        if patch.patch_size_lines > self.MAX_PATCH_LINES:
            suggestions.append(
                f"Dividir patch em {(patch.patch_size_lines // self.MAX_PATCH_LINES) + 1} patches menores"
            )

        functions_count = self._count_functions_modified(patch.diff)
        if functions_count > self.MAX_FUNCTIONS_MODIFIED:
            suggestions.append(
                "Focar em uma função por vez, criando patches incrementais"
            )

        if self._detect_breaking_changes(patch.diff) > 0:
            suggestions.append(
                "Evitar breaking changes: adicionar novos endpoints em vez de modificar existentes"
            )

        if self._calculate_reversibility_score(patch) < self.MIN_REVERSIBILITY_SCORE:
            suggestions.append(
                "Aumentar reversibilidade: evitar mudanças em múltiplos arquivos simultaneamente"
            )

        return suggestions
