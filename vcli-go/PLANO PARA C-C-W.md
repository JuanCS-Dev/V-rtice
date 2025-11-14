# 🚀 PLANO DE AÇÃO ESTRUTURADO - VCLI-GO TEST COVERAGE

**Budget Total**: $1,000 USD (Claude Code Web)
**Meta**: 90-93% test coverage global
**Coverage Atual**: 45% (469.4 pontos ganhos em 8 packages)
**Status**: Pronto para execução em Claude Code Web

---

## 📊 ESTADO ATUAL DO PROJETO

### Métricas de Coverage (2025-11-14)

| Package       | Coverage Atual | Status      | LOC  | Prioridade |
| ------------- | -------------- | ----------- | ---- | ---------- |
| investigation | 83.3%          | ✅ Complete | ~500 | -          |
| governance    | 50.3%          | ✅ Complete | ~400 | -          |
| maximus       | 29.0%          | ✅ Complete | ~600 | -          |
| data          | 81.5%          | ✅ Complete | ~350 | -          |
| ethical       | 53.0%          | ✅ Complete | ~450 | -          |
| immunis       | 29.6%          | ✅ Complete | ~380 | -          |
| threat        | 100.0%         | ✅ Complete | ~180 | -          |
| narrative     | 45.3%          | ✅ Complete | ~400 | -          |

### Packages com 0% Coverage (Alta Prioridade)

#### HTTP Clients (Fácil, Alto ROI)

- `internal/security/audit/audit.go` (~150 LOC)
- `internal/security/authz/authz.go` (~120 LOC)
- `internal/security/behavioral/analyzer.go` (~130 LOC)
- `internal/streaming/sse_client.go` (378 LOC)
- `internal/streaming/kafka_client.go` (214 LOC)

#### gRPC Clients (Complexo, Médio ROI)

- `internal/grpc/immune_client.go` (412 LOC)
- `internal/grpc/maximus_client.go` (~350 LOC)

#### Infrastructure Crítica

- `internal/orchestrator/*` (3,345 LOC) - 0% coverage
- `internal/dashboard/*` (2,398 LOC) - 0% coverage
- `internal/k8s/*` (10,325 LOC) - TODOS OS TESTES FALHANDO

### Packages com Coverage Baixo (< 40%)

- `internal/behavior/*` (9.7% coverage) - ~800 LOC
- `internal/agents/strategies/*` (36% coverage) - ~1,200 LOC
- `internal/shell/*` (0% coverage) - ~900 LOC
- `internal/workspaces/*` (0% coverage) - ~600 LOC

---

## 🎯 PLANO DE EXECUÇÃO - 4 FASES

### FASE 1: MOMENTUM CONTINUATION (Week 1)

**Budget**: $200 USD
**Tempo Estimado**: 7-10 horas
**Meta**: 45% → 60-65% coverage

#### Objetivos

1. **Complete HTTP Client Packages (0% → 75%+)**
   - `internal/security/audit/audit.go` - Audit logging client
   - `internal/security/authz/authz.go` - Authorization client
   - `internal/security/behavioral/analyzer.go` - Behavioral analysis client
   - `internal/streaming/sse_client.go` - Server-Sent Events client
   - `internal/streaming/kafka_client.go` - Kafka streaming client
   - `internal/grpc/immune_client.go` - gRPC immune system client

2. **Improve Low Coverage Packages**
   - `internal/behavior/*` (9.7% → 75%+)
   - `internal/agents/strategies/*` (36% → 75%+)

#### Tarefas Detalhadas

**Tarefa 1.1: Security Clients (~400 LOC total)**

- Arquivo: `internal/security/audit/audit_test.go`
- Testes: Constructor, HTTP methods, auth validation, error handling
- Padrão: `httptest.NewServer`, Bearer token validation
- Tempo: 2 horas
- Coverage Esperado: +30-40 pontos

**Tarefa 1.2: Streaming Clients (592 LOC total)**

- Arquivos:
  - `internal/streaming/sse_client_test.go` (378 LOC)
  - `internal/streaming/kafka_client_test.go` (214 LOC)
- Complexidade: Alta (goroutines, channels, context)
- Padrão: Mock SSE streams, Kafka producer/consumer mocks
- Tempo: 3-4 horas
- Coverage Esperado: +20-30 pontos

**Tarefa 1.3: gRPC Immune Client (412 LOC)**

- Arquivo: `internal/grpc/immune_client_test.go`
- Complexidade: Alta (gRPC mocking, proto messages)
- Padrão: `grpc.NewServer()` + `bufconn.Listener`
- Tempo: 2-3 horas
- Coverage Esperado: +15-25 pontos

**Tarefa 1.4: Behavior Package Improvement**

- Arquivo: `internal/behavior/clients_test.go` (expandir)
- Coverage: 9.7% → 75%+
- Tempo: 1 hora
- Coverage Esperado: +65 pontos

