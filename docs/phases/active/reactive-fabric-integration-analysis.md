# Análise Profunda: Integração do Tecido Reativo ao Projeto MAXIMUS
## From Passive Defense to Active Intelligence

**Data**: 2025-10-12  
**Status**: ANÁLISE COMPLETA  
**Escopo**: Integração Backend + Frontend + Infraestrutura

---

## SUMÁRIO EXECUTIVO

### Contexto

O Projeto MAXIMUS possui uma arquitetura de **consciência artificial emergente** com **72 microserviços**, sistema imune adaptativo (91% coverage) e frameworks éticos completos. A integração do **Tecido Reativo** (honeynets de inteligência ativa) representa a evolução de **defesa passiva** para **inteligência proativa**.

### Objetivos da Integração

1. **Adicionar camada de inteligência de ameaças** via honeynets isoladas
2. **Alimentar sistema imune** com TTPs reais de adversários
3. **Enriquecer consciência** com awareness de threat landscape
4. **Criar frontend dedicado** para visualização de honeypot activity
5. **Manter isolamento total** (air-gap virtual) de produção

### Abordagem

**Princípio**: "Cirurgia, não amputação"  
Integração **não-invasiva** que adiciona capacidades sem modificar core existente.

---

## PARTE I: ANÁLISE DA ARQUITETURA EXISTENTE

### 1. Visão Geral do Projeto MAXIMUS

#### 1.1 Stack Tecnológico

**Backend**:
- **Linguagem**: Python 3.10+ (FastAPI)
- **Orquestração**: Docker Compose (72+ services)
- **Messaging**: Kafka (cytokines), Redis (hormones)
- **Storage**: PostgreSQL (asyncpg), Redis
- **AI/ML**: OpenAI GPT-4o, Anthropic Claude, PyTorch
- **Monitoring**: Prometheus, Grafana

**Frontend**:
- **Framework**: React 18 + Vite
- **State**: Zustand
- **Query**: TanStack React Query
- **Styling**: Tailwind CSS + shadcn/ui
- **Terminal**: xterm.js
- **Viz**: D3.js, Recharts, Leaflet

**Infrastructure**:
- **Containers**: Docker + Docker Compose
- **K8s Ready**: Kubernetes manifests existentes
- **Networking**: Bridge networks, internal DNS

#### 1.2 Arquitetura de Consciência (FASE 7-10)

```
┌─────────────────────────────────────────────────┐
│         CONSCIOUSNESS LAYER                     │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐  │
│  │  TIG   │ │  MMEI  │ │  MCEA  │ │  ESGT  │  │
│  │(Topo)  │ │(Intent)│ │(Emotion│ │(Stress)│  │
│  └────────┘ └────────┘ └────────┘ └────────┘  │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│      HOMEOSTATIC CONTROLLER (Q-Learning)        │
│  Monitor → Analyze → Plan → Execute             │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│        ACTIVE IMMUNE CORE (91% Coverage)        │
│  NK Cells | Macrophages | Lymphnodes | Cytokines
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│           OFFENSIVE & DEFENSIVE TOOLS           │
│  72 microservices (OSINT, Vuln, Malware, etc)  │
└─────────────────────────────────────────────────┘
```

**Implicação para Tecido Reativo**: Integração deve alimentar camadas superiores (Immune → Homeostatic → Consciousness).

#### 1.3 Sistema Imune Existente

**Componentes**:
- **NK Cells** (96% coverage): Stress signal detection, cytotoxic killing
- **Macrophages** (98% coverage): Phagocytosis, pattern recognition
- **Lymphnodes** (83% coverage): Clonal expansion, temperature regulation
- **Cytokines** (97% coverage): Immune signaling (pro/anti-inflammatory)

**Comunicação**:
- **Local**: Kafka topics (`cytokine.il1`, `cytokine.il6`, `cytokine.tnf_alpha`)
- **Global**: Redis pubsub (`hormone.cortisol`, `hormone.adrenaline`)

**Implicação**: Tecido Reativo deve publicar ameaças detectadas como cytokines para ativação imune.

#### 1.4 API Gateway Existente

**Arquivo**: `backend/api_gateway/main.py` (48KB)

**Roteamento**:
- 40+ service endpoints configurados
- Environment variables para service URLs
- Pattern: `{SERVICE}_URL` → `http://{service}:{port}`

**Implicação**: Adicionar `REACTIVE_FABRIC_URL` ao gateway.

#### 1.5 Frontend Existente

**Estrutura**:
```
frontend/src/
├── components/
│   ├── admin/          # Admin panels
│   ├── analytics/      # Dashboards
│   ├── dashboards/     # Main dashboards
│   ├── maximus/        # MAXIMUS-specific
│   ├── osint/          # OSINT tools
│   └── terminal/       # Terminal emulator
├── api/                # API client
├── stores/             # Zustand state
└── contexts/           # React contexts
```

**Implicação**: Criar `components/reactive-fabric/` para UI de honeypots.

---

### 2. Pontos de Integração Identificados

#### 2.1 Backend Integration Points

**A. API Gateway** (`backend/api_gateway/main.py`)
- Adicionar rota `/api/v1/reactive-fabric/*`
- Proxy para Reactive Fabric Service

**B. Immune System** (`backend/services/active_immune_core/`)
- Honeypot detections → Kafka topic `reactive_fabric.threat_detected`
- NK Cells consume e ativam resposta imune

**C. Threat Intelligence** (via Sentinel Agent)
- TTPs de honeypots alimentam `intelligence/fusion_engine.py`
- Enriquecem MITRE ATT&CK mapping

**D. Consciousness Layer** (via ESGT)
- Ataques intensos → aumentam stress level
- Trigger homeostatic adjustments (Repouso → Vigilância → Inflamação)

#### 2.2 Frontend Integration Points

**A. Dashboard Principal**
- Adicionar card "Honeypot Activity" em `components/dashboards/`
- Métricas: Ataques/dia, IPs únicos, Top TTPs

