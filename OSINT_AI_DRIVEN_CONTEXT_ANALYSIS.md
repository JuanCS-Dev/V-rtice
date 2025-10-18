# ANÁLISE COMPLETA: 3 FERRAMENTAS OSINT AI-DRIVEN

**Data:** 2025-10-18  
**Status:** Análise de contexto antes de integração

---

## 🎯 OVERVIEW: 3 FERRAMENTAS DISTINTAS IDENTIFICADAS

### **1. OSINT Dashboard (STANDALONE)**
- **Localização:** `/frontend/src/components/dashboards/OSINTDashboard/`
- **Função:** Dashboard dedicado OSINT com múltiplos módulos
- **Módulos:**
  - Overview
  - Username Search
  - Email Search
  - Phone Search
  - Social Media
  - Dark Web
  - Google Dorking
  - Breach Data
  - **Maximus AI** (deep investigation)
  - Reports

**Características:**
- Interface standalone com sidebar própria
- MaximusAIModule.jsx → `/api/investigate/deep` endpoint
- Usa backend `/backend/services/osint_service/`
- Problema atual: Não retorna resultados úteis

---

### **2. ADW Panel → OSINT Workflows (SUB-ABA)**
- **Localização:** `/frontend/src/components/maximus/ADWPanel.jsx` → OSINTWorkflowsPanel
- **Função:** Workflows AI-driven dentro da dash AI
- **3 Workflows:**
  1. **Attack Surface Mapping** 🎯
     - Network recon + vulnerability correlation
     - Subdomain Enumeration + Port Scanning + CVE Correlation + Nuclei
  
  2. **Credential Intelligence** 🔑
     - Breach data + dark web + username enumeration
     - HIBP + Dark Web Monitoring + Google Dorking + Username Enum
  
  3. **Deep Target Profiling** 👤
     - Social media + EXIF + behavioral patterns
     - Social Media Scraping + Image EXIF + Pattern Detection + SE Vulnerability

**Características:**
- Componente: `OSINTWorkflowsPanel.jsx`
- API calls: `executeAttackSurfaceWorkflow()`, `executeCredentialIntelWorkflow()`, `executeTargetProfilingWorkflow()`
- Workflow status polling + report generation
- Export JSON functionality
- Problema atual: Sub-aba 'reloading' infinito

---

### **3. Workflows Panel → ML Automation (SUB-ABA)**
- **Localização:** `/frontend/src/components/maximus/WorkflowsPanel.jsx`
- **Função:** ML-powered orchestrated pipelines
- **Tabs:**
  - Manual Workflows (Full Assessment, OSINT Investigation, Purple Team, etc.)
  - **ML Automation** (MLAutomationTab)
  - History

**Características:**
- Workflow types: full_assessment, osint_investigation, purple_team, threat_hunting, web_recon, custom
- API calls: `aiFullAssessment()`, `aiOSINTInvestigation()`, `aiPurpleTeamExercise()`, `orchestrateWorkflow()`
- Multi-service orchestration with real-time AI guidance

---

## 🔍 DIFERENÇAS FUNDAMENTAIS

| Feature | OSINT Dashboard | ADW OSINT Workflows | ML Automation |
|---------|----------------|---------------------|---------------|
| **Localização** | Standalone dash | Sub-aba ADW Panel | Sub-aba Workflows Panel |
| **Propósito** | Single-module OSINT | Multi-phase workflows | ML orchestrator |
| **Granularidade** | Individual modules | Workflow phases | High-level orchestration |
| **Backend** | osint_service | adwService API | maximusAI API |
| **AI Integration** | MaximusAIModule | Implicit in workflows | Explicit ML |
| **Input Type** | Single identifiers | Workflow config | Target + options |
| **Output** | Individual results | Comprehensive reports | Multi-service results |

---

## 🚨 PROBLEMAS IDENTIFICADOS

### **1. OSINT Dashboard - Maximus AI Module**
- ❌ Endpoint `/api/investigate/deep` não retorna dados úteis
- ❌ Frontend espera Gemini API mas não está sendo chamada pelo backend
- ❌ Token Twitter agora é pago (pivotar solução)

