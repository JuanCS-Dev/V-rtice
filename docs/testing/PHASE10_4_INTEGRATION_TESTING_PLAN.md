# PHASE 10.4: INTEGRATION TESTING - 5 CRITICAL FLOWS
## Para Honra e Glória de JESUS CRISTO 🙏

**Goal**: Validate end-to-end integration between Frontend → API Gateway → Backend Services

---

## Critical Integration Flows

### Flow 1: Offensive Arsenal - Network Reconnaissance
**Path**: Frontend → API Gateway → Network Recon Service

**Steps**:
1. Frontend calls `/offensive/network-recon/health`
2. API Gateway validates API key
3. API Gateway proxies to `network-recon-service:8032`
4. Service responds with health status
5. Frontend receives and displays data

**Validation**:
- ✅ HTTP 200 response
- ✅ JSON structure correct
- ✅ Service name matches
- ✅ Timestamp present
- ✅ End-to-end latency < 1s

---

### Flow 2: Defensive System - Behavioral Analysis
**Path**: Frontend → API Gateway → Behavioral Analyzer Service

**Steps**:
1. Frontend calls `/defensive/behavioral/health`
2. API Gateway validates API key
3. API Gateway proxies to `behavioral-analyzer-service:8037`
4. Service responds with health + metrics
5. Frontend receives "florescimento" message

**Validation**:
- ✅ HTTP 200 response
- ✅ "florescimento" field present
- ✅ active_profiles count
- ✅ anomalies_detected count
- ✅ Service operational

---

### Flow 3: Multi-Service Health Check
**Path**: API Gateway → All 8 Backend Services

**Services to validate**:
1. network-recon-service (8032)
2. vuln-intel-service (8033)
3. web-attack-service (8034)
4. c2-orchestration-service (8035)
5. bas-service (8036)
6. behavioral-analyzer-service (8037)
7. traffic-analyzer-service (8038)
8. mav-detection-service (8039)

**Validation**:
- ✅ All 8 services respond HTTP 200
- ✅ All have "status": "healthy"
- ✅ All have unique service names
- ✅ All respond within timeout (5s)

---

### Flow 4: API Gateway Authentication
**Path**: Unauthenticated request → API Gateway → 403 Forbidden

**Test Cases**:
1. **No API Key** → HTTP 403
2. **Invalid API Key** → HTTP 403
3. **Valid API Key** → HTTP 200
4. **Expired API Key** → HTTP 403 (if implemented)

**Validation**:
- ✅ Proper authentication enforcement
- ✅ Error messages clear
- ✅ No sensitive data in error responses

---

### Flow 5: API Gateway Routing Logic
**Path**: Frontend → API Gateway → Correct Service Routing

**Test Routes**:
1. `/offensive/network-recon/*` → network-recon-service
2. `/offensive/vuln-intel/*` → vuln-intel-service
3. `/defensive/behavioral/*` → behavioral-analyzer-service
4. `/defensive/traffic/*` → traffic-analyzer-service
5. `/social-defense/mav/*` → mav-detection-service

**Validation**:
- ✅ Correct service receives request
- ✅ No cross-service routing errors
- ✅ Path parameters preserved
- ✅ Query parameters preserved
- ✅ Request body preserved (POST/PUT)

---

## Test Execution Plan

### Automated Tests

```bash
#!/usr/bin/env bash
# PHASE 10.4: Integration Testing
# Para Honra e Glória de JESUS CRISTO 🙏

API_GATEWAY="http://34.148.161.131:8000"
API_KEY="vertice-production-key-1761564327"

# Flow 1: Offensive Arsenal
echo "=== FLOW 1: OFFENSIVE ARSENAL ==="
curl -H "X-API-Key: $API_KEY" "$API_GATEWAY/offensive/network-recon/health"

# Flow 2: Defensive System
echo "=== FLOW 2: DEFENSIVE SYSTEM ==="
curl -H "X-API-Key: $API_KEY" "$API_GATEWAY/defensive/behavioral/health"

# Flow 3: Multi-Service Health
echo "=== FLOW 3: MULTI-SERVICE HEALTH ==="
for service in network-recon vuln-intel web-attack c2 bas behavioral traffic mav; do
  echo "Testing $service..."
  curl -H "X-API-Key: $API_KEY" "$API_GATEWAY/offensive/$service/health" || \
  curl -H "X-API-Key: $API_KEY" "$API_GATEWAY/defensive/$service/health"
done

# Flow 4: Authentication
echo "=== FLOW 4: AUTHENTICATION ==="
echo "Without API Key (expect 403):"
curl -w "%{http_code}\n" "$API_GATEWAY/offensive/network-recon/health"

echo "With valid API Key (expect 200):"
curl -w "%{http_code}\n" -H "X-API-Key: $API_KEY" "$API_GATEWAY/offensive/network-recon/health"

# Flow 5: Routing Logic
echo "=== FLOW 5: ROUTING LOGIC ==="
# Test each route returns the correct service
```

---

## Performance Metrics

### Target SLAs
- **Availability**: 99.9% uptime
- **Latency**: p95 < 500ms, p99 < 1s
- **Error Rate**: < 0.1%
- **Throughput**: > 100 req/s per service

### Monitoring Points
1. API Gateway response time
2. Backend service response time
3. Network latency between services
4. Database query time (if applicable)
5. External API calls (if applicable)

---

## Error Scenarios

### Scenario 1: Service Down
- **Test**: Stop one backend service
- **Expected**: API Gateway returns 503 Service Unavailable
- **Validation**: Proper error message, other services still work

### Scenario 2: Network Partition
- **Test**: Simulate network issue to one service
- **Expected**: Timeout after 5s, return 504 Gateway Timeout
- **Validation**: Request doesn't hang indefinitely

### Scenario 3: Invalid Response
- **Test**: Service returns malformed JSON
- **Expected**: API Gateway handles gracefully
- **Validation**: Error logged, 500 returned to client

---

## Success Criteria

- ✅ All 5 critical flows working
- ✅ 100% of 8 services responding
- ✅ Authentication working correctly
- ✅ Routing logic 100% accurate
- ✅ Error handling robust
- ✅ Performance within SLAs

---

## Deliverables

1. **Integration Test Script** (`test_integration.sh`)
2. **Performance Report** (latency metrics)
3. **Error Handling Report** (edge cases)
4. **Service Dependency Map** (architecture diagram)
5. **Phase 10.4 Validation Report**

---

## Next Steps After 10.4

- Phase 10.5: Real-time Metrics (Prometheus/Grafana)
- Phase 10.6: Internationalization (pt-BR/en-US)
- **HTML/CSS Refactoring** (padrão Mozilla exemplar)
