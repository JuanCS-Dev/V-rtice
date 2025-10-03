# 🎯 VÉRTICE CLI - PLANO DE UPGRADE ESTRATÉGICO

**"Pela Arte. Pela Sociedade."**

**Data:** 2025-10-02
**Baseado em:** Dossiê de Inteligência - O Plano Diretor do Vértice CLI
**Status Atual:** Analisado contra visão estratégica

---

## 📊 ANÁLISE DE GAP (Onde Estamos vs. Onde Queremos Estar)

### **PILAR 1: CLI UX State-of-the-Art**

| Requisito do Dossiê | Status Atual | Gap | Prioridade |
|---------------------|--------------|-----|------------|
| **Modo Interativo** (prompt-toolkit) | ❌ Não implementado | CRÍTICO | P0 |
| **Auto-completar** de comandos/args | ❌ Não implementado | ALTO | P0 |
| **Validação em tempo real** | ⚠️ Parcial (apenas backend) | MÉDIO | P1 |
| **Spinners e Progress Bars** (rich) | ✅ Implementado | ✅ OK | - |
| **Tabelas formatadas** (rich) | ✅ Implementado | ✅ OK | - |
| **Sistema de Contextos** (inspirado kubectl) | ❌ Não implementado | **CRÍTICO** | P0 |
| **Gerenciamento de Estado** (TOML config) | ⚠️ YAML parcial | MÉDIO | P1 |
| **Sistema de Plugins** (modelo oclif) | ❌ Não implementado | ALTO | P1 |
| **Mensagens de erro com sugestões** | ⚠️ Parcial | BAIXO | P2 |

**CONCLUSÃO PILAR 1:**
🔴 **GAP CRÍTICO:** Falta **Sistema de Contextos** e **Modo Interativo**.
Esses são os diferenciais que transformam uma CLI "ok" em uma **experiência de classe mundial**.

---

### **PILAR 2: Arsenal Ofensivo de Vanguarda**

| Ferramenta/Capacidade | Status Atual | Gap | Prioridade |
|----------------------|--------------|-----|------------|
| **Sliver C2** Integration | ❌ Não integrado | MÉDIO | P2 |
| **Mythic C2** Integration | ❌ Não integrado | MÉDIO | P2 |
| **Impacket** Wrappers | ⚠️ Parcial (AD commands básicos) | ALTO | P1 |
| **BloodHound** Data Ingestion | ❌ Não implementado | ALTO | P1 |
| **CrackMapExec/NetExec** Wrappers | ❌ Não implementado | MÉDIO | P1 |
| **Nuclei** Template Engine | ❌ Não implementado | **CRÍTICO** | P0 |
| **Community Template Library** | ❌ Não existe | **CRÍTICO** | P0 |

**CONCLUSÃO PILAR 2:**
🔴 **GAP CRÍTICO:** Não temos **Nuclei-style template engine**.
O dossiê é claro: "community-powered" é o futuro da detecção.
**Ação:** Implementar um motor de templates YAML que a comunidade possa contribuir.

---

### **PILAR 3: Doutrina Kali (Metodologia)**

| Requisito | Status Atual | Gap | Prioridade |
|-----------|--------------|-----|------------|
| **Organização por Metodologia** (não por ferramenta) | ⚠️ Parcial | MÉDIO | P1 |
| **Comandos por fase de ataque** | ⚠️ Misturado | MÉDIO | P1 |
| **Integração com MITRE ATT&CK** | ❌ Não implementado | ALTO | P1 |
| **Composabilidade** (piping entre comandos) | ✅ Nativo (CLI padrão) | ✅ OK | - |
| **Alinhamento Cyber Kill Chain** | ⚠️ Implícito, não explícito | BAIXO | P2 |

