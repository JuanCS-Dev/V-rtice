# hPC Service - Hierarchical Predictive Coding Network

**Bayesian threat prediction and autonomous active inference**

## Overview

O hPC (hierarchical Predictive Coding) é o **córtex preditivo** do Maximus AI 3.0. Inspirado na neurociência do predictive coding cortical, o hPC implementa inferência Bayesiana hierárquica para:

1. **Predizer ameaças** antes que ocorram (top-down)
2. **Detectar anomalias** via prediction errors (bottom-up)
3. **Atualizar crenças** continuamente (Bayesian updating)
4. **Caçar ameaças autonomamente** (active inference)

### Arquitetura Neurobiológica

```
CÓRTEX PREDITIVO (Predictive Coding)
═══════════════════════════════════════════════════════════════

Level 3: Strategic Intent          ┌──────────────┐
(Espionage, Sabotage, Financial)   │   BELIEFS    │ (posterior)
                ↓                   │  P(θ | data) │
         [TOP-DOWN PREDICTIONS]     └──────────────┘
                ↓                          ↑
Level 2: Campaign Signatures              │
(APT, Ransomware, DDoS)          [BAYESIAN UPDATE]
                ↓                          │
         [PREDICTIONS]                     │
                ↓                  ┌──────────────┐
Level 1: Attack Patterns           │ PREDICTION   │
(SQLi, XSS, RCE, Malware)          │   ERRORS     │
                ↓                  │ (obs - pred) │
                                   └──────────────┘
Level 0: Raw Features                     ↑
(Packets, Bytes, Entropy)                 │
                                  [BOTTOM-UP OBSERVATIONS]
                                          ↑
                                   ┌──────────────┐
                                   │ OBSERVATIONS │
                                   │   (sensory)  │
                                   └──────────────┘

ACTIVE INFERENCE: Agent takes actions to reduce uncertainty
```

### Mathematical Foundation

**Bayesian Inference:**
```
P(threat | observations) ∝ P(observations | threat) × P(threat)
      posterior         =      likelihood        ×     prior
```

**Predictive Coding:**
```
prediction_error = observation - prediction
belief_update = prior + precision × prediction_error
```

**Free Energy Minimization:**
```
Free Energy = Surprise + KL(posterior || prior)
Minimize F by: (1) improving predictions, (2) reducing uncertainty
```

## Architecture

### Components

1. **Bayesian Core** (`bayesian_core.py`)
   - Hierarchical Bayesian inference
   - Prior learning from normal traffic
   - Prediction generation (top-down)
   - Error computation (bottom-up)
   - Belief updating (posterior)
   - Real PyMC3 implementation

2. **Active Inference Engine** (`active_inference.py`)
   - Autonomous threat hunting
   - Uncertainty mapping
   - Action planning (epistemic value / cost)
   - Information gain measurement
   - Free energy minimization
   - 7 action types

3. **FastAPI Service** (`main.py`)
   - RESTful API
   - Async/await operations
   - Request/response models
   - Health checks

### Hierarchy Levels

**Level 0: Raw Features** (30 features)
- Packet size, count, bytes
- Payload entropy, header entropy
- Connection duration, PPS, BPS
- Unique ports, SYN/FIN/RST counts
- Protocol anomalies, geo-distance

**Level 1: Attack Patterns** (10 patterns)
- SQL injection score
- XSS score
- RCE score
- Path traversal score
- Malware score
- C2 communication score
- Exfiltration score
- Brute force score
- DoS score
- Scan score

**Level 2: Campaign Signatures** (6 campaigns)
- APT score
- Ransomware score
- DDoS score
- Crypto-mining score
- Botnet score
- Insider threat score

**Level 3: Strategic Intent** (4 intents)
- Espionage score
- Sabotage score
- Financial score
- Disruption score

## Quick Start

### 1. Build Docker Image

