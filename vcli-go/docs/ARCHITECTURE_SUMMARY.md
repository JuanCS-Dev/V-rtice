# vCLI 2.0 Architecture Summary

## Quick Reference

**Comprehensive architecture map created**: `docs/ARCHITECTURE_MAP.md` (1268 lines)

### Key Numbers
- **315 Go source files** in `internal/`
- **60+ command implementations** in `cmd/`
- **73 module directories** for feature organization
- **~21,000 lines of code** in core packages
- **37 direct + 80+ transitive dependencies**

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         vCLI 2.0                             │
│              (High-Performance CLI for Cybersecurity)        │
└──────────────────┬──────────────────────────────────────────┘
                   │
        ┌──────────┼──────────┐
        │          │          │
     ┌──▼──┐   ┌──▼──┐   ┌──▼──┐
     │ CLI │   │ TUI │   │ API │
     │(Cmd)│   │(BubbleTea) │
     └──┬──┘   └──┬──┘   └──┬──┘
        │         │         │
     ┌──┴─────────┴─────────┴──┐
     │   Core Internal Modules   │
     ├──────────────────────────┤
     │ • Agents (AI Framework)   │
     │ • Kubernetes Integration  │
     │ • MAXIMUS (AI Services)   │
     │ • Orchestration Engine    │
     │ • Configuration System    │
     │ • Error Handling          │
     │ • NLP Pipeline            │
     │ • Security & Authorization│
     │ • Resilience Patterns     │
     └──────────────────────────┘
             │
     ┌───────┴──────────┬────────────┬──────────┐
     │                  │            │          │
  ┌──▼──┐        ┌──────▼──┐   ┌────▼──┐   ┌──▼──┐
  │K8s  │        │ MAXIMUS │   │Redis  │   │Badger│
  │API  │        │Services │   │Cache  │   │Store │
  └─────┘        └─────────┘   └───────┘   └──────┘
```

---

## Core Module Breakdown

### 1. Agent Smith Framework (`internal/agents/`)
- **Purpose**: Multi-agent autonomous development system
- **Agents**: Diagnosticador, Arquiteto, DevSenior, Tester
- **Pattern**: Strategy + Factory
- **Key File**: `orchestrator.go` (10.7 KB)

### 2. Interactive Shell (`internal/shell/`)
- **Purpose**: REPL-style command interface
- **Components**: Executor, Completer, BubbleTea TUI
- **Pattern**: Model-View-Update (MVC)
- **Key Files**: `executor.go`, `completer.go` (30 KB)

### 3. Kubernetes Integration (`internal/k8s/`)
- **Purpose**: Unified cluster operations interface
- **Operations**: CRUD, exec, logs, metrics, rollouts
- **Pattern**: Adapter wrapping client-go
- **Key File**: `handlers.go` (34 KB)

### 4. MAXIMUS Integration (`internal/maximus/`)
- **Purpose**: AI consciousness and governance
- **Clients**: Consciousness, Governance, Eureka, Oraculo, Predict
- **Pattern**: Service Adapter
- **Protocol**: REST with JWT

### 5. Orchestration Engine (`internal/orchestrator/`)
- **Purpose**: Complex security operation coordination
- **Domains**: Defensive, Offensive, Monitoring, OSINT
- **Pattern**: Strategy + Observer
- **Key File**: `engine.go` (16.6 KB)

### 6. Configuration System (`internal/config/`)
- **Purpose**: Centralized settings management
- **Pattern**: Singleton with lazy loading
- **Features**: YAML, ENV overrides, runtime configuration

### 7. Error Handling (`internal/errors/`)
- **Purpose**: Structured, context-aware error management
- **Pattern**: Builder + Chain of Responsibility
- **Features**: Error types, suggestions, retryability metadata

### 8. NLP Pipeline (`internal/nlp/`)
- **Purpose**: Natural language intent recognition
- **Pattern**: Pipeline (stages: tokenize → validate → intent → entity → generate)
- **Submodules**: tokenizer, validator, context, intent, entities, generator

---

## Design Patterns Used

| Pattern | Usage | Location |
|---------|-------|----------|
| **Strategy** | Language-specific code analysis | `agents/strategies/` |
| **Command** | CLI command tree | `cmd/` + Cobra |
| **Adapter** | Service integration (K8s, MAXIMUS) | `k8s/`, `maximus/`, `gateway/` |
| **Factory** | Agent instantiation | `agents/orchestrator.go` |
| **Observer** | Event-driven architecture | agents, shell, TUI |
| **Singleton** | Global configuration, clients | `config/config.go` |
| **Registry** | Plugin management | `agents/strategies/` |
| **Pipeline** | NLP processing stages | `nlp/` |
| **Circuit Breaker** | Fault tolerance | `circuitbreaker/` |
| **Retry with Backoff** | Resilient operations | `retry/` |

---

## Dependency Architecture

### External Dependencies (Core)
- **CLI**: Cobra 1.9.1
- **TUI**: Bubble Tea 1.3.4, Bubbles 0.21.0, Lipgloss 1.1.0
- **Cloud**: k8s.io/client-go 0.31.0
- **Communication**: gRPC 1.76.0, Protocol Buffers 3, WebSocket
- **Data**: Redis 9.14.1, Badger 4.8.0
- **Observability**: Prometheus 1.23.2, OpenTelemetry 1.37.0
- **Security**: JWT 5.3.0, OTP 1.5.0

### Internal Hierarchy
```
cmd/ (Command Layer)
  ↓