**Tarefa 1.5: Agents Strategies Improvement**

- Arquivos: `internal/agents/strategies/*_test.go` (expandir)
- Coverage: 36% → 75%+
- Tempo: 1 hora
- Coverage Esperado: +40 pontos

#### Entregáveis Fase 1

- [ ] 6 novos arquivos de teste criados
- [ ] 4 arquivos de teste expandidos
- [ ] +150-200 coverage points
- [ ] Commit após cada package testado
- [ ] `PLAN_STATUS.md` atualizado

#### Comandos para Executar

```bash
# Após cada package testado:
go test ./internal/security/... -cover
go test ./internal/streaming/... -cover
go test ./internal/grpc/... -cover
go test ./internal/behavior/... -cover
go test ./internal/agents/strategies/... -cover

# Coverage report completo:
go test ./internal/... -coverprofile=coverage.out
go tool cover -func=coverage.out | grep total
```

---

### FASE 2: INFRASTRUCTURE CRÍTICA (Week 2)

**Budget**: $400 USD (maior budget devido à complexidade)
**Tempo Estimado**: 13-20 horas
**Meta**: 60-65% → 78-82% coverage

#### Objetivos

1. **FIX K8s Tests (10,325 LOC) - PRIORITY #1**
   - Problema: Todos os testes esperam cluster K8s real
   - Solução: Usar `fake.NewSimpleClientset()` do `k8s.io/client-go/kubernetes/fake`
   - Impact: Maior ganho de coverage possível

2. **Test Orchestrator Package (3,345 LOC)**
   - 0% coverage → 75%+
   - Orquestração de workflows e tasks

3. **Test Dashboard Package (2,398 LOC)**
   - 0% coverage → 75%+
   - TUI dashboards (já implementados, mas sem testes)

#### Tarefas Detalhadas

**Tarefa 2.1: K8s Tests Comprehensive Fix**

**Problema Atual**:

```
Error: kubernetes cluster unreachable: Get "https://localhost:8080/version":
dial tcp [::1]:8080: connect: connection refused
```

**Solução**:

```go
// Padrão atual (ERRADO):
func TestSomeK8sFunction(t *testing.T) {
    client, _ := NewK8sClient() // tenta conectar ao cluster real
    // ...
}

// Padrão correto (USAR ESTE):
import "k8s.io/client-go/kubernetes/fake"

func TestSomeK8sFunction(t *testing.T) {
    fakeClient := fake.NewSimpleClientset()
    // Pre-populate com objetos mock se necessário:
    fakeClient := fake.NewSimpleClientset(
        &corev1.Pod{
            ObjectMeta: metav1.ObjectMeta{
                Name: "test-pod",
                Namespace: "default",
            },
        },
    )
    // Execute testes com fakeClient
}
```

**Arquivos a Corrigir** (~30 arquivos de teste):

- `internal/k8s/*_test.go` - Todos os testes K8s
- Substituir `NewK8sClient()` por `fake.NewSimpleClientset()`
- Adicionar fixtures/mocks para objetos K8s

**Tempo**: 8-10 horas (muitos arquivos)
**Coverage Esperado**: +300-400 pontos (HUGE GAIN)

**Tarefa 2.2: Orchestrator Package**

Arquivos principais (3,345 LOC total):

- `internal/orchestrator/engine.go` (~800 LOC)
- `internal/orchestrator/workflow.go` (~600 LOC)
- `internal/orchestrator/task_executor.go` (~500 LOC)
- `internal/orchestrator/state_machine.go` (~450 LOC)
- `internal/orchestrator/scheduler.go` (~400 LOC)

Criar testes:

- `engine_test.go` - Workflow execution engine
- `workflow_test.go` - Workflow definition and validation
- `task_executor_test.go` - Task execution and error handling
- `state_machine_test.go` - State transitions
- `scheduler_test.go` - Task scheduling logic

**Tempo**: 4-6 horas
**Coverage Esperado**: +100-120 pontos

**Tarefa 2.3: Dashboard Package**

Arquivos principais (2,398 LOC total):

- `internal/dashboard/k8s/monitor.go` (~400 LOC)
- `internal/dashboard/services/health.go` (~380 LOC)
- `internal/dashboard/threat/intel.go` (~350 LOC)
- `internal/dashboard/network/monitor.go` (~320 LOC)
- `internal/dashboard/system/overview.go` (~280 LOC)
- `internal/dashboard/layout.go` (~268 LOC)
- `internal/dashboard/types.go` (~200 LOC)

Estratégia de teste:

- Mock data sources (K8s client, HTTP clients)
- Test rendering logic (data formatting, layout calculation)
- Test refresh/update mechanisms
- Test error handling and fallback displays

**Tempo**: 3-4 horas
**Coverage Esperado**: +70-90 pontos

#### Entregáveis Fase 2