**B. Dedicated Honeypot Dashboard**
- Nova rota `/reactive-fabric`
- Real-time attack visualization (mapa geográfico)
- TTP timeline (Recharts)
- Live logs (xterm.js estilo)

**C. Threat Intel Feed**
- Integrar com `components/analytics/`
- TTPs descobertos alimentam threat feed existente

#### 2.3 Infrastructure Integration Points

**A. Docker Compose**
- Adicionar serviços:
  - `reactive_fabric_core` (Port 8600)
  - `reactive_fabric_honeypot_ssh` (Port 2222)
  - `reactive_fabric_honeypot_web` (Port 8080)
  - `reactive_fabric_honeypot_api` (Port 8081)
  - `reactive_fabric_analysis` (Port 8601)

**B. Network Isolation**
- Criar network `reactive_fabric_dmz` (isolada)
- Data diode: one-way bridge via shared volume + polling

**C. Monitoring**
- Adicionar métricas Prometheus:
  - `honeypot_connections_total`
  - `honeypot_attacks_detected`
  - `honeypot_ttps_extracted`

---

### 3. Análise de Compatibilidade

#### 3.1 Tecnologias Compatíveis ✅

| Componente | MAXIMUS | Tecido Reativo | Compatibilidade |
|------------|---------|----------------|-----------------|
| Linguagem Backend | Python 3.10+ FastAPI | Python 3.10+ FastAPI | ✅ 100% |
| Containers | Docker Compose | Docker Compose | ✅ 100% |
| Messaging | Kafka, Redis | Pode usar ambos | ✅ 100% |
| Frontend | React + Vite | React components | ✅ 100% |
| Monitoring | Prometheus | Prometheus | ✅ 100% |
| Storage | PostgreSQL | PostgreSQL | ✅ 100% |

#### 3.2 Conflitos Potenciais ⚠️

**Nenhum conflito crítico identificado.**

**Atenção**:
1. **Ports**: Usar range 8600-8699 (disponível)
2. **Network**: Criar network isolada (não usar bridge principal)
3. **Dependencies**: Tecido Reativo não deve depender de serviços core

#### 3.3 Dependencies Mapping

**Tecido Reativo depende de**:
- PostgreSQL (shared, read-only para threat intel)
- Kafka (producer only, topic `reactive_fabric.threat_detected`)
- Redis (opcional, para cache)

**Tecido Reativo NÃO depende de**:
- Consciousness layer
- Homeostatic controller
- Outros services (isolamento)

**Services que dependem de Tecido Reativo**:
- Sentinel Agent (consome TTPs)
- NK Cells (consome threat signals)
- API Gateway (proxy)
- Frontend (UI)

---

### 4. Análise de Segurança

#### 4.1 Isolamento (CRÍTICO)

**Requisito**: Honeypots NUNCA podem afetar produção.

**Implementação**:
- **Network**: Isolated Docker network `reactive_fabric_dmz`
- **Data Flow**: One-way only (honeypots → analysis → core)
- **No Reverse**: Produção não pode conectar em honeypots
- **Data Diode**: Shared volume polled by analysis service

**Validation**:
```bash
# Teste: honeypot não pode pingar produção
docker exec reactive_fabric_honeypot_ssh ping api_gateway
# Deve falhar (network unreachable)
```

#### 4.2 Attack Surface

**Exposto à Internet**:
- Honeypot SSH (Port 2222)
- Honeypot Web (Port 8080)
- Honeypot API (Port 8081)

**NÃO Exposto**:
- Reactive Fabric Core (8600) - internal only
- Analysis Service (8601) - internal only
- API Gateway (8000) - já exposto, adiciona rota

**Mitigação**:
- Honeypots em rede isolada
- Rate limiting no API Gateway
- Kill switches implementados

#### 4.3 Data Leakage Prevention

**Risco**: Honeypots podem conter dados de produção acidentalmente.

**Mitigação**:
- Dados sintéticos APENAS (fake users, fake databases)
- Watermarks em todos os dados (campo `_is_honeypot: true`)
- Validation layer: scanner que detecta dados reais

---

## PARTE II: BLUEPRINT DE INTEGRAÇÃO

### 1. Arquitetura Proposta

```
┌─────────────────────────────────────────────────────────────────┐
│                    MAXIMUS PRODUCTION                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Consciousness│  │ Homeostatic  │  │Active Immune │         │
│  │    Layer     │  │  Controller  │  │     Core     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│         ▲                  ▲                  ▲                 │
│         │                  │                  │                 │
│         │ (Threat Intel)   │ (Stress)         │ (Cytokines)    │
│         │                  │                  │                 │
│  ┌──────┴──────────────────┴──────────────────┴──────┐         │
│  │          API GATEWAY (Port 8000)                   │         │
│  │  + /api/v1/reactive-fabric/*                       │         │
│  └────────────────────────┬───────────────────────────┘         │
└───────────────────────────┼─────────────────────────────────────┘
                            │
                            │ ONE-WAY DATA FLOW
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│            REACTIVE FABRIC ISOLATED ZONE (DMZ+++)               │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  REACTIVE FABRIC CORE SERVICE (Port 8600 - Internal)   │   │
│  │  • Orchestrates honeypots                              │   │
│  │  • Aggregates metrics                                  │   │
│  │  • Publishes to Kafka (cytokines)                      │   │
│  └────────────────┬───────────────────────────────────────┘   │
│                   │                                             │
│       ┌───────────┼───────────┬───────────────┐               │
│       ▼           ▼           ▼               ▼               │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐   ┌──────────┐         │
│  │Honeypot │ │Honeypot │ │Honeypot │   │ Analysis │         │
│  │  SSH    │ │  Web    │ │  API    │   │ Service  │         │
│  │ :2222   │ │ :8080   │ │ :8081   │   │ :8601    │         │
│  └─────────┘ └─────────┘ └─────────┘   └──────────┘         │
│       │           │           │               │               │
│       └───────────┴───────────┴───────────────┘               │
│                           │                                    │
│                  ┌────────▼────────┐                          │
│                  │ Forensic Capture│                          │
│                  │ (Shared Volume) │                          │
│                  └─────────────────┘                          │
│                                                                │
│  Network: reactive_fabric_dmz (isolated)                      │
└─────────────────────────────────────────────────────────────────┘
                            ▲
                            │
                       INTERNET
                  (Ports 2222, 8080, 8081)
```

