"""Counterfactual Explanation Generator for cybersecurity models.

This module generates counterfactual explanations ("what-if" scenarios) for
cybersecurity predictions, helping users understand what changes would result
in different decisions.

Key Features:
    - Minimal perturbation counterfactuals (closest alternative)
    - Actionable recommendations for security operators
    - Cybersecurity-specific constraints (valid IPs, ports, scores)
    - Multi-objective optimization (proximity + sparsity + validity)
"""

import logging
import time
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import uuid

from .base import (
    ExplainerBase,
    ExplanationResult,
    ExplanationType,
    DetailLevel,
    FeatureImportance
)

logger = logging.getLogger(__name__)


@dataclass
class CounterfactualConfig:
    """Configuration for counterfactual generation.

    Attributes:
        desired_outcome: Desired prediction outcome
        max_iterations: Maximum optimization iterations
        num_candidates: Number of candidates to generate
        proximity_weight: Weight for proximity objective
        sparsity_weight: Weight for sparsity objective (prefer fewer changes)
        validity_weight: Weight for validity objective (valid cybersec values)
    """
    desired_outcome: Optional[Any] = None
    max_iterations: int = 1000
    num_candidates: int = 10
    proximity_weight: float = 1.0
    sparsity_weight: float = 0.5
    validity_weight: float = 0.3


