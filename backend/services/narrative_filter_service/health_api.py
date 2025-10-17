"""Health check endpoint."""

from datetime import datetime

from fastapi import APIRouter, status

from models import HealthResponse

router = APIRouter()


@router.get("/", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="ok", service="narrative-filter-service", version="1.0.0", timestamp=datetime.utcnow())
