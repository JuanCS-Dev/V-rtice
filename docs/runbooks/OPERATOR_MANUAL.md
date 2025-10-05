# VÉRTICE - Operator Manual
**FASE 7: Production Operations Guide**

## Visão Geral

VÉRTICE é um organismo digital bio-inspirado com **3 camadas neurais**:

1. **Camada 1: Reflexos (RTE)** - < 5ms
2. **Camada 2: Sistema Imunológico (Immunis)** - < 100ms
3. **Camada 3: Córtex (MAXIMUS)** - ~30s

Este manual descreve operações diárias, troubleshooting, e procedimentos de emergência.

---

## 1. Operações Diárias

### 1.1. Health Checks Matinais

Execute diariamente às 09:00:

```bash
# Verificar status de todos os serviços
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Verificar saúde via API
curl http://localhost:8001/health | jq

# Verificar métricas Prometheus
curl http://localhost:9090/-/healthy
```

**Critérios de Sucesso:**
- Todos os serviços com status `Up`
- Health checks retornando `200 OK`
- Prometheus acessível

### 1.2. Monitoramento Contínuo

**Dashboards Grafana:**
- **VÉRTICE Overview:** http://localhost:3000/d/vertice-overview
- **Reflex Layer (RTE):** http://localhost:3000/d/rte-reflex
- **Immune System (Immunis):** http://localhost:3000/d/immunis
- **Conscious Layer (MAXIMUS):** http://localhost:3000/d/maximus

**Métricas Críticas:**
| Métrica | Target | Alerta Se |
|---|---|---|
| RTE p99 Latency | < 50ms | > 50ms |
| Throughput | > 1000 events/s | < 500 events/s |
| Detection Rate | > 95% | < 90% |
| False Positive Rate | < 0.1% | > 1% |

### 1.3. Log Rotation

Logs são rotacionados automaticamente, mas verifique semanalmente:

```bash
# Verificar tamanho dos logs
du -sh /var/log/vertice/*

# Limpar logs antigos (> 30 dias)
find /var/log/vertice -name "*.log" -mtime +30 -delete
```

---

## 2. Troubleshooting

### 2.1. RTE Latency Alta (> 50ms)

**Sintomas:**
- Dashboard mostra p99 > 50ms
- Alerta `RTELatencyHigh` firing

**Diagnóstico:**
```bash
# Verificar CPU usage
docker stats rte_service

# Verificar pattern database size
docker exec rte_service ls -lh /app/patterns/

# Verificar backlog
curl http://localhost:8010/status | jq '.queue_depth'
```

**Soluções:**
1. **High CPU:** Escalar horizontalmente (adicionar réplicas)
2. **Large pattern DB:** Otimizar patterns, remover duplicatas
3. **High backlog:** Aumentar workers

```bash
# Escalar RTE (adicionar 2 réplicas)
docker-compose up -d --scale rte_service=3
```

### 2.2. Cytokine Storm (Immune Overload)

**Sintomas:**
- Alerta `CytokineStorm` firing
- Kafka lag aumentando
- Latência de Immunis > 100ms

**Diagnóstico:**
```bash
# Verificar Kafka lag
docker exec kafka kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --all-groups

# Verificar taxa de mensagens
curl http://localhost:9090/api/v1/query?query='rate(kafka_messages_in_per_sec[1m])'
```

**Soluções:**
1. **Rate Limiting:** Ativar backpressure
2. **Scale Consumers:** Aumentar réplicas de células imunes
3. **Circuit Breaker:** Temporariamente desabilitar células menos críticas

```bash
# Escalar Neutrophils (primeira linha de defesa)
docker-compose up -d --scale immunis_neutrophil_service=5
```

### 2.3. HPC Prediction Error Spike (Zero-Day)

**Sintomas:**
- Alerta `HPCPredictionErrorSpike` firing
- Prediction error > 2x baseline

**Ação:**
1. **Investigate:** Checar recent events no dashboard
2. **Correlate:** Verificar se múltiplos serviços reportam anomalia
3. **Escalate:** Se confirmado zero-day, acionar incident response

```bash
# Verificar últimos eventos anômalos
curl http://localhost:8011/hpc/anomalies | jq '.recent[]'

# Extrair IOCs
curl -X POST http://localhost:8051/extract_iocs \
  -H "Content-Type: application/json" \
  -d '{"event_id": "anomaly_12345"}'
```

### 2.4. MAXIMUS Inference Timeout (> 30s)

**Sintomas:**
- Alerta `MaximusLatencyHigh` firing
- API requests timing out

**Diagnóstico:**
```bash
# Verificar GPU memory
nvidia-smi

# Verificar model size
docker exec maximus_core_service ls -lh /app/models/

# Verificar concurrent requests
curl http://localhost:8001/stats | jq '.active_requests'
```

**Soluções:**
1. **GPU OOM:** Reduzir batch size
2. **Model too large:** Quantizar modelo (INT8)
3. **High concurrency:** Adicionar request queue

---

## 3. Deployment

### 3.1. Blue-Green Deployment

**Procedimento:**

```bash
cd /home/juan/vertice-dev/deployment/blue-green

# Deploy nova versão (blue)
./deploy.sh production blue

# Script executa automaticamente:
# 1. Deploy
# 2. Health checks
# 3. Integration tests
# 4. Canary release (10% → 50% → 100%)
# 5. Full cutover
# 6. Cleanup old environment
```

**Rollback:**
```bash
# Se deployment falhar, rollback automático
# Se precisar rollback manual:
./deploy.sh production green  # volta para versão anterior
```

### 3.2. Hotfix Deployment