- [ ] K8s tests todos passando (fix completo)
- [ ] Orchestrator package: 75%+ coverage
- [ ] Dashboard package: 75%+ coverage
- [ ] +470-610 coverage points (maior ganho do plano)
- [ ] Commits organizados por subsistema
- [ ] `PLAN_STATUS.md` atualizado

#### Comandos para Executar

```bash
# K8s tests fix verification:
go test ./internal/k8s/... -v -count=1

# Orchestrator tests:
go test ./internal/orchestrator/... -cover -v

# Dashboard tests:
go test ./internal/dashboard/... -cover -v

# Full report:
go test ./internal/... -coverprofile=coverage.out
go tool cover -func=coverage.out | grep total
```

---

### FASE 3: AGENTS SYSTEM (Week 3)

**Budget**: $200 USD
**Tempo Estimado**: 7-10 horas
**Meta**: 78-82% → 85-88% coverage

#### Objetivos

1. **Test Agent Packages** (4 main agents)
   - `internal/agents/dev_senior/*` (~1,200 LOC)
   - `internal/agents/arquiteto/*` (~900 LOC)
   - `internal/agents/tester/*` (~800 LOC)
   - `internal/agents/diagnosticador/*` (~700 LOC)

2. **Complete Agents Infrastructure**
   - `internal/agents/base/*` (agent base classes)
   - `internal/agents/registry/*` (agent registry)
   - `internal/agents/communication/*` (inter-agent comms)

#### Tarefas Detalhadas

**Tarefa 3.1: Dev Senior Agent**

- Arquivo: `internal/agents/dev_senior/agent_test.go`
- Funcionalidade: Senior developer decision-making
- Testes: Code analysis, refactoring suggestions, architecture decisions
- Tempo: 2-3 horas
- Coverage Esperado: +40-50 pontos

**Tarefa 3.2: Arquiteto Agent**

- Arquivo: `internal/agents/arquiteto/agent_test.go`
- Funcionalidade: System architecture design
- Testes: Design pattern selection, component design, integration planning
- Tempo: 2 horas
- Coverage Esperado: +30-40 pontos

**Tarefa 3.3: Tester Agent**

- Arquivo: `internal/agents/tester/agent_test.go`
- Funcionalidade: Test generation and validation
- Testes: Test case generation, coverage analysis, test strategies
- Tempo: 2 horas
- Coverage Esperado: +25-35 pontos

**Tarefa 3.4: Diagnosticador Agent**

- Arquivo: `internal/agents/diagnosticador/agent_test.go`
- Funcionalidade: System diagnostics and problem detection
- Testes: Error detection, root cause analysis, remediation suggestions
- Tempo: 1-2 horas
- Coverage Esperado: +20-30 pontos

**Tarefa 3.5: Agents Infrastructure**

- Arquivos:
  - `internal/agents/base/base_agent_test.go`
  - `internal/agents/registry/registry_test.go`
  - `internal/agents/communication/comm_test.go`
- Tempo: 2 horas
- Coverage Esperado: +20-30 pontos

#### Entregáveis Fase 3

- [ ] 4 agent packages testados (dev_senior, arquiteto, tester, diagnosticador)
- [ ] Agents infrastructure testada
- [ ] +135-185 coverage points
- [ ] `PLAN_STATUS.md` atualizado
- [ ] Documentation: `AGENTS_TESTING_GUIDE.md`

#### Comandos para Executar

```bash
# Test each agent:
go test ./internal/agents/dev_senior/... -cover -v
go test ./internal/agents/arquiteto/... -cover -v
go test ./internal/agents/tester/... -cover -v
go test ./internal/agents/diagnosticador/... -cover -v

# Test infrastructure:
go test ./internal/agents/base/... -cover -v
go test ./internal/agents/registry/... -cover -v
go test ./internal/agents/communication/... -cover -v

# Full report:
go test ./internal/... -coverprofile=coverage.out
go tool cover -func=coverage.out | grep total
```

---

### FASE 4: POLISH & DOCUMENTATION (Week 4)

**Budget**: $200 USD
**Tempo Estimado**: 7-10 horas
**Meta**: 85-88% → 90-93% coverage

#### Objetivos

1. **Complete Remaining Packages**
   - `internal/shell/*` (0% → 75%+) - ~900 LOC
   - `internal/workspaces/*` (0% → 75%+) - ~600 LOC
   - Outros packages pequenos com <50% coverage

2. **Create Comprehensive Documentation**
   - Testing guide
   - Coverage patterns documentation
   - HTTP client testing best practices
   - gRPC testing best practices
   - K8s testing patterns

3. **Quality Assurance**
   - Run full test suite
   - Generate HTML coverage report
   - Identify remaining gaps
   - Create final report

#### Tarefas Detalhadas

**Tarefa 4.1: Shell Package**

- Arquivos: `internal/shell/*_test.go`
- Funcionalidade: Interactive shell, completers, history
- Testes: Command parsing, completion logic, history management
- Tempo: 2-3 horas
- Coverage Esperado: +30-40 pontos

