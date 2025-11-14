# 🎯 ANTHROPIC ERROR HANDLING PATTERNS - VCLI-GO

**Date**: 2025-11-14
**Project**: vCLI 2.0
**Purpose**: Error handling patterns aligned with Anthropic/Claude Code best practices
**Mode**: Boris Cherny - Production Quality Standards

---

## 📋 EXECUTIVE SUMMARY

This document synthesizes:
1. **Anthropic Claude Code** best practices (2025)
2. **Go error handling** modern patterns (2025)
3. **Production-ready** strategies for CLI tools

**Key Principle**: "Errors should be impossible to ignore" - Boris Cherny

---

## 🏗️ ANTHROPIC CLAUDE CODE PRINCIPLES

### Core Philosophy

From Anthropic's internal practices and public guidance:

1. **TDD Cycle**: Write tests → Commit → Write code → Pass tests
2. **Explore → Plan → Code → Commit**: Structured workflow
3. **Git Safety**: Always use branches, enable easy rollback
4. **CLAUDE.md**: Document project-specific patterns
5. **Think First**: Use extended thinking for complex decisions

### Error Handling Priorities (Anthropic)

1. **Visibility**: Errors must be observable by users
2. **Context**: Include actionable information
3. **Recovery**: Provide clear next steps
4. **Safety**: Never silent failures
5. **Testing**: Error paths must be tested

---

## 🔧 GO ERROR HANDLING PATTERNS (2025)

### Pattern 1: Check-Handle (Basic) ✅

**When**: Every function that can fail

```go
result, err := doSomething()
if err != nil {
    return fmt.Errorf("failed to do something: %w", err)
}
```

**Key Points**:
- ✅ Immediate error checking
- ✅ Use `%w` for error wrapping (Go 1.13+)
- ✅ Add context to error messages
- ✅ Return early on error

---

### Pattern 2: Sentinel Errors ✅

**When**: Specific error conditions need special handling

```go
package errors

import "errors"

// Sentinel errors for specific conditions
var (
    ErrToolNotFound    = errors.New("tool not found in PATH")
    ErrInvalidConfig   = errors.New("invalid configuration")
    ErrTimeout         = errors.New("operation timed out")
    ErrNetworkFailure  = errors.New("network connection failed")
)

// Usage
func checkTool(name string) error {
    if _, err := exec.LookPath(name); err != nil {
        return fmt.Errorf("%w: %s", ErrToolNotFound, name)
    }
    return nil
}

// Caller can check
if errors.Is(err, ErrToolNotFound) {
    // Handle specifically
}
```

**Key Points**:
- ✅ Pre-defined error constants
- ✅ Use `errors.Is()` for comparison
- ✅ Wrap with `%w` to preserve sentinel
- ✅ Document in package errors

---

### Pattern 3: Custom Error Types (Advanced) ✅

**When**: Errors need additional data/methods

```go
// ToolError carries context about tool failures
type ToolError struct {
    Tool         string
    Err          error
    Severity     Severity
    InstallGuide string
}

func (e *ToolError) Error() string {
    return fmt.Sprintf("%s: %v", e.Tool, e.Err)
}

func (e *ToolError) Unwrap() error {
    return e.Err
}

// Additional method
func (e *ToolError) IsFatal() bool {
    return e.Severity == SeverityFatal
}

// Usage
func checkGoSec() error {
    if _, err := exec.LookPath("gosec"); err != nil {
        return &ToolError{
            Tool:         "gosec",
            Err:          err,
            Severity:     SeverityWarn,
            InstallGuide: "go install github.com/securego/gosec/v2/cmd/gosec@latest",
        }
    }
    return nil
}

// Caller can type-assert
var toolErr *ToolError
if errors.As(err, &toolErr) {
    fmt.Fprintf(os.Stderr, "Install: %s\n", toolErr.InstallGuide)
}
```

**Key Points**:
- ✅ Implements `error` interface
- ✅ Implements `Unwrap()` for error chains
- ✅ Can add custom methods
- ✅ Use `errors.As()` for type assertion

---

### Pattern 4: Error Wrapping & Context ✅

**When**: Errors traverse multiple layers

