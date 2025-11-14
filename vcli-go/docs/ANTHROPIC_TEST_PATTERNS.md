# 🧪 ANTHROPIC TEST PATTERNS - VCLI-GO

**Date**: 2025-11-14
**Project**: vCLI 2.0
**Purpose**: Testing patterns aligned with Anthropic/Claude Code + Go best practices
**Mode**: Boris Cherny - "Tests or it didn't happen"

---

## 📋 EXECUTIVE SUMMARY

This document synthesizes:
1. **Anthropic Claude Code** TDD patterns (2025)
2. **Go testing** best practices (2025)
3. **Integration testing** for external tools
4. **Coverage strategies** for production readiness

**Key Principle**: "Tests are the specification" - TDD Philosophy

**Target**: **90%+ coverage** for all new code

---

## 🏗️ ANTHROPIC CLAUDE CODE TDD PRINCIPLES

### Core TDD Workflow (Anthropic 2025)

```
┌─────────────────────────────────────────────────┐
│  1. WRITE TESTS FIRST                          │
│     - Define expected behavior                  │
│     - No implementation yet                     │
│     - Explicit: "This is TDD"                   │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  2. VERIFY TESTS FAIL                          │
│     - Run tests, confirm red                    │
│     - No mock implementations                   │
│     - Commit failing tests                      │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  3. IMPLEMENT MINIMUM CODE                     │
│     - Make tests pass (green)                   │
│     - Iterate until all green                   │
│     - Commit working code                       │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  4. REFACTOR & ITERATE                         │
│     - Improve code quality                      │
│     - Keep tests passing                        │
│     - Commit improvements                       │
└─────────────────────────────────────────────────┘
```

### Why TDD with Claude Code? ✅

1. **Clear Target**: Tests define success criteria
2. **Iterative Improvement**: Claude can verify & fix
3. **Human Oversight**: Developer controls design via tests
4. **Quality Barrier**: Tests enforce standards
5. **Specification**: Tests document expected behavior

---

## 🔧 GO TESTING PATTERNS (2025)

### Pattern 1: Table-Driven Tests ✅ **GOLD STANDARD**

**When**: Testing multiple scenarios of the same logic

**Structure**:
```go
func TestFunction(t *testing.T) {
    tests := []struct {
        name    string
        input   InputType
        want    OutputType
        wantErr bool
    }{
        {
            name:    "description of test case",
            input:   /* test input */,
            want:    /* expected output */,
            wantErr: false,
        },
        // ... more test cases
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got, err := Function(tt.input)

            if (err != nil) != tt.wantErr {
                t.Errorf("Function() error = %v, wantErr %v", err, tt.wantErr)
                return
            }

            if !reflect.DeepEqual(got, tt.want) {
                t.Errorf("Function() = %v, want %v", got, tt.want)
            }
        })
    }
}
```

**Benefits**:
- ✅ Concise: Test many scenarios with minimal code
- ✅ Clear: Each case has descriptive name
- ✅ Maintainable: Add cases without duplicating logic
- ✅ Independent: Each test isolated via `t.Run()`

---

### Pattern 2: Example - Tool Availability Tests ✅

**File**: `internal/tools/checker_test.go`

```go
package tools

import (
    "testing"
    "github.com/verticedev/vcli-go/internal/errors"
)

func TestChecker_Check(t *testing.T) {
    tests := []struct {
        name       string
        toolName   string
        wantErr    bool
        errType    error
        severity   errors.Severity
    }{
        {
            name:     "tool available - go",
            toolName: "go",
            wantErr:  false,
        },
        {
            name:     "tool missing - nonexistent",
            toolName: "nonexistent-tool-xyz-123",
            wantErr:  true,
            errType:  &errors.ToolError{},
            severity: errors.SeverityWarn,
        },
        {
            name:     "tool available - python3",
            toolName: "python3",
            wantErr:  false,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            checker := NewChecker()

            // Register tool with appropriate severity
            checker.Register(Tool{
                Name:     tt.toolName,
                Severity: tt.severity,
            })

            err := checker.Check(tt.toolName)

            // Check error presence
            if (err != nil) != tt.wantErr {
                t.Errorf("Check() error = %v, wantErr %v", err, tt.wantErr)
                return
            }

            // Check error type
            if tt.wantErr && tt.errType != nil {
                var toolErr *errors.ToolError
                if !errors.As(err, &toolErr) {
                    t.Errorf("Check() error type = %T, want %T", err, tt.errType)
                }

                if toolErr.Severity != tt.severity {
                    t.Errorf("Check() severity = %v, want %v", toolErr.Severity, tt.severity)
                }
            }
        })
    }
}
```

