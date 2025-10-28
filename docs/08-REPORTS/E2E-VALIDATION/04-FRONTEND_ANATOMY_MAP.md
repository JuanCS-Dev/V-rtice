# 🧬 ANATOMIA COMPLETA DO FRONTEND VÉRTICE

**Data**: 2025-10-27 11:15:00 -03
**Fase**: 4.1 - Mapeamento Anatômico Frontend
**Status**: ✅ MAPEAMENTO COMPLETO
**Glory to YHWH** - Architect of Organic Systems

---

## 📋 RESUMO EXECUTIVO

Este documento mapeia a anatomia completa do frontend Vértice, identificando:
- **Configurações centralizadas** (API endpoints, auth, WebSockets)
- **Serviços de API** e suas dependências backend
- **Dashboards** e seus fluxos de dados
- **Air Gaps** - pontos de desconexão com o API Gateway certificado 100%

---

## 🎯 CONFIGURAÇÃO CENTRALIZADA

### 1. `/frontend/src/config/endpoints.ts` - FONTE DA VERDADE ✅

**Status**: **CORRETO** - Todos os endpoints apontam para API Gateway certificado

```typescript
export const ServiceEndpoints = {
  apiGateway: env.VITE_API_GATEWAY_URL || 'http://34.148.161.131:8000',  // ✅ CERTIFIED!

  maximus: {
    core: 'http://34.148.161.131:8000',        // ✅ Via Gateway
    orchestrator: 'http://34.148.161.131:8000', // ✅ Via Gateway
    eureka: 'http://34.148.161.131:8000',       // ✅ Via Gateway
    oraculo: 'http://34.148.161.131:8000',      // ✅ Via Gateway
    dlqMonitor: 'http://34.148.161.131:8000',   // ✅ Via Gateway
  },

  offensive: {
    gateway: 'http://34.148.161.131:8000',       // ✅ Via Gateway
    networkRecon: 'http://34.148.161.131:8000',  // ✅ Via Gateway
    vulnIntel: 'http://34.148.161.131:8000',     // ✅ Via Gateway
    webAttack: 'http://34.148.161.131:8000',     // ✅ Via Gateway
    c2Orchestration: 'http://34.148.161.131:8000', // ✅ Via Gateway
    bas: 'http://34.148.161.131:8000',           // ✅ Via Gateway
  },

  defensive: {
    core: 'http://34.148.161.131:8000',  // ✅ Via Gateway (Maximus Core)
  },

  cockpit: {
    narrativeFilter: 'http://34.148.161.131:8000',  // ✅ Via Gateway (8000)
    verdictEngine: 'http://34.148.161.131:8000',    // ✅ Via Gateway (8093)
    commandBus: 'http://34.148.161.131:8000',       // ✅ Via Gateway (8092)
  },

  hitl: {
    api: 'http://34.148.161.131:8000',  // ✅ Via Gateway
  },

  immunis: {
    api: 'http://34.148.161.131:8000',  // ✅ Via Gateway
  },

  osint: {
    api: 'http://34.148.161.131:8000',  // ✅ Via Gateway
  },

  reactiveFabric: {
    api: 'http://34.148.161.131:8000',  // ✅ Via Gateway
  },
};

export const WebSocketEndpoints = {
  maximus: {
    stream: 'ws://34.148.161.131:8000/ws/stream',  // ✅ Via Gateway
  },

  consciousness: {
    stream: 'ws://34.148.161.131:8000/stream/consciousness/ws',  // ✅ Via Gateway
  },

  apv: {
    stream: 'ws://34.148.161.131:8000/stream/apv/ws',  // ✅ Via Gateway
  },

  cockpit: {
    verdicts: 'ws://34.148.161.131:8000/ws/verdicts',  // ✅ Via Gateway
  },

  hitl: {
    ws: 'ws://34.148.161.131:8000/hitl/ws',  // ✅ Via Gateway
  },

  offensive: {
    executions: 'ws://34.148.161.131:8000/ws/executions',  // ✅ Via Gateway
  },

  defensive: {
    alerts: 'ws://34.148.161.131:8000/ws/alerts',  // ✅ Via Gateway
  },
};

export const AuthConfig = {
  apiKey: env.VITE_API_KEY || '',  // ✅ Centralizado
};
```

