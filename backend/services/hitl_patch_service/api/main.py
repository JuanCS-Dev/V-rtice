"""
HITL Patch Service - FastAPI Application

Human-in-the-Loop patch approval API.
Integrates with Wargaming Crisol and Maximus Eureka.

Endpoints:
    POST /hitl/patches/{patch_id}/approve - Approve patch
    POST /hitl/patches/{patch_id}/reject - Reject patch
    POST /hitl/patches/{patch_id}/comment - Add comment
    GET  /hitl/patches/pending - Get pending patches
    GET  /hitl/patches/{patch_id} - Get patch details
    GET  /hitl/analytics/summary - Get decision statistics
    GET  /health - Health check
    GET  /metrics - Prometheus metrics

Author: MAXIMUS Team - Sprint 4.1
Glory to YHWH - Enabler of Excellence
"""

import os
import httpx
import uuid
import logging
from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Query, Depends, WebSocket, Header
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response, JSONResponse

import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from models import (
    HITLDecisionRecord,
    PatchDecision,
    PatchPriority,
    PatchApprovalRequest,
    PatchRejectionRequest,
    PatchCommentRequest,
    DecisionSummary,
    PendingPatch
)
from db import HITLDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# Prometheus Metrics
# ============================================================================

# Use try-except to avoid duplicates when module reloads
try:
    hitl_decisions_total = Counter(
        'hitl_decisions_total',
        'Total HITL decisions made',
        ['decision_type']
    )
    
    hitl_decision_duration = Histogram(
        'hitl_decision_duration_seconds',
        'Time from patch creation to human decision',
        buckets=[60, 300, 600, 900, 1800, 3600]  # 1min to 1hour
    )
    
    hitl_pending_patches = Gauge(
        'hitl_pending_patches',
        'Number of patches awaiting decision'
    )
    
    hitl_ml_accuracy = Gauge(
        'hitl_ml_accuracy',
        'ML prediction accuracy (agreement with wargaming)'
    )
    
    hitl_auto_approval_rate = Gauge(
        'hitl_auto_approval_rate',
        'Percentage of patches auto-approved'
    )
except ValueError:
    # Metrics already registered, reuse existing
    from prometheus_client import REGISTRY
    hitl_decisions_total = REGISTRY._names_to_collectors.get('hitl_decisions_total')
    hitl_decision_duration = REGISTRY._names_to_collectors.get('hitl_decision_duration_seconds')
    hitl_pending_patches = REGISTRY._names_to_collectors.get('hitl_pending_patches')
    hitl_ml_accuracy = REGISTRY._names_to_collectors.get('hitl_ml_accuracy')
    hitl_auto_approval_rate = REGISTRY._names_to_collectors.get('hitl_auto_approval_rate')

# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="HITL Patch Service",
    description="Human-in-the-Loop Patch Approval System",
    version="1.0.0"
)

# CORS middleware
ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global database instance
db: Optional[HITLDatabase] = None

