# 🚀 vCLI - Quick Start (5 minutos)

**Comece a usar o vCLI em menos de 5 minutos!**

O vCLI é a interface de linha de comando do Vértice Platform - uma plataforma de cybersecurity com IA biomimética.

---

## ⚡ 1. Instalação (2 minutos)

### Pré-requisitos
- Python 3.11+
- Acesso ao backend Vértice (localhost ou remoto)

### Instalar vCLI

```bash
cd vertice-terminal

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows

# Instalar CLI
pip install -e .

# Verificar instalação
vcli --version
```

### Habilitar Shell Completion (Opcional)

```bash
# Instalação automática (recomendado)
vcli --install-completion

# Recarregar shell
source ~/.zshrc   # se Zsh
source ~/.bashrc  # se Bash
```

Agora você pode usar `<TAB>` para autocomplete! 🎉

---

## 🔑 2. Autenticação (30 segundos)

```bash
# Login no backend
vcli auth login

# Verificar status
vcli auth status
```

---

## 🎯 3. Primeiros Comandos (3 minutos)

### 🔍 Investigar um IP Suspeito

```bash
# Lookup básico
vcli ip 8.8.8.8

# Análise profunda
vcli ip 1.2.3.4 --deep

# Verificar reputação
vcli threat 1.2.3.4
```

**Output exemplo**:
```
✓ IP: 1.2.3.4
  Country: US
  ASN: AS15169 (Google LLC)
  Threat Score: 0/100 (Clean)
```

---

### 🦠 Analisar Malware

```bash
# Analisar arquivo suspeito
vcli malware analyze suspicious.exe

# Scan de diretório
vcli malware scan /downloads/

# Verificar hash
vcli malware hash 44d88612fea8a8f36de82e1278abb02f
```

---

### 🤖 Conversar com Maximus AI

```bash
# Modo chat interativo
vcli maximus chat

# Fazer pergunta direta
vcli ask "Find lateral movement in network"

# Investigação assistida
vcli investigate --ioc 1.2.3.4 --ai
```

**Exemplo de sessão**:
```
You: What are the latest APT techniques?
Maximus: Based on MITRE ATT&CK, the top APT techniques in 2025 are...
```

---

### 🔎 Threat Hunting

```bash
# Buscar por IOC
vcli hunt search --ioc 1.2.3.4

# Timeline de ameaças
vcli hunt timeline --start 2025-01-01 --end 2025-01-07

# Executar query VeQL
vcli hunt query "SELECT * FROM processes WHERE name LIKE '%malware%'"
```

---

### 📁 Gerenciar Projetos

```bash
# Criar projeto de pentest
vcli project create pentest-acme

# Listar todos os projetos
vcli project list

# Adicionar host ao projeto
vcli project add-host 192.168.1.100

# Ver estatísticas
vcli project stats
```

---

### 🌐 Network Scanning

```bash
# Scan rápido
vcli scan 192.168.1.0/24

# Port scan específico
vcli scan 192.168.1.100 --ports 80,443,8080

# Scan com detecção de serviços
vcli scan 192.168.1.100 --service-detection
```

---

### 🔎 OSINT (Open Source Intelligence)

```bash
# Buscar informações sobre email
vcli osint email john@example.com

# Buscar username em redes sociais
vcli osint username johndoe

# Buscar domínio
vcli osint domain example.com
```

---

## 🎨 4. Interface Gráfica (TUI)

Quer uma interface visual no terminal?

```bash
# Lançar dashboard full-screen
vcli tui

# Lançar shell interativo
vcli shell
```

**Atalhos do TUI**:
- `Ctrl+P` → Command Palette
- `Ctrl+Q` → Quit
- `1-4` → Quick Actions

---

## 🔥 5. Fluxos Práticos Completos

### Fluxo 1: Investigação de IP Suspeito

```bash
# 1. Lookup inicial
vcli ip 1.2.3.4

# 2. Verificar threat intelligence
vcli threat 1.2.3.4

# 3. Buscar atividades relacionadas
vcli hunt search --ioc 1.2.3.4

# 4. Pedir análise à IA
vcli ask "Analyze threat from IP 1.2.3.4"

# 5. Adicionar ao projeto
vcli project add-host 1.2.3.4 --threat high
```

---

### Fluxo 2: Análise de Malware

```bash
# 1. Scan inicial
vcli malware analyze suspicious.exe

# 2. Ver relatório detalhado
vcli malware report suspicious.exe --format json

# 3. Buscar IOCs extraídos
vcli hunt search --ioc <extracted-hash>

# 4. Gerar contexto com IA
vcli maximus chat
> "Explain this malware behavior: <paste-analysis>"
```

---

### Fluxo 3: Pentest Workflow

```bash
# 1. Criar projeto
vcli project create pentest-company-2025

# 2. Scan de rede
vcli scan 10.0.0.0/24 --output json > hosts.json

# 3. Adicionar hosts ao projeto
vcli project add-host 10.0.0.10 --ports 22,80,443

# 4. Buscar vulnerabilidades
vcli scan 10.0.0.10 --vuln-scan

# 5. Documentar findings
vcli project add-vuln 10.0.0.10 --cve CVE-2023-12345 --severity high

# 6. Gerar relatório
vcli project stats
```

---

## 🛠️ 6. Comandos Úteis

### Help System

```bash
# Help geral
vcli --help

# Help de comando específico
vcli ip --help
vcli malware --help

# Listar todos os comandos
vcli --help | grep "│"
```