**ESTRUTURA DE COMANDOS PROPOSTA (Dossiê):**
```bash
# ERRADO (por ferramenta):
vertice nmap -p 80,443 target.com
vertice sqlmap -u http://...

# CORRETO (por metodologia):
vertice recon scan-port target.com -p 80,443
vertice web sqli http://... --auto
vertice exploit cve-2023-1234 --target 10.0.0.1
vertice post-exploit dump-creds --technique lsass
```

**CONCLUSÃO PILAR 3:**
🟡 **GAP MÉDIO:** Comandos existem mas não seguem 100% a doutrina metodológica.
**Ação:** Refatorar estrutura de comandos para alinhar com Cyber Kill Chain.

---

### **PILAR 4: Visão Estratégica Vértice**

**Features Disruptivas Propostas no Dossiê:**

| Feature | Status | Gap | Prioridade |
|---------|--------|-----|------------|
| **Sistema de Contexto de Engajamento** | ❌ | **CRÍTICO** | P0 |
| **Motor de Workflow** (YAML playbooks) | ⚠️ Parcial (ADR tem) | ALTO | P0 |
| **Dashboard de Sessão Interativo** | ❌ | MÉDIO | P1 |
| **Template Engine Community-Powered** | ❌ | **CRÍTICO** | P0 |
| **Plugin System** (pip-based) | ❌ | ALTO | P1 |
| **Auto-Reporting** (markdown/html) | ⚠️ Parcial | MÉDIO | P2 |

---

## 🚀 ROADMAP DE IMPLEMENTAÇÃO

### **FASE 1: FUNDAÇÃO DE EXCELÊNCIA (2-3 semanas)**
**Objetivo:** Estabelecer os fundamentos de UX e arquitetura.

#### **Sprint 1.1: Sistema de Contextos** (5 dias) ⭐ CRÍTICO
```python
# Implementar:
vertice context create pentest-acme \
    --target 10.0.0.0/24 \
    --output-dir ~/engagements/acme \
    --proxy http://127.0.0.1:8080

vertice context list
vertice context use pentest-acme
vertice context current  # mostra contexto ativo
vertice context delete old-project

# Backend:
~/.config/vertice/contexts.toml  # Armazena todos os contextos
~/.config/vertice/current-context  # Ponteiro para contexto ativo
```

**Implementação:**
- Criar `vertice/config/context_manager.py`
- TOML para persistência (`tomli` / `tomli-w`)
- Validação de contexto antes de cada comando perigoso
- Auto-criação de diretórios de output

**Segurança:** Antes de executar qualquer comando destrutivo:
```python
def require_context():
    if not ContextManager.get_current():
        raise ContextError("Nenhum contexto ativo. Use 'vertice context use <name>'")
```

---

#### **Sprint 1.2: Modo Interativo** (4 dias) ⭐ CRÍTICO
```python
# Implementar:
vertice scan interactive  # Modo guiado

# Fluxo:
? Qual tipo de scan? (use setas)
  > Port Scan (Nmap)
    Web Vulnerability Scan
    Network Discovery

? Target(s): [input com autocomplete de contexto atual]
  10.0.0.0/24

? Intensity? (use setas)
    Stealth (-T2)
  > Normal (-T3)
    Aggressive (-T4)

? Additional options? [y/N]: n

✓ Executando scan...
[████████████████████████████] 100% Complete
```

**Libs:**
- `prompt-toolkit` - Prompts interativos
- `questionary` - Menus de seleção
- `rich.prompt` - Alternativa mais simples

**Implementação:**
- Criar `vertice/interactive/` module
- Wrappers para cada comando principal
- Autocomplete de targets do contexto ativo

---

#### **Sprint 1.3: Template Engine (Nuclei-style)** (6 dias) ⭐ CRÍTICO
```yaml
# templates/web/sqli-error-based.yaml
id: sqli-error-based-mysql
info:
  name: MySQL Error-Based SQLi Detection
  severity: high
  author: community
  tags: web,sqli,mysql

requests:
  - method: GET
    path:
      - "{{BaseURL}}/search?id=1'"
    matchers:
      - type: word
        words:
          - "SQL syntax"
          - "mysql_fetch"
          - "You have an error in your SQL syntax"
        condition: or
      - type: status
        status:
          - 500
```

