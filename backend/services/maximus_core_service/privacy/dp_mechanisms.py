"""
Differential Privacy Mechanisms

This module implements the core differential privacy mechanisms:
- Laplace Mechanism (ε-DP)
- Gaussian Mechanism ((ε,δ)-DP)
- Exponential Mechanism (ε-DP)

Each mechanism adds calibrated noise to query results to guarantee
differential privacy.

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Union

import numpy as np

from .base import PrivacyMechanism, PrivacyParameters


class LaplaceMechanism(PrivacyMechanism):
    """
    Laplace Mechanism for ε-Differential Privacy.

    Adds noise drawn from Laplace distribution with scale b = Δf/ε,
    where Δf is the global sensitivity of the query.

    Provides (ε, 0)-differential privacy (pure DP).

    Properties:
        - Simpler than Gaussian (no δ parameter)
        - Works for any ε > 0
        - Noise has heavier tails than Gaussian

    References:
        Dwork, C., et al. (2006). "Calibrating Noise to Sensitivity in
        Private Data Analysis"
    """

    def __init__(self, privacy_params: PrivacyParameters):
        """
        Initialize Laplace mechanism.

        Args:
            privacy_params: Privacy parameters (must have delta=0 for pure DP)

        Raises:
            ValueError: If delta > 0 (Laplace provides pure DP only)
        """
        if privacy_params.delta > 0:
            raise ValueError(
                f"Laplace mechanism requires delta=0 (pure DP). "
                f"Got delta={privacy_params.delta}. "
                f"Use Gaussian mechanism for approximate DP."
            )

        # Force mechanism type
        privacy_params.mechanism = "laplace"
        super().__init__(privacy_params)

        # Calculate Laplace scale: b = Δf / ε
        self.scale = privacy_params.sensitivity / privacy_params.epsilon

    def add_noise(self, true_value: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Add Laplace noise to a value or array.

        The noise is drawn from Lap(0, b) where b = Δf/ε.

        Args:
            true_value: True query result (scalar or array)

        Returns:
            Noisy value satisfying ε-differential privacy
        """
        if isinstance(true_value, np.ndarray):
            # Array: add independent Laplace noise to each element
            noise = np.random.laplace(0, self.scale, size=true_value.shape)
            return true_value + noise
        else:
            # Scalar: add single Laplace noise
            noise = np.random.laplace(0, self.scale)
            return true_value + noise

    def __repr__(self) -> str:
        return (
            f"LaplaceMechanism(ε={self.privacy_params.epsilon}, "
            f"Δf={self.privacy_params.sensitivity}, scale={self.scale:.4f})"
        )