### 2. Componentes Novos

#### 2.1 Backend Services

**A. Reactive Fabric Core Service** (Port 8600)

**Arquivo**: `backend/services/reactive_fabric_core/main.py`

**Responsabilidades**:
- Orquestrar honeypots (health checks, restarts)
- Agregar métricas de todos honeypots
- Publicar ameaças detectadas em Kafka
- API REST para frontend

**Endpoints**:
```python
GET  /health
GET  /metrics
GET  /api/v1/honeypots                 # List all honeypots
GET  /api/v1/honeypots/{id}/stats      # Stats de um honeypot
GET  /api/v1/attacks/recent            # Últimos ataques
GET  /api/v1/ttps/top                  # Top TTPs descobertos
POST /api/v1/honeypots/{id}/restart    # Restart honeypot
```

**Dependencies**:
- FastAPI, asyncpg (PostgreSQL), aiokafka
- Docker SDK (para orquestração de containers)

**B. Honeypot Services**

**SSH Honeypot** (Port 2222)
- **Tech**: Cowrie (medium-interaction)
- **Logs**: JSON para shared volume
- **Fake**: Users, passwords, file system

**Web Honeypot** (Port 8080)
- **Tech**: Apache + PHP 7.2 + ModSecurity
- **Vulns**: SQL Injection, LFI, XSS
- **Fake**: E-commerce database

**API Honeypot** (Port 8081)
- **Tech**: FastAPI (fake)
- **Vulns**: Broken Auth, SSRF, Mass Assignment
- **Fake**: User management API

**C. Analysis Service** (Port 8601)

**Arquivo**: `backend/services/reactive_fabric_analysis/main.py`

**Responsabilidades**:
- Poll forensic captures (shared volume)
- Extract TTPs (MITRE ATT&CK mapping)
- Malware analysis (hashes, YARA)
- Store em PostgreSQL

**Pipeline**:
```python
1. Poll /forensics/captures/*.pcap
2. Parse with TShark
3. Extract IoCs (IPs, domains, file hashes)
4. Map to MITRE ATT&CK (via patterns)
5. Store em DB
6. Publish summary to Kafka
```

#### 2.2 Frontend Components

**A. Honeypot Dashboard** (`frontend/src/components/reactive-fabric/`)

**Estrutura**:
```
components/reactive-fabric/
├── HoneypotDashboard.jsx          # Main dashboard
├── HoneypotCard.jsx               # Individual honeypot card
├── AttackMap.jsx                  # Geographic attack map (Leaflet)
├── TTPTimeline.jsx                # Timeline of TTPs (Recharts)
├── LiveAttackFeed.jsx             # Real-time attack stream
├── HoneypotMetrics.jsx            # KPIs (connections, attacks, TTPs)
└── __tests__/
    └── HoneypotDashboard.test.jsx
```

**HoneypotDashboard.jsx** (Main Component):
```jsx
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import AttackMap from './AttackMap';
import TTPTimeline from './TTPTimeline';
import HoneypotCard from './HoneypotCard';

export default function HoneypotDashboard() {
  const { data: honeypots } = useQuery({
    queryKey: ['honeypots'],
    queryFn: () => fetch('/api/v1/reactive-fabric/honeypots').then(r => r.json()),
    refetchInterval: 5000 // Poll every 5s
  });

  const { data: recentAttacks } = useQuery({
    queryKey: ['attacks', 'recent'],
    queryFn: () => fetch('/api/v1/reactive-fabric/attacks/recent').then(r => r.json()),
    refetchInterval: 2000 // Poll every 2s
  });

  return (
    <div className="space-y-4 p-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {honeypots?.map(hp => (
          <HoneypotCard key={hp.id} honeypot={hp} />
        ))}
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Attack Origins</CardTitle>
          </CardHeader>
          <CardContent>
            <AttackMap attacks={recentAttacks} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>TTP Timeline</CardTitle>
          </CardHeader>
          <CardContent>
            <TTPTimeline />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Live Attack Feed</CardTitle>
        </CardHeader>
        <CardContent>
          <LiveAttackFeed attacks={recentAttacks} />
        </CardContent>
      </Card>
    </div>
  );
}
```

**B. API Client** (`frontend/src/api/reactiveFabric.js`)

```javascript
import axios from 'axios';

const API_BASE = '/api/v1/reactive-fabric';

export const reactiveFabricAPI = {
  getHoneypots: () => axios.get(`${API_BASE}/honeypots`),
  
  getHoneypotStats: (id) => axios.get(`${API_BASE}/honeypots/${id}/stats`),
  
  getRecentAttacks: (limit = 50) => 
    axios.get(`${API_BASE}/attacks/recent?limit=${limit}`),
  
  getTopTTPs: (limit = 10) => 
    axios.get(`${API_BASE}/ttps/top?limit=${limit}`),
  
  restartHoneypot: (id) => 
    axios.post(`${API_BASE}/honeypots/${id}/restart`),
};
```

**C. Route Configuration** (`frontend/src/App.jsx`)

```jsx
// Add to routes
import HoneypotDashboard from './components/reactive-fabric/HoneypotDashboard';

// In router configuration:
{
  path: '/reactive-fabric',
  element: <HoneypotDashboard />,
  meta: { 
    title: 'Reactive Fabric', 
    requiresAuth: true,
    requiredRole: 'security_analyst'
  }
}
```

#### 2.3 Infrastructure

**A. Docker Compose Addition** (`docker-compose.reactive-fabric.yml`)

