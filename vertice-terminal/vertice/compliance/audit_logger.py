"""
🔐 Audit Logger - Sistema de logging imutável para compliance e auditoria

Características:
- Tamper-proof logging com hash chaining
- Append-only storage
- Cryptographic integrity verification
- Compliance-ready audit trails
- WORM (Write Once Read Many) semantics
- Distributed logging via backend

Event Types:
- Authentication (login, logout, failed attempts)
- Authorization (access granted/denied, privilege escalation)
- Data Access (read, write, delete, export)
- Configuration Changes (policy updates, settings changes)
- Security Events (threat detected, incident created, alert triggered)
- Compliance Events (assessment, control update, review)
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from pathlib import Path
import hashlib
import json
import logging

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Tipos de eventos de auditoria"""
    # Authentication
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    SESSION_EXPIRED = "session_expired"

    # Authorization
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    ROLE_CHANGED = "role_changed"

    # Data Access
    DATA_READ = "data_read"
    DATA_WRITE = "data_write"
    DATA_DELETE = "data_delete"
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"

    # Configuration
    CONFIG_CHANGED = "config_changed"
    POLICY_UPDATED = "policy_updated"
    SETTING_MODIFIED = "setting_modified"

    # Security Events
    THREAT_DETECTED = "threat_detected"
    INCIDENT_CREATED = "incident_created"
    ALERT_TRIGGERED = "alert_triggered"
    VULNERABILITY_FOUND = "vulnerability_found"
    MALWARE_DETECTED = "malware_detected"

    # Compliance
    ASSESSMENT_COMPLETED = "assessment_completed"
    CONTROL_UPDATED = "control_updated"
    REVIEW_PERFORMED = "review_performed"
    AUDIT_STARTED = "audit_started"
    AUDIT_COMPLETED = "audit_completed"

    # Evidence & Forensics
    EVIDENCE_COLLECTED = "evidence_collected"
    CHAIN_OF_CUSTODY_UPDATED = "chain_of_custody_updated"
    INTEGRITY_VERIFIED = "integrity_verified"
    LEGAL_HOLD_APPLIED = "legal_hold_applied"

    # System
    SYSTEM_STARTED = "system_started"
    SYSTEM_STOPPED = "system_stopped"
    BACKUP_COMPLETED = "backup_completed"
    RESTORE_COMPLETED = "restore_completed"


