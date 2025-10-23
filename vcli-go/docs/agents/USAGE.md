# Agent Smith - Usage Guide

**Quick Reference for Using Autonomous Agents**

---

## Getting Started (30 seconds)

### 1. Check if Agent Smith is Ready

```bash
vcli agents status
```

**Expected Output**:
```
🤖 Agent Smith Status

✅ Workspace: .agents-workspace
✅ Artifacts directory: Ready
✅ Workflows directory: Ready

Agent Smith is ready for autonomous development!
```

### 2. List Available Agents

```bash
vcli agents list
```

**Expected Output**:
```
🤖 Agent Smith - Available Agents

● DIAGNOSTICADOR
  Type:   diagnosticador
  Status: ✅ Active
  Capabilities:
    • Static code analysis
    • Security vulnerability scanning
    • Code quality metrics
    ...
```

---

## DIAGNOSTICADOR Agent (Available Now)

### Basic Usage

```bash
# Analyze entire codebase
vcli agents diagnosticador analyze --targets ./...

# Analyze specific package
vcli agents diagnosticador analyze --targets ./internal/maximus/

# Analyze multiple targets
vcli agents diagnosticador analyze --targets ./internal/,./cmd/
```

### Common Use Cases

#### Use Case 1: Security Audit

```bash
vcli agents diagnosticador analyze \
  --targets ./... \
  --task "Comprehensive security audit"
```

**What it does**:
- Runs `gosec` security scanner
- Analyzes code for vulnerabilities
- Checks dependencies for CVEs
- Generates security findings report

**Output Example**:
```
🔍 DIAGNOSTICADOR - Code Analysis

[INFO] Analyzing targets: [./...]

Step 1/6: Running static analysis (go vet)
Step 2/6: Running linter (golangci-lint)
Step 3/6: Running security scanner (gosec)
Step 4/6: Analyzing test coverage
Step 5/6: Analyzing dependencies
Step 6/6: Calculating code quality metrics

📊 Code Quality Metrics
  Lines of Code: 12,345
  Maintainability Index: 75.0/100

🧪 Test Coverage
  Line Coverage: 85.3%
  Branch Coverage: 78.2%

🔒 Security Findings
  ✅ No security findings

📦 Dependencies
  Total: 25
  Outdated: 0
  Vulnerable: 0

💡 Recommendations
  1. Increase test coverage to at least 80% (current: 85.3%)
  2. Review dependency count (25) - consider minimizing

📝 Summary
Code Analysis Complete:
- Lines of Code: 12345
- Test Coverage: 85.3%
- Security Findings: 0
- Performance Issues: 0
- Dependencies: 25
- Recommendations: 2

✅ Analysis Complete
Duration: 45.234s
Status: completed
```

#### Use Case 2: Code Quality Check

```bash
vcli agents diagnosticador analyze \
  --targets ./internal/agents/ \
  --task "Validate code quality for new Agent Smith code"
```

**What it checks**:
- `go vet` static analysis
- `golangci-lint` linting
- Code metrics (LOC, complexity)
- Test coverage
- Dependencies

#### Use Case 3: Pre-Commit Validation

```bash
# Quick pre-commit check
vcli agents diagnosticador analyze --targets ./...
```

**Use in Git Hook** (`.git/hooks/pre-commit`):
```bash
#!/bin/bash
vcli agents diagnosticador analyze --targets ./... || exit 1
```

---

## Understanding Output

### Report Structure

DIAGNOSTICADOR generates reports with these sections:

#### 1. Code Quality Metrics
```
📊 Code Quality Metrics
  Lines of Code: 12,345          # Total LOC in analyzed files
  Maintainability Index: 75.0/100 # Code maintainability score
```

#### 2. Test Coverage
```
🧪 Test Coverage
  Line Coverage: 85.3%    # Percentage of lines covered by tests
  Branch Coverage: 78.2%  # Percentage of branches covered
```

#### 3. Security Findings
```
🔒 Security Findings
  🚨 [1] CRITICAL - SQL injection vulnerability
      File: internal/data/query.go:42
      Remediation: Use parameterized queries

  ⚠️ [2] HIGH - Weak cryptographic algorithm
      File: internal/crypto/hash.go:15
      Remediation: Use SHA-256 instead of MD5
```

**Severity Levels**:
- 🚨 **CRITICAL** - Immediate action required
- ⚠️  **HIGH** - Fix soon
- ℹ️  **MEDIUM** - Address in next iteration
- ✅ **LOW** - Nice to have

