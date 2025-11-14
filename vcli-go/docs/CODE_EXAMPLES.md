# Real-World Code Examples from vCLI-GO

This document contains actual examples from the codebase demonstrating conventions in practice.

## Error Handling Examples

### Example 1: VCLIError in Action

From `internal/errors/types.go`:

```go
// VCLIError represents a structured error with context
type VCLIError struct {
    Type       ErrorType  // Category: CONNECTION, TIMEOUT, etc.
    Message    string     // User-friendly message
    Details    string     // Additional context
    Cause      error      // Underlying cause
    Retryable  bool       // Can this be retried?
    StatusCode int        // HTTP status code
    Service    string     // Which backend service
}

// Error implements the error interface
func (e *VCLIError) Error() string {
    var parts []string
    
    if e.Service != "" {
        parts = append(parts, fmt.Sprintf("[%s]", e.Service))
    }
    
    parts = append(parts, string(e.Type))
    parts = append(parts, e.Message)
    
    if e.Details != "" {
        parts = append(parts, fmt.Sprintf("(%s)", e.Details))
    }
    
    return strings.Join(parts, " ")
}

// NewConnectionError creates a connection error
func NewConnectionError(service, message string) *VCLIError {
    return &VCLIError{
        Type:      ErrorTypeConnection,
        Message:   message,
        Service:   service,
        Retryable: true,
    }
}
```

### Example 2: Using Error Builders

From `internal/errors/builders.go`:

```go
// ConnectionErrorBuilder helps build rich connection errors
type ConnectionErrorBuilder struct {
    service   string
    endpoint  string
    operation string
    cause     error
}

// NewConnectionErrorBuilder creates a new connection error builder
func NewConnectionErrorBuilder(service, endpoint string) *ConnectionErrorBuilder {
    return &ConnectionErrorBuilder{
        service:  service,
        endpoint: endpoint,
    }
}

// WithOperation sets the operation that failed
func (b *ConnectionErrorBuilder) WithOperation(operation string) *ConnectionErrorBuilder {
    b.operation = operation
    return b
}

// WithCause sets the underlying cause
func (b *ConnectionErrorBuilder) WithCause(cause error) *ConnectionErrorBuilder {
    b.cause = cause
    return b
}

// Build constructs the final contextual error
func (b *ConnectionErrorBuilder) Build() *ContextualError {
    base := NewConnectionError(b.service, "Failed to connect")
    if b.cause != nil {
        base = base.WithCause(b.cause)
    }
    
    ctx := ErrorContext{
        Endpoint:    b.endpoint,
        Operation:   b.operation,
        Suggestions: GetSuggestionsFor(ErrorTypeConnection, b.service, b.endpoint),
        HelpCommand: fmt.Sprintf("vcli troubleshoot %s", serviceToCommand(b.service)),
    }
    
    return NewContextualError(base, ctx)
}
```

## Context Usage Examples

### Example 1: HTTP Client with Context

From `internal/httpclient/client.go`:

```go
// Get performs a GET request with context
func (c *Client) Get(ctx context.Context, path string) ([]byte, error) {
    return c.DoRequest(ctx, "GET", path, nil)
}

// DoRequest performs an HTTP request with retry and circuit breaker
func (c *Client) DoRequest(ctx context.Context, method, path string, body []byte) ([]byte, error) {
    url := c.BaseURL + path
    startTime := time.Now()
    
    // Log request start
    c.Logger.Printf("[HTTP] %s %s", method, url)
    
    // Execute through circuit breaker and retrier
    result, err := c.Breaker.CallWithResult(func() (interface{}, error) {
        return c.Retrier.DoWithResult(ctx, func() (interface{}, error) {
            return c.executeRequest(ctx, method, url, body)
        })
    })
    
    // Handle result...
    return result.([]byte), err
}
```

### Example 2: Retry Strategy with Context

From `internal/retry/retry.go`:

