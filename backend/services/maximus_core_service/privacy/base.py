"""
Base Classes and Data Structures for Differential Privacy Module

This module provides the foundational classes and data structures used across
the differential privacy implementation.

Classes:
    - PrivacyBudget: Privacy budget tracker (ε, δ)
    - PrivacyParameters: Privacy parameters configuration
    - DPResult: Result of a differentially private query
    - PrivacyMechanism: Abstract base class for DP mechanisms
    - SensitivityCalculator: Utility for calculating query sensitivity

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np


class PrivacyLevel(str, Enum):
    """Privacy level classification"""

    VERY_HIGH = "very_high"  # ε ≤ 0.1
    HIGH = "high"  # 0.1 < ε ≤ 1.0
    MEDIUM = "medium"  # 1.0 < ε ≤ 3.0
    LOW = "low"  # 3.0 < ε ≤ 10.0
    MINIMAL = "minimal"  # ε > 10.0


@dataclass
class PrivacyBudget:
    """
    Privacy budget tracker for (ε, δ)-differential privacy.

    Tracks cumulative privacy loss from multiple queries and enforces
    global privacy budget limits.

    Attributes:
        total_epsilon: Total privacy budget (ε)
        total_delta: Failure probability budget (δ)
        used_epsilon: Cumulative ε used
        used_delta: Cumulative δ used
        queries_executed: List of executed queries with their privacy cost
        created_at: Budget creation timestamp
    """

    total_epsilon: float
    total_delta: float
    used_epsilon: float = 0.0
    used_delta: float = 0.0
    queries_executed: list[dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def __post_init__(self):
        """Validate privacy budget parameters"""
        if self.total_epsilon <= 0:
            raise ValueError(f"epsilon must be positive, got {self.total_epsilon}")
        if not (0 <= self.total_delta <= 1):
            raise ValueError(f"delta must be in [0,1], got {self.total_delta}")

    @property
    def remaining_epsilon(self) -> float:
        """Get remaining epsilon budget"""
        return max(0.0, self.total_epsilon - self.used_epsilon)

    @property
    def remaining_delta(self) -> float:
        """Get remaining delta budget"""
        return max(0.0, self.total_delta - self.used_delta)

    @property
    def budget_exhausted(self) -> bool:
        """Check if privacy budget is exhausted"""
        return self.remaining_epsilon <= 0 or self.remaining_delta <= 0

    @property
    def privacy_level(self) -> PrivacyLevel:
        """Classify current privacy level based on used epsilon"""
        epsilon = self.used_epsilon
        if epsilon <= 0.1:
            return PrivacyLevel.VERY_HIGH
        if epsilon <= 1.0:
            return PrivacyLevel.HIGH
        if epsilon <= 3.0:
            return PrivacyLevel.MEDIUM
        if epsilon <= 10.0:
            return PrivacyLevel.LOW
        return PrivacyLevel.MINIMAL

    def can_execute(self, epsilon: float, delta: float = 0.0) -> bool:
        """
        Check if a query with given privacy cost can be executed.

        Args:
            epsilon: Privacy cost (ε) of the query
            delta: Failure probability (δ) of the query

        Returns:
            bool: True if query can be executed within budget
        """
        return self.remaining_epsilon >= epsilon and self.remaining_delta >= delta

    def spend(
        self,
        epsilon: float,
        delta: float = 0.0,
        query_type: str = "unknown",
        query_metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Spend privacy budget on a query.

        Args:
            epsilon: Privacy cost (ε) of the query
            delta: Failure probability (δ) of the query
            query_type: Type of query (for auditing)
            query_metadata: Additional metadata about the query

        Raises:
            ValueError: If budget is exhausted or query exceeds budget
        """
        if self.budget_exhausted:
            raise ValueError(
                f"Privacy budget exhausted. Remaining: ε={self.remaining_epsilon:.6f}, δ={self.remaining_delta:.6e}"
            )

        if not self.can_execute(epsilon, delta):
            raise ValueError(
                f"Query exceeds remaining budget. "
                f"Required: ε={epsilon}, δ={delta}. "
                f"Remaining: ε={self.remaining_epsilon:.6f}, "
                f"δ={self.remaining_delta:.6e}"
            )

        # Record query
        query_record = {
            "timestamp": time.time(),
            "epsilon": epsilon,
            "delta": delta,
            "query_type": query_type,
            "metadata": query_metadata or {},
        }
        self.queries_executed.append(query_record)

        # Update used budget
        self.used_epsilon += epsilon
        self.used_delta += delta

    def get_statistics(self) -> dict[str, Any]:
        """
        Get privacy budget statistics.

        Returns:
            dict: Statistics including total, used, remaining budgets
        """
        return {
            "total_epsilon": self.total_epsilon,
            "total_delta": self.total_delta,
            "used_epsilon": self.used_epsilon,
            "used_delta": self.used_delta,
            "remaining_epsilon": self.remaining_epsilon,
            "remaining_delta": self.remaining_delta,
            "budget_exhausted": self.budget_exhausted,
            "privacy_level": self.privacy_level.value,
            "queries_executed": len(self.queries_executed),
            "uptime_seconds": time.time() - self.created_at,
        }


