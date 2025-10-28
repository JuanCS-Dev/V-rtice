# Observability Integration Guide

**Module**: `backend.common.observability`  
**Features**: Prometheus metrics + Structured logging (JSON)  
**Status**: Production-ready ✅

## Quick Start (5 minutes)

### 1. Add to requirements.txt
```txt
prometheus-client>=0.19.0
```

### 2. Update FastAPI app
```python
from fastapi import FastAPI, Request
from backend.common.observability import (
    setup_observability,
    get_logger,
    correlation_id_middleware,
    create_metrics_endpoint
)

# Initialize observability
metrics = setup_observability(
    service_name="bas_service",
    version="1.0.0",
    log_level="INFO",
    log_format="json",
    environment="production"
)

app = FastAPI(title="BAS Service")

# Add correlation ID middleware
@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    return await correlation_id_middleware()(request, call_next)

# Metrics endpoint
@app.get("/metrics")
async def metrics_endpoint():
    return await create_metrics_endpoint(metrics)()

# Use in endpoints
logger = get_logger(__name__, service="bas")

@app.get("/health")
async def health():
    with metrics.track_request("health"):
        logger.info("Health check called")
        return {"status": "healthy"}

@app.post("/simulate")
async def simulate(request: SimulationRequest):
    import time
    start = time.time()
    
    with metrics.track_request("simulate", method="POST"):
        try:
            logger.info(
                "Simulation started",
                extra={
                    "scenario": request.attack_scenario,
                    "target": request.target_service
                }
            )
            
            # Your logic here
            result = run_simulation(request)
            
            # Track business metric
            duration = time.time() - start
            metrics.track_business_operation(
                operation_type="simulation",
                status="success",
                duration=duration
            )
            
            logger.info(
                "Simulation completed",
                extra={"sim_id": result.id, "duration": duration}
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "Simulation failed",
                extra={"error": str(e)},
                exc_info=True
            )
            
            metrics.track_business_operation(
                operation_type="simulation",
                status="failure"
            )
            raise
```

### 3. Run and verify

**Check metrics**:
```bash
curl http://localhost:8000/metrics
```

**Check logs** (JSON format):
```json
{
  "timestamp": "2025-10-11T18:30:45.123Z",
  "level": "INFO",
  "service": "bas_service",
  "logger": "api",
  "message": "Simulation started",
  "correlation_id": "abc-123-def-456",
  "scenario": "credential_access",
  "target": "test_service",
  "file": "api.py",
  "line": 42
}
```

## Available Metrics (RED Method)

### Request Metrics
- `vertice_bas_service_requests_total{method, endpoint, status}` - Total requests
- `vertice_bas_service_requests_duration_seconds{method, endpoint}` - Request latency
- `vertice_bas_service_errors_total{error_type, endpoint}` - Total errors

### Resource Metrics
- `vertice_bas_service_active_connections` - Active connections
- `vertice_bas_service_memory_usage_bytes` - Memory usage

### Business Metrics (Custom)
- `vertice_bas_service_operations_total{operation_type, status}` - Operations count
- `vertice_bas_service_operation_duration_seconds{operation_type}` - Operation duration

### Service Info
- `vertice_bas_service_info{version, environment, git_commit}` - Service metadata

## Logging Features

### Structured Logging
All logs are JSON-formatted with:
- Timestamp (ISO 8601 UTC)
- Log level
- Service name
- Logger name
- Message
- Correlation ID (for request tracing)
- Extra fields (custom context)
- Exception info (if present)

### Correlation ID
Automatically tracked across requests:
```python
# Client sends
curl -H "X-Correlation-ID: my-unique-id" http://localhost:8000/health

# All logs for that request include correlation_id: "my-unique-id"
# Response includes X-Correlation-ID header
```

### Log Levels
```python
logger.debug("Detailed debug info", extra={"data": {...}})
logger.info("Normal operation", extra={"user": "admin"})
logger.warning("Something unexpected", extra={"value": 123})
logger.error("Operation failed", extra={"error": "..."}, exc_info=True)
logger.critical("System failure", extra={"details": "..."})
```

## Grafana Dashboards

### Import Dashboard
1. Go to Grafana → Dashboards → Import
2. Use dashboard ID: Create custom
3. Data source: Prometheus

### Example Queries

