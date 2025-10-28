# 🏗️ TECHNICAL ARCHITECTURE - Active Immune System

**Versão**: 1.0
**Data**: 2025-01-06
**Status**: Production-Ready Specs

---

## 📋 TECH STACK

```yaml
Core Service:
  Framework: FastAPI 0.104+
  Language: Python 3.11+
  Port: 8200

Communication:
  Cytokines: Apache Kafka 3.6 (topics: immunis.cytokines.*)
  Hormones: Redis Pub/Sub 7.2 (channels: hormonio:*)

Databases:
  Agent State: Redis (ephemeral)
  Memory: PostgreSQL 15 (persistent)
  Metrics: Prometheus + TimescaleDB

Orchestration:
  Runtime: Kubernetes 1.28+
  Agents: DaemonSets (1 per node)
  Lymphnodes: StatefulSets (persistent ID)

Observability:
  Metrics: Prometheus (scrape /metrics)
  Logs: Structured JSON (stdout)
  Tracing: OpenTelemetry (optional)
  Dashboard: Grafana
```

---

## 🗂️ SERVICE STRUCTURE

```
backend/services/active_immune_core/
├── main.py                          # FastAPI app (port 8200)
├── config.py                        # Pydantic settings
├── agents/
│   ├── __init__.py
│   ├── base.py                      # AgenteImunologicoBase
│   ├── macrofago.py                 # MacrofagoDigital
│   ├── nk_cell.py                   # CelulaNKDigital
│   └── neutrofilo.py                # NeutrofiloDigital
├── coordination/
│   ├── __init__.py
│   ├── coordinator.py               # CoordenadorCentral
│   ├── lymphnode.py                 # LinfonodoDigital
│   └── circulation.py               # SistemaCirculacaoDigital
├── communication/
│   ├── __init__.py
│   ├── cytokines.py                 # Kafka producer/consumer
│   └── hormones.py                  # Redis Pub/Sub
├── homeostasis/
│   ├── __init__.py
│   ├── states.py                    # Estados metabólicos
│   └── cycles.py                    # SistemaCircadiano
├── observability/
│   ├── __init__.py
│   ├── vitals.py                    # SinaisVitaisOrganismo
│   └── metrics.py                   # Prometheus exporter
├── models/
│   ├── __init__.py
│   ├── agent.py                     # Pydantic models
│   ├── cytokine.py
│   └── hormone.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── Dockerfile
├── requirements.txt
└── k8s/
    ├── deployment.yaml
    ├── service.yaml
    └── configmap.yaml
```

---

## 🔌 API ENDPOINTS (REST)

```python
# Health & Metrics
GET  /health                         # Health check
GET  /metrics                        # Prometheus metrics
GET  /vitals                         # Sinais vitais JSON

# Agent Management
GET    /agents                       # List all agents
GET    /agents/{id}                  # Get agent details
POST   /agents/{id}/activate         # Activate agent
POST   /agents/{id}/deactivate       # Deactivate agent
DELETE /agents/{id}                  # Remove agent

# Lymphnode Management
GET  /lymphnodes                     # List lymphnodes
GET  /lymphnodes/{id}                # Get lymphnode status
POST /lymphnodes/{id}/sync           # Force sync

# Homeostasis
GET  /homeostasis/state              # Current state
POST /homeostasis/transition         # Force transition
    Body: {"target_state": "inflamacao", "reason": "manual"}

# Hormone Secretion
POST /hormones/secrete               # Secrete hormone
    Body: {
      "glandula": "adrenal",
      "hormonio": "adrenalina",
      "nivel": 0.85,
      "duracao": 300
    }

# Mission Control
GET  /missions                       # List active missions
POST /missions                       # Create mission
GET  /missions/{id}                  # Mission status
```

---

## 📊 DATA MODELS (Pydantic)

### AgenteState

