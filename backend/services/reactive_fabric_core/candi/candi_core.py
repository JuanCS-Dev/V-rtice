"""
CANDI Core Engine
Central orchestration and analysis engine for Reactive Fabric
"""

import asyncio
import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable

from .forensic_analyzer import ForensicAnalyzer, ForensicReport
from .attribution_engine import AttributionEngine, AttributionResult
from .threat_intelligence import ThreatIntelligence, ThreatIntelReport

logger = logging.getLogger(__name__)

class ThreatLevel(Enum):
    """Threat classification levels"""
    NOISE = 1           # Automated scans, bots
    OPPORTUNISTIC = 2   # Generic exploits, script kiddies
    TARGETED = 3        # Directed attacks, custom tools
    APT = 4            # Advanced Persistent Threat, nation-state

@dataclass
class AnalysisResult:
    """Complete analysis result from CANDI"""
    analysis_id: str
    timestamp: datetime
    honeypot_id: str
    source_ip: str
    threat_level: ThreatLevel

    # Analysis components
    forensic_report: ForensicReport
    threat_intel: ThreatIntelReport
    attribution: AttributionResult

    # Extracted intelligence
    iocs: List[str] = field(default_factory=list)
    ttps: List[str] = field(default_factory=list)

    # Recommendations
    recommended_actions: List[str] = field(default_factory=list)
    requires_hitl: bool = False
    confidence_score: float = 0.0

    # Metadata
    processing_time_ms: int = 0
    incident_id: Optional[str] = None

class Incident:
    """Tracked security incident"""

    def __init__(self, incident_id: str, initial_event: Dict):
        self.incident_id = incident_id
        self.created_at = datetime.now()
        self.status = "ACTIVE"
        self.events: List[Dict] = [initial_event]
        self.threat_level = ThreatLevel.NOISE
        self.attributed_actor: Optional[str] = None
        self.assigned_to: Optional[str] = None

    def add_event(self, event: Dict):
        """Add related event to incident"""
        self.events.append(event)

    def escalate(self, new_level: ThreatLevel):
        """Escalate incident threat level"""
        if new_level.value > self.threat_level.value:
            self.threat_level = new_level
            logger.warning(f"Incident {self.incident_id} escalated to {new_level.name}")

    def to_dict(self) -> Dict:
        """Convert incident to dictionary"""
        return {
            "incident_id": self.incident_id,
            "created_at": self.created_at.isoformat(),
            "status": self.status,
            "threat_level": self.threat_level.name,
            "event_count": len(self.events),
            "attributed_actor": self.attributed_actor,
            "assigned_to": self.assigned_to
        }