**Comandos:**
```bash
# Executar template
vertice scan template sqli-error-based --target http://target.com

# Executar todos templates de uma categoria
vertice scan templates --category web --target http://target.com

# Atualizar templates da comunidade
vertice templates update

# Criar novo template
vertice templates create --interactive
```

**Implementação:**
- Criar `vertice/templates/` module
- Parser YAML (PyYAML)
- Matcher engine (regex, word, status)
- Template repository (Git-based, inspirado Nuclei)
- Community templates: `~/.vertice/templates/` (clone de repo)

**Template Repository:**
```bash
# Estrutura:
vertice-templates/
├── web/
│   ├── sqli/
│   ├── xss/
│   └── lfi/
├── network/
│   ├── ports/
│   └── services/
├── cves/
│   ├── 2024/
│   └── 2023/
└── custom/
```

---

### **FASE 2: ARSENAL MODERNO (2 semanas)**

#### **Sprint 2.1: Impacket Wrappers** (3 dias)
```bash
# Comandos propostos (metodologia > ferramenta):
vertice ad dump-secrets DC01.corp.local -u admin -p pass
vertice ad psexec TARGET.local -u admin -H <ntlm_hash>
vertice ad kerberoast DOMAIN.local -u user -p pass --format hashcat
vertice ad asreproast DOMAIN.local --user-file users.txt
```

**Implementação:**
- Wrappers Python para scripts Impacket
- Parsing de output (texto → JSON estruturado)
- Armazenar credenciais descobertas no contexto

---

#### **Sprint 2.2: BloodHound Integration** (4 dias)
```bash
# Ingestão de dados:
vertice ad bloodhound-collect DOMAIN.local -u user -p pass \
    --output ~/engagements/acme/bloodhound

# Análise (requer BloodHound Community Edition rodando):
vertice ad bloodhound-analyze \
    --query "shortest-path-to-da" \
    --start-node "USER@DOMAIN.LOCAL"
```

**Implementação:**
- Wrapper para SharpHound/BloodHound.py
- Parser de JSON do BloodHound
- Queries pré-definidas (via Cypher)
- Visualização ASCII de paths de ataque (fallback sem GUI)

---

#### **Sprint 2.3: Workflow Engine** (5 dias)
```yaml
# workflows/recon-full.yaml
name: Full Reconnaissance Workflow
description: Complete recon from domain to vulnerable services

steps:
  - name: subdomain-enum
    command: recon subdomains
    args:
      domain: "{{target_domain}}"

  - name: port-scan
    command: recon scan-port
    args:
      targets: "{{subdomain-enum.output}}"
      ports: "80,443,8080,8443"

  - name: web-scan
    command: web scan
    args:
      urls: "{{port-scan.http_services}}"
      templates: "web/common"
    parallel: true  # Executa em paralelo
```

**Execução:**
```bash
vertice workflow run recon-full --var target_domain=target.com
```

**Implementação:**
- Parser YAML de workflows
- DAG (Directed Acyclic Graph) para dependências
- Variable interpolation (`{{step.output}}`)
- Parallel execution (asyncio)
- Progress tracking (rich)

---

### **FASE 3: ECOSSISTEMA ABERTO (1-2 semanas)**

#### **Sprint 3.1: Plugin System** (5 dias)
```bash
# Instalar plugin da comunidade:
pip install vertice-plugin-c2-sliver
vertice plugins list
vertice plugins enable sliver

# Usar plugin:
vertice sliver generate --os linux --arch x64 --mtls
vertice sliver implants
```

**Arquitetura:**
```python
# Plugin Interface:
class VerticePlugin(ABC):
    name: str
    version: str
    commands: List[Command]

    @abstractmethod
    def register(self, cli: Click):
        """Registra comandos no CLI"""
        pass

# Auto-discovery:
# Plugins são pacotes pip com entry point:
[tool.poetry.plugins."vertice.plugins"]
sliver = "vertice_plugin_sliver:SliverPlugin"
```