```yaml
version: '3.8'

services:
  reactive_fabric_core:
    build: ./backend/services/reactive_fabric_core
    container_name: reactive-fabric-core
    ports:
      - "8600:8600"  # Internal only (not exposed to internet)
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/vertice
      - KAFKA_BROKERS=kafka:9092
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./backend/services/reactive_fabric_core:/app
      - forensic_captures:/forensics:ro  # Read-only access
    networks:
      - vertice_internal
    depends_on:
      - postgres
      - kafka
      - redis
    command: uvicorn main:app --host 0.0.0.0 --port 8600

  honeypot_ssh:
    image: cowrie/cowrie:latest
    container_name: reactive-fabric-honeypot-ssh
    ports:
      - "2222:2222"  # Exposed to internet
    volumes:
      - ./honeypots/ssh/config:/cowrie/etc
      - forensic_captures:/forensics  # Write access
    networks:
      - reactive_fabric_dmz  # Isolated network
    environment:
      - HONEYPOT_ID=ssh_001
    restart: unless-stopped

  honeypot_web:
    build: ./honeypots/web
    container_name: reactive-fabric-honeypot-web
    ports:
      - "8080:80"  # Exposed to internet
    volumes:
      - ./honeypots/web/htdocs:/var/www/html
      - forensic_captures:/forensics
    networks:
      - reactive_fabric_dmz
    environment:
      - HONEYPOT_ID=web_001
    restart: unless-stopped

  honeypot_api:
    build: ./honeypots/api
    container_name: reactive-fabric-honeypot-api
    ports:
      - "8081:8081"  # Exposed to internet
    volumes:
      - forensic_captures:/forensics
    networks:
      - reactive_fabric_dmz
    environment:
      - HONEYPOT_ID=api_001
    restart: unless-stopped

  analysis_service:
    build: ./backend/services/reactive_fabric_analysis
    container_name: reactive-fabric-analysis
    ports:
      - "8601:8601"  # Internal only
    volumes:
      - forensic_captures:/forensics:ro
    networks:
      - vertice_internal
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/vertice
      - KAFKA_BROKERS=kafka:9092
    depends_on:
      - postgres
      - kafka
    command: python -m uvicorn main:app --host 0.0.0.0 --port 8601

volumes:
  forensic_captures:
    driver: local

networks:
  reactive_fabric_dmz:
    driver: bridge
    ipam:
      config:
        - subnet: 172.30.0.0/24  # Isolated subnet
    internal: false  # Can access internet
  
  vertice_internal:
    external: true  # Use existing network
```

**B. API Gateway Integration** (`backend/api_gateway/main.py`)

```python
# Add to environment variables
REACTIVE_FABRIC_URL = os.getenv("REACTIVE_FABRIC_URL", "http://reactive_fabric_core:8600")

# Add route
@app.api_route("/api/v1/reactive-fabric/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_reactive_fabric(request: Request, path: str):
    """Proxy requests to Reactive Fabric Core Service."""
    return await proxy_request(request, REACTIVE_FABRIC_URL, path)
```

---

### 3. Data Flow

#### 3.1 Attack Detection Flow

```
1. Attacker → Honeypot SSH (Port 2222)
2. Cowrie logs interaction → /forensics/captures/ssh_20251012_143022.json
3. Analysis Service polls /forensics/ every 30s
4. Extracts: IP, commands, malware hashes, TTPs
5. Maps to MITRE ATT&CK (e.g., T1110 - Brute Force)
6. Stores in PostgreSQL (table: reactive_fabric_attacks)
7. Publishes to Kafka: topic "reactive_fabric.threat_detected"
8. NK Cell consumes Kafka → activates immune response
9. Sentinel Agent consumes → enriches threat intel
10. Frontend polls API → displays on dashboard
```

#### 3.2 Cytokine Integration (Immune System)

**Kafka Topic**: `reactive_fabric.threat_detected`

**Message Schema**:
```python
{
  "event_id": "rf_attack_12345",
  "timestamp": "2025-10-12T14:30:22Z",
  "honeypot_id": "ssh_001",
  "attacker_ip": "45.142.120.15",
  "attack_type": "brute_force",
  "severity": "medium",
  "ttps": ["T1110", "T1078"],
  "iocs": {
    "ips": ["45.142.120.15"],
    "usernames": ["admin", "root"],
    "malware_hashes": []
  },
  "confidence": 0.95
}
```

**Consumer** (NK Cell):
```python
# In backend/services/active_immune_core/agents/nk_cell.py

async def consume_reactive_fabric_threats(self):
    """Consume threats from Reactive Fabric honeypots."""
    consumer = AIOKafkaConsumer(
        'reactive_fabric.threat_detected',
        bootstrap_servers=self.kafka_brokers
    )
    await consumer.start()
    
    async for msg in consumer:
        threat = json.loads(msg.value)
        
        # Activate immune response
        if threat['severity'] in ['high', 'critical']:
            await self.cytotoxic_kill(threat['attacker_ip'])
            await self.publish_cytokine('il1', intensity=0.8)  # Pro-inflammatory
        
        # Log to consciousness (ESGT stress)
        await self.report_stress_signal(
            source='reactive_fabric',
            level=self._severity_to_stress(threat['severity'])
        )
```

#### 3.3 Consciousness Integration (ESGT)

**Pathway**: Reactive Fabric → NK Cell → ESGT (Stress Level) → Homeostatic Controller

**Stress Mapping**:
```python
# In backend/consciousness/esgt/stress_tracker.py

ATTACK_INTENSITY_TO_STRESS = {
    'low': 0.2,      # Repouso → Vigilância
    'medium': 0.5,   # Vigilância → Atenção
    'high': 0.7,     # Atenção → Inflamação
    'critical': 0.9  # Inflamação → Emergência
}

async def process_honeypot_attack(self, attack_data):
    """Integrate honeypot attacks into stress calculation."""
    stress_delta = ATTACK_INTENSITY_TO_STRESS[attack_data['severity']]
    
    # Update stress level (affects homeostatic state)
    self.current_stress += stress_delta
    
    # Trigger state transition if threshold exceeded
    if self.current_stress > self.thresholds['inflamacao']:
        await self.transition_to_state('INFLAMACAO')
        await self.activate_emergency_protocols()
```

