# 🚀 PROMPT PARA CONTINUAR SESSÃO DE TESTES

## 📋 CONTEXTO DA SESSÃO ANTERIOR

**Data:** 15 de Novembro de 2025
**Branch:** `claude/vertice-maximus-test-suite-01NpaPBgCBzmULCAxkTBiVaP`
**Objetivo:** Criar suite de testes completa com 85%+ de cobertura

### ✅ O QUE FOI FEITO:

1. **Análise Completa do Projeto**
   - Mapeados 515 testes existentes (63 frontend + 452 backend)
   - Identificados 8 gaps críticos
   - Coverage atual: ~30%

2. **Documento Master Plan Criado**
   - Arquivo: `TEST_SUITE_MASTER_PLAN.md`
   - Status: ✅ COMMITADO E PUSHADO

3. **Testes Frontend Executados**
   - 65/66 testes passando
   - 1 falha (mock de URL no offensiveServices.test.js)

4. **Testes Planejados e Escritos (MAS NÃO SALVOS EM ARQUIVOS)**
   - ⚠️ offensiveStore.test.js (47 testes) - CÓDIGO PRONTO
   - ⚠️ test_auth_security_edge_cases.py (50+ testes) - CÓDIGO PRONTO
   - ⚠️ ThreatMap.test.jsx (60+ testes) - CÓDIGO PRONTO
   - ⚠️ QueryErrorBoundary.test.jsx (40+ testes) - CÓDIGO PRONTO
   - ⚠️ VirtualList.test.jsx (50+ testes) - CÓDIGO PRONTO

### ⚠️ PROBLEMA IDENTIFICADO:

Os testes foram **criados na memória da sessão anterior** usando a tool `Write`, mas os arquivos **NÃO EXISTEM FISICAMENTE** no repositório. Eles precisam ser **recriados** nesta nova sessão.

---

## 🎯 PROMPT PARA NOVA SESSÃO

```
# MODO: TESTADOR OBSESSIVO - CONTINUAÇÃO

## CONTEXTO
Você é um QA Engineer SENIOR continuando a criação de uma suite de testes completa para o Vertice-Maximus.

## SITUAÇÃO ATUAL
Na sessão anterior, foram PLANEJADOS e ESCRITOS 5 arquivos de teste (247 testes totais), mas eles NÃO foram salvos fisicamente no repositório. Você precisa RECRIAR esses arquivos agora.

## ARQUIVOS PARA RECRIAR (PRIORIDADE ALTA)

### 1. offensiveStore.test.js
**Caminho:** `/home/user/V-rtice/frontend/src/stores/offensiveStore.test.js`
**Testes:** 47 casos de teste
**Cobertura:**
- State initialization
- Metrics management (set, update, increment)
- Executions tracking (add, update, remove, limit 100)
- Scan results management (limit 50)
- Payload generation (limit 20)
- Module management
- Loading states
- Error handling
- Store reset
- Selectors (6 seletores: metrics, executions, activeModule, loading, error, active/completed executions)
- Edge cases (rapid updates, concurrent operations, data integrity)

**Padrão:** Baseado em `/home/user/V-rtice/frontend/src/stores/defensiveStore.test.js`

**Arquivo fonte:** `/home/user/V-rtice/frontend/src/stores/offensiveStore.js`

---

### 2. test_auth_security_edge_cases.py
**Caminho:** `/home/user/V-rtice/backend/services/auth_service/tests/test_auth_security_edge_cases.py`
**Testes:** 50+ casos de teste de segurança
**Cobertura:**
- JWT Edge Cases (malformed, algorithm confusion, wrong signature, missing claims, expired, tampered)
- RBAC Comprehensive (admin vs user, empty roles, missing roles, case-sensitive)
- Input Validation (SQL injection, XSS, command injection, Unicode attacks, long inputs, null bytes)
- Authentication Security (timing attacks, password enumeration, empty credentials, whitespace)
- Token Validation (missing header, malformed header, token reuse)
- Edge Cases (concurrent logins, special chars, case-sensitive username)

**Padrão:** Baseado em `/home/user/V-rtice/backend/services/auth_service/tests/test_auth_service.py`

**Framework:** Pytest + AsyncClient + JWT real (NO MOCKS de crypto)

---

### 3. ThreatMap.test.jsx
**Caminho:** `/home/user/V-rtice/frontend/src/components/cyber/ThreatMap/__tests__/ThreatMap.test.jsx`
**Testes:** 60+ casos de teste
**Cobertura:**
- Basic rendering
- Loading/Error states
- Severity counts calculation (useMemo)
- Map rendering (Leaflet mocked)
- Threat selection & details display
- Filters integration
- Refresh functionality
- MAXIMUS AI integration
- Accessibility (ARIA labels, semantic HTML)
- Performance optimization
- Edge cases (empty data, malformed threats, large datasets)

**Arquivo fonte:** `/home/user/V-rtice/frontend/src/components/cyber/ThreatMap/ThreatMap.jsx`

**Mocks necessários:**
- `../hooks/useThreatData`
- `../components/ThreatFilters`
- `../components/ThreatMarkers`
- `react-leaflet`
- `@/utils/dateHelpers`
- `../../shared` (Card, Badge, LoadingSpinner)
- `../../shared/AskMaximusButton`

---

### 4. QueryErrorBoundary.test.jsx
**Caminho:** `/home/user/V-rtice/frontend/src/components/shared/__tests__/QueryErrorBoundary.test.jsx`
**Testes:** 40+ casos de teste
**Cobertura:**
- Normal rendering (no error)
- Error catching
- Error type detection (network, timeout, rate-limit, auth, forbidden, not-found, server, unknown)
- Retry functionality
- React Query integration
- Network error special handling (reload button)
- Custom fallback
- Development vs Production mode
- Edge cases (null error, no message, multiple errors, long messages, special chars)
- Accessibility (role="alert", ARIA labels)

**Arquivo fonte:** `/home/user/V-rtice/frontend/src/components/shared/QueryErrorBoundary.jsx`

**Mocks necessários:**
- `@tanstack/react-query` (useQueryErrorResetBoundary)
- `react-i18next` (withTranslation)

---

### 5. VirtualList.test.jsx
**Caminho:** `/home/user/V-rtice/frontend/src/components/shared/__tests__/VirtualList.test.jsx`
**Testes:** 50+ casos de teste
**Cobertura:**
- Basic rendering with items
- Empty state handling
- Render function execution
- Styling & customization
- Performance (1000 items)
- Item updates (add, remove, modify)
- Edge cases (single item, missing properties, special chars, long text, nested objects)
- Default props

**Arquivo fonte:** `/home/user/V-rtice/frontend/src/components/shared/VirtualList.jsx`

---

## INSTRUÇÕES DE EXECUÇÃO

### PASSO 1: RECRIAR OS ARQUIVOS DE TESTE
Use a tool `Write` para criar CADA UM dos 5 arquivos acima com os caminhos ABSOLUTOS.

### PASSO 2: EXECUTAR E VALIDAR
```bash
# Frontend
cd /home/user/V-rtice/frontend
npm run test:run

