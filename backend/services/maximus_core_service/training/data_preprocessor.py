"""
Data Preprocessor for MAXIMUS Training Pipeline

Layer-specific preprocessing for Predictive Coding Network:
- Layer 1 (VAE): Feature vectorization (sensory compression)
- Layer 2 (GNN): Graph construction (behavioral patterns)
- Layer 3 (TCN): Time series (operational threats)
- Layer 4 (LSTM): Sequence encoding (tactical campaigns)
- Layer 5 (Transformer): Context encoding (strategic landscape)

REGRA DE OURO: Zero mocks, production-ready preprocessing
Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

import hashlib
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class LayerType(Enum):
    """Predictive Coding layers."""

    LAYER1_SENSORY = "layer1_sensory"
    LAYER2_BEHAVIORAL = "layer2_behavioral"
    LAYER3_OPERATIONAL = "layer3_operational"
    LAYER4_TACTICAL = "layer4_tactical"
    LAYER5_STRATEGIC = "layer5_strategic"


@dataclass
class PreprocessedSample:
    """Preprocessed sample for training."""

    sample_id: str
    layer: LayerType
    features: np.ndarray
    label: int | None = None
    metadata: dict[str, Any] | None = None

    def __repr__(self) -> str:
        return f"PreprocessedSample(layer={self.layer.value}, features_shape={self.features.shape}, label={self.label})"


class LayerPreprocessor(ABC):
    """Abstract base class for layer-specific preprocessing."""

    def __init__(self, layer: LayerType):
        """Initialize preprocessor.

        Args:
            layer: Target layer type
        """
        self.layer = layer

    @abstractmethod
    def preprocess(self, event: dict[str, Any]) -> PreprocessedSample:
        """Preprocess event for this layer.

        Args:
            event: Raw event data

        Returns:
            Preprocessed sample
        """
        pass

    @abstractmethod
    def get_feature_dim(self) -> int:
        """Get feature dimensionality for this layer.

        Returns:
            Feature dimension
        """
        pass


class Layer1Preprocessor(LayerPreprocessor):
    """Preprocessor for Layer 1 (Sensory) - VAE input.

    Extracts low-level features:
    - Network features (IPs, ports, protocols)
    - Process features (PIDs, names, paths)
    - File features (hashes, sizes, extensions)
    - User features (UIDs, names, domains)
    """

    def __init__(self):
        """Initialize Layer 1 preprocessor."""
        super().__init__(LayerType.LAYER1_SENSORY)

        # Feature extractors
        self.feature_dim = 128  # Fixed dimension for VAE

        # Vocabulary for categorical encoding
        self.protocol_vocab = {"tcp": 0, "udp": 1, "icmp": 2, "http": 3, "https": 4, "dns": 5}
        self.event_type_vocab = {
            "network_connection": 0,
            "process_creation": 1,
            "file_creation": 2,
            "registry_modification": 3,
            "authentication": 4,
        }

    def preprocess(self, event: dict[str, Any]) -> PreprocessedSample:
        """Preprocess event for Layer 1.

        Args:
            event: Raw event data

        Returns:
            Preprocessed sample with 128-dim feature vector
        """
        features = np.zeros(self.feature_dim, dtype=np.float32)

        # Extract event type (one-hot encoding)
        event_type = event.get("type", event.get("event_type", "unknown"))
        event_type_id = self.event_type_vocab.get(event_type, -1)
        if event_type_id >= 0:
            features[event_type_id] = 1.0

        # Extract network features (indices 10-30)
        if "source_ip" in event:
            features[10:14] = self._encode_ip(event["source_ip"])
        if "dest_ip" in event:
            features[14:18] = self._encode_ip(event["dest_ip"])
        if "source_port" in event:
            features[18] = event["source_port"] / 65535.0  # Normalize
        if "dest_port" in event:
            features[19] = event["dest_port"] / 65535.0
        if "protocol" in event:
            protocol = event["protocol"].lower()
            protocol_id = self.protocol_vocab.get(protocol, -1)
            if protocol_id >= 0:
                features[20 + protocol_id] = 1.0

        # Extract process features (indices 30-50)
        if "process_name" in event:
            features[30:34] = self._encode_string(event["process_name"])
        if "process_pid" in event:
            features[34] = min(event["process_pid"] / 10000.0, 1.0)  # Normalize
        if "parent_process_name" in event:
            features[35:39] = self._encode_string(event["parent_process_name"])

        # Extract file features (indices 50-70)
        if "file_name" in event:
            features[50:54] = self._encode_string(event["file_name"])
        if "file_size" in event:
            features[54] = min(event["file_size"] / 1e9, 1.0)  # Normalize (max 1GB)
        if "file_hash" in event:
            features[55:59] = self._encode_hash(event["file_hash"])

        # Extract user features (indices 70-90)
        if "user_name" in event:
            features[70:74] = self._encode_string(event["user_name"])
        if "user_domain" in event:
            features[74:78] = self._encode_string(event["user_domain"])

        # Timestamp features (indices 90-95)
        if "timestamp" in event:
            timestamp = pd.to_datetime(event["timestamp"])
            features[90] = timestamp.hour / 24.0
            features[91] = timestamp.dayofweek / 7.0
            features[92] = timestamp.day / 31.0

        # Statistical features (indices 95-128) - reserved for future use
        # Can be filled with event-specific statistics

        # Extract label
        label = self._extract_label(event)

        # Generate sample ID
        sample_id = self._generate_sample_id(event)

        return PreprocessedSample(
            sample_id=sample_id,
            layer=self.layer,
            features=features,
            label=label,
            metadata={"event_type": event_type, "timestamp": event.get("timestamp")},
        )

    def get_feature_dim(self) -> int:
        """Get feature dimensionality.

        Returns:
            128 dimensions
        """
        return self.feature_dim

    @staticmethod
    def _encode_ip(ip_str: str) -> np.ndarray:
        """Encode IP address to 4-dim vector.

        Args:
            ip_str: IP address string

        Returns:
            Normalized 4-dim vector
        """
        try:
            octets = [int(x) for x in ip_str.split(".")]
            return np.array(octets, dtype=np.float32) / 255.0
        except:
            return np.zeros(4, dtype=np.float32)

    @staticmethod
    def _encode_string(s: str, dim: int = 4) -> np.ndarray:
        """Encode string to fixed-dim vector using hash.

        Args:
            s: Input string
            dim: Output dimension

        Returns:
            Encoded vector
        """
        hash_bytes = hashlib.md5(s.encode()).digest()
        hash_ints = np.frombuffer(hash_bytes[: dim * 4], dtype=np.int32)
        return (hash_ints % 256).astype(np.float32) / 255.0

    @staticmethod
    def _encode_hash(hash_str: str, dim: int = 4) -> np.ndarray:
        """Encode hash (MD5/SHA256) to fixed-dim vector.

        Args:
            hash_str: Hash string
            dim: Output dimension

        Returns:
            Encoded vector
        """
        try:
            hash_bytes = bytes.fromhex(hash_str[: dim * 8])
            hash_ints = np.frombuffer(hash_bytes[: dim * 4], dtype=np.int32)
            return (hash_ints % 256).astype(np.float32) / 255.0
        except:
            return np.zeros(dim, dtype=np.float32)

    @staticmethod
    def _extract_label(event: dict[str, Any]) -> int | None:
        """Extract label from event.

        Args:
            event: Event data

        Returns:
            Label (0=benign, 1=malicious) or None
        """
        # Check common label fields
        labels = event.get("labels", {})
        if isinstance(labels, dict):
            is_threat = labels.get("is_threat", labels.get("is_malicious"))
            if is_threat is not None:
                return 1 if is_threat else 0

        # Check label field
        label_value = event.get("label")
        if label_value is not None:
            # If label is already an integer, return it
            if isinstance(label_value, (int, np.integer)):
                return int(label_value)

            # If label is a string, parse it
            if isinstance(label_value, str):
                label_str = label_value.lower()
                if "threat" in label_str or "malicious" in label_str or "attack" in label_str:
                    return 1
                if "normal" in label_str or "benign" in label_str:
                    return 0

        return None

    @staticmethod
    def _generate_sample_id(event: dict[str, Any]) -> str:
        """Generate unique sample ID.

        Args:
            event: Event data

        Returns:
            Sample ID
        """
        event_id = event.get("id", event.get("event_id"))
        if event_id:
            return f"l1_{event_id}"

        # Generate from event data
        event_str = str(sorted(event.items()))
        hash_id = hashlib.sha256(event_str.encode()).hexdigest()[:16]
        return f"l1_{hash_id}"


class Layer2Preprocessor(LayerPreprocessor):
    """Preprocessor for Layer 2 (Behavioral) - GNN input.

    Constructs behavior graphs:
    - Nodes: Entities (processes, files, IPs)
    - Edges: Interactions (spawns, reads, connects)
    - Node features: Entity attributes
    - Edge features: Interaction types
    """

    def __init__(self):
        """Initialize Layer 2 preprocessor."""
        super().__init__(LayerType.LAYER2_BEHAVIORAL)

        self.node_feature_dim = 64
        self.edge_feature_dim = 16

    def preprocess(self, event: dict[str, Any]) -> PreprocessedSample:
        """Preprocess event for Layer 2.

        Creates a graph representation:
        - features[0:64]: Source node features
        - features[64:128]: Destination node features
        - features[128:144]: Edge features

        Args:
            event: Raw event data

        Returns:
            Preprocessed sample with graph encoding
        """
        features = np.zeros(self.node_feature_dim * 2 + self.edge_feature_dim, dtype=np.float32)

        # Extract source node (process/user/IP)
        source_features = self._extract_entity_features(
            entity_type="source",
            entity_data={
                "name": event.get("process_name", event.get("user_name", event.get("source_ip"))),
                "id": event.get("process_pid", event.get("source_port")),
                "attributes": event.get("process_attributes", {}),
            },
        )
        features[0 : self.node_feature_dim] = source_features

        # Extract destination node (file/IP/service)
        dest_features = self._extract_entity_features(
            entity_type="destination",
            entity_data={
                "name": event.get("file_name", event.get("dest_ip")),
                "id": event.get("dest_port"),
                "attributes": event.get("file_attributes", {}),
            },
        )
        features[self.node_feature_dim : self.node_feature_dim * 2] = dest_features

        # Extract edge (interaction type)
        edge_features = self._extract_interaction_features(event)
        features[self.node_feature_dim * 2 :] = edge_features

        # Extract label
        label = Layer1Preprocessor._extract_label(event)

        # Generate sample ID
        sample_id = f"l2_{Layer1Preprocessor._generate_sample_id(event)[3:]}"

        return PreprocessedSample(
            sample_id=sample_id,
            layer=self.layer,
            features=features,
            label=label,
            metadata={"event_type": event.get("type")},
        )

    def get_feature_dim(self) -> int:
        """Get feature dimensionality.

        Returns:
            144 dimensions (64+64+16)
        """
        return self.node_feature_dim * 2 + self.edge_feature_dim

    def _extract_entity_features(self, entity_type: str, entity_data: dict[str, Any]) -> np.ndarray:
        """Extract node features for an entity.

        Args:
            entity_type: Entity type (source/destination)
            entity_data: Entity data

        Returns:
            64-dim feature vector
        """
        features = np.zeros(self.node_feature_dim, dtype=np.float32)

        # Encode entity name
        name = entity_data.get("name", "")
        if name:
            features[0:4] = Layer1Preprocessor._encode_string(name, dim=4)

        # Encode entity ID
        entity_id = entity_data.get("id")
        if entity_id:
            features[4] = min(entity_id / 10000.0, 1.0)

        # Entity type indicator
        if entity_type == "source":
            features[5] = 1.0
        else:
            features[6] = 1.0

        # Reserved for additional attributes
        return features

    def _extract_interaction_features(self, event: dict[str, Any]) -> np.ndarray:
        """Extract edge features (interaction type).

        Args:
            event: Event data

        Returns:
            16-dim edge feature vector
        """
        features = np.zeros(self.edge_feature_dim, dtype=np.float32)

        event_type = event.get("type", "unknown")

        # Interaction type encoding
        interaction_types = {
            "network_connection": 0,
            "process_creation": 1,
            "file_creation": 2,
            "file_read": 3,
            "file_write": 4,
            "file_delete": 5,
            "registry_read": 6,
            "registry_write": 7,
        }

        type_id = interaction_types.get(event_type, -1)
        if type_id >= 0:
            features[type_id] = 1.0

        return features


class Layer3Preprocessor(LayerPreprocessor):
    """Preprocessor for Layer 3 (Operational) - TCN input.

    Creates time series features:
    - Sliding window of events (e.g., last 10 events)
    - Temporal patterns
    - Rate of events
    """

    def __init__(self, window_size: int = 10):
        """Initialize Layer 3 preprocessor.

        Args:
            window_size: Number of events in time window
        """
        super().__init__(LayerType.LAYER3_OPERATIONAL)

        self.window_size = window_size
        self.event_feature_dim = 32
        self.event_buffer: list[np.ndarray] = []

    def preprocess(self, event: dict[str, Any]) -> PreprocessedSample:
        """Preprocess event for Layer 3.

        Args:
            event: Raw event data

        Returns:
            Preprocessed sample with time series encoding
        """
        # Extract event features
        event_features = self._extract_event_features(event)

        # Add to buffer
        self.event_buffer.append(event_features)

        # Keep only last window_size events
        if len(self.event_buffer) > self.window_size:
            self.event_buffer = self.event_buffer[-self.window_size :]

        # Pad if needed
        features_list = self.event_buffer.copy()
        while len(features_list) < self.window_size:
            features_list.insert(0, np.zeros(self.event_feature_dim, dtype=np.float32))

        # Stack into time series
        features = np.concatenate(features_list)

        # Extract label
        label = Layer1Preprocessor._extract_label(event)

        # Generate sample ID
        sample_id = f"l3_{Layer1Preprocessor._generate_sample_id(event)[3:]}"

        return PreprocessedSample(
            sample_id=sample_id,
            layer=self.layer,
            features=features,
            label=label,
            metadata={"window_size": len(self.event_buffer)},
        )

    def get_feature_dim(self) -> int:
        """Get feature dimensionality.

        Returns:
            window_size * event_feature_dim (default: 320)
        """
        return self.window_size * self.event_feature_dim

    def _extract_event_features(self, event: dict[str, Any]) -> np.ndarray:
        """Extract features for a single event in time series.

        Args:
            event: Event data

        Returns:
            32-dim event feature vector
        """
        features = np.zeros(self.event_feature_dim, dtype=np.float32)

        # Event type (one-hot)
        event_types = ["network_connection", "process_creation", "file_creation", "authentication"]
        event_type = event.get("type", "unknown")
        if event_type in event_types:
            features[event_types.index(event_type)] = 1.0

        # Timestamp features (hour, day of week)
        if "timestamp" in event:
            timestamp = pd.to_datetime(event["timestamp"])
            features[10] = timestamp.hour / 24.0
            features[11] = timestamp.dayofweek / 7.0

        # Basic event attributes
        if "severity" in event:
            features[12] = event["severity"] / 10.0

        return features


class DataPreprocessor:
    """Main preprocessor that coordinates layer-specific preprocessing.

    Example:
        ```python
        preprocessor = DataPreprocessor(output_dir="training/data/preprocessed")

        # Preprocess for all layers
        samples = preprocessor.preprocess_event(event, layers="all")

        # Preprocess for specific layer
        sample = preprocessor.preprocess_event(event, layers=[LayerType.LAYER1_SENSORY])
        ```
    """

    def __init__(self, output_dir: Path | None = None):
        """Initialize preprocessor.

        Args:
            output_dir: Directory to save preprocessed data
        """
        self.output_dir = Path(output_dir) if output_dir else Path("training/data/preprocessed")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize layer preprocessors
        self.preprocessors: dict[LayerType, LayerPreprocessor] = {
            LayerType.LAYER1_SENSORY: Layer1Preprocessor(),
            LayerType.LAYER2_BEHAVIORAL: Layer2Preprocessor(),
            LayerType.LAYER3_OPERATIONAL: Layer3Preprocessor(),
            # Layer 4 and 5 use Layer 3 output with different aggregations
        }

        logger.info(f"DataPreprocessor initialized with {len(self.preprocessors)} layer preprocessors")

    def preprocess_event(
        self, event: dict[str, Any], layers: str | list[LayerType] = "all"
    ) -> PreprocessedSample | dict[LayerType, PreprocessedSample]:
        """Preprocess event for specified layers.

        Args:
            event: Raw event data
            layers: Target layers ("all" or list of LayerType)

        Returns:
            Preprocessed sample(s)
        """
        if layers == "all":
            layers = list(self.preprocessors.keys())

        if isinstance(layers, list) and len(layers) == 1:
            # Single layer
            preprocessor = self.preprocessors[layers[0]]
            return preprocessor.preprocess(event)
        # Multiple layers
        samples = {}
        for layer in layers:
            preprocessor = self.preprocessors[layer]
            samples[layer] = preprocessor.preprocess(event)
        return samples

    def preprocess_batch(self, events: list[dict[str, Any]], layer: LayerType) -> list[PreprocessedSample]:
        """Preprocess batch of events for a specific layer.

        Args:
            events: List of raw events
            layer: Target layer

        Returns:
            List of preprocessed samples
        """
        preprocessor = self.preprocessors[layer]
        samples = [preprocessor.preprocess(event) for event in events]
        return samples

    def save_samples(self, samples: list[PreprocessedSample], filename: str) -> Path:
        """Save preprocessed samples to file.

        Args:
            samples: List of preprocessed samples
            filename: Output filename (without extension)

        Returns:
            Path to saved file
        """
        output_path = self.output_dir / f"{filename}.npz"

        # Extract data
        features_list = [sample.features for sample in samples]
        labels_list = [sample.label if sample.label is not None else -1 for sample in samples]
        sample_ids = [sample.sample_id for sample in samples]

        # Stack features
        features = np.stack(features_list)
        labels = np.array(labels_list)

        # Save
        np.savez_compressed(
            output_path,
            features=features,
            labels=labels,
            sample_ids=sample_ids,
            layer=str(samples[0].layer.value) if samples else "",
        )

        logger.info(f"Saved {len(samples)} samples to {output_path}")
        return output_path

    def load_samples(self, filepath: Path) -> list[PreprocessedSample]:
        """Load preprocessed samples from file.

        Args:
            filepath: Path to .npz file

        Returns:
            List of preprocessed samples
        """
        data = np.load(filepath, allow_pickle=True)

        features = data["features"]
        labels = data["labels"]
        sample_ids = data["sample_ids"]
        layer_str = str(data["layer"])

        layer = LayerType(layer_str)

        samples = []
        for i in range(len(features)):
            label = int(labels[i]) if labels[i] >= 0 else None

            sample = PreprocessedSample(sample_id=str(sample_ids[i]), layer=layer, features=features[i], label=label)
            samples.append(sample)

        logger.info(f"Loaded {len(samples)} samples from {filepath}")
        return samples
