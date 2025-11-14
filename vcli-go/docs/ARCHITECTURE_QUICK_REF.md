# vCLI 2.0 Architecture - Quick Reference Card

## Project Structure at a Glance

```
vcli-go/
├── main.go                Entry point
├── cmd/                   60+ command implementations
│   ├── root.go           Command registration & init
│   ├── agents.go         Agent Smith (39 KB)
│   ├── k8s_*.go          Kubernetes (19 subcommands)
│   ├── maximus.go        AI integration (49 KB)
│   ├── immune*.go        Security operations (42 KB)
│   └── ... 30+ more commands
├── internal/             315 Go files, 73 modules
│   ├── agents/           Multi-agent framework
│   ├── shell/            REPL interface
│   ├── k8s/              K8s operations
│   ├── maximus/          AI service clients
│   ├── orchestrator/     Operation coordination
│   ├── config/           Settings management
│   ├── errors/           Structured error handling
│   ├── nlp/              Intent recognition
│   ├── tui/              Terminal UI
│   ├── security/         Auth/audit
│   └── ... 40+ more modules
├── api/                  gRPC protobuf definitions
└── plugins/              Plugin system
```

## Key Files to Know

| File | Purpose | Size |
|------|---------|------|
| `main.go` | Entry point | 24 lines |
| `cmd/root.go` | CLI framework | 278 lines |
| `cmd/agents.go` | Agent Smith framework | 39 KB |
| `cmd/maximus.go` | AI integration | 49 KB |
| `cmd/k8s.go` | Kubernetes main | 14 KB |
| `internal/agents/orchestrator.go` | Agent coordination | 10.7 KB |
| `internal/shell/completer.go` | Command completion | 30 KB |
| `internal/k8s/handlers.go` | K8s operations | 34 KB |
| `internal/config/config.go` | Config system | 2 KB |
| `internal/errors/types.go` | Error handling | Structured |

## Core Modules at a Glance

### Tier 1: Foundation
```
config/         → Singleton config manager
errors/         → Structured error types
gateway/        → Generic HTTP API client
```

### Tier 2: Infrastructure
```
shell/          → Interactive REPL
tui/            → Terminal UI (Bubble Tea)
k8s/            → Kubernetes wrapper
maximus/        → AI service clients
```

### Tier 3: Business Logic
```
agents/         → Multi-agent framework
orchestrator/   → Operation coordination
nlp/            → Intent recognition
security/       → Auth/audit/behavioral
```

### Tier 4: Resilience
```
retry/          → Retry with backoff
circuitbreaker/ → Fault tolerance
cache/          → Distributed caching
ratelimit/      → Rate limiting
```

### Tier 5: Operations
```
k8s/            → Cluster ops
hunting/        → Threat hunting
immune/         → Immune system
offensive/      → Red team
streams/        → Stream processing
```

## Design Patterns Quick Map

```
Strategy Pattern        → agents/strategies/ (language-specific)
Command Pattern         → cmd/ + Cobra
Adapter Pattern         → k8s/, maximus/, gateway/
Factory Pattern         → agents/orchestrator.go
Observer Pattern        → agents, shell, TUI
Singleton Pattern       → config/config.go
Registry Pattern        → agents/strategies/
Pipeline Pattern        → nlp/
Circuit Breaker         → circuitbreaker/
Retry with Backoff      → retry/
```

## Entry Point Flow

```
main.go
  ↓
cmd.Execute()
  ↓
rootCmd.Run()
  ├─→ Interactive Mode (default)
  │    shell.NewShell()
  │    → REPL loop
  │
  ├─→ Command Mode
  │    [command handler]
  │    → operation execution
  │
  └─→ Configuration Init
      cobra.OnInitialize(initConfig)
      → config.Get() [lazy load]
```

## Command Categories

| Category | Commands | Key Files | Size |
|----------|----------|-----------|------|
| **Kubernetes** | 19 subcommands | k8s*.go | 14 KB |
| **Agent Smith** | agents run/list/status | agents.go | 39 KB |
| **MAXIMUS** | consciousness/governance | maximus.go | 49 KB |
| **Security** | immune/threat/offensive | immune*.go | 42 KB |
| **Investigation** | investigate/hunting/intel | hunt*.go | 50 KB |
| **Data** | data/metrics/sync | data*.go | 50 KB |
| **Advanced** | gateway/hcl/orchestrate | misc | 30 KB |

## Service Integration Points

```
vCLI
├── MAXIMUS Backend (REST API)
│   ├── Consciousness (self-awareness)
│   ├── Governance (HITL decisions)
│   ├── Eureka (discovery)
│   ├── Oraculo (patterns)
│   └── Predict (ML)
│
├── Kubernetes (client-go)
│   ├── API Server
│   └── kubelet nodes
│
└── Optional Services
    ├── Redis (caching)
    └── Badger (local store)
```

## Dependency Hierarchy

