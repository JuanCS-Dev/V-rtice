"""Immunis Dendritic Cell - Antigen Presentation Service - FastAPI Wrapper

Exposes Dendritic Cell - Antigen Presentation capabilities via REST API.

Bio-inspired immune system component.

Endpoints:
- GET /health - Health check
- GET /status - Service status
- POST /process - Main processing endpoint
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uvicorn
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Optional import of core (may not exist yet)
try:
    from dendritic_core import DendriticCore
    CORE_AVAILABLE = True
except ImportError:
    logger.warning("DendriticCore not available - running in limited mode")
    CORE_AVAILABLE = False
    DendriticCore = None

app = FastAPI(
    title="Immunis Dendritic Cell - Antigen Presentation Service",
    version="1.0.0",
    description="Bio-inspired dendritic cell - antigen presentation service"
)

# Initialize core if available
if CORE_AVAILABLE and DendriticCore:
    try:
        core = DendriticCore()
        logger.info("Dendritic Cell - Antigen Presentation core initialized")
    except Exception as e:
        logger.warning(f"Core initialization failed: {e}")
        core = None
else:
    core = None


class ProcessRequest(BaseModel):
    """Generic request model for processing.

    Attributes:
        data (Dict[str, Any]): Input data to process
        context (Optional[Dict[str, Any]]): Optional context
    """
    data: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None


@app.on_event("startup")
async def startup_event():
    """Performs startup tasks."""
    logger.info("🦠 Starting Immunis Dendritic Cell - Antigen Presentation Service...")
    logger.info("✅ Dendritic Cell - Antigen Presentation Service started successfully!")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks."""
    logger.info("👋 Shutting down Immunis Dendritic Cell - Antigen Presentation Service...")
    logger.info("🛑 Dendritic Cell - Antigen Presentation Service shut down.")


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint.

    Returns:
        Dict[str, Any]: Service health status
    """
    return {
        "status": "healthy",
        "service": "immunis_dendritic",
        "core_available": CORE_AVAILABLE and core is not None,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/status")
async def get_status() -> Dict[str, Any]:
    """Get detailed service status.

    Returns:
        Dict[str, Any]: Detailed status information
    """
    if core and hasattr(core, 'get_status'):
        try:
            return await core.get_status()
        except Exception as e:
            logger.error(f"Status retrieval failed: {e}")

    return {
        "status": "operational",
        "service": "immunis_dendritic",
        "mode": "limited" if not core else "full",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/process")
async def process_data(request: ProcessRequest) -> Dict[str, Any]:
    """Main processing endpoint.

    Args:
        request (ProcessRequest): Data to process

    Returns:
        Dict[str, Any]: Processing results

    Raises:
        HTTPException: If processing fails
    """
    if not core:
        raise HTTPException(
            status_code=503,
            detail="Core not available - service in limited mode"
        )

    try:
        # Call core processing method if available
        if hasattr(core, 'process'):
            result = await core.process(request.data, request.context)
        elif hasattr(core, 'analyze'):
            result = await core.analyze(request.data, request.context)
        else:
            result = {"processed": True, "data": request.data}

        return {
            "status": "success",
            "service": "immunis_dendritic",
            "results": result,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8014)
