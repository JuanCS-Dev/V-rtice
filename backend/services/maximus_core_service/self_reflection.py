"""
Maximus Self-Reflection System - AI Quality Assurance
====================================================

Sistema de auto-avaliação e melhoria contínua:

1. QUALITY ASSESSMENT - Avalia qualidade da própria resposta
2. ERROR DETECTION - Detecta erros lógicos e factuais
3. SELF-CORRECTION - Corrige automaticamente quando possível
4. CONTINUOUS LEARNING - Aprende com erros passados

Resolve o problema: "IA que não sabe quando está errada"

Inspiração: Constitutional AI (Anthropic), Self-Critique (OpenAI), Reflexion
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import asyncio


class QualityDimension(str, Enum):
    """Dimensões de qualidade a avaliar"""
    COMPLETENESS = "completeness"      # Respondeu tudo que foi perguntado?
    ACCURACY = "accuracy"              # Informação é precisa/correta?
    RELEVANCE = "relevance"            # Focou no que importa?
    CLARITY = "clarity"                # Explicação clara e compreensível?
    ACTIONABILITY = "actionability"    # Resposta é acionável/útil?
    SAFETY = "safety"                  # Não contém informações perigosas?


class QualityLevel(str, Enum):
    """Níveis de qualidade"""
    EXCELLENT = "excellent"  # 90-100%
    GOOD = "good"           # 70-90%
    ACCEPTABLE = "acceptable"  # 50-70%
    POOR = "poor"           # 30-50%
    UNACCEPTABLE = "unacceptable"  # < 30%


@dataclass
class QualityIssue:
    """Problema identificado na resposta"""
    dimension: QualityDimension
    severity: str  # critical, high, medium, low
    description: str
    suggestion: Optional[str] = None


@dataclass
class QualityAssessment:
    """Avaliação de qualidade completa"""
    overall_score: float  # 0-1
    overall_level: QualityLevel
    dimension_scores: Dict[QualityDimension, float]
    issues: List[QualityIssue] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    can_improve: bool = False
    improvement_suggestions: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": self.overall_score,
            "overall_level": self.overall_level,
            "dimension_scores": {k.value: v for k, v in self.dimension_scores.items()},
            "issues": [
                {"dimension": i.dimension, "severity": i.severity, "description": i.description, "suggestion": i.suggestion}
                for i in self.issues
            ],
            "strengths": self.strengths,
            "can_improve": self.can_improve,
            "improvement_suggestions": self.improvement_suggestions,
            "timestamp": self.timestamp
        }


@dataclass
class CorrectionAttempt:
    """Tentativa de correção"""
    issue: QualityIssue
    original_answer: str
    corrected_answer: str
    success: bool
    reasoning: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class CompletenessEvaluator:
    """Avalia se resposta está completa"""

    async def evaluate(self, query: str, answer: str) -> Tuple[float, List[str]]:
        """
        Verifica se resposta aborda todas as partes da query.

        Returns:
            (completeness_score, missing_aspects)
        """
        issues = []
        score = 0.8  # Baseline

        # 1. Query tem múltiplas perguntas?
        query_parts = self._split_query_parts(query)

        if len(query_parts) > 1:
            # Verifica se resposta aborda cada parte
            answered_parts = sum(
                1 for part in query_parts
                if self._addresses_question(part, answer)
            )

            score = answered_parts / len(query_parts)

            if answered_parts < len(query_parts):
                issues.append(f"Answered {answered_parts}/{len(query_parts)} questions")

        # 2. Query pede exemplos/detalhes?
        if any(word in query.lower() for word in ["example", "explain", "detail", "how"]):
            if len(answer) < 200:
                score *= 0.8
                issues.append("Answer too brief for detailed question")

        # 3. Query pede lista/múltiplos itens?
        if any(word in query.lower() for word in ["list", "what are", "which are"]):
            # Verifica se resposta tem estrutura de lista
            if not any(marker in answer for marker in ["\n-", "\n1.", "\n2.", "•"]):
                score *= 0.9
                issues.append("List format expected but not provided")

        return score, issues

    def _split_query_parts(self, query: str) -> List[str]:
        """Quebra query em partes (perguntas separadas)"""
        # Simples: quebra por '?' ou 'and'
        import re
        parts = re.split(r'\?|and\s+(?:also\s+)?what|and\s+(?:also\s+)?how', query, flags=re.IGNORECASE)
        return [p.strip() for p in parts if p.strip()]

    def _addresses_question(self, question: str, answer: str) -> bool:
        """Verifica se resposta aborda uma questão específica"""
        # Extrai palavras-chave da questão
        keywords = [
            word.lower() for word in question.split()
            if len(word) > 4 and word.isalpha()
        ]

        # Verifica se pelo menos 30% das keywords estão na resposta
        answer_lower = answer.lower()
        matches = sum(1 for kw in keywords if kw in answer_lower)

        return (matches / max(len(keywords), 1)) >= 0.3 if keywords else True


class AccuracyEvaluator:
    """Avalia precisão factual da resposta"""

    async def evaluate(
        self,
        answer: str,
        sources: Optional[List[Dict]] = None
    ) -> Tuple[float, List[str]]:
        """
        Verifica precisão factual.

        Returns:
            (accuracy_score, issues)
        """
        issues = []
        score = 0.7  # Baseline

        # 1. Verifica sinais de imprecisão
        imprecision_markers = [
            "i think", "i believe", "probably", "maybe",
            "might be", "could be", "seems like", "appears to"
        ]

        imprecision_count = sum(
            1 for marker in imprecision_markers
            if marker in answer.lower()
        )

        if imprecision_count > 0:
            score -= (imprecision_count * 0.1)
            issues.append(f"Contains {imprecision_count} imprecision marker(s)")

        # 2. Se tem fontes, verifica consistência
        if sources:
            # Resposta deve ter citações se tem fontes
            has_citations = "[SOURCE" in answer or "according to" in answer.lower()

            if not has_citations:
                score *= 0.9
                issues.append("Has sources but no citations in answer")
        else:
            # Sem fontes é menos preciso
            score *= 0.8
            issues.append("No sources to verify accuracy")

        # 3. Verifica contradições internas
        if self._has_contradictions(answer):
            score *= 0.6
            issues.append("Internal contradictions detected")

        return max(score, 0.0), issues

    def _has_contradictions(self, text: str) -> bool:
        """Detecta contradições básicas"""
        # Procura por negações de statements anteriores
        sentences = [s.strip() for s in text.split('.') if s.strip()]

        for i, sent1 in enumerate(sentences):
            for sent2 in sentences[i+1:]:
                # Checa se sent2 nega sent1
                if "not" in sent2.lower() and any(
                    word in sent2.lower()
                    for word in sent1.lower().split()
                    if len(word) > 4
                ):
                    return True

        return False


class RelevanceEvaluator:
    """Avalia relevância da resposta"""

    async def evaluate(self, query: str, answer: str) -> Tuple[float, List[str]]:
        """
        Verifica se resposta é relevante para a query.

        Returns:
            (relevance_score, issues)
        """
        issues = []

        # Extrai keywords da query
        query_keywords = set(
            word.lower() for word in query.split()
            if len(word) > 3 and word.isalnum()
        )

        # Extrai keywords da resposta
        answer_keywords = set(
            word.lower() for word in answer.split()
            if len(word) > 3 and word.isalnum()
        )

        # Calcula overlap
        overlap = query_keywords & answer_keywords

        if query_keywords:
            relevance_score = len(overlap) / len(query_keywords)
        else:
            relevance_score = 0.5

        # Penaliza se resposta é muito genérica
        generic_phrases = [
            "it depends", "there are many", "it varies",
            "in general", "typically", "usually"
        ]

        generic_count = sum(
            1 for phrase in generic_phrases
            if phrase in answer.lower()
        )

        if generic_count > 2:
            relevance_score *= 0.8
            issues.append("Answer is too generic")

        # Penaliza se resposta é muito curta
        if len(answer) < 50:
            relevance_score *= 0.7
            issues.append("Answer is too brief")

        # Penaliza se resposta divaga muito
        if len(answer) > 1000 and relevance_score < 0.4:
            relevance_score *= 0.9
            issues.append("Answer may be rambling or off-topic")

        return relevance_score, issues


class ClarityEvaluator:
    """Avalia clareza da resposta"""

    async def evaluate(self, answer: str) -> Tuple[float, List[str]]:
        """
        Verifica clareza e compreensibilidade.

        Returns:
            (clarity_score, issues)
        """
        issues = []
        score = 0.8  # Baseline

        # 1. Sentences muito longas prejudicam clareza
        sentences = [s.strip() for s in answer.split('.') if s.strip()]
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)

        if avg_sentence_length > 30:
            score *= 0.9
            issues.append("Sentences are too long (avg > 30 words)")

        # 2. Jargão excessivo sem explicação
        jargon_terms = ["TTPs", "IOCs", "MITRE ATT&CK", "CVSS", "RCE"]
        jargon_count = sum(1 for term in jargon_terms if term in answer)

        if jargon_count > 3:
            # Verifica se tem explicações
            has_explanations = any(
                marker in answer
                for marker in ["which means", "this refers to", "i.e.", "that is"]
            )
            if not has_explanations:
                score *= 0.9
                issues.append("Heavy jargon without explanations")

        # 3. Estrutura clara (parágrafos, listas)
        has_structure = any(marker in answer for marker in ["\n\n", "\n-", "\n1."])
        if not has_structure and len(answer) > 300:
            score *= 0.95
            issues.append("Long answer lacks paragraph structure")

        return score, issues


class SelfReflectionEngine:
    """
    Engine principal de auto-reflexão e qualidade.
    """

    def __init__(self, llm_client=None):
        self.llm_client = llm_client

        self.completeness_eval = CompletenessEvaluator()
        self.accuracy_eval = AccuracyEvaluator()
        self.relevance_eval = RelevanceEvaluator()
        self.clarity_eval = ClarityEvaluator()

        self.assessments_history: List[QualityAssessment] = []

    async def assess_quality(
        self,
        query: str,
        answer: str,
        sources: Optional[List[Dict]] = None,
        reasoning_steps: Optional[List[Dict]] = None
    ) -> QualityAssessment:
        """
        Avalia qualidade completa da resposta.

        Args:
            query: Query original do usuário
            answer: Resposta gerada
            sources: Fontes usadas
            reasoning_steps: Passos de raciocínio

        Returns:
            QualityAssessment com score e issues
        """
        dimension_scores = {}
        all_issues = []
        strengths = []

        # 1. COMPLETENESS
        completeness, comp_issues = await self.completeness_eval.evaluate(query, answer)
        dimension_scores[QualityDimension.COMPLETENESS] = completeness

        if completeness > 0.8:
            strengths.append("Answer is complete and comprehensive")
        else:
            all_issues.extend([
                QualityIssue(
                    dimension=QualityDimension.COMPLETENESS,
                    severity="medium" if completeness > 0.5 else "high",
                    description=issue,
                    suggestion="Address all parts of the question"
                )
                for issue in comp_issues
            ])

        # 2. ACCURACY
        accuracy, acc_issues = await self.accuracy_eval.evaluate(answer, sources)
        dimension_scores[QualityDimension.ACCURACY] = accuracy

        if accuracy > 0.8:
            strengths.append("Answer is factually accurate")
        else:
            all_issues.extend([
                QualityIssue(
                    dimension=QualityDimension.ACCURACY,
                    severity="critical" if accuracy < 0.5 else "high",
                    description=issue,
                    suggestion="Verify facts and cite sources"
                )
                for issue in acc_issues
            ])

        # 3. RELEVANCE
        relevance, rel_issues = await self.relevance_eval.evaluate(query, answer)
        dimension_scores[QualityDimension.RELEVANCE] = relevance

        if relevance > 0.7:
            strengths.append("Answer is relevant and on-topic")
        else:
            all_issues.extend([
                QualityIssue(
                    dimension=QualityDimension.RELEVANCE,
                    severity="medium",
                    description=issue,
                    suggestion="Focus more on the specific question asked"
                )
                for issue in rel_issues
            ])

        # 4. CLARITY
        clarity, clar_issues = await self.clarity_eval.evaluate(answer)
        dimension_scores[QualityDimension.CLARITY] = clarity

        if clarity > 0.8:
            strengths.append("Answer is clear and well-structured")
        else:
            all_issues.extend([
                QualityIssue(
                    dimension=QualityDimension.CLARITY,
                    severity="low",
                    description=issue,
                    suggestion="Improve clarity and structure"
                )
                for issue in clar_issues
            ])

        # 5. ACTIONABILITY (se aplicável)
        actionability = self._evaluate_actionability(query, answer)
        dimension_scores[QualityDimension.ACTIONABILITY] = actionability

        if actionability > 0.7:
            strengths.append("Answer provides actionable guidance")

        # 6. SAFETY
        safety = self._evaluate_safety(answer)
        dimension_scores[QualityDimension.SAFETY] = safety

        if safety < 0.9:
            all_issues.append(
                QualityIssue(
                    dimension=QualityDimension.SAFETY,
                    severity="critical",
                    description="Answer may contain unsafe content",
                    suggestion="Remove or sanitize sensitive information"
                )
            )

        # Calcula score geral (média ponderada)
        weights = {
            QualityDimension.COMPLETENESS: 0.25,
            QualityDimension.ACCURACY: 0.30,
            QualityDimension.RELEVANCE: 0.20,
            QualityDimension.CLARITY: 0.15,
            QualityDimension.ACTIONABILITY: 0.05,
            QualityDimension.SAFETY: 0.05
        }

        overall_score = sum(
            dimension_scores[dim] * weight
            for dim, weight in weights.items()
        )

        overall_level = self._score_to_level(overall_score)

        # Determina se pode melhorar
        can_improve = overall_score < 0.85 and len(all_issues) > 0

        # Gera sugestões de melhoria
        improvement_suggestions = self._generate_improvements(all_issues, dimension_scores)

        assessment = QualityAssessment(
            overall_score=overall_score,
            overall_level=overall_level,
            dimension_scores=dimension_scores,
            issues=all_issues,
            strengths=strengths,
            can_improve=can_improve,
            improvement_suggestions=improvement_suggestions
        )

        self.assessments_history.append(assessment)

        return assessment

    def _evaluate_actionability(self, query: str, answer: str) -> float:
        """Avalia se resposta é acionável"""
        # Query pede recomendações/ações?
        action_keywords = ["what should", "how to", "recommend", "what can", "steps"]
        needs_action = any(kw in query.lower() for kw in action_keywords)

        if not needs_action:
            return 0.8  # Não aplicável, retorna alto

        # Resposta tem ações/recomendações?
        action_markers = [
            "should", "must", "recommend", "suggest", "step 1",
            "first", "then", "next", "finally"
        ]

        action_count = sum(1 for marker in action_markers if marker in answer.lower())

        return min(action_count / 3.0, 1.0)  # Normaliza: 3+ ações = 1.0

    def _evaluate_safety(self, answer: str) -> float:
        """Avalia se resposta é segura"""
        # Verifica se contém informações perigosas
        unsafe_patterns = [
            r"password.*is.*\w+",  # Senhas expostas
            r"api.*key.*[A-Za-z0-9]{20,}",  # API keys
            r"\d{3}-\d{2}-\d{4}",  # SSN
            r"credit.*card.*\d{4}",  # Cartões de crédito
        ]

        import re
        for pattern in unsafe_patterns:
            if re.search(pattern, answer, re.IGNORECASE):
                return 0.0  # UNSAFE

        return 1.0  # SAFE

    def _score_to_level(self, score: float) -> QualityLevel:
        """Converte score em nível categórico"""
        if score >= 0.9:
            return QualityLevel.EXCELLENT
        elif score >= 0.7:
            return QualityLevel.GOOD
        elif score >= 0.5:
            return QualityLevel.ACCEPTABLE
        elif score >= 0.3:
            return QualityLevel.POOR
        else:
            return QualityLevel.UNACCEPTABLE

    def _generate_improvements(
        self,
        issues: List[QualityIssue],
        scores: Dict[QualityDimension, float]
    ) -> List[str]:
        """Gera sugestões de melhoria"""
        suggestions = []

        # Prioriza issues críticos
        critical = [i for i in issues if i.severity == "critical"]
        high = [i for i in issues if i.severity == "high"]

        for issue in critical + high:
            if issue.suggestion:
                suggestions.append(issue.suggestion)

        # Adiciona sugestões gerais para scores baixos
        for dim, score in scores.items():
            if score < 0.6:
                if dim == QualityDimension.COMPLETENESS:
                    suggestions.append("Provide more comprehensive coverage of the topic")
                elif dim == QualityDimension.ACCURACY:
                    suggestions.append("Add citations and verify facts")
                elif dim == QualityDimension.CLARITY:
                    suggestions.append("Simplify language and improve structure")

        return list(set(suggestions))[:5]  # Top 5 únicas

    async def attempt_correction(
        self,
        query: str,
        original_answer: str,
        assessment: QualityAssessment
    ) -> Optional[CorrectionAttempt]:
        """
        Tenta corrigir automaticamente a resposta.

        Returns:
            CorrectionAttempt se conseguiu corrigir, None caso contrário
        """
        if not assessment.can_improve:
            return None

        # Identifica issue mais crítico
        critical_issue = next(
            (i for i in assessment.issues if i.severity == "critical"),
            next((i for i in assessment.issues if i.severity == "high"), None)
        )

        if not critical_issue:
            return None

        # TODO: Usar LLM para gerar correção
        # Por enquanto, retorna placeholder
        corrected_answer = original_answer
        reasoning = f"Would correct: {critical_issue.description}"

        return CorrectionAttempt(
            issue=critical_issue,
            original_answer=original_answer,
            corrected_answer=corrected_answer,
            success=False,
            reasoning=reasoning
        )

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de qualidade"""
        if not self.assessments_history:
            return {"total_assessments": 0}

        avg_score = sum(a.overall_score for a in self.assessments_history) / len(self.assessments_history)

        level_distribution = {}
        for assessment in self.assessments_history:
            level = assessment.overall_level
            level_distribution[level] = level_distribution.get(level, 0) + 1

        return {
            "total_assessments": len(self.assessments_history),
            "average_score": avg_score,
            "level_distribution": level_distribution,
            "improvement_rate": sum(1 for a in self.assessments_history if a.can_improve) / len(self.assessments_history)
        }


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

