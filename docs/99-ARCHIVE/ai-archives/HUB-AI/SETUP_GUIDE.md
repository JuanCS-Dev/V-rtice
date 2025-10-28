# HUB-AI Cockpit Soberano - Setup Guide

## Fase 1 - Dia 1: Infraestrutura Base

### ✅ Serviços Criados

1. **narrative_filter_service** (Port 9200)
2. **verdict_engine_service** (Port 9201)
3. **command_bus_service** (Port 9202)

### 📋 Pré-requisitos

- PostgreSQL 15+
- Kafka 3.0+
- Redis 7+
- Python 3.11+
- NATS 2.10+ (para command_bus)

### 🔧 Setup de Infraestrutura

#### 1. PostgreSQL Schema

```bash
# Aplicar migration
docker exec -i vertice-postgres psql -U vertice -d vertice_db < backend/services/narrative_filter_service/migrations/001_initial_schema.sql
```

**Tabelas criadas:**
- `semantic_representations` - Camada 1: Processamento semântico
- `strategic_patterns` - Camada 2: Padrões estratégicos
- `alliances` - Grafo de alianças entre agentes
- `verdicts` - Camada 3: Veredictos finais
- `c2l_commands` - Comandos de controle C2L
- `audit_trail` - Trilha de auditoria

#### 2. Kafka Topics

```bash
# Setup de topics
./scripts/setup_kafka_topics_hubai.sh
```

**Topics criados:**
- `agent-communications` - Input Camada 1 (6 partitions, 7d retention)
- `semantic-events` - Camada 1→2 (6 partitions, 3d retention)
- `strategic-patterns` - Camada 2→3 (3 partitions, 1d retention)
- `verdict-stream` - Camada 3→UI (3 partitions, 1d retention)

#### 3. NATS JetStream (Command Bus)

```bash
# Start NATS
docker compose -f docker-compose.cockpit.yml up -d nats

# Verify
curl http://localhost:8222/healthz
```

### 🧪 Validação dos Serviços

#### Health Checks

```bash
# narrative_filter_service
curl http://localhost:9200/health/

# verdict_engine_service
curl http://localhost:9201/health/

# command_bus_service
curl http://localhost:9202/health/
```

#### Metrics

```bash
# Prometheus metrics
curl http://localhost:9200/metrics
curl http://localhost:9201/metrics
curl http://localhost:9202/metrics
```

### 📊 Coverage Report

| Service | Tests | Coverage |
|---------|-------|----------|
| narrative_filter | 7 | 96.09% |
| verdict_engine | 4 | 95.12% |
| command_bus | 6 | 95.77% |

### 🏗️ Estrutura de Arquivos

```
backend/services/
├── narrative_filter_service/
│   ├── __init__.py
│   ├── config.py
│   ├── models.py
│   ├── main.py
│   ├── health_api.py
│   ├── migrations/
│   │   └── 001_initial_schema.sql
│   ├── tests/
│   │   ├── test_health.py
│   │   └── test_models.py
│   └── pyproject.toml
├── verdict_engine_service/
│   └── [mesma estrutura]
└── command_bus_service/
    └── [mesma estrutura]
```

### 🔄 Próximos Passos (Dia 2)

1. **Camada 1: Semantic Processor**
   - Embedding generation (sentence-transformers)
   - Intent classification
   - Kafka consumer/producer

2. **Database Repositories**
   - SemanticRepresentationRepository
   - StrategicPatternRepository
   - VerdictRepository

3. **Integration Tests**
   - E2E flow: Kafka → Processing → DB
   - Performance: Throughput > 100 msgs/sec

### 📝 Notas Técnicas

- **Embedding Model**: sentence-transformers/all-MiniLM-L6-v2 (384 dims)
- **PostgreSQL Extension**: pgvector para similarity search
- **Kafka Compression**: Snappy
- **NATS Streams**: JetStream habilitado para durabilidade

### 🎯 Métricas de Sucesso - Dia 1

✅ Todos os critérios atingidos:
- [x] 3 serviços skeleton completos
- [x] Coverage ≥ 95% em todos
- [x] Schema PostgreSQL definido
- [x] Topics Kafka configurados
- [x] Portas registradas (9200-9202)
- [x] Zero TODOs no código
- [x] Zero mocks em produção
- [x] Ruff: 0 errors
- [x] Testes: 100% passing

---

**Status**: Dia 1 COMPLETO ✅  
**Próximo**: Dia 2 - Skeleton Services → Implementação Camada 1
