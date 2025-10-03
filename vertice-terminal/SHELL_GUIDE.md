# 🚀 VÉRTICE Interactive Shell - Guia de Uso

## 📌 Visão Geral

O **VÉRTICE Interactive Shell** é uma interface interativa moderna e minimalista para comandos de cibersegurança, inspirada no Claude Code e Gemini. Quando você entra no shell, você está **dentro do VÉRTICE** - não mais no bash comum.

## 🎯 Como Iniciar

### Opção 1: Comando Direto (Recomendado)
```bash
vertice
```

### Opção 2: Via vcli
```bash
vcli shell
```

### Opção 3: Flag interativa
```bash
vcli --interactive
# ou
vcli -i
```

## 🎨 Características

### ✅ Interface Retangular Restrita
- Prompt visual delimitado (estilo Claude Code/Gemini)
- Usuário restrito ao ambiente VÉRTICE
- Layout clean e minimalista

### ✅ Slash Commands (/)
- **Todos os comandos começam com `/`**
- Autocompletar inteligente
- Lista de comandos ao digitar `/`

### ✅ Autocompletar Inteligente
- Digite `/` para ver todos os comandos
- Continue digitando para filtrar
- Use TAB para completar
- Mostra descrições dos comandos

### ✅ Histórico e Navegação
- **Seta pra cima/baixo**: Navegar histórico
- **Ctrl+R**: Buscar no histórico
- **Ctrl+C**: Cancelar entrada atual
- **Ctrl+D**: Sair do shell

## 📋 Comandos Disponíveis

### Autenticação
```
/auth login       - Login to VÉRTICE platform
/auth logout      - Logout from VÉRTICE
/auth status      - Check authentication status
/auth whoami      - Display current user info
```

### Inteligência de IP
```
/ip analyze <IP>  - Analyze an IP address
/ip my-ip         - Detect your public IP
/ip bulk <file>   - Bulk IP analysis from file
```

### Threat Intelligence
```
/threat lookup    - Lookup threat information
/threat check     - Check for threats
/threat feed      - Access threat feeds
```

### ADR (Detecção e Resposta)
```
/adr status       - Check ADR status
/adr metrics      - View ADR metrics
/adr alerts       - List active alerts
```

### Análise de Malware
```
/malware analyze  - Analyze a file for malware
/malware yara     - Run YARA scan
/malware hash     - Hash lookup
/malware submit   - Submit file for analysis
```

### Maximus AI
```
/maximus ask      - Ask Maximus a question
/maximus analyze  - AI-powered analysis
/maximus investigate - Incident investigation
/maximus oraculo  - Self-improvement mode
/maximus eureka   - Code analysis mode
```

### Scanning
```
/scan ports       - Port scanning
/scan nmap        - Nmap scan
/scan vulns       - Vulnerability scanning
/scan network     - Network discovery
```

### Monitoramento
```
/monitor threats  - Monitor threats
/monitor network  - Network monitoring
/monitor logs     - Log monitoring
```

### Threat Hunting
```
/hunt search      - IOC search
/hunt timeline    - Incident timeline
/hunt pivot       - Pivot analysis
/hunt correlate   - IOC correlation
```

### Menu Interativo
```
/menu             - Launch interactive menu
/menu interactive - Same as above
```

### Comandos Built-in
```
/help             - Show help information
/clear            - Clear screen
/exit             - Exit VÉRTICE shell
```

## 💡 Exemplos de Uso

### Exemplo 1: Análise de IP
```
╭─[VÉRTICE]
╰─> /ip analyze 8.8.8.8
```

### Exemplo 2: Usar Autocompletar
```
╭─[VÉRTICE]
╰─> /mal<TAB>
# Autocompleta para: /malware

╭─[VÉRTICE]
╰─> /malware <TAB>
# Mostra: analyze, yara, hash, submit
```

### Exemplo 3: Buscar no Histórico
```
# Pressione Ctrl+R e digite parte do comando
(reverse-i-search)`ip': /ip analyze 192.168.1.1
```

## 🎯 Diferenças do Modo Tradicional

### Antes (vcli tradicional)
```bash
juan@linux:~$ vcli ip analyze 8.8.8.8
juan@linux:~$ vcli malware analyze file.exe
juan@linux:~$ ls  # mistura com comandos bash
```

### Agora (VÉRTICE Shell)
```
╭─[VÉRTICE]
╰─> /ip analyze 8.8.8.8

╭─[VÉRTICE]
╰─> /malware analyze file.exe

╭─[VÉRTICE]
╰─> ls
[yellow]Commands must start with /[/yellow]
[dim]Type /help for available commands[/dim]
```

## 🔧 Atalhos de Teclado

| Atalho | Ação |
|--------|------|
| `Tab` | Autocompletar |
| `↑` / `↓` | Navegar histórico |
| `Ctrl+R` | Buscar histórico |
| `Ctrl+C` | Cancelar entrada |
| `Ctrl+D` | Sair |
| `Ctrl+A` | Início da linha |
| `Ctrl+E` | Fim da linha |
| `Ctrl+K` | Deletar até o fim |
| `Ctrl+U` | Deletar linha toda |

## 📌 Notas Importantes

1. **Comandos DEVEM começar com `/`**
   - Sem `/` = erro e dica
   - Com `/` = executa comando VÉRTICE

2. **Ambiente Isolado**
   - Você está dentro do VÉRTICE, não no bash
   - Para sair: `/exit` ou `Ctrl+D`

3. **Modo Tradicional**
   - Para usar vcli tradicional: `vcli <comando>`
   - Para shell interativo: `vertice`

4. **Serviços Backend**
   - Alguns comandos precisam dos serviços rodando
   - Verifique com: `docker compose ps`

## 🎨 Visual

```
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   ██╗   ██╗███████╗██████╗ ████████╗██╗ ██████╗███████╗  ║
║   ██║   ██║██╔════╝██╔══██╗╚══██╔══╝██║██╔════╝██╔════╝  ║
║   ██║   ██║█████╗  ██████╔╝   ██║   ██║██║     █████╗    ║
║   ╚██╗ ██╔╝██╔══╝  ██╔══██╗   ██║   ██║██║     ██╔══╝    ║
║    ╚████╔╝ ███████╗██║  ██║   ██║   ██║╚██████╗███████╗  ║
║     ╚═══╝  ╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝ ╚═════╝╚══════╝  ║
║                                                           ║
║            🔒 Cybersecurity Command Center 🔒             ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

  Welcome to VÉRTICE Interactive Shell
  Type /help for available commands or start typing / for autocomplete

╭─[VÉRTICE]
╰─> _
```

## 🚀 Próximos Passos

1. Inicie o shell: `vertice`
2. Digite `/help` para ver comandos
3. Use TAB para autocompletar
4. Explore os comandos disponíveis
5. Use `/exit` para sair

---

**Desenvolvido por Juan para Cybersecurity Professionals** 🛡️
