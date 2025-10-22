# vCLI-Go - AIR GAPS MATRIX
**Data:** 2025-01-22
**Fonte:** Diagnóstico Absoluto vCLI-Go

---

## 📊 MATRIZ CONSOLIDADA DE AIR GAPS

| ID | Component | Status | Gap Type | Severity | Impact | Effort | Files Affected |
|----|-----------|--------|----------|----------|--------|--------|----------------|
| **AG-001** | **Config Management** | 0% | Missing Feature | 🔴 P0-CRITICAL | 100% backend commands | 1 dia (8h) | `cmd/root.go`, `internal/config/manager.go` |
| **AG-002** | **Active Immune Core** | 0% | Implementation | 🔴 P0-CRITICAL | 100% `vcli immune` | 2-3 dias (16-24h) | `internal/grpc/immune_client.go`, `cmd/immune.go` |
| **AG-003** | **MAXIMUS Integration** | 60% | Validation | 🟡 P1-HIGH | 100% `vcli maximus` | 3h-1dia | `cmd/maximus.go` (endpoint config) |
| **AG-004** | **Consciousness Integration** | 50% | Validation | 🟡 P1-HIGH | 100% consciousness commands | 3h | `internal/maximus/consciousness_client.go` |
| **AG-005** | **HITL Auth Flow** | 70% | Feature Gap | 🟡 P1-HIGH | 100% `vcli hitl` | 4h | `cmd/hitl.go`, `internal/hitl/client.go` |
| **AG-006** | **Offline Mode** | 0% | Not Implemented | 🟠 P2-MEDIUM | Offline capability | 1 semana (40h) | `cmd/root.go`, `internal/cache/` |
| **AG-007** | **Plugin System** | 10% | Incomplete | 🟠 P2-MEDIUM | Extensibility | 2 semanas (80h) | `internal/plugins/manager.go` |
| **AG-008** | **Eureka/Oraculo/Predict** | 70% | Config Gap | 🟠 P2-MEDIUM | AI service commands | Incluído em AG-001 | `internal/maximus/*_client.go` |
| **AG-009** | **Mock Redis** | 100% (mock) | Code Quality | 🟡 P1-HIGH | Auth token persistence | 4h | `internal/auth/redis_client.go` |
| **AG-010** | **Governance Workspace** | 0% | Placeholder | 🟢 P3-LOW | TUI feature | 1 semana (40h) | `internal/workspace/governance/` |

---

## 🎯 IMPACT ANALYSIS

### By Severity

**P0 - CRITICAL (2 items):**
- AG-001: Config Management → Blocks ALL backend integration
- AG-002: Active Immune Core → Blocks entire `immune` command tree

**P1 - HIGH (4 items):**
- AG-003: MAXIMUS Integration → Requires validation
- AG-004: Consciousness Integration → Requires validation
- AG-005: HITL Auth Flow → Poor UX without token save
- AG-009: Mock Redis → Violates Doutrina (no mocks in prod)

**P2 - MEDIUM (3 items):**
- AG-006: Offline Mode → Not critical for MVP
- AG-007: Plugin System → Nice to have
- AG-008: AI Services Config → Solved by AG-001

**P3 - LOW (1 item):**
- AG-010: Governance Workspace → UI placeholder

---

## 🔄 DEPENDENCY GRAPH

```
AG-001 (Config Management)
  ├── Blocks → AG-003 (MAXIMUS)
  ├── Blocks → AG-004 (Consciousness)
  ├── Blocks → AG-008 (AI Services)
  └── Enables → AG-005 (HITL Auth improvement)

AG-002 (Immune Core)
  └── Independent (can be done in parallel)

AG-009 (Mock Redis)
  └── Blocks → AG-005 (HITL full auth flow)

AG-006 (Offline Mode)
  └── Requires → AG-001 (Config for cache settings)

AG-007 (Plugin System)
  └── Independent (complex, low priority)

AG-010 (Governance Workspace)
  └── Requires → AG-003 (MAXIMUS backend)
```

---

## 🚀 EXECUTION STRATEGY

### **CRITICAL PATH (Must do first)**

**Week 1:**
1. AG-001: Config Management (1 day)
   - Unblocks AG-003, AG-004, AG-008
2. AG-002: Active Immune Core (2-3 days)
   - Enables all `immune` commands

**Week 2:**
3. AG-003: MAXIMUS Validation (3 hours)
   - Validate backend connection
4. AG-004: Consciousness Validation (3 hours)
   - Test HTTP + WebSocket
5. AG-009: Remove Mock Redis (4 hours)
   - Doutrina compliance
6. AG-005: HITL Auth Flow (4 hours)
   - Token persistence

**Result after Week 2:** 80% operacional

---

### **NICE TO HAVE (Can be deferred)**

**Week 3-4 (Optional):**
7. AG-006: Offline Mode (1 week)
   - Enhances UX, not critical
8. AG-008: AI Services (already solved by AG-001)

**Week 5-6 (Backlog):**
9. AG-007: Plugin System (2 weeks)
   - Complex feature
10. AG-010: Governance Workspace (1 week)
    - Depends on backend

---

## 📝 DETAILED BREAKDOWN

### AG-001: Config Management System
**Why P0-CRITICAL:**
- Blocks 100% of backend integration
- Every command has hardcoded endpoints
- No way to configure for prod/dev/staging

**Tasks:**
1. [ ] Read `~/.vcli/config.yaml` in `cmd/root.go` init()
2. [ ] Implement precedence: CLI flags > ENV > config file > defaults
3. [ ] Add `vcli configure` interactive command
4. [ ] Update all clients to use config

