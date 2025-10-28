# Dashboard Mapping - Métricas para Painéis

**Autor**: Juan Carlo de Souza (JuanCS-DEV @github)  
**Email**: juan.brainfarma@gmail.com  
**Data**: 2024-10-08  
**Status**: Production v1.0

---

## Visão Geral

Este documento mapeia as métricas de telemetria para os dashboards Grafana existentes, especificando quais métricas alimentam cada painel e como são visualizadas.

## Dashboards Existentes

1. **maximus-ai-neural-architecture** - Arquitetura neural e consciência
2. **vertice_overview** - Visão geral da plataforma
3. **consciousness_safety_overview** - Safety e consciência

---

## 1. Dashboard: maximus-ai-neural-architecture

**Arquivo**: `monitoring/grafana/dashboards/maximus-ai-neural-architecture.json`

### Painel: Consciousness Metrics

| Métrica | Fonte | Visualização | Refresh | Alerta |
|---------|-------|--------------|---------|--------|
| `arousal_level` | Prometheus | Time Series | 1s | > 0.9 (5min) |
| `dopamine_spike_events` | Kafka | Event List | real-time | spike_magnitude > 3.0 |
| `consciousness.esgt.ignition` | NATS | Heatmap | real-time | coherence < 0.7 |

**Queries**:
```promql
# Arousal Level
max(maximus_arousal_level) by (instance)

# Dopamine Average
rate(maximus_dopamine_spike_events_total[5m])

# ESGT Frequency
rate(maximus_esgt_ignition_events_total[1m])
```

### Painel: Phi Proxy & Coherence

| Métrica | Fonte | Visualização | Refresh | Alert |
|---------|-------|--------------|---------|-------|
| `phi_proxy` | NATS (esgt events) | Gauge | 5s | < 0.8 |
| `coherence` | NATS (esgt events) | Time Series | 5s | < 0.7 |
| `synchronization_quality.jitter_ns` | NATS | Stat | 5s | > 100 |

**Queries**:
```promql
# Phi Proxy Latest
last_over_time(maximus_phi_proxy[30s])

# Coherence Trend
avg_over_time(maximus_coherence[5m])

# Sync Quality
maximus_sync_jitter_nanoseconds
```

### Painel: Neural Activity

| Métrica | Fonte | Visualização | Refresh | Alert |
|---------|-------|--------------|---------|-------|
| `participating_nodes` | NATS | Node Graph | real-time | - |
| `broadcast_content` | NATS | Table | real-time | salience > 0.9 |
| `energy_consumption` | NATS | Bar Gauge | 5s | > 80 |

---

## 2. Dashboard: vertice_overview

**Arquivo**: `monitoring/grafana/dashboards/vertice_overview.json`

### Painel: System Health

| Métrica | Fonte | Visualização | Refresh | Alert |
|---------|-------|--------------|---------|-------|
| `http_requests_total` | Prometheus | Graph | 15s | error_rate > 0.05 |
| `session.latency` | OTel | Histogram | 10s | p95 > 500ms |
| `stream.connected_clients` | Custom Exporter | Stat | 5s | - |

**Queries**:
```promql
# Request Rate
rate(http_requests_total[5m])

# Error Rate
rate(http_requests_total{status=~"5.."}[5m]) /
rate(http_requests_total[5m])

# Session Latency P95
histogram_quantile(0.95, 
  rate(vcli_session_latency_bucket[5m]))

# Connected Clients
stream_connected_clients_total
```

### Painel: Service Status

| Métrica | Fonte | Visualização | Refresh | Alert |
|---------|-------|--------------|---------|-------|
| `command.executed` | OTel | Counter | 10s | rate < 1 |
| `alert.generated` | HSAS | Event List | real-time | priority=critical |
| `alert.acked` | HSAS | Table | real-time | ack_delay > 5min |

**Queries**:
```promql
# Commands Executed
rate(vcli_command_executed_total[1m])

# Alerts Generated
increase(hsas_alert_generated_total[5m])

# Alert Ack Time
hsas_alert_ack_delay_seconds
```

---

## 3. Dashboard: consciousness_safety_overview

**Arquivo**: `monitoring/grafana/dashboards/consciousness_safety_overview.json`

### Painel: Safety Metrics

| Métrica | Fonte | Visualização | Refresh | Alert |
|---------|-------|--------------|---------|-------|
| `safety.kill_switch_latency` | Prometheus | Gauge | 10s | > 100ms |
| `consciousness.esgt.ignition` | NATS | Status History | real-time | ignition_failure |

**Queries**:
```promql
# Kill Switch Latency
maximus_kill_switch_latency_milliseconds

# Kill Switch Activations
increase(maximus_kill_switch_activations_total[1h])

# ESGT Ignition Success Rate
rate(maximus_esgt_ignition_events_total{type="full_ignition"}[5m]) /
rate(maximus_esgt_ignition_events_total[5m])
```

### Painel: Neuromodulation

