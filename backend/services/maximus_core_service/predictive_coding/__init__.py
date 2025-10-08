"""Hierarchical Predictive Coding Network - Free Energy Minimization

Bio-inspired hierarchical prediction system based on Karl Friston's Free Energy Principle.
Implements 5-layer predictive network that minimizes surprise through prediction and active inference.

Architectural Overview:
====================

```
L5: STRATEGIC (Transformer)
    ↓ Weeks/Months predictions
L4: TACTICAL (Bidirectional LSTM)
    ↓ Days predictions
L3: OPERATIONAL (TCN)
    ↓ Hours predictions
L2: BEHAVIORAL (GNN)
    ↓ Minutes predictions
L1: SENSORY (VAE)
    ↓ Seconds predictions
RAW EVENTS
```

Information Flow:
================

**Bottom-Up (Prediction Errors):**
Raw Events → L1 → L2 → L3 → L4 → L5
Each layer detects what higher layers failed to predict

**Top-Down (Predictions):**
L5 → L4 → L3 → L2 → L1 → Expected Events
Each layer predicts what lower layers should observe

**Learning:**
Minimize Free Energy = minimize prediction error across all layers

Layer Specifications:
====================

**Layer 1: Sensory (VAE)**
- Predicts: Raw events (seconds)
- Model: Variational Autoencoder
- Input: 10k-dimensional event vectors
- Output: 64-dimensional latent representations
- Anomaly: High reconstruction error = unexpected event

**Layer 2: Behavioral (GNN)**
- Predicts: Process/network patterns (minutes)
- Model: Graph Neural Network
- Input: Event graphs from L1
- Output: Behavioral embeddings + event classification
- Anomaly: Unexpected graph patterns (malicious process chains)

**Layer 3: Operational (TCN)**
- Predicts: Immediate threats (hours)
- Model: Temporal Convolutional Network
- Input: L2 behavioral sequences
- Output: Threat predictions + severity scores
- Anomaly: Attack progression indicators

**Layer 4: Tactical (LSTM)**
- Predicts: Attack campaigns (days)
- Model: Bidirectional LSTM
- Input: L3 operational sequences
- Output: Campaign predictions + MITRE ATT&CK TTPs
- Anomaly: APT campaign patterns

**Layer 5: Strategic (Transformer)**
- Predicts: Threat landscape (weeks/months)
- Model: Transformer with temporal attention
- Input: L4 tactical sequences
- Output: APT groups + zero-day trends + global risk
- Anomaly: Emerging threats and landscape shifts

Components:
==========
"""

from .hpc_network import HierarchicalPredictiveCodingNetwork
from .layer1_sensory import EventVAE, SensoryLayer
from .layer2_behavioral import BehavioralGNN, BehavioralLayer, EventGraph
from .layer3_operational import OperationalLayer, OperationalTCN
from .layer4_tactical import TacticalLayer, TacticalLSTM
from .layer5_strategic import StrategicLayer, StrategicTransformer

__all__ = [
    # Main orchestrator
    "HierarchicalPredictiveCodingNetwork",
    # Layer 1
    "SensoryLayer",
    "EventVAE",
    # Layer 2
    "BehavioralLayer",
    "BehavioralGNN",
    "EventGraph",
    # Layer 3
    "OperationalLayer",
    "OperationalTCN",
    # Layer 4
    "TacticalLayer",
    "TacticalLSTM",
    # Layer 5
    "StrategicLayer",
    "StrategicTransformer",
]