@dataclass
class PrivacyParameters:
    """
    Privacy parameters for a differential privacy mechanism.

    Attributes:
        epsilon: Privacy parameter (ε)
        delta: Failure probability (δ)
        sensitivity: Global sensitivity (Δf)
        mechanism: DP mechanism to use ('laplace', 'gaussian', 'exponential')
    """

    epsilon: float
    delta: float = 0.0
    sensitivity: float = 1.0
    mechanism: str = "laplace"

    def __post_init__(self):
        """Validate privacy parameters"""
        if self.epsilon <= 0:
            raise ValueError(f"epsilon must be positive, got {self.epsilon}")
        if not (0 <= self.delta <= 1):
            raise ValueError(f"delta must be in [0,1], got {self.delta}")
        if self.sensitivity < 0:
            raise ValueError(f"sensitivity must be non-negative, got {self.sensitivity}")
        if self.mechanism not in ["laplace", "gaussian", "exponential"]:
            raise ValueError(f"Unknown mechanism: {self.mechanism}")

    @property
    def is_pure_dp(self) -> bool:
        """Check if this is pure (ε,0)-DP"""
        return self.delta == 0.0

    @property
    def noise_scale(self) -> float:
        """
        Calculate noise scale parameter based on mechanism.

        Returns:
            float: Noise scale (b for Laplace, σ for Gaussian)
        """
        if self.mechanism == "laplace":
            # Laplace: b = Δf / ε
            return self.sensitivity / self.epsilon

        if self.mechanism == "gaussian":
            # Gaussian: σ = Δf × sqrt(2 × ln(1.25/δ)) / ε
            if self.delta == 0:
                raise ValueError("Gaussian mechanism requires δ > 0")
            return self.sensitivity * np.sqrt(2 * np.log(1.25 / self.delta)) / self.epsilon

        raise ValueError(f"Noise scale not defined for mechanism: {self.mechanism}")


