# 🧹 INSTRUÇÕES DE LIMPEZA E ORGANIZAÇÃO DO PROJETO VÉRTICE
## Documento Anti-Burro para Gemini CLI

**Data:** 2025-10-03
**Executor:** Gemini CLI
**Objetivo:** Limpar, organizar e estruturar o projeto Vértice mantendo integridade dos serviços ativos

---

## ⚠️ ZONAS PROIBIDAS - NÃO TOCAR EM HIPÓTESE ALGUMA

### 1. **vertice-terminal/**
- **MOTIVO:** Projeto paralelo independente, recém refatorado e validado
- **AÇÃO:** IGNORAR COMPLETAMENTE

### 2. **Serviços MAXIMUS AI (MASSIVE UPGRADE EM ANDAMENTO)**
- **MOTIVO:** Sistema MAXIMUS AI em desenvolvimento e upgrade ativo
- **SERVIÇOS PROIBIDOS DE TOCAR:**
  - `maximus_core_service/` - Core do MAXIMUS
  - `maximus_integration_service/` - Integração
  - `maximus_orchestrator_service/` - Orquestrador
  - `maximus_oraculo/` - Oráculo (auto-melhoria)
  - `maximus_eureka/` - Eureka (análise de código)
  - `maximus_predict/` - Predição
  - `rte_service/` - Runtime Environment (relacionado ao MAXIMUS)
- **AÇÃO:** NÃO MODIFICAR, NÃO MOVER, NÃO TOCAR

### 3. **backend/services/hcl_*_service/**
- **MOTIVO:** Serviços HCL (Hierarchical Cognitive Layer) do MAXIMUS AI em desenvolvimento
- **SERVIÇOS:**
  - `hcl_analyzer_service/` - Analisador HCL
  - `hcl_executor_service/` - Executor HCL
  - `hcl_kb_service/` - Knowledge Base HCL
  - `hcl_monitor_service/` - Monitor HCL
  - `hcl_planner_service/` - Planejador HCL
- **AÇÃO:** NÃO TOCAR

### 4. **Arquivos de Configuração de Produção**
- `.env`
- `.env.example`
- `docker-compose.yml` (em backend/services)
- `Makefile` (em backend/services)
- **AÇÃO:** NÃO MODIFICAR

### 5. **Diretórios do Sistema**
- `.git/`
- `.venv/`
- `__pycache__/`
- `node_modules/`
- `.pytest_cache/`
- `.mypy_cache/`
- `.ruff_cache/`
- **AÇÃO:** NÃO TOCAR

---

## 📋 FASE 1: CRIAR ESTRUTURA DE DESTINO

### 1.1 Criar Diretório LEGADO
```bash
mkdir -p /home/juan/vertice-dev/LEGADO
mkdir -p /home/juan/vertice-dev/LEGADO/documentacao_antiga
mkdir -p /home/juan/vertice-dev/LEGADO/codigo_deprecated
mkdir -p /home/juan/vertice-dev/LEGADO/analises_temporarias
mkdir -p /home/juan/vertice-dev/LEGADO/scripts_antigos
```

### 1.2 Criar Estrutura de Documentação Organizada
```bash
mkdir -p /home/juan/vertice-dev/docs/00-VISAO-GERAL
mkdir -p /home/juan/vertice-dev/docs/01-ARQUITETURA
mkdir -p /home/juan/vertice-dev/docs/02-MAXIMUS-AI
mkdir -p /home/juan/vertice-dev/docs/03-BACKEND
mkdir -p /home/juan/vertice-dev/docs/04-FRONTEND
mkdir -p /home/juan/vertice-dev/docs/05-TESTES
mkdir -p /home/juan/vertice-dev/docs/06-DEPLOYMENT
mkdir -p /home/juan/vertice-dev/docs/07-RELATORIOS
mkdir -p /home/juan/vertice-dev/docs/08-ROADMAPS
```

---

## 📦 FASE 2: MAPEAMENTO E CLASSIFICAÇÃO DE ARQUIVOS MD

### 2.1 DOCUMENTOS PARA ORGANIZAR (NÃO DELETAR)

