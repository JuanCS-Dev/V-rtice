#!/bin/bash
# CVE Whitelist Expiration Auditor
#
# This script checks for expired or expiring CVE whitelist entries
# and creates GitHub Issues for re-review when needed.
#
# Runs weekly via GitHub Actions (dependency-audit-weekly.yml)
#
# Following Doutrina Vértice - Article IV: Antifragilidade Deliberada

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
WHITELIST_FILE="$PROJECT_ROOT/.cve-whitelist.yml"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🕒 CVE Whitelist Expiration Audit${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

cd "$PROJECT_ROOT"

# ============================================================================
# CHECK WHITELIST
# ============================================================================

if [ ! -f "$WHITELIST_FILE" ]; then
    echo -e "${GREEN}✅ No whitelist file found - nothing to audit${NC}"
    exit 0
fi

# Parse whitelist with Python
AUDIT_RESULT=$(python3 <<'EOF'
import yaml
from datetime import datetime, timedelta
import sys

try:
    with open(".cve-whitelist.yml", "r") as f:
        data = yaml.safe_load(f)

    if not data or "whitelisted_cves" not in data:
        print("EMPTY")
        sys.exit(0)

    cves = data.get("whitelisted_cves", [])

    if len(cves) == 0:
        print("EMPTY")
        sys.exit(0)

    now = datetime.now()
    thirty_days = now + timedelta(days=30)
    ninety_days = now + timedelta(days=90)

    expired = []
    expiring_soon = []
    needs_rereview = []

    for cve in cves:
        cve_id = cve.get("id", "UNKNOWN")
        package = cve.get("package", "UNKNOWN")
        expires_at = cve.get("expires_at")
        owner = cve.get("owner", "security-team")
        approved_at = cve.get("approved_at")
        re_review_date = cve.get("re_review_date")
        re_review_status = cve.get("re_review_status", "pending")

        # Check expiration
        if expires_at:
            expire_date = datetime.strptime(str(expires_at), "%Y-%m-%d")

            if expire_date < now:
                expired.append({
                    "id": cve_id,
                    "package": package,
                    "expires_at": str(expires_at),
                    "owner": owner,
                    "days": (now - expire_date).days
                })
            elif expire_date < thirty_days:
                days_left = (expire_date - now).days
                expiring_soon.append({
                    "id": cve_id,
                    "package": package,
                    "expires_at": str(expires_at),
                    "owner": owner,
                    "days": days_left
                })

        # Check re-review (90 days since approval)
        if re_review_date:
            rereview_date = datetime.strptime(str(re_review_date), "%Y-%m-%d")
            if rereview_date < now and re_review_status == "pending":
                needs_rereview.append({
                    "id": cve_id,
                    "package": package,
                    "re_review_date": str(re_review_date),
                    "owner": owner,
                    "days_overdue": (now - rereview_date).days
                })

    # Output results
    if expired:
        for item in expired:
            print(f"EXPIRED|{item['id']}|{item['package']}|{item['expires_at']}|{item['owner']}|{item['days']}")

    if expiring_soon:
        for item in expiring_soon:
            print(f"EXPIRING|{item['id']}|{item['package']}|{item['expires_at']}|{item['owner']}|{item['days']}")

    if needs_rereview:
        for item in needs_rereview:
            print(f"REREVIEW|{item['id']}|{item['package']}|{item['re_review_date']}|{item['owner']}|{item['days_overdue']}")

    if not expired and not expiring_soon and not needs_rereview:
        print("OK")

except Exception as e:
    print(f"ERROR|{e}")
    sys.exit(1)
EOF
)

# ============================================================================
# PROCESS RESULTS
# ============================================================================

declare -a EXPIRED_CVES
declare -a EXPIRING_CVES
declare -a REREVIEW_CVES

while IFS= read -r line; do
    case "$line" in
        EMPTY)
            echo -e "${GREEN}✅ Whitelist is empty - nothing to audit${NC}"
            exit 0
            ;;
        OK)
            echo -e "${GREEN}✅ All CVEs have valid expiration dates${NC}"
            echo "   No re-reviews needed at this time"
            exit 0
            ;;
        EXPIRED|*)
            EXPIRED_CVES+=("${line#EXPIRED|}")
            ;;
        EXPIRING|*)
            EXPIRING_CVES+=("${line#EXPIRING|}")
            ;;
        REREVIEW|*)
            REREVIEW_CVES+=("${line#REREVIEW|}")
            ;;
        ERROR|*)
            echo -e "${RED}❌ Error: ${line#ERROR|}${NC}"
            exit 1
            ;;
    esac
done <<< "$AUDIT_RESULT"

# ============================================================================
# REPORT FINDINGS
# ============================================================================

echo -e "${YELLOW}⚠️  Action required!${NC}"
echo ""

