# 👋 BEM-VINDO, GEMINI!

**Data:** 2025-10-03
**Tarefa:** Limpeza e Organização do Projeto Vértice
**Documento Principal:** `GEMINI_LIMPEZA_PROJETO.md`

---

## 🎯 SUA MISSÃO

Você foi convocado para realizar uma **limpeza completa e organização** do projeto Vértice, um sistema crítico de segurança cibernética. Sua tarefa é:

1. **Organizar** toda a documentação em estrutura categorizada
2. **Arquivar** documentos e código antigos em LEGADO/
3. **Limpar** o diretório root de arquivos dispersos
4. **Preservar** a integridade dos serviços ativos (MAXIMUS AI, HCL, etc.)

---

## 📚 DOCUMENTOS DISPONÍVEIS

### 📖 Instruções Completas
**`GEMINI_LIMPEZA_PROJETO.md`** - Documento detalhado com todas as instruções

**Contém:**
- ⚠️ Zonas proibidas (NÃO TOCAR)
- 📋 Fases de execução (1-7)
- 📂 Mapeamento de arquivos
- ✅ Checklist de validação
- 🎯 Critérios de sucesso

### 🛠️ Script Automatizado
**`gemini_limpeza_executor.sh`** - Script bash pronto para executar

**Recursos:**
- ✅ Verificações de segurança automáticas
- 🚫 Bloqueio de arquivos protegidos
- 📊 Contadores de operações
- 🎨 Output colorido e informativo

---

## 🚀 COMO EXECUTAR

### Opção 1: Execução Automática (RECOMENDADO)

```bash
cd /home/juan/vertice-dev
./gemini_limpeza_executor.sh
```

O script irá:
- Criar toda estrutura de diretórios
- Mover arquivos para os locais corretos
- Validar integridade
- Gerar relatório

### Opção 2: Execução Manual (Passo a Passo)

Siga as instruções em `GEMINI_LIMPEZA_PROJETO.md` fase por fase:
1. Criar estrutura (Fase 1)
2. Mover documentação (Fase 2)
3. Arquivar legado (Fase 3)
4. Consolidar (Fase 4)
5. Validar (Fase 6)
6. Reportar (Fase 7)

---

## ⚠️ REGRAS CRÍTICAS - LEIA COM ATENÇÃO

### 🚫 NUNCA TOQUE EM:

1. **`vertice-terminal/`** - Projeto paralelo validado
2. **Serviços MAXIMUS AI:**
   - `maximus_core_service/`
   - `maximus_integration_service/`
   - `maximus_orchestrator_service/`
   - `maximus_oraculo/`
   - `maximus_eureka/`
   - `maximus_predict/`
   - `rte_service/`

3. **Serviços HCL:**
   - `hcl_analyzer_service/`
   - `hcl_executor_service/`
   - `hcl_kb_service/`
   - `hcl_monitor_service/`
   - `hcl_planner_service/`

4. **Arquivos de Configuração:**
   - `.env`
   - `docker-compose.yml` (em backend/services)
   - `Makefile` (em backend/services)

5. **Diretórios do Sistema:**
   - `.git/`, `.venv/`, `node_modules/`, etc.

### ✅ PODE FAZER:

- ✅ Mover arquivos `.md` do root para `docs/`
- ✅ Arquivar documentos antigos em `LEGADO/`
- ✅ Criar estrutura de diretórios
- ✅ Mover análises temporárias
- ✅ Organizar scripts antigos

### 🚨 NUNCA FAÇA:

- ❌ **DELETAR** arquivos (apenas MOVER)
- ❌ Modificar código de serviços ativos
- ❌ Tocar em arquivos de configuração
- ❌ Mexer em diretórios do sistema

---

## 📊 RESULTADO ESPERADO

### Antes da Limpeza:
```
/home/juan/vertice-dev/
├── 40+ arquivos .md no root (BAGUNÇA)
├── Scripts dispersos (.py, .sh)
├── Análises temporárias
└── Código duplicado
```

