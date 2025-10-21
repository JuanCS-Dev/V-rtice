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
├── setup_vertice_cli.sh         # 🚀 SCRIPT DE SETUP AUTOMÁTICO
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

## 🚀 SETUP AUTOMÁTICO - BASH SCRIPT

**Script completo para criar toda a estrutura do projeto:**

```bash
#!/bin/bash
# setup_vertice_cli.sh
# Script de inicialização automática do Vertice CLI Terminal
# Cria toda a estrutura de diretórios e arquivos base

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Banner
echo -e "${CYAN}"
cat << "EOF"
██╗   ██╗███████╗██████╗ ████████╗██╗ ██████╗███████╗
██║   ██║██╔════╝██╔══██╗╚══██╔══╝██║██╔════╝██╔════╝
██║   ██║█████╗  ██████╔╝   ██║   ██║██║     █████╗
╚██╗ ██╔╝██╔══╝  ██╔══██╗   ██║   ██║██║     ██╔══╝
 ╚████╔╝ ███████╗██║  ██║   ██║   ██║╚██████╗███████╗
  ╚═══╝  ╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝ ╚═════╝╚══════╝

    CLI TERMINAL SETUP - Automated Project Initialization
EOF
echo -e "${NC}"

# Configuration
PROJECT_NAME="vertice-cli"
PROJECT_DIR="${1:-$(pwd)/$PROJECT_NAME}"

echo -e "${GREEN}[INFO]${NC} Initializing Vertice CLI Terminal at: ${BLUE}$PROJECT_DIR${NC}"
echo ""

# Create root directory
echo -e "${YELLOW}[STEP 1/8]${NC} Creating project root..."
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Create directory structure
echo -e "${YELLOW}[STEP 2/8]${NC} Creating directory structure..."

mkdir -p vertice/commands
mkdir -p vertice/connectors
mkdir -p vertice/utils
mkdir -p vertice/config
mkdir -p tests/test_commands
mkdir -p tests/test_connectors
mkdir -p docs

echo -e "${GREEN}  ✓${NC} Directory structure created"

# Create __init__.py files
echo -e "${YELLOW}[STEP 3/8]${NC} Creating Python packages..."

touch vertice/__init__.py
touch vertice/commands/__init__.py
touch vertice/connectors/__init__.py
touch vertice/utils/__init__.py
touch tests/__init__.py
touch tests/test_commands/__init__.py
touch tests/test_connectors/__init__.py

echo -e "${GREEN}  ✓${NC} Python packages initialized"

# Create command files
echo -e "${YELLOW}[STEP 4/8]${NC} Creating command modules..."

cat > vertice/commands/ip.py << 'EOF'
"""IP Intelligence commands."""
import click

@click.group()
def ip():
    """IP intelligence and analysis."""
    pass

@ip.command()
@click.argument('ip_address')
def analyze(ip_address):
    """Analyze an IP address."""
    click.echo(f"Analyzing IP: {ip_address}")
    # TODO: Implement
    pass
EOF

cat > vertice/commands/threat.py << 'EOF'
"""Threat Intelligence commands."""
import click

@click.group()
def threat():
    """Threat intelligence operations."""
    pass

@threat.command()
@click.argument('indicator')
def lookup(indicator):
    """Lookup threat indicator."""
    click.echo(f"Looking up threat: {indicator}")
    # TODO: Implement
    pass
EOF

cat > vertice/commands/adr.py << 'EOF'
"""ADR (Ameaça Digital em Redes) commands."""
import click

@click.group()
def adr():
    """ADR detection and response."""
    pass

@adr.command()
def status():
    """Check ADR system status."""
    click.echo("ADR Status: OK")
    # TODO: Implement
    pass
EOF

cat > vertice/commands/malware.py << 'EOF'
"""Malware Analysis commands."""
import click

@click.group()
def malware():
    """Malware analysis and detection."""
    pass

@malware.command()
@click.argument('file_path')
def scan(file_path):
    """Scan file for malware."""
    click.echo(f"Scanning file: {file_path}")
    # TODO: Implement
    pass
EOF

cat > vertice/commands/aurora.py << 'EOF'
"""Aurora AI Agent commands."""
import click

@click.group()
def aurora():
    """Aurora AI-powered operations."""
    pass

@aurora.command()
@click.argument('query')
def ask(query):
    """Ask Aurora AI a question."""
    click.echo(f"Aurora query: {query}")
    # TODO: Implement
    pass
EOF

cat > vertice/commands/scan.py << 'EOF'
"""Network scanning commands."""
import click

@click.group()
def scan():
    """Network and port scanning."""
    pass

@scan.command()
@click.argument('target')
def ports(target):
    """Scan target for open ports."""
    click.echo(f"Scanning ports on: {target}")
    # TODO: Implement
    pass
EOF

cat > vertice/commands/monitor.py << 'EOF'
"""Real-time monitoring commands."""
import click

@click.group()
def monitor():
    """Real-time security monitoring."""
    pass

@monitor.command()
def network():
    """Monitor network traffic."""
    click.echo("Starting network monitor...")
    # TODO: Implement
    pass
EOF

cat > vertice/commands/hunt.py << 'EOF'
"""Threat hunting commands."""
import click

@click.group()
def hunt():
    """Threat hunting operations."""
    pass

@hunt.command()
@click.argument('ioc')
def search(ioc):
    """Hunt for IOC (Indicator of Compromise)."""
    click.echo(f"Hunting for IOC: {ioc}")
    # TODO: Implement
    pass
EOF

echo -e "${GREEN}  ✓${NC} Command modules created"

# Create connector files
echo -e "${YELLOW}[STEP 5/8]${NC} Creating service connectors..."

cat > vertice/connectors/ip_intel.py << 'EOF'
"""IP Intelligence Service connector."""
import httpx

class IPIntelConnector:
    """Connect to IP Intelligence Service."""

    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()

    async def analyze_ip(self, ip_address):
        """Analyze IP address."""
        # TODO: Implement
        pass
EOF

cat > vertice/connectors/threat_intel.py << 'EOF'
"""Threat Intelligence Service connector."""
import httpx

class ThreatIntelConnector:
    """Connect to Threat Intel Service."""

    def __init__(self, base_url="http://localhost:8013"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()

    async def lookup_threat(self, indicator):
        """Lookup threat indicator."""
        # TODO: Implement
        pass
EOF

cat > vertice/connectors/adr_core.py << 'EOF'
"""ADR Core Service connector."""
import httpx

class ADRCoreConnector:
    """Connect to ADR Core Service."""

    def __init__(self, base_url="http://localhost:8014"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()

    async def get_status(self):
        """Get ADR system status."""
        # TODO: Implement
        pass
EOF

cat > vertice/connectors/malware.py << 'EOF'
"""Malware Analysis Service connector."""
import httpx

class MalwareConnector:
    """Connect to Malware Analysis Service."""

    def __init__(self, base_url="http://localhost:8011"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()

    async def scan_file(self, file_path):
        """Scan file for malware."""
        # TODO: Implement
        pass
EOF

cat > vertice/connectors/ai_agent.py << 'EOF'
"""Aurora AI Agent Service connector."""
import httpx

class AIAgentConnector:
    """Connect to Aurora AI Agent Service."""

    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()

    async def query(self, prompt):
        """Query Aurora AI."""
        # TODO: Implement
        pass
EOF

echo -e "${GREEN}  ✓${NC} Service connectors created"

# Create utility files
echo -e "${YELLOW}[STEP 6/8]${NC} Creating utility modules..."

cat > vertice/utils/banner.py << 'EOF'
"""Banner display utilities."""
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from datetime import datetime

console = Console()

def create_gradient_text(text, colors):
    """Create text with gradient colors."""
    lines = text.strip().split('\n')
    gradient_text = Text()

    for i, line in enumerate(lines):
        color_index = int((i / len(lines)) * len(colors))
        color_index = min(color_index, len(colors) - 1)
        gradient_text.append(line + '\n', style=colors[color_index])

    return gradient_text

def exibir_banner():
    """
    Display Vertice CLI banner.
    ⚠️ COPIED FROM: vertice_cli/utils.py:exibir_banner()
    """
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

    subtitle = Text()
    subtitle.append("Terminal CLI for Cybersecurity Professionals", style="bold white")

    info = Text()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    info.append(f"📅 {now}  ", style="dim cyan")
    info.append("🚀 AI-Powered  ", style="dim green")
    info.append("🔒 Enterprise-Grade", style="dim blue")

    panel_content = Text()
    panel_content.append(gradient_art)
    panel_content.append("\n")
    panel_content.append(Align.center(subtitle))
    panel_content.append("\n")
    panel_content.append(Align.center(info))

    panel = Panel(
        Align.center(panel_content),
        border_style="bright_cyan",
        padding=(1, 4)
    )

    console.print(panel)
    console.print()
EOF

cat > vertice/utils/output.py << 'EOF'
"""Output formatting utilities."""
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import json

console = Console()

def print_table(data, title=None):
    """Print data as a Rich table."""
    # TODO: Implement
    pass

def print_json(data):
    """Print data as formatted JSON."""
    console.print_json(json.dumps(data))

def print_success(message):
    """Print success message."""
    console.print(f"[green]✓[/green] {message}")

def print_error(message):
    """Print error message."""
    console.print(f"[red]✗[/red] {message}")

def print_warning(message):
    """Print warning message."""
    console.print(f"[yellow]⚠[/yellow] {message}")
EOF

cat > vertice/utils/config.py << 'EOF'
"""Configuration management."""
import os
from pathlib import Path
import yaml

class Config:
    """Configuration manager."""

    def __init__(self):
        self.config_dir = Path.home() / ".vertice"
        self.config_file = self.config_dir / "config.yaml"
        self.config = self.load()

    def load(self):
        """Load configuration."""
        if self.config_file.exists():
            with open(self.config_file) as f:
                return yaml.safe_load(f)
        return self.default_config()

    def save(self):
        """Save configuration."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            yaml.dump(self.config, f)

    def default_config(self):
        """Get default configuration."""
        return {
            "api_base_url": "http://localhost:8000",
            "output_format": "table",
            "cache_enabled": True,
            "cache_ttl": 3600,
        }
EOF

cat > vertice/utils/cache.py << 'EOF'
"""Local cache utilities."""
from pathlib import Path
import json
import time

class Cache:
    """Simple file-based cache."""

    def __init__(self, cache_dir=None):
        self.cache_dir = cache_dir or (Path.home() / ".vertice" / "cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, key, ttl=3600):
        """Get cached value."""
        # TODO: Implement
        pass

    def set(self, key, value):
        """Set cached value."""
        # TODO: Implement
        pass

    def clear(self):
        """Clear all cache."""
        # TODO: Implement
        pass
EOF

cat > vertice/utils/validators.py << 'EOF'
"""Input validation utilities."""
import re
from ipaddress import ip_address, AddressValueError

def validate_ip(ip):
    """Validate IP address."""
    try:
        ip_address(ip)
        return True
    except AddressValueError:
        return False

def validate_domain(domain):
    """Validate domain name."""
    pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    return re.match(pattern, domain) is not None

def validate_hash(hash_value, hash_type='md5'):
    """Validate hash value."""
    patterns = {
        'md5': r'^[a-fA-F0-9]{32}$',
        'sha1': r'^[a-fA-F0-9]{40}$',
        'sha256': r'^[a-fA-F0-9]{64}$',
    }
    pattern = patterns.get(hash_type.lower())
    if not pattern:
        return False
    return re.match(pattern, hash_value) is not None
EOF

echo -e "${GREEN}  ✓${NC} Utility modules created"

# Create config files
echo -e "${YELLOW}[STEP 7/8]${NC} Creating configuration files..."

cat > vertice/config/default.yaml << 'EOF'
# Default configuration for Vertice CLI
api:
  base_url: "http://localhost:8000"
  timeout: 30
  retry_attempts: 3

output:
  format: "table"  # Options: table, json, yaml
  color: true
  verbose: false

cache:
  enabled: true
  ttl: 3600  # seconds
  directory: "~/.vertice/cache"

services:
  ip_intelligence: "http://localhost:8000"
  threat_intel: "http://localhost:8013"
  adr_core: "http://localhost:8014"
  malware_analysis: "http://localhost:8011"
  ai_agent: "http://localhost:8001"
EOF

cat > vertice/config/services.yaml << 'EOF'
# Service endpoints configuration
services:
  api_gateway:
    url: "http://localhost:8000"
    port: 8000

  sinesp:
    url: "http://localhost:8001"
    port: 8001

  cyber:
    url: "http://localhost:8002"
    port: 8002

  domain:
    url: "http://localhost:8003"
    port: 8003

  ip_intelligence:
    url: "http://localhost:8004"
    port: 8004

  network_monitor:
    url: "http://localhost:8005"
    port: 8005

  nmap:
    url: "http://localhost:8006"
    port: 8006

  osint:
    url: "http://localhost:8007"
    port: 8007

  aurora_predict:
    url: "http://localhost:8008"
    port: 8008

  atlas:
    url: "http://localhost:8009"
    port: 8009

  auth:
    url: "http://localhost:8010"
    port: 8010

  vuln_scanner:
    url: "http://localhost:8011"
    port: 8011

  social_eng:
    url: "http://localhost:8012"
    port: 8012

  threat_intel:
    url: "http://localhost:8013"
    port: 8013

  malware_analysis:
    url: "http://localhost:8014"
    port: 8014

  ssl_monitor:
    url: "http://localhost:8015"
    port: 8015

  aurora_orchestrator:
    url: "http://localhost:8016"
    port: 8016

  ai_agent:
    url: "http://localhost:8017"
    port: 8017
EOF

echo -e "${GREEN}  ✓${NC} Configuration files created"

# Create main CLI entry point
echo -e "${YELLOW}[STEP 8/8]${NC} Creating main CLI entry point..."

cat > vertice/cli.py << 'EOF'
"""Main CLI entry point."""
import click
from vertice.utils.banner import exibir_banner
from vertice.commands import ip, threat, adr, malware, aurora, scan, monitor, hunt

@click.group()
@click.version_option(version='1.0.0')
@click.option('--no-banner', is_flag=True, help='Skip banner display')
def cli(no_banner):
    """
    Vertice CLI Terminal - Cybersecurity Command Line Interface.

    AI-powered security operations from your terminal.
    """
    if not no_banner:
        exibir_banner()

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
EOF

echo -e "${GREEN}  ✓${NC} Main CLI created"

# Create requirements.txt
cat > requirements.txt << 'EOF'
click>=8.1.0
rich>=13.0.0
httpx>=0.25.0
pyyaml>=6.0
python-dotenv>=1.0.0
questionary>=2.0.0
tabulate>=0.9.0
EOF

# Create setup.py
cat > setup.py << 'EOF'
from setuptools import setup, find_packages

setup(
    name='vertice-cli',
    version='1.0.0',
    description='Vertice CLI Terminal - Cybersecurity Command Line Interface',
    author='JuanCS-Dev',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'click>=8.1.0',
        'rich>=13.0.0',
        'httpx>=0.25.0',
        'pyyaml>=6.0',
        'python-dotenv>=1.0.0',
        'questionary>=2.0.0',
        'tabulate>=0.9.0',
    ],
    entry_points={
        'console_scripts': [
            'vertice=vertice.cli:cli',
        ],
    },
    python_requires='>=3.8',
)
EOF

# Create README.md
cat > README.md << 'EOF'
# 🎯 Vertice CLI Terminal

**AI-Powered Cybersecurity Command Line Interface**

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install CLI
pip install -e .

# Verify installation
vertice --version
```

