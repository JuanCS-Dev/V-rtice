"""Layer 3: Operational - Temporal Convolutional Network for Threat Prediction

Predicts: Immediate threats (hours)
Inputs: L2_predictions + real-time telemetry
Representations: Active reconnaissance, exploitation attempts, attack progression
Model: Temporal Convolutional Network (TCN)

Free Energy Principle: Predict threat evolution over hours using temporal patterns.
Prediction error = unexpected threat progression (novel attack patterns).
"""

import logging

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

logger = logging.getLogger(__name__)


class TemporalBlock(nn.Module):
    """Temporal convolution block with dilated causal convolutions."""

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int,
        stride: int,
        dilation: int,
        dropout: float = 0.2,
    ):
        """Initialize Temporal Block.

        Args:
            in_channels: Input channels
            out_channels: Output channels
            kernel_size: Convolution kernel size
            stride: Convolution stride
            dilation: Dilation rate for causal convolution
            dropout: Dropout probability
        """
        super(TemporalBlock, self).__init__()

        # Causal padding: pad only on the left (past)
        self.padding = (kernel_size - 1) * dilation

        self.conv1 = nn.Conv1d(
            in_channels,
            out_channels,
            kernel_size,
            stride=stride,
            padding=self.padding,
            dilation=dilation,
        )
        self.bn1 = nn.BatchNorm1d(out_channels)
        self.relu1 = nn.ReLU()
        self.dropout1 = nn.Dropout(dropout)

        self.conv2 = nn.Conv1d(
            out_channels,
            out_channels,
            kernel_size,
            stride=stride,
            padding=self.padding,
            dilation=dilation,
        )
        self.bn2 = nn.BatchNorm1d(out_channels)
        self.relu2 = nn.ReLU()
        self.dropout2 = nn.Dropout(dropout)

        # Residual connection
        self.downsample = nn.Conv1d(in_channels, out_channels, 1) if in_channels != out_channels else None

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        Args:
            x: Input tensor [batch, in_channels, seq_len]

        Returns:
            Output tensor [batch, out_channels, seq_len]
        """
        # First convolution
        out = self.conv1(x)

        # Remove future padding (causal)
        if self.padding > 0:
            out = out[:, :, : -self.padding]

        out = self.bn1(out)
        out = self.relu1(out)
        out = self.dropout1(out)

        # Second convolution
        out = self.conv2(out)

        if self.padding > 0:
            out = out[:, :, : -self.padding]

        out = self.bn2(out)
        out = self.relu2(out)
        out = self.dropout2(out)

        # Residual connection
        res = x if self.downsample is None else self.downsample(x)

        # Match sequence lengths
        if res.size(2) != out.size(2):
            res = res[:, :, : out.size(2)]

        return self.relu2(out + res)


class TemporalConvNet(nn.Module):
    """Temporal Convolutional Network for sequence prediction."""

    def __init__(
        self,
        num_inputs: int,
        num_channels: list[int],
        kernel_size: int = 3,
        dropout: float = 0.2,
    ):
        """Initialize TCN.

        Args:
            num_inputs: Input feature dimensionality
            num_channels: List of channel sizes for each layer
            kernel_size: Kernel size for convolutions
            dropout: Dropout probability
        """
        super(TemporalConvNet, self).__init__()

        layers = []
        num_levels = len(num_channels)

        for i in range(num_levels):
            dilation = 2**i  # Exponentially increasing dilation
            in_channels = num_inputs if i == 0 else num_channels[i - 1]
            out_channels = num_channels[i]

            layers.append(
                TemporalBlock(
                    in_channels,
                    out_channels,
                    kernel_size,
                    stride=1,
                    dilation=dilation,
                    dropout=dropout,
                )
            )

        self.network = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        Args:
            x: Input [batch, num_inputs, seq_len]

        Returns:
            Output [batch, num_channels[-1], seq_len]
        """
        return self.network(x)


