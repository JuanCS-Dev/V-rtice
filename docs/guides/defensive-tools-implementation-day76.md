# Defensive AI-Driven Tools - Implementation Plan Day 76
## MAXIMUS VÉRTICE - Glória a YHWH

**Date**: 2025-10-12  
**Session**: Day 76  
**Focus**: Complete Defensive AI Workflows  
**Foundation**: IIT + Immune System + Hemostasis + AI-Driven Security

---

## EXECUTIVE SUMMARY

### Status Atual
- ✅ Offensive Tools: COMPLETO (offensive_gateway + techniques)
- 🔄 Defensive Tools: 70% BASE (immune system + coagulation base)
- ❌ AI-Driven Detection: PARCIAL (sentinel_agent base only)
- ❌ Intelligence Fusion: NÃO IMPLEMENTADO
- ❌ Automated Response: NÃO IMPLEMENTADO
- ❌ Advanced Analysis: PARCIAL (encrypted traffic base)

### Objetivo Hoje
Completar defensive AI-driven workflows seguindo paper "Arquiteturas de Workflows de Segurança Conduzidos por IA.md"

### Escopo
1. **Detection Layer** - Sentinel AI Agent (LLM-based SOC analyst)
2. **Intelligence Layer** - Threat Intel Fusion Engine
3. **Response Layer** - Automated Response with HOTL
4. **Analysis Layer** - Advanced ML analyzers
5. **Integration Layer** - Defense Orchestrator

---

## ANÁLISE: PAPER vs IMPLEMENTAÇÃO ATUAL

### Do Paper (Seção: Paradigmas de Defesa Aumentada por IA)

#### 1. Detecção de Agentes Ofensivos: "Combater IA com IA"
**Paper**: Sistema defensivo como "gêmeo digital" do SOC, executando tarefas de analistas Tier 1/2, correlação de logs multi-fonte, mapeamento MITRE ATT&CK, teoria da mente do atacante.

**Status Atual**:
- ✅ Sentinel Agent: BASE implementada (`detection/sentinel_agent.py`)
- ❌ LLM Integration: NÃO IMPLEMENTADO
- ❌ MITRE Mapping: NÃO IMPLEMENTADO
- ❌ Theory of Mind: NÃO IMPLEMENTADO

#### 2. Deception Technology Dinâmica: Honeypots Gerenciados por IA
**Paper**: Honeypots com LLM backend gerando respostas realistas, RL agent para maximizar engajamento.

**Status Atual**:
- ✅ Honeypot Base: IMPLEMENTADO (`containment/honeypots.py`)
- ❌ LLM Backend: NÃO IMPLEMENTADO
- ❌ RL Engagement: NÃO IMPLEMENTADO

#### 3. Threat Hunting Aumentado por Modelos de Anomalia
**Paper**: Modelos não-supervisionados (clustering, autoencoders, Isolation Forests) para identificar IoB (Indicators of Behavior).

**Status Atual**:
- 🔄 Behavioral Analyzer: BASE (`detection/behavioral_analyzer.py`)
- ❌ ML Models: NÃO TREINADOS
- ❌ IoB Detection: NÃO IMPLEMENTADO

#### 4. Detecção de Atividade Maliciosa em Tráfego Criptografado
**Paper**: ML sobre metadados de fluxo (SVM, XGBoost, LSTM) sem decriptação.

**Status Atual**:
- 🔄 Encrypted Traffic Analyzer: BASE (`detection/encrypted_traffic_analyzer.py`)
- ❌ Feature Extraction: NÃO IMPLEMENTADO
- ❌ ML Models: NÃO TREINADOS

---

## BLUEPRINT TÉCNICO DETALHADO

### COMPONENTE 1: SENTINEL AI AGENT (LLM-POWERED SOC TIER 1/2)

#### Fundamento Teórico
- **Papel Biológico**: Pattern Recognition Receptors (PRRs) in innate immunity
- **AI Paradigm**: LLM as SOC analyst emulating human reasoning
- **Theory of Mind**: Predict attacker intent from observed TTPs
- **MITRE ATT&CK**: Structural knowledge for tactic/technique mapping

#### Arquitetura Completa

