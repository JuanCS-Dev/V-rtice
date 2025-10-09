"""Metacognitive validation utilities for MAXIMUS consciousness stack."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from consciousness.lrr.recursive_reasoner import RecursiveReasoningResult


@dataclass(slots=True)
class MetacognitionMetrics:
    """Aggregated metacognitive metrics derived from reasoning results."""

    self_alignment: float
    narrative_coherence: float
    meta_memory_alignment: float
    introspection_quality: float
    issues: List[str] = field(default_factory=list)

    @property
    def passes(self) -> bool:
        """Return True when all metrics meet minimum thresholds."""
        return (
            self.self_alignment >= 0.8
            and self.narrative_coherence >= 0.85
            and self.meta_memory_alignment >= 0.7
            and self.introspection_quality >= 0.8
        )


class MetacognitionValidator:
    """Evaluates metacognitive consistency using MEA, LRR and episodic signals."""

    def evaluate(self, result: RecursiveReasoningResult) -> MetacognitionMetrics:
        issues: List[str] = []

        attention_state = result.attention_state
        summary = result.self_summary
        boundary = result.boundary_assessment
        episodic_coherence_value = result.episodic_coherence if result.episodic_coherence is not None else 0.0

        if attention_state is None:
            issues.append("Attention state ausente do resultado LRR")
        if summary is None:
            issues.append("Self-summary ausente do resultado LRR")

        # Self alignment: overlap between attention focus and narrative focus
        if attention_state and summary:
            self_alignment = self._token_overlap(attention_state.focus_target, summary.focus_target)
        else:
            self_alignment = 0.0

        # Narrative coherence: combine self narrative confidence with episodic coherence if available
        narrative_coherence = 0.0
        if summary:
            boundary_factor = boundary.stability if boundary else 0.0
            narrative_coherence = 0.5 * summary.confidence + 0.3 * episodic_coherence_value + 0.2 * boundary_factor
        else:
            issues.append("Sem narrativa para avaliar coerência")

        # Meta-memory alignment: compare meta confidence versus episodic coherence metric
        meta_memory_alignment = 0.0
        if result.meta_report:
            meta_reference = narrative_coherence if narrative_coherence > 0 else 0.5
            difference = abs(result.meta_report.average_confidence - meta_reference)
            meta_memory_alignment = max(0.0, 1.0 - difference)
        else:
            issues.append("Meta report ausente para avaliar meta-memory")

        # Introspection quality: heuristics based on narrative length and first-person cues
        introspection_quality = 0.0
        if summary:
            text = summary.narrative.lower()
            length_quality = min(1.0, len(summary.narrative) / 120.0)
            perspective_quality = 1.0 if "eu" in text else 0.5
            introspection_quality = 0.6 * length_quality + 0.4 * perspective_quality
        else:
            issues.append("Sem narrativa introspectiva para avaliar qualidade")

        return MetacognitionMetrics(
            self_alignment=self_alignment,
            narrative_coherence=narrative_coherence,
            meta_memory_alignment=meta_memory_alignment,
            introspection_quality=introspection_quality,
            issues=issues,
        )

    @staticmethod
    def _token_overlap(a: str, b: str) -> float:
        tokens_a = {token for token in a.lower().replace("\n", " ").split() if token}
        tokens_b = {token for token in b.lower().replace("\n", " ").split() if token}
        if not tokens_a or not tokens_b:
            return 0.0
        overlap = len(tokens_a & tokens_b)
        return overlap / len(tokens_a | tokens_b)


__all__ = ["MetacognitionMetrics", "MetacognitionValidator"]
