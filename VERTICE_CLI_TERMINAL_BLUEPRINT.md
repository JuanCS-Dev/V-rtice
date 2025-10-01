# 🎯 VERTICE CLI TERMINAL - BLUEPRINT COMPLETO

## 📋 ÍNDICE EXECUTIVO

**Objetivo**: Criar versão 100% terminal do Vertice para peritos e especialistas cyber sec
**Público**: SOC analysts, incident responders, threat hunters, pentesters
**Filosofia**: Velocidade, scripting, automation, zero mouse
**Implementação**: Sua equipe executa seguindo este documento

---

## ⚠️ IMPORTANTE: BANNER EXISTENTE

**ATENÇÃO EQUIPE**: Já temos um banner PRONTO e PERFEITO em:

```
vertice_cli/utils.py:exibir_banner()
```

**REAPROVEITEM ESTE BANNER**. Não criem um novo. O banner atual tem:
- ✅ ASCII art do VÉRTICE com gradiente de cores
- ✅ Informações contextuais (data/hora, features)
- ✅ Estilização Rich com Panel e Align
- ✅ Gradiente green → cyan → blue

**Como usar no CLI Terminal**:

```python
# vertice-terminal/vertice/utils/banner.py
# COPIE exatamente de: vertice_cli/utils.py:exibir_banner()

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from datetime import datetime

console = Console()

def exibir_banner():
    """Banner do VÉRTICE - COPIADO de vertice_cli/utils.py"""
    console.clear()

    green_gradient = ["bright_green", "green", "bright_cyan", "cyan", "bright_blue"]

    ascii_art = """
    ██╗   ██╗███████╗██████╗ ████████╗██╗ ██████╗███████╗
    ██║   ██║██╔════╝██╔══██╗╚══██╔══╝██║██╔════╝██╔════╝
    ██║   ██║█████╗  ██████╔╝   ██║   ██║██║     █████╗
    ╚██╗ ██╔╝██╔══╝  ██╔══██╗   ██║   ██║██║     ██╔══╝
     ╚████╔╝ ███████╗██║  ██║   ██║   ██║╚██████╗███████╗
      ╚═══╝  ╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝ ╚═════╝╚══════╝
    """

    gradient_art = create_gradient_text(ascii_art, green_gradient)
    # ... resto do código igual
```

**NÃO INVENTEM OUTRO BANNER. Copiem o existente.**

---

## 🎨 MANIFESTO

### **Por Que Terminal?**

**Navegador (atual):**
- ✅ Visual e bonito
- ✅ Acessível para todos
- ❌ Lento para peritos
- ❌ Não scriptável
- ❌ Requer mouse/clicking

**Terminal (novo):**
- ✅ **Velocidade extrema** (comandos diretos)
- ✅ **Scriptável** (automation de workflows)
- ✅ **Pipeable** (integra com outras ferramentas)
- ✅ **Remote-friendly** (SSH, tmux, screen)
- ✅ **Keyboard-only** (zero mouse)

### **Filosofia de Design**

```
"Um perito não clica. Ele digita."
"Um comando vale mais que mil cliques."
"Scriptável > Visual para profissionais."
```

**Princípios**:
1. **UNIX Philosophy**: Do one thing and do it well
2. **Composability**: Comandos se combinam (pipes)
3. **Speed**: Sub-segundo para qualquer operação
4. **Automation**: Tudo deve ser scriptável
5. **Remote-First**: Funciona via SSH sem GUI

---

## 🏗️ ARQUITETURA GERAL