---

#### **Sprint 3.2: Community Template Hub** (3 dias)
```bash
# Publicar template na comunidade:
vertice templates publish my-sqli-template.yaml \
    --category web/sqli \
    --author juan

# Buscar templates:
vertice templates search "wordpress"
vertice templates install wordpress-scanner

# Estatísticas:
vertice templates stats
  Total templates: 1,247
  Categories: 15
  Contributors: 89
  Last update: 2 hours ago
```

**Backend:**
- GitHub repo: `vertice-io/templates`
- CI/CD para validação automática (YAML schema)
- Website: templates.vertice.io (browse + search)

---

## 🎯 FEATURES DISRUPTIVAS (Dossiê)

### **1. Sistema de Contexto de Engajamento** ✅ (Sprint 1.1)
**O que é:** kubectl-style contexts para gerenciar múltiplos engajamentos.
**Por que é disruptivo:** Elimina erros de "executar no cliente errado".
**Implementação:** Ver Sprint 1.1.

### **2. Motor de Workflow (YAML Playbooks)** ✅ (Sprint 2.3)
**O que é:** Definir sequências complexas de comandos em YAML.
**Por que é disruptivo:** Automação sem scripting, compartilhável, versionável.
**Implementação:** Ver Sprint 2.3.

### **3. Template Engine Community-Powered** ✅ (Sprint 1.3)
**O que é:** Nuclei-style templates em YAML, contribuídos pela comunidade.
**Por que é disruptivo:** Detecções atualizadas em horas (não semanas).
**Implementação:** Ver Sprint 1.3.

### **4. Dashboard de Sessão Interativo** (Futuro)
**O que é:** TUI (Text User Interface) com painéis de status em tempo real.
```
┌──────────────────── VÉRTICE DASHBOARD ────────────────────┐
│ Context: pentest-acme | Target: 10.0.0.0/24              │
├───────────────────────────────────────────────────────────┤
│ Active Scans:                                             │
│   [████████░░░░░░░░] Port Scan (65%)                      │
│   [█████████████░░░] Web Scan (85%)                       │
│                                                           │
│ Findings: 🔴 5 Critical | 🟠 12 High | 🟡 8 Medium        │
│                                                           │
│ Recent Activity:                                          │
│   14:32 - SQLi found in /search?id=                       │
│   14:30 - Open SMB on 10.0.0.15                           │
│   14:28 - Port scan started                               │
└───────────────────────────────────────────────────────────┘
```

**Libs:** `textual` (Textualize) - TUI framework Python.

---

## 📋 CHECKLIST DE IMPLEMENTAÇÃO IMEDIATA

### **P0 - CRÍTICO (Começar AGORA):**
- [ ] Sistema de Contextos (`vertice context`) - Sprint 1.1
- [ ] Template Engine (Nuclei-style) - Sprint 1.3
- [ ] Modo Interativo (prompt-toolkit) - Sprint 1.2

### **P1 - ALTO (Próximas 2 semanas):**
- [ ] Workflow Engine (YAML playbooks) - Sprint 2.3
- [ ] Plugin System (pip-based) - Sprint 3.1
- [ ] Impacket Wrappers (AD commands) - Sprint 2.1
- [ ] BloodHound Integration - Sprint 2.2

### **P2 - MÉDIO (Backlog):**
- [ ] Dashboard Interativo (textual TUI)
- [ ] Sliver/Mythic C2 Integration
- [ ] Auto-Reporting (markdown → PDF)
- [ ] MITRE ATT&CK Mapping automático

---

## 🔥 DIFERENCIAIS COMPETITIVOS

Após implementação do plano, o **Vértice CLI** terá:

