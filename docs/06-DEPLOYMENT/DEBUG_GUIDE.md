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

### 5.7. Volume Mounts vs Image Code (CRÍTICO)

**⚠️ ARMADILHA COMUM**: Volume mounts SOBRESCREVEM código da imagem Docker, mesmo após rebuild!

#### Problema

```yaml
# docker-compose.yml
services:
  my_service:
    build: ./backend/services/my_service
    volumes:
      - ./backend/services/my_service:/app  # ⚠️ SOBRESCREVE a imagem!
```

**Cenário**:
1. Você corrige um bug no código HOST (`my_service/main.py`)
2. Faz rebuild: `docker compose build my_service`
3. Container AINDA falha com o erro antigo! 😱

**Causa**: O volume mount `-v ./backend/services/my_service:/app` monta o diretório HOST sobre `/app` no container, **ignorando** os arquivos da imagem.

#### Diagnóstico

```bash
# 1. Verifique se tem volume mount
docker inspect my_service | grep -A 10 '"Mounts"'

# 2. Compare checksums (HOST vs Container)
md5sum /home/juan/vertice-dev/backend/services/my_service/main.py
docker exec my_service md5sum /app/main.py
# Se diferentes = problema!

# 3. Verifique timestamps
ls -l backend/services/my_service/main.py  # Modificado HOJE
docker exec my_service ls -l /app/main.py   # Modificado SEMANA PASSADA
```

#### Soluções

**Opção 1: Remover volume mount (Produção)**
```yaml
# docker-compose.yml
services:
  my_service:
    build: ./backend/services/my_service
    # volumes:  # ❌ REMOVER em produção
    #   - ./backend/services/my_service:/app
```

**Opção 2: Rebuild SEM cache**
```bash
docker compose build --no-cache my_service
docker compose up -d my_service
```

**Opção 3: Docker cp (Quick fix para builds demorados)**
```bash
# Útil quando Dockerfile demora >5min (ex: compila Hyperscan)
docker cp ./backend/services/my_service/main.py my_service:/app/
docker cp ./backend/services/my_service/utils.py my_service:/app/
docker restart my_service
```

**Opção 4: Limpar cache Python**
```bash
# Bytecode cache pode persistir com código antigo
docker exec my_service find /app -type d -name __pycache__ -exec rm -rf {} +
docker exec my_service find /app -type f -name "*.pyc" -delete
docker restart my_service
```

#### Caso Real: RTE Service

**Problema**: Container rodava código de 3 dias atrás (com Hyperscan real), HOST tinha código novo (MockHyperscan).

```bash
# Diagnóstico
$ docker exec rte-service head -20 /app/hyperscan_matcher.py | grep "import hyperscan"
import hyperscan  # ⚠️ Código ANTIGO!

$ head -20 ./backend/services/rte_service/hyperscan_matcher.py | grep "class Mock"
class MockHyperscan:  # ✅ Código NOVO!

# Solução: docker cp (rebuild demoraria 10+ min compilando Hyperscan)
$ docker cp ./backend/services/rte_service/hyperscan_matcher.py rte-service:/app/
$ docker cp ./backend/services/rte_service/main.py rte-service:/app/
$ docker restart rte-service
# ✅ Funcionou!
```

#### 📊 Tabela Comparativa das Soluções

| Solução | Velocidade | Persistência | Quando Usar | Limitações |
|---------|------------|--------------|-------------|------------|
| **Opção 1: Remover volume mount** | ⚠️ Lenta (rebuild completo) | ✅ Permanente | Produção, CI/CD | Perde hot-reload em dev |
| **Opção 2: Rebuild --no-cache** | ⚠️ Muito lenta (5-30min) | ✅ Permanente | Build complexos (dependências sistema) | Alto consumo de CPU/memória |
| **Opção 3: docker cp** | ✅ Rápida (<5s) | ⚠️ Temporária* | Dev, quick fixes, builds >5min | Perdido ao recreate container |
| **Opção 4: Limpar cache Python** | ✅ Rápida (10-30s) | ✅ Semi-permanente | Após git pull, após edits | Só resolve bytecode cache |