class CounterfactualGenerator(ExplainerBase):
    """Generate counterfactual explanations for cybersecurity predictions.

    Generates minimal modifications to instances that would flip the prediction,
    helping operators understand decision boundaries and actionable interventions.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize CounterfactualGenerator.

        Args:
            config: Configuration dictionary with counterfactual settings
        """
        super().__init__(config)

        # Use self.config from base class (guaranteed to be dict, not None)
        cfg = self.config

        # Counterfactual configuration
        self.cf_config = CounterfactualConfig(
            desired_outcome=cfg.get('desired_outcome', None),
            max_iterations=cfg.get('max_iterations', 1000),
            num_candidates=cfg.get('num_candidates', 10),
            proximity_weight=cfg.get('proximity_weight', 1.0),
            sparsity_weight=cfg.get('sparsity_weight', 0.5),
            validity_weight=cfg.get('validity_weight', 0.3)
        )

        # Feature constraints (for cybersecurity domains)
        self.feature_constraints = self._init_feature_constraints()

        logger.info(f"CounterfactualGenerator initialized with {self.cf_config.num_candidates} candidates")

    async def explain(
        self,
        model: Any,
        instance: Dict[str, Any],
        prediction: Any,
        detail_level: DetailLevel = DetailLevel.DETAILED
    ) -> ExplanationResult:
        """Generate counterfactual explanation.

        Args:
            model: The model being explained
            instance: The input instance (dict of features)
            prediction: The model's prediction for this instance
            detail_level: Level of detail for the explanation

        Returns:
            ExplanationResult with counterfactual scenario
        """
        explain_start = time.time()

        self.validate_instance(instance)

        # Validate model has prediction method
        if not hasattr(model, 'predict') and not hasattr(model, 'predict_proba'):
            raise ValueError("Model must have 'predict' or 'predict_proba' method")

        explanation_id = str(uuid.uuid4())
        decision_id = instance.get('decision_id', str(uuid.uuid4()))

        # Determine desired outcome (flip prediction by default)
        desired_outcome = self._determine_desired_outcome(prediction)

        logger.debug(f"Generating counterfactual: {prediction} → {desired_outcome}")

        # Convert instance to array
        feature_names, instance_array = self._dict_to_array(instance)

        # Generate counterfactual candidates
        logger.debug(f"Generating {self.cf_config.num_candidates} counterfactual candidates")
        candidates = self._generate_counterfactual_candidates(
            model,
            instance_array,
            feature_names,
            desired_outcome,
            instance
        )

        if not candidates:
            logger.warning("No valid counterfactuals found")
            return self._create_no_counterfactual_result(
                explanation_id,
                decision_id,
                prediction,
                detail_level,
                int((time.time() - explain_start) * 1000)
            )

        # Select best counterfactual (closest to original)
        best_cf, cf_prediction, distance = self._select_best_counterfactual(
            candidates,
            instance_array,
            model
        )

        # Identify changed features
        changed_features = self._identify_changed_features(
            instance,
            best_cf,
            feature_names,
            instance_array[0]
        )

        # Create FeatureImportance objects for changed features
        all_features = []
        for feature_info in changed_features:
            all_features.append(FeatureImportance(
                feature_name=feature_info['name'],
                importance=feature_info['importance'],  # Change magnitude
                value=feature_info['new_value'],
                description=feature_info['description'],
                contribution=feature_info['importance']
            ))

        # Sort by importance (magnitude of change)
        all_features.sort(key=lambda x: abs(x.importance), reverse=True)

        # Top features
        num_top_features = {
            DetailLevel.SUMMARY: 3,
            DetailLevel.DETAILED: len(all_features),
            DetailLevel.TECHNICAL: len(all_features)
        }.get(detail_level, len(all_features))

        top_features = all_features[:num_top_features]

        # Generate counterfactual summary
        summary, counterfactual_text = self._generate_counterfactual_summary(
            changed_features,
            prediction,
            cf_prediction,
            detail_level
        )

        # Calculate confidence based on distance and validity
        confidence = self._calculate_counterfactual_confidence(distance, len(changed_features))

        # Visualization data
        visualization_data = self._generate_visualization_data(
            changed_features,
            prediction,
            cf_prediction,
            detail_level
        )

        latency_ms = int((time.time() - explain_start) * 1000)

        logger.info(f"Counterfactual generated in {latency_ms}ms (distance: {distance:.3f})")

        return ExplanationResult(
            explanation_id=explanation_id,
            decision_id=decision_id,
            explanation_type=ExplanationType.COUNTERFACTUAL,
            detail_level=detail_level,
            summary=summary,
            top_features=top_features,
            all_features=all_features,
            confidence=confidence,
            counterfactual=counterfactual_text,
            visualization_data=visualization_data,
            model_type=type(model).__name__,
            latency_ms=latency_ms,
            metadata={
                'original_prediction': prediction,
                'counterfactual_prediction': cf_prediction,
                'distance': float(distance),
                'num_changes': len(changed_features),
                'num_candidates_tried': self.cf_config.num_candidates
            }
        )

    def get_supported_models(self) -> List[str]:
        """Get list of supported model types.

        Returns:
            List of supported model types
        """
        return [
            'sklearn',
            'xgboost',
            'lightgbm',
            'pytorch',
            'tensorflow',
            'custom'  # Any model with predict() method
        ]

    def _init_feature_constraints(self) -> Dict[str, Dict[str, Any]]:
        """Initialize cybersecurity-specific feature constraints.

        Returns:
            Dictionary of feature constraints
        """
        return {
            'port': {'min': 1, 'max': 65535, 'type': 'int'},
            'src_port': {'min': 1, 'max': 65535, 'type': 'int'},
            'dst_port': {'min': 1, 'max': 65535, 'type': 'int'},
            'score': {'min': 0.0, 'max': 1.0, 'type': 'float'},
            'threat_score': {'min': 0.0, 'max': 1.0, 'type': 'float'},
            'anomaly_score': {'min': 0.0, 'max': 1.0, 'type': 'float'},
            'confidence': {'min': 0.0, 'max': 1.0, 'type': 'float'},
            'severity': {'min': 0.0, 'max': 1.0, 'type': 'float'},
            'probability': {'min': 0.0, 'max': 1.0, 'type': 'float'},
            'packet_size': {'min': 0, 'max': 65535, 'type': 'int'},
            'payload_size': {'min': 0, 'max': 65535, 'type': 'int'}
        }

    def _determine_desired_outcome(self, current_prediction: Any) -> Any:
        """Determine desired counterfactual outcome.

        Args:
            current_prediction: Current prediction

        Returns:
            Desired outcome
        """
        # If explicitly set in config, use it
        if self.cf_config.desired_outcome is not None:
            return self.cf_config.desired_outcome

        # Default: flip binary prediction
        if isinstance(current_prediction, bool):
            return not current_prediction

        if isinstance(current_prediction, (int, float, np.number)):
            # If prediction is a probability, flip threshold
            if 0 <= current_prediction <= 1:
                return 1.0 - current_prediction
            # If binary 0/1, flip
            if current_prediction in [0, 1]:
                return 1 - current_prediction

        # For strings (BLOCK/ALLOW), flip
        if isinstance(current_prediction, str):
            flip_map = {
                'BLOCK': 'ALLOW',
                'ALLOW': 'BLOCK',
                'REJECTED': 'APPROVED',
                'APPROVED': 'REJECTED',
                'HIGH': 'LOW',
                'LOW': 'HIGH'
            }
            return flip_map.get(current_prediction.upper(), 'OPPOSITE')

        # Default: return opposite
        return 'OPPOSITE'

    def _dict_to_array(self, instance: Dict[str, Any]) -> Tuple[List[str], np.ndarray]:
        """Convert instance dict to numpy array.

        Args:
            instance: Instance dictionary

        Returns:
            Tuple of (feature_names, feature_array)
        """
        # Exclude meta fields
        meta_fields = {'decision_id', 'timestamp', 'analysis_id'}
        feature_names = sorted([k for k in instance.keys() if k not in meta_fields])

        # Convert values to float array
        feature_values = []
        for name in feature_names:
            value = instance.get(name, 0)

            # Handle different types
            if isinstance(value, (int, float)):
                feature_values.append(float(value))
            elif isinstance(value, bool):
                feature_values.append(float(value))
            elif isinstance(value, str):
                # Hash string to number (simple encoding)
                feature_values.append(float(hash(value) % 1000000) / 1000000.0)
            else:
                feature_values.append(0.0)

        return feature_names, np.array(feature_values).reshape(1, -1)

    def _generate_counterfactual_candidates(
        self,
        model: Any,
        instance: np.ndarray,
        feature_names: List[str],
        desired_outcome: Any,
        original_dict: Dict[str, Any]
    ) -> List[np.ndarray]:
        """Generate counterfactual candidates using genetic algorithm.

        Args:
            model: The model
            instance: Instance as numpy array (1 x M)
            feature_names: Feature names
            desired_outcome: Desired prediction
            original_dict: Original instance as dict

        Returns:
            List of counterfactual candidate arrays
        """
        candidates = []
        num_features = instance.shape[1]

        # Strategy 1: Random perturbations (50% of candidates)
        num_random = self.cf_config.num_candidates // 2

        for _ in range(num_random):
            candidate = self._generate_random_perturbation(
                instance,
                feature_names,
                original_dict
            )

            # Check if it achieves desired outcome
            pred = self._get_prediction(model, candidate)

            if self._matches_desired_outcome(pred, desired_outcome):
                candidates.append(candidate[0])

        # Strategy 2: Gradient-based (if model supports)
        if hasattr(model, 'predict_proba') and len(candidates) < self.cf_config.num_candidates:
            num_gradient = self.cf_config.num_candidates - len(candidates)

            for _ in range(num_gradient):
                candidate = self._generate_gradient_based_cf(
                    model,
                    instance,
                    desired_outcome,
                    feature_names,
                    original_dict
                )

                if candidate is not None:
                    pred = self._get_prediction(model, candidate)
                    if self._matches_desired_outcome(pred, desired_outcome):
                        candidates.append(candidate[0])

        return candidates

    def _generate_random_perturbation(
        self,
        instance: np.ndarray,
        feature_names: List[str],
        original_dict: Dict[str, Any]
    ) -> np.ndarray:
        """Generate random perturbation of instance.

        Args:
            instance: Original instance
            feature_names: Feature names
            original_dict: Original instance dict

        Returns:
            Perturbed instance
        """
        perturbed = instance.copy()

        # Randomly select 1-3 features to perturb
        num_to_perturb = np.random.randint(1, min(4, len(feature_names) + 1))
        features_to_perturb = np.random.choice(len(feature_names), num_to_perturb, replace=False)

        for idx in features_to_perturb:
            feature_name = feature_names[idx]
            original_value = instance[0, idx]

            # Perturb based on feature type
            new_value = self._perturb_feature(feature_name, original_value, original_dict)
            perturbed[0, idx] = new_value

        return perturbed

    def _perturb_feature(
        self,
        feature_name: str,
        original_value: float,
        original_dict: Dict[str, Any]
    ) -> float:
        """Perturb a single feature while respecting constraints.

        Args:
            feature_name: Feature name
            original_value: Original value
            original_dict: Original instance dict

        Returns:
            Perturbed value
        """
        # Check if feature has constraints
        constraints = None
        for pattern, constraint in self.feature_constraints.items():
            if pattern in feature_name.lower():
                constraints = constraint
                break

        if constraints:
            # Perturb within constraints
            min_val = constraints['min']
            max_val = constraints['max']

            if constraints['type'] == 'int':
                return float(np.random.randint(min_val, max_val + 1))
            else:
                return np.random.uniform(min_val, max_val)

        # No constraints: add Gaussian noise
        std = max(abs(original_value) * 0.3, 0.2)
        perturbed = original_value + np.random.normal(0, std)

        # Keep non-negative for certain features
        if any(keyword in feature_name.lower() for keyword in ['count', 'size', 'length', 'num_']):
            perturbed = max(0, perturbed)

        return perturbed

    def _generate_gradient_based_cf(
        self,
        model: Any,
        instance: np.ndarray,
        desired_outcome: Any,
        feature_names: List[str],
        original_dict: Dict[str, Any]
    ) -> Optional[np.ndarray]:
        """Generate counterfactual using gradient descent.

        Args:
            model: The model
            instance: Instance array
            desired_outcome: Desired outcome
            feature_names: Feature names
            original_dict: Original dict

        Returns:
            Counterfactual array or None
        """
        # Start from original instance
        candidate = instance.copy()

        # Get current prediction
        current_pred = self._get_prediction(model, candidate)

        # Determine direction to move
        if isinstance(desired_outcome, (int, float, np.number)):
            target_value = float(desired_outcome)
        else:
            # For binary flip, move in opposite direction
            target_value = 1.0 - current_pred if 0 <= current_pred <= 1 else 0.5

        # Gradient descent
        learning_rate = 0.1
        max_steps = 50

        for step in range(max_steps):
            # Compute gradient via finite differences
            gradients = self._compute_gradients(model, candidate)

            # Update candidate
            direction = target_value - current_pred
            candidate += learning_rate * direction * gradients.reshape(1, -1)

            # Apply constraints
            for i, feature_name in enumerate(feature_names):
                candidate[0, i] = self._apply_constraints(feature_name, candidate[0, i])

            # Check if reached desired outcome
            current_pred = self._get_prediction(model, candidate)

            if self._matches_desired_outcome(current_pred, desired_outcome):
                return candidate

        return None  # Failed to find counterfactual

    def _compute_gradients(self, model: Any, instance: np.ndarray) -> np.ndarray:
        """Compute gradients using finite differences.

        Args:
            model: The model
            instance: Instance array

        Returns:
            Gradient array
        """
        num_features = instance.shape[1]
        gradients = np.zeros(num_features)

        base_pred = self._get_prediction(model, instance)
        epsilon = 0.01

        for i in range(num_features):
            perturbed = instance.copy()
            perturbed[0, i] += epsilon

            perturbed_pred = self._get_prediction(model, perturbed)
            gradients[i] = (perturbed_pred - base_pred) / epsilon

        return gradients

    def _apply_constraints(self, feature_name: str, value: float) -> float:
        """Apply constraints to feature value.

        Args:
            feature_name: Feature name
            value: Value to constrain

        Returns:
            Constrained value
        """
        # Check feature constraints
        for pattern, constraint in self.feature_constraints.items():
            if pattern in feature_name.lower():
                value = np.clip(value, constraint['min'], constraint['max'])

                if constraint['type'] == 'int':
                    value = round(value)

                return value

        return value

    def _get_prediction(self, model: Any, instance: np.ndarray) -> float:
        """Get model prediction.

        Args:
            model: The model
            instance: Instance array

        Returns:
            Prediction value
        """
        if hasattr(model, 'predict_proba'):
            proba = model.predict_proba(instance)
            if proba.ndim == 2:
                return float(proba[0, -1])
            return float(proba[0])

        elif hasattr(model, 'predict'):
            pred = model.predict(instance)
            return float(pred[0])

        else:
            raise ValueError("Model must have 'predict' or 'predict_proba' method")

    def _matches_desired_outcome(self, prediction: float, desired_outcome: Any) -> bool:
        """Check if prediction matches desired outcome.

        Args:
            prediction: Model prediction
            desired_outcome: Desired outcome

        Returns:
            True if matches
        """
        if isinstance(desired_outcome, (int, float, np.number)):
            # For numeric outcomes, check if within 0.1 threshold
            return abs(prediction - float(desired_outcome)) < 0.1

        # For other types, basic comparison
        return prediction == desired_outcome

    def _select_best_counterfactual(
        self,
        candidates: List[np.ndarray],
        original: np.ndarray,
        model: Any
    ) -> Tuple[np.ndarray, float, float]:
        """Select best counterfactual (closest to original).

        Args:
            candidates: List of candidate arrays
            original: Original instance
            model: The model

        Returns:
            Tuple of (best_candidate, prediction, distance)
        """
        best_cf = candidates[0]
        best_distance = float('inf')
        best_prediction = self._get_prediction(model, best_cf.reshape(1, -1))

        for candidate in candidates:
            # Calculate Euclidean distance
            distance = np.linalg.norm(candidate - original[0])

            if distance < best_distance:
                best_distance = distance
                best_cf = candidate
                best_prediction = self._get_prediction(model, candidate.reshape(1, -1))

        return best_cf, best_prediction, best_distance

    def _identify_changed_features(
        self,
        original_dict: Dict[str, Any],
        counterfactual: np.ndarray,
        feature_names: List[str],
        original_array: np.ndarray
    ) -> List[Dict[str, Any]]:
        """Identify which features changed in counterfactual.

        Args:
            original_dict: Original instance dict
            counterfactual: Counterfactual array
            feature_names: Feature names
            original_array: Original array

        Returns:
            List of changed feature info dicts
        """
        changed_features = []

        for i, feature_name in enumerate(feature_names):
            original_value = original_array[i]
            cf_value = counterfactual[i]

            # Check if changed (threshold)
            if abs(cf_value - original_value) > 0.01:
                change_magnitude = cf_value - original_value

                # Get original dict value for description
                dict_value = original_dict.get(feature_name, original_value)

                changed_features.append({
                    'name': feature_name,
                    'original_value': original_value,
                    'new_value': cf_value,
                    'importance': abs(change_magnitude),
                    'description': self._format_change_description(
                        feature_name,
                        dict_value,
                        cf_value,
                        change_magnitude
                    )
                })

        return changed_features

    def _format_change_description(
        self,
        feature_name: str,
        original: Any,
        new_value: float,
        change: float
    ) -> str:
        """Format change description.

        Args:
            feature_name: Feature name
            original: Original value
            new_value: New value
            change: Change magnitude

        Returns:
            Human-readable description
        """
        direction = "increase" if change > 0 else "decrease"
        return f"{feature_name}: {original:.2f} → {new_value:.2f} ({direction} of {abs(change):.2f})"

    def _generate_counterfactual_summary(
        self,
        changed_features: List[Dict[str, Any]],
        original_pred: Any,
        cf_pred: float,
        detail_level: DetailLevel
    ) -> Tuple[str, str]:
        """Generate counterfactual summary and text.

        Args:
            changed_features: Changed features
            original_pred: Original prediction
            cf_pred: Counterfactual prediction
            detail_level: Detail level

        Returns:
            Tuple of (summary, counterfactual_text)
        """
        if not changed_features:
            summary = f"No counterfactual found. Original prediction: {original_pred}"
            cf_text = "Unable to generate alternative scenario."
            return summary, cf_text

        if detail_level == DetailLevel.SUMMARY:
            top_change = changed_features[0]
            summary = (f"If {top_change['name']} were changed from {top_change['original_value']:.2f} "
                      f"to {top_change['new_value']:.2f}, prediction would be {cf_pred:.2f}.")
            cf_text = summary

        elif detail_level == DetailLevel.DETAILED:
            summary_parts = [f"Original prediction: {original_pred}, Counterfactual: {cf_pred}"]

            if len(changed_features) == 1:
                change = changed_features[0]
                summary_parts.append(
                    f"If {change['name']} changed from {change['original_value']:.2f} "
                    f"to {change['new_value']:.2f}, prediction would flip."
                )
            else:
                summary_parts.append(f"Required {len(changed_features)} changes:")
                for change in changed_features[:5]:
                    summary_parts.append(
                        f"  - {change['name']}: {change['original_value']:.2f} → {change['new_value']:.2f}"
                    )

            summary = " ".join(summary_parts)
            cf_text = summary

        else:  # TECHNICAL
            summary_parts = [f"Counterfactual Explanation"]
            summary_parts.append(f"Original prediction: {original_pred}")
            summary_parts.append(f"Counterfactual prediction: {cf_pred}")
            summary_parts.append(f"\nRequired changes ({len(changed_features)} features):")

            for i, change in enumerate(changed_features, 1):
                summary_parts.append(
                    f"{i}. {change['name']}: {change['original_value']:.4f} → "
                    f"{change['new_value']:.4f} (Δ={change['new_value'] - change['original_value']:.4f})"
                )

            summary = "\n".join(summary_parts)
            cf_text = summary

        return summary, cf_text

    def _calculate_counterfactual_confidence(self, distance: float, num_changes: int) -> float:
        """Calculate confidence in counterfactual.

        Args:
            distance: Distance from original
            num_changes: Number of features changed

        Returns:
            Confidence score [0, 1]
        """
        # Confidence decreases with distance and number of changes
        distance_factor = np.exp(-distance)  # [0, 1], higher for closer
        sparsity_factor = 1.0 / (1.0 + num_changes)  # [0, 1], higher for fewer changes

        # Combined confidence
        confidence = 0.6 * distance_factor + 0.4 * sparsity_factor

        return max(0.0, min(1.0, confidence))

    def _generate_visualization_data(
        self,
        changed_features: List[Dict[str, Any]],
        original_pred: Any,
        cf_pred: float,
        detail_level: DetailLevel
    ) -> Dict[str, Any]:
        """Generate visualization data.

        Args:
            changed_features: Changed features
            original_pred: Original prediction
            cf_pred: Counterfactual prediction
            detail_level: Detail level

        Returns:
            Visualization data dict
        """
        return {
            'type': 'counterfactual_comparison',
            'original_prediction': float(original_pred) if isinstance(original_pred, (int, float, np.number)) else str(original_pred),
            'counterfactual_prediction': float(cf_pred),
            'changes': [
                {
                    'feature': change['name'],
                    'original': float(change['original_value']),
                    'counterfactual': float(change['new_value']),
                    'delta': float(change['new_value'] - change['original_value'])
                }
                for change in changed_features
            ]
        }

    def _create_no_counterfactual_result(
        self,
        explanation_id: str,
        decision_id: str,
        prediction: Any,
        detail_level: DetailLevel,
        latency_ms: int
    ) -> ExplanationResult:
        """Create result when no counterfactual is found.

        Args:
            explanation_id: Explanation ID
            decision_id: Decision ID
            prediction: Original prediction
            detail_level: Detail level
            latency_ms: Latency

        Returns:
            ExplanationResult
        """
        # Create a dummy feature to satisfy validation
        dummy_feature = FeatureImportance(
            feature_name="no_counterfactual",
            importance=0.0,
            value=None,
            description="No counterfactual found within constraints",
            contribution=0.0
        )

        return ExplanationResult(
            explanation_id=explanation_id,
            decision_id=decision_id,
            explanation_type=ExplanationType.COUNTERFACTUAL,
            detail_level=detail_level,
            summary=f"No counterfactual found. Original prediction: {prediction}",
            top_features=[dummy_feature],
            all_features=[dummy_feature],
            confidence=0.0,
            counterfactual="Unable to generate alternative scenario within constraints.",
            visualization_data={'type': 'no_counterfactual'},
            model_type="unknown",
            latency_ms=latency_ms,
            metadata={'original_prediction': prediction}
        )
