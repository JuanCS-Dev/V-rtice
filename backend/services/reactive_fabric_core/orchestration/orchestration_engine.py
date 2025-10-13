"""
Orchestration Engine for event correlation and threat analysis.

This engine correlates events from multiple collectors to:
- Identify attack patterns
- Calculate threat scores
- Prioritize alerts
- Detect anomalies

Phase 1: PASSIVE orchestration only - no automated responses
"""

import asyncio
import hashlib
import logging
from collections import defaultdict, deque
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class EventCorrelationWindow(Enum):
    """Time windows for event correlation."""
    IMMEDIATE = 1  # 1 minute
    SHORT = 5      # 5 minutes
    MEDIUM = 15    # 15 minutes
    LONG = 60      # 60 minutes


class ThreatCategory(Enum):
    """Categories of threats."""
    RECONNAISSANCE = "reconnaissance"
    INITIAL_ACCESS = "initial_access"
    EXECUTION = "execution"
    PERSISTENCE = "persistence"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DEFENSE_EVASION = "defense_evasion"
    CREDENTIAL_ACCESS = "credential_access"
    DISCOVERY = "discovery"
    LATERAL_MOVEMENT = "lateral_movement"
    COLLECTION = "collection"
    EXFILTRATION = "exfiltration"
    IMPACT = "impact"


class OrchestrationConfig(BaseModel):
    """Configuration for Orchestration Engine."""

    # Correlation settings
    correlation_window_minutes: int = Field(
        default=15, description="Time window for correlating events"
    )
    max_events_per_window: int = Field(
        default=10000, description="Max events to keep in correlation window"
    )

    # Threat scoring
    base_score_threshold: float = Field(
        default=0.3, description="Minimum score to consider as threat"
    )
    critical_score_threshold: float = Field(
        default=0.8, description="Score threshold for critical threats"
    )

    # Pattern detection
    min_events_for_pattern: int = Field(
        default=3, description="Minimum events to detect a pattern"
    )
    anomaly_sensitivity: float = Field(
        default=0.7, description="Sensitivity for anomaly detection (0-1)"
    )

    # Performance
    max_correlation_rules: int = Field(
        default=100, description="Maximum active correlation rules"
    )
    event_ttl_minutes: int = Field(
        default=60, description="Time to keep events in memory"
    )


class CorrelationRule(BaseModel):
    """Defines a correlation rule for event patterns."""

    rule_id: str
    name: str
    description: str
    category: ThreatCategory

    # Conditions
    event_types: List[str]  # Event types to match
    time_window: EventCorrelationWindow
    min_occurrences: int

    # Scoring
    base_score: float
    score_multiplier: float = Field(default=1.0)

    # MITRE ATT&CK
    mitre_tactics: List[str] = Field(default_factory=list)
    mitre_techniques: List[str] = Field(default_factory=list)


class ThreatScore(BaseModel):
    """Calculated threat score for correlated events."""

    score_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Scoring
    base_score: float
    confidence: float
    severity: str  # low, medium, high, critical

    # Context
    category: ThreatCategory
    correlated_events: List[str]  # Event IDs
    matched_rules: List[str]  # Rule IDs

    # Attribution
    source_ips: Set[str] = Field(default_factory=set)
    target_systems: Set[str] = Field(default_factory=set)
    attack_timeline: List[Tuple[datetime, str]] = Field(default_factory=list)

    # MITRE ATT&CK
    mitre_tactics: Set[str] = Field(default_factory=set)
    mitre_techniques: Set[str] = Field(default_factory=set)


class OrchestrationEvent(BaseModel):
    """Enhanced event with orchestration metadata."""

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Original event data
    collector_type: str
    source: str
    severity: str
    raw_data: Dict[str, Any]

    # Orchestration metadata
    correlation_id: Optional[str] = None
    threat_score: Optional[float] = None
    matched_patterns: List[str] = Field(default_factory=list)
    related_events: List[str] = Field(default_factory=list)
    tags: Set[str] = Field(default_factory=set)