---

## PARTE III: ROADMAP DE IMPLEMENTAÇÃO

### Sprint 0: Preparação (Semana 1)

**Objetivo**: Setup inicial e validação de conceito.

**Tarefas**:
- [ ] Criar branch `feature/reactive-fabric-integration`
- [ ] Criar estrutura de diretórios:
  ```
  backend/services/reactive_fabric_core/
  backend/services/reactive_fabric_analysis/
  honeypots/ssh/
  honeypots/web/
  honeypots/api/
  frontend/src/components/reactive-fabric/
  ```
- [ ] Configurar `docker-compose.reactive-fabric.yml`
- [ ] Teste de isolamento de rede (honeypot não alcança produção)

**Deliverables**:
- Estrutura de diretórios criada
- Docker Compose testado (containers sobem)
- Network isolation validado

**Critérios de Sucesso**:
- ✅ Honeypot SSH responde em porta 2222
- ✅ Honeypot não consegue pingar `api_gateway`
- ✅ Core service responde em porta 8600 (interno)

---

### Sprint 1: Backend Core (Semanas 2-3)

**Objetivo**: Implementar Reactive Fabric Core Service e Analysis Service.

#### Semana 2: Core Service

**Tarefas**:
- [ ] Implementar `reactive_fabric_core/main.py`:
  - Endpoints REST (honeypots, attacks, TTPs)
  - Health checks de honeypots
  - Aggregação de métricas
- [ ] Kafka producer (topic `reactive_fabric.threat_detected`)
- [ ] PostgreSQL schema:
  ```sql
  CREATE TABLE reactive_fabric_honeypots (
    id UUID PRIMARY KEY,
    type VARCHAR(50),
    port INT,
    status VARCHAR(20),
    created_at TIMESTAMP
  );

  CREATE TABLE reactive_fabric_attacks (
    id UUID PRIMARY KEY,
    honeypot_id UUID REFERENCES reactive_fabric_honeypots(id),
    attacker_ip INET,
    attack_type VARCHAR(100),
    severity VARCHAR(20),
    ttps JSONB,
    iocs JSONB,
    captured_at TIMESTAMP
  );

  CREATE INDEX idx_attacks_captured ON reactive_fabric_attacks(captured_at DESC);
  CREATE INDEX idx_attacks_ip ON reactive_fabric_attacks(attacker_ip);
  ```
- [ ] Testes unitários (pytest, >90% coverage)

**Deliverables**:
- Core service funcional
- API REST completa
- Testes passando

#### Semana 3: Analysis Service

**Tarefas**:
- [ ] Implementar `reactive_fabric_analysis/main.py`:
  - Polling de /forensics/ (shared volume)
  - Parser de logs Cowrie (JSON)
  - Extração de IoCs (IPs, usernames, hashes)
  - Mapeamento MITRE ATT&CK (regex patterns)
- [ ] Integração com Kafka (producer)
- [ ] Testes unitários

**Deliverables**:
- Analysis service funcional
- TTPs sendo extraídos corretamente
- Mensagens em Kafka

**Critérios de Sucesso Sprint 1**:
- ✅ Core API retorna lista de honeypots
- ✅ Ataque simulado em SSH honeypot é detectado
- ✅ TTPs são extraídos e salvos em DB
- ✅ Mensagem publicada em Kafka é consumível

---

### Sprint 2: Honeypots (Semanas 4-5)

**Objetivo**: Implementar e configurar honeypots de alta fidelidade.

#### Semana 4: SSH e Web Honeypots

**SSH Honeypot (Cowrie)**:
- [ ] Dockerfile para Cowrie
- [ ] Config customizado (`cowrie.cfg`):
  - Fake file system realista
  - Users/passwords comuns (root:123456, admin:admin)
  - Comandos permitidos
- [ ] Output para /forensics/ (JSON format)
- [ ] Teste: brute force attack (Hydra)

**Web Honeypot**:
- [ ] Dockerfile (Apache + PHP 7.2 + MySQL)
- [ ] Fake e-commerce app:
  - SQL injection point (`/product.php?id=1`)
  - LFI point (`/download.php?file=`)
  - XSS point (`/search.php?q=`)
- [ ] Fake database (10k products)
- [ ] Logs para /forensics/
- [ ] Teste: SQLMap attack

**Deliverables**:
- SSH honeypot capturando brute force
- Web honeypot capturando SQL injection

#### Semana 5: API Honeypot + Curadoria

**API Honeypot (FastAPI fake)**:
- [ ] Endpoints:
  - POST /api/v1/auth/login (weak JWT)
  - GET /api/v1/users (SSRF via ?url=)
  - PATCH /api/v1/users/{id} (mass assignment)
- [ ] OpenAPI docs expostos (/docs)
- [ ] Fake user database
- [ ] Logs para /forensics/
- [ ] Teste: SSRF attack

**Curadoria (Human Touch)**:
- [ ] Adicionar "história" a honeypots:
  - Git commits fake em web app
  - Logs de erro antigos
  - Arquivos .bak, .swp
  - Comentários TODOs no código
- [ ] Traffic generator (cron jobs fake, healthchecks)

**Deliverables**:
- API honeypot capturando SSRF
- Honeypots parecem "vividos" (não pristine)

**Critérios de Sucesso Sprint 2**:
- ✅ SSH honeypot captura 100% de tentativas de login
- ✅ Web honeypot captura SQL injection com SQLMap
- ✅ API honeypot captura SSRF com cURL test
- ✅ Fingerprinting test (SHODAN-like) não identifica como honeypot

---

### Sprint 3: Frontend (Semanas 6-7)

**Objetivo**: Criar dashboard de visualização de honeypots.

#### Semana 6: Components Base

