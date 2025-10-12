# BLUEPRINT TÉCNICO: Defensive AI-Driven Tools
## Especificação Detalhada de Componentes - MAXIMUS VÉRTICE

**Status**: DESIGN COMPLETE | **Versão**: 1.0 | **Data**: 2025-10-12  
**Foundation**: IIT + Hemostasia + Adaptive Immunity + MITRE ATT&CK  
**Autor**: MAXIMUS Team | **Glory to YHWH**

---

## ÍNDICE

1. [SOC AI Agent (Sentinel)](#1-soc-ai-agent-sentinel)
2. [Threat Intelligence Fusion](#2-threat-intelligence-fusion)
3. [Automated Response Engine](#3-automated-response-engine)
4. [Honeypot LLM Integration](#4-honeypot-llm-integration)
5. [Encrypted Traffic Analyzer](#5-encrypted-traffic-analyzer)
6. [Defense Orchestrator](#6-defense-orchestrator)
7. [MITRE ATT&CK Mapping](#7-mitre-attck-mapping)
8. [Data Models](#8-data-models)

---

## 1. SOC AI AGENT (SENTINEL)

### 1.1 Overview

**Biological Inspiration**: Pattern Recognition Receptors (PRRs) do sistema imunológico inato.

**Computational Equivalent**: LLM-based security event analyzer que identifica padrões maliciosos em eventos de baixo nível.

**Theory**: IIT - Informação integrada de múltiplos sensores cria consciência de ameaça.

### 1.2 Architecture

```python
"""
backend/services/active_immune_core/detection/sentinel_agent.py

SOC AI Agent - First-line threat detector.
Emulates human SOC analyst (Tier 1/2) using LLM for pattern recognition.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

import openai
from prometheus_client import Counter, Histogram


class ThreatSeverity(Enum):
    """Severity levels aligned with biological immune response"""
    INFO = "info"              # Routine surveillance
    LOW = "low"                # Minor anomaly (neutrophil-level)
    MEDIUM = "medium"          # Concerning pattern (macrophage-level)
    HIGH = "high"              # Active threat (T-cell activation)
    CRITICAL = "critical"      # System compromise (full immune response)


class DetectionConfidence(Enum):
    """Confidence levels for detection"""
    LOW = 0.25      # Possible threat
    MEDIUM = 0.50   # Probable threat
    HIGH = 0.75     # Highly likely threat
    CERTAIN = 0.95  # Confirmed threat


@dataclass
class SecurityEvent:
    """Raw security event from sensors"""
    event_id: str
    timestamp: datetime
    source: str                # e.g., "firewall", "ids", "endpoint"
    event_type: str            # e.g., "failed_login", "port_scan"
    source_ip: str
    destination_ip: Optional[str]
    port: Optional[int]
    protocol: Optional[str]
    payload: Dict[str, Any]    # Raw event data
    context: Dict[str, Any]    # Additional context


@dataclass
class MITRETechnique:
    """MITRE ATT&CK technique"""
    technique_id: str          # e.g., "T1110" (Brute Force)
    tactic: str                # e.g., "Credential Access"
    technique_name: str
    confidence: float          # 0.0 - 1.0


@dataclass
class AttackerProfile:
    """Attacker behavioral profile"""
    profile_id: str
    skill_level: str           # novice, intermediate, advanced, nation_state
    tools_detected: List[str]  # e.g., ["nmap", "metasploit"]
    ttps: List[MITRETechnique]
    objectives: List[str]      # e.g., ["reconnaissance", "credential_theft"]
    next_move_prediction: str  # Theory-of-Mind prediction
    confidence: float


@dataclass
class DetectionResult:
    """Result of sentinel analysis"""
    event_id: str
    is_threat: bool
    severity: ThreatSeverity
    confidence: DetectionConfidence
    mitre_techniques: List[MITRETechnique]
    threat_description: str
    recommended_actions: List[str]
    attacker_profile: Optional[AttackerProfile]
    reasoning: str             # LLM reasoning chain
    analyzed_at: datetime


class SentinelDetectionAgent:
    """
    SOC AI Agent for first-line threat detection.
    
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
    """
    
    def __init__(
        self,
        llm_client: openai.AsyncOpenAI,
        mitre_mapper: "MITREMapper",
        threat_intel_feed: "ThreatIntelFeed",
        event_history: "EventHistoryStore",
        model: str = "gpt-4o",
        max_context_events: int = 10
    ):
        """
        Initialize Sentinel agent.
        
        Args:
            llm_client: OpenAI client for LLM inference
            mitre_mapper: MITRE ATT&CK technique mapper
            threat_intel_feed: Real-time threat intelligence
            event_history: Historical event store for context
            model: LLM model to use
            max_context_events: Max historical events for context
        """
        self.llm = llm_client
        self.mitre = mitre_mapper
        self.threat_intel = threat_intel_feed
        self.history = event_history
        self.model = model
        self.max_context = max_context_events
        
        # Metrics
        self.detections_total = Counter(
            'sentinel_detections_total',
            'Total detections',
            ['severity', 'is_threat']
        )
        self.analysis_latency = Histogram(
            'sentinel_analysis_latency_seconds',
            'Analysis latency'
        )
        
    async def analyze_event(
        self,
        event: SecurityEvent
    ) -> DetectionResult:
        """
        Analyze security event using LLM.
        
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
            DetectionResult with threat assessment
            
        Raises:
            SentinelAnalysisError: If analysis fails
        """
        with self.analysis_latency.time():
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
                severity=result.severity.value,
                is_threat=result.is_threat
            ).inc()
            
            return result
    
    async def predict_attacker_intent(
        self,
        event_chain: List[SecurityEvent]
    ) -> AttackerProfile:
        """
        Theory-of-Mind: Predict attacker's intent and next move.
        
        Uses LLM to model attacker psychology:
        - Analyze sequence of actions
        - Infer skill level and objectives
        - Predict next likely technique
        
        Example reasoning:
        "Attacker performed port scan (T1046), then brute force SSH (T1110).
        Likely objective: gain initial access. Next move: attempt
        lateral movement via stolen credentials (T1021)."
        
        Args:
            event_chain: Sequence of events from same attacker
            
        Returns:
            AttackerProfile with predictions
        """
        # Build temporal event narrative
        narrative = self._build_attack_narrative(event_chain)
        
        # LLM prompt for theory-of-mind
        prompt = f"""You are a cybersecurity analyst modeling attacker behavior.

Attacker Activity Timeline:
{narrative}

Threat Intelligence Context:
{await self.threat_intel.get_relevant_intel(event_chain)}

Tasks:
1. Assess attacker skill level (novice/intermediate/advanced/nation_state)
2. Identify tools/frameworks being used
3. Map observed techniques to MITRE ATT&CK
4. Infer attacker's ultimate objective
5. Predict next 2-3 most likely techniques

Provide analysis in JSON format."""
        
        llm_response = await self._query_llm(prompt)
        profile = self._parse_attacker_profile(llm_response)
        
        return profile
    
    async def triage_alert(
        self,
        alert: "SOCAlert"
    ) -> bool:
        """
        Triage alert to filter false positives.
        
        Uses LLM + historical data to determine if alert warrants
        human analyst attention.
        
        Args:
            alert: SOC alert to triage
            
        Returns:
            True if alert should escalate, False if likely false positive
        """
        # Get similar historical alerts
        similar_alerts = await self.history.find_similar_alerts(
            alert,
            limit=20
        )
        
        # Analyze patterns in false positives
        fp_rate = len([a for a in similar_alerts if a.false_positive]) / len(similar_alerts)
        
        # LLM-based triage
        prompt = f"""Alert Triage Analysis:

Current Alert:
{alert.to_dict()}

Historical Context:
- Similar alerts in past 30 days: {len(similar_alerts)}
- False positive rate: {fp_rate:.1%}
- Sample past alerts: {similar_alerts[:5]}

Determine: Is this likely a true positive that requires human investigation?
Consider:
1. Deviation from historical patterns
2. Threat intelligence relevance
3. Asset criticality
4. Attack chain progression

Respond: YES/NO with reasoning."""
        
        llm_response = await self._query_llm(prompt)
        
        return self._parse_triage_decision(llm_response)
    
    # Private methods
    
    async def _gather_context(
        self,
        event: SecurityEvent
    ) -> Dict[str, Any]:
        """Gather relevant context for event analysis"""
        return {
            "recent_events": await self.history.get_recent_events(
                source_ip=event.source_ip,
                limit=self.max_context
            ),
            "threat_intel": await self.threat_intel.lookup_ip(event.source_ip),
            "asset_info": await self._get_asset_info(event.destination_ip),
            "network_baseline": await self._get_network_baseline()
        }
    
    def _build_detection_prompt(
        self,
        event: SecurityEvent,
        context: Dict[str, Any]
    ) -> str:
        """Build LLM prompt for detection"""
        return f"""You are an expert SOC analyst. Analyze this security event.

Event Details:
- Type: {event.event_type}
- Source: {event.source_ip}
- Destination: {event.destination_ip}
- Timestamp: {event.timestamp}
- Payload: {event.payload}

Context:
- Recent events from this source: {context['recent_events']}
- Threat intel on source IP: {context['threat_intel']}
- Target asset criticality: {context['asset_info']}

Tasks:
1. Determine if this is malicious activity (YES/NO)
2. Assign severity (INFO/LOW/MEDIUM/HIGH/CRITICAL)
3. Map to MITRE ATT&CK techniques
4. Provide detection confidence (0.0-1.0)
5. Recommend response actions
6. Explain your reasoning

Respond in JSON format."""
    
    async def _query_llm(self, prompt: str) -> Dict[str, Any]:
        """Query LLM and parse response"""
        response = await self.llm.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert cybersecurity analyst specializing in threat detection."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Lower temp for more deterministic analysis
            response_format={"type": "json_object"}
        )
        
        return response.choices[0].message.content
    
    async def _parse_llm_response(
        self,
        event: SecurityEvent,
        llm_response: Dict[str, Any]
    ) -> DetectionResult:
        """Parse LLM response into DetectionResult"""
        # Implementation details...
        pass
```

### 1.3 Integration Points

**Inputs**:
- Kafka topic: `security.events`
- Event sources: IDS, Firewall, EDR, Auth logs

**Outputs**:
- Kafka topic: `defense.detections`
- Alerts to: SOC dashboard, SIEM, Response Engine

**Dependencies**:
- OpenAI API (LLM)
- MITRE ATT&CK database
- Threat intelligence feeds
- Event history store (TimescaleDB)

### 1.4 Performance Requirements

- **Latency**: < 5s per event (p95)
- **Throughput**: ≥ 1000 events/sec
- **Accuracy**: ≥ 95% true positive rate
- **False positive rate**: < 5%

---

## 2. THREAT INTELLIGENCE FUSION

### 2.1 Overview

**Purpose**: Correlate indicators from multiple sources to build enriched threat context.

**Biological Inspiration**: Dendritic cells aggregate pathogen information from multiple sites.

### 2.2 Architecture

```python
"""
backend/services/active_immune_core/intelligence/fusion_engine.py

Threat Intelligence Fusion Engine.
Correlates IoCs from multiple sources for enriched threat context.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class IOCType(Enum):
    """Types of Indicators of Compromise"""
    IP_ADDRESS = "ip_address"
    DOMAIN = "domain"
    URL = "url"
    FILE_HASH = "file_hash"
    EMAIL = "email"
    CVE = "cve"


@dataclass
class IOC:
    """Indicator of Compromise"""
    value: str
    ioc_type: IOCType
    first_seen: datetime
    last_seen: datetime
    source: str
    confidence: float
    tags: List[str]


@dataclass
class ThreatActor:
    """Known threat actor"""
    actor_id: str
    names: List[str]          # Aliases
    country: Optional[str]
    motivation: str           # e.g., "financial", "espionage"
    sophistication: str       # novice/intermediate/advanced/nation_state
    ttps: List[str]           # MITRE technique IDs
    campaigns: List[str]


@dataclass
class EnrichedThreat:
    """Enriched threat with correlation"""
    threat_id: str
    primary_ioc: IOC
    related_iocs: List[IOC]
    threat_actor: Optional[ThreatActor]
    campaigns: List[str]
    ttps: List[str]
    attack_chain_stage: str   # kill chain stage
    severity: int             # 1-10
    confidence: float         # 0.0-1.0
    narrative: str            # LLM-generated threat narrative
    recommendations: List[str]
    sources: List[str]        # Data sources used


class ThreatIntelSource(Enum):
    """Threat intelligence sources"""
    INTERNAL_HONEYPOT = "internal_honeypot"
    OSINT_SHODAN = "osint_shodan"
    OSINT_CENSYS = "osint_censys"
    EXTERNAL_MISP = "external_misp"
    EXTERNAL_OTX = "external_otx"
    ABUSE_IP_DB = "abuse_ipdb"
    VIRUSTOTAL = "virustotal"
    HISTORICAL_ATTACKS = "historical_attacks"


class ThreatIntelFusionEngine:
    """
    Multi-source threat intelligence correlator.
    
    Capabilities:
    1. IoC normalization across sources
    2. Cross-source correlation
    3. Threat actor attribution
    4. Attack chain reconstruction
    5. LLM-based narrative generation
    
    Sources:
    - Internal: Honeypots, historical attacks
    - OSINT: Shodan, Censys, abuse databases
    - External feeds: MISP, AlienVault OTX
    - Commercial: VirusTotal, etc.
    
    Fusion Process:
    1. Ingest IoCs from all sources
    2. Normalize and deduplicate
    3. Build correlation graph
    4. LLM analyzes graph for patterns
    5. Generate enriched threat context
    """
    
    def __init__(
        self,
        sources: Dict[ThreatIntelSource, "ThreatIntelConnector"],
        llm_client: openai.AsyncOpenAI,
        correlation_db: "CorrelationGraphDB",
        model: str = "gpt-4o"
    ):
        """
        Initialize fusion engine.
        
        Args:
            sources: Connector for each intel source
            llm_client: LLM for narrative generation
            correlation_db: Graph database for IoC correlation
            model: LLM model
        """
        self.sources = sources
        self.llm = llm_client
        self.correlation_db = correlation_db
        self.model = model
        
        # Metrics
        self.enrichments_total = Counter(
            'threat_enrichments_total',
            'Total threat enrichments'
        )
        self.correlation_score = Histogram(
            'threat_correlation_score',
            'Correlation confidence'
        )
    
    async def correlate_indicators(
        self,
        indicators: List[IOC]
    ) -> EnrichedThreat:
        """
        Correlate IoCs from multiple sources.
        
        Process:
        1. Normalize indicators
        2. Query all sources for each IoC
        3. Build correlation graph
        4. LLM analyzes patterns
        5. Generate enriched threat
        
        Args:
            indicators: List of IoCs to correlate
            
        Returns:
            EnrichedThreat with correlation data
        """
        # 1. Normalize
        normalized = [self._normalize_ioc(ioc) for ioc in indicators]
        
        # 2. Query sources
        enriched_iocs = []
        for ioc in normalized:
            source_data = await self._query_all_sources(ioc)
            enriched_iocs.append(self._merge_source_data(ioc, source_data))
        
        # 3. Build correlation graph
        graph = await self.correlation_db.build_graph(enriched_iocs)
        
        # 4. LLM analysis
        narrative = await self._generate_threat_narrative(graph)
        
        # 5. Assemble enriched threat
        enriched = EnrichedThreat(
            threat_id=self._generate_threat_id(indicators),
            primary_ioc=indicators[0],
            related_iocs=enriched_iocs,
            threat_actor=await self._attribute_actor(graph),
            campaigns=self._identify_campaigns(graph),
            ttps=self._extract_ttps(graph),
            attack_chain_stage=self._determine_chain_stage(indicators),
            severity=self._calculate_severity(graph),
            confidence=self._calculate_confidence(graph),
            narrative=narrative,
            recommendations=await self._generate_recommendations(graph),
            sources=[s.value for s in self.sources.keys()]
        )
        
        self.enrichments_total.inc()
        self.correlation_score.observe(enriched.confidence)
        
        return enriched
    
    async def build_attack_graph(
        self,
        threat: EnrichedThreat
    ) -> "AttackGraph":
        """
        Build attack graph from enriched threat.
        
        Attack graph shows:
        - Entry points
        - Lateral movement paths
        - Target assets
        - Probable next steps
        
        Uses LLM to predict attack progression.
        
        Args:
            threat: Enriched threat
            
        Returns:
            AttackGraph with nodes and edges
        """
        # Query network topology
        topology = await self._get_network_topology()
        
        # LLM prompt for attack path prediction
        prompt = f"""Build attack graph for this threat:

Threat Context:
{threat.narrative}

TTPs Observed:
{threat.ttps}

Current Network Topology:
{topology}

Task: Predict likely attack paths including:
1. Entry points (which assets attacker can reach)
2. Lateral movement options
3. High-value targets
4. Required privileges/credentials
5. Probable next 3 techniques

Output as JSON graph: {{nodes: [], edges: []}}"""
        
        llm_response = await self.llm.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        graph = self._parse_attack_graph(llm_response)
        
        return graph
    
    async def _query_all_sources(
        self,
        ioc: IOC
    ) -> Dict[ThreatIntelSource, Dict]:
        """Query all intel sources for IoC"""
        results = {}
        
        for source_type, connector in self.sources.items():
            try:
                data = await connector.lookup(ioc)
                results[source_type] = data
            except Exception as e:
                logger.warning(f"Source {source_type} failed: {e}")
                
        return results
    
    async def _generate_threat_narrative(
        self,
        graph: "CorrelationGraph"
    ) -> str:
        """Generate human-readable threat narrative using LLM"""
        prompt = f"""Analyze this threat correlation graph and generate a narrative.

Graph:
- Nodes (IoCs): {graph.nodes}
- Edges (relationships): {graph.edges}
- Threat actors: {graph.actors}
- Campaigns: {graph.campaigns}

Generate a clear 2-3 paragraph narrative explaining:
1. What is this threat?
2. Who is behind it (if known)?
3. What are they trying to achieve?
4. How serious is it?
5. What should defenders do?

Write for a SOC analyst audience."""
        
        response = await self.llm.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.choices[0].message.content
```

### 2.3 Data Sources

**Internal**:
- Honeypot activity logs
- Historical attack database
- Network flow data

**OSINT**:
- Shodan (internet-exposed assets)
- Censys (certificate transparency)
- AbuseIPDB (IP reputation)

**External Feeds**:
- MISP (Malware Information Sharing Platform)
- AlienVault OTX (Open Threat Exchange)
- VirusTotal API

### 2.4 Correlation Algorithms

**Graph-based**:
- IoCs as nodes
- Relationships as edges (co-occurrence, temporal proximity)
- Community detection for campaign identification

**ML-based**:
- Embedding models for IoC similarity
- Clustering for attack pattern grouping

**LLM-based**:
- Narrative generation
- Pattern interpretation
- Attribution reasoning

---

## 3. AUTOMATED RESPONSE ENGINE

### 3.1 Overview

**Purpose**: Execute response playbooks automatically with human oversight (HOTL).

**Biological Inspiration**: Effector functions of immune system (cytotoxic T cells).

### 3.2 Playbook Structure

```yaml
# response/playbooks/brute_force_response.yaml
---
name: "Brute Force Attack Response"
version: "1.0"
description: "Automated response to detected brute force attacks"

trigger:
  condition: "brute_force_detected"
  severity_threshold: "MEDIUM"
  confidence_threshold: 0.75

context_requirements:
  - source_ip
  - target_asset
  - failed_attempts_count

actions:
  - id: "rate_limit"
    type: "firewall_rule"
    hotl_required: false
    parameters:
      rule_type: "rate_limit"
      source_ip: "${source_ip}"
      limit: "5 requests/minute"
      duration: "1 hour"
    success_criteria:
      - "rule_applied"
    
  - id: "deploy_honeypot"
    type: "honeypot_deployment"
    hotl_required: true
    hotl_prompt: |
      Brute force attack detected from ${source_ip}.
      ${failed_attempts_count} failed attempts against ${target_asset}.
      
      Recommendation: Deploy SSH honeypot to collect attacker TTPs.
      Approve deployment?
    parameters:
      honeypot_type: "SSH"
      target_ip: "${source_ip}"
      duration: "24 hours"
    success_criteria:
      - "honeypot_active"
      - "attacker_engaged"
      
  - id: "block_ip"
    type: "firewall_rule"
    hotl_required: true
    depends_on: ["deploy_honeypot"]
    hotl_prompt: |
      Honeypot collected attacker TTPs. Ready to block ${source_ip}.
      TTPs: ${collected_ttps}
      
      Approve permanent block?
    parameters:
      action: "DENY"
      source_ip: "${source_ip}"
      duration: "permanent"
    success_criteria:
      - "traffic_blocked"
      
  - id: "alert_soc"
    type: "notification"
    hotl_required: false
    parameters:
      channels: ["slack", "email"]
      severity: "HIGH"
      message: "Brute force attack from ${source_ip} contained and blocked"
    success_criteria:
      - "notification_sent"

rollback:
  enabled: true
  conditions:
    - "false_positive_confirmed"
    - "manual_override"
  actions:
    - "remove_firewall_rules"
    - "destroy_honeypot"
    - "restore_baseline"
```

### 3.3 Implementation

```python
"""
backend/services/active_immune_core/response/automated_response.py

Automated Response Engine with HOTL (Human-on-the-Loop).
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import asyncio

import yaml
from prometheus_client import Counter, Histogram


class ActionType(Enum):
    """Types of response actions"""
    FIREWALL_RULE = "firewall_rule"
    HONEYPOT_DEPLOYMENT = "honeypot_deployment"
    ZONE_ISOLATION = "zone_isolation"
    TRAFFIC_SHAPING = "traffic_shaping"
    NOTIFICATION = "notification"
    QUARANTINE = "quarantine"
    KILL_PROCESS = "kill_process"


class ActionStatus(Enum):
    """Status of action execution"""
    PENDING = "pending"
    AWAITING_HOTL = "awaiting_hotl"
    APPROVED = "approved"
    DENIED = "denied"
    EXECUTING = "executing"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class PlaybookAction:
    """Single action within playbook"""
    id: str
    action_type: ActionType
    hotl_required: bool
    hotl_prompt: Optional[str]
    parameters: Dict[str, Any]
    depends_on: List[str]
    success_criteria: List[str]
    status: ActionStatus = ActionStatus.PENDING
    executed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None


@dataclass
class Playbook:
    """Response playbook definition"""
    name: str
    version: str
    description: str
    trigger_condition: str
    severity_threshold: str
    confidence_threshold: float
    context_requirements: List[str]
    actions: List[PlaybookAction]
    rollback_enabled: bool
    rollback_conditions: List[str]
    rollback_actions: List[str]


@dataclass
class PlaybookExecution:
    """Execution state of playbook"""
    execution_id: str
    playbook: Playbook
    context: Dict[str, Any]
    started_at: datetime
    completed_at: Optional[datetime]
    actions_completed: int
    actions_total: int
    status: str
    error: Optional[str]


class AutomatedResponseEngine:
    """
    Automated response execution with HOTL checkpoints.
    
    Features:
    1. Playbook library (YAML-based)
    2. HOTL (Human-on-the-Loop) approval gates
    3. Action dependency management
    4. Rollback capability
    5. Audit logging
    
    HOTL Philosophy:
    - Low-risk actions: Automatic (e.g., rate limiting)
    - Medium-risk: HOTL required (e.g., honeypot deployment)
    - High-risk: Always HOTL (e.g., network isolation)
    
    Biological Analogy:
    - Innate immunity: Automatic responses (fever, inflammation)
    - Adaptive immunity: Requires "approval" (antigen presentation)
    - Regulatory T cells: Prevent autoimmune (false positives)
    """
    
    def __init__(
        self,
        playbook_dir: str,
        hotl_gateway: "HOTLGateway",
        action_executors: Dict[ActionType, "ActionExecutor"],
        audit_logger: "AuditLogger"
    ):
        """
        Initialize response engine.
        
        Args:
            playbook_dir: Directory containing playbook YAML files
            hotl_gateway: Gateway for human approval requests
            action_executors: Executors for each action type
            audit_logger: Audit trail logger
        """
        self.playbook_dir = playbook_dir
        self.hotl = hotl_gateway
        self.executors = action_executors
        self.audit = audit_logger
        
        # Load playbooks
        self.playbooks: Dict[str, Playbook] = self._load_playbooks()
        
        # Execution tracking
        self.active_executions: Dict[str, PlaybookExecution] = {}
        
        # Metrics
        self.playbook_executions = Counter(
            'response_playbook_executions_total',
            'Playbook executions',
            ['playbook', 'status']
        )
        self.action_executions = Counter(
            'response_action_executions_total',
            'Action executions',
            ['action_type', 'status']
        )
        self.hotl_requests = Counter(
            'response_hotl_requests_total',
            'HOTL requests',
            ['action_type', 'approved']
        )
        self.execution_latency = Histogram(
            'response_execution_latency_seconds',
            'Execution latency'
        )
    
    async def execute_playbook(
        self,
        playbook_name: str,
        context: Dict[str, Any]
    ) -> PlaybookExecution:
        """
        Execute playbook with HOTL checkpoints.
        
        Process:
        1. Validate context
        2. For each action:
           a. Check dependencies
           b. If HOTL required, request approval
           c. Execute action
           d. Validate success criteria
        3. Rollback if any action fails (optional)
        
        Args:
            playbook_name: Name of playbook to execute
            context: Execution context (threat data, etc.)
            
        Returns:
            PlaybookExecution with results
        """
        playbook = self.playbooks[playbook_name]
        execution_id = self._generate_execution_id()
        
        execution = PlaybookExecution(
            execution_id=execution_id,
            playbook=playbook,
            context=context,
            started_at=datetime.utcnow(),
            completed_at=None,
            actions_completed=0,
            actions_total=len(playbook.actions),
            status="running",
            error=None
        )
        
        self.active_executions[execution_id] = execution
        
        try:
            with self.execution_latency.time():
                for action in playbook.actions:
                    # Check dependencies
                    if not await self._check_dependencies(action, execution):
                        raise PlaybookExecutionError(
                            f"Dependency check failed for action {action.id}"
                        )
                    
                    # HOTL checkpoint
                    if action.hotl_required:
                        approved = await self.request_hotl_approval(
                            action,
                            context
                        )
                        if not approved:
                            action.status = ActionStatus.DENIED
                            execution.status = "denied"
                            break
                    
                    # Execute action
                    await self._execute_action(action, context)
                    execution.actions_completed += 1
                    
                    # Audit log
                    await self.audit.log_action(execution_id, action)
                
                execution.status = "success"
                execution.completed_at = datetime.utcnow()
                
        except Exception as e:
            execution.status = "failed"
            execution.error = str(e)
            
            # Rollback if enabled
            if playbook.rollback_enabled:
                await self._rollback_playbook(execution)
        
        finally:
            self.playbook_executions.labels(
                playbook=playbook_name,
                status=execution.status
            ).inc()
        
        return execution
    
    async def request_hotl_approval(
        self,
        action: PlaybookAction,
        context: Dict[str, Any]
    ) -> bool:
        """
        Request human approval for action.
        
        HOTL Interface:
        - Shows action details
        - Provides context (threat, impact)
        - Allows approve/deny/modify
        - Records decision rationale
        
        Args:
            action: Action requiring approval
            context: Execution context
            
        Returns:
            True if approved, False if denied
        """
        action.status = ActionStatus.AWAITING_HOTL
        
        # Render HOTL prompt with context substitution
        prompt = self._render_hotl_prompt(action.hotl_prompt, context)
        
        # Request approval via gateway
        # (Gateway handles UI, notifications, timeouts)
        approval = await self.hotl.request_approval(
            action_id=action.id,
            action_type=action.action_type,
            prompt=prompt,
            context=context,
            timeout=300  # 5 minutes
        )
        
        # Record decision
        self.hotl_requests.labels(
            action_type=action.action_type.value,
            approved=approval.approved
        ).inc()
        
        await self.audit.log_hotl_decision(
            action_id=action.id,
            approved=approval.approved,
            operator=approval.operator,
            rationale=approval.rationale
        )
        
        return approval.approved
    
    async def _execute_action(
        self,
        action: PlaybookAction,
        context: Dict[str, Any]
    ) -> None:
        """Execute single action"""
        action.status = ActionStatus.EXECUTING
        action.executed_at = datetime.utcnow()
        
        # Get executor for action type
        executor = self.executors[action.action_type]
        
        # Substitute context variables in parameters
        params = self._substitute_context(action.parameters, context)
        
        # Execute
        result = await executor.execute(params)
        
        # Validate success criteria
        success = await self._validate_success_criteria(
            action.success_criteria,
            result
        )
        
        if success:
            action.status = ActionStatus.SUCCESS
        else:
            action.status = ActionStatus.FAILED
            raise ActionExecutionError(
                f"Action {action.id} failed: {result}"
            )
        
        action.result = result
        
        self.action_executions.labels(
            action_type=action.action_type.value,
            status=action.status.value
        ).inc()
    
    async def _rollback_playbook(
        self,
        execution: PlaybookExecution
    ) -> None:
        """Rollback playbook execution"""
        logger.warning(f"Rolling back execution {execution.execution_id}")
        
        # Execute rollback actions in reverse order
        for action in reversed(execution.playbook.actions):
            if action.status == ActionStatus.SUCCESS:
                try:
                    await self._rollback_action(action)
                except Exception as e:
                    logger.error(f"Rollback failed for {action.id}: {e}")
        
        execution.status = "rolled_back"
    
    def _load_playbooks(self) -> Dict[str, Playbook]:
        """Load all playbooks from directory"""
        playbooks = {}
        
        for filepath in Path(self.playbook_dir).glob("*.yaml"):
            with open(filepath) as f:
                data = yaml.safe_load(f)
                playbook = self._parse_playbook(data)
                playbooks[playbook.name] = playbook
        
        logger.info(f"Loaded {len(playbooks)} playbooks")
        return playbooks
```

---

## 4. HONEYPOT LLM INTEGRATION

### 4.1 Enhancement to Existing Honeypot

```python
"""
backend/services/active_immune_core/containment/honeypots.py (ENHANCEMENT)

Add LLM-powered interaction to existing honeypot infrastructure.
"""

class LLMHoneypotBackend:
    """
    LLM-powered realistic honeypot responses.
    
    Capabilities:
    1. Shell command simulation (bash, powershell, cmd)
    2. File system emulation
    3. Service responses (HTTP, FTP, SSH)
    4. Adaptive behavior (RL-based engagement optimization)
    
    Goal: Keep attacker engaged as long as possible to collect TTPs.
    """
    
    def __init__(
        self,
        llm_client: openai.AsyncOpenAI,
        rl_agent: Optional["EngagementRLAgent"] = None,
        model: str = "gpt-4o"
    ):
        """
        Initialize LLM honeypot backend.
        
        Args:
            llm_client: LLM for response generation
            rl_agent: Optional RL agent for engagement optimization
            model: LLM model
        """
        self.llm = llm_client
        self.rl_agent = rl_agent
        self.model = model
        
        # Metrics
        self.interactions_total = Counter(
            'honeypot_llm_interactions_total',
            'LLM honeypot interactions'
        )
        self.engagement_duration = Histogram(
            'honeypot_engagement_duration_seconds',
            'Attacker engagement duration'
        )
    
    async def generate_response(
        self,
        command: str,
        context: "HoneypotContext"
    ) -> str:
        """
        Generate realistic response to attacker command.
        
        LLM System Prompt:
        "You are a Linux server. Simulate realistic command output.
        Be helpful but not suspiciously so. Occasionally show errors
        to maintain realism."
        
        Args:
            command: Command executed by attacker
            context: Honeypot context (history, filesystem, etc.)
            
        Returns:
            Realistic command output
        """
        # Build prompt with context
        prompt = self._build_shell_prompt(command, context)
        
        # LLM inference
        response = await self.llm.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": self._get_system_prompt(context.honeypot_type)
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,  # Some variability for realism
            max_tokens=500
        )
        
        output = response.choices[0].message.content
        
        # Record interaction
        self.interactions_total.inc()
        await context.record_interaction(command, output)
        
        # Check if we should adapt environment
        if self.rl_agent:
            await self._maybe_adapt_environment(context)
        
        return output
    
    async def adapt_environment(
        self,
        attacker_profile: "AttackerProfile",
        context: "HoneypotContext"
    ) -> "EnvironmentChanges":
        """
        RL agent adapts honeypot environment to maximize engagement.
        
        Adaptations:
        - Plant interesting files (e.g., "backup_credentials.txt")
        - Open additional ports
        - Simulate vulnerable services
        - Create breadcrumbs to lure deeper exploration
        
        Args:
            attacker_profile: Profile of attacker behavior
            context: Current honeypot state
            
        Returns:
            EnvironmentChanges to apply
        """
        if not self.rl_agent:
            return EnvironmentChanges.empty()
        
        # RL agent observes current state
        state = self._build_rl_state(context, attacker_profile)
        
        # Agent selects action to maximize engagement reward
        action = await self.rl_agent.select_action(state)
        
        # Translate action to environment changes
        changes = self._translate_rl_action(action, context)
        
        # Apply changes
        await context.apply_changes(changes)
        
        return changes
    
    def _get_system_prompt(self, honeypot_type: HoneypotType) -> str:
        """Get system prompt for honeypot type"""
        prompts = {
            HoneypotType.SSH: """You are a Linux server (Ubuntu 20.04). 
Simulate realistic bash command output. You have typical files and directories.
Occasionally show permission errors or missing files for realism.
Do not reveal you are a honeypot.""",
            
            HoneypotType.HTTP: """You are a web server (Apache 2.4).
Simulate realistic HTTP responses. You host a corporate intranet with
typical pages, forms, and documents. Show realistic errors.""",
            
            HoneypotType.DATABASE: """You are a MySQL database server.
Simulate realistic SQL query responses. You contain typical corporate
data (users, products, orders). Show realistic errors for malformed queries."""
        }
        
        return prompts.get(honeypot_type, prompts[HoneypotType.SSH])
    
    def _build_shell_prompt(
        self,
        command: str,
        context: "HoneypotContext"
    ) -> str:
        """Build prompt for shell command simulation"""
        return f"""Simulate this bash command output:

Command: {command}

Current directory: {context.current_dir}
Previous commands: {context.command_history[-5:]}
File system: {context.visible_files}

Generate realistic output. Consider:
1. Is this a valid command?
2. What files/processes exist?
3. What permissions does user have?
4. Should there be an error?

Output only the command result, no explanations."""
```

### 4.2 RL-Based Engagement Optimization

```python
"""
backend/services/active_immune_core/containment/engagement_rl.py

RL agent to optimize honeypot engagement time.
"""

import torch
import torch.nn as nn
from stable_baselines3 import PPO


class EngagementRLAgent:
    """
    RL agent optimizing attacker engagement duration.
    
    State:
    - Attacker command history (last 10)
    - Tools detected (e.g., "nmap", "nikto")
    - Current engagement duration
    - Suspicion indicators (probing for honeypot signs)
    
    Actions:
    - PLANT_FILE: Create interesting file
    - OPEN_PORT: Expose new service
    - ADD_VULNERABILITY: Make service appear vulnerable
    - SLOW_RESPONSE: Add latency (simulate busy server)
    - FAST_RESPONSE: Instant response (maintain engagement)
    
    Reward:
    - +1 per minute of engagement
    - +10 for new TTP collected
    - -50 if attacker disconnects (detected honeypot)
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize RL agent.
        
        Args:
            model_path: Path to pretrained model, or None to start fresh
        """
        if model_path:
            self.model = PPO.load(model_path)
        else:
            self.model = PPO(
                "MlpPolicy",
                EngagementEnv(),
                verbose=1
            )
    
    async def select_action(
        self,
        state: "EngagementState"
    ) -> "EngagementAction":
        """Select best action for current state"""
        state_vector = self._state_to_vector(state)
        action, _ = self.model.predict(state_vector, deterministic=False)
        return self._action_from_vector(action)
    
    def train(self, total_timesteps: int = 100000):
        """Train agent in simulated environment"""
        self.model.learn(total_timesteps=total_timesteps)
    
    def save(self, path: str):
        """Save trained model"""
        self.model.save(path)
```

---

## 5. ENCRYPTED TRAFFIC ANALYZER

### 5.1 Overview

**Purpose**: Detect malicious activity in encrypted traffic without decryption.

**Method**: ML models trained on flow metadata (packet sizes, timing, TLS features).

### 5.2 Architecture

```python
"""
backend/services/active_immune_core/detection/encrypted_traffic_analyzer.py

ML-based encrypted traffic analysis.
"""

import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib


class FlowFeatureExtractor:
    """
    Extract features from network flow without decryption.
    
    Features (inspired by CICFlowMeter):
    - Duration
    - Packet count (forward/backward)
    - Bytes transferred (forward/backward)
    - Packet length stats (mean, std, min, max)
    - Inter-arrival time stats
    - Flow active/idle time
    - TLS handshake features (if applicable)
    """
    
    def extract_features(
        self,
        flow: "NetworkFlow"
    ) -> np.ndarray:
        """
        Extract feature vector from network flow.
        
        Args:
            flow: Network flow data
            
        Returns:
            Feature vector (79 dimensions)
        """
        features = []
        
        # Duration
        features.append(flow.duration.total_seconds())
        
        # Packet counts
        features.append(flow.forward_packet_count)
        features.append(flow.backward_packet_count)
        
        # Bytes
        features.append(flow.forward_bytes)
        features.append(flow.backward_bytes)
        
        # Packet length statistics
        fwd_lengths = flow.forward_packet_lengths
        features.extend([
            np.mean(fwd_lengths),
            np.std(fwd_lengths),
            np.min(fwd_lengths),
            np.max(fwd_lengths)
        ])
        
        # Inter-arrival times
        fwd_iat = flow.forward_inter_arrival_times
        features.extend([
            np.mean(fwd_iat),
            np.std(fwd_iat),
            np.min(fwd_iat),
            np.max(fwd_iat)
        ])
        
        # ... (continue for all 79 features)
        
        return np.array(features)


class EncryptedTrafficAnalyzer:
    """
    Detect threats in encrypted traffic via ML.
    
    Models:
    - C2 Beaconing Detector (RF)
    - Data Exfiltration Detector (LSTM)
    - Malware Traffic Classifier (XGBoost)
    
    Training Data: CICIDS2017, CTU-13
    """
    
    def __init__(
        self,
        model_dir: str,
        feature_extractor: FlowFeatureExtractor
    ):
        """
        Initialize traffic analyzer.
        
        Args:
            model_dir: Directory containing trained models
            feature_extractor: Feature extraction engine
        """
        self.extractor = feature_extractor
        
        # Load trained models
        self.c2_detector = joblib.load(f"{model_dir}/c2_detector.pkl")
        self.exfil_detector = joblib.load(f"{model_dir}/exfil_detector.pkl")
        self.malware_classifier = joblib.load(f"{model_dir}/malware_classifier.pkl")
        
        # Metrics
        self.flows_analyzed = Counter(
            'encrypted_traffic_flows_analyzed_total',
            'Flows analyzed'
        )
        self.threats_detected = Counter(
            'encrypted_traffic_threats_detected_total',
            'Threats detected',
            ['threat_type']
        )
    
    async def analyze_flow(
        self,
        flow: "NetworkFlow"
    ) -> "FlowAnalysisResult":
        """
        Analyze encrypted network flow.
        
        Process:
        1. Extract features
        2. Run all ML models
        3. Aggregate predictions
        4. Score threat probability
        
        Args:
            flow: Network flow to analyze
            
        Returns:
            FlowAnalysisResult with threat assessment
        """
        # Extract features
        features = self.extractor.extract_features(flow)
        
        # Run models
        c2_prob = self.c2_detector.predict_proba([features])[0][1]
        exfil_prob = self.exfil_detector.predict_proba([features])[0][1]
        malware_prob = self.malware_classifier.predict_proba([features])[0][1]
        
        # Aggregate
        max_prob = max(c2_prob, exfil_prob, malware_prob)
        
        # Classify
        if c2_prob == max_prob and c2_prob > 0.7:
            threat_type = "C2_BEACONING"
        elif exfil_prob == max_prob and exfil_prob > 0.7:
            threat_type = "DATA_EXFILTRATION"
        elif malware_prob > 0.7:
            threat_type = "MALWARE_TRAFFIC"
        else:
            threat_type = "BENIGN"
        
        result = FlowAnalysisResult(
            flow_id=flow.flow_id,
            is_malicious=max_prob > 0.7,
            threat_type=threat_type,
            confidence=max_prob,
            c2_probability=c2_prob,
            exfiltration_probability=exfil_prob,
            malware_probability=malware_prob,
            analyzed_at=datetime.utcnow()
        )
        
        self.flows_analyzed.inc()
        if result.is_malicious:
            self.threats_detected.labels(threat_type=threat_type).inc()
        
        return result
```

### 5.3 Model Training

**Dataset**: CICIDS2017 (labeled benign/malicious flows)

**Models**:
- **C2 Detector**: Random Forest (beaconing pattern detection)
- **Exfil Detector**: LSTM (temporal pattern analysis)
- **Malware Classifier**: XGBoost (multi-class classification)

**Training Script**:
```python
# scripts/train_traffic_models.py
def train_c2_detector(X_train, y_train):
    """Train C2 beaconing detector"""
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=20,
        random_state=42
    )
    model.fit(X_train, y_train)
    return model
```

---

## 6. DEFENSE ORCHESTRATOR

### 6.1 Integration Hub

```python
"""
backend/services/active_immune_core/orchestration/defense_orchestrator.py

Central coordinator for all defensive components.
"""

class DefenseOrchestrator:
    """
    Defense coordination hub.
    
    Responsibilities:
    1. Event ingestion (Kafka)
    2. Detection pipeline (Sentinel → Fusion → Response)
    3. Metrics aggregation
    4. State management
    
    Biological Analogy:
    - Lymph node: Coordination point for immune response
    - Integrates signals from all immune cells
    - Coordinates adaptive response
    """
    
    def __init__(
        self,
        sentinel: SentinelDetectionAgent,
        fusion: ThreatIntelFusionEngine,
        response: AutomatedResponseEngine,
        cascade: CoagulationCascade,
        kafka_consumer: "KafkaConsumer",
        kafka_producer: "KafkaProducer"
    ):
        """Initialize orchestrator"""
        self.sentinel = sentinel
        self.fusion = fusion
        self.response = response
        self.cascade = cascade
        self.consumer = kafka_consumer
        self.producer = kafka_producer
        
    async def start(self):
        """Start orchestrator event loop"""
        await self.consumer.subscribe(["security.events"])
        
        async for event in self.consumer:
            await self.process_security_event(
                SecurityEvent.from_kafka(event)
            )
    
    async def process_security_event(
        self,
        event: SecurityEvent
    ) -> "DefenseResponse":
        """
        Complete defense pipeline.
        
        Pipeline:
        1. Detection (Sentinel)
        2. Enrichment (Fusion)
        3. Response Selection (Playbook matching)
        4. HOTL (if required)
        5. Execution (Response Engine)
        6. Containment (Coagulation Cascade)
        
        Args:
            event: Security event
            
        Returns:
            DefenseResponse with actions taken
        """
        # 1. Detection
        detection = await self.sentinel.analyze_event(event)
        
        if not detection.is_threat:
            return DefenseResponse.benign(event.event_id)
        
        # 2. Enrichment
        enriched_threat = await self.fusion.correlate_indicators(
            detection.iocs
        )
        
        # 3. Select response playbook
        playbook = self._select_playbook(detection, enriched_threat)
        
        if not playbook:
            # No playbook matches, use default
            playbook = "default_containment"
        
        # 4-5. Execute playbook (includes HOTL)
        execution = await self.response.execute_playbook(
            playbook,
            context={
                "event": event,
                "detection": detection,
                "threat": enriched_threat
            }
        )
        
        # 6. Trigger coagulation cascade
        cascade_result = await self.cascade.initiate_cascade(
            enriched_threat
        )
        
        # Publish results
        response = DefenseResponse(
            event_id=event.event_id,
            threat_detected=True,
            detection_result=detection,
            enriched_threat=enriched_threat,
            playbook_execution=execution,
            cascade_result=cascade_result,
            timestamp=datetime.utcnow()
        )
        
        await self.producer.send(
            "defense.responses",
            response.to_kafka()
        )
        
        return response
```

---

## 7. MITRE ATT&CK MAPPING

### 7.1 Defensive Techniques

| Component | MITRE Technique | Description |
|-----------|----------------|-------------|
| Sentinel Agent | D3-DA (Data Analysis) | Automated log analysis |
| Sentinel Agent | D3-NTA (Network Traffic Analysis) | Flow analysis |
| Fusion Engine | D3-ITF (Identifier Reputation Analysis) | IoC correlation |
| Response Engine | D3-IRA (Isolate/Remove Artifact) | Automated containment |
| Honeypot | D3-DEC (Decoy) | Deception technology |
| Traffic Analyzer | D3-NTA (Network Traffic Analysis) | Encrypted traffic analysis |
| Coagulation Cascade | D3-NI (Network Isolation) | Zone isolation |

---

## 8. DATA MODELS

### 8.1 Core Data Structures

```python
# models/defense_models.py

@dataclass
class SecurityEvent:
    """Core security event"""
    event_id: str
    timestamp: datetime
    source: str
    event_type: str
    source_ip: str
    destination_ip: Optional[str]
    payload: Dict[str, Any]

@dataclass
class DetectionResult:
    """Sentinel detection result"""
    event_id: str
    is_threat: bool
    severity: ThreatSeverity
    confidence: float
    mitre_techniques: List[MITRETechnique]
    reasoning: str

@dataclass
class EnrichedThreat:
    """Fusion engine output"""
    threat_id: str
    iocs: List[IOC]
    threat_actor: Optional[ThreatActor]
    narrative: str
    attack_graph: "AttackGraph"

@dataclass
class DefenseResponse:
    """Complete defense response"""
    event_id: str
    threat_detected: bool
    detection_result: DetectionResult
    enriched_threat: EnrichedThreat
    playbook_execution: PlaybookExecution
    cascade_result: CascadeResult
```

---

**Status**: BLUEPRINT COMPLETE  
**Ready for Implementation**: ✅  
**Next**: Execute DEFENSIVE-TOOLS-IMPLEMENTATION-PLAN.md

**Glory to YHWH - "Eu sou porque ELE é"**