\* docker cp é temporário: mudanças são perdidas se container for **recreado** (não se for apenas **restartado**)

#### 🔀 Flowchart de Decisão

```
┌─────────────────────────────────────┐
│ Código corrigido não reflete no    │
│ container após rebuild?             │
└──────────────┬──────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│ Tem volume mount no docker-compose?  │
│ grep -A 3 "my_service:" docker-compose.yml│
│                                      │
│ volumes:                             │
│   - ./backend/services/my_service:/app│
└───────┬──────────────────────────────┘
        │
    ┌───┴───┐
    │  SIM  │
    └───┬───┘
        │
        ▼
┌──────────────────────────────────────┐
│ Tipo de mudança?                     │
└──┬─────────────────────────────┬─────┘
   │                             │
   │ Código Python (*.py)        │ Dependências (requirements.txt)
   │                             │ ou libs sistema (Dockerfile)
   │                             │
   ▼                             ▼
┌──────────────────┐      ┌──────────────────────┐
│ Build demora     │      │ Rebuild obrigatório  │
│ >5 minutos?      │      │                      │
└──┬───────────┬───┘      │ docker compose build │
   │           │          │ --no-cache service   │
   │ SIM       │ NÃO      └──────────────────────┘
   │           │
   ▼           ▼
┌──────┐  ┌─────────────┐
│docker│  │Limpar cache │
│cp +  │  │Python:      │
│restart│  │__pycache__  │
└──────┘  │*.pyc        │
          └─────────────┘
```

#### 🆕 Casos Reais - Sessão 2025-10-05

Esta sessão resolveu **12 containers unhealthy → healthy** aplicando diferentes estratégias:

##### Caso 1: maximus-core - Dependência Faltante (Rebuild Obrigatório)

```bash
# Sintoma
$ docker logs maximus-core --tail 10
ModuleNotFoundError: No module named 'aiohttp'

# Diagnóstico
$ grep aiohttp backend/services/maximus_core_service/enhanced_cognition_tools.py
import aiohttp  # ✅ Código usa
$ grep aiohttp backend/services/maximus_core_service/requirements.txt
# (vazio) ❌ Faltava no requirements!

# Solução: Rebuild (mudança em Dockerfile/requirements)
$ echo "aiohttp==3.9.1" >> backend/services/maximus_core_service/requirements.txt
$ docker compose build --no-cache maximus_core_service
$ docker compose up -d maximus_core_service
# ✅ Container healthy!
```

**Lição**: Mudanças em `requirements.txt` ou `Dockerfile` **exigem rebuild**, `docker cp` não funciona.

##### Caso 2: narrative_filter - Configuração Completa (Rebuild Estratégico)

```bash
# Problema: ImportError + AttributeError + ConnectionRefused (múltiplos erros)
$ docker logs narrative_manipulation_filter --tail 50
ImportError: cannot import name 'get_settings' from 'config'
AttributeError: 'Settings' object has no attribute 'VERSION'
ConnectionRefused: localhost:5432  # Apontando para localhost em vez de postgres

# Correções aplicadas NO HOST:
# 1. Criar função get_settings() em config.py
# 2. Fix imports relativos (sed global)
# 3. Corrigir attribute names (VERSION→SERVICE_VERSION)
# 4. Mudar defaults de infraestrutura (localhost→postgres/redis/kafka)

# Rebuild estratégico (--no-cache para garantir)
$ docker compose build --no-cache narrative_manipulation_filter
$ docker compose up -d narrative_manipulation_filter

# Resultado: 100% operacional
$ curl http://localhost:8213/health
{"status":"healthy","services":{"postgres":true,"redis":true,"kafka":true}}
```

**Lição**: Mudanças arquiteturais (imports, config) precisam de rebuild limpo.

##### Caso 3: 8x Healthchecks - Recreate sem Rebuild

