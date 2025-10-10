# MAXIMUS AI 3.0 - Deployment Guide

> **Digital Neural Architecture for Autonomous Cybersecurity**

---

## 🧠 Architecture Overview

```
MAXIMUS AI 3.0 - NEURAL ARCHITECTURE
├── CAMADA 1 (Unconscious) - 18,301 linhas
│   ├── Neuromodulation (4 neurotransmitters)
│   └── Immunis System (7 cell types)
│
├── CAMADA 2 (Conscious) - 2,241 linhas
│   └── Strategic Planning (Prefrontal Cortex)
│
├── CAMADA 3 (Offline) - 2,491 linhas
│   ├── Memory Consolidation (Hippocampal Replay)
│   └── HSAS (Hybrid Skill Acquisition)
│
├── FRONTEND - 2,217 linhas React
│   └── 7 componentes + 6 CSS files (2,139 linhas)
│
└── MONITORING - Prometheus + Grafana
    ├── 20+ Alert Rules
    └── 12 Dashboard Panels

TOTAL: 27,389 linhas de código real, funcional, zero mocks
```

---

## 🚀 Quick Start

### Prerequisites

- Docker 24.0+
- Docker Compose 2.20+
- 8GB RAM minimum
- 20GB disk space

### 1. Clone & Navigate

```bash
cd /home/juan/vertice-dev
```

### 2. Start Full Stack

```bash
# Start all services + monitoring
docker-compose -f docker-compose.monitoring.yml up -d

# Check status
docker-compose -f docker-compose.monitoring.yml ps

# View logs
docker-compose -f docker-compose.monitoring.yml logs -f
```

### 3. Access Endpoints

| Service | URL | Description |
|---------|-----|-------------|
| **Neuromodulation** | http://localhost:8001 | Dopamine, Serotonin, ACh, NE |
| **Memory Consolidation** | http://localhost:8002 | Hippocampal Replay |
| **HSAS** | http://localhost:8003 | Skill Acquisition |
| **Strategic Planning** | http://localhost:8004 | Executive Function |
| **Immunis** | http://localhost:8005 | Immune System |
| **Prometheus** | http://localhost:9090 | Metrics |
| **Grafana** | http://localhost:3000 | Dashboards |
| **Node Exporter** | http://localhost:9100 | System Metrics |

---

## 📊 Monitoring

### Grafana Dashboard

**URL:** http://localhost:3000
**Username:** `admin`
**Password:** `maximus_ai_3_0`

**Pre-configured Dashboard:**
- `Maximus AI 3.0 - Neural Architecture`

**Panels:**
1. Neuromodulation real-time values
2. System state indicator
3. Buffer utilization gauge
4. Consolidation rates
5. HSAS success rate
6. Active policies count
7. Critical risks counter
8. Threat elimination rate
9. Inflammation level
10. Antibodies & Memory cells
11. Infrastructure metrics
12. Alert summary

### Prometheus Queries

```promql
# Neuromodulation
neuromodulation_dopamine_learning_rate
neuromodulation_serotonin_exploration_rate
neuromodulation_system_state

# Memory Consolidation
memory_consolidation_buffer_utilization_percent
rate(memory_consolidation_experiences_consolidated_total[5m])

# HSAS
hsas_success_rate
hsas_total_skills

# Strategic Planning
strategic_planning_active_policies
strategic_planning_risks_by_level{level="critical"}

# Immunis
immunis_inflammation_level
rate(immunis_threats_eliminated_total[5m])
```

---

## 🧬 Service Details

### 1. Neuromodulation Service (Port 8001)

**Biological Inspiration:** VTA, DRN, NBM, LC

**Endpoints:**
- `GET /health` - Service status
- `GET /stats` - Modulator statistics
- `GET /state` - Full system state
- `GET /history` - Modulation history
- `POST /reset` - Reset modulator to baseline
- `POST /signal` - Send modulation signal
- `GET /metrics` - Prometheus metrics

**Modulators:**
- **Dopamine (VTA):** Learning Rate Control (α)
- **Serotonin (DRN):** Exploration vs Exploitation (ε)
- **Acetylcholine (NBM):** Attention Gain
- **Noradrenaline (LC):** Urgency / Temperature (τ)