### Depois da Limpeza:
```
/home/juan/vertice-dev/
├── README.md (único MD no root)
├── docs/ (documentação organizada)
│   ├── 00-VISAO-GERAL/
│   ├── 01-ARQUITETURA/
│   ├── 02-MAXIMUS-AI/
│   ├── 03-BACKEND/
│   ├── 04-FRONTEND/
│   ├── 05-TESTES/
│   ├── 06-DEPLOYMENT/
│   ├── 07-RELATORIOS/
│   └── 08-ROADMAPS/
├── LEGADO/ (arquivos antigos)
│   ├── documentacao_antiga/
│   ├── codigo_deprecated/
│   ├── analises_temporarias/
│   └── scripts_antigos/
├── backend/ (intacto)
├── vertice-terminal/ (intacto)
└── [outros diretórios de código] (intactos)
```

---

## 🎯 CHECKLIST DE EXECUÇÃO

### Antes de Começar:
- [ ] Li completamente o `GEMINI_LIMPEZA_PROJETO.md`
- [ ] Entendi as zonas proibidas
- [ ] Verifiquei que o script está executável
- [ ] Estou no diretório correto (`/home/juan/vertice-dev`)

### Durante a Execução:
- [ ] Estou executando apenas operações MOVE (não DELETE)
- [ ] Estou verificando cada arquivo antes de mover
- [ ] Estou respeitando as zonas proibidas
- [ ] Estou logando todas as operações

### Após Execução:
- [ ] Validei que vertice-terminal/ está intacto
- [ ] Validei que serviços MAXIMUS/HCL estão intactos
- [ ] Contei arquivos MD no root (deve ter apenas README.md)
- [ ] Verifiquei estrutura docs/
- [ ] Verifiquei estrutura LEGADO/
- [ ] Gerei relatório de limpeza

---

## 🆘 EM CASO DE PROBLEMAS

### Se algo der errado:

1. **PARE IMEDIATAMENTE**
2. **NÃO DELETE NADA**
3. **Documente o erro:**
   - Comando executado
   - Mensagem de erro
   - Arquivos afetados
4. **Reporte ao supervisor (Claude/Juan)**
5. **Aguarde instruções**

### Contatos de Emergência:
- **Supervisor Técnico:** Claude Code (outra sessão)
- **Owner:** Juan
- **Documento de Referência:** `GEMINI_LIMPEZA_PROJETO.md`

---

## 💡 DICAS IMPORTANTES

1. **Execute em etapas**: Não tente fazer tudo de uma vez
2. **Valide constantemente**: Verifique após cada fase
3. **Use o script**: Ele tem proteções automáticas
4. **Documente tudo**: Mantenha log do que foi feito
5. **Pergunte quando em dúvida**: Melhor perguntar do que quebrar

---

## 📈 PROGRESSO ESPERADO

- **Fase 1** (Estrutura): ~5 minutos
- **Fase 2** (Documentação): ~15 minutos
- **Fase 3** (Legado): ~10 minutos
- **Fase 4** (Consolidação): ~10 minutos
- **Fase 5** (Validação): ~5 minutos
- **Fase 6** (Relatório): ~5 minutos

**TOTAL ESTIMADO:** ~50 minutos

---

## 🎉 CRITÉRIOS DE SUCESSO

A tarefa será considerada **100% COMPLETA** quando:

- ✅ Todos os MDs organizados em `docs/`
- ✅ Root limpo (apenas README.md)
- ✅ LEGADO criado e populado
- ✅ vertice-terminal/ INTOCADO
- ✅ Serviços MAXIMUS/HCL INTOCADOS
- ✅ INDEX.md criado
- ✅ Relatório gerado
- ✅ Zero arquivos deletados
- ✅ Projeto 100% funcional

---

## 📞 MENSAGEM FINAL

Gemini, você foi escolhido para esta tarefa por sua precisão e atenção aos detalhes. Este projeto é **crítico** e **ativo em produção**. Cada arquivo tem sua importância.

**Lembre-se:**
- 🎯 Foco na organização, não na destruição
- 🔒 Segurança acima de tudo
- 📋 Siga o plano à risca
- ✅ Valide constantemente
- 🤝 Pergunte quando em dúvida

**Boa sorte! Você consegue! 🚀**

---

**Gerado por:** Claude Code
**Para:** Gemini CLI
**Projeto:** Vértice - Cybersecurity Platform
**Importância:** CRÍTICA ⚠️
