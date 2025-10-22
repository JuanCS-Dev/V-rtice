# vCLI-Go - IMPLEMENTATION ROADMAP
**Data:** 2025-01-22
**Objetivo:** Levar vCLI-Go de 60% → 100% Operacional
**Timeline:** 4-6 semanas

---

## 🎯 ROADMAP OVERVIEW

```
CURRENT STATE (60%)          TARGET STATE (100%)
┌─────────────────┐          ┌─────────────────┐
│ ✅ K8s (100%)    │          │ ✅ K8s (100%)    │
│ ✅ TUI (100%)    │   →→→    │ ✅ TUI (100%)    │
│ ✅ Shell (100%)  │          │ ✅ Shell (100%)  │
│ ✅ NLP (93%)     │          │ ✅ NLP (100%)    │
│ ❌ Backend (0%)  │          │ ✅ Backend (100%)│
│ ❌ Config (0%)   │          │ ✅ Config (100%) │
│ ❌ Immune (0%)   │          │ ✅ Immune (100%) │
│ ❌ Auth (50%)    │          │ ✅ Auth (100%)   │
└─────────────────┘          └─────────────────┘

     60% Operational      →        100% Operational
```

---

## 📅 WEEK-BY-WEEK PLAN

### **WEEK 1-2: P0 BLOCKERS (CRITICAL PATH)**
**Goal:** Desbloquear 100% backend integration
**Outcome:** 80% operacional

#### Day 1-2: AG-001 - Config Management System
**Esforço:** 1 dia (8 horas)
**Owner:** Backend Team Lead

**Tasks:**
- [ ] **Day 1 Morning:** Design config.yaml schema
  ```yaml
  # ~/.vcli/config.yaml
  version: "2.0"

  backends:
    maximus:
      endpoint: "grpc://production.vertice.dev:50051"
      insecure: false
      timeout: 30s

    consciousness:
      endpoint: "http://consciousness.vertice.dev:8022"
      stream_url: "ws://consciousness.vertice.dev:8022/stream"

    hitl:
      endpoint: "https://hitl.vertice.dev/api"
      token_file: "~/.vcli/tokens/hitl.json"

    immune:
      endpoint: "grpc://immune.vertice.dev:50052"

    ai_services:
      eureka: "http://eureka.vertice.dev:8024"
      oraculo: "http://oraculo.vertice.dev:8026"
      predict: "http://predict.vertice.dev:8028"

  kubernetes:
    default_context: "production"
    default_namespace: "default"

  defaults:
    output_format: "table"
    offline_mode: false
  ```

- [ ] **Day 1 Afternoon:** Implement config loader
  ```go
  // internal/config/manager.go

  type Config struct {
      Version   string
      Backends  BackendsConfig
      Kubernetes K8sConfig
      Defaults  DefaultsConfig
  }

  func LoadConfig(path string) (*Config, error) {
      // 1. Check ~/.vcli/config.yaml
      // 2. Check env var VCLI_CONFIG_PATH
      // 3. Use defaults
  }

  func (c *Config) GetEndpoint(service string) string {
      // With precedence: ENV > file > defaults
  }
  ```

- [ ] **Day 2 Morning:** Integrate config in root.go
  ```go
  // cmd/root.go

  var globalConfig *config.Config

  func init() {
      cobra.OnInitialize(initConfig)
      // ...
  }

  func initConfig() {
      configPath := configFile
      if configPath == "" {
          home, _ := os.UserHomeDir()
          configPath = filepath.Join(home, ".vcli", "config.yaml")
      }

      var err error
      globalConfig, err = config.LoadConfig(configPath)
      if err != nil {
          // Use defaults if config doesn't exist
          globalConfig = config.DefaultConfig()
      }
  }
  ```

- [ ] **Day 2 Afternoon:** Update all clients to use config
  - `cmd/maximus.go`: Use `globalConfig.GetEndpoint("maximus")`
  - `cmd/hitl.go`: Use `globalConfig.GetEndpoint("hitl")`
  - 8 client files to update

