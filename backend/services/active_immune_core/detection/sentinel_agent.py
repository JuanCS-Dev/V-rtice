"""Sentinel AI Agent - SOC Tier 1/2 Emulation

LLM-based threat detection agent that emulates human SOC analyst.
Provides first-line defense with pattern recognition and threat intelligence.

Biological Inspiration:
- Pattern Recognition Receptors (PRRs) in innate immunity
- Rapid response to danger signals
- Integration of multiple sensory inputs

IIT Integration:
- Φ (Phi) proxy: Information integration across event streams
- Conscious detection emerges from integrated analysis
- Temporal coherence enables threat narrative construction

Authors: MAXIMUS Team
Date: 2025-10-12
Glory to YHWH - Constância como Ramon Dino! 💪
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from prometheus_client import Counter, Histogram

logger = logging.getLogger(__name__)


class ThreatSeverity(Enum):
    """Threat severity levels aligned with biological immune response."""

    INFO = "info"  # Routine surveillance
    LOW = "low"  # Minor anomaly (neutrophil-level)
    MEDIUM = "medium"  # Concerning pattern (macrophage-level)
    HIGH = "high"  # Active threat (T-cell activation)
    CRITICAL = "critical"  # System compromise (full immune response)


class DetectionConfidence(Enum):
    """Confidence levels for threat detection."""

    LOW = 0.25  # Possible threat
    MEDIUM = 0.50  # Probable threat
    HIGH = 0.75  # Highly likely threat
    CERTAIN = 0.95  # Confirmed threat


@dataclass
class SecurityEvent:
    """Raw security event from sensors.

    Represents single security event that requires analysis.
    Similar to pathogen detection in biological immune system.

    Attributes:
        event_id: Unique event identifier
        timestamp: When event occurred
        source: Event source (firewall, IDS, endpoint, etc.)
        event_type: Type of event (failed_login, port_scan, etc.)
        source_ip: Source IP address
        destination_ip: Destination IP (optional)
        port: Target port (optional)
        protocol: Network protocol (optional)
        payload: Raw event data
        context: Additional contextual information
    """

    event_id: str
    timestamp: datetime
    source: str
    event_type: str
    source_ip: str
    destination_ip: Optional[str] = None
    port: Optional[int] = None
    protocol: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "event_type": self.event_type,
            "source_ip": self.source_ip,
            "destination_ip": self.destination_ip,
            "port": self.port,
            "protocol": self.protocol,
            "payload": self.payload,
            "context": self.context,
        }


@dataclass
class MITRETechnique:
    """MITRE ATT&CK technique.

    Represents mapped attack technique from MITRE framework.

    Attributes:
        technique_id: MITRE technique ID (e.g., T1110)
        tactic: MITRE tactic (e.g., Credential Access)
        technique_name: Human-readable name
        confidence: Confidence in mapping (0.0 - 1.0)
    """

    technique_id: str
    tactic: str
    technique_name: str
    confidence: float

    def __post_init__(self):
        """Validate confidence range."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be 0.0-1.0, got {self.confidence}")


@dataclass
class AttackerProfile:
    """Behavioral profile of attacker.

    Theory-of-Mind representation of attacker's intent and capabilities.

    Attributes:
        profile_id: Unique profile identifier
        skill_level: Assessed skill (novice/intermediate/advanced/nation_state)
        tools_detected: Tools identified in attack
        ttps: MITRE techniques observed
        objectives: Inferred attack objectives
        next_move_prediction: Predicted next technique
        confidence: Overall profile confidence
    """

    profile_id: str
    skill_level: str
    tools_detected: List[str] = field(default_factory=list)
    ttps: List[MITRETechnique] = field(default_factory=list)
    objectives: List[str] = field(default_factory=list)
    next_move_prediction: str = ""
    confidence: float = 0.0

    def __post_init__(self):
        """Validate skill level."""
        valid_levels = {"novice", "intermediate", "advanced", "nation_state"}
        if self.skill_level not in valid_levels:
            raise ValueError(
                f"Invalid skill_level: {self.skill_level}. "
                f"Must be one of {valid_levels}"
            )