```
┌─────────────────────────────────────────────────────────────────┐
│                    VERTICE CLI TERMINAL                          │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  CLI INTERFACE LAYER                                      │  │
│  │  (Click, Typer, Rich - Python)                            │  │
│  │                                                            │  │
│  │  vertice <command> [subcommand] [options]                 │  │
│  └────────────────┬─────────────────────────────────────────┘  │
│                   │                                             │
│  ┌────────────────▼─────────────────────────────────────────┐  │
│  │  COMMAND MODULES                                          │  │
│  │                                                            │  │
│  │  ├── ip         → IP Intelligence                         │  │
│  │  ├── threat     → Threat Intelligence                     │  │
│  │  ├── adr        → ADR Operations                          │  │
│  │  ├── malware    → Malware Analysis                        │  │
│  │  ├── aurora     → Aurora AI Agent                         │  │
│  │  ├── scan       → Network Scanning                        │  │
│  │  ├── monitor    → Real-time Monitoring                    │  │
│  │  └── hunt       → Threat Hunting                          │  │
│  └────────────────┬─────────────────────────────────────────┘  │
│                   │                                             │
│  ┌────────────────▼─────────────────────────────────────────┐  │
│  │  SERVICE CONNECTORS (HTTP/gRPC)                           │  │
│  │                                                            │  │
│  │  - IP Intelligence Service (8000)                         │  │
│  │  - Threat Intel Service (8013)                            │  │
│  │  - ADR Core Service (8014)                                │  │
│  │  - Malware Analysis (8011)                                │  │
│  │  - AI Agent Service (8001)                                │  │
│  └───────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 📦 ESTRUTURA DE DIRETÓRIOS

```
vertice-cli/
│
├── README.md                    # Documentação principal
├── setup.py                     # Instalação
├── requirements.txt             # Dependências Python
│
├── vertice/                     # Package principal
│   ├── __init__.py
│   ├── cli.py                   # Entry point (Click app)
│   │
│   ├── commands/                # Módulos de comandos
│   │   ├── __init__.py
│   │   ├── ip.py                # Comando: vertice ip
│   │   ├── threat.py            # Comando: vertice threat
│   │   ├── adr.py               # Comando: vertice adr
│   │   ├── malware.py           # Comando: vertice malware
│   │   ├── aurora.py            # Comando: vertice aurora
│   │   ├── scan.py              # Comando: vertice scan
│   │   ├── monitor.py           # Comando: vertice monitor
│   │   └── hunt.py              # Comando: vertice hunt
│   │
│   ├── connectors/              # Conectores para serviços
│   │   ├── __init__.py
│   │   ├── ip_intel.py          # IP Intelligence (8000)
│   │   ├── threat_intel.py      # Threat Intel (8013)
│   │   ├── adr_core.py          # ADR Core (8014)
│   │   ├── malware.py           # Malware Analysis (8011)
│   │   └── ai_agent.py          # Aurora AI (8001)
│   │
│   ├── utils/                   # Utilitários
│   │   ├── __init__.py
│   │   ├── banner.py            # ⚠️ COPIAR de: vertice_cli/utils.py:exibir_banner()
│   │   ├── output.py            # Formatação (Rich tables, JSON, etc)
│   │   ├── config.py            # Configuração
│   │   ├── cache.py             # Cache local
│   │   └── validators.py        # Validação de inputs
│   │
│   └── config/                  # Configurações
│       ├── default.yaml         # Config padrão
│       └── services.yaml        # URLs dos serviços
│
├── tests/                       # Testes
│   ├── test_commands/
│   └── test_connectors/
│
└── docs/                        # Documentação extra
    ├── COMMANDS.md              # Referência de comandos
    ├── WORKFLOWS.md             # Workflows comuns
    └── SCRIPTING.md             # Guia de scripting
