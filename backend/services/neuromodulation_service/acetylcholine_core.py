"""Neuromodulation Service - Production-Ready Acetylcholine Module

Bio-inspired acetylcholine modulator that implements:
1. **Prediction Error from hPC**
   - Receives prediction errors from hierarchical Predictive Coding
   - Tracks novelty and unexpectedness
   - Drives attention allocation

2. **Attention Gain Computation**
   - Computes attention gain for stimuli
   - High prediction error → High attention
   - Modulates sensory processing

3. **Transformer Attention Integration**
   - Modulates attention weights in Transformers
   - Scales attention scores based on novelty
   - Enhances processing of unexpected inputs

Like biological acetylcholine: Modulates attention and learning based on surprise.
NO MOCKS - Production-ready implementation.
"""

import logging
import math
from datetime import datetime
from typing import Dict, Any, Optional, List
from collections import deque
import numpy as np

logger = logging.getLogger(__name__)


class AcetylcholineCore:
    """Production-ready Acetylcholine module for attention modulation.

    Computes attention gain based on prediction errors:
    - High prediction error → High attention gain (novelty detection)
    - Low prediction error → Low attention gain (familiar stimuli)
    """

    def __init__(
        self,
        base_attention_gain: float = 1.0,
        min_gain: float = 0.1,
        max_gain: float = 10.0,
        prediction_error_window: int = 100
    ):
        """Initialize Acetylcholine Core.

        Args:
            base_attention_gain: Base attention gain multiplier
            min_gain: Minimum attention gain
            max_gain: Maximum attention gain
            prediction_error_window: Window size for prediction error history
        """
        self.base_gain = base_attention_gain
        self.min_gain = min_gain
        self.max_gain = max_gain

        self.current_gain = base_attention_gain
        self.prediction_error_history: deque = deque(maxlen=prediction_error_window)
        self.attention_allocation: Dict[str, float] = {}  # stimulus_id -> attention weight

        self.last_modulation_time: Optional[datetime] = None
        self.modulation_count = 0

        logger.info(
            f"AcetylcholineCore initialized (base_gain={base_attention_gain}, "
            f"range=[{min_gain}, {max_gain}])"
        )

    def compute_prediction_error_from_hpc(
        self,
        predicted: np.ndarray,
        actual: np.ndarray,
        layer: str = "L1"
    ) -> float:
        """Compute prediction error from hierarchical Predictive Coding.

        In hPC, prediction error flows bottom-up:
        PE = actual - predicted

        Args:
            predicted: Predicted sensory input from hPC
            actual: Actual sensory input
            layer: Predictive coding layer (L1, L2, etc.)

        Returns:
            Prediction error magnitude
        """
        # Compute prediction error (L2 norm)
        pe_vector = actual - predicted
        pe_magnitude = np.linalg.norm(pe_vector)

        # Normalize by input magnitude
        input_magnitude = np.linalg.norm(actual)
        normalized_pe = pe_magnitude / (input_magnitude + 1e-8)

        # Store in history
        self.prediction_error_history.append({
            'timestamp': datetime.now().isoformat(),
            'layer': layer,
            'pe_magnitude': pe_magnitude,
            'normalized_pe': normalized_pe
        })

        logger.debug(
            f"Prediction error computed (layer={layer}): {normalized_pe:.4f}"
        )

        return normalized_pe

    def compute_attention_gain(
        self,
        prediction_error: float,
        context_confidence: float = 0.5
    ) -> float:
        """Compute attention gain based on prediction error.

        Strategy:
        - High PE → High gain (focus on novelty)
        - Low PE → Low gain (ignore familiar)
        - Context confidence modulates sensitivity

        Args:
            prediction_error: Prediction error from hPC
            context_confidence: Confidence in current context (0-1)

        Returns:
            Attention gain multiplier
        """
        # Normalize prediction error by recent history
        if len(self.prediction_error_history) > 10:
            pe_std = self._compute_pe_std()
            normalized_pe = min(1.0, prediction_error / (3 * pe_std))  # 3-sigma
        else:
            normalized_pe = min(1.0, prediction_error)

        # Compute gain (logarithmic scale for wide dynamic range)
        # Low confidence → more sensitive to prediction errors
        sensitivity = 1.0 - 0.5 * context_confidence

        log_gain = math.log(self.base_gain) + \
                   (math.log(self.max_gain) - math.log(self.base_gain)) * \
                   normalized_pe * sensitivity

        gain = math.exp(log_gain)
        gain = max(self.min_gain, min(self.max_gain, gain))

        self.current_gain = gain
        self.last_modulation_time = datetime.now()
        self.modulation_count += 1

        logger.info(
            f"Attention gain computed: {gain:.2f} (PE={prediction_error:.4f}, "
            f"confidence={context_confidence:.2f})"
        )

        return gain

    def _compute_pe_std(self) -> float:
        """Compute standard deviation of recent prediction errors.

        Returns:
            Standard deviation of prediction errors
        """
        if len(self.prediction_error_history) < 2:
            return 1.0

        pe_values = [entry['normalized_pe'] for entry in self.prediction_error_history]
        mean_pe = sum(pe_values) / len(pe_values)
        variance = sum((x - mean_pe) ** 2 for x in pe_values) / len(pe_values)

        return math.sqrt(variance)

    def modulate_transformer_attention(
        self,
        attention_scores: np.ndarray,
        prediction_errors: Optional[np.ndarray] = None,
        stimulus_ids: Optional[List[str]] = None
    ) -> np.ndarray:
        """Modulate Transformer attention weights based on prediction errors.

        Args:
            attention_scores: Original attention scores (shape: [seq_len, seq_len])
            prediction_errors: Prediction errors for each token (shape: [seq_len])
            stimulus_ids: Optional stimulus IDs for tracking

        Returns:
            Modulated attention scores
        """
        if prediction_errors is None:
            return attention_scores

        # Compute attention gains for each token
        gains = np.array([
            self.compute_attention_gain(pe) for pe in prediction_errors
        ])

        # Apply gains to attention scores (broadcast)
        # High PE tokens receive more attention
        modulated_scores = attention_scores * gains[:, np.newaxis]

        # Track attention allocation
        if stimulus_ids is not None:
            for i, stimulus_id in enumerate(stimulus_ids):
                self.attention_allocation[stimulus_id] = float(gains[i])

        logger.debug(
            f"Transformer attention modulated: gain_range=[{gains.min():.2f}, {gains.max():.2f}]"
        )

        return modulated_scores

    def allocate_attention_to_stimuli(
        self,
        stimuli: Dict[str, np.ndarray],
        predictions: Dict[str, np.ndarray]
    ) -> Dict[str, float]:
        """Allocate attention across multiple stimuli based on prediction errors.

        Args:
            stimuli: Dictionary of stimulus_id -> actual input
            predictions: Dictionary of stimulus_id -> predicted input

        Returns:
            Dictionary of stimulus_id -> attention weight (0-1, normalized)
        """
        attention_weights = {}

        # Compute prediction error for each stimulus
        for stimulus_id in stimuli:
            if stimulus_id in predictions:
                pe = self.compute_prediction_error_from_hpc(
                    predictions[stimulus_id],
                    stimuli[stimulus_id]
                )
                gain = self.compute_attention_gain(pe)
                attention_weights[stimulus_id] = gain
            else:
                # Unknown stimulus = high attention
                attention_weights[stimulus_id] = self.max_gain

        # Normalize to sum to 1.0 (softmax-like)
        total_weight = sum(attention_weights.values())
        if total_weight > 0:
            normalized_weights = {
                k: v / total_weight for k, v in attention_weights.items()
            }
        else:
            # Uniform distribution
            normalized_weights = {
                k: 1.0 / len(attention_weights) for k in attention_weights
            }

        self.attention_allocation = normalized_weights

        logger.info(
            f"Attention allocated across {len(stimuli)} stimuli: "
            f"max={max(normalized_weights.values()):.3f}"
        )

        return normalized_weights

    def get_prediction_error_statistics(self, window: int = 100) -> Dict[str, Any]:
        """Get prediction error statistics.

        Args:
            window: Window size for statistics

        Returns:
            Prediction error statistics
        """
        if not self.prediction_error_history:
            return {'count': 0}

        recent = list(self.prediction_error_history)[-window:]

        pe_values = [entry['normalized_pe'] for entry in recent]
        mean_pe = sum(pe_values) / len(pe_values)

        return {
            'count': len(recent),
            'mean_pe': mean_pe,
            'std_pe': self._compute_pe_std(),
            'min_pe': min(pe_values),
            'max_pe': max(pe_values)
        }

    async def get_status(self) -> Dict[str, Any]:
        """Get Acetylcholine module status.

        Returns:
            Status dictionary
        """
        stats = self.get_prediction_error_statistics()

        return {
            'status': 'operational',
            'current_gain': self.current_gain,
            'base_gain': self.base_gain,
            'gain_range': [self.min_gain, self.max_gain],
            'modulation_count': self.modulation_count,
            'last_modulation': self.last_modulation_time.isoformat() if self.last_modulation_time else 'N/A',
            'attention_allocation': self.attention_allocation,
            'prediction_error_statistics': stats
        }
