# Testing Infrastructure - Container Management

## Problema Identificado
Sistema com 66+ containers rodando simultaneamente causando:
- CPU: Load average 5.46 (91% saturação em 6 cores)
- Temperatura: CPU 65°C, NVMe 62.9°C
- Memória: 8.3Gi/15Gi usado
- Container maximus-core sozinho: 404% CPU, 3GB RAM, 130 PIDs

## Estratégia: Test-Driven Container Lifecycle

Rodar apenas containers necessários para cada bateria de testes, depois derrubar.

---

## 📦 Core Infrastructure Services

Sempre necessários (manter rodando durante testes):

```bash
# Start Core Infrastructure
docker compose up -d \
  vertice-redis \
  vertice-postgres \
  vertice-qdrant \
  vertice-grafana
```

**Recursos Core:**
- Redis: ~22 MB RAM
- PostgreSQL: ~53 MB RAM
- Qdrant: ~300 MB RAM
- Grafana: ~293 MB RAM
**Total: ~668 MB RAM**

---

## 🧪 Test Profiles

### Profile 1: Maximus Core Testing
**Dependências:**
- Core Infrastructure (acima)
- Kafka + Zookeeper
- RabbitMQ (opcional, se usar mensageria)

```bash
# Start Maximus Test Environment
docker compose up -d \
  vertice-redis \
  vertice-postgres \
  hcl-kafka \
  maximus-zookeeper-immunity \
  maximus-core

# Run Tests
cd backend/services/maximus_core_service
pytest tests/unit/ -v --cov

# Cleanup
docker compose stop maximus-core hcl-kafka maximus-zookeeper-immunity
```

**Recursos Estimados:**
- Core: 668 MB
- Kafka: 675 MB
- Zookeeper: 132 MB
- Maximus: 3 GB (reduzir config se necessário)
**Total: ~4.5 GB RAM**

---

### Profile 2: Consciousness Services Testing
**Dependências:**
- Core Infrastructure
- Kafka (broadcasting)
- Redis Streams (hot path)

```bash
# Start Consciousness Test Environment
docker compose up -d \
  vertice-redis \
  hcl-kafka \
  vertice-visual-cortex \
  vertice-auditory-cortex \
  vertice-somatosensory \
  vertice-chemical-sensing \
  vertice-vestibular \
  vertice-neuromodulation \
  memory-consolidation-service

# Run Tests
cd backend/services/consciousness
pytest tests/ -v

# Cleanup
docker compose stop \
  vertice-visual-cortex \
  vertice-auditory-cortex \
  vertice-somatosensory \
  vertice-chemical-sensing \
  vertice-vestibular \
  vertice-neuromodulation \
  memory-consolidation-service \
  hcl-kafka
```

**Recursos Estimados:**
- Core: 668 MB
- Kafka: 675 MB
- 7 services × ~40 MB: 280 MB
**Total: ~1.6 GB RAM**

---

### Profile 3: Immunity Services Testing
**Dependências:**
- Core Infrastructure
- PostgreSQL (immune data)
- RabbitMQ (cell communication)

```bash
# Start Immunity Test Environment
docker compose up -d \
  vertice-redis \
  vertice-postgres \
  maximus-postgres-immunity \
  vertice-rabbitmq \
  active-immune-core \
  vertice-immunis-neutrophil \
  vertice-immunis-macrophage \
  vertice-immunis-dendritic \
  vertice-immunis-nk-cell \
  vertice-immunis-helper-t \
  vertice-immunis-cytotoxic-t \
  vertice-immunis-bcell \
  immunis-treg-service \
  adaptive-immunity-service

# Run Tests
cd backend/services/active_immune_core
pytest tests/ -v

# Cleanup
docker compose stop \
  active-immune-core \
  vertice-immunis-* \
  immunis-treg-service \
  adaptive-immunity-service \
  maximus-postgres-immunity \
  vertice-rabbitmq
```

**Recursos Estimados:**
- Core: 668 MB
- RabbitMQ: 162 MB
- Immune Services: ~500 MB
**Total: ~1.3 GB RAM**

---

### Profile 4: HCL (Human Cognition Loop) Testing
**Dependências:**
- Core Infrastructure
- Kafka (orchestration)

```bash
# Start HCL Test Environment
docker compose up -d \
  vertice-redis \
  vertice-postgres \
  hcl-kafka \
  vertice-hcl-analyzer \
  vertice-hcl-planner \
  vertice-hcl-executor \
  vertice-hcl-monitor \
  hcl-kb-service

# Run Tests
cd backend/services/hcl
pytest tests/ -v

# Cleanup
docker compose stop \
  vertice-hcl-* \
  hcl-kb-service \
  hcl-kafka
```

**Recursos Estimados:**
- Core: 668 MB
- Kafka: 675 MB
- HCL Services: ~200 MB
**Total: ~1.5 GB RAM**

---

### Profile 5: Security/Offensive Tools Testing
**Dependências:**
- Core Infrastructure apenas

```bash
# Start Security Test Environment
docker compose up -d \
  vertice-redis \
  vertice-postgres \
  vertice-qdrant \
  vertice-nmap \
  vertice-vuln-scanner \
  vertice-malware-analysis \
  vertice-offensive-tools

# Run Tests
cd backend/services/security
pytest tests/ -v

# Cleanup
docker compose stop \
  vertice-nmap \
  vertice-vuln-scanner \
  vertice-malware-analysis \
  vertice-offensive-tools
```

