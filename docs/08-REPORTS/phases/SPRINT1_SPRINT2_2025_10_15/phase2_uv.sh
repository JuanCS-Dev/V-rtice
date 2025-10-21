#!/bin/bash
VALIDATION_DIR=$(cat /tmp/validation_dir.txt)
cd /home/juan/vertice-dev/backend/services

cat > "$VALIDATION_DIR/02_dependencies.md" << 'HEADER'
# VALIDAÇÃO UV DEPENDENCIES - FASE 2

HEADER

echo "## Serviços com pyproject.toml" >> "$VALIDATION_DIR/02_dependencies.md"
echo "" >> "$VALIDATION_DIR/02_dependencies.md"

SUCCESS=0
FAILED=0

for SERVICE in */; do
    if [ -f "${SERVICE}pyproject.toml" ]; then
        SERVICE_NAME="${SERVICE%/}"
        echo "### $SERVICE_NAME" >> "$VALIDATION_DIR/02_dependencies.md"
        
        cd "$SERVICE"
        
        # Validate pyproject.toml syntax
        if python3 -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb'))" 2>/dev/null; then
            echo "- ✅ \`pyproject.toml\` sintaxe válida" >> "$VALIDATION_DIR/02_dependencies.md"
            
            # Try UV sync
            if timeout 30 uv sync --quiet 2>&1 | grep -q "error\|failed"; then
                echo "- ❌ \`uv sync\` FALHOU" >> "$VALIDATION_DIR/02_dependencies.md"
                ((FAILED++))
            else
                echo "- ✅ \`uv sync\` OK" >> "$VALIDATION_DIR/02_dependencies.md"
                ((SUCCESS++))
            fi
        else
            echo "- ❌ \`pyproject.toml\` SINTAXE INVÁLIDA" >> "$VALIDATION_DIR/02_dependencies.md"
            ((FAILED++))
        fi
        
        cd ..
        echo "" >> "$VALIDATION_DIR/02_dependencies.md"
    fi
done

echo "---" >> "$VALIDATION_DIR/02_dependencies.md"
echo "" >> "$VALIDATION_DIR/02_dependencies.md"
echo "## Serviços SEM pyproject.toml (Migração UV Necessária)" >> "$VALIDATION_DIR/02_dependencies.md"
echo "" >> "$VALIDATION_DIR/02_dependencies.md"

for SERVICE in */; do
    if [ ! -f "${SERVICE}pyproject.toml" ]; then
        echo "- ${SERVICE%/}" >> "$VALIDATION_DIR/02_dependencies.md"
    fi
done

cat >> "$VALIDATION_DIR/02_dependencies.md" << EOF

---

## Resumo UV

| Métrica | Valor |
|---------|-------|
| UV sync SUCCESS | $SUCCESS |
| UV sync FAILED | $FAILED |

EOF

echo "$SUCCESS|$FAILED"