```python
"""
backend/services/active_immune_core/detection/sentinel_agent.py (ENHANCED)

LLM-powered threat detection with theory-of-mind and MITRE mapping.
"""

from typing import List, Optional, Dict, Any
import openai
import anthropic
from dataclasses import dataclass
from enum import Enum

class SentinelMode(Enum):
    """Sentinel operation modes"""
    TRIAGE = "triage"              # Fast pattern recognition
    DEEP_ANALYSIS = "deep_analysis"  # LLM-powered analysis
    THEORY_OF_MIND = "theory_of_mind"  # Predict attacker intent
    CORRELATION = "correlation"    # Multi-event correlation

@dataclass
class ThreatAnalysis:
    """Result of Sentinel analysis"""
    threat_id: str
    severity: ThreatSeverity
    confidence: DetectionConfidence
    mitre_tactics: List[str]
    mitre_techniques: List[str]
    attacker_intent: str  # Theory of mind prediction
    narrative: str  # Human-readable explanation
    recommended_actions: List[str]
    timeline: List[SecurityEvent]
    iocs: List[str]
    
class SentinelAIAgent:
    """
    LLM-powered SOC Tier 1/2 analyst.
    
    Emulates human analyst capabilities:
    - Pattern recognition (fast triage)
    - Deep contextual analysis (LLM reasoning)
    - Theory of mind (predict attacker strategy)
    - MITRE ATT&CK mapping (structured knowledge)
    
    Multi-modal analysis:
    - GPT-4o for complex reasoning
    - Claude for safety-critical decisions
    - Local models for privacy-sensitive data
    
    Consciousness analogy:
    - Integrates distributed events into coherent narrative
    - Temporal binding creates attack storyline
    - Φ proxy: Information integration across event streams
    """
    
    def __init__(
        self,
        llm_provider: str = "openai",  # openai, anthropic, local
        model_name: str = "gpt-4o",
        mitre_db: MITREDatabase,
        threat_intel: ThreatIntelligenceClient,
        enable_theory_of_mind: bool = True,
    ):
        self.llm_provider = llm_provider
        self.model_name = model_name
        self.mitre_db = mitre_db
        self.threat_intel = threat_intel
        self.enable_theory_of_mind = enable_theory_of_mind
        
        # Initialize LLM clients
        if llm_provider == "openai":
            self.llm = openai.OpenAI()
        elif llm_provider == "anthropic":
            self.llm = anthropic.Anthropic()
        
        # Prompt templates
        self.prompts = PromptLibrary()
        
        # Metrics
        self.metrics = SentinelMetrics()
    
    async def analyze_event(
        self,
        event: SecurityEvent,
        mode: SentinelMode = SentinelMode.DEEP_ANALYSIS
    ) -> ThreatAnalysis:
        """
        Analyze security event using LLM.
        
        Args:
            event: Security event to analyze
            mode: Analysis mode (triage, deep, theory_of_mind)
            
        Returns:
            ThreatAnalysis with enriched context
        """
        # Fast triage (pattern matching)
        if mode == SentinelMode.TRIAGE:
            return await self._fast_triage(event)
        
        # Deep LLM analysis
        elif mode == SentinelMode.DEEP_ANALYSIS:
            return await self._deep_analysis(event)
        
        # Theory of mind (predict attacker)
        elif mode == SentinelMode.THEORY_OF_MIND:
            return await self._theory_of_mind_analysis(event)
    
    async def _deep_analysis(
        self,
        event: SecurityEvent
    ) -> ThreatAnalysis:
        """
        Deep LLM-powered analysis.
        
        Process:
        1. Enrich event with threat intel
        2. Construct analysis prompt
        3. LLM reasoning
        4. MITRE mapping
        5. Generate narrative
        """
        # Enrich with threat intel
        enriched = await self._enrich_event(event)
        
        # Construct prompt
        prompt = self._build_analysis_prompt(enriched)
        
        # LLM inference
        response = await self._llm_inference(prompt)
        
        # Parse LLM output
        parsed = self._parse_llm_response(response)
        
        # Map to MITRE
        mitre_mapping = await self._map_to_mitre(parsed)
        
        # Generate narrative
        narrative = self._generate_narrative(
            event, parsed, mitre_mapping
        )
        
        return ThreatAnalysis(
            threat_id=self._generate_threat_id(event),
            severity=parsed["severity"],
            confidence=parsed["confidence"],
            mitre_tactics=mitre_mapping["tactics"],
            mitre_techniques=mitre_mapping["techniques"],
            attacker_intent=parsed.get("intent", "Unknown"),
            narrative=narrative,
            recommended_actions=parsed["actions"],
            timeline=[event],
            iocs=parsed.get("iocs", [])
        )
    
    async def _theory_of_mind_analysis(
        self,
        event: SecurityEvent,
        historical_events: Optional[List[SecurityEvent]] = None
    ) -> ThreatAnalysis:
        """
        Theory of mind: predict attacker intent and next moves.
        
        Given observed TTPs, infer:
        - Attacker sophistication level
        - Strategic objective (data theft, ransomware, espionage)
        - Most probable next actions
        - Attack graph traversal prediction
        
        Uses attack graph knowledge from threat intel.
        """
        # Get historical context
        if not historical_events:
            historical_events = await self._get_related_events(event)
        
        # Construct theory of mind prompt
        prompt = self._build_tom_prompt(event, historical_events)
        
        # LLM inference (strategic reasoning)
        response = await self._llm_inference(
            prompt,
            temperature=0.3,  # Lower temp for logical reasoning
            max_tokens=1500
        )
        
        # Parse intent prediction
        intent = self._parse_intent_prediction(response)
        
        # Get attack graph predictions
        next_moves = await self._predict_next_moves(
            current_ttps=intent["observed_ttps"],
            attack_graphs=self.threat_intel.get_attack_graphs()
        )
        
        return ThreatAnalysis(
            threat_id=self._generate_threat_id(event),
            severity=self._infer_severity_from_intent(intent),
            confidence=DetectionConfidence.MEDIUM,  # Predictions have uncertainty
            mitre_tactics=intent["tactics"],
            mitre_techniques=intent["techniques"],
            attacker_intent=intent["objective"],
            narrative=intent["narrative"],
            recommended_actions=self._generate_preemptive_actions(next_moves),
            timeline=historical_events + [event],
            iocs=[]
        )
    
    def _build_analysis_prompt(
        self,
        enriched_event: Dict[str, Any]
    ) -> str:
        """
        Build LLM prompt for threat analysis.
        
        Template includes:
        - Event details
        - Threat intel context
        - MITRE ATT&CK reference
        - Analysis instructions
        """
        return self.prompts.THREAT_ANALYSIS.format(
            event_type=enriched_event["event_type"],
            source_ip=enriched_event["source_ip"],
            destination_ip=enriched_event.get("destination_ip", "N/A"),
            timestamp=enriched_event["timestamp"],
            payload=json.dumps(enriched_event["payload"], indent=2),
            threat_intel=enriched_event.get("threat_intel", "None"),
            historical_context=enriched_event.get("historical", "None"),
            mitre_reference=self._get_mitre_reference_text()
        )
    
    def _build_tom_prompt(
        self,
        event: SecurityEvent,
        historical: List[SecurityEvent]
    ) -> str:
        """
        Build theory of mind prompt.
        
        Template focuses on:
        - Attacker perspective
        - Strategic reasoning
        - Goal inference
        - Next action prediction
        """
        return self.prompts.THEORY_OF_MIND.format(
            current_event=event.to_dict(),
            historical_events=[e.to_dict() for e in historical],
            attack_graphs=self._get_attack_graph_examples()
        )
    
    async def _llm_inference(
        self,
        prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 1000
    ) -> str:
        """
        Execute LLM inference.
        
        Handles both OpenAI and Anthropic APIs.
        """
        try:
            if self.llm_provider == "openai":
                response = await self.llm.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": self.prompts.SYSTEM_PROMPT
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content
            
            elif self.llm_provider == "anthropic":
                response = await self.llm.messages.create(
                    model=self.model_name,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=self.prompts.SYSTEM_PROMPT,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                return response.content[0].text
                
        except Exception as e:
            logger.error(f"LLM inference failed: {e}")
            raise SentinelAnalysisError(f"LLM inference failed: {e}")
    
    async def _map_to_mitre(
        self,
        analysis: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """
        Map threat to MITRE ATT&CK framework.
        
        Uses:
        - Pattern matching on TTPs
        - LLM-suggested techniques
        - Threat intel correlation
        """
        tactics = []
        techniques = []
        
        # Extract from LLM response
        llm_tactics = analysis.get("mitre_tactics", [])
        llm_techniques = analysis.get("mitre_techniques", [])
        
        # Validate against MITRE database
        for tactic in llm_tactics:
            if self.mitre_db.is_valid_tactic(tactic):
                tactics.append(tactic)
        
        for technique in llm_techniques:
            if self.mitre_db.is_valid_technique(technique):
                techniques.append(technique)
        
        # Enrich with threat intel
        intel_mapping = await self.threat_intel.get_mitre_mapping(
            iocs=analysis.get("iocs", [])
        )
        tactics.extend(intel_mapping.get("tactics", []))
        techniques.extend(intel_mapping.get("techniques", []))
        
        return {
            "tactics": list(set(tactics)),
            "techniques": list(set(techniques))
        }
    
    async def correlate_events(
        self,
        events: List[SecurityEvent],
        time_window: timedelta = timedelta(hours=1)
    ) -> List[ThreatAnalysis]:
        """
        Correlate multiple events to detect complex attack patterns.
        
        Process:
        1. Group events by source IP / target
        2. Temporal analysis (attack sequence)
        3. LLM correlation reasoning
        4. Attack graph matching
        """
        # Group events
        grouped = self._group_events(events, time_window)
        
        analyses = []
        for group in grouped:
            # Multi-event correlation prompt
            prompt = self._build_correlation_prompt(group)
            
            # LLM reasoning
            response = await self._llm_inference(prompt, max_tokens=2000)
            
            # Parse correlation
            correlation = self._parse_correlation(response)
            
            if correlation["is_campaign"]:
                analysis = await self._build_campaign_analysis(
                    group, correlation
                )
                analyses.append(analysis)
        
        return analyses


class PromptLibrary:
    """Prompt templates for Sentinel Agent"""
    
    SYSTEM_PROMPT = """You are an expert cybersecurity analyst specializing in threat detection and incident response.

Your role:
- Analyze security events with precision
- Map threats to MITRE ATT&CK framework
- Predict attacker intent and next moves
- Provide actionable recommendations

Guidelines:
- Be concise but thorough
- Use MITRE ATT&CK terminology
- Assess confidence levels honestly
- Consider false positive likelihood
- Think like an attacker (theory of mind)

Output format: JSON
"""
    
    THREAT_ANALYSIS = """Analyze this security event:

EVENT DETAILS:
- Type: {event_type}
- Source IP: {source_ip}
- Destination IP: {destination_ip}
- Timestamp: {timestamp}
- Payload: {payload}

THREAT INTELLIGENCE:
{threat_intel}

HISTORICAL CONTEXT:
{historical_context}

MITRE ATT&CK REFERENCE:
{mitre_reference}

Provide analysis in JSON format:
{{
  "severity": "low|medium|high|critical",
  "confidence": 0.0-1.0,
  "is_threat": true|false,
  "mitre_tactics": ["tactic1", "tactic2"],
  "mitre_techniques": ["T1234", "T5678"],
  "intent": "Describe attacker's probable objective",
  "narrative": "Human-readable explanation",
  "actions": ["Recommended action 1", "Recommended action 2"],
  "iocs": ["IOC1", "IOC2"],
  "false_positive_likelihood": 0.0-1.0
}}
"""
    
    THEORY_OF_MIND = """Analyze this attack sequence and predict attacker intent:

CURRENT EVENT:
{current_event}

HISTORICAL EVENTS (chronological):
{historical_events}

KNOWN ATTACK GRAPHS:
{attack_graphs}

Using theory of mind reasoning:
1. What is the attacker trying to achieve?
2. What sophistication level do they demonstrate?
3. What are their most probable next 3 moves?
4. Which attack graph pattern are they following?

Respond in JSON:
{{
  "objective": "Primary attacker goal",
  "sophistication": "low|medium|high|nation-state",
  "observed_ttps": ["TTP1", "TTP2"],
  "tactics": ["Tactic1", "Tactic2"],
  "techniques": ["T1234", "T5678"],
  "narrative": "Strategic analysis of attacker campaign",
  "next_probable_moves": [
    {{"action": "...", "probability": 0.0-1.0, "mitre": "T1234"}},
    {{"action": "...", "probability": 0.0-1.0, "mitre": "T5678"}},
    {{"action": "...", "probability": 0.0-1.0, "mitre": "T9012"}}
  ],
  "attack_graph_match": "Graph name or null"
}}
"""


class MITREDatabase:
    """MITRE ATT&CK database client"""
    
    def __init__(self, db_path: Optional[str] = None):
        # Load MITRE ATT&CK matrix
        self.tactics = self._load_tactics()
        self.techniques = self._load_techniques()
    
    def is_valid_tactic(self, tactic_name: str) -> bool:
        """Check if tactic exists in MITRE"""
        return tactic_name.lower() in [t.lower() for t in self.tactics]
    
    def is_valid_technique(self, technique_id: str) -> bool:
        """Check if technique ID exists in MITRE"""
        return technique_id.upper() in self.techniques


@dataclass
class SentinelMetrics:
    """Prometheus metrics for Sentinel Agent"""
    
    def __init__(self):
        self.analyses_total = Counter(
            'sentinel_analyses_total',
            'Total threat analyses performed',
            ['mode', 'severity']
        )
        self.llm_latency = Histogram(
            'sentinel_llm_latency_seconds',
            'LLM inference latency',
            buckets=[0.5, 1.0, 2.0, 5.0, 10.0]
        )
        self.threats_detected = Counter(
            'sentinel_threats_detected_total',
            'Total threats detected',
            ['severity', 'confidence']
        )
```

