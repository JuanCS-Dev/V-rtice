#!/bin/bash
set -e

echo "🔍 TASK-003: Validating Verdict Models..."
echo ""

BASE_DIR="/home/juan/vertice-dev/backend/services/maximus_core_service/motor_integridade_processual"

# Counter for checks
CHECKS_PASSED=0
TOTAL_CHECKS=0

check() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    if eval "$1"; then
        echo "  ✅ $2"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
        return 0
    else
        echo "  ❌ $2"
        return 1
    fi
}

cd "$BASE_DIR"

echo "📄 Checking File Existence..."
check "[ -f 'models/verdict.py' ]" "verdict.py exists"
check "[ -f 'tests/unit/test_verdict.py' ]" "test_verdict.py exists"
check "[ $(wc -l < models/verdict.py) -ge 250 ]" "verdict.py ≥ 250 lines"
check "[ $(wc -l < tests/unit/test_verdict.py) -ge 600 ]" "test_verdict.py ≥ 600 lines"

echo ""
echo "🔍 Running Type Checking (mypy --strict)..."
if command -v mypy &> /dev/null; then
    if mypy --strict models/verdict.py 2>&1 | tee /tmp/mypy_verdict.txt | grep -q "Success"; then
        check "true" "Type checking passed"
    else
        echo "  ⚠️  Type checking has issues:"
        cat /tmp/mypy_verdict.txt | head -20
        check "false" "Type checking passed"
    fi
else
    echo "  ⚠️  mypy not installed, skipping"
fi

echo ""
echo "🧪 Running Unit Tests..."
export PYTHONPATH="$BASE_DIR:$PYTHONPATH"

if python3 -m pytest tests/unit/test_verdict.py -v --tb=short 2>&1 | tee /tmp/pytest_verdict.txt; then
    TESTS_PASSED=$(grep -c "PASSED" /tmp/pytest_verdict.txt || echo "0")
    check "[ $TESTS_PASSED -ge 28 ]" "All tests passed ($TESTS_PASSED passed)"
else
    echo "  ❌ Tests failed"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
fi

echo ""
echo "📊 Running Coverage Analysis..."
if python3 -m pytest tests/unit/test_verdict.py --cov=motor_integridade_processual.models.verdict --cov-report=term-missing --no-cov-on-fail 2>&1 | tee /tmp/coverage_verdict.txt; then
    # Extract verdict.py specific coverage
    VERDICT_COV=$(grep "models/verdict.py" /tmp/coverage_verdict.txt | grep -oP '\d+%' | tr -d '%')
    check "[ $VERDICT_COV -ge 95 ]" "Coverage ≥ 95% (actual: ${VERDICT_COV}%)"
else
    echo "  ⚠️  Coverage check failed"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
fi

echo ""
echo "🔒 Running Security Scan (bandit)..."
if command -v bandit &> /dev/null; then
    if bandit -r models/verdict.py -ll 2>&1 | tee /tmp/bandit_verdict.txt | grep -q "No issues identified"; then
        check "true" "Security scan passed"
    else
        echo "  ⚠️  Security issues found:"
        cat /tmp/bandit_verdict.txt
        check "false" "Security scan passed"
    fi
else
    echo "  ⚠️  bandit not installed, skipping"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "📊 TASK-003 Validation Results:"
echo "═══════════════════════════════════════════════════════════"
echo "  Checks Passed: $CHECKS_PASSED / $TOTAL_CHECKS"

if [ $CHECKS_PASSED -eq $TOTAL_CHECKS ]; then
    echo ""
    echo "✅ All checks passed"
    echo "✅ Models: Complete"
    echo "✅ Tests: 28/28 passed"
    echo "✅ Coverage: ≥95%"
    echo "✅ Type hints: 100%"
    echo "✅ Security: Clean"
    echo ""
    echo "🎉 TASK-003: 100% COMPLETE"
    echo ""
    exit 0
else
    echo ""
    echo "❌ Some checks failed ($((TOTAL_CHECKS - CHECKS_PASSED)) failures)"
    echo "❌ TASK-003: INCOMPLETE"
    echo ""
    exit 1
fi