## Quick Start

```bash
# Display help
vertice --help

# Analyze IP
vertice ip analyze 8.8.8.8

# Threat lookup
vertice threat lookup malicious.com

# Aurora AI query
vertice aurora ask "What are the latest threats?"

# Network scan
vertice scan ports example.com

# Start monitoring
vertice monitor network
```

## Documentation

See `docs/` directory for detailed documentation:

- `COMMANDS.md` - Complete command reference
- `WORKFLOWS.md` - Common workflows
- `SCRIPTING.md` - Scripting guide

## Configuration

Configuration file: `~/.vertice/config.yaml`

Service endpoints: `vertice/config/services.yaml`

## Architecture

- **Commands**: High-level user commands
- **Connectors**: Backend service integrations
- **Utils**: Shared utilities (output, config, cache)
- **Tests**: Unit and integration tests

## Development

```bash
# Run tests
pytest

# Run with debug
vertice --verbose ip analyze 1.2.3.4

# Clear cache
rm -rf ~/.vertice/cache
```

## License

Proprietary - Vertice Platform
EOF

# Create basic documentation
cat > docs/COMMANDS.md << 'EOF'
# Vertice CLI - Command Reference

## Commands

### ip
IP Intelligence and analysis

### threat
Threat intelligence operations

### adr
ADR detection and response