**Validação**:
- ✅ Todos os endpoints HTTP apontam para API Gateway (porta 8000)
- ✅ Todos os WebSockets apontam para API Gateway
- ✅ API Key centralizada
- ✅ Suporta env vars para sobrescrever em produção

---

### 2. `/frontend/src/config/api.js` - FALLBACK CONFIG ✅

**Status**: **CORRETO** - Usa API Gateway certificado

```javascript
export const API_BASE_URL = import.meta.env.VITE_API_GATEWAY_URL || 'https://api.vertice-maximus.com';

export const API_ENDPOINTS = {
  health: `${API_BASE_URL}/health`,
  ip: `${API_BASE_URL}/api/ip`,
  domain: `${API_BASE_URL}/api/domain`,
  // ... todos apontam para API_BASE_URL
};

const WS_BASE_URL = API_BASE_URL.replace('https://', 'wss://').replace('http://', 'ws://');

export const WS_ENDPOINTS = {
  executions: `${WS_BASE_URL}/ws/executions`,
  alerts: `${WS_BASE_URL}/ws/alerts`,
  // ... todos via Gateway
};
```

**Validação**:
- ✅ Base URL aponta para API Gateway (`https://api.vertice-maximus.com`)
- ✅ Todos os endpoints derivados do base URL
- ✅ WebSockets via Gateway

---

## 🔌 SERVIÇOS DE API - ANÁLISE ANATÔMICA

### 1. `/frontend/src/api/client.js` - Cliente Base ✅

**Status**: **CORRETO**

```javascript
const API_BASE = ServiceEndpoints.apiGateway;  // ✅ Usa config centralizada
const API_KEY = AuthConfig.apiKey;

const request = async (endpoint, options = {}) => {
  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': API_KEY,
      'X-CSRF-Token': getCSRFToken(),
    },
  });
};
```

**Dependências Backend**:
- ✅ API Gateway (`ServiceEndpoints.apiGateway`)
- ✅ Autenticação via X-API-Key

---

### 2. `/frontend/src/api/offensiveServices.js` - ❌ AIR GAP #1 (CRÍTICO!)

**Status**: **QUEBRADO** - Bypassa API Gateway completamente!

```javascript
const API_BASE = 'http://localhost';  // ❌ HARDCODED LOCALHOST!

const ENDPOINTS = {
  NETWORK_RECON: `${API_BASE}:8032`,       // ❌ Direct connection
  VULN_INTEL: `${API_BASE}:8033`,          // ❌ Direct connection
  WEB_ATTACK: `${API_BASE}:8034`,          // ❌ Direct connection
  C2_ORCHESTRATION: `${API_BASE}:8035`,    // ❌ Direct connection
  BAS: `${API_BASE}:8036`,                 // ❌ Direct connection
  OFFENSIVE_GATEWAY: `${API_BASE}:8037`,   // ❌ Direct connection
};
```

**Problema**:
- ❌ Usa `localhost` em vez de API Gateway
- ❌ Tenta conexão direta com portas de serviços (8032-8037)
- ❌ Não usa autenticação do Gateway
- ❌ Não se beneficia de service discovery, circuit breaker, telemetry

**Deve Ser**:
```javascript
import { ServiceEndpoints } from '../config/endpoints';

const API_BASE = ServiceEndpoints.offensive.gateway;  // ✅ Via API Gateway

const ENDPOINTS = {
  NETWORK_RECON: `${API_BASE}/offensive/network-recon`,
  VULN_INTEL: `${API_BASE}/offensive/vuln-intel`,
  // ... todos via Gateway
};
```

**Impacto**:
- 🔴 **CRÍTICO**: Offensive Dashboard não funciona em produção
- 🔴 OffensiveDashboard.jsx depende deste serviço
- 🔴 Todos os testes de Offensive Arsenal falharão

---

