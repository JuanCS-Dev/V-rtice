"""Fairness & Bias Mitigation Module for VÉRTICE Platform.

This module provides comprehensive fairness monitoring and bias mitigation for
cybersecurity AI models, ensuring equitable treatment across different groups.

Key Components:
    - FairnessConstraints: Demographic parity, equalized odds, calibration
    - BiasDetector: Statistical tests, disparate impact analysis
    - MitigationEngine: Reweighing, adversarial debiasing, threshold optimization
    - FairnessMonitor: Continuous monitoring and alerting

Protected Attributes:
    - Geographic location (country/region)
    - Organization size (SMB vs Enterprise)
    - Industry vertical

Target Metrics:
    - Fairness violations: <1%
    - Bias detection accuracy: >95%
    - False positive rate: <5%
"""

__version__ = "1.0.0"
__author__ = "VÉRTICE Platform Team"

from .base import BiasDetectionResult, FairnessMetric, FairnessResult, MitigationResult, ProtectedAttribute
from .bias_detector import BiasDetector
from .constraints import FairnessConstraints
from .mitigation import MitigationEngine
from .monitor import FairnessMonitor

__all__ = [
    "ProtectedAttribute",
    "FairnessMetric",
    "FairnessResult",
    "BiasDetectionResult",
    "MitigationResult",
    "FairnessConstraints",
    "BiasDetector",
    "MitigationEngine",
    "FairnessMonitor",
]