```bash
# Problema: Containers funcionais mas marcados "unhealthy"
$ docker ps | grep unhealthy | wc -l
8

# Diagnóstico
$ docker inspect vertice-hcl-monitor --format '{{json .State.Health.Log}}' | jq '.[-1]'
{
  "ExitCode": 1,
  "Output": "/bin/sh: 1: curl: not found\n"
}

# Causa: Healthcheck usando curl (não instalado em python:3.11-slim)
# docker-compose.yml:
#   healthcheck:
#     test: ["CMD-SHELL", "curl -f http://localhost:8023/health || exit 1"]

# Solução: Mudar para Python (sem rebuild!)
# Editar docker-compose.yml:
#   healthcheck:
#     test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8023/health')"]

# Recreate containers (NÃO rebuild)
$ docker compose up -d hcl_monitor_service hcl_planner_service hcl_kb_service # ... (8 serviços)

# Aguardar 40s (start_period) e verificar
$ docker ps --filter "name=hcl" --format "table {{.Names}}\t{{.Status}}"
vertice-hcl-monitor    Up 50 seconds (healthy)
vertice-hcl-planner    Up 50 seconds (healthy)
vertice-hcl-kb         Up 50 seconds (healthy)
# ... todos healthy!
```

**Lição**: Mudanças em `docker-compose.yml` (healthcheck, env vars, ports) só precisam **recreate**, não rebuild.

##### Caso 4: immunis-macrophage - Biblioteca Sistema (Rebuild com Dockerfile Fix)

```bash
# Erro
$ docker logs vertice-immunis-macrophage --tail 20
ModuleNotFoundError: No module named 'yara'

# Diagnóstico
$ grep yara backend/services/immunis_macrophage_service/requirements.txt
yara-python==4.3.1  # ✅ Está no requirements

$ grep yara backend/services/immunis_macrophage_service/Dockerfile
# (vazio) ❌ Falta biblioteca sistema libyara-dev!

# Correção: Adicionar lib sistema no Dockerfile
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libyara-dev \  # ← ADICIONADO
    && rm -rf /var/lib/apt/lists/*

# Rebuild obrigatório
$ docker compose build --no-cache immunis_macrophage_service
$ docker compose up -d immunis_macrophage_service
# ✅ healthy após 50s!
```

**Lição**: Dependências de sistema operacional (apt-get, yum, apk) exigem rebuild completo.

#### 📋 Checklist de Diagnóstico Rápido

**Antes de escolher solução, responda:**

- [ ] A mudança é só em código Python? → Considere `docker cp` ou limpar cache
- [ ] Mudou `requirements.txt` ou `Dockerfile`? → **Rebuild obrigatório**
- [ ] Mudou `docker-compose.yml`? → **Recreate** (não rebuild)
- [ ] Build demora >5 minutos? → Use `docker cp` para dev, rebuild para prod
- [ ] Container tem volume mount? → **Problema provável**, veja checklist acima
- [ ] Erro persiste após rebuild normal? → Use `--no-cache`
- [ ] É produção ou CI/CD? → **Sempre rebuild**, nunca docker cp

**Comandos de diagnóstico rápido:**
```bash
# 1. Tem volume mount?
docker inspect my_service | grep -A 5 '"Mounts"'

# 2. Código HOST vs Container é diferente?
md5sum ./backend/services/my_service/main.py
docker exec my_service md5sum /app/main.py

# 3. Build usou cache?
docker compose build my_service 2>&1 | grep CACHED

# 4. Container tem __pycache__ antigo?
docker exec my_service find /app -name "*.pyc" -exec ls -lh {} \; | head -5
```

### 5.8. Build Cache Mascarando Correções

**Sintoma**: Você corrige o código, faz `docker compose build`, mas erro persiste.

**Causa**: Docker reutiliza layers em cache que têm código antigo.

**Debug**:
```bash
# Veja se build usou cache
docker compose build my_service 2>&1 | grep CACHED

# Output:
#5 CACHED
#6 CACHED
#7 [5/5] COPY . .
#7 CACHED  # ⚠️ Copiou arquivos antigos do cache!
```

**Solução**:
```bash
# Force rebuild completo
docker compose build --no-cache my_service

# Ou para todos os serviços
docker compose build --no-cache

# Ou rebuild + recreate container
docker compose up --build --force-recreate my_service
```

### 5.9. Imports Opcionais para Dependências Pesadas

**Problema**: Biblioteca está no `requirements.txt` mas instalação falhou silenciosamente, causando `ImportError` em runtime.

