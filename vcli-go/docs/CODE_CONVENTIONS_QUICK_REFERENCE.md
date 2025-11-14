# Code Conventions Quick Reference

Quick lookup for the most common code patterns and conventions.

## Error Handling - Quick Reference

### Creating Errors

```go
// Basic error with context
err := errors.NewConnectionError("MAXIMUS", "failed to connect")

// Wrapping existing error
err := errors.Wrap(originalErr, errors.ErrorTypeTimeout, "request timed out")

// HTTP errors
err := errors.NewHTTPError(503, responseBody)

// Builder for complex context
err := errors.NewConnectionErrorBuilder("service", "http://endpoint").
    WithOperation("operation_name").
    WithCause(underlying).
    Build()
```

### Error Types Available

**Transient/Retryable:**
- `ErrorTypeTimeout`
- `ErrorTypeNetwork`
- `ErrorTypeConnection`
- `ErrorTypeUnavailable`

**Non-Retryable:**
- `ErrorTypeAuth`, `ErrorTypePermission`, `ErrorTypeCredentials`
- `ErrorTypeValidation`, `ErrorTypeNotFound`, `ErrorTypeConflict`
- `ErrorTypeServer`, `ErrorTypeInternal`
- `ErrorTypeConfig`, `ErrorTypeInput`
- `ErrorTypeCircuitOpen`

## Naming - Quick Reference

| What | Style | Example |
|------|-------|---------|
| Variables | camelCase | `maxRetries` |
| Functions (exported) | PascalCase | `NewClient` |
| Functions (private) | camelCase | `isRetryable` |
| Types | PascalCase | `VCLIError` |
| Constants | UPPER_SNAKE_CASE | `ErrorTypeTimeout` |
| Packages | lowercase | `httpclient` |

### Function Patterns

```go
// Constructor
func NewClient(config ClientConfig) *Client

// Handler (in commands)
func HandleGetPods(cmd *cobra.Command, args []string) error

// Runner (in cmd package)
func runAgentsList(cmd *cobra.Command, args []string) error

// Strategy factory
func DefaultStrategy() *Strategy

// Setter
func (c *Client) SetLogger(logger *log.Logger)

// Getter
func (o *Orchestrator) GetAgent(agentType AgentType) (Agent, bool)
```

## Context Usage - Quick Reference

### Pass context as first parameter

```go
func (c *Client) Get(ctx context.Context, path string) ([]byte, error)
func (s *Strategy) Do(ctx context.Context, fn func() error) error
```

### Creating contexts

```go
// For background operations
ctx := context.Background()

// With timeout
ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
defer cancel()

// With cancellation
ctx, cancel := context.WithCancel(context.Background())
defer cancel()
```

### Respecting cancellation in loops

```go
select {
case <-ctx.Done():
    return ctx.Err()
case <-time.After(delay):
    // Continue
}
```

## Logging - Quick Reference

### Setting up a logger

```go
import "log"

logger := log.New(os.Stdout, "[ServiceName] ", log.LstdFlags)
logger.Printf("Operation completed in %v", duration)
```

### In structs

```go
type Client struct {
    Logger *log.Logger
}

func (c *Client) SetLogger(logger *log.Logger) {
    c.Logger = logger
}
```

### Debug logging

```go
if debug {
    fmt.Fprintf(os.Stderr, "[DEBUG] %s\n", message)
}
```

## Comments - Quick Reference

### Exported functions (Godoc style)

```go
// ErrorType represents the category of error
type ErrorType string

// NewClient creates a new HTTP client with retry and circuit breaker
func NewClient(config ClientConfig) *Client

// WithCause adds a cause to the error and returns it for chaining
func (e *VCLIError) WithCause(cause error) *VCLIError
```

### Unexported helpers

```go
// shouldRetry checks if we should retry the operation
func (s *Strategy) shouldRetry(err error, attempt int) bool
```

### Inline comments - explain why, not what

```go
// Respect context cancellation to enable graceful shutdown
select {
case <-ctx.Done():
    return ctx.Err()
```

## File Organization - Quick Reference

### Command file layout

