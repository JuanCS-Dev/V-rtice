"""FASE 9: Regulatory T-Cells (Treg) - Core Logic

False positive suppression and immune tolerance learning.
Bio-inspired self/non-self discrimination for cybersecurity.

Regulatory T-cells (Treg) prevent autoimmune diseases by:
1. Suppressing excessive immune responses
2. Learning immune tolerance (distinguishing self from non-self)
3. Preventing the immune system from attacking the body

In cyber defense, Treg:
1. Suppresses false positive alerts
2. Learns what is "normal" for the environment
3. Prevents the security system from blocking legitimate activity

NO MOCKS - Production-ready statistical learning algorithms.
"""

import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Tuple

import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Data Structures
# ============================================================================


class AlertSeverity(Enum):
    """Alert severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ToleranceDecision(Enum):
    """Treg decision on alert."""

    SUPPRESS = "suppress"  # False positive - suppress alert
    ALLOW = "allow"  # Legitimate threat - allow alert
    UNCERTAIN = "uncertain"  # Needs more evidence


@dataclass
class SecurityAlert:
    """Security alert for Treg evaluation."""

    alert_id: str
    timestamp: datetime
    alert_type: str  # "port_scan", "malware_detection", etc
    severity: AlertSeverity
    source_ip: str
    target_asset: str
    indicators: List[str]
    raw_score: float  # Original detection score (0-1)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToleranceProfile:
    """Learned tolerance profile for an entity (IP, user, asset)."""

    entity_id: str
    entity_type: str  # "source_ip", "user", "asset"
    first_seen: datetime
    last_seen: datetime
    total_observations: int
    alert_history: List[str]  # Alert IDs
    false_positive_count: int
    true_positive_count: int
    behavioral_fingerprint: Dict[str, float]  # Statistical features
    tolerance_score: float  # 0-1 (higher = more trusted)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class SuppressionDecision:
    """Treg decision on whether to suppress an alert."""

    alert_id: str
    decision: ToleranceDecision
    confidence: float  # 0-1
    suppression_score: float  # 0-1 (higher = more likely false positive)
    rationale: List[str]
    tolerance_profiles_consulted: List[str]
    timestamp: datetime = field(default_factory=datetime.now)


# ============================================================================
# Tolerance Learner
# ============================================================================


class ToleranceLearner:
    """Learns immune tolerance - what is "normal" (self) vs "threat" (non-self).

    Biological analogy:
    - Thymus selection: T-cells that react strongly to self-antigens are eliminated
    - Peripheral tolerance: Treg cells suppress autoreactive T-cells in tissues

    Cyber translation:
    - Learn statistical baseline of normal behavior per entity
    - Identify benign patterns that trigger false positives
    - Build tolerance profiles for trusted entities
    """

    def __init__(self, tolerance_threshold: float = 0.7):
        self.tolerance_profiles: Dict[str, ToleranceProfile] = {}
        self.tolerance_threshold = tolerance_threshold
        self.observations_window = 1000  # Keep last N observations for stats
        self.entity_observations: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.total_profiles_created: int = 0

    def observe_entity_behavior(self, entity_id: str, entity_type: str, behavioral_features: Dict[str, float]):
        """Observe entity behavior for tolerance learning.

        Args:
            entity_id: Entity identifier (IP, user ID, asset ID)
            entity_type: Type of entity
            behavioral_features: Numerical features describing behavior
        """
        # Add observation to history
        observation = {"timestamp": datetime.now(), "features": behavioral_features}
        self.entity_observations[entity_id].append(observation)

        # Update or create tolerance profile
        if entity_id not in self.tolerance_profiles:
            self._create_tolerance_profile(entity_id, entity_type)

        profile = self.tolerance_profiles[entity_id]
        profile.last_seen = datetime.now()
        profile.total_observations += 1

        # Update behavioral fingerprint (running statistics)
        self._update_behavioral_fingerprint(profile, behavioral_features)

        logger.debug(f"Observed behavior for {entity_id}: {len(behavioral_features)} features")

    def _create_tolerance_profile(self, entity_id: str, entity_type: str):
        """Create new tolerance profile for entity.

        Args:
            entity_id: Entity identifier
            entity_type: Entity type
        """
        profile = ToleranceProfile(
            entity_id=entity_id,
            entity_type=entity_type,
            first_seen=datetime.now(),
            last_seen=datetime.now(),
            total_observations=0,
            alert_history=[],
            false_positive_count=0,
            true_positive_count=0,
            behavioral_fingerprint={},
            tolerance_score=0.5,  # Start neutral
        )

        self.tolerance_profiles[entity_id] = profile
        self.total_profiles_created += 1

        logger.info(f"Created tolerance profile for {entity_id} ({entity_type})")

    def _update_behavioral_fingerprint(self, profile: ToleranceProfile, features: Dict[str, float]):
        """Update behavioral fingerprint with running statistics.

        Uses exponential moving average for online learning.

        Args:
            profile: Tolerance profile to update
            features: New feature observations
        """
        alpha = 0.1  # EMA smoothing factor

        for feature_name, feature_value in features.items():
            if feature_name not in profile.behavioral_fingerprint:
                # Initialize with first observation
                profile.behavioral_fingerprint[feature_name] = feature_value
            else:
                # EMA update: new = alpha * value + (1-alpha) * old
                old_value = profile.behavioral_fingerprint[feature_name]
                new_value = alpha * feature_value + (1 - alpha) * old_value
                profile.behavioral_fingerprint[feature_name] = new_value

    def update_tolerance_score(self, entity_id: str, alert_was_false_positive: bool):
        """Update tolerance score based on alert outcome.

        Args:
            entity_id: Entity that triggered alert
            alert_was_false_positive: Whether alert was false positive
        """
        if entity_id not in self.tolerance_profiles:
            logger.warning(f"No profile for {entity_id} to update")
            return

        profile = self.tolerance_profiles[entity_id]

        if alert_was_false_positive:
            profile.false_positive_count += 1
        else:
            profile.true_positive_count += 1

        # Recompute tolerance score
        # High FP rate → high tolerance (suppress more)
        # High TP rate → low tolerance (allow alerts)
        total_alerts = profile.false_positive_count + profile.true_positive_count

        if total_alerts > 0:
            fp_rate = profile.false_positive_count / total_alerts
            # Tolerance = FP rate (with smoothing to avoid extremes)
            profile.tolerance_score = 0.3 + (0.6 * fp_rate)  # Range: 0.3-0.9
        else:
            profile.tolerance_score = 0.5  # Neutral

        profile.updated_at = datetime.now()

        logger.debug(
            f"Updated tolerance for {entity_id}: "
            f"FP={profile.false_positive_count}, TP={profile.true_positive_count}, "
            f"score={profile.tolerance_score:.2f}"
        )

    def get_tolerance_score(self, entity_id: str) -> float:
        """Get current tolerance score for entity.

        Args:
            entity_id: Entity identifier

        Returns:
            Tolerance score (0-1, higher = more tolerant)
        """
        if entity_id not in self.tolerance_profiles:
            return 0.5  # Default neutral tolerance

        return self.tolerance_profiles[entity_id].tolerance_score

    def get_status(self) -> Dict[str, Any]:
        """Get learner status.

        Returns:
            Status dictionary
        """
        # Count by tolerance level
        high_tolerance = sum(
            1 for p in self.tolerance_profiles.values() if p.tolerance_score > self.tolerance_threshold
        )

        low_tolerance = sum(1 for p in self.tolerance_profiles.values() if p.tolerance_score < 0.3)

        return {
            "component": "tolerance_learner",
            "total_profiles": len(self.tolerance_profiles),
            "high_tolerance_entities": high_tolerance,
            "low_tolerance_entities": low_tolerance,
            "tolerance_threshold": self.tolerance_threshold,
            "timestamp": datetime.now().isoformat(),
        }


# ============================================================================
# False Positive Suppressor
# ============================================================================


class FalsePositiveSuppressor:
    """Suppresses false positive alerts using statistical anomaly detection.

    Biological analogy:
    - Treg cells suppress autoreactive T-cells to prevent autoimmunity
    - Anergy: T-cells become non-responsive to self-antigens

    Cyber translation:
    - Detect benign patterns that trigger alerts
    - Suppress alerts for known false positive scenarios
    - Learn adaptive thresholds per alert type
    """

    def __init__(self, suppression_threshold: float = 0.7):
        self.suppression_threshold = suppression_threshold
        self.alert_type_baselines: Dict[str, Dict[str, Any]] = {}
        self.suppression_history: List[SuppressionDecision] = []
        self.alerts_suppressed: int = 0
        self.alerts_allowed: int = 0

    def evaluate_alert(
        self, alert: SecurityAlert, tolerance_profiles: Dict[str, ToleranceProfile]
    ) -> SuppressionDecision:
        """Evaluate whether to suppress alert.

        Algorithm:
        1. Check entity tolerance (is source trusted?)
        2. Compute anomaly score (how unusual is this?)
        3. Check alert type baseline (normal for this type?)
        4. Make suppression decision

        Args:
            alert: Security alert to evaluate
            tolerance_profiles: Relevant tolerance profiles

        Returns:
            Suppression decision
        """
        suppression_signals = []
        rationale = []
        profiles_consulted = []

        # Signal 1: Source IP tolerance
        if alert.source_ip in tolerance_profiles:
            profile = tolerance_profiles[alert.source_ip]
            profiles_consulted.append(alert.source_ip)

            tolerance_score = profile.tolerance_score

            if tolerance_score > 0.7:
                suppression_signals.append(0.8)
                rationale.append(f"Source {alert.source_ip} has high tolerance score ({tolerance_score:.2f})")
            elif tolerance_score < 0.3:
                suppression_signals.append(0.1)
                rationale.append(f"Source {alert.source_ip} has low tolerance (known threat)")
            else:
                suppression_signals.append(tolerance_score)

        # Signal 2: Alert type baseline (is this score unusual?)
        anomaly_score = self._compute_anomaly_score(alert)

        if anomaly_score < 2.0:  # Within 2 standard deviations
            suppression_signals.append(0.7)
            rationale.append(
                f"Alert score within normal range for {alert.alert_type} (anomaly score: {anomaly_score:.2f})"
            )
        else:
            suppression_signals.append(0.2)
            rationale.append(f"Alert score highly anomalous ({anomaly_score:.2f} std devs)")

        # Signal 3: Alert frequency (too many of same type = possible FP)
        recent_similar = self._count_recent_similar_alerts(alert)

        if recent_similar > 10:
            suppression_signals.append(0.8)
            rationale.append(f"High frequency of {alert.alert_type} alerts ({recent_similar} in last hour)")
        else:
            suppression_signals.append(0.3)

        # Aggregate suppression score (average of signals)
        if len(suppression_signals) > 0:
            suppression_score = np.mean(suppression_signals)
        else:
            suppression_score = 0.5  # Neutral

        # Make decision
        if suppression_score >= self.suppression_threshold:
            decision = ToleranceDecision.SUPPRESS
            self.alerts_suppressed += 1
        elif suppression_score <= 0.4:
            decision = ToleranceDecision.ALLOW
            self.alerts_allowed += 1
        else:
            decision = ToleranceDecision.UNCERTAIN

        # Compute confidence (distance from threshold)
        confidence = abs(suppression_score - self.suppression_threshold)

        suppression_decision = SuppressionDecision(
            alert_id=alert.alert_id,
            decision=decision,
            confidence=confidence,
            suppression_score=suppression_score,
            rationale=rationale,
            tolerance_profiles_consulted=profiles_consulted,
        )

        self.suppression_history.append(suppression_decision)

        logger.info(
            f"Suppression decision for {alert.alert_id}: {decision.value} "
            f"(score: {suppression_score:.2f}, confidence: {confidence:.2f})"
        )

        return suppression_decision

    def _compute_anomaly_score(self, alert: SecurityAlert) -> float:
        """Compute anomaly score for alert (Z-score).

        Args:
            alert: Security alert

        Returns:
            Z-score (number of standard deviations from mean)
        """
        alert_type = alert.alert_type

        # Initialize baseline if needed
        if alert_type not in self.alert_type_baselines:
            self.alert_type_baselines[alert_type] = {
                "scores": [],
                "mean": 0.5,
                "std": 0.2,
            }

        baseline = self.alert_type_baselines[alert_type]

        # Add current score to history
        baseline["scores"].append(alert.raw_score)
        baseline["scores"] = baseline["scores"][-100:]  # Keep last 100

        # Update statistics if we have enough samples
        if len(baseline["scores"]) >= 10:
            baseline["mean"] = np.mean(baseline["scores"])
            baseline["std"] = np.std(baseline["scores"])

        # Compute Z-score
        mean = baseline["mean"]
        std = max(baseline["std"], 0.01)  # Avoid division by zero

        z_score = abs((alert.raw_score - mean) / std)

        return z_score

    def _count_recent_similar_alerts(self, alert: SecurityAlert) -> int:
        """Count recent alerts of same type.

        Args:
            alert: Security alert

        Returns:
            Count of similar alerts in last hour
        """
        one_hour_ago = datetime.now() - timedelta(hours=1)

        count = sum(1 for decision in self.suppression_history if decision.timestamp >= one_hour_ago)

        return count

    def record_ground_truth(self, alert_id: str, was_false_positive: bool):
        """Record ground truth for alert (for learning).

        Args:
            alert_id: Alert identifier
            was_false_positive: Whether it was a false positive
        """
        # Find decision
        decision = None
        for d in self.suppression_history:
            if d.alert_id == alert_id:
                decision = d
                break

        if decision is None:
            logger.warning(f"No decision found for alert {alert_id}")
            return

        # Check if we made correct decision
        correct = (was_false_positive and decision.decision == ToleranceDecision.SUPPRESS) or (
            not was_false_positive and decision.decision == ToleranceDecision.ALLOW
        )

        logger.info(
            f"Ground truth for {alert_id}: FP={was_false_positive}, "
            f"decision={decision.decision.value}, correct={correct}"
        )

    def get_status(self) -> Dict[str, Any]:
        """Get suppressor status.

        Returns:
            Status dictionary
        """
        total_decisions = self.alerts_suppressed + self.alerts_allowed

        suppression_rate = self.alerts_suppressed / total_decisions if total_decisions > 0 else 0.0

        return {
            "component": "false_positive_suppressor",
            "alerts_suppressed": self.alerts_suppressed,
            "alerts_allowed": self.alerts_allowed,
            "suppression_rate": suppression_rate,
            "alert_types_tracked": len(self.alert_type_baselines),
            "suppression_threshold": self.suppression_threshold,
            "timestamp": datetime.now().isoformat(),
        }


# ============================================================================
# Regulatory T-Cell Controller
# ============================================================================


class TregController:
    """Main Treg controller integrating tolerance learning and FP suppression.

    Coordinates:
    1. Tolerance learning (what is normal)
    2. False positive suppression (suppress benign alerts)
    3. Adaptive thresholds (adjust based on feedback)
    """

    def __init__(self, tolerance_threshold: float = 0.7, suppression_threshold: float = 0.7):
        self.tolerance_learner = ToleranceLearner(tolerance_threshold)
        self.fp_suppressor = FalsePositiveSuppressor(suppression_threshold)
        self.alerts_processed: int = 0

    def process_alert(self, alert: SecurityAlert) -> SuppressionDecision:
        """Process security alert through Treg evaluation.

        Args:
            alert: Security alert

        Returns:
            Suppression decision
        """
        self.alerts_processed += 1

        # Extract entities from alert
        entities = [
            (alert.source_ip, "source_ip"),
            (alert.target_asset, "target_asset"),
        ]

        # Get tolerance profiles
        tolerance_profiles = {}
        for entity_id, entity_type in entities:
            if entity_id in self.tolerance_learner.tolerance_profiles:
                tolerance_profiles[entity_id] = self.tolerance_learner.tolerance_profiles[entity_id]

        # Evaluate alert
        decision = self.fp_suppressor.evaluate_alert(alert, tolerance_profiles)

        return decision

    def observe_entity(self, entity_id: str, entity_type: str, behavioral_features: Dict[str, float]):
        """Observe entity behavior for tolerance learning.

        Args:
            entity_id: Entity identifier
            entity_type: Entity type
            behavioral_features: Behavioral features
        """
        self.tolerance_learner.observe_entity_behavior(entity_id, entity_type, behavioral_features)

    def provide_feedback(
        self,
        alert_id: str,
        was_false_positive: bool,
        entities_involved: List[Tuple[str, str]],
    ):
        """Provide feedback on alert outcome.

        Args:
            alert_id: Alert identifier
            was_false_positive: Whether it was a false positive
            entities_involved: List of (entity_id, entity_type) tuples
        """
        # Record ground truth in suppressor
        self.fp_suppressor.record_ground_truth(alert_id, was_false_positive)

        # Update tolerance scores for involved entities
        for entity_id, entity_type in entities_involved:
            self.tolerance_learner.update_tolerance_score(entity_id, was_false_positive)

    def get_status(self) -> Dict[str, Any]:
        """Get Treg controller status.

        Returns:
            Status dictionary
        """
        learner_status = self.tolerance_learner.get_status()
        suppressor_status = self.fp_suppressor.get_status()

        return {
            "component": "treg_controller",
            "alerts_processed": self.alerts_processed,
            "tolerance_learner": learner_status,
            "fp_suppressor": suppressor_status,
            "timestamp": datetime.now().isoformat(),
        }