---

### Pattern 3: Testing Error Paths ✅

**Golden Rule**: Every error return needs a test

```go
func TestHomeDir_EmptyHOME(t *testing.T) {
    // Save original
    originalHome := os.Getenv("HOME")
    defer os.Setenv("HOME", originalHome)

    // Set empty HOME
    os.Setenv("HOME", "")

    _, err := fs.HomeDir()
    if err == nil {
        t.Fatal("expected error when HOME is empty")
    }

    expectedMsg := "home directory is empty string"
    if !strings.Contains(err.Error(), expectedMsg) {
        t.Errorf("error message = %v, want to contain %q", err, expectedMsg)
    }
}

func TestHomeDir_Success(t *testing.T) {
    home, err := fs.HomeDir()
    if err != nil {
        t.Fatalf("unexpected error: %v", err)
    }

    if home == "" {
        t.Error("home directory should not be empty")
    }

    // Verify it's an absolute path
    if !filepath.IsAbs(home) {
        t.Errorf("home = %q is not absolute path", home)
    }
}
```

---

### Pattern 4: Subtests for Edge Cases ✅

```go
func TestFormatCode(t *testing.T) {
    tests := []struct {
        name    string
        code    string
        wantErr bool
    }{
        {
            name: "valid python code",
            code: "def hello():\n    print('world')",
            wantErr: false,
        },
        {
            name: "empty code",
            code: "",
            wantErr: false,  // Should return empty, not error
        },
        {
            name: "invalid syntax",
            code: "def hello(\n",  // Unclosed paren
            wantErr: true,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            strategy := NewPythonCodeGenStrategy()
            result, err := strategy.FormatCode(tt.code)

            if (err != nil) != tt.wantErr {
                t.Errorf("FormatCode() error = %v, wantErr %v", err, tt.wantErr)
                return
            }

            if !tt.wantErr && result == "" && tt.code != "" {
                t.Error("FormatCode() returned empty string for valid code")
            }
        })
    }
}
```

---

## 🧩 MOCKING EXTERNAL DEPENDENCIES

### Pattern 5: Interface-Based Mocking ✅

**When**: Testing code that calls external tools

**Step 1**: Define interface
```go
// internal/tools/interface.go
package tools

type ToolChecker interface {
    Check(toolName string) error
    Register(tool Tool)
}
```

**Step 2**: Create mock
```go
// internal/tools/mock_checker_test.go
package tools

type MockChecker struct {
    CheckFunc    func(string) error
    RegisterFunc func(Tool)
}

func (m *MockChecker) Check(toolName string) error {
    if m.CheckFunc != nil {
        return m.CheckFunc(toolName)
    }
    return nil
}

func (m *MockChecker) Register(tool Tool) {
    if m.RegisterFunc != nil {
        m.RegisterFunc(tool)
    }
}
```

**Step 3**: Use in tests
```go
func TestRunGosec_ToolMissing(t *testing.T) {
    mockChecker := &MockChecker{
        CheckFunc: func(name string) error {
            if name == "gosec" {
                return &errors.ToolError{
                    Tool:     "gosec",
                    Err:      errors.ErrToolNotFound,
                    Severity: errors.SeverityWarn,
                }
            }
            return nil
        },
    }

    strategy := &GoAnalysisStrategy{
        checker: mockChecker,
    }

    result := &agents.DiagnosticResult{}
    err := strategy.runSecurityScan(context.Background(), []string{"."}, result)

    // Should handle gracefully
    if err == nil {
        t.Error("expected error when gosec missing")
    }

    // Should add warning to result
    if len(result.Warnings) == 0 {
        t.Error("expected warning in result")
    }
}
```

---

### Pattern 6: Test Fixtures ✅

**When**: Tests need consistent test data

**Structure**:
```
internal/agents/strategies/
├── python_testing.go
├── python_testing_test.go
└── testdata/
    ├── pytest_report_success.json
    ├── pytest_report_failure.json
    └── coverage_report.json
```

**Usage**:
```go
func TestParsePytestReport_Success(t *testing.T) {
    data, err := os.ReadFile("testdata/pytest_report_success.json")
    if err != nil {
        t.Fatalf("failed to read fixture: %v", err)
    }

    strategy := NewPythonTestStrategy()
    result := &agents.TestResult{}

    err = strategy.parsePytestReportData(data, result)
    if err != nil {
        t.Errorf("parsePytestReportData() error = %v", err)
    }

    // Verify parsed data
    if result.Passed == 0 {
        t.Error("expected passed tests > 0")
    }
}
```