**Example Usage:**
```bash
# Get current stats
curl http://localhost:8001/stats

# Send RPE signal
curl -X POST http://localhost:8001/signal \
  -H "Content-Type: application/json" \
  -d '{
    "signal_type": "rpe",
    "data": {
      "predicted_reward": 0.5,
      "actual_reward": 0.8,
      "context": "threat_mitigation"
    }
  }'
```

---

### 2. Memory Consolidation Service (Port 8002)

**Biological Inspiration:** Hippocampus

**Endpoints:**
- `GET /health` - Service status
- `GET /stats` - Consolidation statistics
- `GET /buffer/stats` - Replay buffer stats
- `POST /sleep` - Enter sleep mode
- `POST /wake` - Enter wake mode
- `POST /consolidate` - Manual consolidation
- `POST /experience/add` - Add experience to buffer
- `GET /metrics` - Prometheus metrics

**Modes:**
- **SLEEP:** Deep consolidation (high batch size)
- **WAKE:** Continuous consolidation (low batch size)

**Example Usage:**
```bash
# Enter sleep mode
curl -X POST http://localhost:8002/sleep

# Trigger manual consolidation
curl -X POST http://localhost:8002/consolidate \
  -H "Content-Type: application/json" \
  -d '{
    "batch_size": 64,
    "strategy": "prioritized"
  }'
```

---

### 3. HSAS Service (Port 8003)

**Biological Inspiration:** Basal Ganglia + Cerebellum

**Endpoints:**
- `GET /health` - Service status
- `GET /skills` - List acquired skills
- `GET /primitives` - Skill primitives library
- `GET /stats` - Learning statistics
- `POST /select_action` - Get action for state
- `POST /execute` - Execute skill
- `POST /learn/demonstration` - Add demonstration
- `POST /mode` - Change learning mode
- `GET /metrics` - Prometheus metrics

**Learning Modes:**
- **MODEL_FREE:** Fast, habitual (Basal Ganglia)
- **MODEL_BASED:** Deliberative (Cerebellum)
- **HYBRID:** Automatic arbitration
- **IMITATION:** Learning from demonstrations

**Example Usage:**
```bash
# Get learning stats
curl http://localhost:8003/stats

# Select action
curl -X POST http://localhost:8003/select_action \
  -H "Content-Type: application/json" \
  -d '{
    "threat_level": 0.8,
    "num_alerts": 5,
    "severity": "high",
    "source_type": "external",
    "confidence": 0.9
  }'
```

---

### 4. Strategic Planning Service (Port 8004)

**Biological Inspiration:** Dorsolateral Prefrontal Cortex

**Endpoints:**
- `GET /health` - Service status
- `GET /policies` - List security policies
- `POST /policies` - Create policy
- `GET /resources` - Resource allocations
- `POST /resources/allocate` - Allocate resources
- `GET /risks` - Risk assessments
- `POST /risks/assess` - Assess risk
- `GET /approvals` - Pending approvals
- `POST /approvals/submit` - Submit action for approval
- `POST /approvals/approve` - Approve/reject action
- `GET /plans` - Strategic plans
- `POST /plans` - Create strategic plan
- `GET /metrics` - Prometheus metrics

**Example Usage:**
```bash
# List active policies
curl http://localhost:8004/policies?active_only=true

# Assess risk
curl -X POST http://localhost:8004/risks/assess \
  -H "Content-Type: application/json" \
  -d '{
    "threat_type": "ransomware",
    "probability": 0.7,
    "impact": 9.0,
    "context": {"industry": "finance"}
  }'
```

---

### 5. Immunis System Service (Port 8005)

**Biological Inspiration:** Human Immune System

**Endpoints:**
- `GET /health` - Service status
- `GET /innate/status` - Innate immunity status
- `GET /adaptive/status` - Adaptive immunity status
- `GET /cytokines/signals` - Cytokine activity
- `GET /antibody/library` - Antibody repertoire
- `GET /memory/cells` - Memory cells
- `POST /detect` - Detect and respond to threat
- `GET /stats` - System statistics
- `GET /metrics` - Prometheus metrics