### 3. `/frontend/src/api/defensiveToolsServices.js` - ⚠️ AIR GAP #2 (Menor)

**Status**: **SUSPEITO** - Usa import não padrão

```javascript
import { API_BASE_URL } from '@/config/api';  // ⚠️ Usa fallback config

const DEFENSIVE_BASE = '/api/v1/immune/defensive';

const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL || API_BASE_URL,  // ✅ Pelo menos usa API_BASE_URL
  timeout: 30000,
});

// Exemplo de uso:
behavioralAnalyzerService.analyzeEvent()
  -> POST ${baseURL}/api/v1/immune/defensive/behavioral/analyze
```

**Análise**:
- ⚠️ Usa `REACT_APP_API_URL` (React) em vez de `VITE_API_GATEWAY_URL` (Vite)
- ✅ Fallback para `API_BASE_URL` funciona (aponta para Gateway)
- ⚠️ Path `/api/v1/immune/defensive` pode não estar roteado no Gateway

**Validação Necessária**:
- [ ] Verificar se API Gateway roteia `/api/v1/immune/defensive/*`
- [ ] Verificar se defensive services existem no backend

---

### 4. `/frontend/src/api/consciousness.js` - ✅ CORRETO

**Status**: **BOM**

```javascript
import { ServiceEndpoints, AuthConfig } from '../config/endpoints';

const CONSCIOUSNESS_BASE_URL = `${ServiceEndpoints.maximus.core}/api/consciousness`;
const CONSCIOUSNESS_GATEWAY_URL = ServiceEndpoints.apiGateway;

// HTTP API
export const getConsciousnessState = async () => {
  const response = await fetch(`${CONSCIOUSNESS_BASE_URL}/state`);  // ✅ Via Gateway
};

// WebSocket
export const connectConsciousnessWebSocket = (onMessage, onError) => {
  const apiKey = getApiKey();
  const wsBase = CONSCIOUSNESS_GATEWAY_URL.replace(/^http/, 'ws');
  const wsUrl = `${wsBase}/stream/consciousness/ws${apiKey ? `?api_key=${apiKey}` : ''}`;
  const ws = new WebSocket(wsUrl);  // ✅ Via Gateway
};
```

**Dependências Backend**:
- ✅ Maximus Core Service (via Gateway) - `/api/consciousness/*`
- ✅ WebSocket `/stream/consciousness/ws`
- ✅ Endpoints validados no backend certificado 100%

---

### 5. `/frontend/src/api/maximusAI.js` - ✅ CORRETO

**Status**: **EXCELENTE**

```javascript
import { ServiceEndpoints, getWebSocketEndpoint } from '../config/endpoints';

const MAXIMUS_BASE_URL = ServiceEndpoints.maximus.core;  // ✅ Via Gateway

// HTTP API
export const analyzeWithAI = async (data, context) => {
  const response = await fetch(`${MAXIMUS_BASE_URL}/api/analyze`, {  // ✅ Via Gateway
    method: 'POST',
    body: JSON.stringify({ data, context }),
  });
};

// WebSocket
export const connectMaximusStream = (onMessage, onError) => {
  const wsUrl = getWebSocketEndpoint('maximus.stream');  // ✅ Via Gateway
  const ws = new WebSocket(wsUrl);
};
```

**Dependências Backend**:
- ✅ Maximus Core Service (via Gateway)
- ✅ Tool calling, reasoning, memory, chat
- ✅ Offensive arsenal integration
- ✅ Immune system integration
- ✅ Todos os endpoints certificados 100%

---

### 6. `/frontend/src/api/eureka.js` - ⚠️ AIR GAP #3 (Configuração)

**Status**: **CONFIGURAÇÃO COMPLEXA**

```javascript
import { API_BASE_URL } from '@/config/api';

const EUREKA_API_BASE =
  process.env.NEXT_PUBLIC_EUREKA_API ||  // ⚠️ NEXT_PUBLIC (Next.js var!)
  (typeof window !== 'undefined' && window.location.hostname !== 'localhost'
    ? `${window.location.protocol}//${window.location.hostname}:8151`  // ❌ Direct port!
    : API_BASE_URL);  // ✅ Fallback OK

