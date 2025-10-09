"""Uvicorn entrypoint for Tegumentar Service."""

from __future__ import annotations

import uvicorn

from .app import app, service_settings


def run() -> None:
    uvicorn.run(
        app,
        host=service_settings.host,
        port=service_settings.port,
        log_level="info",
    )


if __name__ == "__main__":
    run()
