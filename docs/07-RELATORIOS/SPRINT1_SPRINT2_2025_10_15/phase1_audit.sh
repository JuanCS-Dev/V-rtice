#!/bin/bash
VALIDATION_DIR=$(cat /tmp/validation_dir.txt)
cd /home/juan/vertice-dev/backend/services

cat > "$VALIDATION_DIR/01_inventory.md" << 'HEADER'
# INVENTÁRIO DE SERVIÇOS - FASE 1

HEADER

echo "## Estrutura Esperada" >> "$VALIDATION_DIR/01_inventory.md"
cat >> "$VALIDATION_DIR/01_inventory.md" << 'EXPECTED'
```
service_name/
├── __init__.py
├── main.py (ou app.py)
├── pyproject.toml (UV)
├── tests/
│   ├── __init__.py
│   └── test_*.py
└── README.md
```

EXPECTED

echo "" >> "$VALIDATION_DIR/01_inventory.md"
echo "## Validação por Serviço" >> "$VALIDATION_DIR/01_inventory.md"
echo "" >> "$VALIDATION_DIR/01_inventory.md"

TOTAL=0
COMPLETE=0
MISSING_TESTS=0
MISSING_UV=0

for SERVICE in */; do
    ((TOTAL++))
    SERVICE_NAME="${SERVICE%/}"
    echo "### $SERVICE_NAME" >> "$VALIDATION_DIR/01_inventory.md"
    
    ISSUES=0
    
    # Check __init__.py
    if [ -f "${SERVICE}__init__.py" ]; then
        echo "- ✅ \`__init__.py\`" >> "$VALIDATION_DIR/01_inventory.md"
    else
        echo "- ❌ **FALTA** \`__init__.py\`" >> "$VALIDATION_DIR/01_inventory.md"
        ((ISSUES++))
    fi
    
    # Check main/app.py
    if [ -f "${SERVICE}main.py" ] || [ -f "${SERVICE}app.py" ]; then
        ENTRY=$([ -f "${SERVICE}main.py" ] && echo "main.py" || echo "app.py")
        echo "- ✅ \`$ENTRY\`" >> "$VALIDATION_DIR/01_inventory.md"
    else
        echo "- ❌ **FALTA** \`main.py\` ou \`app.py\`" >> "$VALIDATION_DIR/01_inventory.md"
        ((ISSUES++))
    fi
    
    # Check pyproject.toml
    if [ -f "${SERVICE}pyproject.toml" ]; then
        echo "- ✅ \`pyproject.toml\` (UV)" >> "$VALIDATION_DIR/01_inventory.md"
    else
        echo "- ⚠️ **FALTA** \`pyproject.toml\` (migração UV necessária)" >> "$VALIDATION_DIR/01_inventory.md"
        ((MISSING_UV++))
        ((ISSUES++))
    fi
    
    # Check tests/
    if [ -d "${SERVICE}tests" ]; then
        TEST_COUNT=$(find "${SERVICE}tests" -name "test_*.py" 2>/dev/null | wc -l)
        if [ "$TEST_COUNT" -gt 0 ]; then
            echo "- ✅ \`tests/\` ($TEST_COUNT arquivos)" >> "$VALIDATION_DIR/01_inventory.md"
        else
            echo "- ⚠️ \`tests/\` existe mas sem \`test_*.py\`" >> "$VALIDATION_DIR/01_inventory.md"
            ((MISSING_TESTS++))
            ((ISSUES++))
        fi
    else
        echo "- ❌ **FALTA** \`tests/\`" >> "$VALIDATION_DIR/01_inventory.md"
        ((MISSING_TESTS++))
        ((ISSUES++))
    fi
    
    # Check README
    if [ -f "${SERVICE}README.md" ]; then
        LINES=$(wc -l < "${SERVICE}README.md")
        if [ "$LINES" -gt 20 ]; then
            echo "- ✅ \`README.md\` ($LINES linhas)" >> "$VALIDATION_DIR/01_inventory.md"
        else
            echo "- ⚠️ \`README.md\` muito curto ($LINES linhas)" >> "$VALIDATION_DIR/01_inventory.md"
        fi
    else
        echo "- ⚠️ **FALTA** \`README.md\`" >> "$VALIDATION_DIR/01_inventory.md"
    fi
    
    if [ "$ISSUES" -eq 0 ]; then
        echo "- **Status:** ✅ COMPLETO" >> "$VALIDATION_DIR/01_inventory.md"
        ((COMPLETE++))
    else
        echo "- **Status:** ❌ INCOMPLETO ($ISSUES problemas)" >> "$VALIDATION_DIR/01_inventory.md"
    fi
    
    echo "" >> "$VALIDATION_DIR/01_inventory.md"
done

cat >> "$VALIDATION_DIR/01_inventory.md" << EOF

---

## Resumo Estrutural

| Métrica | Valor |
|---------|-------|
| Total de serviços | $TOTAL |
| Estrutura completa | $COMPLETE |
| Sem testes | $MISSING_TESTS |
| Sem UV (pyproject.toml) | $MISSING_UV |

**Conformidade:** $(echo "scale=1; $COMPLETE * 100 / $TOTAL" | bc)%

EOF

echo "$TOTAL|$COMPLETE|$MISSING_TESTS|$MISSING_UV"
