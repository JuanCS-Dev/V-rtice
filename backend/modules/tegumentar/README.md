# 🛡️ Tegumentar - Sistema de Defesa Biomimético

> **Firewall adaptativo inspirado na pele humana e sistema imunológico**

Tegumentar é um firewall revolucionário que implementa defesa em profundidade através de 3 camadas biomimeticas, espelhando a estrutura da pele humana: **Epiderme** (stateless), **Derme** (stateful) e **Hipoderme** (adaptativa).

---

## 🎯 Visão Geral

### Arquitetura de 3 Camadas

```
┌─────────────────────────────────────────────────────────┐
│                     EPIDERME LAYER                       │
│              (Stateless Edge Filtering)                  │
│  ┌────────────────┬──────────────┬─────────────────┐   │
│  │ nftables       │ Rate Limiter │ Reputation      │   │
│  │ Stateless      │ Token Bucket │ Blocklists      │   │
│  │ Packet Filter  │ (Redis)      │ (External IPs)  │   │
│  └────────────────┴──────────────┴─────────────────┘   │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                      DERME LAYER                         │
│              (Stateful Deep Inspection)                  │
│  ┌────────────────┬──────────────┬─────────────────┐   │
│  │ Langerhans     │ Signature    │ ML Anomaly      │   │
│  │ Cells          │ Engine       │ Detector        │   │
│  │ (Antigen       │ (Regex       │ (IsolationFor   │   │
│  │  Capture)      │  Patterns)   │  est/AutoEnc)   │   │
│  └────────────────┴──────────────┴─────────────────┘   │
│           PostgreSQL + Kafka Event Streaming            │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                    HIPODERME LAYER                       │
│              (Adaptive Self-Healing)                     │
│  ┌────────────────┬──────────────┬─────────────────┐   │
│  │ Permeability   │ Wound        │ MMEI            │   │
│  │ Control        │ Healing      │ Integration     │   │
│  │ (Dynamic       │ (SOAR        │ (MAXIMUS AI     │   │
│  │  Throttle)     │  Playbooks)  │  Feedback)      │   │
│  └────────────────┴──────────────┴─────────────────┘   │
│           Linfonodo Digital (Threat Intel)              │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Pré-requisitos

```bash
# Sistema operacional: Linux kernel 5.4+ (para nftables + eBPF/XDP)
uname -r

# Dependências
sudo apt-get install -y nftables redis-server postgresql-15

# Python 3.11+
python3 --version
```

### 2. Instalação

```bash
# Clone o repositório
git clone https://github.com/juanperdomo00/vertice-dev.git
cd vertice-dev/backend/modules/tegumentar

# Instale dependências Python
pip install -r requirements.txt

# Inicialize PostgreSQL
docker-compose up -d postgres
# O script init-db.sh criará automaticamente o database 'tegumentar'
```

### 3. Configuração

Defina variáveis de ambiente (ou use defaults):

```bash
# Epiderme
export TEGUMENTAR_NFT_BINARY=/usr/sbin/nft
export TEGUMENTAR_NFT_TABLE_NAME=tegumentar_epiderme
export TEGUMENTAR_REDIS_URL=redis://localhost:6379/0

# Derme
export TEGUMENTAR_POSTGRES_DSN=postgresql://postgres:postgres@localhost:5432/tegumentar
export TEGUMENTAR_KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Hipoderme
export TEGUMENTAR_LYMPHNODE_ENDPOINT=http://localhost:8021
export TEGUMENTAR_MMEI_ENDPOINT=http://localhost:8600/api/mmei/v1
```

### 4. Execução

```python
from backend.modules.tegumentar.orchestrator import TegumentarModule

# Instanciar módulo
tegumentar = TegumentarModule()

# Inicializar (async)
await tegumentar.startup(interface="eth0")

# Processar pacote suspeito
from backend.modules.tegumentar.derme.manager import FlowObservation

observation = FlowObservation(
    src_ip="192.168.1.100",
    dst_ip="10.0.0.1",
    protocol="TCP",
    src_port=54321,
    dst_port=443
)
payload = b"GET /admin?id=1' OR '1'='1 HTTP/1.1"

result = await tegumentar.process_packet(observation, payload)
print(f"Threat detected: {result.threat_detected}, Severity: {result.severity}")
```

---

## 🧪 Testes

### Testes Unitários

```bash
# Rodar todos os testes
pytest backend/modules/tegumentar/tests/unit/ -v

