"""
Decision Executor - Executes HITL decisions system-wide.

Consumes HITL decision messages from RabbitMQ and executes them:
- Update Oráculo APV state
- Trigger follow-up actions
- Send status callbacks
- Log execution results

Provides centralized decision execution separate from HITL console,
enabling distributed processing and horizontal scaling.
"""

import logging
from typing import Optional

from ..messaging.client import RabbitMQClient, get_rabbitmq_client
from ..messaging.consumer import HITLDecisionConsumer
from ..models.hitl import HITLDecisionMessage
from ..oraculo.triage_engine import TriageEngine
from ..database import DatabaseClient

logger = logging.getLogger(__name__)


class DecisionExecutor:
    """
    Executes HITL decisions and updates system state.

    Features:
    - Consumes decisions from RabbitMQ
    - Updates Oráculo APV state
    - Triggers follow-up actions
    - Logs execution results
    - Distributed execution support
    """

    def __init__(
        self,
        db_client: DatabaseClient,
        rabbitmq_client: Optional[RabbitMQClient] = None,
    ):
        """
        Initialize decision executor.

        Args:
            db_client: Database client instance
            rabbitmq_client: RabbitMQ client (optional, will get global instance if not provided)
        """
        self.db_client = db_client
        self.triage_engine = TriageEngine(db_client)

        # Initialize RabbitMQ consumer
        if rabbitmq_client is None:
            rabbitmq_client = get_rabbitmq_client()

        self.consumer = HITLDecisionConsumer(
            client=rabbitmq_client,
            callback=self.handle_decision,
        )

        logger.info("DecisionExecutor initialized")

    async def start(self) -> None:
        """
        Start consuming HITL decisions.

        Runs indefinitely until stopped.
        """
        logger.info("🚀 Starting DecisionExecutor...")

        try:
            await self.consumer.start()
            logger.info("✅ DecisionExecutor started and consuming messages")

        except Exception as e:
            logger.error(f"❌ Failed to start DecisionExecutor: {e}", exc_info=True)
            raise

    async def handle_decision(self, decision: HITLDecisionMessage) -> None:
        """
        Handle incoming HITL decision.

        Args:
            decision: HITLDecisionMessage from RabbitMQ

        Raises:
            Exception: If decision handling fails (will be sent to DLQ)
        """
        logger.info(
            f"📨 Handling decision: {decision.apv_code} → {decision.decision} "
            f"(reviewer={decision.reviewer_name})"
        )

        try:
            # Execute decision based on type
            if decision.decision == "approve":
                await self._handle_approve(decision)

            elif decision.decision == "reject":
                await self._handle_reject(decision)

            elif decision.decision == "modify":
                await self._handle_modify(decision)

            elif decision.decision == "escalate":
                await self._handle_escalate(decision)

            else:
                logger.warning(f"⚠️ Unknown decision type: {decision.decision}")
                return

            logger.info(
                f"✅ Decision executed: {decision.apv_code} → {decision.decision}"
            )

        except Exception as e:
            logger.error(
                f"❌ Failed to handle decision {decision.apv_code}: {e}",
                exc_info=True,
            )
            raise  # Re-raise to send to DLQ

    async def _handle_approve(self, decision: HITLDecisionMessage) -> None:
        """
        Handle approve decision.

        Updates APV state to "hitl_approved" → "resolved"

        Args:
            decision: HITLDecisionMessage
        """
        logger.info(f"✅ Approving APV: {decision.apv_code}")

        # Update APV state to approved
        self.triage_engine.update_apv_status(
            apv_id=decision.apv_id,
            new_status="hitl_approved",
            reason=f"Approved by {decision.reviewer_name}: {decision.justification}",
            updated_by=decision.reviewer_email,
        )

        # If PR was merged in DecisionEngine, mark as resolved
        if decision.action_type == "merge_pr":
            self.triage_engine.update_apv_status(
                apv_id=decision.apv_id,
                new_status="resolved",
                reason=f"PR merged (decision_id={decision.decision_id})",
                updated_by="system",
            )

        logger.info(f"✅ APV approved and marked resolved: {decision.apv_code}")

    async def _handle_reject(self, decision: HITLDecisionMessage) -> None:
        """
        Handle reject decision.

        Updates APV state to "hitl_rejected" → "suppressed"

        Args:
            decision: HITLDecisionMessage
        """
        logger.info(f"❌ Rejecting APV: {decision.apv_code}")

        # Update APV state to rejected
        self.triage_engine.update_apv_status(
            apv_id=decision.apv_id,
            new_status="hitl_rejected",
            reason=f"Rejected by {decision.reviewer_name}: {decision.justification}",
            updated_by=decision.reviewer_email,
        )

        # Suppress APV (intentionally not fixing)
        self.triage_engine.suppress_apv(
            apv_id=decision.apv_id,
            reason=f"HITL rejection: {decision.justification}",
            suppressed_by=decision.reviewer_email,
            expires_at=None,  # Permanent suppression
        )

        logger.info(f"✅ APV rejected and suppressed: {decision.apv_code}")

    async def _handle_modify(self, decision: HITLDecisionMessage) -> None:
        """
        Handle modify decision.

        Updates APV with requested modifications and transitions back to remediation.

        Args:
            decision: HITLDecisionMessage
        """
        logger.info(f"🔧 Modifying APV: {decision.apv_code}")

        # Update APV status
        self.triage_engine.update_apv_status(
            apv_id=decision.apv_id,
            new_status="in_remediation",
            reason=f"Modifications requested by {decision.reviewer_name}: {decision.justification}",
            updated_by=decision.reviewer_email,
        )

        # Store modifications in APV metadata
        with self.db_client.get_session() as session:
            from ..database.models import APV

            apv = session.query(APV).filter(APV.id == decision.apv_id).first()
            if apv:
                if not apv.metadata:
                    apv.metadata = {}

                apv.metadata["hitl_modifications"] = {
                    "requested_by": decision.reviewer_name,
                    "requested_at": decision.timestamp.isoformat(),
                    "justification": decision.justification,
                    "modifications": decision.modifications or {},
                    "decision_id": decision.decision_id,
                }

                session.commit()

        logger.info(f"✅ APV modifications recorded: {decision.apv_code}")

    async def _handle_escalate(self, decision: HITLDecisionMessage) -> None:
        """
        Handle escalate decision.

        Escalates APV to higher authority for review.

        Args:
            decision: HITLDecisionMessage
        """
        logger.info(f"⬆️ Escalating APV: {decision.apv_code}")

        # Use triage_engine's escalate_to_hitl (even though already in HITL)
        # This will create a new HITL decision record with higher urgency
        self.triage_engine.escalate_to_hitl(
            apv_id=decision.apv_id,
            reason=f"Escalated by {decision.reviewer_name}: {decision.justification}",
            urgency="critical",  # Escalations are always critical
        )

        # Store escalation in metadata
        with self.db_client.get_session() as session:
            from ..database.models import APV

            apv = session.query(APV).filter(APV.id == decision.apv_id).first()
            if apv:
                if not apv.metadata:
                    apv.metadata = {}

                escalations = apv.metadata.get("escalations", [])
                escalations.append({
                    "escalated_by": decision.reviewer_name,
                    "escalated_at": decision.timestamp.isoformat(),
                    "reason": decision.justification,
                    "followup_reason": decision.followup_reason,
                    "decision_id": decision.decision_id,
                })

                apv.metadata["escalations"] = escalations
                session.commit()

        logger.info(f"✅ APV escalated: {decision.apv_code}")

    async def stop(self) -> None:
        """Stop decision executor."""
        logger.info("⏹️ Stopping DecisionExecutor...")
        # Consumer cleanup would go here if needed
        logger.info("✅ DecisionExecutor stopped")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()