```python
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any

class AgentType(str, Enum):
    MACROFAGO = "macrofago"
    NEUTROFILO = "neutrofilo"
    NK_CELL = "nk_cell"
    CELULA_B = "celula_b"
    CELULA_T_CITOTOXICA = "celula_t_citotoxica"
    CELULA_T_HELPER = "celula_t_helper"
    CELULA_DENDRITICA = "celula_dendritica"
    CELULA_TREG = "celula_treg"

class AgentStatus(str, Enum):
    DORMINDO = "dormindo"
    PATRULHANDO = "patrulhando"
    INVESTIGANDO = "investigando"
    NEUTRALIZANDO = "neutralizando"
    FAGOCITANDO = "fagocitando"
    MORTO = "morto"

class AgenteState(BaseModel):
    """Estado completo de um agente (armazenado em Redis)"""

    # Identificação
    id: str = Field(..., description="UUID do agente")
    tipo: AgentType
    geracao: int = Field(default=1, description="Geração (clonagem)")
    pai_id: Optional[str] = Field(None, description="ID do agente pai (se clone)")

    # Estado operacional
    status: AgentStatus = Field(default=AgentStatus.DORMINDO)
    ativo: bool = Field(default=False)
    essencial: bool = Field(default=False, description="Não pode dormir")

    # Localização & Patrulha
    localizacao_atual: str = Field(..., description="Subnet/host atual")
    area_patrulha: str = Field(..., description="Área designada")
    ultima_patrulha: datetime = Field(default_factory=datetime.now)
    intervalo_patrulha: int = Field(default=900, description="Segundos entre patrulhas")

    # Parâmetros comportamentais
    nivel_agressividade: float = Field(default=0.5, ge=0.0, le=1.0)
    sensibilidade: float = Field(default=0.7, ge=0.0, le=1.0)
    taxa_processamento: float = Field(default=1.0, ge=0.5, le=2.0)

    # Especialização (clones)
    especializacao: Optional[str] = Field(None, description="Tipo de ameaça")
    receptor_padrao: Optional[Dict[str, Any]] = Field(None)
    afinidade_ameaca: Optional[float] = Field(None, ge=0.0, le=1.0)

    # Estatísticas
    deteccoes_total: int = Field(default=0)
    neutralizacoes_total: int = Field(default=0)
    falsos_positivos: int = Field(default=0)
    uptime_segundos: int = Field(default=0)

    # Metadados
    criado_em: datetime = Field(default_factory=datetime.now)
    atualizado_em: datetime = Field(default_factory=datetime.now)
    linfonodo_id: Optional[str] = Field(None)

    class Config:
        use_enum_values = True
```

### CytokineMessage

```python
class CytokineType(str, Enum):
    ALARME = "alarme"
    RECRUTAMENTO = "recrutamento"
    INFLAMACAO = "inflamacao"
    SUPRESSAO = "supressao"
    FEEDBACK = "feedback"

class CytokineMessage(BaseModel):
    """Mensagem de citocina (Kafka)"""

    tipo: CytokineType
    emissor_id: str = Field(..., description="ID do agente emissor")
    timestamp: datetime = Field(default_factory=datetime.now)
    prioridade: int = Field(default=1, ge=1, le=10)

    # Payload específico por tipo
    payload: Dict[str, Any] = Field(...)

    # Opcional: área alvo
    area_alvo: Optional[str] = Field(None)

    # TTL (tempo de vida da mensagem)
    ttl_segundos: int = Field(default=300)

    class Config:
        use_enum_values = True

# Exemplos de payloads:
# ALARME: {"alvo": "192.168.1.100", "tipo_ameaca": "ransomware", "score": 0.87}
# RECRUTAMENTO: {"quantidade": 50, "tipo_agente": "neutrofilo", "urgencia": 0.9}
# INFLAMACAO: {"nivel": 0.85, "motivo": "ddos_attack"}
```

### HormonioMessage

