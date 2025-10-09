#!/usr/bin/env bash
set -euo pipefail

# E2E Simple Test - Validação de Artefatos
# Autor: Juan Carlo de Souza (JuanCS-DEV @github)

REPORTS_DIR="$(pwd)/tests/e2e/reports"
mkdir -p "$REPORTS_DIR"

echo "=== E2E Simple Test Suite v0.9 ==="
echo "Autor: Juan Carlo de Souza"
echo ""

# Test 1: SBOM exists
echo "[Test 1] SBOM Validation"
if [ -f "artifacts/vcli-go/sbom-vcli-go.json" ]; then
  size=$(stat -c%s "artifacts/vcli-go/sbom-vcli-go.json")
  echo "  ✅ SBOM found ($size bytes)"
  echo "PASS" > "$REPORTS_DIR/test1.txt"
else
  echo "  ❌ SBOM not found"
  echo "FAIL" > "$REPORTS_DIR/test1.txt"
fi

# Test 2: Vulnerability report exists
echo "[Test 2] Vulnerability Report"
if [ -f "artifacts/vcli-go/vuln-vcli-go.json" ]; then
  size=$(stat -c%s "artifacts/vcli-go/vuln-vcli-go.json")
  echo "  ✅ Vuln report found ($size bytes)"
  echo "PASS" > "$REPORTS_DIR/test2.txt"
else
  echo "  ❌ Vuln report not found"
  echo "FAIL" > "$REPORTS_DIR/test2.txt"
fi

# Test 3: vcli binary exists
echo "[Test 3] vcli Binary"
if [ -f "vcli-go/bin/vcli" ] && [ -x "vcli-go/bin/vcli" ]; then
  size=$(stat -c%s "vcli-go/bin/vcli")
  echo "  ✅ vcli binary found ($size bytes)"
  echo "PASS" > "$REPORTS_DIR/test3.txt"
else
  echo "  ❌ vcli binary not found or not executable"
  echo "FAIL" > "$REPORTS_DIR/test3.txt"
fi

# Test 4: Latency simulation (CLI execution)
echo "[Test 4] CLI Latency Test"
if [ -x "vcli-go/bin/vcli" ]; then
  start=$(date +%s%N)
  ./vcli-go/bin/vcli --version > /dev/null 2>&1 || true
  end=$(date +%s%N)
  latency=$(( (end - start) / 1000000 ))
  
  if [ $latency -lt 500 ]; then
    echo "  ✅ Latency ${latency}ms (< 500ms threshold)"
    echo "PASS:${latency}ms" > "$REPORTS_DIR/test4.txt"
  else
    echo "  ⚠️  Latency ${latency}ms (> 500ms threshold)"
    echo "WARN:${latency}ms" > "$REPORTS_DIR/test4.txt"
  fi
else
  echo "  ⏭️  SKIP (binary not available)"
  echo "SKIP" > "$REPORTS_DIR/test4.txt"
fi

# Generate report
echo ""
echo "=== Test Results ==="
total=0
passed=0

for i in {1..4}; do
  if [ -f "$REPORTS_DIR/test${i}.txt" ]; then
    result=$(cat "$REPORTS_DIR/test${i}.txt")
    total=$((total + 1))
    if [[ "$result" == "PASS"* ]]; then
      passed=$((passed + 1))
    fi
  fi
done

success_rate=$(( passed * 100 / total ))

cat > "$REPORTS_DIR/e2e-results.json" <<EOF
{
  "timestamp": "$(date -Iseconds)",
  "total_tests": $total,
  "passed": $passed,
  "failed": $((total - passed)),
  "success_rate": $success_rate,
  "details": {
    "sbom": "$(cat $REPORTS_DIR/test1.txt)",
    "vuln_report": "$(cat $REPORTS_DIR/test2.txt)",
    "binary": "$(cat $REPORTS_DIR/test3.txt)",
    "latency": "$(cat $REPORTS_DIR/test4.txt)"
  }
}
EOF

echo "Tests: $passed/$total passed ($success_rate%)"
echo "Report: $REPORTS_DIR/e2e-results.json"
echo ""

if [ $passed -eq $total ]; then
  echo "✅ ALL TESTS PASSED"
  exit 0
else
  echo "⚠️  SOME TESTS FAILED"
  exit 1
fi