if [ ${#EXPIRED_CVES[@]} -gt 0 ]; then
    echo -e "${RED}🔴 EXPIRED CVEs (must update or remove):${NC}"
    for cve_info in "${EXPIRED_CVES[@]}"; do
        IFS='|' read -ra PARTS <<< "$cve_info"
        cve_id="${PARTS[0]}"
        package="${PARTS[1]}"
        expired_date="${PARTS[2]}"
        owner="${PARTS[3]}"
        days_expired="${PARTS[4]}"
        echo "  - $cve_id ($package) - Expired $days_expired days ago on $expired_date"
        echo "    Owner: $owner"
    done
    echo ""
fi

if [ ${#EXPIRING_CVES[@]} -gt 0 ]; then
    echo -e "${YELLOW}🟡 EXPIRING SOON (< 30 days):${NC}"
    for cve_info in "${EXPIRING_CVES[@]}"; do
        IFS='|' read -ra PARTS <<< "$cve_info"
        cve_id="${PARTS[0]}"
        package="${PARTS[1]}"
        expires_date="${PARTS[2]}"
        owner="${PARTS[3]}"
        days_left="${PARTS[4]}"
        echo "  - $cve_id ($package) - Expires in $days_left days on $expires_date"
        echo "    Owner: $owner"
    done
    echo ""
fi

if [ ${#REREVIEW_CVES[@]} -gt 0 ]; then
    echo -e "${YELLOW}🟠 RE-REVIEW OVERDUE (90 days elapsed):${NC}"
    for cve_info in "${REREVIEW_CVES[@]}"; do
        IFS='|' read -ra PARTS <<< "$cve_info"
        cve_id="${PARTS[0]}"
        package="${PARTS[1]}"
        rereview_date="${PARTS[2]}"
        owner="${PARTS[3]}"
        days_overdue="${PARTS[4]}"
        echo "  - $cve_id ($package) - Re-review overdue by $days_overdue days (was: $rereview_date)"
        echo "    Owner: $owner"
    done
    echo ""
fi

# ============================================================================
# CREATE GITHUB ISSUES (if gh CLI available)
# ============================================================================

if command -v gh &> /dev/null && [ -n "${GITHUB_TOKEN:-}" ]; then
    echo -e "${BLUE}📋 Creating GitHub Issues...${NC}"
    echo ""

    for cve_info in "${EXPIRED_CVES[@]}"; do
        IFS='|' read -ra PARTS <<< "$cve_info"
        cve_id="${PARTS[0]}"
        package="${PARTS[1]}"
        expired_date="${PARTS[2]}"
        owner="${PARTS[3]}"
        days_expired="${PARTS[4]}"

        ISSUE_TITLE="🔴 EXPIRED: CVE Whitelist - $cve_id ($package)"
        ISSUE_BODY=$(cat <<EOFISSUE
## ⚠️  CVE Whitelist Expired

**CVE ID**: $cve_id
**Package**: $package
**Expired on**: $expired_date ($days_expired days ago)
**Owner**: @$owner

### Required Actions

1. **Review the CVE** - Is it still relevant?
   - [ ] Check if vulnerability still applies to our platform
   - [ ] Verify mitigations are still in place
   - [ ] Confirm attack vector is not exposed

2. **Choose one**:
   - [ ] **Update package** to patched version (preferred)
   - [ ] **Extend whitelist** with new justification + expiration
   - [ ] **Remove whitelist** if no longer valid

3. **Update .cve-whitelist.yml**:
   - If extending: Update \`expires_at\` and add \`re_review_justification\`
   - If removing: Delete entry from whitelist

### Files to Update
- \`.cve-whitelist.yml\`
- \`requirements.txt\` (if updating package)
- \`requirements.txt.lock\` (regenerate after changes)

### References
- [DEPENDENCY_POLICY.md](../blob/main/backend/services/active_immune_core/DEPENDENCY_POLICY.md)
- [CVE Details](https://nvd.nist.gov/vuln/detail/$cve_id)

---
Auto-generated by \`audit-whitelist-expiration.sh\`
EOFISSUE
)

        echo "Creating issue for $cve_id..."
        gh issue create \
            --title "$ISSUE_TITLE" \
            --body "$ISSUE_BODY" \
            --label "security,dependencies,whitelist-expired" \
            --assignee "$owner" \
            || echo "  Failed to create issue (may already exist)"
    done

    for cve_info in "${EXPIRING_CVES[@]}"; do
        IFS='|' read -ra PARTS <<< "$cve_info"
        cve_id="${PARTS[0]}"
        package="${PARTS[1]}"
        expires_date="${PARTS[2]}"
        owner="${PARTS[3]}"
        days_left="${PARTS[4]}"

        # Only create issue if < 14 days
        if [ "$days_left" -lt 14 ]; then
            ISSUE_TITLE="🟡 EXPIRING SOON: CVE Whitelist - $cve_id ($package) - $days_left days left"
            ISSUE_BODY=$(cat <<EOFISSUE
## ⚠️  CVE Whitelist Expiring Soon

**CVE ID**: $cve_id
**Package**: $package
**Expires on**: $expires_date ($days_left days remaining)
**Owner**: @$owner

### Action Required

Please review this whitelisted CVE before it expires.

Choose one:
- [ ] **Update package** to patched version
- [ ] **Extend whitelist** with renewed justification
- [ ] **Remove whitelist** if no longer needed

See [DEPENDENCY_POLICY.md](../blob/main/backend/services/active_immune_core/DEPENDENCY_POLICY.md) for process.

---
Auto-generated by \`audit-whitelist-expiration.sh\`
EOFISSUE
)

            echo "Creating expiration warning for $cve_id..."
            gh issue create \
                --title "$ISSUE_TITLE" \
                --body "$ISSUE_BODY" \
                --label "security,dependencies,whitelist-expiring" \
                --assignee "$owner" \
                || echo "  Failed to create issue (may already exist)"
        fi
    done
fi

# ============================================================================
# EXIT CODE
# ============================================================================

if [ ${#EXPIRED_CVES[@]} -gt 0 ]; then
    echo -e "${RED}❌ Audit failed: ${#EXPIRED_CVES[@]} expired CVE(s)${NC}"
    exit 1
elif [ ${#EXPIRING_CVES[@]} -gt 0 ] || [ ${#REREVIEW_CVES[@]} -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Audit warning: Action required soon${NC}"
    exit 0  # Warning only, not blocking
else
    echo -e "${GREEN}✅ Audit passed${NC}"
    exit 0
fi
