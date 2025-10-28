"""High-level orchestration of the Tegumentar module."""

from __future__ import annotations

import logging
from typing import Optional

from .config import TegumentarSettings, get_settings

logger = logging.getLogger(__name__)
from .derme.manager import DermeLayer, FlowObservation, InspectionResult
from .epiderme.manager import EpidermeLayer
from .hipoderme.adaptive_throttling import AdaptiveThrottler
from .hipoderme.mmei_interface import create_app
from .hipoderme.permeability_control import PermeabilityController
from .hipoderme.wound_healing import WoundHealingOrchestrator


class TegumentarModule:
    """Entry point used by MAXIMUS orchestrator."""

    def __init__(self, settings: Optional[TegumentarSettings] = None):
        self._settings = settings or get_settings()
        self.epiderme = EpidermeLayer(self._settings)
        self.derme = DermeLayer(self._settings)
        self.permeability = PermeabilityController(self.epiderme.stateless_filter, self._settings)
        self.wound_healing = WoundHealingOrchestrator(self._settings)
        self._throttler: Optional[AdaptiveThrottler] = None

    async def startup(self, interface: str) -> None:
        await self.epiderme.startup(interface)
        # Derme layer disabled - requires PostgreSQL infrastructure (no PostgreSQL available)
        # await self.derme.startup()
        self._throttler = AdaptiveThrottler(interface)

    async def shutdown(self) -> None:
        await self.controller_shutdown()

    async def controller_shutdown(self) -> None:
        await self.permeability.shutdown()
        await self.wound_healing.shutdown()
        # await self.derme.shutdown()  # Disabled
        await self.epiderme.shutdown()

    async def process_packet(self, observation: FlowObservation, payload: bytes) -> InspectionResult:
        return await self.derme.process_packet(observation, payload)

    def fastapi_app(self):
        return create_app(self.epiderme, self.derme, self.permeability, self.wound_healing, self._settings)


__all__ = ["TegumentarModule"]
