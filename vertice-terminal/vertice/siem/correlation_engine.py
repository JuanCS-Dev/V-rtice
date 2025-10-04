"""
🔗 Correlation Engine - Correlação de eventos e detecção de attack chains

Correlaciona eventos de log para identificar:
- Attack chains (multi-stage attacks)
- Lateral movement
- Privilege escalation sequences
- Data exfiltration patterns
- Brute force attempts
- Suspicious user behavior
- Command & Control activity
- Persistence mechanisms

Features:
- Time-based correlation windows
- Multi-source correlation
- Pattern matching
- Statistical anomaly detection
- Machine learning correlation
- Custom correlation rules
- Real-time alerting
- MITRE ATT&CK mapping
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set, Callable
from datetime import datetime, timedelta
from enum import Enum
import logging
import hashlib

logger = logging.getLogger(__name__)


class CorrelationType(Enum):
    """Tipos de correlação"""
    TIME_WINDOW = "time_window"  # Eventos no mesmo intervalo
    SEQUENTIAL = "sequential"  # Eventos em sequência
    FREQUENCY = "frequency"  # Frequência anormal
    PATTERN = "pattern"  # Pattern matching
    STATISTICAL = "statistical"  # Anomalia estatística
    BEHAVIORAL = "behavioral"  # Comportamento anormal
    GEOLOCATION = "geolocation"  # Geolocalização suspeita
    CUSTOM = "custom"  # Regra customizada


class CorrelationSeverity(Enum):
    """Severidade da correlação"""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CorrelationStatus(Enum):
    """Status da correlação"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"
    INVESTIGATING = "investigating"


@dataclass
class CorrelationCondition:
    """
    Condição de correlação

    Attributes:
        field: Campo a verificar
        operator: Operador (eq, ne, gt, lt, contains, regex)
        value: Valor esperado
        threshold: Threshold (para frequency/statistical)
    """
    field: str
    operator: str
    value: Any
    threshold: Optional[int] = None


@dataclass
class CorrelationRule:
    """
    Regra de correlação

    Attributes:
        id: Rule ID
        name: Rule name
        description: Rule description
        correlation_type: Type of correlation
        severity: Severity level
        enabled: If rule is enabled
        conditions: Correlation conditions
        time_window: Time window in seconds
        event_count: Minimum event count
        mitre_tactics: MITRE ATT&CK tactics
        mitre_techniques: MITRE ATT&CK techniques
        tags: Rule tags
        metadata: Additional metadata
    """
    id: str
    name: str
    description: str
    correlation_type: CorrelationType
    severity: CorrelationSeverity
    enabled: bool = True

    # Correlation logic
    conditions: List[CorrelationCondition] = field(default_factory=list)
    time_window: int = 300  # 5 minutes default
    event_count: int = 2  # Minimum events to correlate

    # MITRE ATT&CK mapping
    mitre_tactics: List[str] = field(default_factory=list)
    mitre_techniques: List[str] = field(default_factory=list)

    # Metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Statistics
    executions: int = 0
    matches: int = 0
    last_match: Optional[datetime] = None


@dataclass
class CorrelatedEvent:
    """
    Evento correlacionado

    Attributes:
        id: Event ID
        rule_id: Correlation rule ID
        name: Event name
        description: Event description
        severity: Severity level
        status: Event status
        created_at: Creation timestamp
        updated_at: Last update timestamp
        events: Correlated log events
        event_count: Number of events
        time_span: Time span of events
        indicators: Attack indicators
        mitre_tactics: MITRE ATT&CK tactics
        mitre_techniques: MITRE ATT&CK techniques
        remediation: Remediation suggestions
        metadata: Additional metadata
    """
    id: str
    rule_id: str
    name: str
    description: str
    severity: CorrelationSeverity
    status: CorrelationStatus = CorrelationStatus.ACTIVE

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Correlated events
    events: List[Dict[str, Any]] = field(default_factory=list)
    event_count: int = 0
    time_span: timedelta = timedelta(0)

    # Attack chain info
    indicators: List[str] = field(default_factory=list)
    mitre_tactics: List[str] = field(default_factory=list)
    mitre_techniques: List[str] = field(default_factory=list)

    # Response
    remediation: List[str] = field(default_factory=list)

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


