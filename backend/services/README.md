# HCL Services - Homeostatic Control Loop

**Sistema completo de controle autônomo inspirado em neurociência e imunologia.**

## Arquitetura MAPE-K

```
┌─────────────────────────────────────────────────────────────────┐
│                      HCL - MAPE-K Loop                           │
│                                                                   │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │ MONITOR  │───▶│ ANALYZE  │───▶│  PLAN    │───▶│ EXECUTE  │  │
│  │ (8001)   │    │ (8002)   │    │ (8003)   │    │ (8004)   │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│       │               │                │               │         │
│       │               │                │               │         │
│       └───────────────┴────────────────┴───────────────┘         │
│                            │                                     │
│                            ▼                                     │
│                  ┌──────────────────┐                           │
│                  │   KNOWLEDGE      │                           │
│                  │   (PostgreSQL    │                           │
│                  │   + TimescaleDB) │                           │
│                  │   (8000)         │                           │
│                  └──────────────────┘                           │
└─────────────────────────────────────────────────────────────────┘
```

## Serviços

### 1. HCL Knowledge Base (Port 8000)
- **Função:** Memória persistente do sistema
- **Tecnologia:** PostgreSQL + TimescaleDB
- **Armazena:**
  - Métricas históricas (hypertables)
  - Decisões tomadas
  - Versões de modelos ML
  - Análises de desempenho

### 2. HCL Monitor (Port 8001)
- **Função:** Coleta de métricas do sistema
- **Tecnologia:** psutil, pynvml, FastAPI, Prometheus
- **Coleta:**
  - CPU, Memory, GPU usage
  - Disk I/O, Network I/O
  - Latência, Error rate
  - Queue depth

### 3. HCL Analyzer (Port 8002)
- **Função:** Análise preditiva com ML
- **Tecnologia:** SARIMA, Isolation Forest, XGBoost
- **Predições:**
  - Forecast 1-24h (SARIMA)
  - Anomaly detection (Isolation Forest)
  - Failure prediction (XGBoost)

### 4. HCL Planner (Port 8003)
- **Função:** Tomada de decisão
- **Tecnologia:** Fuzzy Logic (scikit-fuzzy) + RL (SAC)
- **Decisões:**
  - Modo operacional (ENERGY_EFFICIENT, BALANCED, HIGH_PERFORMANCE)
  - Scaling de réplicas
  - Ajuste de resources

### 5. HCL Executor (Port 8004)
- **Função:** Execução de ações no K8s
- **Tecnologia:** Kubernetes Python Client
- **Ações:**
  - Scale deployments
  - Update resource limits
  - Manage HPA
  - Rollback automático

## Quick Start

### Pré-requisitos

```bash
# Docker e Docker Compose
docker --version  # 20.10+
docker-compose --version  # 1.29+

# (Opcional) Kubectl para executor K8s
kubectl version --client
```

### Iniciar todos os serviços

```bash
cd /home/juan/vertice-dev/backend/services

# Criar .env
cp .env.example .env

# Build e start
docker-compose up -d

# Ver logs
docker-compose logs -f

# Ver status
docker-compose ps
```

### Verificar health

```bash
# Knowledge Base
curl http://localhost:8000/health

# Monitor
curl http://localhost:8001/health

# Analyzer
curl http://localhost:8002/health

# Planner
curl http://localhost:8003/health

# Executor
curl http://localhost:8004/health
```

### Acessar UIs

- **Grafana:** http://localhost:3000 (admin/admin)
- **Prometheus:** http://localhost:9090
- **Kafka:** localhost:9094 (external)

## Fluxo de Dados

### 1. Coleta de Métricas (Monitor → KB + Kafka)

```bash
# Monitor coleta métricas a cada 15s
# Envia para:
# - Knowledge Base (HTTP): Persistência
# - Kafka topic: system.telemetry.raw (Streaming)
```

### 2. Análise Preditiva (Analyzer)

```bash
# Consome: system.telemetry.raw
# Processa com modelos ML
# Publica: system.predictions
```

### 3. Planejamento (Planner)

```bash
# Consome: system.predictions
# Decide modo operacional (Fuzzy Logic)
# Computa ações (RL Agent)
# Publica: system.actions
```

