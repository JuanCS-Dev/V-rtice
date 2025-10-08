"""
Differential Privacy Aggregator

This module provides high-level API for differentially private aggregation
queries commonly used in threat intelligence analytics:
- Count (by group, by time window)
- Sum (total threats, severity scores)
- Mean (average threat score)
- Histogram (distribution analysis)

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from __future__ import annotations

from enum import Enum
from typing import Any

import numpy as np
import pandas as pd

from .base import (
    DPResult,
    PrivacyBudget,
    PrivacyParameters,
    SensitivityCalculator,
)
from .dp_mechanisms import GaussianMechanism, LaplaceMechanism


class DPQueryType(str, Enum):
    """Type of differential privacy query"""

    COUNT = "count"
    SUM = "sum"
    MEAN = "mean"
    HISTOGRAM = "histogram"
    COUNT_DISTINCT = "count_distinct"


class DPAggregator:
    """
    High-level API for differentially private aggregation.

    Provides simple interface for common threat intelligence queries:
    - Geographic threat distribution
    - Temporal threat patterns
    - Severity statistics
    - Attack vector histograms

    Example:
        >>> aggregator = DPAggregator(epsilon=1.0, delta=1e-5)
        >>> result = aggregator.count_by_group(data=threat_data, group_column="country")
        >>> print(f"Noisy counts: {result.noisy_value}")
    """

    def __init__(
        self,
        epsilon: float = 1.0,
        delta: float = 1e-5,
        privacy_budget: PrivacyBudget | None = None,
        mechanism: str = "laplace",
    ):
        """
        Initialize DP aggregator.

        Args:
            epsilon: Privacy parameter (default: 1.0 - Google-level privacy)
            delta: Failure probability (default: 1e-5)
            privacy_budget: Optional global privacy budget tracker
            mechanism: 'laplace' or 'gaussian' (default: 'laplace')
        """
        self.default_epsilon = epsilon
        self.default_delta = delta
        self.default_mechanism = mechanism

        # Privacy budget tracker (optional)
        self.privacy_budget = privacy_budget

    def _spend_budget(
        self, epsilon: float, delta: float, query_type: str, metadata: dict[str, Any] | None = None
    ) -> None:
        """
        Spend privacy budget if tracker is enabled.

        Args:
            epsilon: Privacy cost of query
            delta: Failure probability
            query_type: Type of query
            metadata: Additional query metadata

        Raises:
            ValueError: If budget is exhausted
        """
        if self.privacy_budget is not None:
            self.privacy_budget.spend(epsilon=epsilon, delta=delta, query_type=query_type, query_metadata=metadata)

    def count(
        self,
        data: pd.DataFrame | np.ndarray | list,
        epsilon: float | None = None,
        delta: float | None = None,
        clamp_output: bool = True,
    ) -> DPResult:
        """
        Differentially private count query.

        Counts the number of records in the dataset with DP guarantee.

        Args:
            data: Dataset to count
            epsilon: Privacy parameter (uses default if None)
            delta: Failure probability (uses default if None)
            clamp_output: If True, clamp negative counts to 0

        Returns:
            DPResult with noisy count
        """
        # Get true count
        if isinstance(data, pd.DataFrame) or isinstance(data, np.ndarray):
            true_count = len(data)
        else:
            true_count = len(data)

        # Privacy parameters
        eps = epsilon if epsilon is not None else self.default_epsilon
        dlt = delta if delta is not None else self.default_delta

        # Sensitivity = 1 (adding/removing one record changes count by 1)
        sensitivity = SensitivityCalculator.count_sensitivity()

        # Create privacy parameters
        params = PrivacyParameters(epsilon=eps, delta=dlt, sensitivity=sensitivity, mechanism=self.default_mechanism)

        # Choose mechanism
        if params.is_pure_dp:
            mechanism = LaplaceMechanism(params)
        else:
            mechanism = GaussianMechanism(params)

        # Execute query
        result = mechanism.execute_query(true_value=float(true_count), query_type=DPQueryType.COUNT.value)

        # Clamp negative counts to 0
        if clamp_output and result.noisy_value < 0:
            result.noisy_value = 0.0

        # Spend budget
        self._spend_budget(eps, dlt, DPQueryType.COUNT.value)

        return result

    def count_by_group(
        self,
        data: pd.DataFrame,
        group_column: str,
        epsilon: float | None = None,
        delta: float | None = None,
        clamp_output: bool = True,
    ) -> DPResult:
        """
        Differentially private group-by count.

        Counts records per group (e.g., threats by country, by attack type).

        Args:
            data: DataFrame with records
            group_column: Column name to group by
            epsilon: Privacy parameter (uses default if None)
            delta: Failure probability (uses default if None)
            clamp_output: If True, clamp negative counts to 0

        Returns:
            DPResult with noisy counts per group (as dict)
        """
        # Get true counts per group
        true_counts = data[group_column].value_counts().to_dict()
        groups = sorted(true_counts.keys())
        true_values = np.array([true_counts[g] for g in groups])

        # Privacy parameters
        eps = epsilon if epsilon is not None else self.default_epsilon
        dlt = delta if delta is not None else self.default_delta

        # Sensitivity = 1 per group (one record affects one group)
        sensitivity = SensitivityCalculator.count_sensitivity()

        # Create privacy parameters
        params = PrivacyParameters(epsilon=eps, delta=dlt, sensitivity=sensitivity, mechanism=self.default_mechanism)

        # Choose mechanism
        if params.is_pure_dp:
            mechanism = LaplaceMechanism(params)
        else:
            mechanism = GaussianMechanism(params)

        # Execute query
        result = mechanism.execute_query(
            true_value=true_values,
            query_type=DPQueryType.COUNT.value,
            metadata={"groups": groups, "group_column": group_column},
        )

        # Clamp negative counts to 0
        if clamp_output:
            result.noisy_value = np.maximum(result.noisy_value, 0)

        # Convert to dict for readability
        noisy_counts = {g: float(c) for g, c in zip(groups, result.noisy_value, strict=False)}
        result.noisy_value = noisy_counts
        result.true_value = true_counts

        # Spend budget
        self._spend_budget(eps, dlt, DPQueryType.COUNT.value, {"groups": len(groups)})

        return result

    def sum(
        self,
        data: pd.DataFrame | np.ndarray | list,
        value_column: str | None = None,
        value_range: float = 1.0,
        epsilon: float | None = None,
        delta: float | None = None,
    ) -> DPResult:
        """
        Differentially private sum query.

        Sums values in a column with DP guarantee.

        Args:
            data: Dataset with values to sum
            value_column: Column name (if DataFrame)
            value_range: Maximum value range [0, R] (for sensitivity calculation)
            epsilon: Privacy parameter (uses default if None)
            delta: Failure probability (uses default if None)

        Returns:
            DPResult with noisy sum
        """
        # Extract values
        if isinstance(data, pd.DataFrame):
            if value_column is None:
                raise ValueError("value_column required for DataFrame")
            values = data[value_column].values
        elif isinstance(data, np.ndarray):
            values = data
        else:
            values = np.array(data)

        # Get true sum
        true_sum = float(np.sum(values))

        # Privacy parameters
        eps = epsilon if epsilon is not None else self.default_epsilon
        dlt = delta if delta is not None else self.default_delta

        # Sensitivity = value_range (one record with max value)
        sensitivity = SensitivityCalculator.sum_sensitivity(value_range)

        # Create privacy parameters
        params = PrivacyParameters(epsilon=eps, delta=dlt, sensitivity=sensitivity, mechanism=self.default_mechanism)

        # Choose mechanism
        if params.is_pure_dp:
            mechanism = LaplaceMechanism(params)
        else:
            mechanism = GaussianMechanism(params)

        # Execute query
        result = mechanism.execute_query(
            true_value=true_sum, query_type=DPQueryType.SUM.value, metadata={"value_range": value_range}
        )

        # Spend budget
        self._spend_budget(eps, dlt, DPQueryType.SUM.value)

        return result

    def mean(
        self,
        data: pd.DataFrame | np.ndarray | list,
        value_column: str | None = None,
        value_range: float = 1.0,
        epsilon: float | None = None,
        delta: float | None = None,
        clamp_bounds: tuple[float, float] | None = None,
    ) -> DPResult:
        """
        Differentially private mean query.

        Computes mean of values with DP guarantee.

        Args:
            data: Dataset with values
            value_column: Column name (if DataFrame)
            value_range: Maximum value range [0, R]
            epsilon: Privacy parameter (uses default if None)
            delta: Failure probability (uses default if None)
            clamp_bounds: Optional (min, max) to clamp values

        Returns:
            DPResult with noisy mean
        """
        # Extract values
        if isinstance(data, pd.DataFrame):
            if value_column is None:
                raise ValueError("value_column required for DataFrame")
            values = data[value_column].values
        elif isinstance(data, np.ndarray):
            values = data
        else:
            values = np.array(data)

        # Clamp values if bounds provided
        if clamp_bounds is not None:
            min_val, max_val = clamp_bounds
            values = np.clip(values, min_val, max_val)

        # Get true mean
        n = len(values)
        true_mean = float(np.mean(values))

        # Privacy parameters
        eps = epsilon if epsilon is not None else self.default_epsilon
        dlt = delta if delta is not None else self.default_delta

        # Sensitivity = value_range / n
        sensitivity = SensitivityCalculator.mean_sensitivity(value_range, n)

        # Create privacy parameters
        params = PrivacyParameters(epsilon=eps, delta=dlt, sensitivity=sensitivity, mechanism=self.default_mechanism)

        # Choose mechanism
        if params.is_pure_dp:
            mechanism = LaplaceMechanism(params)
        else:
            mechanism = GaussianMechanism(params)

        # Execute query
        result = mechanism.execute_query(
            true_value=true_mean, query_type=DPQueryType.MEAN.value, metadata={"value_range": value_range, "n": n}
        )

        # Spend budget
        self._spend_budget(eps, dlt, DPQueryType.MEAN.value)

        return result

    def histogram(
        self,
        data: pd.DataFrame | np.ndarray | list,
        value_column: str | None = None,
        bins: int | np.ndarray = 10,
        epsilon: float | None = None,
        delta: float | None = None,
        clamp_output: bool = True,
    ) -> DPResult:
        """
        Differentially private histogram.

        Computes histogram bin counts with DP guarantee.

        Args:
            data: Dataset with values
            value_column: Column name (if DataFrame)
            bins: Number of bins or bin edges
            epsilon: Privacy parameter (uses default if None)
            delta: Failure probability (uses default if None)
            clamp_output: If True, clamp negative counts to 0

        Returns:
            DPResult with noisy histogram (bin counts)
        """
        # Extract values
        if isinstance(data, pd.DataFrame):
            if value_column is None:
                raise ValueError("value_column required for DataFrame")
            values = data[value_column].values
        elif isinstance(data, np.ndarray):
            values = data
        else:
            values = np.array(data)

        # Compute true histogram
        true_counts, bin_edges = np.histogram(values, bins=bins)

        # Privacy parameters
        eps = epsilon if epsilon is not None else self.default_epsilon
        dlt = delta if delta is not None else self.default_delta

        # Sensitivity = 1 (one record affects at most one bin)
        sensitivity = SensitivityCalculator.histogram_sensitivity()

        # Create privacy parameters
        params = PrivacyParameters(epsilon=eps, delta=dlt, sensitivity=sensitivity, mechanism=self.default_mechanism)

        # Choose mechanism
        if params.is_pure_dp:
            mechanism = LaplaceMechanism(params)
        else:
            mechanism = GaussianMechanism(params)

        # Execute query
        result = mechanism.execute_query(
            true_value=true_counts.astype(float),
            query_type=DPQueryType.HISTOGRAM.value,
            metadata={"bins": len(true_counts), "bin_edges": bin_edges.tolist()},
        )

        # Clamp negative counts to 0
        if clamp_output:
            result.noisy_value = np.maximum(result.noisy_value, 0)

        # Spend budget
        self._spend_budget(eps, dlt, DPQueryType.HISTOGRAM.value)

        return result

    def count_distinct_approximate(
        self,
        data: pd.DataFrame | np.ndarray | list,
        value_column: str | None = None,
        epsilon: float | None = None,
        delta: float | None = None,
    ) -> DPResult:
        """
        Approximate differentially private count distinct.

        Uses HyperLogLog sketch for cardinality estimation with DP noise.

        Note: This is approximate and requires careful sensitivity analysis.
        For small datasets, prefer exact count with post-processing.

        Args:
            data: Dataset with values
            value_column: Column name (if DataFrame)
            epsilon: Privacy parameter (uses default if None)
            delta: Failure probability (uses default if None)

        Returns:
            DPResult with approximate noisy distinct count
        """
        # Extract values
        if isinstance(data, pd.DataFrame):
            if value_column is None:
                raise ValueError("value_column required for DataFrame")
            values = data[value_column].values
        elif isinstance(data, np.ndarray):
            values = data
        else:
            values = np.array(data)

        # Get true distinct count
        true_distinct = float(len(np.unique(values)))

        # Privacy parameters
        eps = epsilon if epsilon is not None else self.default_epsilon
        dlt = delta if delta is not None else self.default_delta

        # Sensitivity: For exact count distinct, sensitivity is 1
        # (adding/removing one record changes distinct count by at most 1)
        sensitivity = 1.0

        # Create privacy parameters
        params = PrivacyParameters(epsilon=eps, delta=dlt, sensitivity=sensitivity, mechanism=self.default_mechanism)

        # Choose mechanism
        if params.is_pure_dp:
            mechanism = LaplaceMechanism(params)
        else:
            mechanism = GaussianMechanism(params)

        # Execute query
        result = mechanism.execute_query(true_value=true_distinct, query_type=DPQueryType.COUNT_DISTINCT.value)

        # Clamp to non-negative
        result.noisy_value = max(0.0, result.noisy_value)

        # Spend budget
        self._spend_budget(eps, dlt, DPQueryType.COUNT_DISTINCT.value)

        return result

    def get_budget_status(self) -> dict[str, Any] | None:
        """
        Get privacy budget statistics.

        Returns:
            dict: Budget statistics if budget tracking enabled, None otherwise
        """
        if self.privacy_budget is None:
            return None

        return self.privacy_budget.get_statistics()