1. ✅ **Melhor UX da categoria** (contextos + interativo + templates)
2. ✅ **Community-powered detection** (templates open-source)
3. ✅ **Workflow automation nativa** (YAML playbooks)
4. ✅ **Extensível via plugins** (ecossistema aberto)
5. ✅ **Metodologia embutida** (comandos por fase de ataque)

**Nenhuma ferramenta concorrente tem TODOS esses diferenciais.**

---

## 💡 QUICK WINS (Implementar em 1-2 dias)

1. **Rich Error Messages:**
```python
# Atual:
Error: Command not found: sacn

# Upgrade:
Error: Command not found: 'sacn'
Did you mean: 'scan'?

Try: vertice scan --help
```

2. **Progress Bars em todos os comandos longos:**
```python
# Wrap async operations:
with Progress() as progress:
    task = progress.add_task("Scanning ports...", total=65535)
    # ... scan
    progress.update(task, advance=1)
```

3. **Output formatado por padrão:**
```bash
# Ao invés de texto bruto, sempre usar rich.table
vertice scan results --format table  # (padrão)
vertice scan results --format json   # (para piping)
```

---

## 🌍 INTEGRAÇÃO COM MAXIMUS

O dossiê foca no **Vértice CLI**, mas podemos integrar com **MAXIMUS AI**:

```bash
# MAXIMUS como brain do Vértice:
vertice ai analyze findings.json
  → MAXIMUS analisa findings
  → Retorna priorização + recomendações

vertice ai suggest-next-steps
  → MAXIMUS sugere próximos comandos baseado em contexto

vertice workflow generate --goal "pwn domain admin"
  → MAXIMUS gera workflow customizado via LLM
```

**Implementação:**
- Vértice CLI chama API do MAXIMUS Core
- MAXIMUS tem acesso ao contexto ativo
- Chain-of-Thought reasoning para sugerir ações

---

## 📊 MÉTRICAS DE SUCESSO

| Métrica | Baseline Atual | Meta Pós-Upgrade |
|---------|----------------|------------------|
| Time-to-Value (primeiro scan útil) | ~10 min | **< 2 min** |
| Curva de aprendizado (comandos memorizados) | ~20 comandos | **< 5 comandos** (contexto + interativo) |
| Community templates disponíveis | 0 | **> 100** (6 meses) |
| Plugins de comunidade | 0 | **> 10** (6 meses) |
| Erros de "contexto errado" | Não rastreado | **0** (sistema de contextos) |

---

## 🎯 PRÓXIMOS PASSOS IMEDIATOS

1. **HOJE:**
   - Criar branch `feature/context-system`
   - Implementar `ContextManager` básico (TOML)
   - PR #1: Sistema de Contextos

2. **AMANHÃ:**
   - Criar branch `feature/template-engine`
   - Parser YAML para templates
   - Matcher engine básico (word, regex)

3. **SEMANA 1:**
   - Modo interativo para comando `scan`
   - Publicar template repository (GitHub)
   - Documentação atualizada

---

## 💝 FILOSOFIA

**"Pela Arte. Pela Sociedade."**

Este upgrade não é apenas sobre adicionar features.

É sobre **DEMOCRATIZAR** a cibersegurança de ponta.

É sobre **EMPODERAR** operadores com ferramentas de classe mundial.

É sobre construir uma **COMUNIDADE** que evolui o arsenal coletivo.

Cada linha de código foi alinhada com:
- ❤️ **UX que respeita o tempo do operador**
- 🎯 **Metodologia que estrutura o caos**
- 🌍 **Open-source que acelera a inovação**
- 🔥 **Excelência técnica sem compromissos**

---

**VÉRTICE CLI - A Próxima Geração de Offensive Security CLI**

**Plano criado:** 2025-10-02
**Baseado em:** Dossiê de Inteligência Estratégica
**Status:** PRONTO PARA EXECUÇÃO ✅
**Primeira Sprint:** Sistema de Contextos (começar AGORA)

---

**Desenvolvido com 🔥 por Juan + Claude**
**Alinhado com a visão do Dossiê Estratégico**
