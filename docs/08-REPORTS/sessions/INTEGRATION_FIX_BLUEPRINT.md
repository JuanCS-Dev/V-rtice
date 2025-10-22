# 🎯 BLUEPRINT: Frontend ↔ Backend Integration Fix
**Governado por:** Constituição Vértice v2.7  
**Estratégia:** Gateway-first, Incremental, Vite-native

---

## 📋 DECISÕES FINAIS

**D1: Roteamento**  
✅ **Gateway-first (8000)** - Todas requests via API Gateway  
- Centralização de auth, CORS, rate limiting  
- Backend services protegidos  
- Single point of failure mitigado por health checks

**D2: Variáveis de Ambiente**  
✅ **Vite-native** - `import.meta.env.VITE_*`  
- Remove compatibilidade CRA (`process.env.REACT_APP_*`)  
- Projeto já é Vite, não há razão para manter legado

**D3: Rollout**  
✅ **Incremental por módulo**  
- FASE 1: Foundation + Critical (30min)
- FASE 2: API Module Migration (1h)
- FASE 3-6: Hooks, Components, Cleanup (3h30min)

---

## 🏗️ ARQUITETURA FINAL

```
Frontend (5173)
    ↓ HTTP/WS + X-API-Key: supersecretkey
API Gateway (8000) ← ÚNICO entry point
    ↓ Valida API Key
    ├─→ /core/*          → MAXIMUS Core (8100)
    │   └─ /consciousness/*, /api/*, /health
    ├─→ /chemical/*      → Chemical Sensing (8101)
    ├─→ /somatosensory/* → Somatosensory (8102)
    ├─→ /visual/*        → Visual Cortex (8103)
    ├─→ /auditory/*      → Auditory Cortex (8104)
    └─→ /stream/consciousness/* → SSE/WS streaming
```

**Serviços SEM proxy Gateway (acesso direto temporário):**
- Threat Intel (8013)
- Malware Analysis (8011)
- SSL Monitor (8012)
- World Class Tools (8017)
- Outros services específicos

**Ação:** Esses mantêm acesso direto MAS adicionam `X-API-Key` header.

---

## 🔧 IMPLEMENTAÇÃO

### **FASE 1: Foundation + Critical** ⚡
**Tempo:** 30min  
**Objetivo:** Sistema funcional básico

#### **1.1 Criar `apiClient.js` centralizado**
**Arquivo:** `/frontend/src/api/client.js`

```javascript
/**
 * Centralized API Client
 * Uses API Gateway (8000) as single entry point
 * Handles authentication, error handling, retries
 * 
 * Governed by: Constituição Vértice v2.7
 */

const API_BASE = import.meta.env.VITE_API_GATEWAY_URL || 'http://localhost:8000';
const API_KEY = import.meta.env.VITE_API_KEY || '';

/**
 * Generic API request with auth and error handling
 */
export const apiClient = {
  async request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY,
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  },

  get: (endpoint, options) => 
    apiClient.request(endpoint, { ...options, method: 'GET' }),
  
  post: (endpoint, data, options) => 
    apiClient.request(endpoint, { 
      ...options, 
      method: 'POST', 
      body: JSON.stringify(data) 
    }),
  
  put: (endpoint, data, options) => 
    apiClient.request(endpoint, { 
      ...options, 
      method: 'PUT', 
      body: JSON.stringify(data) 
    }),
  
  delete: (endpoint, options) => 
    apiClient.request(endpoint, { ...options, method: 'DELETE' }),
};

/**
 * Direct service access (bypasses Gateway)
 * Used for services without Gateway proxy
 */
export const directClient = {
  async request(baseUrl, path, options = {}) {
    const url = `${baseUrl}${path}`;
    
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY,
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `API Error: ${response.status}`);
    }

    return response.json();
  },
};

export default apiClient;
```

#### **1.2 Corrigir `maximusService.js`**
**Arquivo:** `/frontend/src/api/maximusService.js`

