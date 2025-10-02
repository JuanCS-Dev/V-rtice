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
virtualenv/
venv/
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
