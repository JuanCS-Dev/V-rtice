"""
Mock API Server - In-memory API for E2E testing without database.

Provides all HITL endpoints with in-memory storage for testing.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from hitl.models import (
    DecisionRecord,
    DecisionRequest,
    ReviewContext,
    ReviewListItem,
    ReviewStats,
)
from hitl.test_data_generator import TestDataGenerator
from hitl.websocket_manager import WebSocketConnectionManager
from hitl.websocket_models import WebSocketMessageType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory storage
MOCK_REVIEWS: Dict[str, ReviewContext] = {}
MOCK_DECISIONS: List[DecisionRecord] = []

# WebSocket connection manager
ws_manager = WebSocketConnectionManager()

# Create FastAPI app
app = FastAPI(
    title="HITL Mock API",
    description="In-memory mock API for E2E testing",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _initialize_test_data() -> None:
    """Initialize mock data on startup."""
    global MOCK_REVIEWS

    logger.info("Initializing mock test data...")
    generator = TestDataGenerator()
    test_apvs = generator.generate_test_suite()

    for apv in test_apvs:
        MOCK_REVIEWS[apv.apv_id] = apv

    logger.info(f"✅ Initialized {len(MOCK_REVIEWS)} mock APVs")


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize data on startup."""
    _initialize_test_data()


