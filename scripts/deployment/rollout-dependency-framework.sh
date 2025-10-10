#!/bin/bash
# Dependency Framework Rollout Script
#
# Applies the dependency governance framework to a target service
#
# Usage:
#   bash scripts/rollout-dependency-framework.sh <service-path>
#
# Example:
#   bash scripts/rollout-dependency-framework.sh backend/services/maximus_core_service

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
RESET='\033[0m'

# Source reference (active_immune_core)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REFERENCE_SERVICE="$PROJECT_ROOT/backend/services/active_immune_core"

# Target service
if [ $# -lt 1 ]; then
    echo -e "${RED}❌ Error: Service path required${RESET}"
    echo "Usage: $0 <service-path>"
    echo "Example: $0 backend/services/maximus_core_service"
    exit 1
fi

TARGET_SERVICE="$PROJECT_ROOT/$1"
SERVICE_NAME="$(basename "$1")"

echo -e "${BLUE}${BOLD}🚀 Dependency Framework Rollout${RESET}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""
echo -e "${BOLD}Target Service:${RESET} $SERVICE_NAME"
echo -e "${BOLD}Path:${RESET} $TARGET_SERVICE"
echo ""

# Validate target service exists
if [ ! -d "$TARGET_SERVICE" ]; then
    echo -e "${RED}❌ Error: Service directory not found: $TARGET_SERVICE${RESET}"
    exit 1
fi

# Validate reference service exists
if [ ! -d "$REFERENCE_SERVICE" ]; then
    echo -e "${RED}❌ Error: Reference service not found: $REFERENCE_SERVICE${RESET}"
    exit 1
fi

cd "$TARGET_SERVICE"

# ============================================================================
# STEP 1: CREATE SCRIPTS DIRECTORY
# ============================================================================

echo -e "${BLUE}[1/7] Creating scripts directory...${RESET}"

if [ ! -d "scripts" ]; then
    mkdir -p scripts
    echo -e "${GREEN}✓${RESET} Created scripts/"
else
    echo -e "${GREEN}✓${RESET} scripts/ already exists"
fi

# ============================================================================
# STEP 2: COPY DEPENDENCY SCRIPTS
# ============================================================================

echo -e "${BLUE}[2/7] Copying dependency scripts...${RESET}"

SCRIPTS=(
    "dependency-audit.sh"
    "check-cve-whitelist.sh"
    "audit-whitelist-expiration.sh"
    "generate-dependency-metrics.sh"
)

for script in "${SCRIPTS[@]}"; do
    if [ -f "$REFERENCE_SERVICE/scripts/$script" ]; then
        cp "$REFERENCE_SERVICE/scripts/$script" "scripts/$script"
        chmod +x "scripts/$script"
        echo -e "${GREEN}✓${RESET} Copied $script"
    else
        echo -e "${YELLOW}⚠️${RESET}  Warning: $script not found in reference service"
    fi
done

# ============================================================================
# STEP 3: CREATE CVE WHITELIST
# ============================================================================

echo -e "${BLUE}[3/7] Creating CVE whitelist...${RESET}"

if [ ! -f ".cve-whitelist.yml" ]; then
    cp "$REFERENCE_SERVICE/.cve-whitelist.yml" ".cve-whitelist.yml"
    echo -e "${GREEN}✓${RESET} Created .cve-whitelist.yml"
else
    echo -e "${GREEN}✓${RESET} .cve-whitelist.yml already exists (skipping)"
fi

# ============================================================================
# STEP 4: CREATE/LINK POLICY DOCUMENT
# ============================================================================

echo -e "${BLUE}[4/7] Creating policy document...${RESET}"

if [ ! -f "DEPENDENCY_POLICY.md" ]; then
    # Create symlink to shared policy
    ln -s "$REFERENCE_SERVICE/DEPENDENCY_POLICY.md" "DEPENDENCY_POLICY.md"
    echo -e "${GREEN}✓${RESET} Created symlink to DEPENDENCY_POLICY.md"
else
    echo -e "${GREEN}✓${RESET} DEPENDENCY_POLICY.md already exists (skipping)"
fi

if [ ! -f "DEPENDENCY_EMERGENCY_RUNBOOK.md" ]; then
    # Create symlink to shared runbook
    ln -s "$REFERENCE_SERVICE/DEPENDENCY_EMERGENCY_RUNBOOK.md" "DEPENDENCY_EMERGENCY_RUNBOOK.md"
    echo -e "${GREEN}✓${RESET} Created symlink to DEPENDENCY_EMERGENCY_RUNBOOK.md"
else
    echo -e "${GREEN}✓${RESET} DEPENDENCY_EMERGENCY_RUNBOOK.md already exists (skipping)"
fi

# ============================================================================
# STEP 5: GENERATE LOCK FILE
# ============================================================================

echo -e "${BLUE}[5/7] Generating lock file...${RESET}"

if [ -f "requirements.txt" ]; then
    if [ ! -f "requirements.txt.lock" ]; then
        # Check if pip-tools is installed
        if command -v pip-compile &> /dev/null; then
            echo -e "${YELLOW}→${RESET} Running pip-compile..."
            pip-compile requirements.txt --output-file requirements.txt.lock --quiet 2>&1 | head -20 || {
                echo -e "${YELLOW}⚠️${RESET}  Warning: pip-compile failed, but continuing..."
            }

            if [ -f "requirements.txt.lock" ]; then
                echo -e "${GREEN}✓${RESET} Generated requirements.txt.lock"
            else
                echo -e "${YELLOW}⚠️${RESET}  Warning: Lock file not generated (manual creation required)"
            fi
        else
            echo -e "${YELLOW}⚠️${RESET}  Warning: pip-tools not installed (run: pip install pip-tools)"
            echo -e "${YELLOW}→${RESET} Manually run: pip-compile requirements.txt --output-file requirements.txt.lock"
        fi
    else
        echo -e "${GREEN}✓${RESET} requirements.txt.lock already exists"
    fi
else
    echo -e "${YELLOW}⚠️${RESET}  Warning: requirements.txt not found (skipping lock file)"
fi

# ============================================================================
# STEP 6: UPDATE README
# ============================================================================

echo -e "${BLUE}[6/7] Updating README...${RESET}"

if [ -f "README.md" ]; then
    # Check if README already has dependency section
    if grep -q "## 📦 Dependency Management" README.md 2>/dev/null; then
        echo -e "${GREEN}✓${RESET} README.md already has dependency section (skipping)"
    else
        echo -e "${YELLOW}→${RESET} Adding dependency section to README.md..."

        # Find insertion point (before Documentation section or at end)
        if grep -q "## 📚 Documentation" README.md; then
            # Insert before Documentation section
            sed -i '/## 📚 Documentation/i\
## 📦 Dependency Management\
\
This service follows **strict dependency governance** to ensure security, stability, and reproducibility.\
\
### Quick Reference\
\
**Check for vulnerabilities**:\
```bash\
bash scripts/dependency-audit.sh\
```\
\
**Add new dependency**:\
```bash\
echo "package==1.2.3" >> requirements.txt\
pip-compile requirements.txt --output-file requirements.txt.lock\
bash scripts/dependency-audit.sh  # Verify no CVEs\
git add requirements.txt requirements.txt.lock\
git commit -m "feat: add package for feature X"\
```\
\
**Update dependency**:\
```bash\
vim requirements.txt  # Update version\
pip-compile requirements.txt --output-file requirements.txt.lock --upgrade\
bash scripts/dependency-audit.sh  # Verify no CVEs\
git commit -am "chore(deps): update package to X.Y.Z"\
```\
\
### Policies & SLAs\
\
📋 **[DEPENDENCY_POLICY.md](./DEPENDENCY_POLICY.md)** - Complete policy documentation\
\
**Key SLAs**:\
- **CRITICAL (CVSS >= 9.0)**: 24 hours\
- **HIGH (CVSS >= 7.0)**: 72 hours\
- **MEDIUM (CVSS >= 4.0)**: 2 weeks\
- **LOW (CVSS < 4.0)**: 1 month\
\
### Available Scripts\
\
| Script | Purpose |\
|--------|---------|\
| `dependency-audit.sh` | Full CVE scan |\
| `check-cve-whitelist.sh` | Validate whitelist |\
| `audit-whitelist-expiration.sh` | Check expired CVEs |\
| `generate-dependency-metrics.sh` | Generate metrics JSON |\
\
See [Active Immune Core README](../active_immune_core/README.md#-dependency-management) for complete documentation.\
\
---\
\
' README.md
            echo -e "${GREEN}✓${RESET} Added dependency section to README.md"
        else
            # Append to end
            cat >> README.md << 'EOF'

---

## 📦 Dependency Management

This service follows **strict dependency governance** to ensure security, stability, and reproducibility.

### Quick Reference

**Check for vulnerabilities**:
```bash
bash scripts/dependency-audit.sh
```

**Add new dependency**:
```bash
echo "package==1.2.3" >> requirements.txt
pip-compile requirements.txt --output-file requirements.txt.lock
bash scripts/dependency-audit.sh  # Verify no CVEs
git add requirements.txt requirements.txt.lock
git commit -m "feat: add package for feature X"
```

### Policies & SLAs

📋 **[DEPENDENCY_POLICY.md](./DEPENDENCY_POLICY.md)** - Complete policy documentation

**Key SLAs**:
- **CRITICAL (CVSS >= 9.0)**: 24 hours
- **HIGH (CVSS >= 7.0)**: 72 hours
- **MEDIUM (CVSS >= 4.0)**: 2 weeks
- **LOW (CVSS < 4.0)**: 1 month

### Available Scripts

| Script | Purpose |
|--------|---------|
| `dependency-audit.sh` | Full CVE scan |
| `check-cve-whitelist.sh` | Validate whitelist |
| `audit-whitelist-expiration.sh` | Check expired CVEs |
| `generate-dependency-metrics.sh` | Generate metrics JSON |

See [Active Immune Core README](../active_immune_core/README.md#-dependency-management) for complete documentation.

EOF
            echo -e "${GREEN}✓${RESET} Appended dependency section to README.md"
        fi
    fi
else
    echo -e "${YELLOW}⚠️${RESET}  Warning: README.md not found (skipping)"
fi

# ============================================================================
# STEP 7: VALIDATE INSTALLATION
# ============================================================================

echo -e "${BLUE}[7/7] Validating installation...${RESET}"

VALIDATION_PASSED=true

# Check scripts are executable
for script in "${SCRIPTS[@]}"; do
    if [ ! -x "scripts/$script" ]; then
        echo -e "${RED}❌${RESET} Script not executable: $script"
        VALIDATION_PASSED=false
    fi
done

# Check whitelist is valid
if [ -f "scripts/check-cve-whitelist.sh" ]; then
    if bash scripts/check-cve-whitelist.sh validate &> /dev/null; then
        echo -e "${GREEN}✓${RESET} CVE whitelist is valid"
    else
        echo -e "${YELLOW}⚠️${RESET}  Warning: CVE whitelist validation failed"
    fi
fi

# Check metrics generation works
if [ -f "scripts/generate-dependency-metrics.sh" ]; then
    if bash scripts/generate-dependency-metrics.sh > /dev/null 2>&1; then
        echo -e "${GREEN}✓${RESET} Metrics generation works"
    else
        echo -e "${YELLOW}⚠️${RESET}  Warning: Metrics generation failed"
    fi
fi

# ============================================================================
# SUMMARY
# ============================================================================

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"

if [ "$VALIDATION_PASSED" = true ]; then
    echo -e "${GREEN}${BOLD}✅ Rollout Complete!${RESET}"
    echo ""
    echo -e "${BOLD}Next Steps:${RESET}"
    echo "1. Run audit: ${YELLOW}bash scripts/dependency-audit.sh${RESET}"
    echo "2. Generate lock: ${YELLOW}pip-compile requirements.txt --output-file requirements.txt.lock${RESET}"
    echo "3. Commit changes: ${YELLOW}git add . && git commit -m \"feat(deps): add dependency governance framework\"${RESET}"
else
    echo -e "${YELLOW}${BOLD}⚠️  Rollout Complete with Warnings${RESET}"
    echo ""
    echo -e "Review warnings above and fix any issues."
fi

echo ""
echo -e "${BOLD}Files Created:${RESET}"
echo "  • scripts/dependency-audit.sh"
echo "  • scripts/check-cve-whitelist.sh"
echo "  • scripts/audit-whitelist-expiration.sh"
echo "  • scripts/generate-dependency-metrics.sh"
echo "  • .cve-whitelist.yml"
echo "  • DEPENDENCY_POLICY.md (symlink)"
echo "  • DEPENDENCY_EMERGENCY_RUNBOOK.md (symlink)"
if [ -f "requirements.txt.lock" ]; then
    echo "  • requirements.txt.lock"
fi
echo ""
