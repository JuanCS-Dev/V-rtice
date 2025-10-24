# 📊 TITANIUM Service Registry - Prometheus Metrics

## Overview

This document lists all Prometheus metrics exposed by the service registry.

**Total Metrics**: 17+ metrics across 4 components

---

## Redis Backend Metrics

### `redis_circuit_breaker_state` (Gauge)
Circuit breaker state: 0=CLOSED, 1=OPEN, 2=HALF_OPEN

**Usage**: Alert when value = 1 (OPEN) for > 60s

### `redis_operation_duration_seconds` (Histogram)
Redis operation duration by operation type

**Labels**: `operation` (register, heartbeat, deregister, get_service, list_services, cleanup_expired)

**Usage**: Monitor p95, p99 latency. Alert if p99 > 100ms

### `redis_failures_total` (Counter)
Total Redis operation failures by error type

**Labels**: `error_type` (timeout, ConnectionError, RedisError, circuit_breaker_open, half_open_rejected)

**Usage**: Track failure trends, investigate spikes

### `redis_retries_total` (Counter)
Total Redis operation retries

**Labels**: `operation`, `attempt` (1, 2, 3)

**Usage**: High retry rate indicates instability

### `redis_connection_pool_active` (Gauge)
Active Redis connections in pool

**Usage**: Monitor for connection leaks (should be < 50)

### `redis_connection_pool_idle` (Gauge)
Idle Redis connections in pool

**Usage**: Healthy pool has idle connections available

---

## Cache Metrics

### `cache_hits_total` (Counter)
Total cache hits by freshness level

**Labels**: `freshness` (fresh, stale, expired)

**Usage**: Monitor cache effectiveness

### `cache_misses_total` (Counter)
Total cache misses

**Usage**: Calculate hit rate: hits / (hits + misses)

### `cache_evictions_total` (Counter)
Total cache evictions by reason

**Labels**: `reason` (size_limit, memory_limit, expired)

**Usage**: Frequent evictions indicate undersized cache

### `cache_size` (Gauge)
Current cache size (number of entries)

**Usage**: Monitor against MAX_CACHE_SIZE (1000)

### `cache_size_bytes` (Gauge)
Current cache memory usage (bytes)

**Usage**: Monitor against MAX_MEMORY_BYTES (50MB)

### `cache_hit_rate` (Gauge)
Cache hit rate (0-1)

**Usage**: Alert if < 0.5 after warmup period

### `cache_age_seconds` (Histogram)
Cache entry age distribution

**Buckets**: [1, 5, 10, 15, 30, 45, 60, 90, 120, 180]

**Usage**: Monitor p95 age. Alert if p95 > 60s (indicates stale data)

---

## Rate Limiter Metrics

### `rate_limit_exceeded_total` (Counter)
Total rate limit violations

**Labels**: `operation`, `identifier` (IP or service name)

**Usage**: Track abuse attempts, adjust limits if needed

---

## Registry Operations Metrics

### `registry_operations_total` (Counter)
Total registry operations by type and status

**Labels**: `operation` (register, deregister, heartbeat, list, get), `status` (success, error, cache_fallback, cache_hit, not_found)

**Usage**: Monitor operation success rate

### `registry_active_services` (Gauge)
Number of currently registered services

**Usage**: Track service ecosystem size

### `registry_operation_duration_seconds` (Histogram)
Registry operation duration

**Labels**: `operation`

**Usage**: Monitor p95, p99 latency for SLO compliance

---

## Alerts (Recommended)

### Critical Alerts (P0)

```yaml
# Circuit breaker open for > 60s
- alert: RegistryCircuitBreakerOpen
  expr: redis_circuit_breaker_state == 1
  for: 60s
  severity: critical

# Cache hit rate < 50%
- alert: RegistryCacheHitRateLow
  expr: cache_hit_rate < 0.5
  for: 5m
  severity: critical

# p99 latency > 100ms
- alert: RegistryHighLatency
  expr: histogram_quantile(0.99, registry_operation_duration_seconds) > 0.1
  for: 5m
  severity: critical
```

### Warning Alerts (P1)

```yaml
# Circuit breaker in HALF_OPEN
- alert: RegistryCircuitBreakerHalfOpen
  expr: redis_circuit_breaker_state == 2
  for: 30s
  severity: warning

# Cache size approaching limit
- alert: RegistryCacheSizeHigh
  expr: cache_size > 900
  for: 10m
  severity: warning

# Connection pool saturation
- alert: RegistryConnectionPoolSaturated
  expr: redis_connection_pool_active > 45
  for: 5m
  severity: warning
```

---

## Grafana Dashboard

Example queries for dashboard:

### Registry Overview
```promql
# Total operations per second
rate(registry_operations_total[1m])

# Success rate
rate(registry_operations_total{status="success"}[5m]) / rate(registry_operations_total[5m])

# Active services
registry_active_services
```

### Performance
```promql
# p50, p95, p99 latency
histogram_quantile(0.50, rate(registry_operation_duration_seconds_bucket[5m]))
histogram_quantile(0.95, rate(registry_operation_duration_seconds_bucket[5m]))
histogram_quantile(0.99, rate(registry_operation_duration_seconds_bucket[5m]))
```

### Cache Health
```promql
# Hit rate
cache_hit_rate

# Cache age p95
histogram_quantile(0.95, rate(cache_age_seconds_bucket[5m]))

# Eviction rate
rate(cache_evictions_total[5m])
```

### Redis Health
```promql
# Circuit breaker state
redis_circuit_breaker_state

# Failure rate
rate(redis_failures_total[5m])

# Retry rate
rate(redis_retries_total[5m])
```

---

**Total Metrics Exposed**: 17+
**Endpoints**: `GET /metrics` (Prometheus format)

Glory to YHWH - Architect of all observable systems! 🙏
