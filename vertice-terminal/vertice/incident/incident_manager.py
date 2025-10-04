"""
🚨 Incident Manager - Gerenciamento de incidentes de segurança

Integra com backend incident_service para persistência e colaboração.

Lifecycle de incidente:
1. NEW → Incidente criado
2. TRIAGED → Avaliação inicial completa
3. INVESTIGATING → Investigação ativa
4. CONTAINED → Ameaça contida
5. ERADICATED → Ameaça removida
6. RECOVERING → Recuperação de sistemas
7. CLOSED → Incidente resolvido

Baseado em NIST Incident Response Framework
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class IncidentStatus(Enum):
    """Status do incidente (NIST phases)"""
    NEW = "new"
    TRIAGED = "triaged"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    ERADICATED = "eradicated"
    RECOVERING = "recovering"
    CLOSED = "closed"
    FALSE_POSITIVE = "false_positive"


class IncidentSeverity(Enum):
    """Severidade do incidente"""
    SEV0_CRITICAL = "sev0_critical"  # Multiple systems, active breach
    SEV1_HIGH = "sev1_high"  # Single system, data exfiltration
    SEV2_MEDIUM = "sev2_medium"  # Contained threat, no data loss
    SEV3_LOW = "sev3_low"  # Suspicious activity, no confirmed threat
    SEV4_INFO = "sev4_info"  # Informational only


class IncidentCategory(Enum):
    """Categoria do incidente"""
    MALWARE = "malware"
    RANSOMWARE = "ransomware"
    PHISHING = "phishing"
    DATA_BREACH = "data_breach"
    INSIDER_THREAT = "insider_threat"
    DDoS = "ddos"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    CREDENTIAL_COMPROMISE = "credential_compromise"
    LATERAL_MOVEMENT = "lateral_movement"
    POLICY_VIOLATION = "policy_violation"
    OTHER = "other"


@dataclass
class IncidentUpdate:
    """
    Update/nota em incidente
    """
    id: str
    author: str
    timestamp: datetime
    content: str
    is_public: bool = True  # Se False, apenas responders veem
    attachments: List[str] = field(default_factory=list)


@dataclass
class Incident:
    """
    Incidente de segurança
    """
    id: str
    title: str
    description: str
    severity: IncidentSeverity
    status: IncidentStatus
    category: IncidentCategory

    # Timing
    discovered_at: datetime
    reported_at: datetime = field(default_factory=datetime.now)
    first_activity_at: Optional[datetime] = None  # Quando o ataque começou
    contained_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    # Attribution
    created_by: str = "system"
    assigned_to: Optional[str] = None
    team: Optional[str] = None

    # Affected resources
    affected_systems: List[str] = field(default_factory=list)  # Hostnames/IPs
    affected_users: List[str] = field(default_factory=list)
    affected_applications: List[str] = field(default_factory=list)

    # Threat intel
    iocs: List[str] = field(default_factory=list)
    threat_actors: List[str] = field(default_factory=list)
    mitre_tactics: List[str] = field(default_factory=list)
    mitre_techniques: List[str] = field(default_factory=list)

    # Impact
    data_compromised: bool = False
    data_exfiltrated: bool = False
    systems_disrupted: bool = False
    estimated_impact_usd: Optional[float] = None

    # Response
    containment_actions: List[str] = field(default_factory=list)
    eradication_actions: List[str] = field(default_factory=list)
    recovery_actions: List[str] = field(default_factory=list)

    # Communication
    updates: List[IncidentUpdate] = field(default_factory=list)
    stakeholders_notified: List[str] = field(default_factory=list)

    # Related items
    related_alerts: List[str] = field(default_factory=list)
    related_detections: List[str] = field(default_factory=list)
    related_cases: List[str] = field(default_factory=list)
    soar_incident_id: Optional[str] = None

    # Tags and metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class IncidentManager:
    """
    Incident Response Manager

    Features:
    - Incident lifecycle management
    - SLA tracking
    - Metrics e KPIs
    - Backend integration
    - SOAR integration
    - Notification system
    """

    def __init__(
        self,
        backend_url: Optional[str] = None,
        use_backend: bool = True,
        # SLA targets (em minutos)
        sla_triage_sev0: int = 15,
        sla_triage_sev1: int = 30,
        sla_triage_sev2: int = 60,
        sla_containment_sev0: int = 60,
        sla_containment_sev1: int = 240,
    ):
        """
        Args:
            backend_url: URL do incident_service
            use_backend: Se True, persiste no backend
            sla_triage_sev0: SLA para triage de SEV0 (minutos)
            sla_triage_sev1: SLA para triage de SEV1
            sla_triage_sev2: SLA para triage de SEV2
            sla_containment_sev0: SLA para containment de SEV0
            sla_containment_sev1: SLA para containment de SEV1
        """
        self.backend_url = backend_url or "http://localhost:8009"
        self.use_backend = use_backend

        # SLA targets
        self.sla_triage = {
            IncidentSeverity.SEV0_CRITICAL: sla_triage_sev0,
            IncidentSeverity.SEV1_HIGH: sla_triage_sev1,
            IncidentSeverity.SEV2_MEDIUM: sla_triage_sev2,
            IncidentSeverity.SEV3_LOW: 120,
            IncidentSeverity.SEV4_INFO: 240,
        }

        self.sla_containment = {
            IncidentSeverity.SEV0_CRITICAL: sla_containment_sev0,
            IncidentSeverity.SEV1_HIGH: sla_containment_sev1,
            IncidentSeverity.SEV2_MEDIUM: 480,  # 8h
            IncidentSeverity.SEV3_LOW: 1440,  # 24h
        }

        # Incidents cache
        self.incidents: Dict[str, Incident] = {}

    def create_incident(self, incident: Incident) -> str:
        """
        Cria novo incidente

        Args:
            incident: Incident object

        Returns:
            Incident ID
        """
        # Validate
        if not incident.id:
            import uuid
            incident.id = f"INC-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"

        # Auto-set status if NEW
        if incident.status == IncidentStatus.NEW:
            # Auto-triage para incidentes SEV0/SEV1
            if incident.severity in [IncidentSeverity.SEV0_CRITICAL, IncidentSeverity.SEV1_HIGH]:
                logger.warning(
                    f"High severity incident {incident.id} requires immediate triage!"
                )

        # Store
        self.incidents[incident.id] = incident

        # Persist to backend
        if self.use_backend:
            try:
                self._create_incident_backend(incident)
            except Exception as e:
                logger.error(f"Backend incident creation failed: {e}")

        logger.info(
            f"Incident created: {incident.id} - {incident.title} "
            f"({incident.severity.value})"
        )

        return incident.id

    def update_incident(
        self,
        incident_id: str,
        updates: Dict[str, Any],
        author: str = "system",
    ) -> bool:
        """
        Atualiza incidente

        Args:
            incident_id: Incident ID
            updates: Dict com campos para atualizar
            author: Quem fez a atualização

        Returns:
            True se sucesso
        """
        incident = self.get_incident(incident_id)

        if not incident:
            logger.error(f"Incident not found: {incident_id}")
            return False

        # Apply updates
        for key, value in updates.items():
            if hasattr(incident, key):
                old_value = getattr(incident, key)
                setattr(incident, key, value)

                # Log status changes
                if key == "status":
                    logger.info(
                        f"Incident {incident_id} status: {old_value.value} → {value.value}"
                    )

                    # Set timestamps
                    if value == IncidentStatus.CONTAINED and not incident.contained_at:
                        incident.contained_at = datetime.now()

                    elif value == IncidentStatus.CLOSED and not incident.resolved_at:
                        incident.resolved_at = datetime.now()

        # Update backend
        if self.use_backend:
            try:
                self._update_incident_backend(incident)
            except Exception as e:
                logger.error(f"Backend update failed: {e}")

        return True

    def add_update(
        self,
        incident_id: str,
        content: str,
        author: str,
        is_public: bool = True,
    ) -> bool:
        """
        Adiciona update/nota ao incidente

        Args:
            incident_id: Incident ID
            content: Conteúdo da nota
            author: Autor
            is_public: Se público

        Returns:
            True se sucesso
        """
        incident = self.get_incident(incident_id)

        if not incident:
            return False

        import uuid

        update = IncidentUpdate(
            id=str(uuid.uuid4())[:8],
            author=author,
            timestamp=datetime.now(),
            content=content,
            is_public=is_public,
        )

        incident.updates.append(update)

        # Update backend
        if self.use_backend:
            try:
                self._update_incident_backend(incident)
            except Exception as e:
                logger.error(f"Backend update failed: {e}")

        return True

    def transition_status(
        self,
        incident_id: str,
        new_status: IncidentStatus,
        author: str = "system",
        notes: Optional[str] = None,
    ) -> bool:
        """
        Transiciona status do incidente (com validação de workflow)

        Args:
            incident_id: Incident ID
            new_status: Novo status
            author: Quem fez a transição
            notes: Notas da transição

        Returns:
            True se transição válida
        """
        incident = self.get_incident(incident_id)

        if not incident:
            return False

        # Validate transition
        valid_transitions = self._get_valid_transitions(incident.status)

        if new_status not in valid_transitions:
            logger.warning(
                f"Invalid status transition: {incident.status.value} → {new_status.value}"
            )
            return False

        # Update status
        old_status = incident.status
        incident.status = new_status

        # Add update note
        transition_note = f"Status changed: {old_status.value} → {new_status.value}"
        if notes:
            transition_note += f"\n{notes}"

        self.add_update(incident_id, transition_note, author, is_public=True)

        logger.info(f"Incident {incident_id}: {old_status.value} → {new_status.value}")

        return True

    def _get_valid_transitions(self, current_status: IncidentStatus) -> List[IncidentStatus]:
        """
        Retorna status válidos para transição

        Args:
            current_status: Status atual

        Returns:
            Lista de status válidos
        """
        transitions = {
            IncidentStatus.NEW: [
                IncidentStatus.TRIAGED,
                IncidentStatus.FALSE_POSITIVE,
                IncidentStatus.CLOSED,
            ],
            IncidentStatus.TRIAGED: [
                IncidentStatus.INVESTIGATING,
                IncidentStatus.FALSE_POSITIVE,
            ],
            IncidentStatus.INVESTIGATING: [
                IncidentStatus.CONTAINED,
                IncidentStatus.FALSE_POSITIVE,
            ],
            IncidentStatus.CONTAINED: [
                IncidentStatus.ERADICATED,
            ],
            IncidentStatus.ERADICATED: [
                IncidentStatus.RECOVERING,
            ],
            IncidentStatus.RECOVERING: [
                IncidentStatus.CLOSED,
            ],
            IncidentStatus.FALSE_POSITIVE: [
                IncidentStatus.CLOSED,
            ],
            IncidentStatus.CLOSED: [],
        }

        return transitions.get(current_status, [])

    def get_incident(self, incident_id: str) -> Optional[Incident]:
        """
        Retorna incidente por ID

        Args:
            incident_id: Incident ID

        Returns:
            Incident ou None
        """
        # Check cache
        if incident_id in self.incidents:
            return self.incidents[incident_id]

        # Try backend
        if self.use_backend:
            try:
                return self._get_incident_backend(incident_id)
            except Exception as e:
                logger.error(f"Backend retrieval failed: {e}")

        return None

    def list_incidents(
        self,
        status: Optional[IncidentStatus] = None,
        severity: Optional[IncidentSeverity] = None,
        category: Optional[IncidentCategory] = None,
        assigned_to: Optional[str] = None,
        limit: int = 100,
    ) -> List[Incident]:
        """
        Lista incidentes com filtros

        Args:
            status: Filter by status
            severity: Filter by severity
            category: Filter by category
            assigned_to: Filter by assignee
            limit: Max incidents

        Returns:
            List of Incident
        """
        incidents = list(self.incidents.values())

        if status:
            incidents = [i for i in incidents if i.status == status]

        if severity:
            incidents = [i for i in incidents if i.severity == severity]

        if category:
            incidents = [i for i in incidents if i.category == category]

        if assigned_to:
            incidents = [i for i in incidents if i.assigned_to == assigned_to]

        # Sort by severity (mais grave primeiro) e timestamp
        severity_order = {
            IncidentSeverity.SEV0_CRITICAL: 0,
            IncidentSeverity.SEV1_HIGH: 1,
            IncidentSeverity.SEV2_MEDIUM: 2,
            IncidentSeverity.SEV3_LOW: 3,
            IncidentSeverity.SEV4_INFO: 4,
        }

        incidents = sorted(
            incidents,
            key=lambda i: (severity_order[i.severity], i.reported_at),
            reverse=False,
        )

        return incidents[:limit]

    def check_sla_breach(self, incident: Incident) -> Dict[str, Any]:
        """
        Verifica se incidente está em breach de SLA

        Args:
            incident: Incident object

        Returns:
            Dict com status de SLA
        """
        now = datetime.now()
        breaches = {}

        # Check triage SLA
        if incident.status == IncidentStatus.NEW:
            sla_minutes = self.sla_triage.get(incident.severity, 60)
            elapsed = (now - incident.reported_at).total_seconds() / 60

            breaches["triage"] = {
                "sla_minutes": sla_minutes,
                "elapsed_minutes": elapsed,
                "is_breached": elapsed > sla_minutes,
                "time_remaining": sla_minutes - elapsed,
            }

        # Check containment SLA
        if incident.status in [IncidentStatus.TRIAGED, IncidentStatus.INVESTIGATING]:
            if incident.severity in self.sla_containment:
                sla_minutes = self.sla_containment[incident.severity]
                elapsed = (now - incident.reported_at).total_seconds() / 60

                breaches["containment"] = {
                    "sla_minutes": sla_minutes,
                    "elapsed_minutes": elapsed,
                    "is_breached": elapsed > sla_minutes,
                    "time_remaining": sla_minutes - elapsed,
                }

        return breaches

    def get_metrics(
        self,
        time_period_days: int = 30,
    ) -> Dict[str, Any]:
        """
        Retorna métricas de incidentes

        Args:
            time_period_days: Período para métricas

        Returns:
            Dict com métricas
        """
        cutoff = datetime.now() - timedelta(days=time_period_days)

        recent_incidents = [
            i for i in self.incidents.values()
            if i.reported_at >= cutoff
        ]

        # Count by severity
        by_severity = {}
        for sev in IncidentSeverity:
            by_severity[sev.value] = len([i for i in recent_incidents if i.severity == sev])

        # Count by status
        by_status = {}
        for status in IncidentStatus:
            by_status[status.value] = len([i for i in recent_incidents if i.status == status])

        # MTTD (Mean Time To Detect)
        detection_times = [
            (i.discovered_at - i.first_activity_at).total_seconds() / 3600
            for i in recent_incidents
            if i.first_activity_at and i.discovered_at
        ]
        mttd_hours = sum(detection_times) / len(detection_times) if detection_times else 0

        # MTTR (Mean Time To Resolve)
        resolution_times = [
            (i.resolved_at - i.reported_at).total_seconds() / 3600
            for i in recent_incidents
            if i.resolved_at
        ]
        mttr_hours = sum(resolution_times) / len(resolution_times) if resolution_times else 0

        return {
            "total_incidents": len(recent_incidents),
            "by_severity": by_severity,
            "by_status": by_status,
            "mttd_hours": mttd_hours,
            "mttr_hours": mttr_hours,
            "time_period_days": time_period_days,
        }

    # Backend integration methods

    def _create_incident_backend(self, incident: Incident) -> bool:
        """Cria incidente no backend"""
        import httpx

        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.post(
                    f"{self.backend_url}/api/incidents",
                    json={
                        "id": incident.id,
                        "title": incident.title,
                        "description": incident.description,
                        "severity": incident.severity.value,
                        "status": incident.status.value,
                        "category": incident.category.value,
                        "discovered_at": incident.discovered_at.isoformat(),
                        "created_by": incident.created_by,
                    }
                )
                response.raise_for_status()
                return True

        except Exception as e:
            logger.error(f"Backend incident creation failed: {e}")
            raise

    def _update_incident_backend(self, incident: Incident) -> bool:
        """Atualiza incidente no backend"""
        import httpx

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.put(
                    f"{self.backend_url}/api/incidents/{incident.id}",
                    json={
                        "status": incident.status.value,
                        "assigned_to": incident.assigned_to,
                        "contained_at": incident.contained_at.isoformat() if incident.contained_at else None,
                        "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
                    }
                )
                response.raise_for_status()
                return True

        except Exception as e:
            logger.error(f"Backend update failed: {e}")
            return False

    def _get_incident_backend(self, incident_id: str) -> Optional[Incident]:
        """Busca incidente no backend"""
        import httpx

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{self.backend_url}/api/incidents/{incident_id}")

                if response.status_code == 404:
                    return None

                response.raise_for_status()

                # TODO: Parse response to Incident
                return None  # Placeholder

        except Exception as e:
            logger.error(f"Backend retrieval failed: {e}")
            return None
