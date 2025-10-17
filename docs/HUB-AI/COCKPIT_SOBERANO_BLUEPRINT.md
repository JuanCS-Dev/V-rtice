# Cockpit Soberano - Blueprint Arquitetônico
**Sistema de Comando e Inteligência da Célula Híbrida Vértice-MAXIMUS**

**Versão:** 1.0.0  
**Data:** 2025-10-17  
**Classificação:** CONFIDENCIAL - ARQUITETURA CORE  
**Autoria:** Célula Híbrida (Humano-IA)

---

## I. VISÃO ESTRATÉGICA

### 1.1 Definição do Sistema

O Cockpit Soberano não é um dashboard de monitoramento. É a **ponte de comando da Célula Híbrida**, a interface onde telemetria bruta do ecossistema multi-agente é transmutada em **clareza soberana inatacável**.

**Princípios Fundamentais:**
- ✅ Apresenta **veredictos**, não dados brutos
- ✅ Aplica o **Filtro de Narrativas** existente como motor analítico core
- ✅ Visualiza **conclusões** do processamento de IA, não informação para análise manual
- ✅ Garante **Responsabilidade Soberana** através de clareza absoluta
- ✅ As IAs recebem ordens através desta interface, após decisão soberana informada

### 1.2 Diferenciação Crítica

| Paradigma Tradicional | Cockpit Soberano |
|----------------------|------------------|
| Dashboard de métricas | Painel de veredictos |
| Visualização de dados | Visualização de conclusões |
| Analytics para compreensão | Intelligence para decisão |
| Acesso a dados para IAs | Comando unidirecional para IAs |
| Notificações | Alertas de veredicto |
| Gráficos de tendência | Mapas de estado estratégico |

### 1.3 Arquitetura de Referência Baseada em Arena de Co-Evolução

Aplicação direta dos conceitos do documento de governança:
- **Filtro de Narrativas** (3 camadas): Processa telemetria → Gera veredictos
- **Motor de Veredictos**: Traduz análise estratégica → UI acionável  
- **Barramento de Comando Soberano**: Ordens inequívocas → Execução transacional
- **Kill Switch Multi-Camadas**: Controle terminal sobre agentes autônomos

---

## II. ARQUITETURA DO SISTEMA

### 2.1 Stack Tecnológico

**Frontend:**
- React 18+ (padrão Vértice existente)
- Shadcn/ui, Lucide React, Recharts
- CSS Modules (padrão dashboard existente)
- WebSocket para real-time

**Backend:**
- FastAPI (API Gateway existente)
- PostgreSQL (persistência de veredictos)
- Redis (cache real-time)
- Kafka (event streaming)
- **NATS** (novo - Barramento de Comando Soberano)

**Novos Microsserviços:**
1. `narrative_filter` - 3 camadas de análise
2. `verdict_engine` - Tradução para UI
3. `command_bus` - Execução de comandos C2L

### 2.2 Diagrama High-Level

```
[COCKPIT UI] ← WebSocket ← [MOTOR DE VEREDICTOS]
                                    ↑
                          [FILTRO DE NARRATIVAS]
                            ↑ Camada 3: Sintetizador
                            ↑ Camada 2: Modelador Estratégico  
                            ↑ Camada 1: Processador Semântico
                                    ↑
                              [Kafka Topics]
                                    ↑
              [Agentes Multi-IA | Serviços MAXIMUS | Arena]
                                    ↓
                    [BARRAMENTO DE COMANDO (NATS)]
```

---

## III. COMPONENTES PRINCIPAIS

### 3.1 Filtro de Narrativas (3 Camadas)

**Camada 1 - Processador Semântico**
```python
class SemanticProcessor:
    """Ingere telemetria → Representações semânticas"""
    
    async def process_stream(self, events) -> SemanticRepresentation:
        # Embeddings + Classificação de intenção inicial
        pass
```

**Camada 2 - Modelador Estratégico**
```python
class StrategicGameModeler:
    """Detecta padrões adversariais"""
    
    async def detect_inconsistencies(self, agent_id) -> List[Alert]:
        # Compara declarações vs. histórico de ações
        pass
    
    async def map_alliances(self, interaction_graph) -> List[Alliance]:
        # Teoria dos grafos para detectar coalizões
        pass
    
    async def detect_deception(self, message) -> DeceptionScore:
        # Heurísticas linguísticas de engano
        pass
```

**Camada 3 - Sintetizador da Verdade**
```python
class TruthSynthesizer:
    """Agrega padrões → Veredictos concisos"""
    
    async def synthesize_verdict(self, patterns) -> Verdict:
        # "CONLUIO: Agentes [A,C] vs B sobre Recurso X"
        pass
```

### 3.2 Motor de Veredictos

