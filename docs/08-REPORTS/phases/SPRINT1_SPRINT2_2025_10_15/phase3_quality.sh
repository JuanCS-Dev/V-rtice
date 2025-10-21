#!/bin/bash
VALIDATION_DIR=$(cat /tmp/validation_dir.txt)
cd /home/juan/vertice-dev/backend/services

cat > "$VALIDATION_DIR/03_quality.md" << 'HEADER'
# ANÁLISE DE QUALIDADE - FASE 3

HEADER

echo "## TODO/FIXME/HACK Count" >> "$VALIDATION_DIR/03_quality.md"
echo "" >> "$VALIDATION_DIR/03_quality.md"

TOTAL_TODOS=0
CRITICAL_SERVICES=0

for SERVICE in */; do
    SERVICE_NAME="${SERVICE%/}"
    TODO_COUNT=$(grep -r "TODO\|FIXME\|XXX\|HACK" --include="*.py" "$SERVICE" 2>/dev/null | grep -v "/tests/" | grep -v "__pycache__" | wc -l)
    
    if [ "$TODO_COUNT" -gt 0 ]; then
        TOTAL_TODOS=$((TOTAL_TODOS + TODO_COUNT))
        
        if [ "$TODO_COUNT" -gt 100 ]; then
            echo "- ❌ **$SERVICE_NAME**: $TODO_COUNT TODOs (CRÍTICO)" >> "$VALIDATION_DIR/03_quality.md"
            ((CRITICAL_SERVICES++))
        elif [ "$TODO_COUNT" -gt 50 ]; then
            echo "- ⚠️ **$SERVICE_NAME**: $TODO_COUNT TODOs (Alto)" >> "$VALIDATION_DIR/03_quality.md"
        elif [ "$TODO_COUNT" -gt 10 ]; then
            echo "- ⚠️ $SERVICE_NAME: $TODO_COUNT TODOs (Médio)" >> "$VALIDATION_DIR/03_quality.md"
        else
            echo "- ℹ️ $SERVICE_NAME: $TODO_COUNT TODOs (Baixo)" >> "$VALIDATION_DIR/03_quality.md"
        fi
    fi
done

cat >> "$VALIDATION_DIR/03_quality.md" << EOF

---

## Mocks/Stubs em Código Produção

EOF

MOCK_TOTAL=0

for SERVICE in */; do
    SERVICE_NAME="${SERVICE%/}"
    MOCK_COUNT=$(grep -r "pass  # TODO\|raise NotImplementedError\|# STUB\|# PLACEHOLDER" --include="*.py" "$SERVICE" 2>/dev/null | grep -v "/tests/" | grep -v "__pycache__" | wc -l)
    
    if [ "$MOCK_COUNT" -gt 0 ]; then
        echo "- ❌ **$SERVICE_NAME**: $MOCK_COUNT mocks/stubs" >> "$VALIDATION_DIR/03_quality.md"
        MOCK_TOTAL=$((MOCK_TOTAL + MOCK_COUNT))
    fi
done

if [ "$MOCK_TOTAL" -eq 0 ]; then
    echo "✅ Nenhum mock/stub detectado em código de produção" >> "$VALIDATION_DIR/03_quality.md"
fi

cat >> "$VALIDATION_DIR/03_quality.md" << EOF

---

## Resumo de Qualidade

| Métrica | Valor | Status |
|---------|-------|--------|
| Total TODOs | $TOTAL_TODOS | $([ $TOTAL_TODOS -lt 100 ] && echo "✅" || echo "❌") |
| Serviços críticos (>100 TODOs) | $CRITICAL_SERVICES | $([ $CRITICAL_SERVICES -eq 0 ] && echo "✅" || echo "❌") |
| Total Mocks/Stubs | $MOCK_TOTAL | $([ $MOCK_TOTAL -eq 0 ] && echo "✅" || echo "❌") |

EOF

echo "$TOTAL_TODOS|$CRITICAL_SERVICES|$MOCK_TOTAL"
