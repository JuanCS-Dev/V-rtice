# Code Conventions and Patterns - vCLI-GO

This document outlines the established code conventions, patterns, and best practices used throughout the vCLI-GO codebase.

## Table of Contents

1. [Error Handling Patterns](#error-handling-patterns)
2. [Naming Conventions](#naming-conventions)
3. [Context Usage](#context-usage)
4. [Logging and Metrics](#logging-and-metrics)
5. [File Organization](#file-organization)
6. [Comments and Documentation](#comments-and-documentation)
7. [Type and Interface Patterns](#type-and-interface-patterns)
8. [Package Structure](#package-structure)

---

## Error Handling Patterns

### Custom Error Types

The codebase uses custom error types defined in `internal/errors/` and `internal/errors_new/`:

#### VCLIError (Primary Error Type)
Located in `internal/errors/types.go`, represents a structured error with context:

```go
type VCLIError struct {
    Type       ErrorType    // Category of error (CONNECTION, TIMEOUT, etc.)
    Message    string       // User-friendly message
    Details    string       // Additional context
    Cause      error        // Underlying cause (for wrapping)
    Retryable  bool         // Whether error can be retried
    StatusCode int          // HTTP status code (if applicable)
    Service    string       // Source service name
}
```

**Error Type Constants** (`ErrorType` is a string type):
- Connection errors: `ErrorTypeConnection`, `ErrorTypeTimeout`, `ErrorTypeNetwork`
- Auth errors: `ErrorTypeAuth`, `ErrorTypePermission`, `ErrorTypeCredentials`
- Validation errors: `ErrorTypeValidation`, `ErrorTypeNotFound`, `ErrorTypeConflict`
- Server errors: `ErrorTypeServer`, `ErrorTypeInternal`, `ErrorTypeUnavailable`
- Client errors: `ErrorTypeClient`, `ErrorTypeConfig`, `ErrorTypeInput`
- Circuit breaker: `ErrorTypeCircuitOpen`

### Error Creation Patterns

#### 1. **Using Constructor Functions** (Preferred)

```go
// Simple error creation
err := errors.NewConnectionError("MAXIMUS", "Failed to connect to governance API")

// Wrapping existing errors
err := errors.Wrap(originalErr, errors.ErrorTypeTimeout, "Request timeout")

// For HTTP errors
err := errors.NewHTTPError(503, responseBody)

// With additional context
err := errors.NewValidationError("Invalid configuration")
```

#### 2. **Using Builder Pattern**

For more complex error context, use builder pattern from `internal/errors/builders.go`:

```go
err := errors.NewConnectionErrorBuilder("MAXIMUS", "http://maximus:8080").
    WithOperation("governance_check").
    WithCause(underlying).
    Build()
```

#### 3. **Error Wrapping with fmt.Errorf** (Secondary Pattern)

While custom errors are preferred, `fmt.Errorf` is used for:
- Internal/temporary errors that won't be returned to users
- Orchestration layer errors
- Construction failures (e.g., in NewXxx functions)

```go
if err := os.MkdirAll(path, 0755); err != nil {
    return nil, fmt.Errorf("failed to create workspace: %w", err)
}
```

### Error Interface Implementation

All VCLIError types implement Go's error interface:

```go
func (e *VCLIError) Error() string {
    // Returns formatted error message
    return fmt.Sprintf("[%s] %s: %s", e.Service, e.Type, e.Message)
}

func (e *VCLIError) Unwrap() error {
    // Returns underlying cause for error chain inspection
    return e.Cause
}

func (e *VCLIError) IsRetryable() bool {
    return e.Retryable
}
```

### Error Context Chain Methods

VCLIError supports fluent context building:

```go
err := errors.NewAuthError("service", "auth failed").
    WithCause(tokenErr).
    WithDetails("reason: token expired")
```

### Error Handling Guidelines

1. **Always wrap errors with context**
   ```go
   // Good
   if err != nil {
       return errors.Wrap(err, errors.ErrorTypeNetwork, "failed to fetch data")
   }
   
   // Avoid
   if err != nil {
       return err  // Lost context
   }
   ```

2. **Use Retryable flag for resilience**
   ```go
   err := errors.NewTimeoutError("service", "request timed out")
   if errors.IsRetryable(err) {
       // Implement retry logic
   }
   ```

3. **Include service context**
   - Errors from external services should include the service name
   - Helps with observability and debugging

---

## Naming Conventions

### Variable Naming

- **camelCase for all variables and parameters**
  ```go
  maxRetries := 3
  kubeconfigPath := "/home/user/.kube/config"
  isNamespaced := true
  ```

- **Single letter variables only for:**
  - Loop iterators: `for i := 0; i < len(items); i++`
  - Method receivers: `func (c *Client) Get() {}`
  - Temporary intermediate results in short scopes

- **Avoid single letters for:**
  - Package-level variables
  - Function parameters
  - Struct fields

### Function and Method Naming

#### Command Handlers
- **Pattern**: `Handle<Resource><Action>`
- Located in handler files (e.g., `internal/k8s/handlers.go`)

```go
func HandleGetPods(cmd *cobra.Command, args []string) error
func HandleGetNamespace(cmd *cobra.Command, args []string) error
func HandleApplyConfig(cmd *cobra.Command, args []string) error
```

#### Constructors and Factories
- **Pattern**: `New<Type>`
- Returns initialized instance or error

```go
func NewClient(config ClientConfig) *Client
func NewAgentOrchestrator(config AgentConfig) (*AgentOrchestrator, error)
func NewRetrier(config RetryConfig) *Retrier
func NewConnectionErrorBuilder(service, endpoint string) *ConnectionErrorBuilder
```

#### Runners and Executors
- **Pattern**: `run<Command>` or `Run<Command>` (camelCase in cmd package)
- Handles cobra command execution
- Called from cobra.Command.RunE field

```go
func runAgentsList(cmd *cobra.Command, args []string) error
func runGraphStore(cmd *cobra.Command, args []string) error
```

#### Getters and Setters
- **Pattern**: `Get<Field>` / `Set<Field>`
- For accessing private fields

```go
func (c *Client) SetLogger(logger *log.Logger)
func (o *AgentOrchestrator) GetAgent(agentType AgentType) (Agent, bool)
```

#### Strategy and Config Functions
- **Pattern**: `<Strategy>Strategy()` or `Default<Config>()`
- Returns strategy/config instances

```go
func DefaultStrategy() *Strategy
func AggressiveStrategy() *Strategy
func ConservativeStrategy() *Strategy
func DefaultConfig(baseURL string) ClientConfig
```

#### Public Helpers
- **Pattern**: Short, descriptive names
- Lowercase if unexported, CamelCase if exported

```go
func (s *Strategy) shouldRetry(err error, attempt int) bool
func (b *AuthErrorBuilder) WithCause(cause error) *AuthErrorBuilder
func serviceToCommand(service string) string
```

### Type Naming

- **PascalCase for all types**
  ```go
  type VCLIError struct { ... }
  type AgentOrchestrator struct { ... }
  type ErrorType string
  type OutputFormat string
  type HandlerConfig struct { ... }
  ```

- **Concrete types (structs)**: Noun form
  ```go
  type Client struct { ... }
  type Pod struct { ... }
  type Namespace struct { ... }
  type CircuitBreaker struct { ... }
  ```

- **Interface types**: Verb or descriptor
  ```go
  type Formatter interface { ... }
  type Agent interface { ... }
  type Handler interface { ... }
  ```

- **Type aliases**: Follow base type style
  ```go
  type ErrorType string      // Constant-like strings
  type OutputFormat string   // Config values
  ```

### Package Naming

- **Lowercase, single word**
  ```go
  package k8s
  package retry
  package config
  package shell
  package errors
  package agents
  ```

- **For multi-word concepts, use shortest clear form**
  ```go
  package httpclient    // not httpClient or http_client
  package circuitbreaker  // not circuit_breaker
  package authz         // not authorization
  ```

### Constants and Global Variables

- **Constants**: UPPER_SNAKE_CASE or PascalCase based on context
  ```go
  const (
      version   = "2.0.0"
      buildDate = "2025-10-07"
      MinWidth  = 86
      MinHeight = 30
  )
  
  // Error type constants use PascalCase
  const (
      ErrorTypeTimeout ErrorType = "TIMEOUT"
      ErrorTypeNetwork ErrorType = "NETWORK"
  )
  ```

- **Package-level variables**: camelCase (unexported)
  ```go
  var (
      globalConfig *Config
      globalMutex  sync.RWMutex
      loaded       bool
  )
  ```

- **Exported variables**: PascalCase
  ```go
  var DefaultConfig = Config{ ... }
  ```

---

## Context Usage

### Context Passing Pattern

Context is passed as the **first parameter** in functions that perform I/O or can block:

```go
func (c *Client) Get(ctx context.Context, path string) ([]byte, error)
func (c *Client) DoRequest(ctx context.Context, method, path string, body []byte) ([]byte, error)
func (s *Strategy) Do(ctx context.Context, fn func() error) error
func (c *Client) Execute(ctx context.Context, fn func() error) error
```

### Context Creation Patterns

#### Background Context
Used for operations without timeout requirements:
```go
ctx := context.Background()
result, err := handler(ctx)
```

#### Timeout Context
Standard pattern for HTTP operations and external service calls:
```go
ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
defer cancel()
err := client.Get(ctx, "/api/endpoint")
```

#### Cancellation
For interactive operations and long-running tasks:
```go
ctx, cancel := context.WithCancel(context.Background())
defer cancel()

// Can be cancelled externally
<-signalChan  // User interrupt
cancel()      // Stop all operations
```

### Context in Retry Logic

Properly respects context cancellation:

```go
func (s *Strategy) Do(ctx context.Context, fn func() error) error {
    for attempt := 1; attempt <= s.MaxAttempts; attempt++ {
        err := fn()
        if err == nil {
            return nil
        }
        
        if !s.shouldRetry(err, attempt) {
            return err
        }
        
        delay := s.calculateDelay(attempt)
        
        // Respect context cancellation
        select {
        case <-ctx.Done():
            return ctx.Err()
        case <-time.After(delay):
            // Continue to next attempt
        }
    }
    return fmt.Errorf("max attempts exceeded")
}
```

### Context in Circuit Breaker

Circuit breaker operations accept context:

```go
func (c *CircuitBreaker) Execute(ctx context.Context, fn func() error) error {
    // Check context before executing
    select {
    case <-ctx.Done():
        return ctx.Err()
    default:
    }
    
    // Proceed with function execution...
}
```

### Key Patterns

1. **Always pass context through the call chain**
   - From handlers down to low-level operations
   - Enables cancellation propagation

2. **Create timeouts at the boundary**
   - HTTP client creation: wrap in timeout
   - User-initiated operations: respect context

3. **Check context early**
   - Before starting expensive operations
   - In retry loops

---

## Logging and Metrics

### Logging Library

The codebase uses Go's standard `log` package:

```go
import "log"

logger := log.New(os.Stdout, "[ServiceName] ", log.LstdFlags)
logger.Printf("Operation completed in %v", duration)
```

### Logger Configuration Patterns

#### Default Logger
```go
Logger: log.New(io.Discard, "", 0), // Default: no logging (opt-in)
```

#### Custom Prefix Logger
```go
logger := log.New(
    os.Stdout,
    "[DIAGNOSTICADOR] ",
    log.LstdFlags,  // Includes date and time
)
```

#### Struct Field Pattern
Services include a logger field:

```go
type Client struct {
    BaseURL    string
    HTTPClient *http.Client
    Logger     *log.Logger
    Retrier    *Retrier
    Breaker    *CircuitBreaker
}

// Setter method
func (c *Client) SetLogger(logger *log.Logger) {
    c.Logger = logger
}
```

### Logging Patterns

#### Operation Logging
```go
c.Logger.Printf("[HTTP] %s %s", method, url)
```

#### Debug Logging
```go
if c.debug {
    fmt.Fprintf(os.Stderr, "[DEBUG] [%s] Executing with resilience\n", c.name)
}
```

#### Formatted Output
```go
fmt.Fprintf(os.Stderr, "[DEBUG] [%s] Retry attempt %d after %v\n", 
    c.name, attempt.Number, attempt.Delay)
```

### Log Levels

While not explicitly enforced, pattern shows:
- **Debug**: Detailed execution flow (requires flag check)
- **Info**: Operation milestones (printed to stdout/stderr)
- **Error**: Error conditions (part of error handling)
- **No Warn**: Standard library doesn't support; use Info instead

### Metrics/Observability

The codebase integrates with Prometheus:

```go
require (
    github.com/prometheus/client_golang v1.23.2
)
```

Metrics are typically:
- **Recorded in client implementations**
- **Exposed via metrics endpoints**
- **Examples in httpclient and agent packages**

#### Metric Naming Pattern
```
vcli_<component>_<metric>_<unit>
```

Example locations where metrics may be recorded:
- Request latency in HTTP clients
- Agent execution times
- Circuit breaker state changes
- Retry attempt counts

---

## File Organization

### Directory Structure

#### Command Layer (`cmd/`)
- **One file per major command** (e.g., `agents.go`, `k8s.go`, `data.go`)
- **Subcommand definitions** within command file
- **Command variable naming**: `<command><subcommand>Cmd`
- **Command handler functions**: `run<SubCommand>` (in same file)

```
cmd/
├── root.go           # Root command and initialization
├── agents.go         # agents command and all agent subcommands
├── k8s.go            # k8s command and resource subcommands
├── data.go           # data command and ingestion subcommands
├── examples.go       # examples command
└── ...
```

#### Internal Packages (`internal/`)

- **One concern per package**
- **Exported types and functions only**
- **Private helpers are package-local**

```
internal/
├── errors/              # Error types and builders
├── errors_new/          # Alternative error implementation
├── k8s/                 # Kubernetes operations
│   ├── handlers.go      # HTTP request handlers
│   ├── models.go        # Kubernetes model types
│   ├── formatters.go    # Output formatting
│   └── *_test.go        # Tests
├── httpclient/          # HTTP client with retry/breaker
├── retry/               # Retry strategy implementation
├── resilience/          # Combined retry + circuit breaker
├── config/              # Configuration management
├── agents/              # Multi-agent orchestration
└── shell/               # Interactive shell
```

### File Naming Patterns

#### Handler Files
```
<package>_handlers.go
k8s_handlers.go
```

#### Model/Type Files
```
<package>_models.go
k8s_models.go
types.go
```

#### Test Files
```
<filename>_test.go
client_test.go
handlers_test.go
formatters_test.go
```

#### Build/Config Files
```
<component>_test.go         # Integration tests
<filename>_100pct_test.go   # Complete coverage variants
```

### File Size Guidelines

- **Keep files focused**: One primary type per file (with related helpers)
- **Handlers file**: Can contain multiple related handlers
- **Models file**: Types, constants, and constructors

---

## Comments and Documentation

### Godoc Comment Pattern

#### Package Documentation
Located at top of file, before `package` declaration:

```go
// Package errors provides structured error types and creation patterns
// for the vCLI application, supporting error wrapping, context building,
// and retryability detection.
package errors
```

#### Type Documentation
Immediately before type definition:

```go
// VCLIError represents a structured error with context and metadata
// for better error handling and user-facing error messages.
type VCLIError struct {
    Type       ErrorType  // Category of error
    Message    string     // User-friendly message
    Cause      error      // Underlying cause
    Retryable  bool       // Whether error can be retried
}
```

#### Function/Method Documentation
Immediately before declaration, following pattern: "Name <verb> <description>":

```go
// Error implements the error interface for VCLIError
func (e *VCLIError) Error() string { ... }

// NewConnectionError creates a connection error with service context
func NewConnectionError(service, message string) *VCLIError { ... }

// WithCause adds a cause to the error and returns the error for chaining
func (e *VCLIError) WithCause(cause error) *VCLIError { ... }
```

### Inline Comments

#### Explaining Complex Logic
```go
// Double-check after acquiring write lock to ensure another goroutine
// didn't already load the configuration
if loaded && globalConfig != nil {
    return globalConfig, nil
}
```

#### Section Separators
Used in command files to organize related commands:

```go
// ============================================================================
// GET COMMAND
// ============================================================================

// getPodsCmd gets all pods in a namespace
var getPodsCmd = &cobra.Command{ ... }
```

#### Marking Private vs Exported
```go
// isRetryable determines if an error type is retryable
// (unexported helper function)
func isRetryable(errType ErrorType) bool { ... }

// IsRetryable checks if an error can be retried
// (exported public function)
func IsRetryable(err error) bool { ... }
```

### Comment Style Guidelines

1. **Complete sentences** for exported items
   ```go
   // Good
   // NewClient creates a new HTTP client with resilience patterns
   
   // Avoid
   // create client
   ```

2. **Concise descriptions** for common patterns
   ```go
   // Unexported helpers
   // shouldRetry checks if we should retry the operation
   ```

3. **Explain why, not what**
   ```go
   // Good - explains intention
   // Respect context cancellation to enable proper shutdown
   select {
   case <-ctx.Done():
       return ctx.Err()
   
   // Avoid - states obvious code
   // Check if context is done
   ```

4. **No redundant comments**
   ```go
   // Good
   return globalConfig, nil
   
   // Avoid
   return globalConfig, nil  // Return config and nil error
   ```

---

## Type and Interface Patterns

### Struct Patterns

#### Configuration Structs
Include all settings, with sensible zero values:

```go
type ClientConfig struct {
    BaseURL       string
    Timeout       time.Duration
    RetryConfig   RetryConfig
    BreakerConfig BreakerConfig
    Headers       map[string]string
}
```

**Pattern**: Provide factory function with defaults:

```go
func DefaultClientConfig(baseURL string) ClientConfig {
    return ClientConfig{
        BaseURL:       baseURL,
        Timeout:       30 * time.Second,
        RetryConfig:   DefaultRetryConfig(),
        BreakerConfig: DefaultBreakerConfig(),
        Headers:       make(map[string]string),
    }
}
```

#### Service Structs
Contain dependencies and state:

```go
type Client struct {
    BaseURL    string
    HTTPClient *http.Client
    Retrier    *Retrier           // Dependency
    Breaker    *CircuitBreaker    // Dependency
    Logger     *log.Logger        // Optional
    Headers    map[string]string  // Configuration
}
```

#### State Tracking Structs
Include mutexes for concurrent access:

```go
type AgentOrchestrator struct {
    agents            map[AgentType]Agent
    mu                sync.RWMutex        // Protects agents
    runningWorkflows  map[string]*WorkflowExecution
    workflowMu        sync.RWMutex        // Protects workflows
    logger            *log.Logger
}
```

### Interface Patterns

#### Single-Method Interfaces
Used for specific capabilities:

```go
type Formatter interface {
    Format(data interface{}) (string, error)
}

type Agent interface {
    Type() AgentType
    Name() string
    Execute(ctx context.Context, task Task) (*Result, error)
}
```

#### Builder Interfaces
For fluent API construction:

```go
type ConnectionErrorBuilder struct {
    service   string
    endpoint  string
    operation string
    cause     error
}

// Methods return *ConnectionErrorBuilder for chaining
func (b *ConnectionErrorBuilder) WithOperation(operation string) *ConnectionErrorBuilder {
    b.operation = operation
    return b
}
```

### Enum Patterns

Using type alias for enumerated values:

```go
type ErrorType string

const (
    ErrorTypeConnection ErrorType = "CONNECTION"
    ErrorTypeTimeout    ErrorType = "TIMEOUT"
    ErrorTypeNetwork    ErrorType = "NETWORK"
    ErrorTypeAuth       ErrorType = "AUTH"
)

type OutputFormat string

const (
    OutputFormatTable OutputFormat = "table"
    OutputFormatJSON  OutputFormat = "json"
    OutputFormatYAML  OutputFormat = "yaml"
)
```

**Validation pattern**:
```go
func (f OutputFormat) IsValid() bool {
    switch f {
    case OutputFormatTable, OutputFormatJSON, OutputFormatYAML:
        return true
    default:
        return false
    }
}
```

### Builder Pattern Implementation

```go
// Stage 1: Creation
builder := errors.NewConnectionErrorBuilder("service", "endpoint")

// Stage 2: Configuration (chaining)
builder.
    WithOperation("operation").
    WithCause(err)

// Stage 3: Build (finalization)
finalError := builder.Build()
```

---

## Package Structure

### Internal Package Organization

#### Layered Architecture

**Command Layer** (`cmd/`)
- Accepts user input
- Calls handler functions
- Delegates to business logic

**Handler Layer** (functions in `internal/<component>/`)
- Parses arguments/flags
- Validates input
- Orchestrates operations

**Business Logic Layer** (`internal/<component>/`)
- Core algorithms
- External service integration
- Data transformation

**Utility Layer** (`internal/errors/`, `internal/retry/`, etc.)
- Cross-cutting concerns
- Reusable patterns
- Framework code

#### Export Strategy

**What to export:**
- User-facing types (errors, config)
- Public APIs (handler functions)
- Factory functions (New*, Default*)
- Interface definitions

**What to keep private:**
- Implementation details
- Helper functions
- Internal state managers

**Pattern**:
```go
// Exported - used by other packages
type VCLIError struct { ... }
func New(errType ErrorType, message string) *VCLIError { ... }
func (e *VCLIError) Error() string { ... }

// Private - internal only
func isRetryable(errType ErrorType) bool { ... }
```

### Import Organization

Standard Go convention - three groups separated by blank lines:

```go
import (
    // Standard library
    "context"
    "fmt"
    "log"
    
    // Third-party packages
    "github.com/spf13/cobra"
    "github.com/charmbracelet/bubbletea"
    
    // Internal packages
    "github.com/verticedev/vcli-go/internal/errors"
    "github.com/verticedev/vcli-go/internal/k8s"
)
```

---

## Summary Table

| Aspect | Convention | Example |
|--------|-----------|---------|
| **Variables** | camelCase | `maxRetries`, `kubeconfigPath` |
| **Functions** | CamelCase (exported), camelCase (private) | `NewClient`, `isRetryable` |
| **Types** | PascalCase | `VCLIError`, `CircuitBreaker` |
| **Constants** | UPPER_SNAKE_CASE or PascalCase | `ErrorTypeTimeout`, `MinWidth` |
| **Packages** | lowercase | `errors`, `k8s`, `httpclient` |
| **Errors** | Custom types with context | `errors.NewConnectionError(...)` |
| **Context** | First parameter in I/O funcs | `func Get(ctx context.Context, ...` |
| **Logging** | `log.New()` with prefix | `log.New(os.Stdout, "[Service] ", log.LstdFlags)` |
| **Comments** | Godoc style for exported items | `// Error implements the error interface` |
| **Files** | One concern per file | `handlers.go`, `models.go` |
| **Tests** | `_test.go` suffix | `client_test.go` |

---

## Best Practices Checklist

When writing new code:

- [ ] Use custom error types with context, not bare errors
- [ ] Pass context as first parameter in functions that do I/O
- [ ] Use builder pattern for complex error construction
- [ ] Keep functions focused and testable
- [ ] Export only necessary types and functions
- [ ] Include Godoc comments for all exported items
- [ ] Use sync.RWMutex for concurrent map access
- [ ] Implement fluent APIs using method chaining
- [ ] Validate input in constructors/handlers
- [ ] Include service/endpoint context in errors
- [ ] Handle context cancellation in loops
- [ ] Use interfaces for dependencies (dependency injection)
- [ ] Test error conditions thoroughly
- [ ] Avoid global state (prefer dependency injection)
- [ ] Document non-obvious algorithmic choices