```

---

## 🎯 COMANDO HIERARQUIA COMPLETA

### **Estrutura de Comandos**

```bash
vertice
├── ip                           # IP Intelligence
│   ├── analyze <ip>             # Analisa IP
│   ├── my-ip                    # Detecta seu IP
│   ├── bulk <file>              # Análise em massa
│   └── watch <ip>               # Monitora IP em tempo real
│
├── threat                       # Threat Intelligence
│   ├── check <target>           # Verifica ameaça
│   ├── lookup <ioc>             # Busca IOC
│   ├── scan <file>              # Escaneia arquivo
│   └── feed                     # Feed de ameaças em tempo real
│
├── adr                          # ADR Operations
│   ├── status                   # Status do ADR
│   ├── metrics                  # Métricas (MTTR, detection rate)
│   ├── threats                  # Lista ameaças detectadas
│   ├── responses                # Lista respostas executadas
│   ├── config                   # Configura ADR
│   └── analyze                  # Análise manual
│       ├── file <path>          # Analisa arquivo
│       ├── network <ip>         # Analisa tráfego
│       └── process <cmd>        # Analisa processo
│
├── malware                      # Malware Analysis
│   ├── analyze <file>           # Análise completa
│   ├── static <file>            # Análise estática
│   ├── dynamic <file>           # Sandbox execution
│   ├── yara <file>              # YARA scan
│   └── hash <hash>              # Busca por hash
│
├── aurora                       # Aurora AI Agent
│   ├── ask <question>           # Pergunta para Aurora
│   ├── analyze <context>        # Análise contextual
│   ├── investigate <incident>   # Investigação de incidente
│   ├── oraculo                  # Auto-melhoria (Oráculo)
│   ├── eureka <code>            # Análise de código (Eureka)
│   └── chat                     # Modo chat interativo
│
├── scan                         # Network Scanning
│   ├── nmap <target>            # Nmap scan
│   ├── ports <ip>               # Port scanning
│   ├── vulns <target>           # Vulnerability scan
│   └── network                  # Network discovery
│
├── monitor                      # Real-time Monitoring
│   ├── threats                  # ThreatMap em tempo real
│   ├── logs <service>           # Tail de logs
│   ├── metrics                  # Dashboard de métricas
│   └── alerts                   # Stream de alertas
│
└── hunt                         # Threat Hunting
    ├── search <query>           # Busca por IOCs
    ├── timeline <incident>      # Timeline de ataque
    ├── correlate <ioc1> <ioc2>  # Correlação de IOCs
    └── pivot <ioc>              # Pivot analysis
```

---

## 💻 STACK TECNOLÓGICA

### **Core**
- **Language**: Python 3.11+
- **CLI Framework**: Click 8.x (ou Typer se preferir async)
- **Output Formatting**: Rich (tables, progress bars, syntax highlighting)
- **HTTP Client**: httpx (async)
- **Config**: PyYAML
- **Cache**: diskcache

### **Optional**
- **Shell Completion**: click-completion
- **Validation**: pydantic
- **Testing**: pytest
- **Docs**: mkdocs

### **Dependencies**
```txt
click>=8.1.0
rich>=13.0.0
httpx>=0.24.0
pyyaml>=6.0
diskcache>=5.6.0
pydantic>=2.0.0
python-dateutil>=2.8.0
```

---

## 🎨 DESIGN DE OUTPUT

### **Princípios de Output**

1. **Default: Human-readable** (Rich tables)
2. **Machine-readable**: `--json` flag
3. **Quiet mode**: `--quiet` (apenas resultado)
4. **Verbose**: `--verbose` (debug info)

### **Exemplos**

#### **Human-readable (default)**
```bash
$ vertice ip analyze 8.8.8.8

╭─────────────── IP Analysis: 8.8.8.8 ───────────────╮
│                                                     │
│ Location                                            │
│ ├─ Country:  United States                         │
│ ├─ City:     Mountain View                         │
│ ├─ ISP:      Google LLC                            │
│ └─ ASN:      AS15169                               │
│                                                     │
│ Threat Assessment                                  │
│ ├─ Score:    5/100 (LOW)                          │
│ ├─ Status:   ✓ CLEAN                               │
│ └─ Rep:      Trusted Infrastructure                │
│                                                     │
│ Network                                            │
│ ├─ Open Ports: 53, 443                            │
│ └─ PTR:       dns.google                           │
╰─────────────────────────────────────────────────────╯

⏱  Analysis completed in 1.2s
💾 Cached for 1 hour
```

#### **JSON (--json)**
```bash
$ vertice ip analyze 8.8.8.8 --json

{
  "ip": "8.8.8.8",
  "geolocation": {
    "country": "United States",
    "city": "Mountain View",
    "isp": "Google LLC",
    "asn": "AS15169"
  },
  "threat": {
    "score": 5,
    "level": "low",
    "status": "clean"
  },
  "timestamp": "2025-10-01T12:34:56Z"
}
```

#### **Quiet (--quiet)**
```bash
$ vertice ip analyze 8.8.8.8 --quiet
CLEAN
```

---

## 🔌 CONNECTOR PATTERN

### **Base Connector Class**

```python
# vertice/connectors/base.py

