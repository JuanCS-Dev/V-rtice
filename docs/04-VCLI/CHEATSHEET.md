# 📋 vCLI Cheatsheet

**Referência rápida de comandos vCLI** - Versão 1.0 | 2025-10-05

*Todos os 34 comandos organizados por categoria para consulta rápida.*

---

## 🔐 Authentication & Context

```bash
# Autenticação
vcli auth login                      # Login no backend
vcli auth logout                     # Logout
vcli auth status                     # Verificar status de autenticação
vcli auth token                      # Mostrar token atual

# Gerenciamento de contexto
vcli context list                    # Listar contextos
vcli context switch <name>           # Trocar contexto
vcli context status                  # Ver contexto atual
vcli context create <name>           # Criar novo contexto
```

---

## 🔍 IP Intelligence & Network

```bash
# IP Intelligence
vcli ip 8.8.8.8                      # Lookup básico
vcli ip 1.2.3.4 --deep               # Análise profunda
vcli ip 1.2.3.4 --json               # Output JSON
vcli ip scan 192.168.1.0/24          # Scan de range

# Network Scanning
vcli scan 192.168.1.100              # Scan de host
vcli scan 192.168.1.0/24             # Scan de rede
vcli scan <target> --ports 80,443    # Portas específicas
vcli scan <target> --service         # Detecção de serviços
vcli scan <target> --vuln            # Scan de vulnerabilidades
vcli scan <target> --output file.json # Salvar resultados

# Monitoring
vcli monitor status                  # Status geral
vcli monitor alerts                  # Ver alertas
vcli monitor logs <service>          # Logs de serviço
vcli monitor service <name>          # Status de serviço específico
```

---

## 🛡️ Threat Intelligence

```bash
# Threat Lookup
vcli threat 1.2.3.4                  # Verificar IP
vcli threat example.com              # Verificar domínio
vcli threat 44d88612...              # Verificar hash
vcli threat <ioc> --feed all         # Consultar todos feeds

# Threat Intel Platform
vcli threat_intel feeds              # Listar feeds ativos
vcli threat_intel search <query>     # Buscar IOCs
vcli threat_intel update             # Atualizar feeds
vcli threat_intel stats              # Estatísticas
```

---

## 🦠 Malware Analysis

```bash
# Análise de Malware
vcli malware analyze file.exe        # Analisar arquivo
vcli malware scan /path/             # Scan de diretório
vcli malware hash <hash>             # Lookup por hash
vcli malware report <file> --json    # Relatório JSON
vcli malware sandbox <file>          # Executar em sandbox
vcli malware yara <file>             # Scan YARA

# Offline Analysis
vcli malware offline <file>          # Análise offline (sem API)
```

---

## 🔎 Threat Hunting

```bash
# Hunt Operations
vcli hunt search --ioc 1.2.3.4       # Buscar por IOC
vcli hunt query <veql-query>         # Executar query VeQL
vcli hunt artifact <name>            # Executar artifact pré-built
vcli hunt timeline --start <date>    # Timeline de atividades
vcli hunt pivot --from <ioc>         # Pivot analysis
vcli hunt correlate --ioc1 <a> --ioc2 <b> # Correlacionar IOCs
```

---

## 🚨 Incident Response

```bash
# Incident Management
vcli incident list                   # Listar incidentes
vcli incident create                 # Criar incidente
vcli incident show <id>              # Ver detalhes
vcli incident update <id>            # Atualizar status
vcli incident close <id>             # Fechar incidente
vcli incident report <id>            # Gerar relatório
```

---

## 🤖 MAXIMUS AI & Intelligence

```bash
# Maximus AI (Cérebro Central)
vcli maximus chat                    # Chat interativo
vcli maximus analyze <data>          # Análise de dados
vcli maximus predict <scenario>      # Predição de ameaças
vcli maximus optimize                # Otimização de recursos

# Ask (AI Conversational)
vcli ask "Find lateral movement"     # Pergunta direta
vcli ask "Analyze traffic anomalies" # Análise assistida

# Investigate (AI-Orchestrated)
vcli investigate --ioc 1.2.3.4       # Investigação completa
vcli investigate --ioc <ip> --ai     # Com assistência IA
vcli investigate report <id>         # Gerar relatório

# Memory System
vcli memory search <query>           # Buscar na memória
vcli memory add <data>               # Adicionar à memória
vcli memory consolidate              # Consolidar memórias
vcli memory stats                    # Estatísticas
```

---