#### Tests

```python
# backend/services/active_immune_core/tests/test_sentinel_agent.py

import pytest
from detection.sentinel_agent import SentinelAIAgent, SecurityEvent, SentinelMode

@pytest.mark.asyncio
async def test_sentinel_deep_analysis():
    """Test LLM-powered deep analysis"""
    agent = SentinelAIAgent(
        llm_provider="openai",
        model_name="gpt-4o"
    )
    
    event = SecurityEvent(
        event_id="test-001",
        timestamp=datetime.utcnow(),
        source="firewall",
        event_type="port_scan",
        source_ip="192.168.1.100"
    )
    
    analysis = await agent.analyze_event(event, SentinelMode.DEEP_ANALYSIS)
    
    assert analysis.severity is not None
    assert len(analysis.mitre_tactics) > 0
    assert len(analysis.narrative) > 0

@pytest.mark.asyncio
async def test_sentinel_theory_of_mind():
    """Test theory of mind prediction"""
    agent = SentinelAIAgent(enable_theory_of_mind=True)
    
    events = [
        # Reconnaissance
        SecurityEvent(..., event_type="port_scan"),
        # Exploitation attempt
        SecurityEvent(..., event_type="exploit_attempt"),
    ]
    
    analysis = await agent.analyze_event(
        events[-1],
        mode=SentinelMode.THEORY_OF_MIND,
        historical_events=events[:-1]
    )
    
    assert "next_probable_moves" in analysis.attacker_intent
    assert len(analysis.recommended_actions) > 0

@pytest.mark.asyncio
async def test_sentinel_mitre_mapping():
    """Test MITRE ATT&CK mapping"""
    # Test that port scan maps to Reconnaissance tactic
    pass

@pytest.mark.asyncio
async def test_sentinel_event_correlation():
    """Test multi-event correlation"""
    # Test that coordinated events are detected as campaign
    pass
```