### malware
Malware analysis and detection

### aurora
Aurora AI-powered operations

### scan
Network and port scanning

### monitor
Real-time security monitoring

### hunt
Threat hunting operations

---

See README.md for usage examples.
EOF

cat > docs/WORKFLOWS.md << 'EOF'
# Common Workflows

## Incident Response

```bash
# 1. Analyze suspicious IP
vertice ip analyze 1.2.3.4

# 2. Lookup in threat feeds
vertice threat lookup 1.2.3.4

# 3. Check for malware
vertice malware scan /path/to/file

# 4. Hunt for IOCs
vertice hunt search <hash>
```

## Threat Hunting

```bash
# 1. Query Aurora AI
vertice aurora ask "Latest APT campaigns"

# 2. Scan network
vertice scan ports 192.168.1.0/24

# 3. Monitor traffic
vertice monitor network
```

---

See COMMANDS.md for all available commands.
EOF

cat > docs/SCRIPTING.md << 'EOF'
# Scripting Guide

## Bash Integration

```bash
#!/bin/bash
# Scan multiple IPs

for ip in $(cat ips.txt); do
  vertice ip analyze "$ip" --output json >> results.json
done
```

## Python Integration

```python
import subprocess
import json

result = subprocess.run(
    ['vertice', 'ip', 'analyze', '8.8.8.8', '--output', 'json'],
    capture_output=True,
    text=True
)

data = json.loads(result.stdout)
print(data)
```

