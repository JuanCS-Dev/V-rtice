# 📋 OSINT MODULE - OPERATIONAL PLAN

## Status Atual: DIAGNÓSTICO COMPLETO

### Problemas Identificados:
1. ❌ API Gemini não integrada no backend OSINT
2. ❌ API OpenAI duplicada no .env (corrigido)
3. ❌ Twitter API requer pagamento (graceful degradation implementado)
4. ❌ Frontend não retorna dados úteis (shallow data)
5. ❌ PhoneModule.jsx com erro JSX (sintaxe)
6. ❌ Scroll bloqueado nas abas OSINT dash
7. ❌ ADW OSINT sub-aba em "reloading" infinito

---

## 🎯 FASE 1: FIXES CRÍTICOS (IMEDIATO)

### 1.1 - Backend Integration
**Arquivo:** `backend/services/osint_service/ai_processor.py`
**Status:** ✅ Gemini + OpenAI já integrados
**Action:** Validar propagação de variáveis de ambiente

### 1.2 - Frontend JSX Fix
**Arquivo:** `frontend/src/components/osint/PhoneModule.jsx`
**Status:** ❌ Erro JSX na linha 137
**Action:** Corrigir estrutura JSX faltante

### 1.3 - Environment Variables
**Arquivo:** `.env`
**Status:** ✅ OPENAI_API_KEY corrigido (duplicação removida)
**Vars:**
- ✅ GEMINI_API_KEY=AIzaSyC5FGwfkuZfpgNT2j5AWRc0tiAMuOmXs1Q
- ✅ OPENAI_API_KEY=sk-proj-gjQq8nUo...

### 1.4 - Twitter API Pivot
**Status:** ✅ Graceful degradation implementado
**Logic:** Retorna mensagem "Twitter API requires paid subscription"

---

## 🎯 FASE 2: DEEP SEARCH ENHANCEMENT

### 2.1 - Maximus AI Integration
**Goal:** MAXIMUS controla OSINT via ai_orchestrator.py
**Files:**
- `backend/services/osint_service/ai_orchestrator.py`
- `backend/services/osint_service/api.py` (endpoints)

**Enhancements:**
1. Agregar múltiplas fontes (breach, google, darkweb, social)
2. AI Correlation via Gemini/OpenAI
3. Risk scoring baseado em ML
4. Timeline construction
5. Anomaly detection

### 2.2 - Data Sources Integration
**Current:**
- BreachDataAnalyzer ✅
- GoogleDorkScanner ✅
- DarkWebMonitor ✅
- SocialMediaScraper ⚠️ (Twitter degraded)

**Add:**
- Shodan integration (IP intel)
- HaveIBeenPwned API
- TOR network search
- Pastebin scraping
- GitHub commits search

### 2.3 - Response Structure
**Format:** Human-Friendly Presentation
```json
{
  "executive_summary": "2-3 sentence overview",
  "entity_profile": {
    "name": "...",
    "username": "...",
    "online_presence_score": 75
  },
  "risk_assessment": {
    "level": "high",
    "overall_score": 85,
    "factors": [...]
  },
  "timeline": [...],
  "insights": [...],
  "anomalies": [...],
  "confidence": {
    "overall_score": 90,
    "data_completeness": 85,
    "cross_validation": 95
  }
}
```

---

## 🎯 FASE 3: FRONTEND FIXES

### 3.1 - Scroll Issue
**Problema:** Frame central não permite scroll
**Files Affected:**
- `frontend/src/components/osint/MaximusAIModule.jsx`
- `frontend/src/components/osint/PhoneModule.jsx`
- `frontend/src/components/osint/EmailModule.jsx`
- Todas as abas OSINT

**Fix:**
```css
.results-container {
  max-height: 600px;
  overflow-y: auto;
  padding-right: 8px; /* Scrollbar spacing */
}
```

**Status:** Parcialmente implementado em MaximusAIModule (linha 91)
**Action:** Propagar para todos os módulos

### 3.2 - ADW OSINT Reloading Fix
**File:** `frontend/src/components/maximus/OSINTWorkflowsPanel.jsx`
**Problema:** Polling infinito sem dados
**Root Cause:** API endpoint não implementado ou erro 500

