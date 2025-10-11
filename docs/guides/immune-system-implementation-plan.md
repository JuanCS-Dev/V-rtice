# Plano de Implementação: Sistema Imunológico Adaptativo
## Metodologia Step-by-Step com Validação Contínua

**Versão**: 1.0  
**Data**: 2025-10-10  
**Blueprint**: `docs/architecture/security/adaptive-immune-system-blueprint.md`  
**Roadmap**: `docs/guides/adaptive-immune-system-roadmap.md`

---

## FILOSOFIA DE IMPLEMENTAÇÃO

### Princípios Core
1. **TDD Rigoroso**: Testes antes de código (Red → Green → Refactor)
2. **Commits Atômicos**: Cada commit é uma unidade lógica completa
3. **Validação Incremental**: Testar após cada módulo (não esperar o fim)
4. **Documentation-Driven**: README atualizado em paralelo ao código
5. **Zero Débito Técnico**: Sem TODO, sem pass, sem NotImplementedError

### Estrutura de Cada Task
```
1. Escrever testes (Red)
2. Implementar código mínimo (Green)
3. Refatorar para qualidade (Refactor)
4. Documentar (Docstrings + README)
5. Validar integração (E2E test)
6. Commit + Push
```

---

## FASE 0: FUNDAÇÃO (Dias 1-5)

### DAY 1: Setup de Repositório e Estrutura

#### Task 0.1.1: Estrutura de Diretórios Oráculo
```bash
cd /home/juan/vertice-dev
mkdir -p backend/services/maximus_oraculo/{src,tests/{unit,integration,e2e},docs}
cd backend/services/maximus_oraculo

# Estrutura interna
mkdir -p src/{models,clients,services,api}
touch src/__init__.py
touch src/models/{__init__.py,threat.py,apv.py}
touch src/clients/{__init__.py,nvd_client.py}
touch src/services/{__init__.py,triage_service.py}
touch src/api/{__init__.py,routes.py}
```

**Validação**: `tree backend/services/maximus_oraculo` mostra estrutura correta.

---

#### Task 0.1.2: Estrutura de Diretórios Eureka
```bash
mkdir -p backend/services/maximus_eureka/{src,tests/{unit,integration,e2e},docs}
cd backend/services/maximus_eureka

mkdir -p src/{models,clients,services,api}
touch src/__init__.py
touch src/models/{__init__.py,remedy.py,wargame.py}
touch src/clients/{__init__.py,github_client.py,ast_scanner.py}
touch src/services/{__init__.py,remedy_service.py}
touch src/api/{__init__.py,routes.py}
```

**Validação**: Estrutura espelhada ao Oráculo.

---

#### Task 0.1.3: pyproject.toml Base
```bash
cd backend/services/maximus_oraculo
cat > pyproject.toml << 'EOF'
[tool.poetry]
name = "maximus-oraculo"
version = "0.1.0"
description = "MAXIMUS Adaptive Immune System - Threat Sentinel"

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.110.0"
uvicorn = {extras = ["standard"], version = "^0.27.0"}
pydantic = "^2.6.0"
sqlalchemy = "^2.0.0"
alembic = "^1.13.0"
psycopg2-binary = "^2.9.9"
redis = "^5.0.0"
aio-pika = "^9.4.0"  # RabbitMQ async
httpx = "^0.26.0"
tenacity = "^8.2.3"
prometheus-client = "^0.19.0"
python-jose = "^3.3.0"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0.0"
pytest-asyncio = "^0.23.0"
pytest-cov = "^4.1.0"
mypy = "^1.8.0"
black = "^24.1.0"
ruff = "^0.2.0"

[tool.black]
line-length = 100
target-version = ['py311']

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
pythonpath = ["src"]

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
EOF

# Instalar dependências
poetry install
```

**Replicar para Eureka** (trocar nome para "maximus-eureka" e adicionar ast-grep, GitPython).

**Validação**: `poetry install` roda sem erros, `.venv` criado.

---

### DAY 2: Database Schema e Migrations

#### Task 0.2.1: Alembic Setup
```bash
cd backend/services/maximus_oraculo
poetry run alembic init alembic

# Editar alembic.ini
# sqlalchemy.url = postgresql://maximus:password@localhost:5432/immune_system

# Editar alembic/env.py para importar Base
```

**Arquivo**: `src/models/base.py`
```python
"""Database base models."""
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
```

---