Para correções urgentes sem downtime:

```bash
# 1. Build hotfix image
docker build -t vertice/maximus_core:hotfix-001 .

# 2. Deploy em staging primeiro
docker-compose -f docker-compose.staging.yml up -d maximus_core_service

# 3. Validar
curl http://staging.vertice.local:8001/health

# 4. Deploy em produção (blue-green)
./deploy.sh production blue
```

---

## 4. Backup e Recovery

### 4.1. Backup Diário

**O que fazer backup:**
- PostgreSQL (incident history, B Cell memory)
- Neo4j (knowledge graph)
- Kafka topics (cytokine messages - últimos 7 dias)
- Model weights (MAXIMUS, HSAS, hPC)

**Script automático:**
```bash
# Executar via cron (01:00 diariamente)
/home/juan/vertice-dev/scripts/backup.sh
```

### 4.2. Recovery

**Cenário: Perda total de dados**

```bash
# 1. Restaurar PostgreSQL
pg_restore -d vertice_db /backups/postgres/latest.dump

# 2. Restaurar Neo4j
neo4j-admin load --from=/backups/neo4j/latest.backup --database=neo4j

# 3. Restaurar Kafka topics
kafka-console-producer.sh --bootstrap-server localhost:9092 \
  --topic cytokine.alerts < /backups/kafka/cytokine.alerts.txt

# 4. Restaurar model weights
cp /backups/models/* /app/models/

# 5. Restart services
docker-compose restart
```

---

## 5. Performance Tuning

### 5.1. RTE Optimization

**Hyperscan Pattern Compilation:**
```bash
# Recompilar patterns para CPU atual (AVX2, AVX512)
docker exec rte_service /app/compile_patterns.sh --cpu-native
```

**Tuning:**
- **CPU Affinity:** Pinnar RTE em cores dedicados
- **NUMA:** Evitar cross-NUMA memory access
- **Huge Pages:** Habilitar para Hyperscan database

```bash
# Habilitar huge pages
echo 1024 > /proc/sys/vm/nr_hugepages

# Pinnar RTE em cores 0-7
docker update --cpuset-cpus="0-7" rte_service
```

### 5.2. GPU Optimization (MAXIMUS)

**Model Quantization:**
```python
# INT8 quantization (reduz latência 2-3x)
from transformers import AutoModelForCausalLM

model = AutoModelForCausalLM.from_pretrained("google/gemma-2-27b-it")
model = model.to(torch.int8)
model.save_pretrained("/app/models/gemma_int8")
```

**Batch Inference:**
```bash
# Aumentar batch size (se GPU memory permitir)
docker exec maximus_core_service \
  sed -i 's/BATCH_SIZE=1/BATCH_SIZE=4/' /app/.env

docker restart maximus_core_service
```

---

## 6. Security

### 6.1. Credenciais

**Rotacionar chaves trimestralmente:**
```bash
# Gerar nova API key
openssl rand -hex 32

# Atualizar .env
sed -i 's/API_KEY=.*/API_KEY=<nova_key>/' .env

# Reload services
docker-compose up -d
```

### 6.2. Network Isolation

**Firewall rules:**
```bash
# Permitir apenas IPs autorizados
ufw allow from 10.0.0.0/8 to any port 8001  # MAXIMUS
ufw allow from 10.0.0.0/8 to any port 9090  # Prometheus
ufw deny 8001  # Bloquear acesso externo
```

---

## 7. Escalação

### 7.1. Quando Escalar

**Indicadores:**
- CPU > 80% sustained (> 10min)
- Memory > 90%
- Latency p99 > target (RTE: 50ms, Immunis: 100ms, MAXIMUS: 30s)
- Queue depth > 1000

### 7.2. Horizontal Scaling

**Stateless services (podem escalar livremente):**
- RTE
- Immunis (todas as células)
- HPC
- HSAS

```bash
# Escalar automaticamente com HPA (Horizontal Pod Autoscaler)
kubectl autoscale deployment rte-service --cpu-percent=70 --min=3 --max=10
```

**Stateful services (escalar com cuidado):**
- MAXIMUS Core (compartilha model weights)
- Neuromodulation (estado global)

---

## 8. Incident Response

### 8.1. Severity Levels

| Nível | Descrição | SLA | Exemplos |
|---|---|---|---|
| **P0 - Critical** | Sistema down | 15min | All services down, data loss |
| **P1 - High** | Degraded performance | 1h | RTE latency > 100ms, FP rate > 5% |
| **P2 - Medium** | Partial outage | 4h | Single service down, backlog growing |
| **P3 - Low** | Minor issue | 24h | Log errors, config warnings |

### 8.2. On-Call Runbook

**P0 - Sistema Down:**
1. Verificar infraestrutura (AWS, K8s)
2. Checar recent deployments (rollback se necessário)
3. Verificar logs: `docker-compose logs --tail=1000`
4. Acionar backup team se não resolver em 15min

**P1 - RTE Latency Crítica:**
1. Escalar RTE horizontalmente
2. Verificar pattern database corruption
3. Ativar circuit breaker (bypass RTE, usar fallback)
4. Investigar root cause após mitigação

---

## 9. Contacts

**Escalação:**
- **L1 Support:** vertice-l1@empresa.com
- **L2 Support:** vertice-l2@empresa.com
- **On-Call Engineer:** +55 11 99999-9999 (PagerDuty)

**Vendors:**
- **Google Cloud (Gemini API):** support@google.com
- **Confluent (Kafka):** support@confluent.io

---

**Última atualização:** FASE 7 - 2025-10-05
**Versão:** 1.0
**Autor:** VÉRTICE DevOps Team
