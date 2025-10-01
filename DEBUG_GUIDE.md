# 🔧 VERTICE PLATFORM - UNIFIED DEBUG GUIDE

> **Guia Completo de Debugging para Todo o Ecossistema Vertice**
> Frontend (React/Vite) • Backend (FastAPI/Python) • CLI (Typer/Gemini) • Docker Infrastructure

**Última atualização**: 2025-10-01
**Autor**: JuanCS-Dev
**Status**: Production-Ready

---

## 📑 ÍNDICE

1. [Visão Geral da Arquitetura](#1-visão-geral-da-arquitetura)
2. [Debugging do Frontend](#2-debugging-do-frontend)
3. [Debugging do Backend](#3-debugging-do-backend)
4. [Debugging do Vertice CLI](#4-debugging-do-vertice-cli)
5. [Debugging da Infraestrutura Docker](#5-debugging-da-infraestrutura-docker)
6. [Debugging de Serviços Específicos](#6-debugging-de-serviços-específicos)
7. [Troubleshooting Comum](#7-troubleshooting-comum)
8. [Ferramentas e Utilitários](#8-ferramentas-e-utilitários)
9. [Logs Centralizados](#9-logs-centralizados)
10. [Performance Profiling](#10-performance-profiling)

---

## 1. VISÃO GERAL DA ARQUITETURA

### Stack Completo

```
┌─────────────────────────────────────────────────────────────┐
│                      VERTICE PLATFORM                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   │
│  │   FRONTEND   │   │    BACKEND   │   │  VERTICE CLI │   │
│  │  React/Vite  │   │  FastAPI/Py  │   │  Typer/Gemini│   │
│  │  Port: 5173  │   │  Port: 8000  │   │   Standalone │   │
│  └──────────────┘   └──────────────┘   └──────────────┘   │
│         │                   │                   │           │
│         └───────────────────┴───────────────────┘           │
│                             │                                │
│              ┌──────────────┴──────────────┐                │
│              │     API GATEWAY (8000)      │                │
│              └──────────────┬──────────────┘                │
│                             │                                │
│    ┌────────────────────────┼────────────────────────┐      │
│    │                        │                        │      │
│  ┌─┴──────────┐   ┌────────┴────────┐   ┌─────────┴─────┐ │
│  │  Redis     │   │  21 Microservices│   │  Monitoring   │ │
│  │  (6379)    │   │  (8001-8017)     │   │  Prom/Grafana │ │
│  └────────────┘   └──────────────────┘   └───────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Serviços Backend (21 Microservices)

| Port | Service | Description |
|------|---------|-------------|
| 8000 | API Gateway | Entry point, routing |
| 8001 | SINESP Service | Vehicle intelligence |
| 8002 | Cyber Service | System security monitoring |
| 8003 | Domain Service | Domain/DNS analysis |
| 8004 | IP Intelligence | IP threat analysis |
| 8005 | Network Monitor | Real-time network monitoring |
| 8006 | Nmap Service | Port scanning |
| 8007 | OSINT Service | Open-source intelligence |
| 8008 | Aurora Predict | ML prediction engine |
| 8009 | Atlas Service | Geographic intelligence |
| 8010 | Auth Service | Authentication/authorization |
| 8011 | Vuln Scanner | Vulnerability scanning |
| 8012 | Social Engineering | Social eng simulation |
| 8013 | Threat Intel | Threat intelligence aggregation |
| 8014 | Malware Analysis | Malware scanning/analysis |
| 8015 | SSL Monitor | SSL/TLS certificate monitoring |
| 8016 | Aurora Orchestrator | AI orchestration layer |
| 8017 | AI Agent Service | Advanced AI agent (brain) |
| 9090 | Prometheus | Metrics collection |
| 3001 | Grafana | Metrics visualization |
| 6379 | Redis | Cache layer |

### Tecnologias

**Frontend**:
- React 18.2
- Vite 5.2
- Tailwind CSS 3.4
- CSS Modules
- Leaflet (maps)
- xterm.js (terminal)

**Backend**:
- FastAPI 0.104+
- Uvicorn
- Pydantic 2.4
- httpx (async HTTP)
- Redis 5.0
- Python 3.11+

**CLI**:
- Typer (CLI framework)
- Google Gemini API
- Rich (terminal UI)
- Questionary (prompts)

**Infrastructure**:
- Docker & Docker Compose
- Nginx (reverse proxy)
- Prometheus (metrics)
- Grafana (dashboards)

---

## 2. DEBUGGING DO FRONTEND

### 2.1. Setup de Desenvolvimento

```bash
# Navegue para o frontend
cd /home/juan/vertice-dev/frontend

# Instale dependências
npm install

# Inicie o dev server
npm run dev
# Acesse: http://localhost:5173
```

### 2.2. Problemas Comuns e Soluções

#### ❌ Erro: Build Failing com `@import must precede all other statements`

**Sintoma**:
```
@import must precede all other statements (besides @charset or empty @layer)
```

**Causa**: `@import` CSS após diretivas `@tailwind`

**Solução**:
```css
/* src/index.css */
/* ✅ CORRETO: imports ANTES de @tailwind */
@import './styles/themes.css';

@tailwind base;
@tailwind components;
@tailwind utilities;

/* ❌ ERRADO: imports DEPOIS */
@tailwind base;
@import './styles/themes.css'; /* Vai falhar */
```

#### ❌ Erro: `Could not resolve "../../../../styles/tokens/colors.css"`

**Sintoma**: Build falha buscando arquivos CSS em caminhos relativos quebrados

**Causa**: CSS modules importando tokens desnecessariamente (variáveis já são globais)

**Solução**:
```css
/* ❌ REMOVER imports desnecessários de *.module.css */
/* @import '../../../../styles/tokens/colors.css'; */
/* @import '../../../../styles/tokens/spacing.css'; */

/* ✅ Variáveis CSS já estão disponíveis globalmente via themes.css */
.myClass {
  color: var(--color-primary); /* Funciona sem import */
}
```

**Script para fix em massa**:
```bash
# Remove todos os @import de arquivos .module.css
find src -name "*.module.css" -type f -exec sed -i '/@import.*tokens/d' {} \;
```

#### ❌ Erro: `Expected ")" but found ";"`

**Sintoma**: Build falha com erro de sintaxe em componentes React

**Causa**: Padrão incorreto de `React.memo` com double parenthesis

**Código Problemático**:
```javascript
// ❌ ERRADO - double parenthesis
const Component = (({ props }) => {
  return <div>...</div>;
};

export default React.memo(Component);
```

**Solução**:
```javascript
// ✅ CORRETO - single parenthesis
const Component = ({ props }) => {
  return <div>...</div>;
};

export default React.memo(Component);
```

**Script de busca**:
```bash
# Encontra arquivos com double parenthesis
find src -name "*.jsx" -exec grep -l "^const.*= (({" {} \;
```

#### ❌ Erro: ESLint configuration invalid

**Sintoma**: `Invalid option '--ext' - perhaps you meant '-c'?`

**Causa**: ESLint 9.x mudou CLI interface

**Solução Temporária**:
```bash
# Skip linting, foque no build primeiro
npm run build
```

**Solução Permanente**:
```json
// package.json - atualizar script
{
  "scripts": {
    "lint": "eslint . --report-unused-disable-directives --max-warnings 0"
  }
}
```

#### ❌ Erro: `Could not resolve "../../../shared"`

**Sintoma**: Imports de componentes shared quebrados

**Causa**: Path relativo incorreto ou arquivo inexistente

**Debug**:
```bash
# Verifique se o diretório shared existe
ls -la src/components/shared/

# Verifique exports do index
cat src/components/shared/index.js
```

**Solução**:
```javascript
// Ajuste o path relativo
// De: import { Button } from '../../../shared'
// Para: import { Button } from '../../shared'

// Ou use path absoluto (configure vite.config.js)
import { Button } from '@/components/shared'
```

### 2.3. Build Process

```bash
# 1. Limpar cache
rm -rf node_modules/.vite
rm -rf dist/

# 2. Rebuild completo
npm run build

# 3. Verificar output
ls -la dist/
# Deve ter: index.html, assets/, vite.svg

# 4. Preview production build
npm run preview
# Acesse: http://localhost:4173
```

### 2.4. Debugging em Runtime

#### Browser DevTools

```javascript
// Enable React DevTools profiling
// Em qualquer componente:
console.log('[Component Name] props:', props);
console.log('[Component Name] state:', state);

// Performance measurement
performance.mark('start-operation');
// ... código
performance.mark('end-operation');
performance.measure('operation', 'start-operation', 'end-operation');
console.log(performance.getEntriesByName('operation'));
```

#### Vite Debug Mode

```bash
# Start com debug logs
DEBUG=vite:* npm run dev

# Ou apenas transforms
DEBUG=vite:transform npm run dev
```

#### Network Issues

```javascript
// src/api/client.js
import axios from 'axios';

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 10000,
});

// Interceptor para debug
client.interceptors.request.use(config => {
  console.log('[API Request]', config.method?.toUpperCase(), config.url);
  return config;
});

client.interceptors.response.use(
  response => {
    console.log('[API Response]', response.status, response.config.url);
    return response;
  },
  error => {
    console.error('[API Error]', error.response?.status, error.config?.url, error.message);
    return Promise.reject(error);
  }
);

export default client;
```

### 2.5. Testing

```bash
# Run unit tests
npm run test

# Run with UI
npm run test:ui

# Run with coverage
npm run test:coverage

# Watch mode
npm run test -- --watch
```

### 2.6. Checklist de Debug Frontend

```markdown
✅ Frontend Debug Checklist:

□ `npm install` completou sem erros
□ `npm run build` passa 100% (sem erros)
□ ESLint configurado corretamente
□ CSS imports em ordem correta (themes.css antes de @tailwind)
□ Nenhum import de tokens em *.module.css
□ Todos React.memo com sintaxe correta
□ Paths relativos corretos (../ vs ../../)
□ Environment variables configuradas (.env)
□ DevTools React extension instalada
□ Network tab mostra requests corretos
□ Console sem erros críticos
□ Hot reload funcionando
□ Production build testado (npm run preview)
```

---

## 3. DEBUGGING DO BACKEND

### 3.1. Setup de Desenvolvimento

```bash
# Navegue para o backend
cd /home/juan/vertice-dev/backend

# Ative o virtualenv (se necessário)
source ../.venv/bin/activate

# Ou use o venv do projeto
python3 -m venv venv
source venv/bin/activate

# Instale dependências de um serviço específico
cd services/ai_agent_service
pip install -r requirements.txt
```

### 3.2. Estrutura de Serviços

```
backend/
├── api_gateway/          # Entry point
├── services/
│   ├── ai_agent_service/
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   ├── reasoning_engine.py
│   │   ├── memory_system.py
│   │   ├── tools_world_class.py
│   │   └── tool_orchestrator.py
│   ├── aurora_orchestrator_service/
│   ├── threat_intel_service/
│   ├── malware_analysis_service/
│   ├── ... (18 outros serviços)
```

### 3.3. Problemas Comuns e Soluções

#### ❌ Erro: `ModuleNotFoundError: No module named 'fastapi'`

**Causa**: Dependências não instaladas

**Solução**:
```bash
cd backend/services/[service_name]
pip install -r requirements.txt

# Ou instale globalmente no venv do projeto
pip install fastapi uvicorn httpx pydantic python-dotenv redis
```

#### ❌ Erro: `ImportError: cannot import name 'ReasoningEngine'`

**Causa**: Módulos locais não encontrados (PYTHONPATH)

**Solução**:
```bash
# Opção 1: Run do diretório do serviço
cd backend/services/ai_agent_service
uvicorn main:app --reload

# Opção 2: Ajustar PYTHONPATH
export PYTHONPATH=/home/juan/vertice-dev/backend/services/ai_agent_service:$PYTHONPATH
python main.py

# Opção 3: Use Docker (recomendado)
docker-compose up ai_agent_service
```

#### ❌ Erro: Port Already in Use

**Sintoma**: `OSError: [Errno 98] Address already in use`

**Debug**:
```bash
# Descubra qual processo está usando a porta
lsof -i :8017
# ou
netstat -tulpn | grep 8017

# Mate o processo
kill -9 [PID]

# Ou use outra porta
uvicorn main:app --port 8018 --reload
```

#### ❌ Erro: Connection Refused ao chamar outro serviço

**Sintoma**: `httpx.ConnectError: [Errno 111] Connection refused`

**Causa**: Serviço dependente não está rodando

**Debug**:
```bash
# Liste todos os containers
docker ps

# Verifique se o serviço alvo está UP
docker ps | grep threat_intel_service

# Se não estiver, inicie-o
docker-compose up -d threat_intel_service

# Veja os logs
docker logs -f vertice-threat-intel
```

#### ❌ Erro: API Key Missing

**Sintoma**: `KeyError: 'ANTHROPIC_API_KEY'`

**Solução**:
```bash
# Crie .env na raiz do projeto
cd /home/juan/vertice-dev

cat > .env << EOF
# AI Services
ANTHROPIC_API_KEY=sk-ant-xxxxx
OPENAI_API_KEY=sk-xxxxx
GEMINI_API_KEY=xxxxx

# Threat Intelligence
ABUSEIPDB_API_KEY=xxxxx
VIRUSTOTAL_API_KEY=xxxxx
GREYNOISE_API_KEY=xxxxx
OTX_API_KEY=xxxxx

# Auth
GOOGLE_CLIENT_ID=xxxxx
GOOGLE_CLIENT_SECRET=xxxxx
JWT_SECRET=vertice-super-secret-key-2024

# Feature Flags
LLM_PROVIDER=anthropic
EOF

# Recarregue os containers
docker-compose down
docker-compose up -d
```

### 3.4. Running Services Standalone

```bash
# Modo 1: Uvicorn direto (desenvolvimento)
cd backend/services/ai_agent_service
uvicorn main:app --host 0.0.0.0 --port 8017 --reload

# Modo 2: Python direto (se main.py tem __main__)
python main.py

# Modo 3: Docker (produção-like)
docker-compose up ai_agent_service

# Modo 4: Docker com rebuild
docker-compose up --build ai_agent_service
```

### 3.5. Debugging com Logs

#### Adicionar Logs Detalhados

```python
# Em main.py de qualquer serviço
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Mude para INFO em produção
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Use em endpoints
@app.post("/analyze")
async def analyze(request: AnalysisRequest):
    logger.info(f"Received analysis request: {request.target}")

    try:
        result = await perform_analysis(request.target)
        logger.info(f"Analysis completed: {result.status}")
        return result
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

#### Ver Logs de Containers

```bash
# Logs de um serviço específico
docker logs -f vertice-ai-agent

# Logs com timestamp
docker logs -f --timestamps vertice-ai-agent

# Últimas 100 linhas
docker logs --tail 100 vertice-ai-agent

# Logs de todos os serviços
docker-compose logs -f

# Logs apenas do gateway
docker-compose logs -f api_gateway
```

### 3.6. Health Checks

```bash
# Check se o serviço está respondendo
curl http://localhost:8017/health

# Check todos os serviços via gateway
curl http://localhost:8000/health

# Check com jq para format bonito
curl -s http://localhost:8017/health | jq .
```

#### Implementar Health Check

```python
# Adicione em main.py de cada serviço
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ai_agent_service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "dependencies": {
            "redis": await check_redis(),
            "llm_api": await check_llm_api(),
        }
    }

async def check_redis():
    try:
        # Test Redis connection
        # return True if OK
        return {"status": "ok"}
    except:
        return {"status": "error"}
```

### 3.7. Interactive Debugging (pdb)

```python
# Adicione breakpoint no código
import pdb

@app.post("/analyze")
async def analyze(request: AnalysisRequest):
    pdb.set_trace()  # Execução vai pausar aqui

    # Ou use o builtin (Python 3.7+)
    breakpoint()

    result = await perform_analysis(request.target)
    return result
```

**Uso**:
```bash
# Run uvicorn em modo interativo (não --reload)
uvicorn main:app --host 0.0.0.0 --port 8017

# Faça request
curl -X POST http://localhost:8017/analyze -d '{"target":"test"}'

# Terminal vai entrar em debug mode:
# (Pdb) print(request)
# (Pdb) print(request.target)
# (Pdb) continue  # ou 'c' para continuar
```

### 3.8. Performance Profiling

```python
# Adicione profiling
import cProfile
import pstats
from io import StringIO

@app.post("/analyze")
async def analyze(request: AnalysisRequest):
    profiler = cProfile.Profile()
    profiler.enable()

    result = await perform_analysis(request.target)

    profiler.disable()
    s = StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats()

    logger.info(f"Profiling results:\n{s.getvalue()}")
    return result
```

### 3.9. Testing Backend

```bash
# Run pytest em um serviço
cd backend/services/ai_agent_service
pytest test_world_class_tools.py -v

# Run com coverage
pytest --cov=. --cov-report=html

# Run apenas testes de integração
pytest -m integration

# Run com output detalhado
pytest -vv -s
```

### 3.10. Checklist de Debug Backend

```markdown
✅ Backend Debug Checklist:

□ Python 3.11+ instalado
□ Virtualenv ativado
□ `pip install -r requirements.txt` completou
□ .env configurado com todas as API keys
□ Redis rodando (docker ou local)
□ Port desejada livre (não em uso)
□ PYTHONPATH correto (se rodando fora do Docker)
□ Dependências externas acessíveis (APIs de terceiros)
□ Health check respondendo /health
□ Logs configurados (logging.basicConfig)
□ Tratamento de exceções em todos endpoints
□ Timeout configurado em httpx.AsyncClient
□ CORS configurado no FastAPI (se necessário)
□ Docker compose up sem erros
```

---

## 4. DEBUGGING DO VERTICE CLI

### 4.1. Setup

```bash
cd /home/juan/vertice-dev/vertice_cli

# Criar virtualenv
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Configurar .env
cp .env.example .env
# Edite e adicione GEMINI_API_KEY
```

### 4.2. Estrutura

```
vertice_cli/
├── cli.py              # Main CLI commands (Oráculo, Eureka, etc.)
├── main_cli.py         # Alternative entry point
├── utils.py            # Utilities (console, banner, git)
├── utils/              # Utility modules
├── modules/            # Additional modules
├── requirements.txt
└── .env.example
```

### 4.3. Running CLI

```bash
# Modo 1: Python direto
python cli.py --help

# Modo 2: Make executable
chmod +x cli.py
./cli.py --help

# Modo 3: Install como package (recomendado)
pip install -e .
vertice --help
```

### 4.4. Problemas Comuns

#### ❌ Erro: `No module named 'google.generativeai'`

**Solução**:
```bash
pip install google-generativeai
```

#### ❌ Erro: `KeyError: 'GEMINI_API_KEY'`

**Solução**:
```bash
# Adicione ao .env
echo "GEMINI_API_KEY=your-key-here" >> .env

# Ou export temporário
export GEMINI_API_KEY=your-key-here
```

#### ❌ Erro: CLI não encontra comandos

**Debug**:
```python
# Em cli.py, adicione debug
@app.callback()
def main():
    """Vertice CLI."""
    import sys
    print(f"Python path: {sys.path}")
    print(f"Current dir: {os.getcwd()}")
```

### 4.5. Debugging CLI Commands

```python
# Adicione verbose mode
@app.command()
def oraculo(verbose: bool = False):
    """Gera ideias técnicas."""

    if verbose:
        console.print("[cyan]Debug mode enabled[/cyan]")
        console.print(f"Working dir: {os.getcwd()}")
        console.print(f"Files collected: {len(files)}")

    # ... resto do código
```

**Uso**:
```bash
python cli.py oraculo --verbose
```

### 4.6. Gemini API Debugging

```python
# Test connection
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel('gemini-1.5-pro-latest')

response = model.generate_content("Hello world")
print(response.text)
```

#### Rate Limiting

```python
import time
from functools import wraps

def rate_limit(calls_per_minute=15):
    """Decorator para rate limiting."""
    min_interval = 60.0 / calls_per_minute
    last_called = [0.0]

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed

            if left_to_wait > 0:
                time.sleep(left_to_wait)

            last_called[0] = time.time()
            return func(*args, **kwargs)
        return wrapper
    return decorator

@rate_limit(calls_per_minute=15)
def call_gemini(prompt):
    response = model.generate_content(prompt)
    return response.text
```

### 4.7. Git Integration Debug

```python
# Test git commands
from utils import git_safe_execute

# Check if git repo
result = git_safe_execute("git status")
print(result)

# Check branch
result = git_safe_execute("git branch --show-current")
print(f"Current branch: {result.strip()}")
```

### 4.8. Checklist CLI Debug

```markdown
✅ CLI Debug Checklist:

□ Python 3.11+ instalado
□ Virtualenv ativado
□ Dependências instaladas (requirements.txt)
□ .env configurado com GEMINI_API_KEY
□ Typer instalado corretamente
□ Rich e Questionary funcionando
□ Git disponível no PATH
□ Permissão de execução (chmod +x)
□ CLI entry point correto (app = typer.Typer())
□ Comandos registrados (@app.command())
□ Utils funcionando (banner, console)
□ Rate limiting implementado para API
```

---

## 5. DEBUGGING DA INFRAESTRUTURA DOCKER

### 5.1. Docker Compose Basics

```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d ai_agent_service

# Stop all
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Rebuild
docker-compose up --build

# View status
docker-compose ps

# View logs
docker-compose logs -f [service_name]
```

### 5.2. Problemas Comuns

#### ❌ Erro: `Cannot start service X: port is already allocated`

**Debug**:
```bash
# Encontre o processo usando a porta
sudo lsof -i :8017

# Mate o processo
sudo kill -9 [PID]

# Ou mude a porta no docker-compose.yml
ports:
  - "8018:80"  # Mude 8017 para 8018
```

#### ❌ Erro: Container reiniciando constantemente

**Debug**:
```bash
# Veja os logs
docker logs vertice-ai-agent

# Check exit code
docker inspect vertice-ai-agent | grep -A 5 "State"

# Run interativo para debug
docker run -it --rm vertice-ai-agent /bin/bash
```

#### ❌ Erro: Cannot connect to Docker daemon

**Solução**:
```bash
# Start Docker service
sudo systemctl start docker

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Test
docker ps
```

#### ❌ Erro: Network vertice-network not found

**Solução**:
```bash
# Recrie a network
docker network create vertice-network

# Ou deixe o compose criar
docker-compose down
docker-compose up -d
```

### 5.3. Service Communication Debug

```bash
# Enter em um container
docker exec -it vertice-ai-agent /bin/bash

# Dentro do container, teste conectividade
curl http://threat_intel_service/health
curl http://redis:6379

# Test DNS resolution
nslookup threat_intel_service
ping threat_intel_service

# Check environment variables
env | grep SERVICE_URL
```

### 5.4. Volume Issues

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect vertice-dev_redis-data

# Remove unused volumes
docker volume prune

# Recreate volume
docker-compose down -v
docker-compose up -d
```

### 5.5. Resource Monitoring

```bash
# Check resource usage
docker stats

# Check disk usage
docker system df

# Clean up
docker system prune -a
```

### 5.6. Networking Debug

```bash
# Inspect network
docker network inspect vertice-network

# Check service IPs
docker inspect -f '{{.NetworkSettings.Networks.vertice-network.IPAddress}}' vertice-ai-agent

# Test connectivity between containers
docker exec vertice-ai-agent ping vertice-threat-intel
```

### 5.7. Checklist Docker Debug

```markdown
✅ Docker Debug Checklist:

□ Docker daemon running (sudo systemctl status docker)
□ User in docker group (groups | grep docker)
□ docker-compose.yml syntax válido
□ Todas as portas livres (não em uso)
□ .env file presente na raiz
□ Networks criadas (docker network ls)
□ Volumes criados (docker volume ls)
□ Todos containers UP (docker-compose ps)
□ Logs sem erros críticos (docker-compose logs)
□ Services comunicando entre si (curl interno)
□ Health checks passando
□ Resources suficientes (RAM, disk)
```

---

## 6. DEBUGGING DE SERVIÇOS ESPECÍFICOS

### 6.1. AI Agent Service (Port 8017)

**Componentes**:
- Reasoning Engine (chain-of-thought)
- Memory System (short/long-term)
- Tool Orchestrator (parallel execution)
- World-Class Tools (21 tools)

**Debug Específico**:
```bash
# Test reasoning engine
curl -X POST http://localhost:8017/think \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Analyze IP 1.2.3.4",
    "context": "security"
  }'

# Test tool execution
curl -X POST http://localhost:8017/execute-tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "ip_intelligence",
    "parameters": {"ip": "1.2.3.4"}
  }'

# Check memory
curl http://localhost:8017/memory/context/session-123
```

**Logs Importantes**:
```python
logger.info(f"[ReasoningEngine] Starting thought chain for: {query}")
logger.info(f"[ToolOrchestrator] Executing {len(tools)} tools in parallel")
logger.info(f"[MemorySystem] Retrieved {len(memories)} relevant memories")
```

### 6.2. Aurora Orchestrator (Port 8016)

**Purpose**: Coordena múltiplos serviços para análise holística

**Debug**:
```bash
# Comprehensive analysis
curl -X POST http://localhost:8016/orchestrate \
  -H "Content-Type: application/json" \
  -d '{
    "target": "example.com",
    "analysis_types": ["domain", "ssl", "threat_intel", "vuln_scan"]
  }'

# Check orchestration status
curl http://localhost:8016/status/[job_id]
```

### 6.3. Threat Intel Service (Port 8013)

**APIs Integradas**:
- AbuseIPDB
- VirusTotal
- GreyNoise
- AlienVault OTX

**Debug**:
```bash
# Test API keys
curl http://localhost:8013/check-keys

# IP reputation
curl "http://localhost:8013/ip/1.2.3.4"

# Domain reputation
curl "http://localhost:8013/domain/malicious.com"
```

**Common Issues**:
- API key inválida: Check .env
- Rate limit: Implement caching
- Timeout: Increase httpx timeout

### 6.4. Malware Analysis (Port 8014)

**Debug**:
```bash
# Upload file for analysis
curl -X POST http://localhost:8014/analyze \
  -F "file=@suspicious.exe"

# Check analysis status
curl http://localhost:8014/analysis/[hash]
```

### 6.5. Network Monitor (Port 8005)

**Requirements**: Precisa de `NET_ADMIN` e `NET_RAW` capabilities

**Debug**:
```bash
# Check capabilities
docker exec vertice-network-monitor capsh --print

# Start monitoring
curl -X POST http://localhost:8005/start

# Get events
curl http://localhost:8005/events

# Stop monitoring
curl -X POST http://localhost:8005/stop
```

### 6.6. OSINT Service (Port 8007)

**Features**:
- Social media investigation
- Breach data search
- Google dorking
- Dark web monitoring

**Debug**:
```bash
# Social media investigation
curl -X POST http://localhost:8007/investigate \
  -H "Content-Type: application/json" \
  -d '{
    "target": "username",
    "platforms": ["twitter", "linkedin", "github"]
  }'

# Breach data search
curl "http://localhost:8007/breach/email@example.com"
```

---

## 7. TROUBLESHOOTING COMUM

### 7.1. Frontend não conecta ao Backend

**Sintoma**: CORS errors, network failed

**Debug**:
```javascript
// Check API URL
console.log('API URL:', import.meta.env.VITE_API_URL);

// Test connectivity
fetch('http://localhost:8000/health')
  .then(r => r.json())
  .then(d => console.log('Backend:', d))
  .catch(e => console.error('Error:', e));
```

**Solução**:
```python
# Em api_gateway/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 7.2. Redis Connection Failed

**Debug**:
```bash
# Test Redis
docker exec -it vertice-redis redis-cli ping
# Deve retornar: PONG

# Check connections
docker exec -it vertice-redis redis-cli INFO clients

# Monitor commands
docker exec -it vertice-redis redis-cli MONITOR
```

**Solução**:
```python
# Em qualquer serviço usando Redis
import redis

try:
    r = redis.Redis(host='redis', port=6379, decode_responses=True)
    r.ping()
    logger.info("Redis connection OK")
except redis.ConnectionError as e:
    logger.error(f"Redis connection failed: {e}")
```

### 7.3. High Memory Usage

**Debug**:
```bash
# Check memory by container
docker stats --no-stream

# Check memory limit
docker inspect vertice-ai-agent | grep -i memory

# Set memory limit
# Em docker-compose.yml:
services:
  ai_agent_service:
    mem_limit: 2g
    mem_reservation: 1g
```

### 7.4. Slow Response Times

**Debug**:
```bash
# Time requests
time curl http://localhost:8017/health

# Detailed timing
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8017/analyze

# curl-format.txt:
# time_total:  %{time_total}\n
# time_connect:  %{time_connect}\n
# time_starttransfer:  %{time_starttransfer}\n
```

**Solutions**:
- Add caching (Redis)
- Implement async operations
- Use connection pooling
- Optimize database queries
- Add pagination

### 7.5. Database Locks (se usar PostgreSQL/MySQL)

```sql
-- Check active locks
SELECT * FROM pg_locks WHERE granted = false;

-- Kill long-running queries
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'active' AND query_start < NOW() - INTERVAL '5 minutes';
```

---

## 8. FERRAMENTAS E UTILITÁRIOS

### 8.1. Health Check Script

```bash
#!/bin/bash
# health_check.sh

SERVICES=(
  "8000:API Gateway"
  "8001:SINESP"
  "8002:Cyber"
  "8003:Domain"
  "8004:IP Intel"
  "8005:Network Monitor"
  "8006:Nmap"
  "8007:OSINT"
  "8008:Aurora Predict"
  "8009:Atlas"
  "8010:Auth"
  "8011:Vuln Scanner"
  "8012:Social Eng"
  "8013:Threat Intel"
  "8014:Malware Analysis"
  "8015:SSL Monitor"
  "8016:Aurora Orchestrator"
  "8017:AI Agent"
)

echo "=== VERTICE HEALTH CHECK ==="
for service in "${SERVICES[@]}"; do
  port="${service%%:*}"
  name="${service##*:}"

  if curl -s -f "http://localhost:$port/health" > /dev/null; then
    echo "✅ $name (port $port): HEALTHY"
  else
    echo "❌ $name (port $port): DOWN"
  fi
done

echo ""
echo "=== INFRASTRUCTURE ==="
docker exec vertice-redis redis-cli ping > /dev/null 2>&1 && echo "✅ Redis: OK" || echo "❌ Redis: DOWN"
curl -s http://localhost:9090/-/healthy > /dev/null && echo "✅ Prometheus: OK" || echo "❌ Prometheus: DOWN"
curl -s http://localhost:3001/api/health > /dev/null && echo "✅ Grafana: OK" || echo "❌ Grafana: DOWN"
```

**Uso**:
```bash
chmod +x health_check.sh
./health_check.sh
```

### 8.2. Log Aggregation Script

```bash
#!/bin/bash
# aggregate_logs.sh

OUTPUT_DIR="./logs_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUTPUT_DIR"

echo "Collecting logs to $OUTPUT_DIR..."

# Frontend logs
npm run build > "$OUTPUT_DIR/frontend_build.log" 2>&1

# Backend logs
for service in $(docker-compose ps --services); do
  echo "Collecting logs from $service..."
  docker logs "$service" > "$OUTPUT_DIR/${service}.log" 2>&1
done

# Docker stats
docker stats --no-stream > "$OUTPUT_DIR/docker_stats.txt"

# System info
df -h > "$OUTPUT_DIR/disk_usage.txt"
free -h > "$OUTPUT_DIR/memory_usage.txt"

echo "Logs collected in $OUTPUT_DIR"
tar -czf "${OUTPUT_DIR}.tar.gz" "$OUTPUT_DIR"
echo "Archive created: ${OUTPUT_DIR}.tar.gz"
```

### 8.3. Performance Test Script

```bash
#!/bin/bash
# perf_test.sh

echo "=== VERTICE PERFORMANCE TEST ==="

# Test API Gateway
echo "Testing API Gateway..."
ab -n 1000 -c 10 http://localhost:8000/health

# Test AI Agent
echo "Testing AI Agent..."
ab -n 100 -c 5 -p request.json -T application/json http://localhost:8017/analyze

# Test Threat Intel
echo "Testing Threat Intel..."
ab -n 500 -c 10 http://localhost:8013/ip/8.8.8.8

echo "Tests completed!"
```

### 8.4. Database Backup Script (se aplicável)

```bash
#!/bin/bash
# backup_db.sh

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Backup Redis
docker exec vertice-redis redis-cli SAVE
docker cp vertice-redis:/data/dump.rdb "$BACKUP_DIR/redis_$TIMESTAMP.rdb"

# Backup volumes
docker run --rm -v vertice-dev_redis-data:/data -v "$BACKUP_DIR":/backup alpine tar czf /backup/redis-volume_$TIMESTAMP.tar.gz /data

echo "Backup completed: $BACKUP_DIR"
```

---

## 9. LOGS CENTRALIZADOS

### 9.1. Loki + Grafana (Opcional)

```yaml
# docker-compose.yml - adicionar
loki:
  image: grafana/loki:latest
  ports:
    - "3100:3100"
  volumes:
    - ./loki-config.yml:/etc/loki/local-config.yaml
  networks:
    - vertice-network

promtail:
  image: grafana/promtail:latest
  volumes:
    - /var/log:/var/log
    - ./promtail-config.yml:/etc/promtail/config.yml
  networks:
    - vertice-network
```

### 9.2. Structured Logging

```python
# Implemente em todos os serviços
import structlog

logger = structlog.get_logger()

@app.post("/analyze")
async def analyze(request: AnalysisRequest):
    logger.info(
        "analysis_started",
        target=request.target,
        user_id=request.user_id,
        timestamp=datetime.utcnow().isoformat()
    )

    try:
        result = await perform_analysis(request.target)
        logger.info("analysis_completed", target=request.target, status="success")
        return result
    except Exception as e:
        logger.error("analysis_failed", target=request.target, error=str(e), exc_info=True)
        raise
```

---

## 10. PERFORMANCE PROFILING

### 10.1. Frontend Performance

```javascript
// src/utils/performance.js
export const measurePerformance = (name, fn) => {
  const start = performance.now();
  const result = fn();
  const end = performance.now();

  console.log(`[Performance] ${name}: ${(end - start).toFixed(2)}ms`);

  // Send to analytics
  if (window.gtag) {
    window.gtag('event', 'timing_complete', {
      name: name,
      value: Math.round(end - start),
    });
  }

  return result;
};

// Uso:
measurePerformance('fetchData', () => {
  return axios.get('/api/data');
});
```

### 10.2. Backend Performance

```python
# Add profiling middleware
from time import time
from starlette.middleware.base import BaseHTTPMiddleware

class PerformanceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time()
        response = await call_next(request)
        duration = time() - start

        response.headers["X-Process-Time"] = str(duration)

        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            duration=duration,
            status_code=response.status_code
        )

        return response

app.add_middleware(PerformanceMiddleware)
```

### 10.3. Load Testing

```bash
# Install locust
pip install locust

# Create locustfile.py
cat > locustfile.py << 'EOF'
from locust import HttpUser, task, between

class VerticeUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def health_check(self):
        self.client.get("/health")

    @task(1)
    def analyze_ip(self):
        self.client.post("/api/ip/analyze", json={"ip": "8.8.8.8"})
EOF

# Run load test
locust -f locustfile.py --host=http://localhost:8000
# Acesse: http://localhost:8089
```

---

## 🎯 QUICK REFERENCE CARD

```
┌─────────────────────────────────────────────────────────────┐
│                  VERTICE DEBUG CHEAT SHEET                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ FRONTEND                                                     │
│ • Dev:     npm run dev                                       │
│ • Build:   npm run build                                     │
│ • Test:    npm run test                                      │
│ • URL:     http://localhost:5173                             │
│                                                              │
│ BACKEND                                                      │
│ • Start All:  docker-compose up -d                           │
│ • Logs:       docker-compose logs -f [service]               │
│ • Health:     curl http://localhost:8000/health              │
│ • Restart:    docker-compose restart [service]               │
│                                                              │
│ CLI                                                          │
│ • Run:     python cli.py --help                              │
│ • Env:     source venv/bin/activate                          │
│ • Test:    python cli.py oraculo                             │
│                                                              │
│ DOCKER                                                       │
│ • Status:  docker-compose ps                                 │
│ • Logs:    docker logs -f [container]                        │
│ • Shell:   docker exec -it [container] /bin/bash             │
│ • Clean:   docker system prune -a                            │
│                                                              │
│ COMMON PORTS                                                 │
│ • 5173:  Frontend Dev Server                                 │
│ • 8000:  API Gateway                                         │
│ • 8017:  AI Agent Service                                    │
│ • 6379:  Redis                                               │
│ • 9090:  Prometheus                                          │
│ • 3001:  Grafana                                             │
│                                                              │
│ EMERGENCY COMMANDS                                           │
│ • Kill port:  sudo lsof -i :[port] | grep LISTEN | awk '{print $2}' | xargs kill -9
│ • Restart all: docker-compose down && docker-compose up -d   │
│ • Clear cache: rm -rf node_modules/.vite dist/ && npm install│
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📝 NOTAS FINAIS

Este guia cobre os cenários mais comuns de debugging. Para problemas específicos:

1. **Check os logs primeiro**: 90% dos problemas estão nos logs
2. **Isole o problema**: Frontend? Backend? Networking?
3. **Use health checks**: Valide que dependências estão UP
4. **Test incrementalmente**: Um componente por vez
5. **Document issues**: Mantenha um log de problemas recorrentes

**Manutenção deste documento**:
- Atualize com novos serviços
- Adicione troubleshooting conforme surgem
- Versione no git

**Contribuições**:
- Issues resolvidos devem ser adicionados aqui
- Soluções criativas devem ser compartilhadas
- Mantenha exemplos práticos e testados

---

**Última atualização**: 2025-10-01
**Versão**: 1.0.0
**Mantido por**: JuanCS-Dev

**Links Úteis**:
- Repositório: `/home/juan/vertice-dev`
- Documentação: `/home/juan/vertice-dev/docs`
- Issues: Track problemas conhecidos

---

*"Debug is twice as hard as writing the code in the first place. Therefore, if you write the code as cleverly as possible, you are, by definition, not smart enough to debug it." - Brian Kernighan*