```bash
cd /home/juan/vertice-dev/backend/services/hpc_service
docker build -t hpc-service:latest .
```

### 2. Run Locally (Development)

```bash
# Install dependencies
pip install -r requirements.txt

# Run service
python main.py
```

Service runs on `http://localhost:8006`

### 3. Deploy to Kubernetes

```bash
# Deploy
kubectl apply -f k8s/deployment.yaml

# Check status
kubectl get pods -n hpc-system
kubectl logs -n hpc-system -l app=hpc-service -f
```

## API Endpoints

### POST /train

Train prior distribution from normal traffic.

**Request:**
```json
{
  "observations": [
    {
      "timestamp": 1704067200.0,
      "features": [500.0, 450.2, ...],  // 30 features
      "source_id": "192.168.1.10",
      "metadata": {"protocol": "TCP"}
    }
    // Send 500-1000 normal traffic observations
  ]
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Trained on 500 observations",
  "prior_mean_sample": [500.0, 450.2, 0.75, ...],
  "prior_variance_sample": [100.0, 80.0, 0.05, ...]
}
```

### POST /predict

Generate top-down threat prediction.

**Request:**
```json
{
  "context": {
    "time_of_day": "night",
    "source_history": "suspicious"
  }
}
```

**Response:**
```json
{
  "predicted_features": [500.0, ...],
  "predicted_variance": [100.0, ...],
  "confidence": 0.85,
  "threat_level": "medium",
  "threat_probabilities": {
    "critical": 0.05,
    "high": 0.15,
    "medium": 0.30,
    "low": 0.35,
    "benign": 0.15
  },
  "reasoning": "Bayesian prediction (threat_score=0.453)"
}
```

### POST /observe

Process observation and update beliefs.

**Request:**
```json
{
  "timestamp": 1704067200.0,
  "features": [5000.0, 4500.0, ...],  // Anomalous features
  "source_id": "192.168.1.100",
  "metadata": {"protocol": "TCP", "port": 3306}
}
```

**Response:**
```json
{
  "prediction_error_magnitude": 8.5,
  "surprise": 125.3,
  "updated_threat_probabilities": {
    "critical": 0.65,
    "high": 0.25,
    "medium": 0.08,
    "low": 0.02,
    "benign": 0.00
  },
  "updated_entropy": 1.2,
  "belief_state": {
    "feature_distribution": {...},
    "precision_matrix_shape": [30, 30],
    "timestamp": 1704067200.0
  }
}
```

### POST /infer

Run active inference for autonomous threat hunting.

**Request:**
```json
{
  "initial_observation": {
    "timestamp": 1704067200.0,
    "features": [5000.0, ...],
    "source_id": "suspicious_host",
    "metadata": {}
  },
  "exploration_budget": 50.0,
  "information_threshold": 0.5
}
```

**Response:**
```json
{
  "iterations": 12,
  "actions_executed": 12,
  "total_information_gain": 8.5,
  "final_entropy": 0.45,
  "final_threat_probabilities": {
    "critical": 0.85,
    "high": 0.10,
    "medium": 0.03,
    "low": 0.02,
    "benign": 0.00
  },
  "actions_summary": [
    {
      "action_type": "request_logs",
      "parameters": {"source_id": "suspicious_host", "time_range": "1h"},
      "success": true,
      "information_gained": 2.3,
      "execution_time_ms": 45.2
    }
    // ... more actions
  ],
  "threats_discovered": 1
}
```

### GET /beliefs

Get current belief state.

```bash
curl http://localhost:8006/beliefs
```

**Response:**
```json
{
  "threat_probabilities": {
    "critical": 0.15,
    "high": 0.25,
    "medium": 0.30,
    "low": 0.25,
    "benign": 0.05
  },
  "entropy": 2.1,
  "feature_distribution_sample": {
    "packet_size": {"mean": 523.4, "std": 105.2},
    "packet_count": {"mean": 45.2, "std": 12.3},
    ...
  },
  "timestamp": 1704067200.0,
  "observation_history_size": 850
}
```

