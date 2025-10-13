# 🧪 INSTRUÇÕES PARA TESTE MANUAL - PASSO A PASSO

## ⚠️ IMPORTANTE: LEIA ANTES DE COMEÇAR

Este documento contém instruções METODICAS para executar os testes manuais do HITL Console.
**Siga cada passo na ordem. NÃO pule etapas.**

---

## 📋 PRÉ-REQUISITOS (VERIFICAR ANTES DE INICIAR)

### ✅ Verificação 1: Mock API rodando
```bash
curl http://localhost:8003/hitl/health
```
**Esperado:** `{"status":"healthy","mode":"MOCK"}`

Se não estiver rodando:
```bash
cd /home/juan/vertice-dev/backend/services/adaptive_immune_system
PYTHONPATH=. python3 -m hitl.test_mock_api
```

### ✅ Verificação 2: Frontend environment
```bash
cat /home/juan/vertice-dev/frontend/.env | grep VITE_HITL_API_URL
```
**Esperado:** `VITE_HITL_API_URL=http://localhost:8003`

---

## 🚀 PASSO 1: INICIAR FRONTEND DEV SERVER

### Terminal 1: Mock API (já deve estar rodando)
```bash
# Verificar se está rodando:
curl http://localhost:8003/hitl/health

# Se não estiver, iniciar:
cd /home/juan/vertice-dev/backend/services/adaptive_immune_system
PYTHONPATH=. python3 -m hitl.test_mock_api
```

**Aguarde aparecer:**
```
🚀 Starting HITL Mock API Server...
📍 http://localhost:8003
✅ Initialized 15 mock APVs
INFO:     Uvicorn running on http://0.0.0.0:8003
```

### Terminal 2: Frontend Dev Server
```bash
cd /home/juan/vertice-dev/frontend
npm run dev
```

**Aguarde aparecer:**
```
VITE v5.4.x ready in xxx ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

**⏱️ Aguarde ~5 segundos para o servidor estar pronto**

---

## 🌐 PASSO 2: ABRIR BROWSER

1. Abra o navegador (Firefox ou Chrome)
2. Digite na barra de endereço: `http://localhost:5173`
3. Pressione ENTER
4. **Aguarde a página carregar completamente (~3-5 segundos)**

---

## 🧭 PASSO 3: NAVEGAR ATÉ HITL CONSOLE

1. Na página inicial, procure por "Admin Dashboard" ou "Admin"
2. Clique em "Admin Dashboard"
3. Você verá várias tabs/abas no topo
4. Procure pela tab **"HITL"** (deve ter ícone 🛡️)
5. Clique na tab "HITL"
6. **Aguarde a página carregar (~2-3 segundos)**

---

## ✅ TESTE CATEGORIA 1: INITIAL LOAD

### Teste 1.1: Verificar que a página carregou

**O QUE VERIFICAR:**
- [ ] 3 colunas aparecem na tela:
  - Esquerda: Lista de APVs (ReviewQueue)
  - Centro: Detalhes (ReviewDetails) - deve mostrar "No APV selected"
  - Direita: Painel de decisão (DecisionPanel) - deve estar desabilitado
- [ ] Header no topo mostra "HITL Console"
- [ ] Linha de scan animada (amarela) aparece
- [ ] Quick stats no header (números de pending/today)
- [ ] Barra de stats na parte inferior (6 cards com números)

**SE TUDO ACIMA ESTIVER OK:**
- Abra o arquivo: `/tmp/manual_ui_test_results.md`
- Procure por "Test 1.1: Page Loads Without Errors"
- Altere "Status: PENDING" para "Status: PASSED ✅"
- Em "Actual:" escreva "Página carregou corretamente, 3 colunas visíveis"

**SE ALGO FALHAR:**
- Altere para "Status: FAILED ❌"
- Em "Actual:" descreva o que você viu
- Em "Notes:" adicione detalhes do erro

---

## ✅ TESTE CATEGORIA 2: REVIEWQUEUE (COLUNA ESQUERDA)

### Teste 2.1: Verificar lista de APVs