async def example_usage():
    """Demonstra uso do sistema de self-reflection"""

    engine = SelfReflectionEngine()

    # Exemplo 1: Resposta de alta qualidade
    print("=== EXAMPLE 1: HIGH QUALITY ANSWER ===")
    assessment1 = await engine.assess_quality(
        query="What is CVE-2024-1234 and how can I mitigate it?",
        answer="""CVE-2024-1234 is a critical remote code execution vulnerability in Apache Log4j version 2.x [SOURCE 1].

It allows attackers to execute arbitrary code via crafted LDAP queries, with a CVSS score of 9.8/10.

MITIGATION STEPS:
1. Immediately upgrade to Log4j 2.17.1 or later
2. If upgrade is not possible, set the system property log4j2.formatMsgNoLookups=true
3. Remove the JndiLookup class from the classpath
4. Monitor for suspicious LDAP requests in logs

This vulnerability is actively exploited in the wild and should be patched immediately [SOURCE 2].""",
        sources=[
            {"id": "nvd", "type": "official_db", "content": "CVE-2024-1234 details"},
            {"id": "cert", "type": "gov", "content": "Mitigation guidance"}
        ]
    )
    print(json.dumps(assessment1.to_dict(), indent=2))

    # Exemplo 2: Resposta de baixa qualidade
    print("\n=== EXAMPLE 2: LOW QUALITY ANSWER ===")
    assessment2 = await engine.assess_quality(
        query="What are the top 3 cyber threats in 2024 and how can I protect against them?",
        answer="I think there are many threats. Ransomware is probably one. Maybe phishing too. It depends on your environment.",
        sources=[]
    )
    print(json.dumps(assessment2.to_dict(), indent=2))

    # Tenta correção
    if assessment2.can_improve:
        correction = await engine.attempt_correction(
            query="What are the top 3 cyber threats in 2024?",
            original_answer="I think there are many threats...",
            assessment=assessment2
        )
        if correction:
            print(f"\nCORRECTION ATTEMPTED: {correction.reasoning}")

    # Stats
    print("\n=== STATS ===")
    print(json.dumps(engine.get_stats(), indent=2))


if __name__ == "__main__":
    asyncio.run(example_usage())
