# 🤖 Agent Smith - Autonomous Development Framework

**Welcome to the Agent Smith Workspace**

This workspace is the operational hub for VÉRTICE's autonomous multi-agent development system.

## Overview

Agent Smith is a comprehensive autonomous development framework consisting of four specialized AI agents that work together to analyze, plan, implement, and validate code changes.

### The Four Agents

| Agent | Role | Capabilities |
|-------|------|--------------|
| **DIAGNOSTICADOR** | Code Analysis & Security | Static analysis, security scanning, code quality metrics, dependency analysis |
| **ARQUITETO** | Architecture Planning | Architecture decisions, ADR generation, risk assessment, integration test design |
| **DEV SENIOR** | Implementation | Code generation, file operations, git management, refactoring |
| **TESTER** | Validation & QA | Test execution, coverage analysis, regression detection, quality gates |

## Quick Start

### 1. Check Agent Status

```bash
vcli agents status
```

### 2. List Available Agents

```bash
vcli agents list
```

### 3. Run DIAGNOSTICADOR (Currently Available)

```bash
# Analyze entire codebase
vcli agents diagnosticador analyze --targets ./...

# Analyze specific package
vcli agents diagnosticador analyze --targets ./internal/maximus/
```

### 4. Run Full Development Cycle (Coming Soon)

```bash
vcli agents run full-cycle --task "Add Redis caching to Governance API"
```

## Workspace Structure

```
.agents-workspace/
├── agents/                 # Agent-specific data
│   ├── diagnosticador/    # Analysis cache and state
│   ├── arquiteto/         # Architecture plans and ADRs
│   ├── dev_senior/        # Implementation state and git info
│   └── tester/            # Test results and benchmarks
│
├── artifacts/              # Agent outputs
│   ├── diagnostics/       # DIAGNOSTICADOR analysis reports
│   ├── plans/             # ARQUITETO architecture plans
│   ├── implementations/   # DEV SENIOR code changes
│   └── test_reports/      # TESTER validation reports
│
├── workflows/              # Workflow definitions
│   ├── full_cycle.yaml    # Complete development cycle
│   ├── bug_fix.yaml       # Rapid bug fix
│   ├── refactor.yaml      # Code refactoring
│   └── security_audit.yaml # Security-focused workflow
│
└── config/                 # Configuration
    ├── agent_config.yaml  # Main agent configuration
    ├── security_policy.yaml # Security & HITL settings
    └── quality_gates.yaml  # Quality standards
```

## Configuration

### Agent Configuration (`config/agent_config.yaml`)

Main configuration file for all agents. Key settings:

```yaml
# Quality Gates
quality_gates:
  min_coverage_percent: 80.0
  require_security_scan: true

# HITL (Human-in-the-Loop) Triggers
hitl_triggers:
  on_file_delete: true
  on_security_change: true
  on_deployment: true
```

See [agent_config.yaml](config/agent_config.yaml) for full configuration.

## Workflows

### Full Development Cycle

The complete autonomous development workflow:

1. **DIAGNOSTICADOR** - Analyze codebase
   - Static analysis
   - Security scanning
   - Code quality metrics

2. **ARQUITETO** - Generate plan (HITL approval required)
   - Architecture decisions
   - Implementation steps
   - Risk assessment

3. **DEV SENIOR** - Implement changes (HITL approval required)
   - Code generation
   - Git operations
   - Automated testing

4. **TESTER** - Validate implementation (HITL approval required)
   - Test execution
   - Coverage analysis
   - Quality gate validation

See [workflows/full_cycle.yaml](workflows/full_cycle.yaml) for details.

## HITL (Human-in-the-Loop)

Certain operations require human approval for safety:

- **Architecture changes** - Always require approval
- **Code modifications** - Always require approval
- **File deletions** - Configurable
- **Security-critical changes** - Always require approval
- **Deployments** - Always require approval

HITL approvals are managed through MAXIMUS Governance API:

