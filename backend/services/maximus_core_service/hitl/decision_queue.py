"""
HITL Decision Queue

Priority queue for decisions awaiting human review. Manages:
- Priority-based queueing (CRITICAL > HIGH > MEDIUM > LOW)
- SLA monitoring and timeout detection
- Operator assignment (round-robin or manual)
- Queue metrics and statistics

Queue Structure:
    CRITICAL queue (SLA: 5min)
    HIGH queue (SLA: 10min)
    MEDIUM queue (SLA: 15min)
    LOW queue (SLA: 30min)

Author: Claude Code + JuanCS-Dev
Date: 2025-10-06
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from collections import deque
import logging
import threading

from .base import (
    HITLDecision,
    DecisionStatus,
    RiskLevel,
    SLAConfig,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Queued Decision
# ============================================================================

@dataclass
class QueuedDecision:
    """
    Wrapper for decision in queue with queueing metadata.
    """
    # Decision reference
    decision: HITLDecision

    # Queue metadata
    queued_at: datetime = field(default_factory=datetime.utcnow)
    queue_position: int = 0
    priority_score: float = 0.0  # Higher = more urgent

    # Assignment tracking
    assigned: bool = False
    assignment_attempts: int = 0

    # SLA tracking
    sla_warning_sent: bool = False
    sla_violated: bool = False

    def get_time_in_queue(self) -> timedelta:
        """Get time decision has been in queue."""
        return datetime.utcnow() - self.queued_at

    def get_time_until_sla(self) -> Optional[timedelta]:
        """Get time remaining until SLA deadline."""
        if self.decision.sla_deadline is None:
            return None
        remaining = self.decision.sla_deadline - datetime.utcnow()
        return remaining if remaining.total_seconds() > 0 else timedelta(0)

    def is_sla_violated(self) -> bool:
        """Check if SLA has been violated."""
        if self.decision.sla_deadline is None:
            return False
        return datetime.utcnow() > self.decision.sla_deadline

    def should_send_sla_warning(self, warning_threshold: float = 0.75) -> bool:
        """Check if SLA warning should be sent."""
        if self.sla_warning_sent or self.decision.sla_deadline is None:
            return False

        time_in_queue = self.get_time_in_queue()
        total_sla = self.decision.sla_deadline - self.decision.created_at

        if total_sla.total_seconds() <= 0:
            return False

        fraction_elapsed = time_in_queue.total_seconds() / total_sla.total_seconds()
        return fraction_elapsed >= warning_threshold


# ============================================================================
# SLA Monitor
# ============================================================================

class SLAMonitor:
    """
    Monitors decisions for SLA violations and warnings.

    Runs periodic checks and triggers callbacks for:
    - SLA warnings (75% of time elapsed)
    - SLA violations (deadline exceeded)
    """

    def __init__(self, sla_config: SLAConfig, check_interval: int = 30):
        """
        Initialize SLA monitor.

        Args:
            sla_config: SLA configuration
            check_interval: Check interval in seconds
        """
        self.sla_config = sla_config
        self.check_interval = check_interval
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Callbacks
        self._warning_callbacks: List[callable] = []
        self._violation_callbacks: List[callable] = []

        # Monitoring state
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None

        # Metrics
        self.metrics = {
            "warnings_sent": 0,
            "violations_detected": 0,
        }

    def register_warning_callback(self, callback: callable):
        """Register callback for SLA warnings. Signature: callback(decision)"""
        self._warning_callbacks.append(callback)

    def register_violation_callback(self, callback: callable):
        """Register callback for SLA violations. Signature: callback(decision)"""
        self._violation_callbacks.append(callback)

    def start(self):
        """Start SLA monitoring (in background thread)."""
        if self._running:
            self.logger.warning("SLA monitor already running")
            return

        self._running = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop, daemon=True
        )
        self._monitor_thread.start()
        self.logger.info(f"SLA monitor started (check_interval={self.check_interval}s)")

    def stop(self):
        """Stop SLA monitoring."""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        self.logger.info("SLA monitor stopped")

    def _monitor_loop(self):
        """Background monitoring loop."""
        import time

        while self._running:
            time.sleep(self.check_interval)
            # Monitoring happens via check_decision() calls from queue

    def check_decision(self, queued_decision: QueuedDecision):
        """
        Check decision for SLA warning/violation.

        Args:
            queued_decision: Queued decision to check
        """
        # Check for warning
        if queued_decision.should_send_sla_warning(
            self.sla_config.warning_threshold
        ):
            self._trigger_warning(queued_decision)

        # Check for violation
        if queued_decision.is_sla_violated():
            self._trigger_violation(queued_decision)

    def _trigger_warning(self, queued_decision: QueuedDecision):
        """Trigger SLA warning callbacks."""
        queued_decision.sla_warning_sent = True
        queued_decision.decision.sla_warning_sent = True
        self.metrics["warnings_sent"] += 1

        self.logger.warning(
            f"SLA warning: {queued_decision.decision.decision_id} "
            f"(risk={queued_decision.decision.risk_level.value}, "
            f"time_remaining={queued_decision.get_time_until_sla()})"
        )

        for callback in self._warning_callbacks:
            try:
                callback(queued_decision.decision)
            except Exception as e:
                self.logger.error(f"SLA warning callback failed: {e}", exc_info=True)

    def _trigger_violation(self, queued_decision: QueuedDecision):
        """Trigger SLA violation callbacks."""
        if queued_decision.sla_violated:
            return  # Already handled

        queued_decision.sla_violated = True
        queued_decision.decision.status = DecisionStatus.TIMEOUT
        self.metrics["violations_detected"] += 1

        self.logger.error(
            f"SLA VIOLATION: {queued_decision.decision.decision_id} "
            f"(risk={queued_decision.decision.risk_level.value}, "
            f"overdue_by={abs(queued_decision.get_time_until_sla())})"
        )

        for callback in self._violation_callbacks:
            try:
                callback(queued_decision.decision)
            except Exception as e:
                self.logger.error(f"SLA violation callback failed: {e}", exc_info=True)


# ============================================================================
# Decision Queue
# ============================================================================

class DecisionQueue:
    """
    Priority queue for decisions awaiting human review.

    Implements multi-level priority queue with SLA monitoring.
    """

    def __init__(self, sla_config: Optional[SLAConfig] = None, max_size: int = 1000):
        """
        Initialize decision queue.

        Args:
            sla_config: SLA configuration
            max_size: Maximum queue size (0 = unlimited)
        """
        self.sla_config = sla_config or SLAConfig()
        self.max_size = max_size
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Priority queues (one per risk level)
        self._queues: Dict[RiskLevel, deque] = {
            RiskLevel.CRITICAL: deque(),
            RiskLevel.HIGH: deque(),
            RiskLevel.MEDIUM: deque(),
            RiskLevel.LOW: deque(),
        }

        # Decision lookup (by decision_id)
        self._decisions: Dict[str, QueuedDecision] = {}

        # Operator assignment tracking
        self._operators: Set[str] = set()
        self._operator_assignments: Dict[str, List[str]] = {}  # operator_id -> [decision_ids]
        self._current_operator_index: int = 0  # For round-robin

        # SLA monitor
        self.sla_monitor = SLAMonitor(self.sla_config)
        self.sla_monitor.register_warning_callback(self._handle_sla_warning)
        self.sla_monitor.register_violation_callback(self._handle_sla_violation)
        self.sla_monitor.start()

        # Metrics
        self.metrics = {
            "total_enqueued": 0,
            "total_dequeued": 0,
            "total_assigned": 0,
            "sla_warnings": 0,
            "sla_violations": 0,
        }

        self.logger.info("Decision Queue initialized")

    def enqueue(self, decision: HITLDecision) -> QueuedDecision:
        """
        Add decision to queue.

        Args:
            decision: Decision to enqueue

        Returns:
            QueuedDecision wrapper

        Raises:
            ValueError: If queue is full
        """
        # Check queue size
        if self.max_size > 0 and self.get_total_size() >= self.max_size:
            raise ValueError(f"Queue is full (max_size={self.max_size})")

        # Create queued decision
        queued = QueuedDecision(
            decision=decision,
            priority_score=self._calculate_priority(decision),
        )

        # Add to appropriate queue
        risk_queue = self._queues[decision.risk_level]
        risk_queue.append(queued)

        # Add to lookup
        self._decisions[decision.decision_id] = queued

        # Update metrics
        self.metrics["total_enqueued"] += 1

        self.logger.info(
            f"Decision enqueued: {decision.decision_id} "
            f"(risk={decision.risk_level.value}, queue_size={len(risk_queue)})"
        )

        return queued

    def dequeue(
        self, risk_level: Optional[RiskLevel] = None, operator_id: Optional[str] = None
    ) -> Optional[HITLDecision]:
        """
        Remove and return highest priority decision from queue.

        Args:
            risk_level: Specific risk level to dequeue from (None = highest priority)
            operator_id: Operator ID (for assignment tracking)

        Returns:
            HITLDecision, or None if queue is empty
        """
        # Determine which queue to dequeue from
        if risk_level:
            queues_to_check = [risk_level]
        else:
            # Check in priority order: CRITICAL > HIGH > MEDIUM > LOW
            queues_to_check = [
                RiskLevel.CRITICAL,
                RiskLevel.HIGH,
                RiskLevel.MEDIUM,
                RiskLevel.LOW,
            ]

        # Find first non-empty queue
        for level in queues_to_check:
            queue = self._queues[level]
            if queue:
                queued = queue.popleft()
                decision = queued.decision

                # Remove from lookup
                del self._decisions[decision.decision_id]

                # Assign to operator if provided
                if operator_id:
                    self._assign_to_operator(decision, operator_id)

                # Update metrics
                self.metrics["total_dequeued"] += 1

                self.logger.info(
                    f"Decision dequeued: {decision.decision_id} "
                    f"(risk={decision.risk_level.value}, operator={operator_id})"
                )

                return decision

        return None  # All queues empty

    def get_pending_decisions(
        self, risk_level: Optional[RiskLevel] = None, operator_id: Optional[str] = None
    ) -> List[HITLDecision]:
        """
        Get pending decisions without removing from queue.

        Args:
            risk_level: Filter by risk level (None = all)
            operator_id: Filter by assigned operator (None = all)

        Returns:
            List of pending decisions
        """
        decisions = []

        # Determine which queues to check
        if risk_level:
            queues_to_check = [(risk_level, self._queues[risk_level])]
        else:
            queues_to_check = list(self._queues.items())

        # Collect decisions
        for level, queue in queues_to_check:
            for queued in queue:
                # Filter by operator if specified
                # Only skip if decision is assigned to a DIFFERENT operator
                # Unassigned decisions (None) are available to all operators
                if (operator_id and
                    queued.decision.assigned_operator is not None and
                    queued.decision.assigned_operator != operator_id):
                    continue

                decisions.append(queued.decision)

        return decisions

    def get_decision(self, decision_id: str) -> Optional[QueuedDecision]:
        """Get decision from queue by ID (without removing)."""
        return self._decisions.get(decision_id)

    def remove_decision(self, decision_id: str) -> bool:
        """
        Remove decision from queue by ID.

        Args:
            decision_id: Decision ID to remove

        Returns:
            True if removed, False if not found
        """
        queued = self._decisions.get(decision_id)
        if queued is None:
            return False

        # Remove from queue
        risk_level = queued.decision.risk_level
        queue = self._queues[risk_level]

        try:
            queue.remove(queued)
            del self._decisions[decision_id]
            self.logger.info(f"Decision removed from queue: {decision_id}")
            return True
        except ValueError:
            self.logger.warning(f"Decision not in queue: {decision_id}")
            return False

    def assign_to_operator(self, decision: HITLDecision, operator_id: str):
        """
        Assign decision to operator.

        Args:
            decision: Decision to assign
            operator_id: Operator ID
        """
        self._assign_to_operator(decision, operator_id)

    def _assign_to_operator(self, decision: HITLDecision, operator_id: str):
        """Internal assignment method."""
        decision.assigned_operator = operator_id
        decision.assigned_at = datetime.utcnow()

        # Track assignment
        if operator_id not in self._operator_assignments:
            self._operator_assignments[operator_id] = []
        self._operator_assignments[operator_id].append(decision.decision_id)

        # Add operator to set
        self._operators.add(operator_id)

        # Update metrics
        self.metrics["total_assigned"] += 1

        self.logger.info(
            f"Decision assigned: {decision.decision_id} → {operator_id}"
        )

    def get_next_operator_round_robin(self) -> Optional[str]:
        """Get next operator using round-robin assignment."""
        if not self._operators:
            return None

        operators = sorted(list(self._operators))
        operator = operators[self._current_operator_index % len(operators)]
        self._current_operator_index += 1

        return operator

    def check_sla_status(self):
        """Check SLA status for all queued decisions."""
        for queued in self._decisions.values():
            self.sla_monitor.check_decision(queued)

    def _handle_sla_warning(self, decision: HITLDecision):
        """Handle SLA warning (callback from SLAMonitor)."""
        self.metrics["sla_warnings"] += 1
        self.logger.warning(
            f"SLA warning for decision: {decision.decision_id} "
            f"(risk={decision.risk_level.value})"
        )

    def _handle_sla_violation(self, decision: HITLDecision):
        """Handle SLA violation (callback from SLAMonitor)."""
        self.metrics["sla_violations"] += 1
        self.logger.error(
            f"SLA violation for decision: {decision.decision_id} "
            f"(risk={decision.risk_level.value})"
        )

    def _calculate_priority(self, decision: HITLDecision) -> float:
        """
        Calculate priority score for decision.

        Higher score = higher priority.

        Args:
            decision: Decision to prioritize

        Returns:
            Priority score (0.0 to 1.0)
        """
        # Base priority from risk level
        risk_priority = {
            RiskLevel.CRITICAL: 1.0,
            RiskLevel.HIGH: 0.75,
            RiskLevel.MEDIUM: 0.5,
            RiskLevel.LOW: 0.25,
        }[decision.risk_level]

        # Boost by threat score
        threat_boost = decision.context.threat_score * 0.1

        # Boost by confidence (higher confidence = slightly higher priority)
        confidence_boost = decision.context.confidence * 0.05

        total_priority = risk_priority + threat_boost + confidence_boost
        return min(1.0, total_priority)

    def get_total_size(self) -> int:
        """Get total number of decisions in queue."""
        return sum(len(queue) for queue in self._queues.values())

    def get_size_by_risk(self) -> Dict[RiskLevel, int]:
        """Get queue size by risk level."""
        return {level: len(queue) for level, queue in self._queues.items()}

    def get_metrics(self) -> Dict[str, any]:
        """Get queue metrics."""
        return {
            **self.metrics,
            "current_queue_size": self.get_total_size(),
            "queue_by_risk": {
                level.value: size for level, size in self.get_size_by_risk().items()
            },
            "average_time_in_queue": self._calculate_average_time_in_queue(),
        }

    def _calculate_average_time_in_queue(self) -> float:
        """Calculate average time decisions spend in queue (seconds)."""
        if not self._decisions:
            return 0.0

        total_time = sum(
            queued.get_time_in_queue().total_seconds()
            for queued in self._decisions.values()
        )
        return total_time / len(self._decisions)

    def __del__(self):
        """Cleanup: stop SLA monitor."""
        if hasattr(self, 'sla_monitor'):
            self.sla_monitor.stop()