**O QUE VERIFICAR:**
- [ ] Coluna esquerda mostra lista de APVs (deve ter ~15 itens)
- [ ] Cada APV card mostra:
  - APV Code (ex: "APV-TEST-001")
  - CVE ID (ex: "CVE-2024-12345")
  - Badge de severidade (🔴 Critical, 🟠 High, 🟡 Medium, 🟢 Low)
  - Package name (ex: "requests")
  - Patch strategy (ex: "version_bump")
  - Wargame verdict (ex: "PATCH_EFFECTIVE")
  - Tempo de espera (ex: "2.5 hours ago")

**DOCUMENTAR:**
- Arquivo: `/tmp/manual_ui_test_results.md`
- Teste: "Test 2.1: APV List Display"
- Status: PASSED ✅ ou FAILED ❌
- Actual: Descrever o que viu

### Teste 2.2: Filtro de Severity

**PASSOS:**
1. Na coluna esquerda, procure por um dropdown de "Severity"
2. Clique no dropdown
3. Selecione "Critical"
4. **Aguarde ~1 segundo**
5. Conte quantos APVs aparecem (deve ser ~3-5)
6. Volte o dropdown para "All"

**VERIFICAR:**
- [ ] Apenas APVs críticos (🔴) aparecem quando filtrado
- [ ] Lista volta ao normal quando seleciona "All"
- [ ] Sem erros no console do browser (F12 → Console)

**DOCUMENTAR:**
- Teste: "Test 2.2: Severity Filter"
- Status: PASSED ✅ ou FAILED ❌

### Teste 2.3: Filtro de Wargame Verdict

**PASSOS:**
1. Procure dropdown "Wargame Verdict" (ou similar)
2. Clique no dropdown
3. Selecione "PATCH_EFFECTIVE"
4. **Aguarde ~1 segundo**
5. Conte quantos APVs aparecem (deve ser ~5)
6. Volte para "All"

**VERIFICAR:**
- [ ] Apenas APVs com verdict "PATCH_EFFECTIVE" aparecem
- [ ] Badges verdes visíveis
- [ ] Lista volta ao normal

**DOCUMENTAR:**
- Teste: "Test 2.3: Wargame Verdict Filter"
- Status: PASSED ✅ ou FAILED ❌

### Teste 2.4: Filtros Combinados

**PASSOS:**
1. Selecione Severity: "Critical"
2. Selecione Wargame Verdict: "PATCH_EFFECTIVE"
3. **Aguarde ~1 segundo**
4. Conte APVs (deve ser 1-2)
5. Resete ambos filtros para "All"

**VERIFICAR:**
- [ ] Ambos filtros aplicados simultaneamente
- [ ] Apenas APVs que atendem AMBOS critérios aparecem

**DOCUMENTAR:**
- Teste: "Test 2.4: Combined Filters"
- Status: PASSED ✅ ou FAILED ❌

### Teste 2.5: Seleção de APV

**PASSOS:**
1. Resete todos filtros ("All")
2. Clique no PRIMEIRO APV da lista
3. **Observe a borda do card - deve ficar AMARELA**
4. Observe a coluna CENTRAL - deve mostrar detalhes do APV
5. Clique no SEGUNDO APV da lista
6. Observe que a borda amarela moveu para o segundo APV

**VERIFICAR:**
- [ ] APV selecionado tem borda amarela
- [ ] Coluna central atualiza com detalhes
- [ ] Apenas um APV selecionado por vez

**DOCUMENTAR:**
- Teste: "Test 2.5: APV Selection"
- Status: PASSED ✅ ou FAILED ❌

---

## ✅ TESTE CATEGORIA 3: REVIEWDETAILS (COLUNA CENTRAL)

### Teste 3.1: Navegação entre Tabs

**PASSOS:**
1. Certifique-se que um APV está selecionado (borda amarela)
2. Na coluna CENTRAL, você deve ver 4 tabs:
   - CVE
   - Patch
   - Wargame
   - Validation
3. Clique em cada tab, uma por vez
4. **Aguarde ~0.5s entre cada clique**

**VERIFICAR:**
- [ ] 4 tabs aparecem
- [ ] Tab ativa tem underline AMARELO
- [ ] Conteúdo muda ao clicar em cada tab
- [ ] Sem erros no console

**DOCUMENTAR:**
- Teste: "Test 3.1: Tab Navigation"
- Status: PASSED ✅ ou FAILED ❌

### Teste 3.2: Tab CVE

**PASSOS:**
1. Clique na tab "CVE"
2. **Observe o conteúdo**

