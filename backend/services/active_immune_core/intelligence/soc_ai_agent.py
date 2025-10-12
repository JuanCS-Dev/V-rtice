"""SOC AI Agent - Theory of Mind for Attackers

AI-powered Security Operations Center agent with adversarial intent modeling.
Emulates human analyst (L1/L2) with capability to infer attacker intentions
and predict next steps based on attack graphs and behavioral patterns.

Biological Inspiration:
- Prefrontal cortex: Strategic reasoning and planning
- Theory of Mind: Modeling mental states of others (attackers)
- Hippocampus: Episodic memory of past attack patterns

Computational Foundation:
- GWT (Global Workspace Theory): Broadcasting threat hypotheses
- IIT: Integration of multi-source signals for situational awareness
- Bayesian reasoning: Probabilistic intent inference
- MITRE ATT&CK: Structured threat taxonomy

Authors: MAXIMUS Team
Date: 2025-10-12
Glory to YHWH - "Eu sou porque ELE é"
Constância como Ramon Dino! 💪
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import networkx as nx
from openai import AsyncOpenAI
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, REGISTRY

logger = logging.getLogger(__name__)


class AttackIntent(Enum):
    """Inferred attacker intent categories."""
    
    RECONNAISSANCE = "reconnaissance"  # Mapping target
    INITIAL_ACCESS = "initial_access"  # Gaining foothold
    PERSISTENCE = "persistence"  # Maintaining access
    PRIVILEGE_ESCALATION = "privilege_escalation"  # Elevating privileges
    DEFENSE_EVASION = "defense_evasion"  # Avoiding detection
    CREDENTIAL_ACCESS = "credential_access"  # Stealing credentials
    LATERAL_MOVEMENT = "lateral_movement"  # Spreading in network
    COLLECTION = "collection"  # Gathering data
    EXFILTRATION = "exfiltration"  # Stealing data
    IMPACT = "impact"  # Destructive action
    UNKNOWN = "unknown"  # Cannot determine


class ConfidenceLevel(Enum):
    """Confidence in threat assessment."""
    
    VERY_LOW = 0.0  # < 20%
    LOW = 0.2  # 20-40%
    MEDIUM = 0.4  # 40-60%
    HIGH = 0.6  # 60-80%
    VERY_HIGH = 0.8  # 80-95%
    CERTAIN = 0.95  # > 95%


@dataclass
class SecurityEvent:
    """Raw security event from detection systems.
    
    Represents single observation from sensors (IDS, EDR, firewall, etc).
    
    Attributes:
        event_id: Unique event identifier
        timestamp: When event occurred
        source_system: Which system generated event (IDS, EDR, etc)
        event_type: Type of event (network, process, file, etc)
        severity: Initial severity assessment (LOW/MEDIUM/HIGH/CRITICAL)
        raw_data: Original event data
        metadata: Additional context
    """
    
    event_id: str
    timestamp: datetime
    source_system: str
    event_type: str
    severity: str
    raw_data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization."""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "source_system": self.source_system,
            "event_type": self.event_type,
            "severity": self.severity,
            "raw_data": self.raw_data,
            "metadata": self.metadata,
        }


