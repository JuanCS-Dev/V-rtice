#!/usr/bin/env python3
"""
Main entry point for the service.

Run with: python -m service_template.main
Or: uvicorn service_template.main:app --reload
"""
import uvicorn

from .infrastructure.config import get_settings
from .presentation.app import create_app

app = create_app()


def main() -> None:
    """Run the service."""
    settings = get_settings()

    uvicorn.run(
        "service_template.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