---

See WORKFLOWS.md for common use cases.
EOF

# Create .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Testing
.pytest_cache/
.coverage
htmlcov/

# Config
.env
*.local.yaml
EOF

# Final message
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Vertice CLI Terminal setup completed successfully!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${CYAN}Project structure created at:${NC}"
echo -e "  ${BLUE}$PROJECT_DIR${NC}"
echo ""
echo -e "${CYAN}Next steps:${NC}"
echo -e "  1. ${YELLOW}cd $PROJECT_DIR${NC}"
echo -e "  2. ${YELLOW}python3 -m venv venv${NC}"
echo -e "  3. ${YELLOW}source venv/bin/activate${NC}"
echo -e "  4. ${YELLOW}pip install -r requirements.txt${NC}"
echo -e "  5. ${YELLOW}pip install -e .${NC}"
echo -e "  6. ${YELLOW}vertice --help${NC}"
echo ""
echo -e "${GREEN}Happy hacking! 🚀${NC}"
echo ""

# Tree output (if available)
if command -v tree &> /dev/null; then
    echo -e "${CYAN}Project structure:${NC}"
    tree -L 3 -I '__pycache__|*.pyc|venv|env' "$PROJECT_DIR"
else
    echo -e "${YELLOW}[TIP]${NC} Install 'tree' to visualize project structure: ${BLUE}sudo apt install tree${NC}"
fi
```

**Save this as**: `setup_vertice_cli.sh`

**Usage**:
```bash
# Give execution permission
chmod +x setup_vertice_cli.sh

# Run with default location (./vertice-cli)
./setup_vertice_cli.sh

# Or specify custom directory
./setup_vertice_cli.sh /path/to/custom/location
```

**What it does**:
1. ✅ Creates complete directory structure
2. ✅ Creates all `__init__.py` files
3. ✅ Creates all command modules (8 commands)
4. ✅ Creates all connector modules (5 connectors)
5. ✅ Creates all utility modules (banner, output, config, cache, validators)
6. ✅ Creates configuration files (YAML)
7. ✅ Creates main CLI entry point
8. ✅ Creates `setup.py` for installation
9. ✅ Creates `requirements.txt`
10. ✅ Creates `README.md` with docs
11. ✅ Creates documentation files
12. ✅ Creates `.gitignore`
13. ✅ Shows pretty output with colors
14. ✅ Displays next steps

**After running**:
```bash
cd vertice-cli
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
vertice --help
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