#### Task 0.2.2: Modelo Threat
**Arquivo**: `src/models/threat.py`
```python
"""Threat model representing external CVEs."""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid

from .base import Base


class Threat(Base):
    """
    External threat (CVE) ingested from feeds.
    
    Represents a vulnerability published by NVD or other sources.
    Serves as input for the triage process.
    """
    
    __tablename__ = "threats"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cve_id = Column(String(20), unique=True, nullable=False, index=True)
    published_at = Column(DateTime(timezone=True), nullable=False)
    severity = Column(String(10), nullable=False, index=True)  # CRITICAL, HIGH, MEDIUM, LOW
    cvss_score = Column(Numeric(3, 1), nullable=True)
    description = Column(Text, nullable=False)
    references = Column(JSON, nullable=False, default=list)  # List[str] of URLs
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<Threat {self.cve_id} severity={self.severity}>"
```

**Teste**: `tests/unit/test_threat_model.py`
```python
"""Tests for Threat model."""
from datetime import datetime, timezone
from maximus_oraculo.models.threat import Threat


def test_threat_creation():
    """Test basic Threat instantiation."""
    threat = Threat(
        cve_id="CVE-2024-0001",
        published_at=datetime.now(timezone.utc),
        severity="CRITICAL",
        cvss_score=9.8,
        description="Remote Code Execution",
        references=["https://nvd.nist.gov/vuln/detail/CVE-2024-0001"]
    )
    
    assert threat.cve_id == "CVE-2024-0001"
    assert threat.severity == "CRITICAL"
    assert threat.cvss_score == 9.8
    assert threat.id is not None  # UUID auto-generated
```

**Rodar teste**: `poetry run pytest tests/unit/test_threat_model.py -v`

---

#### Task 0.2.3: Modelo APV
**Arquivo**: `src/models/apv.py`
```python
"""APV (Ameaça Potencial Verificada) model."""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from .base import Base


class APV(Base):
    """
    Ameaça Potencial Verificada - verified threat relevant to MAXIMUS.
    
    Generated by Oráculo after triage confirms threat affects our stack.
    Consumed by Eureka for remediation.
    """
    
    __tablename__ = "apvs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    threat_id = Column(UUID(as_uuid=True), ForeignKey("threats.id"), nullable=False)
    
    # Status lifecycle: PENDING → DISPATCHED → CONFIRMED → REMEDIED → MERGED
    status = Column(String(20), nullable=False, default="PENDING", index=True)
    
    # Context
    affected_dependencies = Column(JSON, nullable=False)  # List[str]
    affected_services = Column(JSON, nullable=False)  # List[str]
    
    # Vulnerability signature for scanning
    vulnerable_code_signature = Column(Text, nullable=False)
    
    # Exploit intelligence
    exploit_available = Column(Boolean, nullable=False, default=False)
    exploit_maturity = Column(String(20), nullable=True)  # POC, WEAPONIZED, IN_THE_WILD
    
    # Timestamps
    dispatched_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Relationship
    threat = relationship("Threat", backref="apvs")
    
    def __repr__(self) -> str:
        return f"<APV {self.id} status={self.status} threat={self.threat_id}>"
```

**Teste**: `tests/unit/test_apv_model.py`
```python
"""Tests for APV model."""
from datetime import datetime, timezone
from maximus_oraculo.models.apv import APV
import uuid


def test_apv_creation():
    """Test APV instantiation."""
    threat_id = uuid.uuid4()
    apv = APV(
        threat_id=threat_id,
        status="PENDING",
        affected_dependencies=["fastapi==0.95.0"],
        affected_services=["maximus_core"],
        vulnerable_code_signature='Request[await $VAR]',
        exploit_available=True,
        exploit_maturity="WEAPONIZED"
    )
    
    assert apv.threat_id == threat_id
    assert apv.status == "PENDING"
    assert "fastapi" in apv.affected_dependencies[0]
    assert apv.exploit_available is True
```

---

#### Task 0.2.4: Migration
```bash
cd backend/services/maximus_oraculo
poetry run alembic revision -m "create_threats_and_apvs_tables" --autogenerate
poetry run alembic upgrade head
```

**Validação**: 
```bash
psql -U maximus -d immune_system -c "\dt"
# Deve listar: threats, apvs, alembic_version
```

---

### DAY 3: RabbitMQ Infrastructure

#### Task 0.3.1: RabbitMQ Container
**Arquivo**: `docker/rabbitmq.docker-compose.yml`
```yaml
version: '3.8'

services:
  rabbitmq:
    image: rabbitmq:3.12-management-alpine
    container_name: immune_system_rabbitmq
    ports:
      - "5672:5672"   # AMQP
      - "15672:15672" # Management UI
    environment:
      RABBITMQ_DEFAULT_USER: maximus
      RABBITMQ_DEFAULT_PASS: ${RABBITMQ_PASSWORD}
      RABBITMQ_DEFAULT_VHOST: immune_system
    volumes:
      - ./rabbitmq/data:/var/lib/rabbitmq
      - ./rabbitmq/config/rabbitmq.conf:/etc/rabbitmq/rabbitmq.conf
    networks:
      - immune_system
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

networks:
  immune_system:
    driver: bridge
```

