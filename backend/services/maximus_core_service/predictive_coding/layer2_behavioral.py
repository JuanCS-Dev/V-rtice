"""Layer 2: Behavioral - Graph Neural Network for Event Relationships

Predicts: Process/network events (minutes)
Inputs: L1_predictions + enriched logs
Representations: Anomalous process trees, suspicious connections, event graphs
Model: Graph Neural Network (GNN) over event graphs

Free Energy Principle: Model relationships between events as graph structure.
Prediction error = unexpected graph patterns (e.g., anomalous process chains).
"""

import logging
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EventGraph:
    """Event graph representation."""
    node_features: torch.Tensor  # [num_nodes, feature_dim]
    edge_index: torch.Tensor  # [2, num_edges] (source, target pairs)
    edge_features: Optional[torch.Tensor] = None  # [num_edges, edge_feature_dim]
    node_labels: Optional[torch.Tensor] = None  # [num_nodes] ground truth


class GraphConvLayer(nn.Module):
    """Graph Convolutional Layer for message passing."""

    def __init__(self, in_features: int, out_features: int):
        """Initialize Graph Conv Layer.

        Args:
            in_features: Input feature dimensionality
            out_features: Output feature dimensionality
        """
        super(GraphConvLayer, self).__init__()

        self.linear = nn.Linear(in_features, out_features)
        self.activation = nn.ReLU()

    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor
    ) -> torch.Tensor:
        """Forward pass: aggregate neighbor features.

        Args:
            x: Node features [num_nodes, in_features]
            edge_index: Edge connectivity [2, num_edges]

        Returns:
            Updated node features [num_nodes, out_features]
        """
        # Message passing: aggregate features from neighbors
        row, col = edge_index
        num_nodes = x.size(0)

        # Simple mean aggregation (can be replaced with attention)
        aggregated = torch.zeros(num_nodes, x.size(1), device=x.device)

        for i in range(edge_index.size(1)):
            src, dst = row[i], col[i]
            aggregated[dst] += x[src]

        # Normalize by degree
        degree = torch.bincount(col, minlength=num_nodes).float().clamp(min=1)
        aggregated = aggregated / degree.unsqueeze(1)

        # Transform and activate
        out = self.linear(aggregated + x)  # Residual connection
        out = self.activation(out)

        return out