### 4. Execução (Executor)

```bash
# Consome: system.actions
# Valida e executa no K8s
# Registra resultado na KB
```

## Kafka Topics

```bash
# Criar manualmente (se necessário)
docker exec -it hcl-kafka kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --create --topic system.telemetry.raw \
  --partitions 3 --replication-factor 1

docker exec -it hcl-kafka kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --create --topic system.predictions \
  --partitions 3 --replication-factor 1

docker exec -it hcl-kafka kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --create --topic system.actions \
  --partitions 1 --replication-factor 1
```

### Ver mensagens

```bash
# Ver métricas
docker exec -it hcl-kafka kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic system.telemetry.raw \
  --from-beginning

# Ver predições
docker exec -it hcl-kafka kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic system.predictions \
  --from-beginning

# Ver ações
docker exec -it hcl-kafka kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic system.actions \
  --from-beginning
```

## Treinamento de Modelos ML

### SARIMA (Forecasting)

```bash
# Treinar modelo de CPU
curl -X POST "http://localhost:8002/train/sarima/cpu_usage?days=30"

# Treinar modelo de Memory
curl -X POST "http://localhost:8002/train/sarima/memory_usage?days=30"

# Treinar modelo de GPU
curl -X POST "http://localhost:8002/train/sarima/gpu_usage?days=30"
```

### Isolation Forest (Anomaly Detection)

```bash
curl -X POST "http://localhost:8002/train/isolation_forest?days=30"
```

### RL Agent (Resource Allocation)

```bash
# Treinar agente SAC (50k timesteps)
curl -X POST "http://localhost:8003/train/rl?timesteps=50000"
```

## Testes de Integração

### 1. Teste Manual - Fluxo Completo

```bash
# 1. Coletar métricas
curl http://localhost:8001/metrics/latest

# 2. Forçar análise
curl -X POST http://localhost:8002/analyze

# 3. Forçar decisão
curl -X POST http://localhost:8003/decide \
  -H "Content-Type: application/json" \
  -d '{
    "state": {
      "timestamp": "2025-10-03T10:30:00Z",
      "cpu_usage": 85.5,
      "memory_usage": 78.2,
      "gpu_usage": 45.0,
      "queue_depth": 350,
      "error_rate": 12.5,
      "latency": 450.0,
      "replicas": {
        "maximus_core": 3,
        "threat_intel": 2,
        "malware": 2
      }
    }
  }'

# 4. Ver histórico de execuções
curl http://localhost:8004/history
```

### 2. Teste Fuzzy Logic

```bash
# Testar diferentes cenários
curl "http://localhost:8003/fuzzy/test?cpu=20&memory=30&error_rate=5&latency=80"
# Resultado: ENERGY_EFFICIENT

curl "http://localhost:8003/fuzzy/test?cpu=85&memory=78&error_rate=12&latency=450"
# Resultado: HIGH_PERFORMANCE
```

### 3. Teste Kubernetes (Dry-run)

```bash
# Listar deployments
curl http://localhost:8004/deployments

# Testar scale (dry-run)
curl -X POST http://localhost:8004/scale \
  -H "Content-Type: application/json" \
  -d '{"service": "maximus_core", "target_replicas": 5}'
```

## Consultas PostgreSQL

```bash
# Conectar ao banco
docker exec -it hcl-postgres psql -U hcl_user -d hcl_knowledge

# Ver métricas recentes
SELECT * FROM system_metrics ORDER BY timestamp DESC LIMIT 10;

# Ver decisões tomadas
SELECT * FROM hcl_decisions ORDER BY timestamp DESC LIMIT 10;

# Estatísticas de CPU (última hora)
SELECT
  time_bucket('5 minutes', timestamp) AS bucket,
  avg(value) as avg_cpu,
  max(value) as max_cpu
FROM system_metrics
WHERE metric_name = 'cpu_usage_percent'
  AND timestamp > NOW() - INTERVAL '1 hour'
GROUP BY bucket
ORDER BY bucket DESC;
```

## Monitoramento com Prometheus

### Queries úteis