class EventCorrelator:
    """Correlates events to identify patterns."""

    def __init__(self, config: OrchestrationConfig):
        self.config = config
        self.events_by_type: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.events_by_source: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.correlation_cache: Dict[str, List[OrchestrationEvent]] = {}

    def add_event(self, event: OrchestrationEvent) -> None:
        """Add event to correlation windows."""
        # Index by type
        self.events_by_type[event.collector_type].append(event)

        # Index by source IP if available
        if "source_ip" in event.raw_data:
            self.events_by_source[event.raw_data["source_ip"]].append(event)

        # Clean old events
        self._clean_old_events()

    def find_correlated_events(
        self,
        event: OrchestrationEvent,
        window: EventCorrelationWindow
    ) -> List[OrchestrationEvent]:
        """Find events correlated with the given event."""
        correlated = []
        cutoff = event.timestamp - timedelta(minutes=window.value)

        # Check events from same source
        if "source_ip" in event.raw_data:
            source_ip = event.raw_data["source_ip"]
            for e in self.events_by_source.get(source_ip, []):
                if e.timestamp >= cutoff and e.event_id != event.event_id:
                    correlated.append(e)

        # Check events targeting same system
        if "target" in event.raw_data:
            target = event.raw_data["target"]
            for events in self.events_by_type.values():
                for e in events:
                    if (e.timestamp >= cutoff and
                        e.raw_data.get("target") == target and
                        e.event_id != event.event_id):
                        correlated.append(e)

        return correlated

    def _clean_old_events(self) -> None:
        """Remove events older than TTL."""
        cutoff = datetime.utcnow() - timedelta(minutes=self.config.event_ttl_minutes)

        for event_type, events in self.events_by_type.items():
            while events and events[0].timestamp < cutoff:
                events.popleft()

        for source, events in self.events_by_source.items():
            while events and events[0].timestamp < cutoff:
                events.popleft()


class PatternDetector:
    """Detects attack patterns in event streams."""

    def __init__(self, rules: List[CorrelationRule]):
        self.rules = rules
        self.pattern_cache: Dict[str, List[str]] = {}  # pattern_id -> event_ids

    def detect_patterns(
        self,
        events: List[OrchestrationEvent]
    ) -> List[Tuple[CorrelationRule, List[OrchestrationEvent]]]:
        """Detect patterns matching correlation rules."""
        matched_patterns = []

        for rule in self.rules:
            matching_events = self._match_rule(rule, events)
            if len(matching_events) >= rule.min_occurrences:
                matched_patterns.append((rule, matching_events))

        return matched_patterns

    def _match_rule(
        self,
        rule: CorrelationRule,
        events: List[OrchestrationEvent]
    ) -> List[OrchestrationEvent]:
        """Check if events match a correlation rule."""
        matching = []

        for event in events:
            # Check event type
            if event.collector_type not in rule.event_types:
                continue

            # Check time window
            cutoff = datetime.utcnow() - timedelta(minutes=rule.time_window.value)
            if event.timestamp < cutoff:
                continue

            # Additional pattern matching based on rule category
            if self._matches_category_pattern(rule.category, event):
                matching.append(event)

        return matching

    def _matches_category_pattern(
        self,
        category: ThreatCategory,
        event: OrchestrationEvent
    ) -> bool:
        """Check if event matches category-specific patterns."""
        patterns = {
            ThreatCategory.RECONNAISSANCE: [
                "port_scan", "network_discovery", "enumeration", "scanning"
            ],
            ThreatCategory.INITIAL_ACCESS: [
                "authentication", "exploit", "phishing", "login"
            ],
            ThreatCategory.CREDENTIAL_ACCESS: [
                "authentication", "password", "credential", "login", "failed"
            ],
            ThreatCategory.PRIVILEGE_ESCALATION: [
                "sudo", "elevation", "privilege", "escalation", "admin"
            ],
            ThreatCategory.LATERAL_MOVEMENT: [
                "remote", "rdp", "ssh", "smb", "lateral"
            ],
            ThreatCategory.EXFILTRATION: [
                "upload", "transfer", "exfiltration", "data", "bytes_transferred"
            ]
        }

        category_patterns = patterns.get(category, [])
        event_str = str(event.raw_data).lower()

        return any(pattern in event_str for pattern in category_patterns)