**Request rate (requests/sec)**:
```promql
rate(vertice_bas_service_requests_total[5m])
```

**Error rate (%)**:
```promql
rate(vertice_bas_service_errors_total[5m]) 
/ 
rate(vertice_bas_service_requests_total[5m]) * 100
```

**95th percentile latency**:
```promql
histogram_quantile(0.95, 
  rate(vertice_bas_service_requests_duration_seconds_bucket[5m])
)
```

**Active simulations**:
```promql
vertice_bas_service_operations_total{operation_type="simulation", status="success"}
```

## Alerting Rules

### Prometheus Alerting
```yaml
groups:
  - name: bas_service_alerts
    rules:
      - alert: HighErrorRate
        expr: |
          rate(vertice_bas_service_errors_total[5m]) > 0.05
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate in BAS service"
          description: "Error rate is {{ $value | humanizePercentage }}"
      
      - alert: HighLatency
        expr: |
          histogram_quantile(0.95, 
            rate(vertice_bas_service_requests_duration_seconds_bucket[5m])
          ) > 5.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency in BAS service"
          description: "95th percentile latency is {{ $value }}s"
```

## Log Aggregation (ELK/Loki)

### Loki Query Examples

**All logs for a simulation**:
```logql
{service="bas_service"} |= "Simulation" | json | sim_id="abc-123"
```

**Errors in last hour**:
```logql
{service="bas_service"} | json | level="ERROR" | line_format "{{.timestamp}} {{.message}}"
```

**Correlation ID tracing**:
```logql
{service=~".*"} | json | correlation_id="abc-123-def-456"
```

## Testing Observability

### Unit Tests
```python
def test_metrics_tracking():
    metrics = ServiceMetrics("test_service")
    
    with metrics.track_request("test"):
        # Your code
        pass
    
    # Verify metrics updated
    assert metrics.requests_total._value.get() > 0

def test_logging():
    logger = get_logger("test")
    
    with pytest.raises(Exception):
        logger.error("Test error", exc_info=True)
    
    # Verify log output
    assert "Test error" in caplog.text
```

### Integration Tests
```bash
# Start service
docker compose up bas_service

# Generate traffic
for i in {1..100}; do
  curl http://localhost:8000/simulate -d '{"scenario":"test"}'
done

# Check metrics
curl http://localhost:8000/metrics | grep requests_total

# Check logs
docker compose logs bas_service | jq .
```

## Rollout Strategy

### Phase 1: Core Services (Week 1)
- [x] BAS Service
- [ ] Exploit Database Service
- [ ] Network Recon Service
- [ ] Vuln Intel Service
- [ ] Maximus Core Service

### Phase 2: Intelligence Layer (Week 2)
- [ ] Narrative Filter Service
- [ ] Pattern Recognition Service
- [ ] Adaptive Immunity Service

### Phase 3: All Remaining (Week 3)
- [ ] 80+ other services

### Validation Criteria
- ✅ /metrics endpoint responds
- ✅ Prometheus scrapes successfully
- ✅ Logs are JSON-formatted
- ✅ Correlation IDs present
- ✅ Grafana dashboard working

## Best Practices

### Do's ✅
- Use `extra={}` for contextual data
- Track business operations
- Set correlation IDs
- Use appropriate log levels
- Monitor RED metrics

### Don'ts ❌
- Don't log sensitive data (passwords, tokens)
- Don't log in hot paths (use DEBUG level)
- Don't create excessive custom metrics
- Don't hardcode correlation IDs
- Don't ignore metric cardinality

## Troubleshooting

**Metrics not appearing?**
- Check Prometheus available: `python -c "import prometheus_client"`
- Verify /metrics endpoint accessible
- Check Prometheus scrape config

**Logs not JSON?**
- Verify `json` module available
- Check `format_type="json"` in setup
- Test: `python -c "import json; print(json.dumps({'test': 1}))"`

**High memory usage?**
- Reduce metric cardinality (labels)
- Lower histogram buckets
- Enable log rotation

## Support

**Documentation**: `docs/guides/observability-integration.md`  
**Issues**: GitHub Issues #10, #21  
**Examples**: `backend/services/bas_service/api.py`

---
**Version**: 1.0.0  
**Updated**: 2025-10-11  
**Status**: Production-ready ✅
