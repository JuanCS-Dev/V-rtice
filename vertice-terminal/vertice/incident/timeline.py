"""
⏱️ Timeline Builder - Reconstrução de timeline de ataques

Reconstrói timeline de eventos para análise de incidentes.

Features:
- Event correlation
- Attack chain visualization
- MITRE ATT&CK mapping
- Kill chain phases
- Automated event ingestion
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Tipo de evento"""
    NETWORK = "network"
    PROCESS = "process"
    FILE = "file"
    REGISTRY = "registry"
    AUTHENTICATION = "authentication"
    DETECTION = "detection"
    ALERT = "alert"
    USER_ACTION = "user_action"
    SYSTEM_EVENT = "system_event"


class KillChainPhase(Enum):
    """Cyber Kill Chain phases (Lockheed Martin)"""
    RECONNAISSANCE = "reconnaissance"
    WEAPONIZATION = "weaponization"
    DELIVERY = "delivery"
    EXPLOITATION = "exploitation"
    INSTALLATION = "installation"
    COMMAND_AND_CONTROL = "command_and_control"
    ACTIONS_ON_OBJECTIVES = "actions_on_objectives"


@dataclass
class TimelineEvent:
    """
    Evento individual na timeline
    """
    id: str
    timestamp: datetime
    event_type: EventType
    source: str  # Endpoint, log source, etc

    # Event details
    title: str
    description: str
    raw_data: Dict[str, Any] = field(default_factory=dict)

    # Correlation
    correlated_events: List[str] = field(default_factory=list)
    parent_event_id: Optional[str] = None
    child_events: List[str] = field(default_factory=list)

    # Attribution
    kill_chain_phase: Optional[KillChainPhase] = None
    mitre_techniques: List[str] = field(default_factory=list)

    # Enrichment
    iocs: List[str] = field(default_factory=list)
    threat_actors: List[str] = field(default_factory=list)

    # Severity
    severity: str = "info"  # info, low, medium, high, critical

    # Metadata
    tags: List[str] = field(default_factory=list)
    confidence: float = 1.0  # 0.0 to 1.0


@dataclass
class AttackChain:
    """
    Cadeia de ataque reconstruída
    """
    id: str
    name: str
    description: str

    # Events in order
    events: List[TimelineEvent] = field(default_factory=list)

    # Attack metadata
    initial_access_time: Optional[datetime] = None
    final_action_time: Optional[datetime] = None
    duration_minutes: float = 0.0

    # Kill chain coverage
    kill_chain_phases: List[KillChainPhase] = field(default_factory=list)

    # MITRE ATT&CK
    mitre_tactics: List[str] = field(default_factory=list)
    mitre_techniques: List[str] = field(default_factory=list)

    # Attribution
    suspected_threat_actor: Optional[str] = None
    confidence: float = 0.5


