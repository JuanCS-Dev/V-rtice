"""Hierarchical Predictive Coding (hPC) Network - Main Orchestrator

Integrates all 5 layers into a unified predictive system based on the Free Energy Principle.
Implements top-down predictions and bottom-up prediction errors for learning.

Layers:
1. Sensory (VAE) - Raw events (seconds)
2. Behavioral (GNN) - Process/network patterns (minutes)
3. Operational (TCN) - Immediate threats (hours)
4. Tactical (LSTM) - Attack campaigns (days)
5. Strategic (Transformer) - Threat landscape (weeks/months)

Free Energy Minimization: System learns to predict future states and acts to minimize surprise.
"""

import logging

import numpy as np

from .layer1_sensory import SensoryLayer
from .layer2_behavioral import BehavioralLayer, EventGraph
from .layer3_operational import OperationalLayer
from .layer4_tactical import TacticalLayer
from .layer5_strategic import StrategicLayer

logger = logging.getLogger(__name__)


class HierarchicalPredictiveCodingNetwork:
    """Main hPC Network coordinating all 5 layers.

    Implements hierarchical predictive coding with top-down predictions
    and bottom-up prediction errors.
    """

    def __init__(self, latent_dim: int = 64, device: str = "cpu"):
        """Initialize hPC Network.

        Args:
            latent_dim: Latent space dimensionality (consistent across layers)
            device: Computation device ('cpu' or 'cuda')
        """
        self.latent_dim = latent_dim
        self.device = device

        # Initialize all 5 layers
        self.l1_sensory = SensoryLayer(input_dim=10000, latent_dim=latent_dim, device=device)

        self.l2_behavioral = BehavioralLayer(latent_dim=latent_dim, device=device)

        self.l3_operational = OperationalLayer(latent_dim=latent_dim, device=device, prediction_horizon_hours=6)

        self.l4_tactical = TacticalLayer(latent_dim=latent_dim, device=device, prediction_horizon_days=7)

        self.l5_strategic = StrategicLayer(latent_dim=latent_dim, device=device, prediction_horizon_weeks=12)

        # Prediction error buffers
        self.prediction_errors = {"l1": [], "l2": [], "l3": [], "l4": [], "l5": []}

        logger.info(f"hPC Network initialized with {latent_dim}D latent space on {device}")

    def hierarchical_inference(
        self,
        raw_event: np.ndarray,
        event_graph: EventGraph | None = None,
        l2_sequence: np.ndarray | None = None,
        l3_sequence: np.ndarray | None = None,
        l4_sequence: np.ndarray | None = None,
    ) -> dict:
        """Perform hierarchical inference through all layers.

        Bottom-up flow: Raw event → L1 → L2 → L3 → L4 → L5

        Args:
            raw_event: Raw event vector for L1
            event_graph: Event graph for L2 (optional)
            l2_sequence: Sequence of L2 embeddings for L3 (optional)
            l3_sequence: Sequence of L3 embeddings for L4 (optional)
            l4_sequence: Sequence of L4 embeddings for L5 (optional)

        Returns:
            Dictionary with predictions from all layers
        """
        results = {}

        # Layer 1: Sensory - Event compression
        l1_output = self.l1_sensory.predict(raw_event)
        results["l1_sensory"] = l1_output

        # Layer 2: Behavioral - Graph patterns (if graph provided)
        if event_graph is not None:
            l2_output = self.l2_behavioral.predict(event_graph)
            results["l2_behavioral"] = l2_output
        else:
            results["l2_behavioral"] = None

        # Layer 3: Operational - Threat prediction (if sequence provided)
        if l2_sequence is not None:
            l3_output = self.l3_operational.predict(l2_sequence)
            results["l3_operational"] = l3_output
        else:
            results["l3_operational"] = None

        # Layer 4: Tactical - Campaign prediction (if sequence provided)
        if l3_sequence is not None:
            l4_output = self.l4_tactical.predict(l3_sequence)
            results["l4_tactical"] = l4_output
        else:
            results["l4_tactical"] = None

        # Layer 5: Strategic - Landscape prediction (if sequence provided)
        if l4_sequence is not None:
            l5_output = self.l5_strategic.predict(l4_sequence)
            results["l5_strategic"] = l5_output
        else:
            results["l5_strategic"] = None

        return results

    def compute_free_energy(self, predictions: dict, ground_truth: dict | None = None) -> dict[str, float]:
        """Compute Free Energy (prediction error) for each layer.

        Free Energy ≈ Prediction Error = surprise

        Args:
            predictions: Predictions from hierarchical_inference()
            ground_truth: Ground truth values for each layer (if available)

        Returns:
            Dictionary of free energy scores per layer
        """
        free_energy = {}

        if ground_truth is None:
            # Use reconstruction error as proxy
            if predictions["l1_sensory"] is not None:
                free_energy["l1"] = predictions["l1_sensory"]["prediction_error"]
            else:
                free_energy["l1"] = 0.0

            # Higher layers: use default
            free_energy.update({"l2": 0.0, "l3": 0.0, "l4": 0.0, "l5": 0.0})
        else:
            # Compute per-layer prediction errors
            for layer in ["l1", "l2", "l3", "l4", "l5"]:
                if f"{layer}_pred" in predictions and layer in ground_truth:
                    pred = predictions[f"{layer}_pred"]
                    truth = ground_truth[layer]
                    error = np.mean((pred - truth) ** 2)
                    free_energy[layer] = float(error)
                else:
                    free_energy[layer] = 0.0

        # Store in buffers
        for layer, error in free_energy.items():
            self.prediction_errors[layer].append(error)
            if len(self.prediction_errors[layer]) > 1000:
                self.prediction_errors[layer] = self.prediction_errors[layer][-1000:]

        return free_energy

    def get_unified_threat_assessment(self, predictions: dict) -> dict:
        """Generate unified threat assessment from all layers.

        Combines predictions from all layers into single assessment.

        Args:
            predictions: Predictions from hierarchical_inference()

        Returns:
            Unified threat assessment
        """
        assessment = {
            "timestamp": None,
            "threat_level": "LOW",
            "confidence": 0.0,
            "findings": [],
        }

        # Layer 1: Anomalies
        if predictions["l1_sensory"] and predictions["l1_sensory"]["is_anomalous"]:
            assessment["findings"].append(
                {
                    "layer": "SENSORY",
                    "type": "ANOMALY",
                    "score": predictions["l1_sensory"]["anomaly_score"],
                }
            )

        # Layer 2: Behavioral patterns
        if predictions["l2_behavioral"] and predictions["l2_behavioral"]["is_anomalous"].any():
            assessment["findings"].append(
                {
                    "layer": "BEHAVIORAL",
                    "type": "ANOMALOUS_PATTERN",
                    "affected_nodes": int(predictions["l2_behavioral"]["is_anomalous"].sum()),
                }
            )

        # Layer 3: Operational threats
        if predictions["l3_operational"]:
            severity = predictions["l3_operational"]["severity_score"]
            if severity > 0.7:
                assessment["findings"].append(
                    {
                        "layer": "OPERATIONAL",
                        "type": predictions["l3_operational"].get("threat_type", "UNKNOWN"),
                        "severity": float(severity),
                    }
                )

        # Layer 4: Tactical campaigns
        if predictions["l4_tactical"]:
            persistence = predictions["l4_tactical"]["persistence_score"]
            if persistence > 0.7:
                assessment["findings"].append(
                    {
                        "layer": "TACTICAL",
                        "type": "APT_CAMPAIGN",
                        "persistence": float(persistence),
                    }
                )

        # Layer 5: Strategic risk
        if predictions["l5_strategic"]:
            risk = predictions["l5_strategic"]["global_risk_score"]
            if risk > 0.75:
                assessment["findings"].append(
                    {
                        "layer": "STRATEGIC",
                        "type": "ELEVATED_RISK",
                        "risk_score": float(risk),
                    }
                )

        # Determine overall threat level
        if len(assessment["findings"]) >= 3:
            assessment["threat_level"] = "CRITICAL"
            assessment["confidence"] = 0.95
        elif len(assessment["findings"]) >= 2:
            assessment["threat_level"] = "HIGH"
            assessment["confidence"] = 0.80
        elif len(assessment["findings"]) >= 1:
            assessment["threat_level"] = "MEDIUM"
            assessment["confidence"] = 0.65
        else:
            assessment["threat_level"] = "LOW"
            assessment["confidence"] = 0.50

        return assessment

    def save_all_models(self, base_path: str):
        """Save all layer models."""
        self.l1_sensory.save_model(f"{base_path}/l1_sensory.pt")
        self.l2_behavioral.save_model(f"{base_path}/l2_behavioral.pt")
        self.l3_operational.save_model(f"{base_path}/l3_operational.pt")
        self.l4_tactical.save_model(f"{base_path}/l4_tactical.pt")
        self.l5_strategic.save_model(f"{base_path}/l5_strategic.pt")
        logger.info(f"All models saved to {base_path}")

    def load_all_models(self, base_path: str):
        """Load all layer models."""
        self.l1_sensory.load_model(f"{base_path}/l1_sensory.pt")
        self.l2_behavioral.load_model(f"{base_path}/l2_behavioral.pt")
        self.l3_operational.load_model(f"{base_path}/l3_operational.pt")
        self.l4_tactical.load_model(f"{base_path}/l4_tactical.pt")
        self.l5_strategic.load_model(f"{base_path}/l5_strategic.pt")
        logger.info(f"All models loaded from {base_path}")