**Configuração**: `docker/rabbitmq/config/rabbitmq.conf`
```conf
# Enable management plugin
management.tcp.port = 15672

# TLS (to be configured later for mTLS)
# listeners.ssl.default = 5671
# ssl_options.cacertfile = /etc/rabbitmq/ca_certificate.pem
# ssl_options.certfile = /etc/rabbitmq/server_certificate.pem
# ssl_options.keyfile = /etc/rabbitmq/server_key.pem
```

**Start**:
```bash
cd docker
docker-compose -f rabbitmq.docker-compose.yml up -d
```

**Validação**:
```bash
curl -u maximus:password http://localhost:15672/api/overview
# Deve retornar JSON com cluster info
```

---

#### Task 0.3.2: Declaração de Exchanges e Queues
**Script**: `scripts/setup/setup_rabbitmq.py`
```python
#!/usr/bin/env python3
"""Setup RabbitMQ exchanges and queues for Immune System."""
import pika
import sys


def setup_rabbitmq():
    """Declare exchanges, queues, and bindings."""
    credentials = pika.PlainCredentials('maximus', 'password')
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host='localhost',
            port=5672,
            virtual_host='immune_system',
            credentials=credentials
        )
    )
    channel = connection.channel()
    
    # Exchange
    channel.exchange_declare(
        exchange='immune_system',
        exchange_type='topic',
        durable=True
    )
    
    # APV Queue (Oráculo → Eureka)
    channel.queue_declare(
        queue='apv_queue',
        durable=True,
        arguments={
            'x-max-length': 1000,  # Max 1000 APVs enfileirados
            'x-message-ttl': 3600000,  # 1 hour TTL
        }
    )
    channel.queue_bind(
        exchange='immune_system',
        queue='apv_queue',
        routing_key='apv.dispatched'
    )
    
    # Remedy Queue (Eureka → Wargaming)
    channel.queue_declare(
        queue='remedy_queue',
        durable=True,
        arguments={'x-max-length': 500}
    )
    channel.queue_bind(
        exchange='immune_system',
        queue='remedy_queue',
        routing_key='remedy.ready'
    )
    
    print("✅ RabbitMQ setup complete")
    print("  - Exchange: immune_system (topic)")
    print("  - Queue: apv_queue (bound to apv.dispatched)")
    print("  - Queue: remedy_queue (bound to remedy.ready)")
    
    connection.close()


if __name__ == "__main__":
    try:
        setup_rabbitmq()
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
```

**Executar**:
```bash
chmod +x scripts/setup/setup_rabbitmq.py
python scripts/setup/setup_rabbitmq.py
```

