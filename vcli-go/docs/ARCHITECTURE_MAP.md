# vCLI 2.0 Architecture Map

**Document Status**: Comprehensive Architecture Overview  
**Project**: vCLI 2.0 - High-performance Cybersecurity Operations CLI  
**Build Version**: 2.0.0 (2025-10-07)  
**Author**: Architecture Analysis & Documentation

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Directory Structure](#directory-structure)
3. [Core Modules](#core-modules)
4. [Design Patterns](#design-patterns)
5. [Dependency Flow](#dependency-flow)
6. [Entry Points](#entry-points)
7. [Service Integrations](#service-integrations)
8. [Module Responsibilities](#module-responsibilities)

---

## Project Overview

vCLI 2.0 is a high-performance Go implementation of the Vértice CLI, providing an interactive Terminal User Interface (TUI) for cybersecurity operations. Built on the Cobra command framework and Bubble Tea TUI library, it implements a sophisticated multi-layered architecture supporting:

- **Ethical AI Governance** (HITL - Human-in-the-Loop decision making)
- **Autonomous Investigation** (Multi-agent systems)
- **Situational Awareness** (Real-time monitoring)
- **Kubernetes Integration** (Cluster management)
- **Advanced Security Operations** (Threat hunting, incident response)

**Key Metrics**:
- Go Version: 1.24.0+
- Code Files: 315 internal modules, 60+ command implementations
- Lines of Code: ~21,000+ in internal package
- External Dependencies: 37 direct, 80+ transitive

---

## Directory Structure

### Root Level Organization

```
/home/juan/vertice-dev/vcli-go/
├── main.go                    # Entry point - delegates to cmd.Execute()
├── go.mod / go.sum            # Dependency management
├── Makefile                   # Build automation
├── Dockerfile                 # Container configuration
├── cmd/                       # Command implementations
├── internal/                  # Core application packages
├── api/                       # Protocol buffers & gRPC definitions
├── pkg/                       # Public API packages
├── plugins/                   # Plugin system
├── k8s/                       # Kubernetes manifests
├── examples/                  # Demo applications
├── docs/                      # Documentation
└── test/                      # Test fixtures & utilities
```

### **cmd/** - Command Package Structure

**Purpose**: Implements CLI commands following Cobra framework patterns  
**Files**: 60+ command implementations  
**Total Lines**: ~21,000

#### Command Categories:

**Core Infrastructure**
```
├── root.go                    # Root command initialization & global flags
├── version.go                 # Version information
├── config.go                  # Configuration management
```

**Agent Smith Framework**
```
├── agents.go                  # Multi-agent orchestration (39KB)
└── implements: diagnosticador, arquiteto, dev_senior, tester
```

**Kubernetes Management** (19 subcommands)
```
├── k8s.go                     # Main k8s command (14KB)
├── k8s_auth.go                # Authentication
├── k8s_apply.go               # Resource deployment
├── k8s_create.go              # Resource creation
├── k8s_create_configmap.go    # ConfigMap management
├── k8s_create_secret.go       # Secret management (17KB)
├── k8s_delete.go              # Resource deletion
├── k8s_describe.go            # Resource information
├── k8s_exec.go                # Pod execution
├── k8s_label.go               # Labeling
├── k8s_patch.go               # Patching
├── k8s_logs.go                # Log retrieval
├── k8s_rollout.go             # Deployment rollout
├── k8s_scale.go               # Pod scaling
├── k8s_port_forward.go        # Port forwarding
├── k8s_watch.go               # Resource watching
├── k8s_top.go                 # Resource metrics
├── k8s_wait.go                # Condition waiting
└── k8s_test.go                # Testing utilities
```

**MAXIMUS Integration**
```
├── maximus.go                 # AI consciousness & governance (49KB)
├── Endpoints: consciousness, governance, eureka, oraculo, predict
└── Implements: Decision-making, pattern recognition, predictions
```

**Cybersecurity Operations**
```
├── immune.go                  # Immune system operations (23KB)
├── immunis.go                 # Advanced immunology (19KB)
├── threat.go                  # Threat assessment (149 lines)
├── offensive.go               # Offensive security operations (15KB)
├── investigate.go             # Investigation framework (19KB)
├── hunting.go                 # Threat hunting (14KB)
├── intel.go                   # Intelligence gathering (17KB)
├── neuro.go                   # Neuro-immune integration (16KB)
├── vulnerable.go              # Vulnerability scanning
└── vulnscan.go                # Vulnerability assessment (133 lines)
```

**Data & Analytics**
```
├── data.go                    # Data processing (16KB)
├── metrics.go                 # Metrics collection (13KB)
├── examples.go                # Example commands (12KB)
├── sync.go                    # Data synchronization (387 lines)
└── hitl.go                    # Human-in-the-loop (18KB)
```

**Advanced Features**
```
├── gateway.go                 # API Gateway operations (12KB)
├── hcl.go                     # HCL configuration (7KB)
├── orchestrate.go             # Orchestration (unspecified)
├── stream.go                  # Stream processing
├── ethical.go                 # Ethical AI governance (8KB)
└── troubleshoot.go            # Diagnostics (298 lines)
```

**Emerging Command Categories**
```
├── behavior.go                # Behavioral analysis
├── config.go                  # Configuration management
├── architect.go               # Architecture design
├── edge.go                    # Edge computing
├── homeostasis.go             # System homeostasis
├── integration.go             # System integration
├── maba.go                    # MABA module
├── nis.go                     # NIS module
├── pipeline.go                # Pipeline management
├── purple.go                  # Purple team operations
├── registry.go                # Registry management
├── rte.go                     # Runtime execution
└── specialized.go             # Specialized operations
```

---

### **internal/** - Core Modules

**Purpose**: Package private implementation of all business logic  
**Structure**: 73 directories, 315 Go source files  
**Organization**: Feature-based with shared utilities

#### Module Categories:

**1. Agent Systems** (`internal/agents/`)
```
├── orchestrator.go            # Multi-agent workflow coordinator
├── planning.go                # Task planning system
├── reflection.go              # Self-reflection mechanism
├── self_healing.go            # Auto-recovery system
├── types.go                   # Agent type definitions (11KB)
├── strategies/                # Language-specific strategies
│   ├── strategy.go            # Strategy pattern interfaces
│   ├── go_analysis.go         # Go code analysis
│   ├── go_codegen.go          # Go code generation
│   ├── python_analysis.go     # Python analysis
│   ├── python_codegen.go      # Python generation
│   └── python_testing.go      # Python test execution
├── arquiteto/                 # Architecture agent
├── dev_senior/                # Senior developer agent
├── diagnosticador/            # Diagnostic agent
├── tester/                    # Testing agent
├── language/                  # Language detection
├── utils/                     # Agent utilities
├── workflow/                  # Workflow management
├── oraculo/                   # Prediction service client
└── runtime/                   # Agent runtime environment
```

**Design Pattern**: Strategy Pattern + Factory Pattern
- Extensible language support (Go, Python)
- Pluggable analysis/codegen strategies
- Registry-based strategy lookup

**2. Shell & Interactive Interface** (`internal/shell/`)
```
├── shell.go                   # Main shell interface (3KB)
├── executor.go                # Command executor (12KB)
├── completer.go               # Command completion (30KB)
└── bubbletea/                 # TUI implementation
    ├── shell.go               # BubbleTea shell
    ├── model.go               # State management (12KB)
    ├── update.go              # Event handling (19KB)
    ├── view.go                # Rendering (13KB)
    ├── messages.go            # Message types
    └── statusline.go          # Status display
```

**Design Pattern**: Model-View-Update (MVC) for TUI
- Reactive event-driven architecture
- Comprehensive command completion with context
- Real-time status updates

**3. Configuration System** (`internal/config/`)
```
├── config.go                  # Singleton config manager (2KB)
├── loader.go                  # YAML/ENV loader (5KB)
├── types.go                   # Configuration types (3KB)
└── config.yaml.example        # Configuration template
```

**Design Pattern**: Singleton with Lazy Loading
- Thread-safe global configuration
- Environment variable & file overrides
- Service endpoint management

**4. Kubernetes Integration** (`internal/k8s/`)
```
├── handlers.go                # Command handlers (34KB)
├── operations.go              # K8s operations
├── kubeconfig.go              # Kubeconfig management (5KB)
├── auth.go                    # Authentication (6KB)
├── apply.go                   # Resource application (12KB)
├── delete.go                  # Resource deletion (11KB)
├── describe.go                # Resource description (8KB)
├── logs.go                    # Log retrieval (6KB)
├── label_annotate.go          # Metadata management (6KB)
├── exec.go                    # Pod execution (5KB)
├── formatters.go              # Output formatting (21KB)
├── cluster_manager.go         # Cluster operations (4KB)
├── yaml_parser.go             # YAML parsing
├── utils.go                   # Utilities
└── mutation_models_test.go    # Testing utilities
```

**Design Pattern**: Adapter Pattern
- Wraps Kubernetes client-go library
- Provides consistent CLI interface
- Extensible output formatters

**5. MAXIMUS Integration** (`internal/maximus/`)
```
├── types.go                   # Protocol types (Consciousness Architecture)
├── consciousness_client.go    # Consciousness service client
├── governance_client.go       # Governance decision service
├── eureka_client.go           # Eureka discovery service
├── oraculo_client.go          # Prediction service
├── predict_client.go          # ML prediction client
├── formatters.go              # Response formatting
```

**Design Pattern**: Service Adapter Pattern
- Wraps REST API endpoints
- Manages authentication (JWT)
- Provides high-level abstractions

**6. Orchestration Engine** (`internal/orchestrator/`)
```
├── engine.go                  # Main orchestration engine (16KB)
├── types.go                   # Orchestration types (6KB)
├── defensive/                 # Defensive operations
│   ├── threat_hunting.go      # Threat hunting strategies
│   └── threat_response.go     # Incident response
├── offensive/                 # Offensive operations
│   ├── apt_simulation.go      # APT simulations
│   └── target_assessment.go   # Target evaluation
├── monitoring/                # Monitoring operations
│   ├── anomaly_response.go    # Anomaly detection
│   └── security_posture.go    # Security metrics
└── osint/                     # OSINT operations
    ├── deep_investigation.go  # Investigation workflows
    └── actor_profiling.go     # Threat actor profiling
```

**Design Pattern**: Strategy + Observer Pattern
- Pluggable operation strategies
- Event-driven monitoring
- Multi-phase incident response

**7. Error Handling** (`internal/errors/`)
```
├── types.go                   # VCLIError structure
├── builders.go                # Error construction helpers
├── suggestions.go             # Error suggestions/remediation
└── user_friendly.go           # User-facing error messages
```

**Design Pattern**: Builder Pattern + Chain of Responsibility
- Structured error types with context
- Service-aware error categorization
- Retryability metadata

**8. API Gateway Client** (`internal/gateway/`)
```
└── client.go                  # Generic REST client (90+ KB)
```

**Design Pattern**: Adapter Pattern
- Provides unified API for backend services
- Handles authentication and error translation
- Connection pooling and timeouts

**9. Shell/Command Infrastructure** (`internal/shell/`)
```
└── completer.go               # Advanced command completion
```

**Design Pattern**: Trie-based Suggestion Engine
- Context-aware suggestions
- Description support
- Fuzzy matching capabilities

**10. Workspace Management** (`internal/workspace/` & `internal/workspaces/`)
```
├── workspace/
│   ├── manager.go             # Workspace lifecycle
│   ├── governance/            # Governance workspace
│   ├── investigation/         # Investigation workspace
│   └── situational/           # Situational awareness workspace
└── workspaces/
    ├── governance/            # Advanced governance
    └── performance/           # Performance monitoring
```

**Design Pattern**: Strategy + Composite Pattern
- Multiple specialized workspaces
- Plugin-based workspace extensions
- State isolation per workspace

**11. TUI Components** (`internal/tui/`)
```
├── model.go                   # Main TUI model (12KB)
├── update.go                  # Event handling (19KB)
├── view.go                    # Rendering logic (13KB)
├── messages.go                # Message types
├── plugin_integration.go      # Plugin support (6KB)
└── widgets/                   # Custom widgets
```

**Design Pattern**: Bubble Tea Pattern + Composite
- Event-driven update loop
- Immutable state management
- Pluggable widget system

**12. NLP & Intent Recognition** (`internal/nlp/`)
```
├── orchestrator.go            # NLP orchestrator
├── tokenizer/                 # Text tokenization
├── validator/                 # Input validation
├── context/                   # Contextual analysis
├── learning/                  # Machine learning integration
├── intent/                    # Intent classification
├── entities/                  # Named entity recognition
├── generator/                 # Response generation
└── [tests]
```

**Design Pattern**: Pipeline Pattern
- Modular NLP pipeline stages
- Context management
- Intent-based command routing

**13. Security & Authorization** (`internal/security/`)
```
├── auth/                      # Authentication
├── audit/                      # Audit logging
├── behavioral/                # Behavioral analysis
├── intent_validation/         # Intent validation
└── [other security modules]
```

**14. Resilience Patterns** (`internal/`)
```
├── retry/                     # Retry strategy with backoff
├── resilience/                # Resilience patterns
├── circuitbreaker/            # Circuit breaker pattern
├── cache/                     # Caching mechanisms
├── batch/                     # Batch operations
└── ratelimit/                 # Rate limiting
```

**Design Patterns**: Bulkhead, Circuit Breaker, Retry
- Configurable retry policies
- Graceful degradation
- Resource isolation

**15. Additional Modules**
```
├── auth/                      # Authentication management
├── authz/                     # Authorization rules
├── audit/                     # Audit trail
├── governance/                # Governance policies
├── behavioral/                # Behavioral analysis
├── hunting/                   # Threat hunting
├── intel/                     # Intelligence gathering
├── immunity/                  # Immune system
├── immune/                    # Immune operations
├── maba/                      # MABA service integration
├── nis/                       # NIS service integration
├── neuro/                     # Neuro-immune integration
├── offensive/                 # Offensive security
├── purple/                    # Purple team operations
├── rte/                       # Runtime execution
├── streams/                   # Stream processing
├── vulnscan/                  # Vulnerability scanning
├── pipeline/                  # Pipeline orchestration
├── registry/                  # Registry management
├── edge/                      # Edge computing
├── homeostasis/               # System homeostasis
├── integration/               # System integration
├── architect/                 # Architecture AI
├── behavior/                  # Behavior analysis
├── dashboard/                 # Dashboard components
├── data/                      # Data processing
├── ethical/                   # Ethical AI
├── gateway/                   # Gateway management
├── grpc/                      # gRPC utilities
├── help/                      # Help system
├── hitl/                      # HITL framework
├── hcl/                       # HCL parsing
├── investigation/             # Investigation tools
├── narrative/                 # Narrative generation
├── observability/             # Observability metrics
├── offline/                   # Offline mode
├── osint/                     # OSINT operations
├── palette/                   # Color/styling
├── plugins/                   # Plugin system
├── sandbox/                   # Sandboxing
├── suggestions/               # Suggestion engine
├── threat/                    # Threat assessment
├── triage/                    # Issue triage
├── visual/                    # Visual components & banner
└── workspace/                 # Workspace management
```

---

### **api/** - Protocol Definitions

```
api/
├── grpc/                      # Compiled gRPC services
│   ├── maximus/
│   │   ├── maximus.pb.go      # Protocol buffer definitions
│   │   └── maximus_grpc.pb.go # gRPC service stubs
│   ├── governance/            # Governance service protos
│   ├── immune/                # Immune system protos
│   └── kafka/                 # Kafka integration protos
└── proto/                     # Source protocol files
    ├── governance.proto       # Governance service definition
    ├── maximus/               # MAXIMUS service definitions
    ├── immune/                # Immune service definitions
    └── kafka/                 # Kafka service definitions
```

**Technology**: Protocol Buffers v3, gRPC 1.76.0

---

### **pkg/** - Public Packages

```
pkg/
├── nlp/                       # NLP public API
│   └── [NLP utilities]
└── security/                  # Security public API
    └── [Security utilities]
```

**Purpose**: Re-exportable packages for external consumers

---

### **plugins/** - Plugin System

```
plugins/
├── kubernetes/
│   └── kubernetes.go          # K8s plugin implementation
└── [Other plugins]
```

**Design Pattern**: Plugin Pattern (Registry-based)

---

### **examples/** - Reference Implementations

```
examples/
├── nlp-simple/
│   └── main.go                # Simple NLP example
└── nlp-shell/
    └── main.go                # Interactive NLP shell
```

---

## Core Modules

### 1. **Agent Smith Framework** (Autonomous Development)

**Location**: `internal/agents/`  
**Responsibility**: Multi-agent autonomous development system

**Architecture**:
```
AgentOrchestrator
├── Diagnosticador Agent    (Analysis & Scanning)
├── Arquiteto Agent         (Architecture Planning)
├── DevSenior Agent         (Code Implementation)
└── Tester Agent            (Validation & QA)
```

**Key Components**:
- `Agent` interface for extensibility
- `StrategyRegistry` for language-specific implementations
- `AgentOrchestrator` for workflow coordination
- Support for Go & Python via pluggable strategies

**Patterns**:
- Strategy Pattern (language-specific analysis/codegen)
- Factory Pattern (agent instantiation)
- Observer Pattern (workflow events)

---

### 2. **Interactive Shell** (User Interface)

**Location**: `internal/shell/`  
**Responsibility**: Command-line interaction and command execution

**Architecture**:
```
Shell
├── Executor      (Command execution via cobra)
├── Completer     (Advanced completion engine)
└── BubbleTea TUI (Rich terminal interface)
    ├── Model     (State management)
    ├── Update    (Event loop)
    └── View      (Rendering)
```

**Features**:
- REPL-style interactive shell
- Context-aware command completion
- Real-time status feedback
- History management
- Mouse support

---

### 3. **Kubernetes Integration** (Cluster Management)

**Location**: `internal/k8s/`  
**Responsibility**: Unified Kubernetes operations interface

**Architecture**:
```
K8s Module
├── Client     (K8s API wrapper)
├── Handlers   (Operation implementations)
├── Formatters (Output formatting)
└── Auth       (Authentication management)
```

**Supported Operations**:
- Cluster authentication & management
- Resource CRUD operations
- Pod execution & logs
- Deployment rollout management
- Label/annotation manipulation
- Resource metrics & monitoring

---

### 4. **MAXIMUS Integration** (AI Consciousness)

**Location**: `internal/maximus/`  
**Responsibility**: Integration with MAXIMUS AI services

**Architecture**:
```
MaximusClients
├── ConsciousnessClient     (Self-awareness, decision-making)
├── GovernanceClient        (Ethical governance, HITL)
├── EurekaClient            (Service discovery)
├── OraculoClient           (Pattern recognition)
└── PredictClient           (ML predictions)
```

**Protocol**: REST API with JWT authentication

---

### 5. **Orchestration Engine** (Operation Coordination)

**Location**: `internal/orchestrator/`  
**Responsibility**: Coordinate complex security operations

**Architecture**:
```
OrchestrationEngine
├── DefensiveOps    (Threat hunting, incident response)
├── OffensiveOps    (Red team exercises, APT simulation)
├── MonitoringOps   (Anomaly detection, posture)
└── OSINTOps        (Intelligence gathering, profiling)
```

---

### 6. **Configuration Management** (Settings & Endpoints)

**Location**: `internal/config/`  
**Responsibility**: Centralized configuration with environment overrides

**Features**:
- YAML-based configuration
- Environment variable overrides
- Runtime endpoint configuration
- Service discovery integration

---

### 7. **Error Handling** (Structured Errors)

**Location**: `internal/errors/`  
**Responsibility**: Structured, context-aware error management

**Features**:
- Error type classification
- Service context tracking
- Retryability metadata
- User-friendly messages
- Error suggestions

---

## Design Patterns

### 1. **Strategy Pattern** (Pluggable Behaviors)

**Usage**: Language-specific code analysis and generation

```
AnalysisStrategy
├── GoAnalysisStrategy      (Go code analysis)
└── PythonAnalysisStrategy  (Python code analysis)

TestStrategy
├── GoTestStrategy          (Go testing)
└── PythonTestStrategy      (Python testing)

CodeGenStrategy
├── GoCodeGenStrategy       (Go code generation)
└── PythonCodeGenStrategy   (Python generation)
```

**Location**: `internal/agents/strategies/`  
**Registry**: `StrategyRegistry` in same location

---

### 2. **Command Pattern** (CLI Operations)

**Usage**: Command-based CLI architecture

```
Cobra Command Tree
├── Root Command (vcli)
├── SubCommands (agents, k8s, maximus, etc.)
└── SubSubCommands (k8s apply, k8s delete, etc.)
```

**Location**: `cmd/` package  
**Framework**: Spf13/Cobra

---

### 3. **Adapter Pattern** (Service Integration)

**Usage**: Wrapping external service APIs

```
Adapters
├── K8sAdapter          (wraps k8s client-go)
├── MaximusAdapter      (wraps REST API)
└── GatewayAdapter      (generic REST client)
```

**Benefit**: Consistent interface regardless of backend

---

### 4. **Factory Pattern** (Object Creation)

**Usage**: Agent instantiation

```
AgentFactory
├── CreateDiagnosticador()
├── CreateArquiteto()
├── CreateDevSenior()
└── CreateTester()
```

**Location**: `internal/agents/orchestrator.go`

---

### 5. **Observer Pattern** (Event Handling)

**Usage**: Agent workflow events and TUI updates

```
EventEmitter
├── OnWorkflowStart
├── OnStepComplete
├── OnError
└── OnCompletion
```

**Location**: Multiple - agents, shell, TUI

---

### 6. **Singleton Pattern** (Global State)

**Usage**: Configuration and global clients

```
Singletons
├── config.Get()        (Global configuration)
└── MaximusClients      (Shared service clients)
```

**Location**: `internal/config/config.go`  
**Thread Safety**: RWMutex-protected

---

### 7. **Registry Pattern** (Plugin Management)

**Usage**: Agent registration and strategy lookup

```
Registries
├── StrategyRegistry    (language strategies)
├── AgentRegistry       (available agents)
└── PluginRegistry      (external plugins)
```

---

### 8. **Pipeline Pattern** (Data Processing)

**Usage**: NLP processing stages

```
NLPPipeline
├── Tokenizer
├── Validator
├── ContextAnalyzer
├── IntentClassifier
├── EntityRecognizer
└── ResponseGenerator
```

**Location**: `internal/nlp/`

---

### 9. **Circuit Breaker Pattern** (Resilience)

**Location**: `internal/circuitbreaker/`  
**Purpose**: Prevent cascading failures

---

### 10. **Retry with Backoff Pattern** (Resilience)

**Location**: `internal/retry/`  
**Purpose**: Automatic request retry with exponential backoff

---

## Dependency Flow

### External Dependencies (Top-Level)

```
├── CLI Framework
│   └── github.com/spf13/cobra v1.9.1
│       └── github.com/spf13/pflag v1.0.6
│
├── TUI Components
│   ├── github.com/charmbracelet/bubbletea v1.3.4
│   ├── github.com/charmbracelet/bubbles v0.21.0
│   └── github.com/charmbracelet/lipgloss v1.1.0
│
├── Cloud & Infrastructure
│   ├── k8s.io/client-go v0.31.0
│   ├── k8s.io/api v0.31.0
│   └── k8s.io/metrics v0.31.0
│
├── Communication & Messaging
│   ├── google.golang.org/grpc v1.76.0
│   ├── google.golang.org/protobuf v1.36.10
│   └── github.com/gorilla/websocket v1.5.3
│
├── Data & Caching
│   ├── github.com/redis/go-redis/v9 v9.14.1
│   ├── github.com/dgraph-io/badger/v3 v3.2103.5
│   └── github.com/dgraph-io/badger/v4 v4.8.0
│
├── Observability
│   ├── github.com/prometheus/client_golang v1.23.2
│   └── go.opentelemetry.io/* (telemetry stack)
│
├── Security & Crypto
│   ├── github.com/golang-jwt/jwt/v5 v5.3.0
│   └── github.com/pquerna/otp v1.5.0
│
├── Utilities
│   ├── github.com/google/uuid v1.6.0
│   ├── github.com/fatih/color v1.18.0
│   ├── github.com/agnivade/levenshtein v1.2.1
│   └── gopkg.in/yaml.v3 v3.0.1
│
├── Shell & Terminal
│   ├── github.com/c-bata/go-prompt v0.2.6
│   ├── github.com/mattn/go-isatty v0.0.20
│   └── golang.org/x/term v0.34.0
│
└── Testing
    └── github.com/stretchr/testify v1.11.1
```

### Internal Dependency Hierarchy

```
cmd/
├── root.go
│   └── internal/shell         (Shell interface)
│   └── internal/workspace     (Workspace manager)
│   └── internal/visual        (UI components)
│
├── agents.go
│   └── internal/agents        (Agent framework)
│       └── internal/agents/strategies (Language strategies)
│       └── internal/maximus   (MAXIMUS client)
│
├── k8s_*.go
│   └── internal/k8s           (K8s operations)
│       └── k8s.io/client-go   (K8s API)
│
├── maximus.go
│   └── internal/maximus       (MAXIMUS clients)
│       └── internal/gateway   (Gateway client)
│
└── [other commands]
    └── internal/[corresponding modules]
    └── internal/config        (Configuration)
    └── internal/errors        (Error handling)
    └── internal/visual        (UI rendering)

internal/
├── agents/
│   ├── orchestrator.go
│   ├── planning.go
│   ├── reflection.go
│   └── types.go
│   └── strategies/            (Plugin registry)
│       ├── strategy.go        (Interface definitions)
│       ├── go_analysis.go
│       └── python_analysis.go
│
├── shell/
│   ├── executor.go
│   ├── completer.go
│   └── bubbletea/
│       ├── model.go
│       └── update.go
│
├── k8s/
│   ├── handlers.go
│   ├── operations.go
│   └── client-go wrappers
│
├── maximus/
│   ├── consciousness_client.go
│   ├── governance_client.go
│   └── gateway/
│       └── client.go
│
├── config/
│   ├── config.go              (Singleton)
│   └── loader.go
│
└── errors/
    ├── types.go
    └── builders.go
```

### Service Integration Points

```
vCLI
├── MAXIMUS Backend
│   ├── Consciousness Service (consciousness.maximus.local:8001)
│   ├── Governance Service    (governance.maximus.local:8001)
│   ├── Eureka Service        (discovery)
│   ├── Oraculo Service       (pattern recognition)
│   └── Predict Service       (predictions)
│
├── Kubernetes Cluster
│   ├── K8s API Server        (configured via kubeconfig)
│   └── kubelet nodes
│
├── Data Services (Optional)
│   ├── Redis                 (caching)
│   └── Badger DB             (local persistence)
│
└── Monitoring/Telemetry
    ├── Prometheus            (metrics)
    └── OpenTelemetry         (distributed tracing)
```

---

## Entry Points

### 1. **Application Entry Point** (`main.go`)

```go
package main

func main() {
    cmd.Execute()  // Delegates to Cobra root command
}
```

**Flow**:
1. Go runtime starts program
2. `main()` executes
3. `cmd.Execute()` initializes Cobra command tree
4. Command routing or interactive shell launches

### 2. **Root Command Initialization** (`cmd/root.go`)

**Key Structures**:

```go
var rootCmd = &cobra.Command{
    Use:   "vcli",
    Short: "vCLI 2.0 - High-performance cybersecurity operations CLI",
    Run: func(cmd *cobra.Command, args []string) {
        // Check if running in interactive terminal
        if isTerminal(os.Stdin) {
            sh := shell.NewShell(cmd.Root(), version, buildDate)
            sh.Run()  // Launch interactive shell
        } else {
            cmd.Help()
        }
    },
}
```

**Initialization Order** (via `init()` in root.go):
1. `cobra.OnInitialize(initConfig)` - Config system setup
2. `rootCmd.PersistentFlags()` - Global flags registration:
   - `--debug` - Debug mode
   - `--config` - Config file path
   - `--offline` - Offline mode
   - `--no-telemetry` - Telemetry control
   - `--backend` - Backend type (http/grpc)
3. `rootCmd.AddCommand()` - Register all subcommands
4. Workspace subcommand setup
5. Offline mode subcommand setup

### 3. **Command Registration**

**Root-Level Commands Added**:
```go
rootCmd.AddCommand(tuiCmd)          // TUI launcher
rootCmd.AddCommand(versionCmd)      // Version info
rootCmd.AddCommand(workspaceCmd)    // Workspace management
rootCmd.AddCommand(offlineCmd)      // Offline mode
rootCmd.AddCommand(offensiveCmd)    // Offensive ops
rootCmd.AddCommand(streamsCmd)      // Stream processing
rootCmd.AddCommand(specializedCmd)  // Specialized ops
rootCmd.AddCommand(configCmd)       // Configuration
rootCmd.AddCommand(architectCmd)    // Architecture AI
rootCmd.AddCommand(behaviorCmd)     // Behavior analysis
// ... more commands
```

**Subcommand Hierarchy Example**:
```
vcli k8s
├── vcli k8s auth
├── vcli k8s apply
├── vcli k8s create
│   ├── vcli k8s create configmap
│   └── vcli k8s create secret
├── vcli k8s delete
├── vcli k8s logs
└── vcli k8s rollout
```

### 4. **Interactive Shell Path**

**Flow**:
```
main() 
  → cmd.Execute()
    → rootCmd.Run()
      → NewShell(rootCmd, version, buildDate)
        → shell.executor = NewExecutor(rootCmd)
        → shell.completer = NewCompleter(rootCmd)
        → shell.Run()
          → prompt.New() [start REPL loop]
            → s.execute() [on input]
            → s.complete() [for suggestions]
```

### 5. **Command Execution Path**

**When user types command**:
```
Input: "agents run diagnosticador --targets ./internal/"
  → Completer provides suggestions
  → Executor parses input
  → Cobra routes to agentsCmd
    → runAgents() handler executes
      → agents.NewOrchestrator()
      → orchestrator.Execute()
        → diagnosticador.Analyze()
        → Results output
```

### 6. **Config Initialization**

**Called by**: `cobra.OnInitialize(initConfig)`

```go
func initConfig() {
    // Determine config path
    configPath := configFile
    if configPath == "" {
        configPath = filepath.Join(home, ".vcli", "config.yaml")
    }
    
    // Config loads lazily on first use via config.Get()
}
```

**Config Loading**:
- YAML file: `~/.vcli/config.yaml` (default)
- Environment: Overrides YAML values
- Flags: Overrides everything else

---

## Service Integrations

### 1. **MAXIMUS Consciousness Service**

**Purpose**: AI consciousness and decision-making  
**Protocol**: REST with JWT  
**Location**: `internal/maximus/consciousness_client.go`

```go
type ConsciousnessClient struct {
    BaseURL string
    Token   string
}

// Methods:
Ping() error
GetArousalLevel() (ArousalLevel, error)
GetConsciousness() (*ConsciousnessState, error)
GetSituationalAwareness() (*SituationalAwareness, error)
```

### 2. **MAXIMUS Governance Service**

**Purpose**: Ethical AI governance and HITL decisions  
**Protocol**: REST with JWT  
**Location**: `internal/maximus/governance_client.go`

```go
type GovernanceClient struct {
    BaseURL string
    Token   string
}

// Methods:
CreateDecision(input *DecisionInput) (*Decision, error)
ListDecisions(filter *DecisionFilter) ([]Decision, error)
GetDecision(id string) (*Decision, error)
UpdateDecision(id string, update *DecisionUpdate) (*Decision, error)
ApproveDecision(id string) error
```

### 3. **Kubernetes API**

**Purpose**: Cluster management and operations  
**Client Library**: `k8s.io/client-go`  
**Location**: `internal/k8s/`

```go
type K8sClient struct {
    clientset kubernetes.Clientset
    config    *rest.Config
}

// Major operations:
ApplyResources(yaml []byte) error
DeleteResources(kind, name string) error
GetLogs(pod, namespace string) (string, error)
ExecuteInPod(pod, namespace, cmd string) (stdout, stderr string, error)
GetResourceMetrics(kind string) (Metrics, error)
```

### 4. **API Gateway**

**Purpose**: Generic REST API routing  
**Protocol**: HTTP with JWT  
**Location**: `internal/gateway/client.go`

```go
type GatewayClient struct {
    baseURL    string
    httpClient *http.Client
    token      string
}

// Methods:
Query(service, endpoint string, params map[string]string) (json.RawMessage, error)
Post(service, endpoint string, body interface{}) (json.RawMessage, error)
Put(service, endpoint string, body interface{}) (json.RawMessage, error)
Delete(service, endpoint string) error
```

### 5. **Redis (Optional Caching)**

**Purpose**: Distributed caching  
**Client Library**: `github.com/redis/go-redis`  
**Configuration**: `internal/config/`

### 6. **Prometheus Metrics**

**Purpose**: Observability and monitoring  
**Client Library**: `github.com/prometheus/client_golang`  
**Metrics Exported**: Operation duration, error rates, etc.

---

## Module Responsibilities

### High-Level Module Map

| Module | Responsibility | Key Files | Pattern |
|--------|-----------------|-----------|---------|
| `cmd/` | CLI command implementations | root.go, agents.go, k8s_*.go | Command |
| `agents/` | Autonomous agent system | orchestrator.go, strategies/ | Strategy + Factory |
| `shell/` | Interactive REPL interface | shell.go, completer.go | REPL + MVC |
| `k8s/` | Kubernetes operations | handlers.go, operations.go | Adapter |
| `maximus/` | AI service clients | consciousness_client.go | Service Adapter |
| `orchestrator/` | Operation orchestration | engine.go, defensive/, offensive/ | Strategy |
| `config/` | Configuration management | config.go, loader.go | Singleton |
| `errors/` | Structured error handling | types.go, builders.go | Builder |
| `gateway/` | Generic API client | client.go | Adapter |
| `nlp/` | Natural language processing | orchestrator.go, tokenizer/ | Pipeline |
| `tui/` | Terminal UI components | model.go, update.go, view.go | Bubble Tea MVC |
| `workspace/` | Workspace management | manager.go, governance/, investigation/ | Strategy |
| `security/` | Security operations | auth/, audit/, behavioral/ | Mixed |
| `visual/` | UI rendering & styling | banner/, palette/ | Decorator |
| `plugins/` | Plugin system | kubernetes/ | Registry |

---

## Code Metrics

```
Total Lines:        ~21,000+ (internal/)
Go Files:           315 (internal/)
Command Files:      60+ (cmd/)
Directories:        73 (internal/)
External Deps:      37 direct, 80+ transitive
Go Version:         1.24.0+

Largest Modules:
- cmd/maximus.go          ~49 KB (49,524 lines)
- cmd/agents.go           ~39 KB (39,123 lines)
- internal/k8s/handlers.go ~34 KB (34,282 lines)
- cmd/immune.go           ~23 KB (23,769 lines)
- cmd/immunis.go          ~19 KB (19,888 lines)
- cmd/investigate.go      ~19 KB (19,659 lines)
```

---

## Architectural Principles

1. **Modularity**: Feature-based package organization with clear boundaries
2. **Extensibility**: Strategy pattern for language/operation support
3. **Resilience**: Circuit breaker, retry, and rate limiting patterns
4. **Security**: Structured error handling, audit logging, HITL framework
5. **Observability**: Prometheus metrics, distributed tracing support
6. **User Experience**: Rich TUI with context-aware completion
7. **Testability**: Dependency injection, interface-based design
8. **Maintainability**: Clear separation of concerns, consistent patterns

---

## Technology Stack

| Category | Technologies |
|----------|---|
| **Language** | Go 1.24.0+ |
| **CLI Framework** | Cobra 1.9.1 |
| **TUI Library** | Bubble Tea 1.3.4 |
| **Cloud** | Kubernetes client-go 0.31.0 |
| **Communication** | gRPC 1.76.0, Protocol Buffers 3 |
| **Messaging** | WebSocket (gorilla) |
| **Caching** | Redis 9.14.1, Badger 4.8.0 |
| **Security** | JWT 5.3.0, OTP 1.5.0 |
| **Observability** | Prometheus 1.23.2, OpenTelemetry 1.37.0 |
| **Configuration** | YAML 3.0.1 |
| **Testing** | Testify 1.11.1 |

---

## Future Enhancement Areas

1. **Plugin System**: Expand kubernetes plugin to support other orchestration platforms
2. **Workflow Engine**: Dedicated workflow definition and execution
3. **Advanced NLP**: Incorporate transformer models for intent recognition
4. **Performance**: Implement request batching and caching strategies
5. **Analytics**: Enhanced metrics collection and dashboards
6. **Mobile**: Native mobile CLI clients
7. **Multi-tenancy**: Workspace isolation and RBAC

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-14  
**Status**: Final Comprehensive Architecture Map