### Output Formats

```bash
# JSON output
vcli ip 8.8.8.8 --json

# Salvar em arquivo
vcli scan 192.168.1.0/24 --output results.json

# Modo verboso
vcli threat 1.2.3.4 --verbose
```

### Context Switching

```bash
# Trocar contexto de trabalho
vcli context list
vcli context switch production

# Ver contexto atual
vcli context status
```

---

## 🚨 7. Troubleshooting Rápido

### Problema 1: "Command not found: vcli"

**Solução**:
```bash
# Verificar se ambiente virtual está ativo
which python  # Deve mostrar path do venv

# Reativar venv
source venv/bin/activate

# Reinstalar se necessário
pip install -e .
```

---

### Problema 2: "Connection refused to backend"

**Solução**:
```bash
# Verificar se backend está rodando
curl http://localhost:8000/health

# Verificar configuração
cat ~/.vertice/config.yaml

# Reconfigurar backend
vcli auth login --url http://localhost:8000
```

---

### Problema 3: "Permission denied"

**Solução**:
```bash
# Verificar permissões
ls -lh ~/.vertice/

# Corrigir permissões se necessário
chmod 755 ~/.vertice/
chmod 644 ~/.vertice/config.yaml
```

---

## 📚 8. Próximos Passos

Agora que você domina o básico, explore mais:

- **[CHEATSHEET.md](CHEATSHEET.md)** - Referência rápida de todos os comandos
- **[README.md](README.md)** - Documentação completa do vCLI
- **[Completion Guide](completions/README.md)** - Shell completion avançado
- **[Roadmap](ROADMAP_2025_2027.md)** - Features futuras

### Comandos Avançados para Explorar

```bash
vcli offensive         # Offensive Security Arsenal (uso autorizado)
vcli immunis           # AI Immune System operations
vcli distributed       # Distributed organism (edge + cloud)
vcli hcl               # Human-Centric Language
vcli memory            # Maximus Memory System
vcli cognitive         # ASA Cognitive Services
vcli compliance        # Multi-framework compliance
vcli dlp               # Data Loss Prevention
vcli siem              # SIEM Integration
vcli plugin            # Plugin management
vcli script            # VScript workflow automation
```

---

## 🎓 9. Exemplos Práticos por Caso de Uso

### SOC Analyst

```bash
# Monitoramento diário
vcli monitor alerts --last 24h
vcli threat intel --feed latest
vcli hunt search --ioc <today's-iocs>
```

### Incident Responder

```bash
# Resposta a incidente
vcli incident create --severity critical
vcli hunt timeline --incident-id <id>
vcli maximus analyze-incident <id>
vcli incident report --format pdf
```

### Penetration Tester

```bash
# Workflow de pentest
vcli project create client-pentest
vcli scan <target-network> --aggressive
vcli offensive exploit <target> --safe-mode
vcli project report --template pentest
```

### Threat Hunter

```bash
# Caça a ameaças proativa
vcli hunt query --veql <query>
vcli hunt pivot --from 1.2.3.4
vcli hunt correlate --ioc1 <ip> --ioc2 <hash>
vcli ask "Find anomalies in network traffic"
```

---

## ⚡ 10. Pro Tips

### Tip 1: Use Aliases

Adicione ao seu `~/.bashrc` ou `~/.zshrc`:

```bash
alias vip='vcli ip'
alias vscan='vcli scan'
alias vhunt='vcli hunt search'
alias vai='vcli maximus chat'
alias vproject='vcli project'
```

### Tip 2: Output JSON para Pipelines

```bash
# Extrair IPs de scan e investigar
vcli scan 192.168.1.0/24 --json | jq -r '.hosts[].ip' | xargs -I {} vcli ip {}
```

### Tip 3: Combinar com Ferramentas Unix

```bash
# Buscar e filtrar
vcli hunt search --ioc <ioc> | grep -E "HIGH|CRITICAL"

# Paginação
vcli project list | less

# Contar resultados
vcli threat intel --feed all | wc -l
```

### Tip 4: Use Shell Interativo para Fluxos Longos

```bash
vcli shell
# Agora você tem um shell dedicado com histórico e autocomplete!
```

---

## 🎯 Resumo

**Você aprendeu**:
- ✅ Instalar e configurar vCLI
- ✅ Top 10 comandos mais usados
- ✅ 3 fluxos práticos completos
- ✅ Troubleshooting comum
- ✅ Dicas pro de produtividade

**Tempo total**: ~5 minutos ⏱️

---

## 🤝 Ajuda e Suporte

- **Help inline**: `vcli --help` ou `vcli <command> --help`
- **Documentação**: `vertice-terminal/README.md`
- **Issues**: [GitHub Issues](https://github.com/JuanCS-Dev/V-rtice/issues)
- **Cheatsheet**: `vertice-terminal/CHEATSHEET.md`

---

**Bem-vindo ao Vértice Platform! 🎉**

*Cybersecurity com IA Biomimética - O primeiro sistema imunológico digital do mundo.*

---

<div align="center">

[![MAXIMUS AI 3.0](https://img.shields.io/badge/MAXIMUS-AI%203.0-blueviolet.svg)](https://github.com)
[![vCLI](https://img.shields.io/badge/vCLI-34%20Commands-green.svg)](https://github.com)
[![Completion](https://img.shields.io/badge/Shell-Completion-blue.svg)](completions/)

**🤖 Built with [Claude Code](https://claude.com/claude-code)**

</div>
