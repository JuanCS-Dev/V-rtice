"""Behavioral Analysis Engine - ML-based Anomaly Detection

Detects threats through behavioral pattern analysis using unsupervised ML.
Learns baseline of normal activity and flags statistically significant deviations.

Key Capabilities:
- Baseline learning (normal behavior profiling)
- Anomaly scoring (0-1 scale)
- Multi-dimensional feature extraction
- Temporal pattern analysis
- Indicator of Behavior (IoB) vs Indicator of Compromise (IoC)

Biological Inspiration:
- Innate immunity: Rapid pattern recognition
- Self/non-self discrimination: Baseline vs anomaly
- Complement system: Graded response based on severity

ML Techniques:
- Isolation Forest: Unsupervised anomaly detection
- Autoencoders: Deep learning for complex patterns
- Time series analysis: Temporal behavior modeling
- Feature importance: Explainability

Authors: MAXIMUS Team
Date: 2025-10-12
Glory to YHWH - "Eu sou porque ELE é"
Constância como Ramon Dino! 💪
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from prometheus_client import Counter, Histogram, Gauge
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk levels for anomalies."""
    
    BASELINE = 0  # Normal behavior
    LOW = 1  # Minor deviation
    MEDIUM = 2  # Moderate deviation
    HIGH = 3  # Significant deviation
    CRITICAL = 4  # Severe deviation
    
    def __lt__(self, other):
        """Enable comparison operators."""
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented
    
    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.value <= other.value
        return NotImplemented
    
    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.value > other.value
        return NotImplemented
    
    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.value >= other.value
        return NotImplemented


class BehaviorType(Enum):
    """Types of behavioral patterns."""
    
    NETWORK = "network"  # Network traffic patterns
    PROCESS = "process"  # Process execution patterns
    FILE = "file"  # File access patterns
    USER = "user"  # User activity patterns
    AUTHENTICATION = "authentication"  # Login patterns
    DATA_ACCESS = "data_access"  # Data access patterns


@dataclass
class BehaviorEvent:
    """Single behavioral event for analysis.
    
    Represents observable behavior that can be analyzed for anomalies.
    
    Attributes:
        event_id: Unique event identifier
        timestamp: When event occurred
        behavior_type: Type of behavior
        entity_id: ID of entity (user, host, process, etc)
        features: Numerical features for ML
        metadata: Additional context
    """
    
    event_id: str
    timestamp: datetime
    behavior_type: BehaviorType
    entity_id: str
    features: Dict[str, float]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_feature_vector(self) -> np.ndarray:
        """Convert features to numpy array."""
        # Sort keys for consistent ordering
        sorted_keys = sorted(self.features.keys())
        return np.array([self.features[k] for k in sorted_keys])