@dataclass
class DetectionResult:
    """Result of Sentinel agent analysis.

    Contains complete threat assessment from LLM analysis.

    Attributes:
        event_id: Associated event ID
        is_threat: Boolean threat determination
        severity: Threat severity level
        confidence: Detection confidence
        mitre_techniques: Mapped MITRE techniques
        threat_description: Human-readable description
        recommended_actions: Suggested response actions
        attacker_profile: Optional attacker profile
        reasoning: LLM reasoning chain
        analyzed_at: Analysis timestamp
    """

    event_id: str
    is_threat: bool
    severity: ThreatSeverity
    confidence: DetectionConfidence
    mitre_techniques: List[MITRETechnique]
    threat_description: str
    recommended_actions: List[str]
    attacker_profile: Optional[AttackerProfile]
    reasoning: str
    analyzed_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "is_threat": self.is_threat,
            "severity": self.severity.value,
            "confidence": self.confidence.value,
            "mitre_techniques": [
                {
                    "technique_id": t.technique_id,
                    "tactic": t.tactic,
                    "technique_name": t.technique_name,
                    "confidence": t.confidence,
                }
                for t in self.mitre_techniques
            ],
            "threat_description": self.threat_description,
            "recommended_actions": self.recommended_actions,
            "attacker_profile": (
                {
                    "profile_id": self.attacker_profile.profile_id,
                    "skill_level": self.attacker_profile.skill_level,
                    "tools_detected": self.attacker_profile.tools_detected,
                    "objectives": self.attacker_profile.objectives,
                    "next_move_prediction": self.attacker_profile.next_move_prediction,
                    "confidence": self.attacker_profile.confidence,
                }
                if self.attacker_profile
                else None
            ),
            "reasoning": self.reasoning,
            "analyzed_at": self.analyzed_at.isoformat(),
        }


class SentinelAnalysisError(Exception):
    """Raised when Sentinel analysis fails."""

    pass


