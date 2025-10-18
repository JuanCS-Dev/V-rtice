"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MAXIMUS AI - Emergency Circuit Breaker
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Module: justice/emergency_circuit_breaker.py
Purpose: Emergency halt system for CRITICAL constitutional violations

AUTHORSHIP:
├─ Architecture & Design: Juan Carlos de Souza (Human)
├─ Implementation: Claude Code v0.8 (Anthropic, 2025-10-14)

DOUTRINA:
├─ Triggered by CRITICAL violations (Lei Zero, Lei I)
├─ Halts all pending actions
├─ Escalates to HITL immediately
└─ Enters safe mode (requires human approval for any action)

INTEGRATION:
└─ Called by ConstitutionalValidator when CRITICAL violation detected
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import logging
from typing import Dict, Any, List
from datetime import datetime
from justice.constitutional_validator import ViolationReport

logger = logging.getLogger(__name__)


class EmergencyCircuitBreaker:
    """Handles emergency stops for CRITICAL constitutional violations.

    When triggered:
    1. Halt all pending actions
    2. Escalate to HITL immediately
    3. Log critical incident with full context
    4. Enter safe mode (require human approval for any action)

    This is a fail-safe mechanism to prevent MAXIMUS from executing
    actions that violate Lei Zero or Lei I.

    Example usage:
        breaker = EmergencyCircuitBreaker()

        # In validation code:
        if verdict.requires_emergency_stop():
            breaker.trigger(verdict)

        # Check if in safe mode before any action:
        if breaker.safe_mode:
            raise RuntimeError("System in SAFE MODE - human approval required")
    """

    def __init__(self):
        """Initialize emergency circuit breaker."""
        self.triggered = False
        self.safe_mode = False
        self.trigger_count = 0
        self.incidents: List[ViolationReport] = []

    def trigger(self, violation: ViolationReport):
        """Trigger emergency circuit breaker.

        This is called when a CRITICAL constitutional violation is detected.
        System enters safe mode and requires human oversight to resume.

        Args:
            violation: ViolationReport with CRITICAL level
        """
        self.triggered = True
        self.trigger_count += 1
        self.incidents.append(violation)

        logger.critical("=" * 80)
        logger.critical("╔═══════════════════════════════════════════════════════════╗")
        logger.critical("║     EMERGENCY CIRCUIT BREAKER TRIGGERED                   ║")
        logger.critical("╚═══════════════════════════════════════════════════════════╝")
        logger.critical(f"Timestamp: {datetime.utcnow().isoformat()}")
        logger.critical(f"Violation: {violation.violated_law}")
        logger.critical(f"Level: {violation.level.name}")
        logger.critical(f"Type: {violation.violation_type.value if violation.violation_type else 'Unknown'}")
        logger.critical(f"Description: {violation.description}")
        logger.critical(f"Evidence:")
        for i, evidence_item in enumerate(violation.evidence, 1):
            logger.critical(f"  {i}. {evidence_item}")
        logger.critical(f"Action Details: {violation.action}")
        logger.critical(f"Context: {violation.context}")
        logger.critical("=" * 80)

        # Enter safe mode
        self.enter_safe_mode()

        # Escalate to HITL
        self._escalate_to_hitl(violation)

        # Log incident
        self._log_incident(violation)

    def enter_safe_mode(self):
        """Enter safe mode - all actions require human approval.

        In safe mode:
        - No autonomous actions allowed
        - All decisions must be reviewed by human
        - System waits for human authorization
        - Logged to audit trail
        """
        self.safe_mode = True
        logger.warning("=" * 80)
        logger.warning("╔═══════════════════════════════════════════════════════════╗")
        logger.warning("║           SYSTEM ENTERED SAFE MODE                        ║")
        logger.warning("║   All actions require human approval                      ║")
        logger.warning("╚═══════════════════════════════════════════════════════════╝")
        logger.warning("=" * 80)

    def exit_safe_mode(self, human_authorization: str):
        """Exit safe mode with human authorization.

        Args:
            human_authorization: Authorization code/token from human operator
                Format: "HUMAN_AUTH_{timestamp}_{operator_id}"

        Raises:
            ValueError: If authorization is invalid
        """
        # Validate authorization against expected format
        if not human_authorization or not human_authorization.strip():
            raise ValueError("Invalid authorization: empty or whitespace")

        # Validate format: HUMAN_AUTH_{timestamp}_{operator_id}
        if not human_authorization.startswith("HUMAN_AUTH_"):
            raise ValueError(
                f"Invalid authorization format: must start with 'HUMAN_AUTH_', got '{human_authorization[:20]}...'"
            )
        
        parts = human_authorization.split("_")
        if len(parts) < 4:  # HUMAN, AUTH, timestamp, operator_id
            raise ValueError(
                f"Invalid authorization format: expected 'HUMAN_AUTH_{{timestamp}}_{{operator_id}}', got '{human_authorization}'"
            )
        
        # Validate timestamp is numeric
        try:
            timestamp = int(parts[2])
            # Check timestamp is not too old (e.g., within last hour)
            current_ts = int(datetime.utcnow().timestamp())
            if abs(current_ts - timestamp) > 3600:
                raise ValueError(f"Authorization timestamp too old or in future: {timestamp}")
        except (ValueError, IndexError) as e:
            raise ValueError(f"Invalid authorization timestamp: {e}")

        # Additional validation could include:
        # - Check authorization format
        # - Verify operator ID exists
        # - Check timestamp is recent
        # - Validate signature/token

        self.safe_mode = False
        self.triggered = False

        logger.info("=" * 80)
        logger.info("SAFE MODE DISABLED")
        logger.info(f"Human authorization: {human_authorization}")
        logger.info(f"Timestamp: {datetime.utcnow().isoformat()}")
        logger.info(f"Total incidents during safe mode: {len(self.incidents)}")
        logger.info("=" * 80)

    def _escalate_to_hitl(self, violation: ViolationReport):
        """Escalate critical violation to Human-in-the-Loop system.

        Creates escalation payload and sends to HITL service.
        HITL service should:
        - Alert on-call operator
        - Display violation details
        - Request immediate review
        - Provide authorization interface

        Args:
            violation: ViolationReport to escalate
        """
        escalation = {
            "type": "constitutional_violation",
            "severity": "CRITICAL",
            "violation": violation.violated_law,
            "violation_type": violation.violation_type.value if violation.violation_type else None,
            "description": violation.description,
            "evidence": violation.evidence,
            "action": violation.action,
            "context": violation.context,
            "requires_immediate_attention": True,
            "timestamp": datetime.utcnow().isoformat(),
            "breach_count": self.trigger_count
        }

        logger.critical("=" * 80)
        logger.critical("HITL ESCALATION INITIATED")
        logger.critical(f"Escalation Type: {escalation['type']}")
        logger.critical(f"Severity: {escalation['severity']}")
        logger.critical(f"Requires Immediate Attention: {escalation['requires_immediate_attention']}")
        logger.critical("=" * 80)

        # Integration with HITL backend
        try:
            # Write escalation to file queue for HITL system
            escalation_file = Path("/var/log/vertice/hitl_escalations.jsonl")
            escalation_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(escalation_file, "a") as f:
                import json
                f.write(json.dumps(escalation) + "\n")
            
            logger.critical(f"HITL escalation written to {escalation_file}")
        except Exception as e:
            logger.error(f"Failed to write HITL escalation: {e}")

        logger.critical(f"HITL Escalation Payload: {escalation}")

    def _log_incident(self, violation: ViolationReport):
        """Log critical incident for audit trail.

        Incident log should be:
        - Immutable (write-only)
        - Timestamped
        - Cryptographically signed (future enhancement)
        - Stored in secure audit database

        Args:
            violation: ViolationReport to log
        """
        incident = {
            "timestamp": datetime.utcnow().isoformat(),
            "incident_id": f"CONST_VIOLATION_{self.trigger_count:04d}",
            "violation_level": violation.level.name,
            "violation_type": violation.violation_type.value if violation.violation_type else None,
            "violated_law": violation.violated_law,
            "description": violation.description,
            "evidence": violation.evidence,
            "action": violation.action,
            "context": violation.context,
            "recommendation": violation.recommendation,
            "safe_mode_triggered": self.safe_mode,
            "total_incidents": len(self.incidents)
        }

        # Write to audit log database
        audit_file = Path("/var/log/vertice/circuit_breaker_audit.jsonl")
        audit_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(audit_file, "a") as f:
                import json
                f.write(json.dumps(incident) + "\n")
            logger.info(f"Audit incident logged to {audit_file}")
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")

        logger.critical("=" * 80)
        logger.critical("INCIDENT LOGGED TO AUDIT TRAIL")
        logger.critical(f"Incident ID: {incident['incident_id']}")
        logger.critical(f"Timestamp: {incident['timestamp']}")
        logger.critical("=" * 80)

        # For now, log to standard logger
        logger.critical(f"Incident Details: {incident}")

    def get_status(self) -> Dict[str, Any]:
        """Return circuit breaker status for monitoring.

        Returns:
            Dictionary with:
            - triggered: Is circuit breaker currently triggered
            - safe_mode: Is system in safe mode
            - trigger_count: How many times breaker has been triggered
            - incident_count: Number of logged incidents
            - last_incident: Most recent incident (if any)
        """
        status = {
            "triggered": self.triggered,
            "safe_mode": self.safe_mode,
            "trigger_count": self.trigger_count,
            "incident_count": len(self.incidents),
            "last_incident": None
        }

        if self.incidents:
            last = self.incidents[-1]
            status["last_incident"] = {
                "violated_law": last.violated_law,
                "level": last.level.name,
                "type": last.violation_type.value if last.violation_type else None,
                "description": last.description
            }

        return status

    def get_incident_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Return recent incident history.

        Args:
            limit: Maximum number of incidents to return

        Returns:
            List of incident summaries, most recent first
        """
        recent_incidents = self.incidents[-limit:][::-1]  # Last N, reversed

        return [
            {
                "violated_law": incident.violated_law,
                "level": incident.level.name,
                "type": incident.violation_type.value if incident.violation_type else None,
                "description": incident.description,
                "evidence_count": len(incident.evidence)
            }
            for incident in recent_incidents
        ]

    def reset(self, authorization: str):
        """Reset circuit breaker (for testing or post-incident).

        Args:
            authorization: Human authorization required

        Raises:
            ValueError: If not authorized
        """
        if not authorization or not authorization.strip():
            raise ValueError("Authorization required to reset circuit breaker")

        self.triggered = False
        self.safe_mode = False
        # Note: trigger_count and incidents are NOT reset (audit trail)

        logger.warning(f"Circuit breaker reset with authorization: {authorization}")