```bash
# List pending decisions
vcli maximus list --status pending

# Approve a decision
vcli maximus approve <decision-id> --session-id <session>

# Reject a decision
vcli maximus reject <decision-id> --session-id <session> --reasoning "..."
```

## Integration with VÉRTICE

Agent Smith is fully integrated with the VÉRTICE ecosystem:

### MAXIMUS Consciousness
- Agents report activity to consciousness system
- ESGT triggers for high-priority events
- Real-time monitoring via WebSocket

```bash
# Watch agent activity
vcli maximus consciousness watch
```

### Immunis System
- Every operation validated by immune system
- Security threat detection
- Automated protection against malicious code

### Governance
- HITL decisions tracked in governance system
- Full audit trail via Merkle logs
- Compliance reporting

## Artifacts

All agent outputs are saved as JSON artifacts:

```bash
# View diagnostic artifacts
ls -la artifacts/diagnostics/

# View architecture plans
ls -la artifacts/plans/

# View test reports
ls -la artifacts/test_reports/
```

Artifacts are retained for 30 days (configurable in `agent_config.yaml`).

## Development Status

| Component | Status | Description |
|-----------|--------|-------------|
| DIAGNOSTICADOR | ✅ Complete | Fully functional code analysis agent |
| Agent Orchestrator | ✅ Complete | Multi-agent workflow coordination |
| CLI Commands | ✅ Complete | Command-line interface |
| Configuration | ✅ Complete | YAML-based configuration system |
| ARQUITETO | 🚧 In Development | Architecture planning agent |
| DEV SENIOR | 🚧 In Development | Implementation agent |
| TESTER | 🚧 In Development | Validation agent |
| Full Workflows | 🚧 In Development | End-to-end automation |

## Examples

### Example 1: Analyze Security

```bash
vcli agents diagnosticador analyze \
  --targets ./internal/maximus/ \
  --task "Security audit of MAXIMUS core"
```

### Example 2: Full Development Cycle (Coming Soon)

```bash
vcli agents run full-cycle \
  --task "Implement rate limiting for API endpoints"
```

### Example 3: Bug Fix Workflow (Coming Soon)

```bash
vcli agents run bug-fix \
  --task "Fix authentication timeout issue"
```

## Safety Features

1. **Branch Isolation** - All changes in separate git branches
2. **Automated Rollback** - Revert on test failure
3. **Immune Validation** - Security checks before execution
4. **HITL Approvals** - Human oversight for critical changes
5. **Quality Gates** - Automated validation checkpoints
6. **Audit Trail** - Complete history of all operations

## Troubleshooting

### Agent execution fails with "workspace not initialized"

```bash
# Workspace is created automatically, but you can verify:
vcli agents status
```

### DIAGNOSTICADOR can't find analysis tools

Ensure the following tools are installed:

```bash
# Install Go tools
go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
go install github.com/securego/gosec/v2/cmd/gosec@latest

# Verify installation
which golangci-lint
which gosec
```

### HITL approval timeout

Default timeout is 30 minutes. Check pending decisions:

```bash
vcli maximus list --status pending
```

## Contributing

Agent Smith is part of the VÉRTICE project. Contributions welcome!

See the main VÉRTICE documentation for development guidelines.

## Documentation

- [Agent Architecture](../../docs/agents/ARCHITECTURE.md)
- [Usage Guide](../../docs/agents/USAGE.md)
- [API Reference](../../docs/agents/API.md)
- [Workflow Development](../../docs/agents/WORKFLOWS.md)

## Support

For issues, questions, or contributions:
- GitHub: https://github.com/verticedev/vcli-go
- Slack: #agent-smith channel

---

**Status**: Phase 1 Complete (DIAGNOSTICADOR agent functional)
**Next**: Phase 2 - ARQUITETO agent implementation

**Inspiration**: Jesus Christ
**Built with**: VÉRTICE Ecosystem