- [ ] **Day 2 EOD:** Implement `vcli configure` command
  ```bash
  vcli configure
  # Interactive wizard:
  # 1. MAXIMUS endpoint? [localhost:50051]
  # 2. HITL endpoint? [http://localhost:8000/api]
  # 3. Save to ~/.vcli/config.yaml? [Y/n]
  ```

**Validation:**
```bash
# Test 1: Config file is read
echo "backends:
  maximus:
    endpoint: 'test.example.com:9999'
" > ~/.vcli/config.yaml

vcli maximus list --debug
# Should try to connect to test.example.com:9999

# Test 2: ENV var overrides
export VCLI_MAXIMUS_ENDPOINT=override.example.com:8888
vcli maximus list --debug
# Should try to connect to override.example.com:8888

# Test 3: CLI flag overrides all
vcli maximus list --server final.example.com:7777 --debug
# Should try to connect to final.example.com:7777
```

**Deliverables:**
- `internal/config/manager.go` (new file, ~200 LOC)
- `cmd/root.go` (modified, +50 LOC)
- `cmd/configure.go` (new file, ~150 LOC)
- 8 client files (modified, ~10 LOC each)
- **Total:** ~500 LOC

---

#### Day 3-5: AG-002 - Active Immune Core Client
**Esforço:** 2-3 dias (16-24 horas)
**Owner:** gRPC Integration Team

**Tasks:**
- [ ] **Day 3 Morning:** Study proto definition
  ```bash
  # Review proto
  cat api/proto/immune/immune.proto

  # Verify generated code
  ls -lh api/grpc/immune/
  ```

- [ ] **Day 3 Afternoon:** Implement ImmuneClient wrapper
  ```go
  // internal/grpc/immune_client.go

  type ImmuneClient struct {
      conn   *grpc.ClientConn
      client pb.ImmuneServiceClient
  }

  func NewImmuneClient(endpoint string) (*ImmuneClient, error) {
      conn, err := grpc.NewClient(endpoint,
          grpc.WithTransportCredentials(insecure.NewCredentials()),
      )
      if err != nil {
          return nil, err
      }

      return &ImmuneClient{
          conn:   conn,
          client: pb.NewImmuneServiceClient(conn),
      }, nil
  }

  func (c *ImmuneClient) ListAgents(ctx context.Context,
      filters *pb.AgentFilters) ([]*pb.Agent, error) {

      stream, err := c.client.ListAgents(ctx, &pb.ListAgentsRequest{
          Filters: filters,
      })
      if err != nil {
          return nil, err
      }

      var agents []*pb.Agent
      for {
          agent, err := stream.Recv()
          if err == io.EOF {
              break
          }
          if err != nil {
              return nil, err
          }
          agents = append(agents, agent)
      }

      return agents, nil
  }

  // Implement: CloneAgent, TerminateAgent, StreamCytokines...
  ```

- [ ] **Day 4:** Integrate in cmd/immune.go
  ```go
  // cmd/immune.go

  var immuneListAgentsCmd = &cobra.Command{
      Use:   "list-agents",
      Short: "List all adaptive immune agents",
      RunE:  runListAgents,
  }

  func runListAgents(cmd *cobra.Command, args []string) error {
      endpoint := globalConfig.GetEndpoint("immune")
      client, err := grpc.NewImmuneClient(endpoint)
      if err != nil {
          return fmt.Errorf("failed to connect: %w", err)
      }
      defer client.Close()

      ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
      defer cancel()

      agents, err := client.ListAgents(ctx, nil)
      if err != nil {
          return fmt.Errorf("failed to list agents: %w", err)
      }

      // Format output (table, json, yaml)
      formatAgents(agents, outputFormat)
      return nil
  }
  ```

- [ ] **Day 5:** Testing & Documentation
  ```bash
  # Unit tests
  go test ./internal/grpc/immune_client_test.go -v

  # Integration test (requires backend)
  vcli immune list-agents --endpoint localhost:50052
  vcli immune clone-agent <agent-id>
  vcli immune stream-cytokines
  ```

