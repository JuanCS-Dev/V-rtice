"""Immunis B-Cell - Antibody Generation Service - FastAPI Wrapper

Exposes B-Cell - Antibody Generation capabilities via REST API.

Bio-inspired immune system component.

Endpoints:
- GET /health - Health check
- GET /status - Service status
- POST /process - Main processing endpoint
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Optional import of core (may not exist yet)
try:
    from bcell_core import BcellCore

    CORE_AVAILABLE = True
except ImportError:
    logger.warning("BcellCore not available - running in limited mode")
    CORE_AVAILABLE = False
    BcellCore = None

app = FastAPI(
    title="Immunis B-Cell - Antibody Generation Service",
    version="1.0.0",
    description="Bio-inspired b-cell - antibody generation service",
)

# Initialize core if available
if CORE_AVAILABLE and BcellCore:
    try:
        core = BcellCore()
        logger.info("B-Cell - Antibody Generation core initialized")
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
    logger.info("🦠 Starting Immunis B-Cell - Antibody Generation Service...")
    logger.info("✅ B-Cell - Antibody Generation Service started successfully!")


@app.on_event("shutdown")
async def shutdown_event():
    """Performs shutdown tasks."""
    logger.info("👋 Shutting down Immunis B-Cell - Antibody Generation Service...")
    logger.info("🛑 B-Cell - Antibody Generation Service shut down.")


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint.

    Returns:
        Dict[str, Any]: Service health status
    """
    return {
        "status": "healthy",
        "service": "immunis_bcell",
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
        "service": "immunis_bcell",
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
        raise HTTPException(status_code=503, detail="Core not available - service in limited mode")

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
            "service": "immunis_bcell",
            "results": result,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8016)