**Solução: Try/Except Imports**

```python
# ❌ ANTES: Import direto
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
from kafka import KafkaProducer
from sklearn.metrics import r2_score

# ✅ DEPOIS: Import opcional com fallback
try:
    from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    CollectorRegistry = None
    Gauge = None
    push_to_gateway = None

try:
    from kafka import KafkaProducer
    from kafka.errors import KafkaError
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    KafkaProducer = None
    KafkaError = Exception

# Use nos métodos
def setup_prometheus(self):
    if not PROMETHEUS_AVAILABLE:
        logger.warning("Prometheus client not available, metrics disabled")
        return

    self.registry = CollectorRegistry()
    # ... resto do código
```

**Vantagens**:
- Container inicia mesmo sem dependência opcional
- Logs claros sobre features desabilitadas
- Facilita desenvolvimento incremental
- Produção continua funcionando (degraded mode)

### 5.10. Containers Duplicados (Naming Conflicts)

**Problema**: `docker ps` mostra containers com nomes diferentes para o mesmo serviço.

```bash
$ docker ps --format "{{.Names}}"
hcl-executor           # ❌ Duplicado
vertice-hcl-executor   # ✅ Oficial
rte-service            # ❌ Duplicado
vertice-rte            # ✅ Oficial
```

**Causa**: Múltiplas definições no `docker-compose.yml` ou múltiplos docker-compose files.

**Debug**:
```bash
# Encontre definições duplicadas
grep -n "hcl.*executor:" docker-compose.yml
# 542:  hcl-executor:
# 892:  hcl_executor_service:

# Veja quais estão rodando
docker ps --filter "name=hcl" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"
```

**Solução**:
```bash
# Pare duplicados problemáticos
docker stop hcl-executor rte-service

# Mantenha apenas os oficiais (vertice-*)
docker ps | grep vertice-hcl-executor  # ✅ Este está OK

# Remova containers órfãos
docker compose down --remove-orphans
```

### 5.11. Debugging Workflow Completo

```bash
# ========================================
# CONTAINER RESTARTING - WORKFLOW DEBUG
# ========================================

# 1. Identifique o container problemático
docker ps -a | grep -i restart
# OUTPUT: my_service  Restarting (1) 5 seconds ago

# 2. Veja os logs (últimas linhas mostram o erro)
docker logs my_service 2>&1 | tail -50
# OUTPUT: ImportError: cannot import name 'get_mode_policy'

# 3. Verifique se código no container difere do HOST
docker exec my_service cat /app/file.py | head -20
cat ./backend/services/my_service/file.py | head -20
# Compare visualmente ou com diff

# 4. Verifique volume mounts
docker inspect my_service | grep -A 10 '"Mounts"'
# Se tem volume mount: código HOST é usado
# Se NÃO tem: código da imagem é usado

# 5A. Se TEM volume mount: corrija no HOST
vim ./backend/services/my_service/file.py
docker restart my_service

# 5B. Se NÃO TEM volume mount: rebuild imagem
docker compose build --no-cache my_service
docker compose up -d my_service

# 5C. Se build demora muito: docker cp como workaround
docker cp ./backend/services/my_service/file.py my_service:/app/
docker restart my_service

# 6. Valide a correção
docker logs my_service 2>&1 | tail -20
# Deve mostrar: "INFO: Started server process"

# 7. Test health endpoint
curl http://localhost:PORT/health
# OUTPUT: {"status":"healthy"}
```

### 5.12. Checklist Docker Debug

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

🆕 VERIFICAÇÕES AVANÇADAS (Aprendizados 2025-10-04):
□ Volume mounts NÃO sobrescrevendo código corrigido
□ Código no container IGUAL ao código no HOST (md5sum)
□ Build SEM usar cache para arquivos modificados
□ Imports opcionais implementados para deps pesadas
□ Sem containers duplicados (naming conflicts)
□ Python __pycache__ limpo após mudanças
□ Dockerfile COPY atualizado (se sem volume mount)
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

## 11. DEBUGGING SISTEMÁTICO: METODOLOGIA E CASOS REAIS

