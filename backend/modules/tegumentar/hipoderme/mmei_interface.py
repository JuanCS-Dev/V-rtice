"""FastAPI interface connecting tegumentar module with MMEI."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel

from ..config import get_settings, TegumentarSettings
from ..derme.manager import DermeLayer
from ..epiderme.manager import EpidermeLayer
from .permeability_control import PermeabilityController
from .wound_healing import WoundHealingOrchestrator

logger = logging.getLogger(__name__)


class PostureRequest(BaseModel):
    posture: str


class WoundHealingRequest(BaseModel):
    playbook: str
    context: dict = {}


def create_app(
    epiderme: EpidermeLayer,
    derme: DermeLayer,
    permeability: PermeabilityController,
    wound_healing: WoundHealingOrchestrator,
    settings: Optional[TegumentarSettings] = None,
) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="Tegumentar Module", version="1.0.0")
    router = APIRouter(prefix="/api/tegumentar")

    @router.post("/posture")
    async def set_posture(req: PostureRequest):
        try:
            await permeability.set_posture(req.posture)
            return {"status": "ok", "posture": req.posture}
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to set posture: %s", exc)
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @router.get("/status")
    async def status():
        return {
            "environment": settings.environment,
            "epiderme_interface": epiderme.interface,
            "qualia": derme.snapshot(),
        }

    @router.get("/qualia")
    async def qualia():
        return derme.snapshot()

    @router.post("/wound-healing")
    async def trigger_wound_healing(req: WoundHealingRequest):
        await wound_healing.execute(req.playbook, req.context)
        return {"status": "queued", "playbook": req.playbook}

    app.include_router(router)

    @app.get("/metrics")
    async def metrics_endpoint():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app


__all__ = ["create_app", "PostureRequest", "WoundHealingRequest"]