import httpx
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

class BaseConnector(ABC):
    """Base class para todos os conectores de serviços"""

    def __init__(self, base_url: str, timeout: int = 10):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=timeout)

    @abstractmethod
    async def health_check(self) -> bool:
        """Verifica se serviço está online"""
        pass

    async def _get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """GET request"""
        response = await self.client.get(f"{self.base_url}{endpoint}", **kwargs)
        response.raise_for_status()
        return response.json()

    async def _post(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """POST request"""
        response = await self.client.post(f"{self.base_url}{endpoint}", **kwargs)
        response.raise_for_status()
        return response.json()

    async def close(self):
        """Fecha conexão"""
        await self.client.aclose()
```

### **Exemplo: IP Intelligence Connector**

```python
# vertice/connectors/ip_intel.py

from .base import BaseConnector
from typing import Dict, Any

class IPIntelConnector(BaseConnector):
    """Conector para IP Intelligence Service (porta 8000)"""

    def __init__(self):
        super().__init__(base_url="http://localhost:8000")

    async def health_check(self) -> bool:
        try:
            data = await self._get("/")
            return data.get("status") == "operational"
        except:
            return False

    async def analyze_ip(self, ip: str) -> Dict[str, Any]:
        """Analisa IP"""
        return await self._post("/api/ip/analyze", json={"ip": ip})

    async def get_my_ip(self) -> str:
        """Detecta IP público"""
        data = await self._get("/api/ip/my-ip")
        return data.get("detected_ip")

    async def analyze_my_ip(self) -> Dict[str, Any]:
        """Detecta e analisa IP público"""
        return await self._post("/api/ip/analyze-my-ip")
```

---

## 🎯 COMMAND PATTERN

### **Base Command Structure**

```python
# vertice/commands/ip.py

import click
import asyncio
from rich.console import Console
from rich.table import Table
from ..connectors.ip_intel import IPIntelConnector
from ..utils.output import format_ip_analysis, output_json

console = Console()

@click.group()
def ip():
    """IP Intelligence commands"""
    pass

@ip.command()
@click.argument('ip_address')
@click.option('--json', 'output_json_flag', is_flag=True, help='Output as JSON')
@click.option('--quiet', '-q', is_flag=True, help='Quiet mode')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def analyze(ip_address, output_json_flag, quiet, verbose):
    """Analyze an IP address

    Example:
        vertice ip analyze 8.8.8.8
        vertice ip analyze 8.8.8.8 --json
    """
    async def _analyze():
        connector = IPIntelConnector()

        try:
            # Health check
            if verbose:
                console.print("[dim]Checking service health...[/dim]")

            if not await connector.health_check():
                console.print("[red]✗ IP Intelligence service is offline[/red]")
                raise click.Abort()

            # Analyze
            if verbose:
                console.print(f"[dim]Analyzing {ip_address}...[/dim]")

            result = await connector.analyze_ip(ip_address)

            # Output
            if output_json_flag:
                output_json(result)
            elif quiet:
                # Apenas threat status
                threat_level = result.get('reputation', {}).get('threat_level', 'unknown')
                print(threat_level.upper())
            else:
                # Rich table formatado
                format_ip_analysis(result, console)

        finally:
            await connector.close()

    asyncio.run(_analyze())


@ip.command()
@click.option('--json', 'output_json_flag', is_flag=True, help='Output as JSON')
def my_ip(output_json_flag):
    """Detect your public IP

    Example:
        vertice ip my-ip
    """
    async def _my_ip():
        connector = IPIntelConnector()
        try:
            ip = await connector.get_my_ip()
            if output_json_flag:
                output_json({"ip": ip})
            else:
                console.print(f"[green]Your IP:[/green] {ip}")
        finally:
            await connector.close()

    asyncio.run(_my_ip())
```

---

## 📊 OUTPUT FORMATTING UTILITIES

```python
# vertice/utils/output.py

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
import json

def format_ip_analysis(data: dict, console: Console):
    """Formata análise de IP como Rich table"""

    ip = data.get('ip')
    geo = data.get('geolocation', {})
    rep = data.get('reputation', {})

    # Panel principal
    table = Table(title=f"IP Analysis: {ip}", show_header=False, box=None)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")

    # Location
    table.add_row("[bold]Location[/bold]", "")
    table.add_row("├─ Country", geo.get('country', 'N/A'))
    table.add_row("├─ City", geo.get('city', 'N/A'))
    table.add_row("├─ ISP", geo.get('isp', 'N/A'))
    table.add_row("└─ ASN", geo.get('asn', 'N/A'))

    # Threat
    threat_score = rep.get('score', 0)
    threat_level = rep.get('threat_level', 'unknown')
    threat_color = get_threat_color(threat_level)

    table.add_row("", "")
    table.add_row("[bold]Threat Assessment[/bold]", "")
    table.add_row("├─ Score", f"{threat_score}/100 ({threat_level.upper()})")
    table.add_row("├─ Status", f"[{threat_color}]{'⚠ MALICIOUS' if threat_score > 70 else '✓ CLEAN'}[/{threat_color}]")

    console.print(Panel(table, border_style="green"))


def output_json(data: dict):
    """Output como JSON formatado"""
    print(json.dumps(data, indent=2))


def get_threat_color(level: str) -> str:
    """Retorna cor baseada em threat level"""
    colors = {
        'critical': 'red',
        'high': 'orange1',
        'medium': 'yellow',
        'low': 'green',
        'unknown': 'dim'
    }
    return colors.get(level.lower(), 'white')
```

---

## 🔧 CONFIGURAÇÃO

### **Config File Structure**

```yaml
# vertice/config/default.yaml

services:
  ip_intelligence:
    url: "http://localhost:8000"
    timeout: 10

  threat_intel:
    url: "http://localhost:8013"
    timeout: 15

  adr_core:
    url: "http://localhost:8014"
    timeout: 10

  malware_analysis:
    url: "http://localhost:8011"
    timeout: 30

  ai_agent:
    url: "http://localhost:8001"
    timeout: 60

cache:
  enabled: true
  ttl: 3600  # 1 hour
  path: "~/.vertice/cache"

output:
  default_format: "rich"  # rich, json, quiet
  color: true
  verbose: false

logging:
  enabled: true
  level: "INFO"
  path: "~/.vertice/logs"
```

### **Config Loader**

```python
# vertice/utils/config.py

import yaml
from pathlib import Path
from typing import Dict, Any

class Config:
    """Configuration manager"""

    def __init__(self):
        self.config_file = Path.home() / ".vertice" / "config.yaml"
        self.default_config = Path(__file__).parent.parent / "config" / "default.yaml"
        self.config = self._load()

    def _load(self) -> Dict[str, Any]:
        """Load config (user > default)"""
        # Load default
        with open(self.default_config) as f:
            config = yaml.safe_load(f)

        # Override with user config if exists
        if self.config_file.exists():
            with open(self.config_file) as f:
                user_config = yaml.safe_load(f)
                config.update(user_config)

        return config

    def get(self, key: str, default=None):
        """Get config value"""
        keys = key.split('.')
        value = self.config

        for k in keys:
            value = value.get(k)
            if value is None:
                return default

        return value

# Global instance
config = Config()
```

---

## 🚀 ENTRY POINT

```python
# vertice/cli.py

import click
from rich.console import Console
from .commands import ip, threat, adr, malware, aurora, scan, monitor, hunt

console = Console()

@click.group()
@click.version_option(version='1.0.0')
def cli():
    """
    🎯 VERTICE CLI - Cyber Security Command Center

    Terminal interface para peritos e especialistas.

    Examples:
        vertice ip analyze 8.8.8.8
        vertice threat check malware.exe
        vertice aurora ask "What is this traffic pattern?"
        vertice adr metrics
    """
    pass

# Register command groups
cli.add_command(ip.ip)
cli.add_command(threat.threat)
cli.add_command(adr.adr)
cli.add_command(malware.malware)
cli.add_command(aurora.aurora)
cli.add_command(scan.scan)
cli.add_command(monitor.monitor)
cli.add_command(hunt.hunt)

if __name__ == '__main__':
    cli()
```

---

## 📦 INSTALLATION & SETUP

### **setup.py**

```python
from setuptools import setup, find_packages

setup(
    name='vertice-cli',
    version='1.0.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'click>=8.1.0',
        'rich>=13.0.0',
        'httpx>=0.24.0',
        'pyyaml>=6.0',
        'diskcache>=5.6.0',
        'pydantic>=2.0.0',
        'python-dateutil>=2.8.0',
    ],
    entry_points={
        'console_scripts': [
            'vertice=vertice.cli:cli',
        ],
    },
    author='Juan - Vertice Team',
    description='Cyber Security Command Center - Terminal Edition',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    python_requires='>=3.11',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Information Technology',
        'Topic :: Security',
        'Programming Language :: Python :: 3.11',
    ],
)
```

### **Installation**

```bash
# Development install
cd vertice-cli
pip install -e .