#### **00-VISAO-GERAL/**
- `README.md` → Manter na raiz + criar cópia em docs/00-VISAO-GERAL/
- `PROJECT_STATE.md` → Mover para docs/00-VISAO-GERAL/

#### **01-ARQUITETURA/**
- `AI_FIRST_ARCHITECTURE.md` → Mover para docs/01-ARQUITETURA/
- `VERTICE_CLI_TERMINAL_BLUEPRINT.md` → Mover para docs/01-ARQUITETURA/

#### **02-MAXIMUS-AI/**
- `MAXIMUS_AI_ROADMAP_2025_REFACTORED.md` → Mover para docs/02-MAXIMUS-AI/ (VERSÃO ATUAL)
- `MAXIMUS_AI_ROADMAP_2025.md` → Mover para LEGADO/documentacao_antiga/ (VERSÃO ANTIGA)
- `MAXIMUS_AI_2.0_IMPLEMENTATION_COMPLETE.md` → Mover para docs/02-MAXIMUS-AI/
- `MAXIMUS_INTEGRATION_COMPLETE.md` → Mover para docs/02-MAXIMUS-AI/
- `MAXIMUS_INTEGRATION_GUIDE.md` → Mover para docs/02-MAXIMUS-AI/
- `MAXIMUS_DASHBOARD_STATUS.md` → Mover para docs/02-MAXIMUS-AI/
- `MAXIMUS_FRONTEND_IMPLEMENTATION.md` → Mover para docs/02-MAXIMUS-AI/
- `ORACULO_EUREKA_INTEGRATION_VISION.md` → Mover para docs/02-MAXIMUS-AI/
- `REASONING_ENGINE_INTEGRATION.md` → Mover para docs/02-MAXIMUS-AI/
- `MEMORY_SYSTEM_IMPLEMENTATION.md` → Mover para docs/02-MAXIMUS-AI/

#### **03-BACKEND/**
- `BACKEND_VALIDATION_REPORT.md` → Mover para docs/03-BACKEND/
- `REAL_SERVICES_INTEGRATION_REPORT.md` → Mover para docs/03-BACKEND/
- `ANALISE_SINESP_SERVICE.md` → Mover para docs/03-BACKEND/

#### **04-FRONTEND/**
- `FRONTEND_TEST_REPORT.md` → Mover para docs/04-FRONTEND/
- `WORLD_CLASS_TOOLS_FRONTEND_INTEGRATION.md` → Mover para docs/04-FRONTEND/

#### **05-TESTES/**
- `FINAL_TESTING_REPORT.md` → Mover para docs/05-TESTES/
- `GUIA_DE_TESTES.md` → Mover para docs/05-TESTES/
- `TESTE_FERRAMENTAS_COMPLETO.md` → Mover para docs/05-TESTES/
- `TEST_MAXIMUS_LOCALLY.md` → Mover para docs/05-TESTES/
- `VALIDATION_REPORT.md` → Mover para docs/05-TESTES/
- `VALIDACAO_COMPLETA.md` → Mover para docs/05-TESTES/
- `CLI_VALIDATION.md` → Mover para docs/05-TESTES/

#### **06-DEPLOYMENT/**
- `DOCKER_COMPOSE_FIXES.md` → Mover para docs/06-DEPLOYMENT/
- `DEBUG_GUIDE.md` → Mover para docs/06-DEPLOYMENT/
- `AURORA_DEPLOYMENT.md` → Mover para docs/06-DEPLOYMENT/

#### **07-RELATORIOS/**
- `EXECUTIVE_SUMMARY.md` → Mover para docs/07-RELATORIOS/
- `EPIC_COMPLETED.md` → Mover para docs/07-RELATORIOS/
- `BUG_FIX_REPORT.md` → Mover para docs/07-RELATORIOS/
- `ADR_INTEGRATION_COMPLETE.md` → Mover para docs/07-RELATORIOS/
- `FASE_1_ADR_CORE_IMPLEMENTADO.md` → Mover para docs/07-RELATORIOS/
- `FASE_3_TOOL_EXPANSION.md` → Mover para docs/07-RELATORIOS/

