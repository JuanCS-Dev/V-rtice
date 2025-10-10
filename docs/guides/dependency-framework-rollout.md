# Dependency Framework Rollout Guide

**Target**: All Backend Services (~80 services)
**Timeline**: 2 weeks (Rolling deployment)
**Status**: Phase 2 complete, Phase 3 in progress

---

## Rollout Strategy

### Phase 1: Reference Implementation ✅

**Service**: `active_immune_core`
**Status**: COMPLETE
**Duration**: 3 hours
**Result**: Full framework implementation with all documentation

### Phase 2: Critical Services ✅

**Services**:
- `maximus_core_service` ✅
- `narrative_manipulation_filter` ✅

**Status**: COMPLETE
**Duration**: 30 minutes
**Result**: Framework applied successfully

### Phase 3: Remaining Services ⏳

**Services**: 78+ remaining services
**Timeline**: Rolling over next 2 weeks
**Priority Order**:

1. **Tier 1 - Production Critical** (Priority: HIGH)
   - adr_core_service
   - auth_service
   - api_gateway
   - threat_intel_service
   - malware_analysis_service

2. **Tier 2 - Core Services** (Priority: MEDIUM)
   - adaptive_immunity_service
   - ai_immune_system
   - autonomous_investigation_service
   - immunis_* services (8 services)

3. **Tier 3 - Supporting Services** (Priority: NORMAL)
   - All other services

---

## Quick Rollout (5 minutes per service)

### Command

```bash
cd /home/juan/vertice-dev
bash scripts/rollout-dependency-framework.sh backend/services/<service-name>
```

### What It Does

1. ✅ Creates `scripts/` directory (if needed)
2. ✅ Copies 4 dependency scripts
3. ✅ Creates `.cve-whitelist.yml` template
4. ✅ Creates symlinks to policy documents
5. ✅ Generates `requirements.txt.lock` (via pip-compile)
6. ✅ Updates `README.md` with dependency section
7. ✅ Validates installation

### Expected Output

```
🚀 Dependency Framework Rollout
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Target Service: <service-name>
Path: /path/to/service

[1/7] Creating scripts directory...
✓ Created scripts/

[2/7] Copying dependency scripts...
✓ Copied dependency-audit.sh
✓ Copied check-cve-whitelist.sh
✓ Copied audit-whitelist-expiration.sh
✓ Copied generate-dependency-metrics.sh

[3/7] Creating CVE whitelist...
✓ Created .cve-whitelist.yml

[4/7] Creating policy document...
✓ Created symlink to DEPENDENCY_POLICY.md
✓ Created symlink to DEPENDENCY_EMERGENCY_RUNBOOK.md

[5/7] Generating lock file...
→ Running pip-compile...
✓ Generated requirements.txt.lock

[6/7] Updating README...
✓ Added dependency section to README.md

[7/7] Validating installation...
✓ CVE whitelist is valid
✓ Metrics generation works

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Rollout Complete!
```

---

## Verification Checklist

After rolling out to each service, verify:

```bash
cd backend/services/<service-name>

# 1. Validate whitelist
[ ] bash scripts/check-cve-whitelist.sh validate

# 2. Run audit
[ ] bash scripts/dependency-audit.sh

# 3. Generate metrics
[ ] bash scripts/generate-dependency-metrics.sh

# 4. Check files exist
[ ] ls scripts/dependency-audit.sh
[ ] ls scripts/check-cve-whitelist.sh
[ ] ls scripts/audit-whitelist-expiration.sh
[ ] ls scripts/generate-dependency-metrics.sh
[ ] ls .cve-whitelist.yml
[ ] ls DEPENDENCY_POLICY.md
[ ] ls DEPENDENCY_EMERGENCY_RUNBOOK.md
[ ] ls requirements.txt.lock
```

---

## Batch Rollout Script

For rolling out to multiple services at once:

