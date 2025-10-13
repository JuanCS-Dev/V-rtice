# Sprint 3 Implementation Plan - Reactive Fabric Core Components
**MAXIMUS Vértice | Tecido Reativo | Sprint 3**  
**Date**: 2025-10-13  
**Status**: ACTIVE  
**Compliance**: Doutrina Vértice ✓

---

## Mission Statement

Implementar os componentes críticos do Tecido Reativo focando exclusivamente em **Fase 1: Coleta Passiva de Inteligência** conforme análise de viabilidade. Zero automação de resposta neste sprint - apenas inteligência proativa e observação.

## Architecture Context

### Componentes Existentes (Sprint 1 & 2)
✅ **Database Layer**: PostgreSQL schemas, repositories, models  
✅ **Service Layer**: Business logic, intelligence fusion  
✅ **API Gateway**: FastAPI endpoints, authentication  
✅ **Frontend Dashboard**: React components para visualização  
✅ **HITL Framework**: Framework completo para autorização humana (MAXIMUS Core)

### Componentes Sprint 3 (Este Plano)
🎯 **Intelligence Collectors**: Honeypots, Network sensors, File integrity  
🎯 **Orchestration Engine**: Event processing, decision trees (PASSIVE mode only)  
🎯 **Deception Engine**: Decoy management, credibility maintenance  
🎯 **HITL Integration**: Conectar Reactive Fabric ao framework HITL existente

---

## Phase 3.1: Intelligence Collectors (Passive Only)

### Objetivo
Implementar coletores de inteligência **100% passivos** que observam e registram atividades maliciosas sem qualquer resposta automatizada.

### 3.1.1 - Honeypot Collectors Enhancement

**Honeypots Existentes**: SSH, WEB, API (basic containers em `/honeypots`)