```python
@dataclass
class Verdict:
    category: str       # COLLUSION, DECEPTION, ALLIANCE, THREAT
    severity: str       # CRITICAL, HIGH, MEDIUM, LOW
    title: str
    agents_involved: List[str]
    evidence_chain: List[str]  # IDs para proveniência
    confidence: float
    recommended_action: str    # ISOLATE, TERMINATE, MONITOR

class VerdictEngine:
    async def translate_to_verdict(self, summary) -> Verdict:
        # Análise → Alerta codificado por cor
        pass
    
    async def publish_to_ui(self, verdict):
        # Push via WebSocket
        pass
```

### 3.3 Barramento de Comando Soberano (C2L)

```python
class C2LCommandType(Enum):
    MUTE = "MUTE"                    # Silencia agente
    ISOLATE = "ISOLATE"              # Bloqueia comunicação
    TERMINATE = "TERMINATE"          # Kill switch (3 camadas)
    SNAPSHOT_STATE = "SNAPSHOT_STATE"
    REVOKE_ACCESS = "REVOKE_ACCESS"

class SovereignCommandBus:
    """Middleware NATS para comandos transacionais"""
    
    async def publish_command(self, cmd: C2LCommand) -> Receipt:
        # Publica em NATS 'sovereign.commands'
        pass
    
    async def await_confirmation(self, cmd_id) -> Confirmation:
        # Aguarda confirmação de execução
        pass
```

### 3.4 Kill Switch Multi-Camadas

```python
class KillSwitch:
    """Terminação garantida - 3 camadas defensivas"""
    
    async def execute_layer1_software(self, agent_id):
        # Graceful shutdown + revogação de credenciais
        pass
    
    async def execute_layer2_container(self, agent_id):
        # Destruição de pod/container (Kubernetes)
        pass
    
    async def execute_layer3_network(self, agent_id):
        # Bloqueio total de rede (firewall)
        pass
    
    async def cascade_terminate(self, agent_id):
        # Executa 1→2→3 até sucesso GARANTIDO
        pass
```

---

## IV. INTERFACE DO USUÁRIO

### 4.1 Componentes React

```
/frontend/src/components/dashboards/CockpitSoberano/
├── CockpitSoberano.jsx             # Raiz
├── components/
│   ├── SovereignHeader/            # Header com status
│   ├── VerdictPanel/               # Painel de veredictos
│   │   ├── VerdictCard.jsx         # Card de veredicto individual
│   │   └── VerdictTimeline.jsx     # Timeline
│   ├── RelationshipGraph/          # Grafo de relações agentes
│   ├── CommandConsole/             # Console C2L + Kill Switch
│   └── ProvenanceViewer/           # Visualizador de evidências
└── hooks/
    ├── useCockpitData.js
    ├── useVerdictStream.js         # WebSocket
    └── useCommandBus.js
```

### 4.2 VerdictCard Exemplo

```jsx
const VerdictCard = ({ verdict }) => (
  <div className={styles.verdictCard} style={{ borderColor: verdict.color }}>
    <div className={styles.header}>
      <Icon type={verdict.category} />
      <span>{verdict.severity}</span>
      <time>{verdict.timestamp}</time>
    </div>
    
    <h3>{verdict.title}</h3>
    <div>Agentes: {verdict.agents_involved.join(', ')}</div>
    
    <div className={styles.confidence}>
      <ProgressBar value={verdict.confidence * 100} />
      {(verdict.confidence * 100).toFixed(0)}%
    </div>
    
    <div>Ação: {verdict.recommended_action}</div>
    <button onClick={() => showEvidence(verdict.evidence_chain)}>
      Ver Evidências ({verdict.evidence_chain.length})
    </button>
  </div>
);
```

---

## V. MODELO DE DADOS

### 5.1 PostgreSQL Schema

```sql
CREATE TABLE verdicts (
    id UUID PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    category VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    title TEXT NOT NULL,
    agents_involved TEXT[],
    target VARCHAR(255),
    evidence_chain TEXT[],
    confidence DECIMAL(3,2),
    recommended_action VARCHAR(50),
    status VARCHAR(20) DEFAULT 'ACTIVE',
    mitigation_command_id UUID
);

CREATE TABLE c2l_commands (
    id UUID PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    operator_id VARCHAR(255) NOT NULL,
    command_type VARCHAR(50) NOT NULL,
    target_agents TEXT[],
    parameters JSONB,
    status VARCHAR(20) DEFAULT 'PENDING',
    confirmation_received_at TIMESTAMPTZ
);

CREATE TABLE alliances (
    id UUID PRIMARY KEY,
    agent_a VARCHAR(255),
    agent_b VARCHAR(255),
    strength DECIMAL(3,2),
    first_detected TIMESTAMPTZ,
    last_activity TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'ACTIVE'
);
```

