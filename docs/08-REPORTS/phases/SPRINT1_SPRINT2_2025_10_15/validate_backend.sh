#!/bin/bash
set -e

LOG_FILE="/tmp/maximus_validation/validation_$(date +%Y%m%d_%H%M%S).log"
RESULTS_FILE="/tmp/maximus_validation/results.txt"
CERTIFIED=0
FAILED=0
SKIPPED=0

> $RESULTS_FILE

while IFS= read -r SERVICE; do
    echo "" | tee -a $LOG_FILE
    echo "════════════════════════════════════════" | tee -a $LOG_FILE
    echo "VALIDATING: $SERVICE" | tee -a $LOG_FILE
    echo "════════════════════════════════════════" | tee -a $LOG_FILE
    
    cd "/home/juan/vertice-dev/backend/services/$SERVICE"
    
    # Check if Python service
    PY_FILES=$(find . -name "*.py" -type f ! -path "./venv/*" ! -path "./__pycache__/*" 2>/dev/null | wc -l)
    
    if [ "$PY_FILES" -eq 0 ]; then
        echo "⚠️  No Python files, skipping" | tee -a $LOG_FILE
        echo "$SERVICE|SKIPPED|No Python files" >> $RESULTS_FILE
        ((SKIPPED++))
        continue
    fi
    
    echo "Python files: $PY_FILES" | tee -a $LOG_FILE
    
    # Setup virtual environment
    if [ ! -d "venv" ]; then
        echo "Creating venv..." | tee -a $LOG_FILE
        python3 -m venv venv >> $LOG_FILE 2>&1
    fi
    
    source venv/bin/activate
    
    # Install test dependencies
    echo "Installing dependencies..." | tee -a $LOG_FILE
    pip install -q pytest pytest-cov mypy ruff 2>> $LOG_FILE
    
    # Install service dependencies
    if [ -f "requirements.txt" ]; then
        pip install -q -r requirements.txt 2>> $LOG_FILE
    fi
    
    # Run tests
    echo "Running tests..." | tee -a $LOG_FILE
    if [ -d "tests" ]; then
        pytest tests/ -v --tb=short > /tmp/test_output.txt 2>&1
        TEST_EXIT=$?
        
        TESTS_PASSED=$(grep -c "PASSED" /tmp/test_output.txt || echo 0)
        TESTS_FAILED=$(grep -c "FAILED" /tmp/test_output.txt || echo 0)
        
        echo "Tests: $TESTS_PASSED passed, $TESTS_FAILED failed" | tee -a $LOG_FILE
    else
        echo "⚠️  No tests directory" | tee -a $LOG_FILE
        TEST_EXIT=1
        TESTS_PASSED=0
        TESTS_FAILED=0
    fi
    
    # Coverage
    echo "Checking coverage..." | tee -a $LOG_FILE
    if [ -d "tests" ]; then
        pytest --cov=. --cov-report=json --cov-report=term-missing tests/ > /tmp/cov_output.txt 2>&1
        
        if [ -f "coverage.json" ]; then
            COVERAGE=$(python3 -c "import json; print('{:.2f}'.format(json.load(open('coverage.json'))['totals']['percent_covered']))" 2>/dev/null || echo "0.00")
        else
            COVERAGE=$(grep "TOTAL" /tmp/cov_output.txt | awk '{print $NF}' | sed 's/%//' || echo "0.00")
        fi
        
        echo "Coverage: ${COVERAGE}%" | tee -a $LOG_FILE
    else
        COVERAGE="0.00"
    fi
    
    # Mypy check
    echo "Running mypy..." | tee -a $LOG_FILE
    mypy . --ignore-missing-imports > /tmp/mypy_output.txt 2>&1
    MYPY_ERRORS=$(grep -c "error:" /tmp/mypy_output.txt || echo 0)
    echo "Mypy errors: $MYPY_ERRORS" | tee -a $LOG_FILE
    
    # Ruff check
    echo "Running ruff..." | tee -a $LOG_FILE
    ruff check . > /tmp/ruff_output.txt 2>&1
    RUFF_ERRORS=$(wc -l < /tmp/ruff_output.txt)
    echo "Ruff errors: $RUFF_ERRORS" | tee -a $LOG_FILE
    
    # TODOs check
    TODO_COUNT=$(grep -r "TODO\|FIXME\|XXX\|HACK" --include="*.py" . 2>/dev/null | grep -v "test" | grep -v "venv" | wc -l)
    echo "TODOs: $TODO_COUNT" | tee -a $LOG_FILE
    
    # Evaluate certification
    COVERAGE_INT=$(echo $COVERAGE | cut -d. -f1)
    
    if [ "$COVERAGE_INT" = "100" ] && \
       [ "$TEST_EXIT" -eq 0 ] && \
       [ "$TESTS_FAILED" -eq 0 ] && \
       [ "$MYPY_ERRORS" -eq 0 ] && \
       [ "$RUFF_ERRORS" -eq 0 ] && \
       [ "$TODO_COUNT" -eq 0 ]; then
        echo "✅ $SERVICE: CERTIFIED" | tee -a $LOG_FILE
        echo "$SERVICE|CERTIFIED|${COVERAGE}%|$TESTS_PASSED tests" >> $RESULTS_FILE
        ((CERTIFIED++))
    else
        echo "❌ $SERVICE: NEEDS FIX" | tee -a $LOG_FILE
        echo "$SERVICE|FAILED|${COVERAGE}%|Tests:$TESTS_FAILED|Mypy:$MYPY_ERRORS|Ruff:$RUFF_ERRORS|TODO:$TODO_COUNT" >> $RESULTS_FILE
        ((FAILED++))
    fi
    
    deactivate
    
done < /tmp/maximus_validation/services_list.txt

# Summary
TOTAL_SERVICES=$(wc -l < /tmp/maximus_validation/services_list.txt)

echo "" | tee -a $LOG_FILE
echo "═══════════════════════════════════════════════" | tee -a $LOG_FILE
echo "VALIDATION SUMMARY" | tee -a $LOG_FILE
echo "═══════════════════════════════════════════════" | tee -a $LOG_FILE
echo "Total services: $TOTAL_SERVICES" | tee -a $LOG_FILE
echo "Certified (100%): $CERTIFIED" | tee -a $LOG_FILE
echo "Failed: $FAILED" | tee -a $LOG_FILE
echo "Skipped: $SKIPPED" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

if [ "$CERTIFIED" -gt 0 ]; then
    echo "✅ CERTIFIED SERVICES:" | tee -a $LOG_FILE
    grep "CERTIFIED" $RESULTS_FILE | cut -d'|' -f1 | tee -a $LOG_FILE
fi

echo "" | tee -a $LOG_FILE

if [ "$FAILED" -gt 0 ]; then
    echo "❌ SERVICES NEEDING FIXES:" | tee -a $LOG_FILE
    grep "FAILED" $RESULTS_FILE | while IFS='|' read -r name status coverage details; do
        echo "  $name: $coverage, $details" | tee -a $LOG_FILE
    done
fi

# Export for final step
echo "CERTIFIED=$CERTIFIED" > /tmp/maximus_validation/counters.env
echo "FAILED=$FAILED" >> /tmp/maximus_validation/counters.env
echo "SKIPPED=$SKIPPED" >> /tmp/maximus_validation/counters.env
echo "TOTAL_SERVICES=$TOTAL_SERVICES" >> /tmp/maximus_validation/counters.env
