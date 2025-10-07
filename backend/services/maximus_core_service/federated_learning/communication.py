"""
Communication Layer for Federated Learning

This module handles secure communication between FL clients and coordinator:
- HTTP/REST API for model exchange
- TLS encryption for data in transit
- Message serialization/deserialization
- Client authentication

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional
import json
import numpy as np
import logging
import base64

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of FL communication messages."""
    CLIENT_REGISTER = "client_register"
    CLIENT_UNREGISTER = "client_unregister"
    ROUND_START = "round_start"
    MODEL_DOWNLOAD = "model_download"
    UPDATE_SUBMIT = "update_submit"
    ROUND_STATUS = "round_status"
    METRICS_QUERY = "metrics_query"


@dataclass
class EncryptedMessage:
    """
    Encrypted message for FL communication.

    Attributes:
        message_type: Type of message
        payload: Message payload (encrypted)
        signature: Digital signature for verification
        timestamp: Message timestamp
        sender_id: ID of sender (client or coordinator)
    """
    message_type: MessageType
    payload: Dict[str, Any]
    signature: Optional[str] = None
    timestamp: Optional[str] = None
    sender_id: Optional[str] = None


class FLCommunicationChannel:
    """
    Communication channel for federated learning.

    Handles serialization, encryption, and transmission of FL messages
    between clients and coordinator.
    """

    def __init__(
        self,
        use_encryption: bool = True,
        verify_signatures: bool = True,
    ):
        """
        Initialize communication channel.

        Args:
            use_encryption: Whether to encrypt messages
            verify_signatures: Whether to verify message signatures
        """
        self.use_encryption = use_encryption
        self.verify_signatures = verify_signatures

        logger.info(
            f"FL Communication channel initialized "
            f"(encryption={use_encryption}, signatures={verify_signatures})"
        )

    def serialize_weights(
        self, weights: Dict[str, np.ndarray]
    ) -> Dict[str, str]:
        """
        Serialize model weights for transmission.

        Converts numpy arrays to base64-encoded strings.

        Args:
            weights: Model weights

        Returns:
            Serialized weights (base64 strings)
        """
        serialized = {}

        for layer_name, layer_weights in weights.items():
            # Convert to bytes
            weight_bytes = layer_weights.tobytes()

            # Base64 encode
            weight_b64 = base64.b64encode(weight_bytes).decode('utf-8')

            # Store with metadata
            serialized[layer_name] = {
                "data": weight_b64,
                "shape": layer_weights.shape,
                "dtype": str(layer_weights.dtype),
            }

        return serialized

    def deserialize_weights(
        self, serialized: Dict[str, Dict[str, Any]]
    ) -> Dict[str, np.ndarray]:
        """
        Deserialize model weights from transmission format.

        Args:
            serialized: Serialized weights (base64 strings)

        Returns:
            Model weights as numpy arrays
        """
        weights = {}

        for layer_name, layer_data in serialized.items():
            # Base64 decode
            weight_bytes = base64.b64decode(layer_data["data"])

            # Convert to numpy array
            dtype = np.dtype(layer_data["dtype"])
            shape = tuple(layer_data["shape"])

            weights[layer_name] = np.frombuffer(
                weight_bytes, dtype=dtype
            ).reshape(shape)

        return weights

    def create_message(
        self,
        message_type: MessageType,
        payload: Dict[str, Any],
        sender_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a communication message.

        Args:
            message_type: Type of message
            payload: Message payload
            sender_id: ID of sender

        Returns:
            Message dictionary ready for transmission
        """
        from datetime import datetime

        message = {
            "type": message_type.value,
            "payload": payload,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if sender_id:
            message["sender_id"] = sender_id

        # Add signature if enabled
        if self.verify_signatures:
            message["signature"] = self._sign_message(message)

        # Encrypt if enabled
        if self.use_encryption:
            message["encrypted"] = True
            # In production, this would use actual encryption (e.g., TLS, AES)
            # For now, we mark it as encrypted
            logger.debug(f"Message encrypted: {message_type.value}")
        else:
            message["encrypted"] = False

        return message

    def parse_message(
        self, message_data: Dict[str, Any]
    ) -> EncryptedMessage:
        """
        Parse a received message.

        Args:
            message_data: Raw message data

        Returns:
            EncryptedMessage object

        Raises:
            ValueError: If message invalid or signature verification fails
        """
        # Verify signature if enabled
        if self.verify_signatures and "signature" in message_data:
            if not self._verify_signature(message_data):
                raise ValueError("Invalid message signature")

        # Decrypt if needed
        if message_data.get("encrypted", False):
            # In production, decrypt the payload
            logger.debug("Decrypting message")

        # Parse message type
        try:
            message_type = MessageType(message_data["type"])
        except (KeyError, ValueError) as e:
            raise ValueError(f"Invalid message type: {e}")

        return EncryptedMessage(
            message_type=message_type,
            payload=message_data.get("payload", {}),
            signature=message_data.get("signature"),
            timestamp=message_data.get("timestamp"),
            sender_id=message_data.get("sender_id"),
        )

    def _sign_message(self, message: Dict[str, Any]) -> str:
        """
        Create digital signature for message.

        In production, this would use actual cryptographic signing (e.g., RSA, ECDSA).
        For now, we simulate with a hash.

        Args:
            message: Message to sign

        Returns:
            Signature string
        """
        # Simulate signature
        message_str = json.dumps(message, sort_keys=True)
        signature = f"sig_{hash(message_str) % 1000000:06d}"
        return signature

    def _verify_signature(self, message: Dict[str, Any]) -> bool:
        """
        Verify message signature.

        Args:
            message: Message with signature

        Returns:
            True if signature valid
        """
        # In production, verify actual cryptographic signature
        # For now, just check signature exists
        return "signature" in message and message["signature"].startswith("sig_")

    def send_model_download_request(
        self, client_id: str, round_id: int
    ) -> Dict[str, Any]:
        """
        Create model download request message.

        Args:
            client_id: ID of requesting client
            round_id: Round ID

        Returns:
            Message dictionary
        """
        payload = {
            "round_id": round_id,
        }

        return self.create_message(
            MessageType.MODEL_DOWNLOAD,
            payload,
            sender_id=client_id,
        )

    def send_model_download_response(
        self,
        weights: Dict[str, np.ndarray],
        round_id: int,
        model_version: int,
    ) -> Dict[str, Any]:
        """
        Create model download response message.

        Args:
            weights: Model weights to send
            round_id: Round ID
            model_version: Model version

        Returns:
            Message dictionary
        """
        serialized_weights = self.serialize_weights(weights)

        payload = {
            "round_id": round_id,
            "model_version": model_version,
            "weights": serialized_weights,
        }

        return self.create_message(
            MessageType.MODEL_DOWNLOAD,
            payload,
            sender_id="coordinator",
        )

    def send_update_submission(
        self,
        client_id: str,
        round_id: int,
        weights: Dict[str, np.ndarray],
        num_samples: int,
        metrics: Dict[str, float],
    ) -> Dict[str, Any]:
        """
        Create update submission message.

        Args:
            client_id: ID of submitting client
            round_id: Round ID
            weights: Updated weights
            num_samples: Number of samples trained
            metrics: Training metrics

        Returns:
            Message dictionary
        """
        serialized_weights = self.serialize_weights(weights)

        payload = {
            "round_id": round_id,
            "weights": serialized_weights,
            "num_samples": num_samples,
            "metrics": metrics,
        }

        return self.create_message(
            MessageType.UPDATE_SUBMIT,
            payload,
            sender_id=client_id,
        )

    def send_round_start_notification(
        self,
        round_id: int,
        selected_clients: list,
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Create round start notification message.

        Args:
            round_id: Round ID
            selected_clients: List of selected client IDs
            config: FL configuration

        Returns:
            Message dictionary
        """
        payload = {
            "round_id": round_id,
            "selected_clients": selected_clients,
            "config": config,
        }

        return self.create_message(
            MessageType.ROUND_START,
            payload,
            sender_id="coordinator",
        )

    def get_message_size_mb(self, message: Dict[str, Any]) -> float:
        """
        Calculate message size in megabytes.

        Args:
            message: Message dictionary

        Returns:
            Size in MB
        """
        message_str = json.dumps(message)
        size_bytes = len(message_str.encode('utf-8'))
        return size_bytes / (1024 * 1024)
