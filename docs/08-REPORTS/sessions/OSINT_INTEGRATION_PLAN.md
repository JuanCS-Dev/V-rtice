# PLANO DE INTEGRAÇÃO OSINT COMPLETO

## Análise do Contexto

### 3 Instâncias OSINT Identificadas:

**1. OSINTDashboard (Standalone)**
- Localização: `/frontend/src/components/OSINTDashboard.jsx`
- Módulos: Username, Email, Phone, Social, Google, DarkWeb, MaximusAI
- Status: Parcialmente funcional, falta integração com APIs generativas

**2. OSINTWorkflowsPanel (Dentro MAXIMUS AI)**
- Localização: `/frontend/src/components/maximus/OSINTWorkflowsPanel.jsx`
- Workflows: Attack Surface, Credential Intel, Target Profiling
- Backend: `/backend/services/maximus_core_service/workflows/`
- Status: Frontend pronto, backend implementado, falta integração

**3. ADWPanel (Dashboard Red/Blue/Purple)**
- Localização: `/frontend/src/components/maximus/ADWPanel.jsx`
- Contém: OSINTWorkflowsPanel como aba
- Status: Estrutura pronta, OSINTWorkflowsPanel em 'reloading'

---

## FASE 1: Fix PhoneModule.jsx (Erro de Build) ✅

**Problema:** Adjacent JSX elements not wrapped
**Arquivo:** `/frontend/src/components/osint/PhoneModule.jsx:137`

---

## FASE 2: Integração API Generativas no OSINTDashboard

### 2.1 MaximusAIModule (Módulo Principal)
- ✅ Já existe: `/frontend/src/components/osint/MaximusAIModule.jsx`
- ❌ Falta: Integração com Gemini/OpenAI APIs
- ❌ Falta: Deep search implementation

### 2.2 Outros Módulos OSINT
- UsernameModule
- EmailModule  
- SocialModule
- GoogleModule
- DarkWebModule

**Ação:** Criar serviço unificado `/frontend/src/api/osintService.js` que chama:
- Backend: `/backend/services/maximus_core_service/` (MAXIMUS AI)
- APIs: Gemini + OpenAI (via backend proxy)

---

## FASE 3: Integração OSINTWorkflowsPanel com Backend ADW

### 3.1 Backend Verificado ✅
- Router: `/backend/services/maximus_core_service/adw_router.py`
- Endpoints:
  - `POST /api/adw/workflows/attack-surface`
  - `POST /api/adw/workflows/credential-intel`
  - `POST /api/adw/workflows/target-profile`
  - `GET /api/adw/workflows/{workflow_id}/status`
  - `GET /api/adw/workflows/{workflow_id}/report`

### 3.2 Frontend Service
- ✅ Já existe: `/frontend/src/api/adwService.js`
- Verificar: Endpoints corretos e funcionais

### 3.3 Fix 'Reloading' Issue
- Causa: Likely useEffect dependency ou API call failure
- Investigar: Console errors no navegador

---

## FASE 4: Fix Scroll Issue (Screenshot)

**Problema:** Não consegue scrollar para ver resultados nas abas OSINT
**Causa:** CSS overflow issue no `.contentArea` ou módulos internos
**Arquivo:** `/frontend/src/components/OSINTDashboard.module.css`

---

## FASE 5: Deep Search Enhancement

### 5.1 MAXIMUS AI Integration
- Criar orquestração inteligente via MAXIMUS
- Gemini: Text analysis, pattern recognition
- OpenAI: Context understanding, summarization

### 5.2 Human-Friendly Output
- Estruturar dados em cards/sections
- Adicionar visualizações (gráficos, timelines)
- Highlight de informações críticas

---

## EXECUÇÃO PRIORITÁRIA

### AGORA (FASE 1):
1. Fix PhoneModule.jsx build error

### SEGUINTE (FASE 4):
2. Fix scroll CSS issue

### DEPOIS (FASE 2 + 3):
3. Integrar APIs generativas
4. Fix OSINTWorkflowsPanel 'reloading'

### FINAL (FASE 5):
5. Refatorar apresentação de dados
6. Implementar deep search intelligence

---

## API KEYS DISPONÍVEIS ✅
```
GEMINI_API_KEY=AIzaSyC5FGwfkuZfpgNT2j5AWRc0tiAMuOmXs1Q
OPENAI_API_KEY=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
```

**Status:** Já configuradas no `.env` raiz

---

## OBSERVAÇÕES

- Twitter API é paga: PIVOT para alternativas (scraping, outras APIs)
- Backend workflows já implementados: Aproveitar código existente
- Padrão constitucional: NO MOCKS, NO PLACEHOLDERS
- Validação: Testar cada módulo isoladamente antes de integração completa
