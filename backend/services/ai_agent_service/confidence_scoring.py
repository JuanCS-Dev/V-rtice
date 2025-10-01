"""
Aurora Confidence Scoring System - Trustworthy AI
==================================================

Sistema de scoring de confiança para respostas de IA, resolvendo o problema
crítico do Manifesto: "46% dos profissionais desconfiam da precisão da IA"

O sistema avalia múltiplas dimensões:

1. SOURCE QUALITY - Qualidade das fontes usadas
2. REASONING COHERENCE - Coerência lógica do raciocínio
3. FACTUAL CONSISTENCY - Consistência factual
4. UNCERTAINTY SIGNALS - Sinais de incerteza na resposta
5. HISTORICAL ACCURACY - Precisão histórica do sistema

Inspiração: Anthropic's Constitutional AI, Google's RLHF, Perplexity's Citations
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re
import json


class ConfidenceLevel(str, Enum):
    """Níveis categóricos de confiança"""
    VERY_HIGH = "very_high"  # > 90% - Use with confidence
    HIGH = "high"  # 70-90% - Generally reliable
    MEDIUM = "medium"  # 50-70% - Verify before critical use
    LOW = "low"  # 30-50% - High verification needed
    VERY_LOW = "very_low"  # < 30% - Do not use without verification


class ConfidenceReason(str, Enum):
    """Razões para ajuste de confiança"""
    HIGH_QUALITY_SOURCES = "high_quality_sources"
    MULTIPLE_SOURCES = "multiple_sources"
    STRONG_REASONING = "strong_reasoning"
    FACTUAL_CONSISTENCY = "factual_consistency"
    NO_UNCERTAINTY = "no_uncertainty"
    HISTORICAL_ACCURACY = "historical_accuracy"

    # Negative
    NO_SOURCES = "no_sources"
    LOW_QUALITY_SOURCES = "low_quality_sources"
    WEAK_REASONING = "weak_reasoning"
    CONTRADICTIONS = "contradictions"
    UNCERTAINTY_MARKERS = "uncertainty_markers"
    HISTORICAL_ERRORS = "historical_errors"
    HALLUCINATION_RISK = "hallucination_risk"


@dataclass
class ConfidenceScore:
    """
    Score de confiança com explicação detalhada.
    """
    score: float  # 0-1
    level: ConfidenceLevel
    breakdown: Dict[str, float]  # Scores por dimensão
    reasons: List[ConfidenceReason]  # Razões para o score
    explanation: str  # Explicação human-readable
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "level": self.level,
            "breakdown": self.breakdown,
            "reasons": self.reasons,
            "explanation": self.explanation,
            "warnings": self.warnings,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }

    def is_reliable(self, threshold: float = 0.7) -> bool:
        """Check se score é confiável o suficiente"""
        return self.score >= threshold


@dataclass
class HistoricalRecord:
    """Registro histórico de precisão"""
    query_type: str
    was_correct: bool
    confidence_at_time: float
    actual_accuracy: float
    timestamp: str
    feedback: Optional[str] = None


class SourceQualityAnalyzer:
    """
    Analisa qualidade das fontes usadas na resposta.
    """

    # Tiers de qualidade de fonte
    SOURCE_TIERS = {
        "tier_1": {  # Altamente confiável
            "types": ["official_db", "peer_reviewed", "gov", "academic"],
            "multiplier": 1.0,
            "examples": ["NVD", "CVE", "IEEE", "Nature"]
        },
        "tier_2": {  # Confiável
            "types": ["industry_report", "reputable_news", "documentation"],
            "multiplier": 0.8,
            "examples": ["Threat Intel Feeds", "TechCrunch", "Official Docs"]
        },
        "tier_3": {  # Moderadamente confiável
            "types": ["blog", "forum", "social_media_verified"],
            "multiplier": 0.6,
            "examples": ["Medium", "Reddit", "Twitter Verified"]
        },
        "tier_4": {  # Baixa confiabilidade
            "types": ["unverified", "anonymous", "user_generated"],
            "multiplier": 0.3,
            "examples": ["Random blogs", "Anonymous forums"]
        }
    }

    def analyze(self, sources: List[Dict[str, Any]]) -> Tuple[float, List[str]]:
        """
        Analisa qualidade das fontes.

        Returns:
            (quality_score, issues)
        """
        if not sources:
            return 0.0, ["No sources provided"]

        issues = []
        total_quality = 0.0

        for source in sources:
            source_type = source.get("type", "unverified")
            relevance = source.get("relevance", 0.5)

            # Determina tier
            tier_multiplier = 0.3  # default tier 4
            for tier, config in self.SOURCE_TIERS.items():
                if source_type in config["types"]:
                    tier_multiplier = config["multiplier"]
                    break

            # Quality = tier * relevance
            quality = tier_multiplier * relevance
            total_quality += quality

            # Issues
            if tier_multiplier < 0.5:
                issues.append(f"Low-tier source: {source.get('id', 'unknown')}")

        avg_quality = total_quality / len(sources)

        # Bonus para múltiplas fontes
        if len(sources) >= 3:
            avg_quality = min(avg_quality * 1.1, 1.0)
        elif len(sources) == 1:
            issues.append("Only one source - low redundancy")
            avg_quality *= 0.8

        return avg_quality, issues


class ReasoningCoherenceAnalyzer:
    """
    Analisa coerência lógica do raciocínio.
    """

    COHERENCE_PATTERNS = {
        "strong": [
            r"because\s+\w+",
            r"therefore\s+\w+",
            r"as a result",
            r"consequently",
            r"this means",
            r"which indicates"
        ],
        "weak": [
            r"maybe\s+\w+",
            r"possibly\s+\w+",
            r"might be",
            r"could be",
            r"not sure",
            r"unclear"
        ]
    }

    def analyze(
        self,
        answer: str,
        reasoning_steps: Optional[List[Dict]] = None
    ) -> Tuple[float, List[str]]:
        """
        Analisa coerência do raciocínio.

        Returns:
            (coherence_score, issues)
        """
        issues = []
        score = 0.5  # Baseline

        # 1. Analisa conectores lógicos
        strong_count = sum(
            len(re.findall(pattern, answer.lower()))
            for pattern in self.COHERENCE_PATTERNS["strong"]
        )
        weak_count = sum(
            len(re.findall(pattern, answer.lower()))
            for pattern in self.COHERENCE_PATTERNS["weak"]
        )

        if strong_count > 0:
            score += 0.2
        if weak_count > 2:
            score -= 0.2
            issues.append(f"Multiple weak reasoning signals ({weak_count})")

        # 2. Se tem reasoning steps explícitos
        if reasoning_steps:
            score += 0.2

            # Verifica se steps são coerentes
            steps_with_confidence = [
                s for s in reasoning_steps
                if s.get("confidence", 0) > 0
            ]
            if len(steps_with_confidence) == len(reasoning_steps):
                score += 0.1
            else:
                issues.append("Some reasoning steps lack confidence scores")

        # 3. Verifica contradições internas
        if self._has_contradictions(answer):
            score -= 0.3
            issues.append("Internal contradictions detected")

        return min(max(score, 0.0), 1.0), issues

    def _has_contradictions(self, text: str) -> bool:
        """Detecta contradições simples (placeholder)"""
        # TODO: Análise mais sofisticada
        contradiction_patterns = [
            (r"is\s+\w+", r"is not\s+\w+"),
            (r"will\s+\w+", r"will not\s+\w+"),
            (r"true", r"false")
        ]

        text_lower = text.lower()
        for positive, negative in contradiction_patterns:
            if re.search(positive, text_lower) and re.search(negative, text_lower):
                return True

        return False


class UncertaintyDetector:
    """
    Detecta sinais de incerteza na resposta.
    """

    UNCERTAINTY_MARKERS = [
        # Expressões de incerteza
        "i don't know",
        "i'm not sure",
        "i cannot verify",
        "uncertain",
        "unclear",
        "may not be accurate",
        "might be wrong",
        "could be incorrect",

        # Qualificadores
        "possibly",
        "probably",
        "likely",
        "perhaps",
        "maybe",
        "might",
        "could",

        # Disclaimers
        "based on my training",
        "as of my knowledge cutoff",
        "i don't have access",
        "i cannot access",
        "according to my training data"
    ]

    def analyze(self, text: str) -> Tuple[float, List[str]]:
        """
        Detecta incerteza.

        Returns:
            (certainty_score, uncertainty_markers_found)
        """
        text_lower = text.lower()
        found_markers = []

        for marker in self.UNCERTAINTY_MARKERS:
            if marker in text_lower:
                found_markers.append(marker)

        # Mais markers = menos certeza
        uncertainty_count = len(found_markers)
        certainty_score = max(1.0 - (uncertainty_count * 0.15), 0.0)

        return certainty_score, found_markers


class FactualConsistencyChecker:
    """
    Verifica consistência factual contra fontes.
    """

    def analyze(
        self,
        answer: str,
        sources: List[Dict[str, Any]],
        query: str
    ) -> Tuple[float, List[str]]:
        """
        Verifica consistência factual.

        Returns:
            (consistency_score, issues)
        """
        issues = []

        if not sources:
            return 0.0, ["No sources to verify against"]

        # 1. Verifica se resposta é suportada por fontes
        source_texts = [s.get("content", "") for s in sources]
        combined_sources = " ".join(source_texts).lower()
        answer_lower = answer.lower()

        # Extrai claims principais (simplificado)
        answer_sentences = [s.strip() for s in answer.split(".") if len(s.strip()) > 10]

        if not answer_sentences:
            return 0.5, ["Answer too short to verify"]

        # Verifica cada sentence
        supported_count = 0
        for sentence in answer_sentences[:5]:  # Check primeiras 5 sentences
            # Extrai palavras-chave da sentence
            keywords = [
                word for word in sentence.lower().split()
                if len(word) > 4  # palavras significativas
            ]

            # Verifica se keywords estão nas fontes
            keyword_matches = sum(
                1 for kw in keywords
                if kw in combined_sources
            )

            if len(keywords) > 0:
                support_ratio = keyword_matches / len(keywords)
                if support_ratio > 0.3:  # 30%+ keywords found
                    supported_count += 1

        # Score
        if len(answer_sentences) > 0:
            consistency_score = supported_count / len(answer_sentences)
        else:
            consistency_score = 0.5

        if consistency_score < 0.5:
            issues.append(f"Low factual support: only {consistency_score:.0%}")

        return consistency_score, issues


class HistoricalAccuracyTracker:
    """
    Rastreia precisão histórica do sistema para calibrar confiança.
    """

    def __init__(self):
        self.history: List[HistoricalRecord] = []
        self.accuracy_by_type: Dict[str, float] = {}

    def add_record(self, record: HistoricalRecord):
        """Adiciona registro histórico"""
        self.history.append(record)
        self._update_accuracy_by_type(record)

    def _update_accuracy_by_type(self, record: HistoricalRecord):
        """Atualiza accuracy por tipo de query"""
        qtype = record.query_type

        if qtype not in self.accuracy_by_type:
            self.accuracy_by_type[qtype] = record.actual_accuracy
        else:
            # Média móvel exponencial
            alpha = 0.3
            old_acc = self.accuracy_by_type[qtype]
            new_acc = record.actual_accuracy
            self.accuracy_by_type[qtype] = (alpha * new_acc) + ((1 - alpha) * old_acc)

    def get_calibration_factor(self, query_type: str) -> float:
        """
        Retorna fator de calibração baseado em histórico.

        Se sistema historicamente superestima confiança, ajusta para baixo.
        Se subestima, ajusta para cima.
        """
        if query_type not in self.accuracy_by_type:
            return 1.0  # Sem histórico, sem ajuste

        historical_accuracy = self.accuracy_by_type[query_type]

        # Se accuracy histórica < 70%, sistema superestima → penalizar
        # Se accuracy histórica > 90%, sistema subestima → bonificar
        if historical_accuracy < 0.7:
            return 0.8  # Reduz confiança
        elif historical_accuracy > 0.9:
            return 1.1  # Aumenta confiança
        else:
            return 1.0  # Mantém

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas"""
        total = len(self.history)
        if total == 0:
            return {"total": 0}

        correct = sum(1 for r in self.history if r.was_correct)

        return {
            "total_queries": total,
            "correct": correct,
            "accuracy": correct / total,
            "accuracy_by_type": self.accuracy_by_type
        }


