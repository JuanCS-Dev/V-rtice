"""Controls permeability states across the tegumentar membrane."""

from __future__ import annotations

import logging
from typing import Optional

import httpx

from ..config import get_settings, TegumentarSettings
from ..epiderme.stateless_filter import StatelessFilter

logger = logging.getLogger(__name__)


class PermeabilityController:
    """Translates cognitive posture into network enforcement."""

    def __init__(
        self,
        stateless_filter: StatelessFilter,
        settings: Optional[TegumentarSettings] = None,
    ):
        self._stateless_filter = stateless_filter
        self._settings = settings or get_settings()
        self._client: Optional[httpx.AsyncClient] = (
            httpx.AsyncClient(timeout=20.0) if self._settings.sdnc_endpoint else None
        )

    async def set_posture(self, posture: str) -> None:
        posture = posture.upper()
        if posture == "LOCKDOWN":
            self._stateless_filter.set_policy("drop")
            await self._notify_sdnc({"mode": "strict"})
        elif posture == "HARDENED":
            self._stateless_filter.set_policy("drop")
            await self._notify_sdnc({"mode": "moderate"})
        elif posture in {"BALANCED", "EXPLORE"}:
            self._stateless_filter.set_policy("accept")
            await self._notify_sdnc({"mode": "open"})
        else:
            raise ValueError(f"Unknown posture: {posture}")
        logger.info("Permeability posture set to %s", posture)

    async def shutdown(self) -> None:
        if self._client:
            await self._client.aclose()

    async def _notify_sdnc(self, payload: dict) -> None:
        if not self._client or not self._settings.sdnc_endpoint:
            return
        url = f"{self._settings.sdnc_endpoint}/operations/tegumentar:permeability"
        response = await self._client.post(url, json=payload)
        response.raise_for_status()


__all__ = ["PermeabilityController"]
