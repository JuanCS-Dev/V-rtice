"""Transforms network telemetry into qualia vectors for MAXIMUS."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import time
from typing import Deque

from .deep_inspector import InspectionResult
from .stateful_inspector import FlowObservation, InspectorAction


@dataclass(slots=True)
class SensorySnapshot:
    timestamp: float
    pressure: float
    temperature: float
    pain: float
    description: str


class SensoryProcessor:
    """Accumulates inspection events and emits qualia metrics."""

    def __init__(self):
        self._events: Deque[tuple[FlowObservation, InspectionResult]] = deque(
            maxlen=1000
        )

    def register_event(
        self, observation: FlowObservation, inspection: InspectionResult
    ) -> None:
        self._events.append((observation, inspection))

    def render_snapshot(self, window: float = 60.0) -> SensorySnapshot:
        now = time.time()
        relevant = [
            (obs, ins) for (obs, ins) in self._events if now - obs.timestamp <= window
        ]
        pressure = sum(obs.payload_size for obs, _ in relevant) / max(window, 1.0)
        temperature = sum(ins.anomaly_score or 0.0 for _, ins in relevant) / max(
            len(relevant), 1
        )
        pain = sum(
            1.0 if ins.action != InspectorAction.PASS else 0.0 for _, ins in relevant
        ) / max(len(relevant), 1)

        description = f"window={len(relevant)} pressure={pressure:.2f} temperature={temperature:.2f} pain={pain:.2f}"
        return SensorySnapshot(
            timestamp=now,
            pressure=pressure,
            temperature=temperature,
            pain=pain,
            description=description,
        )


__all__ = ["SensoryProcessor", "SensorySnapshot"]
