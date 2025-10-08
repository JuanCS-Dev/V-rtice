"""CyberSecLIME - LIME adapted for cybersecurity threat classification.

This module implements LIME (Local Interpretable Model-agnostic Explanations)
specifically adapted for cybersecurity use cases, handling network features,
threat scores, behavioral indicators, and text-based threat intelligence.

Key Adaptations:
    - Network feature perturbation (IPs, ports, protocols)
    - Threat score perturbation with domain constraints
    - Text-based perturbation for narrative analysis
    - Cybersecurity-specific feature descriptions
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
class PerturbationConfig:
    """Configuration for feature perturbation.

    Attributes:
        num_samples: Number of perturbed samples to generate
        feature_selection: Method for feature selection ('auto', 'lasso', 'forward_selection')
        kernel_width: Width of the exponential kernel
        sample_around_instance: Whether to sample around the instance
    """

    num_samples: int = 5000
    feature_selection: str = "auto"
    kernel_width: float = 0.25
    sample_around_instance: bool = True


class CyberSecLIME(ExplainerBase):
    """LIME explainer adapted for cybersecurity models.

    Supports:
        - Network traffic classification
        - Threat scoring models
        - Behavioral anomaly detection
        - Narrative manipulation detection
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize CyberSecLIME.

        Args:
            config: Configuration dictionary with perturbation settings
        """
        super().__init__(config)

        # Use self.config from base class (guaranteed to be dict, not None)
        cfg = self.config

        # Perturbation configuration
        self.perturbation_config = PerturbationConfig(
            num_samples=cfg.get("num_samples", 5000),
            feature_selection=cfg.get("feature_selection", "auto"),
            kernel_width=cfg.get("kernel_width", 0.25),
            sample_around_instance=cfg.get("sample_around_instance", True),
        )

        # Feature type handlers
        self.feature_handlers = {
            "numeric": self._perturb_numeric,
            "categorical": self._perturb_categorical,
            "ip_address": self._perturb_ip,
            "port": self._perturb_port,
            "score": self._perturb_score,
            "text": self._perturb_text,
        }

        logger.info(f"CyberSecLIME initialized with {self.perturbation_config.num_samples} samples")

    async def explain(
        self, model: Any, instance: dict[str, Any], prediction: Any, detail_level: DetailLevel = DetailLevel.DETAILED
    ) -> ExplanationResult:
        """Generate LIME explanation for a cybersecurity prediction.

        Args:
            model: The model being explained (must have predict() or predict_proba())
            instance: The input instance (dict of features)
            prediction: The model's prediction for this instance
            detail_level: Level of detail for the explanation

        Returns:
            ExplanationResult with feature importances
        """
        explain_start = time.time()

        self.validate_instance(instance)

        # Validate model has prediction method
        if not hasattr(model, "predict") and not hasattr(model, "predict_proba"):
            raise ValueError("Model must have 'predict' or 'predict_proba' method")

        explanation_id = str(uuid.uuid4())
        decision_id = instance.get("decision_id", str(uuid.uuid4()))

        # Determine feature types
        feature_types = self._infer_feature_types(instance)

        # Generate perturbed samples
        logger.debug(f"Generating {self.perturbation_config.num_samples} perturbed samples")
        perturbed_samples, distances = self._generate_perturbed_samples(
            instance, feature_types, self.perturbation_config.num_samples
        )

        # Get predictions for perturbed samples
        logger.debug(f"Getting predictions for {len(perturbed_samples)} samples")
        predictions = self._get_model_predictions(model, perturbed_samples)

        # Calculate kernel weights (samples closer to original get higher weight)
        weights = self._calculate_kernel_weights(distances, self.perturbation_config.kernel_width)

        # Fit interpretable model (weighted linear regression)
        logger.debug("Fitting interpretable model")
        feature_importances = self._fit_interpretable_model(
            perturbed_samples, predictions, weights, feature_types.keys()
        )

        # Filter out internal fields and sort by absolute importance
        sorted_features = sorted(
            [(k, v) for k, v in feature_importances.items() if k != "__intercept__"],
            key=lambda x: abs(x[1]),
            reverse=True,
        )

        # Create FeatureImportance objects
        all_features = []
        for feature_name, importance in sorted_features:
            feature_value = instance.get(feature_name)
            description = self.format_feature_description(feature_name, feature_value)

            all_features.append(
                FeatureImportance(
                    feature_name=feature_name,
                    importance=importance,
                    value=feature_value,
                    description=description,
                    contribution=importance,  # For LIME, contribution = importance
                )
            )

        # Top features (based on detail level)
        num_top_features = {
            DetailLevel.SUMMARY: 3,
            DetailLevel.DETAILED: 10,
            DetailLevel.TECHNICAL: len(all_features),
        }.get(detail_level, 10)

        top_features = all_features[:num_top_features]

        # Generate summary
        summary = self._generate_summary(top_features, prediction, detail_level)

        # Calculate explanation confidence (R² of interpretable model)
        confidence = self._calculate_explanation_confidence(
            predictions, self._predict_interpretable_model(perturbed_samples, feature_importances), weights
        )

        # Visualization data for SHAP-style plots
        visualization_data = self._generate_visualization_data(top_features, prediction, detail_level)

        latency_ms = int((time.time() - explain_start) * 1000)

        logger.info(f"LIME explanation generated in {latency_ms}ms (confidence: {confidence:.2f})")

        return ExplanationResult(
            explanation_id=explanation_id,
            decision_id=decision_id,
            explanation_type=ExplanationType.LIME,
            detail_level=detail_level,
            summary=summary,
            top_features=top_features,
            all_features=all_features,
            confidence=confidence,
            visualization_data=visualization_data,
            model_type=type(model).__name__,
            latency_ms=latency_ms,
            metadata={
                "num_samples": self.perturbation_config.num_samples,
                "num_features": len(all_features),
                "prediction": prediction,
            },
        )

    def get_supported_models(self) -> list[str]:
        """Get list of supported model types.

        Returns:
            List of supported model types
        """
        return [
            "sklearn",
            "xgboost",
            "lightgbm",
            "pytorch",
            "tensorflow",
            "custom",  # Any model with predict() method
        ]

    def _infer_feature_types(self, instance: dict[str, Any]) -> dict[str, str]:
        """Infer feature types from instance data.

        Args:
            instance: Instance dictionary

        Returns:
            Dictionary mapping feature names to types
        """
        feature_types = {}

        for feature_name, value in instance.items():
            # Skip meta fields
            if feature_name in ["decision_id", "timestamp", "analysis_id"]:
                continue

            # Infer type based on name and value
            if "ip" in feature_name.lower() or "address" in feature_name.lower():
                feature_types[feature_name] = "ip_address"
            elif "port" in feature_name.lower():
                feature_types[feature_name] = "port"
            elif "score" in feature_name.lower() or "confidence" in feature_name.lower():
                feature_types[feature_name] = "score"
            elif isinstance(value, (int, float)):
                feature_types[feature_name] = "numeric"
            elif isinstance(value, str):
                if len(value) > 50:
                    feature_types[feature_name] = "text"
                else:
                    feature_types[feature_name] = "categorical"
            else:
                feature_types[feature_name] = "categorical"

        return feature_types

    def _generate_perturbed_samples(
        self, instance: dict[str, Any], feature_types: dict[str, str], num_samples: int
    ) -> tuple:
        """Generate perturbed samples around the instance.

        Args:
            instance: Original instance
            feature_types: Feature type mapping
            num_samples: Number of samples to generate

        Returns:
            Tuple of (perturbed_samples, distances)
        """
        perturbed_samples = []
        distances = []

        for _ in range(num_samples):
            perturbed = {}
            distance = 0.0

            for feature_name, feature_type in feature_types.items():
                original_value = instance.get(feature_name)

                # Perturb based on feature type
                handler = self.feature_handlers.get(feature_type, self._perturb_numeric)
                perturbed_value = handler(original_value, feature_name)

                perturbed[feature_name] = perturbed_value

                # Calculate distance (normalized)
                feature_distance = self._calculate_feature_distance(original_value, perturbed_value, feature_type)
                distance += feature_distance**2

            # Euclidean distance
            distance = np.sqrt(distance / len(feature_types))

            # Copy meta fields
            for key in ["decision_id", "timestamp", "analysis_id"]:
                if key in instance:
                    perturbed[key] = instance[key]

            perturbed_samples.append(perturbed)
            distances.append(distance)

        return perturbed_samples, np.array(distances)

    def _perturb_numeric(self, value: float, feature_name: str) -> float:
        """Perturb numeric feature.

        Args:
            value: Original value
            feature_name: Feature name

        Returns:
            Perturbed value
        """
        if value is None:
            return 0.0

        # Add Gaussian noise (std = 20% of value or 0.1 if value is small)
        std = max(abs(value) * 0.2, 0.1)
        perturbed = value + np.random.normal(0, std)

        # Keep non-negative for certain features
        if any(keyword in feature_name.lower() for keyword in ["count", "size", "length", "num_"]):
            perturbed = max(0, perturbed)

        return perturbed

    def _perturb_categorical(self, value: str, feature_name: str) -> str:
        """Perturb categorical feature.

        Args:
            value: Original value
            feature_name: Feature name

        Returns:
            Perturbed value (randomly changed 30% of the time)
        """
        if value is None:
            return "unknown"

        # Keep original value 70% of the time
        if np.random.random() < 0.7:
            return value

        # Common categorical values for cybersecurity
        common_values = {
            "protocol": ["TCP", "UDP", "ICMP", "HTTP", "HTTPS", "DNS", "SSH"],
            "http_method": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
            "severity": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
            "decision": ["BLOCK", "ALLOW", "INVESTIGATE"],
        }

        # Try to find matching category
        for category, values in common_values.items():
            if category in feature_name.lower():
                return np.random.choice(values)

        # Default: return original
        return value

    def _perturb_ip(self, value: str, feature_name: str) -> str:
        """Perturb IP address (keep network, change host).

        Args:
            value: Original IP
            feature_name: Feature name

        Returns:
            Perturbed IP
        """
        if not value or not isinstance(value, str):
            return "0.0.0.0"

        try:
            # Keep first 3 octets, randomize last octet
            parts = value.split(".")
            if len(parts) == 4:
                parts[3] = str(np.random.randint(1, 255))
                return ".".join(parts)
        except (ValueError, TypeError, AttributeError, IndexError) as e:
            # Invalid IP format or type - return original value
            logger.debug(f"IP perturbation failed for {value}: {e}")
            pass

        return value

    def _perturb_port(self, value: int, feature_name: str) -> int:
        """Perturb port number.

        Args:
            value: Original port
            feature_name: Feature name

        Returns:
            Perturbed port (common ports + random)
        """
        if value is None:
            return 0

        # Common ports (50% probability)
        if np.random.random() < 0.5:
            common_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 3306, 3389, 5432, 8080, 8443]
            return np.random.choice(common_ports)

        # Random port (1024-65535)
        return np.random.randint(1024, 65536)

    def _perturb_score(self, value: float, feature_name: str) -> float:
        """Perturb score (bounded 0-1).

        Args:
            value: Original score
            feature_name: Feature name

        Returns:
            Perturbed score [0, 1]
        """
        if value is None:
            return 0.5

        # Add noise, keep in [0, 1]
        perturbed = value + np.random.normal(0, 0.1)
        return max(0.0, min(1.0, perturbed))

    def _perturb_text(self, value: str, feature_name: str) -> str:
        """Perturb text feature (not implemented - return original).

        Args:
            value: Original text
            feature_name: Feature name

        Returns:
            Original text (unmodified)

        Note:
            Text perturbation (word dropout, synonym replacement) is not implemented.
            For text-based features, LIME explanations may be less informative.
            Consider using numerical/categorical features for better explanations.
        """
        return value

    def _calculate_feature_distance(self, original: Any, perturbed: Any, feature_type: str) -> float:
        """Calculate distance between original and perturbed feature.

        Args:
            original: Original value
            perturbed: Perturbed value
            feature_type: Feature type

        Returns:
            Normalized distance [0, 1]
        """
        if original is None or perturbed is None:
            return 1.0

        if feature_type in ["numeric", "score", "port"]:
            # Normalized numeric distance
            try:
                orig_val = float(original)
                pert_val = float(perturbed)
                diff = abs(orig_val - pert_val)

                # Normalize by max(value, 1) to avoid division by zero
                normalizer = max(abs(orig_val), 1.0)
                return min(1.0, diff / normalizer)
            except (ValueError, TypeError, ZeroDivisionError) as e:
                # Cannot convert to float or division error - return max distance
                logger.debug(f"Distance calculation failed for {original} vs {perturbed}: {e}")
                return 1.0

        elif feature_type in ["categorical", "ip_address", "text"]:
            # Binary distance for categorical
            return 0.0 if original == perturbed else 1.0

        return 1.0

    def _get_model_predictions(self, model: Any, samples: list[dict[str, Any]]) -> np.ndarray:
        """Get model predictions for perturbed samples.

        Args:
            model: The model
            samples: List of perturbed samples

        Returns:
            Array of predictions
        """
        # Try predict_proba first (for classifiers)
        if hasattr(model, "predict_proba"):
            # Convert samples to format expected by model
            X = self._samples_to_model_input(samples, model)
            proba = model.predict_proba(X)

            # Use probability of positive class (or first class for multi-class)
            if proba.ndim == 2:
                return proba[:, -1]  # Last column (typically positive class)
            return proba

        # Fall back to predict()
        if hasattr(model, "predict"):
            X = self._samples_to_model_input(samples, model)
            return model.predict(X)

        raise ValueError("Model must have 'predict' or 'predict_proba' method")

    def _samples_to_model_input(self, samples: list[dict[str, Any]], model: Any) -> Any:
        """Convert samples to model input format.

        Args:
            samples: List of sample dicts
            model: The model

        Returns:
            Input in format expected by model (numpy array, DataFrame, etc.)
        """
        # For most sklearn models: convert to numpy array
        # Assume features are in same order as original training

        # Get feature names (excluding meta fields)
        meta_fields = {"decision_id", "timestamp", "analysis_id"}
        feature_names = sorted([k for k in samples[0].keys() if k not in meta_fields])

        # Convert to numpy array
        X = np.array([[sample.get(f, 0) for f in feature_names] for sample in samples])

        return X

    def _calculate_kernel_weights(self, distances: np.ndarray, kernel_width: float) -> np.ndarray:
        """Calculate kernel weights for samples.

        Args:
            distances: Array of distances from original instance
            kernel_width: Width of exponential kernel

        Returns:
            Array of weights
        """
        # Exponential kernel: exp(-d^2 / width^2)
        return np.exp(-(distances**2) / (kernel_width**2))

    def _fit_interpretable_model(
        self, samples: list[dict[str, Any]], predictions: np.ndarray, weights: np.ndarray, feature_names: list[str]
    ) -> dict[str, float]:
        """Fit weighted linear regression model.

        Args:
            samples: Perturbed samples
            predictions: Model predictions
            weights: Sample weights
            feature_names: Feature names

        Returns:
            Dictionary of feature importances (coefficients)
        """
        from sklearn.linear_model import Ridge

        # Convert samples to feature matrix
        meta_fields = {"decision_id", "timestamp", "analysis_id"}
        feature_names = sorted([f for f in feature_names if f not in meta_fields])

        X = np.array([[sample.get(f, 0) for f in feature_names] for sample in samples])

        # Fit weighted ridge regression
        model = Ridge(alpha=1.0)
        model.fit(X, predictions, sample_weight=weights)

        # Return coefficients as importances (include intercept for prediction)
        importances = {}
        for i, feature_name in enumerate(feature_names):
            importances[feature_name] = float(model.coef_[i])

        # Store intercept for accurate predictions
        importances["__intercept__"] = float(model.intercept_)

        return importances

    def _predict_interpretable_model(self, samples: list[dict[str, Any]], importances: dict[str, float]) -> np.ndarray:
        """Predict using interpretable model.

        Args:
            samples: Samples to predict
            importances: Feature importances (coefficients)

        Returns:
            Predictions
        """
        meta_fields = {"decision_id", "timestamp", "analysis_id", "__intercept__"}
        feature_names = sorted([f for f in importances if f not in meta_fields])

        X = np.array([[sample.get(f, 0) for f in feature_names] for sample in samples])
        coefficients = np.array([importances[f] for f in feature_names])

        # Include intercept in prediction
        intercept = importances.get("__intercept__", 0.0)
        return X.dot(coefficients) + intercept

    def _calculate_explanation_confidence(
        self, true_predictions: np.ndarray, interpretable_predictions: np.ndarray, weights: np.ndarray
    ) -> float:
        """Calculate explanation confidence (weighted R²).

        Args:
            true_predictions: Model's predictions
            interpretable_predictions: Interpretable model's predictions
            weights: Sample weights

        Returns:
            R² score (confidence)
        """
        # Weighted R²
        residuals = true_predictions - interpretable_predictions
        ss_res = np.sum(weights * (residuals**2))

        mean_pred = np.average(true_predictions, weights=weights)
        ss_tot = np.sum(weights * ((true_predictions - mean_pred) ** 2))

        if ss_tot == 0:
            # No variance in predictions
            if ss_res == 0:
                return 1.0  # Perfect explanation (no variance, no residuals)
            return 0.0  # Degenerate case: no variance but still have residuals

        r_squared = 1 - (ss_res / ss_tot)
        return max(0.0, min(1.0, r_squared))

    def _generate_summary(
        self, top_features: list[FeatureImportance], prediction: Any, detail_level: DetailLevel
    ) -> str:
        """Generate human-readable summary.

        Args:
            top_features: Top important features
            prediction: Model prediction
            detail_level: Detail level

        Returns:
            Summary string
        """
        if detail_level == DetailLevel.SUMMARY:
            # Short summary (1-2 sentences)
            if not top_features:
                return f"Prediction: {prediction}. No significant features identified."

            top_feature = top_features[0]
            direction = "increases" if top_feature.importance > 0 else "decreases"

            return (
                f"Prediction: {prediction}. "
                f"The most important factor is {top_feature.feature_name} "
                f"which {direction} the likelihood of this prediction."
            )

        if detail_level == DetailLevel.DETAILED:
            # Detailed summary with top 3 features
            summary_parts = [f"Prediction: {prediction}."]

            positive_features = [f for f in top_features if f.importance > 0][:2]
            negative_features = [f for f in top_features if f.importance < 0][:2]

            if positive_features:
                features_str = ", ".join([f.feature_name for f in positive_features])
                summary_parts.append(f"Key factors supporting this prediction: {features_str}.")

            if negative_features:
                features_str = ", ".join([f.feature_name for f in negative_features])
                summary_parts.append(f"Key factors against this prediction: {features_str}.")

            return " ".join(summary_parts)

        # TECHNICAL
        # Full technical details
        summary_parts = [f"LIME Explanation for prediction: {prediction}"]
        summary_parts.append(f"Top {len(top_features)} features by importance:")

        for i, feature in enumerate(top_features[:10], 1):
            direction = "+" if feature.importance >= 0 else "-"
            summary_parts.append(
                f"{i}. {feature.feature_name}: {direction}{abs(feature.importance):.4f} (value: {feature.value})"
            )

        return "\n".join(summary_parts)

    def _generate_visualization_data(
        self, top_features: list[FeatureImportance], prediction: Any, detail_level: DetailLevel
    ) -> dict[str, Any]:
        """Generate data for visualization.

        Args:
            top_features: Top features
            prediction: Prediction
            detail_level: Detail level

        Returns:
            Visualization data dict
        """
        return {
            "type": "lime_bar_chart",
            "prediction": float(prediction) if isinstance(prediction, (int, float, np.number)) else str(prediction),
            "features": [
                {"name": f.feature_name, "importance": f.importance, "value": str(f.value)} for f in top_features
            ],
        }