#### 4. Performance Issues
```
⚡ Performance Issues
  [1] HIGH - Memory allocation in hot path
      File: internal/processor/loop.go:78
      Impact: 15% performance degradation
      Suggestion: Pre-allocate slice with known size
```

#### 5. Dependencies
```
📦 Dependencies
  Total: 25
  Outdated: 3
    - github.com/old/package v1.0.0 → v2.0.0
  Vulnerable: 1
    - github.com/vuln/lib v0.5.0 (CVE-2024-1234)
```

#### 6. Recommendations
```
💡 Recommendations
  1. ⚠️  Increase test coverage to at least 80% (current: 75.3%)
  2. 🚨 Address 1 critical security finding immediately
  3. 📦 Update 3 outdated dependencies
  4. ⚡ Fix 2 high-priority performance issues
```

---

## Artifacts

All DIAGNOSTICADOR outputs are saved as JSON artifacts.

### Artifact Location

```bash
.agents-workspace/artifacts/diagnostics/
└── <workflow-id>-<timestamp>.json
```

### Viewing Artifacts

```bash
# List all diagnostic reports
ls -la .agents-workspace/artifacts/diagnostics/

# View latest report (JSON)
cat .agents-workspace/artifacts/diagnostics/<latest>.json | jq .

# Extract specific data
cat .agents-workspace/artifacts/diagnostics/<latest>.json | \
  jq '.Result.SecurityFindings'
```

### Artifact Structure (JSON)

```json
{
  "AgentType": "diagnosticador",
  "Status": "completed",
  "Result": {
    "CodeQuality": {
      "LinesOfCode": 12345,
      "CyclomaticComplexity": 0,
      "MaintainabilityIndex": 75.0,
      "TechnicalDebt": 0
    },
    "SecurityFindings": [
      {
        "Severity": "high",
        "Category": "vulnerability",
        "Description": "Potential SQL injection",
        "FilePath": "internal/data/query.go",
        "LineNumber": 42,
        "CWE": "CWE-89",
        "Remediation": "Use parameterized queries"
      }
    ],
    "TestCoverage": {
      "LineCoverage": 85.3,
      "BranchCoverage": 78.2,
      "UncoveredFiles": []
    },
    "Dependencies": {
      "Total": 25,
      "Outdated": ["pkg1", "pkg2"],
      "Vulnerable": ["vuln-pkg"],
      "Licenses": {"MIT": 20, "Apache-2.0": 5}
    },
    "Recommendations": [
      "Increase test coverage",
      "Fix security issues"
    ],
    "Summary": "Code Analysis Complete..."
  },
  "Artifacts": [
    ".agents-workspace/artifacts/diagnostics/abc123.json"
  ],
  "Metrics": {
    "security_findings_count": 1,
    "performance_issues_count": 0,
    "test_coverage_percent": 85.3,
    "lines_of_code": 12345
  },
  "StartedAt": "2025-10-23T10:00:00Z",
  "CompletedAt": "2025-10-23T10:00:45Z",
  "Duration": 45234000000
}
```

---

## Configuration

### Configuration File

Location: `.agents-workspace/config/agent_config.yaml`

### Key Configuration Options

#### Quality Gates

```yaml
quality_gates:
  min_coverage_percent: 80.0      # Minimum test coverage
  allow_lint_warnings: false      # Fail on lint warnings
  require_security_scan: true     # Always run gosec
  require_test_pass: true         # All tests must pass
  max_security_critical: 0        # Max critical findings allowed
  max_security_high: 2            # Max high findings allowed
```

#### Service Endpoints

```yaml
maximus:
  eureka_endpoint: "http://localhost:8024"
  consciousness_endpoint: "http://localhost:8022"
```

#### Timeouts

```yaml
agents:
  diagnosticador:
    timeout_seconds: 300  # 5 minutes max
```

### Override Configuration

```bash
# Use custom workspace
vcli agents --workspace /custom/path diagnosticador analyze --targets ./...

# Custom configuration via environment
export VCLI_AGENTS_WORKSPACE=/custom/path
vcli agents diagnosticador analyze --targets ./...
```

---

## Advanced Usage

### Integration with CI/CD

#### GitHub Actions

```yaml
name: Agent Smith Analysis

on: [push, pull_request]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install vcli
        run: |
          curl -sSL https://install.vertice.ai/vcli | bash

      - name: Run DIAGNOSTICADOR
        run: |
          vcli agents diagnosticador analyze --targets ./... --output json > report.json

      - name: Upload Artifacts
        uses: actions/upload-artifact@v3
        with:
          name: agent-smith-report
          path: report.json
```

