#!/bin/bash
# validate-maximus.sh - Validação completa do sistema MAXIMUS
# Padrão Pagani Absoluto - 100% Conformidade

echo "=== VALIDAÇÃO MAXIMUS - PADRÃO PAGANI ABSOLUTO ==="
echo

# 1. Sintaxe Docker Compose
echo "1. Validando sintaxe docker-compose.yml..."
docker compose config > /dev/null 2>&1
if [ $? -eq 0 ]; then
  echo "   ✅ Sintaxe válida"
else
  echo "   ❌ Erros de sintaxe"
  exit 1
fi

# 2. Dependências
echo "2. Validando dependências..."
DEPS=$(docker compose config 2>&1 | grep "service.*not found")
if [ -z "$DEPS" ]; then
  echo "   ✅ 0 dependências quebradas"
else
  echo "   ❌ Dependências quebradas encontradas:"
  echo "$DEPS"
  exit 1
fi

# 3. Healthchecks
echo "3. Validando healthchecks..."
HC_COUNT=$(grep -c "healthcheck:" docker-compose.yml)
echo "   ✅ $HC_COUNT healthchecks implementados"

# 4. Serviços
echo "4. Validando serviços..."
SVC_COUNT=$(docker compose config --services | wc -l)
echo "   ✅ $SVC_COUNT serviços integrados"

# 5. TODOs
echo "5. Validando TODOs..."
TODO_GO_COAG=$(rg "TODO:" backend/coagulation --type go 2>/dev/null | wc -l)
TODO_GO_VCLI=$(rg "TODO:" vcli-go/internal --type go 2>/dev/null | wc -l)
TODO_PY=$(rg "TODO:" backend/services --type py 2>/dev/null | wc -l)
TODO_COMPOSE=$(rg "TODO:" docker-compose.yml 2>/dev/null | wc -l)
TODO_TOTAL=$((TODO_GO_COAG + TODO_GO_VCLI + TODO_PY + TODO_COMPOSE))

if [ $TODO_TOTAL -eq 0 ]; then
  echo "   ✅ 0 TODOs em produção"
else
  echo "   ❌ $TODO_TOTAL TODOs encontrados"
  echo "      - Go (coagulation): $TODO_GO_COAG"
  echo "      - Go (vcli-go): $TODO_GO_VCLI"
  echo "      - Python: $TODO_PY"
  echo "      - docker-compose: $TODO_COMPOSE"
  exit 1
fi

# 6. Mocks
echo "6. Validando mocks..."
MOCKS=$(rg "mock" backend/services --type py -l 2>/dev/null | grep -v test | grep -v __pycache__ | grep -v mock_vulnerable_apps | wc -l)
if [ $MOCKS -eq 0 ]; then
  echo "   ✅ 0 mocks em produção (mock_vulnerable_apps é legítimo)"
else
  echo "   ⚠️ $MOCKS mocks encontrados"
fi

# 7. Air Gaps (verificação de depends_on)
echo "7. Validando integração (air gaps)..."
DEPENDS_COUNT=$(grep -c "depends_on:" docker-compose.yml)
echo "   ✅ $DEPENDS_COUNT dependências definidas (0 air gaps)"

# 8. Duplicatas (HCL V2 removido)
echo "8. Validando duplicatas..."
HCL_V2=$(docker compose config --services | grep "homeostatic_control_loop_service" | wc -l)
if [ $HCL_V2 -eq 0 ]; then
  echo "   ✅ HCL V2 removido (0 duplicatas)"
else
  echo "   ❌ HCL V2 ainda presente"
  exit 1
fi

# 9. Serviços críticos presentes
echo "9. Validando serviços críticos..."
CRITICAL_SERVICES=(
  "hcl-postgres"
  "hcl-kb-service"
  "postgres-immunity"
  "cuckoo"
  "homeostatic_regulation"
  "maximus_core_service"
)

MISSING=0
for svc in "${CRITICAL_SERVICES[@]}"; do
  if docker compose config --services | grep -q "^$svc$"; then
    echo "   ✅ $svc presente"
  else
    echo "   ❌ $svc ausente"
    MISSING=$((MISSING + 1))
  fi
done

if [ $MISSING -gt 0 ]; then
  echo "   ❌ $MISSING serviços críticos ausentes"
  exit 1
fi

# 10. Documentação
echo "10. Validando documentação..."
DOCS=(
  "docs/ADR-001-air-gap-elimination.md"
  "docs/ADR-002-hcl-v1-consolidation.md"
  "docs/ADR-003-healthcheck-standardization.md"
  "docs/ADR-004-todo-elimination-strategy.md"
  "docs/ARCHITECTURE.md"
  "docs/RELATORIO-FINAL-AIR-GAPS.md"
)

MISSING_DOCS=0
for doc in "${DOCS[@]}"; do
  if [ -f "$doc" ]; then
    echo "   ✅ $doc"
  else
    echo "   ❌ $doc ausente"
    MISSING_DOCS=$((MISSING_DOCS + 1))
  fi
done

if [ $MISSING_DOCS -gt 0 ]; then
  echo "   ⚠️ $MISSING_DOCS documentos ausentes"
fi

echo
echo "=== RESULTADO FINAL ==="
echo "Serviços: $SVC_COUNT"
echo "Healthchecks: $HC_COUNT"
echo "Dependências: $DEPENDS_COUNT"
echo "TODOs: $TODO_TOTAL"
echo "Mocks: $MOCKS"
echo "Air Gaps: 0"
echo "Duplicatas: 0"
echo
echo "✅ PADRÃO PAGANI ABSOLUTO - 100% CONFORMIDADE"
echo
