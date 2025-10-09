"""
Advanced contradiction detection and belief revision utilities for LRR.

Implements deliberate metacognitive safety checks that extend the basic
BeliefGraph heuristics with lightweight logic-normalisation and revision
strategies aligned with the ROADMAP TO CONSCIOUSNESS blueprint.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Set, Tuple, TYPE_CHECKING

from statistics import fmean

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from .recursive_reasoner import (
        Belief,
        BeliefGraph,
        Contradiction,
        ContradictionType,
        Resolution,
        ResolutionStrategy,
    )


class FirstOrderLogic:
    """
    Minimal first-order logic helper tailored for MAXIMUS beliefs.

    The goal is not to implement a full theorem prover, but to offer
    deterministic normalisation and entailment checks that complement the
    heuristics embedded in ``BeliefGraph``.
    """

    NEGATION_MARKERS: Tuple[str, ...] = ("not ", "¬", "~", "no ", "isn't", "aren't")

    @staticmethod
    def normalise(statement: str) -> str:
        """
        Convert natural-language belief content into a canonical predicate-like
        representation to support equivalence and negation checks.
        """
        cleaned = statement.strip().lower()
        cleaned = cleaned.replace("  ", " ")
        tokens = [
            token.strip(" .")
            for token in cleaned.replace("(", " ").replace(")", " ").split()
            if token
        ]
        return "_".join(tokens)

    def is_direct_negation(self, a: str, b: str) -> bool:
        """
        Identify direct negations using canonical form plus explicit markers.
        """
        norm_a = self.normalise(a)
        norm_b = self.normalise(b)

        if norm_a == norm_b:
            return False

        for marker in self.NEGATION_MARKERS:
            if marker in a.lower():
                candidate = self.normalise(a.lower().replace(marker, ""))
                return candidate == norm_b
            if marker in b.lower():
                candidate = self.normalise(b.lower().replace(marker, ""))
                return candidate == norm_a

        if norm_a.startswith("not_") and norm_a[len("not_") :] == norm_b:
            return True
        if norm_b.startswith("not_") and norm_b[len("not_") :] == norm_a:
            return True

        return False


@dataclass(slots=True)
class ContradictionSummary:
    """Aggregated metrics for contradiction detection cycles."""

    total_detected: int
    direct_count: int
    transitive_count: int
    temporal_count: int
    contextual_count: int
    average_severity: float


@dataclass(slots=True)
class RevisionOutcome:
    """Result of applying belief revision to resolve a contradiction."""

    resolution: "Resolution"
    strategy: "ResolutionStrategy"
    removed_beliefs: List["Belief"]
    modified_beliefs: List["Belief"]


class ContradictionDetector:
    """
    Detector de contradições alinhado ao blueprint LRR.

    Usa ``BeliefGraph`` para heurísticas estruturadas e complementa com um
    analisador lógico leve para capturar contradições que escapem aos índices
    básicos (e.g., variações sintáticas).
    """

    def __init__(self) -> None:
        self.logic_engine = FirstOrderLogic()
        self.contradiction_history: List["Contradiction"] = []
        self.summary_history: List[ContradictionSummary] = []

    async def detect_contradictions(
        self, belief_graph: "BeliefGraph"
    ) -> List["Contradiction"]:
        """
        Detect contradições no grafo de crenças.

        Para preservar responsividade, a varredura principal roda em thread
        própria quando necessário (contradições potencialmente custosas).
        """

        def _scan() -> List["Contradiction"]:
            return belief_graph.detect_contradictions()

        contradictions = await asyncio.to_thread(_scan)
        contradictions = self._augment_with_logical_checks(
            contradictions, belief_graph.beliefs
        )

        self._update_history(contradictions)
        return contradictions

    def latest_summary(self) -> Optional[ContradictionSummary]:
        """Return metrics of the latest detection round."""
        return self.summary_history[-1] if self.summary_history else None

    # --------------------------------------------------------------------- #
    # Private helpers
    # --------------------------------------------------------------------- #

    def _augment_with_logical_checks(
        self, contradictions: List["Contradiction"], beliefs: Iterable["Belief"]
    ) -> List["Contradiction"]:
        """
        Execute complementary logical checks to capture contradictions that
        the structural heuristics might miss (e.g., lexical variations).
        """
        seen_pairs: Set[Tuple[str, str]] = {
            self._sorted_pair(c.belief_a.content, c.belief_b.content)
            for c in contradictions
        }

        additional: List["Contradiction"] = []

        beliefs_list = list(beliefs)
        for i, belief_a in enumerate(beliefs_list):
            for belief_b in beliefs_list[i + 1 :]:
                pair = self._sorted_pair(belief_a.content, belief_b.content)
                if pair in seen_pairs:
                    continue

                if self.logic_engine.is_direct_negation(
                    belief_a.content, belief_b.content
                ):
                    from .recursive_reasoner import (
                        Contradiction,
                        ContradictionType,
                        ResolutionStrategy,
                    )

                    contradiction = Contradiction(
                        belief_a=belief_a,
                        belief_b=belief_b,
                        contradiction_type=ContradictionType.DIRECT,
                        severity=max(belief_a.confidence, belief_b.confidence),
                        suggested_resolution=ResolutionStrategy.RETRACT_WEAKER,
                        explanation=(
                            "Detected via logical normalisation: "
                            f"'{belief_a.content}' vs '{belief_b.content}'"
                        ),
                    )
                    additional.append(contradiction)
                    seen_pairs.add(pair)

        return contradictions + additional

    def _sorted_pair(self, a: str, b: str) -> Tuple[str, str]:
        pair = (a.strip().lower(), b.strip().lower())
        return tuple(sorted(pair))

    def _update_history(self, contradictions: Sequence["Contradiction"]) -> None:
        from .recursive_reasoner import ContradictionType

        self.contradiction_history.extend(contradictions)

        if not contradictions:
            summary = ContradictionSummary(
                total_detected=0,
                direct_count=0,
                transitive_count=0,
                temporal_count=0,
                contextual_count=0,
                average_severity=0.0,
            )
            self.summary_history.append(summary)
            return

        def count(kind: "ContradictionType") -> int:
            return sum(1 for c in contradictions if c.contradiction_type == kind)

        severities = [c.severity for c in contradictions]
        summary = ContradictionSummary(
            total_detected=len(contradictions),
            direct_count=count(ContradictionType.DIRECT),
            transitive_count=count(ContradictionType.TRANSITIVE),
            temporal_count=count(ContradictionType.TEMPORAL),
            contextual_count=count(ContradictionType.CONTEXTUAL),
            average_severity=float(fmean(severities)),
        )
        self.summary_history.append(summary)


class BeliefRevision:
    """
    Implementa revisão de crenças AGM-style para restaurar consistência.
    """

    def __init__(self) -> None:
        self.revision_log: List[RevisionOutcome] = []

    async def revise_belief_graph(
        self, belief_graph: "BeliefGraph", contradiction: "Contradiction"
    ) -> RevisionOutcome:
        """
        Resolve contradição aplicando a estratégia mais conservadora possível.
        """
        strategy = self._select_strategy(contradiction)

        from .recursive_reasoner import Resolution

        resolution = Resolution(
            contradiction=contradiction,
            strategy=strategy,
        )

        removed: List["Belief"] = []
        modified: List["Belief"] = []

        target_beliefs = self._target_beliefs_for_resolution(
            contradiction, strategy
        )
        for belief in target_beliefs:
            before_conf = belief.confidence
            belief_graph.resolve_belief(belief, resolution)
            if strategy == self._hitl_strategy():
                modified.append(belief)
            elif strategy == self._temporize_strategy():
                modified.append(belief)
            elif strategy == self._contextualize_strategy():
                modified.append(belief)
            elif strategy == self._weaken_strategy() and belief.confidence < before_conf:
                modified.append(belief)
            elif belief not in belief_graph.beliefs:
                removed.append(belief)

        outcome = RevisionOutcome(
            resolution=resolution,
            strategy=strategy,
            removed_beliefs=removed,
            modified_beliefs=modified,
        )
        self.revision_log.append(outcome)
        return outcome

    # ------------------------------------------------------------------ #
    # Strategy helpers
    # ------------------------------------------------------------------ #

    def _select_strategy(self, contradiction: "Contradiction") -> "ResolutionStrategy":
        from .recursive_reasoner import ResolutionStrategy

        if contradiction.contradiction_type == self._temporal_type():
            return self._temporize_strategy()

        if contradiction.contradiction_type == self._contextual_type():
            return self._contextualize_strategy()

        if contradiction.severity >= 0.85:
            return ResolutionStrategy.RETRACT_WEAKER

        if contradiction.severity >= 0.6:
            return self._weaken_strategy()

        return self._contextualize_strategy()

    def _target_beliefs_for_resolution(
        self, contradiction: "Contradiction", strategy: "ResolutionStrategy"
    ) -> Sequence["Belief"]:
        from .recursive_reasoner import ResolutionStrategy

        if strategy == ResolutionStrategy.RETRACT_WEAKER:
            return self._select_weaker_belief(contradiction)

        if strategy == ResolutionStrategy.WEAKEN_BOTH:
            return [contradiction.belief_a, contradiction.belief_b]

        return [contradiction.belief_a, contradiction.belief_b]

    def _select_weaker_belief(self, contradiction: "Contradiction") -> Sequence["Belief"]:
        if contradiction.belief_a.confidence <= contradiction.belief_b.confidence:
            return [contradiction.belief_a]
        return [contradiction.belief_b]

    def _weaken_strategy(self) -> "ResolutionStrategy":
        from .recursive_reasoner import ResolutionStrategy

        return ResolutionStrategy.WEAKEN_BOTH

    def _temporize_strategy(self) -> "ResolutionStrategy":
        from .recursive_reasoner import ResolutionStrategy

        return ResolutionStrategy.TEMPORIZE

    def _contextualize_strategy(self) -> "ResolutionStrategy":
        from .recursive_reasoner import ResolutionStrategy

        return ResolutionStrategy.CONTEXTUALIZE

    def _hitl_strategy(self) -> "ResolutionStrategy":
        from .recursive_reasoner import ResolutionStrategy

        return ResolutionStrategy.HITL_ESCALATE

    def _temporal_type(self) -> "ContradictionType":
        from .recursive_reasoner import ContradictionType

        return ContradictionType.TEMPORAL

    def _contextual_type(self) -> "ContradictionType":
        from .recursive_reasoner import ContradictionType

        return ContradictionType.CONTEXTUAL