---

## 🔬 INTEGRATION TESTS

### Pattern 7: Build Tags for Separation ✅

**File**: `internal/tools/checker_integration_test.go`

```go
//go:build integration
// +build integration

package tools

import (
    "testing"
)

func TestChecker_RealTools(t *testing.T) {
    // This test runs ONLY with: go test -tags=integration

    checker := NewChecker()

    // Test with real system tools
    realTools := []string{"go", "git", "python3"}

    for _, tool := range realTools {
        t.Run(tool, func(t *testing.T) {
            checker.Register(Tool{
                Name: tool,
                Severity: errors.SeverityInfo,
            })

            err := checker.Check(tool)
            if err != nil {
                t.Logf("Tool %s not available (expected in CI): %v", tool, err)
                // Not fatal - just log
            } else {
                t.Logf("Tool %s available ✅", tool)
            }
        })
    }
}
```

**Run integration tests**:
```bash
# Unit tests only (default)
go test ./...

# Integration tests
go test -tags=integration ./...

# All tests
go test -tags=integration ./...
```

---

### Pattern 8: Temp File Testing ✅

**Testing our /tmp fix**:

```go
func TestCreateTempReport_Cleanup(t *testing.T) {
    strategy := NewPythonTestStrategy()

    // Track temp files created
    var tempFiles []string

    // Patch os.CreateTemp (in real code, use interface)
    originalCreateTemp := os.CreateTemp
    defer func() { os.CreateTemp = originalCreateTemp }()

    os.CreateTemp = func(dir, pattern string) (*os.File, error) {
        f, err := originalCreateTemp(dir, pattern)
        if err == nil {
            tempFiles = append(tempFiles, f.Name())
        }
        return f, err
    }

    // Run test that creates temp files
    _, err := strategy.RunTests(context.Background(), []string{"."})

    // Verify cleanup
    for _, path := range tempFiles {
        if _, err := os.Stat(path); !os.IsNotExist(err) {
            t.Errorf("temp file not cleaned up: %s", path)
        }
    }
}

func TestCreateTempReport_RaceCondition(t *testing.T) {
    // Test parallel execution doesn't conflict
    strategy := NewPythonTestStrategy()

    // Run 10 tests in parallel
    t.Run("parallel", func(t *testing.T) {
        for i := 0; i < 10; i++ {
            i := i  // Capture loop var
            t.Run(fmt.Sprintf("test_%d", i), func(t *testing.T) {
                t.Parallel()

                _, err := strategy.RunTests(context.Background(), []string{"."})
                if err != nil {
                    t.Errorf("test %d failed: %v", i, err)
                }
            })
        }
    })
}
```

---

## 📊 COVERAGE STRATEGIES

### Pattern 9: 100% Coverage Pattern (Anthropic-Aligned) ✅

**Strategy**: Dual test files for critical code

```
internal/errors/
├── tool_errors.go
├── tool_errors_test.go       # Standard tests (80-90%)
└── tool_errors_100pct_test.go  # Edge cases to reach 100%
```

**tool_errors_test.go** (Core functionality):
```go
func TestToolError_Error(t *testing.T) {
    err := &ToolError{
        Tool: "gosec",
        Err:  errors.New("not found"),
    }

    got := err.Error()
    want := "gosec: not found"

    if got != want {
        t.Errorf("Error() = %q, want %q", got, want)
    }
}

func TestToolError_Unwrap(t *testing.T) {
    inner := errors.New("inner error")
    err := &ToolError{
        Tool: "test",
        Err:  inner,
    }

    if errors.Unwrap(err) != inner {
        t.Error("Unwrap() did not return inner error")
    }
}
```

**tool_errors_100pct_test.go** (Edge cases):
```go
func TestToolError_EdgeCases(t *testing.T) {
    t.Run("nil inner error", func(t *testing.T) {
        err := &ToolError{
            Tool: "test",
            Err:  nil,  // Edge case
        }

        got := err.Error()
        if got != "test: <nil>" {
            t.Errorf("unexpected error message: %q", got)
        }
    })

    t.Run("empty tool name", func(t *testing.T) {
        err := &ToolError{
            Tool: "",  // Edge case
            Err:  errors.New("error"),
        }

        got := err.Error()
        // Should handle gracefully
        if got == "" {
            t.Error("empty error message")
        }
    })

    t.Run("zero value struct", func(t *testing.T) {
        var err ToolError  // Zero value

        _ = err.Error()  // Should not panic
        _ = err.Unwrap()  // Should return nil
    })
}
```