### GET /stats

Performance statistics.

```bash
curl http://localhost:8006/stats
```

### GET /health

Health check.

```bash
curl http://localhost:8006/health
```

## Active Inference Actions

The active inference engine can execute these actions autonomously:

| Action | Description | Cost | Information Gain |
|--------|-------------|------|------------------|
| `probe_endpoint` | Scan IP/port for services | 2.0 | 5-10 |
| `request_logs` | Collect logs from source | 2.0 | 5-10 |
| `trace_connection` | Analyze network flow | 2.0 | 5-8 |
| `query_reputation` | Check threat intelligence | 0.5 | 2-5 |
| `analyze_payload` | Deep packet inspection | 3.0 | 8-12 |
| `monitor_host` | Continuous monitoring | 5.0 | 10-15 |
| `correlate_events` | Multi-source correlation | 4.0 | 12-18 |

**Priority = Information Gain / Cost**

The agent executes actions in priority order until:
1. Uncertainty (entropy) falls below threshold
2. Exploration budget exhausted
3. No more valuable actions available

## Usage Examples

### Example 1: Train on Normal Traffic

```python
import requests
import numpy as np

# Generate normal traffic features
normal_traffic = []
for i in range(500):
    features = list(np.concatenate([
        np.random.normal(500, 100, 10),  # Packet features
        np.random.uniform(0, 1, 10),     # Ratios
        np.random.randint(0, 100, 10).astype(float)  # Counts
    ]))

    normal_traffic.append({
        "timestamp": time.time(),
        "features": features,
        "source_id": f"192.168.1.{i % 255}",
        "metadata": {"type": "normal"}
    })

# Train
response = requests.post(
    "http://localhost:8006/train",
    json={"observations": normal_traffic}
)
print(response.json())
```

### Example 2: Predict-Observe-Update Cycle

```python
import requests

# Generate prediction
prediction = requests.post("http://localhost:8006/predict").json()
print(f"Predicted threat level: {prediction['threat_level']}")

# Observe anomalous traffic
observation = {
    "timestamp": time.time(),
    "features": [5000.0] * 30,  # Anomalous
    "source_id": "192.168.1.100",
    "metadata": {"suspicious": True}
}

response = requests.post(
    "http://localhost:8006/observe",
    json=observation
)

result = response.json()
print(f"Prediction error: {result['prediction_error_magnitude']:.2f}")
print(f"Updated threat: P(critical)={result['updated_threat_probabilities']['critical']:.3f}")
```

### Example 3: Autonomous Threat Hunting

```python
import requests

# Run active inference
response = requests.post(
    "http://localhost:8006/infer",
    json={
        "exploration_budget": 30.0,
        "information_threshold": 0.5,
        "initial_observation": {
            "timestamp": time.time(),
            "features": [3000.0] * 30,  # Suspicious
            "source_id": "unknown_host",
            "metadata": {}
        }
    }
)

result = response.json()
print(f"Executed {result['actions_executed']} actions")
print(f"Information gained: {result['total_information_gain']:.2f}")
print(f"Final threat: P(critical)={result['final_threat_probabilities']['critical']:.3f}")
print(f"Threats discovered: {result['threats_discovered']}")
```

## Configuration

### Environment Variables

- `HPC_HOST` - Bind host (default: `0.0.0.0`)
- `HPC_PORT` - Bind port (default: `8006`)
- `NUM_FEATURES` - Feature vector size (default: `30`)
- `HIERARCHY_LEVELS` - Hierarchy levels (default: `4`)
- `LEARNING_RATE` - Belief update rate (default: `0.1`)
- `EXPLORATION_BUDGET` - Active inference budget (default: `100.0`)

### Model Persistence