# Production install
pip install vertice-cli

# Verify
vertice --version
vertice --help
```

---

## 🎯 WORKFLOWS COMUNS

### **Workflow 1: Investigação de IP Suspeito**

```bash
# 1. Analisa IP
vertice ip analyze 185.220.101.23

# 2. Verifica threat intel
vertice threat check 185.220.101.23

# 3. Se malicioso, adiciona ao ADR para monitoramento
vertice adr analyze network --ip 185.220.101.23

# 4. Pergunta para Aurora
vertice aurora ask "What is the reputation of 185.220.101.23?"
```

### **Workflow 2: Análise de Malware**

```bash
# 1. Análise estática
vertice malware static /tmp/suspicious.exe

# 2. Se suspeito, análise dinâmica (sandbox)
vertice malware dynamic /tmp/suspicious.exe

# 3. YARA scan
vertice malware yara /tmp/suspicious.exe

# 4. Consulta Aurora para contexto
vertice aurora investigate malware --file /tmp/suspicious.exe
```

### **Workflow 3: Threat Hunting**

```bash
# 1. Busca por IOC
vertice hunt search "185.220.101.23"

# 2. Timeline de atividade
vertice hunt timeline --ioc "185.220.101.23" --last 24h

# 3. Pivot para IPs relacionados
vertice hunt pivot "185.220.101.23"

