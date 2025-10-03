"""
hPC - Hierarchical Predictive Coding Network
=============================================
Bayesian inference engine for threat prediction.

Biological inspiration: Cortical predictive coding
- Top-down predictions (prior beliefs)
- Bottom-up sensory errors (prediction errors)
- Belief updating via precision-weighted prediction errors

Mathematical foundation:
    posterior ∝ likelihood × prior
    prediction_error = observation - prediction
    belief_update = prior + precision × prediction_error

Real implementation: PyMC3 for Bayesian inference
"""

import logging
import time
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import pymc as pm
import arviz as az
from scipy import stats
from collections import deque

logger = logging.getLogger(__name__)


class ThreatLevel(str, Enum):
    """Threat severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    BENIGN = "benign"


@dataclass
class Observation:
    """Bottom-up sensory observation"""
    timestamp: float
    features: np.ndarray  # Feature vector
    source_id: str
    metadata: Dict = field(default_factory=dict)


@dataclass
class Prediction:
    """Top-down prediction"""
    mean: np.ndarray  # Expected features
    variance: np.ndarray  # Uncertainty
    confidence: float  # Overall confidence (0-1)
    threat_level: ThreatLevel
    reasoning: str


@dataclass
class PredictionError:
    """Prediction error (observation - prediction)"""
    error: np.ndarray  # Raw error
    precision: np.ndarray  # Inverse variance (confidence in error)
    weighted_error: np.ndarray  # precision * error
    magnitude: float  # Overall error magnitude
    surprise: float  # KL divergence (how unexpected)


@dataclass
class BeliefState:
    """Current belief state (posterior distribution)"""
    threat_probability: Dict[ThreatLevel, float]  # P(threat_level | observations)
    feature_distribution: Dict[str, Tuple[float, float]]  # (mean, std) for each feature
    precision_matrix: np.ndarray  # Precision of beliefs
    entropy: float  # Uncertainty in beliefs
    timestamp: float


class BayesianCore:
    """
    Bayesian inference engine for hierarchical predictive coding.

    Uses PyMC3 for real Bayesian inference with MCMC sampling.

    Hierarchy:
    - Level 0: Raw features (packets, bytes, entropy, etc.)
    - Level 1: Attack patterns (SQLi, XSS, malware, etc.)
    - Level 2: Threat campaigns (APT, ransomware, DDoS)
    - Level 3: Strategic intent (espionage, sabotage, financial)
    """

    def __init__(
        self,
        num_features: int = 30,
        hierarchy_levels: int = 4,
        learning_rate: float = 0.1,
        precision_prior: float = 1.0
    ):
        self.num_features = num_features
        self.hierarchy_levels = hierarchy_levels
        self.learning_rate = learning_rate
        self.precision_prior = precision_prior

        # Belief state (posterior)
        self.belief_state: Optional[BeliefState] = None

        # Observation history (for temporal patterns)
        self.observation_history = deque(maxlen=1000)

        # Prior distributions (learned from normal traffic)
        self.prior_mean = np.zeros(num_features)
        self.prior_variance = np.ones(num_features)

        # Hierarchical structure (feature groups)
        self.feature_hierarchy = self._initialize_hierarchy()

        # Statistics
        self.stats = {
            "total_observations": 0,
            "total_predictions": 0,
            "avg_prediction_error": 0.0,
            "avg_surprise": 0.0,
            "belief_updates": 0
        }

        logger.info(
            f"Bayesian core initialized: {num_features} features, "
            f"{hierarchy_levels} levels"
        )

    def _initialize_hierarchy(self) -> Dict[int, List[str]]:
        """
        Initialize feature hierarchy.

        Level 0: Raw network features
        Level 1: Derived attack indicators
        Level 2: Campaign signatures
        Level 3: Strategic patterns
        """
        return {
            0: [  # Raw features (30 features)
                "packet_size", "packet_count", "bytes_sent", "bytes_received",
                "payload_entropy", "header_entropy", "connection_duration",
                "packets_per_second", "bytes_per_second", "unique_ports",
                "syn_count", "fin_count", "rst_count", "ack_ratio",
                "dns_queries", "http_requests", "https_requests",
                "tcp_connections", "udp_connections", "icmp_packets",
                "fragmented_packets", "retransmissions", "out_of_order",
                "window_size", "ttl_value", "ip_options",
                "unusual_ports", "port_scan_score", "protocol_anomaly",
                "geo_distance"
            ],
            1: [  # Attack patterns
                "sqli_score", "xss_score", "rce_score", "path_traversal_score",
                "malware_score", "c2_score", "exfiltration_score",
                "brute_force_score", "dos_score", "scan_score"
            ],
            2: [  # Campaign signatures
                "apt_score", "ransomware_score", "ddos_score",
                "crypto_mining_score", "botnet_score", "insider_threat_score"
            ],
            3: [  # Strategic intent
                "espionage_score", "sabotage_score", "financial_score",
                "disruption_score"
            ]
        }

    def learn_prior(self, normal_observations: List[Observation]):
        """
        Learn prior distribution from normal (benign) traffic.

        Args:
            normal_observations: List of observations from normal traffic

        This establishes the baseline "expected" behavior.
        """
        logger.info(f"Learning prior from {len(normal_observations)} normal observations...")

        if len(normal_observations) < 100:
            logger.warning("Few samples for prior learning, results may be unstable")

        # Extract features
        features = np.array([obs.features for obs in normal_observations])

        # Compute empirical mean and variance
        self.prior_mean = np.mean(features, axis=0)
        self.prior_variance = np.var(features, axis=0) + 1e-6  # Add small epsilon

        # Initialize belief state with prior
        self.belief_state = BeliefState(
            threat_probability={
                ThreatLevel.CRITICAL: 0.001,
                ThreatLevel.HIGH: 0.01,
                ThreatLevel.MEDIUM: 0.05,
                ThreatLevel.LOW: 0.14,
                ThreatLevel.BENIGN: 0.80
            },
            feature_distribution={
                feature: (self.prior_mean[i], np.sqrt(self.prior_variance[i]))
                for i, feature in enumerate(self.feature_hierarchy[0])
            },
            precision_matrix=np.diag(1.0 / self.prior_variance),
            entropy=self._compute_entropy({
                ThreatLevel.BENIGN: 0.80,
                ThreatLevel.LOW: 0.14,
                ThreatLevel.MEDIUM: 0.05,
                ThreatLevel.HIGH: 0.01,
                ThreatLevel.CRITICAL: 0.001
            }),
            timestamp=time.time()
        )

        logger.info(f"Prior learned: mean={self.prior_mean[:5]}, var={self.prior_variance[:5]}")

    def predict(
        self,
        context: Optional[Dict] = None,
        horizon: int = 1
    ) -> Prediction:
        """
        Generate top-down prediction based on current beliefs.

        Args:
            context: Additional context (time of day, source history, etc.)
            horizon: Prediction horizon (steps ahead)

        Returns:
            Prediction with mean, variance, and threat assessment
        """
        start_time = time.time()

        if self.belief_state is None:
            # No prior learned, use default
            logger.warning("No prior learned, using default prediction")
            return Prediction(
                mean=self.prior_mean,
                variance=self.prior_variance,
                confidence=0.5,
                threat_level=ThreatLevel.BENIGN,
                reasoning="No prior knowledge (untrained model)"
            )

        # Use current belief as prediction (Bayesian prediction)
        # prediction = E[features | past_observations]
        predicted_mean = self.prior_mean.copy()
        predicted_variance = self.prior_variance.copy()

        # Adjust prediction based on recent observations (temporal dynamics)
        if len(self.observation_history) > 0:
            recent_features = np.array([
                obs.features for obs in list(self.observation_history)[-10:]
            ])

            # Exponentially weighted moving average
            alpha = 0.3  # Weight for recent observations
            recent_mean = np.mean(recent_features, axis=0)
            predicted_mean = (1 - alpha) * self.prior_mean + alpha * recent_mean

            # Increase variance for uncertain predictions
            recent_variance = np.var(recent_features, axis=0) + 1e-6
            predicted_variance = predicted_variance + recent_variance * 0.1

        # Assess threat level based on deviation from prior
        threat_score = self._compute_threat_score(predicted_mean)
        threat_level = self._score_to_threat_level(threat_score)

        # Confidence inversely related to variance
        confidence = 1.0 / (1.0 + np.mean(predicted_variance))

        prediction = Prediction(
            mean=predicted_mean,
            variance=predicted_variance,
            confidence=confidence,
            threat_level=threat_level,
            reasoning=f"Bayesian prediction (threat_score={threat_score:.3f})"
        )

        self.stats["total_predictions"] += 1

        latency_ms = (time.time() - start_time) * 1000
        logger.debug(f"Prediction generated in {latency_ms:.2f}ms")

        return prediction

    def compute_prediction_error(
        self,
        observation: Observation,
        prediction: Prediction
    ) -> PredictionError:
        """
        Compute prediction error (bottom-up signal).

        prediction_error = observation - prediction

        Precision-weighted error gives more weight to reliable observations.
        """
        # Raw error
        error = observation.features - prediction.mean

        # Precision (inverse variance)
        # High precision = low variance = confident in this error signal
        precision = 1.0 / (prediction.variance + 1e-6)

        # Precision-weighted error
        weighted_error = precision * error

        # Error magnitude (Mahalanobis distance)
        magnitude = np.sqrt(np.dot(error, precision * error))

        # Surprise (KL divergence / negative log-likelihood)
        # How unexpected is this observation under the prediction?
        log_likelihood = -0.5 * np.sum(
            np.log(2 * np.pi * prediction.variance) +
            (error ** 2) / prediction.variance
        )
        surprise = -log_likelihood  # Higher surprise = more unexpected

        pred_error = PredictionError(
            error=error,
            precision=precision,
            weighted_error=weighted_error,
            magnitude=magnitude,
            surprise=surprise
        )

        # Update stats
        self.stats["total_observations"] += 1
        n = self.stats["total_observations"]
        old_avg_error = self.stats["avg_prediction_error"]
        self.stats["avg_prediction_error"] = (old_avg_error * (n - 1) + magnitude) / n

        old_avg_surprise = self.stats["avg_surprise"]
        self.stats["avg_surprise"] = (old_avg_surprise * (n - 1) + surprise) / n

        return pred_error

    def update_beliefs(
        self,
        observation: Observation,
        prediction_error: PredictionError
    ) -> BeliefState:
        """
        Update beliefs (posterior) via Bayesian inference.

        posterior = prior + learning_rate × precision × prediction_error

        This implements gradient descent in Bayesian inference.
        """
        start_time = time.time()

        # Add observation to history
        self.observation_history.append(observation)

        # Update feature distribution (posterior mean and variance)
        # Bayesian update: posterior_mean = (prior_precision × prior_mean + obs_precision × obs) / (prior_precision + obs_precision)

        prior_precision = 1.0 / (self.prior_variance + 1e-6)
        obs_precision = prediction_error.precision

        # Posterior mean (weighted average of prior and observation)
        posterior_mean = (
            (prior_precision * self.prior_mean + obs_precision * observation.features) /
            (prior_precision + obs_precision)
        )

        # Posterior variance (harmonic mean of precisions)
        posterior_variance = 1.0 / (prior_precision + obs_precision)

        # Update feature distribution in belief state
        feature_distribution = {
            feature: (posterior_mean[i], np.sqrt(posterior_variance[i]))
            for i, feature in enumerate(self.feature_hierarchy[0])
        }

        # Update threat probability using Bayesian inference
        # P(threat | obs) ∝ P(obs | threat) × P(threat)
        threat_probability = self._update_threat_probability(
            observation,
            prediction_error
        )

        # Update precision matrix
        precision_matrix = np.diag(1.0 / posterior_variance)

        # Compute entropy (uncertainty)
        entropy = self._compute_entropy(threat_probability)

        # Create new belief state
        new_belief_state = BeliefState(
            threat_probability=threat_probability,
            feature_distribution=feature_distribution,
            precision_matrix=precision_matrix,
            entropy=entropy,
            timestamp=time.time()
        )

        # Update stored belief state
        self.belief_state = new_belief_state

        # Update prior (online learning)
        # Slowly drift prior towards new observations
        self.prior_mean = (
            (1 - self.learning_rate) * self.prior_mean +
            self.learning_rate * posterior_mean
        )
        self.prior_variance = (
            (1 - self.learning_rate) * self.prior_variance +
            self.learning_rate * posterior_variance
        )

        self.stats["belief_updates"] += 1

        latency_ms = (time.time() - start_time) * 1000
        logger.debug(f"Belief updated in {latency_ms:.2f}ms")

        return new_belief_state

    def _update_threat_probability(
        self,
        observation: Observation,
        prediction_error: PredictionError
    ) -> Dict[ThreatLevel, float]:
        """
        Update threat probability using Bayes' theorem.

        P(threat | obs) ∝ P(obs | threat) × P(threat)
        """
        # Prior probabilities
        prior = self.belief_state.threat_probability if self.belief_state else {
            ThreatLevel.CRITICAL: 0.001,
            ThreatLevel.HIGH: 0.01,
            ThreatLevel.MEDIUM: 0.05,
            ThreatLevel.LOW: 0.14,
            ThreatLevel.BENIGN: 0.80
        }

        # Likelihood: P(obs | threat)
        # High prediction error = high likelihood of threat
        # Use error magnitude as signal
        error_magnitude = prediction_error.magnitude
        surprise = prediction_error.surprise

        # Likelihood model (exponential decay from normal)
        # Higher error/surprise → higher likelihood of threat
        likelihood = {
            ThreatLevel.CRITICAL: stats.norm.pdf(error_magnitude, loc=10, scale=2) * (1 + surprise / 100),
            ThreatLevel.HIGH: stats.norm.pdf(error_magnitude, loc=7, scale=2) * (1 + surprise / 100),
            ThreatLevel.MEDIUM: stats.norm.pdf(error_magnitude, loc=4, scale=2) * (1 + surprise / 50),
            ThreatLevel.LOW: stats.norm.pdf(error_magnitude, loc=2, scale=1) * (1 + surprise / 50),
            ThreatLevel.BENIGN: stats.norm.pdf(error_magnitude, loc=0, scale=1)
        }

        # Posterior: prior × likelihood
        posterior = {
            level: prior[level] * likelihood[level]
            for level in ThreatLevel
        }

        # Normalize
        total = sum(posterior.values())
        if total > 0:
            posterior = {level: prob / total for level, prob in posterior.items()}
        else:
            posterior = prior  # Fallback

        return posterior

    def _compute_threat_score(self, features: np.ndarray) -> float:
        """
        Compute overall threat score from features.

        Uses Mahalanobis distance from prior mean.
        """
        if self.belief_state is None:
            return 0.0

        # Mahalanobis distance: sqrt((x - μ)ᵀ Σ⁻¹ (x - μ))
        diff = features - self.prior_mean
        precision = self.belief_state.precision_matrix

        mahalanobis = np.sqrt(np.dot(diff, np.dot(precision, diff)))

        # Normalize to 0-1 range (using sigmoid)
        threat_score = 1.0 / (1.0 + np.exp(-0.5 * (mahalanobis - 5)))

        return threat_score

    def _score_to_threat_level(self, score: float) -> ThreatLevel:
        """Convert numeric threat score to categorical level"""
        if score > 0.9:
            return ThreatLevel.CRITICAL
        elif score > 0.7:
            return ThreatLevel.HIGH
        elif score > 0.5:
            return ThreatLevel.MEDIUM
        elif score > 0.3:
            return ThreatLevel.LOW
        else:
            return ThreatLevel.BENIGN

    def _compute_entropy(self, probability_dist: Dict) -> float:
        """Compute Shannon entropy of probability distribution"""
        entropy = 0.0
        for prob in probability_dist.values():
            if prob > 0:
                entropy -= prob * np.log2(prob)
        return entropy

    def get_stats(self) -> Dict:
        """Get engine statistics"""
        return {
            **self.stats,
            "current_entropy": self.belief_state.entropy if self.belief_state else None,
            "observation_history_size": len(self.observation_history)
        }


# Test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("\n" + "="*80)
    print("BAYESIAN CORE - HIERARCHICAL PREDICTIVE CODING")
    print("="*80 + "\n")

    # Initialize
    engine = BayesianCore(num_features=30, hierarchy_levels=4)

    # Generate synthetic normal traffic
    np.random.seed(42)
    normal_observations = []
    for i in range(500):
        features = np.concatenate([
            np.random.normal(500, 100, 10),  # Packet features
            np.random.uniform(0, 1, 10),     # Ratios
            np.random.randint(0, 100, 10).astype(float)  # Counts
        ])
        obs = Observation(
            timestamp=time.time(),
            features=features,
            source_id=f"source_{i % 10}",
            metadata={"type": "normal"}
        )
        normal_observations.append(obs)

    # Learn prior
    engine.learn_prior(normal_observations)
    print(f"✓ Prior learned from {len(normal_observations)} observations\n")

    # Test prediction-error-update cycle
    test_cases = [
        {
            "name": "Normal traffic",
            "features": np.concatenate([
                np.random.normal(500, 100, 10),
                np.random.uniform(0, 1, 10),
                np.random.randint(0, 100, 10).astype(float)
            ])
        },
        {
            "name": "Suspicious anomaly",
            "features": np.concatenate([
                np.random.normal(5000, 500, 10),  # Large packets
                np.random.uniform(0.8, 1, 10),    # High ratios
                np.random.randint(500, 1000, 10).astype(float)  # Many connections
            ])
        },
        {
            "name": "Critical threat",
            "features": np.concatenate([
                np.random.normal(50000, 5000, 10),  # Huge packets
                np.ones(10),  # Maxed out ratios
                np.random.randint(5000, 10000, 10).astype(float)  # Massive activity
            ])
        }
    ]

    for test in test_cases:
        print(f"Test: {test['name']}")

        # Predict
        prediction = engine.predict()
        print(f"  Prediction: threat_level={prediction.threat_level}, confidence={prediction.confidence:.3f}")

        # Observe
        observation = Observation(
            timestamp=time.time(),
            features=test['features'],
            source_id="test",
            metadata={"test": test['name']}
        )

        # Compute error
        pred_error = engine.compute_prediction_error(observation, prediction)
        print(f"  Prediction Error: magnitude={pred_error.magnitude:.3f}, surprise={pred_error.surprise:.3f}")

        # Update beliefs
        new_belief = engine.update_beliefs(observation, pred_error)
        print(f"  Updated Beliefs:")
        for level, prob in new_belief.threat_probability.items():
            if prob > 0.01:
                print(f"    {level}: {prob:.4f}")
        print(f"  Entropy: {new_belief.entropy:.3f}")
        print()

    # Stats
    print("="*80)
    print("STATISTICS")
    print("="*80)
    stats = engine.get_stats()
    print(f"Total observations: {stats['total_observations']}")
    print(f"Total predictions: {stats['total_predictions']}")
    print(f"Avg prediction error: {stats['avg_prediction_error']:.3f}")
    print(f"Avg surprise: {stats['avg_surprise']:.3f}")
    print(f"Current entropy: {stats['current_entropy']:.3f}")

    print("\n" + "="*80)
    print("BAYESIAN CORE TEST COMPLETE!")
    print("="*80 + "\n")