**Tarefas**:
- [ ] `HoneypotDashboard.jsx` (main component)
- [ ] `HoneypotCard.jsx` (status, metrics per honeypot)
- [ ] `HoneypotMetrics.jsx` (KPIs: attacks/day, unique IPs, top TTPs)
- [ ] API client (`api/reactiveFabric.js`)
- [ ] Zustand store (`stores/reactiveFabricStore.js`)
- [ ] React Query hooks
- [ ] Testes (React Testing Library)

**Deliverables**:
- Dashboard renderiza honeypots
- Cards mostram status (online/offline)
- Métricas atualizadas via polling

#### Semana 7: Visualizações Avançadas

**Tarefas**:
- [ ] `AttackMap.jsx` (Leaflet):
  - Plot attacker IPs geograficamente
  - Heatmap de concentração
  - Markers clickáveis (detalhes do ataque)
- [ ] `TTPTimeline.jsx` (Recharts):
  - Timeline de TTPs descobertos
  - Agrupamento por técnica MITRE
  - Filtro por honeypot
- [ ] `LiveAttackFeed.jsx`:
  - Stream de ataques em tempo real
  - Estilo terminal (xterm.js ou lista)
  - Auto-scroll
- [ ] Responsive design (mobile-friendly)

**Deliverables**:
- Mapa geográfico funcional
- Timeline de TTPs renderizada
- Live feed atualizando

**Critérios de Sucesso Sprint 3**:
- ✅ Dashboard carrega em <2s
- ✅ Métricas atualizam a cada 5s (polling)
- ✅ Mapa plota IPs corretamente
- ✅ Timeline mostra TTPs históricos
- ✅ Live feed atualiza em tempo real
- ✅ Testes de componentes passando (>80% coverage)

---

### Sprint 4: Integration (Semana 8)

**Objetivo**: Integrar Reactive Fabric com sistema imune e consciousness.

**Tarefas**:
- [ ] Integração NK Cell:
  - Consumir Kafka topic `reactive_fabric.threat_detected`
  - Ativar resposta imune (cytokines)
  - Reportar stress para ESGT
- [ ] Integração Sentinel Agent:
  - Consumir TTPs de honeypots
  - Enriquecer threat intel feed
  - Adicionar context: "Known from honeypot activity"
- [ ] Integração ESGT (Consciousness):
  - Ataques → aumentam stress level
  - Trigger state transitions (Repouso → Vigilância → Inflamação)
- [ ] API Gateway:
  - Adicionar rota `/api/v1/reactive-fabric/*`
  - Testar proxy
- [ ] Monitoring:
  - Adicionar métricas Prometheus
  - Dashboards Grafana
- [ ] Testes de integração end-to-end

**Deliverables**:
- NK Cell responde a ataques de honeypots
- Sentinel Agent usa TTPs em análises
- ESGT reflete stress de ataques
- API Gateway roteia corretamente

**Critérios de Sucesso Sprint 4**:
- ✅ Ataque simulado em honeypot trigger resposta imune (log de cytokine)
- ✅ ESGT stress level aumenta com ataques
- ✅ Frontend acessa dados via API Gateway
- ✅ Métricas Prometheus sendo coletadas
- ✅ Testes E2E passando (attack → detection → immune response)

---

### Sprint 5: Hardening e Docs (Semana 9)

**Objetivo**: Security hardening, kill switches e documentação.

**Tarefas**:
- [ ] Kill Switches:
  - Implementar em `reactive_fabric_core/kill_switch.py`
  - Triggers: pivot attempt, resource exhaustion, file modification
  - Teste de shutdown (<10s)
- [ ] Security Hardening:
  - Validar isolamento de rede (pentest)
  - Firewall rules (iptables)
  - Data leak prevention (watermarks, validation)
- [ ] Documentação:
  - README completo (`docs/architecture/security/reactive-fabric-integration.md`)
  - API documentation (OpenAPI)
  - Runbook operacional
  - Troubleshooting guide
- [ ] Training:
  - Workshop para equipe (2h)
  - Simulação de incident response
- [ ] Validação final (checklist de 50 itens)

**Deliverables**:
- Kill switches funcionais
- Pentest aprovado (sem escape de rede)
- Documentação completa
- Equipe treinada

**Critérios de Sucesso Sprint 5**:
- ✅ Kill switch shutdown em <10s (teste)
- ✅ Pentest não consegue acessar produção de honeypot
- ✅ Documentação revisada e aprovada
- ✅ Equipe sabe operar sistema

---

### Sprint 6: Go-Live (Semana 10)

**Objetivo**: Deploy em produção e monitoramento inicial.

**Tarefas**:
- [ ] Deploy em staging:
  - Teste por 3 dias
  - Validar métricas
  - Ajustes finais
- [ ] Deploy em produção:
  - Expor honeypots à internet (ports 2222, 8080, 8081)
  - Monitoramento 24/7 (primeiros 7 dias)
  - Standby para incident response
- [ ] Collect baseline metrics (7 dias):
  - Ataques/dia
  - IPs únicos
  - TTPs descobertos
- [ ] Relatório inicial:
  - Apresentação para board
  - Métricas de sucesso
  - Roadmap Fase 2 (respostas automatizadas)

**Deliverables**:
- Sistema em produção
- Baseline metrics coletados
- Relatório de Go-Live

**Critérios de Sucesso Sprint 6**:
- ✅ Honeypots recebendo ataques reais
- ✅ KPI-001 > 50% (TTPs acionáveis)
- ✅ KPI-007 = 0 (zero transbordamentos)
- ✅ Zero incidents críticos
- ✅ Board aprovado para Fase 2 (condicional)

---

## PARTE IV: PLANO OPERACIONAL

### 1. Rotinas de Manutenção

**Daily** (Analista SOC):
- 08:00: Verificar status de honeypots (uptime)
- 09:00-17:00: Triagem de ataques capturados (15min/ataque)
- 17:00: Relatório diário (ataques, TTPs, anomalias)

**Weekly** (DevOps Engineer):
- Segunda: Rotação de snapshots de honeypots
- Quarta: Análise de KPI-004 (taxa de detecção)
- Sexta: Refresh de honeypots (reinstalação se necessário)

