"""Feature extraction utilities for anomaly detection."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import List

from ..stateful_inspector import FlowObservation


@dataclass(slots=True)
class FeatureVector:
    payload_length: int
    entropy: float
    printable_ratio: float
    digit_ratio: float
    average_byte_value: float
    tcp_flag_score: float
    inter_packet_interval: float

    def as_list(self) -> List[float]:
        return [
            float(self.payload_length),
            self.entropy,
            self.printable_ratio,
            self.digit_ratio,
            self.average_byte_value,
            self.tcp_flag_score,
            self.inter_packet_interval,
        ]


class FeatureExtractor:
    """Transforms observations and payloads into numerical feature vectors."""

    def __init__(self):
        self._last_timestamp: float | None = None

    def transform(self, observation: FlowObservation, payload: bytes) -> FeatureVector:
        entropy = self._shannon_entropy(payload)
        printable = sum(1 for b in payload if 32 <= b <= 126)
        digits = sum(1 for b in payload if 48 <= b <= 57)
        average = sum(payload) / max(len(payload), 1)
        interval = (
            observation.timestamp - self._last_timestamp
            if self._last_timestamp is not None
            else 0.0
        )
        self._last_timestamp = observation.timestamp

        flag_score = self._tcp_flag_score(observation.flags)

        return FeatureVector(
            payload_length=len(payload),
            entropy=entropy,
            printable_ratio=printable / max(len(payload), 1),
            digit_ratio=digits / max(len(payload), 1),
            average_byte_value=average,
            tcp_flag_score=flag_score,
            inter_packet_interval=interval,
        )

    @staticmethod
    def _shannon_entropy(data: bytes) -> float:
        if not data:
            return 0.0
        counts = {}
        for byte in data:
            counts[byte] = counts.get(byte, 0) + 1
        entropy = 0.0
        length = len(data)
        for count in counts.values():
            p = count / length
            entropy -= p * math.log2(p)
        return entropy

    @staticmethod
    def _tcp_flag_score(flags: str | None) -> float:
        if not flags:
            return 0.0
        score = 0.0
        if "S" in flags and "A" not in flags:
            score += 1.0
        if "F" in flags:
            score += 0.5
        if "P" in flags:
            score += 0.2
        return score


__all__ = ["FeatureExtractor", "FeatureVector"]