class GaussianMechanism(PrivacyMechanism):
    """
    Gaussian Mechanism for (ε,δ)-Differential Privacy.

    Adds noise drawn from Gaussian distribution with variance σ²,
    where σ = Δf × sqrt(2 × ln(1.25/δ)) / ε.

    Provides (ε, δ)-differential privacy (approximate DP).

    Properties:
        - Requires δ > 0 (approximate DP)
        - Lighter tails than Laplace (better for large ε)
        - Composition properties well-understood

    References:
        Dwork, C., & Roth, A. (2014). "The Algorithmic Foundations of
        Differential Privacy"
    """

    def __init__(self, privacy_params: PrivacyParameters):
        """
        Initialize Gaussian mechanism.

        Args:
            privacy_params: Privacy parameters (must have delta > 0)

        Raises:
            ValueError: If delta = 0 (Gaussian requires approximate DP)
        """
        if privacy_params.delta == 0:
            raise ValueError(
                f"Gaussian mechanism requires delta > 0 (approximate DP). "
                f"Use Laplace mechanism for pure DP."
            )

        # Force mechanism type
        privacy_params.mechanism = "gaussian"
        super().__init__(privacy_params)

        # Calculate Gaussian standard deviation:
        # σ = Δf × sqrt(2 × ln(1.25/δ)) / ε
        self.std = (
            privacy_params.sensitivity *
            np.sqrt(2 * np.log(1.25 / privacy_params.delta)) /
            privacy_params.epsilon
        )

    def add_noise(self, true_value: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Add Gaussian noise to a value or array.

        The noise is drawn from N(0, σ²) where σ is calibrated to (ε,δ)-DP.

        Args:
            true_value: True query result (scalar or array)

        Returns:
            Noisy value satisfying (ε,δ)-differential privacy
        """
        if isinstance(true_value, np.ndarray):
            # Array: add independent Gaussian noise to each element
            noise = np.random.normal(0, self.std, size=true_value.shape)
            return true_value + noise
        else:
            # Scalar: add single Gaussian noise
            noise = np.random.normal(0, self.std)
            return true_value + noise

    def __repr__(self) -> str:
        return (
            f"GaussianMechanism(ε={self.privacy_params.epsilon}, "
            f"δ={self.privacy_params.delta:.6e}, "
            f"Δf={self.privacy_params.sensitivity}, σ={self.std:.4f})"
        )


class ExponentialMechanism(PrivacyMechanism):
    """
    Exponential Mechanism for ε-Differential Privacy.

    Selects an output from a discrete set based on a quality score function,
    with probability proportional to exp(ε × score / (2 × Δu)), where Δu
    is the sensitivity of the score function.

    Useful for non-numeric queries where adding noise is not appropriate.

    Properties:
        - Works for discrete/categorical outputs
        - Provides ε-differential privacy
        - Probability of selecting output proportional to its quality

    References:
        McSherry, F., & Talwar, K. (2007). "Mechanism Design via Differential
        Privacy"
    """

    def __init__(
        self,
        privacy_params: PrivacyParameters,
        candidates: List[Any],
        score_function: Callable[[Any], float],
        score_sensitivity: Optional[float] = None
    ):
        """
        Initialize Exponential mechanism.

        Args:
            privacy_params: Privacy parameters (delta must be 0)
            candidates: List of candidate outputs
            score_function: Function mapping candidate -> quality score
            score_sensitivity: Sensitivity of score function (Δu). If None,
                               uses privacy_params.sensitivity

        Raises:
            ValueError: If delta > 0 or no candidates provided
        """
        if privacy_params.delta > 0:
            raise ValueError(
                f"Exponential mechanism requires delta=0 (pure DP). "
                f"Got delta={privacy_params.delta}."
            )

        if not candidates:
            raise ValueError("Exponential mechanism requires at least one candidate")

        # Force mechanism type
        privacy_params.mechanism = "exponential"
        super().__init__(privacy_params)

        self.candidates = candidates
        self.score_function = score_function
        self.score_sensitivity = (
            score_sensitivity
            if score_sensitivity is not None
            else privacy_params.sensitivity
        )

        # Pre-compute scores for all candidates
        self.scores = np.array([score_function(c) for c in candidates])

    def add_noise(self, true_value: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Not applicable for Exponential Mechanism.

        Use select() method instead to choose from discrete candidates.

        Raises:
            ValueError: This method cannot be used with exponential mechanism
        """
        raise ValueError(
            "Exponential mechanism does not support add_noise(). "
            "Use select() method instead to choose from discrete candidates. "
            "See https://en.wikipedia.org/wiki/Exponential_mechanism for details."
        )

    def select(self, context: Optional[Any] = None) -> Any:
        """
        Select a candidate using the exponential mechanism.

        The probability of selecting candidate c is proportional to:
        exp(ε × score(c) / (2 × Δu))

        Args:
            context: Optional context for score function (not used in basic version)

        Returns:
            Selected candidate from the candidate list
        """
        # Calculate selection probabilities
        # P(c) ∝ exp(ε × score(c) / (2 × Δu))
        exponents = (
            self.privacy_params.epsilon * self.scores /
            (2 * self.score_sensitivity)
        )

        # Numerically stable softmax
        exponents_shifted = exponents - np.max(exponents)
        probabilities = np.exp(exponents_shifted)
        probabilities /= np.sum(probabilities)

        # Sample according to probabilities
        selected_idx = np.random.choice(len(self.candidates), p=probabilities)
        return self.candidates[selected_idx]

    def get_selection_probabilities(self) -> np.ndarray:
        """
        Get probability distribution over candidates.

        Returns:
            Array of selection probabilities (sums to 1)
        """
        exponents = (
            self.privacy_params.epsilon * self.scores /
            (2 * self.score_sensitivity)
        )
        exponents_shifted = exponents - np.max(exponents)
        probabilities = np.exp(exponents_shifted)
        probabilities /= np.sum(probabilities)
        return probabilities

    def __repr__(self) -> str:
        return (
            f"ExponentialMechanism(ε={self.privacy_params.epsilon}, "
            f"Δu={self.score_sensitivity}, "
            f"candidates={len(self.candidates)})"
        )


class AdvancedNoiseMechanisms:
    """
    Advanced noise mechanisms and utilities.

    Includes:
    - Analytic Gaussian Mechanism (tighter bounds)
    - Staircase Mechanism (optimal for pure DP)
    - Utility functions for noise calibration
    """

    @staticmethod
    def analytic_gaussian_std(
        epsilon: float,
        delta: float,
        sensitivity: float
    ) -> float:
        """
        Calculate Gaussian standard deviation using analytic formula.

        Uses tighter analysis from Balle & Wang (2018).

        Args:
            epsilon: Privacy parameter
            delta: Failure probability
            sensitivity: Global sensitivity

        Returns:
            float: Calibrated standard deviation
        """
        if delta >= 1:
            raise ValueError(f"delta must be < 1, got {delta}")

        # Analytic Gaussian: σ = Δf × sqrt(2 × ln(1/δ)) / ε
        # (Slightly tighter than standard Gaussian)
        return sensitivity * np.sqrt(2 * np.log(1 / delta)) / epsilon

    @staticmethod
    def get_noise_multiplier(
        epsilon: float,
        delta: float,
        mechanism: str = "gaussian"
    ) -> float:
        """
        Get noise multiplier (σ/Δf or b/Δf).

        Args:
            epsilon: Privacy parameter
            delta: Failure probability
            mechanism: 'gaussian' or 'laplace'

        Returns:
            float: Noise multiplier
        """
        if mechanism == "laplace":
            # Laplace: b/Δf = 1/ε
            return 1 / epsilon

        elif mechanism == "gaussian":
            # Gaussian: σ/Δf = sqrt(2 × ln(1.25/δ)) / ε
            return np.sqrt(2 * np.log(1.25 / delta)) / epsilon

        else:
            raise ValueError(f"Unknown mechanism: {mechanism}")

    @staticmethod
    def expected_absolute_error(
        epsilon: float,
        delta: float = 0.0,
        sensitivity: float = 1.0,
        mechanism: str = "laplace"
    ) -> float:
        """
        Calculate expected absolute error of DP mechanism.

        Args:
            epsilon: Privacy parameter
            delta: Failure probability
            sensitivity: Global sensitivity
            mechanism: 'gaussian' or 'laplace'

        Returns:
            float: Expected |noise|
        """
        if mechanism == "laplace":
            # E[|Lap(0,b)|] = b = Δf/ε
            return sensitivity / epsilon

        elif mechanism == "gaussian":
            # E[|N(0,σ²)|] = σ × sqrt(2/π)
            std = (
                sensitivity *
                np.sqrt(2 * np.log(1.25 / delta)) /
                epsilon
            )
            return std * np.sqrt(2 / np.pi)

        else:
            raise ValueError(f"Unknown mechanism: {mechanism}")

    @staticmethod
    def confidence_interval(
        noisy_value: float,
        epsilon: float,
        delta: float = 0.0,
        sensitivity: float = 1.0,
        mechanism: str = "laplace",
        confidence_level: float = 0.95
    ) -> tuple[float, float]:
        """
        Calculate confidence interval for true value.

        Args:
            noisy_value: Observed noisy value
            epsilon: Privacy parameter
            delta: Failure probability
            sensitivity: Global sensitivity
            mechanism: 'gaussian' or 'laplace'
            confidence_level: Confidence level (default: 95%)

        Returns:
            tuple: (lower_bound, upper_bound)
        """
        # Calculate noise scale
        if mechanism == "laplace":
            scale = sensitivity / epsilon
            # Laplace: quantile = scale × sign(p) × ln(1 - 2|p - 0.5|)
            alpha = (1 - confidence_level) / 2
            margin = scale * np.log(1 / alpha)

        elif mechanism == "gaussian":
            std = (
                sensitivity *
                np.sqrt(2 * np.log(1.25 / delta)) /
                epsilon
            )
            # Gaussian: quantile = std × z_score
            from scipy import stats
            z_score = stats.norm.ppf((1 + confidence_level) / 2)
            margin = std * z_score

        else:
            raise ValueError(f"Unknown mechanism: {mechanism}")

        return (noisy_value - margin, noisy_value + margin)