**Files to Modify:**
- `cmd/root.go`: Read config file
- `internal/config/manager.go`: Implement config struct & loader
- `cmd/maximus.go`: Use config.Get("maximus.endpoint")
- `cmd/hitl.go`: Use config.Get("hitl.endpoint")
- 8+ client files: Accept config in NewClient()

**Example config.yaml:**
```yaml
maximus:
  endpoint: "production.vertice.dev:50051"
  insecure: false

consciousness:
  endpoint: "http://consciousness.vertice.dev:8022"
  stream_url: "ws://consciousness.vertice.dev:8022/stream"

hitl:
  endpoint: "https://hitl.vertice.dev/api"
  token_file: "~/.vcli/tokens/hitl.json"

eureka:
  endpoint: "http://eureka.vertice.dev:8024"

oraculo:
  endpoint: "http://oraculo.vertice.dev:8026"

predict:
  endpoint: "http://predict.vertice.dev:8028"

immune:
  endpoint: "immune.vertice.dev:50052"
```

---

### AG-002: Active Immune Core Client
**Why P0-CRITICAL:**
- Complete command tree não funciona: `vcli immune <subcommand>`
- Proto exists, client wrapper is empty
- Backend ready, only Go client missing

**Tasks:**
1. [ ] Implement `NewImmuneClient(endpoint string) (*ImmuneClient, error)`
2. [ ] Add method: `ListAgents(ctx, filters) ([]*Agent, error)`
3. [ ] Add method: `CloneAgent(ctx, agentID) (*Agent, error)`
4. [ ] Add method: `TerminateAgent(ctx, agentID) error`
5. [ ] Add method: `StreamCytokines(ctx, handler) error`
6. [ ] Integrate in `cmd/immune.go` RunE functions

**Files to Modify:**
- `internal/grpc/immune_client.go`: Full implementation
- `cmd/immune.go`: Replace TODOs with client calls

**Proto Reference:**
- `api/grpc/immune/immune.proto`: Proto definition
- `api/grpc/immune/immune_grpc.pb.go`: Generated client

---

### AG-003: MAXIMUS Integration Validation
**Why P1-HIGH:**
- Client exists and looks correct
- Backend may be running but on different endpoint
- Need validation, not implementation

**Tasks:**
1. [ ] Verify backend status: `docker ps | grep maximus`
2. [ ] Check actual endpoint (not localhost)
3. [ ] Test with correct endpoint: `vcli maximus list --server <real-endpoint>`
4. [ ] Document correct configuration

**Potential Issues:**
- Backend in different host
- Backend using different port
- Network firewall blocking gRPC
- TLS/mTLS required but not configured

---

### AG-009: Remove Mock Redis (DOUTRINA VIOLATION)
**Why P1-HIGH:**
- **Artigo II, Seção 2:** "Fica proibida a existência de MOCKS no código principal"
- Token storage não persiste entre execuções
- Auth flow requires re-login every command

**Tasks:**
1. [ ] Uncomment `RealRedisClient` in `internal/auth/redis_client.go:119`
2. [ ] Implement Redis connection logic
3. [ ] Add feature flag: `--redis-mock` for dev mode
4. [ ] Document Redis setup: `docker run -d -p 6379:6379 redis:alpine`
5. [ ] Update `vcli hitl login` to save token in Redis

**Code Location:**
```go
// internal/auth/redis_client.go:119-125
// type RealRedisClient struct { ... }  // <-- UNCOMMENT THIS
//
// func NewRealRedisClient(addr string) (*RealRedisClient, error) {
//     client := redis.NewClient(&redis.Options{Addr: addr})
//     return &RealRedisClient{client: client}, nil
// }
```

---

## 🎯 SUCCESS CRITERIA

### AG-001 DONE quando:
- [ ] `~/.vcli/config.yaml` is read on startup
- [ ] All clients accept config
- [ ] `vcli configure` command works
- [ ] ENV vars > flags > file > defaults (precedence works)

### AG-002 DONE quando:
- [ ] `vcli immune list-agents` returns real data
- [ ] `vcli immune clone-agent <id>` clones agent
- [ ] `vcli immune stream-cytokines` streams events
- [ ] All 8+ commands functional

### AG-003 DONE quando:
- [ ] `vcli maximus list` returns decisions (not connection refused)
- [ ] `vcli maximus submit` creates decision
- [ ] `vcli maximus watch` streams events
- [ ] Documentation updated with correct endpoint

### AG-009 DONE quando:
- [ ] Real Redis client implemented
- [ ] Token persists between commands
- [ ] Mock only used in dev mode (with flag)
- [ ] Zero mocks in production code path

---

## 📈 PROGRESS TRACKING

### Current State (2025-01-22)
```
AG-001: [          ] 0% - Not started
AG-002: [          ] 0% - Not started
AG-003: [██████    ] 60% - Client exists, needs validation
AG-004: [█████     ] 50% - Client exists, needs validation
AG-005: [███████   ] 70% - Auth works, token save missing
AG-006: [          ] 0% - Placeholder only
AG-007: [█         ] 10% - Structure exists, no implementation
AG-008: [███████   ] 70% - Clients exist, config missing
AG-009: [██████████] 100% - Mock working, real needed
AG-010: [          ] 0% - Placeholder only
```

### Target State (After P0+P1)
```
AG-001: [██████████] 100% - Config system working
AG-002: [██████████] 100% - Immune commands functional
AG-003: [██████████] 100% - MAXIMUS validated
AG-004: [██████████] 100% - Consciousness validated
AG-005: [██████████] 100% - Auth flow complete
AG-009: [██████████] 100% - Real Redis in prod
```

---

**END OF AIR GAPS MATRIX**

*Padrão Pagani: Zero ambiguidade, 100% acionável.*