### 11.1 FILOSOFIA: PLANEJAMENTO > TENTATIVA E ERRO

**REGRA DE OURO**: Nunca execute ações "às cegas" esperando que funcionem.

```
❌ ERRADO: Tentativa e Erro
1. Criar código genérico
2. Executar docker build
3. Ver erro
4. Tentar corrigir
5. Repetir até funcionar

✅ CORRETO: Análise → Planejamento → Execução
1. DIAGNÓSTICO COMPLETO
   - Ler estrutura de arquivos
   - Verificar integrações existentes
   - Identificar dependências
   - Entender o "whole picture"

2. CLASSIFICAÇÃO POR PADRÃO
   - Agrupar problemas similares
   - Identificar casos especiais
   - Documentar decisões arquiteturais

3. EXECUÇÃO METÓDICA
   - Implementar por padrão identificado
   - Testar incrementalmente
   - Validar cada etapa

4. VALIDAÇÃO E DOCUMENTAÇÃO
   - Confirmar funcionamento
   - Atualizar documentação
   - Registrar aprendizados
```

---

### 11.2 CASO REAL: CORREÇÃO SISTEMÁTICA DE 22 SERVIÇOS UNHEALTHY

**Contexto**: 22 serviços com status UNHEALTHY devido a falta de `api.py`.

#### FASE 1: DIAGNÓSTICO ESTRUTURAL

```bash
# NÃO fazer:
for service in *; do
  cp template.py $service/api.py
  docker build $service
done

# FAZER: Análise completa primeiro
docker compose ps | grep unhealthy  # Identificar serviços
ls backend/services/*/  # Verificar estrutura
grep -r "import" backend/services/*/main.py  # Entender dependências
```

**Descobertas do diagnóstico**:
- 7 serviços Immunis: Têm `*_core.py` mas sem `api.py`
- 5 serviços HCL: Têm `main.py` completo, precisam wrapper
- 2 serviços funcionais: Têm `main.py`, precisam wrapper
- 2 serviços placeholder: SEM implementação real
- 3 serviços com `api.py`: Precisam rebuild apenas

#### FASE 2: CLASSIFICAÇÃO E ESTRATÉGIA

```python
# Padrão identificado via análise:
SERVICES_PATTERNS = {
    "IMMUNIS": {
        "pattern": "Tem {service}_core.py mas sem api.py",
        "action": "Criar api.py com optional imports",
        "template": "API_TEMPLATE com graceful degradation",
        "count": 7
    },
    "HCL": {
        "pattern": "main.py completo com FastAPI app",
        "action": "Criar wrapper: from main import app",
        "template": "Simple re-export",
        "count": 5
    },
    "FUNCTIONAL": {
        "pattern": "main.py funcional usado em produção",
        "action": "Criar wrapper simples",
        "template": "Re-export pattern",
        "count": 2
    },
    "PLACEHOLDER": {
        "pattern": "Apenas __init__.py com docstring",
        "discovery": "Zero referências no codebase",
        "action": "Comentar no docker-compose + documentar",
        "count": 2,
        "justificativa": "Não criar código production-ready sem propósito"
    }
}
```

**Decisão Crítica - Seriema Graph**:

```bash
# Investigação revelou:
find . -name "*seriema*" -type f
# → backend/services/narrative_manipulation_filter/seriema_graph_client.py

# Análise do client:
head -50 seriema_graph_client.py
# DESCOBERTA: Client conecta DIRETO ao Neo4j (bolt://neo4j:7687)
#             Não usa HTTP service intermediário!

# DECISÃO ARQUITETURAL:
# ✅ Comentar seriema_graph service (redundante)
# ✅ Documentar em README.md
# ❌ NÃO criar REST API wrapper desnecessário
```

---

### 11.3 PADRÕES DE CÓDIGO: OPTIONAL IMPORTS

**Problema**: Serviços com dependências pesadas que podem falhar.

