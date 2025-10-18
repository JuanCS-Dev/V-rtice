"""
Triage Engine - APV priority scoring and lifecycle management.

Manages APV triage workflow:
- Dynamic priority recalculation
- Status transitions (pending_triage -> triaged -> dispatched -> resolved)
- Automatic escalation for critical APVs
- Human-in-the-loop integration
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy import and_, desc

from ..database import DatabaseClient
from ..database.models import APV, HITLDecision

logger = logging.getLogger(__name__)


class TriageEngine:
    """
    Manages APV triage and prioritization.

    Features:
    - Multi-factor priority scoring
    - Automatic escalation rules
    - Status lifecycle management
    - HITL decision tracking
    - Metrics and reporting
    """

    # Priority thresholds
    PRIORITY_CRITICAL = 9  # Immediate action required
    PRIORITY_HIGH = 7  # Action required within 24h
    PRIORITY_MEDIUM = 5  # Action required within 7 days
    PRIORITY_LOW = 3  # Action required within 30 days

    # Status transitions
    VALID_TRANSITIONS = {
        "pending_triage": ["triaged", "false_positive", "suppressed"],
        "triaged": ["dispatched", "false_positive", "suppressed"],
        "dispatched": ["in_remediation", "false_positive", "suppressed"],
        "in_remediation": ["remedy_generated", "failed"],
        "remedy_generated": ["in_wargame", "failed"],
        "in_wargame": ["wargame_passed", "wargame_failed"],
        "wargame_passed": ["pending_hitl"],
        "wargame_failed": ["failed"],
        "pending_hitl": ["hitl_approved", "hitl_rejected"],
        "hitl_approved": ["resolved"],
        "hitl_rejected": ["suppressed"],
        "failed": ["triaged"],  # Allow retry
        "false_positive": [],  # Terminal state
        "suppressed": [],  # Terminal state
        "resolved": [],  # Terminal state
    }

    def __init__(self, db_client: DatabaseClient):
        """
        Initialize triage engine.

        Args:
            db_client: Database client instance
        """
        self.db_client = db_client
        logger.info("TriageEngine initialized")

    def triage_apvs(
        self,
        project: Optional[str] = None,
        auto_dispatch_critical: bool = True,
    ) -> Dict[str, int]:
        """
        Triage all pending APVs.

        Args:
            project: Optional project filter
            auto_dispatch_critical: Automatically dispatch critical APVs

        Returns:
            Dictionary with triage statistics
        """
        logger.info(f"🔍 Starting APV triage" + (f" for project: {project}" if project else ""))

        stats = {
            "total_triaged": 0,
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "auto_dispatched": 0,
            "escalated_to_hitl": 0,
        }

        with self.db_client.get_session() as session:
            # Get pending APVs
            query = session.query(APV).filter(APV.status == "pending_triage")

            if project:
                query = query.filter(APV.project == project)

            pending_apvs = query.all()

            logger.info(f"Found {len(pending_apvs)} APVs pending triage")

            for apv in pending_apvs:
                # Recalculate priority
                new_priority = self._recalculate_priority(apv)

                if new_priority != apv.priority:
                    logger.info(
                        f"Priority updated for {apv.apv_code}: "
                        f"{apv.priority} -> {new_priority}"
                    )
                    apv.priority = new_priority

                # Update status to triaged
                apv.status = "triaged"
                apv.triaged_at = datetime.utcnow()

                stats["total_triaged"] += 1

                # Categorize by priority
                if new_priority >= self.PRIORITY_CRITICAL:
                    stats["critical"] += 1

                    # Auto-dispatch critical APVs
                    if auto_dispatch_critical:
                        apv.status = "dispatched"
                        apv.dispatched_at = datetime.utcnow()
                        stats["auto_dispatched"] += 1
                        logger.info(f"🚨 Auto-dispatched critical APV: {apv.apv_code}")

                elif new_priority >= self.PRIORITY_HIGH:
                    stats["high"] += 1

                elif new_priority >= self.PRIORITY_MEDIUM:
                    stats["medium"] += 1

                else:
                    stats["low"] += 1

            session.commit()

            logger.info(
                f"✅ Triage complete: {stats['total_triaged']} APVs triaged, "
                f"{stats['auto_dispatched']} auto-dispatched"
            )

        return stats

    def update_apv_status(
        self,
        apv_id: str,
        new_status: str,
        reason: Optional[str] = None,
        updated_by: Optional[str] = None,
    ) -> bool:
        """
        Update APV status with validation.

        Args:
            apv_id: APV UUID
            new_status: New status
            reason: Optional reason for status change
            updated_by: Optional user identifier

        Returns:
            True if status updated successfully

        Raises:
            ValueError: If status transition is invalid
        """
        with self.db_client.get_session() as session:
            apv = session.query(APV).filter(APV.id == apv_id).first()

            if not apv:
                raise ValueError(f"APV not found: {apv_id}")

            # Validate transition
            if not self._is_valid_transition(apv.status, new_status):
                raise ValueError(
                    f"Invalid status transition: {apv.status} -> {new_status}"
                )

            old_status = apv.status
            apv.status = new_status

            # Update timestamp fields
            if new_status == "triaged":
                apv.triaged_at = datetime.utcnow()
            elif new_status == "dispatched":
                apv.dispatched_at = datetime.utcnow()
            elif new_status == "resolved":
                apv.resolved_at = datetime.utcnow()

            # Add metadata
            if not apv.metadata:
                apv.metadata = {}

            apv.metadata["status_history"] = apv.metadata.get("status_history", [])
            apv.metadata["status_history"].append({
                "old_status": old_status,
                "new_status": new_status,
                "timestamp": datetime.utcnow().isoformat(),
                "reason": reason,
                "updated_by": updated_by,
            })

            session.commit()

            logger.info(
                f"Status updated for {apv.apv_code}: {old_status} -> {new_status}"
            )

            return True

    def escalate_to_hitl(
        self,
        apv_id: str,
        reason: str,
        urgency: str = "normal",
    ) -> bool:
        """
        Escalate APV to Human-in-the-Loop review.

        Args:
            apv_id: APV UUID
            reason: Reason for escalation
            urgency: Urgency level (low, normal, high, critical)

        Returns:
            True if escalated successfully
        """
        with self.db_client.get_session() as session:
            apv = session.query(APV).filter(APV.id == apv_id).first()

            if not apv:
                raise ValueError(f"APV not found: {apv_id}")

            # Update APV status
            apv.status = "pending_hitl"

            # Create HITL decision record
            hitl_decision = HITLDecision(
                apv_id=apv.id,
                reason=reason,
                urgency=urgency,
                status="pending",
            )

            session.add(hitl_decision)
            session.commit()

            logger.info(f"🔺 APV escalated to HITL: {apv.apv_code} - {reason}")

            return True

    def get_pending_hitl_apvs(self) -> List[APV]:
        """
        Get APVs pending HITL review.

        Returns:
            List of APVs sorted by priority
        """
        with self.db_client.get_session() as session:
            apvs = (
                session.query(APV)
                .filter(APV.status == "pending_hitl")
                .order_by(desc(APV.priority), APV.created_at)
                .all()
            )

            return apvs

    def get_critical_apvs(
        self,
        project: Optional[str] = None,
        age_days: int = 7,
    ) -> List[APV]:
        """
        Get critical APVs requiring immediate attention.

        Args:
            project: Optional project filter
            age_days: Consider APVs older than N days

        Returns:
            List of critical APVs
        """
        cutoff_date = datetime.utcnow() - timedelta(days=age_days)

        with self.db_client.get_session() as session:
            query = (
                session.query(APV)
                .filter(
                    and_(
                        APV.priority >= self.PRIORITY_CRITICAL,
                        APV.status.in_(["triaged", "dispatched", "in_remediation"]),
                        APV.created_at >= cutoff_date,
                    )
                )
                .order_by(desc(APV.priority), APV.created_at)
            )

            if project:
                query = query.filter(APV.project == project)

            return query.all()

    def get_stale_apvs(self, days: int = 30) -> List[APV]:
        """
        Get APVs that have been pending for too long.

        Args:
            days: Consider APVs older than N days

        Returns:
            List of stale APVs
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        with self.db_client.get_session() as session:
            apvs = (
                session.query(APV)
                .filter(
                    and_(
                        APV.status.in_(["pending_triage", "triaged", "dispatched"]),
                        APV.created_at < cutoff_date,
                    )
                )
                .order_by(desc(APV.priority), APV.created_at)
                .all()
            )

            return apvs

    def get_triage_metrics(self, project: Optional[str] = None) -> Dict[str, any]:
        """
        Get triage metrics and statistics.

        Args:
            project: Optional project filter

        Returns:
            Dictionary with metrics
        """
        with self.db_client.get_session() as session:
            query = session.query(APV)

            if project:
                query = query.filter(APV.project == project)

            all_apvs = query.all()

            # Count by status
            status_counts = {}
            for apv in all_apvs:
                status_counts[apv.status] = status_counts.get(apv.status, 0) + 1

            # Count by priority
            priority_counts = {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
            }

            for apv in all_apvs:
                if apv.priority >= self.PRIORITY_CRITICAL:
                    priority_counts["critical"] += 1
                elif apv.priority >= self.PRIORITY_HIGH:
                    priority_counts["high"] += 1
                elif apv.priority >= self.PRIORITY_MEDIUM:
                    priority_counts["medium"] += 1
                else:
                    priority_counts["low"] += 1

            # Calculate resolution metrics
            resolved_apvs = [apv for apv in all_apvs if apv.status == "resolved"]
            total_resolution_time = timedelta()
            count_with_times = 0

            for apv in resolved_apvs:
                if apv.created_at and apv.resolved_at:
                    total_resolution_time += apv.resolved_at - apv.created_at
                    count_with_times += 1

            avg_resolution_time = (
                total_resolution_time / count_with_times if count_with_times > 0 else None
            )

            return {
                "total_apvs": len(all_apvs),
                "status_counts": status_counts,
                "priority_counts": priority_counts,
                "resolved_count": len(resolved_apvs),
                "resolution_rate": (
                    len(resolved_apvs) / len(all_apvs) if all_apvs else 0.0
                ),
                "avg_resolution_time_days": (
                    avg_resolution_time.days if avg_resolution_time else None
                ),
            }

    def _recalculate_priority(self, apv: APV) -> int:
        """
        Recalculate APV priority based on current data.

        Args:
            apv: APV instance

        Returns:
            New priority score (1-10)
        """
        score = 0.0

        # Factor 1: CVSS score (40% weight)
        if apv.cvss_score:
            score += (apv.cvss_score / 10.0) * 4.0

        # Factor 2: Severity (30% weight)
        severity_weights = {
            "critical": 3.0,
            "high": 2.5,
            "medium": 1.5,
            "low": 0.5,
        }
        if apv.severity:
            score += severity_weights.get(apv.severity.lower(), 1.0)

        # Factor 3: Age (10% weight) - newer is more urgent
        if apv.created_at:
            days_old = (datetime.utcnow() - apv.created_at).days
            if days_old < 1:
                score += 1.0
            elif days_old < 7:
                score += 0.7
            elif days_old < 30:
                score += 0.4

        # Factor 4: Affected files count (10% weight)
        if apv.affected_files:
            file_count = len(apv.affected_files)
            if file_count > 10:
                score += 1.0
            elif file_count > 5:
                score += 0.7
            elif file_count > 0:
                score += 0.4

        # Factor 5: Has vulnerable code signature (10% weight)
        if apv.vulnerable_code_signature:
            score += 1.0

        # Normalize to 1-10 range
        priority = int(min(max(score, 1), 10))

        return priority

    def _is_valid_transition(self, current_status: str, new_status: str) -> bool:
        """
        Check if status transition is valid.

        Args:
            current_status: Current APV status
            new_status: Proposed new status

        Returns:
            True if transition is valid
        """
        if current_status not in self.VALID_TRANSITIONS:
            return False

        return new_status in self.VALID_TRANSITIONS[current_status]

    def mark_false_positive(
        self,
        apv_id: str,
        reason: str,
        marked_by: str,
    ) -> bool:
        """
        Mark APV as false positive.

        Args:
            apv_id: APV UUID
            reason: Reason for false positive
            marked_by: User identifier

        Returns:
            True if marked successfully
        """
        return self.update_apv_status(
            apv_id,
            "false_positive",
            reason=f"False positive: {reason}",
            updated_by=marked_by,
        )

    def suppress_apv(
        self,
        apv_id: str,
        reason: str,
        suppressed_by: str,
        expires_at: Optional[datetime] = None,
    ) -> bool:
        """
        Suppress APV (intentionally not fixing).

        Args:
            apv_id: APV UUID
            reason: Reason for suppression
            suppressed_by: User identifier
            expires_at: Optional expiration date

        Returns:
            True if suppressed successfully
        """
        with self.db_client.get_session() as session:
            apv = session.query(APV).filter(APV.id == apv_id).first()

            if not apv:
                raise ValueError(f"APV not found: {apv_id}")

            apv.status = "suppressed"

            if not apv.metadata:
                apv.metadata = {}

            apv.metadata["suppression"] = {
                "reason": reason,
                "suppressed_by": suppressed_by,
                "suppressed_at": datetime.utcnow().isoformat(),
                "expires_at": expires_at.isoformat() if expires_at else None,
            }

            session.commit()

            logger.info(f"APV suppressed: {apv.apv_code} - {reason}")

            return True