## 🔎 OSINT (Open Source Intelligence)

```bash
# OSINT Operations
vcli osint email john@example.com    # Intel sobre email
vcli osint username johndoe          # Buscar username
vcli osint phone +5511999999999      # Intel sobre telefone
vcli osint domain example.com        # Intel sobre domínio
vcli osint ip 1.2.3.4                # OSINT sobre IP
vcli osint search <query>            # Busca geral
vcli osint report <target> --pdf     # Gerar relatório PDF
```

---

## 📁 Project & Workspace Management

```bash
# Project Management
vcli project list                    # Listar projetos
vcli project create <name>           # Criar projeto
vcli project switch <name>           # Trocar projeto ativo
vcli project delete <name>           # Deletar projeto
vcli project stats                   # Estatísticas
vcli project status                  # Status atual

# Workspace Operations
vcli project add-host 192.168.1.100  # Adicionar host
vcli project add-port <host> <port>  # Adicionar porta
vcli project add-vuln <host> <cve>   # Adicionar vulnerabilidade
vcli project hosts                   # Listar hosts
vcli project vulns                   # Listar vulnerabilidades
vcli project commit                  # Commit para Git
vcli project query "natural language" # Query com IA
```

---

## ⚔️ Offensive Security Arsenal (Uso Autorizado Apenas)

```bash
# Network Reconnaissance
vcli offensive recon <target>        # Reconhecimento
vcli offensive scan <target>         # Scan agressivo
vcli offensive enum <target>         # Enumeração

# Exploitation (Authorized Only!)
vcli offensive exploit <target>      # Exploração (safe mode)
vcli offensive c2 <command>          # Command & Control
vcli offensive pivot <from> <to>     # Pivoting

# BAS (Breach & Attack Simulation)
vcli offensive bas run <scenario>    # Executar cenário BAS
vcli offensive bas report            # Relatório BAS
```

**⚠️ ATENÇÃO**: Uso exclusivo para ambientes autorizados!

---

## 🛡️ AI Immune System (Immunis Machina)

```bash
# Immunis Operations
vcli immunis status                  # Status do sistema imune
vcli immunis cells                   # Listar células ativas
vcli immunis activate <cell-type>    # Ativar célula específica
vcli immunis threats                 # Ameaças detectadas
vcli immunis response <threat-id>    # Resposta a ameaça

# Cell Types
# - macrophage    → Detecção de padrões
# - dendritic     → Threat intel gathering
# - b-cell        → Memória imunológica
# - t-helper      → Coordenação
# - t-cytotoxic   → Neutralização
# - nk-cell       → Resposta rápida
# - neutrophil    → Primeira resposta
```

---

## 🌐 Distributed & Edge Operations

```bash
# Distributed Organism (FASE 10)
vcli distributed status              # Status distribuído
vcli distributed nodes               # Listar nodes
vcli distributed deploy <node>       # Deploy em edge
vcli distributed sync                # Sincronizar estado
vcli distributed health              # Health check global
```

---

## 📝 Human-Centric Language (HCL)

```bash
# HCL Operations
vcli hcl execute "scale up maximus"  # Executar comando HCL
vcli hcl plan "optimize network"     # Planejar ação
vcli hcl monitor                     # Monitorar loop homeostático
vcli hcl analyze <system>            # Analisar sistema
```

---

## 🧠 Cognitive & Sensory Services

```bash
# ASA Cognitive Services (FASE 8)
vcli cognitive visual <image>        # Análise visual
vcli cognitive audio <file>          # Análise de áudio
vcli cognitive text <data>           # Análise textual
vcli cognitive pattern <data>        # Detecção de padrões
vcli cognitive sentiment <text>      # Análise de sentimento
```

---

## 🔍 Detection & Response

```bash
# ADR (Adaptive Threat Response)
vcli adr status                      # Status ADR
vcli adr detect <file>               # Detecção de ameaças
vcli adr respond <threat-id>         # Resposta automática
vcli adr playbook <name>             # Executar playbook

# Detection Engine
vcli detect yara <file>              # Scan YARA
vcli detect sigma <logs>             # Regras Sigma
vcli detect ioc <data>               # Detectar IOCs
vcli detect anomaly <data>           # Detecção de anomalias
```

---

## 📋 Compliance & Governance

```bash
# Compliance Management
vcli compliance frameworks           # Listar frameworks
vcli compliance scan <framework>     # Scan de conformidade
vcli compliance report <framework>   # Gerar relatório
vcli compliance gap-analysis         # Análise de gaps

# DLP (Data Loss Prevention)
vcli dlp scan <path>                 # Scan DLP
vcli dlp policies                    # Listar políticas
vcli dlp violations                  # Ver violações
```

