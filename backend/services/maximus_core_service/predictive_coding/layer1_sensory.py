"""Layer 1: Sensory - Event Compression via Variational Autoencoder (VAE)

Predicts: Raw events (seconds)
Inputs: raw_logs + network_packets + syscalls
Representations: Individual events (process spawn, network connect, file access)
Model: Variational Autoencoder (VAE) for compression

Free Energy Principle: Compress high-dimensional events into low-dimensional latent space.
Prediction error = reconstruction error (events that don't fit learned patterns).
"""

import logging
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, Tuple, Optional

logger = logging.getLogger(__name__)


class EventVAE(nn.Module):
    """Variational Autoencoder for event compression.

    Compresses high-dimensional event vectors (e.g., 10k features) into
    64D latent representations, learning normal patterns.

    High reconstruction error = anomalous event (high prediction error).
    """

    def __init__(
        self,
        input_dim: int = 10000,
        hidden_dims: list = [1024, 256],
        latent_dim: int = 64
    ):
        """Initialize Event VAE.

        Args:
            input_dim: Dimensionality of input events (e.g., one-hot encoded features)
            hidden_dims: Hidden layer dimensions for encoder/decoder
            latent_dim: Dimensionality of latent space (default 64)
        """
        super(EventVAE, self).__init__()

        self.input_dim = input_dim
        self.latent_dim = latent_dim

        # Encoder layers
        encoder_layers = []
        in_dim = input_dim

        for h_dim in hidden_dims:
            encoder_layers.extend([
                nn.Linear(in_dim, h_dim),
                nn.BatchNorm1d(h_dim),
                nn.ReLU(),
                nn.Dropout(0.2)
            ])
            in_dim = h_dim

        self.encoder = nn.Sequential(*encoder_layers)

        # Latent space parameters
        self.fc_mu = nn.Linear(hidden_dims[-1], latent_dim)
        self.fc_logvar = nn.Linear(hidden_dims[-1], latent_dim)

        # Decoder layers
        decoder_layers = []
        in_dim = latent_dim

        for h_dim in reversed(hidden_dims):
            decoder_layers.extend([
                nn.Linear(in_dim, h_dim),
                nn.BatchNorm1d(h_dim),
                nn.ReLU(),
                nn.Dropout(0.2)
            ])
            in_dim = h_dim

        decoder_layers.append(nn.Linear(in_dim, input_dim))
        decoder_layers.append(nn.Sigmoid())  # Output probabilities

        self.decoder = nn.Sequential(*decoder_layers)

        logger.info(f"EventVAE initialized: {input_dim}D → {latent_dim}D latent")

    def encode(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Encode input to latent distribution parameters.

        Args:
            x: Input event tensor [batch_size, input_dim]

        Returns:
            (mu, logvar): Mean and log variance of latent distribution
        """
        h = self.encoder(x)
        mu = self.fc_mu(h)
        logvar = self.fc_logvar(h)
        return mu, logvar

    def reparameterize(self, mu: torch.Tensor, logvar: torch.Tensor) -> torch.Tensor:
        """Reparameterization trick for VAE training.

        z = mu + sigma * epsilon, where epsilon ~ N(0, 1)

        Args:
            mu: Mean tensor
            logvar: Log variance tensor

        Returns:
            Sampled latent vector z
        """
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std

    def decode(self, z: torch.Tensor) -> torch.Tensor:
        """Decode latent vector to event reconstruction.

        Args:
            z: Latent vector [batch_size, latent_dim]

        Returns:
            Reconstructed event [batch_size, input_dim]
        """
        return self.decoder(z)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """Forward pass through VAE.

        Args:
            x: Input event tensor [batch_size, input_dim]

        Returns:
            (z, x_reconstructed, mu, logvar, prediction_error):
                - z: Latent representation
                - x_reconstructed: Reconstruction
                - mu: Latent mean
                - logvar: Latent log variance
                - prediction_error: Per-sample reconstruction error
        """
        # Encode
        mu, logvar = self.encode(x)

        # Sample latent vector
        z = self.reparameterize(mu, logvar)

        # Decode
        x_reconstructed = self.decode(z)

        # Compute prediction error (reconstruction error)
        prediction_error = F.binary_cross_entropy(
            x_reconstructed, x, reduction='none'
        ).sum(dim=1)  # Sum over features, keep batch dimension

        return z, x_reconstructed, mu, logvar, prediction_error

    def compute_loss(
        self,
        x: torch.Tensor,
        x_reconstructed: torch.Tensor,
        mu: torch.Tensor,
        logvar: torch.Tensor,
        beta: float = 1.0
    ) -> Tuple[torch.Tensor, Dict[str, float]]:
        """Compute VAE loss (ELBO).

        Loss = Reconstruction Loss + β * KL Divergence

        Args:
            x: Original input
            x_reconstructed: Reconstructed output
            mu: Latent mean
            logvar: Latent log variance
            beta: KL divergence weight (default 1.0, beta-VAE for β>1)

        Returns:
            (total_loss, loss_dict): Total loss and individual components
        """
        # Reconstruction loss (Binary Cross Entropy)
        recon_loss = F.binary_cross_entropy(x_reconstructed, x, reduction='sum')

        # KL Divergence: KL(q(z|x) || p(z)) where p(z) = N(0, I)
        # KL = -0.5 * sum(1 + log(sigma^2) - mu^2 - sigma^2)
        kl_div = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())

        # Total loss
        total_loss = recon_loss + beta * kl_div

        loss_dict = {
            'total_loss': total_loss.item(),
            'reconstruction_loss': recon_loss.item(),
            'kl_divergence': kl_div.item(),
            'beta': beta
        }

        return total_loss, loss_dict


class SensoryLayer:
    """Layer 1 of Hierarchical Predictive Coding Network.

    Compresses raw events into latent representations and detects
    anomalies via reconstruction error (prediction error).
    """

    def __init__(
        self,
        input_dim: int = 10000,
        latent_dim: int = 64,
        device: str = 'cpu',
        anomaly_threshold: float = 3.0
    ):
        """Initialize Sensory Layer.

        Args:
            input_dim: Event feature dimensionality
            latent_dim: Latent space dimensionality
            device: Device for computation ('cpu' or 'cuda')
            anomaly_threshold: Z-score threshold for anomaly detection
        """
        self.device = torch.device(device)
        self.latent_dim = latent_dim
        self.anomaly_threshold = anomaly_threshold

        # VAE model
        self.vae = EventVAE(
            input_dim=input_dim,
            hidden_dims=[1024, 256],
            latent_dim=latent_dim
        ).to(self.device)

        # Prediction error statistics (for anomaly detection)
        self.error_mean = 0.0
        self.error_std = 1.0
        self.error_history = []

        logger.info(f"SensoryLayer initialized on {device}")

    def predict(self, event: np.ndarray) -> Dict:
        """Predict event representation and detect anomalies.

        Args:
            event: Event feature vector [input_dim]

        Returns:
            Dictionary with:
                - latent_z: Compressed representation
                - reconstruction: Predicted event
                - prediction_error: Reconstruction error
                - is_anomalous: Boolean anomaly flag
                - anomaly_score: Z-score of prediction error
        """
        self.vae.eval()

        with torch.no_grad():
            # Convert to tensor
            x = torch.FloatTensor(event).unsqueeze(0).to(self.device)

            # Forward pass
            z, x_recon, mu, logvar, pred_error = self.vae(x)

            # Compute anomaly score (z-score)
            error_value = pred_error.item()

            if self.error_std > 0:
                z_score = abs((error_value - self.error_mean) / self.error_std)
            else:
                z_score = 0.0

            is_anomalous = z_score > self.anomaly_threshold

            # Update error statistics
            self.error_history.append(error_value)
            if len(self.error_history) > 1000:
                self.error_history = self.error_history[-1000:]

            self.error_mean = np.mean(self.error_history)
            self.error_std = np.std(self.error_history)

            return {
                'latent_z': z.cpu().numpy()[0],  # [latent_dim]
                'reconstruction': x_recon.cpu().numpy()[0],  # [input_dim]
                'prediction_error': error_value,
                'is_anomalous': is_anomalous,
                'anomaly_score': z_score
            }

    def train_step(
        self,
        events_batch: np.ndarray,
        optimizer: torch.optim.Optimizer,
        beta: float = 1.0
    ) -> Dict[str, float]:
        """Single training step.

        Args:
            events_batch: Batch of events [batch_size, input_dim]
            optimizer: PyTorch optimizer
            beta: KL divergence weight

        Returns:
            Dictionary of loss components
        """
        self.vae.train()

        # Convert to tensor
        x = torch.FloatTensor(events_batch).to(self.device)

        # Forward pass
        z, x_recon, mu, logvar, pred_error = self.vae(x)

        # Compute loss
        loss, loss_dict = self.vae.compute_loss(x, x_recon, mu, logvar, beta=beta)

        # Backward pass
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        return loss_dict

    def save_model(self, path: str):
        """Save VAE model checkpoint."""
        torch.save({
            'vae_state_dict': self.vae.state_dict(),
            'error_mean': self.error_mean,
            'error_std': self.error_std,
            'latent_dim': self.latent_dim
        }, path)
        logger.info(f"Model saved to {path}")

    def load_model(self, path: str):
        """Load VAE model checkpoint."""
        checkpoint = torch.load(path, map_location=self.device)
        self.vae.load_state_dict(checkpoint['vae_state_dict'])
        self.error_mean = checkpoint['error_mean']
        self.error_std = checkpoint['error_std']
        logger.info(f"Model loaded from {path}")