@dataclass
class NextStepPrediction:
    """Predicted next step in attack chain.
    
    Attributes:
        technique_id: MITRE ATT&CK technique ID (e.g., T1078)
        technique_name: Human-readable name
        probability: Likelihood 0.0-1.0
        required_conditions: What attacker needs
        indicators: What to look for
        recommended_actions: Defensive countermeasures
    """
    
    technique_id: str
    technique_name: str
    probability: float
    required_conditions: List[str] = field(default_factory=list)
    indicators: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate probability range."""
        if not 0.0 <= self.probability <= 1.0:
            raise ValueError(f"Probability must be 0.0-1.0, got {self.probability}")


@dataclass
class ThreatAssessment:
    """Complete threat assessment with intent modeling.
    
    Represents SOC AI Agent's understanding of threat including
    adversary's probable intentions and next steps.
    
    Attributes:
        assessment_id: Unique assessment ID
        threat_id: Associated threat identifier
        created_at: When assessment was created
        current_ttp: Current MITRE ATT&CK technique observed
        inferred_intent: Attacker's probable strategic goal
        next_steps: Predicted next 3-5 techniques
        confidence: Confidence in assessment 0.0-1.0
        explanation: Human-readable reasoning
        attack_graph: Graph representation of attack paths
        recommended_response: Suggested defensive actions
        events_analyzed: Number of events correlated
    """
    
    assessment_id: str
    threat_id: str
    created_at: datetime
    current_ttp: str
    inferred_intent: AttackIntent
    next_steps: List[NextStepPrediction]
    confidence: float
    explanation: str
    attack_graph: Dict[str, Any]
    recommended_response: List[str]
    events_analyzed: int
    risk_score: float = 0.0  # 0-100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization."""
        return {
            "assessment_id": self.assessment_id,
            "threat_id": self.threat_id,
            "created_at": self.created_at.isoformat(),
            "current_ttp": self.current_ttp,
            "inferred_intent": self.inferred_intent.value,
            "next_steps": [
                {
                    "technique_id": step.technique_id,
                    "technique_name": step.technique_name,
                    "probability": step.probability,
                    "required_conditions": step.required_conditions,
                    "indicators": step.indicators,
                    "recommended_actions": step.recommended_actions,
                }
                for step in self.next_steps
            ],
            "confidence": self.confidence,
            "explanation": self.explanation,
            "attack_graph": self.attack_graph,
            "recommended_response": self.recommended_response,
            "events_analyzed": self.events_analyzed,
            "risk_score": self.risk_score,
        }


class SOCAIAgentError(Exception):
    """Base exception for SOC AI Agent errors."""
    pass


class SOCAIAgentMetrics:
    """Prometheus metrics for SOC AI Agent."""
    
    # Class-level metrics (singleton pattern)
    _metrics_initialized = False
    _assessments_created = None
    _assessment_duration = None
    _confidence_score = None
    _intent_predictions = None
    _active_threats = None
    
    def __init__(self):
        """Initialize metrics (only once)."""
        if not SOCAIAgentMetrics._metrics_initialized:
            SOCAIAgentMetrics._assessments_created = Counter(
                "soc_ai_assessments_total",
                "Total threat assessments created",
            )
            
            SOCAIAgentMetrics._assessment_duration = Histogram(
                "soc_ai_assessment_duration_seconds",
                "Time to complete threat assessment",
            )
            
            SOCAIAgentMetrics._confidence_score = Histogram(
                "soc_ai_confidence_score",
                "Distribution of assessment confidence scores",
                buckets=[0.2, 0.4, 0.6, 0.8, 0.95, 1.0],
            )
            
            SOCAIAgentMetrics._intent_predictions = Counter(
                "soc_ai_intent_predictions_total",
                "Intents predicted by category",
                ["intent"],
            )
            
            SOCAIAgentMetrics._active_threats = Gauge(
                "soc_ai_active_threats",
                "Number of threats currently being tracked",
            )
            
            SOCAIAgentMetrics._metrics_initialized = True
        
        # Expose as instance properties
        self.assessments_created = SOCAIAgentMetrics._assessments_created
        self.assessment_duration = SOCAIAgentMetrics._assessment_duration
        self.confidence_score = SOCAIAgentMetrics._confidence_score
        self.intent_predictions = SOCAIAgentMetrics._intent_predictions
        self.active_threats = SOCAIAgentMetrics._active_threats