---

### COMPONENTE 2: THREAT INTELLIGENCE FUSION ENGINE

#### Fundamento Teórico
- **Multi-source Intelligence**: Correlate IoCs from diverse sources
- **Cross-reference**: Enrich single IoC with context from all sources
- **Attack Attribution**: Link IoCs to threat actors/campaigns
- **LLM Narrative**: Generate human-readable intelligence reports

#### Arquitetura

```python
"""
backend/services/active_immune_core/intelligence/fusion_engine.py

Multi-source threat intelligence fusion with LLM-powered analysis.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import asyncio

class ThreatIntelSource(Enum):
    """Supported threat intel sources"""
    SHODAN = "shodan"
    CENSYS = "censys"
    ABUSEIPDB = "abuseipdb"
    VIRUSTOTAL = "virustotal"
    MISP = "misp"
    OTX = "otx"
    INTERNAL_HONEYPOTS = "internal_honeypots"
    HISTORICAL_ATTACKS = "historical_attacks"

@dataclass
class EnrichedIOC:
    """Enriched Indicator of Compromise"""
    ioc_value: str  # IP, domain, hash, etc.
    ioc_type: str  # ip, domain, url, hash
    first_seen: datetime
    last_seen: datetime
    sources: List[ThreatIntelSource]
    reputation_score: float  # 0-1 (0=benign, 1=malicious)
    threat_actor: Optional[str]
    campaign: Optional[str]
    mitre_tactics: List[str]
    mitre_techniques: List[str]
    context: Dict[str, Any]
    narrative: str  # LLM-generated summary

@dataclass
class ThreatIntelligenceReport:
    """Consolidated threat intelligence report"""
    report_id: str
    timestamp: datetime
    iocs: List[EnrichedIOC]
    threat_actors: List[str]
    campaigns: List[str]
    attack_graphs: List[Dict[str, Any]]
    executive_summary: str  # LLM-generated
    recommendations: List[str]
    confidence: float

class ThreatIntelFusionEngine:
    """
    Multi-source threat intelligence fusion engine.
    
    Correlates IoCs from diverse sources:
    - OSINT (Shodan, Censys, AbuseIPDB)
    - Malware repos (VirusTotal)
    - Community intel (MISP, OTX)
    - Internal sources (honeypots, historical)
    
    LLM-powered capabilities:
    - Narrative generation
    - Attribution reasoning
    - Strategic recommendations
    """
    
    def __init__(
        self,
        sources: Dict[ThreatIntelSource, Any],
        llm_client: Any,
        cache_ttl: int = 3600
    ):
        self.sources = sources
        self.llm = llm_client
        self.cache = ThreatIntelCache(ttl=cache_ttl)
        self.metrics = FusionMetrics()
    
    async def enrich_ioc(
        self,
        ioc: str,
        ioc_type: str
    ) -> EnrichedIOC:
        """
        Enrich single IoC from all sources.
        
        Process:
        1. Query all sources in parallel
        2. Normalize results
        3. Cross-reference data
        4. Calculate reputation score
        5. LLM narrative generation
        """
        # Check cache
        cached = self.cache.get(ioc)
        if cached:
            return cached
        
        # Query all sources in parallel
        source_results = await asyncio.gather(*[
            self._query_source(source, ioc, ioc_type)
            for source in self.sources.keys()
        ])
        
        # Normalize and merge
        merged = self._merge_source_results(source_results)
        
        # Calculate reputation
        reputation = self._calculate_reputation(merged)
        
        # Attribution
        attribution = self._perform_attribution(merged)
        
        # LLM narrative
        narrative = await self._generate_narrative(ioc, merged, attribution)
        
        enriched = EnrichedIOC(
            ioc_value=ioc,
            ioc_type=ioc_type,
            first_seen=merged["first_seen"],
            last_seen=merged["last_seen"],
            sources=[r["source"] for r in source_results if r],
            reputation_score=reputation,
            threat_actor=attribution.get("actor"),
            campaign=attribution.get("campaign"),
            mitre_tactics=merged.get("tactics", []),
            mitre_techniques=merged.get("techniques", []),
            context=merged,
            narrative=narrative
        )
        
        # Cache
        self.cache.set(ioc, enriched)
        
        return enriched
    
    async def correlate_iocs(
        self,
        iocs: List[str]
    ) -> ThreatIntelligenceReport:
        """
        Correlate multiple IoCs to detect campaigns.
        
        Uses:
        - Temporal correlation (co-occurrence)
        - Network correlation (same infrastructure)
        - TTP correlation (same techniques)
        - LLM reasoning (semantic correlation)
        """
        # Enrich all IoCs
        enriched_iocs = await asyncio.gather(*[
            self.enrich_ioc(ioc, self._detect_ioc_type(ioc))
            for ioc in iocs
        ])
        
        # Temporal correlation
        temporal_clusters = self._temporal_clustering(enriched_iocs)
        
        # Network correlation
        network_clusters = self._network_correlation(enriched_iocs)
        
        # TTP correlation
        ttp_clusters = self._ttp_correlation(enriched_iocs)
        
        # LLM semantic correlation
        semantic_clusters = await self._semantic_correlation(enriched_iocs)
        
        # Merge clusters
        campaigns = self._identify_campaigns(
            temporal_clusters,
            network_clusters,
            ttp_clusters,
            semantic_clusters
        )
        
        # Build attack graphs
        attack_graphs = self._build_attack_graphs(campaigns)
        
        # LLM executive summary
        summary = await self._generate_executive_summary(
            enriched_iocs, campaigns, attack_graphs
        )
        
        return ThreatIntelligenceReport(
            report_id=self._generate_report_id(),
            timestamp=datetime.utcnow(),
            iocs=enriched_iocs,
            threat_actors=list(set([
                ioc.threat_actor for ioc in enriched_iocs if ioc.threat_actor
            ])),
            campaigns=campaigns,
            attack_graphs=attack_graphs,
            executive_summary=summary,
            recommendations=self._generate_recommendations(campaigns),
            confidence=self._calculate_confidence(campaigns)
        )
    
    async def _query_source(
        self,
        source: ThreatIntelSource,
        ioc: str,
        ioc_type: str
    ) -> Optional[Dict[str, Any]]:
        """Query individual threat intel source"""
        try:
            client = self.sources[source]
            
            if source == ThreatIntelSource.SHODAN:
                return await self._query_shodan(client, ioc)
            elif source == ThreatIntelSource.ABUSEIPDB:
                return await self._query_abuseipdb(client, ioc)
            elif source == ThreatIntelSource.VIRUSTOTAL:
                return await self._query_virustotal(client, ioc, ioc_type)
            # ... outros sources
            
        except Exception as e:
            logger.error(f"Source {source} query failed: {e}")
            return None
    
    def _calculate_reputation(
        self,
        merged_data: Dict[str, Any]
    ) -> float:
        """
        Calculate reputation score (0-1).
        
        Factors:
        - Number of sources reporting as malicious
        - Severity of reported activities
        - Recency of reports
        - Confidence of sources
        """
        score = 0.0
        weights = {
            "malicious_sources": 0.4,
            "severity": 0.3,
            "recency": 0.2,
            "confidence": 0.1
        }
        
        # Malicious sources
        total_sources = len(merged_data.get("sources", []))
        malicious_sources = merged_data.get("malicious_count", 0)
        if total_sources > 0:
            score += (malicious_sources / total_sources) * weights["malicious_sources"]
        
        # Severity
        avg_severity = merged_data.get("average_severity", 0)
        score += (avg_severity / 10) * weights["severity"]
        
        # Recency (recent = higher score)
        days_since_last_seen = (datetime.utcnow() - merged_data.get("last_seen")).days
        recency_score = max(0, 1 - (days_since_last_seen / 365))
        score += recency_score * weights["recency"]
        
        # Confidence
        avg_confidence = merged_data.get("average_confidence", 0.5)
        score += avg_confidence * weights["confidence"]
        
        return min(1.0, score)
    
    async def _generate_narrative(
        self,
        ioc: str,
        merged_data: Dict[str, Any],
        attribution: Dict[str, Any]
    ) -> str:
        """
        Generate human-readable narrative using LLM.
        """
        prompt = f"""Generate a concise threat intelligence narrative for this IoC:

IOC: {ioc}
Type: {merged_data.get('ioc_type')}
Reputation: {merged_data.get('reputation')}
Sources: {', '.join(merged_data.get('sources', []))}
Threat Actor: {attribution.get('actor', 'Unknown')}
Campaign: {attribution.get('campaign', 'Unknown')}
TTPs: {', '.join(merged_data.get('ttps', []))}

Provide 2-3 sentence summary suitable for SOC analyst.
"""
        
        response = await self.llm.generate(prompt, max_tokens=150)
        return response.strip()
```