**VERIFICAR:**
- [ ] CVE ID mostrado (ex: CVE-2024-12345)
- [ ] CVSS Score (ex: 9.8 / 10.0)
- [ ] Severity badge (🔴🟠🟡🟢)
- [ ] CWE information (ex: CWE-502: Deserialization)
- [ ] Description (parágrafo de texto)
- [ ] Published date

**DOCUMENTAR:**
- Teste: "Test 3.2: CVE Tab"
- Status: PASSED ✅ ou FAILED ❌

### Teste 3.3: Tab Patch

**PASSOS:**
1. Clique na tab "Patch"
2. **Observe o conteúdo**

**VERIFICAR:**
- [ ] Patch strategy label (ex: "Version Bump")
- [ ] Old version (ex: 1.2.3)
- [ ] New version (ex: 1.2.4)
- [ ] Diff viewer (linhas vermelhas/verdes)
- [ ] Syntax highlighting no diff

**DOCUMENTAR:**
- Teste: "Test 3.3: Patch Tab"
- Status: PASSED ✅ ou FAILED ❌

### Teste 3.4: Tab Wargame

**PASSOS:**
1. Clique na tab "Wargame"
2. **Observe o conteúdo**

**VERIFICAR:**
- [ ] Verdict badge (PATCH_EFFECTIVE/INCONCLUSIVE/PATCH_INSUFFICIENT)
- [ ] Seção "Before Patch":
  - Exit code (ex: 1)
  - Duration (ex: 2.34s)
  - Status badge (vermelho se vulnerável)
- [ ] Seção "After Patch":
  - Exit code (ex: 0)
  - Duration (ex: 0.12s)
  - Status badge (verde se protegido)

**DOCUMENTAR:**
- Teste: "Test 3.4: Wargame Tab"
- Status: PASSED ✅ ou FAILED ❌

### Teste 3.5: Tab Validation

**PASSOS:**
1. Clique na tab "Validation"
2. **Observe o conteúdo**

**VERIFICAR:**
- [ ] 5 validation checks visíveis:
  1. ✅ Syntax Valid
  2. ✅ Tests Pass
  3. ✅ Builds Successfully
  4. ✅ Security Scan Clean
  5. ✅ Performance Acceptable
- [ ] Cada check tem ícone (✅ ou ❌)
- [ ] Confidence score mostrado (ex: 0.95)
- [ ] Barra de confiança visual

**DOCUMENTAR:**
- Teste: "Test 3.5: Validation Tab"
- Status: PASSED ✅ ou FAILED ❌

---

## ✅ TESTE CATEGORIA 4: DECISIONPANEL (COLUNA DIREITA)

### Teste 4.1: Estado Inicial do Painel

**PASSOS:**
1. ANTES de selecionar um APV:
   - Observe a coluna DIREITA
   - Todos botões devem estar DESABILITADOS (cinza/opaco)
2. DEPOIS de selecionar um APV:
   - Observe novamente
   - Botões devem estar HABILITADOS (coloridos)

**VERIFICAR:**
- [ ] Sem APV: controles desabilitados
- [ ] Com APV: controles habilitados
- [ ] 4 botões visíveis: Approve, Reject, Modify, Escalate

**DOCUMENTAR:**
- Teste: "Test 4.1: Panel Initial State"
- Status: PASSED ✅ ou FAILED ❌

### Teste 4.2: Decisão APPROVE

**PASSOS:**
1. Selecione um APV com verdict "PATCH_EFFECTIVE" (verde)
2. Na coluna direita, clique no botão "Approve" (VERDE)
3. Campo de texto "Justification" deve aparecer
4. Digite: "Patch is effective and wargaming confirms protection. No issues detected."
5. Ajuste slider "Confidence" para 95%
6. Clique em "Submit Decision"
7. **Aguarde ~1-2 segundos**

**VERIFICAR:**
- [ ] Mensagem de sucesso aparece
- [ ] Sem erros no console
- [ ] Stats na parte inferior atualizam (Approved +1)

**DOCUMENTAR:**
- Teste: "Test 4.2: Approve Decision"
- Status: PASSED ✅ ou FAILED ❌

### Teste 4.3: Decisão REJECT

