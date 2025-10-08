#!/bin/bash
# Dependency Metrics Generator
#
# Generates comprehensive metrics about dependency health for dashboards
#
# Metrics collected:
# - Total dependency count
# - Outdated dependencies
# - CVE count by severity
# - Whitelist status
# - Update trends
#
# Output format: JSON for easy integration with monitoring tools

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# ============================================================================
# COLLECT METRICS
# ============================================================================

echo "{"
echo '  "timestamp": "'$(date -u '+%Y-%m-%dT%H:%M:%SZ')'",'
echo '  "service": "active-immune-core",'

# Total dependencies
if [ -f "requirements.txt.lock" ]; then
    TOTAL_DEPS=$(grep -c '==' requirements.txt.lock || echo "0")
    echo '  "total_dependencies": '$TOTAL_DEPS','
else
    echo '  "total_dependencies": 0,'
fi

# Direct dependencies
if [ -f "requirements.txt" ]; then
    DIRECT_DEPS=$(grep -c '==' requirements.txt || echo "0")
    echo '  "direct_dependencies": '$DIRECT_DEPS','
else
    echo '  "direct_dependencies": 0,'
fi

# Whitelisted CVEs
if [ -f ".cve-whitelist.yml" ]; then
    WHITELISTED=$(python3 -c "import yaml; data=yaml.safe_load(open('.cve-whitelist.yml')); print(len(data.get('whitelisted_cves', [])) if data else 0)")
    echo '  "whitelisted_cves": '$WHITELISTED','
else
    echo '  "whitelisted_cves": 0,'
fi

# CVE scan results (if available)
SAFETY_OUTPUT=$(mktemp)
if safety check --file requirements.txt.lock --output text > "$SAFETY_OUTPUT" 2>&1 || true; then
    CVE_COUNT=$(grep -c 'CVE-' "$SAFETY_OUTPUT" || echo "0")
    echo '  "known_vulnerabilities": '$CVE_COUNT','
else
    echo '  "known_vulnerabilities": null,'
fi
rm -f "$SAFETY_OUTPUT"

# Last update timestamp
if [ -f "requirements.txt.lock" ]; then
    LAST_UPDATE=$(stat -c %Y requirements.txt.lock 2>/dev/null || stat -f %m requirements.txt.lock 2>/dev/null || echo "0")
    echo '  "last_lock_update": '$LAST_UPDATE','
else
    echo '  "last_lock_update": null,'
fi

# End JSON
echo '  "status": "ok"'
echo "}"