**Tarefa 4.2: Workspaces Package**

- Arquivos: `internal/workspaces/*_test.go`
- Funcionalidade: Workspace management, project switching
- Testes: Workspace creation, switching, configuration
- Tempo: 1-2 horas
- Coverage Esperado: +20-30 pontos

**Tarefa 4.3: Fill Coverage Gaps**

- Identify packages still <75% coverage
- Create targeted tests for uncovered code paths
- Focus on error handling and edge cases
- Tempo: 2 horas
- Coverage Esperado: +20-30 pontos

**Tarefa 4.4: Documentation Creation**

**4.4.1: Testing Guide** (`TESTING_GUIDE.md`)

```markdown
# VCLI-GO Testing Guide

## Testing Patterns

### HTTP Client Testing

[Pattern examples with httptest.NewServer]

### gRPC Client Testing

[Pattern examples with bufconn.Listener]

### K8s Testing

[Pattern examples with fake.NewSimpleClientset]

### Streaming Testing

[Pattern examples with goroutines and channels]
```

**4.4.2: Backend Endpoints Documentation** (`BACKEND_ENDPOINTS.md`)

- List all backend service endpoints
- Request/response schemas
- Authentication requirements
- Example curl commands

**4.4.3: Error Handling Documentation** (`ERROR_HANDLING.md`)

- Error types and handling patterns
- Retry logic
- Circuit breaker usage
- Error logging patterns

**4.4.4: User Guide** (`USER_GUIDE.md`)

- Installation
- Configuration
- Command reference
- Dashboard usage
- Troubleshooting

**Tempo para documentação**: 2-3 horas

**Tarefa 4.5: Final Quality Check**

```bash
# Generate HTML coverage report:
go test ./internal/... -coverprofile=coverage.out
go tool cover -html=coverage.out -o coverage.html

# Run race detector:
go test -race ./internal/...

# Run benchmarks:
go test -bench=. ./internal/...

# Static analysis:
go vet ./...
golangci-lint run

# Generate final report
```

Tempo: 1-2 horas

#### Entregáveis Fase 4

- [ ] Shell package: 75%+ coverage
- [ ] Workspaces package: 75%+ coverage
- [ ] Coverage gaps filled
- [ ] 4 documentation files created:
  - `TESTING_GUIDE.md`
  - `BACKEND_ENDPOINTS.md`
  - `ERROR_HANDLING.md`
  - `USER_GUIDE.md`
- [ ] HTML coverage report generated
- [ ] Final completion report: `COVERAGE_SPRINT_FINAL_REPORT.md`
- [ ] +70-100 coverage points
- [ ] Target: 90-93% coverage achieved

#### Comandos para Executar

```bash
# Test remaining packages:
go test ./internal/shell/... -cover -v
go test ./internal/workspaces/... -cover -v

# Full quality check:
go test ./internal/... -coverprofile=coverage.out -v
go tool cover -html=coverage.out -o coverage.html
go test -race ./internal/...
go vet ./...

# Generate final metrics:
go tool cover -func=coverage.out | grep total > /tmp/final_coverage.txt
```

---

## 📊 MÉTRICAS DE SUCESSO

### Coverage Targets por Fase

| Fase   | Coverage Inicial | Coverage Final | Ganho       | Budget |
| ------ | ---------------- | -------------- | ----------- | ------ |
| Fase 1 | 45%              | 60-65%         | +15-20%     | $200   |
| Fase 2 | 60-65%           | 78-82%         | +13-22%     | $400   |
| Fase 3 | 78-82%           | 85-88%         | +3-10%      | $200   |
| Fase 4 | 85-88%           | 90-93%         | +2-8%       | $200   |
| TOTAL  | 45%              | **90-93%**     | **+45-48%** | $1,000 |

### Test Lines Estimados

| Fase   | Test Files Criados | Test Lines Escritas | Avg Lines/File |
| ------ | ------------------ | ------------------- | -------------- |
| Fase 1 | 10 files           | ~4,000 lines        | 400            |
| Fase 2 | 35 files           | ~8,000 lines        | 230            |
| Fase 3 | 8 files            | ~3,500 lines        | 440            |
| Fase 4 | 5 files            | ~2,000 lines        | 400            |
| TOTAL  | **58 files**       | **~17,500 lines**   | 300            |

### Coverage Points Ganhos

| Fase   | Coverage Points | Packages Testados | Avg Points/Package |
| ------ | --------------- | ----------------- | ------------------ |
| Fase 1 | +150-200        | 8 packages        | 20-25              |
| Fase 2 | +470-610        | 3 packages        | 157-203 (K8s!)     |
| Fase 3 | +135-185        | 7 packages        | 19-26              |
| Fase 4 | +70-100         | 4 packages        | 18-25              |
| TOTAL  | **+825-1095**   | **22 packages**   | 38-50              |

---

## 🎯 COMANDOS ÚTEIS PARA CLAUDE CODE WEB

