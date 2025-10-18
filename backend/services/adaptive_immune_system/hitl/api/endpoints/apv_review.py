"""
APV Review Endpoints - List and retrieve APVs pending human review.

Endpoints:
- GET /hitl/reviews - List pending reviews (paginated, filterable)
- GET /hitl/reviews/{apv_id} - Get full review context for specific APV
- GET /hitl/reviews/stats - Get statistics for dashboard
"""

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from ...models import ReviewContext, ReviewListItem, ReviewStats

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hitl/reviews", tags=["HITL Reviews"])


@router.get("/", response_model=List[ReviewListItem])
async def list_pending_reviews(
    severity: Optional[str] = Query(None, description="Filter by severity (critical/high/medium/low)"),
    patch_strategy: Optional[str] = Query(None, description="Filter by patch strategy"),
    wargame_verdict: Optional[str] = Query(None, description="Filter by wargame verdict"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
) -> List[ReviewListItem]:
    """
    List APVs pending human review.

    Filters:
    - severity: Filter by CVE severity
    - patch_strategy: Filter by patch strategy
    - wargame_verdict: Filter by wargame verdict
    - limit: Maximum results (default 50, max 200)
    - offset: Pagination offset

    Returns:
        List of ReviewListItem (abbreviated APV info)

    Example:
        GET /hitl/reviews?severity=critical&limit=10
        GET /hitl/reviews?wargame_verdict=partial
    """
    logger.info(
        f"Listing reviews: severity={severity}, strategy={patch_strategy}, "
        f"verdict={wargame_verdict}, limit={limit}, offset={offset}"
    )

    try:
        # In production: Query PostgreSQL for pending APVs
        # SELECT * FROM apvs
        # WHERE status = 'pending_hitl_review'
        # AND severity = ? (if filter)
        # ORDER BY priority DESC, created_at ASC
        # LIMIT ? OFFSET ?

        # Mock data for now
        mock_reviews = _generate_mock_reviews()

        # Apply filters
        filtered = mock_reviews

        if severity:
            filtered = [r for r in filtered if r.severity.lower() == severity.lower()]

        if patch_strategy:
            filtered = [r for r in filtered if r.patch_strategy == patch_strategy]

        if wargame_verdict:
            filtered = [r for r in filtered if r.wargame_verdict == wargame_verdict]

        # Apply pagination
        paginated = filtered[offset : offset + limit]

        logger.info(f"Returning {len(paginated)} reviews (total: {len(filtered)})")

        return paginated

    except Exception as e:
        logger.error(f"Failed to list reviews: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list reviews: {str(e)}")


@router.get("/stats", response_model=ReviewStats)
async def get_review_stats() -> ReviewStats:
    """
    Get statistics for HITL dashboard.

    Returns:
        ReviewStats with counts, timing metrics, and agreement rates

    Example:
        GET /hitl/reviews/stats
    """
    logger.info("Getting review statistics")

    try:
        # In production: Query PostgreSQL for statistics
        # SELECT
        #   COUNT(*) FILTER (WHERE status = 'pending_hitl_review') as pending_reviews,
        #   COUNT(*) FILTER (WHERE decided_at >= NOW() - INTERVAL '1 day') as decisions_today,
        #   AVG(EXTRACT(EPOCH FROM (decided_at - created_at))) as avg_review_time,
        #   ...
        # FROM apvs

        # Mock data for now
        stats = ReviewStats(
            pending_reviews=12,
            total_decisions=487,
            decisions_today=23,
            decisions_this_week=156,
            approved_count=342,
            rejected_count=89,
            modified_count=45,
            escalated_count=11,
            average_review_time_seconds=842.5,
            median_review_time_seconds=623.0,
            fastest_review_seconds=87.0,
            slowest_review_seconds=3421.0,
            human_ai_agreement_rate=0.87,
            auto_merge_prevention_rate=0.13,
            critical_pending=3,
            high_pending=5,
            medium_pending=3,
            low_pending=1,
        )

        logger.info(f"Returning stats: {stats.pending_reviews} pending")

        return stats

    except Exception as e:
        logger.error(f"Failed to get stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.get("/{apv_id}", response_model=ReviewContext)
async def get_review_details(apv_id: str) -> ReviewContext:
    """
    Get complete review context for specific APV.

    Args:
        apv_id: APV identifier (UUID)

    Returns:
        ReviewContext with full details (CVE, patch, scores, wargame results)

    Raises:
        404: APV not found
        500: Database error

    Example:
        GET /hitl/reviews/550e8400-e29b-41d4-a716-446655440000
    """
    logger.info(f"Getting review details for {apv_id}")

    try:
        # In production: Query PostgreSQL for APV
        # SELECT * FROM apvs WHERE apv_id = ?
        # JOIN cves ON apvs.cve_id = cves.id
        # JOIN patches ON apvs.patch_id = patches.id
        # JOIN wargame_results ON apvs.id = wargame_results.apv_id

        # Mock data for now
        context = _generate_mock_review_context(apv_id)

        if not context:
            raise HTTPException(status_code=404, detail=f"APV {apv_id} not found")

        logger.info(f"Returning review context: {context.apv_code}")

        return context

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get review details: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get review details: {str(e)}"
        )


# --- Mock Data Generators (for MVP) ---


def _generate_mock_reviews() -> List[ReviewListItem]:
    """Generate mock review list items."""
    now = datetime.utcnow()

    return [
        ReviewListItem(
            apv_id="550e8400-e29b-41d4-a716-446655440001",
            apv_code="APV-20251013-001",
            cve_id="CVE-2024-1234",
            severity="critical",
            package_name="django",
            patch_strategy="version_bump",
            wargame_verdict="success",
            confirmation_confidence=0.95,
            created_at=now,
            waiting_since=2.5,
        ),
        ReviewListItem(
            apv_id="550e8400-e29b-41d4-a716-446655440002",
            apv_code="APV-20251013-002",
            cve_id="CVE-2024-5678",
            severity="high",
            package_name="requests",
            patch_strategy="code_rewrite",
            wargame_verdict="partial",
            confirmation_confidence=0.78,
            created_at=now,
            waiting_since=4.2,
        ),
        ReviewListItem(
            apv_id="550e8400-e29b-41d4-a716-446655440003",
            apv_code="APV-20251013-003",
            cve_id="CVE-2024-9012",
            severity="high",
            package_name="flask",
            patch_strategy="version_bump",
            wargame_verdict="success",
            confirmation_confidence=0.92,
            created_at=now,
            waiting_since=1.8,
        ),
        ReviewListItem(
            apv_id="550e8400-e29b-41d4-a716-446655440004",
            apv_code="APV-20251013-004",
            cve_id="CVE-2024-3456",
            severity="medium",
            package_name="express",
            patch_strategy="config_change",
            wargame_verdict="inconclusive",
            confirmation_confidence=0.65,
            created_at=now,
            waiting_since=6.1,
        ),
        ReviewListItem(
            apv_id="550e8400-e29b-41d4-a716-446655440005",
            apv_code="APV-20251013-005",
            cve_id="CVE-2024-7890",
            severity="critical",
            package_name="lodash",
            patch_strategy="version_bump",
            wargame_verdict="failure",
            confirmation_confidence=0.58,
            created_at=now,
            waiting_since=8.3,
        ),
    ]


def _generate_mock_review_context(apv_id: str) -> Optional[ReviewContext]:
    """Generate mock review context."""
    now = datetime.utcnow()

    # Simple mock: only return context for first APV
    if apv_id != "550e8400-e29b-41d4-a716-446655440001":
        return None

    return ReviewContext(
        # APV Information
        apv_id=apv_id,
        apv_code="APV-20251013-001",
        priority=9,
        status="pending_hitl_review",
        # CVE Information
        cve_id="CVE-2024-1234",
        cve_title="SQL Injection in Django ORM",
        cve_description="A SQL injection vulnerability was found in Django's ORM when using raw() queries with unsanitized user input.",
        cvss_score=9.8,
        severity="critical",
        cwe_ids=["CWE-89"],
        # Dependency Information
        package_name="django",
        package_version="4.2.0",
        package_ecosystem="pypi",
        fixed_version="4.2.7",
        # Vulnerability Details
        vulnerable_code_signature="User.objects.raw(f'SELECT * FROM users WHERE id = {user_id}')",
        vulnerable_code_type="raw_query",
        affected_files=["backend/api/views.py", "backend/api/models.py"],
        # Confirmation Scores
        confirmed=True,
        confirmation_confidence=0.95,
        static_confidence=0.92,
        dynamic_confidence=0.98,
        false_positive_probability=0.05,
        # Patch Information
        patch_strategy="version_bump",
        patch_description="Upgrade Django from 4.2.0 to 4.2.7 (security release)",
        patch_diff="""--- a/requirements.txt
+++ b/requirements.txt
-django==4.2.0
+django==4.2.7
""",
        patch_confidence=0.98,
        patch_risk_level="low",
        # Validation Results
        validation_passed=True,
        validation_confidence=0.96,
        validation_warnings=[],
        # PR Information
        pr_number=1234,
        pr_url="https://github.com/user/repo/pull/1234",
        pr_branch="fix/cve-2024-1234",
        # Wargaming Results
        wargame_verdict="success",
        wargame_confidence=0.94,
        wargame_run_url="https://github.com/user/repo/actions/runs/12345",
        wargame_evidence={
            "exploit_exit_before": 1,
            "exploit_exit_after": 0,
            "expected_exit_before": 1,
            "expected_exit_after": 0,
            "workflow_duration_seconds": 145.2,
            "all_steps_completed": True,
        },
        # Timestamps
        created_at=now,
        updated_at=now,
    )
