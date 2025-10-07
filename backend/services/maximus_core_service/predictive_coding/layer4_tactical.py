"""Layer 4: Tactical - Bidirectional LSTM for Campaign Prediction

Predicts: Attack campaigns (days)
Inputs: L3_predictions + historical_incidents
Representations: Multi-stage attack TTPs, lateral movement patterns, APT campaigns
Model: Bidirectional LSTM with memory cells

Free Energy Principle: Model long-term attack patterns and campaign progression.
Prediction error = unexpected campaign evolution (novel TTPs).
"""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

logger = logging.getLogger(__name__)


class TacticalLSTM(nn.Module):
    """Bidirectional LSTM for tactical threat prediction (days ahead).

    Models multi-day attack campaigns, lateral movement, APT TTPs.
    """

    def __init__(
        self,
        input_dim: int = 64,  # From L3 operational representations
        hidden_dim: int = 256,
        num_layers: int = 2,
        output_dim: int = 64,
        num_campaign_types: int = 20,
        dropout: float = 0.3,
    ):
        """Initialize Tactical LSTM.

        Args:
            input_dim: Input feature dimensionality
            hidden_dim: LSTM hidden state size
            num_layers: Number of LSTM layers
            output_dim: Output embedding dimensionality
            num_campaign_types: Number of campaign categories (APT groups, TTPs)
            dropout: Dropout probability
        """
        super(TacticalLSTM, self).__init__()

        self.hidden_dim = hidden_dim
        self.num_layers = num_layers

        # Bidirectional LSTM
        self.lstm = nn.LSTM(
            input_dim,
            hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if num_layers > 1 else 0,
        )

        # Prediction heads
        lstm_output_dim = hidden_dim * 2  # Bidirectional
        self.campaign_predictor = nn.Linear(lstm_output_dim, output_dim)
        self.campaign_classifier = nn.Linear(lstm_output_dim, num_campaign_types)
        self.ttp_detector = nn.Linear(lstm_output_dim, 50)  # MITRE ATT&CK tactics
        self.persistence_score = nn.Linear(lstm_output_dim, 1)

        self.dropout = nn.Dropout(dropout)

        logger.info(
            f"TacticalLSTM initialized: {input_dim}D → {output_dim}D "
            f"(hidden={hidden_dim}, layers={num_layers})"
        )

    def forward(
        self,
        sequence: torch.Tensor,
        hidden: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, Tuple]:
        """Forward pass.

        Args:
            sequence: Input sequence [batch, seq_len, input_dim]
            hidden: Optional initial hidden state

        Returns:
            (campaign_pred, campaign_class, ttp_scores, persistence, hidden):
                - campaign_pred: Predicted next campaign state [batch, output_dim]
                - campaign_class: Campaign type probabilities [batch, num_campaign_types]
                - ttp_scores: MITRE ATT&CK tactic scores [batch, 50]
                - persistence: Campaign persistence score [batch, 1]
                - hidden: Final LSTM hidden state
        """
        # LSTM forward
        lstm_out, hidden = self.lstm(sequence, hidden)  # [batch, seq_len, hidden*2]

        # Use final timestep
        final_output = lstm_out[:, -1, :]  # [batch, hidden*2]
        final_output = self.dropout(final_output)

        # Predictions
        campaign_pred = self.campaign_predictor(final_output)
        campaign_class = self.campaign_classifier(final_output)
        ttp_scores = torch.sigmoid(self.ttp_detector(final_output))  # Multi-label
        persistence = torch.sigmoid(self.persistence_score(final_output))

        return campaign_pred, campaign_class, ttp_scores, persistence, hidden