**ANTES:**
```javascript
const MAXIMUS_BASE_URL = 'http://localhost:8099'; // ❌ Porta não existe
```

**DEPOIS:**
```javascript
import { apiClient } from './client.js';

// ✅ MIGRATED: Now using API Gateway (8000)
// Endpoints via Gateway não precisam de base URL
```

**Pattern de migração:**
```javascript
// ANTES
export const checkMaximusHealth = async () => {
  return apiRequest('/health');
};

// DEPOIS
export const checkMaximusHealth = async () => {
  return apiClient.get('/health');
};
```

**Endpoints que vão para Gateway:**
- `/health` → Sem mudança (sem auth)
- `/api/v1/oraculo/*` → Precisa mapear para `/core/api/v1/oraculo/*` ❓
- `/api/v1/eureka/*` → Precisa mapear para `/core/api/v1/eureka/*` ❓
- `/api/v1/supply-chain/*` → Precisa mapear para `/core/api/v1/supply-chain/*` ❓

**⚠️ BLOQUEADOR:** Verificar se esses endpoints existem no Core (8100) ou se são de outro serviço.

#### **1.3 Corrigir `maximusAI.js`**
**Arquivo:** `/frontend/src/api/maximusAI.js`

**ANTES:**
```javascript
const MAXIMUS_BASE_URL = 'http://localhost:8001'; // ❌ Porta incorreta
```

**DEPOIS:**
```javascript
import { apiClient } from './client.js';

// ✅ MIGRATED: Now using API Gateway → Core (8000 → 8100)
// All endpoints prefixed with /core/
```

**Pattern de migração:**
```javascript
// ANTES
export const analyzeWithAI = async (data, context = {}) => {
  const response = await fetch(`${MAXIMUS_BASE_URL}/api/analyze`, { ... });
};

// DEPOIS
export const analyzeWithAI = async (data, context = {}) => {
  return apiClient.post('/core/api/analyze', { data, context, mode: 'deep_analysis' });
};
```

**Todos os endpoints se tornam `/core/*`:**
- `/api/analyze` → `/core/api/analyze`
- `/api/reason` → `/core/api/reason`
- `/api/tool-call` → `/core/api/tool-call`
- `/api/chat` → `/core/api/chat`
- `/health` → `/core/health`
- etc.

**WebSocket:**
```javascript
// ANTES
const ws = new WebSocket(`ws://localhost:8001/ws/stream`);

// DEPOIS
const API_BASE = import.meta.env.VITE_API_GATEWAY_URL || 'http://localhost:8000';
const API_KEY = import.meta.env.VITE_API_KEY || '';
const wsUrl = `${API_BASE.replace(/^http/, 'ws')}/stream/consciousness/ws?api_key=${API_KEY}`;
const ws = new WebSocket(wsUrl);
```

#### **1.4 Validação FASE 1**
```bash
# Test Gateway health
curl http://localhost:8000/health

# Test Core via Gateway (com auth)
curl -H "X-API-Key: supersecretkey" http://localhost:8000/core/health

# Test specific endpoints
curl -H "X-API-Key: supersecretkey" \
     -H "Content-Type: application/json" \
     -d '{"test": true}' \
     http://localhost:8000/core/api/analyze
