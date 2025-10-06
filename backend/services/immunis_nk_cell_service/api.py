"""Immunis NK Cell - Rapid Cytotoxicity Service - FastAPI Wrapper

Exposes NK Cell - Rapid Cytotoxicity capabilities via REST API.

Bio-inspired immune system component.

Endpoints:
- GET /health - Health check
- GET /status - Service status
- POST /process - Main processing endpoint
"""

from datetime import datetime
import logging
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Optional import of core (may not exist yet)
try:
    from nk_cell_core import NkCellCore

    CORE_AVAILABLE = True
except ImportError:
    logger.warning("NkCellCore not available - running in limited mode")
    CORE_AVAILABLE = False
    NkCellCore = None

app = FastAPI(
    title="Immunis NK Cell - Rapid Cytotoxicity Service",
    version="1.0.0",
    description="Bio-inspired nk cell - rapid cytotoxicity service",
)

# Initialize core if available
if CORE_AVAILABLE and NkCellCore:
    try:
        core = NkCellCore()
        logger.info("NK Cell - Rapid Cytotoxicity core initialized")
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
    logger.info("🦠 Starting Immunis NK Cell - Rapid Cytotoxicity Service...")
    logger.info("✅ NK Cell - Rapid Cytotoxicity Service started successfully!")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks."""
    logger.info("👋 Shutting down Immunis NK Cell - Rapid Cytotoxicity Service...")
    logger.info("🛑 NK Cell - Rapid Cytotoxicity Service shut down.")


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint.

    Returns:
        Dict[str, Any]: Service health status
    """
    return {
        "status": "healthy",
        "service": "immunis_nk_cell",
        "core_available": CORE_AVAILABLE and core is not None,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/status")
async def get_status() -> Dict[str, Any]:
    """Get detailed service status.

    Returns:
        Dict[str, Any]: Detailed status information
    """
    if core and hasattr(core, "get_status"):
        try:
            return await core.get_status()
        except Exception as e:
            logger.error(f"Status retrieval failed: {e}")

    return {
        "status": "operational",
        "service": "immunis_nk_cell",
        "mode": "limited" if not core else "full",
        "timestamp": datetime.now().isoformat(),
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
            status_code=503, detail="Core not available - service in limited mode"
        )

    try:
        # Call core processing method if available
        if hasattr(core, "process"):
            result = await core.process(request.data, request.context)
        elif hasattr(core, "analyze"):
            result = await core.analyze(request.data, request.context)
        else:
            result = {"processed": True, "data": request.data}

        return {
            "status": "success",
            "service": "immunis_nk_cell",
            "results": result,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8019)