#### GitLab CI

```yaml
agent-smith:
  stage: test
  script:
    - vcli agents diagnosticador analyze --targets ./...
  artifacts:
    paths:
      - .agents-workspace/artifacts/diagnostics/
```

### Programmatic Access

#### Using Artifacts

```bash
#!/bin/bash
# Extract critical security findings

REPORT=$(ls -t .agents-workspace/artifacts/diagnostics/*.json | head -1)

CRITICAL=$(cat $REPORT | jq -r '.Result.SecurityFindings[] | select(.Severity == "critical") | .Description')

if [ ! -z "$CRITICAL" ]; then
  echo "CRITICAL SECURITY FINDINGS:"
  echo "$CRITICAL"
  exit 1
fi
```

---

## Troubleshooting

### Common Issues

#### Issue: "workspace not initialized"

**Solution**:
```bash
# Workspace is auto-created, but verify:
vcli agents status

# Manually create if needed:
mkdir -p .agents-workspace/{agents,artifacts,workflows,config}
```

#### Issue: "golangci-lint: command not found"

**Solution**:
```bash
# Install golangci-lint
go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest

# Verify installation
which golangci-lint
```

#### Issue: "gosec: command not found"

**Solution**:
```bash
# Install gosec
go install github.com/securego/gosec/v2/cmd/gosec@latest

# Verify installation
which gosec
```

#### Issue: Analysis takes too long

**Solution**:
```bash
# Analyze specific packages instead of ./...
vcli agents diagnosticador analyze --targets ./internal/agents/

# Or increase timeout in config:
# agents.diagnosticador.timeout_seconds: 600
```

---

## Tips & Best Practices

### 1. Run Before Commits

```bash
# Add to .git/hooks/pre-commit
vcli agents diagnosticador analyze --targets ./...
```

### 2. Focus on Changed Files

```bash
# Get changed files
CHANGED=$(git diff --name-only HEAD | grep '\.go$' | xargs dirname | sort -u)

# Analyze only changed packages
for pkg in $CHANGED; do
  vcli agents diagnosticador analyze --targets ./$pkg/
done
```

### 3. Monitor Trends

```bash
# Save reports with timestamps
vcli agents diagnosticador analyze --targets ./... > "report-$(date +%Y%m%d).txt"

# Compare coverage over time
grep "Line Coverage" report-*.txt
```

### 4. Set Quality Gates

Configure minimum standards in `agent_config.yaml`:

```yaml
quality_gates:
  min_coverage_percent: 80.0
  max_security_critical: 0
  max_security_high: 2
```

Then enforce in CI:
```bash
vcli agents diagnosticador analyze --targets ./... || exit 1
```

---

## Next Steps

### After Running DIAGNOSTICADOR

1. **Review Findings** - Check security and performance issues
2. **Fix Critical Items** - Address critical security findings
3. **Improve Coverage** - Add tests for uncovered code
4. **Update Dependencies** - Update outdated packages

### Coming Soon: Full Workflows

```bash
# Full development cycle (Phase 2)
vcli agents run full-cycle --task "Add feature X"

# This will:
# 1. Run DIAGNOSTICADOR (analysis)
# 2. Run ARQUITETO (planning) - requires HITL approval
# 3. Run DEV SENIOR (implementation) - requires HITL approval
# 4. Run TESTER (validation) - requires HITL approval
```

---

## Reference

### Commands Quick Reference

```bash
# List all agents
vcli agents list

# Check status
vcli agents status

# Analyze code (DIAGNOSTICADOR)
vcli agents diagnosticador analyze --targets <path>

# Get help
vcli agents --help
vcli agents diagnosticador --help
```

### Flags

```bash
--workspace string    # Workspace path (default: .agents-workspace)
--output string       # Output format: text|json (default: text)
--targets strings     # Target paths to analyze
--task string         # Task description
```

---

## Support

For issues, questions, or feature requests:

- **GitHub**: https://github.com/verticedev/vcli-go
- **Documentation**: `docs/agents/ARCHITECTURE.md`
- **Slack**: #agent-smith channel

---

**Last Updated**: 2025-10-23
**Status**: DIAGNOSTICADOR fully functional, other agents in development
**Next Release**: Phase 2 - ARQUITETO, DEV SENIOR, TESTER agents
