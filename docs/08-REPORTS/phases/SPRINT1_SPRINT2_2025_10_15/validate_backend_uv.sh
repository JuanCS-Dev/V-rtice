#!/bin/bash

LOG_FILE="/tmp/maximus_validation/validation_uv_$(date +%Y%m%d_%H%M%S).log"
RESULTS_FILE="/tmp/maximus_validation/results_uv.txt"
CERTIFIED=0
FAILED=0
SKIPPED=0

> $RESULTS_FILE
> $LOG_FILE

echo "=== MAXIMUS BACKEND VALIDATION (UV-based) ===" | tee -a $LOG_FILE
echo "Started: $(date)" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

# Ensure project dependencies are installed
echo "Installing project dependencies with uv..." | tee -a $LOG_FILE
cd /home/juan/vertice-dev
uv pip install -e . >> $LOG_FILE 2>&1
uv pip install pytest pytest-cov mypy ruff >> $LOG_FILE 2>&1

echo "" | tee -a $LOG_FILE

while IFS= read -r SERVICE; do
    echo "──────────────────────────────────────" | tee -a $LOG_FILE
    echo "[$((CERTIFIED+FAILED+SKIPPED+1))/83] $SERVICE" | tee -a $LOG_FILE
    
    cd "/home/juan/vertice-dev/backend/services/$SERVICE"
    
    # Quick check - count Python files
    PY_FILES=$(find . -maxdepth 3 -name "*.py" -type f ! -path "./__pycache__/*" ! -path "./tests/*" 2>/dev/null | wc -l)
    
    if [ "$PY_FILES" -eq 0 ]; then
        echo "⚠️  SKIPPED (no Python files)" | tee -a $LOG_FILE
        echo "$SERVICE|SKIPPED|No Python files" >> $RESULTS_FILE
        ((SKIPPED++))
        continue
    fi
    
    # Check for tests directory
    if [ ! -d "tests" ]; then
        echo "❌ FAILED (no tests)" | tee -a $LOG_FILE
        echo "$SERVICE|FAILED|0%|No tests directory" >> $RESULTS_FILE
        ((FAILED++))
        continue
    fi
    
    TEST_FILES=$(find tests -name "test_*.py" 2>/dev/null | wc -l)
    if [ "$TEST_FILES" -eq 0 ]; then
        echo "❌ FAILED (no test files)" | tee -a $LOG_FILE
        echo "$SERVICE|FAILED|0%|No test files in tests/" >> $RESULTS_FILE
        ((FAILED++))
        continue
    fi
    
    # Check for TODOs/FIXMEs in main code (not tests)
    TODO_COUNT=$(grep -r "TODO\|FIXME\|XXX\|HACK" --include="*.py" . 2>/dev/null | grep -v "/tests/" | grep -v "__pycache__" | wc -l)
    
    if [ "$TODO_COUNT" -gt 0 ]; then
        echo "❌ FAILED ($TODO_COUNT TODOs)" | tee -a $LOG_FILE
        echo "$SERVICE|FAILED|?%|TODOs:$TODO_COUNT" >> $RESULTS_FILE
        ((FAILED++))
        continue
    fi
    
    # Check for obvious mocks/stubs in main code
    MOCK_COUNT=$(grep -r "pass  # TODO\|raise NotImplementedError\|# STUB\|# PLACEHOLDER" --include="*.py" . 2>/dev/null | grep -v "/tests/" | wc -l)
    
    if [ "$MOCK_COUNT" -gt 0 ]; then
        echo "❌ FAILED ($MOCK_COUNT mocks/stubs)" | tee -a $LOG_FILE
        echo "$SERVICE|FAILED|?%|Mocks:$MOCK_COUNT" >> $RESULTS_FILE
        ((FAILED++))
        continue
    fi
    
    # Run tests with coverage using uv
    echo "  Running tests..." | tee -a $LOG_FILE
    cd /home/juan/vertice-dev
    
    # Use PYTHONPATH to include the service
    PYTHONPATH="/home/juan/vertice-dev/backend/services/$SERVICE:$PYTHONPATH" \
    uv run pytest "backend/services/$SERVICE/tests/" \
        --cov="backend/services/$SERVICE" \
        --cov-report=json:/tmp/coverage_${SERVICE}.json \
        --cov-report=term-missing \
        -v \
        > /tmp/test_${SERVICE}.log 2>&1
    
    TEST_EXIT=$?
    
    # Parse results
    TESTS_PASSED=$(grep -c "PASSED" /tmp/test_${SERVICE}.log || echo 0)
    TESTS_FAILED=$(grep -c "FAILED" /tmp/test_${SERVICE}.log || echo 0)
    
    if [ -f "/tmp/coverage_${SERVICE}.json" ]; then
        COVERAGE=$(python3 -c "import json; print('{:.2f}'.format(json.load(open('/tmp/coverage_${SERVICE}.json'))['totals']['percent_covered']))" 2>/dev/null || echo "0.00")
    else
        COVERAGE="0.00"
    fi
    
    echo "  Tests: $TESTS_PASSED passed, $TESTS_FAILED failed | Coverage: ${COVERAGE}%" | tee -a $LOG_FILE
    
    # Run mypy
    cd "/home/juan/vertice-dev/backend/services/$SERVICE"
    mypy . --ignore-missing-imports > /tmp/mypy_${SERVICE}.log 2>&1
    MYPY_ERRORS=$(grep -c "error:" /tmp/mypy_${SERVICE}.log || echo 0)
    
    # Run ruff
    ruff check . > /tmp/ruff_${SERVICE}.log 2>&1
    RUFF_ERRORS=$(wc -l < /tmp/ruff_${SERVICE}.log)
    
    echo "  Mypy: $MYPY_ERRORS errors | Ruff: $RUFF_ERRORS issues" | tee -a $LOG_FILE
    
    # Evaluate certification
    COVERAGE_INT=$(echo $COVERAGE | cut -d. -f1)
    
    if [ "$COVERAGE_INT" = "100" ] && \
       [ "$TEST_EXIT" -eq 0 ] && \
       [ "$TESTS_FAILED" -eq 0 ] && \
       [ "$MYPY_ERRORS" -eq 0 ] && \
       [ "$RUFF_ERRORS" -eq 0 ]; then
        echo "  ✅ CERTIFIED" | tee -a $LOG_FILE
        echo "$SERVICE|CERTIFIED|${COVERAGE}%|$TESTS_PASSED tests|Mypy:0|Ruff:0" >> $RESULTS_FILE
        ((CERTIFIED++))
    else
        echo "  ❌ NEEDS FIX" | tee -a $LOG_FILE
        echo "$SERVICE|NEEDS_FIX|${COVERAGE}%|Tests:$TESTS_FAILED|Mypy:$MYPY_ERRORS|Ruff:$RUFF_ERRORS" >> $RESULTS_FILE
        ((FAILED++))
    fi
    
