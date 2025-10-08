# FASE C: Python↔Go Bridge - Design Document

**Status**: 🏗️ IN PROGRESS
**Version**: 1.0
**Date**: 2025-10-07

---

## 1. Executive Summary

**Objective**: Create a production-ready communication bridge between vCLI-Go (CLI tool) and Vértice Python backend services.

**Scope**:
- gRPC-based communication for high-performance operations
- REST fallback for services without gRPC
- Real-time event streaming (SSE/WebSocket)
- Offline mode with local cache (BadgerDB)

**Out of Scope** (future phases):
- Full service mesh integration (FASE G)
- Multi-cluster federation (FASE H)

---

## 2. Current State Analysis

### 2.1 Existing Integration

✅ **Already Implemented**:
- `vcli-go/internal/governance/` - HTTP + SSE client for MAXIMUS Governance
- `vcli-go/api/grpc/governance/` - gRPC proto definitions for Governance
- `vcli-go/internal/grpc/governance_client.go` - gRPC client implementation

📊 **Coverage**: ~5% (only Governance service)

### 2.2 Backend Services Requiring Integration

| Priority | Service | Protocol | Use Case |
|----------|---------|----------|----------|
| **P0** | `maximus_orchestrator_service` | gRPC | Decision workflow, governance |
| **P0** | `active_immune_core` | gRPC + Kafka | Agent management, cytokine streaming |
| **P1** | `api_gateway` | REST | Unified entry point |
| **P1** | Prometheus/Grafana | REST | Observability queries |
| **P2** | `ethical_audit_service` | REST | Ethical decision auditing |
| **P2** | `narrative_manipulation_filter` | REST | Cognitive defense analysis |
| **P3** | Other services | REST | As needed |

---

## 3. Architecture Design

### 3.1 Communication Patterns

```
┌─────────────────────────────────────────────────────────────┐
│                         vCLI-Go                             │
│  ┌───────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐ │
│  │  Commands │──│  Bridge  │──│  Cache   │──│  Display  │ │
│  │   Layer   │  │  Layer   │  │ BadgerDB │  │   (TUI)   │ │
│  └───────────┘  └──────────┘  └──────────┘  └───────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   ┌────▼────┐    ┌───▼────┐    ┌───▼─────┐
   │  gRPC   │    │  REST  │    │  SSE/WS │
   │ (fast)  │    │(compat)│    │(stream) │
   └────┬────┘    └───┬────┘    └───┬─────┘
        │             │              │
┌───────▼─────────────▼──────────────▼────────────────────────┐
│              Python Backend Services                        │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  MAXIMUS    │  │ Active       │  │  API Gateway     │  │
│  │ Orchestrator│  │ Immune Core  │  │  + Prometheus    │  │
│  └─────────────┘  └──────────────┘  └──────────────────┘  │
│        │                  │                    │            │
│        ▼                  ▼                    ▼            │
│   PostgreSQL          Kafka + Redis        Time-series DB  │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Protocol Selection Matrix

| Operation Type | Protocol | Justification |
|----------------|----------|---------------|
| **Command execution** | gRPC | Low latency, type safety, bi-directional streaming |
| **Event streaming** | SSE/gRPC Stream | Real-time updates (decisions, agent events) |
| **Observability queries** | REST | Prometheus/Grafana standard HTTP API |
| **Fallback/legacy** | REST | Services without gRPC support |
| **Offline cache sync** | gRPC | Batch data transfer on reconnect |

---

## 4. Implementation Plan

### Phase 1: Core gRPC Services (Week 1-2)

#### 4.1 MAXIMUS Orchestrator Integration (P0)

**Expand existing governance gRPC**:

```protobuf
// vcli-go/api/grpc/maximus/maximus.proto

service MaximusOrchestrator {
  // Decision Management
  rpc SubmitDecision(DecisionRequest) returns (DecisionResponse);
  rpc GetDecision(GetDecisionRequest) returns (Decision);
  rpc ListDecisions(ListDecisionsRequest) returns (stream Decision);

  // Real-time Events
  rpc StreamDecisionEvents(EventsRequest) returns (stream DecisionEvent);

  // Governance
  rpc GetGovernanceMetrics(MetricsRequest) returns (GovernanceMetrics);
}
```

**vCLI-Go commands**:
```bash
vcli maximus submit --decision "Deploy new agent version" --context production
vcli maximus list --status pending --format table
vcli maximus watch --decision-id abc123  # Real-time streaming
vcli maximus metrics --range 1h
```

#### 4.2 Active Immune Core Integration (P0)

```protobuf
// vcli-go/api/grpc/immune/immune.proto

