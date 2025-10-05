"""Maximus AI Immune System - Consensus Validator Module.

This module implements a consensus-based validation mechanism for the Maximus
AI Immune System. It is responsible for aggregating and evaluating telemetry
data or anomaly reports from multiple sources or internal services to reach a
'consensus' on the true state of the system or the presence of a threat.

By requiring multiple independent confirmations or a weighted agreement before
triggering a full immune response, this module helps to reduce false positives
and ensures that critical defensive actions are taken only when there is a high
degree of certainty. This enhances the reliability and precision of the AI's
self-defense capabilities.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime


class ConsensusValidator:
    """Aggregates and evaluates telemetry data or anomaly reports from multiple
    sources to reach a 'consensus' on the true state of the system or the
    presence of a threat.

    Helps reduce false positives and ensures critical defensive actions are
    taken only when there is a high degree of certainty.
    """

    def __init__(self, required_consensus_score: float = 0.7):
        """Initializes the ConsensusValidator module.

        Args:
            required_consensus_score (float): The score (0.0 to 1.0) required to reach consensus.
        """
        self.required_consensus_score = required_consensus_score
        self.validation_records: List[Dict[str, Any]] = []

    async def validate_telemetry(self, service_id: str, metrics: Dict[str, Any]) -> bool:
        """Validates incoming telemetry data to determine if it indicates an anomaly.

        Args:
            service_id (str): The ID of the service submitting telemetry.
            metrics (Dict[str, Any]): The metrics reported by the service.

        Returns:
            bool: True if an anomaly is validated by consensus, False otherwise.
        """
        print(f"[ConsensusValidator] Validating telemetry from {service_id}...")
        await asyncio.sleep(0.1) # Simulate validation process

        # Simplified consensus logic: check for high CPU or memory usage
        anomaly_score = 0.0
        if metrics.get("cpu_usage", 0) > 80:
            anomaly_score += 0.4
        if metrics.get("memory_usage", 0) > 90:
            anomaly_score += 0.4
        if metrics.get("error_rate", 0) > 0.1:
            anomaly_score += 0.3

        # Record the validation event
        self.validation_records.append({
            "timestamp": datetime.now().isoformat(),
            "service_id": service_id,
            "metrics": metrics,
            "anomaly_score": anomaly_score,
            "consensus_reached": anomaly_score >= self.required_consensus_score
        })

        if anomaly_score >= self.required_consensus_score:
            print(f"[ConsensusValidator] Consensus reached: Anomaly detected for {service_id} (score: {anomaly_score:.2f})")
            return True
        else:
            print(f"[ConsensusValidator] No consensus for anomaly on {service_id} (score: {anomaly_score:.2f})")
            return False

    async def get_validation_history(self, service_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieves the history of validation records.

        Args:
            service_id (Optional[str]): Filter records by service ID. If None, returns all.
            limit (int): The maximum number of records to retrieve.

        Returns:
            List[Dict[str, Any]]: A list of validation record dictionaries.
        """
        filtered_records = [r for r in self.validation_records if service_id is None or r["service_id"] == service_id]
        return sorted(filtered_records, key=lambda x: x["timestamp"], reverse=True)[:limit]

    def set_required_consensus_score(self, new_score: float):
        """Sets a new required consensus score.

        Args:
            new_score (float): The new score (0.0 to 1.0).
        
        Raises:
            ValueError: If new_score is outside the valid range [0.0, 1.0].
        """
        if not 0.0 <= new_score <= 1.0:
            raise ValueError("Consensus score must be between 0.0 and 1.0.")
        self.required_consensus_score = new_score
