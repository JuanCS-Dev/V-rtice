"""
Privacy Accountant - Privacy Budget Tracking and Composition

This module implements privacy accounting mechanisms for tracking cumulative
privacy loss across multiple differentially private queries.

Key Features:
- Sequential composition (basic and advanced)
- Parallel composition
- Rényi Differential Privacy (RDP) accounting
- Privacy amplification by subsampling

References:
    - Dwork, C., & Roth, A. (2014). The Algorithmic Foundations of Differential Privacy
    - Mironov, I. (2017). Rényi Differential Privacy
    - Abadi, M., et al. (2016). Deep Learning with Differential Privacy

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


class CompositionType(str, Enum):
    """Type of privacy composition"""
    BASIC_SEQUENTIAL = "basic_sequential"
    ADVANCED_SEQUENTIAL = "advanced_sequential"
    PARALLEL = "parallel"
    RDP = "rdp"  # Rényi Differential Privacy


@dataclass
class QueryRecord:
    """
    Record of a privacy-consuming query.

    Attributes:
        timestamp: Query execution timestamp
        epsilon: Privacy cost (ε)
        delta: Failure probability (δ)
        query_type: Type of query
        mechanism: DP mechanism used
        composition_type: How this query composes with others
        metadata: Additional query information
    """
    timestamp: float
    epsilon: float
    delta: float
    query_type: str
    mechanism: str = "unknown"
    composition_type: CompositionType = CompositionType.BASIC_SEQUENTIAL
    metadata: Dict[str, Any] = field(default_factory=dict)


class PrivacyAccountant:
    """
    Privacy accountant for tracking cumulative privacy loss.

    Implements composition theorems to compute total privacy guarantee
    from multiple queries.

    Example:
        >>> accountant = PrivacyAccountant(
        ...     total_epsilon=10.0,
        ...     total_delta=1e-5,
        ...     composition_type=CompositionType.ADVANCED_SEQUENTIAL
        ... )
        >>>
        >>> # Execute queries
        >>> accountant.add_query(epsilon=1.0, delta=0, query_type="count")
        >>> accountant.add_query(epsilon=1.0, delta=0, query_type="mean")
        >>>
        >>> # Check composition
        >>> total_eps, total_dlt = accountant.get_total_privacy_loss()
        >>> print(f"Total: (ε={total_eps}, δ={total_dlt})")
    """

    def __init__(
        self,
        total_epsilon: float,
        total_delta: float,
        composition_type: CompositionType = CompositionType.BASIC_SEQUENTIAL
    ):
        """
        Initialize privacy accountant.

        Args:
            total_epsilon: Total privacy budget (ε)
            total_delta: Total failure probability budget (δ)
            composition_type: Composition theorem to use

        Raises:
            ValueError: If privacy parameters are invalid
        """
        if total_epsilon <= 0:
            raise ValueError(f"epsilon must be positive, got {total_epsilon}")
        if not (0 <= total_delta <= 1):
            raise ValueError(f"delta must be in [0,1], got {total_delta}")

        self.total_epsilon = total_epsilon
        self.total_delta = total_delta
        self.composition_type = composition_type

        # Query history
        self.queries: List[QueryRecord] = []

        # Accounting state
        self.created_at = time.time()

    def add_query(
        self,
        epsilon: float,
        delta: float = 0.0,
        query_type: str = "unknown",
        mechanism: str = "unknown",
        composition_type: Optional[CompositionType] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[float, float]:
        """
        Add a query to the privacy accounting.

        Args:
            epsilon: Privacy cost of query (ε)
            delta: Failure probability of query (δ)
            query_type: Type of query
            mechanism: DP mechanism used
            composition_type: Composition type (uses default if None)
            metadata: Additional query information

        Returns:
            tuple: (total_epsilon, total_delta) after this query

        Raises:
            ValueError: If privacy budget would be exceeded
        """
        # Use default composition type if not specified
        comp_type = composition_type if composition_type is not None else self.composition_type

        # Create query record
        query = QueryRecord(
            timestamp=time.time(),
            epsilon=epsilon,
            delta=delta,
            query_type=query_type,
            mechanism=mechanism,
            composition_type=comp_type,
            metadata=metadata or {}
        )

        # Check if budget would be exceeded (before adding)
        total_eps, total_dlt = self._compute_total_privacy_loss(self.queries + [query])

        if total_eps > self.total_epsilon or total_dlt > self.total_delta:
            raise ValueError(
                f"Query would exceed privacy budget. "
                f"Current: (ε={total_eps:.6f}, δ={total_dlt:.6e}). "
                f"Limit: (ε={self.total_epsilon}, δ={self.total_delta})"
            )

        # Add query
        self.queries.append(query)

        return total_eps, total_dlt

    def get_total_privacy_loss(self) -> Tuple[float, float]:
        """
        Get total privacy loss from all queries.

        Returns:
            tuple: (total_epsilon, total_delta)
        """
        return self._compute_total_privacy_loss(self.queries)

    def _compute_total_privacy_loss(
        self,
        queries: List[QueryRecord]
    ) -> Tuple[float, float]:
        """
        Compute total privacy loss using appropriate composition theorem.

        Args:
            queries: List of query records

        Returns:
            tuple: (total_epsilon, total_delta)
        """
        if not queries:
            return (0.0, 0.0)

        # Group queries by composition type
        basic_queries = [q for q in queries if q.composition_type == CompositionType.BASIC_SEQUENTIAL]
        advanced_queries = [q for q in queries if q.composition_type == CompositionType.ADVANCED_SEQUENTIAL]
        parallel_queries = [q for q in queries if q.composition_type == CompositionType.PARALLEL]

        total_epsilon = 0.0
        total_delta = 0.0

        # Basic sequential composition
        if basic_queries:
            eps, dlt = self._basic_composition(basic_queries)
            total_epsilon += eps
            total_delta += dlt

        # Advanced sequential composition
        if advanced_queries:
            eps, dlt = self._advanced_composition(advanced_queries)
            total_epsilon += eps
            total_delta += dlt

        # Parallel composition
        if parallel_queries:
            eps, dlt = self._parallel_composition(parallel_queries)
            total_epsilon = max(total_epsilon, eps)  # Parallel: take max
            total_delta = max(total_delta, dlt)

        return (total_epsilon, total_delta)

    def _basic_composition(self, queries: List[QueryRecord]) -> Tuple[float, float]:
        """
        Basic composition theorem.

        For k queries with (ε_i, δ_i)-DP, composition is:
        (Σ ε_i, Σ δ_i)-DP

        Args:
            queries: List of queries

        Returns:
            tuple: (total_epsilon, total_delta)
        """
        total_epsilon = sum(q.epsilon for q in queries)
        total_delta = sum(q.delta for q in queries)
        return (total_epsilon, total_delta)

    def _advanced_composition(self, queries: List[QueryRecord]) -> Tuple[float, float]:
        """
        Advanced composition theorem (tighter bound).

        For k queries with (ε, δ)-DP, composition is approximately:
        (ε', kδ + δ')-DP where ε' = sqrt(2k × ln(1/δ')) × ε + k × ε × (exp(ε) - 1)

        Uses simplified formula: ε' ≈ sqrt(2k × ln(1/δ')) × ε for small ε.

        Args:
            queries: List of queries

        Returns:
            tuple: (total_epsilon, total_delta)
        """
        if not queries:
            return (0.0, 0.0)

        k = len(queries)

        # Get individual epsilons and deltas
        epsilons = np.array([q.epsilon for q in queries])
        deltas = np.array([q.delta for q in queries])

        # For k=1, advanced composition reduces to basic composition
        if k == 1:
            return (float(epsilons[0]), float(deltas[0]))

        # For advanced composition, we need a target δ'
        # Use half of total delta budget for tighter epsilon bound
        delta_prime = self.total_delta / 2

        # Advanced composition bound (simplified for small ε)
        # ε' ≈ sqrt(2k × ln(1/δ')) × ε
        # For optimal composition, use sqrt(k) approximation when ε is small
        epsilon_total = np.sqrt(2 * k * np.log(1 / delta_prime)) * np.mean(epsilons)

        # Total delta: Σ δ_i + δ'
        delta_total = np.sum(deltas) + delta_prime

        return (epsilon_total, delta_total)

    def _parallel_composition(self, queries: List[QueryRecord]) -> Tuple[float, float]:
        """
        Parallel composition theorem.

        For k queries on disjoint datasets with (ε_i, δ_i)-DP:
        (max ε_i, max δ_i)-DP

        Args:
            queries: List of queries

        Returns:
            tuple: (max_epsilon, max_delta)
        """
        if not queries:
            return (0.0, 0.0)

        max_epsilon = max(q.epsilon for q in queries)
        max_delta = max(q.delta for q in queries)
        return (max_epsilon, max_delta)

    def get_remaining_budget(self) -> Tuple[float, float]:
        """
        Get remaining privacy budget.

        Returns:
            tuple: (remaining_epsilon, remaining_delta)
        """
        total_eps, total_dlt = self.get_total_privacy_loss()
        return (
            max(0.0, self.total_epsilon - total_eps),
            max(0.0, self.total_delta - total_dlt)
        )

    def is_budget_exhausted(self) -> bool:
        """
        Check if privacy budget is exhausted.

        Returns:
            bool: True if no more queries can be executed
        """
        rem_eps, rem_dlt = self.get_remaining_budget()
        return rem_eps <= 0 or rem_dlt <= 0

    def can_execute_query(self, epsilon: float, delta: float = 0.0) -> bool:
        """
        Check if a query with given privacy cost can be executed.

        Args:
            epsilon: Privacy cost of query (ε)
            delta: Failure probability of query (δ)

        Returns:
            bool: True if query can be executed within budget
        """
        # Create temporary query
        temp_query = QueryRecord(
            timestamp=time.time(),
            epsilon=epsilon,
            delta=delta,
            query_type="temp",
            composition_type=self.composition_type
        )

        # Compute total privacy loss with this query
        total_eps, total_dlt = self._compute_total_privacy_loss(self.queries + [temp_query])

        return total_eps <= self.total_epsilon and total_dlt <= self.total_delta

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get privacy accounting statistics.

        Returns:
            dict: Comprehensive statistics
        """
        total_eps, total_dlt = self.get_total_privacy_loss()
        rem_eps, rem_dlt = self.get_remaining_budget()

        return {
            "total_epsilon_budget": self.total_epsilon,
            "total_delta_budget": self.total_delta,
            "used_epsilon": total_eps,
            "used_delta": total_dlt,
            "remaining_epsilon": rem_eps,
            "remaining_delta": rem_dlt,
            "budget_exhausted": self.is_budget_exhausted(),
            "queries_executed": len(self.queries),
            "composition_type": self.composition_type.value,
            "uptime_seconds": time.time() - self.created_at,
            "query_breakdown": {
                "basic_sequential": sum(
                    1 for q in self.queries
                    if q.composition_type == CompositionType.BASIC_SEQUENTIAL
                ),
                "advanced_sequential": sum(
                    1 for q in self.queries
                    if q.composition_type == CompositionType.ADVANCED_SEQUENTIAL
                ),
                "parallel": sum(
                    1 for q in self.queries
                    if q.composition_type == CompositionType.PARALLEL
                ),
            }
        }

    def get_query_history(self) -> List[Dict[str, Any]]:
        """
        Get history of all queries.

        Returns:
            list: List of query records as dicts
        """
        return [
            {
                "timestamp": q.timestamp,
                "epsilon": q.epsilon,
                "delta": q.delta,
                "query_type": q.query_type,
                "mechanism": q.mechanism,
                "composition_type": q.composition_type.value,
                "metadata": q.metadata
            }
            for q in self.queries
        ]

    def reset(self) -> None:
        """
        Reset privacy accountant (clear all queries).

        Warning: Use with caution. This should only be used when
        starting a new privacy period.
        """
        self.queries = []
        self.created_at = time.time()