#### **08-ROADMAPS/**
- `RoadMap.md` → Mover para docs/08-ROADMAPS/
- `AURORA_2025_STRATEGIC_ROADMAP.md` → Mover para docs/08-ROADMAPS/
- `VERTICE_UPGRADE_PLAN.md` → Mover para docs/08-ROADMAPS/

### 2.2 DOCUMENTOS PARA LEGADO (VERSÕES ANTIGAS/DUPLICADAS)

#### **LEGADO/documentacao_antiga/**
- `AURORA_2.0_BLUEPRINT_COMPLETE.md` → Versão consolidada antiga
- `AURORA_2.0_MANIFESTO.md` → Documento visionário antigo
- `AURORA_MASTERPIECE_PLAN.md` → Plano superado

---

## 🗑️ FASE 3: IDENTIFICAR ARQUIVOS TEMPORÁRIOS E CÓDIGO LEGADO

### 3.1 Scripts Python Temporários para LEGADO
```bash
# Verificar e mover se existirem:
- auto_analyzer.py → LEGADO/scripts_antigos/
- oraculo_ideias_*.md → LEGADO/documentacao_antiga/
```

### 3.2 Diretórios de Análise Temporária para LEGADO
```bash
# Mover INTEIROS se existirem:
- backend_analysis/ → LEGADO/analises_temporarias/
- frontend_performance_analysis/ → LEGADO/analises_temporarias/
- frontend_security_analysis/ → LEGADO/analises_temporarias/
- docker_security_analysis/ → LEGADO/analises_temporarias/
```

### 3.3 Código Frontend/Backend Antigo
```bash
# Verificar diretórios:
- vertice_cli/ → Se diferente de vertice-terminal, mover para LEGADO/codigo_deprecated/
- frontend/ → Se antigo (sem package.json recente ou README), investigar antes de mover
```

### 3.4 Scripts Temporários no Root
```bash
# Scripts identificados no root para LEGADO:
- auto_analyzer.py → LEGADO/scripts_antigos/
- setup_cli.sh → Verificar se ainda usado; se não, LEGADO/scripts_antigos/
- validate_maximus.sh → Verificar se ainda usado; se não, LEGADO/scripts_antigos/
- setup_vertice_cli.sh → Verificar se ainda usado; se não, LEGADO/scripts_antigos/
```

---

## 📝 FASE 4: CONSOLIDAÇÃO DE DOCUMENTOS

### 4.1 Criar Índice Master
Criar arquivo: `/home/juan/vertice-dev/docs/INDEX.md`