**Validation:**
```bash
# Test 1: List agents
vcli immune list-agents
# Expected: Table of agents or "no agents found"

# Test 2: Clone agent
vcli immune clone-agent agent-123-abc
# Expected: "Agent cloned successfully: agent-456-def"

# Test 3: Stream cytokines
vcli immune stream-cytokines --duration 10s
# Expected: Real-time stream of cytokine events
```

**Deliverables:**
- `internal/grpc/immune_client.go` (new implementation, ~400 LOC)
- `cmd/immune.go` (modified, +200 LOC)
- Tests: `internal/grpc/immune_client_test.go` (~300 LOC)
- **Total:** ~900 LOC

---

#### Day 6-7: AG-003 & AG-004 - Validation
**Esforço:** 6 horas total
**Owner:** QA Lead

**Tasks:**
- [ ] **Day 6 Morning:** Validate MAXIMUS backend
  ```bash
  # 1. Check backend status
  docker ps | grep maximus
  # OR
  ps aux | grep maximus_orchestrator

  # 2. Test gRPC connectivity
  grpcurl -plaintext localhost:50051 list

  # 3. Test vCLI integration
  vcli maximus list
  vcli maximus submit --type test --title "Test decision"
  vcli maximus watch <decision-id>
  ```

- [ ] **Day 6 Afternoon:** Validate Consciousness backend
  ```bash
  # 1. Check backend status
  curl http://localhost:8022/api/consciousness/state

  # 2. Test vCLI integration
  vcli maximus consciousness state
  vcli maximus consciousness esgt events --limit 10
  vcli maximus consciousness watch
  ```

- [ ] **Day 7:** Document findings & fix issues
  - Create validation report
  - Fix any connectivity issues
  - Update documentation with correct endpoints

---

### **WEEK 3: P1 HIGH PRIORITY**
**Goal:** Polish core features
**Outcome:** 90% operacional

#### Day 8: AG-009 - Remove Mock Redis
**Esforço:** 4 horas

**Tasks:**
- [ ] **Morning:** Implement RealRedisClient
  ```go
  // internal/auth/redis_client.go

  type RealRedisClient struct {
      client *redis.Client
  }

  func NewRealRedisClient(addr string) (*RealRedisClient, error) {
      client := redis.NewClient(&redis.Options{
          Addr: addr,
          Password: os.Getenv("REDIS_PASSWORD"),
          DB: 0,
      })

      // Test connection
      _, err := client.Ping(context.Background()).Result()
      if err != nil {
          return nil, fmt.Errorf("redis connection failed: %w", err)
      }

      return &RealRedisClient{client: client}, nil
  }

  func (r *RealRedisClient) Set(key, value string, expiration time.Duration) error {
      return r.client.Set(context.Background(), key, value, expiration).Err()
  }

  // Implement Get, Delete, Exists...
  ```

- [ ] **Afternoon:** Add feature flag
  ```go
  // cmd/root.go

  var useMockRedis bool

  func init() {
      rootCmd.PersistentFlags().BoolVar(&useMockRedis, "redis-mock", false,
          "Use mock Redis (dev mode only)")
  }

  func getRedisClient() (RedisClient, error) {
      if useMockRedis {
          return NewMockRedisClient(), nil
      }

      addr := globalConfig.GetString("redis.addr", "localhost:6379")
      return NewRealRedisClient(addr)
  }
  ```

**Validation:**
```bash
# Test 1: Real Redis
docker run -d -p 6379:6379 redis:alpine
vcli hitl login --username admin --password secret
# Token should persist in Redis

# Test 2: Mock mode (dev)
vcli hitl login --username admin --password secret --redis-mock
# Should work without Redis running
```

---

#### Day 9: AG-005 - HITL Auth Flow
**Esforço:** 4 horas