class BehavioralGNN(nn.Module):
    """Graph Neural Network for behavioral event prediction.

    Models relationships between events (e.g., process spawns, network connections)
    to predict next events and detect anomalous patterns.
    """

    def __init__(
        self,
        input_dim: int = 64,  # From L1 latent representations
        hidden_dims: List[int] = [128, 128, 64],
        output_dim: int = 64,  # Predicted next event embedding
        num_classes: int = 10  # Event types (e.g., benign, malware, exploit)
    ):
        """Initialize Behavioral GNN.

        Args:
            input_dim: Node feature dimensionality (from L1)
            hidden_dims: Hidden layer dimensions
            output_dim: Output embedding dimensionality
            num_classes: Number of event classes for classification
        """
        super(BehavioralGNN, self).__init__()

        # Graph convolutional layers
        self.conv_layers = nn.ModuleList()
        in_dim = input_dim

        for h_dim in hidden_dims:
            self.conv_layers.append(GraphConvLayer(in_dim, h_dim))
            in_dim = h_dim

        # Prediction heads
        self.event_predictor = nn.Linear(hidden_dims[-1], output_dim)
        self.event_classifier = nn.Linear(hidden_dims[-1], num_classes)

        # Dropout for regularization
        self.dropout = nn.Dropout(0.3)

        logger.info(f"BehavioralGNN initialized: {input_dim}D → {output_dim}D")

    def forward(
        self,
        node_features: torch.Tensor,
        edge_index: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Forward pass through GNN.

        Args:
            node_features: Node embeddings [num_nodes, input_dim]
            edge_index: Graph connectivity [2, num_edges]

        Returns:
            (node_embeddings, next_event_prediction, event_classification):
                - node_embeddings: Final node representations [num_nodes, hidden_dims[-1]]
                - next_event_prediction: Predicted next event [num_nodes, output_dim]
                - event_classification: Event type probabilities [num_nodes, num_classes]
        """
        x = node_features

        # Graph convolutions
        for conv in self.conv_layers:
            x = conv(x, edge_index)
            x = self.dropout(x)

        node_embeddings = x

        # Predict next event
        next_event = self.event_predictor(x)

        # Classify event types
        event_classes = self.event_classifier(x)

        return node_embeddings, next_event, event_classes


class BehavioralLayer:
    """Layer 2 of Hierarchical Predictive Coding Network.

    Models event relationships as graphs and predicts behavioral patterns.
    Detects anomalous process chains, suspicious network flows, etc.
    """

    def __init__(
        self,
        latent_dim: int = 64,
        device: str = 'cpu',
        anomaly_threshold: float = 0.7
    ):
        """Initialize Behavioral Layer.

        Args:
            latent_dim: Latent space dimensionality (from L1)
            device: Computation device
            anomaly_threshold: Threshold for anomaly classification
        """
        self.device = torch.device(device)
        self.latent_dim = latent_dim
        self.anomaly_threshold = anomaly_threshold

        # GNN model
        self.gnn = BehavioralGNN(
            input_dim=latent_dim,
            hidden_dims=[128, 128, 64],
            output_dim=latent_dim,
            num_classes=10
        ).to(self.device)

        # Prediction error statistics
        self.error_history = []
        self.error_mean = 0.0
        self.error_std = 1.0

        logger.info(f"BehavioralLayer initialized on {device}")

    def predict(self, event_graph: EventGraph) -> Dict:
        """Predict behavioral patterns and detect anomalies.

        Args:
            event_graph: Graph of events with node features from L1

        Returns:
            Dictionary with predictions and anomaly scores
        """
        self.gnn.eval()

        with torch.no_grad():
            node_features = event_graph.node_features.to(self.device)
            edge_index = event_graph.edge_index.to(self.device)

            # Forward pass
            embeddings, next_event_pred, event_classes = self.gnn(
                node_features, edge_index
            )

            # Compute prediction error (if ground truth available)
            if event_graph.node_labels is not None:
                labels = event_graph.node_labels.to(self.device)
                pred_error = F.cross_entropy(event_classes, labels, reduction='none')

                # Anomaly detection via prediction error
                error_mean = pred_error.mean().item()
                anomaly_scores = (pred_error - self.error_mean) / (self.error_std + 1e-8)
                is_anomalous = anomaly_scores > self.anomaly_threshold

                # Update error statistics
                self.error_history.append(error_mean)
                if len(self.error_history) > 500:
                    self.error_history = self.error_history[-500:]

                self.error_mean = np.mean(self.error_history)
                self.error_std = np.std(self.error_history)
            else:
                # No ground truth - use classification confidence
                probs = F.softmax(event_classes, dim=1)
                max_probs, _ = probs.max(dim=1)
                is_anomalous = max_probs < (1.0 - self.anomaly_threshold)
                anomaly_scores = 1.0 - max_probs

            return {
                'node_embeddings': embeddings.cpu().numpy(),
                'next_event_predictions': next_event_pred.cpu().numpy(),
                'event_class_probs': F.softmax(event_classes, dim=1).cpu().numpy(),
                'is_anomalous': is_anomalous.cpu().numpy(),
                'anomaly_scores': anomaly_scores.cpu().numpy()
            }

    def detect_anomalous_chains(
        self,
        event_graph: EventGraph,
        chain_length: int = 5
    ) -> List[List[int]]:
        """Detect anomalous event chains (e.g., suspicious process trees).

        Args:
            event_graph: Graph of events
            chain_length: Maximum chain length to analyze

        Returns:
            List of anomalous node chains (process trees, attack paths)
        """
        prediction = self.predict(event_graph)
        is_anomalous = prediction['is_anomalous']

        # Find anomalous nodes
        anomalous_nodes = np.where(is_anomalous)[0]

        # Trace chains backwards through graph edges
        edge_index = event_graph.edge_index.numpy()
        chains = []

        for node in anomalous_nodes:
            chain = self._trace_chain_backwards(node, edge_index, chain_length)
            if len(chain) >= 2:  # At least 2 events in chain
                chains.append(chain)

        return chains

    def _trace_chain_backwards(
        self,
        node: int,
        edge_index: np.ndarray,
        max_length: int
    ) -> List[int]:
        """Trace event chain backwards from anomalous node.

        Args:
            node: Starting node (anomalous event)
            edge_index: Graph edges [2, num_edges]
            max_length: Maximum chain length

        Returns:
            List of nodes in chain (reversed chronologically)
        """
        chain = [node]
        current = node

        for _ in range(max_length - 1):
            # Find parent nodes (incoming edges)
            parents = edge_index[0][edge_index[1] == current]

            if len(parents) == 0:
                break

            # Take first parent (can be extended to explore all branches)
            current = parents[0]
            chain.append(current)

        return list(reversed(chain))  # Chronological order

    def train_step(
        self,
        event_graph: EventGraph,
        optimizer: torch.optim.Optimizer
    ) -> Dict[str, float]:
        """Single training step.

        Args:
            event_graph: Batch of event graphs with labels
            optimizer: PyTorch optimizer

        Returns:
            Loss components
        """
        self.gnn.train()

        node_features = event_graph.node_features.to(self.device)
        edge_index = event_graph.edge_index.to(self.device)
        labels = event_graph.node_labels.to(self.device)

        # Forward pass
        _, next_event_pred, event_classes = self.gnn(node_features, edge_index)

        # Classification loss
        class_loss = F.cross_entropy(event_classes, labels)

        # Prediction loss (MSE for next event)
        if node_features.size(0) > 1:
            # Predict next event = shift features by 1
            next_events_true = node_features[1:]  # Skip first
            next_event_pred_subset = next_event_pred[:-1]  # Skip last
            pred_loss = F.mse_loss(next_event_pred_subset, next_events_true)
        else:
            pred_loss = torch.tensor(0.0, device=self.device)

        # Total loss
        total_loss = class_loss + 0.5 * pred_loss

        # Backward pass
        optimizer.zero_grad()
        total_loss.backward()
        optimizer.step()

        return {
            'total_loss': total_loss.item(),
            'classification_loss': class_loss.item(),
            'prediction_loss': pred_loss.item()
        }

    def save_model(self, path: str):
        """Save GNN model checkpoint."""
        torch.save({
            'gnn_state_dict': self.gnn.state_dict(),
            'error_mean': self.error_mean,
            'error_std': self.error_std,
            'latent_dim': self.latent_dim
        }, path)
        logger.info(f"Model saved to {path}")

    def load_model(self, path: str):
        """Load GNN model checkpoint."""
        checkpoint = torch.load(path, map_location=self.device)
        self.gnn.load_state_dict(checkpoint['gnn_state_dict'])
        self.error_mean = checkpoint['error_mean']
        self.error_std = checkpoint['error_std']
        logger.info(f"Model loaded from {path}")
