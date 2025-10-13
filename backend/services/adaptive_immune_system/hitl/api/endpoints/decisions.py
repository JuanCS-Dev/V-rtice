"""
Decision Endpoints - Submit and track human decisions on APVs.

Endpoints:
- POST /hitl/decisions - Submit decision on APV
- GET /hitl/decisions/{decision_id} - Get decision record
- GET /hitl/decisions/history/{apv_id} - Get decision history for APV
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...decision_engine import DecisionEngine
from ...models import DecisionRequest, DecisionRecord, ReviewContext

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hitl/decisions", tags=["HITL Decisions"])


# Dependency: Get DecisionEngine instance
def get_decision_engine() -> DecisionEngine:
    """
    Get DecisionEngine instance.

    In production: Load config from environment variables.
    """
    # TODO: Load from config
    github_token = "ghp_mock_token"  # Would be from env: GITHUB_TOKEN
    repository_owner = "vertice-dev"  # Would be from env: GITHUB_OWNER
    repository_name = "backend"  # Would be from env: GITHUB_REPO

    return DecisionEngine(
        github_token=github_token,
        repository_owner=repository_owner,
        repository_name=repository_name,
    )


# Dependency: Get database session
async def get_db_session() -> AsyncSession:
    """
    Get database session.

    In production: Use SQLAlchemy async session pool.
    """
    # TODO: Implement actual database session
    # from ...database import AsyncSessionLocal
    # async with AsyncSessionLocal() as session:
    #     yield session
    raise NotImplementedError("Database session not implemented yet")


@router.post("/", response_model=DecisionRecord, status_code=201)
async def submit_decision(
    decision: DecisionRequest,
    engine: DecisionEngine = Depends(get_decision_engine),
    # db_session: AsyncSession = Depends(get_db_session),  # Disabled for MVP
) -> DecisionRecord:
    """
    Submit human decision on APV.

    Workflow:
    1. Validate decision (APV exists, decision type valid, etc.)
    2. Determine action (merge PR, close PR, request changes, escalate)
    3. Execute action on GitHub
    4. Log decision to database
    5. Send notification via RabbitMQ
    6. Return decision record

    Args:
        decision: DecisionRequest with apv_id, decision, justification, etc.

    Returns:
        DecisionRecord with outcome

    Raises:
        400: Invalid decision (validation failed)
        404: APV not found
        500: Action execution failed

    Example:
        POST /hitl/decisions
        {
            "apv_id": "550e8400-e29b-41d4-a716-446655440001",
            "decision": "approve",
            "justification": "Patch validated successfully, wargame passed with 94% confidence.",
            "confidence": 0.95,
            "reviewer_name": "Alice Johnson",
            "reviewer_email": "alice@example.com"
        }
    """
    logger.info(
        f"Received decision: {decision.decision} on {decision.apv_id} by {decision.reviewer_name}"
    )

    try:
        # Get review context (full APV details)
        context = await _get_review_context(decision.apv_id)

        if not context:
            raise HTTPException(
                status_code=404, detail=f"APV {decision.apv_id} not found"
            )

        # Process decision (validate, execute action, log)
        # Note: Using mock db_session for MVP
        mock_db_session = None  # type: ignore
        record = await engine.process_decision(
            decision=decision,
            context=context,
            db_session=mock_db_session,
        )

        logger.info(
            f"Decision processed: {record.decision_id} - {record.decision} → {record.action_taken}"
        )

        # TODO: Send notification via RabbitMQ
        # await _send_decision_notification(record)

        return record

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Invalid decision: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        logger.error(f"Failed to execute action: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Action execution failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error processing decision: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/{decision_id}", response_model=DecisionRecord)
async def get_decision(decision_id: str) -> DecisionRecord:
    """
    Get decision record by ID.

    Args:
        decision_id: Decision identifier (DEC-YYYYMMDD-HHMMSS-APVID)

    Returns:
        DecisionRecord with full details

    Raises:
        404: Decision not found
        500: Database error

    Example:
        GET /hitl/decisions/DEC-20251013-143022-550e8400
    """
    logger.info(f"Getting decision record: {decision_id}")

    try:
        # In production: Query PostgreSQL
        # SELECT * FROM decisions WHERE decision_id = ?

        # Mock data for now
        record = _generate_mock_decision_record(decision_id)

        if not record:
            raise HTTPException(
                status_code=404, detail=f"Decision {decision_id} not found"
            )

        return record

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get decision: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get decision: {str(e)}")


@router.get("/history/{apv_id}", response_model=List[DecisionRecord])
async def get_decision_history(apv_id: str) -> List[DecisionRecord]:
    """
    Get decision history for APV.

    Useful for APVs with multiple review cycles (modify → re-review).

    Args:
        apv_id: APV identifier (UUID)

    Returns:
        List of DecisionRecord (chronological order)

    Example:
        GET /hitl/decisions/history/550e8400-e29b-41d4-a716-446655440001
    """
    logger.info(f"Getting decision history for APV: {apv_id}")

    try:
        # In production: Query PostgreSQL
        # SELECT * FROM decisions
        # WHERE apv_id = ?
        # ORDER BY decided_at ASC

        # Mock data for now
        history = _generate_mock_decision_history(apv_id)

        return history

    except Exception as e:
        logger.error(f"Failed to get decision history: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get decision history: {str(e)}"
        )


# --- Helper Functions ---


async def _get_review_context(apv_id: str) -> Optional[ReviewContext]:
    """
    Get review context for APV.

    In production: Query PostgreSQL for full APV details.
    """
    # Import here to avoid circular dependency
    from .apv_review import _generate_mock_review_context

    return _generate_mock_review_context(apv_id)


def _generate_mock_decision_record(decision_id: str) -> Optional[DecisionRecord]:
    """Generate mock decision record."""
    from datetime import datetime

    if decision_id != "DEC-20251013-143022-550e8400":
        return None

    return DecisionRecord(
        decision_id=decision_id,
        apv_id="550e8400-e29b-41d4-a716-446655440001",
        apv_code="APV-20251013-001",
        decision="approve",
        justification="Patch validated successfully. Wargame passed with 94% confidence. Django upgrade to 4.2.7 is well-tested and low-risk.",
        confidence=0.95,
        modifications=None,
        reviewer_name="Alice Johnson",
        reviewer_email="alice@example.com",
        cve_id="CVE-2024-1234",
        severity="critical",
        patch_strategy="version_bump",
        wargame_verdict="success",
        action_taken="pr_merged",
        outcome_notes="Merged at abc12345",
        decided_at=datetime.utcnow(),
        action_completed_at=datetime.utcnow(),
    )


def _generate_mock_decision_history(apv_id: str) -> List[DecisionRecord]:
    """Generate mock decision history."""
    from datetime import datetime, timedelta

    if apv_id != "550e8400-e29b-41d4-a716-446655440001":
        return []

    now = datetime.utcnow()

    return [
        DecisionRecord(
            decision_id="DEC-20251013-120000-550e8400",
            apv_id=apv_id,
            apv_code="APV-20251013-001",
            decision="modify",
            justification="Wargame result inconclusive. Requesting additional testing with edge case inputs.",
            confidence=0.75,
            modifications={"additional_tests": ["edge_case_1", "edge_case_2"]},
            reviewer_name="Bob Smith",
            reviewer_email="bob@example.com",
            cve_id="CVE-2024-1234",
            severity="critical",
            patch_strategy="version_bump",
            wargame_verdict="inconclusive",
            action_taken="changes_requested",
            outcome_notes="Changes requested",
            decided_at=now - timedelta(hours=2),
            action_completed_at=now - timedelta(hours=2),
        ),
        DecisionRecord(
            decision_id="DEC-20251013-143022-550e8400",
            apv_id=apv_id,
            apv_code="APV-20251013-001",
            decision="approve",
            justification="Additional tests passed. Wargame now shows 94% confidence. Approving for merge.",
            confidence=0.95,
            modifications=None,
            reviewer_name="Alice Johnson",
            reviewer_email="alice@example.com",
            cve_id="CVE-2024-1234",
            severity="critical",
            patch_strategy="version_bump",
            wargame_verdict="success",
            action_taken="pr_merged",
            outcome_notes="Merged at abc12345",
            decided_at=now,
            action_completed_at=now,
        ),
    ]
