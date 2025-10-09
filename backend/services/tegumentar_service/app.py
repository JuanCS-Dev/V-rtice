"""FastAPI application exposing the Tegumentar module."""

from __future__ import annotations

import logging

from fastapi import FastAPI

from backend.modules.tegumentar import TegumentarModule

from .config import get_module, get_service_settings

logger = logging.getLogger(__name__)

service_settings = get_service_settings()
module: TegumentarModule = get_module()

app: FastAPI = module.fastapi_app()


@app.on_event("startup")
async def startup_event() -> None:
    logger.info("Starting Tegumentar service on interface %s", service_settings.interface)
    await module.startup(service_settings.interface)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    logger.info("Shutting down Tegumentar service")
    await module.shutdown()


__all__ = ["app", "service_settings"]