class TacticalLayer:
    """Layer 4 of Hierarchical Predictive Coding Network.

    Predicts multi-day attack campaigns using bidirectional LSTM.
    Detects APT patterns, lateral movement, persistent threats.
    """

    def __init__(
        self,
        latent_dim: int = 64,
        device: str = "cpu",
        prediction_horizon_days: int = 7,
    ):
        """Initialize Tactical Layer.

        Args:
            latent_dim: Latent space dimensionality
            device: Computation device
            prediction_horizon_days: How many days ahead to predict
        """
        self.device = torch.device(device)
        self.latent_dim = latent_dim
        self.prediction_horizon = prediction_horizon_days

        # LSTM model
        self.lstm = TacticalLSTM(
            input_dim=latent_dim,
            hidden_dim=256,
            num_layers=2,
            output_dim=latent_dim,
            num_campaign_types=20,
            dropout=0.3,
        ).to(self.device)

        logger.info(
            f"TacticalLayer initialized (horizon={prediction_horizon_days} days)"
        )

    def predict(self, event_sequence: np.ndarray) -> Dict:
        """Predict campaign evolution from event sequence.

        Args:
            event_sequence: Sequence of L3 embeddings [seq_len, latent_dim]

        Returns:
            Dictionary with campaign predictions
        """
        self.lstm.eval()

        with torch.no_grad():
            sequence = torch.FloatTensor(event_sequence).unsqueeze(0).to(self.device)

            campaign_pred, campaign_class, ttp_scores, persistence, _ = self.lstm(
                sequence
            )

            # Campaign type
            campaign_probs = F.softmax(campaign_class, dim=1)
            campaign_id = campaign_probs.argmax(dim=1).item()

            # Top TTPs (MITRE ATT&CK tactics)
            top_ttps = torch.topk(ttp_scores[0], k=5)

            return {
                "next_campaign_embedding": campaign_pred.cpu().numpy()[0],
                "campaign_type_id": campaign_id,
                "campaign_confidence": campaign_probs[0, campaign_id].item(),
                "campaign_probabilities": campaign_probs.cpu().numpy()[0],
                "persistence_score": persistence.cpu().numpy()[0, 0],
                "top_ttp_ids": top_ttps.indices.cpu().numpy().tolist(),
                "top_ttp_scores": top_ttps.values.cpu().numpy().tolist(),
                "prediction_horizon_days": self.prediction_horizon,
            }

    def detect_apt_indicators(
        self, event_sequence: np.ndarray, persistence_threshold: float = 0.7
    ) -> Dict:
        """Detect APT campaign indicators.

        Args:
            event_sequence: Sequence of L3 embeddings
            persistence_threshold: Minimum persistence for APT classification

        Returns:
            APT indicators and campaign assessment
        """
        prediction = self.predict(event_sequence)

        is_apt = prediction["persistence_score"] > persistence_threshold
        campaign_name = self._get_campaign_name(prediction["campaign_type_id"])

        indicators = {
            "apt_likely": is_apt,
            "campaign_type": campaign_name,
            "persistence_score": prediction["persistence_score"],
            "confidence": prediction["campaign_confidence"],
            "ttps": [
                self._get_ttp_name(ttp_id) for ttp_id in prediction["top_ttp_ids"]
            ],
            "severity": "CRITICAL" if is_apt else "MEDIUM",
        }

        return indicators

    def _get_campaign_name(self, campaign_id: int) -> str:
        """Map campaign ID to name."""
        campaigns = [
            "BENIGN",
            "APT29_COZY_BEAR",
            "APT28_FANCY_BEAR",
            "LAZARUS_GROUP",
            "CARBANAK",
            "FIN7",
            "WINNTI",
            "EQUATION_GROUP",
            "TURLA",
            "APT41",
            "SANDWORM",
            "DARKHOTEL",
            "OCEANLOTUS",
            "HAFNIUM",
            "NOBELIUM",
            "STRONTIUM",
            "PLATINUM",
            "GALLIUM",
            "PHOSPHORUS",
            "THALLIUM",
        ]
        return (
            campaigns[campaign_id]
            if campaign_id < len(campaigns)
            else f"UNKNOWN_{campaign_id}"
        )

    def _get_ttp_name(self, ttp_id: int) -> str:
        """Map TTP ID to MITRE ATT&CK tactic."""
        tactics = [
            "Reconnaissance",
            "Resource Development",
            "Initial Access",
            "Execution",
            "Persistence",
            "Privilege Escalation",
            "Defense Evasion",
            "Credential Access",
            "Discovery",
            "Lateral Movement",
            "Collection",
            "Command and Control",
            "Exfiltration",
            "Impact",
        ]
        return tactics[ttp_id] if ttp_id < len(tactics) else f"TTP_{ttp_id}"

    def train_step(
        self,
        sequence_batch: torch.Tensor,
        target_campaigns: torch.Tensor,
        target_classes: torch.Tensor,
        target_ttps: torch.Tensor,
        target_persistence: torch.Tensor,
        optimizer: torch.optim.Optimizer,
    ) -> Dict[str, float]:
        """Single training step."""
        self.lstm.train()

        sequence_batch = sequence_batch.to(self.device)
        target_campaigns = target_campaigns.to(self.device)
        target_classes = target_classes.to(self.device)
        target_ttps = target_ttps.to(self.device)
        target_persistence = target_persistence.to(self.device)

        # Forward
        campaign_pred, campaign_class, ttp_scores, persistence, _ = self.lstm(
            sequence_batch
        )

        # Losses
        pred_loss = F.mse_loss(campaign_pred, target_campaigns)
        class_loss = F.cross_entropy(campaign_class, target_classes)
        ttp_loss = F.binary_cross_entropy(ttp_scores, target_ttps)
        persist_loss = F.mse_loss(persistence, target_persistence)

        total_loss = pred_loss + class_loss + ttp_loss + persist_loss

        # Backward
        optimizer.zero_grad()
        total_loss.backward()
        optimizer.step()

        return {
            "total_loss": total_loss.item(),
            "prediction_loss": pred_loss.item(),
            "classification_loss": class_loss.item(),
            "ttp_loss": ttp_loss.item(),
            "persistence_loss": persist_loss.item(),
        }

    def save_model(self, path: str):
        """Save model checkpoint."""
        torch.save(
            {
                "lstm_state_dict": self.lstm.state_dict(),
                "latent_dim": self.latent_dim,
                "prediction_horizon": self.prediction_horizon,
            },
            path,
        )
        logger.info(f"Model saved to {path}")

    def load_model(self, path: str):
        """Load model checkpoint."""
        checkpoint = torch.load(path, map_location=self.device)
        self.lstm.load_state_dict(checkpoint["lstm_state_dict"])
        logger.info(f"Model loaded from {path}")