```go
func readConfig() error {
    home, err := os.UserHomeDir()
    if err != nil {
        return fmt.Errorf("cannot determine home directory: %w", err)
    }

    configPath := filepath.Join(home, ".vcli", "config.yaml")
    data, err := os.ReadFile(configPath)
    if err != nil {
        return fmt.Errorf("cannot read config at %s: %w", configPath, err)
    }

    if err := yaml.Unmarshal(data, &cfg); err != nil {
        return fmt.Errorf("invalid YAML in %s: %w", configPath, err)
    }

    return nil
}

// Error chain example:
// "invalid YAML in /home/user/.vcli/config.yaml:
//    cannot read config at /home/user/.vcli/config.yaml:
//       cannot determine home directory:
//          $HOME not set"
```

**Key Points**:
- ✅ Build error chains with `%w`
- ✅ Add context at each layer
- ✅ Include relevant data (paths, names)
- ✅ Preserve original error

---

### Pattern 5: Severity Classification ✅

**When**: Different errors require different responses

```go
type Severity int

const (
    SeverityFatal Severity = iota  // Must abort immediately
    SeverityError                   // Operation failed, continue with degradation
    SeverityWarn                    // Problem detected, fully functional
    SeverityInfo                    // Informational only
)

type ClassifiedError struct {
    Err      error
    Severity Severity
    Context  map[string]interface{}
}

func (e *ClassifiedError) Error() string {
    return fmt.Sprintf("[%s] %v", e.Severity, e.Err)
}

func (s Severity) String() string {
    return [...]string{"FATAL", "ERROR", "WARN", "INFO"}[s]
}

// Usage in CLI
func handleError(err error) {
    var classErr *ClassifiedError
    if errors.As(err, &classErr) {
        switch classErr.Severity {
        case SeverityFatal:
            fmt.Fprintf(os.Stderr, "❌ FATAL: %v\n", classErr.Err)
            os.Exit(1)
        case SeverityError:
            fmt.Fprintf(os.Stderr, "❌ ERROR: %v\n", classErr.Err)
        case SeverityWarn:
            fmt.Fprintf(os.Stderr, "⚠️  WARN: %v\n", classErr.Err)
        case SeverityInfo:
            fmt.Fprintf(os.Stderr, "ℹ️  INFO: %v\n", classErr.Err)
        }
    }
}
```

**Key Points**:
- ✅ Clear severity levels
- ✅ Appropriate icons/formatting
- ✅ Different exit codes
- ✅ User-friendly messages

---

### Pattern 6: Defer-Recover (Panic Handling) ⚠️

**When**: Protecting against panics in critical code

```go
func safeExecute(fn func() error) (err error) {
    defer func() {
        if r := recover(); r != nil {
            // Convert panic to error
            err = fmt.Errorf("panic recovered: %v", r)
        }
    }()

    return fn()
}

// Usage
err := safeExecute(func() error {
    // Potentially panicking code
    return riskyOperation()
})
```

**Key Points**:
- ⚠️ Use sparingly (only for library boundaries)
- ✅ Convert panics to errors
- ✅ Log stack trace for debugging
- ❌ Don't use for control flow

---

## 🎯 AIR-GAP SPECIFIC PATTERNS

### Pattern A: Tool Availability Checking ✅

**Problem**: External tools may be missing

```go
// Pre-flight check pattern
func CheckToolAvailability(tool string) error {
    // Step 1: Check if tool exists
    path, err := exec.LookPath(tool)
    if err != nil {
        return &ToolError{
            Tool:         tool,
            Err:          ErrToolNotFound,
            Severity:     SeverityWarn,
            InstallGuide: getInstallGuide(tool),
        }
    }

    // Step 2: Verify tool is executable
    if _, err := os.Stat(path); err != nil {
        return &ToolError{
            Tool:     tool,
            Err:      fmt.Errorf("tool found but not accessible: %w", err),
            Severity: SeverityError,
        }
    }

    return nil
}

// Usage before executing tool
func runGosec(ctx context.Context) error {
    if err := CheckToolAvailability("gosec"); err != nil {
        // Handle based on severity
        var toolErr *ToolError
        if errors.As(err, &toolErr) {
            if toolErr.Severity == SeverityFatal {
                return err // Abort
            }
            // Log warning and continue
            log.Printf("Warning: %v\n", err)
            return nil // Graceful degradation
        }
    }

    // Tool available, proceed
    cmd := exec.CommandContext(ctx, "gosec", "./...")
    return cmd.Run()
}
```

---

### Pattern B: Resource Cleanup ✅

**Problem**: Temp files, file handles must be cleaned