---

### Pattern 10: Coverage Reports ✅

**Generate coverage**:
```bash
# Run tests with coverage
go test -coverprofile=coverage.out ./...

# View in terminal
go tool cover -func=coverage.out

# View in browser
go tool cover -html=coverage.out

# Filter by package
go tool cover -func=coverage.out | grep "internal/errors"
```

**Enforce coverage in CI**:
```bash
# Extract overall percentage
COVERAGE=$(go tool cover -func=coverage.out | grep total | awk '{print $3}' | sed 's/%//')

# Fail if below threshold
if (( $(echo "$COVERAGE < 90" | bc -l) )); then
    echo "❌ Coverage ${COVERAGE}% is below 90% threshold"
    exit 1
fi

echo "✅ Coverage: ${COVERAGE}%"
```

---

## 🧪 BENCHMARK TESTS

### Pattern 11: Performance Benchmarks ✅

**When**: Verify performance doesn't regress

```go
func BenchmarkChecker_Check(b *testing.B) {
    checker := NewChecker()
    checker.Register(Tool{
        Name: "go",
        Severity: errors.SeverityInfo,
    })

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        _ = checker.Check("go")
    }
}

func BenchmarkChecker_CheckCached(b *testing.B) {
    checker := NewChecker()
    checker.Register(Tool{Name: "go"})

    // Prime cache
    _ = checker.Check("go")

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        _ = checker.Check("go")
    }
}
```

**Run benchmarks**:
```bash
# Run benchmarks
go test -bench=. ./internal/tools/

# With memory stats
go test -bench=. -benchmem ./internal/tools/

# Compare before/after
go test -bench=. -count=10 > old.txt
# Make changes
go test -bench=. -count=10 > new.txt
benchcmp old.txt new.txt
```

---

## 🔧 TEST HELPERS & UTILITIES

### Pattern 12: Reusable Test Helpers ✅

**File**: `internal/testutil/helpers.go`

```go
package testutil

import (
    "os"
    "path/filepath"
    "testing"
)

// TempDir creates a temporary directory for tests
func TempDir(t *testing.T) string {
    t.Helper()

    dir, err := os.MkdirTemp("", "vcli-test-*")
    if err != nil {
        t.Fatalf("failed to create temp dir: %v", err)
    }

    t.Cleanup(func() {
        os.RemoveAll(dir)
    })

    return dir
}

// CreateFile creates a test file with content
func CreateFile(t *testing.T, dir, name, content string) string {
    t.Helper()

    path := filepath.Join(dir, name)
    err := os.WriteFile(path, []byte(content), 0644)
    if err != nil {
        t.Fatalf("failed to create file: %v", err)
    }

    return path
}

// MockTool makes a tool appear available in tests
func MockTool(t *testing.T, toolName string) {
    t.Helper()

    // Create mock executable in temp dir
    tmpDir := TempDir(t)
    mockPath := filepath.Join(tmpDir, toolName)

    err := os.WriteFile(mockPath, []byte("#!/bin/sh\necho mock"), 0755)
    if err != nil {
        t.Fatalf("failed to create mock tool: %v", err)
    }

    // Add to PATH
    originalPath := os.Getenv("PATH")
    os.Setenv("PATH", tmpDir+":"+originalPath)

    t.Cleanup(func() {
        os.Setenv("PATH", originalPath)
    })
}
```

**Usage**:
```go
func TestWithTempDir(t *testing.T) {
    dir := testutil.TempDir(t)  // Auto-cleanup via t.Cleanup()

    testutil.CreateFile(t, dir, "config.yaml", "key: value")

    // Use dir in test
    // Cleanup happens automatically
}
```

---

## 📋 TEST CHECKLIST (Per Function)

### For Every Public Function

- [ ] Test happy path (success case)
- [ ] Test error paths (all error returns)
- [ ] Test edge cases (empty input, nil, zero values)
- [ ] Test boundary conditions (min/max values)
- [ ] Use table-driven tests if >2 scenarios
- [ ] Use descriptive test names
- [ ] Use `t.Helper()` in helper functions
- [ ] Clean up resources with `t.Cleanup()` or `defer`

### For Error-Prone Code

- [ ] Test with nil inputs
- [ ] Test with empty strings/slices/maps
- [ ] Test concurrent access (if applicable)
- [ ] Test timeout scenarios
- [ ] Test cleanup on error