done < /tmp/maximus_validation/services_list.txt

# Summary
TOTAL_SERVICES=$(wc -l < /tmp/maximus_validation/services_list.txt)

echo "" | tee -a $LOG_FILE
echo "═══════════════════════════════════════════════" | tee -a $LOG_FILE
echo "VALIDATION SUMMARY (UV-based)" | tee -a $LOG_FILE
echo "═══════════════════════════════════════════════" | tee -a $LOG_FILE
echo "Total services: $TOTAL_SERVICES" | tee -a $LOG_FILE
echo "Certified (100%): $CERTIFIED" | tee -a $LOG_FILE
echo "Needs fix: $FAILED" | tee -a $LOG_FILE
echo "Skipped: $SKIPPED" | tee -a $LOG_FILE

echo "" | tee -a $LOG_FILE

if [ "$CERTIFIED" -gt 0 ]; then
    echo "✅ CERTIFIED SERVICES:" | tee -a $LOG_FILE
    grep "CERTIFIED" $RESULTS_FILE | cut -d'|' -f1 | tee -a $LOG_FILE
fi

echo "" | tee -a $LOG_FILE
echo "Export counters..." | tee -a $LOG_FILE
echo "CERTIFIED=$CERTIFIED" > /tmp/maximus_validation/counters_uv.env
echo "FAILED=$FAILED" >> /tmp/maximus_validation/counters_uv.env
echo "SKIPPED=$SKIPPED" >> /tmp/maximus_validation/counters_uv.env
echo "TOTAL_SERVICES=$TOTAL_SERVICES" >> /tmp/maximus_validation/counters_uv.env

echo "" | tee -a $LOG_FILE
echo "Completed: $(date)" | tee -a $LOG_FILE
