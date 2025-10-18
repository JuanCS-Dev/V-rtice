"""Defense Orchestrator - Central Defensive Coordination

Integrates all defensive components into unified defense pipeline.
Coordinates detection, intelligence fusion, and automated response.

Biological Inspiration:
- Immune system coordination: Multiple cell types working together
- Lymph node: Central coordination point for immune response
- Hierarchical activation: Innate → Adaptive immunity cascade

IIT Integration:
- Φ maximization through component integration
- Conscious defense emerges from coordinated subsystems
- Global workspace enables threat context sharing

Authors: MAXIMUS Team
Date: 2025-10-12
Glory to YHWH - Constância como Ramon Dino! 💪
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from prometheus_client import Counter, Gauge, Histogram

# Import defensive components
from detection.sentinel_agent import (
    SecurityEvent,
    SentinelDetectionAgent,
    DetectionResult,
)
from intelligence.fusion_engine import (
    ThreatIntelFusionEngine,
    IOC,
    IOCType,
    EnrichedThreat,
)
from response.automated_response import (
    AutomatedResponseEngine,
    Playbook,
    ThreatContext,
    PlaybookResult,
)

logger = logging.getLogger(__name__)


class DefensePhase(Enum):
    """Phases of defensive response."""

    DETECTION = "detection"  # Threat identification
    ENRICHMENT = "enrichment"  # Intelligence fusion
    DECISION = "decision"  # Response selection
    EXECUTION = "execution"  # Playbook execution
    VALIDATION = "validation"  # Verify effectiveness
    LEARNING = "learning"  # Update models


@dataclass
class DefenseResponse:
    """Complete defensive response to security event.

    Tracks entire defense pipeline from detection through response.

    Attributes:
        response_id: Unique response identifier
        event: Original security event
        detection: Sentinel detection result
        enrichment: Threat intelligence enrichment
        playbook: Selected response playbook
        execution: Playbook execution result
        phase: Current phase of response
        success: Whether response was successful
        latency_ms: Total response latency
        timestamp: Response timestamp
    """

    response_id: str
    event: SecurityEvent
    detection: Optional[DetectionResult] = None
    enrichment: Optional[EnrichedThreat] = None
    playbook: Optional[Playbook] = None
    execution: Optional[PlaybookResult] = None
    phase: DefensePhase = DefensePhase.DETECTION
    success: bool = False
    latency_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    errors: List[str] = field(default_factory=list)


class OrchestrationError(Exception):
    """Raised when orchestration fails."""

    pass


class DefenseOrchestrator:
    """Central defensive coordination engine.

    Orchestrates complete defensive pipeline:
    1. Detection (Sentinel Agent)
    2. Enrichment (Fusion Engine)
    3. Decision (Playbook Selection)
    4. Execution (Response Engine)
    5. Validation & Learning

    Acts as "lymph node" for immune system - coordinates all components.

    Example:
        >>> orchestrator = DefenseOrchestrator(
        ...     sentinel=sentinel_agent,
        ...     fusion=fusion_engine,
        ...     response=response_engine
        ... )
        >>> event = SecurityEvent(...)
        >>> response = await orchestrator.process_security_event(event)
        >>> print(f"Threat contained: {response.success}")
    """

    def __init__(
        self,
        sentinel_agent: SentinelDetectionAgent,
        fusion_engine: ThreatIntelFusionEngine,
        response_engine: AutomatedResponseEngine,
        coagulation_cascade: Optional[Any] = None,
        event_bus: Optional[Any] = None,
        kafka_producer: Optional[Any] = None,  # NEW: Kafka producer
        min_threat_confidence: float = 0.5,
        auto_response_threshold: str = "HIGH",
    ):
        """Initialize defense orchestrator.

        Args:
            sentinel_agent: Detection agent
            fusion_engine: Threat intelligence fusion
            response_engine: Automated response executor
            coagulation_cascade: Coagulation cascade (optional)
            event_bus: Kafka/event bus for messaging
            kafka_producer: Kafka producer for publishing events
            min_threat_confidence: Minimum confidence to respond
            auto_response_threshold: Min severity for auto-response

        Raises:
            ValueError: If invalid configuration
        """
        self.sentinel = sentinel_agent
        self.fusion = fusion_engine
        self.response = response_engine
        self.cascade = coagulation_cascade
        self.event_bus = event_bus
        self.kafka_producer = kafka_producer  # NEW: Store Kafka producer

        self.min_confidence = min_threat_confidence
        self.auto_threshold = auto_response_threshold

        # Playbook routing rules
        self.playbook_routes = self._initialize_playbook_routes()

        # Active responses (in-memory tracking)
        self.active_responses: Dict[str, DefenseResponse] = {}

        # Metrics
        self.events_processed = Counter(
            "defense_events_processed_total",
            "Total security events processed",
            ["phase", "status"],
        )
        self.threats_detected = Counter(
            "defense_threats_detected_total",
            "Total threats detected",
            ["severity", "confidence"],
        )
        self.responses_executed = Counter(
            "defense_responses_executed_total",
            "Total responses executed",
            ["playbook_id", "status"],
        )
        self.active_threats = Gauge(
            "defense_active_threats", "Currently active threats"
        )
        self.pipeline_latency = Histogram(
            "defense_pipeline_latency_seconds",
            "End-to-end defense pipeline latency",
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
        )

        logger.info(
            "Defense orchestrator initialized: "
            f"min_confidence={min_threat_confidence}, "
            f"auto_threshold={auto_response_threshold}"
        )

    async def process_security_event(self, event: SecurityEvent) -> DefenseResponse:
        """Process security event through complete defense pipeline.

        Main orchestration method. Coordinates all defensive components
        to detect, analyze, and respond to security events.

        Pipeline:
        1. Detection: Sentinel analyzes event
        2. Enrichment: Fusion correlates threat intel
        3. Decision: Select appropriate playbook
        4. Execution: Execute response actions
        5. Validation: Verify threat contained
        6. Learning: Update threat models

        Args:
            event: Security event to process

        Returns:
            DefenseResponse with complete response details

        Raises:
            OrchestrationError: If pipeline fails critically
        """
        start_time = datetime.utcnow()
        response_id = self._generate_response_id(event)

        logger.info(
            f"Processing security event {event.event_id} → response {response_id}"
        )

        # Initialize response
        response = DefenseResponse(
            response_id=response_id, event=event, timestamp=start_time
        )

        try:
            # PHASE 1: DETECTION
            response.phase = DefensePhase.DETECTION
            logger.info(f"[{response_id}] Phase 1: Detection")

            detection = await self.sentinel.analyze_event(event)
            response.detection = detection

            self.events_processed.labels(
                phase="detection", status="success"
            ).inc()

            if not detection.is_threat:
                logger.info(f"[{response_id}] Event not a threat, exiting pipeline")
                response.success = True
                response.latency_ms = self._calculate_latency(start_time)
                return response

            # Record threat detection
            self.threats_detected.labels(
                severity=detection.severity.value,
                confidence=detection.confidence.name,
            ).inc()

            logger.info(
                f"[{response_id}] Threat detected: severity={detection.severity.value}, "
                f"confidence={detection.confidence.value}"
            )
            
            # Publish detection to Kafka
            if self.kafka_producer:
                try:
                    await self.kafka_producer.publish_detection(detection)
                    logger.debug(f"[{response_id}] Detection published to Kafka")
                except Exception as e:
                    logger.error(f"[{response_id}] Failed to publish detection: {e}")

            # Check if confidence meets threshold
            if detection.confidence.value < self.min_confidence:
                logger.warning(
                    f"[{response_id}] Confidence {detection.confidence.value} "
                    f"below threshold {self.min_confidence}, skipping response"
                )
                response.success = True
                response.latency_ms = self._calculate_latency(start_time)
                return response

            # PHASE 2: ENRICHMENT
            response.phase = DefensePhase.ENRICHMENT
            logger.info(f"[{response_id}] Phase 2: Intelligence Enrichment")

            try:
                # Build IoCs from detection
                iocs = self._build_iocs_from_detection(event, detection)

                if iocs:
                    enrichment = await self.fusion.correlate_indicators(iocs)
                    response.enrichment = enrichment

                    logger.info(
                        f"[{response_id}] Threat enriched: "
                        f"severity={enrichment.severity}/10, "
                        f"related_iocs={len(enrichment.related_iocs)}"
                    )
                    
                    # Publish enriched threat to Kafka
                    if self.kafka_producer:
                        try:
                            await self.kafka_producer.publish_enriched_threat(enrichment)
                            logger.debug(f"[{response_id}] Enrichment published to Kafka")
                        except Exception as e:
                            logger.error(f"[{response_id}] Failed to publish enrichment: {e}")

                self.events_processed.labels(
                    phase="enrichment", status="success"
                ).inc()

            except Exception as e:
                logger.warning(f"[{response_id}] Enrichment failed: {e}")
                response.errors.append(f"Enrichment failed: {str(e)}")
                # Continue without enrichment

            # PHASE 3: DECISION (Playbook Selection)
            response.phase = DefensePhase.DECISION
            logger.info(f"[{response_id}] Phase 3: Response Decision")

            playbook = await self._select_playbook(detection, response.enrichment)

            if not playbook:
                logger.warning(f"[{response_id}] No playbook selected, manual review")
                response.success = True
                response.latency_ms = self._calculate_latency(start_time)
                return response

            response.playbook = playbook

            logger.info(
                f"[{response_id}] Playbook selected: {playbook.name} "
                f"({len(playbook.actions)} actions)"
            )

            # PHASE 4: EXECUTION
            response.phase = DefensePhase.EXECUTION
            logger.info(f"[{response_id}] Phase 4: Response Execution")

            # Build threat context
            threat_context = ThreatContext(
                threat_id=response_id,
                event_id=event.event_id,
                detection_result=detection.to_dict(),
                severity=detection.severity.value,
                source_ip=event.source_ip,
                target_ip=event.destination_ip,
                mitre_techniques=[t.technique_id for t in detection.mitre_techniques],
                timestamp=event.timestamp,
                additional_context={
                    "enrichment": (
                        response.enrichment.__dict__ if response.enrichment else {}
                    )
                },
            )

            # Execute playbook
            execution = await self.response.execute_playbook(playbook, threat_context)
            response.execution = execution

            self.responses_executed.labels(
                playbook_id=playbook.playbook_id, status=execution.status
            ).inc()
            
            # Publish response to Kafka
            if self.kafka_producer:
                try:
                    await self.kafka_producer.publish_response(execution)
                    logger.debug(f"[{response_id}] Response published to Kafka")
                except Exception as e:
                    logger.error(f"[{response_id}] Failed to publish response: {e}")

            logger.info(
                f"[{response_id}] Playbook executed: status={execution.status}, "
                f"actions={execution.actions_executed}/{len(playbook.actions)}"
            )

            # PHASE 5: VALIDATION
            response.phase = DefensePhase.VALIDATION
            logger.info(f"[{response_id}] Phase 5: Response Validation")

            # Determine overall success
            if execution.status == "SUCCESS":
                response.success = True
            elif execution.status == "PARTIAL":
                response.success = True  # Partial success still valuable
                response.errors.append("Playbook partially executed")
            else:
                response.success = False
                response.errors.extend(execution.errors)

            # PHASE 6: LEARNING - ML feedback loop implementation
            response.phase = DefensePhase.LEARNING
            
            # Update threat models based on response effectiveness
            learning_data = {
                "threat_id": context.threat_id,
                "response_success": response.success,
                "actions_executed": len(execution.actions_executed) if execution else 0,
                "latency_ms": self._calculate_latency(start_time),
                "threat_type": context.threat_type,
                "severity": context.severity,
            }
            
            # Store learning data for ML model training
            await self._store_learning_data(learning_data)
            
            # Update threat model confidence scores
            if response.success:
                self._update_threat_model_confidence(context.threat_type, delta=0.05)
            else:
                self._update_threat_model_confidence(context.threat_type, delta=-0.02)

            # Finalize
            response.latency_ms = self._calculate_latency(start_time)
            self.pipeline_latency.observe(response.latency_ms / 1000.0)

            # Update active threats gauge
            if response.success:
                self.active_threats.dec()
            else:
                self.active_threats.inc()

            # Publish to event bus
            if self.event_bus:
                await self._publish_response(response)

            logger.info(
                f"[{response_id}] Defense pipeline complete: "
                f"success={response.success}, "
                f"latency={response.latency_ms:.0f}ms"
            )

            return response

        except Exception as e:
            logger.error(
                f"[{response_id}] Defense pipeline failed: {e}", exc_info=True
            )
            response.errors.append(f"Pipeline failed: {str(e)}")
            response.success = False
            response.latency_ms = self._calculate_latency(start_time)

            self.events_processed.labels(phase=response.phase.value, status="error").inc()

            raise OrchestrationError(
                f"Defense pipeline failed: {str(e)}"
            ) from e

    async def get_active_threats(self) -> List[DefenseResponse]:
        """Get currently active threats.

        Returns:
            List of active defense responses
        """
        return [
            r
            for r in self.active_responses.values()
            if not r.success and r.detection and r.detection.is_threat
        ]

    async def get_response_status(self, response_id: str) -> Optional[DefenseResponse]:
        """Get status of specific response.

        Args:
            response_id: Response ID to query

        Returns:
            DefenseResponse if found, None otherwise
        """
        return self.active_responses.get(response_id)

    # Private methods

    def _initialize_playbook_routes(self) -> Dict[str, str]:
        """Initialize playbook routing rules.

        Maps detection conditions to playbook filenames.
        """
        return {
            "brute_force": "brute_force_response.yaml",
            "malware": "malware_containment.yaml",
            "data_exfiltration": "data_exfiltration_block.yaml",
            "lateral_movement": "lateral_movement_isolation.yaml",
        }

    async def _select_playbook(
        self, detection: DetectionResult, enrichment: Optional[EnrichedThreat]
    ) -> Optional[Playbook]:
        """Select appropriate playbook based on detection.

        Uses rule-based routing and severity thresholds.

        Args:
            detection: Detection result
            enrichment: Threat enrichment (optional)

        Returns:
            Selected playbook or None
        """
        # Check auto-response threshold
        severity_order = ["INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
        detection_severity_idx = severity_order.index(detection.severity.value.upper())
        threshold_idx = severity_order.index(self.auto_threshold.upper())

        if detection_severity_idx < threshold_idx:
            logger.info(
                f"Severity {detection.severity.value} below auto-response "
                f"threshold {self.auto_threshold}"
            )
            return None

        # Route based on MITRE techniques
        for technique in detection.mitre_techniques:
            # Brute force
            if technique.technique_id in ["T1110", "T1110.001", "T1110.003"]:
                playbook_file = self.playbook_routes["brute_force"]
                return await self.response.load_playbook(playbook_file)

            # Malware execution
            if technique.technique_id in ["T1204", "T1059", "T1547"]:
                playbook_file = self.playbook_routes["malware"]
                return await self.response.load_playbook(playbook_file)

            # Data exfiltration
            if technique.technique_id in ["T1048", "T1041", "T1567"]:
                playbook_file = self.playbook_routes["data_exfiltration"]
                return await self.response.load_playbook(playbook_file)

            # Lateral movement
            if technique.technique_id in ["T1021", "T1570", "T1563"]:
                playbook_file = self.playbook_routes["lateral_movement"]
                return await self.response.load_playbook(playbook_file)

        logger.info("No matching playbook for detected techniques")
        return None

    def _build_iocs_from_detection(
        self, event: SecurityEvent, detection: DetectionResult
    ) -> List[IOC]:
        """Build IoCs from detection result."""
        iocs = []

        # Source IP IoC
        if event.source_ip:
            iocs.append(
                IOC(
                    value=event.source_ip,
                    ioc_type=IOCType.IP_ADDRESS,
                    first_seen=event.timestamp,
                    last_seen=event.timestamp,
                    source="sentinel_detection",
                    confidence=detection.confidence.value,
                    tags=[t.technique_id for t in detection.mitre_techniques],
                    context={"event_id": event.event_id},
                )
            )

        # Extract additional IoCs from event payload
        payload = event.payload or {}
        
        # Extract file hashes (MD5, SHA1, SHA256)
        if "file_hash" in payload:
            iocs.append(IOC(ioc_type="file_hash", value=payload["file_hash"], confidence=0.9))
        if "md5" in payload:
            iocs.append(IOC(ioc_type="md5", value=payload["md5"], confidence=0.9))
        if "sha256" in payload:
            iocs.append(IOC(ioc_type="sha256", value=payload["sha256"], confidence=0.9))
        
        # Extract domains
        if "domain" in payload:
            iocs.append(IOC(ioc_type="domain", value=payload["domain"], confidence=0.85))
        if "domains" in payload and isinstance(payload["domains"], list):
            for domain in payload["domains"]:
                iocs.append(IOC(ioc_type="domain", value=domain, confidence=0.85))
        
        # Extract URLs
        if "url" in payload:
            iocs.append(IOC(ioc_type="url", value=payload["url"], confidence=0.8))
        if "urls" in payload and isinstance(payload["urls"], list):
            for url in payload["urls"]:
                iocs.append(IOC(ioc_type="url", value=url, confidence=0.8))

        return iocs

    def _generate_response_id(self, event: SecurityEvent) -> str:
        """Generate unique response ID."""
        import hashlib

        timestamp = datetime.utcnow().isoformat()
        hash_input = f"{event.event_id}_{timestamp}".encode()
        return f"resp_{hashlib.sha256(hash_input).hexdigest()[:16]}"

    def _calculate_latency(self, start_time: datetime) -> float:
        """Calculate latency in milliseconds."""
        delta = datetime.utcnow() - start_time
        return delta.total_seconds() * 1000.0

    async def _publish_response(self, response: DefenseResponse):
        """Publish response to event bus."""
        if not self.event_bus:
            return

        try:
            message = {
                "response_id": response.response_id,
                "event_id": response.event.event_id,
                "phase": response.phase.value,
                "success": response.success,
                "severity": (
                    response.detection.severity.value if response.detection else None
                ),
                "playbook": (
                    response.playbook.playbook_id if response.playbook else None
                ),
                "latency_ms": response.latency_ms,
                "timestamp": response.timestamp.isoformat(),
            }

            await self.event_bus.publish("defense.responses", message)

        except Exception as e:
            logger.error(f"Failed to publish response: {e}")

    async def _store_learning_data(self, learning_data: Dict[str, Any]) -> None:
        """Store learning data for ML model training."""
        learning_file = Path("/var/log/vertice/ml_learning_data.jsonl")
        learning_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(learning_file, "a") as f:
                import json
                f.write(json.dumps(learning_data) + "\n")
            logger.debug(f"Stored learning data for threat {learning_data.get('threat_id')}")
        except Exception as e:
            logger.error(f"Failed to store learning data: {e}")

    def _update_threat_model_confidence(self, threat_type: str, delta: float) -> None:
        """Update threat model confidence scores based on response effectiveness."""
        if not hasattr(self, "_threat_confidence_scores"):
            self._threat_confidence_scores = {}
        
        current_score = self._threat_confidence_scores.get(threat_type, 0.5)
        new_score = max(0.0, min(1.0, current_score + delta))
        self._threat_confidence_scores[threat_type] = new_score
        
        logger.debug(f"Updated threat model confidence for {threat_type}: {current_score:.3f} → {new_score:.3f}")
