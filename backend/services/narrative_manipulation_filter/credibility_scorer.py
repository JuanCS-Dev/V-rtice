"""
Bayesian Credibility Scoring Engine for Cognitive Defense System.

Implements dynamic credibility updates using Beta-Binomial conjugate priors,
exponential temporal decay, and Wilson score confidence intervals.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Tuple

import numpy as np
from scipy.stats import beta as beta_dist

from models import CredibilityRating
from utils import (
    beta_distribution_credibility,
    exponential_decay_weight,
    wilson_score_interval,
)

logger = logging.getLogger(__name__)


class BayesianCredibilityScorer:
    """
    Bayesian credibility scorer with temporal decay and confidence intervals.

    Uses Beta-Binomial conjugate prior for efficient online updates.
    """

    def __init__(
        self,
        prior_alpha: float = 1.0,
        prior_beta: float = 1.0,
        decay_half_life_days: int = 30,
    ):
        """
        Initialize Bayesian scorer.

        Args:
            prior_alpha: Beta prior alpha (successes + 1)
            prior_beta: Beta prior beta (failures + 1)
            decay_half_life_days: Temporal decay half-life
        """
        self.prior_alpha = prior_alpha
        self.prior_beta = prior_beta
        self.decay_half_life_days = decay_half_life_days

    def initialize_from_newsguard(self, newsguard_score: float) -> Tuple[float, float]:
        """
        Initialize Beta parameters from NewsGuard score.

        Maps NewsGuard score (0-100) to Beta distribution parameters
        that reflect the initial credibility assessment.

        Args:
            newsguard_score: NewsGuard score 0-100

        Returns:
            (alpha, beta) parameters
        """
        # Normalize to 0-1
        p = newsguard_score / 100.0

        # Set concentration parameter based on confidence
        # Higher scores -> more concentrated (stronger prior)
        if newsguard_score >= 80:
            concentration = 20  # Very confident
        elif newsguard_score >= 60:
            concentration = 10  # Moderately confident
        elif newsguard_score >= 40:
            concentration = 5  # Low confidence
        else:
            concentration = 2  # Very uncertain

        alpha = p * concentration + 1
        beta = (1 - p) * concentration + 1

        return alpha, beta

    def update_with_observation(
        self,
        alpha: float,
        beta: float,
        is_reliable: bool,
        timestamp: datetime,
        weight: float = 1.0,
    ) -> Tuple[float, float]:
        """
        Update Beta parameters with new observation.

        Args:
            alpha: Current alpha parameter
            beta: Current beta parameter
            is_reliable: Whether content was reliable (True) or false (False)
            timestamp: Observation timestamp
            weight: Observation weight (0-1), default 1.0

        Returns:
            Updated (alpha, beta)
        """
        # Apply temporal decay to existing parameters
        decay = exponential_decay_weight(timestamp, self.decay_half_life_days)

        # Decay pulls parameters toward uniform prior (1, 1)
        alpha_decayed = alpha * decay + 1.0 * (1 - decay)
        beta_decayed = beta * decay + 1.0 * (1 - decay)

        # Update with observation
        if is_reliable:
            alpha_new = alpha_decayed + weight
            beta_new = beta_decayed
        else:
            alpha_new = alpha_decayed
            beta_new = beta_decayed + weight

        return alpha_new, beta_new

    def batch_update(self, alpha: float, beta: float, observations: List[Dict[str, Any]]) -> Tuple[float, float]:
        """
        Update with batch of observations.

        Args:
            alpha: Current alpha
            beta: Current beta
            observations: List of dicts with keys: is_reliable, timestamp, weight (optional)

        Returns:
            Updated (alpha, beta)
        """
        alpha_current = alpha
        beta_current = beta

        for obs in observations:
            alpha_current, beta_current = self.update_with_observation(
                alpha_current,
                beta_current,
                is_reliable=obs["is_reliable"],
                timestamp=obs["timestamp"],
                weight=obs.get("weight", 1.0),
            )

        return alpha_current, beta_current

    def get_credibility_score(self, alpha: float, beta: float, method: str = "mean") -> float:
        """
        Calculate credibility score from Beta parameters.

        Args:
            alpha: Alpha parameter
            beta: Beta parameter
            method: Estimation method ("mean", "mode", "median")

        Returns:
            Credibility score (0-1)
        """
        if method == "mean":
            # Expected value of Beta distribution
            return beta_distribution_credibility(alpha, beta)

        elif method == "mode":
            # Mode (most likely value)
            if alpha > 1 and beta > 1:
                return (alpha - 1) / (alpha + beta - 2)
            else:
                return beta_distribution_credibility(alpha, beta)

        elif method == "median":
            # Median (approximation)
            dist = beta_dist(alpha, beta)
            return dist.median()

        else:
            raise ValueError(f"Unknown method: {method}")

    def get_confidence_interval(self, alpha: float, beta: float, confidence: float = 0.95) -> Tuple[float, float]:
        """
        Calculate credibility confidence interval.

        Args:
            alpha: Alpha parameter
            beta: Beta parameter
            confidence: Confidence level (default 0.95)

        Returns:
            (lower_bound, upper_bound)
        """
        dist = beta_dist(alpha, beta)
        lower = dist.ppf((1 - confidence) / 2)
        upper = dist.ppf((1 + confidence) / 2)
        return lower, upper

    def get_uncertainty(self, alpha: float, beta: float) -> float:
        """
        Calculate uncertainty (variance) of credibility estimate.

        Args:
            alpha: Alpha parameter
            beta: Beta parameter

        Returns:
            Uncertainty (variance)
        """
        return (alpha * beta) / ((alpha + beta) ** 2 * (alpha + beta + 1))

    def categorize_credibility(self, score: float, uncertainty: float = 0.0) -> CredibilityRating:
        """
        Convert score to categorical rating.

        Adjusts thresholds based on uncertainty.

        Args:
            score: Credibility score (0-1)
            uncertainty: Uncertainty measure

        Returns:
            CredibilityRating enum
        """
        # Normalize to 0-100 scale
        score_100 = score * 100

        # Adjust thresholds based on uncertainty
        # Higher uncertainty -> more conservative ratings
        threshold_adjustment = uncertainty * 10

        if score_100 >= (80 - threshold_adjustment):
            return CredibilityRating.TRUSTED
        elif score_100 >= (60 - threshold_adjustment):
            return CredibilityRating.GENERALLY_RELIABLE
        elif score_100 >= (40 - threshold_adjustment):
            return CredibilityRating.PROCEED_WITH_CAUTION
        elif score_100 >= (20 - threshold_adjustment):
            return CredibilityRating.UNRELIABLE
        else:
            return CredibilityRating.HIGHLY_UNRELIABLE

    def wilson_score_lower_bound(self, true_count: int, total_count: int, confidence: float = 0.95) -> float:
        """
        Calculate Wilson score lower bound.

        More conservative than simple proportion, especially for small samples.

        Args:
            true_count: Number of true/reliable observations
            total_count: Total observations
            confidence: Confidence level

        Returns:
            Lower bound of credibility score
        """
        if total_count == 0:
            return 0.0

        lower, _ = wilson_score_interval(true_count, total_count, confidence)
        return lower

    def combine_scores(self, scores: List[float], weights: List[float] = None) -> float:
        """
        Combine multiple credibility scores.

        Args:
            scores: List of credibility scores (0-1)
            weights: Optional weights for each score

        Returns:
            Combined score (0-1)
        """
        if not scores:
            return 0.5  # Neutral

        if weights is None:
            weights = [1.0] * len(scores)

        if len(scores) != len(weights):
            raise ValueError("Scores and weights must have same length")

        # Weighted harmonic mean (more conservative than arithmetic)
        total_weight = sum(weights)
        if total_weight == 0:
            return 0.5

        # Avoid division by zero
        safe_scores = [max(s, 0.01) for s in scores]

        harmonic_mean = total_weight / sum(w / s for w, s in zip(weights, safe_scores))
        return np.clip(harmonic_mean, 0.0, 1.0)

    def reputation_decay(self, current_score: float, days_since_update: int) -> float:
        """
        Apply reputation decay over time.

        Scores drift toward neutral (0.5) without new observations.

        Args:
            current_score: Current credibility score
            days_since_update: Days since last update

        Returns:
            Decayed score
        """
        decay_rate = np.log(2) / self.decay_half_life_days
        decay_factor = np.exp(-decay_rate * days_since_update)

        # Drift toward 0.5 (neutral)
        decayed = current_score * decay_factor + 0.5 * (1 - decay_factor)
        return decayed

    def simulate_future_credibility(self, alpha: float, beta: float, num_simulations: int = 1000) -> Dict[str, Any]:
        """
        Monte Carlo simulation of future credibility.

        Args:
            alpha: Alpha parameter
            beta: Beta parameter
            num_simulations: Number of Monte Carlo samples

        Returns:
            Dict with simulation statistics
        """
        dist = beta_dist(alpha, beta)
        samples = dist.rvs(size=num_simulations)

        return {
            "mean": np.mean(samples),
            "median": np.median(samples),
            "std": np.std(samples),
            "percentile_5": np.percentile(samples, 5),
            "percentile_25": np.percentile(samples, 25),
            "percentile_75": np.percentile(samples, 75),
            "percentile_95": np.percentile(samples, 95),
            "probability_high_credibility": np.mean(samples >= 0.7),
            "probability_low_credibility": np.mean(samples <= 0.3),
        }


# ============================================================================
# CREDIBILITY AGGREGATION STRATEGIES
# ============================================================================


class CredibilityAggregator:
    """Aggregate credibility signals from multiple sources."""

    @staticmethod
    def aggregate_newsguard_and_history(
        newsguard_score: float,
        historical_score: float,
        historical_confidence: float,
        newsguard_weight: float = 0.6,
        history_weight: float = 0.4,
    ) -> float:
        """
        Combine NewsGuard score with historical performance.

        Args:
            newsguard_score: NewsGuard rating (0-100)
            historical_score: Historical Bayesian score (0-1)
            historical_confidence: Confidence in historical score (0-1)
            newsguard_weight: Weight for NewsGuard (default 0.6)
            history_weight: Weight for history (default 0.4)

        Returns:
            Combined score (0-1)
        """
        # Normalize NewsGuard to 0-1
        ng_normalized = newsguard_score / 100.0

        # Adjust weights based on historical confidence
        # Low confidence -> rely more on NewsGuard
        adjusted_ng_weight = newsguard_weight + (1 - historical_confidence) * history_weight / 2
        adjusted_hist_weight = 1 - adjusted_ng_weight

        combined = ng_normalized * adjusted_ng_weight + historical_score * adjusted_hist_weight

        return np.clip(combined, 0.0, 1.0)

    @staticmethod
    def penalty_for_false_content(
        base_score: float,
        false_content_count: int,
        total_count: int,
        severity: float = 0.5,
    ) -> float:
        """
        Apply penalty for false content history.

        Args:
            base_score: Base credibility score
            false_content_count: Number of false content instances
            total_count: Total content analyzed
            severity: Penalty severity (0-1)

        Returns:
            Penalized score
        """
        if total_count == 0:
            return base_score

        false_ratio = false_content_count / total_count
        penalty = false_ratio * severity
        penalized = base_score * (1 - penalty)

        return max(penalized, 0.0)

    @staticmethod
    def boost_for_corrections(base_score: float, correction_rate: float, boost_factor: float = 0.1) -> float:
        """
        Boost score for transparent error corrections.

        Args:
            base_score: Base credibility score
            correction_rate: Rate of corrections (0-1)
            boost_factor: Boost strength (0-1)

        Returns:
            Boosted score
        """
        boost = correction_rate * boost_factor
        boosted = base_score + boost * (1 - base_score)  # Diminishing returns

        return min(boosted, 1.0)