```python
class GlandulaType(str, Enum):
    PITUITARIA = "pituitaria"
    ADRENAL = "adrenal"
    TIREOIDE = "tireoide"
    PINEAL = "pineal"

class HormonioType(str, Enum):
    MODO_OPERACIONAL = "modo_operacional"
    ADRENALINA = "adrenalina"
    METABOLISMO = "metabolismo"
    MELATONINA = "melatonina"

class HormonioMessage(BaseModel):
    """Mensagem de hormônio (Redis Pub/Sub)"""

    glandula: GlandulaType
    hormonio: HormonioType
    nivel: float = Field(..., ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.now)
    duracao_estimada: int = Field(..., description="Segundos")

    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True
```

---

## 🔄 COMMUNICATION PROTOCOLS

### Kafka Topics (Cytokines)

```yaml
Topics:
  immunis.cytokines.alarme:
    partitions: 10
    replication-factor: 3
    retention.ms: 3600000  # 1 hour

  immunis.cytokines.recrutamento:
    partitions: 5
    replication-factor: 3
    retention.ms: 1800000  # 30 min

  immunis.cytokines.inflamacao:
    partitions: 3
    replication-factor: 3
    retention.ms: 7200000  # 2 hours

  immunis.cytokines.supressao:
    partitions: 3
    replication-factor: 3
    retention.ms: 3600000  # 1 hour

  immunis.cytokines.feedback:
    partitions: 10
    replication-factor: 3
    retention.ms: 86400000  # 24 hours

Consumer Groups:
  - macrofago-consumers
  - neutrofilo-consumers
  - nk-cell-consumers
  - coordinator-consumers
```

### Redis Channels (Hormones)

```yaml
Channels:
  hormonio:adrenalina:
    pattern: pub/sub
    subscribers: all_agents

  hormonio:modo_operacional:
    pattern: pub/sub
    subscribers: all_agents

  hormonio:metabolismo:
    pattern: pub/sub
    subscribers: all_agents

  hormonio:melatonina:
    pattern: pub/sub
    subscribers: all_agents

Redis Keys:
  agent:state:{agent_id}:
    type: hash
    ttl: null (persistent)

  lymphnode:queue:{lymphnode_id}:
    type: list
    ttl: 3600  # samples queue

  homeostasis:current_state:
    type: string
    ttl: null
```

---

## 🔒 INTEGRATION POINTS

### Com Serviços Existentes

```python
# 1. Immunis Services (8041-8047)
class ImmunisServiceClient:
    """Cliente para serviços Immunis existentes"""

    async def report_to_bcell(self, antigen: Dict):
        """Reportar antígeno para Células B (8041)"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://immunis_bcell_service:8041/antigen/process",
                json=antigen,
                timeout=30.0
            )
            return response.json()

    async def activate_tcell(self, target: str, threat_type: str):
        """Ativar Células T Citotóxicas (8043)"""
        # Similar implementation...

# 2. RTE Service (Reflexos)
class RTEIntegration:
    """Promover anticorpos para reflexos RTE"""

    async def promote_to_reflex(self, antibody_pattern: str):
        """Adicionar regra ao RTE (Hyperscan)"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://rte_service:8xxx/rules/add",
                json={
                    "pattern": antibody_pattern,
                    "action": "block",
                    "priority": "high"
                }
            )
            return response.json()

# 3. Ethical AI (8612)
class EthicalAIValidator:
    """Validar ações com Ethical AI"""

    async def validate_action(
        self,
        agent_id: str,
        target: str,
        action: str
    ) -> bool:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://ethical_audit_service:8612/validate",
                json={
                    "agent": agent_id,
                    "target": target,
                    "action": action,
                    "context": {"source": "active_immune"}
                },
                timeout=10.0
            )
            result = response.json()
            return result["decisao"] == "APROVADO"

# 4. MAXIMUS AI (8150)
class MaximusAIClient:
    """Cliente para MAXIMUS (decisões estratégicas)"""

    async def request_strategic_decision(self, situation: Dict):
        """Consultar MAXIMUS para decisão estratégica"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://maximus_core_service:8150/decision/strategic",
                json=situation,
                timeout=60.0
            )
            return response.json()
```

