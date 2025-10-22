#!/bin/bash
VALIDATION_DIR=$(cat /tmp/validation_dir.txt)

# FASE 5: Config
cat > "$VALIDATION_DIR/05_config.md" << 'HEADER'
# VALIDAÇÃO DE CONFIGURAÇÃO - FASE 5

HEADER

cd /home/juan/vertice-dev

echo "## Environment" >> "$VALIDATION_DIR/05_config.md"
if [ -f ".env" ]; then
    VAR_COUNT=$(grep -v "^#" .env | grep -v "^$" | wc -l)
    echo "- ✅ \`.env\` ($VAR_COUNT variáveis)" >> "$VALIDATION_DIR/05_config.md"
else
    echo "- ⚠️ \`.env\` não encontrado" >> "$VALIDATION_DIR/05_config.md"
fi

[ -f ".env.example" ] && echo "- ✅ \`.env.example\`" >> "$VALIDATION_DIR/05_config.md" || echo "- ⚠️ \`.env.example\` recomendado" >> "$VALIDATION_DIR/05_config.md"

echo "" >> "$VALIDATION_DIR/05_config.md"
echo "## Ports" >> "$VALIDATION_DIR/05_config.md"
for PORT in 8000 5432 6379; do
    if lsof -i:$PORT &>/dev/null; then
        echo "- ⚠️ Porta $PORT em uso" >> "$VALIDATION_DIR/05_config.md"
    else
        echo "- ✅ Porta $PORT disponível" >> "$VALIDATION_DIR/05_config.md"
    fi
done

# FASE 6: Docs
cat > "$VALIDATION_DIR/06_documentation.md" << 'HEADER'
# VALIDAÇÃO DE DOCUMENTAÇÃO - FASE 6

HEADER

echo "## README por Serviço" >> "$VALIDATION_DIR/06_documentation.md"
cd backend/services
GOOD_DOCS=0
POOR_DOCS=0
NO_DOCS=0

for SERVICE in */; do
    if [ -f "${SERVICE}README.md" ]; then
        LINES=$(wc -l < "${SERVICE}README.md")
        if [ "$LINES" -gt 20 ]; then
            ((GOOD_DOCS++))
        else
            echo "- ⚠️ ${SERVICE%/}: $LINES linhas (curto)" >> "$VALIDATION_DIR/06_documentation.md"
            ((POOR_DOCS++))
        fi
    else
        ((NO_DOCS++))
    fi
done

echo "" >> "$VALIDATION_DIR/06_documentation.md"
echo "**Documentação:** $GOOD_DOCS bons / $POOR_DOCS curtos / $NO_DOCS sem README" >> "$VALIDATION_DIR/06_documentation.md"

# FASE 7: Server (skip - too risky)
cat > "$VALIDATION_DIR/07_server.md" << 'EOF'
# VALIDAÇÃO DE SERVIDOR - FASE 7

⚠️ **SKIP**: Validação de servidor pulada devido a:
- Múltiplos erros de import detectados
- Dependências faltantes
- Configurações Pydantic com problemas

**Recomendação:** Corrigir imports e dependências antes de tentar subir servidor.
EOF

echo "SKIP"