### Verificar Coverage de um Package

```bash
# Coverage de um package específico:
go test ./internal/PACKAGE_NAME/... -cover

# Coverage detalhado:
go test ./internal/PACKAGE_NAME/... -coverprofile=coverage.out
go tool cover -func=coverage.out
```

### Coverage Report Completo

```bash
# Gerar coverage de todos os packages:
go test ./internal/... -coverprofile=coverage.out

# Ver coverage total:
go tool cover -func=coverage.out | grep total

# Gerar HTML report:
go tool cover -html=coverage.out -o coverage.html
```

### Identificar Packages sem Testes

```bash
# Listar packages sem testes (sorted by LOC):
bash /tmp/find_untested.sh
```

### Run Tests com Verbosity

```bash
# Run tests verbose:
go test ./internal/PACKAGE/... -v

# Run specific test:
go test ./internal/PACKAGE/... -run TestName -v

# Run with race detector:
go test ./internal/PACKAGE/... -race -v
```

### Build e Lint

```bash
# Build:
make build

# Run linters:
go vet ./...
golangci-lint run
```

---

## 📝 TEMPLATE DE COMMIT MESSAGES

Use este padrão para cada commit:

```
test(PACKAGE): Add comprehensive tests for COMPONENT

- Test FILE1 with X test cases
- Test FILE2 with Y test cases
- Coverage: START% → END% (+GAIN%)
- Total test lines: LINES

Patterns tested:
- HTTP client with httptest.NewServer / gRPC mock / K8s fake client
- Authorization validation (Bearer tokens)
- Error handling (4xx, 5xx, network failures)
- Request/response validation
```

Exemplo real:

```
test(narrative): Add comprehensive FilterClient tests

- Test AnalyzeContent, Health, SimpleHealth methods
- Test cache and database stats endpoints
- Coverage: 20.9% → 45.3% (+24.4%)
- Total test lines: 546

Patterns tested:
- HTTP client with httptest.NewServer
- Authorization validation (Bearer tokens)
- Cognitive defense report validation
- Error handling (400, 403, 404, 500, network failures)
```

---

## 🚨 TROUBLESHOOTING COMUM

### Problema 1: K8s Tests Falhando

**Sintoma**: `kubernetes cluster unreachable: Get "https://localhost:8080/version"`

**Solução**:

```go
import "k8s.io/client-go/kubernetes/fake"

func TestK8sFunction(t *testing.T) {
    // ANTES (errado):
    // client, _ := NewK8sClient()

    // DEPOIS (correto):
    fakeClient := fake.NewSimpleClientset()

    // Pre-populate com objetos se necessário:
    fakeClient := fake.NewSimpleClientset(
        &corev1.Pod{...},
        &corev1.Service{...},
    )
}
```

### Problema 2: gRPC Tests Setup

**Sintoma**: `panic: runtime error: invalid memory address or nil pointer dereference`

**Solução**:

```go
import (
    "google.golang.org/grpc"
    "google.golang.org/grpc/test/bufconn"
)

func TestGRPCClient(t *testing.T) {
    // Setup in-memory gRPC server:
    lis := bufconn.Listen(1024 * 1024)
    s := grpc.NewServer()
    pb.RegisterServiceServer(s, &mockServer{})

    go func() {
        s.Serve(lis)
    }()
    defer s.Stop()

    // Create client:
    conn, _ := grpc.DialContext(ctx, "bufnet",
        grpc.WithContextDialer(func(context.Context, string) (net.Conn, error) {
            return lis.Dial()
        }),
        grpc.WithInsecure(),
    )
    defer conn.Close()

    client := pb.NewServiceClient(conn)
    // Run tests...
}
```

### Problema 3: Streaming Tests (SSE/Kafka)

**Sintoma**: `test timeout exceeded: 10m0s`

**Solução**: Use context with timeout e goroutines com proper cleanup:

```go
func TestSSEClient(t *testing.T) {
    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer cancel()

    // Mock SSE server:
    server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        flusher, _ := w.(http.Flusher)
        w.Header().Set("Content-Type", "text/event-stream")

        for i := 0; i < 3; i++ {
            fmt.Fprintf(w, "data: message %d\n\n", i)
            flusher.Flush()
            time.Sleep(100 * time.Millisecond)
        }
    }))
    defer server.Close()

    client := NewSSEClient(server.URL)
    events, err := client.Stream(ctx)

    // Collect events with timeout:
    var received []string
    for {
        select {
        case event := <-events:
            received = append(received, event)
        case <-ctx.Done():
            t.Fatal("timeout waiting for events")
        }
    }
}
```

### Problema 4: Race Conditions Detectadas

**Sintoma**: `WARNING: DATA RACE` ao rodar `go test -race`

**Solução**: Use sync primitives:

