"""
HITL Decision Framework

Core framework for human-in-the-loop security decisions. Orchestrates risk
assessment, automation level determination, decision queueing, and execution.

Workflow:
    1. AI proposes action → evaluate_action()
    2. Assess risk → RiskAssessor
    3. Determine automation level based on confidence + risk
    4. FULL automation? → Execute immediately + audit
    5. Requires review? → Queue for operator
    6. Operator reviews → approve/reject/escalate
    7. Execute approved actions → audit trail

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .base import (
    ActionType,
    AutomationLevel,
    DecisionContext,
    DecisionStatus,
    HITLConfig,
    HITLDecision,
    OperatorAction,
)
from .risk_assessor import RiskAssessor

logger = logging.getLogger(__name__)


# ============================================================================
# Decision Result
# ============================================================================


@dataclass
class DecisionResult:
    """
    Result of decision processing.

    Indicates whether decision was executed immediately, queued for review,
    or rejected.
    """

    # Decision reference
    decision: HITLDecision

    # Result status
    executed: bool = False
    queued: bool = False
    rejected: bool = False

    # Execution details
    execution_output: dict[str, Any] = field(default_factory=dict)
    execution_error: str | None = None

    # Audit trail entry
    audit_entry_id: str | None = None

    # Timing
    processing_time: float = 0.0  # seconds

    def get_summary(self) -> str:
        """Get human-readable summary."""
        if self.executed:
            return f"Executed: {self.decision.context.action_type.value} (ID: {self.decision.decision_id})"
        if self.queued:
            return f"Queued for review: {self.decision.context.action_type.value} (ID: {self.decision.decision_id})"
        if self.rejected:
            return f"Rejected: {self.decision.context.action_type.value} (ID: {self.decision.decision_id})"
        return f"Pending: {self.decision.decision_id}"


# ============================================================================
# HITL Decision Framework
# ============================================================================


class HITLDecisionFramework:
    """
    Main HITL decision framework.

    Coordinates risk assessment, automation level determination, decision
    queueing, and execution for AI-proposed security actions.
    """

    def __init__(
        self,
        config: HITLConfig | None = None,
        risk_assessor: RiskAssessor | None = None,
    ):
        """
        Initialize HITL framework.

        Args:
            config: HITL configuration
            risk_assessor: Risk assessment engine (created if not provided)
        """
        self.config = config or HITLConfig()
        self.risk_assessor = risk_assessor or RiskAssessor()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Action executors (registered by action type)
        self._executors: dict[ActionType, Callable] = {}

        # Decision queue (will be set by DecisionQueue)
        self._decision_queue: Any | None = None

        # Audit trail (will be set by AuditTrail)
        self._audit_trail: Any | None = None

        # Metrics
        self.metrics = {
            "total_decisions": 0,
            "auto_executed": 0,
            "queued_for_review": 0,
            "rejected": 0,
            "escalated": 0,
        }

        self.logger.info("HITL Decision Framework initialized")

    def set_decision_queue(self, queue):
        """Set decision queue instance."""
        self._decision_queue = queue
        self.logger.info("Decision queue connected")

    def set_audit_trail(self, audit_trail):
        """Set audit trail instance."""
        self._audit_trail = audit_trail
        self.logger.info("Audit trail connected")

    def register_executor(self, action_type: ActionType, executor: Callable):
        """
        Register action executor function.

        Args:
            action_type: Type of action
            executor: Callable that executes the action
                     Signature: executor(context: DecisionContext) -> Dict[str, Any]
        """
        self._executors[action_type] = executor
        self.logger.info(f"Registered executor for {action_type.value}")

    def evaluate_action(
        self,
        action_type: ActionType,
        action_params: dict[str, Any],
        ai_reasoning: str,
        confidence: float,
        threat_score: float = 0.0,
        affected_assets: list[str] | None = None,
        **context_kwargs,
    ) -> DecisionResult:
        """
        Evaluate AI-proposed action and determine automation level.

        This is the main entry point for MAXIMUS AI to submit decisions.

        Args:
            action_type: Type of security action
            action_params: Parameters for the action
            ai_reasoning: AI's reasoning for the action
            confidence: AI's confidence score (0.0 to 1.0)
            threat_score: Threat severity score (0.0 to 1.0)
            affected_assets: List of affected asset IDs
            **context_kwargs: Additional context parameters

        Returns:
            DecisionResult indicating execution status
        """
        start_time = datetime.utcnow()
        self.metrics["total_decisions"] += 1

        # Build decision context
        context = DecisionContext(
            action_type=action_type,
            action_params=action_params,
            ai_reasoning=ai_reasoning,
            confidence=confidence,
            threat_score=threat_score,
            affected_assets=affected_assets or [],
            **context_kwargs,
        )

        # Assess risk
        risk_score = self.risk_assessor.assess_risk(context)

        self.logger.info(
            f"Risk assessment: {risk_score.risk_level.value} "
            f"(score={risk_score.overall_score:.2f}, "
            f"confidence={confidence:.2f}, action={action_type.value})"
        )

        # Determine automation level
        automation_level = self.config.get_automation_level(confidence, risk_score.risk_level)

        # Create HITL decision
        decision = HITLDecision(
            context=context,
            risk_level=risk_score.risk_level,
            automation_level=automation_level,
            status=DecisionStatus.PENDING,
        )

        # Set SLA deadline if requires review
        if decision.requires_human_review():
            sla_timeout = self.config.sla_config.get_timeout_delta(risk_score.risk_level)
            decision.sla_deadline = datetime.utcnow() + sla_timeout

        # Log decision creation to audit trail
        if self._audit_trail:
            audit_entry = self._audit_trail.log_decision_created(decision, risk_score)
            decision.metadata["audit_entry_id"] = audit_entry.entry_id

        # Process based on automation level
        result: DecisionResult

        if automation_level == AutomationLevel.FULL:
            # Execute immediately
            self.logger.info(f"FULL automation: executing {action_type.value} (decision={decision.decision_id})")
            result = self._execute_immediately(decision)
            self.metrics["auto_executed"] += 1

        elif automation_level in [AutomationLevel.SUPERVISED, AutomationLevel.ADVISORY]:
            # Queue for human review
            self.logger.info(
                f"{automation_level.value.upper()} automation: queueing {action_type.value} "
                f"for review (decision={decision.decision_id})"
            )
            result = self._queue_for_review(decision)
            self.metrics["queued_for_review"] += 1

        elif automation_level == AutomationLevel.MANUAL:
            # Manual only - no AI suggestion
            self.logger.info(
                f"MANUAL automation: no AI execution for {action_type.value} "
                f"(decision={decision.decision_id}, confidence too low)"
            )
            decision.status = DecisionStatus.PENDING
            result = self._queue_for_review(decision)
            self.metrics["queued_for_review"] += 1

        else:
            raise ValueError(f"Unknown automation level: {automation_level}")

        # Record processing time
        end_time = datetime.utcnow()
        result.processing_time = (end_time - start_time).total_seconds()

        self.logger.info(
            f"Decision evaluated: {decision.decision_id} → {automation_level.value} "
            f"(processing_time={result.processing_time:.3f}s)"
        )

        return result

    def _execute_immediately(self, decision: HITLDecision) -> DecisionResult:
        """Execute decision immediately (FULL automation)."""
        try:
            # Execute action
            execution_output = self._execute_action(decision.context)

            # Update decision status
            decision.status = DecisionStatus.EXECUTED
            decision.executed_at = datetime.utcnow()
            decision.execution_result = execution_output

            # Log to audit trail
            if self._audit_trail:
                audit_entry = self._audit_trail.log_decision_executed(decision, execution_output)
                audit_entry_id = audit_entry.entry_id
            else:
                audit_entry_id = None

            result = DecisionResult(
                decision=decision,
                executed=True,
                execution_output=execution_output,
                audit_entry_id=audit_entry_id,
            )

            self.logger.info(f"Decision executed: {decision.decision_id} (action={decision.context.action_type.value})")

            return result

        except Exception as e:
            # Execution failed
            self.logger.error(
                f"Execution failed for {decision.decision_id}: {e}",
                exc_info=True,
            )

            decision.status = DecisionStatus.FAILED
            decision.execution_error = str(e)

            # Log failure to audit trail
            if self._audit_trail:
                self._audit_trail.log_decision_failed(decision, str(e))

            return DecisionResult(
                decision=decision,
                executed=False,
                execution_error=str(e),
            )

    def _queue_for_review(self, decision: HITLDecision) -> DecisionResult:
        """Queue decision for human review."""
        if self._decision_queue is None:
            self.logger.warning("Decision queue not set - decision will not be queued")
            return DecisionResult(decision=decision, queued=False)

        # Add to queue
        queued_decision = self._decision_queue.enqueue(decision)

        # Log to audit trail
        if self._audit_trail:
            audit_entry = self._audit_trail.log_decision_queued(decision)
            audit_entry_id = audit_entry.entry_id
        else:
            audit_entry_id = None

        result = DecisionResult(
            decision=decision,
            queued=True,
            audit_entry_id=audit_entry_id,
        )

        self.logger.info(
            f"Decision queued: {decision.decision_id} "
            f"(automation_level={decision.automation_level.value}, "
            f"sla_deadline={decision.sla_deadline})"
        )

        return result

    def execute_decision(self, decision: HITLDecision, operator_action: OperatorAction | None = None) -> DecisionResult:
        """
        Execute a decision (after human approval).

        Args:
            decision: Decision to execute
            operator_action: Operator action (approval/modification)

        Returns:
            DecisionResult
        """
        self.logger.info(f"Executing decision {decision.decision_id} (action={decision.context.action_type.value})")

        # Apply operator modifications if any
        if operator_action and operator_action.modifications:
            self.logger.info(
                f"Applying operator modifications to {decision.decision_id}: {operator_action.modifications}"
            )
            decision.context.action_params.update(operator_action.modifications)

        # Log decision approval to audit trail
        if self._audit_trail and operator_action:
            self._audit_trail.log_decision_approved(decision, operator_action)

        # Execute
        try:
            execution_output = self._execute_action(decision.context)

            # Update decision
            decision.status = DecisionStatus.EXECUTED
            decision.executed_at = datetime.utcnow()
            decision.execution_result = execution_output

            # Log to audit trail
            if self._audit_trail:
                audit_entry = self._audit_trail.log_decision_executed(decision, execution_output, operator_action)
                audit_entry_id = audit_entry.entry_id
            else:
                audit_entry_id = None

            result = DecisionResult(
                decision=decision,
                executed=True,
                execution_output=execution_output,
                audit_entry_id=audit_entry_id,
            )

            self.logger.info(f"Decision executed successfully: {decision.decision_id}")
            return result

        except Exception as e:
            self.logger.error(
                f"Execution failed for {decision.decision_id}: {e}",
                exc_info=True,
            )

            decision.status = DecisionStatus.FAILED
            decision.execution_error = str(e)

            # Log failure
            if self._audit_trail:
                self._audit_trail.log_decision_failed(decision, str(e))

            return DecisionResult(
                decision=decision,
                executed=False,
                execution_error=str(e),
            )

    def _execute_action(self, context: DecisionContext) -> dict[str, Any]:
        """
        Execute security action.

        Args:
            context: Decision context with action details

        Returns:
            Execution result

        Raises:
            ValueError: If no executor registered for action type
            Exception: If execution fails
        """
        action_type = context.action_type

        # Get executor
        executor = self._executors.get(action_type)
        if executor is None:
            raise ValueError(f"No executor registered for action type: {action_type.value}")

        # Execute
        self.logger.debug(f"Executing {action_type.value} with params: {context.action_params}")

        result = executor(context)

        self.logger.debug(f"Execution complete: {action_type.value} → {result}")

        return result

    def reject_decision(self, decision: HITLDecision, operator_action: OperatorAction) -> None:
        """
        Reject a decision (operator veto).

        Args:
            decision: Decision to reject
            operator_action: Operator action with rejection reasoning
        """
        self.logger.info(f"Decision rejected: {decision.decision_id} by {operator_action.operator_id}")

        decision.status = DecisionStatus.REJECTED
        decision.reviewed_by = operator_action.operator_id
        decision.reviewed_at = datetime.utcnow()
        decision.operator_comment = operator_action.comment

        self.metrics["rejected"] += 1

        # Log to audit trail
        if self._audit_trail:
            self._audit_trail.log_decision_rejected(decision, operator_action)

    def escalate_decision(self, decision: HITLDecision, escalation_reason: str, escalated_to: str) -> None:
        """
        Escalate decision to higher authority.

        Args:
            decision: Decision to escalate
            escalation_reason: Reason for escalation
            escalated_to: Target role/person
        """
        self.logger.info(f"Decision escalated: {decision.decision_id} → {escalated_to} (reason: {escalation_reason})")

        decision.status = DecisionStatus.ESCALATED
        decision.escalated = True
        decision.escalated_to = escalated_to
        decision.escalated_at = datetime.utcnow()
        decision.escalation_reason = escalation_reason

        self.metrics["escalated"] += 1

        # Log to audit trail
        if self._audit_trail:
            self._audit_trail.log_decision_escalated(decision, escalation_reason, escalated_to)

    def get_metrics(self) -> dict[str, Any]:
        """Get framework metrics."""
        return {
            **self.metrics,
            "automation_rate": (
                self.metrics["auto_executed"] / self.metrics["total_decisions"]
                if self.metrics["total_decisions"] > 0
                else 0.0
            ),
            "human_review_rate": (
                self.metrics["queued_for_review"] / self.metrics["total_decisions"]
                if self.metrics["total_decisions"] > 0
                else 0.0
            ),
            "rejection_rate": (
                self.metrics["rejected"] / self.metrics["total_decisions"]
                if self.metrics["total_decisions"] > 0
                else 0.0
            ),
        }

    # Convenience methods for common actions

    def block_ip(self, ip_address: str, confidence: float, threat_score: float, reason: str) -> DecisionResult:
        """Convenience method to block IP address."""
        return self.evaluate_action(
            action_type=ActionType.BLOCK_IP,
            action_params={"ip_address": ip_address},
            ai_reasoning=reason,
            confidence=confidence,
            threat_score=threat_score,
        )

    def isolate_host(self, host_id: str, confidence: float, threat_score: float, reason: str) -> DecisionResult:
        """Convenience method to isolate host."""
        return self.evaluate_action(
            action_type=ActionType.ISOLATE_HOST,
            action_params={"host_id": host_id},
            ai_reasoning=reason,
            confidence=confidence,
            threat_score=threat_score,
            affected_assets=[host_id],
        )

    def quarantine_file(
        self,
        file_path: str,
        host_id: str,
        confidence: float,
        threat_score: float,
        reason: str,
    ) -> DecisionResult:
        """Convenience method to quarantine file."""
        return self.evaluate_action(
            action_type=ActionType.QUARANTINE_FILE,
            action_params={"file_path": file_path, "host_id": host_id},
            ai_reasoning=reason,
            confidence=confidence,
            threat_score=threat_score,
            affected_assets=[host_id],
        )

    def kill_process(
        self, process_id: int, host_id: str, confidence: float, threat_score: float, reason: str
    ) -> DecisionResult:
        """Convenience method to kill process."""
        return self.evaluate_action(
            action_type=ActionType.KILL_PROCESS,
            action_params={"process_id": process_id, "host_id": host_id},
            ai_reasoning=reason,
            confidence=confidence,
            threat_score=threat_score,
            affected_assets=[host_id],
        )
