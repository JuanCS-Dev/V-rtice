# Guardian Agents - Constitutional Enforcement System

## Overview

The Guardian Agents system implements **Anexo D: A Doutrina da "Execução Constitucional"** of the Vértice Constitution, providing autonomous enforcement of constitutional principles across the MAXIMUS ecosystem.

## Architecture

```
GuardianCoordinator (Central Orchestration)
    ├── ArticleIIGuardian  (Sovereign Quality Standard)
    ├── ArticleIIIGuardian (Zero Trust Principle)
    ├── ArticleIVGuardian  (Deliberate Antifragility)
    └── ArticleVGuardian   (Prior Legislation)
```

## Guardian Agents

### Article II Guardian - Sovereign Quality Standard ("Padrão Pagani")
- **Enforces:** No mocks, placeholders, or TODOs in production code
- **Monitors:** Code quality, test completeness, technical debt
- **Key Actions:** Vetos deployments with incomplete implementations

### Article III Guardian - Zero Trust Principle
- **Enforces:** No component is inherently trusted
- **Monitors:** Authentication, authorization, input validation, audit trails
- **Key Actions:** Blocks unvalidated AI artifacts, enforces HITL controls

### Article IV Guardian - Deliberate Antifragility
- **Enforces:** System must strengthen from chaos
- **Monitors:** Chaos tests, resilience patterns, experimental features
- **Key Actions:** Runs chaos experiments, quarantines risky features

### Article V Guardian - Prior Legislation
- **Enforces:** Governance before autonomous power
- **Monitors:** Autonomous capabilities, HITL controls, kill switches
- **Key Actions:** Blocks autonomous systems without governance

## Quick Start

### Basic Usage

```python
from governance.guardian import GuardianCoordinator

# Initialize and start the Guardian system
coordinator = GuardianCoordinator()
await coordinator.start()

# Get system status
status = coordinator.get_status()
print(f"Active Guardians: {len(status['guardians'])}")
print(f"Compliance Score: {status['metrics']['compliance_score']:.1f}%")

# Generate compliance report
report = coordinator.generate_compliance_report(period_hours=24)
print(f"Violations in last 24h: {report['summary']['total_violations']}")

# Stop the system
await coordinator.stop()
```

### Running Individual Guardians

```python
from governance.guardian import ArticleIIGuardian

# Create and start a specific guardian
quality_guardian = ArticleIIGuardian()
await quality_guardian.start()

# Monitor for violations
violations = await quality_guardian.monitor()
for violation in violations:
    print(f"[{violation.severity.value}] {violation.description}")

# Generate guardian-specific report
report = quality_guardian.generate_report(period_hours=24)
print(f"Quality compliance: {report.compliance_score:.1f}%")
```

## Key Features

### Veto Power

Guardians can veto actions that violate the Constitution:

```python
veto = await guardian.veto_action(
    action="deploy_to_production",
    system="maximus_core",
    reason="Contains NotImplementedError violations",
    duration_hours=24  # Temporary veto
)
```

### Violation Detection

Guardians continuously monitor for violations:

```python
# Register callbacks for real-time notifications
async def handle_violation(violation: ConstitutionalViolation):
    if violation.severity == GuardianPriority.CRITICAL:
        # Take immediate action
        await emergency_response(violation)

guardian.register_violation_callback(handle_violation)
```

### Conflict Resolution

The Coordinator resolves conflicts between Guardian decisions:

```python
# Conflicts are automatically resolved based on:
# 1. Severity (CRITICAL > HIGH > MEDIUM > LOW)
# 2. Article precedence (V > III > II > IV)
# 3. Constitutional principles
```

## Configuration

### Environment Variables

```bash
# Guardian monitoring intervals (seconds)
GUARDIAN_MONITOR_INTERVAL=60
COORDINATOR_MONITOR_INTERVAL=30

# Thresholds
VETO_ESCALATION_THRESHOLD=3
COMPLIANCE_ALERT_THRESHOLD=80

# Paths to monitor
GUARDIAN_MONITOR_PATHS=/path/to/services
```

### Custom Configuration

```python
coordinator = GuardianCoordinator()

# Customize monitoring interval
coordinator._monitor_interval = 15  # seconds

# Set escalation threshold
coordinator.veto_escalation_threshold = 5

# Add alert channels
coordinator.critical_alert_channels.append(slack_notifier)
```