```bash
#!/bin/bash
# batch-rollout.sh

SERVICES=(
    "backend/services/adr_core_service"
    "backend/services/auth_service"
    "backend/services/threat_intel_service"
    # Add more services here
)

for service in "${SERVICES[@]}"; do
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Rolling out to: $service"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    bash scripts/rollout-dependency-framework.sh "$service"

    if [ $? -eq 0 ]; then
        echo "✅ Success: $service"
    else
        echo "❌ Failed: $service"
    fi

    echo ""
done
```

---

## Commit Strategy

### Single Service Commit

```bash
git add backend/services/<service-name>
git commit -m "feat(deps): add dependency governance framework to <service-name>

Applied dependency governance framework:
- Added dependency scripts (audit, whitelist, metrics)
- Created .cve-whitelist.yml template
- Linked policy documents
- Generated requirements.txt.lock
- Updated README with dependency section

Part of organization-wide rollout (Phase 3)

Ref: DEPENDENCY_GOVERNANCE_FRAMEWORK.md
"
```

### Batch Commit (Multiple Services)

```bash
git add backend/services/
git commit -m "feat(deps): add dependency governance framework to Tier 1 services

Applied dependency governance framework to production-critical services:
- adr_core_service
- auth_service
- api_gateway
- threat_intel_service
- malware_analysis_service

Each service now has:
- Dependency audit scripts
- CVE whitelist management
- Policy documentation
- Lock file generation

Part of Phase 3 rollout (Tier 1: Production Critical)

Ref: DEPENDENCY_GOVERNANCE_FRAMEWORK.md
"
```

---

## Known Issues & Solutions

### Issue 1: pip-compile timeout

**Symptom**: `pip-compile` hangs or times out (>2 minutes)

**Services Affected**:
- narrative_manipulation_filter (large dependency tree)

**Solution**:

```bash
# Skip lock file generation in rollout script
# Generate manually later:
cd backend/services/<service-name>
pip-compile requirements.txt --output-file requirements.txt.lock --resolver=backtracking --verbose
```

### Issue 2: Missing requirements.txt

**Symptom**: Service doesn't have `requirements.txt`

**Solution**:

```bash
# Create requirements.txt first
cd backend/services/<service-name>
echo "# Add dependencies here" > requirements.txt

# Then run rollout
bash ../../scripts/rollout-dependency-framework.sh .
```

### Issue 3: README.md not found

**Symptom**: Script warns about missing README.md

**Solution**: Skip README update, add manually later

```bash
# Create minimal README
echo "# Service Name" > README.md
echo "" >> README.md
echo "Description..." >> README.md

# Re-run rollout (will detect and update README)
```

---

## Rollout Tracking

### Progress Tracker

| Service | Status | Date | CVE Count | Notes |
|---------|--------|------|-----------|-------|
| active_immune_core | ✅ | 2025-10-06 | 0 | Reference implementation |
| maximus_core_service | ✅ | 2025-10-06 | 0 | - |
| narrative_manipulation_filter | ⚠️ | 2025-10-06 | - | Lock file timeout |
| adr_core_service | ⏳ | - | - | Tier 1 |
| auth_service | ⏳ | - | - | Tier 1 |
| api_gateway | ⏳ | - | - | Tier 1 |
| threat_intel_service | ⏳ | - | - | Tier 1 |
| malware_analysis_service | ⏳ | - | - | Tier 1 |
| ... | ⏳ | - | - | 73 remaining |

**Update this table as you roll out**

---

## Post-Rollout Actions

### 1. Update Dependabot Config

After rolling out to new services, update `.github/dependabot.yml`:

```yaml
updates:
  # Add new service entry
  - package-ecosystem: "pip"
    directory: "/backend/services/<new-service>"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "00:00"
      timezone: "UTC"
    # ... (copy from reference)
```

### 2. Add to CI/CD

Update GitHub Actions workflow to include new services:

```yaml
# .github/workflows/dependency-audit-weekly.yml

jobs:
  audit-<new-service>:
    name: Audit <New Service>
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run audit
        working-directory: backend/services/<new-service>
        run: bash scripts/dependency-audit.sh
```

