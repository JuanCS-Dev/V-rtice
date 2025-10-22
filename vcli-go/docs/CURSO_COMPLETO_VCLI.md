# vCLI - Curso Completo de Operação

**Versão**: 2.0
**Data**: 2025-10-22
**Status**: Production Ready - 100% Conformidade Doutrina Vértice
**Autor**: MAXIMUS AI Team

---

## Índice

1. [Introdução](#1-introdução)
2. [Instalação e Configuração](#2-instalação-e-configuração)
3. [Arquitetura e Conceitos](#3-arquitetura-e-conceitos)
4. [Modos de Operação](#4-modos-de-operação)
5. [Comandos CLI - Referência Completa](#5-comandos-cli---referência-completa)
6. [TUI Workspaces](#6-tui-workspaces)
7. [Operação Offline](#7-operação-offline)
8. [Sistema de Erros e Troubleshooting](#8-sistema-de-erros-e-troubleshooting)
9. [Operações Avançadas](#9-operações-avançadas)
10. [Casos de Uso Práticos](#10-casos-de-uso-práticos)
11. [Referência Rápida](#11-referência-rápida)

---

## 1. Introdução

### 1.1 O que é vCLI?

**vCLI** (Vertice Command Line Interface) é uma ferramenta unificada de linha de comando para interagir com todo o ecossistema Vertice, incluindo:

- **MAXIMUS Governance** - Sistema de governança e decisões HITL
- **Immune Core** - Detecção de anomalias e segurança
- **Consciousness Services** - Eureka, Oraculo, Predict, Neuromodulation
- **Kubernetes** - Gerenciamento completo de clusters K8s
- **TUI Workspaces** - Interfaces interativas para monitoramento

### 1.2 Filosofia de Design

vCLI segue a **Doutrina Vértice**:
- ✅ **Zero Compromises** - Production-ready sempre
- ✅ **NO MOCK, NO PLACEHOLDER** - Apenas código real
- ✅ **Production Quality** - Error handling completo
- ✅ **User Experience First** - Mensagens claras e acionáveis

### 1.3 Características Principais

| Característica | Descrição |
|----------------|-----------|
| **Multi-Backend** | Integração com 7+ serviços backend |
| **Offline Mode** | Queue de comandos e sync automático |
| **Enhanced Errors** | Mensagens contextuais com sugestões |
| **TUI Workspaces** | 3 dashboards interativos |
| **Batch Operations** | Processamento paralelo em massa |
| **Auto-Diagnostics** | Comando `troubleshoot` automático |

---

## 2. Instalação e Configuração

### 2.1 Requisitos

**Mínimo**:
- Go 1.21+ (para compilar do source)
- Acesso aos backends Vertice (HTTP/HTTPS)
- Kubernetes cluster (opcional, para comandos K8s)

**Recomendado**:
- Terminal com suporte a cores (256 colors)
- BadgerDB para cache offline
- Redis para sessões HITL

### 2.2 Instalação

#### Opção 1: Build do Source

```bash
# Clone o repositório
git clone https://github.com/verticedev/vcli-go.git
cd vcli-go

# Build
go build -o bin/vcli ./cmd

# Instalar globalmente (opcional)
sudo cp bin/vcli /usr/local/bin/
```

#### Opção 2: Download do Release

```bash
# Linux
wget https://github.com/verticedev/vcli-go/releases/latest/download/vcli-linux-amd64
chmod +x vcli-linux-amd64
sudo mv vcli-linux-amd64 /usr/local/bin/vcli

# macOS
wget https://github.com/verticedev/vcli-go/releases/latest/download/vcli-darwin-amd64
chmod +x vcli-darwin-amd64
sudo mv vcli-darwin-amd64 /usr/local/bin/vcli
```

#### Opção 3: Homebrew (macOS/Linux)

```bash
brew tap verticedev/tap
brew install vcli
```

### 2.3 Configuração Inicial

#### Arquivo de Configuração

Criar `~/.vcli/config.yaml`:

```yaml
# Backend Endpoints
maximus:
  endpoint: http://localhost:8100
  timeout: 30s

immune:
  endpoint: http://localhost:8200
  timeout: 30s

hitl:
  endpoint: http://localhost:8000/api
  redis_url: localhost:6379
  redis_db: 0

consciousness:
  eureka_endpoint: http://localhost:8300
  oraculo_endpoint: http://localhost:8400
  predict_endpoint: http://localhost:8500

# Kubernetes
kubernetes:
  kubeconfig: ~/.kube/config
  context: default

# Offline Mode
offline:
  enabled: true
  sync_interval: 5m
  cache_dir: ~/.vcli/cache

# Performance
performance:
  max_concurrent: 10
  retry_attempts: 3
  timeout: 30s
```

#### Variáveis de Ambiente

Você pode sobrescrever configurações via environment:

```bash
export MAXIMUS_ENDPOINT=http://production-maximus:8100
export HITL_REDIS_URL=redis://prod-redis:6379
export KUBECONFIG=/path/to/prod/kubeconfig
```

**Precedência**:
1. Flags de comando (mais alta)
2. Variáveis de ambiente
3. Arquivo de configuração
4. Defaults (mais baixa)

### 2.4 Verificação da Instalação

```bash
# Verificar versão
vcli version

# Output esperado:
# vCLI v2.0
# Build: 2025-10-22
# Go: go1.21.5

# Testar conectividade
vcli troubleshoot all

# Output esperado:
# ✓ MAXIMUS Governance: OK
# ✓ Immune Core: OK
# ✓ HITL Console: OK
# ✓ Kubernetes: OK
```

---

## 3. Arquitetura e Conceitos

### 3.1 Arquitetura Geral

```
┌─────────────────────────────────────────────────────────────┐
│                        vCLI                                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  CLI Mode    │  │  Shell Mode  │  │  TUI Mode    │     │
│  │  (cobra)     │  │  (REPL)      │  │  (bubbletea) │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                            │                                 │
│         ┌──────────────────┴──────────────────┐             │
│         │                                      │             │
│    ┌────▼─────┐                         ┌─────▼──────┐     │
│    │  HTTP    │                         │   Offline  │     │
│    │ Clients  │◄────────────────────────┤   Manager  │     │
│    └────┬─────┘                         └─────┬──────┘     │
│         │                                      │             │
│         │ ┌────────────────────────────────┐  │             │
│         └─┤     BadgerDB Cache             │◄─┘             │
│           │  - Response cache              │                │
│           │  - Command queue               │                │
│           │  - Sync manager                │                │
│           └────────────────────────────────┘                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                        │
        ────────────────┴────────────────
        │               │               │
   ┌────▼────┐    ┌─────▼─────┐   ┌────▼─────┐
   │ MAXIMUS │    │  Immune   │   │   K8s    │
   │Governan.│    │   Core    │   │ Cluster  │
   └─────────┘    └───────────┘   └──────────┘
```

### 3.2 Componentes Principais

#### 3.2.1 HTTP Clients

Todos os backends usam **HTTP clients** (não gRPC):
- MAXIMUS Governance
- Immune Core
- HITL Console
- Consciousness (Eureka, Oraculo, Predict)

**Benefícios**:
- Simples debugging (curl, browser)
- HTTPS out-of-the-box
- Firewall-friendly
- REST APIs padrão

#### 3.2.2 Offline Manager

Sistema de 3 camadas para operação offline:

1. **Response Cache**: Armazena respostas de leitura
2. **Command Queue**: Queue de operações write
3. **Sync Manager**: Sincronização periódica (5min default)

#### 3.2.3 Error System

Sistema de erros contextual com 3 tipos:

| Tipo | Quando Usar | Exemplo |
|------|-------------|---------|
| **ConnectionError** | Falha de rede/endpoint | Cannot reach MAXIMUS |
| **AuthError** | Credenciais inválidas | HITL login failed |
| **ValidationError** | Input inválido | Invalid decision ID |

Cada erro inclui:
- Descrição clara do problema
- Endpoint/operação afetada
- Sugestões de correção (2-3)
- Comando de help relevante

### 3.3 Modos de Execução

#### CLI Mode (Comandos diretos)

```bash
vcli maximus decision list
vcli k8s get pods -n default
vcli immune health
```

**Quando usar**: Scripts, CI/CD, automação

#### Shell Mode (REPL interativo)

```bash
vcli shell

vcli> maximus decision list
vcli> k8s describe pod nginx-abc123
vcli> exit
```

**Quando usar**: Exploração interativa, múltiplos comandos

#### TUI Mode (Terminal UI)

```bash
vcli tui
```

**Quando usar**: Monitoramento contínuo, dashboards

---

## 4. Modos de Operação

### 4.1 Modo CLI (Command Line Interface)

#### Estrutura de Comando

```
vcli [SERVICE] [RESOURCE] [ACTION] [FLAGS]
```

**Exemplos**:

```bash
# MAXIMUS
vcli maximus decision list
vcli maximus decision get dec-123 --format json
vcli maximus decision approve dec-123 --reason "Approved"

# Immune
vcli immune health
vcli immune anomaly detect --threshold 0.8

# K8s
vcli k8s get pods -n production
vcli k8s delete pod nginx-abc --namespace default
vcli k8s logs nginx-abc -f --tail 100
```

#### Flags Globais

| Flag | Descrição | Exemplo |
|------|-----------|---------|
| `--format` | Output format (json, yaml, table) | `--format json` |
| `--output -o` | Output file | `-o results.json` |
| `--timeout` | Request timeout | `--timeout 60s` |
| `--verbose -v` | Verbose logging | `-v` |
| `--quiet -q` | Quiet mode (errors only) | `-q` |
| `--offline` | Force offline mode | `--offline` |

### 4.2 Modo Shell (REPL)

#### Iniciar Shell

```bash
vcli shell

# Output:
# vCLI Interactive Shell v2.0
# Type 'help' for available commands, 'exit' to quit
#
# vcli>
```

#### Comandos Shell

```bash
# Navegação
vcli> help                    # Lista comandos disponíveis
vcli> help maximus            # Help específico do MAXIMUS
vcli> exit                    # Sair do shell

# Histórico
vcli> history                 # Ver histórico de comandos
vcli> !5                      # Executar comando #5 do histórico
vcli> !!                      # Repetir último comando

# Auto-complete
vcli> max[TAB]                # Auto-completa para "maximus"
vcli> maximus dec[TAB]        # Auto-completa para "decision"
```

#### Configuração Shell

```bash
# Arquivo ~/.vcli/shell_config.yaml
shell:
  history_size: 1000
  autocomplete: true
  vi_mode: false           # false = emacs mode
  prompt: "vcli> "
  colors:
    command: blue
    success: green
    error: red
```

### 4.3 Modo TUI (Terminal UI)

#### Iniciar TUI

```bash
vcli tui

# Ou workspace específico
vcli tui --workspace governance
vcli tui --workspace performance
vcli tui --workspace investigation
```

#### Navegação TUI

**Atalhos de Teclado**:

| Tecla | Ação |
|-------|------|
| `Tab` | Próximo workspace |
| `Shift+Tab` | Workspace anterior |
| `1`, `2`, `3` | Ir para workspace 1, 2, 3 |
| `r` | Refresh/reload |
| `f` | Toggle fullscreen |
| `q` | Quit |
| `?` | Help |
| `Ctrl+C` | Emergency exit |

**Mouse** (se suportado):
- Click para selecionar
- Scroll para navegar
- Right-click para menu contextual

---

## 5. Comandos CLI - Referência Completa

### 5.1 MAXIMUS Governance

#### 5.1.1 Health Check

```bash
vcli maximus health
```

**Output**:
```json
{
  "status": "healthy",
  "version": "2.1.0",
  "uptime": "72h15m",
  "components": {
    "database": "healthy",
    "cache": "healthy",
    "queue": "healthy"
  }
}
```

#### 5.1.2 Decision Management

**Listar Decisões**:

```bash
# Todas as decisões
vcli maximus decision list

# Com filtros
vcli maximus decision list --status pending
vcli maximus decision list --priority high
vcli maximus decision list --limit 50
```

**Output**:
```
ID              STATUS    PRIORITY  CREATED              DESCRIPTION
dec-abc123      pending   high      2025-10-22 10:30     Approve deployment
dec-def456      approved  medium    2025-10-22 09:15     Update config
dec-ghi789      rejected  low       2025-10-21 14:00     Scale down service
```

**Obter Decisão Específica**:

```bash
vcli maximus decision get dec-abc123

# Output JSON detalhado
vcli maximus decision get dec-abc123 --format json
```

**Output**:
```json
{
  "id": "dec-abc123",
  "status": "pending",
  "priority": "high",
  "created_at": "2025-10-22T10:30:00Z",
  "description": "Approve production deployment",
  "context": {
    "service": "payment-api",
    "version": "v2.3.1",
    "risk_level": "medium"
  },
  "options": [
    {"id": "opt-1", "label": "Approve", "score": 0.85},
    {"id": "opt-2", "label": "Reject", "score": 0.15}
  ]
}
```

**Aprovar Decisão**:

```bash
vcli maximus decision approve dec-abc123 \
  --reason "Passed all tests" \
  --reviewer "juan@vertice.dev"
```

**Rejeitar Decisão**:

```bash
vcli maximus decision reject dec-abc123 \
  --reason "Failed security scan" \
  --reviewer "juan@vertice.dev"
```

#### 5.1.3 Batch Decision Operations

**Aprovar Múltiplas Decisões**:

```bash
# Por IDs
vcli maximus batch approve dec-abc123,dec-def456,dec-ghi789

# Por query/filtro
vcli maximus batch approve --priority low --max 10

# Com selector
vcli maximus batch approve --selector "status=pending,priority=low"
```

**Output**:
```
Processing 3 decisions...
[████████████████████████] 100% (3/3)

Results:
✓ dec-abc123: Approved
✓ dec-def456: Approved
✗ dec-ghi789: Failed (already processed)

Success: 2/3 (66%)
```

### 5.2 Immune Core

#### 5.2.1 Health Check

```bash
vcli immune health
```

**Output**:
```json
{
  "status": "healthy",
  "detection_engine": "running",
  "last_scan": "2025-10-22T11:45:00Z",
  "anomalies_detected_24h": 15
}
```

#### 5.2.2 Anomaly Detection

**Detectar Anomalias**:

```bash
# Scan completo
vcli immune anomaly detect

# Com threshold customizado
vcli immune anomaly detect --threshold 0.75

# Por serviço
vcli immune anomaly detect --service payment-api
```

**Output**:
```
Scanning for anomalies... ⏳

Found 3 anomalies:

[HIGH] payment-api: CPU usage spike (score: 0.92)
  - Current: 95%
  - Normal: 30%
  - Duration: 15 minutes

[MEDIUM] user-service: Error rate increase (score: 0.78)
  - Current: 5.2%
  - Normal: 0.5%
  - Duration: 5 minutes

[LOW] db-replica: Connection pool exhaustion (score: 0.65)
  - Current: 98 connections
  - Normal: 45 connections
  - Duration: 2 minutes
```

**Listar Anomalias Históricas**:

```bash
vcli immune anomaly list --since 24h
vcli immune anomaly list --severity high
vcli immune anomaly list --service payment-api --limit 50
```

### 5.3 HITL Console

#### 5.3.1 Authentication

**Login**:

```bash
vcli hitl login --username juan --password <password>

# Ou usando prompt interativo
vcli hitl login --username juan
# Password: ********
```

**Output**:
```
✓ Login successful
Token stored in Redis
Session expires: 2025-10-23 12:00:00
```

**Logout**:

```bash
vcli hitl logout
```

**Session Status**:

```bash
vcli hitl session
```

**Output**:
```
Session Active
Username: juan
Role: admin
Expires: 2025-10-23 12:00:00 (in 23h 45m)
```

#### 5.3.2 Decision Review (via HITL)

**Listar Decisões Pendentes**:

```bash
vcli hitl decisions --status pending
```

**Revisar Decisão**:

```bash
vcli hitl review dec-abc123
```

**Output interativo**:
```
Decision: dec-abc123
Description: Approve production deployment
Priority: high
Created: 2025-10-22 10:30

Options:
  1. Approve (score: 0.85)
  2. Reject (score: 0.15)

Your decision [1-2]: 1
Reason: Passed all tests

✓ Decision approved
```

### 5.4 Kubernetes Operations

#### 5.4.1 Get Resources

**Pods**:

```bash
# Todos os pods no namespace default
vcli k8s get pods

# Namespace específico
vcli k8s get pods -n production

# Todos os namespaces
vcli k8s get pods --all-namespaces

# Com seletores
vcli k8s get pods -l app=nginx
vcli k8s get pods --selector "env=production,tier=frontend"
```

**Output**:
```
NAMESPACE    NAME              READY   STATUS    RESTARTS   AGE
default      nginx-abc123      1/1     Running   0          5h
default      redis-def456      1/1     Running   1          10h
production   api-ghi789        2/2     Running   0          2d
```

**Deployments**:

```bash
vcli k8s get deployments -n production
```

**Services**:

```bash
vcli k8s get services -n default
```

**Nodes**:

```bash
vcli k8s get nodes
```

#### 5.4.2 Describe Resources

**Describe Pod**:

```bash
vcli k8s describe pod nginx-abc123 -n default
```

**Output**:
```
Name:         nginx-abc123
Namespace:    default
Node:         worker-01/192.168.1.10
Start Time:   2025-10-22 06:00:00
Status:       Running
IP:           10.244.1.5

Containers:
  nginx:
    Image:          nginx:1.21
    Port:           80/TCP
    State:          Running
    Ready:          True
    Restart Count:  0

Conditions:
  Type              Status
  Initialized       True
  Ready             True
  ContainersReady   True

Events:
  Type    Reason     Age   Message
  Normal  Scheduled  5h    Successfully assigned pod
  Normal  Pulled     5h    Container image pulled
  Normal  Created    5h    Created container
  Normal  Started    5h    Started container
```

#### 5.4.3 Logs

**Basic Logs**:

```bash
# Últimas linhas
vcli k8s logs nginx-abc123

# Streaming (follow)
vcli k8s logs nginx-abc123 -f

# Últimas N linhas
vcli k8s logs nginx-abc123 --tail 100

# Com timestamps
vcli k8s logs nginx-abc123 --timestamps
```

**Container Específico** (multi-container pods):

```bash
vcli k8s logs api-pod -c api-container
```

**Logs Anteriores** (após restart):

```bash
vcli k8s logs nginx-abc123 --previous
```

#### 5.4.4 Delete Resources

**Delete Pod**:

```bash
vcli k8s delete pod nginx-abc123 -n default
```

**Delete com Selector**:

```bash
# Delete todos os pods com label app=old
vcli k8s delete pods --selector app=old -n default

# Dry-run (preview)
vcli k8s delete pods --selector app=old --dry-run

# Com confirmação
vcli k8s delete pods --selector app=old --confirm
```

**Output**:
```
Selecting pods with: app=old
Found 5 pods

Pods to delete:
  - old-worker-1
  - old-worker-2
  - old-worker-3
  - old-api-1
  - old-api-2

Proceed with deletion? [y/N]: y

Deleting pods... [████████████] 100% (5/5)

Results:
✓ old-worker-1: Deleted
✓ old-worker-2: Deleted
✓ old-worker-3: Deleted
✓ old-api-1: Deleted
✓ old-api-2: Deleted

Success: 5/5 (100%)
```

**Batch Delete**:

```bash
# Processar em paralelo (max 10 concurrent)
vcli k8s batch delete pods \
  --selector app=old \
  --max-concurrent 10 \
  --stop-on-error

# Com rollback automático
vcli k8s batch delete pods \
  --selector app=old \
  --rollback-on-error
```

### 5.5 Consciousness Services

#### 5.5.1 Eureka (Discovery)

```bash
# Service discovery
vcli consciousness eureka discover payment-api

# Health check
vcli consciousness eureka health
```

#### 5.5.2 Oraculo (Predictions)

```bash
# Get prediction
vcli consciousness oraculo predict \
  --model traffic-forecast \
  --input '{"hour": 14, "day": "monday"}'

# List available models
vcli consciousness oraculo models
```

#### 5.5.3 Predict Service

```bash
# Make prediction
vcli consciousness predict \
  --service payment-api \
  --metric cpu \
  --horizon 1h
```

### 5.6 Configuration

#### 5.6.1 Show Config

```bash
# Show all configuration
vcli config show

# Show specific service
vcli config show maximus
vcli config show kubernetes
```

**Output**:
```yaml
maximus:
  endpoint: http://localhost:8100
  timeout: 30s

immune:
  endpoint: http://localhost:8200
  timeout: 30s
```

#### 5.6.2 Set Config

```bash
# Set individual values
vcli config set maximus.endpoint http://prod-maximus:8100
vcli config set kubernetes.context production

# Validate config
vcli config validate
```

### 5.7 Troubleshooting

#### 5.7.1 Troubleshoot Specific Service

```bash
# MAXIMUS
vcli troubleshoot maximus
```

**Output**:
```
Diagnosing MAXIMUS Governance...

[1/5] Checking endpoint reachability...
  Endpoint: http://localhost:8100
  ✓ DNS resolution: OK
  ✓ TCP connection: OK (15ms)
  ✓ HTTP response: OK (200)

[2/5] Testing API health endpoint...
  ✓ /health: healthy
  ✓ Uptime: 72h15m
  ✓ Version: 2.1.0

[3/5] Verifying authentication...
  ⚠ No auth token found
  ℹ MAXIMUS does not require auth for read operations

[4/5] Testing decision API...
  ✓ GET /decisions: 200 OK
  ✓ Response time: 45ms
  ✓ Returned 15 decisions

[5/5] Checking connectivity to dependencies...
  ✓ Database: connected
  ✓ Redis: connected

Summary: ✓ MAXIMUS is healthy

No issues detected.
```

**Troubleshoot com Erros**:

```bash
vcli troubleshoot immune
```

**Output**:
```
Diagnosing Immune Core...

[1/5] Checking endpoint reachability...
  Endpoint: http://localhost:8200
  ✗ TCP connection: FAILED
  Error: dial tcp: connection refused

❌ Cannot reach Immune Core

💡 Suggestions:
  1. Verify Immune Core service is running
     $ systemctl status immune-core
     $ docker ps | grep immune

  2. Check endpoint configuration
     $ vcli config show immune

  3. Test connectivity manually
     $ curl http://localhost:8200/health

  4. Check firewall rules
     $ sudo iptables -L | grep 8200

  5. Check logs for errors
     $ journalctl -u immune-core -n 50

Need help? Run: vcli troubleshoot immune --verbose
```

#### 5.7.2 Troubleshoot All Services

```bash
vcli troubleshoot all
```

**Output**:
```
Running diagnostics on all services...

✓ MAXIMUS Governance: Healthy
✓ Kubernetes: Healthy
✗ Immune Core: Connection failed
✓ HITL Console: Healthy

Summary: 3/4 services healthy (75%)

Issues detected:
  - Immune Core: Cannot connect to http://localhost:8200

Run individual diagnostics:
  vcli troubleshoot immune --verbose
```

---

## 6. TUI Workspaces

### 6.1 Governance Workspace

**Iniciar**:

```bash
vcli tui --workspace governance
```

**Interface**:

```
╭─────────────────────────────────────────────────────────────╮
│ 📋 GOVERNANCE - HITL Decision Review                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Pending Decisions (5)                                      │
│  ┌────────────────────────────────────────────────────┐    │
│  │ ID: dec-abc123                           [HIGH]    │    │
│  │ Approve production deployment                      │    │
│  │ Created: 2025-10-22 10:30                          │    │
│  │ ───────────────────────────────────────────────── │    │
│  │ ID: dec-def456                          [MEDIUM]   │    │
│  │ Update configuration                               │    │
│  │ Created: 2025-10-22 09:15                          │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  Decision Details                                           │
│  ┌────────────────────────────────────────────────────┐    │
│  │ ID: dec-abc123                                     │    │
│  │ Description: Approve production deployment         │    │
│  │ Service: payment-api                               │    │
│  │ Version: v2.3.1                                    │    │
│  │ Risk Level: medium                                 │    │
│  │                                                     │    │
│  │ Options:                                           │    │
│  │   [1] Approve (score: 0.85)                        │    │
│  │   [2] Reject  (score: 0.15)                        │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│ Enter: Review | r: Refresh | Tab: Next Workspace | q: Quit │
╰─────────────────────────────────────────────────────────────╯
```

**Atalhos**:
- `↑`/`↓`: Navegar decisões
- `Enter`: Revisar decisão selecionada
- `a`: Aprovar decisão
- `r`: Rejeitar decisão
- `f`: Filtrar por prioridade
- `s`: Ordenar (por data, prioridade)

### 6.2 Performance Workspace

**Iniciar**:

```bash
vcli tui --workspace performance
```

**Interface**:

```
╭─────────────────────────────────────────────────────────────╮
│ ⚡ PERFORMANCE - Real-time Metrics Dashboard                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  System Throughput                                          │
│  ┌────────────────────────────────────────────────────┐    │
│  │ Current: 1,542 req/s                    ▁▃▅▆▇█▇▆  │    │
│  │ Average: 1,200 req/s                               │    │
│  │ Peak: 2,100 req/s                                  │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  Queue Status                                               │
│  ┌────────────────────────────────────────────────────┐    │
│  │ MAXIMUS:  [████████──────] 125 / 500 (25%)        │    │
│  │ Immune:   [██────────────]  45 / 500 ( 9%)        │    │
│  │ HITL:     [███───────────]  78 / 500 (16%)        │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  SLA Compliance                                             │
│  ┌────────────────────────────────────────────────────┐    │
│  │ API Response Time (<100ms):        ✓ 99.2%        │    │
│  │ Error Rate (<1%):                  ✓ 0.5%         │    │
│  │ Availability (>99.9%):             ✓ 99.95%       │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  Service Health                                             │
│  ┌────────────────────────────────────────────────────┐    │
│  │ MAXIMUS:     ✓ Healthy   (uptime: 72h)            │    │
│  │ Immune:      ✓ Healthy   (uptime: 168h)           │    │
│  │ Kubernetes:  ✓ Healthy   (5/5 nodes ready)        │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│ r: Refresh | i: Inspector | Tab: Next Workspace | q: Quit  │
╰─────────────────────────────────────────────────────────────╯
```

**Features**:
- **Sparklines**: Trending visualization (▁▂▃▄▅▆▇█)
- **Real-time updates**: Auto-refresh every 5s
- **Color coding**: Green (healthy), Yellow (warning), Red (critical)
- **Queue monitoring**: Visual progress bars

**Atalhos**:
- `r`: Refresh manual
- `i`: Abrir inspector detalhado
- `1-5`: Alternar entre views (throughput, queue, SLA, services, custom)
- `+`/`-`: Ajustar refresh interval

### 6.3 Investigation Workspace

**Iniciar**:

```bash
vcli tui --workspace investigation
```

**Interface**:

```
╭─────────────────────────────────────────────────────────────╮
│ 🔍 INVESTIGATION - Resource Inspector                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Namespace: production                    Resource: pod     │
│                                                              │
│  Resources                         Details                  │
│  ┌──────────────────────┐  ┌──────────────────────────┐    │
│  │ > nginx-abc123       │  │ Name: nginx-abc123       │    │
│  │   redis-def456       │  │ Status: Running          │    │
│  │   api-ghi789         │  │ Node: worker-01          │    │
│  │   db-jkl012          │  │ IP: 10.244.1.5           │    │
│  │   cache-mno345       │  │ Created: 5h ago          │    │
│  │                      │  │                          │    │
│  │ (15 total)           │  │ Containers:              │    │
│  └──────────────────────┘  │   - nginx: Running       │    │
│                             │                          │    │
│  Logs (last 10 lines)       │ Events (last 5)          │    │
│  ┌──────────────────────┐  └──────────────────────────┘    │
│  │ 12:01 GET /health OK │  ┌──────────────────────────┐    │
│  │ 12:02 GET /api OK    │  │ 11:00 Pod Scheduled      │    │
│  │ 12:03 POST /data OK  │  │ 11:01 Image Pulled       │    │
│  │ 12:04 GET /health OK │  │ 11:01 Container Created  │    │
│  │ 12:05 GET /api OK    │  │ 11:01 Container Started  │    │
│  └──────────────────────┘  └──────────────────────────┘    │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│ ↑↓: Navigate | Enter: Inspect | l: Logs | e: Events | q: Quit│
╰─────────────────────────────────────────────────────────────╯
```

**Features**:
- **Multi-resource types**: Pods, Deployments, Services, Nodes
- **Live logs**: Streaming logs viewer
- **Event timeline**: Real-time events
- **Resource inspector**: Detailed YAML/JSON viewer

**Atalhos**:
- `↑`/`↓`: Navegar recursos
- `Enter`: Inspect detalhado
- `l`: Abrir log viewer
- `e`: Abrir event timeline
- `y`: Export YAML
- `j`: Export JSON
- `n`: Change namespace
- `t`: Change resource type

### 6.4 Navegação entre Workspaces

**Alternar Workspaces**:

```
Tab                → Próximo workspace
Shift+Tab          → Workspace anterior
1                  → Governance
2                  → Performance
3                  → Investigation
```

**Workspace Switcher** (atalho `w`):

```
╭─────────────────────────────╮
│ Select Workspace:           │
│                             │
│  [1] 📋 Governance          │
│  [2] ⚡ Performance         │
│  [3] 🔍 Investigation       │
│                             │
│  Press 1-3 or ESC to cancel │
╰─────────────────────────────╯
```

---

## 7. Operação Offline

### 7.1 Como Funciona

vCLI possui **3 camadas de offline support**:

1. **Response Cache**: Armazena respostas de leitura (GET requests)
2. **Command Queue**: Queue de operações write (POST/PUT/DELETE)
3. **Sync Manager**: Sincronização automática a cada 5 minutos

**Arquitetura**:

```
Online Mode:
  vcli command → HTTP client → Backend → Response → Cache

Offline Mode:
  vcli command → Queue → BadgerDB
  [Later, when online]
  Sync Manager → Process queue → Backend → Dequeue
```

### 7.2 Operação Offline Automática

**vCLI detecta automaticamente quando está offline**:

```bash
# Você executa um comando
vcli maximus decision approve dec-abc123

# Se offline, automaticamente:
# 1. Comando vai para a queue
# 2. Confirmação local
# 3. Sync quando voltar online
```

**Output Offline**:
```
⚠️  Offline Mode Detected

Command queued for sync:
  Operation: approve_decision
  Decision ID: dec-abc123
  Queued at: 2025-10-22 12:00:00

Queue status: 3 operations pending
Next sync: When connection is restored (auto-retry every 5 min)

✓ Operation will be executed when online
```

### 7.3 Operação Offline Manual

**Forçar Offline Mode**:

```bash
vcli --offline maximus decision list
```

**Output**:
```
Using cached data (last updated: 10 min ago)

ID              STATUS    PRIORITY
dec-abc123      pending   high
dec-def456      approved  medium
dec-ghi789      rejected  low

⚠️  Offline mode - showing cached data
```

### 7.4 Gerenciar Queue

**Ver Queue Status**:

```bash
vcli offline status
```

**Output**:
```
Offline Queue Status

Pending operations: 5

Queue:
  1. [2025-10-22 12:00] approve_decision (dec-abc123)
  2. [2025-10-22 12:05] reject_decision (dec-def456)
  3. [2025-10-22 12:10] update_config (max-concurrent=15)
  4. [2025-10-22 12:15] delete_pod (nginx-abc123)
  5. [2025-10-22 12:20] approve_decision (dec-ghi789)

Last sync attempt: 2025-10-22 12:25 (failed)
Next sync attempt: 2025-10-22 12:30 (in 3 min)
```

**Sincronizar Manualmente**:

```bash
vcli offline sync
```

**Output**:
```
Synchronizing offline queue...

Processing 5 operations... [████████████] 100%

Results:
✓ approve_decision (dec-abc123): Success
✓ reject_decision (dec-def456): Success
✗ update_config: Failed (validation error)
✓ delete_pod (nginx-abc123): Success
✓ approve_decision (dec-ghi789): Success

Success: 4/5 (80%)
Failed operations remain in queue for retry.
```

**Limpar Queue**:

```bash
# Limpar todas as operações
vcli offline clear

# Limpar operações específicas
vcli offline clear --failed-only
vcli offline clear --older-than 24h
```

### 7.5 Cache Management

**Ver Cache Status**:

```bash
vcli cache status
```

**Output**:
```
Cache Status

Total cached responses: 45
Cache size: 2.3 MB
Cache age:
  - <1h:  15 responses
  - 1-6h: 20 responses
  - >6h:  10 responses

Cached endpoints:
  /decisions: 25 responses (last: 15 min ago)
  /health: 10 responses (last: 5 min ago)
  /pods: 10 responses (last: 30 min ago)
```

**Limpar Cache**:

```bash
# Limpar todo o cache
vcli cache clear

# Limpar cache expirado (>6h)
vcli cache clear --expired

# Limpar cache específico
vcli cache clear --endpoint /decisions
```

### 7.6 Configuração Offline Mode

**Arquivo de Config** (`~/.vcli/config.yaml`):

```yaml
offline:
  enabled: true
  sync_interval: 5m          # Auto-sync interval
  cache_ttl: 6h              # Cache TTL
  cache_dir: ~/.vcli/cache
  max_queue_size: 1000       # Max queued operations
  retry_attempts: 3          # Max retries per operation
  retry_backoff: exponential # linear | exponential
```

**Desabilitar Offline Mode**:

```bash
vcli config set offline.enabled false
```

---

## 8. Sistema de Erros e Troubleshooting

### 8.1 Tipos de Erros

#### 8.1.1 Connection Errors

**Quando ocorre**: Falha ao conectar com backend

**Exemplo**:

```bash
vcli maximus health
```

**Output**:
```
❌ CONNECTION Error: MAXIMUS Governance

Failed to connect
Endpoint: http://localhost:8100
Operation: health check
Cause: dial tcp: connection refused

💡 Suggestions:
  1. Verify MAXIMUS Governance service is running
     $ systemctl status maximus-governance
     $ docker ps | grep maximus

  2. Check endpoint configuration
     $ vcli config show maximus

  3. Test connectivity
     $ curl http://localhost:8100/health

Need help? Run: vcli troubleshoot maximus
```

#### 8.1.2 Authentication Errors

**Quando ocorre**: Credenciais inválidas ou token expirado

**Exemplo**:

```bash
vcli hitl login --username test --password wrong
```

**Output**:
```
❌ AUTH Error: HITL Console

Invalid credentials
Endpoint: http://localhost:8000/api
Operation: login

💡 Suggestions:
  1. Verify your credentials are correct

  2. Login again to refresh token
     $ vcli hitl login --username <your-username>

  3. Check if your account has required permissions

Need help? Run: vcli troubleshoot hitl
```

#### 8.1.3 Validation Errors

**Quando ocorre**: Input inválido

**Exemplo**:

```bash
vcli maximus decision get invalid-id-123
```

**Output**:
```
❌ VALIDATION Error: Invalid Decision ID

Input validation failed
Field: decision_id
Value: invalid-id-123
Expected format: dec-[a-z0-9]{6}

💡 Suggestions:
  1. Check the decision ID format
     Valid example: dec-abc123

  2. List available decisions
     $ vcli maximus decision list

  3. See help for decision commands
     $ vcli help maximus decision

Need help? Run: vcli help maximus
```

### 8.2 Troubleshooting Automático

#### 8.2.1 Troubleshoot Service

**MAXIMUS**:

```bash
vcli troubleshoot maximus
```

**Immune**:

```bash
vcli troubleshoot immune
```

**HITL**:

```bash
vcli troubleshoot hitl
```

**Kubernetes**:

```bash
vcli troubleshoot k8s
```

#### 8.2.2 Troubleshoot All

```bash
vcli troubleshoot all
```

**Output detalhado**:
```
╭─────────────────────────────────────────────────────────────╮
│ VCLI System Diagnostics                                     │
├─────────────────────────────────────────────────────────────┤

[1/4] MAXIMUS Governance
  ✓ Endpoint reachable (http://localhost:8100)
  ✓ API health: healthy
  ✓ Response time: 45ms
  ✓ Dependencies: OK

[2/4] Immune Core
  ✗ Endpoint unreachable (http://localhost:8200)
  → Connection refused

  💡 Suggestions:
    1. Start the Immune Core service
       $ docker start immune-core
    2. Check logs
       $ docker logs immune-core
    3. Verify port 8200 is not blocked
       $ sudo netstat -tulpn | grep 8200

[3/4] HITL Console
  ✓ Endpoint reachable (http://localhost:8000)
  ⚠ Authentication: Not logged in
  ✓ API health: healthy

  💡 Login to access full features:
    $ vcli hitl login

[4/4] Kubernetes
  ✓ Kubeconfig found (~/.kube/config)
  ✓ Cluster reachable
  ✓ Context: minikube
  ✓ Nodes: 1/1 ready
  ✓ API server: v1.28.3

╰─────────────────────────────────────────────────────────────╯

Summary: 3/4 services healthy (75%)

Issues:
  - Immune Core: Connection failed

Run detailed diagnostics:
  vcli troubleshoot immune --verbose
```

#### 8.2.3 Verbose Mode

```bash
vcli troubleshoot maximus --verbose
```

**Output**:
```
[DEBUG] Starting MAXIMUS diagnostics...
[DEBUG] Endpoint: http://localhost:8100
[DEBUG] Timeout: 30s

[1/5] DNS Resolution
  [DEBUG] Resolving localhost...
  [DEBUG] IP: 127.0.0.1
  ✓ DNS: OK (2ms)

[2/5] TCP Connection
  [DEBUG] Dialing 127.0.0.1:8100...
  [DEBUG] Connection established
  ✓ TCP: OK (5ms)

[3/5] HTTP Request
  [DEBUG] GET http://localhost:8100/health
  [DEBUG] Response code: 200
  [DEBUG] Response time: 45ms
  [DEBUG] Response body: {"status":"healthy","version":"2.1.0"}
  ✓ HTTP: OK

[4/5] API Validation
  [DEBUG] Parsing JSON response...
  [DEBUG] Validating schema...
  ✓ API: Valid response

[5/5] Dependencies
  [DEBUG] Checking database connection...
  [DEBUG] Database: postgres (connected)
  [DEBUG] Checking Redis connection...
  [DEBUG] Redis: localhost:6379 (connected)
  ✓ Dependencies: All OK

[DEBUG] Diagnostics complete
✓ MAXIMUS is healthy
```

### 8.3 Error Recovery

#### 8.3.1 Auto-Retry

vCLI tenta automaticamente 3x antes de falhar:

```bash
vcli maximus health
```

**Output com retry**:
```
Connecting to MAXIMUS... ⏳
Attempt 1/3: Failed (connection timeout)
Attempt 2/3: Failed (connection timeout)
Attempt 3/3: Success ✓

{"status": "healthy"}
```

#### 8.3.2 Manual Retry

```bash
# Flag --retry
vcli maximus health --retry 5

# Flag --retry-delay
vcli maximus health --retry 3 --retry-delay 10s
```

#### 8.3.3 Fallback para Cache

```bash
# Se falhar, usar cache automaticamente
vcli maximus decision list --use-cache-on-error
```

**Output**:
```
⚠️  Connection failed, using cached data

ID              STATUS    PRIORITY
dec-abc123      pending   high
dec-def456      approved  medium

(Cached 15 min ago)
```

### 8.4 Logging e Debug

#### 8.4.1 Enable Debug Logging

```bash
# Via flag
vcli --debug maximus health

# Via environment
export VCLI_DEBUG=true
vcli maximus health
```

**Output**:
```
[DEBUG 12:00:00] Config loaded from ~/.vcli/config.yaml
[DEBUG 12:00:00] MAXIMUS endpoint: http://localhost:8100
[DEBUG 12:00:00] HTTP GET http://localhost:8100/health
[DEBUG 12:00:00] Request headers: {User-Agent: vcli/2.0}
[DEBUG 12:00:01] Response: 200 OK (45ms)
[DEBUG 12:00:01] Response body: {"status":"healthy"}

{"status": "healthy"}
```

#### 8.4.2 Log File

```bash
# Log to file
vcli --log-file /tmp/vcli.log maximus health

# Tail log
tail -f /tmp/vcli.log
```

**Log format**:
```
2025-10-22 12:00:00 [INFO] Starting vCLI v2.0
2025-10-22 12:00:00 [DEBUG] Loading config from ~/.vcli/config.yaml
2025-10-22 12:00:00 [INFO] Executing command: maximus health
2025-10-22 12:00:00 [DEBUG] HTTP GET http://localhost:8100/health
2025-10-22 12:00:01 [INFO] Response: 200 OK (45ms)
```

---

## 9. Operações Avançadas

### 9.1 Batch Operations

#### 9.1.1 Batch Decision Processing

**Aprovar Múltiplas Decisões**:

```bash
# Por IDs
vcli maximus batch approve dec-abc123,dec-def456,dec-ghi789 \
  --reason "Approved in batch"

# Por selector
vcli maximus batch approve \
  --selector "priority=low,status=pending" \
  --max 50
```

**Output**:
```
Selecting decisions...
Found 50 decisions matching criteria

Processing decisions in parallel (10 concurrent)...
[████████████████████████████████] 100% (50/50)

Results:
✓ Approved: 48
✗ Failed: 2
  - dec-xyz789: Already processed
  - dec-uvw456: Validation error

Success rate: 96% (48/50)
Elapsed time: 5.2s
Average: 104ms per decision
```

**Com Rollback**:

```bash
vcli maximus batch approve \
  --selector "priority=low" \
  --rollback-on-error
```

**Output**:
```
Processing 10 decisions...
[███████───────] 70% (7/10)

✗ Error on decision dec-ghi789: Validation failed

Rolling back 7 approved decisions...
[████████████] 100% (7/7)

All changes rolled back.
No decisions were modified.
```

#### 9.1.2 Batch Kubernetes Operations

**Delete Múltiplos Pods**:

```bash
vcli k8s batch delete pods \
  --selector app=old-version \
  --namespace production \
  --max-concurrent 5
```

**Scale Múltiplos Deployments**:

```bash
vcli k8s batch scale deployments \
  --selector tier=backend \
  --replicas 3 \
  --namespace production
```

#### 9.1.3 Batch Configuration

```yaml
# ~/.vcli/batch_config.yaml
batch:
  max_concurrent: 10      # Max parallel operations
  stop_on_error: false    # Continue even if one fails
  rollback_on_error: true # Rollback all if any fails
  timeout: 60s            # Timeout per operation
  retry_failed: true      # Retry failed operations
  retry_attempts: 3
```

### 9.2 Scripting e Automação

#### 9.2.1 Scripts Bash

**Exemplo 1: Aprovar todas as decisões low priority**:

```bash
#!/bin/bash
# approve_low_priority.sh

set -e

echo "Fetching low priority decisions..."
decisions=$(vcli maximus decision list \
  --priority low \
  --status pending \
  --format json | jq -r '.[].id')

count=$(echo "$decisions" | wc -l)
echo "Found $count decisions to approve"

echo "$decisions" | while read -r dec_id; do
  echo "Approving $dec_id..."
  vcli maximus decision approve "$dec_id" \
    --reason "Auto-approved: low priority"
done

echo "✓ All $count decisions approved"
```

**Exemplo 2: Cleanup de Pods Completed**:

```bash
#!/bin/bash
# cleanup_completed_pods.sh

namespaces="default production staging"

for ns in $namespaces; do
  echo "Cleaning up completed pods in namespace: $ns"

  vcli k8s get pods -n "$ns" \
    --field-selector status.phase=Succeeded \
    --format json | \
    jq -r '.[].metadata.name' | \
    while read -r pod; do
      echo "Deleting pod: $pod"
      vcli k8s delete pod "$pod" -n "$ns"
    done
done

echo "✓ Cleanup complete"
```

#### 9.2.2 CI/CD Integration

**GitLab CI Example**:

```yaml
# .gitlab-ci.yml

deploy:
  stage: deploy
  script:
    # Install vCLI
    - curl -L https://github.com/verticedev/vcli-go/releases/latest/download/vcli-linux-amd64 -o vcli
    - chmod +x vcli

    # Configure
    - export MAXIMUS_ENDPOINT=$PROD_MAXIMUS_ENDPOINT
    - export KUBECONFIG=$PROD_KUBECONFIG

    # Health check
    - ./vcli troubleshoot all || exit 1

    # Deploy
    - kubectl apply -f deploy.yaml

    # Wait for decision approval
    - |
      decision_id=$(./vcli maximus decision list \
        --selector "type=deployment,service=$CI_PROJECT_NAME" \
        --format json | jq -r '.[0].id')

      echo "Waiting for decision approval: $decision_id"

      while true; do
        status=$(./vcli maximus decision get "$decision_id" \
          --format json | jq -r '.status')

        if [ "$status" = "approved" ]; then
          echo "✓ Deployment approved"
          break
        elif [ "$status" = "rejected" ]; then
          echo "✗ Deployment rejected"
          exit 1
        fi

        sleep 10
      done
  only:
    - main
```

**GitHub Actions Example**:

```yaml
# .github/workflows/deploy.yml

name: Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install vCLI
        run: |
          wget https://github.com/verticedev/vcli-go/releases/latest/download/vcli-linux-amd64
          chmod +x vcli-linux-amd64
          sudo mv vcli-linux-amd64 /usr/local/bin/vcli

      - name: Health Check
        env:
          MAXIMUS_ENDPOINT: ${{ secrets.MAXIMUS_ENDPOINT }}
        run: vcli troubleshoot maximus

      - name: Deploy
        env:
          KUBECONFIG: ${{ secrets.KUBECONFIG }}
        run: |
          kubectl apply -f k8s/
          vcli k8s get pods --watch --timeout 5m
```

#### 9.2.3 Cron Jobs

**Exemplo: Daily cleanup**:

```bash
# /etc/cron.d/vcli-cleanup
0 2 * * * vcli-user /usr/local/bin/vcli k8s batch delete pods --selector status=Completed --all-namespaces > /var/log/vcli-cleanup.log 2>&1
```

**Exemplo: Hourly metrics snapshot**:

```bash
# /etc/cron.d/vcli-metrics
0 * * * * vcli-user /usr/local/bin/vcli maximus metrics --format json > /var/log/metrics/maximus-$(date +\%Y\%m\%d-\%H).json
```

### 9.3 Custom Output Formats

#### 9.3.1 JSON Output

```bash
vcli maximus decision list --format json
```

**Output**:
```json
[
  {
    "id": "dec-abc123",
    "status": "pending",
    "priority": "high",
    "created_at": "2025-10-22T10:30:00Z",
    "description": "Approve production deployment"
  },
  {
    "id": "dec-def456",
    "status": "approved",
    "priority": "medium",
    "created_at": "2025-10-22T09:15:00Z",
    "description": "Update configuration"
  }
]
```

**Processar com jq**:

```bash
# Extrair apenas IDs
vcli maximus decision list --format json | jq -r '.[].id'

# Filtrar por priority
vcli maximus decision list --format json | jq '.[] | select(.priority == "high")'

# Contar decisões por status
vcli maximus decision list --format json | jq 'group_by(.status) | map({status: .[0].status, count: length})'
```

#### 9.3.2 YAML Output

```bash
vcli k8s get pods --format yaml
```

**Output**:
```yaml
- metadata:
    name: nginx-abc123
    namespace: default
  spec:
    containers:
    - image: nginx:1.21
      name: nginx
  status:
    phase: Running
```

#### 9.3.3 CSV Output

```bash
vcli maximus decision list --format csv > decisions.csv
```

**Output**:
```csv
id,status,priority,created_at,description
dec-abc123,pending,high,2025-10-22T10:30:00Z,Approve production deployment
dec-def456,approved,medium,2025-10-22T09:15:00Z,Update configuration
```

#### 9.3.4 Custom Templates

**Go Template**:

```bash
vcli maximus decision list \
  --format template \
  --template '{{range .}}{{.id}}: {{.status}} ({{.priority}}){{"\n"}}{{end}}'
```

**Output**:
```
dec-abc123: pending (high)
dec-def456: approved (medium)
dec-ghi789: rejected (low)
```

### 9.4 Watch Mode

#### 9.4.1 Watch Decisions

```bash
vcli maximus decision list --watch
```

**Output (atualiza a cada 5s)**:
```
[12:00:00] 5 decisions

ID              STATUS    PRIORITY
dec-abc123      pending   high
dec-def456      approved  medium
dec-ghi789      rejected  low

[12:00:05] 6 decisions (+1 new)

ID              STATUS    PRIORITY
dec-abc123      approved  high      ← Status changed!
dec-def456      approved  medium
dec-ghi789      rejected  low
dec-jkl012      pending   high      ← New!
```

#### 9.4.2 Watch Pods

```bash
vcli k8s get pods --watch -n production
```

**Output**:
```
[12:00:00]
NAME            READY   STATUS
nginx-abc       1/1     Running
redis-def       1/1     Running

[12:00:05]
NAME            READY   STATUS
nginx-abc       1/1     Running
redis-def       1/1     Running
api-ghi         0/1     Pending   ← New pod

[12:00:10]
NAME            READY   STATUS
nginx-abc       1/1     Running
redis-def       1/1     Running
api-ghi         1/1     Running   ← Now running
```

---

## 10. Casos de Uso Práticos

### 10.1 Caso 1: Deployment com Aprovação HITL

**Cenário**: Deploy de nova versão com aprovação humana requerida

**Passos**:

```bash
# 1. Health check dos serviços
vcli troubleshoot all

# 2. Aplicar deployment no K8s
kubectl apply -f deploy-v2.yaml

# 3. Criar decisão HITL
decision_id=$(vcli maximus decision create \
  --description "Approve deployment v2.3.1" \
  --context '{"service":"payment-api","version":"v2.3.1"}' \
  --priority high \
  --format json | jq -r '.id')

echo "Decision created: $decision_id"

# 4. Aguardar aprovação (polling)
while true; do
  status=$(vcli maximus decision get "$decision_id" --format json | jq -r '.status')

  if [ "$status" = "approved" ]; then
    echo "✓ Deployment approved!"
    break
  elif [ "$status" = "rejected" ]; then
    echo "✗ Deployment rejected!"
    kubectl rollout undo deployment/payment-api
    exit 1
  fi

  echo "Waiting for approval... (status: $status)"
  sleep 10
done

# 5. Verificar deployment
vcli k8s get pods -l app=payment-api --watch --timeout 5m

echo "✓ Deployment complete"
```

### 10.2 Caso 2: Incident Response

**Cenário**: Resposta rápida a anomalia detectada

**Passos**:

```bash
# 1. Detectar anomalia
anomaly=$(vcli immune anomaly detect --threshold 0.8 --format json | jq -r '.[0]')
service=$(echo "$anomaly" | jq -r '.service')
severity=$(echo "$anomaly" | jq -r '.severity')

echo "Anomaly detected: $service ($severity)"

# 2. Abrir Investigation workspace para análise
vcli tui --workspace investigation

# (User inspeciona logs, events, recursos)

# 3. Executar ação corretiva automaticamente
if [ "$severity" = "HIGH" ]; then
  echo "High severity - scaling up service"

  vcli k8s scale deployment "$service" --replicas 5 -n production

  # Criar decisão para review
  vcli maximus decision create \
    --description "Auto-scaled $service due to anomaly" \
    --context "{\"service\":\"$service\",\"anomaly_score\":0.92}" \
    --priority high
fi

# 4. Monitorar recuperação
vcli tui --workspace performance
```

### 10.3 Caso 3: Batch Cleanup

**Cenário**: Limpar recursos antigos em massa

**Passos**:

```bash
# 1. Identificar recursos para cleanup
echo "Finding old completed pods..."
old_pods=$(vcli k8s get pods \
  --all-namespaces \
  --field-selector status.phase=Succeeded \
  --format json | \
  jq -r '.[] | select(.metadata.creationTimestamp < (now - 86400 | strftime("%Y-%m-%dT%H:%M:%SZ"))) | .metadata.name')

count=$(echo "$old_pods" | wc -l)
echo "Found $count old pods to delete"

# 2. Criar decisão para aprovação
decision_id=$(vcli maximus decision create \
  --description "Cleanup $count completed pods older than 24h" \
  --priority low \
  --format json | jq -r '.id')

# 3. Aguardar aprovação
vcli maximus decision get "$decision_id" --watch

# 4. Executar cleanup em batch
echo "$old_pods" | while read -r pod; do
  namespace=$(vcli k8s get pod "$pod" --all-namespaces --format json | jq -r '.metadata.namespace')
  vcli k8s delete pod "$pod" -n "$namespace"
done

echo "✓ Cleanup complete: $count pods deleted"
```

### 10.4 Caso 4: Monitoring Dashboard

**Cenário**: Dashboard de monitoramento contínuo

**Setup**:

```bash
# Terminal 1: Performance metrics
vcli tui --workspace performance

# Terminal 2: Log streaming
vcli k8s logs -l app=payment-api -f --all-containers

# Terminal 3: Watch decisions
vcli maximus decision list --status pending --watch

# Terminal 4: Watch anomalies
watch -n 30 'vcli immune anomaly detect --threshold 0.7'
```

**Uso**:
- Performance workspace mostra métricas em tempo real
- Logs stream mostram atividade da aplicação
- Decisions watch alerta sobre aprovações pendentes
- Anomaly detection roda a cada 30s

### 10.5 Caso 5: Offline Operations

**Cenário**: Trabalhar durante conectividade intermitente

**Passos**:

```bash
# 1. Trabalhar normalmente (mesmo offline)
vcli maximus decision list
# → Usa cache automático se offline

# 2. Executar operações write
vcli maximus decision approve dec-abc123 --reason "Approved offline"
# → Vai para queue automática

vcli k8s delete pod old-pod -n default
# → Queued

# 3. Verificar queue
vcli offline status
# Output:
# Pending operations: 2
#   1. approve_decision (dec-abc123)
#   2. delete_pod (old-pod)

# 4. Quando voltar online, sync automático acontece
# Ou forçar sync manual:
vcli offline sync

# Output:
# ✓ approve_decision: Success
# ✓ delete_pod: Success
# Queue is now empty
```

---

## 11. Referência Rápida

### 11.1 Comandos Essenciais

```bash
# Health checks
vcli maximus health
vcli immune health
vcli troubleshoot all

# MAXIMUS Decisions
vcli maximus decision list
vcli maximus decision get <id>
vcli maximus decision approve <id> --reason "..."
vcli maximus decision reject <id> --reason "..."

# Kubernetes
vcli k8s get pods [-n namespace]
vcli k8s describe pod <name>
vcli k8s logs <pod> [-f] [--tail 100]
vcli k8s delete pod <name>

# HITL
vcli hitl login --username <user>
vcli hitl logout
vcli hitl session

# TUI
vcli tui
vcli tui --workspace governance|performance|investigation

# Offline
vcli offline status
vcli offline sync
vcli offline clear

# Troubleshooting
vcli troubleshoot <service>
vcli troubleshoot all
```

### 11.2 Flags Comuns

```bash
--format json|yaml|table|csv     # Output format
--output -o <file>               # Save to file
--namespace -n <namespace>       # K8s namespace
--selector -l <key=value>        # Label selector
--watch -w                       # Watch mode
--follow -f                      # Follow logs
--timeout <duration>             # Timeout (30s, 1m, etc)
--verbose -v                     # Verbose output
--quiet -q                       # Quiet mode
--debug                          # Debug logging
--offline                        # Force offline mode
```

### 11.3 Environment Variables

```bash
# Endpoints
MAXIMUS_ENDPOINT=http://localhost:8100
IMMUNE_ENDPOINT=http://localhost:8200
HITL_ENDPOINT=http://localhost:8000/api

# Kubernetes
KUBECONFIG=~/.kube/config

# HITL Redis
HITL_REDIS_URL=localhost:6379
HITL_REDIS_DB=0

# Debug
VCLI_DEBUG=true
VCLI_LOG_FILE=/tmp/vcli.log

# Offline
VCLI_OFFLINE_ENABLED=true
VCLI_CACHE_DIR=~/.vcli/cache
```

### 11.4 Arquivos de Configuração

```bash
# Main config
~/.vcli/config.yaml

# Shell history
~/.vcli/shell_history

# Cache
~/.vcli/cache/

# Offline queue
~/.vcli/cache/queue.db
```

### 11.5 Atalhos TUI

```bash
Tab                # Next workspace
Shift+Tab          # Previous workspace
1, 2, 3           # Go to workspace 1, 2, 3
r                 # Refresh
q                 # Quit
?                 # Help
↑↓                # Navigate
Enter             # Select/inspect
```

### 11.6 Exemplos de Seletores

```bash
# Kubernetes label selectors
-l app=nginx
-l app=nginx,env=production
-l 'tier in (frontend,backend)'
-l app,env!=dev

# MAXIMUS decision selectors
--selector status=pending
--selector priority=high,status=pending
--selector 'created_at > 2025-10-22'
```

### 11.7 Formatos de Output

```bash
# Table (default)
vcli maximus decision list

# JSON
vcli maximus decision list --format json

# JSON com jq
vcli maximus decision list --format json | jq '.[] | select(.priority == "high")'

# YAML
vcli k8s get pods --format yaml

# CSV
vcli maximus decision list --format csv > decisions.csv

# Template customizado
vcli maximus decision list \
  --format template \
  --template '{{range .}}{{.id}}: {{.status}}{{"\n"}}{{end}}'
```

### 11.8 Troubleshooting Rápido

```bash
# Serviço não responde
vcli troubleshoot <service> --verbose

# Verificar conectividade
curl http://localhost:8100/health

# Verificar configuração
vcli config show

# Limpar cache
vcli cache clear

# Limpar queue offline
vcli offline clear

# Logs debug
vcli --debug <command>

# Verificar versão
vcli version

# Help
vcli help
vcli help <command>
```

---

## Apêndice A: Glossário

| Termo | Descrição |
|-------|-----------|
| **MAXIMUS** | Sistema de governança e decisões HITL |
| **Immune Core** | Sistema de detecção de anomalias |
| **HITL** | Human-in-the-Loop - Decisões que requerem aprovação humana |
| **TUI** | Terminal User Interface - Interface gráfica no terminal |
| **Workspace** | Dashboard/painel do TUI (Governance, Performance, Investigation) |
| **Offline Mode** | Operação sem conectividade com backend |
| **Sync** | Sincronização de queue offline com backend |
| **Cache** | Armazenamento local de respostas para operação offline |
| **Queue** | Fila de operações pendentes (offline mode) |
| **Selector** | Filtro por labels/campos (ex: `app=nginx,env=prod`) |
| **Batch Operation** | Operação em múltiplos recursos simultaneamente |
| **Sparkline** | Gráfico de tendência em caracteres (▁▂▃▄▅▆▇█) |

## Apêndice B: Recursos Adicionais

### Documentação Online
- Docs oficiais: https://docs.vertice.dev/vcli
- GitHub: https://github.com/verticedev/vcli-go
- Issues: https://github.com/verticedev/vcli-go/issues

### Comunidade
- Discord: https://discord.gg/vertice
- Forum: https://forum.vertice.dev
- Stack Overflow: Tag `vcli`

### Contribuição
- Contribution Guide: CONTRIBUTING.md
- Code of Conduct: CODE_OF_CONDUCT.md
- Development Setup: DEVELOPMENT.md

---

**Fim do Curso Completo vCLI v2.0**

*Documento gerado em: 2025-10-22*
*Versão do documento: 1.0*
*Status: Production Ready*
*Conformidade: 100% Doutrina Vértice*
