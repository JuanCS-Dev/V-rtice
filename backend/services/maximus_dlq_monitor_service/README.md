# MAXIMUS DLQ Monitor Service

**Air Gap Fix:** AG-KAFKA-005
**Priority:** HIGH (Data Loss Prevention)
**Status:** ✅ IMPLEMENTED

## Overview

Dead Letter Queue (DLQ) monitoring service for MAXIMUS Adaptive Immunity APVs. Prevents data loss by monitoring failed APV messages, implementing retry logic, and alerting on critical issues.

## Features

- **DLQ Monitoring**: Consumes `maximus.adaptive-immunity.dlq` topic
- **Automatic Retry**: Retries failed APVs up to 3 times with exponential backoff
- **Alerting**: Sends alerts when DLQ size exceeds threshold (10 messages)
- **Prometheus Metrics**: Exposes metrics for monitoring and dashboards
- **Health Checks**: `/health` endpoint for service status

## Architecture

```
Failed APV → maximus.adaptive-immunity.dlq (DLQ)
                ↓
        DLQ Monitor Service
                ↓
    ┌───────────────────────┐
    │   Retry Logic         │
    │   (Max 3 attempts)    │
    └───────────────────────┘
                ↓
    ┌───────────────────────┐
    │ Success: Back to APV  │
    │ Failure: Alert + Log  │
    └───────────────────────┘
```

## Endpoints

### Health Check
```bash
GET /health
```

Response:
```json
{
  "status": "healthy",
  "service": "maximus-dlq-monitor",
  "kafka_connected": true,
  "dlq_queue_size": 0,
  "alert_threshold": 10
}
```

### Status
```bash
GET /status
```

Response:
```json
{
  "service": "maximus-dlq-monitor",
  "running": true,
  "kafka_bootstrap": "localhost:9092",
  "dlq_topic": "maximus.adaptive-immunity.dlq",
  "retry_topic": "maximus.adaptive-immunity.apv",
  "max_retries": 3,
  "current_queue_size": 0,
  "alert_threshold": 10,
  "alert_status": "normal"
}
```

### Prometheus Metrics
```bash
GET /metrics
```

Metrics exposed:
- `dlq_messages_total{reason, severity}` - Total DLQ messages by reason
- `dlq_retries_total{success}` - Total retry attempts
- `dlq_queue_size` - Current DLQ size
- `dlq_alerts_sent_total` - Total alerts sent

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Kafka bootstrap servers |
| `PORT` | `8085` | Service port |

## Installation

```bash
cd maximus_dlq_monitor_service
pip install -r requirements.txt
```

## Running

```bash
python main.py
```

Or with Docker:

```bash
docker build -t maximus-dlq-monitor .
docker run -p 8085:8085 \
  -e KAFKA_BOOTSTRAP_SERVERS=kafka:9092 \
  maximus-dlq-monitor
```

## Testing

### Force APV Failure (for testing)

1. Modify Oráculo to force validation failure:
```python
# In maximus_oraculo/kafka_integration/apv_publisher.py
raise ValueError("Test failure for DLQ")
```

2. Trigger APV generation via WebSocket

3. Check DLQ monitor logs:
```bash
tail -f /tmp/dlq_monitor.log
```

4. Verify metrics:
```bash
curl http://localhost:8085/metrics | grep dlq_
```

### Expected Output

```
🚨 DLQ Message: validation_error | Severity: high | Retries: 0 | APV ID: apv-123
✅ APV apv-123 retried successfully
```

## Grafana Dashboard

Create dashboard with panels:

1. **DLQ Message Count** (last 24h)
   - Query: `rate(dlq_messages_total[5m])`
2. **DLQ Retry Success Rate**
   - Query: `rate(dlq_retries_total{success="true"}[5m]) / rate(dlq_retries_total[5m])`
3. **DLQ Queue Size**
   - Query: `dlq_queue_size`
4. **Alerts Sent**
   - Query: `rate(dlq_alerts_sent_total[1h])`

## Alerts

Configure Prometheus alerts:

```yaml
groups:
  - name: dlq_alerts
    rules:
      - alert: DLQSizeHigh
        expr: dlq_queue_size > 10
        for: 5m
        annotations:
          summary: "DLQ size exceeds threshold"
          description: "DLQ has {{ $value }} messages (threshold: 10)"

      - alert: DLQRetryFailureRate
        expr: rate(dlq_retries_total{success="false"}[5m]) > 0.5
        for: 10m
        annotations:
          summary: "High DLQ retry failure rate"
          description: "{{ $value }}% of retries are failing"
```

## Integration with Existing Services

### Oráculo APV Publisher

The DLQ monitor integrates with Oráculo's existing DLQ producer:

```python
# maximus_oraculo/kafka_integration/apv_publisher.py (existing)
try:
    self.producer.send("maximus.adaptive-immunity.apv", apv)
except Exception as e:
    # Send to DLQ (already implemented)
    self.producer.send("maximus.adaptive-immunity.dlq", {
        "apv": apv,
        "error": {"type": str(type(e).__name__), "message": str(e)},
        "retry_count": 0,
        "timestamp": datetime.utcnow().isoformat()
    })
```

No changes needed to Oráculo - DLQ monitor works with existing DLQ messages.

## Monitoring

Check service health:

```bash
# Health check
curl http://localhost:8085/health

# Status
curl http://localhost:8085/status

# Metrics
curl http://localhost:8085/metrics | grep dlq_
```

## Troubleshooting

### DLQ Monitor not starting

Check Kafka connection:
```bash
python -c "from kafka import KafkaConsumer; KafkaConsumer(bootstrap_servers='localhost:9092')"
```

### High retry failure rate

1. Check Kafka broker logs
2. Verify Oráculo APV validation logic
3. Review APV schema changes
4. Check network connectivity

### Alerts not triggering

1. Verify Prometheus scraping: `http://localhost:8085/metrics`
2. Check alert threshold: Default is 10 messages
3. Review Prometheus alert rules configuration

## Production Deployment

1. **Set up Kafka cluster** (production brokers)
2. **Configure alerting** (Slack, PagerDuty, email)
3. **Enable monitoring** (Grafana dashboard + Prometheus alerts)
4. **Scale horizontally** (multiple replicas with Kafka consumer groups)
5. **Set up log aggregation** (ELK stack or similar)

## Future Enhancements

- [ ] Dead letter analysis dashboard
- [ ] Automatic root cause detection (ML-based)
- [ ] Slack/PagerDuty/Email integration
- [ ] APV replay from DLQ admin panel
- [ ] Circuit breaker for retry floods

## Links

- Air Gap Report: `/backend/services/DIAGNOSTICADOR_AIR_GAPS_REPORT.md`
- Implementation Plan: `/backend/services/AIR_GAPS_IMPLEMENTATION_PLAN.md`
- Oráculo Service: `/backend/services/maximus_oraculo/`

---

**Implemented:** 2025-10-23
**Version:** 1.0.0
**Padrão Pagani:** Zero compromises - Production ready ✓