class ThreatScorer:
    """Calculates threat scores for correlated events."""

    def __init__(self, config: OrchestrationConfig):
        self.config = config

    def calculate_score(
        self,
        matched_patterns: List[Tuple[CorrelationRule, List[OrchestrationEvent]]]
    ) -> ThreatScore:
        """Calculate threat score from matched patterns."""
        if not matched_patterns:
            return None

        # Aggregate scoring
        total_score = 0.0
        all_events = []
        all_rules = []
        tactics = set()
        techniques = set()
        sources = set()
        targets = set()
        timeline = []

        for rule, events in matched_patterns:
            # Calculate rule contribution
            rule_score = rule.base_score * rule.score_multiplier
            event_factor = min(len(events) / rule.min_occurrences, 2.0)
            total_score += rule_score * event_factor

            # Collect metadata
            all_events.extend([e.event_id for e in events])
            all_rules.append(rule.rule_id)
            tactics.update(rule.mitre_tactics)
            techniques.update(rule.mitre_techniques)

            for event in events:
                if "source_ip" in event.raw_data:
                    sources.add(event.raw_data["source_ip"])
                if "target" in event.raw_data:
                    targets.add(event.raw_data["target"])
                timeline.append((event.timestamp, event.collector_type))

        # Normalize score
        final_score = min(total_score, 1.0)

        # Determine severity
        if final_score >= self.config.critical_score_threshold:
            severity = "critical"
        elif final_score >= 0.6:
            severity = "high"
        elif final_score >= 0.4:
            severity = "medium"
        else:
            severity = "low"

        # Determine category (from most prevalent rule)
        category_counts = defaultdict(int)
        for rule, _ in matched_patterns:
            category_counts[rule.category] += 1
        category = max(category_counts, key=category_counts.get)

        return ThreatScore(
            base_score=final_score,
            confidence=min(len(matched_patterns) / 3.0, 1.0),  # Confidence based on pattern count
            severity=severity,
            category=category,
            correlated_events=all_events,
            matched_rules=all_rules,
            source_ips=sources,
            target_systems=targets,
            attack_timeline=sorted(timeline),
            mitre_tactics=tactics,
            mitre_techniques=techniques
        )