---

## 📈 METRICS (Prometheus)

```python
from prometheus_client import Counter, Gauge, Histogram, Summary

# Contadores
agent_activations_total = Counter(
    'active_immune_agent_activations_total',
    'Total agent activations',
    ['agent_type', 'lymphnode']
)

threats_detected_total = Counter(
    'active_immune_threats_detected_total',
    'Total threats detected',
    ['agent_type', 'threat_type']
)

cytokines_emitted_total = Counter(
    'active_immune_cytokines_emitted_total',
    'Total cytokines emitted',
    ['cytokine_type', 'priority']
)

# Gauges
active_agents_count = Gauge(
    'active_immune_active_agents_count',
    'Current active agents',
    ['agent_type', 'status']
)

homeostasis_state = Gauge(
    'active_immune_homeostasis_state',
    'Current homeostasis state',
    ['state']
)

vitals_score = Gauge(
    'active_immune_vitals_score',
    'System vitals score (0-100)',
    ['metric']
)

# Histogramas
patrol_duration_seconds = Histogram(
    'active_immune_patrol_duration_seconds',
    'Patrol cycle duration',
    ['agent_type'],
    buckets=[1, 5, 10, 30, 60, 120, 300]
)

lymphnode_processing_seconds = Histogram(
    'active_immune_lymphnode_processing_seconds',
    'Lymphnode sample processing time',
    ['lymphnode_id'],
    buckets=[0.1, 0.5, 1, 2, 5, 10]
)

# Summaries
antibody_affinity = Summary(
    'active_immune_antibody_affinity',
    'Antibody affinity score',
    ['antibody_type']
)
```

---

## ⚙️ CONFIGURATION (Pydantic Settings)

```python
from pydantic_settings import BaseSettings
from typing import List

class ActiveImmuneConfig(BaseSettings):
    """Configurações do serviço (via env vars)"""

    # Service
    service_name: str = "active_immune_core"
    service_port: int = 8200
    log_level: str = "INFO"

    # Kafka (Cytokines)
    kafka_bootstrap_servers: str = "kafka:9092"
    kafka_consumer_group: str = "active-immune-core"

    # Redis (Hormones + State)
    redis_url: str = "redis://redis:6379/0"
    redis_max_connections: int = 50

    # PostgreSQL (Persistent memory)
    postgres_url: str = "postgresql://user:pass@postgres:5432/vertice"

    # Homeostasis
    homeostasis_baseline_percentage: float = 0.15  # 15%
    homeostasis_inflammation_percentage: float = 0.50  # 50%
    homeostasis_sleep_percentage: float = 0.05  # 5%

    # Agent Pool
    agent_pool_size_max: int = 10000
    agent_pool_size_initial: int = 5000

    # Lymphnodes
    lymphnode_capacity_samples_per_min: int = 100
    lymphnode_hierarchy_levels: int = 3

    # Cloning
    cloning_enabled: bool = True
    cloning_max_clones_per_threat: int = 100
    cloning_selection_top_k: int = 10

    # Evolution
    evolution_enabled: bool = True
    evolution_generations_max: int = 10
    evolution_convergence_threshold: float = 0.95

    # RTE Integration
    rte_promotion_enabled: bool = True
    rte_promotion_usage_threshold: int = 100
    rte_promotion_efficacy_threshold: float = 0.95

    # Ethical AI
    ethical_ai_url: str = "http://ethical_audit_service:8612"
    ethical_ai_validation_required: bool = True
    ethical_ai_timeout_seconds: int = 10

    # Observability
    metrics_enabled: bool = True
    metrics_port: int = 9090

    class Config:
        env_file = ".env"
        env_prefix = "ACTIVE_IMMUNE_"
```

---

## 🧪 TESTING STRATEGY (Overview)

