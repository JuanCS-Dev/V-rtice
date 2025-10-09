"""
MEA - Attention Schema Model package.

Exports main components for convenience.
"""

from .attention_schema import AttentionSchemaModel, AttentionSignal, AttentionState
from .boundary_detector import BoundaryAssessment, BoundaryDetector
from .prediction_validator import PredictionValidator, ValidationMetrics
from .self_model import FirstPersonPerspective, IntrospectiveSummary, SelfModel

__all__ = [
    "AttentionSchemaModel",
    "AttentionSignal",
    "AttentionState",
    "BoundaryDetector",
    "BoundaryAssessment",
    "PredictionValidator",
    "ValidationMetrics",
    "SelfModel",
    "FirstPersonPerspective",
    "IntrospectiveSummary",
]
