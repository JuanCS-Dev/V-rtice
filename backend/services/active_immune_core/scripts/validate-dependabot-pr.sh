#!/bin/bash
# Dependabot PR Validation Script
#
# This script validates Dependabot PRs to determine auto-merge eligibility.
# Used by GitHub Actions workflow: dependabot-auto-approve.yml
#
# Exit codes:
#   0 = Auto-merge eligible
#   1 = Manual review required
#   2 = Validation error
#
# Following Doutrina Vértice - Article III: Confiança Zero

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔍 Dependabot PR Validation${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ============================================================================
# CONFIGURATION
# ============================================================================

# Critical packages that NEVER auto-merge (even patches)
CRITICAL_PACKAGES=(
    "fastapi"
    "starlette"
    "uvicorn"
    "sqlalchemy"
    "asyncpg"
    "aiohttp"
    "pydantic"
    "transformers"
    "torch"
    "tensorflow"
    "google-generativeai"
    "anthropic"
    "openai"
)

# CVSS threshold for auto-merge (below this = auto, above = manual)
CVSS_THRESHOLD=7.0

# ============================================================================
# FUNCTIONS
# ============================================================================

# Extract update info from PR title
# Expected format: "chore(deps): bump <package> from <old_version> to <new_version>"
parse_pr_title() {
    local pr_title="$1"

    # Extract package name
    PACKAGE_NAME=$(echo "$pr_title" | grep -oP 'bump \K[a-zA-Z0-9_-]+' || echo "")

    # Extract old version
    OLD_VERSION=$(echo "$pr_title" | grep -oP 'from \K[0-9]+\.[0-9]+\.[0-9]+' || echo "")

    # Extract new version
    NEW_VERSION=$(echo "$pr_title" | grep -oP 'to \K[0-9]+\.[0-9]+\.[0-9]+' || echo "")

    if [ -z "$PACKAGE_NAME" ] || [ -z "$OLD_VERSION" ] || [ -z "$NEW_VERSION" ]; then
        echo -e "${RED}❌ Could not parse PR title${NC}"
        echo "Expected format: 'chore(deps): bump <package> from <old> to <new>'"
        return 2
    fi

    echo -e "Package: ${BLUE}$PACKAGE_NAME${NC}"
    echo -e "Version: $OLD_VERSION → $NEW_VERSION"
    echo ""
}

# Determine update type (patch, minor, major)
get_update_type() {
    local old_version="$1"
    local new_version="$2"

    # Split versions
    IFS='.' read -ra OLD <<< "$old_version"
    IFS='.' read -ra NEW <<< "$new_version"

    local old_major="${OLD[0]}"
    local old_minor="${OLD[1]}"
    local old_patch="${OLD[2]}"

    local new_major="${NEW[0]}"
    local new_minor="${NEW[1]}"
    local new_patch="${NEW[2]}"

    if [ "$new_major" != "$old_major" ]; then
        echo "major"
    elif [ "$new_minor" != "$old_minor" ]; then
        echo "minor"
    elif [ "$new_patch" != "$old_patch" ]; then
        echo "patch"
    else
        echo "unknown"
    fi
}

# Check if package is on critical list
is_critical_package() {
    local package="$1"

    for critical in "${CRITICAL_PACKAGES[@]}"; do
        if [ "$package" = "$critical" ]; then
            return 0  # Is critical
        fi
    done

    return 1  # Not critical
}

# Check CVE severity from PR body
# Dependabot includes CVE info in PR description
check_cve_severity() {
    local pr_body="$1"

    # Try to extract CVSS score from PR body
    # Dependabot format: "CVSS score: 7.5"
    CVSS_SCORE=$(echo "$pr_body" | grep -oP 'CVSS score: \K[0-9]+\.[0-9]+' || echo "0.0")

    # Also check for CVE IDs
    CVE_COUNT=$(echo "$pr_body" | grep -c 'CVE-' || echo "0")

    echo -e "CVE Count: $CVE_COUNT"
    echo -e "CVSS Score: $CVSS_SCORE"
    echo ""

    # If CVSS >= threshold, require manual review
    if (( $(echo "$CVSS_SCORE >= $CVSS_THRESHOLD" | bc -l) )); then
        return 1  # Manual review required
    fi

    return 0  # Auto-merge eligible
}

# ============================================================================
# MAIN VALIDATION LOGIC
# ============================================================================

main() {
    # Get PR info from environment or arguments
    PR_TITLE="${1:-${PR_TITLE:-}}"
    PR_BODY="${2:-${PR_BODY:-}}"
    PR_AUTHOR="${3:-${PR_AUTHOR:-}}"

    if [ -z "$PR_TITLE" ]; then
        echo -e "${RED}❌ PR_TITLE not provided${NC}"
        echo "Usage: $0 <pr_title> [pr_body] [pr_author]"
        exit 2
    fi

    # Verify PR is from Dependabot
    if [[ "$PR_AUTHOR" != *"dependabot"* ]]; then
        echo -e "${YELLOW}⚠️  PR is not from Dependabot${NC}"
        echo "Author: $PR_AUTHOR"
        echo ""
        echo -e "${YELLOW}→ MANUAL REVIEW REQUIRED${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓${NC} PR is from Dependabot"
    echo ""

    # Parse PR title
    parse_pr_title "$PR_TITLE"

    # Determine update type
    UPDATE_TYPE=$(get_update_type "$OLD_VERSION" "$NEW_VERSION")
    echo -e "Update type: ${BLUE}$UPDATE_TYPE${NC}"
    echo ""

    # ========================================================================
    # VALIDATION RULES
    # ========================================================================

    # Rule 1: Only patches are eligible for auto-merge
    if [ "$UPDATE_TYPE" != "patch" ]; then
        echo -e "${YELLOW}⚠️  Update type is $UPDATE_TYPE (not patch)${NC}"
        echo ""
        echo -e "${YELLOW}→ MANUAL REVIEW REQUIRED${NC}"
        echo "Reason: Minor and major updates require human approval"
        exit 1
    fi

    echo -e "${GREEN}✓${NC} Update type is patch"
    echo ""

    # Rule 2: Critical packages require manual review even for patches
    if is_critical_package "$PACKAGE_NAME"; then
        echo -e "${YELLOW}⚠️  Package '$PACKAGE_NAME' is on critical list${NC}"
        echo ""
        echo -e "${YELLOW}→ MANUAL REVIEW REQUIRED${NC}"
        echo "Reason: Critical packages require human validation"
        exit 1
    fi

    echo -e "${GREEN}✓${NC} Package is not on critical list"
    echo ""

    # Rule 3: High severity CVEs require manual review
    if [ -n "$PR_BODY" ]; then
        if ! check_cve_severity "$PR_BODY"; then
            echo -e "${YELLOW}⚠️  CVE severity >= $CVSS_THRESHOLD${NC}"
            echo ""
            echo -e "${YELLOW}→ MANUAL REVIEW REQUIRED${NC}"
            echo "Reason: High severity vulnerabilities need security team review"
            exit 1
        fi

        echo -e "${GREEN}✓${NC} No high-severity CVEs detected"
        echo ""
    fi

    # Rule 4: CI must pass (checked by GitHub Actions, not here)
    echo -e "${BLUE}ℹ${NC}  CI validation will be checked by GitHub Actions"
    echo ""

    # ========================================================================
    # DECISION
    # ========================================================================

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${GREEN}✅ AUTO-MERGE ELIGIBLE${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "This PR meets all criteria for auto-merge:"
    echo "  ✓ From Dependabot"
    echo "  ✓ Patch update (x.y.Z)"
    echo "  ✓ Not a critical package"
    echo "  ✓ CVSS < $CVSS_THRESHOLD"
    echo ""
    echo "Next steps:"
    echo "  1. Wait for CI to pass"
    echo "  2. Auto-approve via GitHub Actions"
    echo "  3. Auto-merge with squash commit"
    echo ""

    exit 0
}

# ============================================================================
# SCRIPT ENTRY POINT
# ============================================================================

# Handle different invocation modes
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    # Script is being executed directly
    main "$@"
fi

# Export functions for testing
export -f parse_pr_title
export -f get_update_type
export -f is_critical_package
export -f check_cve_severity
