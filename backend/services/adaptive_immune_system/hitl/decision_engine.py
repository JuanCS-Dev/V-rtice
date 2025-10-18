"""
Decision Engine - Processes human decisions and executes actions.

Responsibilities:
- Validate human decisions
- Execute actions (merge PR, close PR, request changes)
- Log decisions to database
- Update APV status
- Send notifications via RabbitMQ
- Collect metrics
"""

import logging
from datetime import datetime
from typing import Optional

import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    DecisionRequest,
    DecisionRecord,
    ReviewAction,
    ReviewContext,
)
from messaging.client import RabbitMQClient, get_rabbitmq_client
from messaging.publisher import HITLDecisionPublisher

logger = logging.getLogger(__name__)


class DecisionEngine:
    """
    Processes human decisions on APVs.

    Features:
    - Decision validation
    - GitHub PR actions (merge, close, request changes)
    - Database logging
    - Status updates via RabbitMQ
    - Metrics collection
    """

    def __init__(
        self,
        github_token: str,
        repository_owner: str,
        repository_name: str,
        rabbitmq_client: Optional[RabbitMQClient] = None,
    ):
        """
        Initialize decision engine.

        Args:
            github_token: GitHub Personal Access Token
            repository_owner: Repository owner
            repository_name: Repository name
            rabbitmq_client: RabbitMQ client (optional, will get global instance if not provided)
        """
        self.github_token = github_token
        self.repository_owner = repository_owner
        self.repository_name = repository_name
        self.base_url = "https://api.github.com"

        # Initialize HITL decision publisher
        try:
            if rabbitmq_client is None:
                rabbitmq_client = get_rabbitmq_client()
            self.decision_publisher = HITLDecisionPublisher(rabbitmq_client)
            logger.info("✅ HITL decision publisher initialized")
        except Exception as e:
            logger.warning(f"⚠️ HITL decision publisher initialization failed: {e}")
            logger.warning("Decisions will not be published to RabbitMQ")
            self.decision_publisher = None

        logger.info(f"DecisionEngine initialized: {repository_owner}/{repository_name}")

    async def process_decision(
        self,
        decision: DecisionRequest,
        context: ReviewContext,
        db_session: AsyncSession,
    ) -> DecisionRecord:
        """
        Process human decision on APV.

        Args:
            decision: DecisionRequest from reviewer
            context: ReviewContext with full APV details
            db_session: Database session for logging

        Returns:
            DecisionRecord with outcome

        Raises:
            ValueError: If decision is invalid
            RuntimeError: If action execution fails
        """
        logger.info(
            f"Processing decision for {context.apv_code}: {decision.decision} by {decision.reviewer_name}"
        )

        # Validate decision
        self._validate_decision(decision, context)

        # Determine action
        action = self._determine_action(decision, context)

        # Execute action
        action_result = await self._execute_action(action, context)

        # Create decision record
        record = DecisionRecord(
            decision_id=f"DEC-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{context.apv_id[:8]}",
            apv_id=context.apv_id,
            apv_code=context.apv_code,
            decision=decision.decision,
            justification=decision.justification,
            confidence=decision.confidence,
            modifications=decision.modifications,
            reviewer_name=decision.reviewer_name,
            reviewer_email=decision.reviewer_email,
            cve_id=context.cve_id,
            severity=context.severity,
            patch_strategy=context.patch_strategy,
            wargame_verdict=context.wargame_verdict,
            action_taken=action_result.get("action"),
            outcome_notes=action_result.get("notes"),
            decided_at=datetime.utcnow(),
            action_completed_at=datetime.utcnow() if action_result.get("success") else None,
        )

        # Log to database (would be implemented with SQLAlchemy)
        await self._log_decision(record, db_session)

        # Publish decision to RabbitMQ for system execution
        if self.decision_publisher:
            try:
                message_id = await self.decision_publisher.publish_decision(
                    apv_id=record.apv_id,
                    apv_code=record.apv_code,
                    decision=record.decision,
                    justification=record.justification,
                    confidence=record.confidence,
                    reviewer_name=record.reviewer_name,
                    reviewer_email=record.reviewer_email,
                    decision_id=record.decision_id,
                    cve_id=record.cve_id,
                    severity=record.severity,
                    patch_strategy=record.patch_strategy,
                    pr_number=context.pr_number,
                    pr_url=context.pr_url,
                    action_type=action.action_type,
                    action_target_pr=action.target_pr,
                    action_comment=action.comment,
                    action_assignees=action.assignees,
                    action_labels=action.labels,
                    modifications=decision.modifications,
                    requires_followup=(decision.decision == "escalate"),
                    followup_reason=(
                        "Escalated to lead - requires senior review"
                        if decision.decision == "escalate"
                        else None
                    ),
                )
                logger.info(f"✅ Decision published to RabbitMQ (msg_id={message_id})")
            except Exception as e:
                logger.error(f"❌ Failed to publish decision to RabbitMQ: {e}")
                # Don't fail the entire operation if publishing fails

        logger.info(
            f"Decision processed: {record.decision} → {record.action_taken}"
        )

        return record

    def _validate_decision(
        self, decision: DecisionRequest, context: ReviewContext
    ) -> None:
        """Validate decision is appropriate."""
        # Check APV ID matches
        if decision.apv_id != context.apv_id:
            raise ValueError(
                f"APV ID mismatch: decision={decision.apv_id}, context={context.apv_id}"
            )

        # Check decision type is valid
        valid_decisions = ["approve", "reject", "modify", "escalate"]
        if decision.decision not in valid_decisions:
            raise ValueError(
                f"Invalid decision: {decision.decision}. Must be one of {valid_decisions}"
            )

        # Check modifications present if decision is "modify"
        if decision.decision == "modify" and not decision.modifications:
            raise ValueError("Decision 'modify' requires modifications to be specified")

        # Check PR exists if approving/rejecting
        if decision.decision in ["approve", "reject"] and not context.pr_number:
            raise ValueError(
                f"Cannot {decision.decision} without PR. Context has no PR number."
            )

        logger.debug(f"Decision validation passed: {decision.decision}")

    def _determine_action(
        self, decision: DecisionRequest, context: ReviewContext
    ) -> ReviewAction:
        """Determine action to take based on decision."""
        if decision.decision == "approve":
            # Merge PR
            return ReviewAction(
                action_type="merge_pr",
                target_pr=context.pr_number,
                comment=f"✅ Approved by {decision.reviewer_name}\n\n{decision.justification}",
                labels=["hitl-approved"],
            )

        elif decision.decision == "reject":
            # Close PR
            return ReviewAction(
                action_type="close_pr",
                target_pr=context.pr_number,
                comment=f"❌ Rejected by {decision.reviewer_name}\n\n{decision.justification}",
                labels=["hitl-rejected"],
            )

        elif decision.decision == "modify":
            # Request changes
            modifications_summary = "\n".join(
                f"- {key}: {value}" for key, value in (decision.modifications or {}).items()
            )
            return ReviewAction(
                action_type="request_changes",
                target_pr=context.pr_number,
                comment=f"🔧 Modifications requested by {decision.reviewer_name}\n\n{decision.justification}\n\n**Changes:**\n{modifications_summary}",
                labels=["hitl-changes-requested"],
            )

        elif decision.decision == "escalate":
            # Escalate to lead
            return ReviewAction(
                action_type="escalate_to_lead",
                target_pr=context.pr_number,
                comment=f"⬆️ Escalated by {decision.reviewer_name}\n\n{decision.justification}",
                labels=["hitl-escalated", "needs-lead-review"],
                assignees=["security-lead"],  # Would be configurable
            )

        else:
            raise ValueError(f"Unknown decision: {decision.decision}")

    async def _execute_action(
        self, action: ReviewAction, context: ReviewContext
    ) -> dict:
        """Execute action on GitHub PR."""
        try:
            if action.action_type == "merge_pr":
                result = await self._merge_pr(
                    action.target_pr, action.comment, action.labels
                )
                return {"success": True, "action": "pr_merged", "notes": result}

            elif action.action_type == "close_pr":
                result = await self._close_pr(
                    action.target_pr, action.comment, action.labels
                )
                return {"success": True, "action": "pr_closed", "notes": result}

            elif action.action_type == "request_changes":
                result = await self._request_changes(
                    action.target_pr, action.comment, action.labels
                )
                return {"success": True, "action": "changes_requested", "notes": result}

            elif action.action_type == "escalate_to_lead":
                result = await self._escalate(
                    action.target_pr, action.comment, action.labels, action.assignees
                )
                return {"success": True, "action": "escalated", "notes": result}

            else:
                raise ValueError(f"Unknown action type: {action.action_type}")

        except Exception as e:
            logger.error(f"Failed to execute action: {e}", exc_info=True)
            return {
                "success": False,
                "action": f"{action.action_type}_failed",
                "notes": str(e),
            }

    async def _merge_pr(
        self, pr_number: int, comment: str, labels: Optional[list[str]]
    ) -> str:
        """Merge PR on GitHub."""
        logger.info(f"Merging PR #{pr_number}")

        # Add comment
        await self._add_pr_comment(pr_number, comment)

        # Add labels
        if labels:
            await self._add_pr_labels(pr_number, labels)

        # Merge PR
        url = (
            f"{self.base_url}/repos/{self.repository_owner}/{self.repository_name}"
            f"/pulls/{pr_number}/merge"
        )

        payload = {
            "commit_title": f"Merge security fix PR #{pr_number} (HITL approved)",
            "merge_method": "squash",  # Squash for cleaner history
        }

        async with aiohttp.ClientSession() as session:
            async with session.put(
                url,
                headers=self._get_headers(),
                json=payload,
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"PR #{pr_number} merged: {data.get('sha', '')[:8]}")
                    return f"Merged at {data.get('sha', '')[:8]}"
                else:
                    error = await response.text()
                    raise RuntimeError(f"Failed to merge PR: {error}")

    async def _close_pr(
        self, pr_number: int, comment: str, labels: Optional[list[str]]
    ) -> str:
        """Close PR on GitHub."""
        logger.info(f"Closing PR #{pr_number}")

        # Add comment
        await self._add_pr_comment(pr_number, comment)

        # Add labels
        if labels:
            await self._add_pr_labels(pr_number, labels)

        # Close PR
        url = (
            f"{self.base_url}/repos/{self.repository_owner}/{self.repository_name}"
            f"/pulls/{pr_number}"
        )

        payload = {"state": "closed"}

        async with aiohttp.ClientSession() as session:
            async with session.patch(
                url,
                headers=self._get_headers(),
                json=payload,
            ) as response:
                if response.status == 200:
                    logger.info(f"PR #{pr_number} closed")
                    return "PR closed"
                else:
                    error = await response.text()
                    raise RuntimeError(f"Failed to close PR: {error}")

    async def _request_changes(
        self, pr_number: int, comment: str, labels: Optional[list[str]]
    ) -> str:
        """Request changes on PR."""
        logger.info(f"Requesting changes on PR #{pr_number}")

        # Add comment
        await self._add_pr_comment(pr_number, comment)

        # Add labels
        if labels:
            await self._add_pr_labels(pr_number, labels)

        return "Changes requested"

    async def _escalate(
        self,
        pr_number: int,
        comment: str,
        labels: Optional[list[str]],
        assignees: Optional[list[str]],
    ) -> str:
        """Escalate PR to lead reviewer."""
        logger.info(f"Escalating PR #{pr_number}")

        # Add comment
        await self._add_pr_comment(pr_number, comment)

        # Add labels
        if labels:
            await self._add_pr_labels(pr_number, labels)

        # Add assignees
        if assignees:
            await self._add_pr_assignees(pr_number, assignees)

        return "Escalated to lead"

    async def _add_pr_comment(self, pr_number: int, comment: str) -> None:
        """Add comment to PR."""
        url = (
            f"{self.base_url}/repos/{self.repository_owner}/{self.repository_name}"
            f"/issues/{pr_number}/comments"
        )

        payload = {"body": comment}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=self._get_headers(),
                json=payload,
            ) as response:
                if response.status != 201:
                    error = await response.text()
                    logger.warning(f"Failed to add comment: {error}")

    async def _add_pr_labels(self, pr_number: int, labels: list[str]) -> None:
        """Add labels to PR."""
        url = (
            f"{self.base_url}/repos/{self.repository_owner}/{self.repository_name}"
            f"/issues/{pr_number}/labels"
        )

        payload = {"labels": labels}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=self._get_headers(),
                json=payload,
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    logger.warning(f"Failed to add labels: {error}")

    async def _add_pr_assignees(self, pr_number: int, assignees: list[str]) -> None:
        """Add assignees to PR."""
        url = (
            f"{self.base_url}/repos/{self.repository_owner}/{self.repository_name}"
            f"/issues/{pr_number}/assignees"
        )

        payload = {"assignees": assignees}

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=self._get_headers(),
                json=payload,
            ) as response:
                if response.status != 201:
                    error = await response.text()
                    logger.warning(f"Failed to add assignees: {error}")

    async def _log_decision(
        self, record: DecisionRecord, db_session: AsyncSession
    ) -> None:
        """Log decision to database."""
        # Save to database using file-based storage for now
        try:
            decision_log = Path("/var/log/vertice/hitl_decisions.jsonl")
            decision_log.parent.mkdir(parents=True, exist_ok=True)
            
            with open(decision_log, "a") as f:
                import json
                f.write(json.dumps({
                    "decision_id": record.decision_id,
                    "decision": record.decision,
                    "reviewer_name": record.reviewer_name,
                    "timestamp": record.timestamp.isoformat(),
                    "action_taken": record.action_taken,
                    "patch_id": record.patch_id,
                }) + "\n")
            
            logger.info(f"Decision logged: {record.decision_id} - {record.decision} by {record.reviewer_name}")
        except Exception as e:
            logger.error(f"Failed to log decision: {e}")

    def _get_headers(self) -> dict:
        """Get HTTP headers for GitHub API."""
        return {
            "Authorization": f"Bearer {self.github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