| Métrica | Fonte | Visualização | Refresh | Alert |
|---------|-------|--------------|---------|-------|
| `dopamine_spike_events` | gRPC/Kafka | Event Timeline | real-time | abnormal_pattern |
| `arousal_level` | Prometheus | Time Series | 1s | extreme_values |

**Queries**:
```promql
# Dopamine Spike Rate
rate(maximus_dopamine_spike_events_total[1m])

# Dopamine Level Average
avg_over_time(maximus_dopamine_level[5m])

# Arousal vs Dopamine Correlation
(maximus_arousal_level * maximus_dopamine_level)
```

---

## 4. Dashboard: Frontend Performance (Planejado)

**Arquivo**: `monitoring/grafana/dashboards/frontend-performance.json` (a criar)

### Painel: User Experience

| Métrica | Fonte | Visualização | Refresh | Alert |
|---------|-------|--------------|---------|-------|
| `dashboard.render_time` | Web Vitals | Histogram | 30s | p95 > 3s |
| `ws.messages_rate` | WebSocket Client | Graph | 5s | rate > 100/s |
| `stream.connected_clients` | Custom Exporter | Table | 5s | by_service |

**Queries**:
```promql
# Dashboard Render Time P95
histogram_quantile(0.95,
  rate(frontend_dashboard_render_time_bucket[5m]))

# WebSocket Message Rate
rate(frontend_ws_messages_total[1m])

# Connections by Service
stream_connected_clients_total{service!=""}
```

---

## Alertas Configurados

### Consciousness Alerts

```yaml
- alert: LowConsciousnessCoherence
  expr: maximus_coherence < 0.7
  for: 5m
  labels:
    severity: warning
    component: consciousness
  annotations:
    summary: "Consciousness coherence below threshold"
    description: "Coherence {{ $value }} for 5 minutes"

- alert: HighPhiProxyDrop
  expr: rate(maximus_phi_proxy[5m]) < -0.1
  for: 2m
  labels:
    severity: critical
    component: consciousness
  annotations:
    summary: "Rapid drop in Phi proxy"
    description: "Phi proxy dropping {{ $value }}/s"

- alert: KillSwitchLatencyHigh
  expr: maximus_kill_switch_latency_milliseconds > 100
  for: 1m
  labels:
    severity: critical
    component: safety
  annotations:
    summary: "Kill switch latency above 100ms"
    description: "Current latency: {{ $value }}ms"
```

### Performance Alerts

```yaml
- alert: HighErrorRate
  expr: |
    rate(http_requests_total{status=~"5.."}[5m]) /
    rate(http_requests_total[5m]) > 0.05
  for: 5m
  labels:
    severity: warning
    component: gateway
  annotations:
    summary: "High error rate detected"
    description: "Error rate: {{ $value | humanizePercentage }}"

- alert: HighSessionLatency
  expr: |
    histogram_quantile(0.95,
      rate(vcli_session_latency_bucket[5m])) > 0.5
  for: 10m
  labels:
    severity: warning
    component: vcli
  annotations:
    summary: "High session latency"
    description: "P95 latency: {{ $value }}s"
```

---

## 4. Dashboard: consciousness_overview

**Arquivo**: `monitoring/grafana/dashboards/consciousness_overview.json`

| Seção | Métrica | Query PromQL | Visualização |
|-------|---------|--------------|--------------|
| Arousal | `maximus_arousal_level` | `max(maximus_arousal_level{environment=~"$environment"})` | Gauge |
| Arousal | `maximus_arousal_baseline` | `avg(maximus_arousal_baseline{environment=~"$environment"})` | Time Series |
| Health | `maximus_phi_proxy` | `avg(maximus_phi_proxy{environment=~"$environment"})` | Stat |
| TIG | `maximus_tig_nodes_active` | `max(maximus_tig_nodes_active{environment=~"$environment"})` | Time Series |
| TIG | `maximus_tig_connectivity_ratio` | `avg(maximus_tig_connectivity_ratio{environment=~"$environment"})` | Time Series |
| ESGT | `maximus_esgt_success_ratio` | `avg(maximus_esgt_success_ratio{environment=~"$environment"})` | Time Series |
| ESGT | `maximus_esgt_avg_coherence` | `avg(maximus_esgt_avg_coherence{environment=~"$environment"})` | Time Series |
| Eventos | `consciousness_event_total` | `topk(10, increase(consciousness_event_total{environment=~"$environment"}[10m]))` | Table |

---

## 5. Dashboard: esgt_deep_dive

**Arquivo**: `monitoring/grafana/dashboards/esgt_deep_dive.json`