```go
// Strategy defines retry behavior
type Strategy struct {
    MaxAttempts     int
    InitialDelay    time.Duration
    MaxDelay        time.Duration
    BackoffFactor   float64
    RetryableErrors []errors.ErrorType
}

// Do executes a function with retry logic and respects context
func (s *Strategy) Do(ctx context.Context, fn func() error) error {
    var lastErr error
    
    for attempt := 1; attempt <= s.MaxAttempts; attempt++ {
        // Execute the function
        err := fn()
        if err == nil {
            return nil  // Success!
        }
        
        lastErr = err
        
        // Check if we should retry
        if !s.shouldRetry(err, attempt) {
            return err
        }
        
        // Calculate delay with exponential backoff
        delay := s.calculateDelay(attempt)
        
        // Wait or check for context cancellation
        select {
        case <-ctx.Done():
            return ctx.Err()  // Respect cancellation
        case <-time.After(delay):
            // Continue to next attempt
        }
    }
    
    return fmt.Errorf("max retry attempts (%d) exceeded: %w", s.MaxAttempts, lastErr)
}
```

## Naming Convention Examples

### Example 1: Command Handlers

From `cmd/k8s.go`:

```go
// Handler functions use Handle<Resource><Action> pattern
var getPodsCmd = &cobra.Command{
    Use:   "pods",
    Short: "Get pods",
    Long: `Get all pods in a namespace or across all namespaces.`,
    RunE:  k8s.HandleGetPods,  // Delegates to handler
}

var getPodCmd = &cobra.Command{
    Use:   "pod [name]",
    Short: "Get a specific pod or list all pods",
    RunE:  k8s.HandleGetPod,
}

// Handler functions accept cobra parameters
// From internal/k8s/handlers.go (referenced):
// func HandleGetPods(cmd *cobra.Command, args []string) error { ... }
// func HandleGetPod(cmd *cobra.Command, args []string) error { ... }
```

### Example 2: Constructor and Factory Functions

From `internal/agents/orchestrator.go`:

```go
// NewAgentOrchestrator creates a new agent orchestrator
func NewAgentOrchestrator(config AgentConfig) (*AgentOrchestrator, error) {
    // Validate workspace path
    if config.WorkspacePath == "" {
        config.WorkspacePath = ".agents-workspace"
    }
    
    // Create workspace if it doesn't exist
    if err := os.MkdirAll(config.WorkspacePath, 0755); err != nil {
        return nil, fmt.Errorf("failed to create workspace: %w", err)
    }
    
    // Create MAXIMUS clients
    consciousnessClient := maximus.NewConsciousnessClient(config.MaximusConsciousnessEndpoint)
    governanceClient := maximus.NewGovernanceClient(config.MaximusGovernanceEndpoint)
    
    orchestrator := &AgentOrchestrator{
        agents:              make(map[AgentType]Agent),
        config:              config,
        workspacePath:       config.WorkspacePath,
        consciousnessClient: consciousnessClient,
        governanceClient:    governanceClient,
        runningWorkflows:    make(map[string]*WorkflowExecution),
        logger:              log.New(os.Stdout, "[AgentOrchestrator] ", log.LstdFlags),
    }
    
    return orchestrator, nil
}
```

### Example 3: Getter/Setter Pattern

From `internal/agents/orchestrator.go`:

```go
// GetAgent retrieves a registered agent by type
func (o *AgentOrchestrator) GetAgent(agentType AgentType) (Agent, bool) {
    o.mu.RLock()
    defer o.mu.RUnlock()
    agent, exists := o.agents[agentType]
    return agent, exists
}

// From internal/httpclient/client.go:
// SetLogger sets the logger for the client
func (c *Client) SetLogger(logger *log.Logger) {
    c.Logger = logger
}
```

### Example 4: Strategy Factory Functions

From `internal/retry/retry.go`:

