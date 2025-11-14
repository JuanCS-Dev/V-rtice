# vCLI 2.0 Architecture Documentation Index

This directory contains comprehensive architecture documentation for the vCLI 2.0 project.

## Available Documents

### 1. ARCHITECTURE_MAP.md (1,268 lines, 40 KB)
**Comprehensive architecture reference guide**

The complete architecture map covering:
- Full directory structure (root, cmd, internal, api, pkg, plugins)
- All 73 internal modules in detail
- 60+ command implementations organized by category
- 10+ design patterns used throughout the codebase
- Complete dependency flow (external and internal)
- Detailed entry point analysis
- 7+ service integration points
- Module responsibilities matrix

**Best for**: Deep dives, comprehensive understanding, architectural decisions

**Key Sections**:
- [Project Overview](ARCHITECTURE_MAP.md#project-overview)
- [Directory Structure](ARCHITECTURE_MAP.md#directory-structure)
- [Core Modules](ARCHITECTURE_MAP.md#core-modules)
- [Design Patterns](ARCHITECTURE_MAP.md#design-patterns)
- [Dependency Flow](ARCHITECTURE_MAP.md#dependency-flow)
- [Entry Points](ARCHITECTURE_MAP.md#entry-points)
- [Service Integrations](ARCHITECTURE_MAP.md#service-integrations)

---

### 2. ARCHITECTURE_SUMMARY.md (329 lines, 12 KB)
**Quick overview and highlights**

A condensed summary including:
- Key metrics (315 files, 73 modules, 21,000+ LOC)
- High-level architecture diagram
- 8 core module breakdown
- 10 design patterns summary table
- Dependency architecture overview
- Module organization by responsibility
- Architectural highlights and key innovations
- Development recommendations

**Best for**: Getting oriented, team presentations, quick understanding

**Quick Links**:
- [High-Level Architecture](ARCHITECTURE_SUMMARY.md#high-level-architecture)
- [Core Module Breakdown](ARCHITECTURE_SUMMARY.md#core-module-breakdown)
- [Design Patterns Used](ARCHITECTURE_SUMMARY.md#design-patterns-used)
- [Architectural Highlights](ARCHITECTURE_SUMMARY.md#architectural-highlights)

---

### 3. ARCHITECTURE_QUICK_REF.md (This file + reference, 350 lines, 14 KB)
**Quick reference card for development**

Practical reference including:
- Project structure at a glance
- 10 key files to know
- 5-tier module organization
- Design patterns quick map
- Entry point flow diagram
- Command categories table
- Service integration points
- Adding new features checklist
- Naming conventions
- Key interfaces to implement
- Configuration & environment variables
- Quick command reference

**Best for**: Day-to-day development, onboarding, quick lookups

**Quick Links**:
- [Project Structure](ARCHITECTURE_QUICK_REF.md#project-structure-at-a-glance)
- [Core Modules Tiers](ARCHITECTURE_QUICK_REF.md#core-modules-at-a-glance)
- [Adding New Features](ARCHITECTURE_QUICK_REF.md#adding-new-features-checklist)
- [Quick Commands](ARCHITECTURE_QUICK_REF.md#quick-command-reference)

---

## Quick Navigation Guide

### Looking for...

**Understanding the overall architecture?**
- Start with: ARCHITECTURE_SUMMARY.md
- Deep dive: ARCHITECTURE_MAP.md

**Developing a new feature?**
- Start with: ARCHITECTURE_QUICK_REF.md
- Patterns: ARCHITECTURE_MAP.md → Design Patterns section
- Integration: ARCHITECTURE_MAP.md → Service Integrations section

**Onboarding a new team member?**
- Start with: ARCHITECTURE_SUMMARY.md
- Reference: ARCHITECTURE_QUICK_REF.md
- Advanced: ARCHITECTURE_MAP.md

**Understanding module dependencies?**
- ARCHITECTURE_MAP.md → Dependency Flow section
- ARCHITECTURE_QUICK_REF.md → Dependency Hierarchy

**Finding specific commands?**
- ARCHITECTURE_MAP.md → Directory Structure → cmd/
- ARCHITECTURE_QUICK_REF.md → Command Categories

**Implementing a new agent strategy?**
- ARCHITECTURE_MAP.md → Agent Systems section
- ARCHITECTURE_QUICK_REF.md → Agent Strategy checklist

**Integrating a new service?**
- ARCHITECTURE_MAP.md → Service Integrations section
- ARCHITECTURE_QUICK_REF.md → Service Integration checklist

---

## Project Statistics

```
Architecture Overview
├── Total Go Files: 375 (315 internal + 60 cmd)
├── Total Lines: 21,000+ (internal package)
├── Module Directories: 73 (internal)
├── Command Implementations: 60+ (cmd/)
├── Design Patterns: 10+
├── Service Integrations: 7+
├── External Dependencies: 37 direct, 80+ transitive
└── Go Version: 1.24.0+

Code Distribution
├── Agent Smith: 39 KB
├── MAXIMUS Integration: 49 KB
├── Kubernetes: 45 KB
├── Security Operations: 42 KB
├── Investigation: 50 KB
├── Data & Analytics: 50 KB
└── Infrastructure: 30 KB

Module Tiers
├── Tier 1 (Foundation): config, errors, gateway
├── Tier 2 (Infrastructure): shell, tui, k8s, maximus
├── Tier 3 (Business Logic): agents, orchestrator, nlp, security
├── Tier 4 (Resilience): retry, circuitbreaker, cache, ratelimit
└── Tier 5 (Operations): k8s, hunting, immune, offensive, streams
```

---

## Core Concepts

### Multi-Agent Framework (Agent Smith)
- 4 autonomous agents: Diagnosticador, Arquiteto, DevSenior, Tester
- Strategy pattern enables language-specific implementations
- Located in: `internal/agents/`

### Interactive Shell (REPL)
- Command completion with context awareness
- Bubble Tea-based rich TUI
- Located in: `internal/shell/`, `internal/tui/`

### Kubernetes Integration
- Unified interface for cluster operations
- 19 subcommands (apply, delete, logs, rollout, etc.)
- Located in: `internal/k8s/`

### MAXIMUS Integration
- AI consciousness and governance services
- 5 service clients (Consciousness, Governance, Eureka, Oraculo, Predict)
- Located in: `internal/maximus/`

### Orchestration Engine
- Coordinates complex security operations
- 4 operational domains: Defensive, Offensive, Monitoring, OSINT
- Located in: `internal/orchestrator/`

### Error Handling
- Structured error types with context
- Service-aware error categorization
- Retryability metadata
- Located in: `internal/errors/`

### Configuration System
- Singleton pattern with lazy loading
- YAML, environment, and runtime overrides
- Located in: `internal/config/`

### NLP Pipeline
- Intent recognition and entity extraction
- 7 processing stages (tokenize, validate, classify, etc.)
- Located in: `internal/nlp/`

---

## Development Workflows

### Adding a New Command
1. Create `cmd/[feature].go`
2. Implement command handler
3. Register in `cmd/root.go`
4. Add subcommands if needed
5. Reference: ARCHITECTURE_QUICK_REF.md → New Command checklist

### Adding a New Module
1. Create `internal/[feature]/` directory
2. Implement core logic following patterns
3. Export public interfaces
4. Add tests alongside code
5. Reference: ARCHITECTURE_QUICK_REF.md → New Module checklist

### Adding Agent Support for New Language
1. Implement `strategies.AnalysisStrategy`
2. Implement `strategies.CodeGenStrategy`
3. Register with `StrategyRegistry`
4. Create `agents/[language]/` package
5. Reference: ARCHITECTURE_QUICK_REF.md → Agent Strategy checklist

### Integrating a New Service
1. Create `internal/[service]/client.go`
2. Use `gateway.GatewayClient` for HTTP APIs
3. Implement `errors.VCLIError` error handling
4. Add configuration in `config/types.go`
5. Reference: ARCHITECTURE_QUICK_REF.md → Service Integration checklist

---

## Key Design Patterns

| Pattern | Purpose | Examples | Docs |
|---------|---------|----------|------|
| **Strategy** | Pluggable behaviors | Language-specific code analysis | MAP § Design Patterns |
| **Command** | CLI operations | Cobra command tree | MAP § Design Patterns |
| **Adapter** | Service integration | K8s, MAXIMUS, Gateway clients | MAP § Adapter Pattern |
| **Factory** | Object creation | Agent instantiation | MAP § Factory Pattern |
| **Observer** | Event handling | Agent workflows, TUI updates | MAP § Observer Pattern |
| **Singleton** | Global state | Configuration, service clients | MAP § Singleton Pattern |
| **Registry** | Plugin management | Agent/strategy registration | MAP § Registry Pattern |
| **Pipeline** | Data processing | NLP stages | MAP § Pipeline Pattern |
| **Circuit Breaker** | Fault tolerance | Service reliability | QUICK_REF § Tier 4 |
| **Retry with Backoff** | Resilience | Automatic request retry | QUICK_REF § Tier 4 |

---

## File Location Reference

### Critical Files
- `main.go` - Application entry point
- `cmd/root.go` - Command registration and initialization
- `internal/config/config.go` - Configuration system (singleton)
- `internal/errors/types.go` - Error type definitions
- `internal/shell/completer.go` - Command completion engine

### Framework Files
- `internal/agents/orchestrator.go` - Agent coordination
- `internal/shell/executor.go` - Command execution
- `internal/shell/bubbletea/model.go` - TUI state
- `internal/k8s/handlers.go` - Kubernetes operations
- `internal/maximus/consciousness_client.go` - AI service

### System Files
- `internal/gateway/client.go` - Generic HTTP client
- `internal/orchestrator/engine.go` - Operation coordination
- `internal/nlp/orchestrator.go` - NLP pipeline
- `api/proto/` - Protocol buffer definitions
- `internal/security/` - Auth/audit/behavioral modules

---

## Command Quick Reference

### Infrastructure
```bash
vcli version              # Version info
vcli tui                  # Launch TUI
vcli --help               # Show all commands
```

### Agent Smith
```bash
vcli agents list          # List available agents
vcli agents run [agent]   # Run specific agent
vcli agents status        # Get agent status
```

### Kubernetes
```bash
vcli k8s auth             # Configure authentication
vcli k8s apply -f file    # Apply manifest
vcli k8s logs [pod]       # View pod logs
vcli k8s delete [resource]# Delete resource
```

### MAXIMUS
```bash
vcli maximus consciousness [cmd]   # Consciousness operations
vcli maximus governance [cmd]      # Governance operations
```

### Configuration
```bash
vcli config list          # List configuration
vcli config set [key] [value]     # Set value
```

---

## Testing & Build

### Testing
```bash
make test                 # Run all tests
go test ./internal/...    # Test internal packages
go test ./cmd/...         # Test commands
```

### Building
```bash
make build                # Build binary
docker build -t vcli .    # Build Docker image
go install ./...          # Install locally
```

---

## Additional Resources

### Documentation
- Main README: `../../README.md`
- Installation: `../../INSTALL.md`
- Contributing: `.github/CONTRIBUTING.md` (if available)

### Configuration
- Example: `internal/config/config.yaml.example`
- Defaults: `internal/config/types.go`

### Examples
- NLP Simple: `examples/nlp-simple/main.go`
- NLP Shell: `examples/nlp-shell/main.go`

### Kubernetes
- Manifests: `k8s/`
- Configurations: `internal/k8s/*.go`

---

## Document Maintenance

These documents were generated through comprehensive code exploration on 2025-11-14.

### Coverage
- Directory structure: Complete
- Module responsibilities: 73/73 modules
- Design patterns: 10+ patterns documented
- Command implementations: 60+ commands
- Service integrations: 7+ services
- Entry points: All documented

### Update Frequency
- Update when major architectural changes occur
- Update when new modules are added
- Update when design patterns change
- Update when service integrations are modified

### How to Use These Docs
1. **ARCHITECTURE_SUMMARY.md** for meetings and presentations
2. **ARCHITECTURE_MAP.md** for design decisions and deep dives
3. **ARCHITECTURE_QUICK_REF.md** for daily development

---

**Last Generated**: 2025-11-14  
**Exploration Depth**: Medium-High  
**Status**: Complete and ready for use
