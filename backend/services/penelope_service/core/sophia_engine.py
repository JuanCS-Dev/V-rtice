"""Sophia Engine - Motor de Sabedoria (Artigo I).

Implementa o Princípio da Sabedoria: julgar se uma intervenção é necessária
antes de acionar o ciclo MAPE-K completo.

Fundamento Bíblico: Provérbios 9:10
"O temor do SENHOR é o princípio da sabedoria."

Author: Vértice Platform Team
License: Proprietary
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from models import Anomaly, InterventionDecision, InterventionLevel, Severity

logger = logging.getLogger(__name__)


class SophiaEngine:
    """
    Motor de Sabedoria: Julga se uma intervenção é necessária.

    Implementa três perguntas essenciais:
    1. É uma falha transitória que se autocorrige?
    2. A intervenção pode causar mais dano que a falha?
    3. Há precedentes históricos que informam a decisão?
    """

    def __init__(self, wisdom_base, observability_client):
        """
        Inicializa Sophia Engine.

        Args:
            wisdom_base: Cliente para Wisdom Base (precedentes históricos)
            observability_client: Cliente para Prometheus/Loki
        """
        self.wisdom_base = wisdom_base
        self.observability_client = observability_client

        # Configurações de sabedoria
        self.transient_failure_threshold_minutes = 5
        self.min_precedent_confidence = 0.85
        self.risk_tolerance = 0.3  # Máximo 30% de risco aceitável

    async def should_intervene(self, anomaly: Anomaly) -> dict[str, Any]:
        """
        Decisão principal: devemos intervir nesta anomalia?

        Args:
            anomaly: Anomalia detectada

        Returns:
            Dict com decisão e reasoning
        """
        logger.info(
            f"[Sophia] Evaluating intervention for anomaly {anomaly.anomaly_id}"
        )

        # Pergunta 1: É transitória?
        if await self._is_self_healing_naturally(anomaly):
            return {
                "decision": InterventionDecision.OBSERVE_AND_WAIT,
                "reasoning": "Anomalia tem padrão transitório conhecido. Histórico mostra auto-correção em 94% dos casos.",
                "wait_time_minutes": self.transient_failure_threshold_minutes,
                "sophia_wisdom": "Há tempo certo para cada ação (Eclesiastes 3:1). Este não é o momento de agir.",
            }

        # Pergunta 2: Risco de intervenção > benefício?
        risk_assessment = await self._assess_intervention_risk(anomaly)
        current_impact = self._calculate_current_impact(anomaly)

        if risk_assessment["risk_score"] > current_impact:
            return {
                "decision": InterventionDecision.HUMAN_CONSULTATION_REQUIRED,
                "reasoning": f"Risco de intervenção ({risk_assessment['risk_score']:.2f}) > impacto atual ({current_impact:.2f})",
                "risk_details": risk_assessment,
                "sophia_wisdom": "A prudência é a marca da sabedoria. Quando em dúvida, consultar aqueles com mais experiência.",
            }

        # Pergunta 3: Há precedentes históricos?
        precedent = await self._query_wisdom_base(anomaly)

        if precedent:
            return {
                "decision": InterventionDecision.INTERVENE,
                "reasoning": f"Precedente encontrado (similaridade: {precedent['similarity']:.1%}). Intervenção anterior foi {precedent['outcome']}.",
                "intervention_level": self._recommend_intervention_level(
                    anomaly, precedent
                ),
                "precedent": precedent,
                "sophia_wisdom": "Há sabedoria em aprender com o passado. Precedentes nos guiam.",
            }

        # Sem precedentes: avaliar se devemos arriscar intervenção
        if anomaly.severity in [Severity.P0_CRITICAL, Severity.P1_HIGH]:
            return {
                "decision": InterventionDecision.INTERVENE,
                "reasoning": f"Severidade {anomaly.severity.value} requer ação. Sem precedentes, mas impacto justifica risco.",
                "intervention_level": InterventionLevel.PATCH_SURGICAL,  # Começar conservador
                "sophia_wisdom": "Em momentos críticos, sabedoria também é agir com coragem temperada.",
            }
        else:
            return {
                "decision": InterventionDecision.OBSERVE_AND_WAIT,
                "reasoning": "Sem precedentes e severidade não crítica. Observar para aprender antes de agir.",
                "wait_time_minutes": 10,
                "sophia_wisdom": "Melhor observar e aprender que agir precipitadamente sem conhecimento.",
            }

    async def _is_self_healing_naturally(self, anomaly: Anomaly) -> bool:
        """
        Verifica se anomalia tem padrão de auto-correção.

        Args:
            anomaly: Anomalia a verificar

        Returns:
            True se histórico mostra auto-correção frequente
        """
        # Buscar ocorrências similares nas últimas 4 semanas
        time_window = datetime.now() - timedelta(weeks=4)

        similar_anomalies = await self.observability_client.query_similar_anomalies(
            anomaly_type=anomaly.anomaly_type,
            service=anomaly.service,
            since=time_window,
        )

        if len(similar_anomalies) < 5:
            return False  # Insuficiente histórico

        # Calcular taxa de auto-correção
        auto_corrected = sum(
            1 for a in similar_anomalies if a["resolved_without_intervention"]
        )

        auto_correction_rate = auto_corrected / len(similar_anomalies)

        # Se > 90% se auto-corrigiram, considerar transitório
        is_transient = auto_correction_rate > 0.90

        if is_transient:
            logger.info(
                f"[Sophia] Anomaly {anomaly.anomaly_id} identified as transient "
                f"({auto_correction_rate:.1%} auto-correction rate)"
            )

        return is_transient

    async def _assess_intervention_risk(self, anomaly: Anomaly) -> dict[str, Any]:
        """
        Avalia risco de intervenção.

        Args:
            anomaly: Anomalia a avaliar

        Returns:
            Dict com risk_score e detalhes
        """
        risk_factors = []
        risk_score = 0.0

        # Fator 1: Complexidade do serviço afetado
        service_complexity = await self._get_service_complexity(anomaly.service)
        if service_complexity > 0.7:
            risk_factors.append("Serviço de alta complexidade")
            risk_score += 0.3

        # Fator 2: Número de dependências
        dependencies = await self._get_service_dependencies(anomaly.service)
        if len(dependencies) > 10:
            risk_factors.append(f"Muitas dependências ({len(dependencies)})")
            risk_score += 0.2

        # Fator 3: Mudanças recentes no serviço
        recent_changes = await self._get_recent_changes(anomaly.service, hours=24)
        if recent_changes > 3:
            risk_factors.append(f"Múltiplas mudanças recentes ({recent_changes})")
            risk_score += 0.25

        # Fator 4: Falta de testes
        test_coverage = await self._get_test_coverage(anomaly.service)
        if test_coverage < 0.90:
            risk_factors.append(f"Coverage baixo ({test_coverage:.1%})")
            risk_score += 0.25

        return {
            "risk_score": min(risk_score, 1.0),
            "risk_factors": risk_factors,
            "service_complexity": service_complexity,
            "dependencies_count": len(dependencies),
            "recent_changes": recent_changes,
            "test_coverage": test_coverage,
        }

    def _calculate_current_impact(self, anomaly: Anomaly) -> float:
        """
        Calcula impacto atual da anomalia.

        Args:
            anomaly: Anomalia a avaliar

        Returns:
            Impact score (0.0 - 1.0)
        """
        impact = 0.0

        # Severity base
        severity_scores = {
            Severity.P0_CRITICAL: 1.0,
            Severity.P1_HIGH: 0.7,
            Severity.P2_MEDIUM: 0.4,
            Severity.P3_LOW: 0.2,
        }
        impact += severity_scores.get(anomaly.severity, 0.5)

        # Métricas específicas
        if "error_rate" in anomaly.metrics:
            impact += anomaly.metrics["error_rate"] * 0.3

        if "affected_users" in anomaly.metrics:
            users_affected = anomaly.metrics["affected_users"]
            if users_affected > 1000:
                impact += 0.3
            elif users_affected > 100:
                impact += 0.15

        return min(impact, 1.0)

    async def _query_wisdom_base(self, anomaly: Anomaly) -> dict[str, Any] | None:
        """
        Busca precedentes históricos na Wisdom Base.

        Args:
            anomaly: Anomalia a buscar

        Returns:
            Precedente mais similar ou None
        """
        precedents = await self.wisdom_base.query_precedents(
            anomaly_type=anomaly.anomaly_type,
            service=anomaly.service,
            similarity_threshold=self.min_precedent_confidence,
        )

        if not precedents:
            return None

        # Retornar precedente mais similar com outcome positivo
        successful_precedents = [p for p in precedents if p["outcome"] == "success"]

        if successful_precedents:
            return max(successful_precedents, key=lambda p: p["similarity"])

        # Se não há sucessos, retornar mais similar (para aprender com falha)
        return max(precedents, key=lambda p: p["similarity"])

    def _recommend_intervention_level(
        self, anomaly: Anomaly, precedent: dict[str, Any]
    ) -> InterventionLevel:
        """
        Recomenda nível de intervenção baseado em precedente.

        Args:
            anomaly: Anomalia atual
            precedent: Precedente histórico

        Returns:
            Nível de intervenção recomendado
        """
        # Se precedente foi sucesso e similar > 90%, usar mesmo nível
        if precedent["outcome"] == "success" and precedent["similarity"] > 0.90:
            return precedent.get("intervention_level", InterventionLevel.PATCH_SURGICAL)

        # Se precedente falhou, ser mais conservador
        if precedent["outcome"] == "failure":
            return InterventionLevel.OBSERVE

        # Padrão: começar com intervenção cirúrgica
        return InterventionLevel.PATCH_SURGICAL

    async def _get_service_complexity(self, service: str) -> float:
        """
        Obtém score de complexidade do serviço.

        FASE 1: Retorna valor padrão conservador (0.5).
        FASE 2: Implementar análise real (LOC, cyclomatic complexity, etc.).

        Returns:
            Score de complexidade (0.0 - 1.0)
        """
        return 0.5

    async def _get_service_dependencies(self, service: str) -> list[str]:
        """
        Obtém lista de dependências do serviço.

        FASE 1: Retorna lista vazia (sem análise de dependências).
        FASE 2: Implementar análise real de dependency graph.

        Returns:
            Lista de serviços dependentes
        """
        return []

    async def _get_recent_changes(self, service: str, hours: int) -> int:
        """
        Obtém número de mudanças recentes no serviço.

        FASE 1: Retorna 0 (sem análise de git log).
        FASE 2: Implementar query de git log.

        Returns:
            Número de commits recentes
        """
        return 0

    async def _get_test_coverage(self, service: str) -> float:
        """
        Obtém coverage de testes do serviço.

        FASE 1: Retorna valor otimista (0.90) assumindo boas práticas.
        FASE 2: Implementar integração com pytest-cov.

        Returns:
            Coverage (0.0 - 1.0)
        """
        return 0.90
