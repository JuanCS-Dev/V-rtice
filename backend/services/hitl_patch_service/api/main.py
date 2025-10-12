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
import uuid
import logging
from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

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
except ValueError as e:
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
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

async def get_database() -> HITLDatabase:
    """Get database instance."""
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    return db


# Simulate user authentication (TODO: implement real auth)
async def get_current_user() -> str:
    """Get current user from auth token."""
    # TODO: Extract from JWT token or session
    return "operator@maximus.ai"


# ============================================================================
# Health & Metrics
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "hitl-patch-service",
        "version": "1.0.0"
    }


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
    
    # TODO: Notify Eureka to proceed with deployment
    
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
    
    # TODO: Notify Eureka patch was rejected
    
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
    # TODO: Need to add patch_id index to query by patch_id
    # For now, this is a placeholder
    raise HTTPException(status_code=501, detail="Not yet implemented - use decision_id instead")


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
# Admin Endpoints (TODO: Require admin auth)
# ============================================================================

@app.post("/hitl/admin/create-decision")
async def create_decision(
    record: HITLDecisionRecord,
    db: HITLDatabase = Depends(get_database)
):
    """
    Create a new HITL decision record.
    
    This endpoint is called by Wargaming Crisol when a patch needs review.
    
    Args:
        record: Decision record to create
        db: Database instance
        
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
# Run Application
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8027"))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
