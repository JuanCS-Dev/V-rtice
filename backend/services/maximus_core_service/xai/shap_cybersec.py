"""CyberSecSHAP - SHAP adapted for cybersecurity deep learning models.

This module implements SHAP (SHapley Additive exPlanations) specifically adapted
for cybersecurity use cases, supporting neural networks, tree-based models, and
deep learning models used in threat detection.

Key Adaptations:
    - Kernel SHAP for model-agnostic explanations
    - Tree SHAP for XGBoost/LightGBM models
    - Deep SHAP for neural networks
    - Cybersecurity-specific background datasets
    - Optimized for real-time explanation generation
"""

import logging
import time
import uuid
from dataclasses import dataclass
from typing import Any

import numpy as np

from .base import DetailLevel, ExplainerBase, ExplanationResult, ExplanationType, FeatureImportance

logger = logging.getLogger(__name__)


@dataclass
class SHAPConfig:
    """Configuration for SHAP explainer.

    Attributes:
        algorithm: SHAP algorithm ('kernel', 'tree', 'deep', 'linear')
        num_background_samples: Number of background samples for kernel SHAP
        num_features: Number of top features to compute (None = all)
        check_additivity: Whether to check that SHAP values sum to prediction
    """

    algorithm: str = "kernel"
    num_background_samples: int = 100
    num_features: int | None = None
    check_additivity: bool = False