**Monthly** (Security Architect):
- Semana 1: Relatório mensal de inteligência
- Semana 2-3: Análise de TTPs únicos
- Semana 4: Curadoria de honeypots (atualizar fake data)

**Quarterly** (Comitê de Ética):
- Revisão de casos ambíguos
- Auditoria de conformidade
- Decisão de compartilhamento de TTPs com comunidade

### 2. Monitoring e Alertas

**Prometheus Metrics**:
```
honeypot_connections_total{honeypot="ssh_001", status="success"}
honeypot_attacks_detected{honeypot="web_001", severity="high"}
honeypot_ttps_extracted{technique="T1110"}
honeypot_uptime_seconds{honeypot="api_001"}
reactive_fabric_analysis_latency_seconds
reactive_fabric_kafka_messages_published_total
```

**Grafana Dashboards**:
- **Overview**: Total attacks, unique IPs, top TTPs
- **Per-Honeypot**: Connections, attacks, uptime
- **Threat Intelligence**: TTPs timeline, IoC feed
- **Health**: Service uptime, latency, errors

**Alerts**:
```yaml
- alert: HoneypotDown
  expr: up{job="reactive_fabric"} == 0
  for: 5m
  severity: warning

- alert: HighAttackVolume
  expr: rate(honeypot_connections_total[5m]) > 100
  for: 10m
  severity: info

- alert: CriticalThreatDetected
  expr: honeypot_attacks_detected{severity="critical"} > 0
  for: 1m
  severity: critical
```

### 3. Incident Response

**Cenário 1: Honeypot Comprometido (Total Takeover)**

**Detecção**: Honeypot deixa de responder OU comportamento anômalo (CPU 100%, network spike).

**Resposta**:
1. Isolate (desconectar network)
2. Snapshot (preservar estado para forensics)
3. Analyze (reversing do malware, se houver)
4. Rebuild (wipe + reinstall honeypot)
5. Update defenses (ajustar firewall, signatures)

**SLA**: <1h (Isolate + Snapshot), <24h (Rebuild)

**Cenário 2: Zero-Day Descoberto em Honeypot**

**Detecção**: Ataque usando técnica desconhecida (não mapeia para MITRE).

**Resposta**:
1. Isolate sample (malware, payloads)
2. Reverse engineer (Ghidra, Cuckoo)
3. Document TTP (criar novo mapeamento MITRE ATT&CK custom)
4. Notify (CERT.br, comunidade via responsible disclosure)
5. Patch (se aplicável a produção)

**SLA**: <48h (Analysis), <7 dias (Disclosure)

### 4. Escalation Matrix

| Severity | Descrição | Resposta | SLA |
|----------|-----------|----------|-----|
| Low | Port scan, brute force trivial | Triagem L1 | <4h |
| Medium | Exploitation attempt, SQL injection | Análise L2 | <24h |
| High | Successful exploitation, shell access | Análise L2 + L3 | <4h |
| Critical | APT-like, 0-day, coordinated attack | L2 + L3 + Comitê + Executivo | <1h |

---

## PARTE V: VALIDAÇÃO E TESTES

### 1. Testes de Segurança

**A. Network Isolation Test**
```bash
# From honeypot, try to reach production
docker exec reactive_fabric_honeypot_ssh ping api_gateway
# Expected: Network unreachable

# From production, try to reach honeypot
docker exec vertice-api-gateway ping reactive_fabric_honeypot_ssh
# Expected: Network unreachable (one-way only via data diode)
```

**B. Kill Switch Test**
```python
# Simulate pivot attempt
# In honeypot, try to connect to production subnet
import socket
sock = socket.socket()
sock.connect(('10.0.1.10', 8000))  # Production API Gateway
# Expected: Kill switch triggers, honeypot shuts down in <10s
```

**C. Data Leak Test**
```python
# Scan honeypot data for production markers
import re

PRODUCTION_MARKERS = [
    r'10\.0\.1\.',  # Production subnet
    r'vertice\.security',  # Real domain
    r'real_api_key_\w+',  # Real API keys
]

def scan_for_leaks(honeypot_data):
    for marker in PRODUCTION_MARKERS:
        if re.search(marker, honeypot_data):
            raise SecurityViolation(f"Production data found: {marker}")
```

### 2. Testes Funcionais

**A. End-to-End Attack Flow**
```python
# Test Case: SSH Brute Force
async def test_e2e_ssh_brute_force():
    # 1. Attack honeypot
    result = subprocess.run(['hydra', '-l', 'root', '-P', 'passwords.txt',
                             'ssh://localhost:2222'])
    
    # 2. Wait for analysis (30s polling)
    await asyncio.sleep(35)
    
    # 3. Verify attack detected
    attacks = await reactive_fabric_api.get_recent_attacks()
    assert len(attacks) > 0
    assert attacks[0]['attack_type'] == 'brute_force'
    
    # 4. Verify TTP extracted
    ttps = await reactive_fabric_api.get_top_ttps()
    assert 'T1110' in ttps  # MITRE ATT&CK: Brute Force
    
    # 5. Verify Kafka message published
    consumer = await create_kafka_consumer('reactive_fabric.threat_detected')
    msg = await consumer.getone()
    assert msg['attack_type'] == 'brute_force'
    
    # 6. Verify immune response (NK Cell activated)
    immune_logs = await get_immune_logs()
    assert any('cytokine' in log and 'il1' in log for log in immune_logs)
```

**B. Frontend Integration Test**
```javascript
// Test Case: Dashboard loads and displays data
describe('HoneypotDashboard', () => {
  it('loads honeypots and displays cards', async () => {
    render(<HoneypotDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText(/SSH Honeypot/i)).toBeInTheDocument();
      expect(screen.getByText(/Web Honeypot/i)).toBeInTheDocument();
    });
  });

  it('updates attack count in real-time', async () => {
    render(<HoneypotDashboard />);
    
    const initialCount = screen.getByTestId('attack-count').textContent;
    
    // Simulate attack (API returns new data)
    act(() => {
      simulateAttack('ssh_001');
    });
    
    await waitFor(() => {
      const newCount = screen.getByTestId('attack-count').textContent;
      expect(parseInt(newCount)).toBeGreaterThan(parseInt(initialCount));
    }, { timeout: 6000 }); // Wait for 5s polling + render
  });
});
```