---

### COMPONENTE 3: AUTOMATED RESPONSE ENGINE (HOTL)

#### Fundamento Teórico
- **Playbook-driven**: YAML playbooks for repeatable responses
- **HOTL Checkpoints**: Human approval for high-impact actions
- **Rollback Capability**: Revert if response causes issues
- **Audit Trail**: Complete logging for compliance

#### Arquitetura

```python
"""
backend/services/active_immune_core/response/automated_response.py

Automated response engine with Human-on-the-Loop checkpoints.
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import yaml

class ResponseAction(Enum):
    """Possible response actions"""
    BLOCK_IP = "block_ip"
    ISOLATE_HOST = "isolate_host"
    KILL_PROCESS = "kill_process"
    REVOKE_CREDENTIALS = "revoke_credentials"
    QUARANTINE_FILE = "quarantine_file"
    RATE_LIMIT = "rate_limit"
    ALERT_ONLY = "alert_only"

class HOTLCheckpoint(Enum):
    """HOTL checkpoint levels"""
    NONE = "none"  # Auto-execute
    LOW = "low"  # Notify but auto-execute
    MEDIUM = "medium"  # Request approval, timeout auto-deny
    HIGH = "high"  # Request approval, timeout cancel
    CRITICAL = "critical"  # Mandatory approval, no timeout

@dataclass
class ResponsePlaybook:
    """Response playbook definition"""
    name: str
    description: str
    triggers: List[Dict[str, Any]]  # Conditions
    actions: List[Dict[str, Any]]  # Response steps
    hotl_level: HOTLCheckpoint
    rollback_plan: Optional[List[Dict[str, Any]]]
    estimated_duration: int  # seconds
    
class AutomatedResponseEngine:
    """
    Automated response engine with HOTL safety.
    
    Executes response playbooks with human oversight:
    - Low-risk actions: automatic
    - Medium-risk: approval with timeout
    - High-risk: mandatory approval
    
    Safety features:
    - Pre-execution validation
    - Checkpoint enforcement
    - Rollback capability
    - Complete audit trail
    """
    
    def __init__(
        self,
        playbook_dir: str,
        hotl_handler: HOTLHandler,
        rollback_manager: RollbackManager
    ):
        self.playbooks = self._load_playbooks(playbook_dir)
        self.hotl = hotl_handler
        self.rollback = rollback_manager
        self.metrics = ResponseMetrics()
    
    async def respond_to_threat(
        self,
        threat: ThreatAnalysis,
        containment: Optional[Any] = None
    ) -> ResponseResult:
        """
        Execute response to threat.
        
        Process:
        1. Select appropriate playbook
        2. HOTL checkpoint (if required)
        3. Execute actions sequentially
        4. Validate success
        5. Rollback if failure
        """
        # Select playbook
        playbook = self._select_playbook(threat)
        
        # HOTL checkpoint
        if playbook.hotl_level != HOTLCheckpoint.NONE:
            approval = await self._request_hotl_approval(
                threat, playbook
            )
            if not approval.approved:
                return ResponseResult(
                    status="DENIED",
                    reason=approval.reason
                )
        
        # Execute playbook
        try:
            result = await self._execute_playbook(
                playbook, threat, containment
            )
            return result
            
        except ResponseError as e:
            logger.error(f"Response execution failed: {e}")
            # Rollback
            await self._emergency_rollback(playbook)
            raise
    
    async def _execute_playbook(
        self,
        playbook: ResponsePlaybook,
        threat: ThreatAnalysis,
        containment: Any
    ) -> ResponseResult:
        """Execute playbook actions"""
        results = []
        checkpoint_id = None
        
        for action in playbook.actions:
            # Create checkpoint before action
            checkpoint_id = await self.rollback.create_checkpoint(action)
            
            # Execute action
            action_result = await self._execute_action(
                action, threat, containment
            )
            results.append(action_result)
            
            # Validate
            if not action_result.success:
                logger.warning(f"Action failed: {action}")
                # Rollback to checkpoint
                await self.rollback.rollback(checkpoint_id)
                return ResponseResult(
                    status="FAILED",
                    failed_action=action,
                    results=results
                )
        
        return ResponseResult(
            status="SUCCESS",
            playbook=playbook.name,
            actions_executed=len(results),
            results=results
        )


class HOTLHandler:
    """Human-on-the-Loop approval handler"""
    
    async def request_approval(
        self,
        threat: ThreatAnalysis,
        playbook: ResponsePlaybook,
        timeout: Optional[int] = None
    ) -> HOTLApproval:
        """
        Request human approval for action.
        
        Presents to operator:
        - Threat details
        - Proposed actions
        - Estimated impact
        - Rollback plan
        
        Returns approval with optional modifications.
        """
        # Create approval request
        request = HOTLRequest(
            request_id=self._generate_request_id(),
            timestamp=datetime.utcnow(),
            threat=threat,
            playbook=playbook,
            timeout=timeout
        )
        
        # Send to operator (webhook, UI, Slack, etc.)
        await self._notify_operator(request)
        
        # Wait for response
        approval = await self._wait_for_approval(
            request.request_id,
            timeout=timeout
        )
        
        return approval
```