service ActiveImmuneCore {
  // Agent Management
  rpc ListAgents(ListAgentsRequest) returns (stream Agent);
  rpc GetAgent(GetAgentRequest) returns (Agent);
  rpc CloneAgent(CloneAgentRequest) returns (Agent);
  rpc TerminateAgent(TerminateAgentRequest) returns (TerminateResponse);

  // Lymphnode Operations
  rpc GetLymphnodeStatus(LymphnodeRequest) returns (LymphnodeStatus);
  rpc ListLymphnodes(ListLymphnodesRequest) returns (stream Lymphnode);

  // Cytokine Streaming
  rpc StreamCytokines(StreamRequest) returns (stream Cytokine);

  // Coordination
  rpc TriggerMassResponse(MassResponseRequest) returns (MassResponseResponse);
}
```

**vCLI-Go commands**:
```bash
vcli immune agents list --lymphnode ln-us-east-1
vcli immune agents clone --id agent-123 --count 10
vcli immune cytokines stream --topic threats --filter severity=high
vcli immune lymphnodes status --all
```

### Phase 2: REST Integration (Week 3)

#### 2.1 API Gateway Client

```go
// vcli-go/internal/gateway/client.go

type GatewayClient struct {
    baseURL    string
    httpClient *http.Client
    token      string // JWT auth
}

func (c *GatewayClient) Query(service, endpoint string, params map[string]string) (json.RawMessage, error)
func (c *GatewayClient) Post(service, endpoint string, body interface{}) error
```

**Usage**:
```bash
vcli gateway query --service ethical-audit --endpoint /decisions
vcli gateway query --service narrative-filter --endpoint /analyze --data @article.json
```

#### 2.2 Observability Client (Prometheus/Grafana)

```go
// vcli-go/internal/observability/prometheus.go

type PrometheusClient struct {
    baseURL string
}

func (c *PrometheusClient) QueryRange(query, start, end, step string) (*QueryResult, error)
func (c *PrometheusClient) QueryInstant(query string) (*InstantResult, error)
```

**Usage**:
```bash
vcli metrics query 'rate(cytokine_count[5m])' --range 1h
vcli metrics instant 'up{service="maximus"}'
vcli metrics dashboard --name immune-system --output grafana.json
```

### Phase 3: Event Streaming (Week 4)

#### 3.1 SSE Client (Existing - Enhance)

Expand `vcli-go/internal/governance/sse_client.go`:

```go
type SSEClient struct {
    baseURL string
    topics  []string
}

func (c *SSEClient) Subscribe(topics []string) (<-chan Event, error)
func (c *SSEClient) SubscribeWithFilter(topic string, filter func(Event) bool) (<-chan Event, error)
```

#### 3.2 Kafka Consumer (New - via gRPC proxy)

**Problem**: Direct Kafka access from CLI is heavyweight
**Solution**: gRPC streaming proxy in Python backend

```protobuf
service KafkaProxy {
  rpc StreamTopic(TopicRequest) returns (stream KafkaMessage);
}
```

```bash
vcli stream cytokines --topic immune.threats --format json
vcli stream hormones --topic immune.regulations --filter priority=high
```

### Phase 4: Offline Mode & Caching (Week 5)

#### 4.1 BadgerDB Cache Layer

```go
// vcli-go/internal/cache/badger_cache.go

type Cache struct {
    db *badger.DB
}

func (c *Cache) Set(key string, value interface{}, ttl time.Duration) error
func (c *Cache) Get(key string, dest interface{}) error
func (c *Cache) Invalidate(pattern string) error

// Prefetch common queries
func (c *Cache) Prefetch(queries []string) error
```

**Cache strategy**:
- **Hot data** (5min TTL): Agent status, Lymphnode health
- **Warm data** (1h TTL): Decision history, metrics snapshots
- **Cold data** (24h TTL): Configuration, service discovery

#### 4.2 Offline Operation

```bash
# Work offline with cached data
vcli --offline immune agents list  # Uses cached data
vcli --offline maximus list --cached-since 1h

# Sync when back online
vcli sync --full  # Re-download all cached queries
```

---

## 5. Configuration Hierarchy

```yaml
# ~/.vcli/config.yaml (FASE E will implement this fully)

# Bridge configuration
bridge:
  # Backend endpoints
  endpoints:
    maximus: "grpc://maximus.vertice.local:50051"
    immune: "grpc://active-immune.vertice.local:50052"
    gateway: "https://api.vertice.local"
    prometheus: "http://prometheus.vertice.local:9090"

  # Authentication
  auth:
    method: "jwt"  # or "mtls", "api-key"
    token_file: "~/.vcli/token"

  # Retry & circuit breaker
  retry:
    max_attempts: 3
    backoff: "exponential"
  circuit_breaker:
    failure_threshold: 5
    timeout: 30s

  # Cache
  cache:
    enabled: true
    path: "~/.vcli/cache"
    max_size_mb: 500
    ttl_default: 5m