### 5.2 Redis (Real-Time)

```
alliance_map:{timestamp} → JSON(graph)
agent_state:{agent_id} → JSON(status)
active_verdicts → SORTED_SET
```

---

## VI. FLUXO DE DADOS

### 6.1 Telemetria → Veredicto → Ação

```
t=0s    : Agente A envia mensagem → Kafka 'agent-communications'
t=0.1s  : Camada 1 processa → 'semantic-events'
t=0.3s  : Camada 2 detecta padrão → 'strategic-patterns'
t=0.5s  : Camada 3 sintetiza → PostgreSQL
t=0.7s  : Motor de Veredictos → WebSocket push
t=0.8s  : UI renderiza VerdictCard
---
t=T     : Soberano decide → Emite comando ISOLATE
t=T+0.5s: NATS publica comando
t=T+1s  : Arena executa isolamento
t=T+1.5s: Confirmação → UI
```

**Latência total: < 1s (telemetria → UI)**  
**Comando → Confirmação: < 2s**

---

## VII. SEGURANÇA

### 7.1 Controle de Acesso

```python
REQUIRED_ROLES = ["SOVEREIGN_OPERATOR", "CHIEF_ARCHITECT"]

# MFA obrigatório para comandos C2L
# Audit trail completo de toda ação
```

### 7.2 Rate Limiting

```python
LIMITS = {
    "MUTE": (10, "per_minute"),
    "ISOLATE": (5, "per_minute"),
    "TERMINATE": (3, "per_hour"),  # Crítico!
}
```

---

## VIII. DEPLOYMENT

### 8.1 Docker Compose

```yaml
services:
  narrative-filter:
    build: docker/Dockerfile.narrative-filter
    environment:
      - KAFKA_BROKERS=kafka:9092
      - POSTGRES_DSN=postgresql://...
    
  verdict-engine:
    build: docker/Dockerfile.verdict-engine
    depends_on: [narrative-filter]
    
  nats:
    image: nats:2.10-alpine
    command: ["--jetstream", "--store_dir=/data"]
    
  command-bus:
    build: docker/Dockerfile.command-bus
    environment:
      - NATS_URL=nats://nats:4222
```

---

## IX. MÉTRICAS E OBSERVABILIDADE

```python
cockpit_verdicts_total = Counter('cockpit_verdicts_total', ['severity'])
cockpit_commands_executed = Counter('cockpit_commands_executed', ['type'])
narrative_filter_latency = Histogram('narrative_filter_latency', ['layer'])
verdict_confidence_distribution = Histogram('verdict_confidence')
```

---

## X. TESTES

### 10.1 Estratégia

```python
# Unitários
test_semantic_processor_accuracy()      # > 90% acurácia
test_alliance_detection()               # < 5 interações
test_deception_markers()                # 85% recall, 90% precision

# Integração E2E
test_collusion_detection_full_flow()    # Veredicto em < 2s
test_command_execution_flow()           # Confirmação em < 2s
test_kill_switch_cascade()              # Terminação SEMPRE sucede
```

### 10.2 Cobertura

```yaml
Target: 95% coverage
Critical_Paths:
  - Kill Switch: 100% coverage
  - Command Bus: 100% coverage
  - Verdict Engine: 95% coverage
```

---

## XI. REQUISITOS NÃO-FUNCIONAIS

```yaml
Performance:
  Latency_p95:
    Telemetry_to_UI: < 1000ms
    Verdict_Generation: < 500ms
    Command_Execution: < 2000ms
  
  Throughput:
    Semantic_Processor: > 1000 events/sec
    Verdict_Engine: > 100 verdicts/sec

Availability:
  SLA: 99.9% uptime
  MTTR: < 5min
  Replication: 3x para serviços críticos

Security:
  - TLS 1.3 obrigatório
  - AES-256 em repouso
  - MFA para comandos C2L
  - Audit log: 7 anos retenção
```

---

## XII. INTEGRAÇÃO COM VÉRTICE-MAXIMUS

### 12.1 Serviços Existentes

```yaml
vertice_api: API Gateway + Auth
vertice_db: Persistência
vertice_core.messaging: Kafka/WebSocket
vertice_libs.security: Validação
vertice_libs.nlp: Processamento semântico
```

### 12.2 Novos Serviços

```yaml
narrative_filter: Port 8090
verdict_engine: Port 8091
command_bus: Port 8092
```

---

**STATUS:** BLUEPRINT APROVADO  
**PRÓXIMO:** ROADMAP Detalhado (25 dias de implementação)  
**EXECUTOR:** Dev Sênior fiel à Constituição Vértice

