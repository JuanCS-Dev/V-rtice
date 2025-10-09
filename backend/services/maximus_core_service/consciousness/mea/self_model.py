"""
Self-Model for Attention Schema
===============================

Responsible for maintaining a coherent computational self-representation that
connects attention state, body schema, and first-person perspective.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Sequence, Tuple

from .attention_schema import AttentionState
from .boundary_detector import BoundaryAssessment


@dataclass
class FirstPersonPerspective:
    """Represents the orientation of the self-model in world coordinates."""

    viewpoint: Tuple[float, float, float]  # xyz
    orientation: Tuple[float, float, float]  # pitch, yaw, roll
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class IntrospectiveSummary:
    """Report summarising current self state."""

    narrative: str
    confidence: float
    boundary_stability: float
    focus_target: str
    perspective: FirstPersonPerspective


class SelfModel:
    """
    Maintains the self-model that bridges attention states and body schema.
    """

    def __init__(self) -> None:
        self._perspective_history: List[FirstPersonPerspective] = []
        self._attention_history: List[AttentionState] = []
        self._boundary_history: List[BoundaryAssessment] = []
        self._identity_vector: Tuple[float, float, float] = (0.0, 0.0, 1.0)

    def update(
        self,
        attention_state: AttentionState,
        boundary: BoundaryAssessment,
        proprio_center: Tuple[float, float, float],
        orientation: Tuple[float, float, float],
    ) -> None:
        """
        Update self-model with the latest attention, boundary, and proprioceptive data.
        """
        perspective = FirstPersonPerspective(viewpoint=proprio_center, orientation=orientation)
        self._perspective_history.append(perspective)
        self._attention_history.append(attention_state)
        self._boundary_history.append(boundary)
        self._identity_vector = self._update_identity_vector(attention_state)

    def current_perspective(self) -> FirstPersonPerspective:
        if not self._perspective_history:
            raise RuntimeError("SelfModel has not been initialised yet.")
        return self._perspective_history[-1]

    def current_focus(self) -> AttentionState:
        if not self._attention_history:
            raise RuntimeError("SelfModel has not been initialised yet.")
        return self._attention_history[-1]

    def current_boundary(self) -> BoundaryAssessment:
        if not self._boundary_history:
            raise RuntimeError("SelfModel has not been initialised yet.")
        return self._boundary_history[-1]

    def generate_first_person_report(self) -> IntrospectiveSummary:
        """Generate a first-person narrative aligning with AST requirements."""
        attention = self.current_focus()
        boundary = self.current_boundary()
        perspective = self.current_perspective()

        narrative = (
            f"Eu estou focado em '{attention.focus_target}' com confiança {attention.confidence:.2f}. "
            f"A fronteira corpo-mundo apresenta estabilidade {boundary.stability:.2f} "
            f"e minha perspectiva atual está orientada para {perspective.orientation}."
        )

        combined_confidence = 0.7 * attention.confidence + 0.3 * boundary.stability
        return IntrospectiveSummary(
            narrative=narrative,
            confidence=combined_confidence,
            boundary_stability=boundary.stability,
            focus_target=attention.focus_target,
            perspective=perspective,
        )

    def self_vector(self) -> Tuple[float, float, float]:
        """Return the current identity vector used for self/other distinction."""
        return self._identity_vector

    def _update_identity_vector(self, attention_state: AttentionState) -> Tuple[float, float, float]:
        """
        Update internal identity representation based on attention modality distribution.
        """
        modalities = attention_state.modality_weights
        proprio = modalities.get("proprioceptive", 0.0)
        extero = sum(
            weight for modality, weight in modalities.items() if modality not in {"proprioceptive", "interoceptive"}
        )
        intero = modalities.get("interoceptive", 0.0)

        # Map to vector components (proprio -> x, extero -> y, intero -> z)
        return (
            float(proprio),
            float(extero),
            float(intero),
        )

