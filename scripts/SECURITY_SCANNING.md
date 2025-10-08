# Vértice Platform - Security Scanning Guide

Comprehensive guide for running security scans on the Vértice codebase.

## Quick Start

```bash
# Run all security scans (screen output)
./scripts/security-scan.sh

# Generate detailed reports
./scripts/security-scan.sh --report

# Strict mode (fail CI on issues)
./scripts/security-scan.sh --strict
```

---

## Security Tools

### 1. **Bandit** - Python Code Security Scanner

Scans Python code for common security issues and vulnerabilities.

#### Usage

```bash
# Scan entire backend
bandit -r backend/ -c .bandit

# Generate HTML report
bandit -r backend/ -c .bandit -f html -o reports/bandit-report.html

# Generate JSON report (for CI integration)
bandit -r backend/ -c .bandit -f json -o reports/bandit-report.json

# Scan specific service
bandit -r backend/services/maximus_core_service/ -c .bandit
```

#### Configuration

- **Config File**: `.bandit` (project root)
- **Exclusions**: tests/, LEGADO/, node_modules/, etc.
- **Skipped Tests**:
  - `B101`: assert_used (common in tests)
  - `B601`: paramiko_calls (intentional in offensive tools)

#### Common Issues

| Code | Description | Severity | Fix |
|------|-------------|----------|-----|
| B201 | Flask debug mode | HIGH | Set `debug=False` in production |
| B501 | Weak SSL/TLS protocols | MEDIUM | Use TLS 1.2+ |
| B506 | YAML load without safe_load | MEDIUM | Use `yaml.safe_load()` |
| B608 | Possible SQL injection | HIGH | Use parameterized queries |
| B703 | Command injection | HIGH | Use `subprocess` with list args |

---

### 2. **Safety** - Dependency Vulnerability Scanner

Scans Python dependencies for known security vulnerabilities using the PyUp.io Safety DB.

#### Usage

```bash
# Check all dependencies
safety check

# Generate JSON report
safety check --json --output reports/safety-report.json

# Check specific requirements file
safety check -r backend/services/maximus_core_service/requirements.txt

# Ignore specific vulnerabilities (use cautiously)
safety check --ignore 12345,67890
```

#### Configuration

- **API Key**: Set `SAFETY_API_KEY` environment variable for full scans
- **Free Tier**: Limited to recent vulnerabilities
- **Database**: PyUp.io Safety DB (updated daily)

#### Interpreting Results

```json
{
  "package": "requests",
  "vulnerable": "2.25.0",
  "installed": "2.25.0",
  "description": "CVE-2021-12345: SSL verification bypass",
  "id": "12345",
  "more_info_url": "https://pyup.io/vulnerabilities/..."
}
```

**Actions**:
1. Upgrade to patched version: `pip install --upgrade requests`
2. If no patch available: Consider alternative packages
3. If risk acceptable: Document in `SECURITY.md` and use `--ignore`

---

### 3. **pip-audit** - Python Package Vulnerability Audit

Audits Python packages for known vulnerabilities using the OSV database.

#### Usage

```bash
# Audit installed packages
pip-audit

# Generate JSON report
pip-audit --format json --output reports/pip-audit.json

# Generate Markdown report
pip-audit --format markdown > reports/pip-audit.md

# Audit requirements file
pip-audit -r requirements.txt

# Dry-run (no changes)
pip-audit --dry-run
```

#### Configuration

- **Database**: OSV (Open Source Vulnerabilities)
- **Supports**: PyPI, Conda, etc.
- **Auto-fix**: `pip-audit --fix` (experimental)

#### Example Output

```
Found 2 known vulnerabilities in 2 packages

Name    Version  ID                  Fix Versions
------  -------  ------------------  -------------
urllib3 1.25.11  PYSEC-2021-59       1.26.5
jinja2  2.11.3   GHSA-g3rq-g295-4j3m 2.11.3, 3.0.0
```

---

## CI/CD Integration

### GitHub Actions

```yaml
name: Security Scan

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements-dev.txt

      - name: Run security scans
        run: ./scripts/security-scan.sh --report --strict

      - name: Upload reports
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: security-reports
          path: reports/security/
```