class TimelineBuilder:
    """
    Timeline Reconstruction Engine

    Features:
    - Event ingestion from multiple sources
    - Temporal correlation
    - Attack chain reconstruction
    - Kill chain mapping
    - MITRE ATT&CK mapping
    - Backend integration
    """

    def __init__(
        self,
        backend_url: Optional[str] = None,
        use_backend: bool = True,
        # Correlation settings
        correlation_window_seconds: int = 300,  # 5 minutes
    ):
        """
        Args:
            backend_url: URL do timeline_service
            use_backend: Se True, usa backend
            correlation_window_seconds: Window for event correlation
        """
        self.backend_url = backend_url or "http://localhost:8012"
        self.use_backend = use_backend
        self.correlation_window = correlation_window_seconds

        # Timelines storage
        self.timelines: Dict[str, List[TimelineEvent]] = {}

        # Attack chains
        self.attack_chains: List[AttackChain] = []

    def create_timeline(self, timeline_id: str) -> bool:
        """
        Cria nova timeline

        Args:
            timeline_id: Timeline ID

        Returns:
            True se criado
        """
        if timeline_id in self.timelines:
            logger.warning(f"Timeline already exists: {timeline_id}")
            return False

        self.timelines[timeline_id] = []

        logger.info(f"Timeline created: {timeline_id}")

        return True

    def add_event(
        self,
        timeline_id: str,
        event: TimelineEvent,
    ) -> bool:
        """
        Adiciona evento à timeline

        Args:
            timeline_id: Timeline ID
            event: TimelineEvent

        Returns:
            True se adicionado
        """
        if timeline_id not in self.timelines:
            self.create_timeline(timeline_id)

        if not event.id:
            import uuid
            event.id = f"evt-{uuid.uuid4().hex[:12]}"

        # Insert in chronological order
        timeline = self.timelines[timeline_id]

        # Binary search for insertion point
        insert_idx = 0
        for idx, existing_event in enumerate(timeline):
            if event.timestamp < existing_event.timestamp:
                insert_idx = idx
                break
            insert_idx = idx + 1

        timeline.insert(insert_idx, event)

        logger.debug(f"Event added to timeline {timeline_id}: {event.title}")

        # Auto-correlate with nearby events
        self._correlate_event(timeline_id, event)

        return True

    def ingest_events(
        self,
        timeline_id: str,
        events: List[Dict[str, Any]],
        source_type: str = "generic",
    ) -> int:
        """
        Ingere eventos de fonte externa

        Args:
            timeline_id: Timeline ID
            events: Lista de eventos (dicts)
            source_type: Tipo de fonte (sysmon, edr, firewall, etc)

        Returns:
            Número de eventos ingeridos
        """
        count = 0

        for event_data in events:
            try:
                # Parse event
                event = self._parse_event(event_data, source_type)

                # Add to timeline
                self.add_event(timeline_id, event)

                count += 1

            except Exception as e:
                logger.error(f"Failed to ingest event: {e}")

        logger.info(f"Ingested {count} events to timeline {timeline_id}")

        return count

    def _parse_event(
        self,
        event_data: Dict[str, Any],
        source_type: str,
    ) -> TimelineEvent:
        """
        Parse event data para TimelineEvent

        Args:
            event_data: Raw event data
            source_type: Source type

        Returns:
            TimelineEvent
        """
        # Generic parsing
        timestamp_str = event_data.get("timestamp") or event_data.get("@timestamp")

        if timestamp_str:
            if isinstance(timestamp_str, str):
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            else:
                timestamp = timestamp_str
        else:
            timestamp = datetime.now()

        # Detect event type
        event_type = self._detect_event_type(event_data, source_type)

        # Build title and description
        title = event_data.get("event_name") or event_data.get("title") or "Event"
        description = event_data.get("description") or event_data.get("message") or ""

        source = event_data.get("source") or event_data.get("hostname") or "unknown"

        event = TimelineEvent(
            id="",  # Will be set in add_event
            timestamp=timestamp,
            event_type=event_type,
            source=source,
            title=title,
            description=description,
            raw_data=event_data,
        )

        # Extract IOCs
        event.iocs = self._extract_iocs(event_data)

        # Map to MITRE ATT&CK
        event.mitre_techniques = self._map_mitre_techniques(event_data, source_type)

        # Map to Kill Chain
        event.kill_chain_phase = self._map_kill_chain(event.mitre_techniques)

        return event

    def _detect_event_type(
        self,
        event_data: Dict[str, Any],
        source_type: str,
    ) -> EventType:
        """Detecta tipo de evento"""

        # Check event type field
        if "event_type" in event_data:
            try:
                return EventType(event_data["event_type"])
            except ValueError:
                pass

        # Heuristics based on fields
        if "process_name" in event_data or "process_id" in event_data:
            return EventType.PROCESS

        if "file_path" in event_data or "file_name" in event_data:
            return EventType.FILE

        if "source_ip" in event_data or "dest_ip" in event_data:
            return EventType.NETWORK

        if "user" in event_data or "logon_type" in event_data:
            return EventType.AUTHENTICATION

        if "registry_path" in event_data:
            return EventType.REGISTRY

        return EventType.SYSTEM_EVENT

    def _extract_iocs(self, event_data: Dict[str, Any]) -> List[str]:
        """Extrai IOCs de event data"""
        import re

        iocs = []

        # Convert to string for regex
        event_str = str(event_data)

        # IP addresses
        ip_pattern = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
        iocs.extend(re.findall(ip_pattern, event_str))

        # Domains (simple pattern)
        domain_pattern = r'\b[a-zA-Z0-9-]+\.[a-zA-Z]{2,}\b'
        iocs.extend(re.findall(domain_pattern, event_str))

        # Hashes (MD5, SHA1, SHA256)
        hash_patterns = [
            r'\b[a-fA-F0-9]{32}\b',  # MD5
            r'\b[a-fA-F0-9]{40}\b',  # SHA1
            r'\b[a-fA-F0-9]{64}\b',  # SHA256
        ]

        for pattern in hash_patterns:
            iocs.extend(re.findall(pattern, event_str))

        return list(set(iocs))[:10]  # Limit and dedupe

    def _map_mitre_techniques(
        self,
        event_data: Dict[str, Any],
        source_type: str,
    ) -> List[str]:
        """Mapeia evento para MITRE ATT&CK techniques"""

        techniques = []

        # Check if already tagged
        if "mitre_techniques" in event_data:
            return event_data["mitre_techniques"]

        # Heuristic mapping based on event characteristics
        # TODO: Implement comprehensive mapping

        return techniques

    def _map_kill_chain(self, mitre_techniques: List[str]) -> Optional[KillChainPhase]:
        """Mapeia MITRE techniques para Kill Chain phase"""

        # Simplified mapping
        # TODO: Implement full MITRE -> Kill Chain mapping

        if not mitre_techniques:
            return None

        # Example mappings
        recon_techniques = ["T1595", "T1592", "T1589"]
        delivery_techniques = ["T1566", "T1091"]
        exploitation_techniques = ["T1203", "T1210"]
        c2_techniques = ["T1071", "T1095", "T1105"]

        for technique in mitre_techniques:
            if technique in recon_techniques:
                return KillChainPhase.RECONNAISSANCE
            elif technique in delivery_techniques:
                return KillChainPhase.DELIVERY
            elif technique in exploitation_techniques:
                return KillChainPhase.EXPLOITATION
            elif technique in c2_techniques:
                return KillChainPhase.COMMAND_AND_CONTROL

        return None

    def _correlate_event(
        self,
        timeline_id: str,
        event: TimelineEvent,
    ) -> None:
        """
        Correlaciona evento com eventos próximos

        Args:
            timeline_id: Timeline ID
            event: Event to correlate
        """
        timeline = self.timelines[timeline_id]

        # Find events within correlation window
        window_start = event.timestamp - timedelta(seconds=self.correlation_window)
        window_end = event.timestamp + timedelta(seconds=self.correlation_window)

        for other_event in timeline:
            if other_event.id == event.id:
                continue

            if window_start <= other_event.timestamp <= window_end:
                # Check correlation criteria
                if self._should_correlate(event, other_event):
                    # Add correlation
                    if other_event.id not in event.correlated_events:
                        event.correlated_events.append(other_event.id)

                    if event.id not in other_event.correlated_events:
                        other_event.correlated_events.append(event.id)

    def _should_correlate(
        self,
        event1: TimelineEvent,
        event2: TimelineEvent,
    ) -> bool:
        """
        Verifica se dois eventos devem ser correlacionados

        Args:
            event1: First event
            event2: Second event

        Returns:
            True se devem ser correlacionados
        """
        # Same source
        if event1.source == event2.source:
            return True

        # Shared IOCs
        shared_iocs = set(event1.iocs) & set(event2.iocs)
        if shared_iocs:
            return True

        # Same MITRE technique
        shared_techniques = set(event1.mitre_techniques) & set(event2.mitre_techniques)
        if shared_techniques:
            return True

        return False

    def reconstruct_attack_chain(
        self,
        timeline_id: str,
        start_event_id: Optional[str] = None,
    ) -> AttackChain:
        """
        Reconstrói attack chain de eventos correlacionados

        Args:
            timeline_id: Timeline ID
            start_event_id: Starting event (se None, detecta automaticamente)

        Returns:
            AttackChain
        """
        timeline = self.timelines.get(timeline_id, [])

        if not timeline:
            raise ValueError(f"Timeline not found: {timeline_id}")

        # Find start event
        if start_event_id:
            start_event = next((e for e in timeline if e.id == start_event_id), None)
        else:
            # Auto-detect: earliest event with kill chain phase
            start_event = min(
                (e for e in timeline if e.kill_chain_phase),
                key=lambda e: e.timestamp,
                default=None
            )

        if not start_event:
            raise ValueError("Could not find starting event")

        # Build chain by following correlations
        chain_events = [start_event]
        visited = {start_event.id}

        def add_correlated(event):
            for corr_id in event.correlated_events:
                if corr_id not in visited:
                    corr_event = next((e for e in timeline if e.id == corr_id), None)
                    if corr_event:
                        chain_events.append(corr_event)
                        visited.add(corr_id)
                        add_correlated(corr_event)

        add_correlated(start_event)

        # Sort by timestamp
        chain_events.sort(key=lambda e: e.timestamp)

        # Build AttackChain
        import uuid

        attack_chain = AttackChain(
            id=f"chain-{uuid.uuid4().hex[:8]}",
            name=f"Attack Chain - {start_event.title}",
            description=f"Reconstructed attack chain starting from {start_event.timestamp}",
            events=chain_events,
        )

        # Calculate metadata
        if chain_events:
            attack_chain.initial_access_time = chain_events[0].timestamp
            attack_chain.final_action_time = chain_events[-1].timestamp
            attack_chain.duration_minutes = (
                attack_chain.final_action_time - attack_chain.initial_access_time
            ).total_seconds() / 60

        # Extract kill chain phases
        phases = set()
        for event in chain_events:
            if event.kill_chain_phase:
                phases.add(event.kill_chain_phase)

        attack_chain.kill_chain_phases = sorted(list(phases), key=lambda p: p.value)

        # Extract MITRE techniques
        all_techniques = set()
        for event in chain_events:
            all_techniques.update(event.mitre_techniques)

        attack_chain.mitre_techniques = sorted(list(all_techniques))

        self.attack_chains.append(attack_chain)

        logger.info(
            f"Attack chain reconstructed: {attack_chain.id} "
            f"({len(chain_events)} events, {attack_chain.duration_minutes:.1f} min)"
        )

        return attack_chain

    def get_timeline(self, timeline_id: str) -> List[TimelineEvent]:
        """
        Retorna timeline

        Args:
            timeline_id: Timeline ID

        Returns:
            List of TimelineEvent
        """
        return self.timelines.get(timeline_id, [])

    def get_events_by_timerange(
        self,
        timeline_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> List[TimelineEvent]:
        """
        Retorna eventos em range de tempo

        Args:
            timeline_id: Timeline ID
            start_time: Start time
            end_time: End time

        Returns:
            List of TimelineEvent
        """
        timeline = self.timelines.get(timeline_id, [])

        return [
            e for e in timeline
            if start_time <= e.timestamp <= end_time
        ]

    def export_timeline(
        self,
        timeline_id: str,
        format: str = "json",
    ) -> str:
        """
        Exporta timeline

        Args:
            timeline_id: Timeline ID
            format: Export format (json, csv)

        Returns:
            Exported data string
        """
        timeline = self.timelines.get(timeline_id, [])

        if format == "json":
            import json

            events_data = [
                {
                    "id": e.id,
                    "timestamp": e.timestamp.isoformat(),
                    "type": e.event_type.value,
                    "source": e.source,
                    "title": e.title,
                    "description": e.description,
                    "kill_chain_phase": e.kill_chain_phase.value if e.kill_chain_phase else None,
                    "mitre_techniques": e.mitre_techniques,
                    "iocs": e.iocs,
                }
                for e in timeline
            ]

            return json.dumps(events_data, indent=2)

        elif format == "csv":
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)

            # Header
            writer.writerow([
                "Timestamp", "Type", "Source", "Title", "Kill Chain", "MITRE Techniques"
            ])

            # Data
            for e in timeline:
                writer.writerow([
                    e.timestamp.isoformat(),
                    e.event_type.value,
                    e.source,
                    e.title,
                    e.kill_chain_phase.value if e.kill_chain_phase else "",
                    ", ".join(e.mitre_techniques),
                ])

            return output.getvalue()

        return ""