```go
// DefaultStrategy returns a sensible default retry strategy
func DefaultStrategy() *Strategy {
    return &Strategy{
        MaxAttempts:   3,
        InitialDelay:  100 * time.Millisecond,
        MaxDelay:      5 * time.Second,
        BackoffFactor: 2.0,
        RetryableErrors: []errors.ErrorType{
            errors.ErrorTypeTimeout,
            errors.ErrorTypeNetwork,
            errors.ErrorTypeConnection,
            errors.ErrorTypeUnavailable,
        },
    }
}

// AggressiveStrategy returns a more aggressive retry strategy
func AggressiveStrategy() *Strategy {
    return &Strategy{
        MaxAttempts:   5,
        InitialDelay:  50 * time.Millisecond,
        MaxDelay:      10 * time.Second,
        BackoffFactor: 2.0,
        RetryableErrors: []errors.ErrorType{
            errors.ErrorTypeTimeout,
            errors.ErrorTypeNetwork,
            errors.ErrorTypeConnection,
            errors.ErrorTypeUnavailable,
        },
    }
}
```

## Logging Examples

### Example 1: Logger Setup

From `internal/agents/orchestrator.go`:

```go
// Logger is set up during construction with a prefix
orchestrator := &AgentOrchestrator{
    // ... other fields ...
    logger: log.New(os.Stdout, "[AgentOrchestrator] ", log.LstdFlags),
}
```

From `internal/httpclient/client.go`:

```go
// Logger field in struct
type Client struct {
    BaseURL    string
    HTTPClient *http.Client
    Logger     *log.Logger  // Optional logger
    // ... other fields ...
}

// Default: no logging
func NewClient(config ClientConfig) *Client {
    return &Client{
        // ...
        Logger: log.New(io.Discard, "", 0),  // Default: no logging
        // ...
    }
}

// Setter to enable custom logging
func (c *Client) SetLogger(logger *log.Logger) {
    c.Logger = logger
}
```

### Example 2: Logging in Operations

From `internal/httpclient/client.go`:

```go
// Log request start
c.Logger.Printf("[HTTP] %s %s", method, url)

// Log with more context
c.Logger.Printf("Registered agent: %s (%s)", agent.Name(), agentType)
```

### Example 3: Debug Logging

From `internal/resilience/client.go`:

```go
// Debug logging when enabled
if c.debug {
    fmt.Fprintf(os.Stderr, "[DEBUG] [%s] Executing with resilience (state=%s)\n",
        c.name, c.circuitBreaker.State())
}

// Retry attempt logging
if c.debug {
    fmt.Fprintf(os.Stderr, "[DEBUG] [%s] Retry attempt %d after %v (error: %v)\n",
        c.name, attempt.Number, attempt.Delay, attempt.Error)
}
```

## Type and Interface Examples

### Example 1: Configuration Structure

From `internal/httpclient/client.go`:

```go
// ClientConfig holds configuration for HTTP client
type ClientConfig struct {
    BaseURL       string
    Timeout       time.Duration
    RetryConfig   RetryConfig
    BreakerConfig BreakerConfig
    Headers       map[string]string
}

// DefaultClientConfig returns conservative defaults
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

### Example 2: Enum Pattern

From `internal/k8s/formatters.go`:

```go
// OutputFormat defines output format types
type OutputFormat string

const (
    OutputFormatTable OutputFormat = "table"
    OutputFormatJSON  OutputFormat = "json"
    OutputFormatYAML  OutputFormat = "yaml"
)
```

From `internal/errors/types.go`:

```go
// ErrorType represents the category of error
type ErrorType string

const (
    // Connection errors
    ErrorTypeConnection ErrorType = "CONNECTION"
    ErrorTypeTimeout    ErrorType = "TIMEOUT"
    ErrorTypeNetwork    ErrorType = "NETWORK"
    
    // Auth errors
    ErrorTypeAuth       ErrorType = "AUTH"
    // ... more error types ...
)
```

### Example 3: Concurrent Access with Mutex

From `internal/agents/orchestrator.go`:

```go
type AgentOrchestrator struct {
    // Agent registry with protection
    agents map[AgentType]Agent
    mu     sync.RWMutex
    
    // Workflow tracking with protection
    runningWorkflows map[string]*WorkflowExecution
    workflowMu       sync.RWMutex
    
    // Logger (no protection needed)
    logger *log.Logger
}

