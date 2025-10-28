"""Coordinator for the Derme layer."""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from ..config import get_settings, TegumentarSettings
from .deep_inspector import DeepPacketInspector, InspectionResult
from .langerhans_cell import LangerhansCell
from .sensory_processor import SensoryProcessor
from .stateful_inspector import FlowObservation, InspectorAction, StatefulInspector

logger = logging.getLogger(__name__)


class DermeLayer:
    """High-level API for stateful inspection, DPI and antigen capture."""

    def __init__(self, settings: Optional[TegumentarSettings] = None):
        self._settings = settings or get_settings()
        self._stateful = StatefulInspector(self._settings)
        self._dpi = DeepPacketInspector(self._settings)
        self._langerhans = LangerhansCell(self._settings)
        self._sensory = SensoryProcessor()
        self._lock = asyncio.Lock()

    async def startup(self) -> None:
        await self._stateful.startup()
        await self._langerhans.startup()
        logger.info("Derme layer fully initialised")

    async def shutdown(self) -> None:
        await self._langerhans.shutdown()
        await self._stateful.shutdown()

    async def process_packet(
        self, observation: FlowObservation, payload: bytes
    ) -> InspectionResult:
        decision = await self._stateful.process(observation)

        if decision.action == InspectorAction.DROP:
            result = InspectionResult(
                action=InspectorAction.DROP,
                confidence=0.95,
                reason=decision.reason,
            )
            self._sensory.register_event(observation, result)
            return result

        if decision.action == InspectorAction.PASS:
            result = InspectionResult(
                action=InspectorAction.PASS,
                confidence=0.5,
                reason=decision.reason,
            )
            self._sensory.register_event(observation, result)
            return result

        return await self._deep_inspection(observation, payload)

    async def _deep_inspection(
        self, observation: FlowObservation, payload: bytes
    ) -> InspectionResult:
        result = self._dpi.inspect(observation, payload)
        self._sensory.register_event(observation, result)

        if result.anomaly_score and result.anomaly_score > 0.8:
            await self._langerhans.capture_antigen(observation, result, payload)

        return result

    def snapshot(self) -> dict:
        snap = self._sensory.render_snapshot()
        return {
            "timestamp": snap.timestamp,
            "pressure": snap.pressure,
            "temperature": snap.temperature,
            "pain": snap.pain,
            "description": snap.description,
        }


__all__ = ["DermeLayer"]