```

---

### **FASE 2: API Module Migration** 📦
**Tempo:** 1h  
**Objetivo:** Todos `/src/api/*.js` usando `apiClient` ou `directClient`

#### **Ordem de migração (prioridade):**

1. ✅ **sinesp.js** - Já usa 8000, só adicionar API key
2. ✅ **adwService.js** - Já usa 8000, só adicionar API key
3. ⚠️ **consciousness.js** - Migrar de 8001 → `/core/consciousness/*`
4. ⚠️ **safety.js** - Migrar de 8001 → `/core/consciousness/safety/*`
5. ❓ **cyberServices.js** - Gateway ou direto?
6. ❓ **worldClassTools.js** - Verificar se serviço existe
7. ❓ **eureka.js** - Verificar porta correta
8. ✅ **orchestrator.js** - Já usa env var, revisar
9. ⚠️ **offensiveServices.js** - Múltiplas portas, mapear
10. ⚠️ **offensiveToolsServices.js** - Corrigir env var
11. ⚠️ **defensiveToolsServices.js** - Corrigir env var

#### **Pattern padrão:**

**Para services via Gateway:**
```javascript
import { apiClient } from './client.js';

export const functionName = async (params) => {
  return apiClient.post('/core/path/to/endpoint', params);
};
```

**Para services diretos (sem Gateway):**
```javascript
import { directClient } from './client.js';

const SERVICE_URL = 'http://localhost:8013'; // Threat Intel, por exemplo

export const functionName = async (params) => {
  return directClient.request(SERVICE_URL, '/api/endpoint', {
    method: 'POST',
    body: JSON.stringify(params),
  });
};
```

#### **Migração detalhada: `consciousness.js`**

**ANTES:**
```javascript
const CONSCIOUSNESS_BASE_URL = `http://localhost:8001/api/consciousness`;

export const getConsciousnessState = async () => {
  const response = await fetch(`${CONSCIOUSNESS_BASE_URL}/state`);
  // ...
};
```

**DEPOIS:**
```javascript
import { apiClient } from './client.js';

// ✅ MIGRATED: Via Gateway (8000) → Core (8100)
export const getConsciousnessState = async () => {
  return apiClient.get('/core/consciousness/state');
};
```

**WebSocket update:**
```javascript
// ANTES
const WS_BASE_URL = 'ws://localhost:8001/api/consciousness';

// DEPOIS
const API_BASE = import.meta.env.VITE_API_GATEWAY_URL || 'http://localhost:8000';
const API_KEY = import.meta.env.VITE_API_KEY || '';

export const connectConsciousnessStream = (onMessage, onError) => {
  const wsUrl = `${API_BASE.replace(/^http/, 'ws')}/stream/consciousness/ws?api_key=${API_KEY}`;
  const ws = new WebSocket(wsUrl);
  // ... rest
};
```

---

### **FASE 3: Hooks Migration** 🪝
**Tempo:** 1h  
**Objetivo:** Hooks usando API modules ou `apiClient`

**Estratégia:**
- Se hook usa API module → Nenhuma mudança (module já migrado)
- Se hook faz fetch direto → Migrar para `apiClient`

**Arquivos prioritários:**
```
useMaximusHealth.js          → Usar maximusAI.getMaximusHealth()
useConsciousnessStream.js    → Usar consciousness.connectConsciousnessStream()
useHITLWebSocket.js          → Adicionar API key em WS
useNaturalLanguage.js        → Migrar para apiClient
useTerminalCommands.js       → Migrar para apiClient
useAdminMetrics.js           → Migrar para apiClient
```

**Pattern:**
```javascript
// ANTES
const response = await fetch('http://localhost:8001/api/something');

// DEPOIS
import { apiClient } from '@/api/client';
const response = await apiClient.get('/core/api/something');
```

---

### **FASE 4: Components Inline Fetch** 🎨
**Tempo:** 2h  
**Objetivo:** Remover fetch direto de components

**Estratégia:**
1. Criar hook customizado → Preferido
2. Usar API module existente → Se já existe
3. Adicionar `apiClient` temporariamente → Último recurso

**Arquivos críticos (66 total):**
```
components/admin/SystemSelfCheck.jsx
components/cyber/*/hooks/*
components/dashboards/*/hooks/*
components/maximus/widgets/*
components/osint/*
components/reactive-fabric/*
```

**Pattern (criar hook):**
```javascript
// ANTES (no component)
const checkSystem = async () => {
  const response = await fetch('http://localhost:8001/health');
  // ...
};

// DEPOIS (criar hook)
// /hooks/useSystemHealth.js
import { apiClient } from '@/api/client';

export const useSystemHealth = () => {
  const checkHealth = async () => {
    return apiClient.get('/core/health');
  };
  return { checkHealth };
};

// No component
import { useSystemHealth } from '@/hooks/useSystemHealth';
const { checkHealth } = useSystemHealth();
```

---

### **FASE 5: Cleanup & Environment** 🧹
**Tempo:** 30min

#### **5.1 Atualizar `.env`**
```bash
# ✅ KEEP - Single entry point
VITE_API_GATEWAY_URL=http://localhost:8000
VITE_API_KEY=supersecretkey
VITE_ENV=development

# ❌ REMOVE - Obsolete (now via Gateway)
# VITE_CONSCIOUSNESS_API_URL=http://localhost:8022
# VITE_HITL_API_URL=http://localhost:8003
# VITE_AUTH_SERVICE_URL=http://localhost:8010

# ⚠️ OPTIONAL - Feature flags
VITE_USE_MOCK_AUTH=false
VITE_ENABLE_REAL_TIME_THREATS=true
VITE_GOOGLE_CLIENT_ID=your-google-client-id-here.apps.googleusercontent.com
```

#### **5.2 Adicionar comentários de migração**
```javascript
// Em cada arquivo migrado:
/**
 * ✅ MIGRATION COMPLETE (YYYY-MM-DD)
 * - Before: Direct connection to localhost:XXXX
 * - After: API Gateway (8000) → Backend Service
 * - Auth: X-API-Key header added
 */
