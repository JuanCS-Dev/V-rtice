"""Base classes and interfaces for XAI (Explainable AI) module.

This module defines the abstract base class that all explainers must implement,
ensuring a consistent interface for explanation generation across the VÉRTICE platform.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# Configure logging
logger = logging.getLogger(__name__)


class ExplanationType(str, Enum):
    """Types of explanations supported."""

    LIME = "lime"
    SHAP = "shap"
    COUNTERFACTUAL = "counterfactual"
    FEATURE_IMPORTANCE = "feature_importance"
    ANCHORS = "anchors"  # For future implementation


class DetailLevel(str, Enum):
    """Level of detail in explanations."""

    SUMMARY = "summary"  # High-level summary (1-2 sentences)
    DETAILED = "detailed"  # Detailed explanation with top features
    TECHNICAL = "technical"  # Full technical details with all features


@dataclass
class FeatureImportance:
    """Feature importance information.

    Attributes:
        feature_name: Name of the feature
        importance: Importance score (can be positive or negative)
        value: Actual value of the feature in the instance
        description: Human-readable description of the feature
        contribution: Contribution to the final prediction
    """

    feature_name: str
    importance: float
    value: Any
    description: str
    contribution: float

    def __post_init__(self):
        """Validate feature importance."""
        if not self.feature_name:
            raise ValueError("feature_name is required")
        if not isinstance(self.importance, (int, float)):
            raise ValueError(f"importance must be a number, got {type(self.importance)}")


@dataclass
class ExplanationResult:
    """Result from an explanation generation.

    Attributes:
        explanation_id: Unique identifier for this explanation
        decision_id: ID of the decision being explained
        explanation_type: Type of explanation (lime, shap, etc.)
        detail_level: Level of detail
        summary: High-level summary of the explanation
        top_features: Top N most important features
        all_features: All features with importance scores
        confidence: Confidence in the explanation (0.0 to 1.0)
        counterfactual: Optional counterfactual scenario
        visualization_data: Data for visualization (SHAP waterfall, etc.)
        model_type: Type of model being explained
        latency_ms: Time taken to generate explanation
        metadata: Additional metadata
    """

    explanation_id: str
    decision_id: str
    explanation_type: ExplanationType
    detail_level: DetailLevel
    summary: str
    top_features: list[FeatureImportance]
    all_features: list[FeatureImportance]
    confidence: float
    counterfactual: str | None = None
    visualization_data: dict[str, Any] | None = None
    model_type: str = "unknown"
    latency_ms: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate explanation result."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")
        if not self.summary:
            raise ValueError("summary is required and cannot be empty")
        if not self.top_features:
            raise ValueError("top_features must contain at least one feature")
        if not self.decision_id:
            raise ValueError("decision_id is required")


class ExplainerBase(ABC):
    """Abstract base class for all explainers.

    All explainers (LIME, SHAP, Counterfactual) must inherit from this class
    and implement the explain() method.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize the explainer.

        Args:
            config: Configuration dictionary for the explainer
        """
        self.config = config or {}
        self.name = self.__class__.__name__.lower()
        logger.info(f"Initialized {self.__class__.__name__} with config: {self.config}")

    @abstractmethod
    async def explain(
        self,
        model: Any,
        instance: dict[str, Any],
        prediction: Any,
        detail_level: DetailLevel = DetailLevel.DETAILED,
    ) -> ExplanationResult:
        """Generate explanation for a model's prediction.

        Args:
            model: The model being explained (can be sklearn, torch, tf, etc.)
            instance: The input instance being explained
            prediction: The model's prediction for this instance
            detail_level: Level of detail for the explanation

        Returns:
            ExplanationResult with feature importances and summary
        """
        pass

    @abstractmethod
    def get_supported_models(self) -> list[str]:
        """Get list of supported model types.

        Returns:
            List of model type strings (e.g., ['sklearn', 'pytorch', 'tensorflow'])
        """
        pass

    def get_name(self) -> str:
        """Get the explainer name.

        Returns:
            Name of the explainer
        """
        return self.name

    def get_version(self) -> str:
        """Get the explainer version.

        Returns:
            Version string
        """
        return self.config.get("version", "1.0.0")

    def validate_instance(self, instance: dict[str, Any]) -> bool:
        """Validate that instance has required fields.

        Args:
            instance: Instance to validate

        Returns:
            True if valid, raises ValueError otherwise
        """
        if not instance:
            raise ValueError("instance cannot be empty")
        if not isinstance(instance, dict):
            raise ValueError(f"instance must be a dict, got {type(instance)}")
        return True

    def format_feature_description(self, feature_name: str, value: Any) -> str:
        """Format a human-readable feature description.

        Args:
            feature_name: Name of the feature
            value: Value of the feature

        Returns:
            Human-readable description
        """
        # Map technical feature names to human-readable descriptions
        feature_descriptions = {
            "src_ip": f"Source IP address: {value}",
            "dst_ip": f"Destination IP address: {value}",
            "src_port": f"Source port: {value}",
            "dst_port": f"Destination port: {value}",
            "protocol": f"Protocol: {value}",
            "packet_size": f"Packet size: {value} bytes",
            "threat_score": f"Threat score: {value:.2f}",
            "anomaly_score": f"Anomaly score: {value:.2f}",
            "signature_matches": f"Signature matches: {value}",
            "behavioral_score": f"Behavioral score: {value:.2f}",
            "reputation_score": f"Reputation score: {value:.2f}",
            "entropy": f"Data entropy: {value:.3f}",
            "time_of_day": f"Time of day: {value}",
            "request_rate": f"Request rate: {value} req/s",
            "payload_size": f"Payload size: {value} bytes",
            "http_method": f"HTTP method: {value}",
            "user_agent": f"User agent: {value}",
            "emotional_intensity": f"Emotional intensity: {value:.2f}",
            "propaganda_score": f"Propaganda score: {value:.2f}",
            "manipulation_indicators": f"Manipulation indicators: {value}",
            "credibility_score": f"Source credibility: {value:.2f}",
        }

        return feature_descriptions.get(feature_name, f"{feature_name.replace('_', ' ').title()}: {value}")


class ExplanationCache:
    """Simple in-memory cache for explanations.

    Caches explanations for identical decisions to reduce latency.
    """

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        """Initialize the cache.

        Args:
            max_size: Maximum number of cached explanations
            ttl_seconds: Time-to-live for cached explanations in seconds
        """
        self._cache: dict[str, tuple[ExplanationResult, float]] = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        logger.info(f"ExplanationCache initialized: max_size={max_size}, ttl={ttl_seconds}s")

    def get(self, cache_key: str) -> ExplanationResult | None:
        """Get a cached explanation.

        Args:
            cache_key: Unique key for the explanation

        Returns:
            Cached result or None if not found/expired
        """
        import time

        if cache_key in self._cache:
            result, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self.ttl_seconds:
                logger.debug(f"Cache HIT for key: {cache_key}")
                return result
            # Expired, remove it
            logger.debug(f"Cache EXPIRED for key: {cache_key}")
            del self._cache[cache_key]

        logger.debug(f"Cache MISS for key: {cache_key}")
        return None

    def set(self, cache_key: str, result: ExplanationResult):
        """Cache an explanation.

        Args:
            cache_key: Unique key for the explanation
            result: Result to cache
        """
        import time

        # Evict oldest if at max size
        if len(self._cache) >= self.max_size:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]
            logger.debug(f"Cache EVICTED oldest key: {oldest_key}")

        self._cache[cache_key] = (result, time.time())
        logger.debug(f"Cache SET for key: {cache_key}")

    def generate_key(
        self,
        decision_id: str,
        explanation_type: ExplanationType,
        detail_level: DetailLevel,
    ) -> str:
        """Generate a cache key.

        Args:
            decision_id: ID of the decision
            explanation_type: Type of explanation
            detail_level: Detail level

        Returns:
            Unique cache key string
        """
        import hashlib

        key_str = f"{decision_id}:{explanation_type.value}:{detail_level.value}"
        return hashlib.sha256(key_str.encode()).hexdigest()

    def clear(self):
        """Clear all cached explanations."""
        self._cache.clear()
        logger.info("ExplanationCache cleared")

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds,
            "utilization": len(self._cache) / self.max_size if self.max_size > 0 else 0,
        }


class ExplanationException(Exception):
    """Base exception for explanation errors."""

    pass


class ModelNotSupportedException(ExplanationException):
    """Exception raised when a model type is not supported."""

    def __init__(self, model_type: str, supported_types: list[str]):
        self.model_type = model_type
        self.supported_types = supported_types
        super().__init__(f"Model type '{model_type}' is not supported. Supported types: {', '.join(supported_types)}")


class ExplanationTimeoutException(ExplanationException):
    """Exception raised when explanation generation times out."""

    def __init__(self, timeout_seconds: int):
        self.timeout_seconds = timeout_seconds
        super().__init__(f"Explanation generation exceeded timeout of {timeout_seconds} seconds")
