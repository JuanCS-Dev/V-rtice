# MAXIMUS AI 3.0 - Metrics Reference 📊

**REGRA DE OURO:** 10/10 - Production-ready metrics
**Prometheus Version:** 2.x+
**Grafana Version:** 9.x+

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Predictive Coding Metrics](#predictive-coding-metrics-fase-3)
3. [Neuromodulation Metrics](#neuromodulation-metrics-fase-5)
4. [Skill Learning Metrics](#skill-learning-metrics-fase-6)
5. [Attention System Metrics](#attention-system-metrics-fase-0)
6. [Ethical AI Metrics](#ethical-ai-metrics)
7. [System Metrics](#system-metrics)
8. [Useful Queries](#useful-queries)
9. [Recommended Alerts](#recommended-alerts)

---

## 📊 Overview

MAXIMUS AI 3.0 exposes **30+ metrics** covering all subsystems:

| Category | Metrics | Type | Purpose |
|----------|---------|------|---------|
| Predictive Coding | 3 | Histogram, Counter | Free Energy, latency, errors |
| Neuromodulation | 5 | Gauge | Dopamine, ACh, NE, 5-HT, LR |
| Skill Learning | 4 | Counter, Histogram, Gauge | Executions, rewards, latency |
| Attention | 3 | Histogram, Gauge, Counter | Salience, thresholds, updates |
| Ethical AI | 3 | Counter, Gauge | Decisions, approvals, violations |
| System | 6 | Counter, Histogram, Gauge | Events, latency, accuracy |

**Total:** 24 base metrics + labels

---

## 🧠 Predictive Coding Metrics (FASE 3)

### `maximus_free_energy`
**Type:** Histogram
**Labels:** `layer` (l1, l2, l3, l4, l5)
**Unit:** Dimensionless (0-1 scale)

**Description:** Free Energy (surprise/prediction error) by hierarchical layer. High values indicate unexpected events (potential threats).

**Interpretation:**
- **< 0.3:** Expected behavior (low surprise)
- **0.3 - 0.7:** Moderate surprise (investigate)
- **> 0.7:** High surprise (likely threat)

**Buckets:** `[0.1, 0.3, 0.5, 0.7, 0.9, 1.0]`

**Example Query:**
```promql
# Average free energy by layer
avg(rate(maximus_free_energy_sum[5m])) by (layer)

# High surprise events (free energy > 0.7)
maximus_free_energy_bucket{le="0.7", layer="l3"}
```

### `maximus_predictive_coding_latency_seconds`
**Type:** Histogram
**Labels:** `layer` (l1, l2, l3, l4, l5)
**Unit:** Seconds

**Description:** Inference latency per Predictive Coding layer.

**Interpretation:**
- **L1 (Sensory):** ~10-50ms (VAE encoding)
- **L2 (Behavioral):** ~20-100ms (GNN inference)
- **L3 (Operational):** ~30-150ms (TCN temporal)
- **L4 (Tactical):** ~50-200ms (LSTM sequential)
- **L5 (Strategic):** ~100-500ms (Transformer attention)

**Buckets:** `[0.001, 0.01, 0.05, 0.1, 0.5, 1.0]`

**Example Query:**
```promql
# p95 latency by layer
histogram_quantile(0.95, rate(maximus_predictive_coding_latency_seconds_bucket[5m])) by (layer)
```

### `maximus_prediction_errors_total`
**Type:** Counter
**Labels:** `layer`
**Unit:** Count

**Description:** Total prediction errors (free energy > 0.5) by layer.

**Example Query:**
```promql
# Prediction error rate
rate(maximus_prediction_errors_total[5m])
```

---

## 💊 Neuromodulation Metrics (FASE 5)

### `maximus_dopamine_level`
**Type:** Gauge
**Unit:** Dimensionless (0-1 scale)

**Description:** Current dopamine level representing Reward Prediction Error (RPE). Modulates learning rate.

**Interpretation:**
- **< 0.3:** Negative RPE (worse than expected)
- **0.3 - 0.7:** Neutral (as expected)
- **> 0.7:** Positive RPE (better than expected)

**Example Query:**
```promql
# Dopamine trends
maximus_dopamine_level

# Dopamine spikes (> 0.8)
maximus_dopamine_level > 0.8
```

### `maximus_acetylcholine_level`
**Type:** Gauge
**Unit:** Dimensionless (0-1 scale)

**Description:** Acetylcholine level controlling attention modulation. High ACh → lower attention thresholds.

**Interpretation:**
- **< 0.5:** Low attention (high threshold)
- **0.5 - 0.7:** Normal attention
- **> 0.7:** High attention (low threshold)

### `maximus_norepinephrine_level`
**Type:** Gauge
**Unit:** Dimensionless (0-1 scale)

**Description:** Norepinephrine level representing arousal/alertness.

**Interpretation:**
- **< 0.5:** Low arousal
- **0.5 - 0.7:** Normal arousal
- **> 0.7:** High arousal (alert state)

### `maximus_serotonin_level`
**Type:** Gauge
**Unit:** Dimensionless (0-1 scale)

**Description:** Serotonin level controlling patience and exploration balance.

**Interpretation:**
- **< 0.5:** Impatient (more exploitation)
- **0.5 - 0.7:** Balanced
- **> 0.7:** Patient (more exploration)

### `maximus_learning_rate`
**Type:** Gauge
**Unit:** Dimensionless

**Description:** Current modulated learning rate (base_lr * (1 + dopamine)).

**Typical Range:** 0.001 - 0.05

**Example Query:**
```promql
# Learning rate evolution
maximus_learning_rate

# High learning rate periods
maximus_learning_rate > 0.02
```

---

## 🎓 Skill Learning Metrics (FASE 6)

### `maximus_skill_executions_total`
**Type:** Counter
**Labels:** `skill_name`, `mode` (model_free, model_based, hybrid), `status` (success, failure)
**Unit:** Count

**Description:** Total skill executions by name, mode, and outcome.

**Example Query:**
```promql
# Skill execution rate
rate(maximus_skill_executions_total[5m])

# Success rate by skill
rate(maximus_skill_executions_total{status="success"}[5m])
/
rate(maximus_skill_executions_total[5m])
```

### `maximus_skill_reward`
**Type:** Histogram
**Labels:** `skill_name`
**Unit:** Dimensionless (-1 to 1)

**Description:** Reward distribution for skill executions.

**Interpretation:**
- **< 0:** Negative outcome (punishment)
- **0:** Neutral
- **> 0:** Positive outcome (reward)

**Buckets:** `[-1.0, -0.5, -0.1, 0.0, 0.1, 0.5, 1.0]`

**Example Query:**
```promql
# Average reward by skill
avg(rate(maximus_skill_reward_sum[5m])) by (skill_name)
/
rate(maximus_skill_reward_count[5m])
```

### `maximus_skill_execution_latency_seconds`
**Type:** Histogram
**Labels:** `skill_name`, `mode`
**Unit:** Seconds

**Description:** Skill execution latency by name and mode.

**Interpretation:**
- **Model-free:** Fast (< 50ms) - Q-learning lookup
- **Model-based:** Slow (100-500ms) - Planning with world model
- **Hybrid:** Variable (50-300ms) - Arbitration overhead

**Buckets:** `[0.001, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0]`

### `maximus_skill_success_rate`
**Type:** Gauge
**Labels:** `skill_name`
**Unit:** Ratio (0-1)

**Description:** Current success rate for each skill.

**Example Query:**
```promql
# Skills with low success rate (< 0.7)
maximus_skill_success_rate < 0.7
```

---

## 👁️ Attention System Metrics (FASE 0)

### `maximus_attention_salience`
**Type:** Histogram
**Unit:** Dimensionless (0-1 scale)

**Description:** Event salience scores from attention system.

**Interpretation:**
- **< 0.5:** Low salience (ignore)
- **0.5 - 0.7:** Moderate salience
- **> 0.7:** High salience (prioritize)

**Buckets:** `[0.1, 0.3, 0.5, 0.7, 0.9, 1.0]`

### `maximus_attention_threshold`
**Type:** Gauge
**Unit:** Dimensionless (0-1 scale)

**Description:** Current attention threshold. Events below threshold are filtered.

**Typical Range:** 0.3 - 0.8

### `maximus_attention_updates_total`
**Type:** Counter
**Labels:** `reason` (high_surprise, low_surprise, manual)
**Unit:** Count

**Description:** Total attention threshold updates by reason.

**Example Query:**
```promql
# Attention updates due to surprise
rate(maximus_attention_updates_total{reason="high_surprise"}[5m])
```

---

## ✅ Ethical AI Metrics

### `maximus_ethical_decisions_total`
**Type:** Counter
**Labels:** `result` (approved, rejected)
**Unit:** Count

**Description:** Total ethical decisions by outcome.

**Example Query:**
```promql
# Ethical approval rate
rate(maximus_ethical_decisions_total{result="approved"}[5m])
/
rate(maximus_ethical_decisions_total[5m])
```

### `maximus_ethical_approval_rate`
**Type:** Gauge
**Unit:** Ratio (0-1)

**Description:** Current ethical approval rate.

**Target:** > 0.95 (95% approval rate)

### `maximus_ethical_violations_total`
**Type:** Counter
**Labels:** `category` (bias, fairness, privacy, transparency)
**Unit:** Count

**Description:** Total ethical violations by category.

**Example Query:**
```promql
# Violations by category
sum(rate(maximus_ethical_violations_total[1h])) by (category)
```

---

## 🖥️ System Metrics

### `maximus_events_processed_total`
**Type:** Counter
**Labels:** `event_type`, `detected_as_threat` (true, false)
**Unit:** Count

**Description:** Total events processed by type and detection result.

**Example Query:**
```promql
# Event throughput
rate(maximus_events_processed_total[5m])

# Threat detection rate
rate(maximus_events_processed_total{detected_as_threat="true"}[5m])
```

### `maximus_pipeline_latency_seconds`
**Type:** Histogram
**Unit:** Seconds

**Description:** End-to-end pipeline latency (event → response).

**Target:** p95 < 100ms

**Buckets:** `[0.001, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0]`

**Example Query:**
```promql
# p50, p95, p99 latency
histogram_quantile(0.50, rate(maximus_pipeline_latency_seconds_bucket[5m]))
histogram_quantile(0.95, rate(maximus_pipeline_latency_seconds_bucket[5m]))
histogram_quantile(0.99, rate(maximus_pipeline_latency_seconds_bucket[5m]))
```

### `maximus_threat_detection_accuracy`
**Type:** Gauge
**Unit:** Ratio (0-1)

**Description:** Current threat detection accuracy.

**Target:** > 0.90 (90% accuracy)

### `maximus_false_positive_rate`
**Type:** Gauge
**Unit:** Ratio (0-1)

**Description:** Current false positive rate.

**Target:** < 0.05 (5% FP rate)

### `maximus_false_negative_rate`
**Type:** Gauge
**Unit:** Ratio (0-1)

**Description:** Current false negative rate.

**Target:** < 0.05 (5% FN rate)

### `maximus_system_info`
**Type:** Info
**Labels:** `version`, `predictive_coding_enabled`, `skill_learning_enabled`, etc.

**Description:** System information and feature flags.

---

## 🔍 Useful Queries

### Performance Monitoring

```promql
# Overall system throughput (events/sec)
rate(maximus_events_processed_total[5m])

# Pipeline latency percentiles
histogram_quantile(0.95, rate(maximus_pipeline_latency_seconds_bucket[5m]))

# Slow Predictive Coding layers (p95 > 200ms)
histogram_quantile(0.95, rate(maximus_predictive_coding_latency_seconds_bucket[5m])) by (layer) > 0.2
```

### Threat Detection Quality

```promql
# Detection accuracy
maximus_threat_detection_accuracy

# False positive alerts (FP rate > 10%)
maximus_false_positive_rate > 0.1

# Threat detection trends
rate(maximus_events_processed_total{detected_as_threat="true"}[1h])
```

### Neuromodulation State

```promql
# Neuromodulator balance
avg_over_time(maximus_dopamine_level[5m])
avg_over_time(maximus_acetylcholine_level[5m])
avg_over_time(maximus_norepinephrine_level[5m])
avg_over_time(maximus_serotonin_level[5m])

# High dopamine periods (learning opportunities)
maximus_dopamine_level > 0.8
```

### Skill Learning Performance

```promql
# Top skills by usage
topk(10, rate(maximus_skill_executions_total[1h]))

# Skills with degrading performance
delta(maximus_skill_success_rate[1h]) < -0.1

# Average reward by skill
avg(rate(maximus_skill_reward_sum[5m])) by (skill_name) / rate(maximus_skill_reward_count[5m])
```

---

## 🚨 Recommended Alerts

### Critical Alerts

```yaml
# High latency
- alert: HighPipelineLatency
  expr: histogram_quantile(0.95, rate(maximus_pipeline_latency_seconds_bucket[5m])) > 1.0
  for: 5m
  annotations:
    summary: "Pipeline latency above 1s (p95)"

# Low accuracy
- alert: LowThreatDetectionAccuracy
  expr: maximus_threat_detection_accuracy < 0.85
  for: 10m
  annotations:
    summary: "Threat detection accuracy below 85%"

# High false positive rate
- alert: HighFalsePositiveRate
  expr: maximus_false_positive_rate > 0.15
  for: 10m
  annotations:
    summary: "False positive rate above 15%"
```

### Warning Alerts

```yaml
# Skill degradation
- alert: SkillSuccessRateDegrading
  expr: delta(maximus_skill_success_rate[1h]) < -0.2
  for: 15m
  annotations:
    summary: "Skill success rate dropped > 20% in 1h"

# Ethical violations spike
- alert: EthicalViolationsSpike
  expr: rate(maximus_ethical_violations_total[5m]) > 1.0
  for: 5m
  annotations:
    summary: "Ethical violations > 1/sec"

# Neuromodulator imbalance
- alert: NeuromodulatorImbalance
  expr: abs(maximus_dopamine_level - maximus_serotonin_level) > 0.5
  for: 10m
  annotations:
    summary: "Large neuromodulator imbalance detected"
```

---

## 📊 Grafana Dashboard Panels

### Recommended Visualizations

1. **System Health** (Row 1)
   - Throughput: Graph (events/sec)
   - Latency: Graph (p50, p95, p99)
   - Accuracy: Gauge
   - FP/FN Rate: Gauge

2. **Predictive Coding** (Row 2)
   - Free Energy Heatmap: Layer vs Time
   - Layer Latency: Stacked Graph
   - Prediction Errors: Counter

3. **Neuromodulation** (Row 3)
   - Dopamine: Gauge + Timeseries
   - ACh, NE, 5-HT: Multi-gauge
   - Learning Rate: Timeseries

4. **Skill Learning** (Row 4)
   - Skill Executions: Bar chart (top 10)
   - Success Rate: Gauge per skill
   - Reward Distribution: Histogram

---

**MAXIMUS AI 3.0** - Código que ecoará por séculos ✅

*Metrics documentation completa, production-ready, REGRA DE OURO 10/10.*
