#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# VÉRTICE-MAXIMUS SECRET SCANNING SUITE
# ═══════════════════════════════════════════════════════════════════════════
#
# Comprehensive secret detection before making repository public
#
# Copyright © 2025 Juan Carlos de Souza
# ═══════════════════════════════════════════════════════════════════════════

set -e

REPO_PATH="/home/juan/vertice-dev"
REPORT_DIR="$REPO_PATH/security_audit_reports"
mkdir -p "$REPORT_DIR"

echo "=============================================="
echo "🔒 VÉRTICE-MAXIMUS SECRET SCANNING SUITE"
echo "=============================================="
echo ""
echo "Repository: $REPO_PATH"
echo "Reports: $REPORT_DIR"
echo ""

# ═══════════════════════════════════════════════════════════════════════════
# CUSTOM PATTERN SEARCH (No external dependencies)
# ═══════════════════════════════════════════════════════════════════════════

cd "$REPO_PATH"

echo "[1/8] 🔍 Searching for API keys..."
grep -r -n -E "(api[_-]?key|apikey|api[_-]?secret)[\"'\s]*[:=][\"'\s]*[A-Za-z0-9]{20,}" \
  --exclude-dir={venv,.venv,node_modules,.git,security_audit_reports,.archive,.pytest_cache,htmlcov,dist,build} \
  --exclude="*.md" \
  --exclude="*.log" \
  --exclude="scan_secrets.sh" \
  . > "$REPORT_DIR/01-api-keys-found.txt" 2>/dev/null || echo "  ✅ No generic API keys found"

echo "[2/8] 🔍 Searching for AWS credentials..."
grep -r -n "AKIA[0-9A-Z]{16}" \
  --exclude-dir={venv,.venv,node_modules,.git,security_audit_reports,.archive,.pytest_cache} \
  . > "$REPORT_DIR/02-aws-credentials-found.txt" 2>/dev/null || echo "  ✅ No AWS credentials found"

echo "[3/8] 🔍 Searching for Claude API keys..."
grep -r -n "sk-ant-[A-Za-z0-9_-]{95,}" \
  --exclude-dir={venv,.venv,node_modules,.git,security_audit_reports,.archive} \
  . > "$REPORT_DIR/03-claude-keys-found.txt" 2>/dev/null || echo "  ✅ No Claude API keys found"

echo "[4/8] 🔍 Searching for OpenAI keys..."
grep -r -n "sk-[A-Za-z0-9]{32,}" \
  --exclude-dir={venv,.venv,node_modules,.git,security_audit_reports,.archive} \
  --exclude="scan_secrets.sh" \
  . > "$REPORT_DIR/04-openai-keys-found.txt" 2>/dev/null || echo "  ✅ No OpenAI keys found"

echo "[5/8] 🔍 Searching for Google/Gemini keys..."
grep -r -n "AIza[0-9A-Za-z_-]{35}" \
  --exclude-dir={venv,.venv,node_modules,.git,security_audit_reports,.archive} \
  . > "$REPORT_DIR/05-google-keys-found.txt" 2>/dev/null || echo "  ✅ No Google keys found"

echo "[6/8] 🔍 Searching for private keys..."
grep -r -n "BEGIN.*PRIVATE KEY" \
  --exclude-dir={venv,.venv,node_modules,.git,security_audit_reports,.archive} \
  . > "$REPORT_DIR/06-private-keys-found.txt" 2>/dev/null || echo "  ✅ No private keys found"

echo "[7/8] 🔍 Searching for database passwords..."
grep -r -n -E "(POSTGRES_PASSWORD|MYSQL_PASSWORD|DB_PASSWORD|REDIS_PASSWORD)[\"'\s]*[:=][\"'\s]*[^ ]+" \
  --exclude-dir={venv,.venv,node_modules,.git,security_audit_reports,.archive} \
  --exclude="*.example" \
  --exclude="*.md" \
  . > "$REPORT_DIR/07-db-passwords-found.txt" 2>/dev/null || echo "  ✅ No database passwords found"

echo "[8/8] 🔍 Searching for JWT secrets..."
grep -r -n -E "(JWT_SECRET|SECRET_KEY)[\"'\s]*[:=][\"'\s]*[A-Za-z0-9+/=]{32,}" \
  --exclude-dir={venv,.venv,node_modules,.git,security_audit_reports,.archive} \
  --exclude="*.example" \
  --exclude="*.md" \
  . > "$REPORT_DIR/08-jwt-secrets-found.txt" 2>/dev/null || echo "  ✅ No JWT secrets found"

echo ""
echo "=============================================="
echo "📊 SCANNING COMPLETE!"
echo "=============================================="
echo ""

# ═══════════════════════════════════════════════════════════════════════════
# GENERATE SUMMARY
# ═══════════════════════════════════════════════════════════════════════════

SUMMARY_FILE="$REPORT_DIR/00-SUMMARY.txt"
cat > "$SUMMARY_FILE" <<EOF
═══════════════════════════════════════════════════════════════════════════
VÉRTICE-MAXIMUS SECRET SCANNING SUMMARY
═══════════════════════════════════════════════════════════════════════════

Scan Date: $(date '+%Y-%m-%d %H:%M:%S')
Repository: $REPO_PATH

───────────────────────────────────────────────────────────────────────────
FINDINGS
───────────────────────────────────────────────────────────────────────────

EOF

for report in "$REPORT_DIR"/*.txt; do
  if [ -f "$report" ] && [ "$report" != "$SUMMARY_FILE" ]; then
    filename=$(basename "$report")
    count=$(wc -l < "$report" 2>/dev/null || echo 0)

    if [ "$count" -gt 0 ]; then
      echo "⚠️  $filename: $count occurrences found" >> "$SUMMARY_FILE"
    else
      echo "✅ $filename: No issues" >> "$SUMMARY_FILE"
    fi
  fi
done

cat >> "$SUMMARY_FILE" <<EOF

───────────────────────────────────────────────────────────────────────────
NEXT STEPS
───────────────────────────────────────────────────────────────────────────

1. Review each report file in: $REPORT_DIR
2. For each secret found:
   - If FALSE POSITIVE: Document and ignore
   - If REAL SECRET:
     a) ROTATE the credential immediately
     b) Remove from current code
     c) Remove from git history (use BFG Repo-Cleaner)
3. Re-run this script to verify all secrets removed
4. Do NOT make repository public until all secrets are removed

═══════════════════════════════════════════════════════════════════════════
EOF

cat "$SUMMARY_FILE"

echo ""
echo "📁 Detailed reports saved to:"
for report in "$REPORT_DIR"/*.txt; do
  if [ -f "$report" ]; then
    echo "   - $(basename "$report")"
  fi
done
echo ""