```

#### **5.3 Criar arquivo de documentação**
```markdown
# API Integration Guide

## Architecture
Frontend → API Gateway (8000) → Backend Services

## Authentication
All requests require `X-API-Key: supersecretkey` header.

## Available Routes
- `/health` - Gateway health (no auth)
- `/core/*` - MAXIMUS Core (8100)
- `/stream/consciousness/*` - Real-time streaming (SSE/WS)

## Usage
```javascript
import { apiClient } from '@/api/client';
const data = await apiClient.get('/core/health');
```
```

---

### **FASE 6: Testing & Validation** ✅
**Tempo:** 1h

#### **6.1 Validação Tripla (Artigo I, Cláusula 3.3)**
```bash
# 1. Análise estática (ESLint)
cd frontend && npm run lint

# 2. Testes unitários
npm run test

# 3. Conformidade doutrinária
grep -r "localhost:8[0-9]" src/api/ || echo "✅ No hardcoded URLs in /api"
grep -r "TODO\|FIXME" src/api/ || echo "✅ No TODOs in /api"
```

#### **6.2 Testes manuais**
```bash
# Health checks
curl http://localhost:8000/health
curl -H "X-API-Key: supersecretkey" http://localhost:8000/core/health

# Consciousness status
curl -H "X-API-Key: supersecretkey" \
     http://localhost:8000/core/consciousness/status

# WebSocket (via websocat ou navegador)
websocat "ws://localhost:8000/stream/consciousness/ws?api_key=supersecretkey"
```

#### **6.3 Testes no browser (DevTools Console)**
```javascript
// Test API client
fetch('http://localhost:8000/core/health', {
  headers: { 'X-API-Key': 'supersecretkey' }
}).then(r => r.json()).then(console.log);