class OperationalTCN(nn.Module):
    """TCN for operational threat prediction (hours ahead).

    Predicts immediate threats based on temporal patterns in behavioral data.
    """

    def __init__(
        self,
        input_dim: int = 64,  # From L2 behavioral representations
        hidden_channels: list[int] = [128, 128, 64],
        output_dim: int = 64,
        num_threat_classes: int = 15,  # Threat types
        kernel_size: int = 3,
        dropout: float = 0.2,
    ):
        """Initialize Operational TCN.

        Args:
            input_dim: Input feature dimensionality (from L2)
            hidden_channels: TCN hidden channel sizes
            output_dim: Output embedding dimensionality
            num_threat_classes: Number of threat categories
            kernel_size: Convolution kernel size
            dropout: Dropout probability
        """
        super(OperationalTCN, self).__init__()

        self.tcn = TemporalConvNet(
            num_inputs=input_dim,
            num_channels=hidden_channels,
            kernel_size=kernel_size,
            dropout=dropout,
        )

        # Prediction heads
        self.threat_predictor = nn.Linear(hidden_channels[-1], output_dim)
        self.threat_classifier = nn.Linear(hidden_channels[-1], num_threat_classes)
        self.severity_estimator = nn.Linear(hidden_channels[-1], 1)  # Severity score

        logger.info(f"OperationalTCN initialized: {input_dim}D → {output_dim}D")

    def forward(self, sequence: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Forward pass.

        Args:
            sequence: Input sequence [batch, seq_len, input_dim]

        Returns:
            (next_threat_pred, threat_classes, severity):
                - next_threat_pred: Predicted next threat [batch, output_dim]
                - threat_classes: Threat type probabilities [batch, num_threat_classes]
                - severity: Threat severity score [batch, 1]
        """
        # TCN expects [batch, features, time]
        x = sequence.permute(0, 2, 1)

        # Temporal convolutions
        features = self.tcn(x)  # [batch, channels, seq_len]

        # Use final timestep for prediction
        final_features = features[:, :, -1]  # [batch, channels]

        # Predictions
        next_threat = self.threat_predictor(final_features)
        threat_classes = self.threat_classifier(final_features)
        severity = torch.sigmoid(self.severity_estimator(final_features))  # 0-1 score

        return next_threat, threat_classes, severity


class OperationalLayer:
    """Layer 3 of Hierarchical Predictive Coding Network.

    Predicts immediate threats (1-6 hours) using temporal patterns.
    Detects active reconnaissance, exploitation attempts, attack progression.
    """

    def __init__(
        self,
        latent_dim: int = 64,
        device: str = "cpu",
        prediction_horizon_hours: int = 6,
    ):
        """Initialize Operational Layer.

        Args:
            latent_dim: Latent space dimensionality (from L2)
            device: Computation device
            prediction_horizon_hours: How many hours ahead to predict
        """
        self.device = torch.device(device)
        self.latent_dim = latent_dim
        self.prediction_horizon = prediction_horizon_hours

        # TCN model
        self.tcn = OperationalTCN(
            input_dim=latent_dim,
            hidden_channels=[128, 128, 64],
            output_dim=latent_dim,
            num_threat_classes=15,
            kernel_size=3,
            dropout=0.2,
        ).to(self.device)

        # Prediction error tracking
        self.error_history = []
        self.error_mean = 0.0
        self.error_std = 1.0

        logger.info(f"OperationalLayer initialized on {device} (horizon={prediction_horizon_hours}h)")

    def predict(self, event_sequence: np.ndarray, return_all_steps: bool = False) -> dict:
        """Predict immediate threats from event sequence.

        Args:
            event_sequence: Sequence of L2 embeddings [seq_len, latent_dim]
            return_all_steps: If True, return predictions for all timesteps

        Returns:
            Dictionary with predictions and threat assessments
        """
        self.tcn.eval()

        with torch.no_grad():
            # Convert to tensor [1, seq_len, latent_dim]
            sequence = torch.FloatTensor(event_sequence).unsqueeze(0).to(self.device)

            # Forward pass
            next_threat, threat_classes, severity = self.tcn(sequence)

            # Threat type probabilities
            threat_probs = F.softmax(threat_classes, dim=1)

            # Most likely threat
            most_likely_threat_id = threat_probs.argmax(dim=1).item()
            threat_confidence = threat_probs[0, most_likely_threat_id].item()

            return {
                "next_threat_embedding": next_threat.cpu().numpy()[0],
                "threat_type_id": most_likely_threat_id,
                "threat_type_confidence": threat_confidence,
                "threat_probabilities": threat_probs.cpu().numpy()[0],
                "severity_score": severity.cpu().numpy()[0, 0],
                "prediction_horizon_hours": self.prediction_horizon,
            }

    def predict_attack_progression(self, event_sequence: np.ndarray, num_future_steps: int = 10) -> list[dict]:
        """Predict multi-step attack progression.

        Args:
            event_sequence: Sequence of L2 embeddings [seq_len, latent_dim]
            num_future_steps: Number of future steps to predict

        Returns:
            List of predictions for each future timestep
        """
        self.tcn.eval()

        predictions = []
        current_sequence = torch.FloatTensor(event_sequence).to(self.device)

        with torch.no_grad():
            for step in range(num_future_steps):
                # Predict next threat
                sequence_input = current_sequence.unsqueeze(0)
                next_threat, threat_classes, severity = self.tcn(sequence_input)

                # Store prediction
                threat_probs = F.softmax(threat_classes, dim=1)
                most_likely = threat_probs.argmax(dim=1).item()

                predictions.append(
                    {
                        "step": step + 1,
                        "threat_type_id": most_likely,
                        "threat_confidence": threat_probs[0, most_likely].item(),
                        "severity_score": severity.cpu().numpy()[0, 0],
                    }
                )

                # Append prediction to sequence for next iteration
                current_sequence = torch.cat([current_sequence, next_threat.unsqueeze(0)], dim=0)

                # Keep only last N timesteps
                if current_sequence.size(0) > event_sequence.shape[0]:
                    current_sequence = current_sequence[-event_sequence.shape[0] :]

        return predictions

    def detect_attack_indicators(self, event_sequence: np.ndarray, severity_threshold: float = 0.7) -> dict:
        """Detect attack indicators (reconnaissance, exploitation).

        Args:
            event_sequence: Sequence of L2 embeddings
            severity_threshold: Minimum severity for alert

        Returns:
            Dictionary with attack indicators
        """
        prediction = self.predict(event_sequence)

        is_high_severity = prediction["severity_score"] > severity_threshold
        is_high_confidence = prediction["threat_type_confidence"] > 0.8

        indicators = {
            "attack_likely": is_high_severity and is_high_confidence,
            "severity_score": prediction["severity_score"],
            "threat_type": self._get_threat_name(prediction["threat_type_id"]),
            "confidence": prediction["threat_type_confidence"],
            "alert_level": self._determine_alert_level(
                prediction["severity_score"], prediction["threat_type_confidence"]
            ),
        }

        return indicators

    def _get_threat_name(self, threat_id: int) -> str:
        """Map threat ID to human-readable name."""
        threat_names = [
            "BENIGN",
            "RECONNAISSANCE",
            "EXPLOITATION",
            "PRIVILEGE_ESCALATION",
            "LATERAL_MOVEMENT",
            "DATA_EXFILTRATION",
            "RANSOMWARE",
            "DDOS",
            "PHISHING",
            "MALWARE_DELIVERY",
            "C2_COMMUNICATION",
            "PERSISTENCE",
            "DEFENSE_EVASION",
            "CREDENTIAL_ACCESS",
            "DISCOVERY",
        ]

        if 0 <= threat_id < len(threat_names):
            return threat_names[threat_id]
        return f"UNKNOWN_{threat_id}"

    def _determine_alert_level(self, severity: float, confidence: float) -> str:
        """Determine alert level based on severity and confidence."""
        combined_score = severity * confidence

        if combined_score >= 0.8:
            return "CRITICAL"
        if combined_score >= 0.6:
            return "HIGH"
        if combined_score >= 0.4:
            return "MEDIUM"
        return "LOW"

    def train_step(
        self,
        sequence_batch: torch.Tensor,
        target_threats: torch.Tensor,
        target_classes: torch.Tensor,
        target_severity: torch.Tensor,
        optimizer: torch.optim.Optimizer,
    ) -> dict[str, float]:
        """Single training step.

        Args:
            sequence_batch: Batch of sequences [batch, seq_len, latent_dim]
            target_threats: Target next threat embeddings [batch, latent_dim]
            target_classes: Target threat classes [batch]
            target_severity: Target severity scores [batch, 1]
            optimizer: PyTorch optimizer

        Returns:
            Loss components
        """
        self.tcn.train()

        sequence_batch = sequence_batch.to(self.device)
        target_threats = target_threats.to(self.device)
        target_classes = target_classes.to(self.device)
        target_severity = target_severity.to(self.device)

        # Forward pass
        next_threat, threat_classes, severity = self.tcn(sequence_batch)

        # Compute losses
        pred_loss = F.mse_loss(next_threat, target_threats)
        class_loss = F.cross_entropy(threat_classes, target_classes)
        severity_loss = F.mse_loss(severity, target_severity)

        # Combined loss
        total_loss = pred_loss + class_loss + 0.5 * severity_loss

        # Backward pass
        optimizer.zero_grad()
        total_loss.backward()
        optimizer.step()

        return {
            "total_loss": total_loss.item(),
            "prediction_loss": pred_loss.item(),
            "classification_loss": class_loss.item(),
            "severity_loss": severity_loss.item(),
        }

    def save_model(self, path: str):
        """Save TCN model checkpoint."""
        torch.save(
            {
                "tcn_state_dict": self.tcn.state_dict(),
                "error_mean": self.error_mean,
                "error_std": self.error_std,
                "latent_dim": self.latent_dim,
                "prediction_horizon": self.prediction_horizon,
            },
            path,
        )
        logger.info(f"Model saved to {path}")

    def load_model(self, path: str):
        """Load TCN model checkpoint."""
        checkpoint = torch.load(path, map_location=self.device)
        self.tcn.load_state_dict(checkpoint["tcn_state_dict"])
        self.error_mean = checkpoint["error_mean"]
        self.error_std = checkpoint["error_std"]
        logger.info(f"Model loaded from {path}")
