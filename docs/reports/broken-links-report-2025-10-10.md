# 📎 Broken Links Report

**Date**: 2025-10-10  
**Status**: 🟡 Partial Fix Applied  
**Tool**: check-broken-links.py + fix-broken-links.py

---

## 📊 Summary

### Before Automated Fix
- **Total links**: 284
- **Broken**: 43 (84.9% success)
- **Files affected**: 17

### After Automated Fix
- **Total links**: 284
- **Broken**: 32 (88.7% success)
- **Fixed automatically**: 11 links in 5 files
- **Remaining manual fixes**: 32 links in 17 files

**Improvement**: +3.8% success rate

---

## ✅ Automated Fixes Applied

Fixed in 5 files by mapping old→new paths:

1. **README.md** - 3 links fixed
   - ETHICAL_AI_EXECUTIVE_SUMMARY.md → docs/reports/ethical-ai-executive-summary.md
   - PHASE_4_1_DP_COMPLETE.md → docs/phases/completed/phase-4-1-differential-privacy.md
   - PHASE_5_HITL_COMPLETE.md → docs/phases/completed/phase-5-human-in-the-loop.md

2. **docs/guides/dependency-framework-rollout.md** - 1 link
   - DEPENDENCY_GOVERNANCE_FRAMEWORK.md → docs/architecture/dependency-governance-framework.md

3. **docs/reports/dependency-framework-100-percent.md** - 3 links
   - DEPENDENCY_GOVERNANCE_FRAMEWORK.md → relative path
   - DEPENDENCY_FRAMEWORK_COMPLETE_REPORT.md → relative path
   - DEPENDENCY_FRAMEWORK_VALIDATION_REPORT.md → relative path

4. **docs/reports/tier-1-rollout.md** - 2 links
   - DEPENDENCY_GOVERNANCE_FRAMEWORK.md → relative path
   - DEPENDENCY_FRAMEWORK_ROLLOUT_GUIDE.md → relative path

5. **docs/reports/validations/dependency-framework-validation.md** - 2 links
   - DEPENDENCY_GOVERNANCE_FRAMEWORK.md → relative path
   - DEPENDENCY_FRAMEWORK_COMPLETE_REPORT.md → relative path

---

## ⚠️ Remaining Manual Fixes (32 links)

### Priority 1: README.md (3 links)
```
Line 359: vcli-go/internal/k8s/apply_test.go (file doesn't exist)
Line 363: backend/services/hcl_planner_service/app/core/planner.py (file doesn't exist)
Line 455: LICENSE (file doesn't exist - create or remove link)
```

**Action**: Verify if files exist or remove dead links.

### Priority 2: Architecture Docs (5 links)

**docs/01-ARCHITECTURE/diagrams/README.md**
```
Line 315: ../README.md (should be ../../README.md)
Line 316: ../../04-API/ (verify path)
Line 318: ../../07-DEVELOPMENT/ (verify path)
```

**docs/architecture/api-documentation.md**
```
Line 44, 278: templates/fastapi_service_template.py (find correct path)
```

**Action**: Update relative paths or find correct targets.

### Priority 3: Legacy Docs Needing Update (11 links)

**docs/02-MAXIMUS-AI/ETHICAL_AI_INTEGRATION_GUIDE.md**
- 2 links to old policy docs

**docs/architecture/maximus/ai-3-deployment.md**
- 1 link to roadmap doc

**docs/reports/dependency-framework-100-percent.md**
- 2 links to backend/services paths

**docs/reports/tier-1-rollout.md**
- 1 link to backend service

**docs/reports/validations/dependency-framework-validation.md**
- 2 links to backend service docs

**docs/10-MIGRATION/** guides
- 4 links to templates and CI files

**Action**: Find files in backend/ or update to correct paths.

### Priority 4: False Positives / Edge Cases (13 links)

**Regex patterns mistaken as links:**
```
docs/01-ARQUITETURA/VERTICE_CLI_TERMINAL_BLUEPRINT.md:687
docs/reports/security/security-hardening.md:242, 501
  → [?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9]] (regex, not a link)
```

**Placeholder links:**
```
docs/07-RELATORIOS/FASE_3_TOOL_EXPANSION.md:1201 - [**tool_input]
docs/cGPT/PLANO_SESSAO_03_APROVACAO.md:319-322 - [...] ellipsis
```

**Action**: Low priority - these are intentional or documentation artifacts.

---

## 🛠️ Tools Created

### check-broken-links.py
Location: `scripts/testing/check-broken-links.py`

**Features:**
- Scans all markdown files in docs/ and root
- Extracts internal links [text](path)
- Resolves relative paths
- Suggests fixes when similar files found
- Detailed reporting by file

**Usage:**
```bash
./scripts/testing/check-broken-links.py
```

### fix-broken-links.py
Location: `scripts/maintenance/fix-broken-links.py`

**Features:**
- Automatic fixing of known mappings (old→new paths)
- Dry-run mode for safety
- Calculates relative paths correctly
- Handles both direct and ./relative references

**Usage:**
```bash
# Test first
./scripts/maintenance/fix-broken-links.py --dry-run

# Apply fixes
./scripts/maintenance/fix-broken-links.py
```

---

## 📋 Manual Fix Plan

### Phase 1: Verify Files (Priority 1)
```bash
# Check if files exist
ls vcli-go/internal/k8s/apply_test.go
ls backend/services/hcl_planner_service/app/core/planner.py
ls LICENSE

# If missing, remove from README.md or create LICENSE
```

### Phase 2: Update Architecture Docs (Priority 2)
- Review docs/01-ARCHITECTURE/diagrams/README.md paths
- Find correct location for fastapi_service_template.py
- Update all architecture doc links

### Phase 3: Update Legacy References (Priority 3)
- Search for files in backend/services/
- Update migration guides with correct template paths
- Verify MAXIMUS roadmap location

### Phase 4: Cleanup False Positives (Priority 4)
- Document regex patterns that look like links
- Consider escaping or formatting differently

---

## 📈 Impact

### Positive
- ✅ 88.7% of links now working
- ✅ Automated tools for future maintenance
- ✅ Clear report of remaining issues
- ✅ Documented manual fix plan

### Remaining Work
- ⏳ 32 links need manual review
- ⏳ 3 high-priority README fixes
- ⏳ Backend service path validation

---

## 🎯 Recommendations

### Immediate
1. Fix Priority 1 links in README.md (5 min)
2. Verify backend service files exist
3. Create LICENSE file if missing

### Short-term
1. Fix architecture doc paths (15 min)
2. Update legacy doc references (20 min)
3. Run link checker again

### Long-term
1. Add pre-commit hook for link checking
2. Include link validation in CI/CD
3. Regular quarterly link audits

---

## 🔄 Maintenance

### Weekly
- Run check-broken-links.py after major changes

### Monthly
- Full audit with manual review
- Update mappings in fix-broken-links.py

### Quarterly
- Review false positives
- Improve detection patterns

---

**Status**: 🟡 In Progress (11/43 fixed automatically)  
**Next**: Manual fixes for remaining 32 links  
**Tools**: ✅ Automated checker and fixer deployed
