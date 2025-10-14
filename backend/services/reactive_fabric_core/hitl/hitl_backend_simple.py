"""
HITL Backend - Simple Version (for testing)
No authentication, just API endpoints
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
from enum import Enum
import uvicorn

# ============================================================================
# MODELS
# ============================================================================

class DecisionStatus(str, Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"


class DecisionPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Decision(BaseModel):
    decision_id: str
    analysis_id: str
    incident_id: str
    threat_level: str
    source_ip: str
    attributed_actor: str
    confidence: float
    iocs: List[str]
    ttps: List[str]
    recommended_actions: List[str]
    forensic_summary: str
    priority: str
    status: str
    created_at: datetime
    updated_at: datetime


class DecisionCreate(BaseModel):
    status: str
    approved_actions: List[str]
    notes: str


class EscalateRequest(BaseModel):
    reason: str


class SystemStatus(BaseModel):
    status: str
    pending_decisions: int
    critical_pending: int
    in_review_decisions: int
    total_decisions_today: int


class DecisionStats(BaseModel):
    total_pending: int
    critical_pending: int
    high_pending: int
    medium_pending: int
    low_pending: int
    total_approved: int
    total_rejected: int
    total_escalated: int
    approval_rate: float
    avg_response_time_minutes: float
    oldest_pending_minutes: float


# ============================================================================
# IN-MEMORY DATABASE
# ============================================================================

decisions_db = {}
responses_db = {}

# Sample data for testing
sample_decisions = [
    {
        "decision_id": "DEC-001",
        "analysis_id": "CANDI-apt28-001",
        "incident_id": "INC-2025-001",
        "threat_level": "APT",
        "source_ip": "185.86.148.10",
        "attributed_actor": "APT28 (Fancy Bear)",
        "confidence": 94.5,
        "iocs": ["185.86.148.10", "hxxp://apt28-c2.example.com/implant.elf"],
        "ttps": ["T1566.001", "T1059.003", "T1053.005"],
        "recommended_actions": ["block_ip", "quarantine_system", "escalate_to_soc"],
        "forensic_summary": "APT28 C2 communication detected with custom malware",
        "priority": "critical",
        "status": "pending",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    },
    {
        "decision_id": "DEC-002",
        "analysis_id": "CANDI-lazarus-005",
        "incident_id": "INC-2025-002",
        "threat_level": "TARGETED",
        "source_ip": "10.0.5.100",
        "attributed_actor": "Lazarus Group",
        "confidence": 89.2,
        "iocs": ["10.0.5.100", "malware.exe"],
        "ttps": ["T1566", "T1059"],
        "recommended_actions": ["block_ip", "quarantine_system"],
        "forensic_summary": "Lazarus Group targeting financial systems",
        "priority": "high",
        "status": "pending",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
]

for dec in sample_decisions:
    decisions_db[dec["analysis_id"]] = dec

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="HITL Console API (Simple)",
    description="Human-in-the-Loop Decision System - Testing Version",
    version="1.0.0-simple"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "message": "HITL Console API is operational (Simple Mode)",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/api/status")
def get_status():
    pending = sum(1 for d in decisions_db.values() if d["status"] == "pending")
    critical = sum(1 for d in decisions_db.values() if d["status"] == "pending" and d["priority"] == "critical")
    in_review = sum(1 for d in decisions_db.values() if d["status"] == "in_review")

    return {
        "status": "operational",
        "pending_decisions": pending,
        "critical_pending": critical,
        "in_review_decisions": in_review,
        "total_decisions_today": len(decisions_db)
    }


@app.get("/api/decisions/pending")
def list_pending_decisions(priority: Optional[str] = None):
    result = []

    for dec in decisions_db.values():
        if dec["status"] in ["pending", "in_review"]:
            if priority is None or dec["priority"] == priority:
                result.append(dec)

    return result


@app.get("/api/decisions/{analysis_id}")
def get_decision(analysis_id: str):
    if analysis_id not in decisions_db:
        raise HTTPException(status_code=404, detail="Decision not found")

    return decisions_db[analysis_id]


@app.get("/api/decisions/{analysis_id}/response")
def get_decision_response(analysis_id: str):
    if analysis_id not in responses_db:
        raise HTTPException(status_code=404, detail="Decision not yet made")

    return responses_db[analysis_id]


@app.post("/api/decisions/{analysis_id}/decide")
def make_decision(analysis_id: str, decision: DecisionCreate):
    if analysis_id not in decisions_db:
        raise HTTPException(status_code=404, detail="Decision not found")

    # Update decision status
    decisions_db[analysis_id]["status"] = decision.status
    decisions_db[analysis_id]["updated_at"] = datetime.now(timezone.utc)

    # Create response
    response = {
        "decision_id": decisions_db[analysis_id]["decision_id"],
        "analysis_id": analysis_id,
        "status": decision.status,
        "approved_actions": decision.approved_actions,
        "notes": decision.notes,
        "decided_by": "test-user",
        "decided_at": datetime.now(timezone.utc)
    }

    responses_db[analysis_id] = response

    return response


@app.post("/api/decisions/{analysis_id}/escalate")
def escalate_decision(analysis_id: str, escalate: EscalateRequest):
    if analysis_id not in decisions_db:
        raise HTTPException(status_code=404, detail="Decision not found")

    # Update decision status
    decisions_db[analysis_id]["status"] = "escalated"
    decisions_db[analysis_id]["updated_at"] = datetime.now(timezone.utc)

    # Create response
    response = {
        "decision_id": decisions_db[analysis_id]["decision_id"],
        "analysis_id": analysis_id,
        "status": "escalated",
        "approved_actions": [],
        "notes": escalate.reason,
        "decided_by": "test-user",
        "decided_at": datetime.now(timezone.utc)
    }

    responses_db[analysis_id] = response

    return response


@app.get("/api/decisions/stats/summary")
def get_stats():
    pending = [d for d in decisions_db.values() if d["status"] == "pending"]

    critical_pending = sum(1 for d in pending if d["priority"] == "critical")
    high_pending = sum(1 for d in pending if d["priority"] == "high")
    medium_pending = sum(1 for d in pending if d["priority"] == "medium")
    low_pending = sum(1 for d in pending if d["priority"] == "low")

    approved = sum(1 for d in decisions_db.values() if d["status"] == "approved")
    rejected = sum(1 for d in decisions_db.values() if d["status"] == "rejected")
    escalated = sum(1 for d in decisions_db.values() if d["status"] == "escalated")

    total_resolved = approved + rejected + escalated
    approval_rate = (approved / total_resolved * 100) if total_resolved > 0 else 0.0

    return {
        "total_pending": len(pending),
        "critical_pending": critical_pending,
        "high_pending": high_pending,
        "medium_pending": medium_pending,
        "low_pending": low_pending,
        "total_approved": approved,
        "total_rejected": rejected,
        "total_escalated": escalated,
        "approval_rate": approval_rate,
        "avg_response_time_minutes": 12.5,
        "oldest_pending_minutes": 45.2
    }


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("HITL Console Backend - Simple Mode (Testing)")
    print("=" * 60)
    print(f"Starting server on http://0.0.0.0:8001")
    print(f"Health check: http://localhost:8001/health")
    print(f"API Status: http://localhost:8001/api/status")
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