internal/ (Domain Layer)
  ├── agents/ → strategies/
  ├── k8s/ → client-go
  ├── maximus/ → gateway/
  ├── orchestrator/
  ├── shell/ → bubbletea/
  ├── config/ (Singleton)
  ├── errors/
  └── ... (30+ more modules)
```

---

## Entry Points

### 1. Application Start
```
main.go → cmd.Execute() → rootCmd.Run()
```

### 2. Interactive Mode (Default)
```
rootCmd.Run() → shell.NewShell() → REPL loop
```

### 3. Command Mode
```
rootCmd.Run() → [command handler] → Operation execution
```

### 4. Configuration Init
```
cobra.OnInitialize(initConfig) → config.Get() [Lazy load]
```

---

## Service Integration Points

### MAXIMUS Backend Services
- **Consciousness Service**: Self-awareness, decision-making
- **Governance Service**: Ethical governance, HITL decisions
- **Eureka Service**: Service discovery
- **Oraculo Service**: Pattern recognition
- **Predict Service**: ML predictions

### Kubernetes Cluster
- **API Server**: Resource operations
- **kubelet**: Pod execution, metrics

### Optional Data Services
- **Redis**: Distributed caching
- **Badger DB**: Local persistence

### Monitoring/Telemetry
- **Prometheus**: Metrics collection
- **OpenTelemetry**: Distributed tracing

---

## Module Organization

### By Responsibility
```
Infrastructure:
├── config/          (Configuration)
├── errors/          (Error handling)
├── gateway/         (API client)
└── grpc/            (gRPC utilities)

User Interface:
├── shell/           (Interactive shell)
├── tui/             (Terminal UI)
├── visual/          (Rendering & styles)
└── palette/         (Color management)

Business Logic:
├── agents/          (Agent framework)
├── k8s/             (Kubernetes)
├── maximus/         (AI integration)
├── orchestrator/    (Operation coordination)
└── nlp/             (Intent recognition)

Security:
├── auth/            (Authentication)
├── authz/           (Authorization)
├── audit/           (Audit logging)
├── behavioral/      (Behavior analysis)
└── intent_validation/ (Intent validation)

Resilience:
├── retry/           (Retry strategy)
├── resilience/      (Resilience patterns)
├── circuitbreaker/  (Circuit breaker)
├── cache/           (Caching)
├── batch/           (Batch operations)
└── ratelimit/       (Rate limiting)

Operations:
├── k8s/             (Cluster operations)
├── hunting/         (Threat hunting)
├── intel/           (Intelligence)
├── immune/          (Immune system)
├── offensive/       (Offensive security)
├── streams/         (Stream processing)
└── ... (15+ more operation modules)
```

---

## Command Categories

### Kubernetes (19 subcommands)
`k8s auth`, `k8s apply`, `k8s create`, `k8s delete`, `k8s logs`, etc.

### MAXIMUS Integration (49 KB cmd)
Consciousness, Governance, Eureka, Oraculo, Predict services

### Security Operations (90+ KB)
`immune`, `immunis`, `threat`, `offensive`, `investigate`, `hunting`, `intel`

### Data & Analytics (50+ KB)
`data`, `metrics`, `examples`, `sync`, `hitl`

### Advanced Features
`gateway`, `hcl`, `orchestrate`, `stream`, `ethical`, `troubleshoot`

### Emerging Operations
`behavior`, `architect`, `edge`, `homeostasis`, `integration`, `maba`, `nis`, `pipeline`, `purple`, `registry`, `rte`, `specialized`

---

## Architectural Highlights

### Strengths
1. **Modular Design**: 73 independent modules with clear responsibilities
2. **Extensibility**: Strategy pattern enables language/operation plugins
3. **Resilience**: Circuit breaker, retry, and rate limiting built-in
4. **Type Safety**: Structured error types with context
5. **Rich TUI**: Interactive shell with completion and status feedback
6. **Multi-Agent**: Autonomous development agents (AI-driven)
7. **Cloud-Native**: Kubernetes-first design
8. **Observable**: Prometheus metrics and distributed tracing

### Key Innovations
- **Agent Smith**: Multi-agent autonomous development framework
- **HITL Integration**: Human-in-the-loop decision making with MAXIMUS
- **Orchestration Engine**: Unified security operation coordination
- **Strategy Registry**: Language-agnostic code analysis/generation
- **Workspace Manager**: Pluggable workspace system

---

## Development Recommendations

### For Adding New Features
1. Create module in `internal/[feature-name]/`
2. Implement command in `cmd/[feature-name].go`
3. Register with root command in `cmd/root.go`
4. Follow established patterns (Strategy, Adapter, etc.)

### For Service Integration
1. Create client in `internal/[service]/client.go`
2. Use `gateway.GatewayClient` for HTTP
3. Implement error handling via `errors.VCLIError`
4. Add configuration in `config/types.go`

### For Adding Agent Strategies
1. Implement `strategies.AnalysisStrategy` interface
2. Register with `StrategyRegistry`
3. Create language package in `agents/[language]/`
4. Add to `cmd/agents.go` registration

---

## File Statistics

```
Total Files:        ~375 (internal + cmd)
Total Code:         ~21,000 lines (internal)
Largest Module:     maximus.go (49 KB)
Largest Internal:   k8s/handlers.go (34 KB)
Complexity:         Medium-High (distributed design)
Test Coverage:      Present (tests in place)
Documentation:      This map + inline comments
```

---

**See `docs/ARCHITECTURE_MAP.md` for comprehensive details**

**Document Generated**: 2025-11-14  
**Exploration Depth**: Medium-High  
**Coverage**: Complete project architecture