### GitLab CI

```yaml
security_scan:
  stage: test
  script:
    - pip install -r requirements-dev.txt
    - ./scripts/security-scan.sh --report --strict
  artifacts:
    paths:
      - reports/security/
    when: always
```

---

## Pre-Commit Integration

Add to `.pre-commit-config.yaml`:

```yaml
# Bandit - security linter
- repo: https://github.com/PyCQA/bandit
  rev: 1.7.7
  hooks:
    - id: bandit
      args: ['-c', '.bandit', '-r', 'backend/', '--skip', 'B101,B601']
```

---

## Remediation Guidelines

### High Severity Issues

1. **Immediate action required**
2. Create hotfix branch
3. Apply fix and test
4. Deploy ASAP
5. Document in changelog

### Medium Severity Issues

1. Address in next sprint
2. Create GitHub issue with `security` label
3. Track in security backlog
4. Prioritize based on exposure

### Low Severity Issues

1. Address during refactoring
2. Document in technical debt backlog
3. Consider risk vs effort

---

## False Positives

If a finding is a **confirmed false positive**:

1. Document reason in code comment:
   ```python
   # nosec B601 - paramiko required for offensive security module
   import paramiko
   ```

2. Add to `.bandit` skip list (if applicable to entire codebase)

3. Document in `SECURITY.md`

---

## Security Reports

Reports are saved to: `reports/security/`

### Report Types

| Tool | Format | Filename Pattern |
|------|--------|------------------|
| Bandit | JSON | `bandit_YYYYMMDD_HHMMSS.json` |
| Bandit | HTML | `bandit_YYYYMMDD_HHMMSS.html` |
| Bandit | TXT | `bandit_YYYYMMDD_HHMMSS.txt` |
| Safety | JSON | `safety_YYYYMMDD_HHMMSS.json` |
| Safety | TXT | `safety_YYYYMMDD_HHMMSS.txt` |
| pip-audit | JSON | `pip-audit_YYYYMMDD_HHMMSS.json` |
| pip-audit | Markdown | `pip-audit_YYYYMMDD_HHMMSS.md` |

### Viewing HTML Reports

```bash
# Generate and open in browser (macOS)
./scripts/security-scan.sh --report
open reports/security/bandit_*.html

# Linux
xdg-open reports/security/bandit_*.html
```

---

## Best Practices

### 1. **Run Scans Regularly**
- Daily: Automated CI/CD scans
- Weekly: Manual review of reports
- Before release: Full security audit

### 2. **Keep Dependencies Updated**
```bash
# Check for outdated packages
pip list --outdated

# Update specific package
pip install --upgrade package-name

# Update all (use cautiously)
pip install --upgrade -r requirements.txt
```

### 3. **Monitor Security Advisories**
- GitHub Security Advisories
- PyPI Advisory Database
- National Vulnerability Database (NVD)

### 4. **Use Virtual Environments**
```bash
# Isolate project dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 5. **Pin Dependencies**
```
# requirements.txt - pinned versions
requests==2.31.0
pydantic==2.5.0

# requirements-dev.txt - development tools
black>=24.0.0
pytest>=8.0.0
```

---

## Troubleshooting

### "Safety requires API key"

**Solution**: Sign up at https://pyup.io and set:
```bash
export SAFETY_API_KEY="your-api-key"
```

### "Bandit skipping tests"

**Check**: `.bandit` configuration file
```bash
bandit -r backend/ -c .bandit -v  # Verbose output
```

### "pip-audit: package not found"

**Cause**: Package not in OSV database
**Solution**: Check PyPI directly or use Safety instead

---

## Additional Resources

- [Bandit Documentation](https://bandit.readthedocs.io/)
- [Safety Documentation](https://docs.pyup.io/docs)
- [pip-audit Documentation](https://github.com/pypa/pip-audit)
- [OWASP Python Security](https://owasp.org/www-project-python-security/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)

---

## Contact

Security issues: Report to **security@vertice.platform**

**DO NOT** create public GitHub issues for security vulnerabilities.