**Recursos Estimados:**
- Core: 668 MB
- Security Tools: ~200 MB
**Total: ~900 MB RAM**

---

## 🔧 Helper Scripts

### Complete Shutdown
```bash
#!/bin/bash
# scripts/shutdown-all.sh
docker ps -q | xargs -r docker stop
echo "All containers stopped"
sensors | grep -E "Package|Composite"
```

### Start Core Only
```bash
#!/bin/bash
# scripts/start-core.sh
docker compose up -d \
  vertice-redis \
  vertice-postgres \
  vertice-qdrant \
  vertice-grafana

echo "Core infrastructure started"
docker stats --no-stream
```

### Health Check
```bash
#!/bin/bash
# scripts/health-check.sh
echo "=== Container Status ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Size}}"

echo -e "\n=== System Resources ==="
free -h
uptime

echo -e "\n=== Temperatures ==="
sensors | grep -E "Package|Composite|temp1"
```

---

## 📊 Resource Monitoring

### Before Starting Tests
```bash
# Check available resources
free -h
uptime
sensors
docker ps -q | wc -l  # Should be 0 or only core services
```

### During Tests
```bash
# Monitor in real-time
watch -n 2 'docker stats --no-stream; echo "---"; sensors | grep -E "Package|Composite"'
```

### After Tests
```bash
# Cleanup and verify
docker compose stop <service-names>
sleep 5
sensors  # Should see temperature drop
docker ps  # Verify stopped
```

---

## ⚙️ Configuration Recommendations

### Maximus Core Optimization
Se `maximus-core` continuar consumindo 400% CPU, ajustar em `docker-compose.yml`:

```yaml
maximus-core:
  # ... existing config ...
  deploy:
    resources:
      limits:
        cpus: '2.0'      # Limit to 2 cores
        memory: 2G       # Limit to 2GB
      reservations:
        cpus: '1.0'
        memory: 1G
  environment:
    # Add if using ML/Torch
    OMP_NUM_THREADS: 2
    MKL_NUM_THREADS: 2
    NUMEXPR_NUM_THREADS: 2
```

### Kafka Optimization
```yaml
hcl-kafka:
  # ... existing config ...
  environment:
    KAFKA_HEAP_OPTS: "-Xms256M -Xmx512M"  # Reduce from 1G
    KAFKA_JVM_PERFORMANCE_OPTS: "-XX:+UseG1GC -XX:MaxGCPauseMillis=20"
```

---

## 🎯 Testing Workflow

### Daily Development
```bash
# Morning: Start only what you need
./scripts/start-core.sh

# Working on Maximus?
docker compose up -d hcl-kafka maximus-core

# Run tests
cd backend/services/maximus_core_service
pytest tests/unit/

# Done? Stop it
docker compose stop maximus-core hcl-kafka

# End of day: Full cleanup
./scripts/shutdown-all.sh
```

### CI/CD Pipeline
```yaml
# .github/workflows/test-maximus.yml
- name: Start Test Infrastructure
  run: |
    docker compose up -d vertice-redis vertice-postgres hcl-kafka
    sleep 10  # Wait for services

- name: Start Service Under Test
  run: docker compose up -d maximus-core

- name: Run Tests
  run: |
    cd backend/services/maximus_core_service
    pytest tests/ -v --cov

- name: Cleanup
  if: always()
  run: docker compose down
```

---

## 📈 Expected Improvements

**Before (66 containers):**
- Load: 5.46
- CPU Temp: 65°C
- NVMe Temp: 62.9°C
- RAM: 8.3 GB used

**After (Core + 1 Service Profile):**
- Load: ~1.5-2.0
- CPU Temp: ~45-50°C
- NVMe Temp: ~40-45°C
- RAM: ~2-5 GB used (depending on profile)

**Estimated Time Savings:**
- Full stack startup: 2-3 minutes → 10-20 seconds
- Temperature normalization: Never → 5-10 seconds
- Development feedback loop: Faster, more stable

---

## 🚨 Emergency Procedures

### System Overheating
```bash
# Immediate shutdown
docker ps -q | xargs -r docker stop
pkill -9 -f uvicorn  # Kill stuck Python processes

# Wait for cooldown
watch sensors
# Wait until CPU < 50°C, NVMe < 45°C
```

### Memory Pressure
```bash
# Check memory hogs
docker stats --no-stream | sort -k 7 -h

# Stop biggest consumers first
docker stop <container-name>
```

### Stuck Processes
```bash
# Find multiprocessing workers
ps aux | grep multiprocessing

# Kill parent process (safer)
pkill -f "uvicorn.*--workers"

# Nuclear option
ps aux | grep multiprocessing | awk '{print $2}' | xargs kill -9
```

---

## ✅ Pre-Test Checklist

- [ ] All containers stopped (`docker ps` shows empty or only core)
- [ ] CPU temp < 50°C
- [ ] Load average < 2.0
- [ ] Free RAM > 7 GB
- [ ] No stuck Python processes (`ps aux | grep multiprocessing`)

---

## 📝 Notes

- Always run `./scripts/health-check.sh` before starting tests
- Never run all 66 containers simultaneously during development
- Use profiles to isolate what you're testing
- Monitor temperatures - NVMe > 60°C is concerning
- Maximus Core needs resource limits configured
- CI/CD should use minimal profiles

**Generated:** 2025-10-21
**System:** Linux Mint 6.14.0-33 / i5-10400F (6 cores) / 16GB RAM
