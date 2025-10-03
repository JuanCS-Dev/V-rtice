# 🎯 VÉRTICE CLI - Guia Completo de Instalação e Uso

## 📋 Índice
1. [Pré-requisitos](#pré-requisitos)
2. [Instalação](#instalação)
3. [Primeiro Uso](#primeiro-uso)
4. [Comandos Disponíveis](#comandos-disponíveis)
5. [Sistema de Autenticação](#sistema-de-autenticação)
6. [Exemplos Práticos](#exemplos-práticos)
7. [Troubleshooting](#troubleshooting)
8. [Renomeação Maximus → Maximus](#renomeação-maximus--maximus)

---

## 🔧 Pré-requisitos

Antes de começar, certifique-se de ter instalado:

- **Python 3.11+** (verifique com `python --version`)
- **pip** (gerenciador de pacotes Python)
- **Git** (para clonar o repositório)

### Verificando Pré-requisitos

```bash
# Verificar Python
python --version
# Deve mostrar: Python 3.11.x ou superior

# Verificar pip
pip --version
# Deve mostrar a versão do pip

# Verificar Git
git --version
# Deve mostrar a versão do git
```

---

## 📦 Instalação

### Passo 1: Navegar até o diretório

```bash
cd /home/juan/vertice-dev/vertice-terminal
```

### Passo 2: Instalar dependências

```bash
pip install -r requirements.txt
```

**Dependências principais instaladas:**
- `typer` - Framework CLI
- `rich` - Output colorido e bonito
- `httpx` - Cliente HTTP assíncrono
- `keyring` - Armazenamento seguro de tokens
- `cryptography` - Criptografia
- E outras...

### Passo 3: Verificar instalação

```bash
python -m vertice.cli --help
```

Se aparecer o help do CLI, está tudo OK! ✅

---

## 🚀 Primeiro Uso

### 1. Ver o Banner e Ajuda

```bash
# Mostra o banner + lista de comandos
python -m vertice.cli

# Mostra apenas a ajuda (sem banner)
python -m vertice.cli --no-banner

# Mostra a versão
python -m vertice.cli --version
```

### 2. Fazer Login (IMPORTANTE!)

**🔐 Todos os comandos exigem autenticação!**

```bash
# Login com seu email
python -m vertice.cli auth login --email seu.email@gmail.com

# Ou sem o flag (vai pedir o email)
python -m vertice.cli auth login
```

**Super Admin:** `juan.brainfarma@gmail.com` 👑
- Tem TODAS as permissões
- Acesso a ferramentas offensive
- Level 100

**Outros emails:** Role `analyst`
- Permissões: read, write, execute
- Sem acesso offensive
- Level 50

### 3. Verificar Status de Login

```bash
# Status rápido
python -m vertice.cli auth status

# Informações completas do usuário
python -m vertice.cli auth whoami
```

### 4. Logout

```bash
python -m vertice.cli auth logout
```

---

## 📚 Comandos Disponíveis

### 🔐 Auth (Autenticação)

```bash
# Login
python -m vertice.cli auth login --email juan.brainfarma@gmail.com

# Logout
python -m vertice.cli auth logout

# Ver quem está logado
python -m vertice.cli auth whoami

# Status rápido
python -m vertice.cli auth status
```

### 🔍 IP Intelligence

```bash
# Analisar um IP
python -m vertice.cli ip analyze 8.8.8.8

# Analisar com output JSON
python -m vertice.cli ip analyze 8.8.8.8 --json

# Descobrir seu IP público
python -m vertice.cli ip my-ip (ta off, 404)

# Análise em massa de IPs (arquivo)
python -m vertice.cli ip bulk ips.txt
```

**Arquivo ips.txt exemplo:**
```
8.8.8.8
1.1.1.1
185.220.101.23
45.129.56.200
```

### 🛡️ Threat Intelligence

```bash
# Lookup de ameaça (IP, domain, hash)
python -m vertice.cli threat lookup malicious.com

# Verificar target
python -m vertice.cli threat check malware.exe

# Scan de arquivo
python -m vertice.cli threat scan /path/to/file.zip

# Feed de ameaças (em desenvolvimento)
python -m vertice.cli threat feed
```

### ⚔️ ADR (Ameaça Digital em Redes)

```bash
# Status do sistema ADR
python -m vertice.cli adr status

# Métricas (MTTR, detection rate)
python -m vertice.cli adr metrics

# Analisar arquivo
python -m vertice.cli adr analyze file /path/to/suspicious.log

# Analisar tráfego de rede
python -m vertice.cli adr analyze network 192.168.1.100

# Analisar processo
python -m vertice.cli adr analyze process "ls -la"
```

### 🦠 Malware Analysis

```bash
# Analisar arquivo
python -m vertice.cli malware analyze /path/to/suspicious.exe

# YARA scan (em desenvolvimento)
python -m vertice.cli malware yara /path/to/file

# Lookup por hash (em desenvolvimento)
python -m vertice.cli malware hash abc123def456
```

### 🌐 Network Scanning

```bash
# Scan de portas
python -m vertice.cli scan ports example.com

# Nmap scan
python -m vertice.cli scan nmap example.com

# Scan de vulnerabilidades
python -m vertice.cli scan vulns example.com

# Network discovery (em desenvolvimento)
python -m vertice.cli scan network
```

### 🔎 Threat Hunting

```bash
# Buscar IOCs
python -m vertice.cli hunt search "malicious.com"

# Timeline de incidente
python -m vertice.cli hunt timeline INC001 --last 48h

# Análise pivot
python -m vertice.cli hunt pivot "malicious.com"

# Correlacionar IOCs (em desenvolvimento)
python -m vertice.cli hunt correlate "malicious.com" "1.2.3.4"
```

### 🌌 Maximus AI (será renomeado para Maximus)

```bash
# Fazer pergunta para a IA
python -m vertice.cli maximus ask "Qual é o status do sistema?"

# Analisar contexto
python -m vertice.cli maximus analyze "logs de erro aqui..."

# Investigar incidente
python -m vertice.cli maximus investigate "Detalhes do incidente..."

# Chat interativo (em desenvolvimento)
python -m vertice.cli maximus chat

# Oráculo (em desenvolvimento)
python -m vertice.cli maximus oraculo

# Eureka - análise de código (em desenvolvimento)
python -m vertice.cli maximus eureka /path/to/code
```

### 🛰️ Monitor

```bash
# Monitorar ameaças (em desenvolvimento)
python -m vertice.cli monitor threats

# Monitorar logs de serviço
python -m vertice.cli monitor logs ai_agent_service

# Seguir logs em tempo real
python -m vertice.cli monitor logs ai_agent_service --follow

# Dashboard de métricas (em desenvolvimento)
python -m vertice.cli monitor metrics

# Stream de alertas (em desenvolvimento)
python -m vertice.cli monitor alerts
```

### 📋 Menu Interativo

```bash
# Menu com todas as opções categorizadas
python -m vertice.cli menu (off)
```

---

## 🔐 Sistema de Autenticação

### Roles e Permissões

| Role | Level | Permissões | Acesso Offensive |
|------|-------|------------|------------------|
| **super_admin** 👑 | 100 | `*` (todas) | ✅ Sim |
| **admin** | 80 | read, write, execute, manage_users, offensive | ✅ Sim |
| **analyst** | 50 | read, write, execute | ❌ Não |
| **viewer** | 10 | read | ❌ Não |

### Super Admin

**Email:** `juan.brainfarma@gmail.com`

Tem acesso TOTAL a:
- ✅ Todas as ferramentas
- ✅ Ferramentas offensive
- ✅ Comandos administrativos
- ✅ Todas as permissões

### Localização dos Tokens

**Diretório:** `~/.vertice/auth/`

```bash
~/.vertice/auth/
├── token.json        # Metadados do token
└── user.json         # Dados do usuário
```

**Token seguro:** Armazenado no `keyring` do sistema

### Tempo de Sessão

- **Duração:** 1 hora
- **Auto-renovação:** Não (precisa fazer login novamente)

---

## 💡 Exemplos Práticos

### Exemplo 1: Workflow Básico de Análise

```bash
# 1. Login
python -m vertice.cli auth login --email juan.brainfarma@gmail.com

# 2. Verificar se está logado
python -m vertice.cli auth whoami

# 3. Analisar um IP suspeito
python -m vertice.cli ip analyze 185.220.101.23

# 4. Buscar mais informações sobre ameaças
python -m vertice.cli threat lookup 185.220.101.23

# 5. Fazer scan de portas
python -m vertice.cli scan ports 185.220.101.23
```

### Exemplo 2: Investigação com Maximus AI

```bash
# Login
python -m vertice.cli auth login --email juan.brainfarma@gmail.com

# Fazer pergunta para Maximus
python -m vertice.cli maximus ask "Analise este IP: 185.220.101.23"

# Investigar incidente
python -m vertice.cli maximus investigate "IP 185.220.101.23 fazendo varredura de portas"
```

### Exemplo 3: Análise em Massa

```bash
# Criar arquivo com IPs
cat > ips_suspeitos.txt << EOF
185.220.101.23
45.129.56.200
178.162.212.214
91.219.236.232
EOF

# Análise em massa
python -m vertice.cli ip bulk ips_suspeitos.txt

# Com output JSON para processamento
python -m vertice.cli ip bulk ips_suspeitos.txt --json > resultados.json
```

### Exemplo 4: Threat Hunting

```bash
# Login
python -m vertice.cli auth login --email juan.brainfarma@gmail.com

# Buscar IOC
python -m vertice.cli hunt search "malicious-domain.com"

# Timeline dos últimos 7 dias
python -m vertice.cli hunt timeline INC001 --last 7d

# Análise pivot
python -m vertice.cli hunt pivot "malicious-domain.com"
```

---

## 🐛 Troubleshooting

### Erro: "Comando não encontrado"

```bash
# Certifique-se de estar no diretório correto
cd /home/juan/vertice-dev/vertice-terminal

# Use python -m ao invés de apenas vertice
python -m vertice.cli --help
```

### Erro: "Authentication Required"

```bash
# Você precisa fazer login primeiro!
python -m vertice.cli auth login --email seu.email@gmail.com
```

### Erro: "No module named 'vertice'"

```bash
# Instale as dependências
pip install -r requirements.txt

# Verifique se está no diretório correto
pwd
# Deve mostrar: /home/juan/vertice-dev/vertice-terminal
```

### Erro: "Service is offline"

```bash
# O serviço backend não está rodando
# Inicie os serviços do backend primeiro:
cd /home/juan/vertice-dev
docker-compose up -d

# Ou verifique se os serviços estão rodando:
docker-compose ps
```

### Erro: "ModuleNotFoundError: No module named 'keyring'"

```bash
# Instale a dependência faltando
pip install keyring cryptography
```

### Token Expirado

```bash
# Faça logout e login novamente
python -m vertice.cli auth logout
python -m vertice.cli auth login --email seu.email@gmail.com
```

### Ver Logs de Erro

```bash
# Rode com verbose para ver erros detalhados
python -m vertice.cli ip analyze 8.8.8.8 --verbose

# Ou capture o erro
python -m vertice.cli ip analyze 8.8.8.8 2>&1 | tee error.log
```

---

## 🔄 Renomeação Maximus → Maximus

Quando estiver pronto para renomear **Maximus** para **Maximus** em todo o projeto:

### Executar o Script de Renomeação

```bash
# Tornar executável (se ainda não for)
chmod +x rename_maximus_to_maximus.sh

# Executar
./rename_maximus_to_maximus.sh
```

### O que o script faz:

1. ✅ Substitui "Maximus" por "Maximus" em todos os arquivos
2. ✅ Renomeia arquivos e diretórios com "maximus" no nome
3. ✅ Atualiza imports Python
4. ✅ Atualiza configurações YAML
5. ✅ Mantém histórico do Git intacto

### Após executar:

```bash
# Ver mudanças
git diff

# Testar novo nome
python -m vertice.cli maximus --help

# Commit
git add .
git commit -m "refactor: Renomear Maximus para Maximus"
```

---

## 📊 Status dos Comandos

### ✅ Totalmente Implementados
- `auth` - Sistema de autenticação
- `ip` - IP Intelligence
- `threat` - Threat Intelligence
- `adr` - ADR Analysis
- `malware` - Malware Analysis
- `scan` - Network Scanning
- `hunt` - Threat Hunting
- `maximus` - Maximus AI (básico)
- `monitor` - Monitoring (básico)
- `menu` - Menu Interativo

### 🚧 Em Desenvolvimento
- `maximus chat` - Chat interativo
- `maximus oraculo` - Auto-melhoria
- `maximus eureka` - Análise de código
- `threat feed` - Feed de ameaças
- `monitor threats` - ThreatMap real-time
- `monitor metrics` - Dashboard métricas
- `monitor alerts` - Stream de alertas

---

## 🎯 Quick Start para Testers

### Setup Completo em 5 Minutos

```bash
# 1. Navegar para o projeto
cd /home/juan/vertice-dev/vertice-terminal

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Testar instalação
python -m vertice.cli --help

# 4. Login como Super Admin
python -m vertice.cli auth login --email juan.brainfarma@gmail.com

# 5. Verificar status
python -m vertice.cli auth whoami

# 6. Testar comando
python -m vertice.cli ip analyze 8.8.8.8
```

### Teste Rápido de Todos os Comandos

```bash
# Auth
python -m vertice.cli auth status

# IP
python -m vertice.cli ip my-ip

# Threat
python -m vertice.cli threat lookup 8.8.8.8

# ADR
python -m vertice.cli adr status

# Malware
python -m vertice.cli malware analyze /tmp/test.txt

# Scan
python -m vertice.cli scan ports google.com

# Hunt
python -m vertice.cli hunt search "test"

# Maximus
python -m vertice.cli maximus ask "Olá Maximus"

# Monitor
python -m vertice.cli monitor logs test_service

# Menu
python -m vertice.cli menu
```

---

## 📞 Suporte

**Problemas?**
- Verifique o [Troubleshooting](#troubleshooting)
- Veja os [Exemplos Práticos](#exemplos-práticos)
- Contate o admin: `juan.brainfarma@gmail.com`

**Boa sorte nos testes! 🚀**