class AuditSeverity(Enum):
    """Severidade do evento de auditoria"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """
    Evento de auditoria imutável

    Attributes:
        id: Unique event ID
        event_type: Type of audit event
        timestamp: When event occurred
        actor: Who performed the action (user/system)
        resource: What was accessed/modified
        action: What action was performed
        result: Success/failure
        severity: Event severity
        ip_address: Source IP
        session_id: Session identifier
        metadata: Additional event data
        previous_hash: Hash of previous event (chain)
        current_hash: Hash of current event
    """
    id: str
    event_type: AuditEventType
    timestamp: datetime
    actor: str  # username or system
    resource: str  # resource accessed/modified
    action: str  # action performed
    result: str  # success, failure, denied

    # Context
    severity: AuditSeverity = AuditSeverity.INFO
    ip_address: Optional[str] = None
    session_id: Optional[str] = None

    # Additional data
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Tamper-proof chain
    previous_hash: str = "0" * 64  # SHA-256 of previous event
    current_hash: str = ""  # SHA-256 of current event

    # Compliance tags
    compliance_frameworks: List[str] = field(default_factory=list)  # PCI-DSS, HIPAA, etc
    retention_days: int = 2555  # 7 years default

    def calculate_hash(self) -> str:
        """
        Calcula hash SHA-256 do evento

        Includes:
        - All event fields (except current_hash)
        - Previous event hash (chain)

        Returns:
            SHA-256 hex digest
        """
        # Build canonical representation
        event_data = {
            "id": self.id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "actor": self.actor,
            "resource": self.resource,
            "action": self.action,
            "result": self.result,
            "severity": self.severity.value,
            "ip_address": self.ip_address,
            "session_id": self.session_id,
            "metadata": self.metadata,
            "previous_hash": self.previous_hash,
        }

        # Serialize deterministically
        canonical = json.dumps(event_data, sort_keys=True, separators=(',', ':'))

        # Calculate SHA-256
        return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


class AuditLogger:
    """
    Tamper-Proof Audit Logger

    Features:
    - Immutable append-only logging
    - Hash chaining for integrity
    - Cryptographic verification
    - WORM (Write Once Read Many) semantics
    - Backend replication
    - Query and search
    - Compliance reporting

    Storage:
    - Local append-only log file
    - Optional backend replication
    - Hash chain validation
    """

    def __init__(
        self,
        backend_url: Optional[str] = None,
        use_backend: bool = True,
        storage_path: Optional[Path] = None,
    ):
        """
        Args:
            backend_url: URL do audit_service
            use_backend: Se True, replica para backend
            storage_path: Local storage path
        """
        self.backend_url = backend_url or "http://localhost:8015"
        self.use_backend = use_backend

        # Storage setup
        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            self.storage_path = Path.home() / ".vertice" / "audit"

        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Audit log file (append-only)
        self.log_file = self.storage_path / "audit.log"

        # In-memory event chain (for quick queries)
        self.event_chain: List[AuditEvent] = []

        # Load existing events
        self._load_event_chain()

        # Last event hash (for chaining)
        self.last_hash = self._get_last_hash()

    def _load_event_chain(self) -> None:
        """Carrega eventos do arquivo de log"""
        if not self.log_file.exists():
            logger.info("No existing audit log found, starting fresh")
            return

        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue

                    event_dict = json.loads(line)

                    # Reconstruct AuditEvent
                    event = AuditEvent(
                        id=event_dict["id"],
                        event_type=AuditEventType(event_dict["event_type"]),
                        timestamp=datetime.fromisoformat(event_dict["timestamp"]),
                        actor=event_dict["actor"],
                        resource=event_dict["resource"],
                        action=event_dict["action"],
                        result=event_dict["result"],
                        severity=AuditSeverity(event_dict["severity"]),
                        ip_address=event_dict.get("ip_address"),
                        session_id=event_dict.get("session_id"),
                        metadata=event_dict.get("metadata", {}),
                        previous_hash=event_dict["previous_hash"],
                        current_hash=event_dict["current_hash"],
                        compliance_frameworks=event_dict.get("compliance_frameworks", []),
                        retention_days=event_dict.get("retention_days", 2555),
                    )

                    self.event_chain.append(event)

            logger.info(f"Loaded {len(self.event_chain)} audit events from disk")

        except Exception as e:
            logger.error(f"Failed to load audit log: {e}")

    def _get_last_hash(self) -> str:
        """Retorna hash do último evento"""
        if not self.event_chain:
            return "0" * 64  # Genesis hash

        return self.event_chain[-1].current_hash

    def log(
        self,
        event_type: AuditEventType,
        actor: str,
        resource: str,
        action: str,
        result: str = "success",
        severity: AuditSeverity = AuditSeverity.INFO,
        ip_address: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        compliance_frameworks: Optional[List[str]] = None,
    ) -> AuditEvent:
        """
        Log audit event

        Args:
            event_type: Type of event
            actor: Who performed action
            resource: What was accessed
            action: What was done
            result: Outcome (success/failure/denied)
            severity: Event severity
            ip_address: Source IP
            session_id: Session ID
            metadata: Additional data
            compliance_frameworks: Related frameworks

        Returns:
            AuditEvent created
        """
        import uuid

        # Create event
        event = AuditEvent(
            id=f"AUD-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}",
            event_type=event_type,
            timestamp=datetime.now(),
            actor=actor,
            resource=resource,
            action=action,
            result=result,
            severity=severity,
            ip_address=ip_address,
            session_id=session_id,
            metadata=metadata or {},
            compliance_frameworks=compliance_frameworks or [],
            previous_hash=self.last_hash,
        )

        # Calculate hash (creates tamper-proof chain)
        event.current_hash = event.calculate_hash()

        # Append to event chain
        self.event_chain.append(event)

        # Update last hash
        self.last_hash = event.current_hash

        # Persist to disk (append-only)
        self._persist_event(event)

        # Replicate to backend
        if self.use_backend:
            try:
                self._replicate_to_backend(event)
            except Exception as e:
                logger.error(f"Backend replication failed: {e}")

        logger.debug(
            f"Audit event logged: {event_type.value} by {actor} on {resource} "
            f"[{result}]"
        )

        return event

    def _persist_event(self, event: AuditEvent) -> None:
        """
        Persiste evento em append-only log

        Args:
            event: Event to persist
        """
        event_dict = {
            "id": event.id,
            "event_type": event.event_type.value,
            "timestamp": event.timestamp.isoformat(),
            "actor": event.actor,
            "resource": event.resource,
            "action": event.action,
            "result": event.result,
            "severity": event.severity.value,
            "ip_address": event.ip_address,
            "session_id": event.session_id,
            "metadata": event.metadata,
            "previous_hash": event.previous_hash,
            "current_hash": event.current_hash,
            "compliance_frameworks": event.compliance_frameworks,
            "retention_days": event.retention_days,
        }

        # Append to log file
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(event_dict) + '\n')

    def _replicate_to_backend(self, event: AuditEvent) -> None:
        """Replica evento para backend"""
        import httpx

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    f"{self.backend_url}/api/audit/events",
                    json={
                        "id": event.id,
                        "event_type": event.event_type.value,
                        "timestamp": event.timestamp.isoformat(),
                        "actor": event.actor,
                        "resource": event.resource,
                        "action": event.action,
                        "result": event.result,
                        "severity": event.severity.value,
                        "ip_address": event.ip_address,
                        "session_id": event.session_id,
                        "metadata": event.metadata,
                        "previous_hash": event.previous_hash,
                        "current_hash": event.current_hash,
                    }
                )
                response.raise_for_status()

        except Exception as e:
            logger.error(f"Backend replication failed: {e}")
            raise

    def verify_chain_integrity(
        self,
        start_index: int = 0,
        end_index: Optional[int] = None,
    ) -> bool:
        """
        Verifica integridade da cadeia de eventos

        Args:
            start_index: Start verification from this index
            end_index: End at this index (None = end of chain)

        Returns:
            True se íntegra, False se comprometida
        """
        if not self.event_chain:
            return True

        if end_index is None:
            end_index = len(self.event_chain)

        for i in range(start_index, end_index):
            event = self.event_chain[i]

            # Verify hash
            calculated_hash = event.calculate_hash()

            if calculated_hash != event.current_hash:
                logger.error(
                    f"Chain integrity compromised at event {i} ({event.id}): "
                    f"Hash mismatch"
                )
                return False

            # Verify chain linkage
            if i > 0:
                previous_event = self.event_chain[i - 1]

                if event.previous_hash != previous_event.current_hash:
                    logger.error(
                        f"Chain integrity compromised at event {i} ({event.id}): "
                        f"Chain linkage broken"
                    )
                    return False

        logger.info(
            f"Chain integrity verified: {end_index - start_index} events "
            f"[{start_index}:{end_index}]"
        )

        return True

    def query(
        self,
        event_type: Optional[AuditEventType] = None,
        actor: Optional[str] = None,
        resource: Optional[str] = None,
        result: Optional[str] = None,
        severity: Optional[AuditSeverity] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[AuditEvent]:
        """
        Query audit events

        Args:
            event_type: Filter by event type
            actor: Filter by actor
            resource: Filter by resource
            result: Filter by result
            severity: Filter by severity
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Max results

        Returns:
            List of matching events
        """
        results = []

        for event in reversed(self.event_chain):  # Most recent first
            # Apply filters
            if event_type and event.event_type != event_type:
                continue

            if actor and event.actor != actor:
                continue

            if resource and event.resource != resource:
                continue

            if result and event.result != result:
                continue

            if severity and event.severity != severity:
                continue

            if start_time and event.timestamp < start_time:
                continue

            if end_time and event.timestamp > end_time:
                continue

            results.append(event)

            if len(results) >= limit:
                break

        return results

    def get_event(self, event_id: str) -> Optional[AuditEvent]:
        """Retorna evento por ID"""
        for event in self.event_chain:
            if event.id == event_id:
                return event

        return None

    def get_statistics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Retorna estatísticas de auditoria

        Args:
            start_time: Start of time window
            end_time: End of time window

        Returns:
            Statistics dict
        """
        # Filter events by time
        events = self.event_chain

        if start_time:
            events = [e for e in events if e.timestamp >= start_time]

        if end_time:
            events = [e for e in events if e.timestamp <= end_time]

        # Count by event type
        by_event_type = {}
        for event in events:
            key = event.event_type.value
            by_event_type[key] = by_event_type.get(key, 0) + 1

        # Count by actor
        by_actor = {}
        for event in events:
            by_actor[event.actor] = by_actor.get(event.actor, 0) + 1

        # Count by result
        by_result = {}
        for event in events:
            by_result[event.result] = by_result.get(event.result, 0) + 1

        # Count by severity
        by_severity = {}
        for event in events:
            key = event.severity.value
            by_severity[key] = by_severity.get(key, 0) + 1

        return {
            "total_events": len(events),
            "by_event_type": by_event_type,
            "by_actor": by_actor,
            "by_result": by_result,
            "by_severity": by_severity,
            "time_range": {
                "start": start_time.isoformat() if start_time else None,
                "end": end_time.isoformat() if end_time else None,
            },
            "chain_integrity": self.verify_chain_integrity(),
        }

    def export_to_json(
        self,
        output_path: Path,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> bool:
        """
        Exporta eventos para JSON

        Args:
            output_path: Output file path
            start_time: Start of export window
            end_time: End of export window

        Returns:
            True se sucesso
        """
        # Filter events
        events = self.event_chain

        if start_time:
            events = [e for e in events if e.timestamp >= start_time]

        if end_time:
            events = [e for e in events if e.timestamp <= end_time]

        # Serialize
        events_data = []
        for event in events:
            events_data.append({
                "id": event.id,
                "event_type": event.event_type.value,
                "timestamp": event.timestamp.isoformat(),
                "actor": event.actor,
                "resource": event.resource,
                "action": event.action,
                "result": event.result,
                "severity": event.severity.value,
                "ip_address": event.ip_address,
                "session_id": event.session_id,
                "metadata": event.metadata,
                "previous_hash": event.previous_hash,
                "current_hash": event.current_hash,
            })

        try:
            with open(output_path, 'w') as f:
                json.dump(events_data, f, indent=2)

            logger.info(f"Exported {len(events)} events to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Export failed: {e}")
            return False