class ConfidenceScoringSystem:
    """
    Sistema completo de scoring de confiança.

    Combina múltiplas dimensões para score final.
    """

    # Pesos para cada dimensão
    WEIGHTS = {
        "source_quality": 0.30,
        "reasoning_coherence": 0.25,
        "factual_consistency": 0.25,
        "certainty": 0.15,
        "historical_accuracy": 0.05
    }

    def __init__(self):
        self.source_analyzer = SourceQualityAnalyzer()
        self.reasoning_analyzer = ReasoningCoherenceAnalyzer()
        self.uncertainty_detector = UncertaintyDetector()
        self.factual_checker = FactualConsistencyChecker()
        self.historical_tracker = HistoricalAccuracyTracker()

    def score(
        self,
        answer: str,
        query: str,
        sources: Optional[List[Dict[str, Any]]] = None,
        reasoning_steps: Optional[List[Dict]] = None,
        query_type: str = "general"
    ) -> ConfidenceScore:
        """
        Calcula confidence score completo.

        Args:
            answer: Resposta gerada
            query: Query original
            sources: Fontes usadas
            reasoning_steps: Passos de raciocínio
            query_type: Tipo de query para calibração histórica

        Returns:
            ConfidenceScore com breakdown detalhado
        """
        sources = sources or []
        reasoning_steps = reasoning_steps or []

        all_issues = []
        reasons = []
        breakdown = {}

        # 1. SOURCE QUALITY
        source_score, source_issues = self.source_analyzer.analyze(sources)
        breakdown["source_quality"] = source_score
        all_issues.extend(source_issues)

        if source_score > 0.8:
            reasons.append(ConfidenceReason.HIGH_QUALITY_SOURCES)
        elif source_score < 0.4:
            reasons.append(ConfidenceReason.LOW_QUALITY_SOURCES)

        if len(sources) >= 3:
            reasons.append(ConfidenceReason.MULTIPLE_SOURCES)
        elif len(sources) == 0:
            reasons.append(ConfidenceReason.NO_SOURCES)

        # 2. REASONING COHERENCE
        reasoning_score, reasoning_issues = self.reasoning_analyzer.analyze(
            answer, reasoning_steps
        )
        breakdown["reasoning_coherence"] = reasoning_score
        all_issues.extend(reasoning_issues)

        if reasoning_score > 0.7:
            reasons.append(ConfidenceReason.STRONG_REASONING)
        elif reasoning_score < 0.4:
            reasons.append(ConfidenceReason.WEAK_REASONING)

        # 3. FACTUAL CONSISTENCY
        consistency_score, consistency_issues = self.factual_checker.analyze(
            answer, sources, query
        )
        breakdown["factual_consistency"] = consistency_score
        all_issues.extend(consistency_issues)

        if consistency_score > 0.7:
            reasons.append(ConfidenceReason.FACTUAL_CONSISTENCY)
        elif consistency_score < 0.5:
            reasons.append(ConfidenceReason.CONTRADICTIONS)

        # 4. CERTAINTY (inverso de incerteza)
        certainty_score, uncertainty_markers = self.uncertainty_detector.analyze(answer)
        breakdown["certainty"] = certainty_score

        if certainty_score > 0.8:
            reasons.append(ConfidenceReason.NO_UNCERTAINTY)
        elif len(uncertainty_markers) > 0:
            reasons.append(ConfidenceReason.UNCERTAINTY_MARKERS)
            all_issues.append(f"Uncertainty markers: {', '.join(uncertainty_markers[:3])}")

        # 5. HISTORICAL ACCURACY
        calibration_factor = self.historical_tracker.get_calibration_factor(query_type)
        breakdown["historical_calibration"] = calibration_factor

        if calibration_factor > 1.0:
            reasons.append(ConfidenceReason.HISTORICAL_ACCURACY)
        elif calibration_factor < 1.0:
            reasons.append(ConfidenceReason.HISTORICAL_ERRORS)

        # 6. WEIGHTED AVERAGE
        raw_score = (
            breakdown["source_quality"] * self.WEIGHTS["source_quality"] +
            breakdown["reasoning_coherence"] * self.WEIGHTS["reasoning_coherence"] +
            breakdown["factual_consistency"] * self.WEIGHTS["factual_consistency"] +
            breakdown["certainty"] * self.WEIGHTS["certainty"]
        )

        # 7. APPLY HISTORICAL CALIBRATION
        final_score = raw_score * calibration_factor
        final_score = min(max(final_score, 0.0), 1.0)  # Clamp 0-1

        # 8. DETERMINE LEVEL
        level = self._score_to_level(final_score)

        # 9. BUILD EXPLANATION
        explanation = self._build_explanation(breakdown, reasons, final_score)

        # 10. WARNINGS
        warnings = []
        if final_score < 0.5:
            warnings.append("⚠️ LOW CONFIDENCE - Verify before using")
        if len(sources) == 0:
            warnings.append("⚠️ NO SOURCES - Answer may be unreliable")
        if len(uncertainty_markers) > 2:
            warnings.append("⚠️ HIGH UNCERTAINTY - Multiple uncertainty signals detected")

        return ConfidenceScore(
            score=final_score,
            level=level,
            breakdown=breakdown,
            reasons=reasons,
            explanation=explanation,
            warnings=warnings,
            metadata={
                "query_type": query_type,
                "sources_count": len(sources),
                "reasoning_steps_count": len(reasoning_steps),
                "issues": all_issues
            }
        )

    def _score_to_level(self, score: float) -> ConfidenceLevel:
        """Converte score numérico em nível categórico"""
        if score >= 0.9:
            return ConfidenceLevel.VERY_HIGH
        elif score >= 0.7:
            return ConfidenceLevel.HIGH
        elif score >= 0.5:
            return ConfidenceLevel.MEDIUM
        elif score >= 0.3:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW

    def _build_explanation(
        self,
        breakdown: Dict[str, float],
        reasons: List[ConfidenceReason],
        final_score: float
    ) -> str:
        """Constrói explicação human-readable"""
        parts = [f"Confidence: {final_score:.0%}"]

        # Top contributors
        sorted_dims = sorted(breakdown.items(), key=lambda x: x[1], reverse=True)
        top_dim = sorted_dims[0]
        parts.append(f"Strongest: {top_dim[0]} ({top_dim[1]:.0%})")

        # Key reasons
        positive = [r for r in reasons if "quality" in r or "strong" in r or "consistency" in r]
        negative = [r for r in reasons if "low" in r or "weak" in r or "uncertainty" in r]

        if positive:
            parts.append(f"Positives: {', '.join([r.split('_')[0] for r in positive[:2]])}")
        if negative:
            parts.append(f"Concerns: {', '.join([r.split('_')[0] for r in negative[:2]])}")

        return " | ".join(parts)

    def provide_feedback(
        self,
        query: str,
        query_type: str,
        was_correct: bool,
        confidence_at_time: float
    ):
        """
        Fornece feedback sobre precisão da resposta.

        Usado para calibrar confiança futura.
        """
        record = HistoricalRecord(
            query_type=query_type,
            was_correct=was_correct,
            confidence_at_time=confidence_at_time,
            actual_accuracy=1.0 if was_correct else 0.0,
            timestamp=datetime.now().isoformat()
        )
        self.historical_tracker.add_record(record)

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do sistema"""
        return {
            "scoring_weights": self.WEIGHTS,
            "historical_stats": self.historical_tracker.get_stats()
        }


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

def example_usage():
    """Demonstra uso do sistema de confidence scoring"""

    scorer = ConfidenceScoringSystem()

    # Exemplo 1: High confidence (boas fontes, raciocínio sólido)
    print("=== EXAMPLE 1: HIGH CONFIDENCE ===")
    score1 = scorer.score(
        answer="CVE-2024-1234 is a critical remote code execution vulnerability in Apache Log4j. It allows attackers to execute arbitrary code via crafted LDAP queries. This is confirmed by the NVD database and has a CVSS score of 9.8.",
        query="What is CVE-2024-1234?",
        sources=[
            {
                "id": "nvd_001",
                "type": "official_db",
                "content": "CVE-2024-1234: Remote code execution vulnerability in Apache Log4j",
                "relevance": 0.95
            },
            {
                "id": "cve_002",
                "type": "gov",
                "content": "CVSS score 9.8, critical severity",
                "relevance": 0.90
            }
        ],
        reasoning_steps=[
            {"type": "analyze", "confidence": 0.9},
            {"type": "synthesize", "confidence": 0.85}
        ],
        query_type="cve_lookup"
    )
    print(json.dumps(score1.to_dict(), indent=2))

    # Exemplo 2: Low confidence (sem fontes, sinais de incerteza)
    print("\n=== EXAMPLE 2: LOW CONFIDENCE ===")
    score2 = scorer.score(
        answer="I'm not sure, but it might be related to some vulnerability. I don't have access to current data, so this may not be accurate.",
        query="What is CVE-2024-9999?",
        sources=[],
        reasoning_steps=[],
        query_type="cve_lookup"
    )
    print(json.dumps(score2.to_dict(), indent=2))

    # Feedback
    scorer.provide_feedback(
        query="What is CVE-2024-1234?",
        query_type="cve_lookup",
        was_correct=True,
        confidence_at_time=0.85
    )

    print("\n=== STATS ===")
    print(json.dumps(scorer.get_stats(), indent=2))


if __name__ == "__main__":
    example_usage()
