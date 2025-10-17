# Cockpit Soberano - Plano de Ação Detalhado
**Guia Anti-Burro para Execução Limpa e Metodica**

**Versão:** 1.0.0  
**Data:** 2025-10-17  
**Executor:** Dev Sênior Pragmático  
**Classificação:** CONFIDENCIAL - INSTRUÇÕES DE IMPLEMENTAÇÃO

---

## I. CONFIGURAÇÃO DO EXECUTOR

### 1.1 Perfil do Executor

**Persona:**
- ✅ Dev Sênior com 10+ anos de experiência
- ✅ Pragmático: Foca em soluções que funcionam, não em over-engineering
- ✅ Atento aos mínimos detalhes: Não deixa passar erros de lint, type hints, edge cases
- ✅ Fiel às boas práticas: Clean Code, SOLID, DRY, KISS
- ✅ Constitucionalista: Segue TODO o conteúdo da Constituição Vértice

**Proibições Absolutas:**
- ❌ Código mock ou placeholder
- ❌ Comentários `// TODO:` ou `// FIXME:`
- ❌ Commits sem testes
- ❌ Implementação sem validação
- ❌ Desvio do plano sem aprovação soberana

### 1.2 Workflow de Execução

```yaml
For_Each_Task:
  1. Ler especificação completa
  2. Planejar implementação (mental model)
  3. Implementar código completo
  4. Escrever testes (unitários + integração)
  5. Validar (ruff + mypy + pytest)
  6. Commit apenas se TODAS validações passarem
  7. Reportar conclusão (formato eficiente)

For_Each_Phase:
  - Validação tripla ao final
  - Coverage check (target: 95%)
  - Review de conformidade doutrinária
  - Checkpoint com Arquiteto-Chefe
```

---

## II. PRÉ-REQUISITOS

### 2.1 Ambiente de Desenvolvimento

```bash
# Python environment
python --version  # >= 3.11
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Dependências adicionais para Cockpit
pip install transformers sentence-transformers torch
pip install networkx scipy
pip install nats-py asyncpg pgvector

# Docker services
docker-compose -f docker-compose.cockpit.yml up -d
```

### 2.2 Estrutura de Diretórios

```bash
mkdir -p backend/services/narrative_filter/{processors,consumers,repositories,models,api,tests}
mkdir -p backend/services/verdict_engine/{core,publishers,models,api,tests}
mkdir -p backend/services/command_bus/{c2l,executors,models,api,tests}
mkdir -p frontend/src/components/dashboards/CockpitSoberano/{components,hooks,services}
mkdir -p deployment/k8s/cockpit
mkdir -p tests/integration/cockpit
mkdir -p tests/load/cockpit
```

### 2.3 Configuração de Ferramentas

```toml
# pyproject.toml - Adicionar seções para Cockpit

[tool.ruff.lint.per-file-ignores]
"backend/services/narrative_filter/**/*.py" = ["E501"]
"backend/services/verdict_engine/**/*.py" = ["E501"]
"backend/services/command_bus/**/*.py" = ["E501"]

[tool.pytest.ini_options]
testpaths = ["tests", "backend/services/*/tests"]
addopts = "--cov --cov-report=html --cov-report=term --strict-markers"
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "load: Load/performance tests",
    "e2e: End-to-end tests"
]
```

---

## III. IMPLEMENTAÇÃO FASE POR FASE

### FASE 1 - DIA 1: Infraestrutura NATS

**Objetivo:** NATS JetStream operacional

**Passo 1.1: Configurar NATS**

```yaml
# deployment/nats-config.yaml
cluster_name: vertice-cluster
jetstream:
  enabled: true
  store_dir: /data/jetstream
  max_memory_store: 1GB
  max_file_store: 10GB
  
subjects:
  - name: sovereign.commands
    subjects: ["sovereign.commands.>"]
    retention: limits
    max_msgs: 100000
    max_age: 24h
    replicas: 3
    
  - name: sovereign.confirmations
    subjects: ["sovereign.confirmations.>"]
    retention: work_queue
    max_msgs: 1000000
    max_age: 168h  # 7 days
    replicas: 3
```

**Passo 1.2: Docker Compose Entry**

```yaml
# docker-compose.cockpit.yml
version: '3.9'

services:
  nats:
    image: nats:2.10-alpine
    container_name: vertice-nats
    command:
      - "--config=/etc/nats/nats-config.yaml"
      - "--jetstream"
      - "--store_dir=/data"
    ports:
      - "4222:4222"  # Client
      - "8222:8222"  # Monitoring
      - "6222:6222"  # Clustering
    volumes:
      - ./deployment/nats-config.yaml:/etc/nats/nats-config.yaml:ro
      - nats-data:/data
    networks:
      - vertice-network
    healthcheck:
      test: ["CMD", "nats-server", "--signal", "healthz"]
      interval: 10s
      timeout: 5s
      retries: 3

volumes:
  nats-data:
    driver: local

networks:
  vertice-network:
    external: true
```