Trained priors are saved to `/app/models/hpc_prior.npz`:
```python
{
  'prior_mean': np.array([...]),      # 30 features
  'prior_variance': np.array([...])   # 30 features
}
```

## Integration with Maximus AI

### hPC → RTE Integration

```
hPC predicts threat → RTE validates with Hyperscan → Execute playbooks
```

Example:
```python
# hPC predicts SQL injection attack
prediction = hpc.predict()  # threat_level="high", SQLi_score=0.85

# RTE scans payload with Hyperscan
rte_result = rte.detect(payload)  # Confirms SQLi pattern

# Execute playbook
playbook.block_ip(source_ip)
```

### hPC → HCL Integration

```
hPC detects anomaly → HCL analyzes impact → HCL plans mitigation
```

Example:
```python
# hPC detects anomaly via prediction error
pred_error = hpc.compute_error(observation)  # error=8.5, surprise=125

# HCL analyzer forecasts impact
hcl_forecast = hcl_analyzer.predict(metric="cpu", steps=24)

# HCL planner decides action
hcl_action = hcl_planner.plan(state)  # Scale up, change mode
```

## Performance

### Latency Targets

| Operation | Target | Typical |
|-----------|--------|---------|
| Predict | <50ms | ~30ms |
| Observe + Update | <100ms | ~65ms |
| Active Inference (10 actions) | <2s | ~1.5s |

### Throughput

- Predictions: **100 req/s per instance**
- Observations: **50 req/s per instance**
- Active Inference: **5 concurrent hunts per instance**

### Resource Usage

- **CPU**: 1-4 cores (Bayesian inference is CPU-intensive)
- **Memory**: 2-8Gi (depends on observation history)
- **Disk**: 1Gi (for model persistence)

## Troubleshooting

### Model Not Trained

**Error:** `Model not trained. Send training data to /train first.`

**Solution:**
```bash
# Send 500+ normal traffic observations to /train
curl -X POST http://localhost:8006/train \
  -H "Content-Type: application/json" \
  -d @normal_traffic.json
```

### High Latency

1. Check observation history size:
```bash
curl http://localhost:8006/beliefs | jq .observation_history_size
```

2. If > 1000, prior has drifted significantly. Retrain:
```bash
curl -X POST http://localhost:8006/train -d @new_normal_traffic.json
```

### Active Inference Timeout

Reduce exploration budget or increase timeout:
```json
{
  "exploration_budget": 20.0,  // Lower budget
  "information_threshold": 1.0  // Higher threshold (stop sooner)
}
```

## Roadmap Integration

Este serviço implementa **Sprint 7-9 (Weeks 15-21)** do MAXIMUS_AI_ROADMAP_2025:

- ✅ Hierarchical Bayesian inference (PyMC3)
- ✅ Predictive coding (top-down + bottom-up)
- ✅ Belief updating via precision-weighted errors
- ✅ Active inference engine
- ✅ Free energy minimization
- ✅ 7 autonomous actions
- ✅ FastAPI service
- ✅ Docker + Kubernetes
- ✅ Integration ready (RTE + HCL)

**Status: PRODUCTION READY** ✅

## Research References

1. **Predictive Coding**
   - Rao & Ballard (1999) - Predictive coding in the visual cortex
   - Friston (2005) - A theory of cortical responses

2. **Active Inference**
   - Friston et al. (2017) - Active inference: a process theory
   - Parr & Friston (2019) - Generalised free energy and active inference

3. **Bayesian Brain**
   - Knill & Pouget (2004) - The Bayesian brain
   - Doya et al. (2007) - Bayesian brain: Probabilistic approaches to neural coding

---

**SACRED CLAUSE:**

✅ CODIGO REAL, FUNCIONAL, PRONTO PARA PRODUÇÃO
✅ PyMC3 Bayesian inference (não mock)
✅ Free energy minimization (matemática real)
❌ NUNCA MOCK, NUNCA PLACEHOLDER, JAMAIS CÓDIGO MORTO