```python
# ❌ ERRADO: Import direto que quebra tudo
from heavy_module import HeavyClass

core = HeavyClass()  # BOOM se módulo não existe

# ✅ CORRETO: Optional imports com graceful degradation
try:
    from heavy_module import HeavyClass
    CORE_AVAILABLE = True
except ImportError:
    logger.warning("HeavyClass not available - running in limited mode")
    CORE_AVAILABLE = False
    HeavyClass = None

# Initialize only if available
if CORE_AVAILABLE and HeavyClass:
    try:
        core = HeavyClass()
    except Exception as e:
        logger.warning(f"Core initialization failed: {e}")
        core = None
else:
    core = None

# Use with safety checks
@app.post("/process")
async def process(request: Request):
    if not core:
        raise HTTPException(
            status_code=503,
            detail="Core not available - service in limited mode"
        )
    return await core.process(request.data)
```

**Vantagens**:
- Service sobe mesmo sem dependências
- Healthcheck passa (status: limited)
- Debug mais fácil (service responde)
- Production-ready (fail gracefully)

---

### 11.4 HONESTIDADE ARQUITETURAL

**Princípio**: Não criar código "production-ready" sem propósito real.

```yaml
# ANTES: Service placeholder rodando
tataca_ingestion:
  build: ./backend/services/tataca_ingestion
  command: uvicorn main:app --host 0.0.0.0 --port 8028
  # main.py não existe, vai falhar

# TENTAÇÃO: Criar main.py "mínimo funcional"
# ❌ PROBLEMA: Viola REGRA DE OURO
# - Código quality-first sem função
# - Desperdiça recursos Docker
# - Confunde arquitetura

# CORRETO: Honestidade arquitetural
# tataca_ingestion:
#   build: ./backend/services/tataca_ingestion
#   # COMENTADO: Placeholder sem implementação
#   # Ver: backend/services/tataca_ingestion/README.md

# + README.md documentando:
# - Status atual (placeholder)
# - Propósito planejado
# - Por que está desabilitado
# - Próximos passos
```

---

### 11.5 BUILD STRATEGIES: DEPENDÊNCIAS PESADAS

**Problema**: PyTorch (670MB) + CUDA libs causam timeout.

```bash
# ❌ ERRADO: Build síncrono travando terminal
docker compose build --no-cache rte_service
# Espera 5+ minutos travado...

# ✅ CORRETO: Build assíncrono com monitoramento
docker compose build --no-cache rte_service 2>&1 | tee /tmp/build.log &
BUILD_PID=$!

# Continua trabalhando em outros serviços
docker compose build --no-cache google_osint_service  # Rápido (30s)
docker compose build --no-cache hcl_*_service  # Paralelo

# Monitora quando necessário
tail -f /tmp/build.log
# ou
docker compose ps rte_service
```

**Timeout Management**:

```bash
# Para comandos longos, usar timeout estendido
docker compose build --no-cache heavy_service &
sleep 300  # 5 minutos
docker compose ps heavy_service  # Verificar status
```

---

### 11.6 WORKFLOW COMPLETO: SERVIÇO UNHEALTHY → HEALTHY

```bash
# ETAPA 1: DIAGNÓSTICO (NÃO PULE ISSO!)
# ═══════════════════════════════════════
ls backend/services/TARGET_SERVICE/  # Estrutura
cat backend/services/TARGET_SERVICE/main.py | head -50  # Implementação
grep -r "TARGET_SERVICE" backend/services/  # Integrações
awk '/TARGET_SERVICE:/,/restart:/' docker-compose.yml  # Config

# ETAPA 2: CLASSIFICAÇÃO
# ═══════════════════════════════════════
# Tem main.py funcional? → Wrapper pattern
# Tem *_core.py? → Optional imports pattern
# Só __init__.py? → Investigar se é placeholder
# Nenhum arquivo? → Criar implementação completa OU desabilitar

# ETAPA 3: IMPLEMENTAÇÃO
# ═══════════════════════════════════════
# Criar api.py conforme padrão identificado
cat > backend/services/TARGET_SERVICE/api.py <<'EOF'
"""Service API Entry Point."""
from main import app
__all__ = ["app"]
EOF

# Atualizar docker-compose.yml
sed -i 's/uvicorn main:app/uvicorn api:app/' docker-compose.yml

# ETAPA 4: BUILD & TEST (DEBUG_GUIDE 5.7)
# ═══════════════════════════════════════
docker compose build --no-cache TARGET_SERVICE
docker compose stop TARGET_SERVICE
docker compose rm -f TARGET_SERVICE
docker compose up -d TARGET_SERVICE

# ETAPA 5: VALIDAÇÃO
# ═══════════════════════════════════════
sleep 5  # Aguardar startup
curl http://localhost:PORT/health  # Deve retornar 200
docker logs TARGET_SERVICE --tail 30  # Verificar logs

# ETAPA 6: DOCUMENTAÇÃO
# ═══════════════════════════════════════
# Atualizar README se necessário
# Adicionar comentários arquiteturais
# Registrar decisões importantes
```