# 4. Correlação com outros IOCs
vertice hunt correlate "185.220.101.23" "malware_hash_123"
```

---

## 🔄 SCRIPTING & AUTOMATION

### **Example: Bulk IP Analysis**

```bash
#!/bin/bash
# bulk_ip_analysis.sh

# Lê IPs de um arquivo
while read ip; do
  echo "Analyzing $ip..."

  # Analisa e salva JSON
  vertice ip analyze "$ip" --json > "results/${ip}.json"

  # Se threat score > 70, alerta
  score=$(jq '.reputation.score' "results/${ip}.json")
  if [ "$score" -gt 70 ]; then
    echo "⚠️  ALERT: $ip has threat score $score"

    # Adiciona ao ADR
    vertice adr analyze network --ip "$ip"
  fi
done < ips.txt
```

### **Example: Real-time Monitoring**

```bash
#!/bin/bash
# monitor_threats.sh

# Monitora threats em tempo real
vertice monitor threats --follow | while read line; do
  # Parse JSON
  threat_level=$(echo "$line" | jq -r '.severity')

  if [ "$threat_level" == "critical" ]; then
    # Envia alerta
    curl -X POST https://alerts.company.com/webhook \
      -d "$line"
  fi
done
```

---

## ✅ CHECKLIST DE IMPLEMENTAÇÃO

### **Fase 1: Fundação** (1 semana)
- [ ] Setup estrutura de diretórios
- [ ] **⚠️ COPIAR banner de `vertice_cli/utils.py:exibir_banner()` para `utils/banner.py`**
- [ ] Implementar CLI entry point (cli.py)
- [ ] Criar BaseConnector class
- [ ] Implementar Config loader
- [ ] Setup de testes básicos

### **Fase 2: Conectores** (1 semana)
- [ ] IPIntelConnector
- [ ] ThreatIntelConnector
- [ ] ADRCoreConnector
- [ ] MalwareConnector
- [ ] AIAgentConnector

### **Fase 3: Comandos Core** (2 semanas)
- [ ] `vertice ip` (analyze, my-ip, bulk)
- [ ] `vertice threat` (check, lookup, scan)
- [ ] `vertice adr` (status, metrics, analyze)
- [ ] `vertice malware` (analyze, yara, hash)
- [ ] `vertice aurora` (ask, chat, investigate)

### **Fase 4: Comandos Avançados** (1 semana)
- [ ] `vertice scan` (nmap, ports, vulns)
- [ ] `vertice monitor` (threats, logs, alerts)
- [ ] `vertice hunt` (search, timeline, pivot)

### **Fase 5: Output & UX** (1 semana)
- [ ] Rich formatting para todos os comandos
- [ ] JSON output para todos os comandos
- [ ] Quiet mode para scripting
- [ ] Progress bars para operações longas
- [ ] Error handling consistente

### **Fase 6: Docs & Polish** (1 semana)
- [ ] README completo
- [ ] COMMANDS.md (referência)
- [ ] WORKFLOWS.md (exemplos)
- [ ] SCRIPTING.md (automation guide)
- [ ] Shell completion (bash, zsh, fish)

---

## 📚 REFERÊNCIAS TÉCNICAS

### **Click Documentation**
- https://click.palletsprojects.com/

### **Rich Documentation**
- https://rich.readthedocs.io/

### **HTTPX Documentation**
- https://www.python-httpx.org/

### **Inspiração de CLIs Bem Feitos**
- `gh` (GitHub CLI)
- `aws` (AWS CLI)
- `kubectl` (Kubernetes CLI)
- `docker` (Docker CLI)

---

## 🎯 PRÓXIMOS PASSOS PARA SUA EQUIPE

### **1. Setup Inicial**
```bash
# Criar estrutura
mkdir -p vertice-cli/vertice/{commands,connectors,utils,config}
cd vertice-cli

