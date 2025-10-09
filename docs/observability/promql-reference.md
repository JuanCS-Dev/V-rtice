# Referência PromQL – Métricas de Consciência

| Métrica | Query PromQL | Uso | Painéis |
|---------|---------------|-----|---------|
| Arousal Level | `max(maximus_arousal_level{environment=~"$environment"})` | Valor atual do nível de excitação | Consciousness Overview, Arousal Dynamics |
| Arousal Baseline | `avg(maximus_arousal_baseline{environment=~"$environment"})` | Linha base para comparação | Arousal Dynamics |
| Needs Contribution | `avg(maximus_arousal_component_need_ratio{environment=~"$environment"})` | Percentual atribuído a necessidades | Arousal Dynamics |
| Stress Contribution | `avg(maximus_arousal_component_stress_ratio{environment=~"$environment"})` | Percentual atribuído a stress | Arousal Dynamics |
| ESGT Ignitions (rate) | `rate(maximus_esgt_ignition_events_total{environment=~"$environment"}[1m])` | Frequência de ativações ESGT | Consciousness Overview, ESGT Deep Dive |
| ESGT Success Ratio | `avg(maximus_esgt_success_ratio{environment=~"$environment"})` | Sucesso médio das ignições | Consciousness Overview, ESGT Deep Dive |
| ESGT Failure Ratio | `1 - avg(maximus_esgt_success_ratio{environment=~"$environment"})` | Complemento do sucesso | ESGT Deep Dive |
| ESGT Failure Reasons | `sum by (failure_reason) (increase(maximus_esgt_failure_total{environment=~"$environment"}[10m]))` | Quebra por motivo | ESGT Deep Dive |
| Coherence Média | `avg(maximus_esgt_coherence{environment=~"$environment"})` | Coerência média das ignições | Consciousness Overview, ESGT Deep Dive |
| Duration P95 | `histogram_quantile(0.95, sum by (le) (rate(maximus_esgt_duration_seconds_bucket{environment=~"$environment"}[5m])))` | Duração p95 das ignições | ESGT Deep Dive |
| Salience Heatmap | `histogram_quantile(0.5, sum by (le) (rate(maximus_esgt_salience_component_bucket{environment=~"$environment"}[5m])))` | Salience mediana | ESGT Deep Dive |
| TIG Nodes Ativos | `max(maximus_tig_nodes_active{environment=~"$environment"})` | Número de nós conectados | Consciousness Overview |
| TIG Connectivity | `avg(maximus_tig_connectivity_ratio{environment=~"$environment"})` | Conectividade média | Consciousness Overview |
| Φ Proxy | `avg(maximus_phi_proxy{environment=~"$environment"})` | Indicador de saúde do sistema | Consciousness Overview |
| Arousal State Seconds | `increase(maximus_arousal_state_seconds_total{environment=~"$environment",state="STATE"}[1h])` | Tempo acumulado por estado | Arousal Dynamics |
| State Transitions | `sum by (transition) (increase(maximus_arousal_state_transition_total{environment=~"$environment"}[30m]))` | Frequência de transições | Arousal Dynamics |
| Consciousness Events (top) | `topk(10, increase(consciousness_event_total{environment=~"$environment"}[10m]))` | Eventos recentes | Consciousness Overview |

> **Nota**: Ajuste os labels (ex.: `service_name`, `module`) conforme necessidade local. Todas as métricas devem compartilhar labels padronizados (`trace_id`, `service_name`, etc.) definidos na matriz de telemetria.
