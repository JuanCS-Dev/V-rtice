"""Base classes and data structures for fairness module.

This module defines the core data structures used throughout the fairness
and bias mitigation system.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ProtectedAttribute(str, Enum):
    """Protected attributes for fairness analysis in cybersecurity context."""

    GEOGRAPHIC_LOCATION = "geographic_location"  # Country/region
    ORGANIZATION_SIZE = "organization_size"  # SMB vs Enterprise
    INDUSTRY_VERTICAL = "industry_vertical"  # Finance, healthcare, tech, etc.


class FairnessMetric(str, Enum):
    """Fairness metrics supported by the system."""

    DEMOGRAPHIC_PARITY = "demographic_parity"  # P(Ŷ=1|A=0) = P(Ŷ=1|A=1)
    EQUALIZED_ODDS = "equalized_odds"  # TPR and FPR equal across groups
    EQUAL_OPPORTUNITY = "equal_opportunity"  # TPR equal across groups
    CALIBRATION = "calibration"  # P(Y=1|Ŷ=p,A=0) = P(Y=1|Ŷ=p,A=1)
    PREDICTIVE_PARITY = "predictive_parity"  # PPV equal across groups
    TREATMENT_EQUALITY = "treatment_equality"  # FN/FP ratio equal across groups


@dataclass
class FairnessResult:
    """Result from fairness constraint evaluation.

    Attributes:
        metric: Fairness metric evaluated
        protected_attribute: Protected attribute analyzed
        group_0_value: Metric value for reference group
        group_1_value: Metric value for protected group
        difference: Absolute difference between groups
        ratio: Ratio between groups (min/max)
        is_fair: Whether fairness constraint is satisfied
        threshold: Fairness threshold used
        timestamp: When evaluation was performed
        sample_size_0: Sample size for group 0
        sample_size_1: Sample size for group 1
        metadata: Additional metadata
    """

    metric: FairnessMetric
    protected_attribute: ProtectedAttribute
    group_0_value: float
    group_1_value: float
    difference: float
    ratio: float
    is_fair: bool
    threshold: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    sample_size_0: int = 0
    sample_size_1: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate fairness result."""
        if not 0.0 <= self.group_0_value <= 1.0:
            raise ValueError(f"group_0_value must be in [0,1], got {self.group_0_value}")
        if not 0.0 <= self.group_1_value <= 1.0:
            raise ValueError(f"group_1_value must be in [0,1], got {self.group_1_value}")
        if not 0.0 <= self.threshold <= 1.0:
            raise ValueError(f"threshold must be in [0,1], got {self.threshold}")

    def get_disparity_percentage(self) -> float:
        """Get disparity as percentage.

        Returns:
            Disparity percentage
        """
        if self.group_0_value > 0:
            return (self.difference / self.group_0_value) * 100
        return 0.0


@dataclass
class BiasDetectionResult:
    """Result from bias detection analysis.

    Attributes:
        bias_detected: Whether bias was detected
        protected_attribute: Protected attribute analyzed
        detection_method: Method used for detection
        p_value: Statistical p-value (if applicable)
        effect_size: Effect size (Cohen's d or similar)
        confidence: Confidence in detection (0-1)
        affected_groups: List of affected groups
        severity: Bias severity (low, medium, high, critical)
        timestamp: When detection was performed
        sample_size: Total sample size
        metadata: Additional metadata
    """

    bias_detected: bool
    protected_attribute: ProtectedAttribute
    detection_method: str
    p_value: float | None = None
    effect_size: float | None = None
    confidence: float = 0.0
    affected_groups: list[str] = field(default_factory=list)
    severity: str = "low"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    sample_size: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate bias detection result."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be in [0,1], got {self.confidence}")
        if self.p_value is not None and not 0.0 <= self.p_value <= 1.0:
            raise ValueError(f"p_value must be in [0,1], got {self.p_value}")
        valid_severities = ["low", "medium", "high", "critical"]
        if self.severity not in valid_severities:
            raise ValueError(f"severity must be one of {valid_severities}")


@dataclass
class MitigationResult:
    """Result from bias mitigation.

    Attributes:
        mitigation_method: Method used for mitigation
        protected_attribute: Protected attribute targeted
        fairness_before: Fairness metrics before mitigation
        fairness_after: Fairness metrics after mitigation
        performance_impact: Impact on model performance
        success: Whether mitigation was successful
        timestamp: When mitigation was performed
        metadata: Additional metadata
    """

    mitigation_method: str
    protected_attribute: ProtectedAttribute
    fairness_before: dict[str, float]
    fairness_after: dict[str, float]
    performance_impact: dict[str, float]  # e.g., {'accuracy': -0.02, 'f1': -0.01}
    success: bool
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_fairness_improvement(self, metric: str) -> float:
        """Get fairness improvement for a specific metric.

        Args:
            metric: Fairness metric name

        Returns:
            Improvement value (positive = better)
        """
        before = self.fairness_before.get(metric, 0.0)
        after = self.fairness_after.get(metric, 0.0)

        # For fairness metrics, closer to 1.0 is better (parity)
        # So improvement is (after - before)
        return after - before


class FairnessException(Exception):
    """Base exception for fairness module errors."""

    pass


class InsufficientDataException(FairnessException):
    """Exception raised when insufficient data for fairness analysis."""

    def __init__(self, required_samples: int, actual_samples: int):
        self.required_samples = required_samples
        self.actual_samples = actual_samples
        super().__init__(
            f"Insufficient data for fairness analysis. Required: {required_samples}, Got: {actual_samples}"
        )


class FairnessViolationException(FairnessException):
    """Exception raised when fairness constraint is violated."""

    def __init__(self, metric: FairnessMetric, result: FairnessResult):
        self.metric = metric
        self.result = result
        super().__init__(
            f"Fairness violation detected: {metric.value}. "
            f"Difference: {result.difference:.3f}, Threshold: {result.threshold:.3f}"
        )
