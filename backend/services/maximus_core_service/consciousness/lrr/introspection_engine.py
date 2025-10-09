"""
Introspection engine for MAXIMUS LRR.

Transforms recursive reasoning traces into first-person narratives that can be
interpreted by operators and downstream consciousness components.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Sequence, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from .recursive_reasoner import ReasoningLevel, RecursiveReasoningResult


@dataclass(slots=True)
class IntrospectionHighlight:
    """Structured insights referenced inside the narrative."""

    level: int
    belief_content: str
    confidence: float
    justification_summary: str


@dataclass(slots=True)
class IntrospectionReport:
    """Final introspection output, aligned with blueprint expectations."""

    narrative: str
    beliefs_explained: int
    coherence_score: float
    timestamp: datetime
    highlights: List[IntrospectionHighlight]


class NarrativeGenerator:
    """Compose natural-language narratives from introspection fragments."""

    def construct_narrative(self, fragments: Sequence[str]) -> str:
        if not fragments:
            return "Não há raciocínio suficiente para gerar introspecção."

        if len(fragments) == 1:
            return fragments[0]

        intro = fragments[0]
        body = " ".join(fragments[1:-1]) if len(fragments) > 2 else ""
        conclusion = fragments[-1]

        if body:
            return f"{intro} {body} Portanto, {conclusion}"
        return f"{intro} Portanto, {conclusion}"


class BeliefExplainer:
    """Generate concise explanations for beliefs and justification chains."""

    def summarise_justification(self, level: "ReasoningLevel") -> str:
        if not level.steps:
            return "Sem etapas registradas."

        step = level.steps[0]
        if not step.justification_chain:
            return "Confiança baseada na evidência direta disponível."

        evidences = [belief.content for belief in step.justification_chain[:3]]
        more = "" if len(step.justification_chain) <= 3 else "..."
        evidences_str = "; ".join(evidences)
        return f"Justificações principais: {evidences_str}{more}"


class IntrospectionEngine:
    """Produce first-person introspective reports."""

    def __init__(self) -> None:
        self.narrative_generator = NarrativeGenerator()
        self.belief_explainer = BeliefExplainer()

    def generate_introspection_report(
        self, result: "RecursiveReasoningResult"
    ) -> IntrospectionReport:
        fragments: List[str] = []
        highlights: List[IntrospectionHighlight] = []

        for level in result.levels:
            fragment = self._introspect_level(level)
            fragments.append(fragment)

            highlight = IntrospectionHighlight(
                level=level.level,
                belief_content=level.beliefs[0].content if level.beliefs else "Belief not registered",
                confidence=level.coherence,
                justification_summary=self.belief_explainer.summarise_justification(level),
            )
            highlights.append(highlight)

        narrative = self.narrative_generator.construct_narrative(fragments)

        return IntrospectionReport(
            narrative=narrative,
            beliefs_explained=len(result.levels),
            coherence_score=result.coherence_score,
            timestamp=datetime.utcnow(),
            highlights=highlights,
        )

    def _introspect_level(self, level: "ReasoningLevel") -> str:
        if not level.beliefs:
            return f"Nível {level.level}: não possuo crenças registradas."

        primary_belief = level.beliefs[0]
        confidence = f"{level.coherence:.2f}"

        if level.level == 0:
            return (
                f"Nível 0: percebo '{primary_belief.content}' com confiança calibrada {confidence}."
            )
        if level.level == 1:
            return (
                "Nível 1: reconheço minha crença anterior e justifico-a com base "
                f"em evidências consistentes (confiança {confidence})."
            )
        return (
            f"Nível {level.level}: avalio metacognitivamente que minha crença permanece coerente "
            f"({confidence}) e continuo monitorando possíveis dissonâncias."
        )