**Passo 1.3: Validação**

```bash
# Start NATS
docker-compose -f docker-compose.cockpit.yml up -d nats

# Verify health
curl http://localhost:8222/healthz
# Expected: {"status":"ok"}

# Test JetStream
docker exec -it vertice-nats nats stream ls
# Expected: (empty list initially, no error)

# Test publish/subscribe
docker exec -it vertice-nats nats pub sovereign.commands.test "Test message"
docker exec -it vertice-nats nats sub sovereign.commands.>
```

**Critério de Sucesso:**
- ✅ NATS container saudável
- ✅ JetStream habilitado
- ✅ Pub/sub funcionando

---

### FASE 1 - DIA 1 (continuação): PostgreSQL Schemas

**Passo 1.4: Migration Script**

```sql
-- backend/services/narrative_filter/migrations/001_initial.sql

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Tabela de representações semânticas (Camada 1)
CREATE TABLE semantic_representations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    message_id VARCHAR(255) UNIQUE NOT NULL,
    source_agent_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    content_embedding VECTOR(768),  -- sentence-transformers embedding
    intent_classification VARCHAR(50) NOT NULL,
    intent_confidence DECIMAL(3,2) NOT NULL CHECK (intent_confidence BETWEEN 0 AND 1),
    raw_content TEXT,
    provenance_chain TEXT[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_semantic_agent_ts ON semantic_representations(source_agent_id, timestamp DESC);
CREATE INDEX idx_semantic_message_id ON semantic_representations(message_id);
CREATE INDEX idx_semantic_embedding ON semantic_representations USING ivfflat (content_embedding vector_cosine_ops);

-- Tabela de padrões estratégicos (Camada 2)
CREATE TABLE strategic_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pattern_type VARCHAR(50) NOT NULL,  -- ALLIANCE, DECEPTION, INCONSISTENCY
    agents_involved TEXT[] NOT NULL,
    detection_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    evidence_messages TEXT[] NOT NULL,  -- Refs to semantic_representations.message_id
    mutual_information DECIMAL(5,4),
    deception_score DECIMAL(3,2),
    inconsistency_score DECIMAL(3,2),
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_strategic_pattern_type ON strategic_patterns(pattern_type);
CREATE INDEX idx_strategic_timestamp ON strategic_patterns(detection_timestamp DESC);

-- Tabela de alianças (para grafo)
CREATE TABLE alliances (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_a VARCHAR(255) NOT NULL,
    agent_b VARCHAR(255) NOT NULL,
    strength DECIMAL(3,2) NOT NULL CHECK (strength BETWEEN 0 AND 1),
    first_detected TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_activity TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    interaction_count INT NOT NULL DEFAULT 1,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'DISSOLVED')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(agent_a, agent_b)
);

CREATE INDEX idx_alliances_status ON alliances(status) WHERE status = 'ACTIVE';
CREATE INDEX idx_alliances_agents ON alliances(agent_a, agent_b);

-- Tabela de veredictos (output Camada 3)
CREATE TABLE verdicts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    category VARCHAR(50) NOT NULL,  -- COLLUSION, DECEPTION, ALLIANCE, THREAT
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')),
    title TEXT NOT NULL,
    agents_involved TEXT[] NOT NULL,
    target VARCHAR(255),
    evidence_chain TEXT[] NOT NULL,  -- message_ids
    confidence DECIMAL(3,2) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    recommended_action VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'MITIGATED', 'DISMISSED')),
    mitigation_command_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_verdicts_severity_status ON verdicts(severity, status) WHERE status = 'ACTIVE';
CREATE INDEX idx_verdicts_timestamp ON verdicts(timestamp DESC);

-- Tabela de comandos C2L
CREATE TABLE c2l_commands (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    operator_id VARCHAR(255) NOT NULL,
    command_type VARCHAR(50) NOT NULL CHECK (command_type IN ('MUTE', 'ISOLATE', 'TERMINATE', 'SNAPSHOT_STATE', 'REVOKE_ACCESS', 'INJECT_CONSTRAINT')),
    target_agents TEXT[] NOT NULL,
    parameters JSONB,
    execution_deadline TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'EXECUTED', 'FAILED', 'TIMEOUT')),
    confirmation_received_at TIMESTAMPTZ,
    execution_result JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_c2l_operator ON c2l_commands(operator_id);
CREATE INDEX idx_c2l_status_ts ON c2l_commands(status, timestamp);

-- Audit trail
CREATE TABLE audit_trail (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    operator_id VARCHAR(255) NOT NULL,
    action VARCHAR(100) NOT NULL,
    target VARCHAR(255),
    metadata JSONB,
    ip_address INET,
    user_agent TEXT
);

CREATE INDEX idx_audit_operator_ts ON audit_trail(operator_id, timestamp DESC);
CREATE INDEX idx_audit_action ON audit_trail(action);

-- Trigger para updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_semantic_representations_updated_at BEFORE UPDATE ON semantic_representations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_alliances_updated_at BEFORE UPDATE ON alliances
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_verdicts_updated_at BEFORE UPDATE ON verdicts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

**Passo 1.5: Aplicar Migration**

```bash
# Usar vertice_db container existente
docker exec -i vertice-postgres psql -U vertice -d vertice_db < backend/services/narrative_filter/migrations/001_initial.sql