```
External (37 direct)
├── CLI: Cobra 1.9.1
├── TUI: Bubble Tea 1.3.4
├── Cloud: k8s.io/client-go 0.31.0
├── Communication: gRPC 1.76.0
├── Data: Redis 9.14.1, Badger 4.8.0
└── Observability: Prometheus 1.23.2

Internal
cmd/
  → internal/shell
  → internal/agents
  → internal/k8s
  → internal/maximus
  → internal/config
  → internal/errors
  → internal/[40+ modules]
```

## Adding New Features Checklist

### New Module
- [ ] Create `internal/[feature]/` directory
- [ ] Implement core logic
- [ ] Follow established patterns (Strategy, Adapter, etc.)
- [ ] Add tests alongside code

### New Command
- [ ] Create `cmd/[feature].go`
- [ ] Implement command handler
- [ ] Register in `cmd/root.go` via `rootCmd.AddCommand()`
- [ ] Add subcommands if needed

### Service Integration
- [ ] Create client in `internal/[service]/client.go`
- [ ] Use `gateway.GatewayClient` or appropriate wrapper
- [ ] Implement `errors.VCLIError` error handling
- [ ] Add config in `config/types.go`

### Agent Strategy (Language Support)
- [ ] Implement `strategies.AnalysisStrategy` interface
- [ ] Implement `strategies.CodeGenStrategy` interface
- [ ] Register with `StrategyRegistry`
- [ ] Create `agents/[language]/` package

## Statistics at a Glance

```
Code Metrics
├── Total Go Files: 315 (internal) + 60 (cmd)
├── Total Lines: ~21,000 (internal)
├── Directories: 73 (internal)
├── Dependencies: 37 direct + 80+ transitive
└── Go Version: 1.24.0+

Largest Files
├── cmd/maximus.go: 49 KB
├── cmd/agents.go: 39 KB
├── cmd/immune.go: 23 KB
├── internal/k8s/handlers.go: 34 KB
└── internal/shell/completer.go: 30 KB

Architecture Complexity
├── Patterns Used: 10+
├── Service Integrations: 7+
├── Command Count: 60+
└── Module Count: 73
```

## Documentation Files

```
Available Architecture Docs
├── ARCHITECTURE_MAP.md       (1268 lines - comprehensive)
├── ARCHITECTURE_SUMMARY.md   (329 lines - overview)
└── ARCHITECTURE_QUICK_REF.md (this file - quick reference)
```

## Naming Conventions

### Packages
- `cmd/` - Command implementations (one file per command)
- `internal/[feature]/` - Feature modules (private)
- `pkg/` - Public re-exportable packages

### File Patterns
- `*_client.go` - Service clients
- `*_handlers.go` - Operation handlers
- `*_types.go` - Type definitions
- `*_test.go` - Unit tests
- `*_strategy.go` - Strategy implementations

### Interfaces
- `Agent` - Core agent interface
- `AnalysisStrategy` - Language analysis
- `CodeGenStrategy` - Code generation
- `TestStrategy` - Testing
- `Workspace` - TUI workspace

## Key Interfaces to Implement

```go
// Multi-agent framework
type Agent interface {
    Type() AgentType
    Name() string
    Execute(ctx context.Context, input AgentInput) (*AgentOutput, error)
    Validate(input AgentInput) error
    GetCapabilities() []string
    GetStatus() AgentStatus
}

// Language strategies
type AnalysisStrategy interface {
    Language() language.Language
    Analyze(ctx context.Context, targets []string) (*DiagnosticResult, error)
    GetCapabilities() []string
}

// TUI workspace
type Workspace interface {
    Name() string
    Init() error
    Update(msg tea.Msg) (Workspace, tea.Cmd)
    View() string
}
```

## Configuration (config.yaml)

```yaml
api:
  timeout: 30s
  retry: 3
endpoints:
  maximus: "http://localhost:8001"
  kubernetes: "~/.kube/config"
  gateway: "http://localhost:8000"
auth:
  token: "your-jwt-token"
output:
  format: "json|yaml|table"
```

## Environment Variables

```bash
VCLI_DEBUG=true              # Debug mode
VCLI_CONFIG=~/.vcli/config   # Config path
VCLI_OFFLINE=true            # Offline mode
VCLI_BACKEND=grpc            # Backend (http/grpc)
```

## Quick Command Reference

```bash
# Agent Smith
vcli agents list
vcli agents run diagnosticador --targets ./internal/

# Kubernetes
vcli k8s auth
vcli k8s apply -f manifest.yaml
vcli k8s logs deployment/my-app -n default

# MAXIMUS
vcli maximus consciousness ping
vcli maximus governance list-decisions

# Interactive shell
vcli                         # REPL mode
vcli --help                  # Show all commands
vcli tui                     # Launch TUI
```

## Testing

### Run Tests
```bash
make test                    # All tests
go test ./internal/...       # Internal packages
go test ./cmd/...            # Commands
```

### Test Files Pattern
```
internal/[feature]/*_test.go
cmd/*_test.go
```

## Build & Deploy

```bash
# Build
make build                   # Binary to ./bin/vcli

# Docker
docker build -t vcli:latest .

# Install
go install ./...
```

---

**Last Updated**: 2025-11-14  
**Coverage**: Complete vCLI 2.0 architecture  
**For Details**: See ARCHITECTURE_MAP.md