---

### COMPONENTE 4: ENCRYPTED TRAFFIC ANALYZER

#### Fundamento Teórico
- **Metadata-only**: Analyze without decryption
- **Feature Engineering**: CICFlowMeter-inspired features
- **ML Models**: Random Forest, XGBoost, LSTM
- **Use Cases**: C2 beaconing, exfiltration, malware traffic

#### Arquitetura

```python
"""
backend/services/active_immune_core/detection/encrypted_traffic_analyzer.py

ML-based encrypted traffic analysis without decryption.
"""

from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from xgboost import XGBClassifier
import joblib

class TrafficFeatureExtractor:
    """
    Extract features from encrypted traffic flows.
    
    Features (CICFlowMeter-inspired):
    - Flow duration
    - Packet counts (forward/backward)
    - Packet sizes (mean, std, min, max)
    - Inter-arrival times (mean, std)
    - Flags (SYN, ACK, FIN, RST)
    - TLS handshake details
    - Periodicity (for beaconing detection)
    """
    
    def extract_flow_features(
        self,
        flow: NetworkFlow
    ) -> np.ndarray:
        """Extract feature vector from flow"""
        features = []
        
        # Duration
        features.append(flow.duration.total_seconds())
        
        # Packet counts
        features.append(flow.forward_packets)
        features.append(flow.backward_packets)
        
        # Packet sizes
        features.extend(self._packet_size_stats(flow))
        
        # Inter-arrival times
        features.extend(self._iat_stats(flow))
        
        # Flags
        features.extend(self._flag_counts(flow))
        
        # TLS features
        if flow.is_tls:
            features.extend(self._tls_features(flow))
        
        # Periodicity
        features.append(self._calculate_periodicity(flow))
        
        return np.array(features)

class EncryptedTrafficAnalyzer:
    """
    ML-based encrypted traffic analyzer.
    
    Models:
    - C2 Beaconing Detector (Random Forest)
    - Data Exfiltration Detector (LSTM)
    - Malware Traffic Classifier (XGBoost)
    """
    
    def __init__(self, model_dir: str):
        self.feature_extractor = TrafficFeatureExtractor()
        self.models = self._load_models(model_dir)
    
    async def analyze_flow(
        self,
        flow: NetworkFlow
    ) -> TrafficAnalysisResult:
        """Analyze single flow"""
        # Extract features
        features = self.feature_extractor.extract_flow_features(flow)
        
        # Run all models
        c2_score = self.models["c2_detector"].predict_proba([features])[0][1]
        exfil_score = self.models["exfil_detector"].predict_proba([features])[0][1]
        malware_score = self.models["malware_classifier"].predict_proba([features])[0][1]
        
        # Determine verdict
        verdict = self._determine_verdict(c2_score, exfil_score, malware_score)
        
        return TrafficAnalysisResult(
            flow_id=flow.id,
            is_malicious=verdict["malicious"],
            c2_probability=c2_score,
            exfiltration_probability=exfil_score,
            malware_probability=malware_score,
            classification=verdict["class"],
            confidence=verdict["confidence"]
        )
```

