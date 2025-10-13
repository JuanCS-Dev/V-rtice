# 🚀 HITL Console - Quick Start Guide

## 📋 Pré-requisitos

### Backend
- Python 3.11+
- PostgreSQL 14+
- RabbitMQ
- GitHub Personal Access Token (com permissões de PR)

### Frontend
- Node.js 22+
- npm 10+

---

## ⚡ Start Rápido

### 1️⃣ Configuração Inicial (Primeira Vez)

#### Backend Environment Variables
```bash
cd /home/juan/vertice-dev/backend/services/adaptive_immune_system

# Criar .env (se não existir)
cat > .env << EOF
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/adaptive_immune
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
GITHUB_TOKEN=ghp_your_token_here
GITHUB_REPO_OWNER=your-org
GITHUB_REPO_NAME=your-repo
EOF
```

#### Frontend Environment Variables
```bash
cd /home/juan/vertice-dev/frontend

# Já configurado! Apenas verifique:
grep VITE_HITL_API_URL .env
# Deve retornar: VITE_HITL_API_URL=http://localhost:8003
```

### 2️⃣ Iniciar Backend

```bash
cd /home/juan/vertice-dev/backend/services/adaptive_immune_system

# Instalar dependências (se necessário)
pip install -r requirements.txt

# Iniciar API
uvicorn hitl.api.main:app --reload --port 8003
```

**Verificar**: Acesse http://localhost:8003/hitl/docs

### 3️⃣ Iniciar Frontend

```bash
cd /home/juan/vertice-dev/frontend

# Instalar dependências (se necessário)
npm install

# Iniciar dev server
npm run dev
```

**Verificar**: Acesse http://localhost:5173

### 4️⃣ Acessar HITL Console

1. Abra o navegador em http://localhost:5173
2. Navegue até **Admin Dashboard**
3. Clique na tab **HITL** (novo ícone 🛡️)

---

## 🎯 Fluxo de Uso

### 1. Visualizar APVs Pendentes

Na **coluna esquerda** (Review Queue):
- Lista de APVs aguardando revisão humana
- Badges de severidade: 🔴 Critical | 🟠 High | 🟡 Medium | 🟢 Low
- Filtros por severidade e wargame verdict
- Tempo de espera

**Clique em um APV** para ver detalhes.

### 2. Analisar Detalhes

Na **coluna central** (Review Details), explore as tabs:

#### 📊 Tab CVE
- CVE ID e descrição
- CVSS score e vector
- Dependency info (package, version)
- Vulnerability info (versões afetadas/fixadas)

#### 🔧 Tab Patch
- Estratégia de patch (version_bump, code_rewrite, etc.)
- Arquivos modificados
- Diff completo (syntax highlighted)
- Confirmation scores (static, dynamic, aggregation)

#### ⚔️ Tab Wargame
- Veredito: PATCH_EFFECTIVE | INCONCLUSIVE | PATCH_INSUFFICIENT
- Confidence score (0-100%)
- Evidence:
  - Exit codes (before/after)
  - Exploit resultado (before/after)
  - Workflow duration

#### ✅ Tab Validation
- 5 checks:
  - Syntax validation
  - Static analysis
  - Tests
  - Dependencies
  - Build
- Status: PASSED | FAILED | SKIPPED
- Warnings/errors

### 3. Tomar Decisão

Na **coluna direita** (Decision Panel), escolha uma ação:

#### ✅ APPROVE (Verde)
- **Ação**: Merge PR (squash merge)
- **Quando usar**: Patch está correto e completo
- **Preencha**:
  - Justification: Razão da aprovação (min 10 chars)
  - Confidence: Nível de confiança (0-100%)

#### ❌ REJECT (Vermelho)
- **Ação**: Close PR com comentário
- **Quando usar**: Patch incorreto ou insuficiente
- **Preencha**:
  - Justification: Razão da rejeição (detalhada)
  - Confidence: Nível de confiança

#### 🔧 MODIFY (Azul)
- **Ação**: Request changes no PR
- **Quando usar**: Patch precisa de ajustes
- **Preencha**:
  - Justification: Modificações necessárias (detalhadas)
  - Confidence: Nível de confiança

#### ⬆️ ESCALATE (Laranja)
- **Ação**: Assign para security lead
- **Quando usar**: Decisão requer expertise adicional
- **Preencha**:
  - Justification: Razão do escalation
  - Confidence: N/A

### 4. Submeter Decisão

1. Preencha a justificação (min 10 caracteres)
2. Ajuste o slider de confiança
3. Clique no botão da ação desejada
4. Aguarde confirmação (spinner)
5. ✅ Decisão registrada! Lista será atualizada automaticamente

### 5. Monitorar Estatísticas

No **bottom bar** (HITL Stats):
- **Pending Reviews**: Total aguardando revisão
- **Total Decisions**: Total de decisões tomadas
- **Today's Decisions**: Decisões de hoje
- **This Week's Decisions**: Decisões da semana
- **Avg Review Time**: Tempo médio de revisão
- **Agreement Rate**: Taxa de concordância com IA

**Decision Breakdown**:
- Approve: X%
- Reject: X%
- Modify: X%
- Escalate: X%

---

## 🔍 Filtros e Busca

### Filtros Disponíveis

#### Por Severidade
```
All Severities (padrão)
Critical (🔴)
High (🟠)
Medium (🟡)
Low (🟢)
```

#### Por Wargame Verdict
```
All Verdicts (padrão)
Patch Effective (✅)
Inconclusive (⚠️)
Patch Insufficient (❌)
```

### Combinando Filtros

Exemplo: Ver apenas APVs **Critical** com patch **Inconclusive**:
1. Selecione "Critical" no primeiro dropdown
2. Selecione "Inconclusive" no segundo dropdown
3. Lista será filtrada automaticamente