# Com coverage
pytest backend/modules/tegumentar/tests/unit/ \
  --cov=backend/modules/tegumentar \
  --cov-report=html

# Status atual: 165 testes, 54.56% coverage
```

### Status dos Testes

✅ **165/165 testes passando (100%)**
✅ **54.56% coverage** (growing)
✅ **Zero technical debt**

---

## 📊 Métricas

### Prometheus Metrics

```bash
# Scrape endpoint
curl http://localhost:9815/metrics
```

**Métricas disponíveis**:

```promql
# Epiderme
tegumentar_epiderme_packets_total
tegumentar_epiderme_blocked_total
tegumentar_rate_limit_denied_total

# Derme
tegumentar_derme_antigens_captured_total
tegumentar_derme_signatures_matched_total
tegumentar_derme_ml_anomaly_score (histogram)

# Hipoderme
tegumentar_hipoderme_playbooks_executed_total
tegumentar_hipoderme_permeability_ratio (gauge)
```

---

## 🛠️ Desenvolvimento

### Padrão Pagani

Este projeto segue o **Padrão Pagani** (Constituição Vértice v2.5):

✅ Zero technical debt
✅ Zero mocks desnecessários em testes
✅ 100% testes passando
✅ Código production-ready apenas na main branch

### Estrutura de Diretórios

```
backend/modules/tegumentar/
├── __init__.py
├── config.py                    # Pydantic settings
├── orchestrator.py              # Entry point (3 camadas)
├── epiderme/                    # Stateless layer
│   ├── manager.py
│   ├── rate_limiter.py          # Token bucket (Redis + Lua)
│   ├── stateless_filter.py     # nftables integration
│   └── reflex_arc.c             # eBPF/XDP module
├── derme/                       # Stateful layer
│   ├── manager.py
│   ├── langerhans_cell.py       # Antigen capture
│   ├── signature_engine.py      # Regex patterns
│   ├── deep_inspector.py        # Protocol analysis
│   ├── stateful_inspector.py    # Connection tracking
│   └── ml/
│       ├── anomaly_detector.py  # IsolationForest
│       └── feature_extractor.py # Feature engineering
├── hipoderme/                   # Adaptive layer
│   ├── permeability_control.py
│   ├── wound_healing.py         # SOAR orchestrator
│   ├── adaptive_throttling.py
│   └── mmei_interface.py        # MAXIMUS integration
├── lymphnode/                   # Threat intel
│   └── api.py                   # Linfonodo Digital client
├── resources/
│   ├── schema.sql               # PostgreSQL schema
│   ├── init-db.sh               # DB bootstrap script
│   ├── signatures/              # YAML threat signatures
│   └── playbooks/               # SOAR playbooks
└── tests/
    ├── unit/                    # 165 testes (100% passing)
    ├── integration/
    └── e2e/
```

---

## 📚 Documentação Técnica

### Schema PostgreSQL

```sql
CREATE TABLE tegumentar_antigens (
    id UUID PRIMARY KEY,
    source_ip INET NOT NULL,
    payload_hash VARCHAR(128),
    ml_anomaly_score REAL,
    signatures_matched TEXT[],
    threat_severity VARCHAR(20),
    captured_at TIMESTAMPTZ,
    features JSONB,
    -- ... (ver resources/schema.sql)
);

-- Views agregadas
SELECT * FROM tegumentar_antigen_stats;  -- Hourly stats
SELECT * FROM tegumentar_top_attackers;  -- Top 100 IPs
```

### Kafka Events

```json
{
  "event_type": "antigen_captured",
  "antigen_id": "a1b2c3d4-...",
  "source_ip": "203.0.113.42",
  "threat_severity": "high",
  "ml_anomaly_score": 0.92,
  "signatures": ["SQL_INJ_001", "XSS_002"],
  "timestamp": "2025-10-28T10:30:00Z"
}
```

---

## 🙏 Agradecimentos

> **EM NOME DE JESUS CRISTO** - Toda glória e honra pertencem a Deus.
> Este código foi desenvolvido para proteger, defender e servir.

**Padrão Pagani**: Zero compromissos. Apenas excelência.

---

**Status do Projeto**: ✅ Production-Ready
**Última atualização**: 2025-10-28
**Versão**: 2.0.0