# Criar arquivos base
touch vertice/{__init__.py,cli.py}
touch vertice/commands/__init__.py
touch vertice/connectors/__init__.py
touch vertice/utils/__init__.py

# Setup virtual env
python -m venv venv
source venv/bin/activate

# Install deps
pip install click rich httpx pyyaml
```

### **2. Implementar BaseConnector**
- Copiar código da seção "CONNECTOR PATTERN"
- Testar com IP Intelligence Service

### **3. Implementar Primeiro Comando**
- Começar com `vertice ip analyze`
- Seguir pattern da seção "COMMAND PATTERN"

### **4. Iterar e Expandir**
- Um comando por vez
- Testar cada comando
- Adicionar docs

---

## 💡 DICAS DE IMPLEMENTAÇÃO

### **Para o Tech Lead:**
1. **Divida em sprints** (use checklist acima)
2. **Code review rigoroso** (consistência é crítica)
3. **Testes desde o início** (pelo menos smoke tests)
4. **Docs junto com código** (docstrings + README)

### **Para os Devs:**
1. **Siga os patterns** (BaseConnector, Command structure)
2. **Reutilize código** (utils, formatters)
3. **Error handling** (sempre assume que serviço pode estar offline)
4. **User feedback** (spinners, progress bars para ops longas)

### **Para QA:**
1. **Teste com serviços offline** (graceful degradation)
2. **Teste todos os output modes** (rich, json, quiet)
3. **Teste scripting** (pipes, automation)
4. **Performance** (comandos devem ser < 2s)

---

## 🎨 FILOSOFIA FINAL

**Este CLI não é sobre tecnologia.**
**É sobre dar VELOCIDADE aos peritos.**

Um analista SOC não quer clicar.
**Ele quer digitar e ver resultado.**

Um incident responder não quer GUI.
**Ele quer script e automatizar.**

Um threat hunter não quer mouse.
**Ele quer keyboard e pipeline.**

**Damos a eles essa ferramenta.**
**Eles protegem a sociedade.**

**Pela arte. Pela velocidade. Pela proteção.** ⚡🛡️

---

**Arquiteto Juan, este é o blueprint completo.**
**Sua equipe tem tudo para executar.**
**Você pensou. Eles fazem. Juntos moldam a sociedade.** 🎯