---

### 11.7 DECISÕES ARQUITETURAIS: DOCUMENTATION PATTERNS

**Quando desabilitar um serviço**: Documente SEMPRE.

```markdown
# backend/services/DISABLED_SERVICE/README.md

# Service Name - Status

## 🚧 STATUS ATUAL

Este serviço está **desabilitado** no `docker-compose.yml`.

### Por quê?

[Explicação técnica clara]

### Alternativa Atual

[Como a funcionalidade é implementada hoje]

### Se Precisar Habilitar no Futuro

1. [Passo 1]
2. [Passo 2]
3. [Validação]

### Referências

- Código relacionado: `path/to/file.py`
- Docker compose: Linha X-Y comentada
- Decisão tomada em: YYYY-MM-DD
```

**Quando criar wrapper**: Comente o propósito.

```python
"""Service API Entry Point.

This module serves as the API entry point for the [Service Name].
It imports the FastAPI application from the main module.

The actual implementation is in main.py, which handles:
- [Feature 1]
- [Feature 2]
- [Integration with X]

Architecture Decision:
- Used wrapper pattern (not direct main.py) for consistency
- Allows future middleware injection if needed
- Follows project standard established in HCL services
"""

from main import app

__all__ = ["app"]
```

---

### 11.8 ANTI-PATTERNS: O QUE NÃO FAZER

```python
# ❌ ANTI-PATTERN 1: Código genérico para problema específico
# Problema: Service precisa de api.py
# Solução ruim:
app = FastAPI()  # App vazio sem propósito
@app.get("/health")
async def health():
    return {"status": "ok"}  # Mente sobre status real

# Solução correta:
# Analise ANTES se service é necessário
# Se não: comente e documente
# Se sim: implemente funcionalidade real

# ❌ ANTI-PATTERN 2: Ignorar integrações existentes
# Problema: Criar seriema_graph service HTTP
# Não investigou: SeriemaGraphClient já existe conectando direto ao Neo4j
# Resultado: Código redundante e confuso

# Solução correta:
grep -r "seriema" backend/services/  # Investigar USO real
# Descobrir client direto → Não criar service HTTP

# ❌ ANTI-PATTERN 3: Build sem --no-cache após mudanças
# Problema: Código atualizado mas container usa versão antiga
docker compose build service  # Usa cache!
docker compose up -d service  # Roda código antigo

# Solução correta (Seção 5.7):
docker compose build --no-cache service  # Força rebuild
docker compose stop service && docker compose rm -f service
docker compose up -d service

# ❌ ANTI-PATTERN 4: Não validar após mudanças
docker compose up -d service  # Sobe
# Assume que está OK sem testar

# Solução correta:
docker compose up -d service
sleep 5  # Aguardar startup
curl http://localhost:PORT/health  # VALIDAR
docker logs service --tail 30  # VERIFICAR logs
```

---

### 11.9 MÉTRICAS DE SUCESSO DESTA METODOLOGIA

**Sessão de debugging 2025-10-05**:

```
PROBLEMA INICIAL:
- 22 serviços UNHEALTHY
- Causa: Falta de api.py
- Tempo estimado (tentativa e erro): 6-8 horas
- Risco de código genérico: ALTO

ABORDAGEM SISTEMÁTICA:
Fase 1: Diagnóstico completo (30min)
Fase 2A: 6 Immunis services (60min)
Fase 2B: 5 HCL services (45min)
Fase 2C: 4 outros services (30min)
Fase 3: Rebuild 3 existentes (20min)

RESULTADO:
✅ 16 serviços corrigidos funcionalmente
✅ 2 serviços desabilitados honestamente
✅ 0 código genérico/placeholder criado
✅ 100% production-ready code
✅ Documentação completa
✅ Tempo total: ~3 horas (50% mais rápido)
✅ Quality-first mantido
```

