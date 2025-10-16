#!/bin/bash
VALIDATION_DIR=$(cat /tmp/validation_dir.txt)
cd /home/juan/vertice-dev

cat > "$VALIDATION_DIR/04_tests.md" << 'HEADER'
# VALIDAÇÃO DE TESTES - FASE 4

HEADER

echo "## Resultados por Serviço" >> "$VALIDATION_DIR/04_tests.md"
echo "" >> "$VALIDATION_DIR/04_tests.md"

TESTED=0
PASSED=0
FAILED=0
NO_TESTS=0

# Install test tools if needed
source .venv/bin/activate 2>/dev/null || true
pip install -q pytest pytest-cov 2>/dev/null || true

for SERVICE_DIR in backend/services/*/; do
    SERVICE=$(basename "$SERVICE_DIR")
    
    if [ -d "${SERVICE_DIR}tests" ] && [ "$(find ${SERVICE_DIR}tests -name 'test_*.py' 2>/dev/null | wc -l)" -gt 0 ]; then
        echo "### $SERVICE" >> "$VALIDATION_DIR/04_tests.md"
        ((TESTED++))
        
        # Run tests with timeout
        PYTHONPATH="${SERVICE_DIR}:${PWD}:$PYTHONPATH" \
        timeout 30 pytest "${SERVICE_DIR}tests/" \
            --cov="${SERVICE_DIR}" \
            --cov-report=json:"${VALIDATION_DIR}/cov_${SERVICE}.json" \
            --tb=no -q 2>&1 > /tmp/test_${SERVICE}.log
        
        TEST_EXIT=$?
        
        if [ "$TEST_EXIT" -eq 0 ]; then
            echo "- ✅ Testes PASSED" >> "$VALIDATION_DIR/04_tests.md"
            ((PASSED++))
        elif [ "$TEST_EXIT" -eq 124 ]; then
            echo "- ⏱️ TIMEOUT (>30s)" >> "$VALIDATION_DIR/04_tests.md"
            ((FAILED++))
        else
            FAILURES=$(grep -c "FAILED" /tmp/test_${SERVICE}.log 2>/dev/null || echo "?")
            echo "- ❌ Testes FAILED ($FAILURES)" >> "$VALIDATION_DIR/04_tests.md"
            ((FAILED++))
        fi
        
        # Extract coverage if available
        if [ -f "${VALIDATION_DIR}/cov_${SERVICE}.json" ]; then
            COV=$(python3 -c "import json; print('{:.1f}'.format(json.load(open('${VALIDATION_DIR}/cov_${SERVICE}.json'))['totals']['percent_covered']))" 2>/dev/null || echo "0.0")
            echo "- Coverage: ${COV}%" >> "$VALIDATION_DIR/04_tests.md"
        fi
        
        echo "" >> "$VALIDATION_DIR/04_tests.md"
    else
        ((NO_TESTS++))
    fi
done

cat >> "$VALIDATION_DIR/04_tests.md" << EOF

---

## Resumo de Testes

| Métrica | Valor |
|---------|-------|
| Serviços testados | $TESTED |
| Testes PASSED | $PASSED |
| Testes FAILED | $FAILED |
| Sem testes | $NO_TESTS |

**Taxa de sucesso:** $([ $TESTED -gt 0 ] && echo "scale=1; $PASSED * 100 / $TESTED" | bc || echo "0.0")%

EOF

echo "$TESTED|$PASSED|$FAILED|$NO_TESTS"