## Integration Points

### CI/CD Integration

```yaml
# .github/workflows/guardian-check.yml
name: Guardian Constitutional Check

on: [pull_request]

jobs:
  guardian-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Run Guardian Checks
        run: |
          python -m governance.guardian.check_pr \
            --diff "${{ github.event.pull_request.diff_url }}"
```

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Run Article II Guardian check
python -m governance.guardian.article_ii_check

if [ $? -ne 0 ]; then
  echo "Constitutional violations detected. Commit blocked."
  exit 1
fi
```

### API Integration

```python
from fastapi import FastAPI, HTTPException
from governance.guardian import GuardianCoordinator

app = FastAPI()
coordinator = GuardianCoordinator()

@app.get("/guardian/status")
async def get_guardian_status():
    """Get current Guardian system status."""
    return coordinator.get_status()

@app.post("/guardian/override-veto")
async def override_veto(veto_id: str, reason: str, approver_id: str):
    """Override a Guardian veto (requires authorization)."""
    success = await coordinator.override_veto(
        veto_id=veto_id,
        override_reason=reason,
        approver_id=approver_id
    )
    if not success:
        raise HTTPException(400, "Veto override failed")
    return {"status": "overridden"}
```

## Monitoring & Observability

### Metrics Exposed

- `guardian_violations_total`: Total violations detected
- `guardian_interventions_total`: Total interventions made
- `guardian_vetos_active`: Currently active vetos
- `guardian_compliance_score`: System compliance percentage
- `guardian_chaos_experiments_run`: Chaos experiments executed

### Logging

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("guardian")

# Guardians log key events
# INFO: Violations detected, interventions made
# WARNING: Compliance below threshold
# ERROR: Guardian system failures
# CRITICAL: Constitutional crisis requiring human intervention
```

### Dashboards

Recommended dashboard panels:
1. **Compliance Score Trend** - Track overall constitutional compliance
2. **Violations by Article** - Identify problem areas
3. **Active Vetos** - Monitor blocked actions
4. **Guardian Health** - Ensure all guardians are active
5. **Top Violations** - Focus improvement efforts

## Testing

### Run Tests

```bash
# Run all Guardian tests
pytest governance/guardian/test_guardians.py -v

# Run specific guardian tests
pytest governance/guardian/test_guardians.py::TestArticleIIGuardian -v

# Run with coverage
pytest governance/guardian/test_guardians.py --cov=governance.guardian
```

### Test Coverage Areas

- **Unit Tests:** Individual guardian logic
- **Integration Tests:** Multi-guardian coordination
- **Chaos Tests:** System resilience validation
- **Compliance Tests:** Constitutional enforcement

## Troubleshooting

### Common Issues

1. **Guardian not detecting violations**
   - Check monitored paths are correct
   - Verify file patterns match your codebase
   - Ensure guardian is started and active

2. **Too many false positives**
   - Review excluded paths configuration
   - Adjust severity thresholds
   - Add context-specific exemptions

3. **Veto blocking legitimate actions**
   - Review veto reason and evidence
   - Consider override if justified
   - Update guardian rules if needed

4. **High resource usage**
   - Increase monitoring interval
   - Optimize file scanning patterns
   - Enable incremental checking

## Best Practices

1. **Start with monitoring mode** - Run guardians in alert-only mode initially
2. **Gradual enforcement** - Enable veto power after tuning detection rules
3. **Regular reviews** - Review guardian reports weekly
4. **Team training** - Ensure team understands constitutional principles
5. **Continuous improvement** - Update rules based on false positives/negatives

## Constitutional Alignment

This system directly implements the Vértice Constitution:

- **Article I**: Not enforced (human sovereignty)
- **Article II**: Enforced via quality checks
- **Article III**: Enforced via security validation
- **Article IV**: Enforced via chaos engineering
- **Article V**: Enforced via governance precedence

The Guardian system ensures that all development and operations within the MAXIMUS ecosystem comply with these constitutional principles automatically and continuously.

## Support

- **Documentation:** `/docs/guardian-agents/`
- **Issues:** Report in governance repository
- **Emergency:** Contact ERB for critical veto overrides

---

*"A Constituição não é um guia. É a lei fundamental."* - Vértice Constitution v2.5