---

## 📊 Interpretando Scores

### Confirmation Scores

#### Static Score (0.0 - 1.0)
- **0.8+**: Alta confiança (análise estática forte)
- **0.5-0.8**: Média confiança
- **<0.5**: Baixa confiança (revisar manualmente)

#### Dynamic Score (0.0 - 1.0)
- **0.8+**: Alta confiança (análise dinâmica forte)
- **0.5-0.8**: Média confiança
- **<0.5**: Baixa confiança (revisar manualmente)

#### Aggregation Score (0.0 - 1.0)
- **Fórmula**: `(static + dynamic + wargame_confidence) / 3`
- **0.8+**: APV altamente confiável
- **0.5-0.8**: APV moderadamente confiável
- **<0.5**: APV requer revisão cuidadosa

### Wargame Confidence (0-100%)

#### Fatores (pesos):
1. **Exit code match** (30%): Before=0, After!=0
2. **Workflow completion** (20%): Workflow completou sem erros
3. **Key steps** (20%): Todos os steps-chave executaram
4. **Execution time** (15%): Dentro de limites razoáveis
5. **Verdict consistency** (15%): Veredito consistente

#### Interpretação:
- **70%+**: Alta confiança → Patch efetivo
- **50-70%**: Média confiança → Revisar evidências
- **<50%**: Baixa confiança → Patch pode estar incorreto

---

## 🛠️ Troubleshooting

### Backend não inicia

**Erro**: `ModuleNotFoundError: No module named 'hitl'`
```bash
# Solução: Instalar dependências
cd /home/juan/vertice-dev/backend/services/adaptive_immune_system
pip install -r requirements.txt
```

**Erro**: `Connection refused (PostgreSQL)`
```bash
# Solução: Iniciar PostgreSQL
sudo systemctl start postgresql
```

**Erro**: `Connection refused (RabbitMQ)`
```bash
# Solução: Iniciar RabbitMQ
sudo systemctl start rabbitmq-server
```

### Frontend não carrega HITL tab

**Problema**: Tab "HITL" não aparece
```bash
# Solução: Verificar se .env está correto
cd /home/juan/vertice-dev/frontend
cat .env | grep HITL
# Deve retornar: VITE_HITL_API_URL=http://localhost:8003

# Reiniciar dev server
npm run dev
```

**Problema**: API não responde (CORS error)
```bash
# Solução: Verificar se backend está rodando
curl http://localhost:8003/hitl/health
# Deve retornar: {"status":"healthy","timestamp":"..."}
```

### APVs não aparecem na lista

**Problema**: Lista vazia
```bash
# Verificar se há APVs pendentes no banco
# (executar no backend)
python3 -c "
from hitl.api.endpoints.apv_review import get_pending_reviews
print(get_pending_reviews())
"
```

**Problema**: Loading infinito
```bash
# Verificar se backend está acessível
curl http://localhost:8003/hitl/reviews
# Deve retornar JSON com lista de reviews
```

---

## 🎨 Atalhos de Teclado

### Navegação
- `Tab` / `Shift+Tab`: Navegar entre elementos
- `Enter` / `Space`: Selecionar APV
- `Esc`: Fechar modals/panels

### Tabs (Review Details)
- `1`: Tab CVE
- `2`: Tab Patch
- `3`: Tab Wargame
- `4`: Tab Validation

### Ações (Decision Panel)
- `A`: Approve
- `R`: Reject
- `M`: Modify
- `E`: Escalate

*(Nota: Atalhos de ação estão preparados, mas requerem implementação de event listeners)*

---

## 📝 Logs e Debug

### Backend Logs
```bash
# Ver logs em tempo real
cd /home/juan/vertice-dev/backend/services/adaptive_immune_system
tail -f logs/hitl.log
```

### Frontend Logs
```bash
# Abrir console do navegador
# Chrome/Firefox: F12 → Console

# Ver requisições
# Chrome/Firefox: F12 → Network → Filtrar por "hitl"
```

### API Documentation
```
Backend Docs: http://localhost:8003/hitl/docs
Health Check: http://localhost:8003/hitl/health
Metrics: http://localhost:8003/hitl/metrics
```

---

## 📚 Recursos Adicionais

### Documentação Completa
- `FASE_3_INTEGRATION_COMPLETE.md` - Implementação completa
- `HITL_FRONTEND_IMPLEMENTATION_SUMMARY.md` - Frontend details
- `HITL_FRONTEND_DESIGN.md` - Design system

### Código Fonte
- Backend: `/backend/services/adaptive_immune_system/hitl/`
- Frontend: `/frontend/src/components/admin/HITLConsole/`

### API Examples
```bash
# Listar APVs pendentes
curl http://localhost:8003/hitl/reviews

# Ver detalhes de um APV
curl http://localhost:8003/hitl/reviews/APV-2024-001

# Ver estatísticas
curl http://localhost:8003/hitl/reviews/stats

# Submeter decisão
curl -X POST http://localhost:8003/hitl/decisions \
  -H "Content-Type: application/json" \
  -d '{
    "apv_id": "APV-2024-001",
    "decision": "approve",
    "justification": "Patch is correct and complete. All validations passed.",
    "confidence": 0.95,
    "reviewer_name": "John Doe",
    "reviewer_email": "john@example.com"
  }'
```

---

## 🎯 Próximos Passos

Após dominar o básico:
1. Explore os filtros avançados
2. Analise padrões de decisão nas estatísticas
3. Configure alertas (próxima fase)
4. Integre com Prometheus/Grafana (próxima fase)

---

**Versão**: 1.0.0
**Última Atualização**: 2025-10-13
**Suporte**: Adaptive Immune System Team