@dataclass
class DPResult:
    """
    Result of a differentially private query.

    Attributes:
        true_value: True query result (if available, for testing)
        noisy_value: Differentially private (noisy) result
        epsilon_used: Privacy budget (ε) used
        delta_used: Failure probability (δ) used
        sensitivity: Sensitivity of the query
        mechanism: DP mechanism used
        noise_added: Actual noise added (for transparency)
        query_type: Type of query executed
        timestamp: Query execution timestamp
        metadata: Additional query metadata
    """

    true_value: float | np.ndarray | None
    noisy_value: float | np.ndarray
    epsilon_used: float
    delta_used: float
    sensitivity: float
    mechanism: str
    noise_added: float | np.ndarray
    query_type: str
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def absolute_error(self) -> float | None:
        """Calculate absolute error (if true value known)"""
        if self.true_value is None:
            return None

        if isinstance(self.noisy_value, np.ndarray):
            return float(np.abs(self.noisy_value - self.true_value).mean())
        return float(abs(self.noisy_value - self.true_value))

    @property
    def relative_error(self) -> float | None:
        """Calculate relative error (if true value known and non-zero)"""
        if self.true_value is None or self.true_value == 0:
            return None

        abs_error = self.absolute_error
        if abs_error is None:
            return None

        if isinstance(self.true_value, np.ndarray):
            true_val = float(np.abs(self.true_value).mean())
        else:
            true_val = abs(self.true_value)

        return abs_error / true_val if true_val > 0 else None

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary"""
        return {
            "true_value": float(self.true_value) if self.true_value is not None else None,
            "noisy_value": float(self.noisy_value)
            if not isinstance(self.noisy_value, np.ndarray)
            else self.noisy_value.tolist(),
            "epsilon_used": self.epsilon_used,
            "delta_used": self.delta_used,
            "sensitivity": self.sensitivity,
            "mechanism": self.mechanism,
            "noise_added": float(self.noise_added)
            if not isinstance(self.noise_added, np.ndarray)
            else self.noise_added.tolist(),
            "query_type": self.query_type,
            "timestamp": self.timestamp,
            "absolute_error": self.absolute_error,
            "relative_error": self.relative_error,
            "metadata": self.metadata,
        }


class PrivacyMechanism(ABC):
    """
    Abstract base class for differential privacy mechanisms.

    All DP mechanisms (Laplace, Gaussian, Exponential) inherit from this class
    and implement the add_noise() method.
    """

    def __init__(self, privacy_params: PrivacyParameters):
        """
        Initialize privacy mechanism.

        Args:
            privacy_params: Privacy parameters (ε, δ, sensitivity)
        """
        self.privacy_params = privacy_params

    @abstractmethod
    def add_noise(self, true_value: float | np.ndarray) -> float | np.ndarray:
        """
        Add calibrated noise to a value or array.

        Args:
            true_value: True query result

        Returns:
            Noisy value satisfying differential privacy
        """
        pass

    def execute_query(
        self, true_value: float | np.ndarray, query_type: str = "unknown", metadata: dict[str, Any] | None = None
    ) -> DPResult:
        """
        Execute a differentially private query.

        Args:
            true_value: True query result
            query_type: Type of query (for logging)
            metadata: Additional metadata

        Returns:
            DPResult containing noisy value and privacy guarantees
        """
        # Add noise
        noisy_value = self.add_noise(true_value)

        # Calculate noise added
        if isinstance(true_value, np.ndarray):
            noise_added = noisy_value - true_value
        else:
            noise_added = noisy_value - true_value

        # Create result
        return DPResult(
            true_value=true_value,
            noisy_value=noisy_value,
            epsilon_used=self.privacy_params.epsilon,
            delta_used=self.privacy_params.delta,
            sensitivity=self.privacy_params.sensitivity,
            mechanism=self.privacy_params.mechanism,
            noise_added=noise_added,
            query_type=query_type,
            metadata=metadata or {},
        )


class SensitivityCalculator:
    """
    Utility class for calculating query sensitivity.

    Sensitivity (Δf) is the maximum change in query output when
    adding/removing one record from the dataset.
    """

    @staticmethod
    def count_sensitivity() -> float:
        """
        Sensitivity of counting query.

        Adding/removing one record changes count by at most 1.

        Returns:
            float: Sensitivity Δf = 1
        """
        return 1.0

    @staticmethod
    def sum_sensitivity(value_range: float) -> float:
        """
        Sensitivity of sum query.

        Adding/removing one record with value in [0, R] changes sum by at most R.

        Args:
            value_range: Maximum value range (R)

        Returns:
            float: Sensitivity Δf = R
        """
        return value_range

    @staticmethod
    def mean_sensitivity(value_range: float, n: int) -> float:
        """
        Sensitivity of mean query.

        For mean of n values in [0, R]:
        Δf ≈ R/n (assuming n >> 1)

        Args:
            value_range: Maximum value range (R)
            n: Dataset size

        Returns:
            float: Sensitivity Δf ≈ R/n
        """
        if n == 0:
            raise ValueError("Dataset size cannot be zero")
        return value_range / n

    @staticmethod
    def histogram_sensitivity(bins: int = 1) -> float:
        """
        Sensitivity of histogram query.

        Adding/removing one record changes at most one bin by 1.

        Args:
            bins: Number of histogram bins (default: 1)

        Returns:
            float: Sensitivity Δf = 1 (per bin)
        """
        return 1.0