```go
// Always use defer for cleanup
func createTempReport() error {
    // Create temp file
    tmpFile, err := os.CreateTemp("", "pytest-*.json")
    if err != nil {
        return fmt.Errorf("failed to create temp file: %w", err)
    }
    defer os.Remove(tmpFile.Name())  // ✅ Always cleanup
    defer tmpFile.Close()             // ✅ Close handle

    // Use file
    if err := runTestWithReport(tmpFile.Name()); err != nil {
        return fmt.Errorf("test failed: %w", err)
    }

    // Read results
    data, err := os.ReadFile(tmpFile.Name())
    if err != nil {
        return fmt.Errorf("failed to read report: %w", err)
    }

    // Process data
    return processReport(data)
}
```

---

### Pattern C: Context-Aware Operations ✅

**Problem**: Operations may timeout or be cancelled

```go
func checkKubernetesHealth(ctx context.Context) error {
    // Create child context with timeout
    ctx, cancel := context.WithTimeout(ctx, 500*time.Millisecond)
    defer cancel()

    cmd := exec.CommandContext(ctx, "kubectl", "cluster-info")
    err := cmd.Run()

    // Distinguish timeout from other errors
    if ctx.Err() == context.DeadlineExceeded {
        return &ToolError{
            Tool:     "kubectl",
            Err:      errors.New("cluster health check timed out"),
            Severity: SeverityWarn,
        }
    }

    if err != nil {
        return &ToolError{
            Tool:     "kubectl",
            Err:      fmt.Errorf("cluster unreachable: %w", err),
            Severity: SeverityError,
        }
    }

    return nil
}
```

---

## 📚 ERROR AGGREGATION PATTERNS

### Pattern D: Multi-Error Collection ✅

**When**: Multiple operations can fail independently

```go
type MultiError struct {
    Errors []error
}

func (m *MultiError) Error() string {
    if len(m.Errors) == 0 {
        return "no errors"
    }
    if len(m.Errors) == 1 {
        return m.Errors[0].Error()
    }
    return fmt.Sprintf("%d errors occurred: %v", len(m.Errors), m.Errors[0])
}

func (m *MultiError) Add(err error) {
    if err != nil {
        m.Errors = append(m.Errors, err)
    }
}

func (m *MultiError) HasErrors() bool {
    return len(m.Errors) > 0
}

// Usage
func validateAllConfig() error {
    var merr MultiError

    merr.Add(validateEndpoints())
    merr.Add(validateCredentials())
    merr.Add(validateTimeouts())

    if merr.HasErrors() {
        return &merr
    }
    return nil
}
```

---

## 🧪 ERROR TESTING PATTERNS

### Pattern E: Testing Error Paths ✅

**Golden Rule**: Every error return must have a test

```go
func TestCheckTool_NotFound(t *testing.T) {
    err := CheckToolAvailability("nonexistent-tool-xyz")

    // Check error returned
    if err == nil {
        t.Fatal("expected error for missing tool")
    }

    // Check error type
    var toolErr *ToolError
    if !errors.As(err, &toolErr) {
        t.Fatalf("expected ToolError, got %T", err)
    }

    // Check severity
    if toolErr.Severity != SeverityWarn {
        t.Errorf("expected SeverityWarn, got %v", toolErr.Severity)
    }

    // Check install guide present
    if toolErr.InstallGuide == "" {
        t.Error("expected install guide, got empty string")
    }
}

func TestCheckTool_Available(t *testing.T) {
    // Test with tool that's definitely available
    err := CheckToolAvailability("go")
    if err != nil {
        t.Fatalf("expected no error for 'go', got: %v", err)
    }
}
```

---

### Pattern F: Table-Driven Error Tests ✅

```go
func TestToolError_Severity(t *testing.T) {
    tests := []struct {
        name     string
        err      error
        wantFatal bool
    }{
        {
            name: "fatal error",
            err: &ToolError{
                Tool:     "required-tool",
                Err:      ErrToolNotFound,
                Severity: SeverityFatal,
            },
            wantFatal: true,
        },
        {
            name: "warn error",
            err: &ToolError{
                Tool:     "optional-tool",
                Err:      ErrToolNotFound,
                Severity: SeverityWarn,
            },
            wantFatal: false,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            var toolErr *ToolError
            if !errors.As(tt.err, &toolErr) {
                t.Fatal("expected ToolError")
            }

            if got := toolErr.IsFatal(); got != tt.wantFatal {
                t.Errorf("IsFatal() = %v, want %v", got, tt.wantFatal)
            }
        })
    }
}
```

