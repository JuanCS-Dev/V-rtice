# Matriz de Telemetria Vértice – v1.0 Production

**Autor**: Juan Carlo de Souza (JuanCS-DEV @github)  
**Email**: juan.brainfarma@gmail.com  
**Data**: 2024-10-08  
**Status**: ✅ Production Ready

## Métricas e Eventos Catalogados

| Sistema | Métrica / Evento | Fonte | Protocolo | Consumidores | Frequência | Retenção | Status |
|---------|------------------|-------|-----------|--------------|------------|----------|--------|
| MAXIMUS | `arousal_level` | Prometheus (`/metrics`) | HTTP scrape | Cockpit React, TUI Bubble Tea | 1s | 30 dias (Prometheus) | ✅ Instrumentado |
| MAXIMUS | `dopamine_spike_events` | gRPC stream (neuromodulation) | gRPC | Cockpit, Alerting HSAS | streaming | 7 dias (Kafka) | ✅ Schema formalizado |
| MAXIMUS | `safety.kill_switch_latency` | Prometheus | HTTP | SRE, Chaos Days | 10s | 60 dias | ✅ Instrumentado |
| MAXIMUS | `consciousness.esgt.ignition` | Event bus (NATS) | NATS JetStream | CLI, Audit Trail | streaming | 90 dias | ✅ Schema formalizado |
| vcli-go | `command.executed` | OTel exporter | OTLP gRPC | Data Lake, Analytics | near-real-time | 90 dias | ✅ Atributos atualizados |
| vcli-go | `session.latency` | OTel exporter | OTLP gRPC | SRE | near-real-time | 30 dias | ✅ Instrumentado |
| API Gateway | `http_requests_total` | Prometheus | HTTP | Observability | 15s | 30 dias | ✅ Instrumentado |
| API Gateway | `stream.connected_clients` | Custom exporter | SSE/WebSocket | Cockpit | 5s | 7 dias | ✅ Nome normalizado + Schema |
| HSAS | `alert.generated` | REST callback | HTTPS | MAXIMUS, CLI | on demand | 1 ano (S3) | ✅ Instrumentado |
| HSAS | `alert.acked` | REST callback | HTTPS | MAXIMUS | on demand | 1 ano | ✅ Correlação adicionada |
| Frontend | `dashboard.render_time` | Web Vitals | HTTPS | UX/Perf | on demand | 30 dias (Analytics) | ✅ Instrumentado |
| Frontend | `ws.messages_rate` | WebSocket client metrics | WS | Observability | 5s | 7 dias | ✅ Fallback instrumentado |

## Legenda de Status

- ✅ **Instrumentado**: Métrica completamente implementada e catalogada
- 🔄 **Em Andamento**: Implementação parcial
- ⏳ **Planejado**: Especificado mas não implementado
- ❌ **Não Implementado**: Identificado mas não iniciado

**Status Atual**: 12/12 métricas ✅ (100%)

## Schemas Formalizados

Todos os schemas de eventos críticos foram formalizados em:
- `docs/observability/schemas/consciousness-events.yaml`

Incluindo:
- ✅ `dopamine_spike_event` - Eventos de spike de dopamina
- ✅ `consciousness_esgt_ignition` - Eventos de ignição ESGT
- ✅ `stream_connected_clients` - Métricas de conexões de stream
- ✅ `alert_acknowledgement` - Acknowledgements de alertas

## Uniformidade de Labels

### Labels Obrigatórios (Todas as Métricas)

```yaml
common_labels:
  trace_id: "uuid"           # Rastreamento distribuído
  span_id: "uuid"            # Span do trace
  service_name: "string"     # Nome do serviço emissor
  environment: "prod|staging|dev"
  version: "semver"          # Versão do serviço
```

### Labels por Tipo

#### Consciousness Metrics (MAXIMUS)
```yaml
consciousness_labels:
  consciousness_cycle: "integer"
  system_load: "float"
  phi_proxy: "float"
  coherence: "float"
```

#### Stream Metrics
```yaml
stream_labels:
  stream_type: "websocket|sse|grpc"
  connection_id: "uuid"
  client_id: "uuid"
```

#### Security/Auth Metrics
```yaml
security_labels:
  user_id: "uuid"
  session_id: "uuid"
  auth_method: "jwt|spiffe|apikey"
```

## Políticas de Retenção

### Hierarquia de Armazenamento

1. **Hot Storage** (Prometheus - Real-time)
   - Retention: 7-60 dias
   - Query: < 100ms
   - Agregação: 1s-15s

2. **Warm Storage** (VictoriaMetrics/Thanos)
   - Retention: 60-365 dias  
   - Query: < 500ms
   - Agregação: 1m

3. **Cold Storage** (S3/Object Storage)
   - Retention: 1-7 anos
   - Query: 1-5s
   - Agregação: 1h/1d

### Políticas por Tipo

| Tipo de Métrica | Hot | Warm | Cold | Total |
|-----------------|-----|------|------|-------|
| Consciência (crítica) | 60d | 365d | 7y | 7y+ |
| Safety/Kill Switch | 60d | 365d | 7y | 7y+ |
| Performance | 30d | 90d | 1y | 1y |
| Business | 30d | 365d | 3y | 3y |
| Debug/Trace | 7d | 30d | - | 30d |

## Agregações e Downsampling

### Real-time (< 1 minuto)
- Resolution: 1s
- Storage: Prometheus
- Retention: Conforme tabela acima

### Medium-term (1 minuto - 1 hora)
- Resolution: 1m
- Aggregation: avg, min, max, p50, p95, p99
- Storage: VictoriaMetrics

### Long-term (> 1 hora)
- Resolution: 1h
- Aggregation: avg, min, max
- Storage: S3/Parquet

## Mapping Métrica → Dashboard

Documentado em: `docs/observability/dashboard-mapping.md`

## Próximas Ações Concluídas ✅

1. ✅ Schemas formalizados para eventos gRPC/streaming
2. ✅ Uniformidade de labels garantida (trace/span IDs)
3. ✅ Mapping para cockpit documentado
4. ✅ Política de retenção centralizada definida
5. ✅ Todas as pendências (⚠️ e ⚙️) resolvidas

---

**Versão**: 1.0  
**Data de Promoção**: 2024-10-08  
**v0.1 → v1.0**: Todas as métricas validadas e schemas formalizados  
**Compliance**: Doutrina Vértice Artigo VIII ✅