Conteúdo:
```markdown
# 📚 Índice de Documentação - Projeto Vértice

**Última Atualização:** 2025-10-03

---

## 📂 Estrutura de Documentação

### 00-VISAO-GERAL/
- **PROJECT_STATE.md** - Estado atual do projeto
- **README.md** - Visão geral (cópia do root)

### 01-ARQUITETURA/
- **AI_FIRST_ARCHITECTURE.md** - Arquitetura AI-First
- **VERTICE_CLI_TERMINAL_BLUEPRINT.md** - Blueprint do CLI Terminal

### 02-MAXIMUS-AI/
- **MAXIMUS_AI_ROADMAP_2025_REFACTORED.md** - Roadmap Atual (2025)
- **MAXIMUS_AI_2.0_IMPLEMENTATION_COMPLETE.md** - Implementação v2.0
- **MAXIMUS_INTEGRATION_COMPLETE.md** - Integração completa
- **MAXIMUS_INTEGRATION_GUIDE.md** - Guia de integração
- **MAXIMUS_DASHBOARD_STATUS.md** - Status do dashboard
- **MAXIMUS_FRONTEND_IMPLEMENTATION.md** - Implementação frontend
- **ORACULO_EUREKA_INTEGRATION_VISION.md** - Visão Oráculo/Eureka
- **REASONING_ENGINE_INTEGRATION.md** - Motor de raciocínio
- **MEMORY_SYSTEM_IMPLEMENTATION.md** - Sistema de memória

### 03-BACKEND/
- **BACKEND_VALIDATION_REPORT.md** - Relatório de validação
- **REAL_SERVICES_INTEGRATION_REPORT.md** - Integração de serviços reais
- **ANALISE_SINESP_SERVICE.md** - Análise serviço SINESP

### 04-FRONTEND/
- **FRONTEND_TEST_REPORT.md** - Relatório de testes
- **WORLD_CLASS_TOOLS_FRONTEND_INTEGRATION.md** - Integração ferramentas

### 05-TESTES/
- **FINAL_TESTING_REPORT.md** - Relatório final de testes
- **GUIA_DE_TESTES.md** - Guia de testes
- **TESTE_FERRAMENTAS_COMPLETO.md** - Teste completo de ferramentas
- **TEST_MAXIMUS_LOCALLY.md** - Teste local do MAXIMUS
- **VALIDATION_REPORT.md** - Relatório de validação
- **VALIDACAO_COMPLETA.md** - Validação completa
- **CLI_VALIDATION.md** - Validação CLI

### 06-DEPLOYMENT/
- **DOCKER_COMPOSE_FIXES.md** - Correções Docker Compose
- **DEBUG_GUIDE.md** - Guia de debug
- **AURORA_DEPLOYMENT.md** - Deploy Aurora

### 07-RELATORIOS/
- **EXECUTIVE_SUMMARY.md** - Sumário executivo
- **EPIC_COMPLETED.md** - Épicos concluídos
- **BUG_FIX_REPORT.md** - Relatório de correções
- **ADR_INTEGRATION_COMPLETE.md** - Integração ADR completa
- **FASE_1_ADR_CORE_IMPLEMENTADO.md** - Fase 1 ADR
- **FASE_3_TOOL_EXPANSION.md** - Fase 3 expansão

### 08-ROADMAPS/
- **RoadMap.md** - Roadmap geral
- **AURORA_2025_STRATEGIC_ROADMAP.md** - Roadmap estratégico Aurora
- **VERTICE_UPGRADE_PLAN.md** - Plano de upgrade

---

## 🗂️ LEGADO/
Documentos e código antigos arquivados (não mais em uso ativo)
```

### 4.2 Criar README do LEGADO
Criar arquivo: `/home/juan/vertice-dev/LEGADO/README.md`

Conteúdo:
```markdown
# 📦 LEGADO - Arquivos Históricos do Projeto Vértice

**Data de Arquivamento:** 2025-10-03

Este diretório contém código, documentos e análises antigas que não são mais utilizadas
no desenvolvimento ativo do projeto, mas são mantidas para referência histórica.

## 📂 Estrutura

### documentacao_antiga/
Documentos de planejamento e visão superados por versões mais recentes.

### codigo_deprecated/
Código-fonte antigo que foi substituído ou refatorado.

### analises_temporarias/
Análises de segurança, performance e qualidade realizadas durante o desenvolvimento.

### scripts_antigos/
Scripts utilitários que não são mais necessários.

---

⚠️ **IMPORTANTE:** Este conteúdo é mantido apenas para referência.
Para documentação atual, consulte `/docs/`
```

---

## ✅ FASE 5: EXECUÇÃO DAS MOVIMENTAÇÕES

### 5.1 Checklist de Segurança ANTES de Mover

**VERIFICAR:**
- [ ] Arquivo NÃO está em vertice-terminal/
- [ ] Arquivo NÃO está em backend/services/maximus_ai_service/
- [ ] Arquivo NÃO está em backend/services/hcl_*_service/
- [ ] Arquivo NÃO é .env, docker-compose.yml ou Makefile de produção
- [ ] Diretório NÃO é .git, .venv, node_modules, __pycache__

### 5.2 Comandos de Movimentação Seguros

```bash
# SEMPRE usar mv (mover) ao invés de cp (copiar) para evitar duplicação
# SEMPRE verificar se o caminho de destino existe antes

# Exemplo de movimentação segura:
if [ -f "/home/juan/vertice-dev/AURORA_MASTERPIECE_PLAN.md" ]; then
    mv "/home/juan/vertice-dev/AURORA_MASTERPIECE_PLAN.md" \
       "/home/juan/vertice-dev/LEGADO/documentacao_antiga/"
fi
```

### 5.3 Ordem de Execução