class CyberSecSHAP(ExplainerBase):
    """SHAP explainer adapted for cybersecurity models.

    Supports:
        - Tree-based models (XGBoost, LightGBM, Random Forest)
        - Neural networks (PyTorch, TensorFlow)
        - Linear models (Logistic Regression, SVM)
        - Model-agnostic kernel SHAP for any model
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize CyberSecSHAP.

        Args:
            config: Configuration dictionary with SHAP settings
        """
        super().__init__(config)

        # Use self.config from base class (guaranteed to be dict, not None)
        cfg = self.config

        # SHAP configuration
        self.shap_config = SHAPConfig(
            algorithm=cfg.get("algorithm", "kernel"),
            num_background_samples=cfg.get("num_background_samples", 100),
            num_features=cfg.get("num_features", None),
            check_additivity=cfg.get("check_additivity", False),
        )

        # Background dataset (for kernel SHAP)
        self.background_data: np.ndarray | None = None

        logger.info(f"CyberSecSHAP initialized with algorithm={self.shap_config.algorithm}")

    async def explain(
        self, model: Any, instance: dict[str, Any], prediction: Any, detail_level: DetailLevel = DetailLevel.DETAILED
    ) -> ExplanationResult:
        """Generate SHAP explanation for a cybersecurity prediction.

        Args:
            model: The model being explained
            instance: The input instance (dict of features)
            prediction: The model's prediction for this instance
            detail_level: Level of detail for the explanation

        Returns:
            ExplanationResult with SHAP values as feature importances
        """
        explain_start = time.time()

        self.validate_instance(instance)

        explanation_id = str(uuid.uuid4())
        decision_id = instance.get("decision_id", str(uuid.uuid4()))

        # Determine model type and select appropriate SHAP algorithm
        model_type_str = self._detect_model_type(model)
        algorithm = self._select_shap_algorithm(model_type_str)

        logger.debug(f"Using SHAP algorithm: {algorithm} for model type: {model_type_str}")

        # Convert instance to numpy array
        feature_names, feature_array = self._dict_to_array(instance)

        # Compute SHAP values
        logger.debug(f"Computing SHAP values for {len(feature_names)} features")
        shap_values = self._compute_shap_values(model, feature_array, feature_names, algorithm)

        # Convert SHAP values to FeatureImportance objects
        all_features = []
        for i, feature_name in enumerate(feature_names):
            shap_value = float(shap_values[i])
            feature_value = instance.get(feature_name)
            description = self.format_feature_description(feature_name, feature_value)

            all_features.append(
                FeatureImportance(
                    feature_name=feature_name,
                    importance=shap_value,
                    value=feature_value,
                    description=description,
                    contribution=shap_value,  # SHAP value IS the contribution
                )
            )

        # Sort by absolute SHAP value
        all_features.sort(key=lambda x: abs(x.importance), reverse=True)

        # Top features (based on detail level)
        num_top_features = {
            DetailLevel.SUMMARY: 3,
            DetailLevel.DETAILED: 10,
            DetailLevel.TECHNICAL: len(all_features),
        }.get(detail_level, 10)

        top_features = all_features[:num_top_features]

        # Generate summary
        summary = self._generate_summary(top_features, prediction, shap_values, detail_level)

        # Calculate explanation confidence (based on additivity)
        confidence = self._calculate_explanation_confidence(shap_values, prediction)

        # Visualization data (SHAP waterfall chart)
        visualization_data = self._generate_visualization_data(top_features, prediction, shap_values, detail_level)

        latency_ms = int((time.time() - explain_start) * 1000)

        logger.info(f"SHAP explanation generated in {latency_ms}ms (confidence: {confidence:.2f})")

        return ExplanationResult(
            explanation_id=explanation_id,
            decision_id=decision_id,
            explanation_type=ExplanationType.SHAP,
            detail_level=detail_level,
            summary=summary,
            top_features=top_features,
            all_features=all_features,
            confidence=confidence,
            visualization_data=visualization_data,
            model_type=model_type_str,
            latency_ms=latency_ms,
            metadata={
                "algorithm": algorithm,
                "num_features": len(all_features),
                "prediction": prediction,
                "base_value": float(np.mean(shap_values)) if len(shap_values) > 0 else 0.0,
            },
        )

    def get_supported_models(self) -> list[str]:
        """Get list of supported model types.

        Returns:
            List of supported model types
        """
        return [
            "xgboost",
            "lightgbm",
            "random_forest",
            "gradient_boosting",
            "pytorch",
            "tensorflow",
            "keras",
            "sklearn",
            "linear",
            "custom",  # Any model with predict() method
        ]

    def set_background_data(self, background_data: np.ndarray):
        """Set background dataset for kernel SHAP.

        Args:
            background_data: Background samples (N x M array)
        """
        self.background_data = background_data
        logger.info(f"Background data set: {background_data.shape}")

    def _detect_model_type(self, model: Any) -> str:
        """Detect model type from model object.

        Args:
            model: The model

        Returns:
            Model type string
        """
        model_class = type(model).__name__.lower()
        model_module = type(model).__module__.lower() if hasattr(type(model), "__module__") else ""

        if "xgb" in model_module or "xgboost" in model_class:
            return "xgboost"
        if "lightgbm" in model_module or "lgbm" in model_class:
            return "lightgbm"
        if "randomforest" in model_class or "randomforestclassifier" in model_class:
            return "random_forest"
        if "gradientboosting" in model_class:
            return "gradient_boosting"
        if "torch" in model_module or "pytorch" in model_module:
            return "pytorch"
        if "tensorflow" in model_module or "keras" in model_module:
            return "tensorflow"
        if "linear" in model_class or "logistic" in model_class:
            return "linear"
        if "sklearn" in model_module:
            return "sklearn"
        return "custom"

    def _select_shap_algorithm(self, model_type: str) -> str:
        """Select appropriate SHAP algorithm based on model type.

        Args:
            model_type: Detected model type

        Returns:
            SHAP algorithm name
        """
        # If user specified algorithm, use it
        if self.shap_config.algorithm != "kernel":
            return self.shap_config.algorithm

        # Auto-select based on model type
        if model_type in ["xgboost", "lightgbm", "random_forest", "gradient_boosting"]:
            return "tree"
        if model_type in ["pytorch", "tensorflow"]:
            return "deep"
        if model_type == "linear":
            return "linear"
        return "kernel"  # Model-agnostic fallback

    def _dict_to_array(self, instance: dict[str, Any]) -> tuple:
        """Convert instance dict to numpy array.

        Args:
            instance: Instance dictionary

        Returns:
            Tuple of (feature_names, feature_array)
        """
        # Exclude meta fields
        meta_fields = {"decision_id", "timestamp", "analysis_id"}
        feature_names = sorted([k for k in instance if k not in meta_fields])

        # Convert values to float array
        feature_values = []
        for name in feature_names:
            value = instance.get(name, 0)

            # Handle different types
            if isinstance(value, (int, float)) or isinstance(value, bool):
                feature_values.append(float(value))
            elif isinstance(value, str):
                # Hash string to number (simple encoding)
                feature_values.append(float(hash(value) % 1000000) / 1000000.0)
            else:
                feature_values.append(0.0)

        return feature_names, np.array(feature_values).reshape(1, -1)

    def _compute_shap_values(
        self, model: Any, instance: np.ndarray, feature_names: list[str], algorithm: str
    ) -> np.ndarray:
        """Compute SHAP values using specified algorithm.

        Args:
            model: The model
            instance: Instance as numpy array (1 x M)
            feature_names: Feature names
            algorithm: SHAP algorithm to use

        Returns:
            Array of SHAP values (M,)
        """
        if algorithm == "tree":
            return self._compute_tree_shap(model, instance)
        if algorithm == "linear":
            return self._compute_linear_shap(model, instance, feature_names)
        if algorithm == "deep":
            return self._compute_deep_shap(model, instance)
        # kernel (model-agnostic)
        return self._compute_kernel_shap(model, instance, feature_names)

    def _compute_kernel_shap(self, model: Any, instance: np.ndarray, feature_names: list[str]) -> np.ndarray:
        """Compute SHAP values using Kernel SHAP (model-agnostic).

        This is a simplified implementation based on weighted linear regression
        of coalition outcomes.

        Args:
            model: The model
            instance: Instance as numpy array (1 x M)
            feature_names: Feature names

        Returns:
            Array of SHAP values
        """
        num_features = instance.shape[1]

        # Get prediction for full instance
        full_pred = self._get_prediction(model, instance)

        # Generate background data if not provided
        if self.background_data is None:
            # Use zeros as background (simple baseline)
            background = np.zeros_like(instance)
            background_pred = self._get_prediction(model, background)
        else:
            # Use provided background
            background = self.background_data[:1]  # Use first sample
            background_pred = self._get_prediction(model, background)

        # Compute SHAP values using marginal contribution approximation
        shap_values = np.zeros(num_features)

        for i in range(num_features):
            # Create instance with feature i set to background value
            instance_without_i = instance.copy()
            instance_without_i[0, i] = background[0, i]

            # Get prediction without feature i
            pred_without_i = self._get_prediction(model, instance_without_i)

            # Marginal contribution of feature i
            shap_values[i] = full_pred - pred_without_i

        # Normalize to ensure additivity (optional)
        if self.shap_config.check_additivity:
            total = np.sum(shap_values)
            expected_total = full_pred - background_pred

            if abs(total - expected_total) > 0.01:
                logger.warning(f"SHAP values do not add up: sum={total:.4f}, expected={expected_total:.4f}")

        return shap_values

    def _compute_tree_shap(self, model: Any, instance: np.ndarray) -> np.ndarray:
        """Compute SHAP values for tree-based models.

        This uses a simplified tree traversal method. For production,
        consider using the official shap library's TreeExplainer.

        Args:
            model: Tree-based model
            instance: Instance as numpy array

        Returns:
            Array of SHAP values
        """
        # For tree models, we can use feature importances as a proxy
        # (this is a simplification; real TreeSHAP is more complex)

        num_features = instance.shape[1]

        # Try to get feature importances from model
        if hasattr(model, "feature_importances_"):
            importances = model.feature_importances_
        else:
            # Fallback to kernel SHAP
            logger.warning("Model has no feature_importances_, falling back to kernel SHAP")
            return self._compute_kernel_shap(model, instance, list(range(num_features)))

        # Scale importances by feature values
        # (SHAP values should reflect both importance and feature value)
        shap_values = importances * instance[0]

        return shap_values

    def _compute_linear_shap(self, model: Any, instance: np.ndarray, feature_names: list[str]) -> np.ndarray:
        """Compute SHAP values for linear models.

        For linear models, SHAP values = coefficients * (feature - mean)

        Args:
            model: Linear model
            instance: Instance as numpy array
            feature_names: Feature names

        Returns:
            Array of SHAP values
        """
        # Get coefficients
        if hasattr(model, "coef_"):
            coefficients = model.coef_

            # Handle multi-class case (use coefficients of last class)
            if coefficients.ndim > 1:
                coefficients = coefficients[-1]
        else:
            # Fallback to kernel SHAP
            logger.warning("Model has no coef_, falling back to kernel SHAP")
            return self._compute_kernel_shap(model, instance, feature_names)

        # SHAP for linear: coef * (x - E[x])
        # Assume E[x] = 0 for simplicity (or use background data mean)
        if self.background_data is not None:
            mean_values = np.mean(self.background_data, axis=0)
        else:
            mean_values = np.zeros(instance.shape[1])

        shap_values = coefficients * (instance[0] - mean_values)

        return shap_values

    def _compute_deep_shap(self, model: Any, instance: np.ndarray) -> np.ndarray:
        """Compute SHAP values for deep learning models.

        This uses gradient-based approximation (similar to Integrated Gradients).

        Args:
            model: Deep learning model
            instance: Instance as numpy array

        Returns:
            Array of SHAP values
        """
        # For deep models, use gradient-based approximation
        # This is a simplified version; production should use shap.DeepExplainer

        # Check if model has gradient computation capability
        if hasattr(model, "get_gradients"):
            # Custom model with gradient method
            gradients = model.get_gradients(instance)
        else:
            # Fallback to finite difference gradients
            logger.debug("Using finite difference gradients")
            gradients = self._compute_finite_difference_gradients(model, instance)

        # SHAP value ≈ gradient * feature_value (Integrated Gradients approximation)
        shap_values = gradients * instance[0]

        return shap_values

    def _compute_finite_difference_gradients(self, model: Any, instance: np.ndarray) -> np.ndarray:
        """Compute gradients using finite differences.

        Args:
            model: The model
            instance: Instance as numpy array

        Returns:
            Array of gradients
        """
        num_features = instance.shape[1]
        gradients = np.zeros(num_features)

        # Base prediction
        base_pred = self._get_prediction(model, instance)

        # Compute gradient for each feature
        epsilon = 0.01  # Small perturbation

        for i in range(num_features):
            # Perturb feature i
            perturbed = instance.copy()
            perturbed[0, i] += epsilon

            # Get perturbed prediction
            perturbed_pred = self._get_prediction(model, perturbed)

            # Finite difference
            gradients[i] = (perturbed_pred - base_pred) / epsilon

        return gradients

    def _get_prediction(self, model: Any, instance: np.ndarray) -> float:
        """Get model prediction for instance.

        Args:
            model: The model
            instance: Instance as numpy array

        Returns:
            Prediction value (float)
        """
        # Try predict_proba first
        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(instance)
            # Return probability of positive class
            if proba.ndim == 2:
                return float(proba[0, -1])
            return float(proba[0])

        # Fall back to predict
        if hasattr(model, "predict"):
            pred = model.predict(instance)
            return float(pred[0])

        raise ValueError("Model must have 'predict' or 'predict_proba' method")

    def _generate_summary(
        self, top_features: list[FeatureImportance], prediction: Any, shap_values: np.ndarray, detail_level: DetailLevel
    ) -> str:
        """Generate human-readable summary.

        Args:
            top_features: Top important features
            prediction: Model prediction
            shap_values: All SHAP values
            detail_level: Detail level

        Returns:
            Summary string
        """
        base_value = np.mean(shap_values) if len(shap_values) > 0 else 0.0

        if detail_level == DetailLevel.SUMMARY:
            # Short summary
            if not top_features:
                return f"Prediction: {prediction}. No significant features identified."

            top_feature = top_features[0]
            direction = "increases" if top_feature.importance > 0 else "decreases"

            return (
                f"Prediction: {prediction}. "
                f"The most important factor is {top_feature.feature_name} "
                f"which {direction} the prediction by {abs(top_feature.importance):.3f}."
            )

        if detail_level == DetailLevel.DETAILED:
            # Detailed summary with top features
            summary_parts = [f"Prediction: {prediction} (base value: {base_value:.3f})."]

            positive_features = [f for f in top_features if f.importance > 0][:3]
            negative_features = [f for f in top_features if f.importance < 0][:3]

            if positive_features:
                contrib_sum = sum(f.importance for f in positive_features)
                features_str = ", ".join([f"{f.feature_name} (+{f.importance:.3f})" for f in positive_features])
                summary_parts.append(f"Factors increasing prediction (total: +{contrib_sum:.3f}): {features_str}.")

            if negative_features:
                contrib_sum = sum(abs(f.importance) for f in negative_features)
                features_str = ", ".join([f"{f.feature_name} ({f.importance:.3f})" for f in negative_features])
                summary_parts.append(f"Factors decreasing prediction (total: -{contrib_sum:.3f}): {features_str}.")

            return " ".join(summary_parts)

        # TECHNICAL
        # Full technical details
        summary_parts = [f"SHAP Explanation for prediction: {prediction}"]
        summary_parts.append(f"Base value: {base_value:.4f}")
        summary_parts.append("Prediction = Base + Sum(SHAP values)")
        summary_parts.append(f"\nTop {len(top_features)} features by absolute SHAP value:")

        for i, feature in enumerate(top_features[:15], 1):
            sign = "+" if feature.importance >= 0 else ""
            summary_parts.append(
                f"{i}. {feature.feature_name}: {sign}{feature.importance:.4f} (value: {feature.value})"
            )

        return "\n".join(summary_parts)

    def _calculate_explanation_confidence(self, shap_values: np.ndarray, prediction: Any) -> float:
        """Calculate confidence in explanation based on additivity.

        Args:
            shap_values: SHAP values
            prediction: Model prediction

        Returns:
            Confidence score [0, 1]
        """
        # For SHAP, confidence is high if values are well-distributed
        # (not dominated by one feature)

        if len(shap_values) == 0:
            return 0.0

        # Calculate entropy of absolute SHAP values (higher entropy = more distributed)
        abs_shap = np.abs(shap_values)
        total = np.sum(abs_shap)

        if total == 0:
            return 0.5  # Neutral confidence if all SHAP values are zero

        # Normalize to probabilities
        probs = abs_shap / total

        # Calculate entropy
        epsilon = 1e-10
        entropy = -np.sum(probs * np.log(probs + epsilon))

        # Max entropy for N features = log(N)
        max_entropy = np.log(len(shap_values))

        # Normalized entropy [0, 1]
        if max_entropy > 0:
            normalized_entropy = entropy / max_entropy
        else:
            normalized_entropy = 0.0

        # High entropy = high confidence (explanation is well-distributed)
        return float(normalized_entropy)

    def _generate_visualization_data(
        self, top_features: list[FeatureImportance], prediction: Any, shap_values: np.ndarray, detail_level: DetailLevel
    ) -> dict[str, Any]:
        """Generate data for SHAP waterfall visualization.

        Args:
            top_features: Top features
            prediction: Prediction
            shap_values: All SHAP values
            detail_level: Detail level

        Returns:
            Visualization data dict
        """
        base_value = np.mean(shap_values) if len(shap_values) > 0 else 0.0

        # Waterfall chart data
        waterfall_data = []
        cumulative = base_value

        for feature in top_features:
            waterfall_data.append(
                {
                    "feature": feature.feature_name,
                    "shap_value": feature.importance,
                    "feature_value": str(feature.value),
                    "cumulative_before": cumulative,
                    "cumulative_after": cumulative + feature.importance,
                }
            )
            cumulative += feature.importance

        return {
            "type": "shap_waterfall",
            "base_value": float(base_value),
            "prediction": float(prediction) if isinstance(prediction, (int, float, np.number)) else str(prediction),
            "waterfall_data": waterfall_data,
            "features": [
                {"name": f.feature_name, "shap_value": f.importance, "value": str(f.value)} for f in top_features
            ],
        }
