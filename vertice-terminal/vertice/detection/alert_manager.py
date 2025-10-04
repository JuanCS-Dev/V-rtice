"""
🚨 Alert Manager - Gerenciamento e correlação de alertas

Integra com backend alert_service para persistência e correlação distribuída.

Features:
- Deduplicação de alertas
- Correlação por IOCs/tactics
- Alert lifecycle (NEW → INVESTIGATING → RESOLVED)
- Integration com SOAR platforms
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import logging

logger = logging.getLogger(__name__)


class AlertStatus(Enum):
    """Status do alerta"""
    NEW = "new"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"
    ESCALATED = "escalated"


class AlertPriority(Enum):
    """Prioridade do alerta (derivada de severity + context)"""
    P0_CRITICAL = "p0_critical"  # Incidente ativo
    P1_HIGH = "p1_high"  # Requer ação imediata
    P2_MEDIUM = "p2_medium"  # Investigação necessária
    P3_LOW = "p3_low"  # Informativo
    P4_INFO = "p4_info"  # FYI


@dataclass
class Alert:
    """
    Alerta de segurança
    """
    id: str
    title: str
    description: str
    severity: str  # info, low, medium, high, critical
    status: AlertStatus
    priority: AlertPriority = AlertPriority.P2_MEDIUM

    # Source
    source: str  # Endpoint ID, log source, etc
    detection_ids: List[str] = field(default_factory=list)  # Linked detections

    # Timing
    first_seen: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    occurrence_count: int = 1

    # IOCs e contexto
    iocs: List[str] = field(default_factory=list)
    affected_assets: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    # Investigation
    assigned_to: Optional[str] = None
    notes: List[str] = field(default_factory=list)

    # SOAR integration
    soar_incident_id: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AlertCorrelation:
    """
    Correlação entre alertas
    """
    alert_ids: List[str]
    correlation_type: str  # same_ioc, same_asset, temporal, mitre_tactic
    confidence: float  # 0.0 to 1.0
    description: str
    created_at: datetime = field(default_factory=datetime.now)


class AlertManager:
    """
    Gerenciador de alertas com deduplicação e correlação

    Features:
    - Dedup por hash de (title, source, IOCs)
    - Time-based aggregation
    - IOC correlation
    - Backend persistence
    - SOAR integration
    """

    def __init__(
        self,
        backend_url: Optional[str] = None,
        use_backend: bool = True,
        dedup_window: int = 3600,  # 1 hora
    ):
        """
        Args:
            backend_url: URL do alert_service
            use_backend: Se True, persiste no backend
            dedup_window: Janela de deduplicação em segundos
        """
        self.backend_url = backend_url or "http://localhost:8003"
        self.use_backend = use_backend
        self.dedup_window = dedup_window

        # Alertas em memória (cache)
        self.alerts: Dict[str, Alert] = {}

        # Correlações detectadas
        self.correlations: List[AlertCorrelation] = []

        # Dedup hash index
        self.dedup_index: Dict[str, str] = {}  # hash -> alert_id

    def create_alert(self, alert: Alert) -> str:
        """
        Cria alerta com deduplicação automática

        Args:
            alert: Alert object

        Returns:
            Alert ID (existente se dedup)
        """
        # Calcula hash para dedup
        dedup_hash = self._calculate_dedup_hash(alert)

        # Check dedup window
        existing_alert_id = self.dedup_index.get(dedup_hash)

        if existing_alert_id and existing_alert_id in self.alerts:
            existing_alert = self.alerts[existing_alert_id]

            # Verifica se está dentro da janela
            time_diff = (datetime.now() - existing_alert.last_seen).total_seconds()

            if time_diff <= self.dedup_window:
                # Dedup: atualiza alerta existente
                existing_alert.occurrence_count += 1
                existing_alert.last_seen = datetime.now()

                # Merge IOCs e detection IDs
                existing_alert.iocs = list(set(existing_alert.iocs + alert.iocs))
                existing_alert.detection_ids = list(
                    set(existing_alert.detection_ids + alert.detection_ids)
                )

                logger.info(
                    f"Alert deduplicated: {existing_alert.id} "
                    f"(count: {existing_alert.occurrence_count})"
                )

                # Update backend
                if self.use_backend:
                    self._update_alert_backend(existing_alert)

                return existing_alert.id

        # Novo alerta
        self.alerts[alert.id] = alert
        self.dedup_index[dedup_hash] = alert.id

        # Calcula prioridade
        alert.priority = self._calculate_priority(alert)

        logger.info(f"New alert created: {alert.id} ({alert.priority.value})")

        # Persiste no backend
        if self.use_backend:
            self._create_alert_backend(alert)

        # Auto-correlation
        self._check_correlations(alert)

        return alert.id

    def _calculate_dedup_hash(self, alert: Alert) -> str:
        """
        Calcula hash para deduplicação

        Args:
            alert: Alert object

        Returns:
            Hash string
        """
        # Combina: title + source + IOCs sorted
        dedup_key = f"{alert.title}:{alert.source}:{','.join(sorted(alert.iocs))}"

        return hashlib.sha256(dedup_key.encode()).hexdigest()

    def _calculate_priority(self, alert: Alert) -> AlertPriority:
        """
        Calcula prioridade baseado em severity + contexto

        Args:
            alert: Alert object

        Returns:
            AlertPriority
        """
        # Mapa base de severity
        severity_map = {
            "critical": AlertPriority.P0_CRITICAL,
            "high": AlertPriority.P1_HIGH,
            "medium": AlertPriority.P2_MEDIUM,
            "low": AlertPriority.P3_LOW,
            "info": AlertPriority.P4_INFO,
        }

        base_priority = severity_map.get(alert.severity, AlertPriority.P2_MEDIUM)

        # Escalate se múltiplos assets afetados
        if len(alert.affected_assets) >= 5:
            if base_priority == AlertPriority.P1_HIGH:
                return AlertPriority.P0_CRITICAL
            elif base_priority == AlertPriority.P2_MEDIUM:
                return AlertPriority.P1_HIGH

        # Escalate se tem IOCs conhecidos
        if len(alert.iocs) >= 3:
            if base_priority == AlertPriority.P2_MEDIUM:
                return AlertPriority.P1_HIGH

        return base_priority

    def _check_correlations(self, new_alert: Alert) -> None:
        """
        Verifica correlações com alertas existentes

        Args:
            new_alert: Novo alerta
        """
        # Correlação por IOCs
        for existing_alert in self.alerts.values():
            if existing_alert.id == new_alert.id:
                continue

            # IOC overlap
            common_iocs = set(new_alert.iocs) & set(existing_alert.iocs)
            if common_iocs:
                correlation = AlertCorrelation(
                    alert_ids=[new_alert.id, existing_alert.id],
                    correlation_type="same_ioc",
                    confidence=min(len(common_iocs) / 3.0, 1.0),
                    description=f"Shared IOCs: {', '.join(common_iocs)}",
                )
                self.correlations.append(correlation)

                logger.info(
                    f"Alert correlation detected: {new_alert.id} <-> {existing_alert.id}"
                )

            # Same asset
            common_assets = set(new_alert.affected_assets) & set(
                existing_alert.affected_assets
            )
            if common_assets:
                correlation = AlertCorrelation(
                    alert_ids=[new_alert.id, existing_alert.id],
                    correlation_type="same_asset",
                    confidence=0.7,
                    description=f"Same affected assets: {', '.join(common_assets)}",
                )
                self.correlations.append(correlation)

    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """
        Retorna alerta por ID

        Args:
            alert_id: Alert ID

        Returns:
            Alert ou None
        """
        # Try cache first
        if alert_id in self.alerts:
            return self.alerts[alert_id]

        # Try backend
        if self.use_backend:
            return self._get_alert_backend(alert_id)

        return None

    def update_alert(
        self,
        alert_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Atualiza alerta

        Args:
            alert_id: Alert ID
            updates: Dict com campos para atualizar

        Returns:
            True se sucesso
        """
        alert = self.get_alert(alert_id)

        if not alert:
            return False

        # Update fields
        for key, value in updates.items():
            if hasattr(alert, key):
                setattr(alert, key, value)

        # Update backend
        if self.use_backend:
            return self._update_alert_backend(alert)

        return True

    def list_alerts(
        self,
        status: Optional[AlertStatus] = None,
        priority: Optional[AlertPriority] = None,
        source: Optional[str] = None,
        limit: int = 100,
    ) -> List[Alert]:
        """
        Lista alertas com filtros

        Args:
            status: Filtrar por status
            priority: Filtrar por prioridade
            source: Filtrar por source
            limit: Máximo de alertas

        Returns:
            Lista de Alert
        """
        alerts = list(self.alerts.values())

        if status:
            alerts = [a for a in alerts if a.status == status]

        if priority:
            alerts = [a for a in alerts if a.priority == priority]

        if source:
            alerts = [a for a in alerts if a.source == source]

        # Sort por prioridade e timestamp
        alerts = sorted(
            alerts,
            key=lambda a: (a.priority.value, a.last_seen),
            reverse=True
        )

        return alerts[:limit]

    def get_correlations(self, alert_id: str) -> List[AlertCorrelation]:
        """
        Retorna correlações de um alerta

        Args:
            alert_id: Alert ID

        Returns:
            Lista de AlertCorrelation
        """
        return [
            corr for corr in self.correlations
            if alert_id in corr.alert_ids
        ]

    def escalate_to_soar(
        self,
        alert_id: str,
        soar_connector: Any,
    ) -> Optional[str]:
        """
        Escalate alerta para SOAR platform

        Args:
            alert_id: Alert ID
            soar_connector: SOARConnector instance

        Returns:
            Incident ID no SOAR ou None
        """
        alert = self.get_alert(alert_id)

        if not alert:
            return None

        # Cria incident no SOAR
        from ..soar.base import Incident, IncidentSeverity, IncidentStatus, Artifact

        # Map severity
        severity_map = {
            "critical": IncidentSeverity.CRITICAL,
            "high": IncidentSeverity.HIGH,
            "medium": IncidentSeverity.MEDIUM,
            "low": IncidentSeverity.LOW,
            "info": IncidentSeverity.LOW,
        }

        incident = Incident(
            title=alert.title,
            description=alert.description,
            severity=severity_map.get(alert.severity, IncidentSeverity.MEDIUM),
            status=IncidentStatus.NEW,
            tags=alert.tags,
        )

        # Add IOCs as artifacts
        for ioc in alert.iocs:
            # Detect IOC type
            ioc_type = self._detect_ioc_type(ioc)

            artifact = Artifact(
                type=ioc_type,
                value=ioc,
                description=f"IOC from alert {alert.id}",
            )
            incident.artifacts.append(artifact)

        # Create incident
        import asyncio
        incident_id = asyncio.run(soar_connector.create_incident(incident))

        # Update alert
        alert.soar_incident_id = incident_id
        alert.status = AlertStatus.ESCALATED

        logger.info(f"Alert {alert_id} escalated to SOAR: {incident_id}")

        return incident_id

    def _detect_ioc_type(self, ioc: str) -> str:
        """
        Detecta tipo de IOC

        Args:
            ioc: IOC string

        Returns:
            Tipo (ip, domain, hash, etc)
        """
        import re

        # IP
        if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ioc):
            return "ip"

        # Hash (MD5, SHA1, SHA256)
        if re.match(r"^[a-fA-F0-9]{32}$", ioc):
            return "md5"
        if re.match(r"^[a-fA-F0-9]{40}$", ioc):
            return "sha1"
        if re.match(r"^[a-fA-F0-9]{64}$", ioc):
            return "sha256"

        # Domain
        if "." in ioc and not "/" in ioc:
            return "domain"

        # URL
        if ioc.startswith("http"):
            return "url"

        return "other"

    # Backend integration methods

    def _create_alert_backend(self, alert: Alert) -> bool:
        """Persiste alerta no backend"""
        import httpx

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    f"{self.backend_url}/api/alerts",
                    json={
                        "id": alert.id,
                        "title": alert.title,
                        "description": alert.description,
                        "severity": alert.severity,
                        "status": alert.status.value,
                        "priority": alert.priority.value,
                        "source": alert.source,
                        "iocs": alert.iocs,
                        "tags": alert.tags,
                        "metadata": alert.metadata,
                    }
                )
                response.raise_for_status()
                return True

        except Exception as e:
            logger.error(f"Failed to create alert in backend: {e}")
            return False

    def _update_alert_backend(self, alert: Alert) -> bool:
        """Atualiza alerta no backend"""
        import httpx

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.put(
                    f"{self.backend_url}/api/alerts/{alert.id}",
                    json={
                        "status": alert.status.value,
                        "occurrence_count": alert.occurrence_count,
                        "last_seen": alert.last_seen.isoformat(),
                        "iocs": alert.iocs,
                        "assigned_to": alert.assigned_to,
                        "notes": alert.notes,
                    }
                )
                response.raise_for_status()
                return True

        except Exception as e:
            logger.error(f"Failed to update alert in backend: {e}")
            return False

    def _get_alert_backend(self, alert_id: str) -> Optional[Alert]:
        """Busca alerta no backend"""
        import httpx

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{self.backend_url}/api/alerts/{alert_id}")

                if response.status_code == 404:
                    return None

                response.raise_for_status()
                data = response.json()

                # Parse response to Alert
                # TODO: Implement full parsing

                return None  # Placeholder

        except Exception as e:
            logger.error(f"Failed to get alert from backend: {e}")
            return None