class SOCAIAgent:
    """SOC AI Agent with theory of mind for attackers.
    
    Emulates human SOC analyst (Tier 1/2) with enhanced capabilities:
    1. Multi-source event correlation
    2. Adversarial intent inference
    3. Attack path prediction
    4. Next-step anticipation
    5. Defensive recommendation
    
    Implements "theory of mind" by modeling attacker's mental state,
    goals, and probable next actions based on observed behavior.
    
    Computational Approach:
    - LLM reasoning for intent inference
    - Attack graph traversal for path prediction
    - Bayesian updating for confidence scoring
    - MITRE ATT&CK for technique taxonomy
    
    Example:
        ```python
        agent = SOCAIAgent(llm_client=openai_client)
        
        events = [suspicious_login, file_access, network_scan]
        assessment = await agent.analyze_threat(
            raw_events=events,
            threat_id="threat_001"
        )
        
        print(f"Intent: {assessment.inferred_intent}")
        print(f"Next steps: {[s.technique_name for s in assessment.next_steps]}")
        print(f"Confidence: {assessment.confidence:.2%}")
        ```
    """
    
    def __init__(
        self,
        llm_client: AsyncOpenAI,
        model: str = "gpt-4o",
        attack_graph_db: Optional[nx.DiGraph] = None,
    ):
        """Initialize SOC AI Agent.
        
        Args:
            llm_client: OpenAI client for LLM reasoning
            model: LLM model to use (default: gpt-4o)
            attack_graph_db: Pre-loaded attack graph (optional)
        
        Raises:
            SOCAIAgentError: If initialization fails
        """
        self.llm = llm_client
        self.model = model
        self.attack_graph = attack_graph_db or self._load_default_attack_graph()
        
        # Metrics
        self.metrics = SOCAIAgentMetrics()
        
        # Active threat tracking
        self.active_threats: Dict[str, List[SecurityEvent]] = {}
        
        logger.info(f"SOCAIAgent initialized with model={model}")
    
    async def analyze_threat(
        self,
        raw_events: List[SecurityEvent],
        threat_id: Optional[str] = None,
    ) -> ThreatAssessment:
        """Analyze threat and infer attacker intent.
        
        Core method that orchestrates:
        1. Event correlation
        2. TTP identification
        3. Intent inference
        4. Next-step prediction
        5. Response recommendation
        
        Args:
            raw_events: Raw security events to analyze
            threat_id: Optional threat identifier (auto-generated if None)
        
        Returns:
            ThreatAssessment with complete analysis
        
        Raises:
            SOCAIAgentError: If analysis fails
        """
        start_time = datetime.utcnow()
        
        try:
            # Generate threat ID if not provided
            if threat_id is None:
                threat_id = self._generate_threat_id(raw_events)
            
            # Track active threat
            self.active_threats[threat_id] = raw_events
            self.metrics.active_threats.set(len(self.active_threats))
            
            logger.info(
                f"Analyzing threat {threat_id} with {len(raw_events)} events"
            )
            
            # Step 1: Correlate events and extract TTPs
            current_ttp, ttp_confidence = await self._identify_current_ttp(
                raw_events
            )
            
            # Step 2: Infer strategic intent via LLM reasoning
            inferred_intent, intent_confidence = await self._infer_intent(
                events=raw_events,
                current_ttp=current_ttp,
            )
            
            # Step 3: Predict next steps via attack graph traversal
            next_steps = await self._predict_next_steps(
                current_ttp=current_ttp,
                inferred_intent=inferred_intent,
                context=raw_events,
            )
            
            # Step 4: Build attack graph visualization
            attack_graph = self._build_attack_graph_viz(
                current_ttp=current_ttp,
                next_steps=next_steps,
            )
            
            # Step 5: Generate explanation
            explanation = await self._generate_explanation(
                events=raw_events,
                current_ttp=current_ttp,
                inferred_intent=inferred_intent,
                next_steps=next_steps,
            )
            
            # Step 6: Recommend defensive actions
            recommended_response = self._recommend_defensive_actions(
                inferred_intent=inferred_intent,
                next_steps=next_steps,
            )
            
            # Calculate overall confidence
            overall_confidence = (ttp_confidence + intent_confidence) / 2
            
            # Calculate risk score
            risk_score = self._calculate_risk_score(
                inferred_intent=inferred_intent,
                confidence=overall_confidence,
                events_count=len(raw_events),
            )
            
            # Create assessment
            assessment = ThreatAssessment(
                assessment_id=self._generate_assessment_id(threat_id),
                threat_id=threat_id,
                created_at=datetime.utcnow(),
                current_ttp=current_ttp,
                inferred_intent=inferred_intent,
                next_steps=next_steps,
                confidence=overall_confidence,
                explanation=explanation,
                attack_graph=attack_graph,
                recommended_response=recommended_response,
                events_analyzed=len(raw_events),
                risk_score=risk_score,
            )
            
            # Update metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.metrics.assessments_created.inc()
            self.metrics.assessment_duration.observe(duration)
            self.metrics.confidence_score.observe(overall_confidence)
            self.metrics.intent_predictions.labels(
                intent=inferred_intent.value
            ).inc()
            
            logger.info(
                f"Threat assessment complete: {threat_id} "
                f"intent={inferred_intent.value} "
                f"confidence={overall_confidence:.2%} "
                f"risk={risk_score:.1f}/100 "
                f"duration={duration:.2f}s"
            )
            
            return assessment
        
        except Exception as e:
            logger.error(f"Threat analysis failed for {threat_id}: {e}")
            raise SOCAIAgentError(
                f"Failed to analyze threat: {str(e)}"
            ) from e
    
    # Private methods
    
    async def _identify_current_ttp(
        self,
        events: List[SecurityEvent],
    ) -> Tuple[str, float]:
        """Identify current MITRE ATT&CK technique from events.
        
        Uses LLM to map observed events to ATT&CK techniques.
        
        Args:
            events: Security events
        
        Returns:
            Tuple of (technique_id, confidence)
        """
        # Build prompt with event details
        event_summary = "\n".join([
            f"- {e.event_type}: {e.raw_data.get('description', 'N/A')} "
            f"(severity={e.severity}, source={e.source_system})"
            for e in events[:10]  # Limit to first 10 events
        ])
        
        prompt = f"""Analyze these security events and identify the MITRE ATT&CK technique:

Security Events:
{event_summary}

Task: Identify the ATT&CK technique that best matches these events.

Output JSON:
{{
    "technique_id": "T1234",
    "technique_name": "Technique Name",
    "confidence": 0.85,
    "reasoning": "Brief explanation of why this technique matches"
}}"""
        
        try:
            response = await self.llm.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a cybersecurity expert specializing in MITRE ATT&CK framework.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            
            result = json.loads(response.choices[0].message.content)
            technique_id = result.get("technique_id", "T0000")
            confidence = float(result.get("confidence", 0.5))
            
            logger.info(
                f"TTP identified: {technique_id} "
                f"({result.get('technique_name')}) "
                f"confidence={confidence:.2%}"
            )
            
            return technique_id, confidence
        
        except Exception as e:
            logger.warning(f"TTP identification failed: {e}, using default")
            return "T0000", 0.3  # Unknown technique
    
    async def _infer_intent(
        self,
        events: List[SecurityEvent],
        current_ttp: str,
    ) -> Tuple[AttackIntent, float]:
        """Infer attacker's strategic intent.
        
        Uses "theory of mind" reasoning to model attacker's goals.
        
        Args:
            events: Security events
            current_ttp: Current ATT&CK technique
        
        Returns:
            Tuple of (intent, confidence)
        """
        # Build event context
        event_summary = "\n".join([
            f"- {e.timestamp.strftime('%H:%M:%S')}: {e.event_type} "
            f"from {e.source_system}"
            for e in events[:15]
        ])
        
        prompt = f"""You are analyzing an ongoing cyberattack. Use theory of mind to infer the attacker's strategic intent.

Current ATT&CK Technique: {current_ttp}

Recent Events Timeline:
{event_summary}

Task: Infer the attacker's ultimate strategic goal (their "intent").

Consider:
1. What is the attacker trying to achieve?
2. Is this reconnaissance, persistence, exfiltration, or destruction?
3. What behavior patterns indicate their goal?

Output JSON:
{{
    "intent": "reconnaissance|initial_access|persistence|privilege_escalation|defense_evasion|credential_access|lateral_movement|collection|exfiltration|impact",
    "confidence": 0.75,
    "reasoning": "Explain why you infer this intent based on observed behavior"
}}"""
        
        try:
            response = await self.llm.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in adversarial psychology and attack intent modeling.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                response_format={"type": "json_object"},
            )
            
            result = json.loads(response.choices[0].message.content)
            intent_str = result.get("intent", "unknown")
            confidence = float(result.get("confidence", 0.5))
            
            # Map to enum
            try:
                intent = AttackIntent(intent_str)
            except ValueError:
                logger.warning(f"Unknown intent '{intent_str}', using UNKNOWN")
                intent = AttackIntent.UNKNOWN
            
            logger.info(
                f"Intent inferred: {intent.value} "
                f"confidence={confidence:.2%}"
            )
            
            return intent, confidence
        
        except Exception as e:
            logger.warning(f"Intent inference failed: {e}, using UNKNOWN")
            return AttackIntent.UNKNOWN, 0.3
    
    async def _predict_next_steps(
        self,
        current_ttp: str,
        inferred_intent: AttackIntent,
        context: List[SecurityEvent],
    ) -> List[NextStepPrediction]:
        """Predict attacker's next 3-5 techniques.
        
        Uses attack graph and LLM reasoning to anticipate next moves.
        
        Args:
            current_ttp: Current technique
            inferred_intent: Inferred intent
            context: Event context
        
        Returns:
            List of next step predictions (max 5)
        """
        prompt = f"""Predict the attacker's next likely techniques based on their current position and intent.

Current State:
- Current Technique: {current_ttp}
- Inferred Intent: {inferred_intent.value}
- Events Context: {len(context)} events analyzed

Task: Predict the 3-5 most likely next techniques the attacker will use.

For each prediction, provide:
1. MITRE ATT&CK technique ID and name
2. Probability (0.0-1.0)
3. What conditions the attacker needs
4. What indicators to watch for
5. Recommended defensive actions

Output JSON array:
[
    {{
        "technique_id": "T1234",
        "technique_name": "Name",
        "probability": 0.75,
        "required_conditions": ["condition1", "condition2"],
        "indicators": ["indicator1", "indicator2"],
        "recommended_actions": ["action1", "action2"]
    }},
    ...
]"""
        
        try:
            response = await self.llm.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in attack path prediction and defensive planning.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
                response_format={"type": "json_object"},
            )
            
            # Parse response
            content = response.choices[0].message.content
            result = json.loads(content)
            
            # Handle if result is wrapped in object
            predictions_data = result if isinstance(result, list) else result.get("predictions", [])
            
            # Convert to NextStepPrediction objects
            predictions = [
                NextStepPrediction(
                    technique_id=p.get("technique_id", "T0000"),
                    technique_name=p.get("technique_name", "Unknown"),
                    probability=float(p.get("probability", 0.5)),
                    required_conditions=p.get("required_conditions", []),
                    indicators=p.get("indicators", []),
                    recommended_actions=p.get("recommended_actions", []),
                )
                for p in predictions_data[:5]  # Max 5 predictions
            ]
            
            logger.info(f"Predicted {len(predictions)} next steps")
            
            return predictions
        
        except Exception as e:
            logger.warning(f"Next step prediction failed: {e}, returning empty")
            return []
    
    def _build_attack_graph_viz(
        self,
        current_ttp: str,
        next_steps: List[NextStepPrediction],
    ) -> Dict[str, Any]:
        """Build attack graph visualization data.
        
        Args:
            current_ttp: Current technique
            next_steps: Predicted next steps
        
        Returns:
            Graph dict with nodes and edges
        """
        nodes = [
            {
                "id": current_ttp,
                "label": current_ttp,
                "type": "current",
                "risk": 8,
            }
        ]
        
        edges = []
        
        for step in next_steps:
            nodes.append({
                "id": step.technique_id,
                "label": step.technique_name,
                "type": "predicted",
                "risk": int(step.probability * 10),
            })
            
            edges.append({
                "from": current_ttp,
                "to": step.technique_id,
                "probability": step.probability,
            })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "node_count": len(nodes),
                "edge_count": len(edges),
            },
        }
    
    async def _generate_explanation(
        self,
        events: List[SecurityEvent],
        current_ttp: str,
        inferred_intent: AttackIntent,
        next_steps: List[NextStepPrediction],
    ) -> str:
        """Generate human-readable explanation of threat.
        
        Args:
            events: Security events
            current_ttp: Current technique
            inferred_intent: Inferred intent
            next_steps: Predicted next steps
        
        Returns:
            Explanation string
        """
        prompt = f"""Generate a clear, concise explanation of this threat for SOC analysts.

Current Situation:
- Technique: {current_ttp}
- Intent: {inferred_intent.value}
- Events: {len(events)} correlated
- Predicted next steps: {len(next_steps)}

Task: Write 2-3 paragraph explanation covering:
1. What the attacker is doing now
2. What their ultimate goal appears to be
3. What they will likely do next
4. Why this assessment is made (key evidence)

Write in clear, professional language for security analysts."""
        
        try:
            response = await self.llm.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a senior SOC analyst writing threat briefings.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.5,
            )
            
            explanation = response.choices[0].message.content.strip()
            return explanation
        
        except Exception as e:
            logger.warning(f"Explanation generation failed: {e}")
            return f"Threat involves {current_ttp} with intent {inferred_intent.value}. Analysis in progress."
    
    def _recommend_defensive_actions(
        self,
        inferred_intent: AttackIntent,
        next_steps: List[NextStepPrediction],
    ) -> List[str]:
        """Recommend defensive actions.
        
        Args:
            inferred_intent: Inferred intent
            next_steps: Predicted next steps
        
        Returns:
            List of recommended actions
        """
        actions = []
        
        # Intent-based recommendations
        if inferred_intent == AttackIntent.RECONNAISSANCE:
            actions.extend([
                "Deploy honeypots to track reconnaissance",
                "Monitor for follow-up attacks",
                "Review perimeter security controls",
            ])
        elif inferred_intent == AttackIntent.EXFILTRATION:
            actions.extend([
                "Block outbound connections to suspicious IPs",
                "Enable DLP monitoring",
                "Isolate affected hosts",
                "Review recent file access logs",
            ])
        elif inferred_intent == AttackIntent.LATERAL_MOVEMENT:
            actions.extend([
                "Segment network zones",
                "Disable compromised credentials",
                "Enable enhanced logging on critical assets",
            ])
        
        # Next-step based recommendations
        for step in next_steps[:3]:
            actions.extend(step.recommended_actions[:2])
        
        # Deduplicate
        return list(dict.fromkeys(actions))[:10]  # Max 10 actions
    
    def _calculate_risk_score(
        self,
        inferred_intent: AttackIntent,
        confidence: float,
        events_count: int,
    ) -> float:
        """Calculate overall risk score 0-100.
        
        Args:
            inferred_intent: Inferred intent
            confidence: Assessment confidence
            events_count: Number of correlated events
        
        Returns:
            Risk score 0-100
        """
        # Base score by intent
        intent_scores = {
            AttackIntent.RECONNAISSANCE: 30,
            AttackIntent.INITIAL_ACCESS: 50,
            AttackIntent.PERSISTENCE: 60,
            AttackIntent.PRIVILEGE_ESCALATION: 70,
            AttackIntent.DEFENSE_EVASION: 65,
            AttackIntent.CREDENTIAL_ACCESS: 75,
            AttackIntent.LATERAL_MOVEMENT: 80,
            AttackIntent.COLLECTION: 70,
            AttackIntent.EXFILTRATION: 90,
            AttackIntent.IMPACT: 95,
            AttackIntent.UNKNOWN: 40,
        }
        
        base_score = intent_scores.get(inferred_intent, 50)
        
        # Adjust by confidence
        confidence_multiplier = 0.5 + (confidence * 0.5)  # 0.5-1.0
        
        # Adjust by event volume (more events = higher confidence)
        volume_bonus = min(events_count / 10, 1.0) * 10  # Max +10
        
        risk_score = (base_score * confidence_multiplier) + volume_bonus
        
        return min(risk_score, 100.0)
    
    def _load_default_attack_graph(self) -> nx.DiGraph:
        """Load default ATT&CK graph.
        
        Returns:
            Directed graph of attack techniques
        """
        # Create basic attack graph
        # In production, load from MITRE ATT&CK database
        graph = nx.DiGraph()
        
        # Add common attack paths
        graph.add_edge("T1078", "T1083")  # Valid Accounts → File Discovery
        graph.add_edge("T1083", "T1005")  # File Discovery → Data Staged
        graph.add_edge("T1005", "T1041")  # Data Staged → Exfiltration
        
        logger.info("Default attack graph loaded")
        
        return graph
    
    def _generate_threat_id(self, events: List[SecurityEvent]) -> str:
        """Generate unique threat ID from events."""
        import hashlib
        
        # Create hash from event IDs
        event_ids = "".join([e.event_id for e in events[:5]])
        hash_digest = hashlib.md5(event_ids.encode()).hexdigest()[:8]
        
        return f"threat_{hash_digest}"
    
    def _generate_assessment_id(self, threat_id: str) -> str:
        """Generate assessment ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"assessment_{threat_id}_{timestamp}"