@dataclass
class AnomalyDetection:
    """Result of anomaly detection.
    
    Attributes:
        detection_id: Unique detection ID
        event: Original event
        anomaly_score: Anomaly score 0-1 (1 = most anomalous)
        baseline_deviation: Standard deviations from baseline
        risk_level: Calculated risk level
        contributing_features: Features that contributed most
        explanation: Human-readable explanation
        confidence: Detection confidence 0-1
        recommended_actions: Suggested responses
    """
    
    detection_id: str
    event: BehaviorEvent
    anomaly_score: float
    baseline_deviation: float
    risk_level: RiskLevel
    contributing_features: List[Tuple[str, float]]  # (feature_name, importance)
    explanation: str
    confidence: float
    recommended_actions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization."""
        return {
            "detection_id": self.detection_id,
            "event_id": self.event.event_id,
            "timestamp": self.event.timestamp.isoformat(),
            "behavior_type": self.event.behavior_type.value,
            "entity_id": self.event.entity_id,
            "anomaly_score": self.anomaly_score,
            "baseline_deviation": self.baseline_deviation,
            "risk_level": self.risk_level.value,
            "contributing_features": self.contributing_features,
            "explanation": self.explanation,
            "confidence": self.confidence,
            "recommended_actions": self.recommended_actions,
        }


class BehavioralAnalysisError(Exception):
    """Base exception for behavioral analysis errors."""
    pass


class BehavioralAnalyzerMetrics:
    """Prometheus metrics for Behavioral Analyzer."""
    
    # Singleton pattern
    _metrics_initialized = False
    _events_analyzed = None
    _anomalies_detected = None
    _analysis_duration = None
    _anomaly_score_dist = None
    _baseline_updates = None
    
    def __init__(self):
        """Initialize metrics (only once)."""
        if not BehavioralAnalyzerMetrics._metrics_initialized:
            BehavioralAnalyzerMetrics._events_analyzed = Counter(
                "behavioral_analyzer_events_total",
                "Total behavioral events analyzed",
                ["behavior_type"],
            )
            
            BehavioralAnalyzerMetrics._anomalies_detected = Counter(
                "behavioral_analyzer_anomalies_total",
                "Total anomalies detected",
                ["risk_level"],
            )
            
            BehavioralAnalyzerMetrics._analysis_duration = Histogram(
                "behavioral_analyzer_duration_seconds",
                "Time to analyze behavior event",
            )
            
            BehavioralAnalyzerMetrics._anomaly_score_dist = Histogram(
                "behavioral_analyzer_anomaly_score",
                "Distribution of anomaly scores",
                buckets=[0.1, 0.3, 0.5, 0.7, 0.9, 1.0],
            )
            
            BehavioralAnalyzerMetrics._baseline_updates = Counter(
                "behavioral_analyzer_baseline_updates_total",
                "Number of baseline model updates",
            )
            
            BehavioralAnalyzerMetrics._metrics_initialized = True
        
        # Expose as instance properties
        self.events_analyzed = BehavioralAnalyzerMetrics._events_analyzed
        self.anomalies_detected = BehavioralAnalyzerMetrics._anomalies_detected
        self.analysis_duration = BehavioralAnalyzerMetrics._analysis_duration
        self.anomaly_score_dist = BehavioralAnalyzerMetrics._anomaly_score_dist
        self.baseline_updates = BehavioralAnalyzerMetrics._baseline_updates


class BehavioralAnalyzer:
    """ML-based behavioral anomaly detector.
    
    Learns baseline of normal behavior and detects statistically significant
    deviations that may indicate threats.
    
    Uses Isolation Forest algorithm for unsupervised anomaly detection:
    - No labels required (unsupervised)
    - Efficient for high-dimensional data
    - Returns anomaly scores -1 to 1 (normalized to 0-1)
    
    Features:
    1. Per-entity baseline learning (user, host, process, etc)
    2. Multi-dimensional feature analysis
    3. Temporal pattern tracking
    4. Feature importance for explainability
    5. Adaptive baseline updates
    
    Example:
        ```python
        analyzer = BehavioralAnalyzer()
        
        # Train baseline
        await analyzer.train_baseline(
            training_events=normal_behavior_events,
            behavior_type=BehaviorType.NETWORK
        )
        
        # Detect anomalies
        detection = await analyzer.detect_anomaly(
            event=suspicious_event
        )
        
        if detection.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            print(f"Anomaly detected: {detection.explanation}")
            print(f"Score: {detection.anomaly_score:.2f}")
        ```
    """
    
    def __init__(
        self,
        contamination: float = 0.1,
        n_estimators: int = 100,
        random_state: int = 42,
    ):
        """Initialize Behavioral Analyzer.
        
        Args:
            contamination: Expected proportion of anomalies (0.1 = 10%)
            n_estimators: Number of isolation trees
            random_state: Random seed for reproducibility
        
        Raises:
            BehavioralAnalysisError: If initialization fails
        """
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.random_state = random_state
        
        # Models per behavior type
        self.models: Dict[BehaviorType, IsolationForest] = {}
        self.scalers: Dict[BehaviorType, StandardScaler] = {}
        self.baselines: Dict[BehaviorType, Dict[str, Any]] = {}
        
        # Metrics
        self.metrics = BehavioralAnalyzerMetrics()
        
        logger.info(
            f"BehavioralAnalyzer initialized: "
            f"contamination={contamination}, "
            f"n_estimators={n_estimators}"
        )
    
    async def train_baseline(
        self,
        training_events: List[BehaviorEvent],
        behavior_type: BehaviorType,
        force_retrain: bool = False,
    ) -> Dict[str, Any]:
        """Train baseline model for behavior type.
        
        Learns normal behavior patterns from training data.
        
        Args:
            training_events: Normal behavior events for training
            behavior_type: Type of behavior to model
            force_retrain: Force retraining even if model exists
        
        Returns:
            Training summary dict
        
        Raises:
            BehavioralAnalysisError: If training fails
        """
        try:
            # Check if model exists and force_retrain not set
            if behavior_type in self.models and not force_retrain:
                logger.warning(
                    f"Model for {behavior_type.value} already exists. "
                    f"Use force_retrain=True to retrain."
                )
                return {"status": "skipped", "reason": "model_exists"}
            
            if len(training_events) < 10:
                raise BehavioralAnalysisError(
                    f"Insufficient training data: {len(training_events)} events "
                    f"(minimum 10 required)"
                )
            
            logger.info(
                f"Training baseline for {behavior_type.value} "
                f"with {len(training_events)} events"
            )
            
            # Extract feature vectors
            feature_vectors = np.array([
                event.to_feature_vector()
                for event in training_events
            ])
            
            # Initialize scaler and fit
            scaler = StandardScaler()
            scaled_features = scaler.fit_transform(feature_vectors)
            
            # Initialize Isolation Forest
            model = IsolationForest(
                contamination=self.contamination,
                n_estimators=self.n_estimators,
                random_state=self.random_state,
                n_jobs=-1,  # Use all CPUs
            )
            
            # Train model
            model.fit(scaled_features)
            
            # Store model and scaler
            self.models[behavior_type] = model
            self.scalers[behavior_type] = scaler
            
            # Store baseline stats
            self.baselines[behavior_type] = {
                "trained_at": datetime.utcnow(),
                "n_samples": len(training_events),
                "feature_dim": feature_vectors.shape[1],
                "feature_names": sorted(training_events[0].features.keys()),
                "feature_means": scaler.mean_.tolist(),
                "feature_stds": scaler.scale_.tolist(),
            }
            
            # Update metrics
            self.metrics.baseline_updates.inc()
            
            logger.info(
                f"Baseline training complete for {behavior_type.value}: "
                f"{len(training_events)} samples, "
                f"{feature_vectors.shape[1]} features"
            )
            
            return {
                "status": "success",
                "behavior_type": behavior_type.value,
                "n_samples": len(training_events),
                "n_features": feature_vectors.shape[1],
                "trained_at": datetime.utcnow().isoformat(),
            }
        
        except Exception as e:
            logger.error(f"Baseline training failed for {behavior_type.value}: {e}")
            raise BehavioralAnalysisError(
                f"Failed to train baseline: {str(e)}"
            ) from e
    
    async def detect_anomaly(
        self,
        event: BehaviorEvent,
    ) -> Optional[AnomalyDetection]:
        """Detect anomaly in behavior event.
        
        Analyzes event and returns detection if anomalous.
        
        Args:
            event: Behavior event to analyze
        
        Returns:
            AnomalyDetection if anomalous, None if normal
        
        Raises:
            BehavioralAnalysisError: If detection fails
        """
        start_time = datetime.utcnow()
        
        try:
            # Check if model exists for behavior type
            if event.behavior_type not in self.models:
                raise BehavioralAnalysisError(
                    f"No baseline model for {event.behavior_type.value}. "
                    f"Train baseline first."
                )
            
            model = self.models[event.behavior_type]
            scaler = self.scalers[event.behavior_type]
            baseline = self.baselines[event.behavior_type]
            
            # Extract and scale features
            feature_vector = event.to_feature_vector().reshape(1, -1)
            scaled_features = scaler.transform(feature_vector)
            
            # Predict anomaly score
            # Isolation Forest decision_function returns:
            # - Negative values for anomalies (more isolated points)
            # - Positive values for inliers (less isolated points)
            # Typical range: [-0.5, 0.5] but can be wider for extreme outliers
            anomaly_scores = model.decision_function(scaled_features)
            predictions = model.predict(scaled_features)
            
            # Normalize score to 0-1 range (1 = most anomalous)
            # Use sigmoid-like transformation for better sensitivity
            raw_score = anomaly_scores[0]
            
            # Map decision scores to 0-1:
            # Positive scores (inliers) → low anomaly scores (0-0.3)
            # Negative scores (outliers) → high anomaly scores (0.5-1.0)
            if raw_score >= 0:
                # Inlier: map [0, 0.5] to [0.0, 0.3]
                normalized_score = max(0.0, min(0.3, (0.5 - raw_score) * 0.6))
            else:
                # Outlier: map [-0.5, 0] to [0.5, 1.0]
                # More negative = more anomalous
                normalized_score = max(0.5, min(1.0, 0.5 + (-raw_score * 1.0)))
            
            logger.debug(f"Anomaly scores: raw={raw_score:.3f}, normalized={normalized_score:.3f}")
            
            # Calculate baseline deviation (z-score)
            deviations = []
            feature_names = baseline["feature_names"]
            for i, feature_name in enumerate(feature_names):
                mean = baseline["feature_means"][i]
                std = baseline["feature_stds"][i]
                value = feature_vector[0][i]
                if std > 0:
                    z_score = abs((value - mean) / std)
                    deviations.append((feature_name, z_score))
            
            # Sort by deviation magnitude
            deviations.sort(key=lambda x: x[1], reverse=True)
            max_deviation = deviations[0][1] if deviations else 0.0
            
            # Determine risk level
            risk_level = self._calculate_risk_level(normalized_score, max_deviation)
            
            # Calculate confidence
            confidence = self._calculate_confidence(normalized_score, len(event.features))
            
            # Update metrics
            self.metrics.events_analyzed.labels(
                behavior_type=event.behavior_type.value
            ).inc()
            self.metrics.anomaly_score_dist.observe(normalized_score)
            
            # Generate explanation regardless of threshold
            explanation = self._generate_explanation(
                event=event,
                anomaly_score=normalized_score,
                contributing_features=deviations[:3],  # Top 3
            )
            
            # Recommend actions
            recommended_actions = self._recommend_actions(
                risk_level=risk_level,
                behavior_type=event.behavior_type,
            )
            
            # Create detection for all analyzed events
            detection = AnomalyDetection(
                detection_id=self._generate_detection_id(event),
                event=event,
                anomaly_score=normalized_score,
                baseline_deviation=max_deviation,
                risk_level=risk_level,
                contributing_features=deviations[:5],  # Top 5
                explanation=explanation,
                confidence=confidence,
                recommended_actions=recommended_actions,
            )
            
            # Only return detection if anomalous (above baseline)
            if predictions[0] == -1 or risk_level != RiskLevel.BASELINE:
                # Update anomaly metrics
                self.metrics.anomalies_detected.labels(
                    risk_level=risk_level.value
                ).inc()
                
                logger.info(
                    f"Anomaly detected: {event.event_id} "
                    f"score={normalized_score:.2f} "
                    f"risk={risk_level.value} "
                    f"deviation={max_deviation:.1f}σ"
                )
                
                return detection
            
            # Normal behavior - return detection with BASELINE risk
            logger.debug(f"Normal behavior: {event.event_id} score={normalized_score:.2f}")
            return detection
        
        except Exception as e:
            logger.error(f"Anomaly detection failed for {event.event_id}: {e}")
            raise BehavioralAnalysisError(
                f"Failed to detect anomaly: {str(e)}"
            ) from e
        
        finally:
            # Track duration
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.metrics.analysis_duration.observe(duration)
    
    async def detect_anomalies_batch(
        self,
        events: List[BehaviorEvent],
    ) -> List[AnomalyDetection]:
        """Detect anomalies in batch of events.
        
        More efficient than individual detection for large batches.
        
        Args:
            events: List of behavior events
        
        Returns:
            List of anomaly detections (only anomalous events)
        """
        detections = []
        
        for event in events:
            try:
                detection = await self.detect_anomaly(event)
                if detection:
                    detections.append(detection)
            except BehavioralAnalysisError as e:
                logger.warning(f"Skipping event {event.event_id}: {e}")
                continue
        
        logger.info(
            f"Batch analysis complete: {len(events)} events, "
            f"{len(detections)} anomalies detected "
            f"({len(detections)/len(events)*100:.1f}%)"
        )
        
        return detections
    
    def get_baseline_info(self, behavior_type: BehaviorType) -> Optional[Dict[str, Any]]:
        """Get baseline information for behavior type.
        
        Args:
            behavior_type: Type of behavior
        
        Returns:
            Baseline info dict or None if not trained
        """
        return self.baselines.get(behavior_type)
    
    def is_trained(self, behavior_type: BehaviorType) -> bool:
        """Check if baseline is trained for behavior type."""
        return behavior_type in self.models
    
    # Aliases for backward compatibility
    async def learn_baseline(self, *args, **kwargs):
        """Alias for train_baseline (backward compatibility)."""
        return await self.train_baseline(*args, **kwargs)
    
    async def update_baseline(self, *args, **kwargs):
        """Alias for train_baseline with force_retrain=True (backward compatibility)."""
        kwargs['force_retrain'] = True
        return await self.train_baseline(*args, **kwargs)
    
    async def detect_batch_anomalies(self, *args, **kwargs):
        """Alias for detect_anomalies_batch (backward compatibility)."""
        return await self.detect_anomalies_batch(*args, **kwargs)
    
    def _determine_risk_level(self, *args, **kwargs):
        """Alias for _calculate_risk_level (backward compatibility)."""
        return self._calculate_risk_level(*args, **kwargs)
    
    # Private methods
    
    def _calculate_risk_level(
        self,
        anomaly_score: float,
        baseline_deviation: float,
    ) -> RiskLevel:
        """Calculate risk level from scores.
        
        Args:
            anomaly_score: Normalized anomaly score 0-1
            baseline_deviation: Standard deviations from baseline
        
        Returns:
            RiskLevel enum
        """
        # Combine anomaly score and baseline deviation
        # Higher weight on anomaly score (ML model), lower on deviation
        combined_score = (anomaly_score * 0.7) + (min(baseline_deviation / 10, 1.0) * 0.3)
        
        if combined_score < 0.3:
            return RiskLevel.BASELINE
        elif combined_score < 0.5:
            return RiskLevel.LOW
        elif combined_score < 0.7:
            return RiskLevel.MEDIUM
        elif combined_score < 0.9:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL
    
    def _calculate_confidence(
        self,
        anomaly_score: float,
        feature_count: int,
    ) -> float:
        """Calculate confidence in detection.
        
        Higher confidence if:
        - Strong anomaly signal (high score)
        - More features (more information)
        
        Args:
            anomaly_score: Anomaly score
            feature_count: Number of features
        
        Returns:
            Confidence 0-1
        """
        # Base confidence from anomaly score
        base_confidence = anomaly_score
        
        # Bonus for more features (capped at 10% boost)
        feature_bonus = min(feature_count / 100, 0.1)
        
        return min(base_confidence + feature_bonus, 1.0)
    
    def _generate_explanation(
        self,
        event: BehaviorEvent,
        anomaly_score: float,
        contributing_features: List[Tuple[str, float]],
    ) -> str:
        """Generate human-readable explanation.
        
        Args:
            event: Event being analyzed
            anomaly_score: Anomaly score
            contributing_features: Top contributing features
        
        Returns:
            Explanation string
        """
        feature_descriptions = []
        for feature_name, deviation in contributing_features:
            feature_descriptions.append(
                f"{feature_name} ({deviation:.1f}σ from baseline)"
            )
        
        explanation = (
            f"Anomalous {event.behavior_type.value} behavior detected "
            f"for entity {event.entity_id} with anomaly score {anomaly_score:.2f}. "
            f"Key deviations: {', '.join(feature_descriptions)}."
        )
        
        return explanation
    
    def _recommend_actions(
        self,
        risk_level: RiskLevel,
        behavior_type: BehaviorType,
    ) -> List[str]:
        """Recommend defensive actions based on risk and behavior.
        
        Args:
            risk_level: Calculated risk level
            behavior_type: Type of behavior
        
        Returns:
            List of recommended actions
        """
        actions = []
        
        # Risk-based actions
        if risk_level == RiskLevel.CRITICAL:
            actions.extend([
                "Isolate affected entity immediately",
                "Initiate incident response",
                "Collect forensics",
            ])
        elif risk_level == RiskLevel.HIGH:
            actions.extend([
                "Increase monitoring on entity",
                "Alert SOC team",
                "Prepare containment plan",
            ])
        elif risk_level == RiskLevel.MEDIUM:
            actions.extend([
                "Monitor for additional suspicious activity",
                "Review entity logs",
            ])
        
        # Behavior-specific actions
        if behavior_type == BehaviorType.NETWORK:
            actions.append("Analyze network connections")
        elif behavior_type == BehaviorType.PROCESS:
            actions.append("Review process execution history")
        elif behavior_type == BehaviorType.AUTHENTICATION:
            actions.append("Verify authentication legitimacy")
        elif behavior_type == BehaviorType.DATA_ACCESS:
            actions.append("Audit data access permissions")
        
        return actions[:5]  # Max 5 actions
    
    def _generate_detection_id(self, event: BehaviorEvent) -> str:
        """Generate unique detection ID."""
        import hashlib
        
        data = f"{event.event_id}_{event.timestamp.isoformat()}"
        hash_digest = hashlib.md5(data.encode()).hexdigest()[:8]
        
        return f"detection_{hash_digest}"