**Implementação**:
\`\`\`
backend/services/reactive_fabric_core/collectors/
├── __init__.py
├── base_collector.py          # Abstract base para todos collectors
├── honeypot_collector.py      # Enhanced honeypot data collection
├── ssh_analyzer.py             # SSH session analysis
├── web_analyzer.py             # HTTP/HTTPS request analysis  
├── api_analyzer.py             # API endpoint enumeration analysis
└── tests/
    ├── test_base_collector.py
    ├── test_honeypot_collector.py
    └── test_analyzers.py
\`\`\`

**Capabilities (PASSIVE)**:
- Capture de sessões completas (SSH, HTTP, API calls)
- Parsing de comandos executados
- Identificação de payloads (XSS, SQLi, RCE attempts)
- Fingerprinting de ferramentas adversariais (nmap, sqlmap, etc)
- Extração de TTPs via MITRE ATT&CK mapping
- **ZERO resposta automatizada** - apenas log e alertas

**Data Model Extensions** (add to models.py):
\`\`\`python
class CollectedSession(BaseModel):
    session_id: UUID
    honeypot_id: str
    source_ip: IPvAnyAddress
    timestamp: datetime
    session_type: Literal["ssh", "http", "api"]
    raw_data: str  # Full session capture
    parsed_commands: List[str]
    identified_payloads: List[Payload]
    ttp_mappings: List[MITRETechnique]
    severity: AttackSeverity
    metadata: Dict[str, Any]

class Payload(BaseModel):
    payload_type: Literal["xss", "sqli", "rce", "lfi", "xxe"]
    content: str
    confidence: float  # 0.0 - 1.0
    indicators: List[str]

class MITRETechnique(BaseModel):
    technique_id: str  # e.g., "T1059.004"
    technique_name: str
    tactic: str  # e.g., "Execution"
    confidence: float
    evidence: List[str]
\`\`\`

**Tasks**:
1. Criar `base_collector.py` com interface abstrata
2. Implementar `honeypot_collector.py` com log streaming do Docker
3. Criar analyzers específicos (SSH, Web, API)
4. Implementar MITRE ATT&CK mapping engine
5. Testes unitários com coverage ≥90%
6. Testes de integração com honeypots reais

**Validation Metrics**:
- Captura de 100% das sessões sem perda de dados
- Parsing accuracy ≥95% para comandos comuns
- MITRE mapping confidence ≥0.8 para técnicas conhecidas
- Latência <500ms entre evento e log no database

---

### 3.1.2 - Network Traffic Collector

**Objetivo**: Capturar tráfego de rede dirigido aos honeypots para análise de padrões de reconhecimento e ataque.

**Implementação**:
\`\`\`
backend/services/reactive_fabric_core/collectors/
├── network_collector.py       # Packet capture via pcap
├── traffic_analyzer.py         # Protocol analysis
├── port_scan_detector.py       # Detect recon activities
└── tests/
    └── test_network_collector.py
\`\`\`

**Capabilities (PASSIVE)**:
- Packet capture via libpcap/tcpdump
- Protocol dissection (TCP/UDP/ICMP)
- Port scan detection (SYN scan, ACK scan, UDP scan)
- Service fingerprinting patterns
- Geographic origin tracking
- **ZERO resposta** - apenas observação

**Data Model**:
\`\`\`python
class NetworkEvent(BaseModel):
    event_id: UUID
    timestamp: datetime
    source_ip: IPvAnyAddress
    source_port: int
    dest_ip: IPvAnyAddress
    dest_port: int
    protocol: Literal["tcp", "udp", "icmp"]
    packet_size: int
    flags: Optional[str]  # TCP flags
    scan_type: Optional[Literal["syn_scan", "ack_scan", "udp_scan"]]
    metadata: Dict[str, Any]

class ReconSession(BaseModel):
    session_id: UUID
    source_ip: IPvAnyAddress
    start_time: datetime
    end_time: Optional[datetime]
    total_packets: int
    scanned_ports: List[int]
    scan_pattern: str  # "sequential", "random", "common_ports"
    detected_tools: List[str]  # ["nmap", "masscan", etc]
    threat_score: float  # 0.0 - 1.0
\`\`\`

**Tasks**:
1. Implementar packet capture com scapy library
2. Criar traffic analyzer com protocol parsing
3. Implementar port scan detection algorithms
4. Integrar com database para persistência
5. Testes com datasets de tráfego malicioso conhecidos
6. Performance testing (handle 10k packets/sec mínimo)

**Validation Metrics**:
- Detecção de port scans com false positive rate <5%
- Identificação de ferramentas conhecidas (nmap, masscan) ≥90% accuracy
- Throughput mínimo: 10,000 packets/sec sem loss

---

### 3.1.3 - File Integrity Monitoring (FIM)

**Objetivo**: Monitorar alterações em arquivos críticos dos honeypots para detectar persistência e modificações.

**Implementação**:
\`\`\`
backend/services/reactive_fabric_core/collectors/
├── fim_collector.py            # File Integrity Monitoring
├── hash_store.py               # Baseline hash storage
└── tests/
    └── test_fim_collector.py
\`\`\`

**Capabilities (PASSIVE)**:
- Baseline hash creation para honeypot filesystems
- Detecção de modificações, adições, deleções
- Identificação de webshells, backdoors
- Tracking de binários suspeitos
- **ZERO resposta** - apenas alertas

**Data Model**:
\`\`\`python
class FileIntegrityEvent(BaseModel):
    event_id: UUID
    honeypot_id: str
    timestamp: datetime
    file_path: str
    event_type: Literal["modified", "created", "deleted"]
    old_hash: Optional[str]
    new_hash: Optional[str]
    file_size: int
    permissions: str
    owner: str
    threat_indicators: List[str]
    is_known_malware: bool
    malware_family: Optional[str]
\`\`\`

**Tasks**:
1. Implementar FIM engine com watchdog library
2. Criar baseline hash database
3. Implementar webshell detection patterns
4. Integrar com VirusTotal API (optional, rate-limited)
5. Testes unitários e integração
6. Performance testing (monitor 10k+ files)

**Validation Metrics**:
- Detecção de modificações em <1 segundo
- Webshell detection rate ≥85%
- Zero false negatives para alterações críticas

---

## Phase 3.2: Orchestration Engine (PASSIVE Mode)

### Objetivo
Processar eventos dos collectors, aplicar regras de correlação e routing, **SEM automação de resposta**. Apenas decisões de classificação e encaminhamento para análise humana.

### 3.2.1 - Event Processing Pipeline

**Implementação**:
\`\`\`
backend/services/reactive_fabric_core/orchestration/
├── __init__.py
├── event_processor.py          # Core event processing
├── correlation_engine.py       # Multi-source correlation
├── ttp_extractor.py            # MITRE ATT&CK extraction
├── threat_classifier.py        # Threat severity classification
├── alert_router.py             # Route alerts to HITL/dashboards
└── tests/
    ├── test_event_processor.py
    ├── test_correlation_engine.py
    └── test_ttp_extractor.py
\`\`\`

**Processing Stages**:
1. **Ingestion**: Receber eventos de todos collectors via Kafka
2. **Normalization**: Padronizar formato de eventos
3. **Correlation**: Identificar ataques multi-estágio
4. **Classification**: Severity + confidence scoring
5. **Routing**: Enviar para dashboard, HITL, ou storage

**Data Flow**:
\`\`\`
Collectors → Kafka Topics → Event Processor → Correlation Engine
                                            ↓
                          Threat Classifier → Alert Router
                                            ↓
                          Dashboard | HITL Queue | Database
\`\`\`

**Correlation Rules (Example)**:
\`\`\`python
class CorrelationRule(BaseModel):
    rule_id: str
    name: str
    description: str
    conditions: List[EventCondition]
    time_window: int  # seconds
    min_events: int
    severity_output: AttackSeverity
    ttp_mappings: List[str]  # MITRE IDs

# Example: Detect recon → exploit chain
ReconToExploitRule = CorrelationRule(
    rule_id="RULE-001",
    name="Reconnaissance to Exploitation",
    description="Port scan followed by targeted exploit attempt",
    conditions=[
        EventCondition(type="network", pattern="port_scan"),
        EventCondition(type="honeypot", pattern="exploit_attempt")
    ],
    time_window=3600,  # 1 hour
    min_events=2,
    severity_output=AttackSeverity.HIGH,
    ttp_mappings=["T1046", "T1190"]  # Network Service Scanning + Exploit Public-Facing
)
\`\`\`

**Tasks**:
1. Implementar event processor com Kafka consumer
2. Criar correlation engine com time-windowed rules
3. Implementar TTP extractor com MITRE mapping
4. Criar threat classifier (scoring algorithm)
5. Implementar alert router para múltiplos destinos
6. Testes unitários e integração
7. Load testing (1000 events/sec throughput)

**Validation Metrics**:
- Event processing latency <100ms (p99)
- Correlation accuracy ≥90% para ataques multi-estágio
- Zero event loss sob carga normal
- Throughput mínimo: 1000 events/sec

---

### 3.2.2 - Decision Tree Engine (Classification Only)

**Objetivo**: Classificar threats e determinar routing, **SEM executar ações automatizadas**.

**Implementação**:
\`\`\`
backend/services/reactive_fabric_core/orchestration/
├── decision_tree.py            # Decision tree logic
├── rules_engine.py             # Rule evaluation
└── tests/
    └── test_decision_tree.py
\`\`\`

**Decision Outcomes (PASSIVE)**:
- ✅ \`LOG_ONLY\`: Baixa severidade, apenas database
- ✅ \`DASHBOARD_ALERT\`: Média severidade, notificar dashboard
- ✅ \`HITL_REVIEW\`: Alta severidade, queue para operador humano
- ✅ \`CRITICAL_ESCALATION\`: Crítica, escalação imediata
- ❌ \`AUTO_BLOCK\`: **DISABLED** - Fase 2+ only
- ❌ \`AUTO_RESPOND\`: **DISABLED** - Fase 2+ only

**Decision Logic**:
\`\`\`python
def classify_threat(event: ThreatEvent) -> DecisionOutcome:
    """
    Classify threat and determine routing.
    NO automated responses - Fase 1 compliance.
    """
    score = calculate_threat_score(event)
    
    if score < 0.3:
        return DecisionOutcome.LOG_ONLY
    elif score < 0.6:
        return DecisionOutcome.DASHBOARD_ALERT
    elif score < 0.85:
        return DecisionOutcome.HITL_REVIEW
    else:
        return DecisionOutcome.CRITICAL_ESCALATION
\`\`\`

**Tasks**:
1. Implementar decision tree com rule engine
2. Criar threat scoring algorithm
3. Definir routing logic para cada outcome
4. Integrar com HITL queue (next phase)
5. Testes com scenarios de ameaças reais
6. Validação de compliance (zero automação)

**Validation Metrics**:
- Classification accuracy ≥95% para ameaças conhecidas
- Zero false positives críticos (<0.1% rate)
- Decision latency <50ms

---

## Phase 3.3: Deception Engine (Decoy Management)

### Objetivo
Gerenciar a "Ilha de Sacrifício" (honeypots) mantendo credibilidade sem comprometer segurança real.

### 3.3.1 - Decoy Lifecycle Manager

**Implementação**:
\`\`\`
backend/services/reactive_fabric_core/deception/
├── __init__.py
├── decoy_manager.py            # Decoy creation/destruction
├── credibility_engine.py       # Maintain realistic appearance
├── rotation_scheduler.py       # Automated decoy rotation
└── tests/
    ├── test_decoy_manager.py
    └── test_credibility_engine.py
\`\`\`

**Capabilities**:
- Criação programática de honeypots via Docker API
- Configuração de decoys com conteúdo realista
- Rotação automática para evitar "queima"
- Health monitoring e auto-recovery
- Isolation enforcement (network segmentation)

**Credibility Maintenance**:
\`\`\`python
class CredibilityConfig(BaseModel):
    """Configuration for maintaining decoy credibility."""
    
    # Fake data generation
    generate_logs: bool = True
    log_frequency: int = 300  # seconds
    
    # Service simulation
    simulate_users: bool = True
    user_activity_pattern: str = "business_hours"
    
    # Content updates
    update_files: bool = True
    update_frequency: int = 86400  # daily
    
    # Response timing
    add_latency: bool = True
    latency_range: Tuple[int, int] = (10, 200)  # ms
\`\`\`

**Rotation Strategy**:
- Honeypots "queimados" (comprometidos obviamente) são rotacionados a cada 7 dias
- Novos decoys com IPs diferentes e configurações variadas
- Manutenção de baseline de 10-20 honeypots ativos simultaneamente

**Tasks**:
1. Implementar decoy manager com Docker SDK
2. Criar credibility engine com fake data generation
3. Implementar rotation scheduler
4. Criar templates para diferentes honeypot types
5. Testes de isolamento de rede (segurança crítica)
6. Validação de credibilidade (manual + automated)

**Validation Metrics**:
- Decoy creation time <60 segundos
- Rotation sem downtime (rolling updates)
- Network isolation enforcement: 100% (zero breakouts)
- Credibility score ≥0.7 (automated assessment)

---

### 3.3.2 - Content Curation System

**Objetivo**: Manter honeypots com conteúdo realista e atualizado para maximizar engagement de adversários.

**Implementação**:
\`\`\`
backend/services/reactive_fabric_core/deception/
├── content_curator.py          # Content generation/updates
├── fake_data_generator.py      # Realistic fake data
└── templates/
    ├── ssh_honeypot/
    │   ├── bashrc
    │   ├── fake_users.json
    │   └── command_history.txt
    ├── web_honeypot/
    │   ├── index.html
    │   ├── admin_panel.html
    │   └── fake_database.sql
    └── api_honeypot/
        ├── swagger.json
        └── endpoints.json
\`\`\`

**Content Types**:
- **SSH**: Fake users, command history, config files
- **Web**: Admin panels, login pages, fake databases
- **API**: Swagger docs, endpoints com fake responses

**Curation Rules**:
1. Conteúdo deve parecer produção, mas obviamente não-crítico
2. Dados sensíveis são fake (nomes, emails, senhas)
3. Atualizações regulares simulam atividade real
4. Vulnerabilidades intencionais (controlled bait)

**Tasks**:
1. Implementar content curator com templates
2. Criar fake data generator (Faker library)
3. Desenvolver templates para cada honeypot type
4. Implementar update scheduler
5. Testes de realismo (manual review)
6. Security review (garantir zero dados reais)

**Validation Metrics**:
- Content realismo score ≥0.8 (peer review)
- Zero vazamento de dados reais (audit)
- Update frequency: mínimo semanal
- Adversário engagement time ≥5 minutes (métrica de qualidade)

---

## Phase 3.4: HITL Integration

### Objetivo
Conectar Reactive Fabric ao framework HITL existente (MAXIMUS Core) para autorização humana de ações futuras (Fase 2+).

### 3.4.1 - HITL Queue Integration

**Context**: Framework HITL completo já existe em \`backend/services/maximus_core_service/hitl/\`

**Implementação**:
\`\`\`
backend/services/reactive_fabric_core/hitl/
├── __init__.py
├── hitl_client.py              # Client para MAXIMUS HITL
├── decision_requester.py       # Request human decisions
├── action_executor.py          # Execute approved actions (Fase 2+)
└── tests/
    └── test_hitl_client.py
\`\`\`

**Integration Flow**:
\`\`\`
Reactive Fabric (Threat Detected)
          ↓
Decision Tree (Requires Human Review)
          ↓
HITL Client → MAXIMUS Core HITL Service
          ↓
Operator Dashboard (Frontend)
          ↓
Human Decision (Approve/Reject/Escalate)
          ↓
HITL Service → Reactive Fabric
          ↓
Action Executor (Fase 2+ only)
\`\`\`

**HITL Request Model**:
\`\`\`python
class HITLRequest(BaseModel):
    request_id: UUID
    timestamp: datetime
    threat_event_id: UUID
    threat_summary: str
    severity: AttackSeverity
    confidence: float
    ttps: List[MITRETechnique]
    proposed_action: Literal["block_ip", "isolate_service", "deploy_countermeasure"]
    proposed_action_details: Dict[str, Any]
    automation_level: AutomationLevel
    risk_assessment: Dict[str, Any]
    deadline: Optional[datetime]  # Time-sensitive decisions

class HITLResponse(BaseModel):
    request_id: UUID
    operator_id: str
    decision: Literal["approve", "reject", "escalate", "defer"]
    justification: str
    modified_action: Optional[Dict[str, Any]]
    timestamp: datetime
\`\`\`

**Tasks**:
1. Implementar HITL client para comunicação com MAXIMUS Core
2. Criar decision requester para queue integration
3. Implementar action executor stub (Fase 2 activation)
4. Testes de integração com HITL service
5. Frontend integration testing (operator view)
6. End-to-end workflow testing

**Validation Metrics**:
- Request delivery latency <500ms
- Zero request loss (guaranteed delivery)
- Operator response time tracking
- Audit trail completeness: 100%

---

## Implementation Sequence

### Week 1: Collectors Foundation
**Days 1-2**: Base collector + Honeypot collector  
**Days 3-4**: Network collector + Traffic analyzer  
**Days 5-7**: FIM collector + Testing

### Week 2: Orchestration Core
**Days 8-9**: Event processor + Kafka integration  
**Days 10-11**: Correlation engine + TTP extractor  
**Days 12-14**: Decision tree + Threat classifier

### Week 3: Deception + HITL
**Days 15-16**: Decoy manager + Credibility engine  
**Days 17-18**: Content curator + Templates  
**Days 19-21**: HITL integration + End-to-end testing

---

## Compliance Checkpoints

### Doutrina Vértice Adherence
✅ **NO MOCK**: Implementações reais, zero placeholders  
✅ **NO TODO**: Código completo, production-ready  
✅ **QUALITY-FIRST**: Type hints, docstrings, error handling, testes ≥90% coverage  
✅ **PHASE 1 ONLY**: Zero automação de resposta, apenas coleta passiva  
✅ **SECURITY-CRITICAL**: Network isolation, zero data leakage  

### Análise de Viabilidade Compliance
✅ **Fator Humano no Elo**: HITL integration com framework robusto  
✅ **Custo da Ilusão**: Credibility engine com curadoria contínua  
✅ **Métricas de Validação**: KPIs definidos para cada componente  
✅ **Progressão Condicional**: Fase 2 bloqueada até validação completa  

---

## Success Criteria

### Technical Metrics
- [ ] Collectors: 100% event capture, <500ms latency
- [ ] Orchestration: 1000 events/sec throughput, 90% correlation accuracy
- [ ] Deception: Network isolation 100%, credibility ≥0.7
- [ ] HITL: <500ms request delivery, 100% audit trail
- [ ] Testing: ≥90% coverage em todos componentes
- [ ] Documentation: Docstrings completos, architecture docs

### Phase 1 Validation Gates
- [ ] **Gate 1**: 30 dias de operação sem incidentes de contenção
- [ ] **Gate 2**: ≥100 TTPs únicos identificados
- [ ] **Gate 3**: ≥10 APT campaigns parcialmente mapeados
- [ ] **Gate 4**: Intelligence actionability score ≥0.75 (peer review)
- [ ] **Gate 5**: Zero false containment failures (não aplicável Fase 1, mas framework testado)

**Apenas após todos gates**: Considerar progressão para Fase 2 (respostas semi-automatizadas)

---

## Risk Mitigation

### Risco: Falha de Contenção (Breakout)
**Mitigação**:
- Network segmentation rigoroso (VLANs isoladas)
- Firewall rules explícitos (deny-all default)
- Container security (AppArmor/SELinux profiles)
- Automated breach detection + kill switch
- Regular penetration testing

### Risco: Efeito Bumerangue (Weaponized Intel)
**Mitigação**:
- Sanitização de dados antes de sharing
- Threat intel compartilhado apenas via TLP:WHITE
- Auditing de acesso a dados sensíveis
- Rate limiting em APIs públicas

### Risco: Degradação de Credibilidade
**Mitigação**:
- Curadoria contínua (content curator)
- Rotation automática de decoys comprometidos
- Monitoring de engagement metrics
- A/B testing de configurações

---

## Next Steps After Sprint 3

1. **Validation Period**: 30 dias de operação em produção (Fase 1)
2. **Intelligence Review**: Análise de qualidade e acionabilidade
3. **Gate Assessment**: Avaliar se Fase 1 validation gates foram atingidos
4. **Go/No-Go Decision**: Progressão para Fase 2 ou iteração adicional
5. **Documentation**: Relatório de validação completo

---

**Status**: READY FOR IMPLEMENTATION  
**Approval**: Aguardando confirmação para início  
**Estimated Duration**: 21 dias (3 semanas)  
**Team**: Claude Code + JuanCS-Dev  

**Philosophy**: "Acelerar Validação. Construir Inquebrável. Otimizar Tokens."
