# Dependency Emergency Response Runbook

**Version**: 1.0.0
**Last Updated**: 2025-10-06
**Owner**: Security & Infrastructure Team

---

## Table of Contents

1. [When to Use This Runbook](#when-to-use-this-runbook)
2. [Incident Severity Levels](#incident-severity-levels)
3. [P0 - Critical Response (CVSS >= 9.0)](#p0---critical-response-cvss--90)
4. [P1 - High Priority Response (CVSS >= 7.0)](#p1---high-priority-response-cvss--70)
5. [Communication Templates](#communication-templates)
6. [Rollback Procedures](#rollback-procedures)
7. [Post-Mortem Template](#post-mortem-template)

---

## When to Use This Runbook

Activate this emergency runbook when:

- ✅ **CVSS >= 9.0** vulnerability detected in production dependencies
- ✅ **CVSS >= 7.0** with **public exploit** available
- ✅ **Active exploitation** detected in the wild
- ✅ **Customer data** potentially exposed
- ✅ **GitHub Security Advisory** marked as CRITICAL

**Do NOT use for**:
- CVSS < 7.0 without exploit (follow normal SLA)
- Planned dependency updates
- Dev/test environment issues

---

## Incident Severity Levels

| Level | Criteria | Response Time | Team |
|-------|---------|---------------|------|
| **P0 - Critical** | CVSS >= 9.0 + exploit | 2 hours | All hands |
| **P1 - High** | CVSS >= 7.0 + exploit | 8 hours | Security + Backend |
| **P2 - Medium** | CVSS >= 7.0, no exploit | 72 hours | Backend |

---

## P0 - Critical Response (CVSS >= 9.0)

### Phase 1: CONTAINMENT (Hour 0-2)

#### 1.1 Incident Declaration

```bash
# Create incident channel
# Slack command: /incident-create cve-YYYY-MM-DD

# Template message:
🚨 P0 INCIDENT: Critical Dependency Vulnerability

CVE ID: CVE-YYYY-XXXXX
Package: <package-name>==<version>
CVSS Score: X.X
Service: active-immune-core

Status: CONTAINMENT
Incident Commander: @<name>
```

#### 1.2 Code Freeze

```bash
# GitHub: Protect main branch
gh api repos/:owner/:repo/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":[]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":2}' \
  --field restrictions=null

# Notify team
echo "🔒 CODE FREEZE: Main branch protected until CVE-YYYY-XXXXX resolved"
```

#### 1.3 Blast Radius Assessment

**Questions to answer**:
- [ ] Which services use the vulnerable package?
- [ ] Is the vulnerable code path exercised in production?
- [ ] Can we isolate affected services via firewall/network rules?
- [ ] Are there existing WAF/IDS rules that might mitigate?

```bash
# Find all usages
cd /home/juan/vertice-dev
grep -r "<package-name>" backend/services/*/requirements.txt

# Check if code path is active
grep -r "import <vulnerable-module>" backend/services/active_immune_core/
```

#### 1.4 Decision Matrix

| Scenario | Action | Priority |
|----------|--------|----------|
| Patch available + Compatible | **HOTFIX** | 1 |
| Patch available + Breaking | **HOTFIX + Code changes** | 2 |
| No patch + Workaround exists | **WORKAROUND + Whitelist** | 3 |
| No patch + No workaround | **ROLLBACK to last safe version** | 4 |

**Decision**: [  ] HOTFIX  [  ] WORKAROUND  [  ] ROLLBACK

---

### Phase 2: REMEDIATION (Hour 2-4)

#### 2.1 Create Hotfix Branch

```bash
cd /home/juan/vertice-dev/backend/services/active_immune_core

# Create hotfix branch
git checkout main
git pull origin main
git checkout -b hotfix/cve-YYYY-XXXXX

# Update package
vim requirements.txt
# Change: vulnerable-package==1.2.3
# To:     vulnerable-package==1.2.4  (patched version)

# Regenerate lock file
pip-compile requirements.txt --output-file requirements.txt.lock --upgrade

# Install and test locally
pip install -r requirements.txt.lock --no-deps
```

#### 2.2 Run Test Suite

```bash
# Run full test suite
python -m pytest tests/ -v --tb=short

# Run security audit
bash scripts/dependency-audit.sh

# Confirm CVE is fixed
python3 <<EOF
import pkg_resources
pkg = pkg_resources.get_distribution("vulnerable-package")
print(f"Installed: {pkg.version}")
# Verify: version should be patched
EOF
```

#### 2.3 Deploy to Staging

```bash
# Build Docker image
docker build -t active-immune-core:hotfix-cve-YYYY-XXXXX .

# Deploy to staging
kubectl set image deployment/active-immune-core \
  active-immune-core=active-immune-core:hotfix-cve-YYYY-XXXXX \
  --namespace=staging

# Wait for rollout
kubectl rollout status deployment/active-immune-core -n staging
```

#### 2.4 Smoke Test Staging

**Critical Paths to Test**:
- [ ] Health endpoint: `curl https://staging.example.com/health`
- [ ] Authentication flow
- [ ] Database connectivity
- [ ] External API calls
- [ ] Metric emission

```bash
# Automated smoke test
bash scripts/smoke-test-staging.sh
```

---

### Phase 3: VALIDATION (Hour 4-6)

#### 3.1 Re-Scan for CVE

```bash
cd /home/juan/vertice-dev/backend/services/active_immune_core

# Run dependency audit
bash scripts/dependency-audit.sh

# Expected output: ✅ All security scans passed!
```

#### 3.2 Integration Tests

```bash
# Run integration test suite
python -m pytest tests/integration/ -v

# Run load test (if available)
# k6 run load-tests/smoke.js
```

#### 3.3 Get Approvals

**Required Approvers** (for P0):
- [ ] Tech Lead: @<name>
- [ ] Security Team: @<name>
- [ ] (Optional) CTO: @<name> (if customer data exposure)

**Approval Checklist**:
- [ ] CVE confirmed fixed (re-scan passed)
- [ ] All tests passing
- [ ] Staging validated
- [ ] Rollback plan documented
- [ ] Monitoring dashboards ready

---

### Phase 4: DEPLOYMENT (Hour 6-8)

#### 4.1 Phased Rollout Strategy

```bash
# STAGE 1: Canary (1 pod, 10% traffic)
kubectl patch deployment active-immune-core \
  --patch '{"spec":{"strategy":{"rollingUpdate":{"maxSurge":1,"maxUnavailable":0}}}}' \
  -n production

kubectl set image deployment/active-immune-core \
  active-immune-core=active-immune-core:hotfix-cve-YYYY-XXXXX \
  -n production

# Monitor for 30 minutes
watch kubectl get pods -n production

# Check metrics
# - Error rate: should be < 0.1% increase
# - Latency p99: should be < 5% increase
# - CPU/Memory: should be within normal range
```

**Rollout Gates**:

| Stage | Traffic | Duration | Rollback Trigger |
|-------|---------|----------|------------------|
| Canary | 10% | 30 min | Error rate > 0.1% |
| Stage 2 | 50% | 30 min | Error rate > 0.05% |
| Full | 100% | 1 hour | Error rate > 0.02% |

#### 4.2 Monitor Deployment

**Metrics to Watch**:
```bash
# Error rates (Prometheus)
rate(http_requests_total{status=~"5.."}[5m])

# Latency (Prometheus)
histogram_quantile(0.99, http_request_duration_seconds_bucket)

# Logs (Loki/CloudWatch)
kubectl logs -f deployment/active-immune-core -n production --tail=100
```

**Rollback Trigger Conditions**:
- ❌ Error rate increases > 0.1%
- ❌ P99 latency increases > 10%
- ❌ New exceptions in logs
- ❌ Database connection failures

#### 4.3 Complete Rollout

```bash
# If all stages pass, scale to 100%
kubectl scale deployment active-immune-core --replicas=3 -n production

# Verify all pods healthy
kubectl get pods -n production | grep active-immune-core

# Update GitHub issue
gh issue comment <issue-number> --body "✅ Hotfix deployed to production successfully

Deployment completed at $(date -u)
All metrics within normal range
Monitoring for 24h"
```

---

### Phase 5: POST-MORTEM (Hour 8-24)

#### 5.1 Incident Report

**Template**: Copy from [Post-Mortem Template](#post-mortem-template)

**Required Sections**:
- Timeline of events
- Root cause analysis
- Impact assessment (customers, data, services)
- What went well
- What went wrong
- Action items with owners

#### 5.2 Update Policies

**Policy Updates**:
- [ ] Add package to critical list (if not already)
- [ ] Update monitoring thresholds
- [ ] Document new runbook procedures
- [ ] Schedule team training

#### 5.3 Communicate to Stakeholders

```markdown
## Post-Incident Summary: CVE-YYYY-XXXXX

**Incident ID**: INC-YYYY-MM-DD
**Severity**: P0 - Critical
**Duration**: X hours (HH:MM to HH:MM UTC)
**Impact**: [None | Limited | Significant]

### What Happened
<Brief description>

### What We Did
<Actions taken>

### Customer Impact
<None | X customers affected | Data exposure: None>

### Next Steps
<Preventive measures>

Questions? Contact #security-team
```

---

## P1 - High Priority Response (CVSS >= 7.0)

**Similar to P0 but with relaxed timelines**:

- **Containment**: 2 hours (vs 2h)
- **Remediation**: 4 hours (vs 2h)
- **Validation**: 4 hours (vs 2h)
- **Deployment**: Phased rollout (same as P0)

**Key Differences**:
- No immediate code freeze (but PR velocity reduced)
- Can schedule deployment during business hours
- Single approver required (Tech Lead OR Security)

---

## Communication Templates

### 1. Incident Kick-Off Message

```
🚨 P0 INCIDENT DECLARED

CVE: CVE-YYYY-XXXXX
Package: <package>==<version>
CVSS: X.X (CRITICAL)
Exploit: [Public | None]

Incident Commander: @<name>
War Room: #incident-cve-YYYY-MM-DD

Status: CONTAINMENT
ETA: 2 hours
Next Update: HH:MM UTC

Action Items:
- @security: Assess blast radius
- @devops: Prepare staging environment
- @backend: Identify code usage

Updates every 30 minutes.
```

### 2. Hourly Status Update

```
📊 INCIDENT UPDATE (Hour X/8)

CVE-YYYY-XXXXX Status: [CONTAINMENT | REMEDIATION | VALIDATION | DEPLOYMENT]

✅ Completed:
- <task 1>
- <task 2>

🔄 In Progress:
- <task 3> (ETA: HH:MM)

❌ Blocked:
- <none | blocker description>

Next Milestone: <description> (ETA: HH:MM)
```

### 3. Resolution Message

```
✅ INCIDENT RESOLVED

CVE-YYYY-XXXXX has been successfully patched and deployed.

Timeline:
- Detected: HH:MM UTC
- Patched: HH:MM UTC
- Deployed: HH:MM UTC
- Total Duration: X hours

Impact: None (or: X customers, Y transactions)

Hotfix: <git commit hash>
Post-Mortem: <link to document>

Thank you @team for rapid response.
```

---

## Rollback Procedures

### Scenario 1: Rollback Docker Image

```bash
# Get previous image tag
kubectl rollout history deployment/active-immune-core -n production

# Rollback to previous revision
kubectl rollout undo deployment/active-immune-core -n production

# Verify rollback
kubectl rollout status deployment/active-immune-core -n production
```

### Scenario 2: Rollback Git Commit

```bash
# Revert hotfix commit
git revert <commit-hash>

# Push to trigger CI/CD
git push origin main

# Or: Force push (if safe)
git reset --hard HEAD~1
git push origin main --force
```

### Scenario 3: Emergency Database Restore

**DO NOT PERFORM WITHOUT CTO APPROVAL**

```bash
# This is destructive - ensure no other option exists
# Contact DBA team immediately
```

---

## Post-Mortem Template

```markdown
# Post-Mortem: CVE-YYYY-XXXXX

**Date**: YYYY-MM-DD
**Incident ID**: INC-YYYY-MM-DD
**Severity**: P0 - Critical
**Duration**: X hours
**Author**: <name>

## Executive Summary

<2-3 sentence summary of what happened and how it was resolved>

## Timeline (UTC)

- **HH:MM** - CVE detected by <source>
- **HH:MM** - Incident declared, war room created
- **HH:MM** - Hotfix branch created
- **HH:MM** - Deployed to staging
- **HH:MM** - Deployed to production (canary)
- **HH:MM** - Full production rollout
- **HH:MM** - Incident resolved

## Root Cause

<Why did this vulnerability make it to production?>

## Impact Assessment

- **Customers Affected**: X (or None)
- **Data Exposure**: None (or description)
- **Service Downtime**: None (or X minutes)
- **Revenue Impact**: None (or $X)

## What Went Well

- ✅ <thing 1>
- ✅ <thing 2>

## What Went Wrong

- ❌ <thing 1>
- ❌ <thing 2>

## Action Items

| Action | Owner | Deadline | Status |
|--------|-------|----------|--------|
| Update critical package list | Security | YYYY-MM-DD | Pending |
| Add monitoring alert | DevOps | YYYY-MM-DD | Pending |
| Team training session | TechLead | YYYY-MM-DD | Pending |

## Lessons Learned

<Key takeaways>
```

---

## Related Documents

- [DEPENDENCY_POLICY.md](./DEPENDENCY_POLICY.md) - Formal governance policy
- [README.md](./README.md) - Developer quick start
- [scripts/dependency-audit.sh](./scripts/dependency-audit.sh) - Audit tooling

---

**Questions?** Contact `#security-team` or create a GitHub Issue.