// Protected registration
func (o *AgentOrchestrator) RegisterAgent(agent Agent) error {
    o.mu.Lock()
    defer o.mu.Unlock()
    
    agentType := agent.Type()
    if _, exists := o.agents[agentType]; exists {
        return fmt.Errorf("agent %s already registered", agentType)
    }
    
    o.agents[agentType] = agent
    o.logger.Printf("Registered agent: %s (%s)", agent.Name(), agentType)
    
    return nil
}

// Protected access
func (o *AgentOrchestrator) GetAgent(agentType AgentType) (Agent, bool) {
    o.mu.RLock()
    defer o.mu.RUnlock()
    agent, exists := o.agents[agentType]
    return agent, exists
}
```

## File Organization Examples

### Example 1: Command File Structure

From `cmd/k8s.go`:

```go
package cmd

// Root command definition
var k8sCmd = &cobra.Command{
    Use:   "k8s",
    Short: "Kubernetes cluster management",
    Long:  `...`,
}

// ============================================================================
// GET COMMAND
// ============================================================================

var k8sGetCmd = &cobra.Command{
    Use:   "get [resource]",
    Short: "Get Kubernetes resources",
}

// Specific resource commands
var getPodsCmd = &cobra.Command{
    Use:     "pods",
    Aliases: []string{"po"},
    Short:   "Get pods",
    RunE:    k8s.HandleGetPods,
}

// Initialization
func init() {
    rootCmd.AddCommand(k8sCmd)
    k8sCmd.AddCommand(k8sGetCmd)
    k8sGetCmd.AddCommand(getPodsCmd)
    // ... more commands ...
}
```

### Example 2: Package Organization

From `internal/k8s/`:

```
k8s/
├── handlers.go        # Public handler functions (Handle*)
├── models.go          # Kubernetes model types
├── formatters.go      # Output formatting (implements Formatter interface)
├── kubeconfig.go      # Kubeconfig management
├── cluster_manager.go # Cluster operations
├── label_annotate.go  # Label/annotation operations
├── auth.go            # Authentication checks
├── types.go           # Additional types
├── yaml_parser.go     # YAML parsing utilities
└── *_test.go          # Test files
```

## Comments and Documentation Examples

### Example 1: Godoc Style Comments

From `internal/errors/types.go`:

```go
// ErrorType represents the category of error
type ErrorType string

// VCLIError represents a structured error with context
type VCLIError struct {
    Type       ErrorType  // Category of error
    Message    string     // User-friendly message
    Details    string     // Additional context
    Cause      error      // Underlying cause (for wrapping)
    Retryable  bool       // Whether error can be retried
    StatusCode int        // HTTP status code (if applicable)
    Service    string     // Which backend service caused the error
}

// Error implements the error interface
func (e *VCLIError) Error() string {
    // ... implementation ...
}

// Unwrap returns the underlying cause
func (e *VCLIError) Unwrap() error {
    return e.Cause
}

// IsRetryable returns whether this error can be retried
func (e *VCLIError) IsRetryable() bool {
    return e.Retryable
}
```

### Example 2: Inline Comments

From `internal/config/config.go`:

```go
// Get returns the global configuration, loading it if necessary
func Get() (*Config, error) {
    globalMutex.RLock()
    if loaded && globalConfig != nil {
        defer globalMutex.RUnlock()
        return globalConfig, nil
    }
    globalMutex.RUnlock()
    
    globalMutex.Lock()
    defer globalMutex.Unlock()
    
    // Double-check after acquiring write lock
    if loaded && globalConfig != nil {
        return globalConfig, nil
    }
    
    // Load configuration...
}
```

### Example 3: Section Separators

From `cmd/k8s.go`:

```go
// ============================================================================
// GET COMMAND
// ============================================================================

var k8sGetCmd = &cobra.Command {
    // ...
}

// ============================================================================
// GET POD COMMANDS
// ============================================================================

var getPodsCmd = &cobra.Command {
    // ...
}
```