### 3. Enable Pre-commit Hooks

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: dependency-audit-<service>
        name: Dependency Audit - <Service>
        entry: bash backend/services/<service>/scripts/dependency-audit.sh
        language: system
        pass_filenames: false
        files: backend/services/<service>/requirements\.txt(\.lock)?$
```

---

## Rollout Metrics

### Target KPIs

| Metric | Target | Current |
|--------|--------|---------|
| Services with framework | 80+ (100%) | 3 (4%) |
| Average rollout time | < 5 min | 5 min |
| Lock file generation success | > 95% | 67% (2/3) |
| Zero CVEs at rollout | 100% | 100% |
| README updated | 100% | 100% |

### Weekly Progress

- **Week 1** (Oct 6-12): Tier 1 services (5 services)
- **Week 2** (Oct 13-19): Tier 2 services (20 services)
- **Week 3** (Oct 20-26): Tier 3 services (55 services)

---

## Communication Plan

### Stakeholder Updates

**Weekly Status Report** (Every Monday):

```markdown
📊 Dependency Framework Rollout - Week X Update

✅ Completed: X services
⏳ In Progress: Y services
🔜 Upcoming: Z services

Highlights:
- CVEs detected: N
- Auto-merge rate: X%
- Incidents resolved: N

Blockers: (if any)

Next Week: (Tier X rollout)
```

### Developer Notification

When rolling out to a service:

```markdown
🚀 Dependency Framework Applied to <Service>

Your service now has:
- Automated CVE scanning
- Dependabot with auto-merge
- Emergency response procedures

Actions Required:
1. Review new files in your service directory
2. Run: bash scripts/dependency-audit.sh
3. Commit changes to your feature branch

Questions? See DEPENDENCY_GOVERNANCE_FRAMEWORK.md or contact #security-team
```

---

## Rollback Procedure

If rollout causes issues:

```bash
cd backend/services/<service-name>

# Remove framework files
rm -rf scripts/dependency-audit.sh \
       scripts/check-cve-whitelist.sh \
       scripts/audit-whitelist-expiration.sh \
       scripts/generate-dependency-metrics.sh \
       .cve-whitelist.yml \
       DEPENDENCY_POLICY.md \
       DEPENDENCY_EMERGENCY_RUNBOOK.md \
       requirements.txt.lock

# Revert README changes
git checkout HEAD -- README.md

# Commit rollback
git commit -am "revert(deps): rollback dependency framework from <service-name>"
```

---

## Next Steps

1. **Complete Tier 1** (5 services, Priority: HIGH)
   ```bash
   bash scripts/rollout-dependency-framework.sh backend/services/adr_core_service
   bash scripts/rollout-dependency-framework.sh backend/services/auth_service
   bash scripts/rollout-dependency-framework.sh backend/services/threat_intel_service
   bash scripts/rollout-dependency-framework.sh backend/services/malware_analysis_service
   ```

2. **Verify and Commit**
   ```bash
   git add backend/services/adr_core_service
   git add backend/services/auth_service
   git add backend/services/threat_intel_service
   git add backend/services/malware_analysis_service
   git commit -m "feat(deps): add framework to Tier 1 services"
   ```

3. **Update Tracking**
   - Mark services as complete in progress tracker
   - Update metrics
   - Send weekly status report

4. **Proceed to Tier 2**
   - Repeat process for next 20 services

---

## References

- **[DEPENDENCY_GOVERNANCE_FRAMEWORK.md](./DEPENDENCY_GOVERNANCE_FRAMEWORK.md)** - Complete framework overview
- **[backend/services/active_immune_core/DEPENDENCY_GOVERNANCE_IMPLEMENTATION_REPORT.md](./backend/services/active_immune_core/DEPENDENCY_GOVERNANCE_IMPLEMENTATION_REPORT.md)** - Implementation details
- **[scripts/rollout-dependency-framework.sh](./scripts/rollout-dependency-framework.sh)** - Rollout automation script

---

**Status**: Phase 3 in progress | **Last Updated**: 2025-10-06