**PASSOS:**
1. Selecione um APV DIFERENTE
2. Clique no botão "Reject" (VERMELHO)
3. Digite justification: "Patch introduces breaking changes and fails tests."
4. Confidence: 80%
5. Submit

**VERIFICAR:**
- [ ] Mensagem de sucesso
- [ ] Stats atualizam (Rejected +1)

**DOCUMENTAR:**
- Teste: "Test 4.3: Reject Decision"
- Status: PASSED ✅ ou FAILED ❌

### Teste 4.4: Decisão MODIFY

**PASSOS:**
1. Selecione outro APV
2. Clique "Modify" (AMARELO)
3. Justification: "Patch needs minor adjustments to dependencies."
4. **Campo "Modifications" deve aparecer**
5. Modifications: "Change requests==1.2.4 to requests==1.2.5"
6. Confidence: 75%
7. Submit

**VERIFICAR:**
- [ ] Campo "Modifications" aparece (só para Modify)
- [ ] Submissão sucede
- [ ] Stats atualizam (Modified +1)

**DOCUMENTAR:**
- Teste: "Test 4.4: Modify Decision"
- Status: PASSED ✅ ou FAILED ❌

### Teste 4.5: Decisão ESCALATE

**PASSOS:**
1. Selecione APV com verdict "INCONCLUSIVE" (se tiver)
2. Clique "Escalate" (LARANJA)
3. Justification: "Results inconclusive. Requires senior review."
4. Confidence: 60%
5. Submit

**VERIFICAR:**
- [ ] Submissão sucede
- [ ] Stats atualizam (Escalated +1)

**DOCUMENTAR:**
- Teste: "Test 4.5: Escalate Decision"
- Status: PASSED ✅ ou FAILED ❌

### Teste 4.6: Validação de Formulário

**PASSOS:**
1. Selecione um APV
2. Clique "Approve"
3. **DEIXE o campo justification VAZIO**
4. Tente clicar em "Submit"

**VERIFICAR:**
- [ ] Mensagem de erro aparece: "Justification must be at least 10 characters"
- [ ] Submit NÃO acontece (sem chamada API)
- [ ] Botão desabilitado ou erro de validação mostrado

**DOCUMENTAR:**
- Teste: "Test 4.6: Form Validation"
- Status: PASSED ✅ ou FAILED ❌

---

## ✅ TESTE CATEGORIA 5: HITLSTATS (BARRA INFERIOR)

### Teste 5.1: Display de Stats

**PASSOS:**
1. Observe a barra inferior da página
2. Deve haver 6 cards

**VERIFICAR:**
- [ ] 6 stat cards visíveis:
  1. Pending Reviews (número)
  2. Decisions Today (número)
  3. Approved (número)
  4. Rejected (número)
  5. Modified (número)
  6. Escalated (número)
- [ ] Cada card tem ícone/emoji e número

**DOCUMENTAR:**
- Teste: "Test 5.1: Stats Display"
- Status: PASSED ✅ ou FAILED ❌

### Teste 5.2: Stats Atualizam Após Decisão

**PASSOS:**
1. ANTES de submeter decisão:
   - Anote número "Approved": ___
2. Submeta uma decisão APPROVE
3. **Aguarde 5 segundos**
4. Observe o número "Approved" novamente

**VERIFICAR:**
- [ ] Número aumentou em +1
- [ ] "Decisions Today" também aumentou

**DOCUMENTAR:**
- Teste: "Test 5.2: Stats Update After Decision"
- Status: PASSED ✅ ou FAILED ❌

---

## 📝 APÓS COMPLETAR OS TESTES

1. Abra o arquivo: `/tmp/manual_ui_test_results.md`
2. Conte quantos testes passaram vs falharam
3. Atualize a seção "Summary"
4. Se houver falhas, documente na seção "Issues Found"

---

## ⏭️ PRÓXIMOS PASSOS

Após completar os testes manuais, continuaremos com:

**FASE 3.9: WebSocket Real-Time Updates**
- Implementação backend (WebSocket endpoint)
- Implementação frontend (WebSocket hook)
- Testes de broadcast
- Testes de reconexão

**FASE 3.10: Production Deployment**
- PostgreSQL setup
- RabbitMQ configuration
- Docker containerization
- Kubernetes deployment
- Monitoring (Prometheus + Grafana)

---

**FIM DAS INSTRUÇÕES DE TESTE MANUAL**