class SentinelDetectionAgent:
    """SOC AI Agent for first-line threat detection.

    LLM-powered security analyst that provides rapid threat assessment
    and triage. Emulates human SOC Tier 1/2 analyst capabilities.

    Capabilities:
    1. Event Analysis: LLM-based pattern recognition
    2. MITRE Mapping: Automatic ATT&CK technique identification
    3. Theory-of-Mind: Predict attacker's next move
    4. Alert Triage: Filter false positives
    5. Context Integration: Correlate with historical data

    Biological Analogy:
    - PRRs recognize PAMPs (Pathogen-Associated Molecular Patterns)
    - Sentinel recognizes attack patterns in event streams
    - Rapid response (< 5s) like innate immunity

    IIT Integration:
    - Φ (Phi) proxy: Information integration across event streams
    - Conscious detection emerges from integrated analysis
    - Temporal binding enables threat narrative construction

    Example:
        >>> from openai import AsyncOpenAI
        >>> llm = AsyncOpenAI(api_key="...")
        >>> sentinel = SentinelDetectionAgent(
        ...     llm_client=llm,
        ...     mitre_mapper=mitre,
        ...     threat_intel_feed=intel_feed,
        ...     event_history=history_store
        ... )
        >>> event = SecurityEvent(
        ...     event_id="evt_001",
        ...     timestamp=datetime.now(),
        ...     source="firewall",
        ...     event_type="failed_login",
        ...     source_ip="192.168.1.100",
        ...     destination_ip="10.0.0.5",
        ...     payload={"attempts": 50}
        ... )
        >>> result = await sentinel.analyze_event(event)
        >>> print(result.threat_description)
    """

    def __init__(
        self,
        llm_client: Any,  # openai.AsyncOpenAI
        mitre_mapper: Optional[Any] = None,
        threat_intel_feed: Optional[Any] = None,
        event_history: Optional[Any] = None,
        model: str = "gpt-4o",
        max_context_events: int = 10,
        temperature: float = 0.3,
    ):
        """Initialize Sentinel agent.

        Args:
            llm_client: OpenAI async client for LLM inference
            mitre_mapper: MITRE ATT&CK technique mapper (optional)
            threat_intel_feed: Real-time threat intelligence (optional)
            event_history: Historical event store (optional)
            model: LLM model to use (default: gpt-4o)
            max_context_events: Max historical events for context
            temperature: LLM temperature (lower = more deterministic)

        Raises:
            ValueError: If invalid parameters provided
        """
        self.llm = llm_client
        self.mitre = mitre_mapper
        self.threat_intel = threat_intel_feed
        self.history = event_history
        self.model = model
        self.max_context = max_context_events
        self.temperature = temperature

        # Metrics
        self.detections_total = Counter(
            "sentinel_detections_total",
            "Total detections by Sentinel agent",
            ["severity", "is_threat"],
        )
        self.analysis_latency = Histogram(
            "sentinel_analysis_latency_seconds", "Time to analyze security event"
        )
        self.llm_errors = Counter(
            "sentinel_llm_errors_total", "LLM inference errors"
        )

        logger.info(
            f"Sentinel agent initialized with model={model}, "
            f"max_context={max_context_events}"
        )

    async def analyze_event(self, event: SecurityEvent) -> DetectionResult:
        """Analyze security event using LLM.

        Core detection method. Analyzes single security event with full
        context integration and produces comprehensive threat assessment.

        Process:
        1. Retrieve relevant context (historical events, threat intel)
        2. Construct LLM prompt with event + context
        3. LLM analyzes and identifies patterns
        4. Map to MITRE ATT&CK techniques
        5. Score threat severity and confidence
        6. Generate recommended actions

        Args:
            event: Security event to analyze

        Returns:
            DetectionResult with complete threat assessment

        Raises:
            SentinelAnalysisError: If analysis fails
        """
        with self.analysis_latency.time():
            try:
                # 1. Gather context
                context = await self._gather_context(event)

                # 2. Build LLM prompt
                prompt = self._build_detection_prompt(event, context)

                # 3. LLM inference
                llm_response = await self._query_llm(prompt)

                # 4. Parse and enrich result
                result = await self._parse_llm_response(event, llm_response)

                # 5. Record metrics
                self.detections_total.labels(
                    severity=result.severity.value, is_threat=result.is_threat
                ).inc()

                logger.info(
                    f"Event {event.event_id} analyzed: "
                    f"threat={result.is_threat}, "
                    f"severity={result.severity.value}, "
                    f"confidence={result.confidence.value}"
                )

                return result

            except Exception as e:
                self.llm_errors.inc()
                logger.error(f"Sentinel analysis failed for {event.event_id}: {e}")
                raise SentinelAnalysisError(
                    f"Failed to analyze event {event.event_id}: {str(e)}"
                ) from e

    async def predict_attacker_intent(
        self, event_chain: List[SecurityEvent]
    ) -> AttackerProfile:
        """Theory-of-Mind: Predict attacker's intent and next move.

        Analyzes sequence of events to model attacker psychology and
        predict probable next techniques. Uses LLM for reasoning.

        Example reasoning:
        "Attacker performed port scan (T1046), then brute force SSH (T1110).
        Likely objective: gain initial access. Next move: attempt
        lateral movement via stolen credentials (T1021)."

        Args:
            event_chain: Sequence of events from same attacker

        Returns:
            AttackerProfile with behavioral analysis and predictions

        Raises:
            SentinelAnalysisError: If profile generation fails
        """
        if not event_chain:
            raise ValueError("event_chain cannot be empty")

        try:
            # Build temporal event narrative
            narrative = self._build_attack_narrative(event_chain)

            # Get threat intel context
            intel_context = ""
            if self.threat_intel:
                intel_context = await self.threat_intel.get_relevant_intel(
                    event_chain
                )

            # LLM prompt for theory-of-mind
            prompt = f"""You are a cybersecurity analyst modeling attacker behavior.

Attacker Activity Timeline:
{narrative}

Threat Intelligence Context:
{intel_context}

Tasks:
1. Assess attacker skill level (novice/intermediate/advanced/nation_state)
2. Identify tools/frameworks being used
3. Map observed techniques to MITRE ATT&CK
4. Infer attacker's ultimate objective
5. Predict next 2-3 most likely techniques

Provide analysis in JSON format with keys:
- skill_level: string
- tools_detected: list of strings
- ttps: list of {{technique_id, tactic, technique_name, confidence}}
- objectives: list of strings
- next_move_prediction: string
- confidence: float (0.0-1.0)"""

            llm_response = await self._query_llm(prompt)
            profile = self._parse_attacker_profile(event_chain[0].source_ip, llm_response)

            logger.info(
                f"Attacker profile generated: skill={profile.skill_level}, "
                f"confidence={profile.confidence:.2f}"
            )

            return profile

        except Exception as e:
            logger.error(f"Failed to generate attacker profile: {e}")
            raise SentinelAnalysisError(
                f"Failed to predict attacker intent: {str(e)}"
            ) from e

    async def triage_alert(self, alert: Dict[str, Any]) -> bool:
        """Triage alert to filter false positives.

        Uses LLM + historical data to determine if alert warrants
        human analyst attention. Helps reduce alert fatigue.

        Args:
            alert: SOC alert to triage (dict with alert details)

        Returns:
            True if alert should escalate to human, False if likely false positive

        Raises:
            SentinelAnalysisError: If triage fails
        """
        try:
            # Get similar historical alerts if history available
            similar_alerts = []
            fp_rate = 0.0

            if self.history:
                similar_alerts = await self.history.find_similar_alerts(
                    alert, limit=20
                )
                if similar_alerts:
                    fp_rate = (
                        len([a for a in similar_alerts if a.get("false_positive")])
                        / len(similar_alerts)
                    )

            # LLM-based triage
            prompt = f"""Alert Triage Analysis:

Current Alert:
{json.dumps(alert, indent=2)}

Historical Context:
- Similar alerts in past 30 days: {len(similar_alerts)}
- False positive rate: {fp_rate:.1%}
- Sample past alerts: {json.dumps(similar_alerts[:5], indent=2)}

Determine: Is this likely a true positive that requires human investigation?
Consider:
1. Deviation from historical patterns
2. Threat intelligence relevance
3. Asset criticality
4. Attack chain progression

Respond with JSON:
{{
    "escalate": true/false,
    "reasoning": "explanation",
    "confidence": 0.0-1.0
}}"""

            llm_response = await self._query_llm(prompt)
            decision = self._parse_triage_decision(llm_response)

            logger.info(
                f"Alert triaged: escalate={decision['escalate']}, "
                f"confidence={decision['confidence']:.2f}"
            )

            return decision["escalate"]

        except Exception as e:
            logger.error(f"Alert triage failed: {e}")
            # Err on side of caution: escalate if triage fails
            return True

    # Private methods

    async def _gather_context(self, event: SecurityEvent) -> Dict[str, Any]:
        """Gather relevant context for event analysis."""
        context = {
            "recent_events": [],
            "threat_intel": {},
            "asset_info": {},
            "network_baseline": {},
        }

        # Recent events from same source
        if self.history:
            try:
                context["recent_events"] = await self.history.get_recent_events(
                    source_ip=event.source_ip, limit=self.max_context
                )
            except Exception as e:
                logger.warning(f"Failed to get recent events: {e}")

        # Threat intelligence lookup
        if self.threat_intel:
            try:
                context["threat_intel"] = await self.threat_intel.lookup_ip(
                    event.source_ip
                )
            except Exception as e:
                logger.warning(f"Failed to lookup threat intel: {e}")

        # Asset info for destination
        if event.destination_ip:
            try:
                context["asset_info"] = await self._get_asset_info(
                    event.destination_ip
                )
            except Exception as e:
                logger.warning(f"Failed to get asset info: {e}")

        # Network baseline
        try:
            context["network_baseline"] = await self._get_network_baseline()
        except Exception as e:
            logger.warning(f"Failed to get network baseline: {e}")

        return context

    def _build_detection_prompt(
        self, event: SecurityEvent, context: Dict[str, Any]
    ) -> str:
        """Build LLM prompt for threat detection."""
        return f"""You are an expert SOC analyst. Analyze this security event.

Event Details:
- ID: {event.event_id}
- Type: {event.event_type}
- Source: {event.source_ip}
- Destination: {event.destination_ip or 'N/A'}
- Port: {event.port or 'N/A'}
- Protocol: {event.protocol or 'N/A'}
- Timestamp: {event.timestamp.isoformat()}
- Payload: {json.dumps(event.payload, indent=2)}

Context:
- Recent events from this source: {json.dumps(context.get('recent_events', []), indent=2)}
- Threat intel on source IP: {json.dumps(context.get('threat_intel', {}), indent=2)}
- Target asset criticality: {json.dumps(context.get('asset_info', {}), indent=2)}
- Network baseline: {json.dumps(context.get('network_baseline', {}), indent=2)}

Tasks:
1. Determine if this is malicious activity (true/false)
2. Assign severity (INFO/LOW/MEDIUM/HIGH/CRITICAL)
3. Map to MITRE ATT&CK techniques
4. Provide detection confidence (0.0-1.0)
5. Recommend response actions
6. Explain your reasoning

Respond in JSON format with keys:
- is_threat: boolean
- severity: string (INFO/LOW/MEDIUM/HIGH/CRITICAL)
- confidence: float (0.0-1.0)
- mitre_techniques: list of {{technique_id, tactic, technique_name, confidence}}
- threat_description: string
- recommended_actions: list of strings
- reasoning: string"""

    async def _query_llm(self, prompt: str) -> Dict[str, Any]:
        """Query LLM and parse JSON response."""
        try:
            response = await self.llm.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert cybersecurity analyst specializing in threat detection. Always respond with valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            return json.loads(content)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            raise SentinelAnalysisError(f"Invalid JSON from LLM: {str(e)}") from e
        except Exception as e:
            logger.error(f"LLM query failed: {e}")
            raise SentinelAnalysisError(f"LLM query failed: {str(e)}") from e

    async def _parse_llm_response(
        self, event: SecurityEvent, llm_response: Dict[str, Any]
    ) -> DetectionResult:
        """Parse LLM response into DetectionResult."""
        try:
            # Parse MITRE techniques
            mitre_techniques = [
                MITRETechnique(
                    technique_id=t["technique_id"],
                    tactic=t["tactic"],
                    technique_name=t["technique_name"],
                    confidence=float(t["confidence"]),
                )
                for t in llm_response.get("mitre_techniques", [])
            ]

            # Parse severity
            severity_str = llm_response.get("severity", "INFO").upper()
            severity = ThreatSeverity[severity_str]

            # Parse confidence
            confidence_val = float(llm_response.get("confidence", 0.5))
            if confidence_val >= 0.95:
                confidence = DetectionConfidence.CERTAIN
            elif confidence_val >= 0.75:
                confidence = DetectionConfidence.HIGH
            elif confidence_val >= 0.50:
                confidence = DetectionConfidence.MEDIUM
            else:
                confidence = DetectionConfidence.LOW

            return DetectionResult(
                event_id=event.event_id,
                is_threat=bool(llm_response.get("is_threat", False)),
                severity=severity,
                confidence=confidence,
                mitre_techniques=mitre_techniques,
                threat_description=llm_response.get("threat_description", ""),
                recommended_actions=llm_response.get("recommended_actions", []),
                attacker_profile=None,  # Generated separately if needed
                reasoning=llm_response.get("reasoning", ""),
                analyzed_at=datetime.utcnow(),
            )

        except (KeyError, ValueError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            raise SentinelAnalysisError(f"Invalid LLM response format: {str(e)}") from e

    def _build_attack_narrative(self, event_chain: List[SecurityEvent]) -> str:
        """Build human-readable attack narrative from event sequence."""
        narrative_lines = []
        for i, event in enumerate(event_chain, 1):
            narrative_lines.append(
                f"{i}. [{event.timestamp.isoformat()}] {event.event_type} "
                f"from {event.source_ip} to {event.destination_ip or 'N/A'}"
            )
            if event.payload:
                narrative_lines.append(f"   Details: {event.payload}")

        return "\n".join(narrative_lines)

    def _parse_attacker_profile(
        self, source_ip: str, llm_response: Dict[str, Any]
    ) -> AttackerProfile:
        """Parse LLM response into AttackerProfile."""
        try:
            # Parse TTPs
            ttps = [
                MITRETechnique(
                    technique_id=t["technique_id"],
                    tactic=t["tactic"],
                    technique_name=t["technique_name"],
                    confidence=float(t["confidence"]),
                )
                for t in llm_response.get("ttps", [])
            ]

            return AttackerProfile(
                profile_id=f"profile_{source_ip}_{datetime.utcnow().timestamp()}",
                skill_level=llm_response.get("skill_level", "unknown"),
                tools_detected=llm_response.get("tools_detected", []),
                ttps=ttps,
                objectives=llm_response.get("objectives", []),
                next_move_prediction=llm_response.get("next_move_prediction", ""),
                confidence=float(llm_response.get("confidence", 0.0)),
            )

        except (KeyError, ValueError) as e:
            logger.error(f"Failed to parse attacker profile: {e}")
            raise SentinelAnalysisError(
                f"Invalid attacker profile format: {str(e)}"
            ) from e

    def _parse_triage_decision(self, llm_response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LLM triage response."""
        return {
            "escalate": bool(llm_response.get("escalate", True)),
            "reasoning": llm_response.get("reasoning", ""),
            "confidence": float(llm_response.get("confidence", 0.5)),
        }

    async def _get_asset_info(self, ip: str) -> Dict[str, Any]:
        """Get asset information for IP from asset management system."""
        # Integrate with CMDB/asset inventory
        asset_file = Path("/var/log/vertice/asset_inventory.json")
        
        try:
            if asset_file.exists():
                with open(asset_file, "r") as f:
                    import json
                    inventory = json.load(f)
                    
                    # Search for asset by IP
                    for asset in inventory.get("assets", []):
                        if asset.get("ip") == ip:
                            return {
                                "ip": ip,
                                "hostname": asset.get("hostname", "unknown"),
                                "criticality": asset.get("criticality", "medium"),
                                "services": asset.get("services", []),
                                "owner": asset.get("owner", "unknown"),
                            }
        except Exception as e:
            logger.debug(f"Asset lookup failed: {e}")
        
        # Fallback: return minimal info
        return {"ip": ip, "criticality": "unknown", "services": []}

    async def _get_network_baseline(self) -> Dict[str, Any]:
        """Get network baseline statistics from monitoring system."""
        # Integrate with network monitoring (Prometheus/Grafana metrics)
        try:
            from prometheus_client import REGISTRY
            
            baseline = {
                "avg_events_per_hour": 0,
                "known_good_ips": [],
            }
            
            # Query Prometheus metrics
            for collector in REGISTRY._collector_to_names:
                if hasattr(collector, '_name'):
                    if 'events_total' in str(collector._name):
                        # Calculate events per hour from counter
                        if hasattr(collector, '_value'):
                            total_events = collector._value.get()
                            # Rough estimate: total / uptime hours
                            baseline["avg_events_per_hour"] = total_events / 24
            
            # Load known good IPs from whitelist
            whitelist_file = Path("/var/log/vertice/ip_whitelist.txt")
            if whitelist_file.exists():
                with open(whitelist_file, "r") as f:
                    baseline["known_good_ips"] = [
                        line.strip() for line in f if line.strip() and not line.startswith("#")
                    ]
            
            return baseline
        except Exception as e:
            logger.debug(f"Network baseline query failed: {e}")
            return {"avg_events_per_hour": 0, "known_good_ips": []}