---

## 📊 Analytics & SIEM

```bash
# Advanced Analytics
vcli analytics query <query>         # Query analítica
vcli analytics ml <model> <data>     # Análise ML
vcli analytics behavioral <data>     # Análise comportamental
vcli analytics report                # Gerar relatório

# SIEM Integration
vcli siem query <query>              # Query SIEM
vcli siem alerts                     # Ver alertas
vcli siem export <format>            # Exportar dados
```

---

## 📜 Policy-as-Code

```bash
# Policy Management
vcli policy list                     # Listar políticas
vcli policy apply <policy.yaml>      # Aplicar política
vcli policy validate <policy.yaml>   # Validar política
vcli policy test <policy>            # Testar política
```

---

## 🔧 Scripting & Automation

```bash
# VScript Workflow Automation
vcli script run <script.vs>          # Executar VScript
vcli script validate <script.vs>     # Validar sintaxe
vcli script list                     # Listar scripts
vcli script create <name>            # Criar novo script
```

---

## 🔌 Plugin Management

```bash
# Plugin System
vcli plugin list                     # Listar plugins
vcli plugin install <name>           # Instalar plugin
vcli plugin enable <name>            # Habilitar plugin
vcli plugin disable <name>           # Desabilitar plugin
vcli plugin update                   # Atualizar todos
```

---

## 🎨 Interface & Shell

```bash
# TUI (Text User Interface)
vcli tui                             # Lançar dashboard full-screen
# Keybindings:
#   Ctrl+P → Command Palette
#   Ctrl+Q → Quit
#   1-4    → Quick Actions

# Interactive Shell
vcli shell                           # Lançar shell interativo
# Features:
#   - Autocomplete
#   - History
#   - Syntax highlighting

# Interactive Menu
vcli menu                            # Menu categorizado
```

---

## 🛠️ Flags & Options Comuns

```bash
# Output Formats
--json                               # Output JSON
--yaml                               # Output YAML
--table                              # Formato tabela
--csv                                # CSV format

# Output & Logging
--output <file>                      # Salvar em arquivo
--verbose, -v                        # Modo verboso
--quiet, -q                          # Modo silencioso
--log-level <level>                  # Nível de log (debug/info/warn/error)

# Filtering & Sorting
--filter <expr>                      # Filtrar resultados
--sort <field>                       # Ordenar por campo
--limit <n>                          # Limitar resultados

# Timing
--timeout <seconds>                  # Timeout
--async                              # Execução assíncrona
--wait                               # Aguardar conclusão

# Help
--help, -h                           # Mostrar help
--version, -v                        # Mostrar versão
```

---

## ⚡ Pro Tips & Aliases

### Aliases Úteis

Adicione ao seu `~/.bashrc` ou `~/.zshrc`:

```bash
# Shortcuts básicos
alias vip='vcli ip'
alias vscan='vcli scan'
alias vhunt='vcli hunt search'
alias vai='vcli maximus chat'
alias vproject='vcli project'
alias vmalware='vcli malware analyze'

# Workflows comuns
alias vthreat='vcli threat'
alias vinvestigate='vcli investigate --ai'
alias vosint='vcli osint'
alias vdetect='vcli detect'

# Monitoramento
alias vmon='vcli monitor status'
alias valerts='vcli monitor alerts'
```

### Combinações com Unix Tools

```bash
# Pipelines
vcli scan 192.168.1.0/24 --json | jq '.hosts[] | select(.open_ports > 5)'
vcli hunt search --ioc <ioc> | grep -E "HIGH|CRITICAL"
vcli project list | grep "active"

# Batch processing
cat ips.txt | xargs -I {} vcli ip {}
find /suspicious -type f -exec vcli malware analyze {} \;

# Filtering & counting
vcli threat intel --feed all | wc -l
vcli immunis threats | awk '{print $2}' | sort | uniq -c
```

### JSON Queries com jq

```bash
# Extrair campos específicos
vcli ip 1.2.3.4 --json | jq '.threat_score'
vcli scan <target> --json | jq '.hosts[].ports'

# Filtrar e transformar
vcli hunt search --ioc <ioc> --json | jq '.results[] | select(.severity == "high")'
```

---

## 🔄 Shell Completion

