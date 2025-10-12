# PRÓXIMOS PASSOS - Defensive AI Security Tools
## Roadmap para Completar Implementação

**Data**: 2025-10-12  
**Status Atual**: 90% Completo ✅  
**Próxima Sessão**: Ajustes + Integração E2E

---

## SESSÃO 1 (HOJE - CONCLUÍDA) ✅

### Conquistas
- ✅ 6 componentes defensivos core implementados
- ✅ 239 testes passando (74% coverage)
- ✅ 4 playbooks YAML configurados
- ✅ LLM honeypots operacionais
- ✅ Documentação completa

---

## SESSÃO 2 (PRÓXIMA) - Ajustes e Integração

### Objetivo
Atingir 85% coverage e validar integração E2E completa.

### Tarefas Prioritárias

#### 1. Ajustar Testes (1h)
```bash
# Revisar e corrigir testes que falharam
cd backend/services/active_immune_core

# Ajustar test_behavioral_analyzer.py
# - Alinhar com API real (sem behavior_type param)
# - Ajustar AnomalyDetection fields (explanation, confidence)

# Ajustar test_encrypted_traffic_analyzer.py  
# - Verificar EncryptedTrafficAnalyzer.__init__() signature
# - Ajustar FlowFeatureExtractor method names

# Executar
pytest tests/detection/test_behavioral_analyzer.py -v
pytest tests/detection/test_encrypted_traffic_analyzer.py -v

# Target: 100% tests passing
```

#### 2. Completar TODOs Críticos (1h 30min)
```python
# response/automated_response.py
# TODO: Linha 737 - Integrar firewall API
# TODO: Linha 750 - Integrar DNS firewall  
# TODO: Linha 763 - Integrar network segmentation
# TODO: Linha 776 - Integrar HoneypotOrchestrator
# TODO: Linha 792 - Integrar traffic shaping
# TODO: Linha 806 - Integrar SOC notifications

# detection/sentinel_agent.py
# TODO: Linha 741 - Asset management integration
# TODO: Linha 746 - Network monitoring integration

# intelligence/fusion_engine.py
# TODO: Implementar connectors faltantes
```

#### 3. Testes de Integração E2E (1h)
```python
# Criar: tests/integration/test_defense_pipeline_e2e.py

async def test_complete_defense_pipeline():
    """Test SecurityEvent → Detection → Response → Containment"""
    
    # 1. Inject security event
    event = SecurityEvent(
        event_type="brute_force",
        source_ip="203.0.113.42"
    )
    
    # 2. Sentinel detects
    detection = await sentinel.analyze_event(event)
    assert detection.is_threat
    
    # 3. Fusion enriches
    enriched = await fusion.correlate_indicators(detection.iocs)
    assert enriched.threat_actor is not None
    
    # 4. Response executes playbook
    execution = await response.execute_playbook(
        "brute_force_response",
        context={"event": event, "threat": enriched}
    )
    assert execution.status == "success"
    
    # 5. Validate honeypot deployed
    assert honeypot_manager.get_active_count() > 0
    
    # 6. Validate metrics
    assert sentinel.detections_total._value.get() > 0
```

#### 4. Validar Kafka Integration (30min)
```python
# Testar consumers/producers
# orchestration/test_kafka_integration.py

async def test_kafka_event_flow():
    """Test event flow through Kafka"""
    
    # Produce event
    await producer.send("security.events", event)
    
    # Consume and process
    defense_response = await orchestrator.process_security_event(event)
    
    # Verify alert published
    alert = await consumer.read("defense.alerts")
    assert alert.event_id == event.event_id
```

### Deliverables Sessão 2
- ✅ 100% tests passing
- ✅ ≥85% coverage
- ✅ E2E pipeline validated
- ✅ Kafka integration working
- ✅ All critical TODOs resolved

---

## SESSÃO 3 - ML Model Training

### Objetivo
Treinar modelos ML para Encrypted Traffic Analyzer.

### Tarefas

#### 1. Dataset Preparation (1h)
```bash
# Download CICIDS2017 dataset
wget https://www.unb.ca/cic/datasets/ids-2017.html

# Extract features
python scripts/prepare_cicids_dataset.py \
  --input cicids2017/ \
  --output data/ml/cicids_features.pkl
```

#### 2. Train C2 Beaconing Detector (1h)
```python
# scripts/train_c2_detector.py

from sklearn.ensemble import RandomForestClassifier

# Load dataset
X_train, y_train = load_cicids_data("c2_beaconing")

# Train
model = RandomForestClassifier(
    n_estimators=100,
    max_depth=20,
    class_weight='balanced'
)
model.fit(X_train, y_train)

# Evaluate
accuracy = model.score(X_test, y_test)
print(f"C2 Detection Accuracy: {accuracy:.2%}")

# Save
joblib.dump(model, "models/c2_detector.pkl")
```

#### 3. Train Exfiltration Detector (1h 30min)
```python
# scripts/train_exfil_detector.py

import tensorflow as tf
from tensorflow.keras import layers

# LSTM for temporal patterns
model = tf.keras.Sequential([
    layers.LSTM(64, return_sequences=True, input_shape=(seq_len, features)),
    layers.Dropout(0.2),
    layers.LSTM(32),
    layers.Dropout(0.2),
    layers.Dense(16, activation='relu'),
    layers.Dense(1, activation='sigmoid')
])

model.compile(
    optimizer='adam',
    loss='binary_crossentropy',
    metrics=['accuracy', 'precision', 'recall']
)

# Train
history = model.fit(
    X_train, y_train,
    epochs=50,
    batch_size=32,
    validation_split=0.2
)

model.save("models/exfil_detector.h5")
```