```go
// cmd/mycommand.go
package cmd

var myCmd = &cobra.Command{
    Use:   "mycommand",
    Short: "Description",
    // ...
}

var mySubCmd = &cobra.Command{
    Use:   "subcommand",
    RunE:  runMySubCommand,
}

func runMySubCommand(cmd *cobra.Command, args []string) error {
    // Implementation
}

func init() {
    rootCmd.AddCommand(myCmd)
    myCmd.AddCommand(mySubCmd)
}
```

### Internal package layout

```
internal/mypackage/
├── types.go           # Type definitions, constants
├── models.go          # Data models (alternative to types.go)
├── handlers.go        # Public handler functions
├── client.go          # Client/service implementation
├── builders.go        # Builder pattern implementations
├── private.go         # Unexported helpers
└── *_test.go          # Tests
```

## Type Patterns - Quick Reference

### Configuration struct with factory

```go
type ClientConfig struct {
    BaseURL string
    Timeout time.Duration
    Retries int
}

func DefaultClientConfig(baseURL string) ClientConfig {
    return ClientConfig{
        BaseURL: baseURL,
        Timeout: 30 * time.Second,
        Retries: 3,
    }
}
```

### Enum pattern (using type alias)

```go
type OutputFormat string

const (
    OutputFormatTable OutputFormat = "table"
    OutputFormatJSON  OutputFormat = "json"
    OutputFormatYAML  OutputFormat = "yaml"
)
```

### Service struct with dependencies

```go
type Client struct {
    BaseURL    string           // Configuration
    HTTPClient *http.Client     // Dependency
    Retrier    *Retrier         // Dependency
    Logger     *log.Logger      // Optional
    mu         sync.RWMutex     // Protection
}

func NewClient(config ClientConfig) *Client {
    return &Client{
        BaseURL:    config.BaseURL,
        HTTPClient: &http.Client{Timeout: config.Timeout},
        Retrier:    NewRetrier(config.RetryConfig),
        Logger:     log.New(io.Discard, "", 0),
    }
}
```

### Fluent builder

```go
builder := errors.NewConnectionErrorBuilder("service", "endpoint").
    WithOperation("operation").
    WithCause(err)

finalErr := builder.Build()
```

## Testing - Quick Reference

### Test file naming

```go
client_test.go        // Tests for client.go
handlers_test.go      // Tests for handlers.go
types_100pct_test.go  // Complete coverage variant
```

### Test structure

```go
func TestNewClient(t *testing.T) {
    // Setup
    config := DefaultClientConfig("http://localhost:8080")
    
    // Execute
    client := NewClient(config)
    
    // Assert
    assert.NotNil(t, client)
    assert.Equal(t, "http://localhost:8080", client.BaseURL)
}

func TestHandleGetPods_WithValidInput(t *testing.T) {
    t.Run("with default namespace", func(t *testing.T) {
        // Test implementation
    })
    
    t.Run("with custom namespace", func(t *testing.T) {
        // Test implementation
    })
}
```

## Common Gotchas

### Don't forget to pass context

```go
// Wrong - no context
resp := client.Get("/api/endpoint")

// Right - with context
ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
defer cancel()
resp := client.Get(ctx, "/api/endpoint")
```

### Proper error wrapping

```go
// Wrong - lost context
if err != nil {
    return err
}

// Right - wrapped with context
if err != nil {
    return errors.Wrap(err, errors.ErrorTypeNetwork, "failed to fetch data")
}
```

### Mutex protection

```go
// Wrong - no protection
func (o *Orchestrator) GetAgent(agentType AgentType) Agent {
    return o.agents[agentType]
}

// Right - protected
func (o *Orchestrator) GetAgent(agentType AgentType) (Agent, bool) {
    o.mu.RLock()
    defer o.mu.RUnlock()
    agent, exists := o.agents[agentType]
    return agent, exists
}
```

### Context cleanup

```go
// Wrong - defer before return
ctx, cancel := context.WithTimeout(...)
return doSomething(ctx)  // cancel not called

// Right - defer immediately
ctx, cancel := context.WithTimeout(...)
defer cancel()
return doSomething(ctx)
```

