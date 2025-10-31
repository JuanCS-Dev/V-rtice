"""Tapeinophrosyne Monitor - Monitor de Humildade (Artigo III).

Implementa o Princípio da Humildade: avalia competência do sistema e escala
para humanos quando necessário.

Fundamento Bíblico: Filipenses 2:3
"Nada façais por contenda ou por vanglória, mas por humildade."

Author: Vértice Platform Team
License: Proprietary
"""

import logging

from models import CodePatch, CompetenceLevel, Diagnosis, Report

logger = logging.getLogger(__name__)


class TapeinophrosyneMonitor:
    """
    Monitor de Humildade: Avalia competência e escala quando necessário.

    Manifesto:
    1. "Eu não sei" - Reconhecer incerteza quando confiança < 85%
    2. "Preciso de ajuda" - Escalar quando situação excede competência
    3. "Posso estar errado" - Todo patch vem com métrica de confiança
    4. "Aprendo com meus erros" - Feedback loop explícito
    """

    CONFIDENCE_THRESHOLD = 0.85
    DOMAIN_KNOWLEDGE_MIN_CASES = 5

    def __init__(self, wisdom_base):
        """
        Inicializa Tapeinophrosyne Monitor.

        Args:
            wisdom_base: Cliente para Wisdom Base
        """
        self.wisdom_base = wisdom_base
        self.known_domains = set()  # Populado durante startup

    async def assess_competence(self, diagnosis: Diagnosis) -> dict[str, any]:
        """
        Avalia competência do sistema para lidar com diagnóstico.

        Args:
            diagnosis: Diagnóstico a avaliar

        Returns:
            Dict com nível de competência e reasoning
        """
        logger.info(
            f"[Tapeinophrosyne] Assessing competence for {diagnosis.diagnosis_id}"
        )

        confidence = diagnosis.confidence
        domain = diagnosis.domain

        # Domínios conhecidos (≥ 5 casos históricos)
        if domain in self.known_domains:
            if confidence >= self.CONFIDENCE_THRESHOLD:
                return {
                    "competence_level": CompetenceLevel.AUTONOMOUS,
                    "reasoning": f"Domínio conhecido + alta confiança ({confidence:.1%})",
                    "can_proceed": True,
                    "humility_note": (
                        "Tenho experiência com este tipo de falha e alta confiança "
                        "no diagnóstico. Posso agir autonomamente."
                    ),
                }
            else:
                return {
                    "competence_level": CompetenceLevel.ASSISTED,
                    "reasoning": f"Domínio conhecido mas confiança moderada ({confidence:.1%})",
                    "can_proceed": False,
                    "humility_note": (
                        "Conheço este domínio, mas minha confiança no diagnóstico "
                        "está abaixo do limiar. Sugiro patch para revisão humana."
                    ),
                }

        # Domínios desconhecidos (< 5 casos históricos)
        else:
            return {
                "competence_level": CompetenceLevel.DEFER_TO_HUMAN,
                "reasoning": f"Domínio desconhecido ({domain}) - primeira vez enfrentando este tipo de falha",
                "can_proceed": False,
                "humility_note": (
                    "Nunca enfrentei este tipo de falha antes. "
                    "Não tenho competência para agir autonomamente. "
                    "Recomendo supervisão humana imediata."
                ),
            }

    def generate_uncertainty_report(self, patch: CodePatch) -> Report:
        """
        Gera relatório de incerteza para patch.

        Todo patch DEVE vir acompanhado de relatório de incerteza explícito.

        Args:
            patch: Patch a documentar

        Returns:
            Report com incertezas declaradas
        """
        logger.info(
            f"[Tapeinophrosyne] Generating uncertainty report for {patch.patch_id}"
        )

        # Identificar fatores de incerteza
        uncertainty_factors = []

        if patch.confidence < 0.90:
            uncertainty_factors.append(
                f"Confiança moderada ({patch.confidence:.1%}) - há margem para erro"
            )

        if not patch.humility_notes:
            uncertainty_factors.append("Primeira vez aplicando patch deste tipo")

        if patch.patch_size_lines > 15:
            uncertainty_factors.append(
                f"Patch grande ({patch.patch_size_lines} linhas) - maior superfície de erro"
            )

        # Avaliar risco
        risk_profile = self._assess_risk_profile(patch)

        # FASE 1: Lista vazia (sem busca de precedentes).
        # FASE 2: Implementar busca real na Wisdom Base.
        similar_precedents = []

        return Report(
            confidence=patch.confidence,
            risk_assessment=risk_profile,
            similar_precedents=similar_precedents,
            uncertainty_factors=uncertainty_factors,
        )

    def _assess_risk_profile(self, patch: CodePatch) -> dict[str, any]:
        """
        Avalia perfil de risco do patch.

        Args:
            patch: Patch a avaliar

        Returns:
            Dict com análise de risco
        """
        high_risk_scenarios = []
        mitigation_strategies = []

        # Risco 1: Arquivos críticos
        critical_files = ["auth", "payment", "user_data", "security"]
        affected_critical = [
            f
            for f in patch.affected_files
            if any(cf in f.lower() for cf in critical_files)
        ]

        if affected_critical:
            high_risk_scenarios.append(
                f"Modificando arquivos críticos: {', '.join(affected_critical)}"
            )
            mitigation_strategies.append(
                "Validação em digital twin por período estendido (30min)"
            )

        # Risco 2: Confiança moderada
        if patch.confidence < 0.85:
            high_risk_scenarios.append(
                f"Confiança abaixo do ideal ({patch.confidence:.1%})"
            )
            mitigation_strategies.append(
                "Code review humana obrigatória antes de deploy"
            )

        # Risco 3: Patch grande
        if patch.patch_size_lines > 20:
            high_risk_scenarios.append(
                f"Patch extenso ({patch.patch_size_lines} linhas)"
            )
            mitigation_strategies.append("Considerar dividir em patches menores")

        return {
            "overall_risk": self._calculate_overall_risk(patch),
            "high_risk_scenarios": high_risk_scenarios,
            "mitigation_strategies": mitigation_strategies,
        }

    def _calculate_overall_risk(self, patch: CodePatch) -> str:
        """Calcula nível de risco geral (low, medium, high, critical)."""
        risk_score = 0

        # Fatores de risco
        if patch.confidence < 0.70:
            risk_score += 3
        elif patch.confidence < 0.85:
            risk_score += 1

        if patch.patch_size_lines > 20:
            risk_score += 2
        elif patch.patch_size_lines > 15:
            risk_score += 1

        if patch.mansidao_score < 0.70:
            risk_score += 2

        # Classificação
        if risk_score >= 5:
            return "critical"
        elif risk_score >= 3:
            return "high"
        elif risk_score >= 1:
            return "medium"
        else:
            return "low"

    async def learn_from_failure(
        self, failed_patch: CodePatch, actual_outcome: str
    ) -> dict[str, any]:
        """
        Aprende com patch que falhou.

        Args:
            failed_patch: Patch que falhou
            actual_outcome: O que realmente aconteceu

        Returns:
            Dict com lição aprendida
        """
        logger.warning(
            f"[Tapeinophrosyne] Learning from failure: {failed_patch.patch_id}"
        )

        # Diagnosticar por que falhou
        failure_root_cause = await self._diagnose_patch_failure(
            failed_patch, actual_outcome
        )

        lesson = {
            "patch_id": failed_patch.patch_id,
            "what_i_thought": f"Confiança: {failed_patch.confidence:.1%}",
            "what_actually_happened": actual_outcome,
            "root_cause_of_failure": failure_root_cause,
            "lesson_learned": self._extract_lesson(failed_patch, failure_root_cause),
            "adjustment_needed": self._recommend_adjustment(failure_root_cause),
        }

        # Armazenar na Wisdom Base
        await self.wisdom_base.store_lesson(lesson)

        # Broadcast para equipe
        logger.info(f"[Tapeinophrosyne] Lesson learned: {lesson['lesson_learned']}")

        return lesson

    async def _diagnose_patch_failure(self, patch: CodePatch, outcome: str) -> str:
        """
        Diagnostica causa raiz da falha do patch.

        FASE 1: Retorna mensagem genérica.
        FASE 2: Implementar análise real de logs e traces.

        Returns:
            Descrição da causa raiz
        """
        return "Patch causou regressão não prevista"

    def _extract_lesson(self, patch: CodePatch, root_cause: str) -> str:
        """Extrai lição aprendida da falha."""
        if "regressão" in root_cause.lower():
            return "Validação em digital twin deve incluir testes de regressão mais abrangentes"
        elif "dependência" in root_cause.lower():
            return "Análise de dependências deve ser mais profunda antes de gerar patch"
        else:
            return f"Situação não prevista: {root_cause}. Aumentar conservadorismo."

    def _recommend_adjustment(self, root_cause: str) -> str:
        """Recomenda ajuste no sistema baseado em falha."""
        if "regressão" in root_cause.lower():
            return "Adicionar testes de regressão específicos ao validation plan"
        elif "dependência" in root_cause.lower():
            return "Incluir análise de dependency graph no Causal AI"
        else:
            return "Aumentar CONFIDENCE_THRESHOLD de 0.85 para 0.90 temporariamente"

    def get_competence_stats(self) -> dict[str, any]:
        """
        Retorna estatísticas de competência do sistema.

        FASE 1: Retorna estrutura com valores padrão (0).
        FASE 2: Implementar coleta real de métricas.

        Returns:
            Dict com métricas de humildade
        """
        return {
            "known_domains": len(self.known_domains),
            "autonomous_interventions": 0,
            "assisted_interventions": 0,
            "deferred_to_human": 0,
            "false_confidence_rate": 0.0,
            "appropriate_escalation_rate": 0.0,
        }