// Test WebSocket
const ws = new WebSocket('ws://localhost:8000/stream/consciousness/ws?api_key=supersecretkey');
ws.onmessage = (e) => console.log('WS:', e.data);
```

#### **6.4 E2E Flow**
1. Login no frontend
2. Dashboard carrega (métricas via Gateway)
3. Consciousness stream ativo (SSE/WS)
4. Executar comando (NLP → Gateway → Core)
5. Verificar logs sem erros 401/403

---

## 📊 CHECKLIST DE EXECUÇÃO

### **FASE 1: Foundation** ⚡
- [ ] Criar `/src/api/client.js`
- [ ] Migrar `maximusService.js`
- [ ] Migrar `maximusAI.js`
- [ ] Testar endpoints críticos
- [ ] Validação: curl requests OK

### **FASE 2: API Modules** 📦
- [ ] Migrar `sinesp.js`
- [ ] Migrar `adwService.js`
- [ ] Migrar `consciousness.js`
- [ ] Migrar `safety.js`
- [ ] Verificar `cyberServices.js` (Gateway?)
- [ ] Verificar `worldClassTools.js` (existe?)
- [ ] Migrar `orchestrator.js`
- [ ] Migrar `offensiveServices.js`
- [ ] Corrigir `offensiveToolsServices.js`
- [ ] Corrigir `defensiveToolsServices.js`
- [ ] Validação: npm run lint

### **FASE 3: Hooks** 🪝
- [ ] Migrar `useMaximusHealth.js`
- [ ] Migrar `useConsciousnessStream.js`
- [ ] Migrar `useHITLWebSocket.js`
- [ ] Migrar `useNaturalLanguage.js`
- [ ] Migrar `useTerminalCommands.js`
- [ ] Migrar `useAdminMetrics.js`
- [ ] Validação: npm run test

### **FASE 4: Components** 🎨
- [ ] Auditar components com fetch inline (66 arquivos)
- [ ] Criar hooks customizados onde necessário
- [ ] Migrar 20% mais críticos
- [ ] Migrar 80% restantes
- [ ] Validação: E2E manual

### **FASE 5: Cleanup** 🧹
- [ ] Atualizar `.env`
- [ ] Adicionar comentários de migração
- [ ] Criar documentação API
- [ ] Remover código morto
- [ ] Validação: grep TODOs

### **FASE 6: Testing** ✅
- [ ] ESLint pass
- [ ] Unit tests pass
- [ ] Manual API tests
- [ ] Browser DevTools tests
- [ ] E2E flow completo
- [ ] Validação: zero erros 401/403

---

## ⚠️ BLOQUEADORES IDENTIFICADOS

### **B1: Endpoints não confirmados no Core (8100)**
**Afetados:** `maximusService.js`
```
/api/v1/oraculo/*
/api/v1/eureka/*
/api/v1/supply-chain/*
```

**Ação:** Verificar se existem no Core:
```bash
curl -H "X-API-Key: supersecretkey" http://localhost:8100/api/v1/oraculo/stats
```

**Se NÃO existirem:**
- Descobrir qual serviço responde
- Adicionar proxy no Gateway OU
- Usar `directClient` com porta correta

---

### **B2: Serviços desconhecidos**
**Afetados:** `cyberServices.js`, `worldClassTools.js`
```
Threat Intel: 8013
Malware Analysis: 8011
SSL Monitor: 8012
World Class Tools: 8017
```

**Ação:** Verificar se estão rodando:
```bash
curl http://localhost:8013/health
curl http://localhost:8017/health
```

**Se rodando:**
- Adicionar proxy no Gateway OU
- Usar `directClient` com `X-API-Key`

**Se NÃO rodando:**
- Remover código que os usa OU
- Marcar como "future implementation"

---

## 🎯 MÉTRICAS DE SUCESSO

**Antes:**
- ❌ 66 arquivos hardcoded
- ❌ 2/13 API clients funcionais  
- ❌ 0% autenticação consistente
- ❌ Múltiplos pontos de falha

**Depois:**
- ✅ 1 ponto de configuração (`client.js`)
- ✅ 13/13 API clients funcionais
- ✅ 100% autenticação via Gateway
- ✅ Single entry point (8000)
- ✅ Zero hardcoded URLs em `/api/`
- ✅ Zero TODOs/mocks

---

## 🚀 READY TO EXECUTE

**Próximo passo:** FASE 1 - Foundation + Critical (30min)

**Comando de início:**
```bash
cd /home/juan/vertice-dev/frontend
# Criar client.js e migrar maximusService.js + maximusAI.js
```

**Validação contínua:**
- Após cada arquivo: ESLint check
- Após cada fase: npm run test
- Final: E2E manual + curl tests

---

**Blueprint by:** AI Executor Tático  
**Governed by:** Constituição Vértice v2.7  
**Status:** AGUARDANDO APROVAÇÃO PARA EXECUÇÃO