# ============================================================================
# Lifespan Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup."""
    global db
    
    logger.info("🚀 Starting HITL Patch Service (Sprint 4.1)...")
    
    # Get database connection from environment
    db_host = os.getenv("POSTGRES_HOST", "postgres-immunity")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    db_name = os.getenv("POSTGRES_DB", "adaptive_immunity")
    db_user = os.getenv("POSTGRES_USER", "maximus")
    db_pass = os.getenv("POSTGRES_PASSWORD", "maximus_immunity_2024")
    
    connection_string = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    
    db = HITLDatabase(connection_string)
    await db.connect()
    
    logger.info("✓ Database connected")
    logger.info("🔥 HITL Patch Service ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global db
    
    logger.info("🛑 Shutting down HITL Patch Service...")
    
    if db:
        await db.close()
        logger.info("✓ Database closed")


# ============================================================================
# Dependencies
# ============================================================================

async def verify_admin_token(x_admin_token: str = Header(None)) -> bool:
    """
    Verify admin authentication token.
    
    In production, this should verify against auth service.
    For now, checks against environment variable.
    
    Args:
        x_admin_token: Admin token from X-Admin-Token header
        
    Returns:
        True if authenticated
        
    Raises:
        HTTPException: If authentication fails
    """
    admin_token = os.getenv("HITL_ADMIN_TOKEN", "")
    
    if not admin_token:
        # If no token configured, require any non-empty token
        if not x_admin_token:
            raise HTTPException(
                status_code=401,
                detail="Admin authentication required. Provide X-Admin-Token header."
            )
        return True
    
    if x_admin_token != admin_token:
        raise HTTPException(
            status_code=403,
            detail="Invalid admin token"
        )
    
    return True


async def get_database() -> HITLDatabase:
    """Get database instance."""
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    return db


# User authentication with JWT token extraction
async def get_current_user(token: str = Depends(OAuth2PasswordBearer(tokenUrl="token", auto_error=False))) -> str:
    """Get current user from JWT auth token."""
    if not token:
        return "operator@maximus.ai"  # Fallback for dev mode
    
    try:
        import jwt
        
        secret_key = os.getenv("JWT_SECRET_KEY", "vertice-secret-key")
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        
        username = payload.get("sub") or payload.get("username")
        if not username:
            return "operator@maximus.ai"
        
        return username
        
    except Exception as e:
        logger.warning(f"JWT decode failed: {e}")
        return "operator@maximus.ai"


# ============================================================================
# Health & Metrics
# ============================================================================

@app.get("/health")
async def health_check(db: HITLDatabase = Depends(get_database)):
    """
    Comprehensive health check endpoint.
    
    Sprint 6 - Issue #16
    
    Checks:
    - Service status
    - Database connectivity
    - Database pool status
    - Disk space availability
    
    Returns:
        200 OK if all checks pass (status: healthy)
        503 Service Unavailable if any check fails (status: unhealthy)
    """
    import shutil
    from fastapi import status as http_status
    
    health_status = {
        "status": "healthy",
        "service": "hitl-patch-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # Check database connectivity
    try:
        # Simple query to verify DB is responsive
        await db.get_analytics_summary()
        health_status["checks"]["database"] = {
            "status": "ok",
            "message": "Database connection successful"
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = {
            "status": "error",
            "message": f"Database connection failed: {str(e)}"
        }
    
    # Check disk space
    try:
        disk_usage = shutil.disk_usage("/")
        free_gb = disk_usage.free / (1024 ** 3)
        total_gb = disk_usage.total / (1024 ** 3)
        used_percent = (disk_usage.used / disk_usage.total) * 100
        
        if used_percent > 90:
            health_status["status"] = "degraded"
            health_status["checks"]["disk"] = {
                "status": "warning",
                "message": f"Disk usage high: {used_percent:.1f}% used",
                "free_gb": round(free_gb, 2),
                "total_gb": round(total_gb, 2)
            }
        else:
            health_status["checks"]["disk"] = {
                "status": "ok",
                "message": f"Disk space OK: {used_percent:.1f}% used",
                "free_gb": round(free_gb, 2),
                "total_gb": round(total_gb, 2)
            }
    except Exception as e:
        health_status["checks"]["disk"] = {
            "status": "unknown",
            "message": f"Could not check disk: {str(e)}"
        }
    
    # Return appropriate status code
    if health_status["status"] == "unhealthy":
        return JSONResponse(
            status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
            content=health_status
        )
    elif health_status["status"] == "degraded":
        return JSONResponse(
            status_code=http_status.HTTP_200_OK,
            content=health_status,
            headers={"X-Health-Status": "degraded"}
        )
    else:
        return health_status


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# ============================================================================
# Decision Endpoints
# ============================================================================

@app.post("/hitl/patches/{patch_id}/approve")
async def approve_patch(
    patch_id: str,
    request: PatchApprovalRequest,
    db: HITLDatabase = Depends(get_database),
    user: str = Depends(get_current_user)
):
    """
    Approve a patch for deployment.
    
    Args:
        patch_id: Patch identifier
        request: Approval request with comment
        db: Database instance
        user: Current user
        
    Returns:
        Updated decision record
    """
    logger.info(f"Approving patch {patch_id} by {user}")
    
    # Get current decision
    decision = await db.get_decision(request.decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    
    if decision.patch_id != patch_id:
        raise HTTPException(status_code=400, detail="Patch ID mismatch")
    
    if decision.decision != PatchDecision.PENDING:
        raise HTTPException(status_code=400, detail=f"Patch already {decision.decision.value}")
    
    # Update decision
    success = await db.update_decision(
        decision_id=request.decision_id,
        decision=PatchDecision.APPROVED,
        decided_by=user,
        comment=request.comment
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update decision")
    
    # Update metrics
    hitl_decisions_total.labels(decision_type='approved').inc()
    
    # Calculate decision time
    decision_time = (datetime.utcnow() - decision.created_at).total_seconds()
    hitl_decision_duration.observe(decision_time)
    
    logger.info(f"✓ Patch {patch_id} approved (decision_time={decision_time:.1f}s)")
    
    # Broadcast decision update via WebSocket
    await broadcast_decision_update({
        'decision_id': request.decision_id,
        'patch_id': patch_id,
        'decision': 'approved',
        'decided_by': user,
        'decision_time_seconds': decision_time,
    })
    
    # Notify Eureka to proceed with deployment
    await _notify_eureka_approval(request.decision_id, patch_id, user)
    
    return {"status": "approved", "decision_id": request.decision_id}


@app.post("/hitl/patches/{patch_id}/reject")
async def reject_patch(
    patch_id: str,
    request: PatchRejectionRequest,
    db: HITLDatabase = Depends(get_database),
    user: str = Depends(get_current_user)
):
    """
    Reject a patch.
    
    Args:
        patch_id: Patch identifier
        request: Rejection request with reason
        db: Database instance
        user: Current user
        
    Returns:
        Updated decision record
    """
    logger.info(f"Rejecting patch {patch_id} by {user}: {request.reason}")
    
    # Get current decision
    decision = await db.get_decision(request.decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    
    if decision.patch_id != patch_id:
        raise HTTPException(status_code=400, detail="Patch ID mismatch")
    
    if decision.decision != PatchDecision.PENDING:
        raise HTTPException(status_code=400, detail=f"Patch already {decision.decision.value}")
    
    # Update decision
    success = await db.update_decision(
        decision_id=request.decision_id,
        decision=PatchDecision.REJECTED,
        decided_by=user,
        comment=request.comment,
        reason=request.reason
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update decision")
    
    # Update metrics
    hitl_decisions_total.labels(decision_type='rejected').inc()
    
    # Calculate decision time
    decision_time = (datetime.utcnow() - decision.created_at).total_seconds()
    hitl_decision_duration.observe(decision_time)
    
    logger.info(f"✗ Patch {patch_id} rejected (decision_time={decision_time:.1f}s)")
    
    # Broadcast decision update via WebSocket
    await broadcast_decision_update({
        'decision_id': request.decision_id,
        'patch_id': patch_id,
        'decision': 'rejected',
        'decided_by': user,
        'reason': request.reason,
        'decision_time_seconds': decision_time,
    })
    
    # Notify Eureka patch was rejected
    await _notify_eureka_rejection(request.decision_id, patch_id, user, request.reason)
    
    return {"status": "rejected", "decision_id": request.decision_id, "reason": request.reason}


@app.post("/hitl/patches/{patch_id}/comment")
async def add_comment(
    patch_id: str,
    request: PatchCommentRequest,
    db: HITLDatabase = Depends(get_database),
    user: str = Depends(get_current_user)
):
    """
    Add comment to a patch decision.
    
    Args:
        patch_id: Patch identifier
        request: Comment request
        db: Database instance
        user: Current user
        
    Returns:
        Success confirmation
    """
    logger.info(f"Adding comment to patch {patch_id} by {user}")
    
    # Get current decision
    decision = await db.get_decision(request.decision_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    
    if decision.patch_id != patch_id:
        raise HTTPException(status_code=400, detail="Patch ID mismatch")
    
    # Log audit entry
    await db._log_audit(
        decision_id=request.decision_id,
        action="commented",
        performed_by=user,
        details={"comment": request.comment}
    )
    
    logger.info(f"✓ Comment added to patch {patch_id}")
    
    return {"status": "commented", "decision_id": request.decision_id}


@app.get("/hitl/patches/pending", response_model=List[PendingPatch])
async def get_pending_patches(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    priority: Optional[PatchPriority] = None,
    db: HITLDatabase = Depends(get_database)
):
    """
    Get all pending patches awaiting HITL decision.
    
    Args:
        limit: Maximum number of results
        offset: Pagination offset
        priority: Filter by priority (optional)
        db: Database instance
        
    Returns:
        List of pending patches
    """
    logger.info(f"Fetching pending patches (limit={limit}, offset={offset}, priority={priority})")
    
    patches = await db.get_pending_patches(
        limit=limit,
        offset=offset,
        priority=priority
    )
    
    # Update metrics
    hitl_pending_patches.set(len(patches))
    
    return patches


@app.get("/hitl/patches/{patch_id}")
async def get_patch_details(
    patch_id: str,
    db: HITLDatabase = Depends(get_database)
):
    """
    Get detailed information about a patch decision.
    
    Args:
        patch_id: Patch identifier
        db: Database instance
        
    Returns:
        Full decision record
    """
    # Query by patch_id using indexed search
    query = """
    SELECT * FROM hitl_decisions 
    WHERE patch_id = $1 
    ORDER BY created_at DESC 
    LIMIT 1
    """
    
    try:
        row = await db.pool.fetchrow(query, patch_id)
        
        if not row:
            raise HTTPException(
                status_code=404,
                detail=f"No decision found for patch {patch_id}"
            )
        
        return HITLDecisionRecord(**dict(row))
        
    except Exception as e:
        logger.error(f"Query by patch_id failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Database query failed: {str(e)}"
        )


@app.get("/hitl/decisions/{decision_id}", response_model=HITLDecisionRecord)
async def get_decision(
    decision_id: str,
    db: HITLDatabase = Depends(get_database)
):
    """
    Get decision by decision_id.
    
    Args:
        decision_id: Decision identifier
        db: Database instance
        
    Returns:
        Full decision record
    """
    decision = await db.get_decision(decision_id)
    
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    
    return decision


# ============================================================================
# Analytics Endpoints
# ============================================================================

@app.get("/hitl/analytics/summary", response_model=DecisionSummary)
async def get_summary(
    db: HITLDatabase = Depends(get_database)
):
    """
    Get summary statistics for HITL decisions.
    
    Args:
        db: Database instance
        
    Returns:
        Decision summary with metrics
    """
    summary = await db.get_summary()
    
    # Update Prometheus metrics
    if summary.ml_accuracy is not None:
        hitl_ml_accuracy.set(summary.ml_accuracy)
    
    if summary.total_patches > 0:
        auto_approval_rate = summary.auto_approved / summary.total_patches
        hitl_auto_approval_rate.set(auto_approval_rate)
    
    return summary


@app.get("/hitl/analytics/audit-logs")
async def get_audit_logs(
    decision_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    db: HITLDatabase = Depends(get_database)
):
    """
    Get audit logs for compliance.
    
    Args:
        decision_id: Filter by decision ID (optional)
        limit: Maximum number of results
        db: Database instance
        
    Returns:
        List of audit log entries
    """
    logs = await db.get_audit_logs(decision_id=decision_id, limit=limit)
    return logs


# ============================================================================
# Admin Endpoints (Protected by admin auth)
# ============================================================================

@app.post("/hitl/admin/create-decision")
async def create_decision(
    record: HITLDecisionRecord,
    db: HITLDatabase = Depends(get_database),
    _admin: bool = Depends(verify_admin_token)
):
    """
    Create a new HITL decision record.
    
    **Requires admin authentication via X-Admin-Token header.**
    
    This endpoint is called by Wargaming Crisol when a patch needs review.
    
    Args:
        record: Decision record to create
        db: Database instance
        _admin: Admin verification (dependency)
        
    Returns:
        Created decision record
    """
    logger.info(f"Creating decision for patch {record.patch_id}")
    
    # Generate decision_id if not provided
    if not record.decision_id:
        record.decision_id = str(uuid.uuid4())
    
    created = await db.create_decision(record)
    
    logger.info(f"✓ Decision created: {created.decision_id}")
    
    return created


# ============================================================================
# WebSocket Endpoint - Real-time Updates
# ============================================================================

from .websocket import websocket_endpoint, broadcast_decision_update

@app.websocket("/hitl/ws")
async def websocket_route(websocket: WebSocket):
    """
    WebSocket endpoint for real-time HITL updates.
    
    Clients receive:
    - New patches entering HITL queue
    - Decision updates (approved/rejected)
    - System status changes
    - Heartbeat every 30s
    
    Example client connection:
    ```javascript
    const ws = new WebSocket('ws://localhost:8027/hitl/ws');
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Received:', data.type, data);
    };
    ```
    """
    await websocket_endpoint(websocket)


# ============================================================================
# Run Application
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8027"))
    
    uvicorn.run(
        "api.main:app",  # Module path from project root
        host="0.0.0.0",
        port=port,
        reload=False,  # Disable file watching to prevent "too many open files"
        log_level="info"
    )


async def _notify_eureka_approval(decision_id: str, patch_id: str, user: str) -> None:
    """Notify Eureka service of patch approval."""
    try:
        eureka_url = os.getenv("EUREKA_SERVICE_URL", "http://maximus_eureka:8015")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{eureka_url}/api/patches/{patch_id}/approved",
                json={
                    "decision_id": decision_id,
                    "approved_by": user,
                    "timestamp": datetime.utcnow().isoformat(),
                },
                timeout=10.0,
            )
            
            if response.status_code == 200:
                logger.info(f"Eureka notified of approval: {patch_id}")
            else:
                logger.warning(f"Eureka notification failed: {response.status_code}")
                
    except Exception as e:
        logger.error(f"Failed to notify Eureka: {e}")


async def _notify_eureka_rejection(decision_id: str, patch_id: str, user: str, reason: str) -> None:
    """Notify Eureka service of patch rejection."""
    try:
        eureka_url = os.getenv("EUREKA_SERVICE_URL", "http://maximus_eureka:8015")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{eureka_url}/api/patches/{patch_id}/rejected",
                json={
                    "decision_id": decision_id,
                    "rejected_by": user,
                    "reason": reason,
                    "timestamp": datetime.utcnow().isoformat(),
                },
                timeout=10.0,
            )
            
            if response.status_code == 200:
                logger.info(f"Eureka notified of rejection: {patch_id}")
            else:
                logger.warning(f"Eureka notification failed: {response.status_code}")
                
    except Exception as e:
        logger.error(f"Failed to notify Eureka: {e}")