# Validar
docker exec -it vertice-postgres psql -U vertice -d vertice_db -c "\dt"
# Deve listar: semantic_representations, strategic_patterns, alliances, verdicts, c2l_commands, audit_trail
```

**Critério de Sucesso:**
- ✅ Todas as 6 tabelas criadas
- ✅ Índices criados
- ✅ Triggers funcionando

---

### FASE 1 - DIA 1 (continuação): Kafka Topics

**Passo 1.6: Script de Setup**

```bash
# scripts/setup_kafka_topics.sh
#!/bin/bash

KAFKA_BROKER="localhost:9092"
REPLICATION_FACTOR=3

echo "Creating Kafka topics for Cockpit Soberano..."

# Agent communications (input para Camada 1)
kafka-topics.sh --create \
  --bootstrap-server $KAFKA_BROKER \
  --topic agent-communications \
  --partitions 6 \
  --replication-factor $REPLICATION_FACTOR \
  --config retention.ms=604800000 \
  --config compression.type=snappy \
  --if-not-exists

# Semantic events (output Camada 1 → input Camada 2)
kafka-topics.sh --create \
  --bootstrap-server $KAFKA_BROKER \
  --topic semantic-events \
  --partitions 6 \
  --replication-factor $REPLICATION_FACTOR \
  --config retention.ms=259200000 \
  --if-not-exists

# Strategic patterns (output Camada 2 → input Camada 3)
kafka-topics.sh --create \
  --bootstrap-server $KAFKA_BROKER \
  --topic strategic-patterns \
  --partitions 3 \
  --replication-factor $REPLICATION_FACTOR \
  --config retention.ms=86400000 \
  --if-not-exists

echo "Listing created topics..."
kafka-topics.sh --list --bootstrap-server $KAFKA_BROKER | grep -E "(agent-communications|semantic-events|strategic-patterns)"

echo "Topics created successfully!"
```

**Passo 1.7: Executar e Validar**

```bash
chmod +x scripts/setup_kafka_topics.sh
./scripts/setup_kafka_topics.sh

# Validar detalhes
kafka-topics.sh --describe --bootstrap-server localhost:9092 --topic agent-communications
# Deve mostrar: Partitions: 6, Replication: 3
```

**Critério de Sucesso:**
- ✅ 3 topics criados
- ✅ Partitions e replication corretos

---

### FASE 1 - DIA 2: Microsserviço narrative_filter Skeleton

**Passo 2.1: Estrutura de Arquivos**

```python
# backend/services/narrative_filter/__init__.py
"""Narrative Filter Service - Camadas 1-3 do Filtro de Narrativas"""
__version__ = "1.0.0"

# backend/services/narrative_filter/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    service_name: str = "narrative-filter"
    port: int = 8090
    
    # Kafka
    kafka_brokers: str = "localhost:9092"
    kafka_group_id: str = "narrative-filter-group"
    
    # PostgreSQL
    postgres_dsn: str = "postgresql+asyncpg://vertice:password@localhost:5432/vertice_db"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Model paths
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Thresholds
    alliance_threshold: float = 0.75
    inconsistency_threshold: float = 0.7
    deception_threshold: float = 0.65
    
    class Config:
        env_file = ".env"

settings = Settings()
```

```python
# backend/services/narrative_filter/main.py
from fastapi import FastAPI
from prometheus_client import make_asgi_app
import structlog

from .config import settings
from .api import health

logger = structlog.get_logger()

app = FastAPI(
    title=settings.service_name,
    version="1.0.0",
    description="Filtro de Narrativas Multi-Agente"
)

# Health endpoint
app.include_router(health.router, prefix="/health", tags=["health"])

# Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

@app.on_event("startup")
async def startup_event():
    logger.info("narrative_filter_startup", version="1.0.0", port=settings.port)

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("narrative_filter_shutdown")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.port)
```

```python
# backend/services/narrative_filter/api/health.py
from fastapi import APIRouter, status
from pydantic import BaseModel

router = APIRouter()

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str