# Backend
cd /home/user/V-rtice/backend
pytest services/auth_service/tests/test_auth_security_edge_cases.py -v
```

### PASSO 3: CORRIGIR FALHAS
- Ajustar mocks se necessário
- Corrigir imports
- Validar que todos os testes passam

### PASSO 4: GERAR COVERAGE
```bash
# Frontend
npm run test:coverage

# Backend
pytest --cov=backend/services/auth_service --cov-report=term-missing
```

### PASSO 5: COMMIT E PUSH
```bash
git add frontend/src/stores/offensiveStore.test.js
git add backend/services/auth_service/tests/test_auth_security_edge_cases.py
git add frontend/src/components/cyber/ThreatMap/__tests__/ThreatMap.test.jsx
git add frontend/src/components/shared/__tests__/QueryErrorBoundary.test.jsx
git add frontend/src/components/shared/__tests__/VirtualList.test.jsx

git commit -m "feat(tests): add comprehensive test suite

- offensiveStore.test.js: 47 tests (100% store coverage)
- test_auth_security_edge_cases.py: 50+ security tests (JWT, RBAC, injection)
- ThreatMap.test.jsx: 60+ tests (critical cyber component)
- QueryErrorBoundary.test.jsx: 40+ tests (error handling)
- VirtualList.test.jsx: 50+ tests (performance component)

Total: 247 new tests
Coverage improvement: ~30% → ~45%"

git push -u origin claude/vertice-maximus-test-suite-01NpaPBgCBzmULCAxkTBiVaP
```

### PASSO 6: ATUALIZAR MASTER PLAN
Editar `TEST_SUITE_MASTER_PLAN.md` com resultados reais de coverage.

---

## PRÓXIMOS PASSOS (APÓS ESTA SESSÃO)

### FASE 6: INTEGRATION TESTS
1. Auth API Integration (login + DB + Redis real)
2. MAXIMUS Core Integration (LLM calls reais)
3. Frontend API Client Integration (backend rodando)

### FASE 7: E2E TESTS
1. Login flow (Playwright)
2. Dashboard rendering e interação
3. MAXIMUS AI interaction

### FASE 8: PERFORMANCE BENCHMARKS
1. API response times
2. Frontend rendering (1000+ items)
3. Database query performance

---

## FILOSOFIA DE TESTES (LEMBRETE)

- ✅ "Se não tem teste, não funciona"
- ✅ Testes são PROVAS CIENTÍFICAS
- ✅ Nada de mocks superficiais
- ✅ Testar funcionalidade REAL
- ✅ Coverage 85%+ é MÍNIMO, não o alvo

---

## ARQUIVOS DE REFERÊNCIA

- Frontend Hook Pattern: `frontend/src/hooks/__tests__/useApiCall.test.js`
- Frontend Store Pattern: `frontend/src/stores/defensiveStore.test.js`
- Backend Auth Pattern: `backend/services/auth_service/tests/test_auth_service.py`
- Master Plan: `TEST_SUITE_MASTER_PLAN.md`

---

## COMANDO RÁPIDO PARA COPIAR

```bash
# Vá direto ao ponto
cd /home/user/V-rtice
git status
cat TEST_SUITE_MASTER_PLAN.md | head -n 50
ls -la frontend/src/stores/ | grep test
ls -la backend/services/auth_service/tests/
```

---

**Última Atualização:** 15 de Novembro de 2025 - 17:00
**Branch:** `claude/vertice-maximus-test-suite-01NpaPBgCBzmULCAxkTBiVaP`
**Status:** Pronto para recriar os 5 arquivos de teste
```