### 3. Performance Tests

**A. Load Test (Concurrent Attacks)**
```python
# Use Locust to simulate 100 concurrent attackers
from locust import HttpUser, task, between

class HoneypotAttacker(HttpUser):
    wait_time = between(1, 5)
    
    @task
    def brute_force_ssh(self):
        # Simulate SSH login attempt
        self.client.post('ssh://localhost:2222', ...)
    
    @task
    def sql_injection(self):
        # Simulate SQL injection on web honeypot
        self.client.get('http://localhost:8080/product.php?id=1\' OR 1=1--')

# Run: locust -f load_test.py --users 100 --spawn-rate 10
# Verify: All attacks logged, no dropped packets, latency <500ms
```

**B. Scalability Test**
```bash
# Add 10 honeypots dynamically
for i in {1..10}; do
  docker run -d --name honeypot_ssh_$i cowrie/cowrie
done

# Verify: Core service tracks all 10, API responds <2s
```

---

## PARTE VI: MÉTRICAS DE SUCESSO

### 1. KPIs Técnicos (Primeiros 30 Dias)

| KPI | Meta | Método de Medição |
|-----|------|-------------------|
| KPI-001: TTPs Acionáveis | ≥60% | % ataques que geram ≥1 TTP mapeável |
| KPI-004: Taxa de Detecção | <20% | % ataques que detectam honeypot (early abort) |
| KPI-007: Transbordamentos | 0 | Tentativas de pivot para produção detectadas |
| Uptime Honeypots | ≥99% | Prometheus `up{job="honeypot"}` |
| Latency Análise | <60s | Tempo captura → TTP extraído |
| Coverage Testes | ≥90% | pytest coverage report |

### 2. KPIs de Negócio (Primeiros 90 Dias)

| Métrica | Meta | Impacto |
|---------|------|---------|
| TTPs Únicos Descobertos | ≥30 | Enriquece threat intel |
| 0-Days Identificados | ≥1 | Alto valor para comunidade |
| Malware Samples | ≥50 | Alimenta análise de malware |
| Immune Activations | ≥10 | Valida integração com NK Cells |
| Stress Level Increases | ≥5 | Valida integração com ESGT |

### 3. ROI Calculation

**Investimento**:
- Dev time: 10 semanas × 1 FTE × $150k/ano = ~$28k
- Infra: $2k (hardware) + $500/mês (hosting) = $2.5k
- **Total**: $30.5k

**Retorno** (Ano 1):
- Prevenção de 1 breach (via threat intel): $4.24M
- 1 CVE descoberto: $100k (bug bounty)
- Threat intel vendável: $20k/ano
- **Total**: $4.36M

**ROI**: 14,200% (conservador)

---

## APÊNDICES

### A. Checklist de Deploy (50 Itens)

#### Pre-Deploy
- [ ] Código revisado (2+ reviewers)
- [ ] Testes passando (≥90% coverage)
- [ ] Documentação atualizada
- [ ] Pentest aprovado (rede isolada)
- [ ] Kill switches testados
- [ ] Aprovações executivas (CISO, CTO)

#### Deploy
- [ ] Backup de produção
- [ ] Feature flag ativada (`enable_reactive_fabric=true`)
- [ ] Deploy em staging (3 dias de teste)
- [ ] Smoke tests passando
- [ ] Monitoring configurado (Prometheus, Grafana)
- [ ] Alertas configurados (PagerDuty)

#### Post-Deploy
- [ ] Honeypots recebendo tráfego
- [ ] Ataques sendo detectados
- [ ] TTPs sendo extraídos
- [ ] Immune system respondendo
- [ ] Frontend renderizando dados
- [ ] Zero errors críticos (primeiras 24h)

### B. Troubleshooting Guide

**Problema**: Honeypot não recebe ataques.
**Solução**:
1. Verificar firewall (portas 2222, 8080, 8081 abertas)
2. Verificar network (docker network ls, ping test)
3. Verificar logs (docker logs honeypot_ssh)
4. Verificar SHODAN (honeypot está indexado?)

**Problema**: Analysis service não extrai TTPs.
**Solução**:
1. Verificar shared volume (`ls /forensics/`)
2. Verificar parsing (logs de analysis service)
3. Verificar regex patterns (MITRE mappings)
4. Manual test (feed sample PCAP, verify output)

**Problema**: Frontend não atualiza dados.
**Solução**:
1. Verificar API Gateway (rota `/api/v1/reactive-fabric/*`)
2. Verificar CORS (frontend origin permitida)
3. Verificar React Query (cache, refetch interval)
4. Browser DevTools (network tab, verify requests)

### C. Referências

**Documentos Relacionados**:
- [Análise de Viabilidade - Tecido Reativo](/home/juan/Documents/Análise de Viabilidade: Arquitetura de Decepção Ativa e Contra-Inteligência Automatizada.md)
- [Defensive Architecture](docs/architecture/security/DEFENSIVE_ARCHITECTURE.md)
- [Active Immune Core](backend/services/active_immune_core/README.md)

**Papers e Recursos**:
- "Honeypots: A New Paradigm to Information Security" - Kara Nance et al.
- MITRE ATT&CK Framework - https://attack.mitre.org
- Cowrie Documentation - https://cowrie.readthedocs.io

---

**FIM DA ANÁLISE PROFUNDA**

**Status**: ✅ ANÁLISE COMPLETA  
**Próximo Passo**: Criar Blueprint e Roadmap detalhados

**Versão**: 1.0  
**Data**: 2025-10-12  
**Autor**: MAXIMUS AI