**Tasks:**
- [ ] Implement `vcli hitl login` with token save
  ```go
  var hitlLoginCmd = &cobra.Command{
      Use:   "login",
      Short: "Login and save token",
      RunE:  runHITLLogin,
  }

  func runHITLLogin(cmd *cobra.Command, args []string) error {
      client := hitl.NewClient(hitlEndpoint)

      resp, err := client.Login(hitlUsername, hitlPassword)
      if err != nil {
          return err
      }

      // Save token to Redis or file
      tokenStore := getTokenStore()
      tokenStore.SaveToken("hitl", resp.AccessToken, time.Duration(resp.ExpiresIn)*time.Second)

      fmt.Printf("✅ Logged in successfully\n")
      fmt.Printf("Token expires in: %d seconds\n", resp.ExpiresIn)

      return nil
  }
  ```

- [ ] Auto-load token in other commands
  ```go
  func getHITLToken() string {
      // 1. Try --token flag
      if hitlToken != "" {
          return hitlToken
      }

      // 2. Try token store
      tokenStore := getTokenStore()
      token, _ := tokenStore.GetToken("hitl")
      return token
  }
  ```

---

### **WEEK 4-6: P2 FEATURES (OPTIONAL)**
**Goal:** Complete advanced features
**Outcome:** 100% operacional + extras

#### Week 4: AG-006 - Offline Mode
**Esforço:** 1 semana (40 horas)

**High-Level Design:**
1. BadgerDB as local cache
2. Write-through strategy for reads
3. Write-behind queue for writes
4. Periodic sync with backend

**Tasks:**
- [ ] Implement cache layer
- [ ] Sync queue with retries
- [ ] Real implementation of `offline` commands

---

#### Week 5-6: AG-007 - Plugin System
**Esforço:** 2 semanas (80 horas)

**Design:**
- Plugin interface definition
- Dynamic loading (Go plugins or subprocess)
- Sandboxing (resource limits)
- Plugin registry (local + remote)

---

## 📊 PROGRESS TRACKING

### Milestones

| Milestone | Date | Status | Completion |
|-----------|------|--------|------------|
| **M1: P0 Complete** | End of Week 2 | 🟡 In Progress | 0% → 80% |
| **M2: P1 Complete** | End of Week 3 | ⏳ Pending | 80% → 90% |
| **M3: Core Features** | End of Week 4 | ⏳ Pending | 90% → 95% |
| **M4: Full Feature Set** | End of Week 6 | ⏳ Pending | 95% → 100% |

### Weekly Check-ins

**Week 1 Goals:**
- [ ] Config system operational
- [ ] Immune client implemented (50%)

**Week 2 Goals:**
- [ ] Immune client complete (100%)
- [ ] MAXIMUS validation done
- [ ] Consciousness validation done

**Week 3 Goals:**
- [ ] Mock Redis removed
- [ ] HITL auth flow complete
- [ ] All P0+P1 items done

---

## 🎯 SUCCESS CRITERIA

### Definition of Done (DoD)

**For each AIR GAP:**
1. ✅ Implementation complete (no TODOs)
2. ✅ Unit tests passing (>80% coverage)
3. ✅ Integration tests passing (against real backend)
4. ✅ Documentation updated
5. ✅ Code review approved
6. ✅ Merged to main branch

**For Overall Project:**
1. ✅ All P0 items complete (AG-001, AG-002)
2. ✅ All P1 items complete (AG-003, AG-004, AG-005, AG-009)
3. ✅ No mocks in production code
4. ✅ No hardcoded endpoints
5. ✅ 90%+ operacional (all backend commands work)

---

## 🚨 RISK MITIGATION

### Identified Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Backend Python não disponível | Medium | High | Setup local dev environment |
| gRPC proto incompatible | Low | High | Validate proto early (Day 3) |
| Config system complex | Low | Medium | Keep design simple, iterate |
| Redis setup issues | Low | Low | Docker-compose for dev |

### Contingency Plans

**If backend is not available:**
- Focus on standalone features (K8s, TUI, Shell)
- Use mock servers for integration tests
- Defer validation to when backend is ready

**If timeline slips:**
- Cut P2 features (Offline mode, Plugin system)
- Focus on P0+P1 only (80% operacional is acceptable MVP)

---

**END OF ROADMAP**

*Timeline: 4-6 weeks | Target: 100% Operacional | Status: Ready to Execute*