```bash
# Instalar completion
vcli --install-completion

# Testar
vcli <TAB><TAB>           # Lista todos comandos
vcli hunt <TAB><TAB>      # Lista subcomandos de hunt
vcli ip --<TAB><TAB>      # Lista flags disponíveis

# Ver completion instalado
vcli --show-completion
```

**Suporta**: Bash 4.0+, Zsh 5.0+

---

## 📚 Recursos Adicionais

- **[QUICKSTART.md](QUICKSTART.md)** - Guia de 5 minutos
- **[README.md](README.md)** - Documentação completa
- **[Completion Guide](completions/README.md)** - Shell completion
- **[Roadmap](ROADMAP_2025_2027.md)** - Features futuras

---

## 🎯 Fluxos de Trabalho por Persona

### 🛡️ SOC Analyst

```bash
# Rotina matinal
vcli monitor alerts --last 24h
vcli threat intel update
vcli hunt search --ioc <today-iocs>
vcli siem query "severity=high"
```

### 🔥 Incident Responder

```bash
# Resposta a incidente
vcli incident create --severity critical --desc "..."
vcli investigate --ioc <suspicious-ip> --ai
vcli hunt timeline --incident-id <id>
vcli adr respond <threat-id>
vcli incident report <id> --pdf
```

### 🎯 Penetration Tester

```bash
# Workflow de pentest
vcli project create client-pentest-2025
vcli scan <target-network> --vuln
vcli offensive recon <target>
vcli project add-vuln <host> <cve> --severity high
vcli project report --template pentest
```

### 🔍 Threat Hunter

```bash
# Caça proativa
vcli hunt query "SELECT * FROM processes WHERE ..."
vcli hunt pivot --from <ioc>
vcli hunt correlate --ioc1 <a> --ioc2 <b>
vcli ask "Find APT patterns in network traffic"
vcli hunt report --format json
```

### 🤖 Security Researcher

```bash
# Pesquisa e análise
vcli malware analyze <sample> --sandbox
vcli cognitive pattern <data>
vcli maximus analyze <complex-attack>
vcli threat_intel search <apt-group>
vcli osint domain <c2-domain>
```

---

## 🚨 Emergency Response Checklist

```bash
# ⚠️ Incidente Crítico - 5 Passos

# 1. Criar incidente
vcli incident create --severity critical

# 2. Investigar IOC suspeito
vcli investigate --ioc <suspicious-ip> --ai

# 3. Buscar propagação
vcli hunt search --ioc <ip> --timeline

# 4. Acionar resposta automática
vcli adr respond <threat-id>

# 5. Gerar relatório executivo
vcli incident report <id> --format pdf --executive
```

---

## 📊 Comandos por Categoria (Resumo)

| Categoria | Comandos | Uso Principal |
|-----------|----------|---------------|
| **Core** | auth, context | Autenticação e contexto |
| **Intel** | ip, threat, threat_intel | Threat intelligence |
| **Malware** | malware | Análise de malware |
| **Hunting** | hunt | Threat hunting |
| **Response** | incident, adr, detect | Incident response |
| **AI** | maximus, ask, investigate, memory | IA e análise avançada |
| **OSINT** | osint | Open source intel |
| **Project** | project | Gerenciamento de workspaces |
| **Offensive** | offensive | Red team (autorizado) |
| **Defense** | immunis, distributed | Sistema imune digital |
| **Advanced** | hcl, cognitive | Serviços avançados |
| **Compliance** | compliance, dlp, policy | Governança |
| **Analytics** | analytics, siem | Análise e SIEM |
| **Automation** | script, plugin | Automação |
| **Interface** | tui, shell, menu | Interfaces |
| **Monitoring** | monitor, scan | Monitoramento |

---

## 🔢 Estatísticas

- **34 comandos** principais
- **100+ subcomandos** disponíveis
- **200+ flags/options** total
- **12 categorias** funcionais
- **5 personas** principais cobertas

---

<div align="center">

**vCLI - VÉRTICE Command Line Interface**

*Cybersecurity com IA Biomimética*

[![MAXIMUS AI](https://img.shields.io/badge/MAXIMUS-AI%203.0-blueviolet.svg)](https://github.com)
[![Commands](https://img.shields.io/badge/Commands-34-green.svg)](https://github.com)
[![Completion](https://img.shields.io/badge/Completion-Bash%20%7C%20Zsh-blue.svg)](https://github.com)

**Versão**: 1.0 | **Data**: 2025-10-05

🤖 **Built with [Claude Code](https://claude.com/claude-code)**

</div>
