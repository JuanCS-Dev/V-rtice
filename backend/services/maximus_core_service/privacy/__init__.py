"""
Differential Privacy Module for VÉRTICE Ethical AI System

This module provides differential privacy mechanisms for privacy-preserving
threat intelligence aggregation and analysis.

Key Components:
    - DPMechanisms: Laplace, Gaussian, Exponential mechanisms
    - DPAggregator: Private aggregation (count, sum, mean, histogram)
    - PrivacyAccountant: Privacy budget tracking (ε, δ)
    - PrivacyEngine: High-level DP engine

Privacy Guarantees:
    - (ε, δ)-Differential Privacy
    - Global privacy budget enforcement
    - Composition tracking (sequential, parallel)

Usage:
    >>> from privacy import DPAggregator, PrivacyBudget
    >>>
    >>> # Create aggregator with privacy budget
    >>> aggregator = DPAggregator(epsilon=1.0, delta=1e-5)
    >>>
    >>> # Execute private count query
    >>> result = aggregator.count_by_group(data, group_column="region")
    >>> print(f"Noisy count: {result.noisy_value}")
    >>> print(f"Privacy budget used: ε={result.epsilon_used}")

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
Version: 1.0
"""

from .base import (
    DPResult,
    PrivacyBudget,
    PrivacyLevel,
    PrivacyMechanism,
    PrivacyParameters,
    SensitivityCalculator,
)
from .dp_aggregator import (
    DPAggregator,
    DPQueryType,
)
from .dp_mechanisms import (
    ExponentialMechanism,
    GaussianMechanism,
    LaplaceMechanism,
)
from .privacy_accountant import (
    CompositionType,
    PrivacyAccountant,
)

__all__ = [
    # Base classes
    "PrivacyBudget",
    "PrivacyLevel",
    "PrivacyParameters",
    "DPResult",
    "PrivacyMechanism",
    "SensitivityCalculator",
    # DP Mechanisms
    "LaplaceMechanism",
    "GaussianMechanism",
    "ExponentialMechanism",
    # Aggregator
    "DPAggregator",
    "DPQueryType",
    # Accountant
    "PrivacyAccountant",
    "CompositionType",
]

__version__ = "1.0.0"
__author__ = "Claude Code + JuanCS-Dev"