class CorrelationEngine:
    """
    Event Correlation Engine

    Features:
    - Multi-source event correlation
    - Time-based correlation windows
    - Pattern matching
    - Attack chain detection
    - MITRE ATT&CK mapping
    - Real-time alerting
    - Custom rules
    """

    def __init__(
        self,
        backend_url: Optional[str] = None,
        use_backend: bool = True,
    ):
        """
        Args:
            backend_url: URL do siem_service
            use_backend: Se True, usa backend
        """
        self.backend_url = backend_url or "http://localhost:8023"
        self.use_backend = use_backend

        # Correlation rules
        self.rules: Dict[str, CorrelationRule] = {}

        # Active correlations (in-memory)
        self.active_correlations: Dict[str, CorrelatedEvent] = {}

        # Event buffer for correlation (sliding window)
        self.event_buffer: List[Dict[str, Any]] = []
        self.buffer_max_size: int = 10000
        self.buffer_max_age: int = 3600  # 1 hour

        # Callbacks for correlated events
        self.callbacks: List[Callable[[CorrelatedEvent], None]] = []

        # Statistics
        self.total_events_processed: int = 0
        self.total_correlations: int = 0

        # Load default rules
        self._load_default_rules()

    def _load_default_rules(self):
        """Carrega regras de correlação padrão"""

        # 1. Brute Force Detection
        self.add_rule(CorrelationRule(
            id="brute-force-ssh",
            name="SSH Brute Force Attack",
            description="Multiple failed SSH login attempts from same source",
            correlation_type=CorrelationType.FREQUENCY,
            severity=CorrelationSeverity.HIGH,
            conditions=[
                CorrelationCondition(
                    field="message",
                    operator="contains",
                    value="Failed password",
                ),
            ],
            time_window=300,  # 5 minutes
            event_count=5,  # 5+ failed attempts
            mitre_tactics=["TA0001"],  # Initial Access
            mitre_techniques=["T1110"],  # Brute Force
            tags=["brute-force", "ssh", "authentication"],
        ))

        # 2. Privilege Escalation Sequence
        self.add_rule(CorrelationRule(
            id="privilege-escalation",
            name="Privilege Escalation Sequence",
            description="Sequence of privilege escalation events",
            correlation_type=CorrelationType.SEQUENTIAL,
            severity=CorrelationSeverity.CRITICAL,
            conditions=[
                CorrelationCondition(
                    field="message",
                    operator="contains",
                    value="sudo",
                ),
            ],
            time_window=600,  # 10 minutes
            event_count=3,
            mitre_tactics=["TA0004"],  # Privilege Escalation
            mitre_techniques=["T1548"],  # Abuse Elevation Control
            tags=["privilege-escalation", "sudo"],
        ))

        # 3. Data Exfiltration Pattern
        self.add_rule(CorrelationRule(
            id="data-exfiltration",
            name="Data Exfiltration Pattern",
            description="Large data transfer to external destination",
            correlation_type=CorrelationType.STATISTICAL,
            severity=CorrelationSeverity.CRITICAL,
            conditions=[
                CorrelationCondition(
                    field="bytes_sent",
                    operator="gt",
                    value=100000000,  # 100MB
                    threshold=3,  # 3 times in window
                ),
            ],
            time_window=1800,  # 30 minutes
            event_count=3,
            mitre_tactics=["TA0010"],  # Exfiltration
            mitre_techniques=["T1041"],  # Exfiltration Over C2 Channel
            tags=["exfiltration", "data-transfer"],
        ))

        # 4. Lateral Movement
        self.add_rule(CorrelationRule(
            id="lateral-movement",
            name="Lateral Movement Detection",
            description="User accessing multiple systems in short time",
            correlation_type=CorrelationType.PATTERN,
            severity=CorrelationSeverity.HIGH,
            conditions=[
                CorrelationCondition(
                    field="event_type",
                    operator="eq",
                    value="authentication",
                ),
            ],
            time_window=900,  # 15 minutes
            event_count=5,  # 5+ different hosts
            mitre_tactics=["TA0008"],  # Lateral Movement
            mitre_techniques=["T1021"],  # Remote Services
            tags=["lateral-movement", "authentication"],
        ))

        # 5. Port Scanning
        self.add_rule(CorrelationRule(
            id="port-scan",
            name="Port Scanning Activity",
            description="Multiple connection attempts to different ports",
            correlation_type=CorrelationType.FREQUENCY,
            severity=CorrelationSeverity.MEDIUM,
            conditions=[
                CorrelationCondition(
                    field="event_type",
                    operator="eq",
                    value="network_connection",
                ),
            ],
            time_window=60,  # 1 minute
            event_count=20,  # 20+ ports
            mitre_tactics=["TA0043"],  # Reconnaissance
            mitre_techniques=["T1046"],  # Network Service Scanning
            tags=["reconnaissance", "port-scan"],
        ))

        # 6. Suspicious Process Execution
        self.add_rule(CorrelationRule(
            id="suspicious-process-chain",
            name="Suspicious Process Execution Chain",
            description="Sequence of suspicious process executions",
            correlation_type=CorrelationType.SEQUENTIAL,
            severity=CorrelationSeverity.HIGH,
            conditions=[
                CorrelationCondition(
                    field="process_name",
                    operator="regex",
                    value=r"(powershell|cmd|bash|sh)\.exe",
                ),
            ],
            time_window=600,  # 10 minutes
            event_count=3,
            mitre_tactics=["TA0002"],  # Execution
            mitre_techniques=["T1059"],  # Command and Scripting Interpreter
            tags=["execution", "process"],
        ))

        logger.info(f"Loaded {len(self.rules)} default correlation rules")

    def add_rule(self, rule: CorrelationRule) -> None:
        """
        Adiciona regra de correlação

        Args:
            rule: CorrelationRule object
        """
        self.rules[rule.id] = rule
        logger.info(f"Added correlation rule: {rule.name}")

    def remove_rule(self, rule_id: str) -> bool:
        """Remove regra de correlação"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info(f"Removed correlation rule: {rule_id}")
            return True
        return False

    def process_event(self, event: Dict[str, Any]) -> List[CorrelatedEvent]:
        """
        Processa evento e verifica correlações

        Args:
            event: Log event (dict format)

        Returns:
            List of new correlated events
        """
        self.total_events_processed += 1

        # Add to buffer
        self._add_to_buffer(event)

        # Clean old events from buffer
        self._clean_buffer()

        # Check correlations
        new_correlations = []

        for rule in self.rules.values():
            if not rule.enabled:
                continue

            # Check if event matches rule conditions
            if not self._event_matches_conditions(event, rule.conditions):
                continue

            # Get correlated events from buffer
            correlated = self._find_correlated_events(rule)

            if len(correlated) >= rule.event_count:
                # Create correlated event
                correlation = self._create_correlation(rule, correlated)
                new_correlations.append(correlation)

                # Execute callbacks
                for callback in self.callbacks:
                    try:
                        callback(correlation)
                    except Exception as e:
                        logger.error(f"Callback execution failed: {e}")

        return new_correlations

    def _add_to_buffer(self, event: Dict[str, Any]) -> None:
        """Adiciona evento ao buffer"""
        # Add timestamp if not present
        if "timestamp" not in event:
            event["timestamp"] = datetime.now()

        self.event_buffer.append(event)

        # Limit buffer size
        if len(self.event_buffer) > self.buffer_max_size:
            self.event_buffer = self.event_buffer[-self.buffer_max_size:]

    def _clean_buffer(self) -> None:
        """Remove eventos antigos do buffer"""
        cutoff = datetime.now() - timedelta(seconds=self.buffer_max_age)

        self.event_buffer = [
            e for e in self.event_buffer
            if e.get("timestamp", datetime.now()) > cutoff
        ]

    def _event_matches_conditions(
        self,
        event: Dict[str, Any],
        conditions: List[CorrelationCondition],
    ) -> bool:
        """Verifica se evento match condições"""
        import re

        for condition in conditions:
            field_value = event.get(condition.field)

            if field_value is None:
                return False

            # Operator evaluation
            if condition.operator == "eq":
                if field_value != condition.value:
                    return False

            elif condition.operator == "ne":
                if field_value == condition.value:
                    return False

            elif condition.operator == "gt":
                if not (field_value > condition.value):
                    return False

            elif condition.operator == "lt":
                if not (field_value < condition.value):
                    return False

            elif condition.operator == "contains":
                if condition.value not in str(field_value):
                    return False

            elif condition.operator == "regex":
                if not re.search(condition.value, str(field_value)):
                    return False

        return True

    def _find_correlated_events(
        self,
        rule: CorrelationRule,
    ) -> List[Dict[str, Any]]:
        """Encontra eventos correlacionados para a regra"""
        cutoff = datetime.now() - timedelta(seconds=rule.time_window)

        correlated = []

        for event in self.event_buffer:
            # Check time window
            event_time = event.get("timestamp", datetime.now())
            if event_time < cutoff:
                continue

            # Check conditions
            if self._event_matches_conditions(event, rule.conditions):
                correlated.append(event)

        return correlated

    def _create_correlation(
        self,
        rule: CorrelationRule,
        events: List[Dict[str, Any]],
    ) -> CorrelatedEvent:
        """Cria evento correlacionado"""
        import uuid

        # Generate unique ID
        correlation_id = f"corr-{uuid.uuid4().hex[:16]}"

        # Calculate time span
        timestamps = [e.get("timestamp", datetime.now()) for e in events]
        time_span = max(timestamps) - min(timestamps)

        # Extract indicators
        indicators = self._extract_indicators(events)

        # Create correlation
        correlation = CorrelatedEvent(
            id=correlation_id,
            rule_id=rule.id,
            name=rule.name,
            description=rule.description,
            severity=rule.severity,
            events=events,
            event_count=len(events),
            time_span=time_span,
            indicators=indicators,
            mitre_tactics=rule.mitre_tactics,
            mitre_techniques=rule.mitre_techniques,
            remediation=self._generate_remediation(rule),
        )

        # Update statistics
        rule.executions += 1
        rule.matches += 1
        rule.last_match = datetime.now()

        self.active_correlations[correlation_id] = correlation
        self.total_correlations += 1

        logger.info(f"Created correlation: {correlation.name} ({correlation.id})")

        return correlation

    def _extract_indicators(self, events: List[Dict[str, Any]]) -> List[str]:
        """Extrai indicadores dos eventos"""
        indicators = set()

        for event in events:
            # IP addresses
            if "source_ip" in event:
                indicators.add(f"IP: {event['source_ip']}")
            if "dest_ip" in event:
                indicators.add(f"IP: {event['dest_ip']}")

            # Users
            if "user" in event:
                indicators.add(f"User: {event['user']}")

            # Hosts
            if "hostname" in event:
                indicators.add(f"Host: {event['hostname']}")

            # Processes
            if "process_name" in event:
                indicators.add(f"Process: {event['process_name']}")

        return list(indicators)

    def _generate_remediation(self, rule: CorrelationRule) -> List[str]:
        """Gera sugestões de remediação"""
        remediation = []

        # Generic based on severity
        if rule.severity == CorrelationSeverity.CRITICAL:
            remediation.append("Isolate affected systems immediately")
            remediation.append("Contact incident response team")

        elif rule.severity == CorrelationSeverity.HIGH:
            remediation.append("Investigate affected systems")
            remediation.append("Review access logs")

        # Specific based on tags
        if "brute-force" in rule.tags:
            remediation.append("Block source IP")
            remediation.append("Review password policies")

        if "privilege-escalation" in rule.tags:
            remediation.append("Review sudo/admin access")
            remediation.append("Verify user privileges")

        if "exfiltration" in rule.tags:
            remediation.append("Block outbound traffic")
            remediation.append("Review data access logs")

        return remediation

    def register_callback(
        self,
        callback: Callable[[CorrelatedEvent], None],
    ) -> None:
        """
        Registra callback para eventos correlacionados

        Args:
            callback: Callback function
        """
        self.callbacks.append(callback)
        logger.info("Registered correlation callback")

    def get_correlation(self, correlation_id: str) -> Optional[CorrelatedEvent]:
        """Retorna correlação por ID"""
        return self.active_correlations.get(correlation_id)

    def list_correlations(
        self,
        severity: Optional[CorrelationSeverity] = None,
        status: Optional[CorrelationStatus] = None,
        limit: int = 100,
    ) -> List[CorrelatedEvent]:
        """
        Lista correlações com filtros

        Args:
            severity: Filter by severity
            status: Filter by status
            limit: Max results

        Returns:
            List of CorrelatedEvent
        """
        correlations = list(self.active_correlations.values())

        if severity:
            correlations = [c for c in correlations if c.severity == severity]

        if status:
            correlations = [c for c in correlations if c.status == status]

        # Sort by created_at (most recent first)
        correlations = sorted(correlations, key=lambda c: c.created_at, reverse=True)

        return correlations[:limit]

    def update_correlation_status(
        self,
        correlation_id: str,
        status: CorrelationStatus,
    ) -> bool:
        """Atualiza status de correlação"""
        correlation = self.active_correlations.get(correlation_id)

        if not correlation:
            return False

        correlation.status = status
        correlation.updated_at = datetime.now()

        logger.info(f"Updated correlation status: {correlation_id} -> {status.value}")

        return True

    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas"""

        # Count by severity
        by_severity = {}
        for corr in self.active_correlations.values():
            sev = corr.severity.value
            by_severity[sev] = by_severity.get(sev, 0) + 1

        # Count by status
        by_status = {}
        for corr in self.active_correlations.values():
            status = corr.status.value
            by_status[status] = by_status.get(status, 0) + 1

        # Top rules
        top_rules = sorted(
            self.rules.values(),
            key=lambda r: r.matches,
            reverse=True,
        )[:5]

        return {
            "total_rules": len(self.rules),
            "enabled_rules": len([r for r in self.rules.values() if r.enabled]),
            "total_events_processed": self.total_events_processed,
            "total_correlations": self.total_correlations,
            "active_correlations": len(self.active_correlations),
            "buffer_size": len(self.event_buffer),
            "by_severity": by_severity,
            "by_status": by_status,
            "top_rules": [
                {
                    "id": r.id,
                    "name": r.name,
                    "matches": r.matches,
                }
                for r in top_rules
            ],
        }

    def list_rules(
        self,
        correlation_type: Optional[CorrelationType] = None,
        severity: Optional[CorrelationSeverity] = None,
        enabled_only: bool = False,
    ) -> List[CorrelationRule]:
        """
        Lista regras com filtros

        Args:
            correlation_type: Filter by type
            severity: Filter by severity
            enabled_only: Only enabled rules

        Returns:
            List of CorrelationRule
        """
        rules = list(self.rules.values())

        if correlation_type:
            rules = [r for r in rules if r.correlation_type == correlation_type]

        if severity:
            rules = [r for r in rules if r.severity == severity]

        if enabled_only:
            rules = [r for r in rules if r.enabled]

        return rules
