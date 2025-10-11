"""
Wargaming Crisol Main Application - Patch validation via two-phase attack simulation.

Theoretical Foundation:
    Inspired by biological immune system stress testing.
    Before deploying patch to production, test against real exploits.
    
    Two-Phase Protocol:
    Phase 1: Attack vulnerable version (MUST succeed)
    Phase 2: Attack patched version (MUST fail)
    
    If both phases pass → Patch validated ✅
    If any phase fails → Patch rejected ❌

Performance Target:
    - Wargaming time: <5 min per patch
    - Success rate: >95%
    - False positive: <2%

Author: MAXIMUS Team
Glory to YHWH - Validator of protection
"""

import asyncio
import logging
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
from typing import Optional

from exploit_database import load_exploit_database, get_exploit_for_apv
from two_phase_simulator import TwoPhaseSimulator
from websocket_stream import wargaming_ws_manager, wargaming_websocket_endpoint

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Wargaming Crisol API",
    description="Two-phase attack simulation for patch validation",
    version="1.0.0"
)


# Request/Response models
class WargamingRequest(BaseModel):
    """Wargaming request"""
    apv_id: str
    cve_id: Optional[str] = None
    patch_id: str
    target_url: str = "http://localhost:8080"


class WargamingResponse(BaseModel):
    """Wargaming response"""
    apv_id: str
    cve_id: str
    exploit_id: str
    patch_validated: bool
    status: str
    phase_1_passed: bool
    phase_2_passed: bool
    total_duration_seconds: float
    message: str


# Health check
@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "wargaming-crisol",
        "version": "1.0.0"
    }


# WebSocket endpoint for real-time updates
@app.websocket("/ws/wargaming")
async def wargaming_websocket(websocket: WebSocket):
    """WebSocket for real-time wargaming updates"""
    await wargaming_websocket_endpoint(websocket)


# Wargaming endpoint
@app.post("/wargaming/execute", response_model=WargamingResponse)
async def execute_wargaming(request: WargamingRequest):
    """
    Execute two-phase wargaming validation.
    
    Args:
        request: Wargaming request
    
    Returns:
        Wargaming result
    """
    logger.info(f"🎯 Wargaming request: APV={request.apv_id}, Patch={request.patch_id}")
    
    # Load exploit database
    db = load_exploit_database()
    
    # Mock APV (in production: load from database)
    from unittest.mock import Mock
    apv = Mock()
    apv.apv_id = request.apv_id
    apv.cve_id = request.cve_id or f"CVE-{request.apv_id}"
    apv.cwe_ids = ["CWE-89"]  # Example
    
    # Mock Patch
    patch = Mock()
    patch.patch_id = request.patch_id
    patch.unified_diff = "..."
    
    # Find exploit
    exploit = get_exploit_for_apv(apv, db)
    
    if not exploit:
        raise HTTPException(
            status_code=404,
            detail=f"No exploit found for {apv.cve_id}"
        )
    
    logger.info(f"✓ Using exploit: {exploit.name}")
    
    # Execute wargaming
    simulator = TwoPhaseSimulator()
    
    try:
        result = await simulator.execute_wargaming(
            apv=apv,
            patch=patch,
            exploit=exploit,
            target_url=request.target_url
        )
        
        # Stream result to WebSocket clients
        await wargaming_ws_manager.broadcast(
            message_type="wargaming_complete",
            data=result.to_dict()
        )
        
        logger.info(f"✅ Wargaming complete: {result.summary()}")
        
        return WargamingResponse(
            apv_id=result.apv_id,
            cve_id=result.cve_id,
            exploit_id=result.exploit_id,
            patch_validated=result.patch_validated,
            status=result.status.value,
            phase_1_passed=result.phase_1.phase_passed,
            phase_2_passed=result.phase_2.phase_passed,
            total_duration_seconds=result.total_duration_seconds,
            message=result.summary()
        )
        
    except Exception as e:
        logger.error(f"❌ Wargaming failed: {e}")
        
        # Stream error
        await wargaming_ws_manager.stream_error(apv.apv_id, str(e))
        
        raise HTTPException(
            status_code=500,
            detail=f"Wargaming failed: {str(e)}"
        )


# Startup event
@app.on_event("startup")
async def startup_event():
    """Startup initialization"""
    logger.info("🚀 Starting Wargaming Crisol service...")
    
    # Load exploit database
    db = load_exploit_database()
    stats = db.get_statistics()
    
    logger.info(f"✓ Loaded {stats['total']} exploits")
    logger.info(f"✓ CWE Coverage: {len(stats['cwe_coverage'])}")
    logger.info("🔥 Wargaming Crisol ready!")


# Main entry point
if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8026))
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