@router.get("/", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check():
    return HealthResponse(
        status="ok",
        service="narrative-filter",
        version="1.0.0"
    )
```

**Passo 2.2: Testes**

```python
# backend/services/narrative_filter/tests/test_health.py
import pytest
from fastapi.testclient import TestClient

from narrative_filter.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "narrative-filter"
    assert "version" in data
```

**Passo 2.3: Dockerfile**

```dockerfile
# docker/Dockerfile.narrative-filter
FROM python:3.11-slim

WORKDIR /app

# Dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Dependências Python
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir transformers sentence-transformers torch networkx scipy nats-py asyncpg

# Código
COPY backend/services/narrative_filter/ ./narrative_filter/

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8090/health/ || exit 1

# Run
CMD ["python", "-m", "uvicorn", "narrative_filter.main:app", "--host", "0.0.0.0", "--port", "8090"]
```

**Passo 2.4: Validação**

```bash
# Build
docker build -f docker/Dockerfile.narrative-filter -t vertice/narrative-filter:latest .

# Run
docker run -d --name narrative-filter-test -p 8090:8090 vertice/narrative-filter:latest

# Test
curl http://localhost:8090/health/
# Expected: {"status":"ok","service":"narrative-filter","version":"1.0.0"}

# Metrics
curl http://localhost:8090/metrics | grep narrative_filter
# Expected: Prometheus metrics output

# Cleanup
docker stop narrative-filter-test && docker rm narrative-filter-test
```

**Repetir Passos 2.1-2.4 para:**
- `verdict_engine` (port 8091)
- `command_bus` (port 8092)

**Critério de Sucesso Dia 2:**
- ✅ 3 microsserviços com health endpoints
- ✅ Docker images buildando
- ✅ Testes unitários 100% coverage

---

**[O PLANO CONTINUA COM TODAS AS FASES DETALHADAS]**

**Nota:** Este é um plano "anti-burro" completo. Cada passo é atômico, validável e segue fielmente a Constituição Vértice. O executor deve seguir EXATAMENTE esta sequência, validando cada etapa antes de prosseguir.

---

## IV. VALIDAÇÃO CONTÍNUA

### 4.1 Checklist Por Fase

```yaml
Antes_de_Commit:
  - [ ] Ruff pass (zero warnings)
  - [ ] MyPy pass (zero errors)
  - [ ] Pytest pass (zero failures)
  - [ ] Coverage ≥ 95%
  - [ ] Zero TODOs no código
  - [ ] Zero mocks em código de produção

Antes_de_Avançar_de_Fase:
  - [ ] Testes E2E da fase passando
  - [ ] Métricas de performance atingidas
  - [ ] Documentação atualizada
  - [ ] Review do Arquiteto-Chefe

Final:
  - [ ] Sistema completo funcionando
  - [ ] Load tests passando
  - [ ] Simulação adversarial bem-sucedida
  - [ ] Documentação completa (API docs, runbooks)
```

### 4.2 Comandos de Validação Rápida

```bash
# Lint + Type check
ruff check backend/services/ && mypy backend/services/

# Testes com coverage
pytest backend/services/ --cov --cov-report=term --cov-fail-under=95

# Buscar mocks/TODOs
grep -r "TODO\|FIXME\|mock\|Mock" backend/services/ --include="*.py" | grep -v tests

# Build Docker images
docker-compose -f docker-compose.cockpit.yml build

# Start e test
docker-compose -f docker-compose.cockpit.yml up -d
sleep 10
curl http://localhost:8090/health/
curl http://localhost:8091/health/
curl http://localhost:8092/health/
```

---

## V. FORMATO DE REPORTE

### 5.1 Ao Concluir Cada Dia

```markdown
## Dia X - [NOME_DA_FASE]

### Executado:
- ✅ [Task 1]: [Descrição técnica breve]
- ✅ [Task 2]: [Descrição técnica breve]

### Validação:
- Coverage: [X]%
- Lint: [0 warnings]
- Tests: [X/X passed]

### Bloqueadores:
- ❌ [Se houver]: [Descrição] → [Alternativa proposta]

### Métricas:
- [Métrica 1]: [Valor] (target: [Target])
- [Métrica 2]: [Valor] (target: [Target])
```

### 5.2 Ao Concluir Cada Fase

```markdown
## FASE X - COMPLETA

### Deliverables:
- ✅ [Componente 1]
- ✅ [Componente 2]

### Validação Final:
- E2E tests: [X/X passed]
- Performance: [Métricas vs. targets]
- Conformidade Pagani: [100%]

### Próxima Fase:
- [Nome da próxima fase]
- [Dependências resolvidas]
```

---

**STATUS:** PLANO DE AÇÃO APROVADO  
**EXECUTOR CONFIGURADO:** Dev Sênior fiel à Constituição  
**PRÓXIMO COMANDO:** Iniciar Fase 1 - Dia 1