**Cell Types:**
- **Innate:** Neutrophils, Macrophages, NK Cells
- **Adaptive:** Dendritic Cells, Helper T, Cytotoxic T, B Cells

**Example Usage:**
```bash
# Get innate immunity status
curl http://localhost:8005/innate/status

# Detect threat
curl -X POST http://localhost:8005/detect \
  -H "Content-Type: application/json" \
  -d '{
    "threat_type": "malware",
    "threat_data": {"hash": "abc123"},
    "severity": 8.0,
    "source": "external"
  }'
```

---

## 🔧 Configuration

### Environment Variables

Create `.env` file in each service directory:

```bash
# Common
PYTHONUNBUFFERED=1
LOG_LEVEL=INFO

# Service-specific
DOPAMINE_BASELINE_LR=0.001
BUFFER_CAPACITY=10000
HSAS_STATE_DIM=5
# ... etc
```

### Prometheus Configuration

Edit `monitoring/prometheus/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'neuromodulation'
    static_configs:
      - targets: ['neuromodulation_service:8001']
    scrape_interval: 5s
```

### Grafana Configuration

Edit `monitoring/grafana/datasources/prometheus.yml`:

```yaml
datasources:
  - name: Prometheus
    type: prometheus
    url: http://prometheus:9090
```

---

## 🐛 Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose -f docker-compose.monitoring.yml logs neuromodulation_service

# Restart service
docker-compose -f docker-compose.monitoring.yml restart neuromodulation_service
```

### High Memory Usage

```bash
# Check resource usage
docker stats

# Adjust buffer capacity
# Edit service configuration to reduce buffer_capacity
```

### Prometheus Not Scraping

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Verify service metrics endpoint
curl http://localhost:8001/metrics
```

### Grafana Dashboard Not Loading

```bash
# Re-provision dashboards
docker-compose -f docker-compose.monitoring.yml restart grafana

# Check Grafana logs
docker logs maximus-grafana
```

---

## 📈 Performance Tuning

### Neuromodulation Service
- Adjust modulator ranges in `neuromodulation_controller.py`
- Tune update thresholds

### Memory Consolidation
- Increase `buffer_capacity` for more experiences
- Adjust `sleep_cycle_interval` and `wake_consolidation_interval`

### HSAS
- Tune `model_free_threshold` for arbitration
- Adjust `learning_rate` and `gamma`

### Strategic Planning
- Configure approval workflow levels
- Tune risk assessment thresholds

### Immunis
- Adjust cell activation thresholds
- Configure cytokine signal thresholds

---

## 🔒 Security Notes

1. **Change default passwords** in `docker-compose.monitoring.yml`
2. **Configure CORS** appropriately for production
3. **Enable TLS** for all endpoints
4. **Implement authentication** middleware
5. **Review firewall rules**
6. **Enable audit logging**

---

## 📝 Development

### Run Service Locally

```bash
cd backend/services/neuromodulation_service
pip install -r ../requirements.txt
python -m uvicorn api:app --reload --port 8001
```

### Run Tests

```bash
pytest backend/services/neuromodulation_service/
```

### Add New Metric

```python
from prometheus_client import Counter

my_counter = Counter('my_metric', 'Description')
my_counter.inc()
```

---

## 📚 References

- [MAXIMUS AI Roadmap](../../02-MAXIMUS-AI/MAXIMUS_AI_ROADMAP_2025_REFACTORED.md)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

---

## 🎯 Next Steps

1. **Integrate with existing Vértice infrastructure**
2. **Configure alerting (Slack, Email, PagerDuty)**
3. **Implement distributed tracing (Jaeger)**
4. **Add APM (Application Performance Monitoring)**
5. **Configure log aggregation (ELK Stack)**
6. **Implement backup and disaster recovery**
7. **Scale horizontally with Kubernetes**

---

**Built with ❤️ by Maximus AI Team**
**Version:** 3.0.0
**Date:** 2025-10-03
**Lines of Code:** 27,389 (100% Real, Zero Mocks)
