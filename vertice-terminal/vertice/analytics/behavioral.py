"""
🧠 Behavioral Analytics - Detecção de anomalias comportamentais

Integra com backend behavioral_analysis_service para análise distribuída.

Detecta anomalias em:
- Login patterns (horários, geolocação)
- Network traffic volume
- Process execution patterns
- File access patterns
- Lateral movement
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from enum import Enum
import statistics
import logging

logger = logging.getLogger(__name__)


class AnomalyType(Enum):
    """Tipo de anomalia"""
    LOGIN_TIME = "login_time"  # Login fora do horário usual
    LOGIN_LOCATION = "login_location"  # Login de localização incomum
    NETWORK_VOLUME = "network_volume"  # Volume de tráfego anormal
    PROCESS_EXECUTION = "process_execution"  # Processo incomum
    FILE_ACCESS = "file_access"  # Acesso a arquivos incomuns
    LATERAL_MOVEMENT = "lateral_movement"  # Movimento lateral
    DATA_EXFILTRATION = "data_exfiltration"  # Possível exfiltração
    PRIVILEGE_ESCALATION = "privilege_escalation"  # Escalação de privilégios


@dataclass
class Baseline:
    """
    Baseline comportamental de um entity (user, endpoint, etc)
    """
    entity_id: str
    entity_type: str  # user, endpoint, service

    # Temporal patterns
    typical_login_hours: List[int] = field(default_factory=list)  # 0-23
    typical_days: List[int] = field(default_factory=list)  # 0-6 (Mon-Sun)

    # Location patterns
    typical_locations: Set[str] = field(default_factory=set)  # IPs, countries
    typical_geolocations: Set[str] = field(default_factory=set)  # Cities

    # Network patterns
    avg_network_bytes_in: float = 0.0
    avg_network_bytes_out: float = 0.0
    stddev_network_in: float = 0.0
    stddev_network_out: float = 0.0

    # Process patterns
    typical_processes: Set[str] = field(default_factory=set)
    typical_parent_processes: Dict[str, Set[str]] = field(default_factory=dict)

    # File access patterns
    typical_files_accessed: Set[str] = field(default_factory=set)
    typical_file_extensions: Set[str] = field(default_factory=set)

    # Behavioral metadata
    sample_count: int = 0
    last_updated: datetime = field(default_factory=datetime.now)
    confidence: float = 0.0  # 0.0 to 1.0


@dataclass
class Anomaly:
    """
    Anomalia comportamental detectada
    """
    id: str
    entity_id: str
    entity_type: str
    anomaly_type: AnomalyType
    timestamp: datetime

    # Anomaly details
    description: str
    severity: str  # low, medium, high, critical

    # Statistical deviation
    deviation_score: float  # Quantos desvios-padrão da baseline
    confidence: float  # 0.0 to 1.0

    # Context
    observed_value: Any
    baseline_value: Any
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Investigation
    is_investigated: bool = False
    is_false_positive: bool = False


class BehavioralAnalytics:
    """
    Engine de análise comportamental

    Features:
    - Baseline learning de comportamento normal
    - Anomaly detection com desvio estatístico
    - Pattern recognition
    - Backend integration para scale
    """

    def __init__(
        self,
        backend_url: Optional[str] = None,
        use_backend: bool = True,
        learning_period_days: int = 30,
        anomaly_threshold: float = 3.0,  # Z-score threshold
    ):
        """
        Args:
            backend_url: URL do behavioral_analysis_service
            use_backend: Se True, usa backend para análise
            learning_period_days: Período de aprendizado de baseline
            anomaly_threshold: Threshold de desvio-padrão (Z-score)
        """
        self.backend_url = backend_url or "http://localhost:8005"
        self.use_backend = use_backend
        self.learning_period_days = learning_period_days
        self.anomaly_threshold = anomaly_threshold

        # Baselines em cache
        self.baselines: Dict[str, Baseline] = {}

        # Anomalias detectadas
        self.anomalies: List[Anomaly] = []

    def learn_baseline(
        self,
        entity_id: str,
        entity_type: str,
        historical_events: List[Dict[str, Any]],
    ) -> Baseline:
        """
        Aprende baseline de comportamento normal

        Args:
            entity_id: ID do entity (user, endpoint)
            entity_type: Tipo do entity
            historical_events: Lista de eventos históricos

        Returns:
            Baseline aprendida
        """
        if self.use_backend:
            try:
                return self._learn_baseline_backend(entity_id, entity_type, historical_events)
            except Exception as e:
                logger.warning(f"Backend learning failed, falling back to local: {e}")

        # Fallback: learning local
        return self._learn_baseline_local(entity_id, entity_type, historical_events)

    def _learn_baseline_local(
        self,
        entity_id: str,
        entity_type: str,
        events: List[Dict[str, Any]],
    ) -> Baseline:
        """
        Aprende baseline localmente (estatística básica)

        Args:
            entity_id: Entity ID
            entity_type: Entity type
            events: Historical events

        Returns:
            Baseline object
        """
        baseline = Baseline(entity_id=entity_id, entity_type=entity_type)

        # Extract temporal patterns
        login_hours = []
        login_days = []
        locations = set()

        # Network statistics
        network_bytes_in = []
        network_bytes_out = []

        # Process patterns
        processes = set()
        parent_child = {}

        # File patterns
        files = set()
        extensions = set()

        for event in events:
            event_type = event.get("type", "")
            timestamp = event.get("timestamp")

            if timestamp:
                dt = datetime.fromisoformat(timestamp) if isinstance(timestamp, str) else timestamp
                login_hours.append(dt.hour)
                login_days.append(dt.weekday())

            # Login events
            if event_type == "login":
                location = event.get("source_ip") or event.get("location")
                if location:
                    locations.add(location)

            # Network events
            elif event_type == "network":
                bytes_in = event.get("bytes_in", 0)
                bytes_out = event.get("bytes_out", 0)
                network_bytes_in.append(bytes_in)
                network_bytes_out.append(bytes_out)

            # Process events
            elif event_type == "process":
                proc_name = event.get("process_name")
                parent_name = event.get("parent_process")

                if proc_name:
                    processes.add(proc_name)

                if proc_name and parent_name:
                    if parent_name not in parent_child:
                        parent_child[parent_name] = set()
                    parent_child[parent_name].add(proc_name)

            # File events
            elif event_type == "file":
                file_path = event.get("file_path")
                if file_path:
                    files.add(file_path)

                    # Extract extension
                    if "." in file_path:
                        ext = file_path.split(".")[-1]
                        extensions.add(ext)

        # Build baseline
        baseline.typical_login_hours = list(set(login_hours))
        baseline.typical_days = list(set(login_days))
        baseline.typical_locations = locations
        baseline.typical_processes = processes
        baseline.typical_parent_processes = parent_child
        baseline.typical_files_accessed = files
        baseline.typical_file_extensions = extensions

        # Network statistics
        if network_bytes_in:
            baseline.avg_network_bytes_in = statistics.mean(network_bytes_in)
            baseline.stddev_network_in = statistics.stdev(network_bytes_in) if len(network_bytes_in) > 1 else 0.0

        if network_bytes_out:
            baseline.avg_network_bytes_out = statistics.mean(network_bytes_out)
            baseline.stddev_network_out = statistics.stdev(network_bytes_out) if len(network_bytes_out) > 1 else 0.0

        baseline.sample_count = len(events)
        baseline.confidence = min(len(events) / 100.0, 1.0)  # Confiança aumenta com mais samples

        # Cache baseline
        self.baselines[entity_id] = baseline

        logger.info(f"Baseline learned for {entity_id}: {baseline.sample_count} events")

        return baseline

    def _learn_baseline_backend(
        self,
        entity_id: str,
        entity_type: str,
        events: List[Dict[str, Any]],
    ) -> Baseline:
        """
        Aprende baseline via backend (ML avançado)

        Args:
            entity_id: Entity ID
            entity_type: Entity type
            events: Historical events

        Returns:
            Baseline from backend
        """
        import httpx

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.backend_url}/api/behavioral/learn-baseline",
                    json={
                        "entity_id": entity_id,
                        "entity_type": entity_type,
                        "events": events,
                        "learning_period_days": self.learning_period_days,
                    }
                )
                response.raise_for_status()

                result = response.json()

                # Parse baseline from backend
                baseline = Baseline(
                    entity_id=entity_id,
                    entity_type=entity_type,
                    typical_login_hours=result.get("typical_login_hours", []),
                    typical_days=result.get("typical_days", []),
                    typical_locations=set(result.get("typical_locations", [])),
                    typical_processes=set(result.get("typical_processes", [])),
                    avg_network_bytes_in=result.get("avg_network_bytes_in", 0.0),
                    avg_network_bytes_out=result.get("avg_network_bytes_out", 0.0),
                    stddev_network_in=result.get("stddev_network_in", 0.0),
                    stddev_network_out=result.get("stddev_network_out", 0.0),
                    sample_count=result.get("sample_count", 0),
                    confidence=result.get("confidence", 0.0),
                )

                self.baselines[entity_id] = baseline

                return baseline

        except Exception as e:
            logger.error(f"Backend baseline learning failed: {e}")
            raise

    def detect_anomalies(
        self,
        entity_id: str,
        current_event: Dict[str, Any],
    ) -> List[Anomaly]:
        """
        Detecta anomalias em evento atual comparando com baseline

        Args:
            entity_id: Entity ID
            current_event: Evento atual para análise

        Returns:
            Lista de anomalias detectadas
        """
        baseline = self.baselines.get(entity_id)

        if not baseline:
            logger.warning(f"No baseline for entity {entity_id}, cannot detect anomalies")
            return []

        if self.use_backend:
            try:
                return self._detect_anomalies_backend(entity_id, current_event, baseline)
            except Exception as e:
                logger.warning(f"Backend detection failed, falling back to local: {e}")

        # Fallback: detection local
        return self._detect_anomalies_local(entity_id, current_event, baseline)

    def _detect_anomalies_local(
        self,
        entity_id: str,
        event: Dict[str, Any],
        baseline: Baseline,
    ) -> List[Anomaly]:
        """
        Detecta anomalias localmente (regras estatísticas)

        Args:
            entity_id: Entity ID
            event: Current event
            baseline: Baseline object

        Returns:
            List of Anomaly
        """
        anomalies = []
        event_type = event.get("type", "")
        timestamp = event.get("timestamp")

        if timestamp:
            dt = datetime.fromisoformat(timestamp) if isinstance(timestamp, str) else timestamp
        else:
            dt = datetime.now()

        # Check login time anomaly
        if event_type == "login":
            if baseline.typical_login_hours and dt.hour not in baseline.typical_login_hours:
                anomaly = Anomaly(
                    id=f"anom_{entity_id}_{dt.timestamp()}",
                    entity_id=entity_id,
                    entity_type=baseline.entity_type,
                    anomaly_type=AnomalyType.LOGIN_TIME,
                    timestamp=dt,
                    description=f"Login at unusual hour {dt.hour}:00",
                    severity="medium",
                    deviation_score=2.0,
                    confidence=baseline.confidence,
                    observed_value=dt.hour,
                    baseline_value=baseline.typical_login_hours,
                )
                anomalies.append(anomaly)

            # Check location
            location = event.get("source_ip") or event.get("location")
            if location and baseline.typical_locations and location not in baseline.typical_locations:
                anomaly = Anomaly(
                    id=f"anom_loc_{entity_id}_{dt.timestamp()}",
                    entity_id=entity_id,
                    entity_type=baseline.entity_type,
                    anomaly_type=AnomalyType.LOGIN_LOCATION,
                    timestamp=dt,
                    description=f"Login from unusual location: {location}",
                    severity="high",
                    deviation_score=3.0,
                    confidence=baseline.confidence,
                    observed_value=location,
                    baseline_value=list(baseline.typical_locations),
                )
                anomalies.append(anomaly)

        # Check network volume anomaly
        elif event_type == "network":
            bytes_out = event.get("bytes_out", 0)

            if baseline.stddev_network_out > 0:
                z_score = abs(bytes_out - baseline.avg_network_bytes_out) / baseline.stddev_network_out

                if z_score > self.anomaly_threshold:
                    anomaly = Anomaly(
                        id=f"anom_net_{entity_id}_{dt.timestamp()}",
                        entity_id=entity_id,
                        entity_type=baseline.entity_type,
                        anomaly_type=AnomalyType.NETWORK_VOLUME,
                        timestamp=dt,
                        description=f"Unusual network traffic volume: {bytes_out} bytes",
                        severity="high" if z_score > 5 else "medium",
                        deviation_score=z_score,
                        confidence=baseline.confidence,
                        observed_value=bytes_out,
                        baseline_value=baseline.avg_network_bytes_out,
                    )
                    anomalies.append(anomaly)

        # Check process anomaly
        elif event_type == "process":
            proc_name = event.get("process_name")

            if proc_name and baseline.typical_processes and proc_name not in baseline.typical_processes:
                anomaly = Anomaly(
                    id=f"anom_proc_{entity_id}_{dt.timestamp()}",
                    entity_id=entity_id,
                    entity_type=baseline.entity_type,
                    anomaly_type=AnomalyType.PROCESS_EXECUTION,
                    timestamp=dt,
                    description=f"Unusual process execution: {proc_name}",
                    severity="medium",
                    deviation_score=2.0,
                    confidence=baseline.confidence,
                    observed_value=proc_name,
                    baseline_value=list(baseline.typical_processes)[:10],
                )
                anomalies.append(anomaly)

        # Store anomalies
        self.anomalies.extend(anomalies)

        return anomalies

    def _detect_anomalies_backend(
        self,
        entity_id: str,
        event: Dict[str, Any],
        baseline: Baseline,
    ) -> List[Anomaly]:
        """
        Detecta anomalias via backend (ML models)

        Args:
            entity_id: Entity ID
            event: Current event
            baseline: Baseline

        Returns:
            List of Anomaly
        """
        import httpx

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    f"{self.backend_url}/api/behavioral/detect-anomalies",
                    json={
                        "entity_id": entity_id,
                        "event": event,
                        "threshold": self.anomaly_threshold,
                    }
                )
                response.raise_for_status()

                result = response.json()

                anomalies = []
                for anom_data in result.get("anomalies", []):
                    anomaly = Anomaly(
                        id=anom_data.get("id"),
                        entity_id=entity_id,
                        entity_type=baseline.entity_type,
                        anomaly_type=AnomalyType(anom_data.get("type")),
                        timestamp=datetime.fromisoformat(anom_data.get("timestamp")),
                        description=anom_data.get("description"),
                        severity=anom_data.get("severity"),
                        deviation_score=anom_data.get("deviation_score"),
                        confidence=anom_data.get("confidence"),
                        observed_value=anom_data.get("observed_value"),
                        baseline_value=anom_data.get("baseline_value"),
                    )
                    anomalies.append(anomaly)

                self.anomalies.extend(anomalies)

                return anomalies

        except Exception as e:
            logger.error(f"Backend anomaly detection failed: {e}")
            raise

    def get_anomalies(
        self,
        entity_id: Optional[str] = None,
        anomaly_type: Optional[AnomalyType] = None,
        severity: Optional[str] = None,
        limit: int = 100,
    ) -> List[Anomaly]:
        """
        Retorna anomalias filtradas

        Args:
            entity_id: Filter by entity
            anomaly_type: Filter by type
            severity: Filter by severity
            limit: Max anomalies

        Returns:
            List of Anomaly
        """
        anomalies = self.anomalies

        if entity_id:
            anomalies = [a for a in anomalies if a.entity_id == entity_id]

        if anomaly_type:
            anomalies = [a for a in anomalies if a.anomaly_type == anomaly_type]

        if severity:
            anomalies = [a for a in anomalies if a.severity == severity]

        # Sort by timestamp (most recent first)
        anomalies = sorted(anomalies, key=lambda a: a.timestamp, reverse=True)

        return anomalies[:limit]

    def get_baseline(self, entity_id: str) -> Optional[Baseline]:
        """
        Retorna baseline de entity

        Args:
            entity_id: Entity ID

        Returns:
            Baseline or None
        """
        return self.baselines.get(entity_id)
