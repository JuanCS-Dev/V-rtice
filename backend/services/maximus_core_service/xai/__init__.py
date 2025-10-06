"""XAI (Explainable AI) Module for VÉRTICE Platform.

This module provides explainability capabilities for MAXIMUS decision-making,
implementing LIME, SHAP, and counterfactual explanations adapted for cybersecurity.

Key Components:
    - ExplainerBase: Abstract base class for all explainers
    - CyberSecLIME: LIME adapted for threat classification
    - CyberSecSHAP: SHAP adapted for deep learning cybersecurity models
    - CounterfactualGenerator: Generates "what-if" scenarios
    - FeatureImportanceTracker: Tracks feature importance over time
    - ExplanationEngine: Unified interface for all explainers

Usage:
    >>> from xai import ExplanationEngine
    >>> engine = ExplanationEngine()
    >>> explanation = await engine.explain(
    ...     decision_id="uuid",
    ...     explanation_type="lime",
    ...     detail_level="summary"
    ... )

Performance Target: <2s per explanation
"""

__version__ = "1.0.0"
__author__ = "VÉRTICE Platform Team"

from .base import (
    DetailLevel,
    ExplainerBase,
    ExplanationResult,
    ExplanationType,
    FeatureImportance,
)
from .counterfactual import CounterfactualGenerator
from .engine import ExplanationEngine
from .feature_tracker import FeatureImportanceTracker
from .lime_cybersec import CyberSecLIME
from .shap_cybersec import CyberSecSHAP

__all__ = [
    "ExplainerBase",
    "ExplanationResult",
    "ExplanationType",
    "DetailLevel",
    "FeatureImportance",
    "CyberSecLIME",
    "CyberSecSHAP",
    "CounterfactualGenerator",
    "FeatureImportanceTracker",
    "ExplanationEngine",
]
