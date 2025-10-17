"""Health check endpoint."""

from datetime import datetime

from services.command_bus_service.models import HealthResponse
from fastapi import APIRouter, status

router = APIRouter()


@router.get("/", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="ok", service="command-bus-service", version="1.0.0", timestamp=datetime.utcnow())