### **2. ADW OSINT Workflows**
- ❌ Sub-aba 'reloading' infinito
- ❌ Workflows não executam (status nunca atualiza)
- ❌ API integration não funcional

### **3. ML Automation**
- ⚠️ Status desconhecido (verificar)

---

## 🎯 API ENDPOINTS IDENTIFICADOS

### **OSINT Service** (port: verificar)
```
POST /api/investigate/deep
  body: { username, email, phone }
  response: { status, data: { executive_summary, ... } }
```

### **ADW Service** (port: verificar)
```
POST /api/adw/workflows/attack-surface
POST /api/adw/workflows/credential-intel
POST /api/adw/workflows/target-profiling
GET /api/adw/workflows/{workflow_id}/status
GET /api/adw/workflows/{workflow_id}/report
```

### **Maximus AI** (port: verificar)
```
POST /api/maximus/ai/full-assessment
POST /api/maximus/ai/osint-investigation
POST /api/maximus/ai/purple-team
POST /api/maximus/ai/orchestrate
```

---

## 🧬 BACKEND SERVICES IDENTIFICADOS

### **1. osint_service**
- `/backend/services/osint_service/`
- Módulos: ai_orchestrator.py, ai_processor.py, scrapers/, analyzers/
- API: api.py

### **2. google_osint_service**
- `/backend/services/google_osint_service/`
- Função: Google Dorking específico

### **3. maximus_core_service**
- `/backend/services/maximus_core_service/`
- test_osint_workflows.py → testes de workflows

---

## 🔧 INTEGRAÇÕES NECESSÁRIAS

### **Generative AI APIs**
1. **Gemini API**
   - ✅ Key no .env: `GEMINI_API_KEY`
   - ❌ Não está sendo chamada pelo backend OSINT

2. **OpenAI API**
   - ✅ Key fornecida: `sk-proj-gjQj8nUo9IH...`
   - ❌ Não integrada no OSINT

### **Twitter API**
- ❌ Agora é pago → Pivotar para alternativas:
  - Nitter instances
  - Twitter scraping via web scraping
  - Alternative APIs (RapidAPI, etc.)

---

## 📋 PLANO DE AÇÃO (PRÓXIMOS PASSOS)

### **Fase 1: Investigação Backend**
1. ✅ Mapear backend services OSINT
2. ⏳ Verificar ports e rotas disponíveis
3. ⏳ Analisar código de ai_orchestrator.py e ai_processor.py
4. ⏳ Verificar integração com Gemini/OpenAI

### **Fase 2: Fix OSINT Dashboard**
1. ⏳ Adicionar OpenAI key no .env backend
2. ⏳ Integrar Gemini API no ai_processor.py
3. ⏳ Refatorar MaximusAIModule para deep search
4. ⏳ Pivotar Twitter API para alternativa

### **Fase 3: Fix ADW OSINT Workflows**
1. ⏳ Debug sub-aba reloading
2. ⏳ Verificar API endpoints ADW
3. ⏳ Implementar workflow execution
4. ⏳ Integrar AI generativa nos workflows

### **Fase 4: Scroll Fix**
1. ⏳ Corrigir overflow nos módulos OSINT Dashboard

### **Fase 5: Validação E2E**
1. ⏳ Testar Maximus AI Module com dados reais
2. ⏳ Testar 3 workflows ADW
3. ⏳ Testar ML Automation
4. ⏳ Verificar retorno de dados úteis

---

## 🔒 CONSTITUIÇÃO VÉRTICE - COMPLIANCE

- ✅ Análise de contexto completo antes de implementação (Cláusula 3.5)
- ✅ Visão sistêmica das 3 ferramentas distintas (Cláusula 3.2)
- ⏳ Aguardando aprovação do plano pelo Arquiteto-Chefe

---

**Status:** ANÁLISE COMPLETA - AGUARDANDO DIRETRIZ  
**Bloqueadores:** Nenhum  
**Alternativa:** Posso prosseguir com Fase 1 (Investigação Backend) se aprovado
