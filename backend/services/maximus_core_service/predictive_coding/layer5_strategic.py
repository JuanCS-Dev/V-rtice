"""Layer 5: Strategic - Transformer for Threat Landscape Evolution

Predicts: Threat landscape evolution (weeks/months)
Inputs: L4_predictions + external_intel_feeds
Representations: APT campaigns, zero-day emergence, geopolitical events
Model: Transformer with temporal attention

Free Energy Principle: Model global threat landscape and strategic trends.
Prediction error = unexpected threat landscape shifts (emerging APTs, zero-days).
"""

import logging

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

logger = logging.getLogger(__name__)


class StrategicTransformer(nn.Module):
    """Transformer for strategic threat landscape prediction (weeks/months ahead).

    Models long-term trends: APT campaigns, zero-day emergence, geopolitical threats.
    """

    def __init__(
        self,
        input_dim: int = 64,  # From L4 tactical representations
        d_model: int = 512,
        nhead: int = 8,
        num_layers: int = 6,
        output_dim: int = 64,
        num_apt_groups: int = 50,
        num_cve_categories: int = 20,
        dropout: float = 0.1,
    ):
        """Initialize Strategic Transformer.

        Args:
            input_dim: Input feature dimensionality
            d_model: Transformer model dimensionality
            nhead: Number of attention heads
            num_layers: Number of transformer layers
            output_dim: Output embedding dimensionality
            num_apt_groups: Number of APT groups to track
            num_cve_categories: Number of CVE/zero-day categories
            dropout: Dropout probability
        """
        super(StrategicTransformer, self).__init__()

        self.d_model = d_model

        # Input embedding
        self.embedding = nn.Linear(input_dim, d_model)

        # Positional encoding
        self.pos_encoder = PositionalEncoding(d_model, dropout)

        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=d_model * 4,
            dropout=dropout,
            activation="gelu",
            batch_first=True,
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

        # Prediction heads
        self.landscape_predictor = nn.Linear(d_model, output_dim)
        self.apt_classifier = nn.Linear(d_model, num_apt_groups)
        self.cve_predictor = nn.Linear(d_model, num_cve_categories)
        self.risk_estimator = nn.Linear(d_model, 1)  # Global risk score

        self.dropout = nn.Dropout(dropout)

        logger.info(
            f"StrategicTransformer initialized: {input_dim}D → {output_dim}D "
            f"(d_model={d_model}, heads={nhead}, layers={num_layers})"
        )

    def forward(
        self, sequence: torch.Tensor, mask: torch.Tensor | None = None
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """Forward pass.

        Args:
            sequence: Input sequence [batch, seq_len, input_dim]
            mask: Optional attention mask

        Returns:
            (landscape_pred, apt_probs, cve_probs, risk_score):
                - landscape_pred: Predicted threat landscape [batch, output_dim]
                - apt_probs: APT group probabilities [batch, num_apt_groups]
                - cve_probs: Zero-day/CVE probabilities [batch, num_cve_categories]
                - risk_score: Global risk score [batch, 1]
        """
        # Embed and add positional encoding
        x = self.embedding(sequence) * np.sqrt(self.d_model)
        x = self.pos_encoder(x)

        # Transformer encoding
        encoded = self.transformer(x, mask=mask)  # [batch, seq_len, d_model]

        # Use final timestep for predictions
        final_state = encoded[:, -1, :]  # [batch, d_model]
        final_state = self.dropout(final_state)

        # Predictions
        landscape_pred = self.landscape_predictor(final_state)
        apt_logits = self.apt_classifier(final_state)
        cve_logits = self.cve_predictor(final_state)
        risk_score = torch.sigmoid(self.risk_estimator(final_state))

        return landscape_pred, apt_logits, cve_logits, risk_score


class PositionalEncoding(nn.Module):
    """Positional encoding for transformer."""

    def __init__(self, d_model: int, dropout: float = 0.1, max_len: int = 5000):
        super(PositionalEncoding, self).__init__()
        self.dropout = nn.Dropout(p=dropout)

        # Compute positional encodings
        position = torch.arange(max_len).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2) * (-np.log(10000.0) / d_model))

        pe = torch.zeros(1, max_len, d_model)
        pe[0, :, 0::2] = torch.sin(position * div_term)
        pe[0, :, 1::2] = torch.cos(position * div_term)

        self.register_buffer("pe", pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Add positional encoding.

        Args:
            x: Input tensor [batch, seq_len, d_model]

        Returns:
            Tensor with positional encoding added
        """
        x = x + self.pe[:, : x.size(1), :]
        return self.dropout(x)


class StrategicLayer:
    """Layer 5 of Hierarchical Predictive Coding Network.

    Predicts threat landscape evolution over weeks/months using transformer.
    Detects emerging APT groups, zero-day trends, geopolitical threats.
    """

    def __init__(
        self,
        latent_dim: int = 64,
        device: str = "cpu",
        prediction_horizon_weeks: int = 12,
    ):
        """Initialize Strategic Layer.

        Args:
            latent_dim: Latent space dimensionality
            device: Computation device
            prediction_horizon_weeks: How many weeks ahead to predict
        """
        self.device = torch.device(device)
        self.latent_dim = latent_dim
        self.prediction_horizon = prediction_horizon_weeks

        # Transformer model
        self.transformer = StrategicTransformer(
            input_dim=latent_dim,
            d_model=512,
            nhead=8,
            num_layers=6,
            output_dim=latent_dim,
            num_apt_groups=50,
            num_cve_categories=20,
            dropout=0.1,
        ).to(self.device)

        logger.info(f"StrategicLayer initialized (horizon={prediction_horizon_weeks} weeks)")

    def predict(self, event_sequence: np.ndarray) -> dict:
        """Predict threat landscape evolution.

        Args:
            event_sequence: Sequence of L4 embeddings [seq_len, latent_dim]

        Returns:
            Dictionary with strategic predictions
        """
        self.transformer.eval()

        with torch.no_grad():
            sequence = torch.FloatTensor(event_sequence).unsqueeze(0).to(self.device)

            landscape_pred, apt_logits, cve_logits, risk_score = self.transformer(sequence)

            # APT probabilities
            apt_probs = F.softmax(apt_logits, dim=1)
            top_apts = torch.topk(apt_probs[0], k=5)

            # CVE probabilities
            cve_probs = torch.sigmoid(cve_logits)  # Multi-label
            top_cves = torch.topk(cve_probs[0], k=5)

            return {
                "threat_landscape_embedding": landscape_pred.cpu().numpy()[0],
                "global_risk_score": risk_score.cpu().numpy()[0, 0],
                "top_apt_groups": [
                    {
                        "id": int(top_apts.indices[i]),
                        "name": self._get_apt_name(int(top_apts.indices[i])),
                        "probability": float(top_apts.values[i]),
                    }
                    for i in range(5)
                ],
                "top_cve_categories": [
                    {
                        "id": int(top_cves.indices[i]),
                        "category": self._get_cve_category(int(top_cves.indices[i])),
                        "probability": float(top_cves.values[i]),
                    }
                    for i in range(5)
                ],
                "prediction_horizon_weeks": self.prediction_horizon,
            }

    def assess_strategic_risk(self, event_sequence: np.ndarray, risk_threshold: float = 0.75) -> dict:
        """Assess strategic threat landscape risk.

        Args:
            event_sequence: Sequence of L4 embeddings
            risk_threshold: Threshold for high risk classification

        Returns:
            Strategic risk assessment
        """
        prediction = self.predict(event_sequence)

        risk_score = prediction["global_risk_score"]
        is_high_risk = risk_score > risk_threshold

        # Get top threats
        top_apt = prediction["top_apt_groups"][0]["name"]
        top_cve = prediction["top_cve_categories"][0]["category"]

        assessment = {
            "strategic_risk": ("HIGH" if is_high_risk else "MODERATE" if risk_score > 0.5 else "LOW"),
            "risk_score": float(risk_score),
            "emerging_apt_groups": [apt["name"] for apt in prediction["top_apt_groups"][:3]],
            "emerging_vulnerabilities": [cve["category"] for cve in prediction["top_cve_categories"][:3]],
            "primary_threat": top_apt,
            "primary_vulnerability": top_cve,
            "recommendation": self._generate_recommendation(is_high_risk, top_apt, top_cve),
        }

        return assessment

    def _get_apt_name(self, apt_id: int) -> str:
        """Map APT ID to group name."""
        apts = [
            "APT1",
            "APT3",
            "APT28",
            "APT29",
            "APT32",
            "APT33",
            "APT34",
            "APT37",
            "APT38",
            "APT39",
            "APT41",
            "CARBANAK",
            "COBALT_GROUP",
            "DARKHOTEL",
            "EQUATION_GROUP",
            "FIN4",
            "FIN6",
            "FIN7",
            "FIN8",
            "LAZARUS_GROUP",
            "LEVIATHAN",
            "MAGECARТ",
            "MENUPASS",
            "MUDDYWATER",
            "OCEANLOTUS",
            "SANDWORM",
            "SOFACY",
            "STRIDER",
            "TURLA",
            "WINNTI",
            "DRAGONFLY",
            "ENERGETIC_BEAR",
            "PUTTER_PANDA",
            "AXIOM",
            "SHELL_CREW",
            "DEEP_PANDA",
            "BRONZE_BUTLER",
            "THREAT_GROUP_3390",
            "NAIKON",
            "LOTUS_BLOSSOM",
            "ELDERWOOD",
            "NITRO",
            "VOLATILE_CEDAR",
            "CHARMING_KITTEN",
            "CLEAVER",
            "COPYKITTENS",
            "DUST_STORM",
            "IRON_TIGER",
            "KE3CHANG",
            "MOAFEE",
        ]
        return apts[apt_id] if apt_id < len(apts) else f"APT_UNKNOWN_{apt_id}"

    def _get_cve_category(self, cve_id: int) -> str:
        """Map CVE ID to vulnerability category."""
        categories = [
            "REMOTE_CODE_EXECUTION",
            "PRIVILEGE_ESCALATION",
            "AUTHENTICATION_BYPASS",
            "SQL_INJECTION",
            "XSS",
            "CSRF",
            "BUFFER_OVERFLOW",
            "USE_AFTER_FREE",
            "MEMORY_CORRUPTION",
            "INFORMATION_DISCLOSURE",
            "DENIAL_OF_SERVICE",
            "DIRECTORY_TRAVERSAL",
            "XXE",
            "DESERIALIZATION",
            "COMMAND_INJECTION",
            "RACE_CONDITION",
            "CRYPTO_WEAKNESS",
            "SSRF",
            "IDOR",
            "ZERO_DAY_EXPLOIT",
        ]
        return categories[cve_id] if cve_id < len(categories) else f"CVE_CAT_{cve_id}"

    def _generate_recommendation(self, is_high_risk: bool, top_apt: str, top_cve: str) -> str:
        """Generate strategic recommendation."""
        if is_high_risk:
            return (
                f"URGENT: Elevated threat from {top_apt}. Prioritize patching {top_cve} "
                f"vulnerabilities. Increase monitoring and threat hunting activities."
            )
        return (
            f"Monitor {top_apt} activity. Review defenses against {top_cve} exploits. "
            f"Maintain standard security posture."
        )

    def train_step(
        self,
        sequence_batch: torch.Tensor,
        target_landscapes: torch.Tensor,
        target_apts: torch.Tensor,
        target_cves: torch.Tensor,
        target_risks: torch.Tensor,
        optimizer: torch.optim.Optimizer,
    ) -> dict[str, float]:
        """Single training step."""
        self.transformer.train()

        sequence_batch = sequence_batch.to(self.device)
        target_landscapes = target_landscapes.to(self.device)
        target_apts = target_apts.to(self.device)
        target_cves = target_cves.to(self.device)
        target_risks = target_risks.to(self.device)

        # Forward
        landscape_pred, apt_logits, cve_logits, risk_score = self.transformer(sequence_batch)

        # Losses
        pred_loss = F.mse_loss(landscape_pred, target_landscapes)
        apt_loss = F.cross_entropy(apt_logits, target_apts)
        cve_loss = F.binary_cross_entropy(torch.sigmoid(cve_logits), target_cves)
        risk_loss = F.mse_loss(risk_score, target_risks)

        total_loss = pred_loss + apt_loss + cve_loss + risk_loss

        # Backward
        optimizer.zero_grad()
        total_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.transformer.parameters(), max_norm=1.0)
        optimizer.step()

        return {
            "total_loss": total_loss.item(),
            "prediction_loss": pred_loss.item(),
            "apt_loss": apt_loss.item(),
            "cve_loss": cve_loss.item(),
            "risk_loss": risk_loss.item(),
        }

    def save_model(self, path: str):
        """Save model checkpoint."""
        torch.save(
            {
                "transformer_state_dict": self.transformer.state_dict(),
                "latent_dim": self.latent_dim,
                "prediction_horizon": self.prediction_horizon,
            },
            path,
        )
        logger.info(f"Model saved to {path}")

    def load_model(self, path: str):
        """Load model checkpoint."""
        checkpoint = torch.load(path, map_location=self.device)
        self.transformer.load_state_dict(checkpoint["transformer_state_dict"])
        logger.info(f"Model saved to {path}")
