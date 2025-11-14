# VCLI-GO Testing Guide

**Version**: 1.0
**Last Updated**: 2025-11-14
**Coverage Target**: 90-93%
**Standards**: Boris Cherny (Type-safe, Zero Debt, Comprehensive)

---

## Table of Contents

1. [Testing Philosophy](#testing-philosophy)
2. [Testing Patterns](#testing-patterns)
3. [Coverage Metrics](#coverage-metrics)
4. [Package-Specific Guides](#package-specific-guides)
5. [Best Practices](#best-practices)
6. [Common Pitfalls](#common-pitfalls)
7. [Tools and Commands](#tools-and-commands)

---

## Testing Philosophy

### Boris Cherny Standards

All tests in vcli-go follow **Boris Cherny's** senior engineer principles:

✅ **Type-Safe**: Use proper Go types, avoid `interface{}` abuse
✅ **Zero Technical Debt**: No TODOs, placeholders, or skipped tests
✅ **Comprehensive**: Test success paths, error paths, and edge cases
✅ **Table-Driven**: Use table-driven tests for multiple scenarios
✅ **Clean Code**: Clear naming, well-organized structure
✅ **Fast**: Unit tests should run in milliseconds

### Coverage Goals

- **Package Minimum**: 75% coverage per package
- **Project Target**: 90-93% global coverage
- **Critical Packages**: 95%+ coverage (security, streaming, agents)

---

## Testing Patterns

### Pattern 1: HTTP Client Testing with httptest

**Use Case**: Testing HTTP clients (audit, authz, behavioral, governance, etc.)

```go
func TestHTTPClient(t *testing.T) {
    t.Run("successful request", func(t *testing.T) {
        server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            // Validate request
            assert.Equal(t, "/api/endpoint", r.URL.Path)
            assert.Equal(t, "POST", r.Method)
            assert.Equal(t, "Bearer token123", r.Header.Get("Authorization"))

            // Decode request body
            var req RequestType
            err := json.NewDecoder(r.Body).Decode(&req)
            require.NoError(t, err)

            // Return mock response
            w.WriteHeader(http.StatusOK)
            json.NewEncoder(w).Encode(ResponseType{Success: true})
        }))
        defer server.Close()

        client := NewClient(server.URL, "token123")
        result, err := client.Method(args)

        require.NoError(t, err)
        assert.True(t, result.Success)
    })
}
```

**Packages Using This**: `security/audit`, `security/authz`, `security/behavioral`

---

### Pattern 2: gRPC Testing with bufconn

**Use Case**: Testing gRPC clients (ImmuneClient, KafkaClient, MaximusClient)

```go
const bufSize = 1024 * 1024

func setupTestServer(t *testing.T, mockServer pb.ServiceServer) (*grpc.Server, *bufconn.Listener) {
    lis := bufconn.Listen(bufSize)
    server := grpc.NewServer()
    pb.RegisterServiceServer(server, mockServer)

    go func() {
        if err := server.Serve(lis); err != nil {
            t.Logf("Server exited with error: %v", err)
        }
    }()

    return server, lis
}

func createTestClient(t *testing.T, lis *bufconn.Listener) pb.ServiceClient {
    ctx := context.Background()
    conn, err := grpc.DialContext(ctx, "bufnet",
        grpc.WithContextDialer(func(context.Context, string) (net.Conn, error) {
            return lis.Dial()
        }),
        grpc.WithTransportCredentials(insecure.NewCredentials()),
    )
    require.NoError(t, err)
    t.Cleanup(func() { conn.Close() })

    return pb.NewServiceClient(conn)
}
```

**Packages Using This**: `grpc/immune_client`, `streaming/kafka_client`

---

### Pattern 3: Kubernetes Client Testing with Fake Clientset

**Use Case**: Testing K8s operations without a real cluster

```go
func TestK8sOperation(t *testing.T) {
    // Create fake clientset with pre-populated objects
    fakeClient := fake.NewSimpleClientset(
        &corev1.Pod{
            ObjectMeta: metav1.ObjectMeta{
                Name:      "test-pod",
                Namespace: "default",
            },
            Status: corev1.PodStatus{
                Phase: corev1.PodRunning,
            },
        },
    )

    // Use fake client in tests
    pods, err := fakeClient.CoreV1().Pods("default").List(context.Background(), metav1.ListOptions{})
    require.NoError(t, err)
    assert.Len(t, pods.Items, 1)
}
```

**Packages Using This**: `k8s/*`, `dashboard/k8s`, `orchestrator/*`

---

### Pattern 4: Server-Sent Events (SSE) Testing

**Use Case**: Testing SSE streaming clients

```go
func TestSSEClient(t *testing.T) {
    server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        flusher, ok := w.(http.Flusher)
        require.True(t, ok)

        w.Header().Set("Content-Type", "text/event-stream")
        w.Header().Set("Cache-Control", "no-cache")
        w.Header().Set("Connection", "keep-alive")

        // Send events
        fmt.Fprintf(w, "event: message\n")
        fmt.Fprintf(w, "id: 1\n")
        fmt.Fprintf(w, "data: {\"key\":\"value\"}\n\n")
        flusher.Flush()

        time.Sleep(100 * time.Millisecond)

        fmt.Fprintf(w, "event: close\n")
        fmt.Fprintf(w, "data: {\"reason\":\"done\"}\n\n")
        flusher.Flush()
    }))
    defer server.Close()

    client := NewSSEClient(server.URL, "token")

    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer cancel()

    events := make(chan *Event, 10)
    go client.Subscribe(ctx, events)

    // Collect events
    var received []*Event
    for {
        select {
        case event := <-events:
            if event == nil {
                goto done
            }
            received = append(received, event)
        case <-ctx.Done():
            t.Fatal("timeout")
        }
    }
done:
    assert.Len(t, received, 2)
}
```

**Packages Using This**: `streaming/sse_client`

---

### Pattern 5: Table-Driven Tests

**Use Case**: Testing multiple scenarios efficiently

```go
func TestValidation(t *testing.T) {
    tests := []struct {
        name        string
        input       string
        expected    bool
        expectError bool
    }{
        {"valid input", "valid", true, false},
        {"empty input", "", false, true},
        {"invalid format", "!!!", false, true},
        {"edge case", "x", true, false},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            result, err := Validate(tt.input)

            if tt.expectError {
                require.Error(t, err)
            } else {
                require.NoError(t, err)
                assert.Equal(t, tt.expected, result)
            }
        })
    }
}
```

**Packages Using This**: All packages with complex validation or multiple code paths

---

### Pattern 6: Concurrency Testing

**Use Case**: Testing thread-safe code

```go
func TestConcurrentAccess(t *testing.T) {
    client := NewClient()

    var wg sync.WaitGroup
    for i := 0; i < 10; i++ {
        wg.Add(1)
        go func(id int) {
            defer wg.Done()

            // Perform concurrent operations
            _, err := client.Operation(id)
            assert.NoError(t, err)
        }(i)
    }

    wg.Wait()
}
```

**Run with race detector**: `go test -race ./internal/...`

**Packages Using This**: `security/*`, `agents/*`, `orchestrator/*`

---

### Pattern 7: Temporary File/Directory Testing

**Use Case**: Testing file operations

```go
func TestFileOperation(t *testing.T) {
    // Use t.TempDir() for automatic cleanup
    tmpDir := t.TempDir()

    filePath := filepath.Join(tmpDir, "test.txt")
    err := os.WriteFile(filePath, []byte("content"), 0644)
    require.NoError(t, err)

    // Test operations on the file
    result, err := ProcessFile(filePath)
    require.NoError(t, err)
    assert.Equal(t, "expected", result)

    // No need to cleanup - t.TempDir() handles it
}
```

**Packages Using This**: `security/audit`, `shell/*`, `workspaces/*`

---

### Pattern 8: Agent Testing with Mock Strategies

**Use Case**: Testing agent implementations

```go
type mockStrategy struct {
    analyzeFunc func(context.Context, string) (*Result, error)
}

func (m *mockStrategy) Analyze(ctx context.Context, input string) (*Result, error) {
    if m.analyzeFunc != nil {
        return m.analyzeFunc(ctx, input)
    }
    return &Result{Success: true}, nil
}

func TestAgent(t *testing.T) {
    mockStrat := &mockStrategy{
        analyzeFunc: func(ctx context.Context, input string) (*Result, error) {
            return &Result{Score: 0.95}, nil
        },
    }

    agent := NewAgent(mockStrat)
    result, err := agent.Execute(context.Background(), "input")

    require.NoError(t, err)
    assert.Equal(t, 0.95, result.Score)
}
```

**Packages Using This**: `agents/*`, `orchestrator/*`

---

## Coverage Metrics

### Measuring Coverage

```bash
# Single package
go test ./internal/PACKAGE/... -coverprofile=coverage.out
go tool cover -func=coverage.out

# All packages
go test ./internal/... -coverprofile=coverage.out
go tool cover -func=coverage.out | grep total

# HTML report
go tool cover -html=coverage.out -o coverage.html
```

### Coverage Thresholds

| Category | Minimum | Target | Excellent |
|----------|---------|--------|-----------|
| **Critical Packages** | 85% | 90% | 95%+ |
| **Standard Packages** | 70% | 75% | 85%+ |
| **Utility Packages** | 60% | 70% | 80%+ |

**Critical Packages**: security/*, agents/*, streaming/*, grpc/*
**Standard Packages**: dashboard/*, orchestrator/*, k8s/*
**Utility Packages**: testutil/*, visual/*, tui/*

---

## Package-Specific Guides

### Security Package Testing

**Coverage Target**: 95%+

```go
// audit_test.go - File-based audit logging
func TestAuditClient(t *testing.T) {
    tmpDir := t.TempDir()
    logFile := filepath.Join(tmpDir, "audit.log")

    client := NewAuditClient(logFile, 1000)

    // Test logging
    err := client.Log("user1", "read", "resource1")
    require.NoError(t, err)

    // Test querying
    events, err := client.Query(QueryFilter{UserID: "user1"})
    require.NoError(t, err)
    assert.Len(t, events, 1)
}

// authz_test.go - RBAC authorization
func TestAuthzClient(t *testing.T) {
    client := NewAuthzClient()

    // Test permission check
    allowed := client.IsAllowed("user1", "read", "resource1")
    assert.True(t, allowed)
}

// behavioral_test.go - Anomaly detection
func TestBehavioralAnalyzer(t *testing.T) {
    analyzer := NewBehavioralAnalyzer()

    // Train normal behavior
    analyzer.RecordAction("user1", "login", "192.168.1.1")

    // Test anomaly detection
    score := analyzer.AnalyzeAnomaly("user1", "delete-all", "10.0.0.1")
    assert.Greater(t, score, 0.7) // Should detect anomaly
}
```

---

### Streaming Package Testing

**Coverage Target**: 90%+

```go
// sse_client_test.go
func TestSSEReconnection(t *testing.T) {
    reconnectCount := 0

    server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        reconnectCount++

        if reconnectCount == 1 {
            // Simulate server error on first connect
            w.WriteHeader(http.StatusInternalServerError)
            return
        }

        // Success on reconnect
        w.Header().Set("Content-Type", "text/event-stream")
        fmt.Fprintf(w, "data: success\n\n")
    }))
    defer server.Close()

    client := NewSSEClient(server.URL, "token")
    client.MaxReconnectAttempts = 3
    client.ReconnectDelay = 100 * time.Millisecond

    ctx := context.WithTimeout(context.Background(), 5*time.Second)
    events := make(chan *Event, 10)

    go client.Subscribe(ctx, events)

    event := <-events
    assert.Equal(t, "success", event.Data)
    assert.Equal(t, 2, reconnectCount) // Should reconnect once
}
```

---

### Agent Package Testing

**Coverage Target**: 85%+

```go
// dev_senior_test.go
func TestDevSeniorAgent(t *testing.T) {
    t.Run("analyze code quality", func(t *testing.T) {
        agent := NewDevSeniorAgent()

        code := `
            package main
            func add(a, b int) int {
                return a + b
            }
        `

        result, err := agent.AnalyzeCodeQuality(code)
        require.NoError(t, err)

        assert.Greater(t, result.QualityScore, 0.8)
        assert.NotEmpty(t, result.Recommendations)
    })
}

// orchestrator_test.go
func TestAgentOrchestrator(t *testing.T) {
    orchestrator := NewAgentOrchestrator()

    // Register mock agent
    mockAgent := &MockAgent{Name: "test-agent"}
    orchestrator.RegisterAgent("test", mockAgent)

    // Execute workflow
    result, err := orchestrator.ExecuteWorkflow(context.Background(), "test-workflow")
    require.NoError(t, err)
    assert.True(t, result.Success)
}
```

---

### Shell Package Testing

**Coverage Target**: 75%+

```go
// completer_test.go
func TestCompleter(t *testing.T) {
    completer := NewCompleter(nil, nil)

    tests := []struct {
        name     string
        input    string
        expected []string
    }{
        {"k8s command", "k8s ", []string{"pods", "services", "deployments"}},
        {"orchestrate", "orchestrate ", []string{"offensive", "defensive", "workflow"}},
        {"empty", "", []string{}},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            suggestions := completer.CompleteText(tt.input)
            assert.ElementsMatch(t, tt.expected, suggestions)
        })
    }
}

// executor_test.go
func TestCommandExecution(t *testing.T) {
    executor := NewExecutor(nil)

    // Test slash command
    output, err := executor.Execute("/help")
    require.NoError(t, err)
    assert.Contains(t, output, "Available commands")

    // Test built-in command
    output, err = executor.Execute("help")
    require.NoError(t, err)
    assert.NotEmpty(t, output)
}
```

---

### Workspace Package Testing

**Coverage Target**: 80%+

```go
// governance_workspace_test.go
func TestGovernanceWorkspace(t *testing.T) {
    ws := NewGovernanceWorkspace("http://localhost:8080")

    // Test initialization
    cmd := ws.Init()
    assert.NotNil(t, cmd)

    // Test update with window size
    model, cmd := ws.Update(tea.WindowSizeMsg{Width: 120, Height: 40})
    assert.NotNil(t, model)

    // Test view rendering
    view := ws.View()
    assert.NotEmpty(t, view)
    assert.Contains(t, view, "MAXIMUS Governance")
}
```

---

## Best Practices

### 1. Use Subtests for Organization

```go
func TestFeature(t *testing.T) {
    t.Run("success case", func(t *testing.T) {
        // Success path
    })

    t.Run("error - invalid input", func(t *testing.T) {
        // Error path 1
    })

    t.Run("error - network failure", func(t *testing.T) {
        // Error path 2
    })
}
```

### 2. Test Error Paths

```go
func TestErrorHandling(t *testing.T) {
    tests := []struct {
        name          string
        input         string
        expectedError string
    }{
        {"empty input", "", "input cannot be empty"},
        {"invalid format", "abc", "invalid format"},
        {"out of range", "999", "value out of range"},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            _, err := Process(tt.input)
            require.Error(t, err)
            assert.Contains(t, err.Error(), tt.expectedError)
        })
    }
}
```

### 3. Use require vs assert

- **require**: Use for critical assertions (test stops if fails)
- **assert**: Use for non-critical assertions (test continues)

```go
func TestExample(t *testing.T) {
    result, err := Operation()
    require.NoError(t, err) // STOP if error (can't continue)

    assert.NotNil(t, result)      // Continue even if fails
    assert.Equal(t, "expected", result.Value)
}
```

### 4. Cleanup Resources

```go
func TestWithCleanup(t *testing.T) {
    server := httptest.NewServer(handler)
    defer server.Close() // Always cleanup

    client := NewClient(server.URL)
    defer client.Close() // Always cleanup

    // Test code
}
```

### 5. Avoid Test Interdependence

```go
// BAD - Tests depend on each other
var globalState string

func TestA(t *testing.T) {
    globalState = "A"
}

func TestB(t *testing.T) {
    assert.Equal(t, "A", globalState) // FAILS if TestA doesn't run first
}

// GOOD - Tests are independent
func TestA(t *testing.T) {
    state := "A"
    assert.Equal(t, "A", state)
}

func TestB(t *testing.T) {
    state := "B"
    assert.Equal(t, "B", state)
}
```

---

## Common Pitfalls

### 1. Not Testing Error Paths

**Problem**: Only testing happy path

```go
// BAD
func TestOperation(t *testing.T) {
    result, _ := Operation("valid") // Ignoring error
    assert.NotNil(t, result)
}

// GOOD
func TestOperation(t *testing.T) {
    t.Run("success", func(t *testing.T) {
        result, err := Operation("valid")
        require.NoError(t, err)
        assert.NotNil(t, result)
    })

    t.Run("error - invalid input", func(t *testing.T) {
        _, err := Operation("invalid")
        require.Error(t, err)
    })
}
```

### 2. Race Conditions in Tests

**Problem**: Tests fail intermittently

```go
// BAD - Race condition
func TestAsync(t *testing.T) {
    var result string

    go func() {
        result = "done" // Race!
    }()

    assert.Equal(t, "done", result) // May fail
}

// GOOD - Proper synchronization
func TestAsync(t *testing.T) {
    var result string
    var wg sync.WaitGroup

    wg.Add(1)
    go func() {
        defer wg.Done()
        result = "done"
    }()

    wg.Wait()
    assert.Equal(t, "done", result)
}
```

### 3. Not Cleaning Up Resources

**Problem**: Tests leave artifacts

```go
// BAD - Leaks resources
func TestFile(t *testing.T) {
    f, _ := os.Create("/tmp/test.txt")
    // No cleanup!
}

// GOOD - Proper cleanup
func TestFile(t *testing.T) {
    tmpDir := t.TempDir() // Auto-cleanup
    filePath := filepath.Join(tmpDir, "test.txt")

    f, err := os.Create(filePath)
    require.NoError(t, err)
    defer f.Close()

    // Test operations
}
```

### 4. Testing Implementation Instead of Behavior

**Problem**: Tests too coupled to implementation

```go
// BAD - Testing internal structure
func TestCache(t *testing.T) {
    cache := NewCache()
    cache.data["key"] = "value" // Accessing internal field
    assert.Equal(t, "value", cache.data["key"])
}

// GOOD - Testing public API behavior
func TestCache(t *testing.T) {
    cache := NewCache()
    cache.Set("key", "value")

    value, found := cache.Get("key")
    assert.True(t, found)
    assert.Equal(t, "value", value)
}
```

---

## Tools and Commands

### Running Tests

```bash
# Run all tests
go test ./...

# Run specific package
go test ./internal/security/...

# Run with coverage
go test ./... -cover

# Run with coverage profile
go test ./... -coverprofile=coverage.out
go tool cover -func=coverage.out

# HTML coverage report
go tool cover -html=coverage.out -o coverage.html

# Run with race detector
go test -race ./...

# Run verbose
go test -v ./...

# Run specific test
go test -run TestFunctionName ./...

# Run with short flag (skip slow tests)
go test -short ./...

# Run benchmarks
go test -bench=. ./...
```

### Coverage Analysis

```bash
# Show total coverage
go test ./... -coverprofile=coverage.out
go tool cover -func=coverage.out | grep total

# Find packages with low coverage
go tool cover -func=coverage.out | grep -v "100.0%" | sort -k3 -n

# Find uncovered functions
go tool cover -func=coverage.out | grep "0.0%"

# Generate coverage report sorted by package
go test ./... -coverprofile=coverage.out
go tool cover -func=coverage.out | sort -k1
```

### Quality Checks

```bash
# Run linter
golangci-lint run

# Run vet
go vet ./...

# Format code
gofmt -s -w .

# Check for suspicious constructs
go vet ./...

# Static analysis
staticcheck ./...
```

### CI/CD Integration

```yaml
# GitHub Actions example
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-go@v4
        with:
          go-version: '1.21'

      - name: Run tests
        run: go test -race -coverprofile=coverage.out ./...

      - name: Check coverage
        run: |
          COVERAGE=$(go tool cover -func=coverage.out | grep total | awk '{print $3}' | sed 's/%//')
          echo "Coverage: $COVERAGE%"
          if (( $(echo "$COVERAGE < 90" | bc -l) )); then
            echo "Coverage below 90%!"
            exit 1
          fi
```

---

## Summary

This guide provides comprehensive patterns and best practices for testing vcli-go. By following these guidelines, you ensure:

- ✅ High code coverage (90-93%)
- ✅ Type-safe, maintainable tests
- ✅ Fast, reliable test suite
- ✅ Zero technical debt
- ✅ Boris Cherny standards compliance

For questions or improvements, see the project README or consult the development team.

---

**Maintained by**: V-rtice Team
**Standards**: Boris Cherny (Programming TypeScript principles applied to Go)
**Coverage Achievement**: FASE 1-4 Complete (90-93% global coverage)