### For Integration Tests

- [ ] Use build tags (`//go:build integration`)
- [ ] Mock external dependencies when possible
- [ ] Document required external services
- [ ] Make tests idempotent (can run repeatedly)
- [ ] Log informational failures (not fatal in CI)

---

## 🎯 AIR-GAP SPECIFIC TEST STRATEGY

### Tests to Create for Air-Gap Fixes

#### 1. `internal/errors/tool_errors_test.go` ✅
```go
- TestToolError_Error()
- TestToolError_Unwrap()
- TestToolError_IsFatal()
- TestNewToolError()
- Table test for severity levels
```

#### 2. `internal/tools/checker_test.go` ✅
```go
- TestChecker_Check_Available()
- TestChecker_Check_Missing()
- TestChecker_Register()
- TestChecker_Cache()
- Table test for multiple tools
```

#### 3. `internal/fs/home_test.go` ✅
```go
- TestHomeDir_Success()
- TestHomeDir_EmptyHOME()
- TestHomeDir_NotSet()
- TestHomeDirOrCurrent_Fallback()
- TestConfigPath()
```

#### 4. `internal/agents/strategies/python_testing_test.go` ✅
```go
- TestRunTests_TempFileCreation()
- TestRunTests_TempFileCleanup()
- TestRunTests_RaceCondition()
- TestParsePytestReport()
- TestParseCoverageReport()
```

---

## 📊 COVERAGE TARGETS

### By Package Type

| Package Type | Target | Rationale |
|--------------|--------|-----------|
| **Core Infrastructure** (errors, tools, fs) | **100%** | Foundation - must be perfect |
| **Business Logic** (agents, strategies) | **90%+** | Critical functionality |
| **Integration** (k8s, http) | **80%+** | External deps harder to mock |
| **UI/TUI** | **70%+** | Visual components, hard to test |

### Current vs. Target

| Package | Current | Target | Gap |
|---------|---------|--------|-----|
| `internal/errors` (NEW) | 0% | 100% | +100% |
| `internal/tools` (NEW) | 0% | 95% | +95% |
| `internal/fs` (NEW) | 0% | 100% | +100% |
| `internal/agents/strategies` | 0% | 90% | +90% |
| **Overall Project** | **16%** | **90%** | **+74%** |

---

## 🚀 EXECUTION STRATEGY

### Phase 1: New Modules (FASE 1.1)
1. Write `internal/errors/tool_errors_test.go` first
2. Run test → should fail (TDD)
3. Implement `tool_errors.go`
4. Run test → should pass
5. Add edge cases → reach 100%
6. Repeat for `internal/tools/` and `internal/fs/`

### Phase 2: Modified Files (FASE 1.2-1.3)
1. Write tests for new behavior
2. Modify implementation
3. Run tests → ensure passing
4. Add tests for fixed bugs
5. Reach 90%+ coverage

### Phase 3: Integration (FASE 2.2)
1. Create integration tests with build tags
2. Mock external tools
3. Test real tool invocations (optional)
4. Document integration test setup

---

## 📚 RECOMMENDED TESTING TOOLS

### Standard Library ✅
- `testing` - Built-in, comprehensive
- `testing/quick` - Property-based testing
- `testing/iotest` - IO error testing

### Third-Party (Optional)
- `github.com/stretchr/testify` - Assertions (already in go.mod)
- `github.com/golang/mock` - Mock generation
- `github.com/onsi/ginkgo` - BDD-style tests

### For CI/CD
- `gotestsum` - Better test output
- `go-junit-report` - JUnit XML for CI
- `gocov` - Coverage reporting

---

## 🎯 SUCCESS CRITERIA

### For FASE 2 (Testing Phase)

- [ ] All new packages at 95-100% coverage
- [ ] All modified files at 90%+ coverage
- [ ] All error paths tested
- [ ] Integration tests created with build tags
- [ ] Test helpers created for common patterns
- [ ] Coverage enforced in CI (≥90% threshold)
- [ ] Benchmark tests for critical paths
- [ ] Overall project coverage >25% (up from 16%)

### For Production

- [ ] Overall coverage ≥90%
- [ ] All critical paths tested
- [ ] Zero untested error returns
- [ ] Integration tests pass in CI
- [ ] Benchmark baseline established
- [ ] Test documentation complete

---

**Generated**: 2025-11-14
**Mode**: Boris Cherny - "Tests or it didn't happen"
**Sources**: Anthropic 2025, Go 2025 best practices
**Next**: FASE 0.5.3 - Tool Availability Patterns