```yaml
Unit Tests:
  Framework: pytest
  Coverage Target: >95%
  Files:
    - tests/unit/test_agents.py
    - tests/unit/test_coordination.py
    - tests/unit/test_communication.py
    - tests/unit/test_homeostasis.py

Integration Tests:
  Framework: pytest + Docker Compose
  Environment: Kafka + Redis + PostgreSQL
  Files:
    - tests/integration/test_cytokines_flow.py
    - tests/integration/test_hormones_broadcast.py
    - tests/integration/test_lymphnode_hierarchy.py

E2E Tests:
  Framework: pytest + Kubernetes (kind)
  Scenarios:
    - DDoS attack simulation
    - Ransomware detection & neutralization
    - Homeostasis state transitions
    - Clone specialization lifecycle

Performance Tests:
  Framework: Locust
  Targets:
    - 10k agents active simultaneously
    - 1k cytokines/second
    - <100ms lymphnode processing (p99)
```

---

## 🚀 DEPLOYMENT (Kubernetes)

### DaemonSet (Agents)

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: active-immune-agents
  namespace: vertice
spec:
  selector:
    matchLabels:
      app: active-immune-agents
  template:
    metadata:
      labels:
        app: active-immune-agents
    spec:
      containers:
      - name: agent-runner
        image: vertice/active-immune-core:latest
        env:
        - name: ACTIVE_IMMUNE_KAFKA_BOOTSTRAP_SERVERS
          value: "kafka.vertice.svc.cluster.local:9092"
        - name: ACTIVE_IMMUNE_REDIS_URL
          value: "redis://redis.vertice.svc.cluster.local:6379/0"
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

### StatefulSet (Lymphnodes)

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: lymphnode-local
  namespace: vertice
spec:
  serviceName: lymphnode
  replicas: 3  # DMZ, Core, DB
  selector:
    matchLabels:
      app: lymphnode
  template:
    metadata:
      labels:
        app: lymphnode
    spec:
      containers:
      - name: lymphnode
        image: vertice/active-immune-core:latest
        command: ["python", "-m", "active_immune_core.lymphnode"]
        env:
        - name: LYMPHNODE_LEVEL
          value: "1"  # Local
        - name: LYMPHNODE_ID
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

---

## 📝 LOGGING STANDARD

```python
import structlog
from datetime import datetime

logger = structlog.get_logger()

# Formato padrão
logger.info(
    "agent_activated",
    agent_id="mac_001",
    agent_type="macrofago",
    lymphnode_id="dmz_l1",
    timestamp=datetime.now().isoformat()
)

# Output JSON:
{
  "event": "agent_activated",
  "agent_id": "mac_001",
  "agent_type": "macrofago",
  "lymphnode_id": "dmz_l1",
  "timestamp": "2025-01-06T15:30:00",
  "level": "info"
}
```

---

## ✅ CHECKLIST DE PRODUÇÃO

```
Infrastructure:
☐ Kafka cluster 3+ brokers
☐ Redis cluster (HA)
☐ PostgreSQL (replicado)
☐ Kubernetes 1.28+
☐ Prometheus + Grafana

Security:
☐ TLS entre serviços
☐ RBAC configurado
☐ Network policies
☐ Secrets management
☐ Ethical AI integration

Monitoring:
☐ Prometheus scraping /metrics
☐ Grafana dashboards
☐ Alertas configurados
☐ Logging centralizado

Testing:
☐ Unit tests >95% coverage
☐ Integration tests passando
☐ E2E tests validados
☐ Performance tests ok

Documentation:
☐ API docs (OpenAPI)
☐ Runbooks operacionais
☐ Troubleshooting guide
☐ Architecture diagrams
```

---

**Criado**: 2025-01-06
**Versão**: 1.0
**Status**: 🟢 Production-Ready Specs

🤖 **Co-authored by Juan & Claude**

**Generated with [Claude Code](https://claude.com/claude-code)**