---

## 🎨 USER-FACING ERROR MESSAGES

### Best Practices (Anthropic-Aligned)

1. **Clear & Actionable**
   ```
   ❌ Bad:  "error"
   ✅ Good: "kubectl not found - install: https://kubernetes.io/docs/tasks/tools/"
   ```

2. **Include Context**
   ```
   ❌ Bad:  "file not found"
   ✅ Good: "config file not found at /home/user/.vcli/config.yaml"
   ```

3. **Provide Next Steps**
   ```
   ❌ Bad:  "gosec failed"
   ✅ Good: "gosec not installed - run: go install github.com/securego/gosec/v2/cmd/gosec@latest"
   ```

4. **Use Visual Indicators**
   ```
   ❌ FATAL: Cannot continue
   ❗ ERROR: Operation failed
   ⚠️  WARN:  Optional feature unavailable
   ℹ️  INFO:  FYI
   ```

---

## 📊 ERROR HANDLING CHECKLIST

### For Every Function That Can Fail

- [ ] Returns error as last value
- [ ] Error message includes context
- [ ] Uses `%w` for wrapping
- [ ] Has test for error path
- [ ] Has test for success path
- [ ] Documented failure modes

### For CLI Commands

- [ ] User-friendly error messages
- [ ] Appropriate exit codes (0=success, 1=error)
- [ ] Actionable install/fix instructions
- [ ] Severity indicated visually
- [ ] Errors logged for debugging

### For Tool Invocations

- [ ] Pre-flight availability check
- [ ] Clear message if tool missing
- [ ] Install instructions provided
- [ ] Graceful degradation when optional
- [ ] Timeout handling

---

## 🎯 ANTI-PATTERNS TO AVOID

### ❌ Anti-Pattern 1: Silent Failures

```go
// BAD
func doSomething() {
    err := riskyOperation()
    if err != nil {
        return  // ❌ Error lost!
    }
}

// GOOD
func doSomething() error {
    err := riskyOperation()
    if err != nil {
        return fmt.Errorf("failed to do something: %w", err)
    }
    return nil
}
```

---

### ❌ Anti-Pattern 2: Discarding Errors

```go
// BAD
home, _ := os.UserHomeDir()  // ❌ Error ignored!

// GOOD
home, err := os.UserHomeDir()
if err != nil {
    return fmt.Errorf("cannot determine home directory: %w", err)
}
```

---

### ❌ Anti-Pattern 3: Generic Error Messages

```go
// BAD
return errors.New("something went wrong")

// GOOD
return fmt.Errorf("failed to parse config at %s: %w", path, err)
```

---

### ❌ Anti-Pattern 4: Panic for Errors

```go
// BAD
if err != nil {
    panic(err)  // ❌ Don't panic for normal errors!
}

// GOOD
if err != nil {
    return fmt.Errorf("operation failed: %w", err)
}
```

---

## 📚 RECOMMENDED READING

### Anthropic Resources
- Claude Code Best Practices (2025)
- How Anthropic Teams Use Claude Code
- Claude Code 2.0 Workflow Guide

### Go Resources
- Go Blog: Error Handling and Go
- Effective Go: Errors
- Go Wiki: Error Handling Patterns

### Books
- "Error Handling in Go" - Various Authors
- "Production-Ready Go" - Patterns Chapter

---

## 🎯 SUCCESS CRITERIA

### For Air-Gap Implementation

- [ ] All new error types implement `error` interface
- [ ] All error types implement `Unwrap()`
- [ ] Severity system implemented (Fatal/Error/Warn/Info)
- [ ] Tool availability checker created
- [ ] All tool invocations have pre-flight checks
- [ ] User-friendly messages for all errors
- [ ] 100% test coverage on error handling

### For Production

- [ ] Zero silent failures
- [ ] All errors logged
- [ ] User documentation includes troubleshooting
- [ ] Error messages tested with users
- [ ] Metrics track error rates by type

---

**Generated**: 2025-11-14
**Mode**: Boris Cherny - "Errors should be impossible to ignore"
**Sources**: Anthropic 2025, Go 2025 patterns
**Next**: FASE 0.5.2 - Testing Patterns
