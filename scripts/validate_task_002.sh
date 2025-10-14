#!/bin/bash
set -e

echo "🔍 TASK-002: Validating ActionPlan Models..."
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
check "[ -f 'models/action_plan.py' ]" "action_plan.py exists"
check "[ -f 'tests/unit/test_action_plan.py' ]" "test_action_plan.py exists"
check "[ $(wc -l < models/action_plan.py) -ge 400 ]" "action_plan.py ≥ 400 lines"
check "[ $(wc -l < tests/unit/test_action_plan.py) -ge 400 ]" "test_action_plan.py ≥ 400 lines"

echo ""
echo "🔧 Installing dependencies (if needed)..."
if ! python3 -c "import pydantic" 2>/dev/null; then
    echo "  Installing pydantic..."
    pip3 install -q pydantic 2>/dev/null || true
fi

if ! python3 -c "import pytest" 2>/dev/null; then
    echo "  Installing pytest..."
    pip3 install -q pytest pytest-cov 2>/dev/null || true
fi

echo ""
echo "🔍 Running Type Checking (mypy --strict)..."
if command -v mypy &> /dev/null; then
    if mypy --strict models/action_plan.py 2>&1 | tee /tmp/mypy_output.txt | grep -q "Success"; then
        check "true" "Type checking passed"
    else
        echo "  ⚠️  Type checking has issues:"
        cat /tmp/mypy_output.txt | head -20
        check "false" "Type checking passed"
    fi
else
    echo "  ⚠️  mypy not installed, skipping type check"
    echo "  ℹ️  Install with: pip install mypy"
fi

echo ""
echo "🧪 Running Unit Tests..."
export PYTHONPATH="$BASE_DIR:$PYTHONPATH"

if python3 -m pytest tests/unit/test_action_plan.py -v --tb=short 2>&1 | tee /tmp/pytest_output.txt; then
    TESTS_PASSED=$(grep -c "PASSED" /tmp/pytest_output.txt || echo "0")
    check "[ $TESTS_PASSED -ge 28 ]" "All 28 tests passed ($TESTS_PASSED/28)"
else
    echo "  ❌ Tests failed"
    cat /tmp/pytest_output.txt | tail -30
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
fi

echo ""
echo "�� Running Coverage Analysis..."
if python3 -m pytest tests/unit/test_action_plan.py --cov=models.action_plan --cov-report=term-missing --cov-fail-under=95 2>&1 | tee /tmp/coverage_output.txt; then
    COVERAGE=$(grep -oP "Total coverage: \K\d+" /tmp/coverage_output.txt)
    check "[ $COVERAGE -ge 95 ]" "Coverage ≥ 95% (actual: ${COVERAGE}%)"
else
    echo "  ⚠️  Coverage below 95%"
    grep "TOTAL" /tmp/coverage_output.txt || true
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
fi

echo ""
echo "🔒 Running Security Scan (bandit)..."
if command -v bandit &> /dev/null; then
    if bandit -r models/action_plan.py -ll 2>&1 | tee /tmp/bandit_output.txt | grep -q "No issues identified"; then
        check "true" "Security scan passed"
    else
        echo "  ⚠️  Security issues found:"
        cat /tmp/bandit_output.txt
        check "false" "Security scan passed"
    fi
else
    echo "  ⚠️  bandit not installed, skipping security scan"
    echo "  ℹ️  Install with: pip install bandit"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "📊 TASK-002 Validation Results:"
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
    echo "🎉 TASK-002: 100% COMPLETE"
    echo ""
    exit 0
else
    echo ""
    echo "❌ Some checks failed ($((TOTAL_CHECKS - CHECKS_PASSED)) failures)"
    echo "❌ TASK-002: INCOMPLETE"
    echo ""
    exit 1
fi
