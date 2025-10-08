"""
Training Script for Layer 1 (Sensory) - VAE

Trains a Variational Autoencoder for sensory compression:
- Input: 128-dim feature vector (from preprocessed events)
- Latent: 64-dim compressed representation
- Output: 128-dim reconstruction

Architecture:
- Encoder: 128 -> 96 -> 64 (mean + logvar)
- Decoder: 64 -> 96 -> 128

Loss: Reconstruction loss (MSE) + KL divergence

REGRA DE OURO: Zero mocks, production-ready training
Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

import argparse
import logging
from pathlib import Path
from typing import Any

import numpy as np

# Try to import torch
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torch.utils.data import DataLoader, TensorDataset

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logging.warning("PyTorch not available, training will not work")

from training.layer_trainer import LayerTrainer, TrainingConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# MODEL DEFINITION
# =============================================================================

if TORCH_AVAILABLE:

    class Layer1VAE(nn.Module):
        """Variational Autoencoder for Layer 1 (Sensory).

        Compresses 128-dim sensory features to 64-dim latent representation.

        Based on:
        - Kingma & Welling (2014): Auto-Encoding Variational Bayes
        - Applied to cybersecurity event compression
        """

        def __init__(self, input_dim: int = 128, hidden_dim: int = 96, latent_dim: int = 64, dropout: float = 0.2):
            """Initialize VAE.

            Args:
                input_dim: Input feature dimension (128)
                hidden_dim: Hidden layer dimension (96)
                latent_dim: Latent representation dimension (64)
                dropout: Dropout rate for regularization
            """
            super().__init__()

            self.input_dim = input_dim
            self.latent_dim = latent_dim

            # Encoder
            self.encoder = nn.Sequential(
                nn.Linear(input_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(hidden_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout),
            )

            # Latent parameters
            self.fc_mean = nn.Linear(hidden_dim, latent_dim)
            self.fc_logvar = nn.Linear(hidden_dim, latent_dim)

            # Decoder
            self.decoder = nn.Sequential(
                nn.Linear(latent_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(hidden_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(hidden_dim, input_dim),
                nn.Sigmoid(),  # Assuming features are normalized to [0, 1]
            )

            # Initialize weights
            self._initialize_weights()

        def _initialize_weights(self):
            """Initialize network weights using Xavier initialization."""
            for m in self.modules():
                if isinstance(m, nn.Linear):
                    nn.init.xavier_uniform_(m.weight)
                    if m.bias is not None:
                        nn.init.constant_(m.bias, 0)

        def encode(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
            """Encode input to latent parameters.

            Args:
                x: Input tensor (batch_size, input_dim)

            Returns:
                Tuple of (mean, logvar) each (batch_size, latent_dim)
            """
            hidden = self.encoder(x)
            mean = self.fc_mean(hidden)
            logvar = self.fc_logvar(hidden)
            return mean, logvar

        def reparameterize(self, mean: torch.Tensor, logvar: torch.Tensor) -> torch.Tensor:
            """Reparameterization trick for VAE.

            Args:
                mean: Mean tensor (batch_size, latent_dim)
                logvar: Log variance tensor (batch_size, latent_dim)

            Returns:
                Sampled latent vector (batch_size, latent_dim)
            """
            std = torch.exp(0.5 * logvar)
            eps = torch.randn_like(std)
            return mean + eps * std

        def decode(self, z: torch.Tensor) -> torch.Tensor:
            """Decode latent vector to reconstruction.

            Args:
                z: Latent vector (batch_size, latent_dim)

            Returns:
                Reconstruction (batch_size, input_dim)
            """
            return self.decoder(z)

        def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
            """Forward pass.

            Args:
                x: Input tensor (batch_size, input_dim)

            Returns:
                Tuple of (reconstruction, mean, logvar)
            """
            mean, logvar = self.encode(x)
            z = self.reparameterize(mean, logvar)
            reconstruction = self.decode(z)
            return reconstruction, mean, logvar

        def get_latent(self, x: torch.Tensor) -> torch.Tensor:
            """Get latent representation (for inference).

            Args:
                x: Input tensor (batch_size, input_dim)

            Returns:
                Latent representation (batch_size, latent_dim)
            """
            mean, _ = self.encode(x)
            return mean

    # =============================================================================
    # LOSS FUNCTION
    # =============================================================================

    def vae_loss_fn(model: Layer1VAE, batch: tuple[torch.Tensor, torch.Tensor], beta: float = 1.0) -> torch.Tensor:
        """VAE loss function: Reconstruction + KL divergence.

        Loss = MSE(x, x_reconstructed) + beta * KL(q(z|x) || p(z))

        Args:
            model: VAE model
            batch: Tuple of (features, labels) - labels ignored for VAE
            beta: Weight for KL term (beta-VAE)

        Returns:
            Total loss
        """
        features, _ = batch

        # Forward pass
        reconstruction, mean, logvar = model(features)

        # Reconstruction loss (MSE)
        reconstruction_loss = F.mse_loss(reconstruction, features, reduction="mean")

        # KL divergence loss
        # KL(q(z|x) || N(0, I)) = -0.5 * sum(1 + logvar - mean^2 - exp(logvar))
        kl_loss = -0.5 * torch.sum(1 + logvar - mean.pow(2) - logvar.exp(), dim=1)
        kl_loss = kl_loss.mean()

        # Total loss
        total_loss = reconstruction_loss + beta * kl_loss

        return total_loss

    # =============================================================================
    # METRICS
    # =============================================================================

    def reconstruction_error_metric(model: Layer1VAE, batch: tuple[torch.Tensor, torch.Tensor]) -> float:
        """Compute reconstruction error (MSE).

        Args:
            model: VAE model
            batch: Tuple of (features, labels)

        Returns:
            MSE reconstruction error
        """
        features, _ = batch
        reconstruction, _, _ = model(features)
        mse = F.mse_loss(reconstruction, features)
        return mse.item()

    def kl_divergence_metric(model: Layer1VAE, batch: tuple[torch.Tensor, torch.Tensor]) -> float:
        """Compute KL divergence.

        Args:
            model: VAE model
            batch: Tuple of (features, labels)

        Returns:
            KL divergence
        """
        features, _ = batch
        _, mean, logvar = model(features)
        kl = -0.5 * torch.sum(1 + logvar - mean.pow(2) - logvar.exp(), dim=1)
        return kl.mean().item()


# =============================================================================
# TRAINING FUNCTION
# =============================================================================


def train_layer1_vae(
    train_features: np.ndarray,
    train_labels: np.ndarray,
    val_features: np.ndarray | None = None,
    val_labels: np.ndarray | None = None,
    config: TrainingConfig | None = None,
    beta: float = 1.0,
) -> tuple[Any, dict[str, Any]]:
    """Train Layer 1 VAE.

    Args:
        train_features: Training features (N, 128)
        train_labels: Training labels (N,) - ignored for VAE
        val_features: Optional validation features
        val_labels: Optional validation labels
        config: Training configuration
        beta: Beta-VAE weight for KL term

    Returns:
        Tuple of (trained_model, training_history)
    """
    if not TORCH_AVAILABLE:
        logger.error("PyTorch not available, cannot train")
        return None, {}

    # Default config
    if config is None:
        config = TrainingConfig(
            model_name="layer1_vae",
            layer_name="layer1",
            batch_size=32,
            num_epochs=100,
            learning_rate=1e-3,
            early_stopping_patience=10,
        )

    logger.info(f"Training Layer 1 VAE: {len(train_features)} training samples")

    # Create datasets
    train_dataset = TensorDataset(torch.FloatTensor(train_features), torch.LongTensor(train_labels))

    train_loader = DataLoader(train_dataset, batch_size=config.batch_size, shuffle=True, num_workers=4, pin_memory=True)

    val_loader = None
    if val_features is not None:
        val_dataset = TensorDataset(torch.FloatTensor(val_features), torch.LongTensor(val_labels))

        val_loader = DataLoader(
            val_dataset, batch_size=config.batch_size, shuffle=False, num_workers=4, pin_memory=True
        )

    # Create model
    model = Layer1VAE(input_dim=train_features.shape[1], hidden_dim=96, latent_dim=64, dropout=0.2)

    # Create loss function with beta
    def loss_fn(m, batch):
        return vae_loss_fn(m, batch, beta=beta)

    # Metrics
    metrics = {"reconstruction_error": reconstruction_error_metric, "kl_divergence": kl_divergence_metric}

    # Create trainer
    trainer = LayerTrainer(model=model, loss_fn=loss_fn, config=config, metric_fns=metrics)

    # Train
    history = trainer.train(train_loader, val_loader)

    return model, {
        "history": history,
        "config": config,
        "best_val_loss": trainer.best_val_loss,
        "best_epoch": trainer.best_epoch,
    }


# =============================================================================
# CLI
# =============================================================================


def main():
    """Main training script."""
    parser = argparse.ArgumentParser(description="Train Layer 1 VAE for Sensory Compression")

    # Data
    parser.add_argument("--train_data", type=str, required=True, help="Path to training data (.npz)")
    parser.add_argument("--val_data", type=str, default=None, help="Path to validation data (.npz)")

    # Model
    parser.add_argument("--latent_dim", type=int, default=64, help="Latent dimension")
    parser.add_argument("--hidden_dim", type=int, default=96, help="Hidden dimension")
    parser.add_argument("--beta", type=float, default=1.0, help="Beta-VAE weight for KL term")

    # Training
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size")
    parser.add_argument("--num_epochs", type=int, default=100, help="Number of epochs")
    parser.add_argument("--learning_rate", type=float, default=1e-3, help="Learning rate")
    parser.add_argument("--early_stopping_patience", type=int, default=10, help="Early stopping patience")

    # Checkpoints
    parser.add_argument("--checkpoint_dir", type=str, default="training/checkpoints", help="Checkpoint directory")
    parser.add_argument("--log_dir", type=str, default="training/logs", help="Log directory")

    args = parser.parse_args()

    # Load data
    logger.info(f"Loading training data from {args.train_data}")
    train_data = np.load(args.train_data)
    train_features = train_data["features"]
    train_labels = train_data.get("labels", np.zeros(len(train_features)))

    val_features, val_labels = None, None
    if args.val_data:
        logger.info(f"Loading validation data from {args.val_data}")
        val_data = np.load(args.val_data)
        val_features = val_data["features"]
        val_labels = val_data.get("labels", np.zeros(len(val_features)))

    # Create config
    config = TrainingConfig(
        model_name="layer1_vae",
        layer_name="layer1",
        batch_size=args.batch_size,
        num_epochs=args.num_epochs,
        learning_rate=args.learning_rate,
        early_stopping_patience=args.early_stopping_patience,
        checkpoint_dir=Path(args.checkpoint_dir),
        log_dir=Path(args.log_dir),
    )

    # Train
    model, results = train_layer1_vae(
        train_features=train_features,
        train_labels=train_labels,
        val_features=val_features,
        val_labels=val_labels,
        config=config,
        beta=args.beta,
    )

    logger.info("Training complete!")
    logger.info(f"Best validation loss: {results['best_val_loss']:.4f} at epoch {results['best_epoch']}")

    # Save final model
    if TORCH_AVAILABLE and model is not None:
        final_model_path = Path(args.checkpoint_dir) / "layer1_vae_final.pt"
        torch.save(model.state_dict(), final_model_path)
        logger.info(f"Final model saved to {final_model_path}")


if __name__ == "__main__":
    main()