#### 4. Train Malware Classifier (1h)
```python
# scripts/train_malware_classifier.py

from xgboost import XGBClassifier

model = XGBClassifier(
    n_estimators=100,
    learning_rate=0.1,
    max_depth=6,
    subsample=0.8
)

model.fit(X_train, y_train)
joblib.dump(model, "models/malware_classifier.pkl")
```

### Deliverables Sessão 3
- ✅ 3 modelos treinados (C2, Exfil, Malware)
- ✅ Accuracy ≥90% em test set
- ✅ Models deployed em production
- ✅ Performance benchmarks documentados

---

## SESSÃO 4 - Adversarial ML Defense

### Objetivo
Implementar defesas contra ataques a modelos ML (MITRE ATLAS).

### Tarefas

#### 1. Model Poisoning Detection (1h)
```python
# detection/adversarial_defense.py

class ModelPoisoningDetector:
    """Detect poisoned training data."""
    
    def detect_poisoning(self, training_data):
        # Analyze data distribution
        # Detect statistical anomalies
        # Flag suspicious samples
        pass
```

#### 2. Adversarial Input Detection (1h)
```python
class AdversarialInputDetector:
    """Detect crafted inputs to evade models."""
    
    def is_adversarial(self, input_features):
        # Check feature bounds
        # Validate statistical properties
        # Compare with baseline
        pass
```

#### 3. Model Hardening (1h)
```python
# Adversarial training
# Input sanitization
# Ensemble methods
```

### Deliverables Sessão 4
- ✅ ATLAS defenses implemented
- ✅ Adversarial detection ≥85% accuracy
- ✅ Models hardened against evasion

---

## SESSÃO 5 - Learning Loop

### Objetivo
Sistema aprende e adapta defesas automaticamente.

### Tarefas

#### 1. Attack Signature Extraction (B-cells) (1h 30min)
```python
class AttackSignatureExtractor:
    """Extract reusable signatures from attacks."""
    
    def extract_signature(self, attack_events):
        # Pattern mining
        # Signature generation
        # Memory B-cell creation
        pass
```

#### 2. Defense Strategy Optimization (RL) (2h)
```python
class DefenseStrategyOptimizer:
    """RL-based playbook optimization."""
    
    def optimize_playbook(self, playbook, outcomes):
        # Success rate analysis
        # Parameter tuning
        # Strategy evolution
        pass
```

### Deliverables Sessão 5
- ✅ Automatic signature extraction
- ✅ RL-based optimization
- ✅ Improved response times

---

## SESSÃO 6 - Production Deployment

### Objetivo
Deploy completo em produção.

### Tarefas

#### 1. Docker Compose Update (30min)
```yaml
# docker-compose.defense.yml

services:
  defense-orchestrator:
    build: ./backend/services/active_immune_core
    environment:
      - MODE=orchestrator
      - KAFKA_BROKERS=kafka:9092
    depends_on:
      - kafka
      - postgres
      - redis
  
  sentinel-agent:
    build: ./backend/services/active_immune_core
    environment:
      - MODE=sentinel
      - OPENAI_API_KEY=${OPENAI_API_KEY}
  
  # ... outros serviços
```

#### 2. Kubernetes Deployment (1h)
```yaml
# k8s/defense-orchestrator-deployment.yaml
```

#### 3. Monitoring Setup (1h)
```
# Grafana dashboards
# Prometheus alerts
# Log aggregation (ELK)
```

### Deliverables Sessão 6
- ✅ Production deployment
- ✅ Monitoring dashboards
- ✅ Alerting configured
- ✅ Runbook documented

---

## CRONOGRAMA SUGERIDO

```
Semana 1:
├── Seg: Sessão 2 (Ajustes + E2E) - 4h
├── Ter: Sessão 3 (ML Training) - 4h  
├── Qua: Sessão 4 (Adversarial) - 3h
├── Qui: Sessão 5 (Learning Loop) - 4h
└── Sex: Sessão 6 (Deployment) - 3h

Total: 18h (distribuído em 5 dias)
```

---

## COMMANDS RÁPIDOS

### Executar Testes
```bash
cd backend/services/active_immune_core

# Todos os testes
pytest -v --cov=. --cov-report=html

# Apenas defensive
pytest tests/detection tests/intelligence tests/response tests/containment -v

# Com coverage
pytest --cov=detection --cov=intelligence --cov=response --cov=containment --cov-report=term-missing
```

### Executar Componentes
```bash
# Sentinel Agent
python -m detection.sentinel_agent

# Defense Orchestrator
python -m orchestration.defense_orchestrator

# LLM Honeypot
python -m containment.honeypots --type ssh --llm-enabled
```

### Deploy Local
```bash
# Build
docker-compose -f docker-compose.defense.yml build

# Up
docker-compose -f docker-compose.defense.yml up -d

# Logs
docker-compose -f docker-compose.defense.yml logs -f defense-orchestrator
```

---

## MÉTRICAS DE SUCESSO FINAL

### Quando considerar COMPLETO:
```
✅ Tests: 100% passing
✅ Coverage: ≥85%
✅ E2E: Pipeline completo validado
✅ ML Models: Treinados e deployed
✅ Adversarial: ATLAS defenses implemented
✅ Learning: Automatic adaptation working
✅ Production: Deployed e monitorado
✅ Documentation: Completa e atualizada
```

---

**Constância e Disciplina.**  
**Um pé atrás do outro.**  
**Para Glória Dele.** 🙏

---

**Arquivo**: NEXT-STEPS-DEFENSIVE-SECURITY.md  
**Data**: 2025-10-12  
**Status**: ROADMAP ATIVO 🚀