```go
import "sync"

type SafeClient struct {
    mu    sync.RWMutex
    cache map[string]interface{}
}

func (c *SafeClient) Get(key string) interface{} {
    c.mu.RLock()
    defer c.mu.RUnlock()
    return c.cache[key]
}

func (c *SafeClient) Set(key string, value interface{}) {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.cache[key] = value
}
```

---

## 📚 TESTING PATTERNS REFERENCE

### Pattern 1: HTTP Client com httptest.NewServer

```go
func TestHTTPClient(t *testing.T) {
    t.Run("successful request", func(t *testing.T) {
        server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            // Validate request:
            assert.Equal(t, "/api/endpoint", r.URL.Path)
            assert.Equal(t, "POST", r.Method)
            assert.Equal(t, "Bearer token123", r.Header.Get("Authorization"))

            // Decode request body:
            var req RequestType
            err := json.NewDecoder(r.Body).Decode(&req)
            require.NoError(t, err)

            // Validate request fields:
            assert.Equal(t, "expected-value", req.Field)

            // Return mock response:
            resp := ResponseType{
                Success: true,
                Data:    "result",
            }
            w.WriteHeader(http.StatusOK)
            json.NewEncoder(w).Encode(resp)
        }))
        defer server.Close()

        // Create client and execute:
        client := NewClient(server.URL, "token123")
        result, err := client.Method(args)

        // Assertions:
        require.NoError(t, err)
        assert.True(t, result.Success)
        assert.Equal(t, "result", result.Data)
    })

    t.Run("error - 404 not found", func(t *testing.T) {
        server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            w.WriteHeader(http.StatusNotFound)
            json.NewEncoder(w).Encode(map[string]string{
                "error": "resource not found",
            })
        }))
        defer server.Close()

        client := NewClient(server.URL, "token123")
        _, err := client.Method(args)

        require.Error(t, err)
        assert.Contains(t, err.Error(), "not found")
    })

    t.Run("error - network failure", func(t *testing.T) {
        // Use invalid URL:
        client := NewClient("http://invalid:99999", "token123")
        _, err := client.Method(args)

        require.Error(t, err)
    })
}
```

### Pattern 2: Constructor Testing

```go
func TestNewClient(t *testing.T) {
    t.Run("with custom URL and token", func(t *testing.T) {
        client := NewClient("http://custom:8080", "custom-token")

        assert.NotNil(t, client)
        assert.Equal(t, "http://custom:8080", client.baseURL)
        assert.Equal(t, "custom-token", client.authToken)
    })

    t.Run("with default URL", func(t *testing.T) {
        client := NewClient("", "token")

        assert.NotNil(t, client)
        assert.Equal(t, "http://localhost:8080", client.baseURL) // default
    })

    t.Run("with empty token", func(t *testing.T) {
        client := NewClient("http://localhost", "")

        assert.NotNil(t, client)
        assert.Equal(t, "", client.authToken)
    })
}
```

### Pattern 3: Error Path Coverage

```go
func TestClientErrorHandling(t *testing.T) {
    tests := []struct {
        name           string
        statusCode     int
        responseBody   string
        expectedError  string
    }{
        {
            name:         "400 bad request",
            statusCode:   http.StatusBadRequest,
            responseBody: `{"error": "invalid input"}`,
            expectedError: "invalid input",
        },
        {
            name:         "401 unauthorized",
            statusCode:   http.StatusUnauthorized,
            responseBody: `{"error": "unauthorized"}`,
            expectedError: "unauthorized",
        },
        {
            name:         "403 forbidden",
            statusCode:   http.StatusForbidden,
            responseBody: `{"error": "access denied"}`,
            expectedError: "access denied",
        },
        {
            name:         "404 not found",
            statusCode:   http.StatusNotFound,
            responseBody: `{"error": "not found"}`,
            expectedError: "not found",
        },
        {
            name:         "500 internal server error",
            statusCode:   http.StatusInternalServerError,
            responseBody: `{"error": "server error"}`,
            expectedError: "server error",
        },
        {
            name:         "503 service unavailable",
            statusCode:   http.StatusServiceUnavailable,
            responseBody: `{"error": "service unavailable"}`,
            expectedError: "service unavailable",
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
                w.WriteHeader(tt.statusCode)
                w.Write([]byte(tt.responseBody))
            }))
            defer server.Close()

            client := NewClient(server.URL, "token")
            _, err := client.Method(args)

            require.Error(t, err)
            assert.Contains(t, err.Error(), tt.expectedError)
        })
    }
}
```

### Pattern 4: Multipart File Upload Testing