1. **CRIAR** toda estrutura de diretórios
2. **MOVER** documentação para docs/ (categorizado)
3. **MOVER** arquivos antigos para LEGADO/
4. **CRIAR** INDEX.md e READMEs
5. **VERIFICAR** que nada quebrou
6. **REPORTAR** resumo das movimentações

---

## 📊 FASE 6: VALIDAÇÃO PÓS-LIMPEZA

### 6.1 Verificações Obrigatórias

```bash
# 1. Verificar que vertice-terminal não foi tocado
ls -la /home/juan/vertice-dev/vertice-terminal/ | head -5

# 2. Verificar que serviços MAXIMUS/HCL/RTE estão intactos
ls -la /home/juan/vertice-dev/backend/services/ | grep -E "(maximus|hcl_|rte_)"

# 2.1 Contar serviços MAXIMUS (deve ser 7)
ls -d /home/juan/vertice-dev/backend/services/maximus* 2>/dev/null | wc -l

# 2.2 Contar serviços HCL (deve ser 5)
ls -d /home/juan/vertice-dev/backend/services/hcl_* 2>/dev/null | wc -l

# 3. Verificar estrutura docs/
ls -R /home/juan/vertice-dev/docs/

# 4. Verificar LEGADO/
ls -R /home/juan/vertice-dev/LEGADO/

# 5. Contar arquivos MD no root (deve estar limpo)
find /home/juan/vertice-dev -maxdepth 1 -name "*.md" | wc -l
```

### 6.2 Resultado Esperado no Root

Após limpeza, o diretório `/home/juan/vertice-dev/` deve conter:

**ARQUIVOS:**
- `README.md` (único MD permitido no root)

**DIRETÓRIOS:**
- `backend/` - Serviços backend (intocado)
- `vertice/` - Código frontend (se atual)
- `vertice-terminal/` - Projeto CLI (INTOCADO)
- `docs/` - Documentação organizada (NOVO)
- `LEGADO/` - Arquivos antigos (NOVO)
- `data/` - Dados (intocado)
- `scripts/` - Scripts ativos (intocado)
- `.git/`, `.venv/`, etc. - Sistema (intocado)

---

## 📋 FASE 7: RELATÓRIO FINAL

### 7.1 Gerar Relatório de Limpeza

Criar arquivo: `/home/juan/vertice-dev/LIMPEZA_RELATORIO_2025-10-03.md`

Incluir:
1. **Total de arquivos movidos**
2. **Lista de arquivos enviados para LEGADO**
3. **Lista de arquivos organizados em docs/**
4. **Estrutura final de diretórios**
5. **Verificações de integridade realizadas**
6. **Alertas ou problemas encontrados**

---

## 🎯 CRITÉRIOS DE SUCESSO

- [ ] Todos os MDs organizados em `/docs/` categorizado
- [ ] Root limpo (apenas README.md)
- [ ] LEGADO criado e populado
- [ ] vertice-terminal/ INTOCADO
- [ ] backend/services/maximus_ai_service/ INTOCADO
- [ ] backend/services/hcl_*/ INTOCADO
- [ ] INDEX.md criado e completo
- [ ] Relatório de limpeza gerado
- [ ] Nenhum arquivo perdido ou deletado
- [ ] Projeto ainda funcional

---

## 🚨 EM CASO DE ERRO

**SE ALGO DER ERRADO:**
1. **PARAR IMEDIATAMENTE**
2. **NÃO DELETAR NADA**
3. **REPORTAR o erro detalhado**
4. **AGUARDAR instruções**

---

## 📞 OBSERVAÇÕES FINAIS

- **NUNCA deletar arquivos**, apenas MOVER
- **SEMPRE preservar** .git, .env, configurações
- **SEMPRE verificar** antes de mover
- **SEMPRE documentar** o que foi feito
- Este é um projeto de **SEGURANÇA CIBERNÉTICA CRÍTICO**
- **Cautela é OBRIGATÓRIA**

---

**Executor:** Gemini CLI
**Supervisão:** Claude Code
**Aprovação Final:** Juan (Owner)

---

**BOA SORTE! 🧹✨**
