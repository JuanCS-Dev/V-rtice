"""
MEA Integration Bridge
======================

Provides helper utilities to integrate MEA outputs with LRR and ESGT components.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

from consciousness.esgt.coordinator import ESGTCoordinator, SalienceScore
from consciousness.mea import (
    AttentionSchemaModel,
    AttentionState,
    BoundaryAssessment,
    BoundaryDetector,
    IntrospectiveSummary,
    SelfModel,
)
from consciousness.episodic_memory import EpisodicMemory, Episode
from consciousness.autobiographical_narrative import AutobiographicalNarrative
from consciousness.temporal_binding import TemporalBinder


@dataclass
class MEAContextSnapshot:
    """Snapshot of MEA state to feed into other consciousness modules."""

    attention_state: AttentionState
    boundary: BoundaryAssessment
    summary: IntrospectiveSummary
    episode: Episode
    narrative_text: str
    narrative_coherence: float


class MEABridge:
    """
    Utility class that maintains MEA state and exposes integration helpers.
    """

    def __init__(
        self,
        attention_model: AttentionSchemaModel,
        self_model: SelfModel,
        boundary_detector: BoundaryDetector,
        episodic_memory: EpisodicMemory | None = None,
        narrative_builder: AutobiographicalNarrative | None = None,
        temporal_binder: TemporalBinder | None = None,
    ) -> None:
        self.attention_model = attention_model
        self.self_model = self_model
        self.boundary_detector = boundary_detector
        self.episodic_memory = episodic_memory or EpisodicMemory()
        self.narrative_builder = narrative_builder or AutobiographicalNarrative()
        self.temporal_binder = temporal_binder or TemporalBinder()

    def create_snapshot(
        self,
        attention_signals,
        proprio_center: Tuple[float, float, float],
        orientation: Tuple[float, float, float],
    ) -> MEAContextSnapshot:
        """Update underlying models and return integration snapshot."""
        attention_state = self.attention_model.update(attention_signals)
        boundary = self.boundary_detector.evaluate([s.intensity for s in attention_signals if s.modality == "proprioceptive"] or [0.5],
                                                    [s.intensity for s in attention_signals if s.modality != "proprioceptive"] or [0.4])
        self.self_model.update(
            attention_state=attention_state,
            boundary=boundary,
            proprio_center=proprio_center,
            orientation=orientation,
        )
        summary = self.self_model.generate_first_person_report()
        episode = self.episodic_memory.record(attention_state, summary)
        narrative_result = self.narrative_builder.build(self.episodic_memory.timeline())

        return MEAContextSnapshot(
            attention_state=attention_state,
            boundary=boundary,
            summary=summary,
            episode=episode,
            narrative_text=narrative_result.narrative,
            narrative_coherence=narrative_result.coherence_score,
        )

    @staticmethod
    def to_lrr_context(snapshot: MEAContextSnapshot) -> Dict[str, object]:
        """Transform snapshot to LRR context dictionary."""
        return {
            "mea_attention_state": snapshot.attention_state,
            "mea_boundary": snapshot.boundary,
            "mea_summary": snapshot.summary,
            "episodic_episode": snapshot.episode,
            "episodic_narrative": snapshot.narrative_text,
            "episodic_coherence": snapshot.narrative_coherence,
        }

    @staticmethod
    def to_esgt_payload(
        coordinator: ESGTCoordinator,
        snapshot: MEAContextSnapshot,
        arousal_level: float | None = None,
    ) -> Tuple[SalienceScore, dict]:
        """Generate salience score and ESGT content payload from snapshot."""
        salience = coordinator.compute_salience_from_attention(
            attention_state=snapshot.attention_state,
            boundary=snapshot.boundary,
            arousal_level=arousal_level,
        )
        content = coordinator.build_content_from_attention(
            attention_state=snapshot.attention_state,
            summary=snapshot.summary,
        )
        return salience, content
