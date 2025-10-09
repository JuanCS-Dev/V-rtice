#!/bin/bash
# Dependency Drift Detection Script
#
# This script detects if installed dependencies have drifted from the lock file.
# It's designed to run in CI/CD and pre-commit to catch silent dependency changes.
#
# Following Doutrina Vértice - Article IV: Antifragilidade Deliberada

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Dependency Drift Detection${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

cd "$PROJECT_ROOT"

# Check if lock file exists
if [ ! -f "requirements.txt.lock" ]; then
    echo -e "${RED}❌ Lock file not found!${NC}"
    echo "Expected: requirements.txt.lock"
    echo "Run: uv pip compile requirements.txt -o requirements.txt.lock"
    exit 1
fi

# Generate current dependency snapshot
echo -e "${BLUE}📸 Generating current dependency snapshot...${NC}"
CURRENT_SNAPSHOT="/tmp/current-dependencies-$(date +%s).txt"
uv pip list --format=freeze | sort > "$CURRENT_SNAPSHOT"

# Extract packages from lock file (remove comments and empty lines)
LOCK_SNAPSHOT="/tmp/lock-file-packages-$(date +%s).txt"
grep -v '^#' requirements.txt.lock | grep -v '^$' | grep '==' | sort > "$LOCK_SNAPSHOT"

echo -e "${BLUE}📊 Comparing snapshots...${NC}"
echo ""

# Compare snapshots
DRIFT_DETECTED=false
MISSING_PACKAGES=()
EXTRA_PACKAGES=()
VERSION_MISMATCHES=()

# Check for packages in lock file but missing in current environment
while IFS= read -r lock_package; do
    package_name=$(echo "$lock_package" | cut -d'=' -f1)
    lock_version=$(echo "$lock_package" | cut -d'=' -f3)

    # Search for package in current snapshot
    current_package=$(grep -E "^${package_name}==" "$CURRENT_SNAPSHOT" || echo "")

    if [ -z "$current_package" ]; then
        MISSING_PACKAGES+=("$lock_package (missing)")
        DRIFT_DETECTED=true
    else
        current_version=$(echo "$current_package" | cut -d'=' -f3)
        if [ "$current_version" != "$lock_version" ]; then
            VERSION_MISMATCHES+=("$package_name: lock=$lock_version, current=$current_version")
            DRIFT_DETECTED=true
        fi
    fi
done < "$LOCK_SNAPSHOT"

# Check for extra packages not in lock file
while IFS= read -r current_package; do
    package_name=$(echo "$current_package" | cut -d'=' -f1)

    # Skip pip, setuptools, wheel (build tools)
    if [[ "$package_name" == "pip" || "$package_name" == "setuptools" || "$package_name" == "wheel" ]]; then
        continue
    fi

    # Search for package in lock file
    lock_package=$(grep -E "^${package_name}==" "$LOCK_SNAPSHOT" || echo "")

    if [ -z "$lock_package" ]; then
        EXTRA_PACKAGES+=("$current_package (not in lock)")
        DRIFT_DETECTED=true
    fi
done < "$CURRENT_SNAPSHOT"

# ============================================================================
# REPORT
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BLUE}📋 Drift Detection Report${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ "$DRIFT_DETECTED" = false ]; then
    echo -e "${GREEN}✅ No dependency drift detected!${NC}"
    echo ""
    echo "All installed packages match the lock file exactly."
    echo "Environment is reproducible and deterministic."

    # Cleanup
    rm -f "$CURRENT_SNAPSHOT" "$LOCK_SNAPSHOT"
    exit 0
fi

# Drift detected - show detailed report
echo -e "${RED}❌ Dependency drift detected!${NC}"
echo ""

if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    echo -e "${YELLOW}Missing packages (in lock but not installed):${NC}"
    for pkg in "${MISSING_PACKAGES[@]}"; do
        echo "  - $pkg"
    done
    echo ""
fi

if [ ${#VERSION_MISMATCHES[@]} -gt 0 ]; then
    echo -e "${YELLOW}Version mismatches:${NC}"
    for mismatch in "${VERSION_MISMATCHES[@]}"; do
        echo "  - $mismatch"
    done
    echo ""
fi

if [ ${#EXTRA_PACKAGES[@]} -gt 0 ]; then
    echo -e "${YELLOW}Extra packages (installed but not in lock):${NC}"
    for pkg in "${EXTRA_PACKAGES[@]}"; do
        echo "  - $pkg"
    done
    echo ""
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${RED}Action Required:${NC}"
echo ""
echo "Dependency drift can lead to:"
echo "  • Non-deterministic builds"
echo "  • Silent regressions"
echo "  • Security vulnerabilities"
echo "  • Deployment failures"
echo ""
echo "To fix:"
echo "  1. Review changes in requirements.txt"
echo "  2. Regenerate lock file:"
echo "     uv pip compile requirements.txt -o requirements.txt.lock --upgrade"
echo "  3. Install from lock file:"
echo "     uv pip sync requirements.txt.lock"
echo "  4. Re-run drift check:"
echo "     bash scripts/check-dependency-drift.sh"
echo ""
echo "Snapshots saved:"
echo "  - Current: $CURRENT_SNAPSHOT"
echo "  - Lock:    $LOCK_SNAPSHOT"

exit 1