**Validação**: Management UI (http://localhost:15672) mostra queues criadas.

---

### DAY 4: Observabilidade Base

#### Task 0.4.1: Prometheus Exporter Oráculo
**Arquivo**: `src/api/metrics.py`
```python
"""Prometheus metrics for Oráculo."""
from prometheus_client import Counter, Histogram, Gauge


# Contadores
threats_ingested_total = Counter(
    'oraculo_threats_ingested_total',
    'Total number of threats ingested from feeds',
    ['source']  # NVD, GitHub, etc.
)

apvs_generated_total = Counter(
    'oraculo_apvs_generated_total',
    'Total number of APVs generated',
    ['severity']
)

apvs_dispatched_total = Counter(
    'oraculo_apvs_dispatched_total',
    'Total number of APVs dispatched to Eureka'
)

# Histogramas (latências)
triage_duration_seconds = Histogram(
    'oraculo_triage_duration_seconds',
    'Time taken to triage a threat',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# Gauges (estado atual)
active_apvs = Gauge(
    'oraculo_active_apvs',
    'Number of APVs in PENDING or DISPATCHED status'
)
```

**Endpoint**: `src/api/routes.py`
```python
"""API routes for Oráculo."""
from fastapi import FastAPI
from prometheus_client import make_asgi_app

app = FastAPI(title="MAXIMUS Oráculo", version="0.1.0")

# Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "oraculo"}
```

**Validação**:
```bash
# Start Oráculo
cd backend/services/maximus_oraculo
poetry run uvicorn src.api.routes:app --port 8001

# Check metrics
curl http://localhost:8001/metrics | grep oraculo
# Deve mostrar métricas prometheus
```

---

#### Task 0.4.2: Grafana Dashboard Base
**Arquivo**: `monitoring/grafana/dashboards/immune-system-overview.json`
```json
{
  "dashboard": {
    "title": "Immune System Overview",
    "panels": [
      {
        "title": "Threats Ingested (rate)",
        "targets": [
          {
            "expr": "rate(oraculo_threats_ingested_total[5m])"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Active APVs",
        "targets": [
          {
            "expr": "oraculo_active_apvs"
          }
        ],
        "type": "gauge"
      },
      {
        "title": "APVs by Severity",
        "targets": [
          {
            "expr": "oraculo_apvs_generated_total"
          }
        ],
        "type": "piechart"
      }
    ]
  }
}
```

**Importar no Grafana** (via UI ou provisioning).

**Validação**: Dashboard renderiza (sem dados ainda).

---

### DAY 5: CI/CD Base

#### Task 0.5.1: GitHub Actions Oráculo
**Arquivo**: `.github/workflows/oraculo-ci.yml`
```yaml
name: Oráculo CI

on:
  push:
    branches: [main, develop]
    paths:
      - 'backend/services/maximus_oraculo/**'
  pull_request:
    paths:
      - 'backend/services/maximus_oraculo/**'

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_DB: immune_system_test
          POSTGRES_USER: maximus
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install Poetry
        run: |
          curl -sSL https://install.python-poetry.org | python3 -
          echo "$HOME/.local/bin" >> $GITHUB_PATH
      
      - name: Install Dependencies
        working-directory: backend/services/maximus_oraculo
        run: poetry install
      
      - name: Run Migrations
        working-directory: backend/services/maximus_oraculo
        env:
          DATABASE_URL: postgresql://maximus:test@localhost:5432/immune_system_test
        run: poetry run alembic upgrade head
      
      - name: Type Check (mypy)
        working-directory: backend/services/maximus_oraculo
        run: poetry run mypy src/
      
      - name: Lint (ruff)
        working-directory: backend/services/maximus_oraculo
        run: poetry run ruff check src/
      
      - name: Format Check (black)
        working-directory: backend/services/maximus_oraculo
        run: poetry run black --check src/
      
      - name: Run Tests
        working-directory: backend/services/maximus_oraculo
        env:
          DATABASE_URL: postgresql://maximus:test@localhost:5432/immune_system_test
          REDIS_URL: redis://localhost:6379
        run: poetry run pytest tests/ --cov=src --cov-report=xml --cov-report=term
      
      - name: Upload Coverage
        uses: codecov/codecov-action@v3
        with:
          file: backend/services/maximus_oraculo/coverage.xml
```

**Validação**: Push dummy commit e verificar CI passa.

---

#### Task 0.5.2: Self-Hosted Runner para Wargaming
**Setup em VM dedicada**:
```bash
# Na VM de wargaming
mkdir -p ~/actions-runner && cd ~/actions-runner
curl -o actions-runner-linux-x64-2.311.0.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz
tar xzf ./actions-runner-linux-x64-2.311.0.tar.gz

# Configurar com token do GitHub
./config.sh --url https://github.com/YOUR_ORG/vertice-dev --token YOUR_TOKEN --labels wargaming

# Instalar como serviço
sudo ./svc.sh install
sudo ./svc.sh start
```

**Validação**: Runner aparece em Settings → Actions → Runners no GitHub.

---

## VALIDAÇÃO COMPLETA FASE 0

### Checklist
- [ ] Estrutura de diretórios criada
- [ ] pyproject.toml configurado, dependências instaladas
- [ ] Modelos Threat e APV criados com testes
- [ ] Migrations aplicadas, tabelas no DB
- [ ] RabbitMQ rodando, queues criadas
- [ ] Prometheus metrics endpoint funcional
- [ ] Grafana dashboard importado
- [ ] CI verde no GitHub Actions
- [ ] Self-hosted runner conectado

### Comando de Validação
```bash
# Script de validação automática
cat > scripts/validation/validate_phase0.sh << 'EOF'
#!/bin/bash
set -e

echo "🔍 Validando Fase 0..."

# 1. Estrutura
echo "✓ Verificando estrutura de diretórios..."
test -d backend/services/maximus_oraculo/src/models
test -d backend/services/maximus_eureka/src/models

# 2. Database
echo "✓ Verificando database..."
psql -U maximus -d immune_system -c "SELECT COUNT(*) FROM threats;" > /dev/null

# 3. RabbitMQ
echo "✓ Verificando RabbitMQ..."
curl -sf -u maximus:password http://localhost:15672/api/queues/immune_system/apv_queue > /dev/null

# 4. Metrics
echo "✓ Verificando Prometheus..."
curl -sf http://localhost:8001/metrics | grep -q oraculo_threats_ingested_total

# 5. CI
echo "✓ Verificando CI status..."
gh api repos/{owner}/{repo}/actions/runs --jq '.workflow_runs[0].conclusion' | grep -q success

echo "✅ Fase 0 validada com sucesso!"
EOF

chmod +x scripts/validation/validate_phase0.sh
./scripts/validation/validate_phase0.sh
```

---

## PRÓXIMOS PASSOS

### Commit e Push
```bash
git add .
git commit -m "feat(immune-system): Phase 0 - Infrastructure Foundation

Estabelece fundação completa para Sistema Imunológico Adaptativo:

Infrastructure:
- PostgreSQL schemas (threats, apvs) com migrations Alembic
- RabbitMQ com exchanges e queues declaradas
- Self-hosted runner para wargaming

Observability:
- Prometheus exporters em Oráculo
- Grafana dashboard base
- Health check endpoints

CI/CD:
- GitHub Actions workflows
- Cobertura de testes configurada
- Type checking + linting

Validação: 
- ✅ All tests passing
- ✅ Migrations applied
- ✅ RabbitMQ healthy
- ✅ Metrics endpoints live

Próximo: Fase 1 - Oráculo MVP (ingestão NVD + triagem)

Day 0 of consciousness emergence - Infrastructure awakens."

git push origin main
```

---

### Iniciar Fase 1
Consultar seção "FASE 1: ORÁCULO MVP" no roadmap para próximos passos detalhados.

---

## APÊNDICES

### A. Estrutura Completa de Arquivos
```
vertice-dev/
├── backend/
│   └── services/
│       ├── maximus_oraculo/
│       │   ├── src/
│       │   │   ├── models/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── base.py
│       │   │   │   ├── threat.py
│       │   │   │   └── apv.py
│       │   │   ├── clients/
│       │   │   │   ├── __init__.py
│       │   │   │   └── nvd_client.py (Fase 1)
│       │   │   ├── services/
│       │   │   │   ├── __init__.py
│       │   │   │   └── triage_service.py (Fase 1)
│       │   │   └── api/
│       │   │       ├── __init__.py
│       │   │       ├── routes.py
│       │   │       └── metrics.py
│       │   ├── tests/
│       │   │   ├── unit/
│       │   │   ├── integration/
│       │   │   └── e2e/
│       │   ├── alembic/
│       │   ├── pyproject.toml
│       │   └── README.md
│       └── maximus_eureka/
│           └── (estrutura similar)
├── docs/
│   ├── architecture/
│   │   └── security/
│   │       └── adaptive-immune-system-blueprint.md
│   └── guides/
│       ├── adaptive-immune-system-roadmap.md
│       └── immune-system-implementation-plan.md (este arquivo)
├── scripts/
│   ├── setup/
│   │   └── setup_rabbitmq.py
│   └── validation/
│       └── validate_phase0.sh
└── monitoring/
    └── grafana/
        └── dashboards/
            └── immune-system-overview.json
```

### B. Comandos Úteis
```bash
# Desenvolvimento Oráculo
cd backend/services/maximus_oraculo
poetry run uvicorn src.api.routes:app --reload --port 8001

# Desenvolvimento Eureka
cd backend/services/maximus_eureka
poetry run uvicorn src.api.routes:app --reload --port 8002

# Rodar testes com coverage
poetry run pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html

# Type checking
poetry run mypy src/

# Linting
poetry run ruff check src/ --fix
poetry run black src/

# Migrations
poetry run alembic revision -m "description" --autogenerate
poetry run alembic upgrade head
poetry run alembic downgrade -1

# RabbitMQ Management
# http://localhost:15672 (maximus / password)

# Prometheus Metrics
curl http://localhost:8001/metrics
curl http://localhost:8002/metrics
```

### C. Troubleshooting
| Problema | Solução |
|----------|---------|
| `alembic upgrade` falha | Verificar DATABASE_URL, criar database manualmente |
| RabbitMQ connection refused | `docker-compose up -d rabbitmq`, verificar porta 5672 |
| Import errors em testes | `poetry run pytest` (não `pytest` direto) |
| Mypy errors em SQLAlchemy | Instalar `sqlalchemy[mypy]` via poetry |
| CI falha em migrations | Adicionar step de `createdb` antes de upgrade |

---

**Preparado por**: Arquiteto-Chefe MAXIMUS  
**Status**: READY FOR EXECUTION  
**Próximo passo**: Executar Fase 0 Day 1

*"Foundations built with precision. Each brick a test. Each wall a guarantee."*