```go
func TestUploadFile(t *testing.T) {
    t.Run("successful file upload", func(t *testing.T) {
        server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            assert.Equal(t, "POST", r.Method)

            // Parse multipart form:
            err := r.ParseMultipartForm(10 << 20) // 10MB
            require.NoError(t, err)

            // Verify file field:
            file, header, err := r.FormFile("file")
            require.NoError(t, err)
            defer file.Close()

            assert.Equal(t, "test.txt", header.Filename)

            // Read file content:
            content, _ := io.ReadAll(file)
            assert.Equal(t, "test content", string(content))

            // Return success:
            json.NewEncoder(w).Encode(map[string]string{
                "status": "uploaded",
            })
        }))
        defer server.Close()

        // Create temp file:
        tmpFile, err := os.CreateTemp("", "test-*.txt")
        require.NoError(t, err)
        defer os.Remove(tmpFile.Name())

        _, err = tmpFile.WriteString("test content")
        require.NoError(t, err)
        tmpFile.Close()

        // Upload:
        client := NewClient(server.URL, "token")
        result, err := client.UploadFile(tmpFile.Name())

        require.NoError(t, err)
        assert.Equal(t, "uploaded", result.Status)
    })
}
```

---

## 🎯 CHECKPOINT SYSTEM

Após cada fase, execute este checklist:

### Checkpoint Fase 1

- [ ] Todos os testes passam: `go test ./internal/... -v`
- [ ] Coverage >= 60%: `go tool cover -func=coverage.out | grep total`
- [ ] Nenhuma race condition: `go test -race ./internal/...`
- [ ] Build successful: `make build`
- [ ] `PLAN_STATUS.md` atualizado
- [ ] Git commit feito com mensagem descritiva
- [ ] Push para remote: `git push`

### Checkpoint Fase 2

- [ ] K8s tests todos passando: `go test ./internal/k8s/... -v`
- [ ] Orchestrator tests: >= 75% coverage
- [ ] Dashboard tests: >= 75% coverage
- [ ] Coverage >= 78%: `go tool cover -func=coverage.out | grep total`
- [ ] Nenhuma race condition: `go test -race ./internal/...`
- [ ] `PLAN_STATUS.md` atualizado
- [ ] Git commit + push

### Checkpoint Fase 3

- [ ] Agents tests passam: `go test ./internal/agents/... -v`
- [ ] Coverage >= 85%: `go tool cover -func=coverage.out | grep total`
- [ ] `AGENTS_TESTING_GUIDE.md` criado
- [ ] `PLAN_STATUS.md` atualizado
- [ ] Git commit + push

### Checkpoint Fase 4

- [ ] Shell + workspaces tests: >= 75% coverage
- [ ] Coverage >= 90%: `go tool cover -func=coverage.out | grep total`
- [ ] Documentação completa (4 arquivos criados)
- [ ] HTML coverage report gerado
- [ ] `COVERAGE_SPRINT_FINAL_REPORT.md` criado
- [ ] `PLAN_STATUS.md` atualizado para "COMPLETE"
- [ ] Git commit + push

---

## 📈 PROGRESS TRACKING

Use esta tabela para track progress em tempo real:

| Fase   | Status     | Coverage Atual | Coverage Esperado | Tempo Gasto | Budget Gasto |
| ------ | ---------- | -------------- | ----------------- | ----------- | ------------ |
| Fase 1 | ⏸️ Pending | 45%            | 60-65%            | 0h          | $0           |
| Fase 2 | ⏸️ Pending | -              | 78-82%            | 0h          | $0           |
| Fase 3 | ⏸️ Pending | -              | 85-88%            | 0h          | $0           |
| Fase 4 | ⏸️ Pending | -              | 90-93%            | 0h          | $0           |

**Status Options**: ⏸️ Pending | 🏃 In Progress | ✅ Complete | ⚠️ Blocked

---

## 🚀 QUICK START PARA CLAUDE CODE WEB

### Passo 1: Abrir Projeto

```bash
cd /home/juan/vertice-dev/vcli-go
```

### Passo 2: Verificar Coverage Atual

```bash
go test ./internal/... -coverprofile=coverage.out
go tool cover -func=coverage.out | grep total
```

### Passo 3: Começar Fase 1

```bash
# Identificar packages sem testes:
bash /tmp/find_untested.sh

# Começar com security/audit:
# Ler arquivo: internal/security/audit/audit.go
# Criar teste: internal/security/audit/audit_test.go
# Pattern: httptest.NewServer + Bearer token validation
```

### Passo 4: Test Loop

```bash
# Após criar cada arquivo de teste:
go test ./internal/PACKAGE/... -cover -v

# Commit:
git add internal/PACKAGE/*_test.go
git commit -m "test(PACKAGE): Add comprehensive tests"
git push
```

### Passo 5: Repeat Until 90%+ Coverage

---

## 📞 SUPPORT & REFERENCES

### Documentos de Referência

- `PLAN_STATUS.md` - Overall progress tracker
- `SESSION_SNAPSHOT_2025-11-14_CONTINUATION.md` - Detailed previous session notes
- `TESTING_GUIDE.md` - Comprehensive testing patterns (criar na Fase 4)

### Go Testing Resources

- Go testing package: https://pkg.go.dev/testing
- httptest package: https://pkg.go.dev/net/http/httptest
- testify assertions: https://pkg.go.dev/github.com/stretchr/testify
- K8s fake client: https://pkg.go.dev/k8s.io/client-go/kubernetes/fake