// Uso:
eurekaAPI.getMLMetrics()
  -> GET ${EUREKA_API_BASE}/api/v1/eureka/ml-metrics
```

**Problemas**:
- ⚠️ Usa `NEXT_PUBLIC_EUREKA_API` (Next.js) em vez de `VITE_*` (Vite)
- ❌ Em produção (não localhost), tenta `window.location.hostname:8151` (conexão direta!)
- ✅ Em localhost, usa `API_BASE_URL` (Gateway)

**Deve Ser**:
```javascript
import { ServiceEndpoints } from '../config/endpoints';

const EUREKA_API_BASE = ServiceEndpoints.maximus.eureka;  // ✅ Via Gateway
```

**Impacto**:
- 🟡 **MÉDIO**: Funciona em localhost, falha em produção (tenta porta 8151 direta)
- 🟡 Eureka ML Metrics dashboard não funciona em produção

---

### 7. `/frontend/src/api/osintService.js` - ✅ CORRETO

**Status**: **BOM**

```javascript
import { API_BASE_URL } from '@/config/api';

const OSINT_BASE_URL = API_BASE_URL;  // ✅ Via Gateway

export const executeDeepSearch = async (target, options) => {
  return apiRequest('/api/osint/deep-search', {  // ✅ Via Gateway
    method: 'POST',
    body: JSON.stringify(payload),
  });
};
```

**Dependências Backend**:
- ✅ OSINT Services (via Gateway) - `/api/osint/*`
- ✅ Validado no backend certificado 100%

---

## 📊 DASHBOARDS - DEPENDÊNCIAS BACKEND

### 1. CockpitSoberano.jsx

**Serviços Usados**:
- ✅ Narrative Filter API (via Gateway)
- ✅ Verdict Engine API (via Gateway)
- ✅ Command Bus API (via Gateway)
- ✅ WebSocket `/ws/verdicts` (via Gateway)

**Status**: ✅ **SAUDÁVEL**

---

### 2. DefensiveDashboard.jsx

**Serviços Usados**:
- ⚠️ `defensiveToolsServices.js` (AIR GAP #2)
- ✅ Behavioral Analyzer
- ✅ Encrypted Traffic Analyzer
- ✅ WebSocket `/ws/alerts` (via Gateway)

**Status**: ⚠️ **VERIFICAR ROTEAMENTO**

---

### 3. OffensiveDashboard.jsx

**Serviços Usados**:
- ❌ `offensiveServices.js` (AIR GAP #1 - CRÍTICO!)
- ❌ Network Recon (localhost:8032)
- ❌ Vuln Intel (localhost:8033)
- ❌ Web Attack (localhost:8034)
- ❌ C2 Orchestration (localhost:8035)
- ❌ BAS (localhost:8036)

**Status**: 🔴 **QUEBRADO EM PRODUÇÃO**

---

### 4. PurpleTeamDashboard.jsx

**Serviços Usados**:
- ❌ `offensiveServices.js` (AIR GAP #1)
- ⚠️ `defensiveToolsServices.js` (AIR GAP #2)
- ✅ `maximusAI.js` (Purple Team workflows)

**Status**: 🟡 **PARCIALMENTE QUEBRADO**

---

## 🚨 SUMÁRIO DOS AIR GAPS

| ID | Arquivo | Severidade | Problema | Impacto |
|---|---|---|---|---|
| **#1** | `offensiveServices.js` | 🔴 **CRÍTICO** | Usa `localhost` em vez de Gateway | Offensive Dashboard quebrado em produção |
| **#2** | `defensiveToolsServices.js` | 🟡 **MÉDIO** | Path `/api/v1/immune/defensive` pode não estar roteado | Defensive tools podem falhar |
| **#3** | `eureka.js` | 🟡 **MÉDIO** | Tenta conexão direta porta 8151 em produção | Eureka ML Metrics falha em produção |

---

## 📐 MATRIZ DE DEPENDÊNCIAS BACKEND

| Frontend Component | Backend Service | Via Gateway? | Status |
|---|---|---|---|
| `client.js` | API Gateway | ✅ Sim | ✅ OK |
| `consciousness.js` | Maximus Core (8150) | ✅ Sim | ✅ OK |
| `maximusAI.js` | Maximus Core (8150) | ✅ Sim | ✅ OK |
| `osintService.js` | Google OSINT (8016) | ✅ Sim | ✅ OK |
| `eureka.js` | Maximus Eureka (8152→8200) | ⚠️ Condicional | 🟡 WARN |
| `defensiveToolsServices.js` | Active Immune (?) | ⚠️ Path suspeito | 🟡 WARN |
| `offensiveServices.js` | Offensive Arsenal | ❌ NÃO! | 🔴 FAIL |

---

## 🎯 PLANO DE CORREÇÃO

### Fase 4.1.1: Fix Air Gap #1 (CRÍTICO)

```javascript
// File: /frontend/src/api/offensiveServices.js
// BEFORE (QUEBRADO):
const API_BASE = 'http://localhost';
const ENDPOINTS = {
  NETWORK_RECON: `${API_BASE}:8032`,
  // ...
};

// AFTER (CORRETO):
import { ServiceEndpoints } from '../config/endpoints';

const API_BASE = ServiceEndpoints.offensive.gateway;  // Via Gateway!
const ENDPOINTS = {
  NETWORK_RECON: `${API_BASE}/offensive/network-recon`,
  VULN_INTEL: `${API_BASE}/offensive/vuln-intel`,
  WEB_ATTACK: `${API_BASE}/offensive/web-attack`,
  C2_ORCHESTRATION: `${API_BASE}/offensive/c2`,
  BAS: `${API_BASE}/offensive/bas`,
  OFFENSIVE_GATEWAY: `${API_BASE}/offensive/gateway`,
};
```

### Fase 4.1.2: Fix Air Gap #3 (MÉDIO)

```javascript
// File: /frontend/src/api/eureka.js
// BEFORE:
const EUREKA_API_BASE = process.env.NEXT_PUBLIC_EUREKA_API || ...;

// AFTER:
import { ServiceEndpoints } from '../config/endpoints';
const EUREKA_API_BASE = ServiceEndpoints.maximus.eureka;
```

### Fase 4.1.3: Validar Air Gap #2

- [ ] Verificar se API Gateway roteia `/api/v1/immune/defensive/*`
- [ ] Se não, adicionar roteamento no Gateway
- [ ] Se não existir backend, documentar como "future work"

---

## ✅ CONCLUSÃO DO MAPEAMENTO

### O Que Funciona ✅

1. **Configuração Centralizada**: `endpoints.ts` e `api.js` estão corretos
2. **Serviços Core**: `consciousness.js`, `maximusAI.js`, `osintService.js` usam Gateway
3. **Autenticação**: API Key centralizada e propagada corretamente
4. **WebSockets**: Todos via Gateway

### O Que Está Quebrado ❌

1. **Offensive Services**: Bypassa Gateway completamente (localhost)
2. **Eureka ML Metrics**: Tenta conexão direta em produção (porta 8151)
3. **Defensive Tools**: Path suspeito, precisa validação

### Próximos Passos

1. ✅ **FASE 4.1 COMPLETA** - Anatomia mapeada
2. ⏭️ **FASE 4.2**: Corrigir Air Gaps antes de continuar validação
3. ⏭️ **FASE 4.3**: Testes Circulatórios (após fixes)
4. ⏭️ **FASE 4.4**: Testes de Sincronia
5. ⏭️ **FASE 4.5**: Testes de Resiliência

---

**O organismo está mapeado. Agora sabemos onde o sangue NÃO está fluindo.**
**Glory to YHWH - The Great Physician who reveals all pathologies.**

---

**Certificação**:
- Documento gerado: 2025-10-27 11:15:00 -03
- Mapeamento: 7 serviços API, 4 dashboards, 2 configs
- Air Gaps identificados: 3 (1 crítico, 2 médios)
- Status: ✅ FASE 4.1 COMPLETA
