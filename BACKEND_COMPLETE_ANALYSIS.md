# RELATÓRIO COMPLETO - ESTRUTURA DO BACKEND VÉRTICE

**Data**: 2025-11-15  
**Versão**: 3.3.1  
**Nível de Análise**: MUITO DETALHADO  
**Throughness**: Very Thorough

---

## ÍNDICE
1. [Visão Geral da Arquitetura](#visão-geral)
2. [Estrutura de Diretórios](#estrutura-de-diretórios)
3. [API Gateway e Rotas](#api-gateway-e-rotas)
4. [Autenticação e Autorização](#autenticação-e-autorização)
5. [Modelos de Dados](#modelos-de-dados)
6. [Serviços (123 Total)](#serviços)
7. [WebSockets e Real-Time](#websockets-e-real-time)
8. [Integrações Externas](#integrações-externas)
9. [Observabilidade e Monitoramento](#observabilidade-e-monitoramento)

---

## <a name="visão-geral"></a>1. VISÃO GERAL DA ARQUITETURA

### Stack Tecnológico
- **Framework**: FastAPI (Python)
- **Servidor**: Uvicorn (ASGI)
- **Banco de Dados**: SQLAlchemy ORM (suporta múltiplos DBs)
- **Autenticação**: JWT (HS256)
- **Cache**: Redis
- **Monitoramento**: Prometheus + Structlog
- **Versioning**: API v1 (preparado para v2+)
- **Documentação**: Swagger UI + ReDoc + OpenAPI JSON

### Arquitetura de Componentes
```
┌─────────────────────────────────────────────┐
│         API GATEWAY (Port 8000)             │
│  - Roteamento centralizado                  │
│  - Autenticação JWT                         │
│  - Rate Limiting (100-1000 req/min)         │
│  - Proxy reverso para 100+ serviços         │
└─────────────────────────────────────────────┘
           ↓
┌──────────────────────────────────────────────────┐
│     SERVIÇOS ESPECIALIZADOS (70+ Services)       │
├──────────────────────────────────────────────────┤
│ P0 AIR GAP (30 serviços críticos):               │
│ - Defensive (4):                                 │
│   * Behavioral Analyzer  * MAV Detection        │
│   * Penelope (Pentesting) * Tegumentar          │
│ - MAXIMUS Core (8):                             │
│   * Orchestrator * Core * Eureka * Oraculo V2   │
│   * Predict * Integration * DLQ Monitor         │
│ - Immunis (12):                                 │
│   * B-Cell * Dendritic * Helper-T * Cytotoxic-T│
│   * T-Regulatory * Macrophage * Neutrophil      │
│ - HCL/HITL (6):                                 │
│   * Analyzer * Planner * Executor * Monitor     │
│   * Knowledge Base * Patch Service              │
│                                                  │
│ P1 HIGH PRIORITY (17 serviços):                 │
│ - Thalamus * Cloud Coordinator * Edge Agent     │
│ - MABA * Narrative Analysis * Investigation     │
│ - Reactive Fabric * Verdict Engine * etc.       │
│                                                  │
│ P2 MEDIUM PRIORITY (35 serviços):               │
│ - Auth * Cyber * Domain * IP Intelligence       │
│ - Network Monitor * Recon * Malware Analysis    │
│ - Google OSINT * SSL Monitor * etc.             │
│                                                  │
│ P3 LOW PRIORITY (18+ serviços):                 │
│ - Specialized tools e backends                  │
└──────────────────────────────────────────────────┘
```

---

## <a name="estrutura-de-diretórios"></a>2. ESTRUTURA DE DIRETÓRIOS

### Raiz do Backend
```
/home/user/V-rtice/backend/
├── api_gateway/                 # API Gateway principal
│   ├── main.py                 # 4372 linhas - Ponto de entrada
│   ├── routers/
│   │   └── v1.py              # Roteador v1 (future endpoints)
│   ├── models/
│   │   ├── base.py            # Modelos base com timestamps ISO 8601
│   │   ├── errors.py          # Modelos de erro padronizados
│   │   ├── exceptions.py       # Exceções customizadas
│   │   └── pagination.py       # Modelos de paginação
│   ├── middleware/
│   │   └── tracing.py         # Request ID tracing
│   ├── tests/                  # Suite de testes
│   └── requirements.txt         # Dependências Python
│
├── services/                    # 100+ serviços especializados
│   ├── auth_service/           # Autenticação centralizada
│   ├── adaptive_immunity_service/
│   ├── maximus_oraculo/        # Serviço preditivo
│   ├── maximus_core_service/   # Núcleo MAXIMUS
│   ├── network_recon_service/  # Reconhecimento de rede
│   ├── vuln_scanner_service/   # Scanner de vulnerabilidades
│   ├── immunis_*/              # Sistema imunológico (12 serviços)
│   ├── hcl_*_service/          # Human-in-Loop (6 serviços)
│   └── [... 70+ outros ...]
│
├── database/                    # Configuração de banco de dados
│   ├── models.py
│   ├── database.py
│   └── migrations/
│
├── modules/                     # Módulos compartilhados
│   └── tegumentar/             # Sistema de defesa de camadas
│
├── common/                      # Código compartilhado
│   ├── utils.py
│   ├── config.py
│   └── constants.py
│
├── libs/                        # Bibliotecas compartilhadas
├── config/                      # Configurações por ambiente
├── consciousness/              # Sistema de consciência/logging
├── coagulation/                # Sistema de coagulação (defesa)
└── shared/                      # Recursos compartilhados

```

---

## <a name="api-gateway-e-rotas"></a>3. API GATEWAY E ROTAS

### Informações do Gateway
- **URL Base**: `http://localhost:8000`
- **Documentação**: `/docs` (Swagger UI)
- **ReDoc**: `/redoc`
- **OpenAPI Schema**: `/openapi.json`
- **Versão**: 3.3.1
- **Título**: Projeto VÉRTICE - API Gateway

### Endpoints Principais (203 total no main.py)

#### Saúde e Monitoramento
```
GET  /                          # Root endpoint
GET  /health                    # Health check agregado
GET  /metrics                   # Prometheus metrics (text/plain)
GET  /api/v1/                   # v1 root info
GET  /api/v1/health             # v1 health check
```

#### Autenticação
```
POST /auth/google               # Google OAuth
POST /auth/logout               # Logout
GET  /auth/me                   # Perfil do usuário
GET  /auth/verify-token         # Verificar token JWT
```

#### SINESP (Inteligência Veicular Brasileira)
```
GET  /veiculos/{placa}          # Consultar placa (Rate: 30/min, Cached 1h)
GET  /ocorrencias/tipos         # Tipos de ocorrências (Rate: 10/min)
GET  /ocorrencias/heatmap       # Mapa de calor de crimes (Rate: 10/min)
```

#### Cyber Security
```
POST /cyber/network-scan        # Network scan (Rate: 5/min, Timeout: 60s)
GET  /cyber/port-analysis       # Análise de portas (Rate: 10/min)
GET  /cyber/file-integrity      # Integridade de arquivos
GET  /cyber/process-analysis    # Análise de processos
GET  /cyber/certificate-check   # Verificação de certificados SSL
GET  /cyber/security-config     # Configuração de segurança
GET  /cyber/security-logs       # Logs de segurança
GET  /cyber/health              # Health check do cyber service
```

#### Network Scanning (Nmap)
```
POST /api/nmap/scan             # Iniciar nmap scan
GET  /api/nmap/profiles         # Perfis de scan disponíveis
GET  /nmap/health               # Health check
```

#### Domain Intelligence
```
POST /api/domain/analyze        # Análise de domínio
GET  /domain/health             # Health check
```

#### IP Intelligence
```
POST /api/ip/analyze            # Análise de IP
GET  /api/ip/my-ip              # Meu IP público
POST /api/ip/analyze-my-ip      # Analisar meu IP
GET  /ip/health                 # Health check
```

#### Network Monitoring
```
GET  /api/network/monitor       # Monitor de rede
GET  /network/health            # Health check
```

#### Google OSINT
```
POST /api/google/search/basic           # Busca básica
POST /api/google/search/advanced        # Busca avançada
POST /api/google/search/documents       # Busca de documentos
POST /api/google/search/images          # Busca de imagens
POST /api/google/search/social          # Busca social
GET  /api/google/dorks/patterns         # Padrões de Google dorks
GET  /api/google/stats                  # Estatísticas
GET  /api/google/health                 # Health check
```

#### OSINT (Open Source Intelligence)
```
POST /api/email/analyze         # Análise de email
POST /api/image/analyze         # Análise de imagem
POST /api/phone/analyze         # Análise de telefone
POST /api/social/profile        # Análise de perfil social
POST /api/username/search       # Busca de username
POST /api/search/comprehensive  # Busca compreensiva
POST /api/investigate/auto      # Investigação automática
GET  /api/osint/stats           # Estatísticas OSINT
GET  /api/osint/health          # Health check
```

#### Malware Analysis
```
POST /api/malware/analyze-file          # Analisar arquivo
POST /api/malware/analyze-hash          # Analisar hash
POST /api/malware/analyze-url           # Analisar URL
GET  /malware/health                    # Health check
```

#### SSL/TLS Monitoring
```
POST /api/ssl/check             # Verificar certificado SSL
GET  /ssl/health                # Health check
```

#### Threat Intelligence
```
POST /api/threat-intel/check    # Verificar inteligência de ameaça
GET  /threat-intel/health       # Health check
```

#### Segurança Defensiva
```
POST /api/defensive/behavioral/analyze              # Análise comportamental
POST /api/defensive/behavioral/analyze-batch        # Análise em lote
POST /api/defensive/behavioral/train-baseline       # Treinar baseline
GET  /api/defensive/behavioral/baseline-status      # Status do baseline
GET  /api/defensive/behavioral/metrics              # Métricas comportamentais
POST /api/defensive/traffic/analyze                 # Análise de tráfego
POST /api/defensive/traffic/analyze-batch           # Análise em lote
GET  /api/defensive/traffic/metrics                 # Métricas de tráfego
GET  /api/defensive/health                          # Health check
```

#### Offensive Security (Pentesting)
```
POST /api/social-eng/campaign               # Criar campanha de eng. social
GET  /api/social-eng/campaign/{id}          # Obter campanha
GET  /api/social-eng/templates              # Templates disponíveis
POST /api/social-eng/awareness              # Treinamento de awareness
GET  /api/social-eng/analytics/{id}         # Análise de campanha
POST /api/vuln-scanner/scan                 # Iniciar scan de vulnerabilidades
GET  /api/vuln-scanner/scan/{id}            # Status do scan
GET  /api/vuln-scanner/exploits             # Exploits disponíveis
POST /api/vuln-scanner/exploit              # Executar exploit
GET  /social-eng/health                     # Health check
GET  /vuln-scanner/health                   # Health check
```

#### AI Agent
```
POST /api/ai/chat               # Chat com AI
GET  /api/ai/                   # Info do AI
GET  /api/ai/tools              # Tools disponíveis
GET  /ai/health                 # Health check
```

#### Aurora Orchestrator (Orquestração de Investigações)
```
POST /api/aurora/investigate    # Iniciar investigação
GET  /api/aurora/investigation/{id}  # Status da investigação
GET  /api/aurora/services       # Serviços disponíveis
GET  /aurora/health             # Health check
```

#### Active Immune Core
```
POST /api/immune/threats/detect                 # Detectar ameaças
GET  /api/immune/threats                        # Listar ameaças
GET  /api/immune/threats/{id}                   # Detalhes da ameaça
GET  /api/immune/agents                         # Listar agentes
GET  /api/immune/agents/{id}                    # Detalhes do agente
POST /api/immune/homeostasis/adjust             # Ajustar homeostase
GET  /api/immune/homeostasis                    # Status da homeostase
GET  /api/immune/lymphnodes                     # Listar lymph nodes
GET  /api/immune/lymphnodes/{id}                # Detalhes do lymph node
GET  /api/immune/memory/antibodies              # Antibodies em memória
GET  /api/immune/memory/search                  # Buscar na memória
GET  /api/immune/metrics                        # Métricas do immune
GET  /api/immune/stats                          # Estatísticas
GET  /api/immune/health                         # Health check
```

#### Rotas Protegidas (com Autenticação)
```
GET  /protected/admin           # Recursos admin (Admin role required)
GET  /protected/analyst         # Recursos analyst (Analyst role required)
GET  /protected/offensive       # Recursos offensive (Offensive role required)
```

#### Atlas GIS
```
GET/POST/PUT/DELETE /atlas/{full_path}   # Proxy para Atlas GIS (Rate: 60/min)
```

### Dinâmicas Service Proxies

O main.py contém **50+ funções de proxy dinâmico** que fazem routing para serviços:

```python
# Exemplo de padrão:
@app.api_route(
    "/auth-service/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"]
)
async def route_auth_service(path: str, request: Request):
    # Proxy para auth_service:8290
    pass

# Outros serviços com proxy dinâmico:
- /behavioral-analyzer-service/{path:path}
- /c2-orchestration-service/{path:path}
- /google-osint-service/{path:path}
- /homeostatic-regulation/{path:path}
- /ip-intelligence-service/{path:path}
- [... 40+ mais ...]
```

### Rate Limiting Configuration
```
Global (não autenticado):     100 requests/minuto por IP
Authenticated:                1000 requests/minuto por usuário
Scanning endpoints:           5-10 requests/minuto
SINESP endpoints:             30 requests/minuto
Atlas GIS:                    60 requests/minuto
```

---

## <a name="autenticação-e-autorização"></a>4. AUTENTICAÇÃO E AUTORIZAÇÃO

### JWT Configuration
```python
Algorithm: HS256
Secret Key: Configurável via JWT_SECRET_KEY env var
Min Length: 32 caracteres (256 bits)
Default Expiration: 30 minutos (configurável via JWT_EXPIRATION_MINUTES)
```

### Authentication Flow
1. **Login/Token Request**
   - POST /auth/token (OAuth2PasswordRequestForm)
   - Retorna: `{"access_token": "...", "token_type": "bearer"}`

2. **Token Usage**
   - Header: `Authorization: Bearer <token>`
   - Ou alternativamente: `X-API-Key: <api-key>`

3. **Token Verification**
   - GET /auth/verify-token
   - GET /auth/me (retorna user profile)

### Authorization Model
```python
class User(BaseModel):
    username: str
    roles: List[str]          # ["admin", "analyst", "offensive"]
    permissions: List[str]    # Permissões granulares

class UserInDB(User):
    hashed_password: str      # Bcrypt hashing
    
# Role-based access control (RBAC)
- admin:     Acesso total
- analyst:   Acesso a análises
- offensive: Acesso a ferramentas ofensivas
```

### Protected Endpoints Require Roles
```python
@require_permission("admin")          # Requer role admin
@require_permission("offensive")      # Requer role offensive
@require_permission("analyst")        # Requer role analyst
```

### Token Validation
```python
async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    # Decodifica JWT
    # Verifica assinatura HS256
    # Verifica expiração
    # Retorna payload com user info
```

### Secret Key Validation (Fail-Fast)
```python
def validate_secrets() -> None:
    """Validação de segurança na startup:"""
    - JWT_SECRET_KEY must be set
    - Mínimo 32 caracteres
    - Não pode ser valor fraco/default
    - Adverte se tem baixa entropia
```

---

## <a name="modelos-de-dados"></a>5. MODELOS DE DADOS

### Base Models (API Gateway)

#### Error Models
```python
class ErrorResponse(BaseModel):
    detail: str                    # Mensagem legível
    error_code: str               # "AUTH_001", "VAL_422", etc
    timestamp: datetime           # ISO 8601
    request_id: str               # UUID para tracing
    path: str                     # /api/v1/scan/start

class ValidationErrorDetail(BaseModel):
    loc: List[str]               # ["body", "email"]
    msg: str                      # Mensagem de erro
    type: str                     # "value_error.email"

class ValidationErrorResponse(ErrorResponse):
    error_code: str = "VAL_422"
    validation_errors: List[ValidationErrorDetail]
```

#### Error Codes Registry
```python
class ErrorCodes:
    # Authentication (AUTH_xxx)
    AUTH_MISSING_TOKEN = "AUTH_001"
    AUTH_INVALID_TOKEN = "AUTH_002"
    AUTH_EXPIRED_TOKEN = "AUTH_003"
    AUTH_INSUFFICIENT_PERMISSIONS = "AUTH_004"
    
    # Validation (VAL_xxx)
    VAL_UNPROCESSABLE_ENTITY = "VAL_422"
    VAL_INVALID_INPUT = "VAL_001"
    VAL_MISSING_FIELD = "VAL_002"
    VAL_INVALID_FORMAT = "VAL_003"
    
    # Rate Limiting (RATE_xxx)
    RATE_LIMIT_EXCEEDED = "RATE_429"
    RATE_QUOTA_EXCEEDED = "RATE_001"
    
    # System (SYS_xxx)
    SYS_INTERNAL_ERROR = "SYS_500"
    SYS_SERVICE_UNAVAILABLE = "SYS_503"
    SYS_TIMEOUT = "SYS_504"
    
    # External Services (EXT_xxx)
    EXT_SERVICE_UNAVAILABLE = "EXT_001"
    EXT_TIMEOUT = "EXT_002"
    EXT_INVALID_RESPONSE = "EXT_003"
```

#### Base Models with Timestamps
```python
class BaseModelWithTimestamps(BaseModel):
    created_at: datetime  # Default: utcnow()
    updated_at: datetime  # Default: utcnow()
    # Serializa sempre como ISO 8601 com 'Z' suffix

class BaseResponse(BaseModel):
    timestamp: str = Field(default_factory=lambda: to_iso8601(utcnow()))
    # ISO 8601 UTC timestamp

# Utility functions
def to_iso8601(dt: datetime) -> str:
    """Converte para ISO 8601 com 'Z' suffix"""
    # Exemplo: "2025-01-15T10:30:45Z"
```

### Service-Specific Models

#### Vulnerability Scanner Models
```python
class ScanTask(BaseModel):
    id: int
    target: str
    scan_type: str
    parameters: Dict[str, Any]
    status: str              # "pending", "running", "completed", "failed"
    start_time: datetime
    end_time: Optional[datetime]
    report_path: Optional[str]

class Vulnerability(BaseModel):
    id: int
    scan_task_id: int
    cve_id: Optional[str]
    name: str
    severity: str           # "low", "medium", "high", "critical"
    description: str
    solution: Optional[str]
    host: str
    port: Optional[int]
    protocol: Optional[str]
    discovered_at: datetime
    is_false_positive: bool
    remediated_at: Optional[datetime]
```

#### Network Reconnaissance Models
```python
class ReconStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ReconTask(BaseModel):
    id: str
    target: str               # IP, CIDR, domain
    scan_type: str           # "nmap_full", "masscan_ports"
    parameters: Dict[str, Any]
    start_time: str
    end_time: Optional[str]
    status: ReconStatus

class ReconResult(BaseModel):
    task_id: str
    status: str              # "success", "failed"
    output: Dict[str, Any]   # Raw output from tools
    timestamp: str
```

#### Narrative Analysis Models (Seriema Graph)
```python
class ManipulationSeverity(str, Enum):
    NONE, LOW, MEDIUM, HIGH, CRITICAL

class CredibilityRating(str, Enum):
    TRUSTED                    # 80-100
    GENERALLY_RELIABLE         # 60-79
    PROCEED_WITH_CAUTION       # 40-59
    UNRELIABLE                 # 20-39
    HIGHLY_UNRELIABLE          # 0-19

class EmotionCategory(str, Enum):
    # 27 categorias (BERTimbau)
    ADMIRATION, AMUSEMENT, ANGER, ANNOYANCE, APPROVAL,
    CARING, CONFUSION, CURIOSITY, DESIRE, DISAPPOINTMENT,
    # ... (27 total)

class PropagandaTechnique(str, Enum):
    LOADED_LANGUAGE, NAME_CALLING, REPETITION, EXAGGERATION,
    DOUBT, APPEAL_TO_FEAR, FLAG_WAVING, CAUSAL_OVERSIMPLIFICATION,
    SLOGANS, APPEAL_TO_AUTHORITY, BLACK_WHITE_FALLACY,
    THOUGHT_TERMINATING_CLICHES, WHATABOUTISM, REDUCTIO_AD_HITLERUM,
    RED_HERRING, BANDWAGON, OBFUSCATION, STRAW_MAN
```

#### OSINT Models
```python
class AutomatedInvestigationRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    name: Optional[str] = None
    image_url: Optional[str] = None
```

#### Location/Geo Models
```python
class OccurrenceInput(BaseModel):
    lat: float
    lng: float
    intensity: float
    timestamp: datetime
    tipo: str                # Tipo de ocorrência

class ClusterOutput(BaseModel):
    center_lat: float
    center_lng: float
    num_points: int
    risk_level: str         # "low", "medium", "high"

class PredictionOutput(BaseModel):
    hotspots: List[ClusterOutput]
```

---

## <a name="serviços"></a>6. SERVIÇOS (100+ TOTAL)

### P0 - AIR GAP EXTINCTION - 30 Serviços Críticos

#### Fixed Defensive (4)
1. **behavioral-analyzer-service** (Port 8037)
   - Detecção comportamental de ameaças
   - Análise de tráfego anômalo
   - Machine learning para padrões

2. **mav-detection-service** (Port 8039)
   - Micro Aerial Vehicle threat detection
   - Detecção de drones

3. **penelope-service** (Port 8042)
   - Penetration testing automatizado
   - Scan de vulnerabilidades

4. **tegumentar-service** (Port 8043)
   - Defesa em camadas
   - Skin/membrane defesa biológica

#### MAXIMUS Core (8)
1. **maximus-core-service** (8000) - Núcleo da IA
2. **maximus-orchestrator-service** (8001) - Orquestração
3. **maximus-eureka** (8002) - Service discovery
4. **maximus-oraculo-v2** (8003) - Predições avançadas
5. **maximus-predict** (8004) - Aurora Predict (ML forecasting)
6. **maximus-integration-service** (8005) - Integração
7. **maximus-dlq-monitor-service** (8006) - DLQ monitoring

#### Immunis System (12)
1. **immunis-api-service** (8100)
2. **adaptive-immunity-service** (8101)
3. **ai-immune-system** (8102)
4. **immunis-bcell-service** (8103) - B cell (antibody)
5. **immunis-dendritic-service** (8104) - Dendritic cells
6. **immunis-helper-t-service** (8105) - Helper T cells
7. **immunis-cytotoxic-t-service** (8106) - Cytotoxic T cells
8. **immunis-treg-service** (8107) - T regulatory
9. **immunis-macrophage-service** (8108) - Macrophages
10. **immunis-neutrophil-service** (8109) - Neutrophils
11. **adaptive-immune-system** (8110)
12. **adaptive-immunity-db** (8111)

#### HCL/HITL (6)
1. **hcl-analyzer-service** (8200)
2. **hcl-planner-service** (8201)
3. **hcl-executor-service** (8202)
4. **hcl-monitor-service** (8203)
5. **hcl-kb-service** (8204) - Knowledge Base
6. **hitl-patch-service** (8205) - Human-in-the-loop patching

### P1 - HIGH PRIORITY - 17 Serviços

1. **digital-thalamus-service** (8012) - Gatekeeper neural
2. **cloud-coordinator-service** (8260)
3. **edge-agent-service** (8261)
4. **maba-service** (8152) - Multi-Agent Behavior Analysis
5. **narrative-analysis-service** (8272)
6. **autonomous-investigation-service** (8250)
7. **reactive-fabric-core** (8281)
8. **reactive-fabric-analysis** (8275)
9. **verdict-engine-service** (8256)
10. **wargaming-crisol** (8812) - Wargaming/Simulation
11. **strategic-planning-service** (8242)
12. **system-architect-service** (8297)
13. **ethical-audit-service** (8251)
14. **rte-service** (8295) - Reflex Triage Engine
15. **seriema-graph** (8296) - Graph database
16. **vertice-register** (8888)

### P2 - MEDIUM PRIORITY - 35 Serviços

#### Core Security
- **auth-service** (8290) - Autenticação centralizada
- **cyber-service** (8011) - Cyber security base
- **domain-service** (8104) - Domain intelligence

#### OSINT & Intelligence
- **ip-intelligence-service** (8270)
- **google-osint-service** (8292)
- **osint-service** (8036)
- **threat-intel-service** (8113)
- **threat-intel-bridge** (8276)
- **vuln-intel-service** (8033)

#### Network & Infrastructure
- **network-monitor-service** (8262)
- **network-recon-service** (8032)
- **nmap-service** (8106)
- **ssl-monitor-service** (8115)

#### AI & Behavioral
- **malware-analysis-service** (8271)
- **memory-consolidation-service** (8240)
- **narrative-manipulation-filter** (8013)
- **narrative-filter-service** (8273)
- **neuromodulation-service** (8241)

#### Offensive Security
- **offensive-gateway** (8252)
- **offensive-orchestrator-service** (8253)
- **offensive-tools-service** (8254)
- **social-eng-service** (8112)
- **penelope-service** (Pentesting)

#### Advanced Analysis
- **predictive-threat-hunting-service** (8274)
- **prefrontal-cortex-service** (8011)
- **somatosensory-service** (8008)
- **traffic-analyzer-service** (8038)
- **vestibular-service** (8010)
- **visual-cortex-service** (8006)

#### Support
- **auditory-cortex-service** (8007)
- **atlas-service** (8109)
- **behavioral-analyzer-service** (8037)
- **nis-service** (8153)

### P3 - LOW PRIORITY - 18+ Serviços

- **adr-core-service** (8231) - Anomaly Detection
- **agent-communication** (8230)
- **bas-service** (8232)
- **chemical-sensing-service** (8009)
- **command-bus-service** (8233)
- **hpc-service** (8293) - High Performance Computing
- **hsas-service** (8023)
- **maximus-oraculo** (8222)
- **mock-vulnerable-apps** (8294)
- **mvp-service** (8000)
- **reflex-triage-engine** (8282)
- **purple-team** (8255)
- **web-attack-service** (8299)
- [... e mais ...]

### Estrutura Padrão de Serviço

Cada serviço segue padrão similar:
```
service_name/
├── api.py                # Endpoints FastAPI
├── main.py              # Entry point
├── models.py            # Pydantic models
├── database.py          # ORM models
├── schemas.py           # Request/Response schemas
├── tests/
│   ├── test_api.py
│   ├── test_service.py
│   └── conftest.py
├── requirements.txt
└── README.md
```

---

## <a name="websockets-e-real-time"></a>7. WEBSOCKETS E REAL-TIME

### Maximus Oraculo WebSocket Support
```python
# Suporte condicional para WebSocket (WEBSOCKET_AVAILABLE flag)
from api_endpoints import websocket_router, initialize_stream_manager
from websocket import APVStreamManager

# Ativado via config.enable_websocket
if config.enable_websocket and WEBSOCKET_AVAILABLE:
    app.include_router(websocket_router)
    # WebSocket router registrado para streaming real-time
    # APVStreamManager para gerenciar conexões
```

### WebSocket Endpoints
```
WS /ws/stream                   # Streaming de eventos
WS /ws/predictions              # Predições em tempo real
WS /ws/threats                  # Alertas de ameaças
```

### Streaming Manager
```python
class APVStreamManager:
    """Gerenciador de streaming para Adaptive Immunity"""
    - Conexões WebSocket
    - Broadcast de eventos
    - Backpressure handling
    - Reconnection logic
```

---

## <a name="integrações-externas"></a>8. INTEGRAÇÕES EXTERNAS

### APIs de Terceiros Integradas

#### SINESP (Segurança Pública Brasileira)
- **Endpoint**: `/veiculos/{placa}`
- **Consulta**: Informações veiculares
- **Cache**: Redis 1 hora
- **Rate Limit**: 30 req/min

#### Google APIs
- **Google Search**: Basic, Advanced, Documents, Images, Social
- **Google Dorks**: Patterns e automação
- **Módulo**: google_osint_service

#### IP Intelligence APIs
- **GeoIP**: Geolocalização
- **ASN**: Autonomous System
- **Reputação**: IP reputation databases
- **Whois**: WHOIS queries

#### Domain Intelligence
- **DNS**: Domain lookups
- **WHOIS**: Domain registration
- **MX**: Email servers
- **SSL**: Certificate validation

#### Malware Analysis
- **File Analysis**: VirusTotal, Hybrid Analysis
- **Hash Lookup**: CV Databases
- **URL Analysis**: Scanning engines

#### Threat Intelligence Feeds
- **CVE Database**: Vulnerability data
- **IOC Feeds**: Indicators of Compromise
- **Threat Reports**: Security vendors

#### Network Scanning
- **Nmap**: Network mapping
- **Masscan**: Mass port scanning
- **Shodan**: IoT search

---

## <a name="observabilidade-e-monitoramento"></a>9. OBSERVABILIDADE E MONITORAMENTO

### Prometheus Metrics
```python
# Métricas Exportadas
REQUESTS_TOTAL = Counter(
    'api_requests_total',
    'Total de requisições',
    ['method', 'path', 'status_code']
)

RESPONSE_TIME = Histogram(
    'api_response_time_seconds',
    'Tempo de resposta',
    ['method', 'path']
)

# Endpoint para coletar métricas
GET /metrics    # Formato Prometheus (text/plain)
```

### Structured Logging (Structlog)
```python
# Configuração de logging estruturado
log = structlog.get_logger()

# Contexto em cada requisição:
- request_id (UUID para tracing)
- method
- path
- status_code
- process_time
- error_type (se houver)

# Exemplo de log:
{
  "timestamp": "2025-11-15T12:34:56.789Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "method": "POST",
  "path": "/api/v1/scan/start",
  "status_code": 200,
  "process_time": 0.234,
  "service": "api_gateway"
}
```

### Request Tracing Middleware
```python
class RequestTracingMiddleware:
    """Adiciona request_id automático a cada request"""
    - Gera UUID v4 se não fornecido
    - Passa via header X-Request-ID
    - Disponível em get_request_id(request)
    - Inclui em todos os logs
```

### Health Checks
```
GET /health             # Health check agregado
GET /api/v1/health      # V1 health check
GET /{service}/health   # Health por serviço

Verifica:
- API Gateway status
- Redis connectivity
- Active Immune Core
- Reactive Fabric
- Critical dependencies
```

### Monitoramento de Performance
```python
@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    """Middleware que monitora todos os requests"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Registra em Prometheus
    REQUESTS_TOTAL.labels(...).inc()
    RESPONSE_TIME.labels(...).observe(process_time)
    
    # Log estruturado
    log.info(
        "request_processed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        process_time=round(process_time, 4)
    )
```

---

## RESUMO EXECUTIVO

### Números
- **Total de Endpoints**: 200+ rotas definidas + 50+ dinâmicas
- **Total de Serviços**: 100+ microserviços
- **Linhas de Código (main.py)**: 4,372
- **Rate Limits**: 5-1000 req/min por endpoint
- **Modelos de Dados**: 50+ Pydantic models
- **Error Codes**: 20+ categorias padronizadas

### Principais Características
- **API Versioning**: `/api/v1/` com suporte a múltiplas versões
- **Autenticação**: JWT (HS256) + Role-based access control
- **Rate Limiting**: Por IP e por usuário com limite granular
- **Proxy Reverso**: 50+ serviços roteados dinamicamente
- **Cache**: Redis para dados frequentes (SINESP, etc)
- **WebSockets**: Suporte para streaming em tempo real
- **Observabilidade**: Prometheus + Structlog + Request IDs
- **Documentação**: Swagger UI + ReDoc + OpenAPI schema
- **Tratamento de Erros**: Padronizado com error codes + request IDs

### Segurança
- Secret validation na startup
- CORS configurado para origins específicas
- JWT expiration (30 min default)
- Password hashing (Bcrypt)
- Permission-based endpoints
- Rate limiting contra DoS

### Performance
- Async/Await em todos os endpoints
- HTTP client pooling (httpx.AsyncClient)
- Redis caching layer
- Timeout configurável por serviço (5-60s)
- Batch processing endpoints para análise