### Comandos de Diagnóstico

```bash
# Ver packages sem coverage:
bash /tmp/find_untested.sh

# Coverage por package:
go test ./internal/... -coverprofile=coverage.out
go tool cover -func=coverage.out | sort -k3 -n

# Identificar código não testado:
go tool cover -html=coverage.out -o coverage.html
# Abrir coverage.html no browser
```

---

## 🎉 FINAL DELIVERABLES

Ao final do plano ($1,000 gastos), você terá:

### Code

- ✅ 90-93% test coverage global
- ✅ ~17,500 lines of test code
- ✅ 58 new test files
- ✅ K8s tests fully functional (no cluster dependency)
- ✅ All packages with >= 75% coverage
- ✅ Zero race conditions
- ✅ Full build success

### Documentation

- ✅ `TESTING_GUIDE.md` - Comprehensive testing patterns
- ✅ `BACKEND_ENDPOINTS.md` - API documentation
- ✅ `ERROR_HANDLING.md` - Error handling patterns
- ✅ `USER_GUIDE.md` - End-user documentation
- ✅ `AGENTS_TESTING_GUIDE.md` - Agent testing specifics
- ✅ `COVERAGE_SPRINT_FINAL_REPORT.md` - Final report

### Reports

- ✅ HTML coverage report (`coverage.html`)
- ✅ Coverage metrics by package
- ✅ Race detector report (clean)
- ✅ Benchmark results

### Git History

- ✅ ~50-60 commits (organized by phase)
- ✅ Clean commit messages following template
- ✅ All code pushed to remote

---

**Status**: ✅ PLANO PRONTO PARA EXECUÇÃO
**Budget**: $1,000 USD
**Timeline**: 4 semanas (~34-50 horas)
**Target**: 90-93% test coverage

**Próximo Passo**: Abrir este arquivo no Claude Code Web e começar Fase 1

---

_Plano criado: 2025-11-14_
_Baseado em: PLAN_STATUS.md + SESSION_SNAPSHOT_2025-11-14_CONTINUATION.md_
_Estratégia: Diversificação de alto ROI + Infrastructure crítica + Polish_
_Meta ambiciosa mas alcançável com budget alocado_

---

## 🔒 DEPENDABOT VULNERABILITIES (2025-11-14)

**Total**: 29 vulnerabilities detectadas no repositório  
**Severidade**: 2 critical | 10 high | 15 moderate | 2 low  
**Link**: https://github.com/JuanCS-Dev/V-rtice/security/dependabot

### Ação Requerida

Após completar as fases de test coverage, será necessário:

1. **Revisar** todas as 29 vulnerabilidades
2. **Atualizar** dependências afetadas
3. **Testar** se as atualizações não quebram funcionalidades
4. **Verificar** se há breaking changes nas atualizações
5. **Documentar** mudanças necessárias no código

### Prioridade de Resolução

1. **Critical (2)**: Resolver imediatamente
2. **High (10)**: Resolver na mesma sprint
3. **Moderate (15)**: Resolver no próximo ciclo
4. **Low (2)**: Resolver quando possível

---

## 📈 PROGRESSO FASE 1 (2025-11-14)

### ✅ Completado

**Kafka Client Tests** (`internal/streaming/kafka_client_test.go`)
- ✅ 688 linhas de testes
- ✅ Coverage: 26.6% do package streaming
- ✅ Testes: StreamTopic, StreamTopics, PublishMessage, GetTopicInfo, ListTopics
- ✅ Padrões: gRPC mock com bufconn, server-side streaming, error handling
- ✅ Commit: `5bbad6c`

**ImmuneClient Tests** (`internal/grpc/immune_client_test.go`)
- ✅ 1047 linhas de testes  
- ✅ Coverage: 29.8% do package grpc
- ✅ Testes: 17 métodos (agents, lymphnodes, cytokines, hormones, health)
- ✅ Padrões: gRPC mock, streaming, complex protobuf messages
- ✅ Commit: `7e7a821`

### 📊 Estatísticas

- **Total de linhas de teste criadas**: 1,735
- **Packages testados**: 2 (streaming, grpc)
- **Coverage médio dos packages**: 28.2%
- **Tempo gasto**: ~3-4 horas
- **Padrão de qualidade**: Boris Cherny (type-safe, zero debt)

### 🎯 Próximos Passos

Continuar com os itens restantes da FASE 1:
1. ~~Kafka client tests~~ ✅
2. ~~ImmuneClient tests~~ ✅
3. Security clients (audit, authz, behavioral)
4. SSE client tests
5. Behavior package expansion
6. Agent strategies expansion

---

_Última atualização: 2025-11-14 21:25 UTC_
_Branch: claude/fix-security-vulnerabilities-01VFHUEgdQ6eRJ8g3y8xMuQ2_
