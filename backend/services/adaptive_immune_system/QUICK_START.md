# 🚀 QUICK START - Adaptive Immune System Monitoring

**Status**: Production-Ready ✅
**Versão**: 1.0.0
**Data**: 2025-10-13

---

## ⚡ Quick Deploy (5 minutos)

### 1. Instalar Dependências
```bash
cd backend/services/adaptive_immune_system

# Instalar dependências de monitoramento
pip install -r requirements-monitoring.txt
```

### 2. Iniciar Monitoring Stack
```bash
cd monitoring/

# Iniciar todos os serviços
docker-compose -f docker-compose.monitoring.yml up -d

# Verificar status
docker-compose -f docker-compose.monitoring.yml ps
```

### 3. Acessar Interfaces

| Serviço | URL | Credenciais |
|---------|-----|-------------|
| **Prometheus** | http://localhost:9090 | - |
| **Grafana** | http://localhost:3000 | admin / admin |
| **Alertmanager** | http://localhost:9093 | - |
| **Jaeger** | http://localhost:16686 | - |

### 4. Verificar Métricas

```bash
# Verificar endpoint de métricas do HITL API
curl http://localhost:8000/metrics

# Deve retornar métricas Prometheus
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
# ...
```

### 5. Verificar Dashboards

1. Abrir Grafana: http://localhost:3000
2. Login: `admin` / `admin`
3. Ir para: Dashboards → Adaptive Immune System
4. Visualizar:
   - **HITL API - Overview**: Métricas gerais (RED method)
   - **HITL API - SLO**: Tracking de SLOs e error budget

---

## 📊 Dashboards Disponíveis

### HITL API - Overview
**URL**: http://localhost:3000/d/hitl-overview

**Painéis**:
1. Service Status (UP/DOWN)
2. Request Rate (req/s)
3. Error Rate (%)
4. P95 Latency (ms)
5. 30d Availability (%)
6. Request Rate by Endpoint
7. Latency Percentiles (P50/P95/P99)
8. Review Operations
9. Database Connections

**Refresh**: 10s

### HITL API - SLO
**URL**: http://localhost:3000/d/hitl-slo

**Painéis**:
1. Availability SLO (99.9% target)
2. Latency SLO (P95 < 500ms)
3. Error Budget Consumed
4. Error Budget Burn Rate
5. Availability Trend (multi-window)
6. Burn Rate Trend
7. Latency Percentiles
8. Error Rate Breakdown (4xx vs 5xx)
9. SLO Summary Table

**Refresh**: 30s

---

## 🔔 Alertas Configurados

### Critical (PagerDuty + Slack)
1. **HighErrorRate**: > 1% por 5 min
2. **HighLatency**: P95 > 1000ms por 5 min
3. **ServiceDown**: service_up == 0 por 1 min
4. **DatabaseConnectionPoolExhaustion**: sem conexões disponíveis
5. **LowAvailability**: < 95% por 5 min

### Warning (Slack)
1. **ElevatedErrorRate**: > 0.5% por 10 min
2. **ElevatedLatency**: P95 > 500ms por 10 min
3. **ErrorBudgetBurningFast**: burn_rate > 2x por 1h
4. **HighDatabaseErrors**: > 10 erros por 5 min
5. **LowCacheHitRatio**: < 80% por 15 min
6. **HighCacheEvictionRate**: > 100 evictions/s

### SLO Alerts
1. **AvailabilitySLOBreach**: < 99.9% por 5 min
2. **LatencySLOBreach**: P95 > 500ms por 5 min
3. **ErrorBudgetLow**: < 10% restante

---

## 🎯 SLO Definitions

### Availability
- **Target**: 99.9% (30d rolling)
- **Error Budget**: 43.2 min/month
- **Query**: `(sum(rate(http_requests_total{status!~"5.."}[30d])) / sum(rate(http_requests_total[30d]))) * 100`

### Latency
- **Target**: P95 < 500ms (7d rolling)
- **Error Budget**: 5% of requests
- **Query**: `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[7d]))`

### Error Rate
- **Target**: < 0.1% (24h rolling)
- **Error Budget**: 0.1% of requests
- **Query**: `(sum(rate(http_requests_total{status=~"5.."}[24h])) / sum(rate(http_requests_total[24h]))) * 100`

---

## 🔍 PromQL Query Examples

### Request Rate
```promql
# Total request rate (req/s)
sum(rate(http_requests_total[5m]))

# Request rate by endpoint
sum(rate(http_requests_total[5m])) by (endpoint)

# Request rate by method
sum(rate(http_requests_total[5m])) by (method)
```

### Error Rate
```promql
# Error rate (percentage)
(sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))) * 100

# 4xx rate
(sum(rate(http_requests_total{status=~"4.."}[5m])) / sum(rate(http_requests_total[5m]))) * 100
```

### Latency
```promql
# P50 latency
histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))

# P95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# P99 latency
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))
```

### Business Metrics
```promql
# Review creation rate
sum(rate(review_created_total[5m]))

# Review decision rate by decision
sum(rate(review_decision_total[5m])) by (decision)

# APV validation rate by result
sum(rate(apv_validation_total[5m])) by (result)
```

### System Metrics
```promql
# Database connections
db_connections_active
db_connections_idle

# Cache hit ratio
cache_hit_ratio

# Database query duration P95
histogram_quantile(0.95, rate(db_query_duration_seconds_bucket[5m]))
```

---

## 🐛 Troubleshooting

### Prometheus não coleta métricas do HITL API

**Problema**: Dashboard vazio, sem dados

**Solução**:
```bash
# 1. Verificar se HITL API está rodando
curl http://localhost:8000/health

# 2. Verificar endpoint de métricas
curl http://localhost:8000/metrics

# 3. Verificar targets no Prometheus
# Abrir: http://localhost:9090/targets
# Status deve ser "UP" para hitl-api

# 4. Verificar logs do Prometheus
docker logs prometheus
```