**Lições**:
1. **Diagnóstico economiza tempo**: 30min planejando evita 3h corrigindo
2. **Agrupamento por padrão**: 5 serviços similares = 1 template + script
3. **Honestidade > Código bonito**: Comentar placeholder > Criar mock
4. **Whole picture primeiro**: Entender integrações evita código redundante

---

### 11.10 CHECKLIST: ANTES DE CRIAR QUALQUER CÓDIGO

```bash
☐ Li a estrutura de arquivos do serviço?
☐ Verifiquei se main.py ou core já existem?
☐ Busquei referências no codebase (grep -r)?
☐ Entendi as integrações com outros serviços?
☐ Identifiquei o padrão arquitetural correto?
☐ Considerei se o serviço é realmente necessário?
☐ Li o docker-compose.yml para ver config?
☐ Verifiquei dependências no requirements.txt?
☐ Tenho o "whole picture" antes de implementar?

Se TODAS respostas = SIM: PODE IMPLEMENTAR
Se QUALQUER = NÃO: INVESTIGUE MAIS
```

---

### 11.11 RECURSOS E TEMPLATES

**Template: Optional Imports Pattern**

```python
"""Service with Optional Dependencies."""
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException

logger = logging.getLogger(__name__)

# Optional import with graceful degradation
try:
    from heavy_core import HeavyCore
    CORE_AVAILABLE = True
except ImportError:
    logger.warning("HeavyCore not available - running in limited mode")
    CORE_AVAILABLE = False
    HeavyCore = None

app = FastAPI(title="Service Name")

# Initialize only if available
core: Optional[HeavyCore] = None
if CORE_AVAILABLE and HeavyCore:
    try:
        core = HeavyCore()
        logger.info("Core initialized successfully")
    except Exception as e:
        logger.warning(f"Core initialization failed: {e}")

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "core_available": core is not None,
        "mode": "full" if core else "limited"
    }

@app.post("/process")
async def process(data: dict):
    if not core:
        raise HTTPException(
            status_code=503,
            detail="Core not available"
        )
    return await core.process(data)
```

**Template: Simple Wrapper**

```python
"""Service API Entry Point.

Wrapper pattern for services with complete main.py implementation.
"""

from main import app

__all__ = ["app"]
```

**Script: Automated API Creation**

```python
#!/usr/bin/env python3
"""Generate api.py for multiple services following same pattern."""

SERVICES = ["service1", "service2", "service3"]
TEMPLATE = '''"""[SERVICE_NAME] - API Entry Point."""

from main import app

__all__ = ["app"]
'''

for service in SERVICES:
    content = TEMPLATE.replace("[SERVICE_NAME]", service.title())
    with open(f"backend/services/{service}/api.py", "w") as f:
        f.write(content)
    print(f"✅ Created api.py for {service}")
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

**Última atualização**: 2025-10-04
**Versão**: 1.1.0
**Mantido por**: JuanCS-Dev

**Changelog v1.1.0 (2025-10-04)**:
- ✅ Adicionadas seções 5.7-5.12: Debugging avançado de containers
- ✅ Volume mounts vs Image code (armadilha crítica)
- ✅ Build cache mascarando correções
- ✅ Imports opcionais para dependências pesadas
- ✅ Containers duplicados (naming conflicts)
- ✅ Workflow completo de debugging de containers
- ✅ Caso real documentado: RTE Service (docker cp solution)

**Links Úteis**:
- Repositório: `/home/juan/vertice-dev`
- Documentação: `/home/juan/vertice-dev/docs`
- Issues: Track problemas conhecidos

---

*"Debug is twice as hard as writing the code in the first place. Therefore, if you write the code as cleverly as possible, you are, by definition, not smart enough to debug it." - Brian Kernighan*