class CANDICore:
    """
    CANDI Core - Central Analysis & Decision Intelligence

    Pipeline:
    1. Receive event from honeypot
    2. Forensic analysis
    3. Threat intelligence correlation
    4. Attribution scoring
    5. Generate recommendations
    6. Request HITL decision if needed
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize CANDI Core

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}

        # Analysis engines
        self.forensic_analyzer = ForensicAnalyzer()
        self.attribution_engine = AttributionEngine()
        self.threat_intel = ThreatIntelligence()

        # Incident tracking
        self.active_incidents: Dict[str, Incident] = {}
        self.incident_counter = 0

        # Analysis queue
        self.analysis_queue: asyncio.Queue = asyncio.Queue()
        self.workers: List[asyncio.Task] = []
        self._running = False

        # Callbacks
        self.analysis_callbacks: List[Callable] = []
        self.hitl_request_callback: Optional[Callable] = None

        # Statistics
        self.stats = {
            "total_analyzed": 0,
            "by_threat_level": {level.name: 0 for level in ThreatLevel},
            "hitl_requests": 0,
            "active_incidents": 0,
            "avg_processing_time_ms": 0
        }

    async def start(self, num_workers: int = 4):
        """
        Start CANDI analysis workers

        Args:
            num_workers: Number of parallel analysis workers
        """
        if self._running:
            logger.warning("CANDI Core already running")
            return

        self._running = True

        # Initialize analysis engines
        await self.forensic_analyzer.initialize()
        await self.attribution_engine.initialize()
        await self.threat_intel.initialize()

        # Start worker tasks
        for i in range(num_workers):
            worker = asyncio.create_task(self._analysis_worker(f"worker-{i}"))
            self.workers.append(worker)

        logger.info(f"CANDI Core started with {num_workers} workers")

    async def stop(self):
        """Stop CANDI Core"""
        self._running = False

        # Cancel all workers
        for worker in self.workers:
            worker.cancel()

        await asyncio.gather(*self.workers, return_exceptions=True)

        logger.info("CANDI Core stopped")

    async def analyze_honeypot_event(self, event: Dict[str, Any]) -> AnalysisResult:
        """
        Analyze event from honeypot

        Args:
            event: Event data from honeypot

        Returns:
            Complete analysis result
        """
        start_time = datetime.now()

        # Generate analysis ID
        analysis_id = self._generate_analysis_id(event)

        logger.info(f"Starting analysis {analysis_id} for event from {event.get('source_ip')}")

        # Step 1: Forensic Analysis
        forensic_report = await self.forensic_analyzer.analyze(event)

        # Step 2: Threat Intelligence Correlation
        threat_intel_report = await self.threat_intel.correlate(forensic_report)

        # Step 3: Attribution
        attribution = await self.attribution_engine.attribute(
            forensic_report,
            threat_intel_report
        )

        # Step 4: Classify Threat Level
        threat_level = self._classify_threat_level(
            forensic_report,
            threat_intel_report,
            attribution
        )

        # Step 5: Extract IOCs and TTPs
        iocs = self._extract_iocs(forensic_report, threat_intel_report)
        ttps = self._map_to_mitre_attack(forensic_report)

        # Step 6: Generate Recommendations
        recommendations = self._generate_recommendations(
            threat_level,
            attribution,
            forensic_report
        )

        # Step 7: Determine if HITL needed
        requires_hitl = self._requires_hitl_decision(threat_level, attribution)

        # Calculate processing time
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)

        # Create analysis result
        result = AnalysisResult(
            analysis_id=analysis_id,
            timestamp=datetime.now(),
            honeypot_id=event.get('honeypot_id', 'unknown'),
            source_ip=event.get('source_ip', 'unknown'),
            threat_level=threat_level,
            forensic_report=forensic_report,
            threat_intel=threat_intel_report,
            attribution=attribution,
            iocs=iocs,
            ttps=ttps,
            recommended_actions=recommendations,
            requires_hitl=requires_hitl,
            confidence_score=attribution.confidence / 100.0,
            processing_time_ms=processing_time
        )

        # Update statistics
        self._update_stats(result)

        # Create or update incident
        if threat_level.value >= ThreatLevel.TARGETED.value:
            incident = self._create_or_update_incident(event, result)
            result.incident_id = incident.incident_id

        # Request HITL if needed
        if requires_hitl and self.hitl_request_callback:
            await self.hitl_request_callback(result)

        # Notify callbacks
        for callback in self.analysis_callbacks:
            try:
                await callback(result)
            except Exception as e:
                logger.error(f"Analysis callback error: {e}")

        logger.info(
            f"Analysis {analysis_id} complete: {threat_level.name} "
            f"(confidence: {result.confidence_score:.2f}, time: {processing_time}ms)"
        )

        return result

    async def submit_for_analysis(self, event: Dict[str, Any]):
        """
        Submit event to analysis queue

        Args:
            event: Event data from honeypot
        """
        await self.analysis_queue.put(event)

    async def _analysis_worker(self, worker_id: str):
        """
        Analysis worker - processes events from queue

        Args:
            worker_id: Worker identifier
        """
        logger.info(f"Analysis worker {worker_id} started")

        while self._running:
            try:
                # Get event from queue (timeout to allow checking _running)
                try:
                    event = await asyncio.wait_for(
                        self.analysis_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                # Analyze event
                try:
                    await self.analyze_honeypot_event(event)
                except Exception as e:
                    logger.error(f"Worker {worker_id} analysis error: {e}")
                finally:
                    self.analysis_queue.task_done()

            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")

        logger.info(f"Analysis worker {worker_id} stopped")

    def _generate_analysis_id(self, event: Dict) -> str:
        """Generate unique analysis ID"""
        data = f"{event.get('source_ip')}{event.get('timestamp')}{datetime.now()}"
        return f"CANDI-{hashlib.sha256(data.encode()).hexdigest()[:16]}"

    def _classify_threat_level(self,
                               forensic: ForensicReport,
                               intel: ThreatIntelReport,
                               attribution: AttributionResult) -> ThreatLevel:
        """
        Classify threat level based on analysis

        Args:
            forensic: Forensic analysis report
            intel: Threat intelligence report
            attribution: Attribution result

        Returns:
            Threat level classification
        """
        # APT indicators
        if attribution.apt_indicators:
            return ThreatLevel.APT

        # Known APT actor
        if attribution.attributed_actor and "APT" in attribution.attributed_actor:
            return ThreatLevel.APT

        # High sophistication + known tools
        if forensic.sophistication_score > 8 and intel.known_tools:
            return ThreatLevel.TARGETED

        # Custom exploits or zero-days
        if "zero_day" in forensic.behaviors or "custom_exploit" in forensic.behaviors:
            return ThreatLevel.TARGETED

        # Known exploits or tools
        if intel.known_exploits or forensic.malware_detected:
            return ThreatLevel.OPPORTUNISTIC

        # Default to noise
        return ThreatLevel.NOISE

    def _extract_iocs(self,
                      forensic: ForensicReport,
                      intel: ThreatIntelReport) -> List[str]:
        """Extract all Indicators of Compromise"""
        iocs = []

        # From forensic analysis
        iocs.extend(forensic.network_iocs)
        iocs.extend(forensic.file_hashes)

        # From threat intel
        iocs.extend(intel.related_iocs)

        return list(set(iocs))  # Remove duplicates

    def _map_to_mitre_attack(self, forensic: ForensicReport) -> List[str]:
        """Map behaviors to MITRE ATT&CK TTPs"""
        ttps = []

        # Behavior to TTP mapping
        ttp_mapping = {
            'ssh_brute_force': 'T1110.001',
            'sql_injection': 'T1190',
            'command_injection': 'T1059',
            'xss_attack': 'T1189',
            'file_upload': 'T1105',
            'privilege_escalation': 'T1068',
            'lateral_movement': 'T1021',
            'data_exfiltration': 'T1041',
            'persistence': 'T1053',
            'credential_access': 'T1003',
            'discovery': 'T1083',
            'defense_evasion': 'T1070'
        }

        for behavior in forensic.behaviors:
            if behavior in ttp_mapping:
                ttps.append(ttp_mapping[behavior])

        return list(set(ttps))

    def _generate_recommendations(self,
                                  threat_level: ThreatLevel,
                                  attribution: AttributionResult,
                                  forensic: ForensicReport) -> List[str]:
        """Generate recommended actions based on analysis"""
        recommendations = []

        # Based on threat level
        if threat_level == ThreatLevel.APT:
            recommendations.extend([
                "CRITICAL: Potential APT activity detected",
                "Isolate affected systems immediately",
                "Notify security leadership",
                "Initiate incident response protocol",
                "Preserve all forensic evidence"
            ])
        elif threat_level == ThreatLevel.TARGETED:
            recommendations.extend([
                "HIGH: Targeted attack detected",
                "Review and strengthen defenses",
                "Monitor for related activity",
                "Update threat intelligence feeds"
            ])
        elif threat_level == ThreatLevel.OPPORTUNISTIC:
            recommendations.extend([
                "MEDIUM: Opportunistic attack detected",
                "Block identified IOCs",
                "Update signatures and rules"
            ])

        # Based on attribution
        if attribution.confidence > 70:
            recommendations.append(
                f"Attribution: {attribution.attributed_actor} "
                f"(confidence: {attribution.confidence}%)"
            )

        # Based on forensic findings
        if forensic.malware_detected:
            recommendations.append("Submit malware samples to sandbox for analysis")

        if forensic.credentials_compromised:
            recommendations.append("URGENT: Rotate compromised credentials")

        return recommendations

    def _requires_hitl_decision(self,
                                threat_level: ThreatLevel,
                                attribution: AttributionResult) -> bool:
        """Determine if human decision is required"""
        # Always require HITL for APT
        if threat_level == ThreatLevel.APT:
            return True

        # Require HITL for high-confidence attribution
        if attribution.confidence > 80:
            return True

        # Require HITL for targeted attacks
        if threat_level == ThreatLevel.TARGETED:
            return True

        return False

    def _create_or_update_incident(self,
                                   event: Dict,
                                   result: AnalysisResult) -> Incident:
        """Create new incident or update existing one"""
        # Try to find related incident (same source IP, within 24h)
        source_ip = event.get('source_ip')
        cutoff_time = datetime.now() - timedelta(hours=24)

        for incident in self.active_incidents.values():
            if (any(e.get('source_ip') == source_ip for e in incident.events) and
                incident.created_at > cutoff_time):
                # Update existing incident
                incident.add_event(event)
                incident.escalate(result.threat_level)
                if result.attribution.attributed_actor:
                    incident.attributed_actor = result.attribution.attributed_actor
                return incident

        # Create new incident
        self.incident_counter += 1
        incident_id = f"INC-{datetime.now().strftime('%Y%m%d')}-{self.incident_counter:04d}"

        incident = Incident(incident_id, event)
        incident.threat_level = result.threat_level
        if result.attribution.attributed_actor:
            incident.attributed_actor = result.attribution.attributed_actor

        self.active_incidents[incident_id] = incident
        self.stats["active_incidents"] += 1

        logger.info(f"Created incident {incident_id} for {source_ip}")

        return incident

    def _update_stats(self, result: AnalysisResult):
        """Update CANDI statistics"""
        self.stats["total_analyzed"] += 1
        self.stats["by_threat_level"][result.threat_level.name] += 1

        if result.requires_hitl:
            self.stats["hitl_requests"] += 1

        # Update average processing time
        total = self.stats["total_analyzed"]
        current_avg = self.stats["avg_processing_time_ms"]
        new_avg = ((current_avg * (total - 1)) + result.processing_time_ms) / total
        self.stats["avg_processing_time_ms"] = int(new_avg)

    def register_analysis_callback(self, callback: Callable):
        """Register callback for analysis completion"""
        self.analysis_callbacks.append(callback)

    def register_hitl_callback(self, callback: Callable):
        """Register callback for HITL requests"""
        self.hitl_request_callback = callback

    def get_incident(self, incident_id: str) -> Optional[Incident]:
        """Get incident by ID"""
        return self.active_incidents.get(incident_id)

    def get_active_incidents(self) -> List[Dict]:
        """Get all active incidents"""
        return [incident.to_dict() for incident in self.active_incidents.values()]

    def get_stats(self) -> Dict:
        """Get CANDI statistics"""
        return {
            **self.stats,
            "queue_size": self.analysis_queue.qsize(),
            "workers_active": len(self.workers)
        }