```promql
# Taxa de coleta de métricas
rate(metrics_collected_total[5m])

# Latência média
avg(system_latency_ms)

# CPU usage por serviço
avg(cpu_usage_percent) by (service)

# Predições de anomalias (últimos 5min)
sum(rate(anomalies_detected_total[5m]))

# Decisões executadas (por status)
sum(hcl_decisions_total) by (status)
```

## Dashboards Grafana

### Import dashboards

1. Acessar http://localhost:3000
2. Login: admin/admin
3. Import → Upload JSON

**Dashboards recomendados:**
- HCL Overview (métricas gerais)
- ML Models Performance
- Kubernetes Actions
- MAPE-K Loop Latency

## Desenvolvimento

### Rebuild de serviço específico

```bash
# Rebuild Monitor
docker-compose up -d --build hcl-monitor

# Rebuild Planner
docker-compose up -d --build hcl-planner
```

### Ver logs de serviço específico

```bash
docker-compose logs -f hcl-monitor
docker-compose logs -f hcl-analyzer
docker-compose logs -f hcl-planner
docker-compose logs -f hcl-executor
```

### Entrar no container

```bash
docker exec -it hcl-monitor bash
docker exec -it hcl-planner bash
```

## Troubleshooting

### Kafka não conecta

```bash
# Ver logs do Kafka
docker-compose logs kafka

# Verificar topics
docker exec -it hcl-kafka kafka-topics.sh \
  --bootstrap-server localhost:9092 --list

# Recriar Kafka
docker-compose rm -f kafka
docker volume rm services_kafka_data
docker-compose up -d kafka
```

### PostgreSQL connection error

```bash
# Ver logs
docker-compose logs postgres

# Verificar conectividade
docker exec -it hcl-postgres pg_isready -U hcl_user

# Recriar database
docker-compose rm -f postgres
docker volume rm services_postgres_data
docker-compose up -d postgres
```

### Modelos ML não carregam

```bash
# Verificar volumes
docker volume inspect services_analyzer_models
docker volume inspect services_planner_models

# Limpar e retreinar
docker volume rm services_analyzer_models services_planner_models
docker-compose up -d hcl-analyzer hcl-planner

# Treinar novamente
curl -X POST "http://localhost:8002/train/sarima/cpu_usage?days=7"
curl -X POST "http://localhost:8003/train/rl?timesteps=10000"
```

### Executor não acessa K8s

```bash
# Verificar kubeconfig
ls -la ~/.kube/config

# Testar acesso local
kubectl get pods

# Ver logs do executor
docker-compose logs hcl-executor

# Habilitar DRY_RUN se não tiver cluster
# Editar docker-compose.yml:
#   DRY_RUN: "true"
```

## Parar e Limpar

```bash
# Parar serviços
docker-compose down

# Parar e remover volumes (ATENÇÃO: Apaga dados!)
docker-compose down -v

# Limpar tudo
docker-compose down -v --rmi all
```

## Produção

Para deploy em produção:

1. **Ajustar recursos:**
   - Aumentar replicas (Monitor, Analyzer)
   - Aumentar memory limits
   - Configurar PVC para modelos

2. **Segurança:**
   - Trocar passwords padrão
   - Configurar TLS/SSL
   - RBAC K8s adequado

3. **Alta disponibilidade:**
   - Kafka com replication_factor > 1
   - PostgreSQL com replicação
   - Load balancer para APIs

4. **Monitoring:**
   - Alertmanager para Prometheus
   - Logs centralizados (ELK)
   - Distributed tracing (Jaeger)

## Referências

- **MAPE-K:** IBM Autonomic Computing
- **Fuzzy Logic:** Zadeh, L. A. (1965)
- **Soft Actor-Critic:** Haarnoja et al. (2018)
- **TimescaleDB:** https://docs.timescale.com/
- **Kafka:** https://kafka.apache.org/documentation/

## Zero Mock Guarantee

✅ Todos os serviços implementados com código real:
- Real PostgreSQL + TimescaleDB
- Real Kafka (KRaft mode)
- Real ML: statsmodels, scikit-learn, XGBoost, Stable-Baselines3
- Real Fuzzy Logic: scikit-fuzzy
- Real Kubernetes client
- Real Prometheus metrics

**Production-ready code. No placeholders.**