```

---

## 6. Implementation Checklist

### Week 1: MAXIMUS gRPC Integration
- [ ] Create `maximus.proto` with full service definition
- [ ] Generate Go code: `protoc --go_out=. --go-grpc_out=. maximus.proto`
- [ ] Implement `internal/grpc/maximus_client.go`
- [ ] Add CLI commands: `cmd/maximus.go`
- [ ] Integration tests with real MAXIMUS backend
- [ ] Documentation + examples

### Week 2: Active Immune Core gRPC
- [ ] Create `immune.proto` (agents, lymphnodes, cytokines)
- [ ] Generate Go code
- [ ] Implement `internal/grpc/immune_client.go`
- [ ] Add CLI commands: `cmd/immune.go`
- [ ] Cytokine streaming integration test
- [ ] Documentation + examples

### Week 3: REST Clients
- [ ] Implement `internal/gateway/client.go` (generic REST client)
- [ ] Implement `internal/observability/prometheus.go`
- [ ] Add CLI commands: `cmd/gateway.go`, `cmd/metrics.go`
- [ ] Integration tests
- [ ] Documentation

### Week 4: Event Streaming
- [ ] Enhance SSE client (`internal/governance/sse_client.go`)
- [ ] Implement gRPC Kafka proxy (Python side if needed)
- [ ] Add `cmd/stream.go` commands
- [ ] Real-time event display in TUI
- [ ] Integration tests

### Week 5: Offline Mode
- [ ] Implement BadgerDB cache layer (`internal/cache/`)
- [ ] Add `--offline` flag support to all commands
- [ ] Implement `vcli sync` command
- [ ] Prefetch strategies
- [ ] Cache invalidation logic
- [ ] Documentation

---

## 7. Testing Strategy

### 7.1 Unit Tests
- Mock gRPC servers for each service
- Test retry logic, circuit breakers
- Cache hit/miss scenarios

### 7.2 Integration Tests
```bash
# Test with real backends (Docker Compose)
./test/integration/run_bridge_tests.sh

# Tests:
# - MAXIMUS decision submission + retrieval
# - Immune agent cloning + streaming
# - Prometheus metrics queries
# - Offline mode with cache
# - Failover (gRPC → REST fallback)
```

### 7.3 E2E Tests
```bash
# Full workflow tests
./test/e2e/test_decision_workflow.sh
./test/e2e/test_agent_management.sh
./test/e2e/test_offline_mode.sh
```

---

## 8. Performance Targets

| Metric | Target | Justification |
|--------|--------|---------------|
| gRPC latency (p50) | < 10ms | Fast CLI experience |
| gRPC latency (p99) | < 50ms | Acceptable for interactive use |
| REST fallback latency (p50) | < 100ms | Slower but acceptable |
| Cache hit ratio | > 80% | Offline mode usability |
| Cache lookup latency | < 1ms | Instant offline experience |
| Event stream throughput | > 1000 events/sec | Handle high cytokine volume |

---

## 9. Security Considerations

### 9.1 Authentication
- **gRPC**: mTLS or JWT in metadata
- **REST**: JWT Bearer token
- **Credential storage**: OS keyring (macOS Keychain, Linux Secret Service)

### 9.2 Authorization
- vCLI inherits user permissions from backend
- No local privilege escalation

### 9.3 Data Protection
- Cache encryption at rest (AES-256)
- Sensitive fields (tokens, keys) never cached
- Secure credential rotation

---

## 10. Success Criteria

✅ **FASE C is complete when**:
1. vCLI-Go can perform all MAXIMUS operations (submit/list/watch decisions)
2. vCLI-Go can manage Immune Core (agents, lymphnodes, cytokines)
3. vCLI-Go can query Prometheus metrics
4. vCLI-Go works offline with cached data
5. All integration tests pass
6. Performance targets met
7. Documentation complete

---

## 11. Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Python backend doesn't support gRPC | High | Low | Implement gRPC server in Python services (1 week) |
| Network latency too high | Medium | Medium | Implement aggressive caching, prefetch |
| Cache bloat | Low | Medium | Implement LRU eviction, size limits |
| Breaking API changes | High | Medium | Versioned proto files, backward compatibility |

---

## 12. Future Enhancements (Post-FASE C)

- **FASE D**: Enhanced offline mode with conflict resolution
- **FASE E**: Full configuration management (env vars, files, flags precedence)
- **FASE F**: Plugin system (custom backends, formatters)
- **FASE G**: Service mesh integration (Istio/Linkerd)
- **FASE H**: Multi-cluster support

---

**Next Steps**: Begin Week 1 implementation - MAXIMUS gRPC expansion.