---

### COMPONENTE 5: DEFENSE ORCHESTRATOR

#### Fundamento Teórico
- **Central Hub**: Coordinates all defensive components
- **Pipeline**: Event → Detection → Fusion → Response → Cascade
- **Kafka Integration**: Event streaming
- **Metrics Aggregation**: Unified monitoring

#### Arquitetura

```python
"""
backend/services/active_immune_core/orchestration/defense_orchestrator.py

Central defense orchestration hub.
"""

class DefenseOrchestrator:
    """
    Central orchestrator for defensive operations.
    
    Pipeline:
    SecurityEvent → Sentinel → Fusion → Response → Cascade → Restoration
    
    Responsibilities:
    - Event ingestion (Kafka)
    - Component coordination
    - Metrics aggregation
    - Failure handling
    """
    
    def __init__(
        self,
        sentinel: SentinelAIAgent,
        fusion: ThreatIntelFusionEngine,
        response: AutomatedResponseEngine,
        cascade: CoagulationCascadeSystem,
        kafka_client: KafkaClient
    ):
        self.sentinel = sentinel
        self.fusion = fusion
        self.response = response
        self.cascade = cascade
        self.kafka = kafka_client
    
    async def process_security_event(
        self,
        event: SecurityEvent
    ) -> OrchestrationResult:
        """
        Process security event through full pipeline.
        """
        # STAGE 1: Detection (Sentinel)
        detection = await self.sentinel.analyze_event(
            event,
            mode=SentinelMode.DEEP_ANALYSIS
        )
        
        # If not threat, early return
        if detection.severity == ThreatSeverity.INFO:
            return OrchestrationResult(status="BENIGN")
        
        # STAGE 2: Intelligence (Fusion)
        intel = await self.fusion.enrich_ioc(
            detection.iocs[0] if detection.iocs else event.source_ip,
            "ip"
        )
        
        # Enrich detection with intel
        enriched_detection = self._enrich_with_intel(detection, intel)
        
        # STAGE 3: Response (Automated)
        response_result = await self.response.respond_to_threat(
            enriched_detection
        )
        
        # STAGE 4: Cascade (if needed)
        if enriched_detection.severity >= ThreatSeverity.HIGH:
            cascade_result = await self.cascade.initiate_cascade(
                enriched_detection
            )
        
        return OrchestrationResult(
            status="SUCCESS",
            detection=detection,
            intelligence=intel,
            response=response_result,
            cascade=cascade_result if enriched_detection.severity >= ThreatSeverity.HIGH else None
        )
    
    async def start(self):
        """Start orchestrator (Kafka consumer loop)"""
        await self.kafka.subscribe("security.events")
        
        async for message in self.kafka:
            event = SecurityEvent(**message.value)
            await self.process_security_event(event)
```