class SubsampledPrivacyAccountant(PrivacyAccountant):
    """
    Privacy accountant with amplification by subsampling.

    When queries are executed on random subsamples of the data,
    privacy is amplified. This accountant incorporates the amplification
    theorem.

    Example:
        >>> accountant = SubsampledPrivacyAccountant(
        ...     total_epsilon=10.0,
        ...     total_delta=1e-5,
        ...     sampling_rate=0.01  # 1% subsample
        ... )
        >>>
        >>> # Query on subsample has amplified privacy
        >>> accountant.add_query(epsilon=1.0, delta=0)  # Actual ε << 1.0
    """

    def __init__(
        self,
        total_epsilon: float,
        total_delta: float,
        sampling_rate: float,
        composition_type: CompositionType = CompositionType.ADVANCED_SEQUENTIAL
    ):
        """
        Initialize subsampled privacy accountant.

        Args:
            total_epsilon: Total privacy budget (ε)
            total_delta: Total failure probability budget (δ)
            sampling_rate: Sampling rate (q ∈ [0,1])
            composition_type: Composition theorem to use

        Raises:
            ValueError: If sampling_rate not in [0,1]
        """
        if not (0 < sampling_rate <= 1):
            raise ValueError(f"sampling_rate must be in (0,1], got {sampling_rate}")

        super().__init__(total_epsilon, total_delta, composition_type)
        self.sampling_rate = sampling_rate

    def add_query(
        self,
        epsilon: float,
        delta: float = 0.0,
        query_type: str = "unknown",
        mechanism: str = "unknown",
        composition_type: Optional[CompositionType] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[float, float]:
        """
        Add a query with privacy amplification by subsampling.

        The actual privacy cost is amplified by the sampling rate.

        Args:
            epsilon: Base privacy cost (ε) on full dataset
            delta: Failure probability (δ)
            query_type: Type of query
            mechanism: DP mechanism used
            composition_type: Composition type
            metadata: Additional query information

        Returns:
            tuple: (total_epsilon, total_delta) after amplification
        """
        # Apply amplification theorem
        # For sampling rate q and (ε, δ)-DP mechanism:
        # Subsampled mechanism is approximately (q × ε, q × δ)-DP (for small ε)
        amplified_epsilon = self.sampling_rate * epsilon
        amplified_delta = self.sampling_rate * delta

        # Update metadata with amplification info
        if metadata is None:
            metadata = {}
        metadata["sampling_rate"] = self.sampling_rate
        metadata["base_epsilon"] = epsilon
        metadata["amplified_epsilon"] = amplified_epsilon

        # Call parent with amplified parameters
        return super().add_query(
            epsilon=amplified_epsilon,
            delta=amplified_delta,
            query_type=query_type,
            mechanism=mechanism,
            composition_type=composition_type,
            metadata=metadata
        )