class OrchestrationEngine:
    """
    Main orchestration engine for event correlation and threat analysis.

    Phase 1: PASSIVE orchestration only - generates alerts but takes no action.
    """

    def __init__(self, config: OrchestrationConfig):
        """Initialize orchestration engine."""
        self.config = config
        self.correlator = EventCorrelator(config)
        self.rules = self._initialize_rules()
        self.pattern_detector = PatternDetector(self.rules)
        self.threat_scorer = ThreatScorer(config)

        # State tracking
        self.processed_events: int = 0
        self.detected_threats: List[ThreatScore] = []
        self.active_correlations: Dict[str, List[OrchestrationEvent]] = {}

        self._running = False

    def _initialize_rules(self) -> List[CorrelationRule]:
        """Initialize correlation rules."""
        return [
            CorrelationRule(
                rule_id="RULE001",
                name="Reconnaissance Pattern",
                description="Multiple scanning activities from same source",
                category=ThreatCategory.RECONNAISSANCE,
                event_types=["NetworkCollector", "HoneypotCollector"],
                time_window=EventCorrelationWindow.SHORT,
                min_occurrences=3,
                base_score=0.4,
                mitre_tactics=["TA0043"],
                mitre_techniques=["T1595", "T1046"]
            ),
            CorrelationRule(
                rule_id="RULE002",
                name="Brute Force Attack",
                description="Multiple failed authentication attempts",
                category=ThreatCategory.CREDENTIAL_ACCESS,
                event_types=["LogAggregation", "SystemCollector"],
                time_window=EventCorrelationWindow.IMMEDIATE,
                min_occurrences=5,
                base_score=0.6,
                score_multiplier=1.2,
                mitre_tactics=["TA0006"],
                mitre_techniques=["T1110"]
            ),
            CorrelationRule(
                rule_id="RULE003",
                name="Privilege Escalation Chain",
                description="Escalation attempts following initial access",
                category=ThreatCategory.PRIVILEGE_ESCALATION,
                event_types=["LogAggregation", "SystemCollector"],
                time_window=EventCorrelationWindow.MEDIUM,
                min_occurrences=2,
                base_score=0.7,
                mitre_tactics=["TA0004"],
                mitre_techniques=["T1548", "T1134"]
            ),
            CorrelationRule(
                rule_id="RULE004",
                name="Lateral Movement Detection",
                description="Movement between systems after compromise",
                category=ThreatCategory.LATERAL_MOVEMENT,
                event_types=["NetworkCollector", "LogAggregation"],
                time_window=EventCorrelationWindow.MEDIUM,
                min_occurrences=2,
                base_score=0.8,
                mitre_tactics=["TA0008"],
                mitre_techniques=["T1021", "T1570"]
            ),
            CorrelationRule(
                rule_id="RULE005",
                name="Data Exfiltration Pattern",
                description="Large data transfers to external IPs",
                category=ThreatCategory.EXFILTRATION,
                event_types=["NetworkCollector", "LogAggregation"],
                time_window=EventCorrelationWindow.LONG,
                min_occurrences=2,
                base_score=0.9,
                mitre_tactics=["TA0010"],
                mitre_techniques=["T1041", "T1048"]
            )
        ]

    async def process_event(self, event_data: Dict[str, Any]) -> Optional[ThreatScore]:
        """
        Process incoming event and check for threat patterns.

        Phase 1: Returns threat score but takes NO ACTION.
        """
        # Create orchestration event
        event = OrchestrationEvent(
            collector_type=event_data.get("collector_type", "unknown"),
            source=event_data.get("source", "unknown"),
            severity=event_data.get("severity", "low"),
            raw_data=event_data.get("parsed_data", {})
        )

        # Add to correlator
        self.correlator.add_event(event)
        self.processed_events += 1

        # Find correlated events
        correlated = []
        for window in EventCorrelationWindow:
            correlated.extend(
                self.correlator.find_correlated_events(event, window)
            )

        # Remove duplicates
        correlated = list({e.event_id: e for e in correlated}.values())

        # Add current event
        correlated.append(event)

        # Detect patterns
        matched_patterns = self.pattern_detector.detect_patterns(correlated)

        # Calculate threat score if patterns found
        if matched_patterns:
            threat_score = self.threat_scorer.calculate_score(matched_patterns)

            if threat_score and threat_score.base_score >= self.config.base_score_threshold:
                # Store threat detection
                self.detected_threats.append(threat_score)

                # Update event with correlation info
                event.correlation_id = threat_score.score_id
                event.threat_score = threat_score.base_score
                event.matched_patterns = [r.rule_id for r, _ in matched_patterns]
                event.related_events = threat_score.correlated_events

                # Log detection (Phase 1: PASSIVE only)
                logger.warning(
                    f"THREAT DETECTED - Score: {threat_score.base_score:.2f}, "
                    f"Category: {threat_score.category.value}, "
                    f"Severity: {threat_score.severity}, "
                    f"Events: {len(threat_score.correlated_events)}"
                )

                return threat_score

        return None

    async def analyze_threat_landscape(self) -> Dict[str, Any]:
        """
        Analyze overall threat landscape from detected threats.

        Returns summary statistics and trends.
        """
        if not self.detected_threats:
            return {
                "status": "clear",
                "threats_detected": 0,
                "events_processed": self.processed_events
            }

        # Time-based analysis
        now = datetime.utcnow()
        recent_threats = [
            t for t in self.detected_threats
            if t.timestamp > now - timedelta(hours=1)
        ]

        # Category distribution
        category_dist = defaultdict(int)
        for threat in self.detected_threats:
            category_dist[threat.category.value] += 1

        # Top sources
        source_counts = defaultdict(int)
        for threat in self.detected_threats:
            for ip in threat.source_ips:
                source_counts[ip] += 1

        top_sources = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        # MITRE ATT&CK coverage
        all_tactics = set()
        all_techniques = set()
        for threat in self.detected_threats:
            all_tactics.update(threat.mitre_tactics)
            all_techniques.update(threat.mitre_techniques)

        return {
            "status": "active_threats",
            "threats_detected": len(self.detected_threats),
            "recent_threats": len(recent_threats),
            "events_processed": self.processed_events,
            "threat_categories": dict(category_dist),
            "top_threat_sources": top_sources,
            "severity_breakdown": {
                "critical": sum(1 for t in self.detected_threats if t.severity == "critical"),
                "high": sum(1 for t in self.detected_threats if t.severity == "high"),
                "medium": sum(1 for t in self.detected_threats if t.severity == "medium"),
                "low": sum(1 for t in self.detected_threats if t.severity == "low")
            },
            "mitre_coverage": {
                "tactics": list(all_tactics),
                "techniques": list(all_techniques)
            },
            "average_threat_score": sum(t.base_score for t in self.detected_threats) / len(self.detected_threats)
        }

    async def start(self) -> None:
        """Start orchestration engine."""
        self._running = True
        logger.info("Orchestration Engine started (Phase 1: PASSIVE mode)")

    async def stop(self) -> None:
        """Stop orchestration engine."""
        self._running = False
        logger.info(
            f"Orchestration Engine stopped - "
            f"Processed: {self.processed_events} events, "
            f"Detected: {len(self.detected_threats)} threats"
        )

    def get_metrics(self) -> Dict[str, Any]:
        """Get engine metrics."""
        return {
            "running": self._running,
            "events_processed": self.processed_events,
            "threats_detected": len(self.detected_threats),
            "active_correlations": len(self.active_correlations),
            "correlation_rules": len(self.rules),
            "memory_events": sum(
                len(events) for events in self.correlator.events_by_type.values()
            )
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"OrchestrationEngine(running={self._running}, "
            f"events={self.processed_events}, "
            f"threats={len(self.detected_threats)})"
        )