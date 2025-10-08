"""Explanation Engine - Unified interface for XAI in VÉRTICE.

This module provides the main entry point for all explainability functionality,
orchestrating LIME, SHAP, counterfactual generation, and feature tracking.

Key Features:
    - Unified API for all explanation types
    - Automatic explainer selection based on model type
    - Caching for performance
    - Feature importance tracking
    - Drift detection
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any

from .base import (
    DetailLevel,
    ExplanationCache,
    ExplanationException,
    ExplanationResult,
    ExplanationTimeoutException,
    ExplanationType,
)
from .counterfactual import CounterfactualGenerator
from .feature_tracker import FeatureImportanceTracker
from .lime_cybersec import CyberSecLIME
from .shap_cybersec import CyberSecSHAP

logger = logging.getLogger(__name__)


@dataclass
class EngineConfig:
    """Configuration for Explanation Engine.

    Attributes:
        enable_cache: Whether to enable explanation caching
        cache_ttl_seconds: Cache TTL in seconds
        enable_tracking: Whether to track feature importances
        default_explanation_type: Default explanation type
        timeout_seconds: Timeout for explanation generation
        auto_select_explainer: Auto-select best explainer for model
    """

    enable_cache: bool = True
    cache_ttl_seconds: int = 3600
    enable_tracking: bool = True
    default_explanation_type: ExplanationType = ExplanationType.LIME
    timeout_seconds: int = 30
    auto_select_explainer: bool = True


class ExplanationEngine:
    """Unified explanation engine for VÉRTICE platform.

    This is the main entry point for all XAI functionality, providing
    a simple interface for generating explanations across different models.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize ExplanationEngine.

        Args:
            config: Configuration dictionary
        """
        config = config or {}

        # Engine configuration
        self.config = EngineConfig(
            enable_cache=config.get("enable_cache", True),
            cache_ttl_seconds=config.get("cache_ttl_seconds", 3600),
            enable_tracking=config.get("enable_tracking", True),
            default_explanation_type=ExplanationType(config.get("default_explanation_type", "lime")),
            timeout_seconds=config.get("timeout_seconds", 30),
            auto_select_explainer=config.get("auto_select_explainer", True),
        )

        # Initialize explainers
        logger.info("Initializing XAI explainers...")

        self.lime_explainer = CyberSecLIME(config.get("lime", {}))
        self.shap_explainer = CyberSecSHAP(config.get("shap", {}))
        self.counterfactual_generator = CounterfactualGenerator(config.get("counterfactual", {}))

        # Cache and tracking
        self.cache = (
            ExplanationCache(max_size=config.get("cache_max_size", 1000), ttl_seconds=self.config.cache_ttl_seconds)
            if self.config.enable_cache
            else None
        )

        self.tracker = (
            FeatureImportanceTracker(max_history=config.get("tracker_max_history", 10000))
            if self.config.enable_tracking
            else None
        )

        # Statistics
        self.total_explanations_generated: int = 0
        self.cache_hits: int = 0
        self.cache_misses: int = 0

        logger.info("ExplanationEngine initialized successfully")

    async def explain(
        self,
        model: Any,
        instance: dict[str, Any],
        prediction: Any,
        explanation_type: ExplanationType | None = None,
        detail_level: DetailLevel = DetailLevel.DETAILED,
        use_cache: bool = True,
    ) -> ExplanationResult:
        """Generate explanation for a model's prediction.

        This is the main entry point for generating explanations.

        Args:
            model: The model to explain
            instance: Input instance as dictionary
            prediction: Model's prediction
            explanation_type: Type of explanation (auto-selects if None)
            detail_level: Level of detail
            use_cache: Whether to use cache

        Returns:
            ExplanationResult with explanation

        Raises:
            ExplanationException: If explanation generation fails
            ExplanationTimeoutException: If generation times out
        """
        explain_start = time.time()

        try:
            # Auto-select explanation type if not specified
            if explanation_type is None:
                explanation_type = self._auto_select_explainer(model)
                logger.debug(f"Auto-selected explainer: {explanation_type.value}")

            # Check cache first
            if use_cache and self.cache:
                decision_id = instance.get("decision_id", "")
                cache_key = self.cache.generate_key(decision_id, explanation_type, detail_level)

                cached_result = self.cache.get(cache_key)

                if cached_result:
                    self.cache_hits += 1
                    logger.debug(f"Cache HIT for {explanation_type.value}")
                    return cached_result

                self.cache_misses += 1

            # Generate explanation with timeout
            try:
                result = await asyncio.wait_for(
                    self._generate_explanation(model, instance, prediction, explanation_type, detail_level),
                    timeout=self.config.timeout_seconds,
                )
            except TimeoutError:
                raise ExplanationTimeoutException(self.config.timeout_seconds)

            # Cache result
            if use_cache and self.cache:
                self.cache.set(cache_key, result)

            # Track features
            if self.tracker:
                self.tracker.track_explanation(result.all_features)

            # Update statistics
            self.total_explanations_generated += 1

            latency = int((time.time() - explain_start) * 1000)
            logger.info(
                f"Explanation generated: {explanation_type.value}, "
                f"latency={latency}ms, confidence={result.confidence:.2f}"
            )

            return result

        except Exception as e:
            logger.error(f"Explanation generation failed: {e}", exc_info=True)
            raise ExplanationException(f"Failed to generate explanation: {str(e)}")

    async def explain_multiple(
        self,
        model: Any,
        instance: dict[str, Any],
        prediction: Any,
        explanation_types: list[ExplanationType],
        detail_level: DetailLevel = DetailLevel.DETAILED,
    ) -> dict[ExplanationType, ExplanationResult]:
        """Generate multiple explanation types for the same instance.

        Args:
            model: The model
            instance: Input instance
            prediction: Model prediction
            explanation_types: List of explanation types to generate
            detail_level: Detail level

        Returns:
            Dictionary mapping explanation types to results
        """
        logger.info(f"Generating {len(explanation_types)} explanations in parallel")

        # Generate all explanations in parallel
        tasks = []
        for exp_type in explanation_types:
            task = self.explain(
                model=model,
                instance=instance,
                prediction=prediction,
                explanation_type=exp_type,
                detail_level=detail_level,
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Build results dict
        results_dict = {}
        for exp_type, result in zip(explanation_types, results, strict=False):
            if isinstance(result, Exception):
                logger.error(f"Failed to generate {exp_type.value}: {result}")
            else:
                results_dict[exp_type] = result

        return results_dict

    async def _generate_explanation(
        self,
        model: Any,
        instance: dict[str, Any],
        prediction: Any,
        explanation_type: ExplanationType,
        detail_level: DetailLevel,
    ) -> ExplanationResult:
        """Generate explanation using specified explainer.

        Args:
            model: The model
            instance: Input instance
            prediction: Prediction
            explanation_type: Explanation type
            detail_level: Detail level

        Returns:
            ExplanationResult
        """
        if explanation_type == ExplanationType.LIME:
            return await self.lime_explainer.explain(model, instance, prediction, detail_level)

        if explanation_type == ExplanationType.SHAP:
            return await self.shap_explainer.explain(model, instance, prediction, detail_level)

        if explanation_type == ExplanationType.COUNTERFACTUAL:
            return await self.counterfactual_generator.explain(model, instance, prediction, detail_level)

        if explanation_type == ExplanationType.FEATURE_IMPORTANCE:
            # Use LIME for feature importance (fast and model-agnostic)
            return await self.lime_explainer.explain(model, instance, prediction, detail_level)

        raise ValueError(f"Unsupported explanation type: {explanation_type}")

    def _auto_select_explainer(self, model: Any) -> ExplanationType:
        """Auto-select best explainer based on model type.

        Args:
            model: The model

        Returns:
            Selected ExplanationType
        """
        if not self.config.auto_select_explainer:
            return self.config.default_explanation_type

        model_class = type(model).__name__.lower()
        model_module = type(model).__module__.lower() if hasattr(type(model), "__module__") else ""

        # Tree-based models → SHAP (TreeSHAP is fast and accurate)
        if any(
            keyword in model_module + model_class for keyword in ["xgb", "lightgbm", "randomforest", "gradientboosting"]
        ) or any(keyword in model_class for keyword in ["linear", "logistic", "svm"]):
            return ExplanationType.SHAP

        # Neural networks → LIME (more stable for complex models)
        if any(keyword in model_module for keyword in ["torch", "tensorflow", "keras"]):
            return ExplanationType.LIME

        # Default: LIME (model-agnostic)
        return ExplanationType.LIME

    def get_statistics(self) -> dict[str, Any]:
        """Get engine statistics.

        Returns:
            Statistics dictionary
        """
        stats = {
            "total_explanations": self.total_explanations_generated,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": (self.cache_hits / (self.cache_hits + self.cache_misses))
            if (self.cache_hits + self.cache_misses) > 0
            else 0.0,
        }

        if self.cache:
            stats["cache_stats"] = self.cache.get_stats()

        if self.tracker:
            stats["tracker_stats"] = self.tracker.get_statistics()
            stats["top_features"] = self.tracker.get_top_features(n=10)

        return stats

    def get_top_features(self, n: int = 10, time_window_hours: int | None = None) -> list[dict[str, Any]]:
        """Get top N most important features across all explanations.

        Args:
            n: Number of features
            time_window_hours: Optional time window

        Returns:
            List of top features
        """
        if not self.tracker:
            logger.warning("Feature tracking is disabled")
            return []

        return self.tracker.get_top_features(n=n, time_window_hours=time_window_hours)

    def detect_drift(
        self, feature_name: str | None = None, window_size: int = 100, threshold: float = 0.2
    ) -> dict[str, Any]:
        """Detect feature importance drift.

        Args:
            feature_name: Specific feature to check (None = global)
            window_size: Window size for comparison
            threshold: Drift threshold

        Returns:
            Drift detection result
        """
        if not self.tracker:
            logger.warning("Feature tracking is disabled")
            return {"drift_detected": False, "reason": "Tracking disabled"}

        if feature_name:
            return self.tracker.detect_drift(feature_name, window_size, threshold)
        return self.tracker.detect_global_drift(top_n=20, window_size=window_size, threshold=threshold)

    def clear_cache(self):
        """Clear explanation cache."""
        if self.cache:
            self.cache.clear()
            logger.info("Explanation cache cleared")

    def export_tracker_data(self) -> dict[str, Any]:
        """Export feature tracker data.

        Returns:
            Tracker data dictionary
        """
        if not self.tracker:
            return {}

        return self.tracker.export_to_dict()

    async def health_check(self) -> dict[str, Any]:
        """Perform health check on XAI engine.

        Returns:
            Health check results
        """
        health = {"status": "healthy", "explainers": {}, "cache": {}, "tracker": {}}

        # Check explainers
        try:
            # Simple test with dummy data
            dummy_instance = {"test_feature": 0.5}
            dummy_model = DummyModel()
            dummy_prediction = 0.5

            # Test LIME (quick check)
            lime_result = await self.lime_explainer.explain(
                dummy_model, dummy_instance, dummy_prediction, DetailLevel.SUMMARY
            )

            health["explainers"]["lime"] = {"status": "ok", "latency_ms": lime_result.latency_ms}

        except Exception as e:
            logger.error(f"LIME health check failed: {e}")
            health["explainers"]["lime"] = {"status": "error", "error": str(e)}
            health["status"] = "degraded"

        # Check cache
        if self.cache:
            try:
                cache_stats = self.cache.get_stats()
                health["cache"] = {"status": "ok", "stats": cache_stats}
            except Exception as e:
                health["cache"] = {"status": "error", "error": str(e)}
                health["status"] = "degraded"

        # Check tracker
        if self.tracker:
            try:
                tracker_stats = self.tracker.get_statistics()
                health["tracker"] = {"status": "ok", "stats": tracker_stats}
            except Exception as e:
                health["tracker"] = {"status": "error", "error": str(e)}
                health["status"] = "degraded"

        return health


class DummyModel:
    """Dummy model for testing."""

    def predict_proba(self, X):
        """Dummy predict_proba."""
        import numpy as np

        return np.array([[0.5, 0.5]])

    def predict(self, X):
        """Dummy predict."""
        import numpy as np

        return np.array([0.5])


# Global singleton instance (optional)
_global_engine: ExplanationEngine | None = None


def get_global_engine(config: dict[str, Any] | None = None) -> ExplanationEngine:
    """Get or create global ExplanationEngine instance.

    Args:
        config: Optional configuration (only used on first call)

    Returns:
        Global ExplanationEngine instance
    """
    global _global_engine

    if _global_engine is None:
        _global_engine = ExplanationEngine(config)
        logger.info("Created global ExplanationEngine instance")

    return _global_engine


def reset_global_engine():
    """Reset global ExplanationEngine instance."""
    global _global_engine
    _global_engine = None
    logger.info("Reset global ExplanationEngine instance")
