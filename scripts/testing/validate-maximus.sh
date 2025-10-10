#!/bin/bash

echo "🧠 VALIDANDO MAXIMUS AI COMPONENTS..."

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
    else
        echo -e "${RED}✗${NC} $1"
    fi
}

# Check files
echo -e "\n📁 Verificando arquivos..."
test -f backend/services/maximus_oraculo/oraculo.py
check "Oráculo main file"

test -f backend/services/maximus_eureka/eureka.py
check "Eureka main file"

test -f backend/services/maximus_integration_service/main.py
check "Integration service"

test -f frontend/src/components/maximus/MaximusDashboard.jsx
check "Frontend dashboard"

test -f frontend/src/api/maximusService.js
check "API client"

# Check Python syntax
echo -e "\n🐍 Verificando sintaxe Python..."
python3 -m py_compile backend/services/maximus_oraculo/oraculo.py 2>/dev/null
check "Oráculo syntax"

python3 -m py_compile backend/services/maximus_eureka/eureka.py 2>/dev/null
check "Eureka syntax"

python3 -m py_compile backend/services/maximus_integration_service/main.py 2>/dev/null
check "Integration syntax"

# Check React components
echo -e "\n⚛️  Verificando componentes React..."
grep -q "MaximusDashboard" frontend/src/components/maximus/MaximusDashboard.jsx
check "Dashboard component"

grep -q "maximusService" frontend/src/api/maximusService.js
check "API service"

# Check docker-compose
echo -e "\n🐳 Verificando Docker config..."
grep -q "maximus_integration_service" docker-compose.yml
check "Docker-compose entry"

echo -e "\n${GREEN}════════════════════════════════════${NC}"
echo -e "${GREEN}✓ VALIDAÇÃO COMPLETA!${NC}"
echo -e "${GREEN}════════════════════════════════════${NC}"