| Seção | Métrica | Query PromQL | Visualização |
|-------|---------|--------------|--------------|
| Success vs Failure | Success Ratio | `avg(maximus_esgt_success_ratio{environment=~"$environment"})` | Time Series |
| Success vs Failure | Failure Ratio | `1 - avg(maximus_esgt_success_ratio{environment=~"$environment"})` | Time Series |
| Failure Reasons | `maximus_esgt_failure_total` | `sum by (failure_reason) (increase(maximus_esgt_failure_total{environment=~"$environment"}[10m]))` | Pie |
| Salience | `maximus_esgt_salience_component_bucket` | `histogram_quantile(0.5, sum by (le) (rate(maximus_esgt_salience_component_bucket{environment=~"$environment"}[5m])))` | Heatmap |
| Coherence | `maximus_esgt_coherence` | `avg(maximus_esgt_coherence{environment=~"$environment"})` | Time Series |
| Duration | `maximus_esgt_duration_seconds_bucket` | `histogram_quantile(0.95, sum by (le) (rate(maximus_esgt_duration_seconds_bucket{environment=~"$environment"}[5m])))` | Time Series |

---

## 6. Dashboard: arousal_dynamics

**Arquivo**: `monitoring/grafana/dashboards/arousal_dynamics.json`

| Seção | Métrica | Query PromQL | Visualização |
|-------|---------|--------------|--------------|
| Timeline | `maximus_arousal_level` | `max(maximus_arousal_level{environment=~"$environment"})` | Time Series |
| Timeline | `maximus_arousal_baseline` | `avg(maximus_arousal_baseline{environment=~"$environment"})` | Time Series |
| Time in State | `maximus_arousal_state_seconds_total` | `increase(maximus_arousal_state_seconds_total{environment=~"$environment",state="STATE"}[1h])` | Bar Gauge |
| Transitions | `maximus_arousal_state_transition_total` | `sum by (transition) (increase(maximus_arousal_state_transition_total{environment=~"$environment"}[30m]))` | Time Series |
| Needs vs Stress | `maximus_arousal_component_need_ratio` | `avg(maximus_arousal_component_need_ratio{environment=~"$environment"})` | Time Series |
| Needs vs Stress | `maximus_arousal_component_stress_ratio` | `avg(maximus_arousal_component_stress_ratio{environment=~"$environment"})` | Time Series |

---

## Variables Globais

Todas as dashboards devem incluir:

```json
{
  "templating": {
    "list": [
      {
        "name": "environment",
        "type": "query",
        "query": "label_values(environment)",
        "current": "prod"
      },
      {
        "name": "service",
        "type": "query",
        "query": "label_values(service_name)",
        "multi": true
      },
      {
        "name": "interval",
        "type": "interval",
        "options": ["1s", "5s", "10s", "30s", "1m", "5m"],
        "current": "5s"
      }
    ]
  }
}
```

---

## Annotations

### Deploy Events
```json
{
  "datasource": "Prometheus",
  "expr": "changes(service_version_info[1m]) > 0",
  "tagKeys": "service,version",
  "titleFormat": "Deploy",
  "textFormat": "{{ service }} → {{ version }}"
}
```

### Consciousness Events
```json
{
  "datasource": "NATS",
  "stream": "consciousness.events",
  "filter": "type:esgt_ignition",
  "titleFormat": "ESGT Ignition",
  "textFormat": "Type: {{ ignition_type }}, Coherence: {{ coherence }}"
}
```

### Alert Annotations
```json
{
  "datasource": "Alertmanager",
  "tags": ["consciousness", "safety"],
  "titleFormat": "{{ alertname }}",
  "textFormat": "{{ annotations.description }}"
}
```

---

## Próximas Melhorias

### Curto Prazo
1. ⏳ Adicionar dashboard específico de Frontend Performance
2. ⏳ Implementar annotations de eventos de consciência
3. ⏳ Criar alertas para dopamine spikes anormais
4. ⏳ Dashboard de correlação arousal-dopamine

### Médio Prazo
5. ⏳ Dashboard de network topology com métricas
6. ⏳ Implementar distributed tracing view
7. ⏳ Dashboard de skill learning progression
8. ⏳ Real-time consciousness cycle visualization

---

## Comandos Úteis

### Exportar Dashboard
```bash
# Export single dashboard
curl -u admin:password \
  http://localhost:3000/api/dashboards/uid/maximus-neural \
  | jq '.dashboard' > maximus-ai-neural-architecture.json

# Export all dashboards
for uid in $(curl -u admin:password \
  http://localhost:3000/api/search?type=dash-db \
  | jq -r '.[].uid'); do
  curl -u admin:password \
    "http://localhost:3000/api/dashboards/uid/$uid" \
    | jq '.dashboard' > "${uid}.json"
done
```

### Importar Dashboard
```bash
# Import dashboard
curl -X POST -H "Content-Type: application/json" \
  -d @dashboard.json \
  http://localhost:3000/api/dashboards/db
```

### Validar Queries
```bash
# Test PromQL query
curl -G http://localhost:9090/api/v1/query \
  --data-urlencode 'query=maximus_arousal_level' \
  | jq '.data.result'
```

---

**Versão**: 1.0  
**Última Atualização**: 2024-10-08  
**Compliance**: Doutrina Vértice ✅