**Fix Options:**
1. Verificar API `/api/workflows/osint/status`
2. Adicionar error boundary
3. Timeout no polling (max 30s)
4. Fallback UI quando API indisponível

---

## 🎯 FASE 4: AI INTEGRATION (CRÍTICO)

### 4.1 - Backend AI Orchestrator
**File:** `backend/services/osint_service/ai_orchestrator.py`
**Current:** Básico, sem deep intelligence
**Goal:** AI-driven investigation strategy

**Enhancements:**
1. **Dynamic Source Selection**
   - AI decide quais fontes consultar baseado no target type
   - Priority ranking (breach > social > google > darkweb)

2. **Correlation Engine**
   - Cross-reference data entre múltiplas fontes
   - Entity resolution (mesmo usuário em plataformas diferentes)
   - Timeline correlation

3. **Risk Scoring Algorithm**
   ```python
   risk_score = (
       breach_exposure * 0.4 +
       social_footprint * 0.2 +
       darkweb_mentions * 0.3 +
       behavioral_anomalies * 0.1
   )
   ```

4. **Insight Generation (via LLM)**
   - Prompt: "Analyze this OSINT data and provide 3-5 actionable insights"
   - Provider: Gemini Pro (primary) / GPT-4 (fallback)

### 4.2 - Frontend AI Results Display
**File:** `frontend/src/components/osint/MaximusAIModule.jsx`
**Current:** ✅ Estrutura completa já implementada
**Status:** Aguardando backend retornar dados completos

---

## 🎯 FASE 5: E2E VALIDATION

### 5.1 - Test Scenarios
1. **Username Search:**
   - Input: "juan", "elon_musk", "snowden"
   - Expected: Profile + social + breaches + risk score

2. **Email Search:**
   - Input: "test@example.com"
   - Expected: Breach data + domain reputation

3. **Phone Search:**
   - Input: "+5562999999999"
   - Expected: Carrier + location + risk assessment

### 5.2 - Success Criteria
- ✅ 0 erros no console
- ✅ Dados reais retornados (não mock)
- ✅ Response time < 10s
- ✅ AI summary presente
- ✅ Risk score calculado
- ✅ UI responsiva com scroll funcional

---

## 📊 EXECUTION ORDER

### Ordem de Implementação:
```
FASE 1 (30min) → FASE 3.1 (20min) → FASE 3.2 (15min) 
→ FASE 2.1 (1h) → FASE 2.2 (2h) → FASE 4 (2h) 
→ FASE 5 (30min)
```

**Total Estimado:** 6h 35min

### Priority Stack:
1. 🔥 Fix PhoneModule.jsx JSX (BLOQUEADOR)
2. 🔥 Fix scroll issue (UX CRÍTICO)
3. 🔥 Fix ADW OSINT reloading (UX CRÍTICO)
4. ⚡ Integrate AI deep analysis (CORE FEATURE)
5. ⚡ Add missing data sources (DEPTH)
6. ✅ E2E testing

---

## 🚀 PRÓXIMOS PASSOS

### Comandos de Validação:
```bash
# 1. Rebuild backend OSINT service
cd /home/juan/vertice-dev/backend/services/osint_service
docker-compose up --build -d osint_service

# 2. Verificar logs
docker logs -f osint_service

# 3. Test API
curl -X POST http://localhost:8000/api/investigate/deep \
  -H "Content-Type: application/json" \
  -d '{"username": "juan"}'

# 4. Rebuild frontend
cd /home/juan/vertice-dev/frontend
npm run build
```

---

## 📝 NOTAS TÉCNICAS

### AI Provider Selection:
- **Primary:** Gemini Pro (free tier, 60 req/min)
- **Fallback:** OpenAI GPT-4 (paid, más confiável)
- **Strategy:** Try Gemini first → fallback to OpenAI on error

### Rate Limiting:
- OSINT Service: 10 req/s
- Gemini: 60 req/min
- OpenAI: Depende do tier

### Data Persistence:
- Investigation results → PostgreSQL
- Reports → JSON files + DB
- Cache → Redis (1h TTL)

---

**Plano Criado:** 2025-10-18 14:45 UTC
**Status:** AGUARDANDO APROVAÇÃO PARA EXECUÇÃO
**Arquiteto:** Claude (sob direção de Juan)