@app.get("/hitl/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat(), "mode": "MOCK"}


@app.get("/hitl/reviews")
async def get_reviews(
    severity: Optional[str] = Query(None),
    wargame_verdict: Optional[str] = Query(None),
    package_name: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> Dict[str, Any]:
    """Get paginated list of pending reviews with filters."""
    # Filter reviews
    filtered_reviews = list(MOCK_REVIEWS.values())

    if severity:
        filtered_reviews = [r for r in filtered_reviews if r.severity == severity]

    if wargame_verdict:
        filtered_reviews = [
            r for r in filtered_reviews if r.wargame_verdict == wargame_verdict
        ]

    if package_name:
        filtered_reviews = [
            r for r in filtered_reviews if package_name in r.package_name
        ]

    # Sort by priority (desc) and created_at (asc)
    filtered_reviews.sort(key=lambda r: (-r.priority, r.created_at))

    # Pagination
    paginated = filtered_reviews[skip : skip + limit]

    # Convert to ReviewListItem
    review_items = []
    for review in paginated:
        waiting_hours = (datetime.utcnow() - review.created_at).total_seconds() / 3600
        review_items.append(
            ReviewListItem(
                apv_id=review.apv_id,
                apv_code=review.apv_code,
                cve_id=review.cve_id,
                severity=review.severity,
                package_name=review.package_name,
                patch_strategy=review.patch_strategy,
                wargame_verdict=review.wargame_verdict,
                confirmation_confidence=review.confirmation_confidence,
                created_at=review.created_at,
                waiting_since=waiting_hours,
            )
        )

    return {
        "reviews": [r.model_dump() for r in review_items],
        "total": len(filtered_reviews),
        "skip": skip,
        "limit": limit,
    }


@app.get("/hitl/reviews/stats")
async def get_reviews_stats() -> ReviewStats:
    """Get statistics for HITL dashboard."""
    from collections import Counter

    now = datetime.utcnow()

    # Count decisions by timeframe
    decisions_today = [
        d for d in MOCK_DECISIONS if (now - d.decided_at).days == 0
    ]
    decisions_week = [
        d for d in MOCK_DECISIONS if (now - d.decided_at).days <= 7
    ]

    # Decision breakdown
    decision_counts = Counter(d.decision for d in MOCK_DECISIONS)

    # Severity breakdown
    severity_counts = Counter(r.severity for r in MOCK_REVIEWS.values())

    # Calculate timing metrics (mock for now)
    review_times = [3600.0, 7200.0, 1800.0, 5400.0]  # Mock times in seconds

    # Calculate agreement rate (mock)
    human_ai_agreement = 0.85 if MOCK_DECISIONS else 0.0

    return ReviewStats(
        pending_reviews=len(MOCK_REVIEWS),
        total_decisions=len(MOCK_DECISIONS),
        decisions_today=len(decisions_today),
        decisions_this_week=len(decisions_week),
        approved_count=decision_counts.get("approve", 0),
        rejected_count=decision_counts.get("reject", 0),
        modified_count=decision_counts.get("modify", 0),
        escalated_count=decision_counts.get("escalate", 0),
        average_review_time_seconds=sum(review_times) / len(review_times)
        if review_times
        else 0.0,
        median_review_time_seconds=sorted(review_times)[len(review_times) // 2]
        if review_times
        else 0.0,
        fastest_review_seconds=min(review_times) if review_times else 0.0,
        slowest_review_seconds=max(review_times) if review_times else 0.0,
        human_ai_agreement_rate=human_ai_agreement,
        auto_merge_prevention_rate=0.15,
        critical_pending=severity_counts.get("critical", 0),
        high_pending=severity_counts.get("high", 0),
        medium_pending=severity_counts.get("medium", 0),
        low_pending=severity_counts.get("low", 0),
    )


@app.get("/hitl/reviews/{apv_id}")
async def get_review_details(apv_id: str) -> ReviewContext:
    """Get complete review context for specific APV."""
    if apv_id not in MOCK_REVIEWS:
        raise HTTPException(status_code=404, detail=f"APV {apv_id} not found")

    return MOCK_REVIEWS[apv_id]


@app.post("/hitl/decisions")
async def submit_decision(request: DecisionRequest) -> DecisionRecord:
    """Submit human decision on APV."""
    # Validate APV exists
    if request.apv_id not in MOCK_REVIEWS:
        raise HTTPException(status_code=404, detail=f"APV {request.apv_id} not found")

    apv = MOCK_REVIEWS[request.apv_id]

    # Create decision record
    decision_record = DecisionRecord(
        decision_id=str(uuid.uuid4()),
        apv_id=request.apv_id,
        apv_code=apv.apv_code,
        decision=request.decision,
        justification=request.justification,
        confidence=request.confidence,
        modifications=request.modifications,
        reviewer_name=request.reviewer_name,
        reviewer_email=request.reviewer_email,
        cve_id=apv.cve_id,
        severity=apv.severity,
        patch_strategy=apv.patch_strategy,
        wargame_verdict=apv.wargame_verdict,
        action_taken=_map_decision_to_action(request.decision),
        outcome_notes=f"Decision: {request.decision} | Confidence: {request.confidence:.2f}",
        decided_at=datetime.utcnow(),
        action_completed_at=datetime.utcnow(),
    )

    # Store decision
    MOCK_DECISIONS.append(decision_record)

    # Remove from pending reviews (simulate)
    # In real implementation, would update status in DB
    logger.info(
        f"✅ Decision recorded: {request.decision.upper()} for {apv.apv_code} "
        f"by {request.reviewer_name}"
    )

    # Broadcast decision to WebSocket subscribers
    import asyncio
    asyncio.create_task(
        ws_manager.broadcast_decision(
            decision_id=decision_record.decision_id,
            apv_id=decision_record.apv_id,
            apv_code=decision_record.apv_code,
            decision=decision_record.decision,
            reviewer_name=decision_record.reviewer_name,
            action_taken=decision_record.action_taken,
        )
    )

    # Broadcast stats update
    now = datetime.utcnow()
    decisions_today = [d for d in MOCK_DECISIONS if (now - d.decided_at).days == 0]
    asyncio.create_task(
        ws_manager.broadcast_stats_update(
            pending_reviews=len(MOCK_REVIEWS),
            total_decisions=len(MOCK_DECISIONS),
            decisions_today=len(decisions_today),
        )
    )

    return decision_record


def _map_decision_to_action(decision: str) -> str:
    """Map decision to action taken."""
    action_map = {
        "approve": "pr_merged",
        "reject": "pr_closed",
        "modify": "changes_requested",
        "escalate": "assigned_to_lead",
    }
    return action_map.get(decision, "unknown")


@app.websocket("/hitl/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for real-time updates.

    Clients can subscribe to channels: 'apvs', 'decisions', 'stats'
    """
    client_id = await ws_manager.connect(websocket)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            message_type = data.get("type")

            if message_type == WebSocketMessageType.PING:
                # Respond to ping
                await websocket.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})

            elif message_type == WebSocketMessageType.SUBSCRIBE:
                # Subscribe to channels
                channels = data.get("channels", [])
                await ws_manager.subscribe(client_id, channels)
                await websocket.send_json({
                    "type": "subscription_confirmed",
                    "channels": channels,
                    "timestamp": datetime.utcnow().isoformat(),
                })

            elif message_type == WebSocketMessageType.UNSUBSCRIBE:
                # Unsubscribe from channels
                channels = data.get("channels", [])
                await ws_manager.unsubscribe(client_id, channels)
                await websocket.send_json({
                    "type": "unsubscription_confirmed",
                    "channels": channels,
                    "timestamp": datetime.utcnow().isoformat(),
                })

            else:
                # Unknown message type - send error but keep connection alive
                if message_type is None:
                    error_msg = "Message missing 'type' field"
                else:
                    error_msg = f"Unknown message type: {message_type}"

                await websocket.send_json({
                    "type": "error",
                    "error_message": error_msg,
                    "timestamp": datetime.utcnow().isoformat(),
                })
                # Connection continues - client can send more messages

    except WebSocketDisconnect:
        await ws_manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        await ws_manager.disconnect(client_id)


@app.get("/hitl/metrics")
async def get_metrics() -> Dict[str, Any]:
    """Get Prometheus metrics."""
    return {
        "hitl_pending_reviews": len(MOCK_REVIEWS),
        "hitl_total_decisions": len(MOCK_DECISIONS),
        "hitl_decisions_by_type": {
            "approve": len([d for d in MOCK_DECISIONS if d.decision == "approve"]),
            "reject": len([d for d in MOCK_DECISIONS if d.decision == "reject"]),
            "modify": len([d for d in MOCK_DECISIONS if d.decision == "modify"]),
            "escalate": len([d for d in MOCK_DECISIONS if d.decision == "escalate"]),
        },
        "hitl_websocket_connections": ws_manager.get_connection_count(),
    }


if __name__ == "__main__":
    import uvicorn

    logger.info("🚀 Starting HITL Mock API Server...")
    logger.info("📍 http://localhost:8003")
    logger.info("📚 Docs: http://localhost:8003/docs")

    uvicorn.run(app, host="0.0.0.0", port=8003, log_level="info")
