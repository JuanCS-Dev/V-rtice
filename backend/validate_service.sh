#!/bin/bash
SERVICE=$1
cd /home/juan/vertice-dev/backend/services/$SERVICE

echo "=== $SERVICE ==="

# Count files
FILES=$(find . -name "*.py" -type f ! -path "*/venv/*" ! -path "*/__pycache__/*" 2>/dev/null | wc -l)
echo "Files: $FILES"

# Setup venv if missing
if [ ! -d venv ]; then
    python3 -m venv venv >/dev/null 2>&1
fi

# Activate and install
source venv/bin/activate 2>/dev/null
pip install -q pytest pytest-cov mypy ruff 2>/dev/null

# Check if tests exist
if [ ! -d tests ]; then
    echo "❌ NO TESTS"
    echo "Coverage: 0%"
    echo ""
    exit 1
fi

# Run tests
TESTS_OUTPUT=$(pytest tests/ -v --tb=line 2>&1)
TESTS_PASS=$?

# Coverage
COV_OUTPUT=$(pytest --cov=. --cov-report=term-missing --cov-report=json -q 2>&1)
if [ -f coverage.json ]; then
    COV=$(python3 -c "import json; print(f\"{json.load(open('coverage.json'))['totals']['percent_covered']:.2f}\")" 2>/dev/null || echo "0.00")
else
    COV="0.00"
fi

# Quality checks
MYPY=$(mypy . --ignore-missing-imports 2>&1 | grep -c "error:" || echo 0)
RUFF=$(ruff check . 2>&1 | grep -E "^.*\.py:" | wc -l || echo 0)
TODO=$(grep -r "TODO\|FIXME" --include="*.py" . 2>/dev/null | grep -v test | grep -v venv | wc -l || echo 0)

# Report
echo "Coverage: $COV%"
echo "Tests: $(echo $TESTS_OUTPUT | grep -oP '\d+(?= passed)' || echo 0) passed"
echo "Mypy: $MYPY errors"
echo "Ruff: $RUFF issues"
echo "TODOs: $TODO"

# Status
if [ "$COV" == "100.00" ] && [ "$TESTS_PASS" -eq 0 ] && [ "$MYPY" -eq 0 ] && [ "$RUFF" -eq 0 ] && [ "$TODO" -eq 0 ]; then
    echo "✅ CERTIFIED"
else
    echo "❌ NEEDS FIX"
fi

echo ""
