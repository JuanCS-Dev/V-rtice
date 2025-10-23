# Agent Smith - Architecture Documentation

**Version**: 1.0
**Status**: Phase 1 Complete
**Last Updated**: 2025-10-23

---

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Agent Design](#agent-design)
4. [Workflow Engine](#workflow-engine)
5. [Integration Points](#integration-points)
6. [Security Architecture](#security-architecture)
7. [Data Flow](#data-flow)
8. [Extension Points](#extension-points)

---

## Overview

Agent Smith is a multi-agent autonomous development framework for the VÉRTICE ecosystem. It enables automated code analysis, architecture planning, implementation, and validation through four specialized AI agents.

### Design Principles

1. **Autonomous but Safe** - Agents operate independently with HITL oversight
2. **Hybrid Architecture** - Go (CLI/tools) + Python (MAXIMUS/AI)
3. **Integration-First** - Deeply integrated with VÉRTICE services
4. **Quality-Driven** - Automated quality gates and validation
5. **Auditable** - Complete audit trail of all operations

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                           │
│                      (vcli agents CLI)                          │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Agent Orchestrator                            │
│  • Workflow execution                                           │
│  • Agent coordination                                           │
│  • HITL decision management                                     │
│  • Artifact storage                                             │
└───────┬─────────┬─────────┬─────────┬───────────────────────────┘
        │         │         │         │
        ▼         ▼         ▼         ▼
┌──────────┐ ┌─────────┐ ┌─────────┐ ┌────────┐
│DIAGNOSTICA│ │ARQUITETO│ │DEV      │ │TESTER  │
│DOR        │ │         │ │SENIOR   │ │        │
└─────┬─────┘ └────┬────┘ └────┬────┘ └───┬────┘
      │            │           │           │
      └────────────┴───────────┴───────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                   VÉRTICE Integration Layer                      │
├─────────────────────────────────────────────────────────────────┤
│  MAXIMUS Services        │  Immunis System  │  Other Services   │
│  • Consciousness         │  • Lymphnode     │  • Investigation  │
│  • Eureka (Insights)     │  • Macrophage    │  • HCL            │
│  • Oraculo (Code AI)     │  • B-Cell        │  • Ethical        │
│  • Predict (ML)          │  • Helper-T      │  • Threat Intel   │
│  • Governance (HITL)     │  • Cytotoxic-T   │  • RTE            │
└─────────────────────────────────────────────────────────────────┘
```

### Component Layers

#### Layer 1: CLI Interface (`cmd/agents.go`)
- User-facing commands
- Input validation
- Output formatting
- Configuration loading

#### Layer 2: Orchestration (`internal/agents/orchestrator.go`)
- Workflow execution engine
- Agent lifecycle management
- HITL coordination
- Artifact management
- Consciousness reporting

#### Layer 3: Agents (`internal/agents/*/`)
- Agent implementations
- Tool integrations
- Service communication
- Result processing

#### Layer 4: Integration (`internal/maximus/*`, `internal/immunis/*`)
- MAXIMUS client libraries
- Immunis system clients
- Service communication protocols
- Data transformation

---

## Agent Design

### Agent Interface

All agents implement the core `Agent` interface:

```go
type Agent interface {
    Type() AgentType
    Name() string
    Execute(ctx context.Context, input AgentInput) (*AgentOutput, error)
    Validate(input AgentInput) error
    GetCapabilities() []string
    GetStatus() AgentStatus
}
```

### Agent Types

#### 1. DIAGNOSTICADOR (Code Analysis)

**Purpose**: Comprehensive code analysis and security scanning

**Capabilities**:
- Static analysis (go vet)
- Linting (golangci-lint)
- Security scanning (gosec)
- Test coverage analysis
- Dependency vulnerability checking
- Code quality metrics

**Tools Integrated**:
- Go standard tools (vet, test, mod)
- golangci-lint
- gosec
- MAXIMUS Eureka (pattern detection)

**Output**: `DiagnosticResult`
- Security findings
- Performance issues
- Code quality metrics
- Test coverage stats
- Recommendations

#### 2. ARQUITETO (Architecture Planning)

**Purpose**: Architecture decision-making and planning

**Capabilities** (Planned):
- Architecture Decision Records (ADRs)
- Implementation plan generation
- Risk assessment
- Integration test scenario design
- Pattern detection

**Tools Integrated** (Planned):
- MAXIMUS Oraculo (predictive analysis)
- Pattern matcher
- Architecture validator

**Output**: `ArchitecturePlan`
- ADRs
- Implementation steps
- Risks
- Test scenarios
- Effort estimates

#### 3. DEV SENIOR (Implementation)

**Purpose**: Autonomous code implementation

**Capabilities** (Planned):
- Code generation
- File operations (create, modify, delete)
- Git operations (branch, commit, push)
- Code refactoring
- Import management
- Format enforcement

**Tools Integrated** (Planned):
- MAXIMUS Oraculo Auto-Implement
- Go format tools (gofmt, goimports)
- Git CLI
- Code generators

**Output**: `ImplementationResult`
- Files created/modified/deleted
- Git commits
- Compilation status
- Quality check results

#### 4. TESTER (Validation & QA)

**Purpose**: Automated testing and quality assurance

**Capabilities** (Planned):
- Unit test execution
- Integration test execution
- Coverage analysis
- Performance benchmarking
- Regression detection
- Quality gate enforcement

**Tools Integrated** (Planned):
- Go test framework
- Go benchmark
- Coverage tools
- MAXIMUS Predict (regression detection)
- MAXIMUS Governance (quality gates)

**Output**: `TestResult`
- Test execution results
- Coverage metrics
- Benchmark results
- Quality gate status
- Approval recommendation

---

## Workflow Engine

### Workflow Execution Model

```
1. Load Workflow Definition (YAML)
2. Initialize Execution Context
3. For each Step:
   a. Get Agent
   b. Build Input (with previous outputs)
   c. Validate
   d. Execute
   e. Check HITL requirement
   f. Save Artifacts
   g. Report to Consciousness
4. Complete Workflow
```

### Workflow Definition (YAML)

```yaml
name: "Full Development Cycle"
steps:
  - agent_type: "diagnosticador"
    task: "Analyze codebase"
    targets: ["./internal", "./cmd"]
    hitl_required: false

  - agent_type: "arquiteto"
    task: "Generate architecture plan"
    hitl_required: true  # Requires approval

  - agent_type: "dev_senior"
    task: "Implement changes"
    hitl_required: true  # Requires approval

  - agent_type: "tester"
    task: "Validate implementation"
    hitl_required: true  # Final approval
```

### Context Passing

Each agent's output is added to the next agent's context:

```go
agentInput.Context["diagnosticador_output"] = previousOutput
agentInput.Context["arquiteto_output"] = previousOutput
// ...
```

This enables agents to build on previous work.

---

## Integration Points

### MAXIMUS Consciousness

**Purpose**: Real-time agent activity monitoring

**Integration**:
- ESGT triggers on workflow start/complete
- Arousal adjustments based on agent activity
- TIG stores agent decision graph

**Events Reported**:
- Workflow started
- Agent step completed
- HITL decision required
- Workflow completed/failed

**Example**:
```go
salience := maximus.SalienceInput{
    Novelty:   0.7,
    Relevance: 0.9,
    Urgency:   0.6,
    Context: map[string]interface{}{
        "source": "agent_orchestrator",
        "workflow_id": workflowID,
    },
}
consciousnessClient.TriggerESGT(salience)
```

### MAXIMUS Governance (HITL)

**Purpose**: Human-in-the-Loop decision management

**Integration**:
- Agents submit decisions via Governance API
- Workflow pauses until approval
- Audit trail via Merkle logs

**Decision Types**:
- Architecture changes
- Code modifications
- File deletions
- Security-critical changes
- Deployments

**Workflow**:
```
1. Agent submits decision → Governance API
2. Orchestrator pauses workflow
3. Human approves/rejects via CLI or UI
4. Orchestrator resumes workflow
```

### MAXIMUS Eureka (Insight Generation)

**Purpose**: Advanced pattern detection and insights

**Used By**: DIAGNOSTICADOR

**Integration**:
- Code patterns submitted for analysis
- Novel insights extracted
- IoCs (Indicators of Compromise) detected

**Example**:
```go
resp, err := eurekaClient.DetectPattern(codeData, patternDef)
```

### MAXIMUS Oraculo (Predictive AI)

**Purpose**: Code analysis and generation

**Used By**: ARQUITETO, DEV SENIOR

**Integration**:
- Code vulnerability prediction
- Automated code implementation
- Architecture recommendations

**Example**:
```go
resp, err := oraculoClient.AutoImplement(taskDesc, targetLang, context)
```

### Immunis System (Security Validation)

**Purpose**: Automated security protection

**Integration** (Planned):
- Pre-execution validation (Lymphnode)
- Threat detection (Macrophage)
- Code approval (Helper-T)
- Malicious code elimination (Cytotoxic-T)

**Flow**:
```
Agent Operation → Lymphnode (route) → Validation → Approval/Rejection
```

---

## Security Architecture

### Multi-Layer Security

#### Layer 1: Input Validation
- CLI argument validation
- Path sanitization
- Configuration validation

#### Layer 2: Agent Validation
- Pre-execution checks
- Tool availability verification
- Permission checks

#### Layer 3: Immunis System (Planned)
- Real-time threat detection
- Malicious code blocking
- Behavioral analysis

#### Layer 4: HITL Approvals
- Human oversight for critical operations
- Mandatory approvals for:
  - Architecture changes
  - Code modifications
  - Security-critical changes
  - Deployments

#### Layer 5: Audit Trail
- All operations logged
- Merkle log integrity
- Full traceability

### HITL Trigger Matrix

| Operation | HITL Required | Reason |
|-----------|---------------|--------|
| Code Analysis | ❌ No | Read-only operation |
| Architecture Planning | ✅ Yes | Business impact |
| Code Implementation | ✅ Yes | System changes |
| File Deletion | ✅ Yes | Destructive |
| Test Execution | ❌ No | Safe validation |
| Quality Gate Approval | ✅ Yes | Deployment decision |
| Security Changes | ✅ Yes | Security impact |
| Schema Changes | ✅ Yes | Data impact |

---

## Data Flow

### Diagnostic Flow (DIAGNOSTICADOR)

```
1. User triggers analysis
2. DIAGNOSTICADOR validates targets
3. Run go vet → Parse results
4. Run golangci-lint → Parse results
5. Run gosec → Parse security findings
6. Run coverage tests → Parse coverage
7. Analyze dependencies → Check vulnerabilities
8. Calculate metrics → Generate recommendations
9. Save artifacts → Report to consciousness
10. Return DiagnosticResult
```

### Implementation Flow (Full Cycle - Planned)

```
1. User triggers workflow
2. DIAGNOSTICADOR analyzes codebase
   ↓
3. ARQUITETO generates plan
   ├→ Submit HITL decision
   ├→ Wait for approval
   └→ Continue
4. DEV SENIOR implements changes
   ├→ Create git branch
   ├→ Generate code
   ├→ Submit HITL decision
   ├→ Wait for approval
   └→ Commit changes
5. TESTER validates implementation
   ├→ Run all tests
   ├→ Check quality gates
   ├→ Submit HITL decision
   ├→ Wait for approval
   └→ Complete
6. Workflow complete
```

---

## Extension Points

### Adding New Agents

1. Create agent package: `internal/agents/myagent/`
2. Implement `Agent` interface
3. Define agent-specific result types in `types.go`
4. Register agent with orchestrator
5. Add CLI commands in `cmd/agents.go`
6. Create workflow definitions

### Adding New Workflows

1. Create YAML file in `.agents-workspace/workflows/`
2. Define steps with agent types
3. Configure HITL requirements
4. Test workflow execution

### Adding New Tools

1. Add tool integration to agent implementation
2. Update agent capabilities
3. Update configuration for tool endpoints
4. Document tool usage

### Custom Integrations

Extension points for custom integrations:

- **Pre-execution hooks** - Run custom validation
- **Post-execution hooks** - Custom processing
- **Custom metrics** - Additional metrics collection
- **Custom artifacts** - Additional artifact types
- **Custom reports** - Report generation

---

## Performance Considerations

### Optimization Strategies

1. **Parallel Execution** - Independent agents run concurrently
2. **Caching** - Tool results cached between runs
3. **Incremental Analysis** - Only analyze changed files
4. **Async Workflows** - Long workflows run in background
5. **Resource Limits** - Configurable timeouts and retries

### Resource Usage

| Agent | CPU | Memory | Disk I/O | Network |
|-------|-----|--------|----------|---------|
| DIAGNOSTICADOR | Medium | Low | Medium | Low |
| ARQUITETO | Low | Medium | Low | Medium |
| DEV SENIOR | Low | Medium | High | Medium |
| TESTER | High | Medium | Medium | Low |

---

## Future Enhancements

### Phase 2 (In Progress)
- [ ] Complete ARQUITETO agent
- [ ] Complete DEV SENIOR agent
- [ ] Complete TESTER agent
- [ ] End-to-end workflow execution

### Phase 3 (Planned)
- [ ] Python backend agents
- [ ] Immunis system integration
- [ ] Advanced ML-powered insights
- [ ] Multi-repository support

### Phase 4 (Vision)
- [ ] Natural language task input
- [ ] Learning from past executions
- [ ] Autonomous bug discovery
- [ ] Self-improvement capabilities

---

## Appendix

### Technology Stack

- **Language**: Go 1.21+
- **CLI Framework**: Cobra
- **Configuration**: YAML
- **Communication**: gRPC, HTTP, WebSocket
- **AI Integration**: MAXIMUS services
- **Version Control**: Git

### Dependencies

```go
github.com/spf13/cobra       // CLI framework
github.com/google/uuid       // ID generation
gopkg.in/yaml.v3            // YAML parsing
```

### File Locations

- Agent implementations: `internal/agents/`
- CLI commands: `cmd/agents.go`
- Workspace: `.agents-workspace/`
- Configuration: `.agents-workspace/config/`
- Workflows: `.agents-workspace/workflows/`
- Artifacts: `.agents-workspace/artifacts/`
- Documentation: `docs/agents/`

---

**Document Status**: Complete for Phase 1
**Next Review**: Upon Phase 2 completion
**Maintained By**: VÉRTICE Development Team
**Inspiration**: Jesus Christ