### Grafana não mostra dashboards

**Problema**: Dashboards não aparecem

**Solução**:
```bash
# 1. Verificar provisioning
docker exec grafana ls -la /etc/grafana/provisioning/dashboards/

# 2. Verificar logs do Grafana
docker logs grafana

# 3. Reimportar dashboards manualmente
# Grafana UI → Dashboards → Import
# Selecionar: monitoring/grafana/dashboards/hitl-overview.json
```

### Alertmanager não envia notificações

**Problema**: Alertas não chegam no Slack/Email

**Solução**:
```bash
# 1. Verificar configuração do Alertmanager
docker exec alertmanager cat /etc/alertmanager/alertmanager.yml

# 2. Verificar logs
docker logs alertmanager

# 3. Testar webhook manualmente
curl -X POST http://localhost:9093/api/v1/alerts \
  -H 'Content-Type: application/json' \
  -d '[{"labels":{"alertname":"TestAlert","severity":"warning"},"annotations":{"summary":"Test"}}]'

# 4. Verificar receivers configurados
# Alertmanager UI → http://localhost:9093
```

### Jaeger não mostra traces

**Problema**: Nenhum trace aparece no Jaeger

**Solução**:
```bash
# 1. Verificar se tracing está inicializado
# No código Python:
from hitl.monitoring import setup_tracing
setup_tracing(jaeger_host="localhost", jaeger_port=6831)

# 2. Verificar logs do Jaeger
docker logs jaeger

# 3. Verificar se porta 6831 está acessível
nc -zv localhost 6831

# 4. Gerar tráfego para criar traces
for i in {1..10}; do curl http://localhost:8000/health; done
```

---

## 🔧 Comandos Úteis

### Docker Compose
```bash
# Iniciar stack
docker-compose -f docker-compose.monitoring.yml up -d

# Parar stack
docker-compose -f docker-compose.monitoring.yml down

# Reiniciar serviço específico
docker-compose -f docker-compose.monitoring.yml restart prometheus

# Ver logs
docker-compose -f docker-compose.monitoring.yml logs -f prometheus

# Verificar recursos
docker stats
```

### Prometheus
```bash
# Reload config (sem restart)
curl -X POST http://localhost:9090/-/reload

# Health check
curl http://localhost:9090/-/healthy

# Check targets
curl http://localhost:9090/api/v1/targets
```

### Grafana
```bash
# Resetar senha admin
docker exec -it grafana grafana-cli admin reset-admin-password newpassword

# Listar datasources
curl -u admin:admin http://localhost:3000/api/datasources

# Listar dashboards
curl -u admin:admin http://localhost:3000/api/search
```

### Alertmanager
```bash
# Reload config
curl -X POST http://localhost:9093/-/reload

# Silenciar alerta
curl -X POST http://localhost:9093/api/v1/silences \
  -H 'Content-Type: application/json' \
  -d '{"matchers":[{"name":"alertname","value":"HighErrorRate"}],"startsAt":"2025-10-13T12:00:00Z","endsAt":"2025-10-13T13:00:00Z","createdBy":"operator","comment":"Maintenance window"}'
```

---

## 📚 Documentation Links

### FASE 3.12 - CI/CD Pipeline
- [FASE_3.12_CI_CD_PIPELINE_PLAN.md](./FASE_3.12_CI_CD_PIPELINE_PLAN.md)
- [FASE_3.12_CI_CD_PIPELINE_COMPLETE.md](./FASE_3.12_CI_CD_PIPELINE_COMPLETE.md)

### FASE 3.13 - Advanced Monitoring
- [FASE_3.13_ADVANCED_MONITORING_PLAN.md](./FASE_3.13_ADVANCED_MONITORING_PLAN.md)
- [FASE_3.13_ADVANCED_MONITORING_COMPLETE.md](./FASE_3.13_ADVANCED_MONITORING_COMPLETE.md)

### Validation
- [VALIDATION_REPORT.md](./VALIDATION_REPORT.md)

### External Resources
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)
- [Google SRE Book - SLOs](https://sre.google/sre-book/service-level-objectives/)

---

## ✅ Health Check Checklist

Após deployment, verificar:

- [ ] Prometheus coleta métricas (`http://localhost:9090/targets`)
- [ ] Grafana carrega datasource Prometheus
- [ ] Dashboard "HITL API - Overview" mostra dados
- [ ] Dashboard "HITL API - SLO" mostra SLOs
- [ ] Alertmanager está UP (`http://localhost:9093`)
- [ ] Jaeger coleta traces (`http://localhost:16686`)
- [ ] HITL API exporta métricas (`/metrics`)
- [ ] Pelo menos 1 alerta configurado está visível

---

## 🎯 Next Steps

### Development
1. Adicionar custom metrics para regras de negócio específicas
2. Criar dashboards customizados por feature
3. Implementar distributed tracing em funções críticas

### Production
1. Configurar PagerDuty integration (substituir service key)
2. Configurar Slack webhooks (substituir URLs)
3. Configurar Email SMTP (substituir credenciais)
4. Habilitar TLS para Prometheus/Grafana
5. Configurar OAuth/LDAP no Grafana
6. Implementar Prometheus HA (2+ replicas)
7. Adicionar Thanos para long-term storage

### Runbooks
1. Criar runbook para cada alerta crítico
2. Documentar procedimentos de incident response
3. Estabelecer processo de SLO review (mensal)

---

**🎉 Monitoring stack pronto para uso! Qualquer dúvida, consultar [VALIDATION_REPORT.md](./VALIDATION_REPORT.md)**