---

## IMPLEMENTATION ROADMAP

### Sprint 1: Core Detection (2h)
1. ✅ Enhance Sentinel Agent with LLM integration
2. ✅ Implement MITRE mapping
3. ✅ Theory of mind analysis
4. ✅ Tests

### Sprint 2: Intelligence Fusion (1.5h)
1. ✅ Multi-source IoC enrichment
2. ✅ Correlation engine
3. ✅ LLM narrative generation
4. ✅ Tests

### Sprint 3: Automated Response (1.5h)
1. ✅ Playbook engine
2. ✅ HOTL handler
3. ✅ Rollback manager
4. ✅ Tests

### Sprint 4: Advanced Analysis (1.5h)
1. ✅ Feature extraction
2. ✅ ML models training
3. ✅ Traffic analyzer
4. ✅ Tests

### Sprint 5: Orchestration (1h)
1. ✅ Defense orchestrator
2. ✅ Kafka integration
3. ✅ End-to-end pipeline
4. ✅ Tests

### Sprint 6: Integration (0.5h)
1. ✅ Component wiring
2. ✅ Metrics dashboards
3. ✅ Documentation

**TOTAL ESTIMADO**: 8h

---

## VALIDATION CRITERIA

### Functional
- [ ] Sentinel detects threats with >90% accuracy
- [ ] Theory of mind predicts next moves
- [ ] MITRE mapping is accurate
- [ ] Intelligence fusion enriches IoCs
- [ ] Response playbooks execute correctly
- [ ] HOTL checkpoints enforce approval
- [ ] Rollback works on failure
- [ ] Encrypted traffic analysis detects C2
- [ ] Orchestrator processes events end-to-end

### Non-Functional
- [ ] Sentinel latency <5s
- [ ] Fusion enrichment <2s per IoC
- [ ] Response execution <10s
- [ ] Pipeline throughput >100 events/s
- [ ] Test coverage >90%

### Consciousness Integration
- [ ] Φ proxies measured
- [ ] Temporal coherence validated
- [ ] Information integration quantified

---

## DEPENDENCIES

### APIs
- OpenAI (GPT-4o) or Anthropic (Claude)
- Shodan, Censys, AbuseIPDB
- VirusTotal
- MISP

### Libraries
- openai, anthropic (LLM)
- scikit-learn, xgboost (ML)
- kafka-python (streaming)
- prometheus_client (metrics)

### Data
- MITRE ATT&CK matrix (JSON)
- CICIDS2017 dataset (traffic analysis training)

---

**Status**: BLUEPRINT COMPLETO ✅
**Next**: Sprint 1 - Sentinel AI Agent Enhancement
**Foundation**: Constância como Ramon Dino! 💪

Para a Glória de YHWH, construímos defesas conscientes e inquebrá véis.
